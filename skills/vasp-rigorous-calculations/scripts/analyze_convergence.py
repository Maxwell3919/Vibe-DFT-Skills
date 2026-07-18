#!/usr/bin/env python3
"""Analyze an evidence-linked VASP convergence series without claiming physical validity."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_EVIDENCE_COLUMNS = {
    "run_id",
    "observable",
    "unit",
    "comparability_group",
    "state_label",
    "audit_json",
}
OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
UNRESOLVED_LABELS = {"", "unknown", "unresolved", "not_checked", "not-checked", "none", "n/a"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_float(value: str, name: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} is not numeric: {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} is not finite: {value!r}")
    return result


def load_passing_audit(path: Path) -> dict[str, Any]:
    try:
        audit = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError("audit evidence cannot be read") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("audit evidence is invalid JSON") from exc
    if not isinstance(audit, dict) or audit.get("audit_schema_version") != "2.0":
        raise ValueError("audit evidence is not a VASP audit schema 2.0 record")
    if audit.get("auditor") != "audit_vasp_case.py":
        raise ValueError("audit evidence has an unexpected producer")
    if audit.get("mode") != "run":
        raise ValueError("audit evidence was not produced in run mode")
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
        "ionic_convergence": {"pass", "not_applicable"},
        "output_warnings": {"pass"},
        "version_identity": {"pass"},
        "task_specific_validation": {"not_evaluated"},
        "numerical_convergence": {"not_evaluated_by_single_case"},
        "physical_validity": {"not_evaluated_by_single_case"},
        "scientific_claim": {"blocked"},
    }
    if audit.get("task_type") == "relax":
        required["ionic_convergence"] = {"pass"}
    blocked = {name: gates.get(name) for name, allowed in required.items() if gates.get(name) not in allowed}
    if blocked:
        details = ", ".join(f"{name}={status}" for name, status in sorted(blocked.items()))
        raise ValueError(f"audit evidence has blocked technical gates ({details})")
    summary = audit.get("summary")
    if not isinstance(summary, dict) or summary.get("errors") != 0 or summary.get("warnings") != 0:
        raise ValueError("audit evidence contains errors or unresolved warnings")
    files = audit.get("files")
    incar = files.get("INCAR") if isinstance(files, dict) else None
    selected_values = incar.get("selected_values") if isinstance(incar, dict) else None
    if not isinstance(selected_values, dict):
        raise ValueError("audit evidence has no privacy-safe INCAR summary")
    return {
        "sha256": sha256_file(path),
        "case_id": audit.get("case_id"),
        "task_type": audit.get("task_type"),
        "verdict": audit.get("verdict"),
        "selected_values": selected_values,
    }


def require_label(value: str | None, name: str) -> str:
    normalized = (value or "").strip()
    if normalized.casefold() in UNRESOLVED_LABELS:
        raise ValueError(f"{name} must be a resolved, non-placeholder label")
    return normalized


def load_series(path: Path, x_name: str, y_name: str) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = REQUIRED_EVIDENCE_COLUMNS | {x_name, y_name}
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
        rows: list[dict[str, Any]] = []
        for line_number, row in enumerate(reader, 2):
            run_id = require_label(row.get("run_id"), f"run_id at line {line_number}")
            if not OPAQUE_ID.fullmatch(run_id):
                raise ValueError(f"run_id at line {line_number} is not an opaque safe identifier")
            audit_text = require_label(row.get("audit_json"), f"audit_json at line {line_number}")
            audit_path = Path(audit_text)
            if not audit_path.is_absolute():
                audit_path = path.parent / audit_path
            evidence = load_passing_audit(audit_path)
            rows.append(
                {
                    "x": finite_float(row[x_name], x_name),
                    "y": finite_float(row[y_name], y_name),
                    "run_id": run_id,
                    "observable": require_label(row.get("observable"), f"observable at line {line_number}"),
                    "unit": require_label(row.get("unit"), f"unit at line {line_number}"),
                    "comparability_group": require_label(row.get("comparability_group"), f"comparability_group at line {line_number}"),
                    "state_label": require_label(row.get("state_label"), f"state_label at line {line_number}"),
                    "audit_sha256": evidence["sha256"],
                    "audit_case_id": evidence["case_id"],
                    "task_type": evidence["task_type"],
                }
            )
    if len(rows) < 3:
        raise ValueError("At least three evidence-linked data rows are required")
    rows.sort(key=lambda row: row["x"])
    if len({row["x"] for row in rows}) != len(rows):
        raise ValueError("The control variable contains duplicate values")
    if len({row["run_id"] for row in rows}) != len(rows):
        raise ValueError("run_id values must be unique")
    for field in ("observable", "unit", "comparability_group", "state_label", "task_type"):
        values = {row[field] for row in rows}
        if len(values) != 1:
            raise ValueError(f"Series is not comparable: {field} differs across rows")
    return rows


def analyze(rows: list[dict[str, Any]], abs_tol: float, rel_tol: float, min_tail: int) -> dict[str, object]:
    if abs_tol < 0 or rel_tol < 0 or not math.isfinite(abs_tol) or not math.isfinite(rel_tol):
        raise ValueError("Tolerances must be finite and non-negative")
    if min_tail < 3:
        raise ValueError("--min-tail must be at least 3")
    if len(rows) < min_tail:
        raise ValueError("Series has fewer rows than --min-tail")
    required_runtime_fields = {
        "x",
        "y",
        "run_id",
        "observable",
        "unit",
        "comparability_group",
        "state_label",
        "audit_sha256",
        "task_type",
    }
    for index, row in enumerate(rows):
        missing = required_runtime_fields - set(row)
        if missing:
            raise ValueError(f"row {index} lacks evidence fields: {', '.join(sorted(missing))}")
    for field in ("observable", "unit", "comparability_group", "state_label", "task_type"):
        if len({row[field] for row in rows}) != 1:
            raise ValueError(f"Series is not comparable: {field} differs across rows")

    reference = rows[-1]["y"]
    allowed = abs_tol + rel_tol * abs(reference)
    enriched: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        previous = rows[index - 1]["y"] if index else None
        enriched.append(
            {
                "run_id": row["run_id"],
                "audit_sha256": row["audit_sha256"],
                "x": row["x"],
                "y": row["y"],
                "delta_previous": None if previous is None else row["y"] - previous,
                "delta_reference": row["y"] - reference,
            }
        )

    candidate = None
    for start in range(0, len(rows) - min_tail + 1):
        tail = rows[start:]
        if len(tail) >= min_tail and all(abs(row["y"] - reference) <= allowed for row in tail):
            candidate = rows[start]["x"]
            break

    adjacent = [abs(enriched[i]["delta_previous"]) for i in range(1, len(enriched))]
    signed = [enriched[i]["delta_previous"] for i in range(1, len(enriched))]
    nonzero = [value for value in signed if value != 0.0]
    direction_changes = sum(first * second < 0 for first, second in zip(nonzero, nonzero[1:]))
    status = "candidate_found" if candidate is not None else "no_stable_tail"
    observable = str(rows[0]["observable"])
    unit = str(rows[0]["unit"])
    return {
        "convergence_schema_version": "2.0",
        "analyzer": "analyze_convergence.py",
        "status": status,
        "candidate_x": candidate,
        "observable": observable,
        "unit": unit,
        "comparability_group": rows[0]["comparability_group"],
        "state_label": rows[0]["state_label"],
        "task_type": rows[0]["task_type"],
        "reference": {"x": rows[-1]["x"], "y": reference},
        "criterion": {
            "absolute_tolerance": abs_tol,
            "relative_tolerance": rel_tol,
            "combined_tolerance_at_reference": allowed,
            "minimum_tail_points": min_tail,
            "rule": "all values from candidate through final sampled reference lie within tolerance of the final value",
        },
        "gates": {
            "technical_run_evidence": "pass",
            "declared_comparability": "pass",
            "declared_state_continuity": "pass",
            "numerical_stable_tail": "pass" if candidate is not None else "fail",
            "physical_validity": "not_assessed",
        },
        "allowed_evidence_label": (
            f"numerical convergence candidate for {observable} within the stated tolerance ({unit})"
            if candidate is not None
            else "no numerical convergence claim allowed"
        ),
        "diagnostics": {
            "points": len(rows),
            "maximum_adjacent_change": max(adjacent),
            "direction_changes": direction_changes,
            "nonmonotonic": direction_changes > 0,
        },
        "series": enriched,
        "limitations": [
            "The final sampled value is only a provisional reference; this screen cannot exclude convergence beyond the sampled range.",
            "The comparability group and state label are declared metadata; scientific review must verify that the declarations are true.",
            "A stable numerical tail does not establish physical validity or validate the underlying model.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--x", required=True, help="Control-variable column")
    parser.add_argument("--y", required=True, help="Observable column")
    parser.add_argument("--abs-tol", type=float, required=True)
    parser.add_argument("--rel-tol", type=float, default=0.0)
    parser.add_argument("--min-tail", type=int, default=3)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        rows = load_series(args.csv_path, args.x, args.y)
        result = analyze(rows, args.abs_tol, args.rel_tol, args.min_tail)
    except OSError:
        print(json.dumps({"status": "blocked_invalid_evidence", "error": "input evidence cannot be read"}, ensure_ascii=False), file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps({"status": "blocked_invalid_evidence", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["status"] == "candidate_found" else 1


if __name__ == "__main__":
    raise SystemExit(main())
