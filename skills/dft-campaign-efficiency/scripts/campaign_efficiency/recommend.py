from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from statistics import median
from typing import Any

from .contracts import errors as contract_errors
from .store import comparable_records
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _identifier(applicability: dict[str, Any], evidence: list[str]) -> str:
    payload = json.dumps({"applicability": applicability, "evidence": evidence}, sort_keys=True).encode("utf-8")
    return "rec-" + hashlib.sha256(payload).hexdigest()[:24]


def recommendation(
    db: Path,
    code: str,
    code_version: str,
    task_type: str,
    system_class: str,
    atom_count: int,
    protocol_id: str,
) -> dict[str, Any]:
    applicability = {
        "code": code,
        "code_version": code_version,
        "task_type": task_type,
        "system_class": system_class,
        "atom_count": atom_count,
        "scientific_protocol_id": protocol_id,
    }
    records = comparable_records(db, code, code_version, task_type, system_class, atom_count, protocol_id)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[record["configuration_id"]].append(record)
    eligible = {key: value for key, value in groups.items() if len(value) >= 2}
    if len(eligible) < 2:
        result = {
            "schema_version": "1.0",
            "recommendation_id": _identifier(applicability, sorted(record["record_id"] for record in records)),
            "status": "insufficient-evidence",
            "applicability": applicability,
            "baseline_configuration_id": None,
            "recommended_configuration_id": None,
            "evidence_record_ids": sorted(record["record_id"] for record in records),
            "estimated_savings_fraction": None,
            "confidence": "none",
            "scientific_gate": "Collect at least two scientifically accepted observations for each of two controlled configurations under this exact protocol.",
            "limitations": [f"eligible configurations with n>=2: {len(eligible)}"],
            "generated_utc": utc_now(),
        }
    else:
        summary = {
            key: {
                "core_hours": median(record["metrics"]["core_hours"] for record in values),
                "wall_time_s": median(record["metrics"]["wall_time_s"] for record in values),
                "count": len(values),
            }
            for key, values in eligible.items()
        }
        recommended = min(summary, key=lambda key: (summary[key]["core_hours"], summary[key]["wall_time_s"], key))
        baseline = max(summary, key=lambda key: (summary[key]["core_hours"], summary[key]["wall_time_s"], key))
        baseline_cost = summary[baseline]["core_hours"]
        savings = (baseline_cost - summary[recommended]["core_hours"]) / baseline_cost if baseline_cost else 0.0
        selected = eligible[baseline] + eligible[recommended]
        evidence = sorted(record["record_id"] for record in selected)
        result = {
            "schema_version": "1.0",
            "recommendation_id": _identifier(applicability, evidence),
            "status": "validated-for-this-campaign" if savings > 0 else "insufficient-evidence",
            "applicability": applicability,
            "baseline_configuration_id": baseline,
            "recommended_configuration_id": recommended,
            "evidence_record_ids": evidence,
            "estimated_savings_fraction": max(0.0, min(1.0, savings)),
            "confidence": "campaign" if savings > 0 else "none",
            "scientific_gate": "Reproduce the recommended configuration in a controlled pilot and reapply the unchanged scientific acceptance criteria before adoption.",
            "limitations": [
                f"baseline median: {summary[baseline]['core_hours']:.6g} core-hours, {summary[baseline]['wall_time_s']:.6g} s, n={summary[baseline]['count']}",
                f"recommended median: {summary[recommended]['core_hours']:.6g} core-hours, {summary[recommended]['wall_time_s']:.6g} s, n={summary[recommended]['count']}",
                "This is project experience, not official DFT-code guidance.",
            ],
            "generated_utc": utc_now(),
        }
    failures = contract_errors("recommendation", result)
    if failures:
        raise ValueError("generated recommendation is invalid: " + "; ".join(failures))
    return result
