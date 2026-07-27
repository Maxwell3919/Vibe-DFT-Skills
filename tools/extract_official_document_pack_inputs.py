#!/usr/bin/env python3
"""Extract compact metadata-only QE/VASP pack inputs from legacy mirrors.

The generated catalogs deliberately use ``source-pack-*`` names rather than
the legacy ``official-*`` namespace.  They contain identities and slice
metadata only, never official body text, so active-only distributions can
rebuild and validate packs after legacy mirrors are excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any, Sequence
import urllib.parse

import strict_json


ROOT = Path(__file__).resolve().parents[1]
TARGET_NAME = "source-pack-input-catalog.json"
MAX_BYTES = 64 * 1024 * 1024


class ExtractionError(ValueError):
    """Fail-closed metadata extraction error."""


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read(path: Path, label: str) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise ExtractionError(
            f"{label}: input is unavailable ({exc.__class__.__name__})"
        ) from None
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or before.st_nlink != 1
    ):
        raise ExtractionError(
            f"{label}: input must be one regular, non-symlink, non-hard-linked file"
        )
    try:
        raw = strict_json.read_bytes_bounded(
            path,
            label,
            max_bytes=MAX_BYTES,
        )
    except strict_json.StrictJSONError as exc:
        raise ExtractionError(str(exc)) from None
    try:
        after = path.lstat()
    except OSError as exc:
        raise ExtractionError(
            f"{label}: input changed while being read ({exc.__class__.__name__})"
        ) from None
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ExtractionError(f"{label}: input changed while being read")
    return raw


def _object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = _read(path, label)
    try:
        return (
            strict_json.loads_object(raw, label, max_bytes=MAX_BYTES),
            raw,
        )
    except strict_json.StrictJSONError as exc:
        raise ExtractionError(str(exc)) from None


def _contained_file(root: Path, relative: str, label: str) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
    ):
        raise ExtractionError(f"{label}: unsafe relative path")
    candidate = root
    for part in Path(relative).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ExtractionError(f"{label}: symlink path component")
    try:
        resolved_root = root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, ValueError):
        raise ExtractionError(f"{label}: path escapes or is missing") from None
    if not resolved.is_file():
        raise ExtractionError(f"{label}: path is not a regular file")
    return resolved


def _load_qe_guard(root: Path) -> Any:
    path = (
        root
        / "skills"
        / "qe-rigorous-calculations"
        / "scripts"
        / "qe_guard.py"
    )
    specification = importlib.util.spec_from_file_location(
        "_source_pack_qe_guard",
        path,
    )
    if specification is None or specification.loader is None:
        raise ExtractionError("QE guard module cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def qe_catalog(root: Path) -> tuple[Path, bytes]:
    skill = root / "skills" / "qe-rigorous-calculations"
    manifest_path = (
        skill / "references" / "manual-cache-receipts" / "manifest.json"
    )
    manifest, manifest_raw = _object(manifest_path, "QE legacy manifest")
    expected_root = {
        "source_root",
        "generated_utc",
        "input_manuals",
        "user_guides",
        "release_notes",
        "pdf_manuals",
        "retrieved_utc",
        "oldest_source_retrieved_utc",
        "latest_source_retrieved_utc",
        "retrieval_mode",
        "source_cache",
    }
    if set(manifest) != expected_root or not isinstance(
        manifest["input_manuals"], list
    ):
        raise ExtractionError("QE legacy manifest root is not exact")
    manuals: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for manual in manifest["input_manuals"]:
        expected_manual = {
            "name",
            "source_format",
            "program",
            "version",
            "url",
            "last_modified",
            "retrieved_utc",
            "sha256",
            "raw_bytes",
            "raw_file",
            "index_file",
            "sections",
        }
        if not isinstance(manual, dict) or set(manual) != expected_manual:
            raise ExtractionError("QE manual entry is not exact")
        name = manual["name"]
        if name in seen_names:
            raise ExtractionError(f"QE duplicate manual {name!r}")
        seen_names.add(name)
        if (
            not isinstance(manual["raw_bytes"], int)
            or isinstance(manual["raw_bytes"], bool)
            or manual["raw_bytes"] <= 0
        ):
            raise ExtractionError(f"QE raw manual {name}: invalid byte receipt")
        sections: list[dict[str, Any]] = []
        seen_sections: set[str] = set()
        for order, section in enumerate(manual["sections"]):
            if (
                not isinstance(section, dict)
                or set(section)
                != {
                    "order",
                    "id",
                    "title",
                    "file",
                    "sha256",
                    "bytes",
                    "wrapper_sha256",
                    "wrapper_bytes",
                }
                or section["order"] != order
                or section["id"] in seen_sections
            ):
                raise ExtractionError(f"QE {name}: invalid section structure")
            seen_sections.add(section["id"])
            if (
                not isinstance(section["wrapper_sha256"], str)
                or re.fullmatch(r"[a-f0-9]{64}", section["wrapper_sha256"])
                is None
                or not isinstance(section["wrapper_bytes"], int)
                or isinstance(section["wrapper_bytes"], bool)
                or section["wrapper_bytes"] <= 0
            ):
                raise ExtractionError(
                    f"QE {name} section {section['id']}: invalid wrapper receipt"
                )
            sections.append(
                {
                    "order": order,
                    "section_id": section["id"],
                    "title": section["title"],
                    "selected_sha256": section["sha256"],
                    "selected_bytes": section["bytes"],
                    "payload_hash_basis": (
                        "utf-8 bytes of the fenced text payload after removing "
                        "the single wrapper separator newline"
                    ),
                    "wrapper_sha256": section["wrapper_sha256"],
                    "wrapper_bytes": section["wrapper_bytes"],
                }
            )
        manuals.append(
            {
                "name": name,
                "version": manual["version"],
                "url": manual["url"],
                "retrieved_utc": manual["retrieved_utc"],
                "raw_sha256": manual["sha256"],
                "raw_bytes": manual["raw_bytes"],
                "sections": sections,
            }
        )
    output = {
        "schema_version": "1.0",
        "contract_name": "qe-source-pack-input",
        "catalog_type": "qe-input-manifest-metadata-v1",
        "skill_id": "qe-rigorous-calculations",
        "source_root": manifest["source_root"],
        "retrieved_utc": manifest["retrieved_utc"],
        "legacy_manifest_sha256": _sha(manifest_raw),
        "manuals": manuals,
        "limitations": [
            "This catalog stores hashes, byte counts, selectors, titles, URLs, and versions only; official body text is not embedded.",
            "User guides, release notes, PDF manuals, portal navigation, links, images, and assets are outside this bounded input-manual catalog.",
        ],
    }
    return skill / "references" / TARGET_NAME, _canonical(output)


def vasp_catalog(root: Path) -> tuple[Path, bytes]:
    skill = root / "skills" / "vasp-rigorous-calculations"
    manifest_path = (
        skill
        / "references"
        / "manual-cache-receipts"
        / "manifest.json"
    )
    manifest, manifest_raw = _object(manifest_path, "VASP legacy manifest")
    expected_root = {
        "api_url",
        "categories",
        "core_pages",
        "html2md_identity",
        "internal_link_count",
        "official_fragment_compatibility_alias_count",
        "official_root",
        "page_count",
        "pages",
        "public_body_complete",
        "requested_title_count",
        "resolved_requested_title_count",
        "retrieved_utc",
        "scope",
        "unavailable_title_count",
        "unavailable_titles",
        "upstream_universe",
        "upstream_universe_complete",
    }
    if (
        set(manifest) != expected_root
        or not isinstance(manifest["pages"], list)
        or manifest["page_count"] != len(manifest["pages"])
        or manifest["scope"] != "all-main-namespace"
        or manifest["upstream_universe_complete"] is not True
        or manifest["public_body_complete"] is not True
    ):
        raise ExtractionError("VASP legacy manifest is not a complete main-namespace set")
    core_titles = {
        title for title in manifest["core_pages"] if isinstance(title, str)
    }
    selected_by_pageid: dict[int, dict[str, Any]] = {}
    for core_title in core_titles:
        exact = [
            page
            for page in manifest["pages"]
            if isinstance(page, dict) and core_title in page.get("aliases", [])
        ]
        candidates = exact or [
            page
            for page in manifest["pages"]
            if isinstance(page, dict)
            and any(
                isinstance(alias, str)
                and alias.casefold() == core_title.casefold()
                for alias in page.get("aliases", [])
            )
        ]
        if len(candidates) != 1:
            raise ExtractionError(
                f"VASP curated title is missing or ambiguous: {core_title}"
            )
        selected_by_pageid[candidates[0]["pageid"]] = candidates[0]
    selected_pages = list(selected_by_pageid.values())
    if len(core_titles) != 81 or len(selected_pages) != 81:
        raise ExtractionError(
            "VASP complete manifest does not resolve the exact 81-page curated subset"
        )
    pages: list[dict[str, Any]] = []
    seen_pageids: set[int] = set()
    for page in sorted(selected_pages, key=lambda item: item["pageid"]):
        if (
            not isinstance(page, dict)
            or set(page)
            != {
                "aliases",
                "conversion_quality",
                "markdown_path",
                "markdown_sha256",
                "pageid",
                "raw_bytes",
                "raw_path",
                "raw_sha256",
                "revid",
                "title",
                "url",
                "wikitext_bytes",
                "wikitext_sha256",
            }
            or page["pageid"] in seen_pageids
        ):
            raise ExtractionError("VASP page entry is not exact")
        seen_pageids.add(page["pageid"])
        if (
            not isinstance(page["raw_bytes"], int)
            or isinstance(page["raw_bytes"], bool)
            or page["raw_bytes"] <= 0
            or not isinstance(page["wikitext_bytes"], int)
            or isinstance(page["wikitext_bytes"], bool)
            or page["wikitext_bytes"] < 0
        ):
            raise ExtractionError(
                f"VASP page {page['pageid']}: invalid byte receipt"
            )
        api_request_url = manifest["api_url"] + "?" + urllib.parse.urlencode(
            [
                ("action", "parse"),
                ("oldid", str(page["revid"])),
                ("prop", "text|wikitext|revid|displaytitle"),
                ("format", "json"),
                ("formatversion", "2"),
            ]
        )
        pages.append(
            {
                "pageid": page["pageid"],
                "revid": page["revid"],
                "title": page["title"],
                "url": page["url"],
                "api_request_url": api_request_url,
                "raw_json_sha256": page["raw_sha256"],
                "raw_json_bytes": page["raw_bytes"],
                "wikitext_sha256": page["wikitext_sha256"],
                "wikitext_bytes": page["wikitext_bytes"],
            }
        )
    output = {
        "schema_version": "1.0",
        "contract_name": "vasp-source-pack-input",
        "catalog_type": "vasp-wiki-page-metadata-v1",
        "skill_id": "vasp-rigorous-calculations",
        "official_root": manifest["official_root"],
        "api_url": manifest["api_url"],
        "retrieved_utc": manifest["retrieved_utc"],
        "legacy_manifest_sha256": _sha(manifest_raw),
        "pages": pages,
        "limitations": [
            "This catalog stores pageid/revid plus separate raw-JSON and wikitext identities only; official body text is not embedded.",
            "The 81 pages are the curated semantic source-pack subset; full public main-namespace body and link closure is recorded separately by the revision-bound legacy manifest.",
            "The public VASP Portal, protected downloads, images, and third-party assets remain outside the Wiki main-namespace closure.",
        ],
    }
    return skill / "references" / TARGET_NAME, _canonical(output)


def _atomic_write(path: Path, raw: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".source-pack-input-",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            os.fchmod(handle.fileno(), 0o644)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        parent_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    finally:
        if temporary.exists():
            temporary.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true")
    selection.add_argument(
        "--skill",
        action="append",
        choices=("qe-rigorous-calculations", "vasp-rigorous-calculations"),
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    selected = (
        ("qe-rigorous-calculations", "vasp-rigorous-calculations")
        if args.all
        else tuple(args.skill)
    )
    extractors = {
        "qe-rigorous-calculations": qe_catalog,
        "vasp-rigorous-calculations": vasp_catalog,
    }
    stale: list[str] = []
    try:
        prepared = [
            extractors[skill_id](args.root.resolve())
            for skill_id in selected
        ]
        for path, raw in prepared:
            current = _read(path, path.name) if path.is_file() else None
            if current == raw:
                continue
            stale.append(path.relative_to(args.root.resolve()).as_posix())
            if not args.check:
                _atomic_write(path, raw)
    except ExtractionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.check and stale:
        print("ERROR: stale compact pack inputs: " + ", ".join(stale), file=sys.stderr)
        return 2
    print(f"PASS: {'checked' if args.check else 'wrote'} {len(selected)} compact metadata catalog(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
