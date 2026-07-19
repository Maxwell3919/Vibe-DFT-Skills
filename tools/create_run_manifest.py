#!/usr/bin/env python3
"""Create a privacy-safe run manifest for a supported DFT-code campaign handoff."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

from software_registry import calculation_codes
import strict_json
from validate_semantics import semantic_findings


def load_object(path: Path | None) -> dict:
    if path is None:
        return {}
    return strict_json.load_object(path, path.name)


def load_array(path: Path | None) -> list[object]:
    if path is None:
        return []
    return strict_json.load_array(path, path.name)


def main() -> int:
    try:
        supported_codes = calculation_codes()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: cannot load supported calculation codes: {exc}", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", choices=supported_codes, required=True)
    parser.add_argument("--code-version", required=True)
    parser.add_argument("--task-type", required=True)
    parser.add_argument("--case-id", required=True, help="Use an anonymized stable identifier")
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--status", choices=("planned", "running", "completed", "stopped", "failed"), required=True)
    parser.add_argument(
        "--scientific-acceptance",
        choices=("not_assessed", "requires_human_review"),
        required=True,
    )
    parser.add_argument("--configuration", type=Path)
    parser.add_argument("--metrics", type=Path)
    parser.add_argument("--evidence", type=Path, help="JSON array of role/label/status/hash evidence records")
    parser.add_argument("--limitation", action="append", default=[])
    parser.add_argument("--record-id")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    try:
        manifest = {
            "schema_version": "1.0",
            "record_id": args.record_id or f"run-{uuid.uuid4().hex}",
            "code": args.code,
            "code_version": args.code_version,
            "task_type": args.task_type,
            "case_id": args.case_id,
            "scientific_protocol_id": args.protocol_id,
            "status": args.status,
            "scientific_acceptance": args.scientific_acceptance,
            "configuration": load_object(args.configuration),
            "metrics": load_object(args.metrics),
            "evidence": load_array(args.evidence),
            "limitations": args.limitation,
            "provenance": {
                "collector": "create_run_manifest.py",
                "collector_version": "1.2.0",
                "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            },
        }
    except (OSError, strict_json.StrictJSONError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    findings = semantic_findings("run", manifest)
    if findings:
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"ERROR: cannot write run manifest: {exc}", file=sys.stderr)
        return 2
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
