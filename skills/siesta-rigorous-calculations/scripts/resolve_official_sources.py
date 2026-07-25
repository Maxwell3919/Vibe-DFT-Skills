#!/usr/bin/env python3
"""Resolve SIESTA topics or exact FDF labels against pinned official evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from siesta_fdf_labels import matches_official_label


SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCES = SKILL_ROOT / "references"
REGISTRY = REFERENCES / "official-source-registry.json"
FDF_INDEX = REFERENCES / "official-fdf-index.json"
SUPPLEMENTS = REFERENCES / "official-source-supplements.json"
ALLOWED_HOSTS = {"docs.siesta-project.org", "siesta-project.org", "www.siesta-project.org", "gitlab.com"}


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def pattern_matches(term: str, pattern: str) -> bool:
    return matches_official_label(term, pattern)


def load_contracts() -> tuple[dict, dict, dict]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    index = json.loads(FDF_INDEX.read_text(encoding="utf-8"))
    supplements = json.loads(SUPPLEMENTS.read_text(encoding="utf-8"))
    if (
        registry.get("schema_version") != "1.0"
        or not isinstance(registry.get("sources"), list)
        or index.get("schema_version") != "1.0"
        or index.get("code") != "siesta"
        or index.get("entry_count") != len(index.get("entries", []))
        or supplements.get("schema_version") != "1.0"
        or supplements.get("source_commit") != index.get("source_commit")
    ):
        raise ValueError("unsupported or inconsistent official-source contracts")
    return registry, index, supplements


def verified_fetch(url: str, expected_sha256: str | None = None) -> dict:
    try:
        import certifi
    except ModuleNotFoundError:
        context = ssl.create_default_context()
    else:
        context = ssl.create_default_context(cafile=certifi.where())
    request = Request(url, headers={"User-Agent": "vibe-dft-skills/siesta-source-check/2.0"})
    try:
        with urlopen(request, timeout=20, context=context) as response:
            body = response.read()
            final_url = response.geturl()
            host = (urlparse(final_url).hostname or "").casefold()
            if host not in ALLOWED_HOSTS:
                raise ValueError("official source redirected outside approved SIESTA domains")
            observed = hashlib.sha256(body).hexdigest()
            if expected_sha256 is None:
                status = "navigation_only"
            else:
                status = (
                    "verified"
                    if observed == expected_sha256
                    else "hash_mismatch"
                )
            return {
                "status": status,
                "http_status": getattr(response, "status", 200),
                "final_url": final_url,
                "content_sha256": observed,
                "expected_sha256": expected_sha256,
                "bytes": len(body),
                "retrieved_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            }
    except Exception as exc:
        return {"status": "unresolved", "error_type": type(exc).__name__}


def parameter_live_status(record: dict, index: dict) -> dict:
    source = next(
        (
            item
            for item in index["source_files"]
            if item["path"] == record["source_file"]
        ),
        None,
    )
    expected_sha256 = record.get("source_sha256")
    if expected_sha256 is None and source is not None:
        expected_sha256 = source.get("sha256")
    if not isinstance(expected_sha256, str) or not re.fullmatch(
        r"[a-f0-9]{64}",
        expected_sha256,
    ):
        return {"status": "unresolved", "error_type": "SourceHashMissing"}
    encoded_path = "/".join(
        quote(part)
        for part in record["source_file"].split("/")
    )
    url = f"https://gitlab.com/siesta-project/siesta/-/raw/{index['source_commit']}/{encoded_path}"
    return verified_fetch(url, expected_sha256)


def resolve(terms: list[str], live_check: bool = False) -> tuple[dict, int]:
    registry, index, supplements = load_contracts()
    topic_index: dict[str, dict] = {}
    for source in registry["sources"]:
        for label in [source["key"], *source.get("aliases", [])]:
            topic_index[normalize(label)] = source
    manual_entries = index["entries"]
    supplement_entries = [record for record in supplements["records"] if record.get("kind") == "fdf-source-definition"]
    ambiguous = set(index.get("ambiguous_lookup_keys", []))
    matches: list[dict] = []
    unknown: list[str] = []
    unresolved: list[str] = []
    seen: set[tuple[str, str]] = set()
    for term in terms:
        key = normalize(term)
        parameter_matches = [record for record in manual_entries if pattern_matches(term, record["label"])]
        parameter_matches.extend(record for record in supplement_entries if pattern_matches(term, record["label"]))
        if parameter_matches:
            if key in ambiguous or len({(item["source_file"], item["source_line"]) for item in parameter_matches}) > 1:
                unresolved.append(term)
                continue
            record = parameter_matches[0]
            identity = ("parameter", record["label"])
            if identity in seen:
                continue
            seen.add(identity)
            item = {
                "kind": "parameter",
                "query": term,
                "label": record["label"],
                "value_type": record.get("value_type"),
                "documented_default_tex": record.get("documented_default_tex", record.get("observed_default")),
                "evidence_class": "official-manual" if record in manual_entries else "released-source-supplement",
                "source_file": record["source_file"],
                "source_line": record["source_line"],
                "source_url": record["source_url"],
                "documentation_line": index["documentation_line"],
                "code_version": index["code_version"],
                "source_commit": index["source_commit"],
                "cache_status": "pinned_local_index",
            }
            if live_check:
                item["live_check"] = parameter_live_status(record, index)
            matches.append(item)
            continue
        source = topic_index.get(key)
        if source is None:
            unknown.append(term)
            continue
        identity = ("topic", source["key"])
        if identity in seen:
            continue
        seen.add(identity)
        item = {
            "kind": "topic",
            "key": source["key"],
            "url": source["url"],
            "scope": source["scope"],
            "documentation_line": registry["supported_documentation_line_at_retrieval"],
            "registry_retrieved_utc": registry["retrieved_utc"],
            "cache_status": "routing_registry_only",
        }
        if live_check:
            item["live_check"] = verified_fetch(source["url"])
        matches.append(item)
    live_unresolved = live_check and any(item.get("live_check", {}).get("status") != "verified" for item in matches)
    if unknown or unresolved or not matches or live_unresolved:
        decision, status = "block", 2
    elif live_check:
        decision, status = "pass", 0
    else:
        decision, status = "cached_only", 3
    return {
        "schema_version": "2.0",
        "decision": decision,
        "matches": matches,
        "unknown_terms": unknown,
        "ambiguous_or_unresolved_terms": unresolved,
        "limitations": [
            "Offline resolution proves only that a pinned local index/registry record exists; exit 3 is intentionally non-passing.",
            "A successful topic URL fetch without an exact expected hash or central attestation proves navigation availability only and cannot raise the claim ceiling.",
            "A parameter default documents software behavior and is not a scientific recommendation.",
            "Read the surrounding official source and match the executable version before a version-sensitive claim.",
        ],
    }, status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("terms", nargs="+")
    parser.add_argument("--live-check", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        result, status = resolve(args.terms, live_check=args.live_check)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"decision": "block", "error_type": type(exc).__name__, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
