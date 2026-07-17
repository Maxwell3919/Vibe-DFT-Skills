from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import errors as contract_errors
from .privacy import privacy_errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def campaign_from_run(
    run_path: Path,
    system_class: str,
    atom_count: int,
    configuration_id: str,
    accuracy_metrics: dict[str, Any] | None = None,
    record_id: str | None = None,
) -> dict[str, Any]:
    run = json.loads(run_path.read_text(encoding="utf-8"))
    failures = contract_errors("run", run) + privacy_errors(run)
    if failures:
        raise ValueError("invalid or private run manifest: " + "; ".join(failures))
    metrics = run["metrics"]
    if metrics.get("wall_time_s") is None or metrics.get("core_hours") is None:
        raise ValueError("run manifest requires observed wall_time_s and core_hours for efficiency ingestion")
    if run["scientific_acceptance"] == "accepted":
        outcome_status = "accepted"
    elif run["scientific_acceptance"] == "rejected":
        outcome_status = "rejected"
    elif run["status"] == "failed":
        outcome_status = "failed"
    elif run["status"] == "stopped":
        outcome_status = "stopped"
    else:
        raise ValueError("run is not terminally assessed; set accepted/rejected or failed/stopped")
    allowed_metrics = {
        key: metrics[key]
        for key in ("wall_time_s", "core_hours", "queue_wait_s", "peak_memory_mb", "retained_storage_mb", "restarts")
        if key in metrics
    }
    record = {
        "schema_version": "1.0",
        "record_id": record_id or f"campaign-{run['record_id']}",
        "run_manifest_id": run["record_id"],
        "code": run["code"],
        "code_version": run["code_version"],
        "task_type": run["task_type"],
        "system_class": system_class,
        "atom_count": atom_count,
        "scientific_protocol_id": run["scientific_protocol_id"],
        "configuration_id": configuration_id,
        "configuration": run["configuration"],
        "metrics": allowed_metrics,
        "outcome": {
            "scientifically_accepted": run["scientific_acceptance"] == "accepted",
            "status": outcome_status,
            "accuracy_metrics": accuracy_metrics or {},
            "failure_code": None if outcome_status == "accepted" else outcome_status,
        },
        "source_manifest_sha256": sha256_file(run_path),
        "recorded_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    failures = contract_errors("campaign", record) + privacy_errors(record)
    if failures:
        raise ValueError("generated campaign record is invalid: " + "; ".join(failures))
    return record
