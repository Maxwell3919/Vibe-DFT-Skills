from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import errors as contract_errors
from .store import comparable_records


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
            "evidence_record_refs": [],
            "estimated_savings_fraction": None,
            "confidence": "none",
            "scientific_gate": "Collect at least two scientifically accepted observations for each of two controlled configurations under this exact protocol.",
            "limitations": [f"eligible configurations with n>=2: {len(eligible)}"],
            "generated_utc": utc_now(),
        }
    else:
        raise ValueError(
            "positive recommendation is blocked: the v2 private store has no "
            "platform-authenticated content-addressed campaign recordRefs"
        )
    failures = contract_errors("recommendation", result)
    if failures:
        raise ValueError("generated recommendation is invalid: " + "; ".join(failures))
    return result
