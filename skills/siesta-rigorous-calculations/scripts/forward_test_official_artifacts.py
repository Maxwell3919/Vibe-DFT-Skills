#!/usr/bin/env python3
"""Forward-test the output parser against hash-pinned official SIESTA artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from audit_siesta_case import parse_output_text


MANIFEST = Path(__file__).resolve().parents[1] / "references" / "official-artifact-fixtures.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(source_tree: Path) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "1.0" or not isinstance(manifest.get("artifacts"), list):
        raise ValueError("official artifact manifest is invalid")
    try:
        commit = subprocess.run(
            ["git", "-C", str(source_tree), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("source tree is not a readable official Git checkout") from exc
    if commit != manifest["source_commit"]:
        raise ValueError("official checkout commit differs from the pinned fixture manifest")
    results = []
    for record in manifest["artifacts"]:
        path = source_tree / record["path"]
        if not path.is_file() or sha256_file(path) != record["sha256"]:
            raise ValueError(f"official artifact hash mismatch: {record['path']}")
        parsed = parse_output_text(path.read_text(encoding="utf-8", errors="replace"))
        if parsed["versions"] != [manifest["artifact_runtime_version"]]:
            raise ValueError(f"runtime-version grammar mismatch: {record['path']}")
        if (parsed["start_markers"], parsed["end_markers"], parsed["completion_markers"]) != (1, 1, 1):
            raise ValueError(f"run-boundary grammar mismatch: {record['path']}")
        if parsed["fatal_markers"] != record["expected_fatal_markers"]:
            raise ValueError(f"fatal-marker precedence mismatch: {record['path']}")
        if parsed["relaxed_coordinates"] is not record["expected_relaxed"]:
            raise ValueError(f"relaxed-coordinate grammar mismatch: {record['path']}")
        energy = parsed["observables"].get("total_energy", {}).get("value")
        wall = parsed["observables"].get("wall_time", {}).get("value")
        if energy != record["expected_total_energy_ev"] or wall != record["expected_wall_time_s"]:
            raise ValueError(f"observable extraction mismatch: {record['path']}")
        results.append({
            "path_identity_sha256": hashlib.sha256(record["path"].encode()).hexdigest(),
            "artifact_sha256": record["sha256"],
            "status": "parser_grammar_pass",
        })
    return {
        "schema_version": "1.0",
        "status": "pass",
        "source_commit": commit,
        "validation_scope": manifest["validation_scope"],
        "artifacts": results,
        "limitations": manifest["limitations"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-tree", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        result = run(args.source_tree)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "block", "error_type": type(exc).__name__, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
