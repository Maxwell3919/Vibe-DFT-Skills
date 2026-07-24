#!/usr/bin/env python3
"""Emit the deterministic official-document scope catalog for this Skill.

This extractor is offline and metadata-only.  It never connects to the
HTTP-only LASP Hub or retrieves manuals, examples, binaries, interfaces,
models, datasets, structures, trajectories, or calculation output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
SKILL_ID = "lasp-rigorous-simulations"
TARGET = ROOT / "skills" / SKILL_ID / "references" / "source-pack-scope-catalog.json"

SUBJECT_SPECS = (
    {
        "subject_id": "lasp-3-7-capability-context",
        "subject_kind": "capability",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/lasp-rigorous-simulations/references/official-sources.json",
            "skills/lasp-rigorous-simulations/references/public-capability-workflows.md",
        ),
        "statement": (
            "LASP 3.7 PES, SSW, neural-network, reaction-search, and MD "
            "capability context requires the HTTPS author-literature input."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("lasp-author-literature",),
    },
    {
        "subject_id": "lasp-3-7-3-native-contract",
        "subject_kind": "workflow",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/lasp-rigorous-simulations/SKILL.md",
            "skills/lasp-rigorous-simulations/references/official-sources.json",
            "skills/lasp-rigorous-simulations/references/environment-license-execution.md",
        ),
        "statement": (
            "Exact LASP 3.7.3 input, output, completion, restart, resource, "
            "and compatibility contracts remain blocked because HTTPS literature "
            "does not substitute for the HTTP-only Hub manual and examples."
        ),
        "expected_disposition": "blocked",
        "provider_input_ids": ("lasp-author-literature",),
    },
    {
        "subject_id": "lasp-3-7-3-license-terms",
        "subject_kind": "limitation",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/lasp-rigorous-simulations/references/official-sources.json",
            "skills/lasp-rigorous-simulations/references/environment-license-execution.md",
        ),
        "statement": (
            "Complete LASP software, manual, examples, model, interface, and "
            "redistribution terms are not established by the HTTPS literature."
        ),
        "expected_disposition": "blocked",
        "provider_input_ids": ("lasp-author-literature",),
    },
    {
        "subject_id": "lasp-offline-inventory-boundary",
        "subject_kind": "limitation",
        "evidence_class": "repository-policy",
        "origin_paths": (
            "skills/lasp-rigorous-simulations/SKILL.md",
            "skills/lasp-rigorous-simulations/references/environment-license-execution.md",
        ),
        "statement": (
            "The development guard inventories opaque artifacts and cannot "
            "execute LASP or establish a native completion or scientific claim."
        ),
        "expected_disposition": "excluded",
        "provider_input_ids": (),
    },
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_catalog() -> dict[str, object]:
    subjects: list[dict[str, object]] = []
    for spec in SUBJECT_SPECS:
        subject = {
            key: value
            for key, value in spec.items()
            if key not in {"origin_paths", "provider_input_ids"}
        }
        subject["origin_refs"] = [
            {"path": relative, "sha256": _sha256(ROOT / relative)}
            for relative in spec["origin_paths"]
        ]
        subject["provider_input_ids"] = list(spec["provider_input_ids"])
        subjects.append(subject)
    return {
        "schema_version": "1.0",
        "contract_name": "official-document-scope-catalog",
        "skill_id": SKILL_ID,
        "extractor_id": "lasp-document-scope-v1",
        "subjects": subjects,
    }


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    expected = canonical_bytes(build_catalog())
    if args.check:
        actual = TARGET.read_bytes() if TARGET.is_file() else None
        if actual != expected:
            print(f"ERROR: stale scope catalog: {TARGET}", file=sys.stderr)
            return 2
        print(f"PASS: {SKILL_ID} document scope catalog is current")
        return 0
    sys.stdout.buffer.write(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
