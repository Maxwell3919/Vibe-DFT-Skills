#!/usr/bin/env python3
"""Resolve CP2K topics to exact versioned official-manual URLs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import sys
import time
from typing import Any, Callable
import urllib.error
import urllib.request


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = SKILL_ROOT / "references" / "official-source-registry.json"
DEFAULT_SNAPSHOT = SKILL_ROOT / "references" / "official-manual"
VERSION = re.compile(r"^[0-9]{1,4}\.[0-9]{1,2}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
POSITIVE_VERIFICATION_STATES = {"cached_exact", "live_matches_cached"}
VERIFICATION_STATES = {
    *POSITIVE_VERIFICATION_STATES,
    "live_changed_from_cached",
    "live_unavailable_cached_exact",
    "url_only",
    "unresolved",
}


def normalize(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", "-").split())


def load_registry(path: Path = DEFAULT_REGISTRY) -> tuple[dict[str, Any], dict[str, str]]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    if registry.get("schema_version") != "1.0" or not isinstance(registry.get("topics"), dict):
        raise ValueError("official-source registry has an unsupported structure")
    aliases: dict[str, str] = {}
    for topic, record in registry["topics"].items():
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ValueError(f"invalid source-registry record: {topic}")
        path_since = record.get("path_since")
        if path_since is not None and (
            not isinstance(path_since, dict)
            or not VERSION.fullmatch(str(path_since.get("version", "")))
            or not isinstance(path_since.get("path"), str)
        ):
            raise ValueError(f"invalid version-specific path in source-registry record: {topic}")
        keys = [topic, *record.get("aliases", [])]
        for key in keys:
            normalized = normalize(key)
            if normalized in aliases and aliases[normalized] != topic:
                raise ValueError(f"ambiguous official-source alias: {key}")
            aliases[normalized] = topic
    return registry, aliases


def manual_branch(version: str) -> str:
    value = version.strip().casefold()
    if value == "trunk":
        return "trunk"
    if not VERSION.fullmatch(value):
        raise ValueError("version must be an explicit CP2K release such as 2026.2, or trunk")
    return f"cp2k-{value.replace('.', '_')}-branch"


def source_path(record: dict[str, Any], version: str) -> str:
    path_since = record.get("path_since")
    if not isinstance(path_since, dict):
        return record["path"]
    if version.strip().casefold() == "trunk":
        return path_since["path"]
    current = tuple(int(part) for part in version.split("."))
    threshold = tuple(int(part) for part in path_since["version"].split("."))
    return path_since["path"] if current >= threshold else record["path"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an RFC 3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{label} must use an explicit UTC offset")
    return value


def live_receipt(value: Any, expected_url: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("live retrieval receipt must be an object")
    if value.get("http_status") != 200:
        raise ValueError("live retrieval did not return HTTP 200")
    if value.get("final_url") != expected_url:
        raise ValueError("live retrieval final URL differs from the registered official URL")
    content_sha256 = value.get("content_sha256")
    if not isinstance(content_sha256, str) or not SHA256.fullmatch(content_sha256):
        raise ValueError("live retrieval content hash is invalid")
    byte_count = value.get("bytes")
    if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count <= 0:
        raise ValueError("live retrieval byte count is invalid")
    return {
        "http_status": 200,
        "final_url": expected_url,
        "content_sha256": content_sha256,
        "bytes": byte_count,
        "retrieved_utc": utc_timestamp(value.get("retrieved_utc"), "live retrieval time"),
    }


def cached_source(
    topic: str,
    version: str,
    *,
    expected_url: str,
    registry_path: Path,
    snapshot_dir: Path,
) -> dict[str, Any] | None:
    try:
        manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        manifest.get("schema_version") != "1.0"
        or manifest.get("manual_version") != version
        or manifest.get("manual_branch") != manual_branch(version)
        or manifest.get("registry_sha256") != sha256_file(registry_path)
    ):
        return None
    record = manifest.get("pages", {}).get(topic)
    if (
        not isinstance(record, dict)
        or record.get("path") != f"{topic}.md"
        or record.get("source_url") != expected_url
        or not isinstance(record.get("raw_sha256"), str)
        or not SHA256.fullmatch(record["raw_sha256"])
        or not isinstance(record.get("snapshot_sha256"), str)
        or not SHA256.fullmatch(record["snapshot_sha256"])
        or isinstance(record.get("raw_bytes"), bool)
        or not isinstance(record.get("raw_bytes"), int)
        or record["raw_bytes"] <= 0
        or isinstance(record.get("snapshot_bytes"), bool)
        or not isinstance(record.get("snapshot_bytes"), int)
        or record["snapshot_bytes"] <= 0
    ):
        return None
    path = snapshot_dir / record["path"]
    try:
        snapshot_sha256 = sha256_file(path)
        snapshot_bytes = path.stat().st_size
        cached_retrieved_utc = utc_timestamp(manifest.get("retrieved_utc"), "cached retrieval time")
    except OSError:
        return None
    except ValueError:
        return None
    if snapshot_sha256 != record["snapshot_sha256"] or snapshot_bytes != record["snapshot_bytes"]:
        return None
    return {
        "verification": "cached_exact",
        "local_reference": f"references/official-manual/{record['path']}",
        "source_content_sha256": record["raw_sha256"],
        "source_content_bytes": record["raw_bytes"],
        "snapshot_sha256": snapshot_sha256,
        "snapshot_bytes": snapshot_bytes,
        "cached_retrieved_utc": cached_retrieved_utc,
    }


def fetch_url(url: str, timeout: float = 20.0, attempts: int = 3) -> dict[str, Any]:
    if attempts < 1:
        raise ValueError("attempts must be positive")
    try:
        import certifi
    except ModuleNotFoundError:
        context = ssl.create_default_context()
    else:
        context = ssl.create_default_context(cafile=certifi.where())
    request = urllib.request.Request(url, headers={"User-Agent": "vibe-dft-skills-cp2k-source-check/1.0"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
                body = response.read()
                final_url = response.geturl()
                status = getattr(response, "status", 200)
            break
        except urllib.error.HTTPError as exc:
            transient = exc.code in {408, 425, 429} or exc.code >= 500
            if not transient or attempt + 1 == attempts:
                raise
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, ssl.SSLCertVerificationError) or attempt + 1 == attempts:
                raise
        time.sleep(0.25 * (2**attempt))
    return live_receipt({
        "http_status": status,
        "final_url": final_url,
        "content_sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "retrieved_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }, url)


def resolve(
    queries: list[str],
    version: str,
    *,
    live_check: bool,
    registry_path: Path = DEFAULT_REGISTRY,
    snapshot_dir: Path = DEFAULT_SNAPSHOT,
    fetcher: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if fetcher is None:
        fetcher = fetch_url
    registry, aliases = load_registry(registry_path)
    branch = manual_branch(version)
    root = registry["manual_root"].rstrip("/")
    resolved: list[dict[str, Any]] = []
    missing: list[str] = []
    failed: list[dict[str, str]] = []
    for query in queries:
        topic = aliases.get(normalize(query))
        if topic is None:
            missing.append(query)
            continue
        record = registry["topics"][topic]
        url = f"{root}/{branch}/{source_path(record, version)}"
        item: dict[str, Any] = {
            "query": query,
            "topic": topic,
            "manual_version": version,
            "manual_branch": branch,
            "url": url,
            "verification": "unresolved" if live_check else "url_only",
        }
        cached = cached_source(
            topic,
            version,
            expected_url=url,
            registry_path=registry_path,
            snapshot_dir=snapshot_dir,
        )
        if live_check:
            try:
                live = live_receipt(fetcher(url), url)
            except (OSError, ValueError, urllib.error.URLError) as exc:
                failed.append({"query": query, "reason": type(exc).__name__})
                if cached is not None:
                    item.update(cached)
                    item["verification"] = "live_unavailable_cached_exact"
            else:
                item.update(live)
                if cached is None:
                    item["verification"] = "unresolved"
                    failed.append({"query": query, "reason": "MissingCachedBaseline"})
                else:
                    item.update(cached)
                    item.update(live)
                    if live["content_sha256"] == cached["source_content_sha256"]:
                        item["verification"] = "live_matches_cached"
                    else:
                        item["verification"] = "live_changed_from_cached"
                        failed.append({"query": query, "reason": "ContentHashMismatch"})
        else:
            if cached is not None:
                item.update(cached)
        resolved.append(item)
    states = {item["verification"] for item in resolved}
    if missing or failed or not states <= VERIFICATION_STATES:
        status = "blocked_official_source"
    elif live_check and resolved and states == {"live_matches_cached"}:
        status = "pass_live_matches_cached"
    elif not live_check and resolved and states == {"cached_exact"}:
        status = "pass_cached_exact"
    else:
        status = "resolved_url_only"
    return {
        "schema_version": "1.1",
        "status": status,
        "manual_version": version,
        "manual_branch": branch,
        "resolved": resolved,
        "missing": missing,
        "failed": failed,
        "source_repository": registry["source_repository"],
        "limitations": [
            "Only cached_exact and live_matches_cached records can support a positive version-sensitive official claim.",
            "A cached-exact page supports documented behavior only as of its recorded retrieval time.",
            "A live response that changed from, cannot be matched to, or cannot reopen the cached page is fail-closed.",
            "A URL-only result supports navigation only.",
            "The trunk manual is development documentation and must not be projected backward to a stable release.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queries", nargs="+", help="Registered CP2K section, keyword alias, or topic")
    parser.add_argument("--version", required=True, help="Exact release such as 2026.2, or trunk")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live-check", action="store_true")
    mode.add_argument("--offline", action="store_true")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = resolve(
            args.queries,
            args.version,
            live_check=args.live_check,
            registry_path=args.registry,
            snapshot_dir=args.snapshot,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["status"] in {"pass_cached_exact", "pass_live_matches_cached", "resolved_url_only"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
