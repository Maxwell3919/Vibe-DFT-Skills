#!/usr/bin/env python3
"""Resolve VASP topics without promoting unverified local metadata to a pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = (
    Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    / "vibe-dft-skills"
    / "official-provider-mirrors"
    / "vasp-rigorous-calculations"
    / "provider-root"
    / "references"
    / "official-wiki"
    / "manifest.json"
)
DEFAULT_CATALOG = SKILL_ROOT / "references" / "source-pack-input-catalog.json"
DEFAULT_SEED = SKILL_ROOT / "references" / "source-pack-seed.json"

LOCAL_VERIFIED_STATUS = "local_integrity_verified"
METADATA_ONLY_STATUS = "metadata_resolved_unverified"
BLOCKED_STATUS = "blocked_local_official_source"


def normalized_keys(title: str) -> set[str]:
    value = " ".join(title.strip().split()).casefold()
    keys = {value}
    if value.startswith("category:"):
        keys.add(value.removeprefix("category:"))
    return keys


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_index(
    manifest_path: Path = DEFAULT_MANIFEST,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], str]:
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
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
    return manifest, index, sha256_bytes(manifest_raw)


def anchor_manifest(
    manifest_sha256: str,
    catalog_path: Path | None,
    seed_path: Path | None,
) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    if catalog_path is None or seed_path is None:
        return (
            {
                "anchor_status": "unverified",
                "anchor_reason": "anchor_not_configured",
                "catalog_sha256": None,
                "expected_manifest_sha256": None,
            },
            {},
        )
    try:
        catalog_raw = catalog_path.read_bytes()
        catalog = json.loads(catalog_raw)
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return (
            {
                "anchor_status": "blocked",
                "anchor_reason": "anchor_unreadable_or_invalid",
                "catalog_sha256": None,
                "expected_manifest_sha256": None,
            },
            {},
        )
    catalog_sha256 = sha256_bytes(catalog_raw)
    providers = seed.get("providers")
    matching = (
        [
            item
            for item in providers
            if isinstance(item, dict)
            and item.get("adapter_id") == "vasp-wiki-manifest-v1"
        ]
        if isinstance(providers, list)
        else []
    )
    source_ref = matching[0].get("source_ref") if len(matching) == 1 else None
    if (
        catalog.get("contract_name") != "vasp-source-pack-input"
        or catalog.get("catalog_type") != "vasp-wiki-page-metadata-v1"
        or not isinstance(source_ref, dict)
        or source_ref.get("sha256") != catalog_sha256
    ):
        return (
            {
                "anchor_status": "blocked",
                "anchor_reason": "catalog_seed_binding_invalid",
                "catalog_sha256": catalog_sha256,
                "expected_manifest_sha256": catalog.get(
                    "legacy_manifest_sha256"
                ),
            },
            {},
        )
    expected_manifest_sha256 = catalog.get("legacy_manifest_sha256")
    if expected_manifest_sha256 != manifest_sha256:
        return (
            {
                "anchor_status": "blocked",
                "anchor_reason": "manifest_hash_mismatch",
                "catalog_sha256": catalog_sha256,
                "expected_manifest_sha256": expected_manifest_sha256,
            },
            {},
        )
    pages = catalog.get("pages")
    if not isinstance(pages, list):
        return (
            {
                "anchor_status": "blocked",
                "anchor_reason": "catalog_pages_invalid",
                "catalog_sha256": catalog_sha256,
                "expected_manifest_sha256": expected_manifest_sha256,
            },
            {},
        )
    catalog_pages: dict[int, dict[str, Any]] = {}
    for page in pages:
        pageid = page.get("pageid") if isinstance(page, dict) else None
        if not isinstance(pageid, int) or pageid in catalog_pages:
            return (
                {
                    "anchor_status": "blocked",
                    "anchor_reason": "catalog_page_identity_invalid",
                    "catalog_sha256": catalog_sha256,
                    "expected_manifest_sha256": expected_manifest_sha256,
                },
                {},
            )
        catalog_pages[pageid] = page
    return (
        {
            "anchor_status": "verified",
            "anchor_reason": "seed_catalog_manifest_hash_chain",
            "catalog_sha256": catalog_sha256,
            "expected_manifest_sha256": expected_manifest_sha256,
        },
        catalog_pages,
    )


def read_bounded_file(skill_root: Path, relative_value: Any) -> bytes:
    if not isinstance(relative_value, str):
        raise OSError("manifest artifact path is not a string")
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise OSError("manifest artifact path is outside the Skill")
    root = skill_root.resolve()
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise OSError("manifest artifact is unavailable")
    return candidate.read_bytes()


def anchored_page_matches(
    record: dict[str, Any],
    catalog_record: dict[str, Any] | None,
    raw_payload: bytes,
) -> tuple[bool, str | None]:
    if catalog_record is None:
        return False, None
    if any(
        record.get(key) != catalog_record.get(key)
        for key in ("pageid", "revid", "title", "url")
    ):
        return False, None
    raw_sha256 = sha256_bytes(raw_payload)
    if (
        raw_sha256 != record.get("raw_sha256")
        or raw_sha256 != catalog_record.get("raw_json_sha256")
        or len(raw_payload) != catalog_record.get("raw_json_bytes")
    ):
        return False, None
    try:
        raw_record = json.loads(raw_payload)
    except json.JSONDecodeError:
        return False, None
    if any(
        raw_record.get(key) != record.get(key)
        for key in ("pageid", "revid", "title")
    ):
        return False, None
    wikitext = raw_record.get("wikitext")
    if not isinstance(wikitext, str):
        return False, None
    wikitext_payload = wikitext.encode("utf-8")
    wikitext_sha256 = sha256_bytes(wikitext_payload)
    if (
        wikitext_sha256 != catalog_record.get("wikitext_sha256")
        or len(wikitext_payload) != catalog_record.get("wikitext_bytes")
    ):
        return False, None
    return True, wikitext_sha256


def resolve(
    queries: list[str],
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    catalog_path: Path | None = DEFAULT_CATALOG,
    seed_path: Path | None = DEFAULT_SEED,
) -> dict[str, Any]:
    try:
        manifest, index, manifest_sha256 = load_index(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {
            "status": BLOCKED_STATUS,
            "maximum_conclusion": "official_source_claim_blocked",
            "mirror_scope": None,
            "mirror_retrieved_utc": None,
            "resolved": [],
            "missing": list(queries),
            "corrupt": [],
            "integrity": {
                "anchor_status": "blocked",
                "anchor_reason": "mirror_manifest_unavailable_or_invalid",
                "catalog_sha256": None,
                "expected_manifest_sha256": None,
                "manifest_sha256": None,
                "body_hash_status": "not_evaluated",
                "platform_attestation_status": "not_evaluated",
            },
            "rule": (
                "Local integrity verifies only the exact pinned provider artifacts. "
                "It does not prove freshness or platform-attested external resolution. "
                "Missing, corrupt, unpinned, or unattested evidence never authorizes a "
                "remembered software-behavior claim."
            ),
        }
    anchor, catalog_pages = anchor_manifest(
        manifest_sha256,
        catalog_path,
        seed_path,
    )
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
        try:
            markdown_payload = read_bounded_file(
                skill_root,
                record.get("markdown_path"),
            )
        except OSError:
            corrupt.append(query)
            continue
        markdown_sha256 = sha256_bytes(markdown_payload)
        if markdown_sha256 != record.get("markdown_sha256"):
            corrupt.append(query)
            continue
        raw_sha256: str | None = None
        wikitext_sha256: str | None = None
        if anchor["anchor_status"] == "verified":
            try:
                raw_payload = read_bounded_file(
                    skill_root,
                    record.get("raw_path"),
                )
            except OSError:
                corrupt.append(query)
                continue
            anchored, wikitext_sha256 = anchored_page_matches(
                record,
                catalog_pages.get(record.get("pageid")),
                raw_payload,
            )
            if not anchored:
                corrupt.append(query)
                continue
            raw_sha256 = sha256_bytes(raw_payload)
        resolved.append(
            {
                "query": query,
                "title": record["title"],
                "url": record["url"],
                "revision": record["revid"],
                "retrieved_utc": manifest.get("retrieved_utc"),
                "local_path": record["markdown_path"],
                "markdown_sha256": markdown_sha256,
                "raw_json_sha256": raw_sha256,
                "wikitext_sha256": wikitext_sha256,
            }
        )
    if missing or corrupt or anchor["anchor_status"] == "blocked":
        status = BLOCKED_STATUS
        maximum_conclusion = "official_source_claim_blocked"
    elif anchor["anchor_status"] == "verified":
        status = LOCAL_VERIFIED_STATUS
        maximum_conclusion = "exact_local_mirror_integrity_only"
    else:
        status = METADATA_ONLY_STATUS
        maximum_conclusion = "metadata_resolution_only"
    return {
        "status": status,
        "maximum_conclusion": maximum_conclusion,
        "mirror_scope": manifest.get("scope"),
        "mirror_retrieved_utc": manifest.get("retrieved_utc"),
        "resolved": resolved,
        "missing": missing,
        "corrupt": corrupt,
        "integrity": {
            **anchor,
            "manifest_sha256": manifest_sha256,
            "body_hash_status": (
                "mismatch"
                if corrupt
                else "verified"
                if resolved
                else "not_evaluated"
            ),
            "platform_attestation_status": "not_evaluated",
        },
        "rule": (
            "Local integrity verifies only the exact pinned provider artifacts. "
            "It does not prove freshness or "
            "platform-attested external resolution. Missing, corrupt, "
            "unpinned, or unattested evidence never authorizes a remembered "
            "software-behavior claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queries", nargs="+", help="Exact VASP tag or official page title")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        result = resolve(
            args.queries,
            args.manifest,
            catalog_path=args.catalog,
            seed_path=args.seed,
        )
    except OSError:
        print(json.dumps({"status": "error", "error": "local official mirror cannot be read"}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["status"] == LOCAL_VERIFIED_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
