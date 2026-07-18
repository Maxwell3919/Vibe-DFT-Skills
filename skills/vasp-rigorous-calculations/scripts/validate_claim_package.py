#!/usr/bin/env python3
"""Validate a VASP task evidence package and fail closed before expert acceptance."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

from analyze_convergence import load_passing_audit, sha256_file


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILES = SKILL_ROOT / "references" / "task-evidence-profiles.json"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
PACKAGE_KEYS = {
    "schema_version",
    "claim_id",
    "task_type",
    "observable",
    "unit",
    "absolute_tolerance",
    "relative_tolerance",
    "audit_json",
    "convergence_json",
    "checks",
}


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def resolved_path(value: Any, base: Path, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty path")
    path = Path(value)
    return path if path.is_absolute() else base / path


def finite_nonnegative(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


def required_checks(task_type: str, profiles_path: Path = DEFAULT_PROFILES) -> tuple[bool, set[str]]:
    profiles = load_object(profiles_path, "task evidence profiles")
    if profiles.get("schema_version") != "1.0":
        raise ValueError("unsupported task evidence profile schema")
    profile = profiles.get("profiles", {}).get(task_type)
    if not isinstance(profile, dict):
        raise ValueError(f"unsupported task_type: {task_type}")
    common = profiles.get("common_checks")
    specific = profile.get("required_checks")
    if not isinstance(common, list) or not isinstance(specific, list):
        raise ValueError("task evidence profile has invalid check lists")
    checks = {str(item) for item in common + specific}
    return bool(profile.get("claim_supported")), checks


def conditional_checks(selected_values: dict[str, Any]) -> set[str]:
    checks: set[str] = set()
    true_values = {"T", ".TRUE.", "TRUE", "1", "YES", "Y"}

    def enabled(tag: str) -> bool:
        value = selected_values.get(tag)
        return isinstance(value, str) and value.strip().upper() in true_values

    if selected_values.get("ISPIN") == "2" or "MAGMOM" in selected_values:
        checks.add("magnetic-state-search-and-final-moments")
    if enabled("LSORBIT"):
        checks.add("soc-axis-orientation-and-state-comparability")
    if enabled("LNONCOLLINEAR"):
        checks.add("noncollinear-spin-definition-and-final-state")
    if enabled("LDAU"):
        checks.add("dftu-formulation-mapping-and-parameter-provenance")
    if enabled("LHFCALC"):
        checks.add("hybrid-definition-and-numerical-controls")
    ivdw = selected_values.get("IVDW")
    if isinstance(ivdw, str) and ivdw.strip() not in {"", "0"}:
        checks.add("dispersion-definition-and-sensitivity")
    if enabled("LDIPOL"):
        checks.add("dipole-origin-direction-and-boundary-treatment")
    if "NELECT" in selected_values:
        checks.add("charge-state-and-electrostatic-treatment")
    return checks


def validate_checks(value: Any, required: set[str], base: Path) -> dict[str, Any]:
    if not isinstance(value, list):
        raise ValueError("checks must be an array")
    records: dict[str, dict[str, Any]] = {}
    malformed: list[str] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            malformed.append(f"checks[{index}] is not an object")
            continue
        check_id = record.get("id")
        if not isinstance(check_id, str) or not SAFE_ID.fullmatch(check_id):
            malformed.append(f"checks[{index}] has an invalid id")
            continue
        if check_id in records:
            malformed.append(f"duplicate check id: {check_id}")
            continue
        evidence_files = record.get("evidence_files")
        hashes: list[str] = []
        if not isinstance(evidence_files, list) or not evidence_files or any(not isinstance(item, str) or not item.strip() for item in evidence_files):
            malformed.append(f"{check_id} requires one or more evidence files")
        else:
            for item in evidence_files:
                evidence_path = Path(item)
                if not evidence_path.is_absolute():
                    evidence_path = base / evidence_path
                if not evidence_path.is_file():
                    malformed.append(f"{check_id} evidence file is missing")
                    continue
                hashes.append(sha256_file(evidence_path))
        record = dict(record)
        record["computed_evidence_sha256"] = hashes
        records[check_id] = record
    missing = sorted(required - set(records))
    unexpected = sorted(set(records) - required)
    blocked = sorted(
        check_id for check_id in required & set(records) if records[check_id].get("status") != "pass"
    )
    return {
        "status": "pass" if not (malformed or missing or unexpected or blocked) else "blocked",
        "required": sorted(required),
        "missing": missing,
        "unexpected": unexpected,
        "blocked": blocked,
        "malformed": malformed,
        "evidence": {
            check_id: sorted(set(records[check_id].get("computed_evidence_sha256", [])))
            for check_id in sorted(required & set(records))
            if isinstance(records[check_id].get("computed_evidence_sha256"), list)
        },
    }


def validate_package(package_path: Path, profiles_path: Path = DEFAULT_PROFILES) -> dict[str, Any]:
    package = load_object(package_path, "claim package")
    missing_keys = sorted(PACKAGE_KEYS - set(package))
    extra_keys = sorted(set(package) - PACKAGE_KEYS)
    if missing_keys or extra_keys:
        raise ValueError(f"claim package keys invalid; missing={missing_keys}, extra={extra_keys}")
    if package.get("schema_version") != "1.0":
        raise ValueError("unsupported claim package schema")
    claim_id = package.get("claim_id")
    if not isinstance(claim_id, str) or not SAFE_ID.fullmatch(claim_id):
        raise ValueError("claim_id must be an opaque safe identifier")
    task_type = package.get("task_type")
    if not isinstance(task_type, str):
        raise ValueError("task_type must be a string")
    claim_supported, required = required_checks(task_type, profiles_path)
    observable = package.get("observable")
    unit = package.get("unit")
    if not isinstance(observable, str) or not observable.strip() or not isinstance(unit, str) or not unit.strip():
        raise ValueError("observable and unit must be nonempty strings")
    abs_tol = finite_nonnegative(package.get("absolute_tolerance"), "absolute_tolerance")
    rel_tol = finite_nonnegative(package.get("relative_tolerance"), "relative_tolerance")

    base = package_path.parent
    audit_path = resolved_path(package.get("audit_json"), base, "audit_json")
    convergence_path = resolved_path(package.get("convergence_json"), base, "convergence_json")
    audit = load_passing_audit(audit_path)
    required |= conditional_checks(audit["selected_values"])
    convergence = load_object(convergence_path, "convergence evidence")
    convergence_hash = sha256_file(convergence_path)
    blockers: list[str] = []
    if not claim_supported:
        blockers.append("generic task profile cannot support a scientific claim")
    if audit.get("task_type") != task_type:
        blockers.append("audit task_type differs from claim package")
    if convergence.get("convergence_schema_version") != "2.0" or convergence.get("analyzer") != "analyze_convergence.py":
        blockers.append("convergence evidence has an unexpected schema or producer")
    if convergence.get("status") != "candidate_found":
        blockers.append("convergence evidence has no stable-tail candidate")
    if convergence.get("task_type") != task_type:
        blockers.append("convergence task_type differs from claim package")
    if convergence.get("observable") != observable or convergence.get("unit") != unit:
        blockers.append("convergence observable or unit differs from claim package")
    criterion = convergence.get("criterion")
    if not isinstance(criterion, dict):
        blockers.append("convergence evidence has no criterion")
    else:
        if criterion.get("absolute_tolerance") != abs_tol or criterion.get("relative_tolerance") != rel_tol:
            blockers.append("convergence tolerance differs from claim package")
    series = convergence.get("series")
    audit_hashes = {
        item.get("audit_sha256")
        for item in series
        if isinstance(item, dict) and isinstance(item.get("audit_sha256"), str)
    } if isinstance(series, list) else set()
    if audit["sha256"] not in audit_hashes:
        blockers.append("selected run audit is not part of the convergence series")
    convergence_gates = convergence.get("gates")
    expected_convergence_gates = {
        "technical_run_evidence": "pass",
        "declared_comparability": "pass",
        "declared_state_continuity": "pass",
        "numerical_stable_tail": "pass",
        "physical_validity": "not_assessed",
    }
    if not isinstance(convergence_gates, dict) or any(
        convergence_gates.get(name) != status for name, status in expected_convergence_gates.items()
    ):
        blockers.append("convergence gate map is incomplete or blocked")

    checks = validate_checks(package.get("checks"), required, base)
    if checks["status"] != "pass":
        blockers.append("task evidence checks are incomplete or blocked")
    eligible = not blockers
    return {
        "claim_package_schema_version": "1.0",
        "claim_id": claim_id,
        "task_type": task_type,
        "case_id": audit.get("case_id"),
        "observable": observable,
        "unit": unit,
        "audit_sha256": audit["sha256"],
        "convergence_sha256": convergence_hash,
        "checks": checks,
        "blockers": blockers,
        "gates": {
            "technical_run_evidence": "pass",
            "numerical_convergence_candidate": "pass" if convergence.get("status") == "candidate_found" else "fail",
            "task_specific_evidence_package": checks["status"],
            "physical_validity": "declared_evidence_complete_not_independently_verified" if eligible else "unresolved",
            "scientific_acceptance": "requires_expert_review" if eligible else "blocked",
        },
        "status": "eligible_for_expert_review" if eligible else "blocked",
        "maximum_allowed_conclusion": (
            "The structured VASP evidence package is complete for expert scientific review; it is not automatically accepted."
            if eligible
            else "No scientific claim is allowed until every blocker is resolved."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_package(args.package, args.profiles)
    except OSError:
        print(json.dumps({"status": "blocked_invalid_package", "error": "claim evidence cannot be read"}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "blocked_invalid_package", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["status"] == "eligible_for_expert_review" else 2


if __name__ == "__main__":
    raise SystemExit(main())
