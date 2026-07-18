#!/usr/bin/env python3
"""Analyze an evidence-linked CP2K convergence series without claiming physical validity."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


REQUIRED_COLUMNS = {
    "run_id",
    "observable",
    "unit",
    "protocol_id",
    "comparability_group",
    "state_label",
    "audit_json",
}
OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
PLACEHOLDERS = {"", "unknown", "unresolved", "not_checked", "none", "n/a"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value: str, label: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise ValueError(f"{label} is not numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} is not finite")
    return result


def resolved(value: str | None, label: str) -> str:
    result = (value or "").strip()
    if result.casefold() in PLACEHOLDERS:
        raise ValueError(f"{label} must be a resolved non-placeholder label")
    return result


def load_audit(path: Path) -> dict[str, Any]:
    try:
        audit = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("audit evidence cannot be read as JSON") from exc
    if not isinstance(audit, dict) or audit.get("audit_schema_version") != "1.0":
        raise ValueError("audit evidence is not a CP2K audit schema 1.0 record")
    if audit.get("auditor") != "audit_cp2k_case.py" or audit.get("mode") != "run":
        raise ValueError("audit evidence has an unexpected producer or mode")
    if audit.get("verdict") != "technical_run_gates_passed_scientific_claim_blocked":
        raise ValueError("audit evidence does not have the strict technical-run verdict")
    gates = audit.get("gates")
    if not isinstance(gates, dict):
        raise ValueError("audit evidence has no gate map")
    required = {
        "input_integrity": {"pass"},
        "input_reproducibility": {"pass"},
        "execution_completion": {"pass"},
        "electronic_convergence": {"pass"},
        "ionic_or_task_completion": {"pass", "not_applicable"},
        "output_warnings": {"pass"},
        "version_identity": {"pass"},
        "input_output_binding": {"pass"},
        "runtime_environment": {"pass"},
        "numerical_convergence": {"not_evaluated_by_single_case"},
        "task_specific_validation": {"not_evaluated"},
        "physical_validity": {"not_evaluated_by_single_case"},
        "scientific_claim": {"blocked"},
    }
    blocked = {name: gates.get(name) for name, allowed in required.items() if gates.get(name) not in allowed}
    if blocked:
        details = ", ".join(f"{name}={status}" for name, status in sorted(blocked.items()))
        raise ValueError(f"audit evidence has blocked technical gates ({details})")
    summary = audit.get("summary")
    if not isinstance(summary, dict) or summary.get("errors") != 0:
        raise ValueError("audit evidence contains errors")
    return {
        "sha256": sha256_file(path),
        "case_id": audit.get("case_id"),
        "task_type": audit.get("task_type"),
    }


def load_series(path: Path, x_name: str, y_name: str) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = sorted((REQUIRED_COLUMNS | {x_name, y_name}) - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
        rows: list[dict[str, Any]] = []
        for line_number, row in enumerate(reader, 2):
            run_id = resolved(row.get("run_id"), f"run_id at line {line_number}")
            if not OPAQUE_ID.fullmatch(run_id):
                raise ValueError(f"run_id at line {line_number} is not an opaque safe identifier")
            audit_text = resolved(row.get("audit_json"), f"audit_json at line {line_number}")
            audit_path = Path(audit_text)
            if not audit_path.is_absolute():
                audit_path = path.parent / audit_path
            evidence = load_audit(audit_path)
            rows.append(
                {
                    "x": finite(row[x_name], x_name),
                    "y": finite(row[y_name], y_name),
                    "run_id": run_id,
                    "observable": resolved(row.get("observable"), "observable"),
                    "unit": resolved(row.get("unit"), "unit"),
                    "protocol_id": resolved(row.get("protocol_id"), "protocol_id"),
                    "comparability_group": resolved(row.get("comparability_group"), "comparability_group"),
                    "state_label": resolved(row.get("state_label"), "state_label"),
                    "audit_sha256": evidence["sha256"],
                    "audit_case_id": evidence["case_id"],
                    "task_type": evidence["task_type"],
                }
            )
    if len(rows) < 3:
        raise ValueError("At least three evidence-linked rows are required")
    rows.sort(key=lambda item: item["x"])
    if len({item["x"] for item in rows}) != len(rows):
        raise ValueError("The control variable contains duplicate values")
    if len({item["run_id"] for item in rows}) != len(rows):
        raise ValueError("run_id values must be unique")
    for field in ("observable", "unit", "protocol_id", "comparability_group", "state_label", "task_type"):
        if len({item[field] for item in rows}) != 1:
            raise ValueError(f"Series is not comparable: {field} differs across rows")
    return rows


def analyze(rows: list[dict[str, Any]], abs_tol: float, rel_tol: float, min_tail: int) -> dict[str, Any]:
    if not math.isfinite(abs_tol) or not math.isfinite(rel_tol) or abs_tol < 0 or rel_tol < 0:
        raise ValueError("Tolerances must be finite and non-negative")
    if min_tail < 3:
        raise ValueError("--min-tail must be at least 3")
    if len(rows) < min_tail:
        raise ValueError("Series has fewer rows than --min-tail")
    reference = rows[-1]["y"]
    allowed = abs_tol + rel_tol * abs(reference)
    candidate: float | None = None
    for start in range(len(rows) - min_tail + 1):
        tail = rows[start:]
        if len(tail) >= min_tail and all(abs(item["y"] - reference) <= allowed for item in tail):
            candidate = rows[start]["x"]
            break
    series = []
    signed_changes: list[float] = []
    for index, item in enumerate(rows):
        change = None if index == 0 else item["y"] - rows[index - 1]["y"]
        if change is not None:
            signed_changes.append(change)
        series.append(
            {
                "run_id": item["run_id"],
                "audit_sha256": item["audit_sha256"],
                "x": item["x"],
                "y": item["y"],
                "delta_previous": change,
                "delta_reference": item["y"] - reference,
            }
        )
    nonzero = [value for value in signed_changes if value != 0]
    direction_changes = sum(left * right < 0 for left, right in zip(nonzero, nonzero[1:]))
    status = "candidate_found" if candidate is not None else "no_stable_tail"
    return {
        "convergence_schema_version": "1.0",
        "analyzer": "analyze_convergence.py",
        "status": status,
        "candidate_x": candidate,
        "observable": rows[0]["observable"],
        "unit": rows[0]["unit"],
        "protocol_id": rows[0]["protocol_id"],
        "comparability_group": rows[0]["comparability_group"],
        "state_label": rows[0]["state_label"],
        "task_type": rows[0]["task_type"],
        "reference": {"x": rows[-1]["x"], "y": reference},
        "criterion": {
            "absolute_tolerance": abs_tol,
            "relative_tolerance": rel_tol,
            "combined_tolerance_at_reference": allowed,
            "minimum_tail_points": min_tail,
            "rule": "all values from candidate through the final sampled reference lie within tolerance of the final value",
        },
        "gates": {
            "technical_run_evidence": "pass",
            "declared_protocol_consistency": "pass",
            "declared_comparability": "pass",
            "declared_state_continuity": "pass",
            "numerical_stable_tail": "pass" if candidate is not None else "fail",
            "physical_validity": "not_assessed",
        },
        "allowed_evidence_label": (
            f"numerical convergence candidate for {rows[0]['observable']} within the stated tolerance ({rows[0]['unit']})"
            if candidate is not None
            else "no numerical convergence claim allowed"
        ),
        "diagnostics": {
            "points": len(rows),
            "maximum_adjacent_change": max(abs(value) for value in signed_changes),
            "direction_changes": direction_changes,
            "nonmonotonic": direction_changes > 0,
        },
        "series": series,
        "limitations": [
            "The final sampled value is only a provisional reference.",
            "Protocol, comparability, and state labels are declarations that require scientific review.",
            "A stable numerical tail does not establish physical validity or validate the model.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--x", required=True)
    parser.add_argument("--y", required=True)
    parser.add_argument("--abs-tol", required=True, type=float)
    parser.add_argument("--rel-tol", type=float, default=0.0)
    parser.add_argument("--min-tail", type=int, default=3)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        rows = load_series(args.csv_path, args.x, args.y)
        result = analyze(rows, args.abs_tol, args.rel_tol, args.min_tail)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked_invalid_evidence", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["status"] == "candidate_found" else 1


if __name__ == "__main__":
    raise SystemExit(main())
