#!/usr/bin/env python3
"""Emit the deterministic official-document scope catalog for this Skill.

The extractor is intentionally offline.  It hashes repository-owned policy and
catalog files only; it never contacts Gaussian, discovers a binary, or reads a
licensed manual, example, basis payload, checkpoint, or calculation output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
SKILL_ID = "gaussian-rigorous-calculations"
TARGET = (
    ROOT
    / "skills"
    / SKILL_ID
    / "references"
    / "source-pack-scope-catalog.json"
)

SUBJECT_SPECS = (
    {
        "subject_id": "g16-c01-navigation",
        "subject_kind": "documented-claim",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/gaussian-rigorous-calculations/references/official-sources.md",
            "skills/gaussian-rigorous-calculations/references/feature-catalog.json",
        ),
        "statement": (
            "The public Gaussian documentation navigation boundary requires "
            "the separately bounded C.01 provider input."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("gaussian-g16-c01-public",),
    },
    {
        "subject_id": "g16-c01-user-reference",
        "subject_kind": "documented-claim",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/gaussian-rigorous-calculations/references/official-sources.md",
            "skills/gaussian-rigorous-calculations/references/feature-catalog.json",
        ),
        "statement": (
            "Public Gaussian 16 user-reference, input, keyword, and IOp pages "
            "used by this Skill require the separately bounded C.01 provider input."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("gaussian-g16-c01-public",),
    },
    {
        "subject_id": "g16-c01-keywords",
        "subject_kind": "input-keyword",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/gaussian-rigorous-calculations/SKILL.md",
            "skills/gaussian-rigorous-calculations/references/feature-catalog.json",
        ),
        "statement": (
            "The Gaussian keyword universe requires the bounded C.01 keyword "
            "index and cannot be inferred from a runtime fixture."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("gaussian-g16-c01-public",),
    },
    {
        "subject_id": "g16-c01-iops",
        "subject_kind": "parameter",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/gaussian-rigorous-calculations/references/official-sources.md",
            "skills/gaussian-rigorous-calculations/references/feature-catalog.json",
        ),
        "statement": (
            "The Gaussian internal-option overlay boundary requires the "
            "bounded C.01 IOp index."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("gaussian-g16-c01-public",),
    },
    {
        "subject_id": "g16-c01-input-grammar",
        "subject_kind": "workflow",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/gaussian-rigorous-calculations/SKILL.md",
            "skills/gaussian-rigorous-calculations/references/feature-catalog.json",
        ),
        "statement": (
            "Input-section ordering, route syntax, Link 0 vocabulary, and "
            "blank-line termination require public first-party reference evidence."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("gaussian-g16-c01-public",),
    },
    {
        "subject_id": "g16-c02-release-delta",
        "subject_kind": "documented-claim",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/gaussian-rigorous-calculations/references/official-sources.md",
            "skills/gaussian-rigorous-calculations/references/feature-catalog.json",
        ),
        "statement": (
            "Gaussian 16 Rev. C.02 release and platform statements require a "
            "C.02-specific provider input and do not re-version the C.01 reference."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("gaussian-g16-c02-delta",),
    },
    {
        "subject_id": "g16-c02-platform-profile",
        "subject_kind": "documented-claim",
        "evidence_class": "official-provider-required",
        "origin_paths": (
            "skills/gaussian-rigorous-calculations/references/official-sources.md",
            "skills/gaussian-rigorous-calculations/references/feature-catalog.json",
        ),
        "statement": (
            "Gaussian 16 Rev. C.02 platform statements require the bounded "
            "C.02 platform-list source and remain separate from C.01 syntax."
        ),
        "expected_disposition": "partial",
        "provider_input_ids": ("gaussian-g16-c02-delta",),
    },
    {
        "subject_id": "gaussian-offline-guard-boundary",
        "subject_kind": "limitation",
        "evidence_class": "repository-policy",
        "origin_paths": (
            "skills/gaussian-rigorous-calculations/SKILL.md",
            "skills/gaussian-rigorous-calculations/references/environment-and-license.md",
        ),
        "statement": (
            "The development guard remains offline, non-executing, and unable "
            "to issue a positive scientific claim."
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
        "extractor_id": "gaussian-document-scope-v1",
        "subjects": subjects,
    }


def canonical_bytes(value: object) -> bytes:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed scope catalog instead of emitting it",
    )
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
