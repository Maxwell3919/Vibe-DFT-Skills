#!/usr/bin/env python3
"""Emit the deterministic official-document scope catalog for this Skill.

Only repository-owned metadata is read.  The extractor has no network or
native-execution path and cannot retrieve LOBSTER manuals, examples, basis
resources, binaries, parent wavefunctions, or calculation results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
SKILL_ID = "lobster-bonding-analysis"
TARGET = ROOT / "skills" / SKILL_ID / "references" / "source-pack-scope-catalog.json"

SUBJECT_SPECS = (
    {
        "subject_id": "lobster-cohp-method-definition",
        "subject_kind": "documented-claim",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/lobster-bonding-analysis/references/official-sources.yaml",
            "skills/lobster-bonding-analysis/references/official-sources-and-version-strategy.md",
        ),
        "statement": (
            "COHP and projected-COHP definitions require the provider-required "
            "ACS method-literature input and do not establish native syntax."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("lobster-acs-method-literature",),
    },
    {
        "subject_id": "lobster-framework-capability",
        "subject_kind": "capability",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/lobster-bonding-analysis/references/official-sources.yaml",
            "skills/lobster-bonding-analysis/references/official-sources-and-version-strategy.md",
        ),
        "statement": (
            "The LOBSTER projection framework requires the provider-required "
            "Wiley method-literature input and remains distinct from 5.1.1 grammar."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("lobster-wiley-method-literature",),
    },
    {
        "subject_id": "lobster-5-1-1-native-contract",
        "subject_kind": "workflow",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/lobster-bonding-analysis/SKILL.md",
            "skills/lobster-bonding-analysis/references/official-sources-and-version-strategy.md",
            "skills/lobster-bonding-analysis/references/environment-license-boundary.md",
        ),
        "statement": (
            "LOBSTER 5.1.1 argv, lobsterin grammar, completion markers, output "
            "schemas, examples, and basis resources remain blocked after review "
            "of the bounded method-literature inputs because they require an "
            "authorized manual."
        ),
        "expected_disposition": "blocked",
        "provider_input_ids": (
            "lobster-acs-method-literature",
            "lobster-wiley-method-literature",
        ),
    },
    {
        "subject_id": "lobster-5-1-1-license-boundary",
        "subject_kind": "limitation",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/lobster-bonding-analysis/references/official-sources-and-version-strategy.md",
            "skills/lobster-bonding-analysis/references/environment-license-boundary.md",
        ),
        "statement": (
            "The registered non-profit license and non-redistribution boundary "
            "is reported by a query-bearing first-party page that cannot be "
            "activated under the central query policy; external entitlement "
            "evidence remains required and bundled payloads remain prohibited."
        ),
        "expected_disposition": "blocked",
        "provider_input_ids": (
            "lobster-acs-method-literature",
            "lobster-wiley-method-literature",
        ),
    },
    {
        "subject_id": "lobster-synthetic-guard-boundary",
        "subject_kind": "limitation",
        "evidence_class": "repository-policy",
        "origin_paths": (
            "skills/lobster-bonding-analysis/SKILL.md",
            "skills/lobster-bonding-analysis/references/environment-license-boundary.md",
        ),
        "statement": (
            "Synthetic fixtures and deterministic checks cannot authenticate "
            "native LOBSTER 5.1.1 formats or chemical-bonding conclusions."
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
        "extractor_id": "lobster-document-scope-v1",
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
