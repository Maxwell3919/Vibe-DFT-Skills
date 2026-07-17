#!/usr/bin/env python3
"""Create a privacy-safe run manifest for QE or VASP campaign handoff."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

from validate_contract import validation_errors


def load_object(path: Path | None) -> dict:
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", choices=("qe", "vasp"), required=True)
    parser.add_argument("--code-version", required=True)
    parser.add_argument("--task-type", required=True)
    parser.add_argument("--case-id", required=True, help="Use an anonymized stable identifier")
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--status", choices=("planned", "running", "completed", "stopped", "failed", "accepted"), required=True)
    parser.add_argument("--scientific-acceptance", choices=("accepted", "rejected", "not_assessed"), required=True)
    parser.add_argument("--configuration", type=Path)
    parser.add_argument("--metrics", type=Path)
    parser.add_argument("--limitation", action="append", default=[])
    parser.add_argument("--record-id")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

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
        "evidence": [],
        "limitations": args.limitation,
        "provenance": {
            "collector": "create_run_manifest.py",
            "collector_version": "1.0.0",
            "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        },
    }
    errors = validation_errors("run", manifest)
    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
