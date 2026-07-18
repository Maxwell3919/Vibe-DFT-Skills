#!/usr/bin/env python3
"""Analyze a SIESTA series whose values are bound to current input/output audits."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


TOOL_VERSION = "2.0.0"
SCHEMA_VERSION = "2.0"
CSV_FIELDS = ["setting", "observable", "protocol_id", "audit_report", "input_file", "output_file"]
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
AUDIT_GATES = (
    "scientific_plan", "official_source_resolution", "fdf_syntax", "fdf_semantics", "structure_consistency",
    "pseudopotential_provenance", "numerical_controls", "parent_ancestry", "official_version_match",
    "input_output_consistency", "execution_completion", "electronic_convergence", "output_warnings", "output_observables",
)


def generated_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not readable JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def finite(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} is not finite")
    return result


def same_number(left: Any, right: Any, *, absolute: float = 0.0) -> bool:
    try:
        return math.isclose(float(left), float(right), rel_tol=1e-12, abs_tol=absolute)
    except (TypeError, ValueError):
        return False


def evidence_path(csv_root: Path, raw: str | None, row: int, role: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"row {row} has no {role} path")
    candidate = Path(raw)
    candidate = (candidate if candidate.is_absolute() else csv_root / candidate).resolve()
    if not candidate.is_file():
        raise ValueError(f"row {row} {role} is not a readable file")
    return candidate


def validate_plan_contract(plan: dict[str, Any], protocol_id: str, observable: str, unit: str, abs_tol: float | None, rel_tol: float | None) -> None:
    if (
        plan.get("schema_version") != "2.0"
        or plan.get("producer") != "create_siesta_plan.py"
        or plan.get("producer_version") != "2.0.0"
        or plan.get("decision") != "pass"
        or plan.get("state") != "plan_ready"
    ):
        raise ValueError("plan was not produced by the current SIESTA scientific-plan tool")
    if plan.get("scientific_protocol_id") != protocol_id:
        raise ValueError("plan protocol differs from --protocol-id")
    contract = plan.get("observable")
    if not isinstance(contract, dict) or contract.get("name") != observable or contract.get("unit") != unit:
        raise ValueError("requested observable/unit differs from the plan")
    for requested, field in ((abs_tol, "absolute_tolerance"), (rel_tol, "relative_tolerance")):
        planned = contract.get(field)
        if requested is None and planned is None:
            continue
        if requested is None or planned is None or not same_number(requested, planned):
            raise ValueError(f"requested {field} differs from the plan")


def load_series(
    csv_path: Path,
    plan_path: Path,
    protocol_id: str,
    parameter: str,
    parameter_unit: str,
    observable: str,
    observable_unit: str,
) -> list[dict[str, Any]]:
    plan_sha = sha256_file(plan_path)
    csv_root = csv_path.resolve().parent
    points: list[dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != CSV_FIELDS:
            raise ValueError("CSV requires exactly setting, observable, protocol_id, audit_report, input_file, and output_file columns")
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"row {row_number} has too many fields")
            if row.get("protocol_id") != protocol_id:
                raise ValueError(f"row {row_number} protocol differs from --protocol-id")
            setting = finite(row.get("setting"), f"setting at row {row_number}")
            observed = finite(row.get("observable"), f"observable at row {row_number}")
            audit_path = evidence_path(csv_root, row.get("audit_report"), row_number, "audit report")
            input_path = evidence_path(csv_root, row.get("input_file"), row_number, "input")
            output_path = evidence_path(csv_root, row.get("output_file"), row_number, "output")
            audit = load_object(audit_path, f"row {row_number} audit")
            if (
                audit.get("schema_version") != "2.0"
                or audit.get("auditor") != "audit_siesta_case.py"
                or audit.get("auditor_version") != "2.0.0"
                or audit.get("mode") != "run"
                or audit.get("decision") != "pass"
                or audit.get("maximum_conclusion") != "technical_run_gates_passed_scientific_claim_blocked"
            ):
                raise ValueError(f"row {row_number} is not a current passing SIESTA run audit")
            gates = audit.get("gates")
            if not isinstance(gates, dict) or any(gates.get(name) != "pass" for name in AUDIT_GATES):
                raise ValueError(f"row {row_number} audit has incomplete technical gates")
            if gates.get("scientific_acceptance") != "blocked" or gates.get("numerical_convergence") != "not_assessed" or gates.get("physical_validity") != "not_assessed":
                raise ValueError(f"row {row_number} audit does not preserve scientific gate separation")
            if audit.get("task_type") == "relax" and gates.get("task_specific_validity") != "pass":
                raise ValueError(f"row {row_number} relaxation task validity did not pass")
            evidence = audit.get("evidence")
            if not isinstance(evidence, dict):
                raise ValueError(f"row {row_number} audit evidence is missing")
            audit_input = evidence.get("input")
            audit_output = evidence.get("output")
            audit_plan = evidence.get("plan")
            input_sha = sha256_file(input_path)
            output_sha = sha256_file(output_path)
            if not isinstance(audit_input, dict) or audit_input.get("sha256") != input_sha:
                raise ValueError(f"row {row_number} input hash differs from its audit")
            if not isinstance(audit_output, dict) or audit_output.get("sha256") != output_sha:
                raise ValueError(f"row {row_number} output hash differs from its audit")
            if not isinstance(audit_plan, dict) or audit_plan.get("sha256") != plan_sha:
                raise ValueError(f"row {row_number} audit is bound to a different plan")
            if audit.get("scientific_protocol_id") != protocol_id:
                raise ValueError(f"row {row_number} audit protocol differs")
            parameters = evidence.get("convergence_parameters")
            parameter_record = parameters.get(parameter) if isinstance(parameters, dict) else None
            if not isinstance(parameter_record, dict):
                raise ValueError(f"row {row_number} audit has no verified {parameter} input evidence")
            if parameter_record.get("unit") != parameter_unit or not same_number(parameter_record.get("value"), setting):
                raise ValueError(f"row {row_number} setting/unit differs from the audited input")
            observables = evidence.get("observables")
            observable_record = observables.get(observable) if isinstance(observables, dict) else None
            if not isinstance(observable_record, dict):
                raise ValueError(f"row {row_number} audit has no verified {observable} output evidence")
            if observable_record.get("unit") != observable_unit or not same_number(observable_record.get("value"), observed, absolute=1e-14):
                raise ValueError(f"row {row_number} observable/unit differs from the audited output")
            points.append({
                "setting": setting,
                "observable": observed,
                "audit_sha256": sha256_file(audit_path),
                "input_sha256": input_sha,
                "output_sha256": output_sha,
                "case_id": audit.get("case_id"),
                "state_id": audit.get("state_id"),
                "task_type": audit.get("task_type"),
                "code_version": audit.get("expected_code_version"),
            })
    if len(points) < 3:
        raise ValueError("at least three evidence-linked points are required")
    for field in ("case_id", "state_id", "task_type", "code_version"):
        if len({point[field] for point in points}) != 1:
            raise ValueError(f"series is not comparable: {field} differs across audits")
    for field in ("setting", "audit_sha256", "input_sha256", "output_sha256"):
        if len({point[field] for point in points}) != len(points):
            raise ValueError(f"each point requires a distinct {field}")
    return points


def analyze(
    points: list[dict[str, Any]],
    *,
    parameter: str,
    parameter_unit: str,
    observable: str,
    observable_unit: str,
    protocol_id: str,
    absolute_tolerance: float | None,
    relative_tolerance: float | None,
    min_tail: int,
    direction: str,
) -> dict[str, Any]:
    absolute = 0.0 if absolute_tolerance is None else finite(absolute_tolerance, "absolute tolerance")
    relative = 0.0 if relative_tolerance is None else finite(relative_tolerance, "relative tolerance")
    if absolute < 0 or relative < 0 or (absolute_tolerance is None and relative_tolerance is None):
        raise ValueError("provide finite nonnegative absolute and/or relative tolerances")
    if min_tail < 3 or len(points) < min_tail:
        raise ValueError("stable-tail analysis requires at least three available tail points")
    if direction not in {"increasing", "decreasing"}:
        raise ValueError("direction must be increasing or decreasing")
    ordered = sorted(points, key=lambda point: point["setting"], reverse=direction == "decreasing")
    reference = ordered[-1]["observable"]
    allowed = absolute + relative * abs(reference)
    candidate: float | None = None
    for start in range(len(ordered) - min_tail + 1):
        tail = ordered[start:]
        if len(tail) >= min_tail and all(abs(point["observable"] - reference) <= allowed for point in tail):
            candidate = ordered[start]["setting"]
            break
    changes = [ordered[index]["observable"] - ordered[index - 1]["observable"] for index in range(1, len(ordered))]
    nonzero = [value for value in changes if value != 0]
    direction_changes = sum(left * right < 0 for left, right in zip(nonzero, nonzero[1:]))
    status = "candidate_found" if candidate is not None else "no_stable_tail"
    series = []
    for index, point in enumerate(ordered):
        series.append({
            "setting": point["setting"],
            "observable": point["observable"],
            "delta_previous": None if index == 0 else changes[index - 1],
            "delta_reference": point["observable"] - reference,
            "audit_sha256": point["audit_sha256"],
            "input_sha256": point["input_sha256"],
            "output_sha256": point["output_sha256"],
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "analyzer": "analyze_convergence.py",
        "analyzer_version": TOOL_VERSION,
        "code": "siesta",
        "status": status,
        "candidate_setting": candidate,
        "parameter": {"name": parameter, "unit": parameter_unit, "direction": direction},
        "observable": {"name": observable, "unit": observable_unit},
        "scientific_protocol_id": protocol_id,
        "case_id": ordered[0]["case_id"],
        "state_id": ordered[0]["state_id"],
        "task_type": ordered[0]["task_type"],
        "code_version": ordered[0]["code_version"],
        "reference": {"setting": ordered[-1]["setting"], "observable": reference},
        "criterion": {
            "absolute_tolerance": absolute_tolerance,
            "relative_tolerance": relative_tolerance,
            "combined_tolerance_at_reference": allowed,
            "minimum_tail_points": min_tail,
            "rule": "all values from the candidate through the most converged sampled reference lie within tolerance of the final value",
        },
        "gates": {
            "audited_input_output_binding": "pass",
            "plan_protocol_state_continuity": "pass",
            "numerical_stable_tail": "pass" if candidate is not None else "fail",
            "task_specific_validity": "not_reassessed",
            "physical_validity": "not_assessed",
            "scientific_acceptance": "blocked",
        },
        "allowed_evidence_label": f"numerical convergence candidate for {observable} within the declared {observable_unit} tolerance" if candidate is not None else "no numerical convergence claim allowed",
        "diagnostics": {
            "points": len(ordered),
            "maximum_adjacent_change": max(abs(value) for value in changes),
            "direction_changes": direction_changes,
            "nonmonotonic": direction_changes > 0,
        },
        "series": series,
        "limitations": [
            "The final sampled value is a provisional reference and cannot exclude changes beyond the sampled range.",
            "A stable tail for one observable does not establish basis completeness, eggbox control, state correctness, or model validity.",
            "Scientific acceptance remains blocked pending task-specific and physical review.",
        ],
        "provenance": {"collector": "analyze_convergence.py", "collector_version": TOOL_VERSION, "generated_utc": generated_utc()},
    }


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise ValueError("refusing to overwrite an existing convergence report")
    if not path.parent.is_dir():
        raise ValueError("report output parent directory does not exist")
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        handle.write(rendered)
        staged = Path(handle.name)
    os.replace(staged, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--parameter", required=True)
    parser.add_argument("--parameter-unit", required=True)
    parser.add_argument("--observable", required=True)
    parser.add_argument("--observable-unit", required=True)
    parser.add_argument("--absolute-tolerance", type=float)
    parser.add_argument("--relative-tolerance", type=float)
    parser.add_argument("--min-tail", type=int, default=3)
    parser.add_argument("--direction", choices=("increasing", "decreasing"), default="increasing")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        plan = load_object(args.plan, "scientific plan")
        validate_plan_contract(plan, args.protocol_id, args.observable, args.observable_unit, args.absolute_tolerance, args.relative_tolerance)
        points = load_series(args.csv, args.plan, args.protocol_id, args.parameter, args.parameter_unit, args.observable, args.observable_unit)
        result = analyze(
            points,
            parameter=args.parameter,
            parameter_unit=args.parameter_unit,
            observable=args.observable,
            observable_unit=args.observable_unit,
            protocol_id=args.protocol_id,
            absolute_tolerance=args.absolute_tolerance,
            relative_tolerance=args.relative_tolerance,
            min_tail=args.min_tail,
            direction=args.direction,
        )
        if args.out:
            protected = {args.csv.resolve(), args.plan.resolve()}
            if args.out.resolve() in protected:
                raise ValueError("--out must not overwrite CSV or plan evidence")
            atomic_write(args.out, result)
        else:
            print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
        return 0 if result["status"] == "candidate_found" else 1
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "blocked_invalid_evidence", "error_type": type(exc).__name__, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
