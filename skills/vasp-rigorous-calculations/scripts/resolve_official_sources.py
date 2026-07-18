#!/usr/bin/env python3
"""Resolve exact VASP tags/topics to provenance-bearing pages in the local official mirror."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = SKILL_ROOT / "references" / "official-wiki" / "manifest.json"


def normalized_keys(title: str) -> set[str]:
    value = " ".join(title.strip().split()).casefold()
    keys = {value}
    if value.startswith("category:"):
        keys.add(value.removeprefix("category:"))
    return keys


def load_index(manifest_path: Path = DEFAULT_MANIFEST) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = manifest.get("pages")
    if not isinstance(pages, list):
        raise ValueError("official mirror manifest has no pages array")
    index: dict[str, dict[str, Any]] = {}
    for record in pages:
        if not isinstance(record, dict) or not isinstance(record.get("title"), str):
            raise ValueError("official mirror manifest contains an invalid page record")
        for key in normalized_keys(record["title"]):
            if key in index and index[key].get("pageid") != record.get("pageid"):
                raise ValueError(f"ambiguous normalized official title: {key}")
            index[key] = record
    return manifest, index


def resolve(queries: list[str], manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest, index = load_index(manifest_path)
    resolved: list[dict[str, Any]] = []
    missing: list[str] = []
    corrupt: list[str] = []
    skill_root = manifest_path.resolve().parents[2]
    for query in queries:
        key = " ".join(query.strip().split()).casefold()
        record = index.get(key)
        if record is None:
            missing.append(query)
            continue
        local_path = skill_root / record["markdown_path"]
        try:
            digest = hashlib.sha256(local_path.read_bytes()).hexdigest()
        except OSError:
            corrupt.append(query)
            continue
        if digest != record.get("markdown_sha256"):
            corrupt.append(query)
            continue
        resolved.append(
            {
                "query": query,
                "title": record["title"],
                "url": record["url"],
                "revision": record["revid"],
                "retrieved_utc": manifest.get("retrieved_utc"),
                "local_path": record["markdown_path"],
                "markdown_sha256": record["markdown_sha256"],
            }
        )
    return {
        "status": "pass" if not (missing or corrupt) else "blocked_local_official_source",
        "mirror_scope": manifest.get("scope"),
        "mirror_retrieved_utc": manifest.get("retrieved_utc"),
        "resolved": resolved,
        "missing": missing,
        "corrupt": corrupt,
        "rule": "A missing local page does not prove the live official Wiki is silent; verify the live official page or report the claim unresolved.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queries", nargs="+", help="Exact VASP tag or official page title")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        result = resolve(args.queries, args.manifest)
    except OSError:
        print(json.dumps({"status": "error", "error": "local official mirror cannot be read"}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
