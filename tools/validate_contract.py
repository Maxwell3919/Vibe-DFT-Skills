#!/usr/bin/env python3
"""Validate DFT skill interchange JSON against the canonical contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker


SCHEMAS = {
    "run": "run-manifest.schema.json",
    "artifact": "artifact-manifest.schema.json",
    "campaign": "campaign-record.schema.json",
    "recommendation": "recommendation-record.schema.json",
    "dataset": "normalized-dataset.schema.json",
    "plan": "postprocess-plan.schema.json",
    "execution": "tool-execution.schema.json",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_schema(kind: str) -> dict:
    path = repo_root() / "contracts" / SCHEMAS[kind]
    return json.loads(path.read_text(encoding="utf-8"))


def validation_errors(kind: str, data: object) -> list[str]:
    validator = Draft202012Validator(load_schema(kind), format_checker=FormatChecker())
    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def validate_file(kind: str, path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"<file>: {exc}"]
    return validation_errors(kind, data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(SCHEMAS))
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()
    errors = validate_file(args.kind, args.json_file)
    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        return 2
    print(f"PASS: {args.json_file} matches {SCHEMAS[args.kind]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
