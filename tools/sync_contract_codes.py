#!/usr/bin/env python3
"""Check or synchronize contract code enums with the software registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from software_registry import aggregate_codes, calculation_codes, repo_root


CONTRACT_CODE_KINDS = {
    "run-manifest.schema.json": "calculation",
    "campaign-record.schema.json": "calculation",
    "artifact-manifest.schema.json": "aggregate",
    "normalized-dataset.schema.json": "aggregate",
    "postprocess-plan.schema.json": "aggregate",
}
CODE_ENUM = re.compile(r'("code"\s*:\s*\{\s*"enum"\s*:\s*)\[[^\]]*\]')


def expected_codes(kind: str, registry: Path | None = None) -> list[str]:
    values = list(calculation_codes(registry))
    if kind == "aggregate":
        values.extend(aggregate_codes(registry))
    return values


def contract_drift(root: Path | None = None) -> list[str]:
    selected_root = root or repo_root()
    registry = selected_root / "registry" / "software-registry.yaml"
    failures: list[str] = []
    for filename, kind in CONTRACT_CODE_KINDS.items():
        path = selected_root / "contracts" / filename
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            actual = schema["properties"]["code"]["enum"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            failures.append(f"{filename}: cannot read code enum: {exc}")
            continue
        expected = expected_codes(kind, registry)
        if actual != expected:
            failures.append(f"{filename}: code enum {actual!r} != registry {expected!r}")
    return failures


def synchronize(root: Path | None = None) -> list[Path]:
    selected_root = root or repo_root()
    registry = selected_root / "registry" / "software-registry.yaml"
    changed: list[Path] = []
    for filename, kind in CONTRACT_CODE_KINDS.items():
        path = selected_root / "contracts" / filename
        text = path.read_text(encoding="utf-8")
        replacement = json.dumps(expected_codes(kind, registry), ensure_ascii=False)
        updated, count = CODE_ENUM.subn(lambda match: match.group(1) + replacement, text, count=1)
        if count != 1:
            raise ValueError(f"{filename}: expected exactly one code enum, found {count}")
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Update enum lines in place before checking")
    args = parser.parse_args()
    try:
        changed = synchronize() if args.write else []
        failures = contract_drift()
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for path in changed:
        print(f"updated: {path.relative_to(repo_root())}")
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        print("Run tools/sync_contract_codes.py --write after reviewing the registry change.", file=sys.stderr)
        return 2
    print(f"PASS: {len(CONTRACT_CODE_KINDS)} contract code enums match the software registry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
