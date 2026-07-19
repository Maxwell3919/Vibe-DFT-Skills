from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

from .contracts import errors as contract_errors
from .privacy import privacy_errors
from strict_json import StrictJSONError, loads_object, read_bytes_bounded
from validate_semantics import semantic_findings


def campaign_from_run(
    run_path: Path,
    system_class: str,
    atom_count: int,
    configuration_id: str,
    accuracy_metrics: dict[str, Any] | None = None,
    record_id: str | None = None,
) -> dict[str, Any]:
    try:
        run_raw = read_bytes_bounded(run_path, run_path.name)
        run = loads_object(run_raw, run_path.name)
    except (OSError, StrictJSONError) as exc:
        raise ValueError(f"invalid run manifest: {exc}") from exc
    failures = [finding.render() for finding in semantic_findings("run", run)]
    failures += privacy_errors(run)
    if failures:
        raise ValueError("invalid or private run manifest: " + "; ".join(failures))
    metrics = run["metrics"]
    if metrics.get("wall_time_s") is None or metrics.get("core_hours") is None:
        raise ValueError("run manifest requires observed wall_time_s and core_hours for efficiency ingestion")
    if run["status"] == "completed":
        outcome_status = "completed-unreviewed"
    elif run["status"] == "failed":
        outcome_status = "failed"
    elif run["status"] == "stopped":
        outcome_status = "stopped"
    else:
        raise ValueError(
            "run is not a cost-recordable terminal state; use completed, failed, or stopped"
        )
    allowed_metrics = {
        key: metrics[key]
        for key in ("wall_time_s", "core_hours", "queue_wait_s", "peak_memory_mb", "retained_storage_mb", "restarts")
        if key in metrics
    }
    source_sha256 = hashlib.sha256(run_raw).hexdigest()
    record = {
        "schema_version": "1.0",
        "record_id": record_id or f"campaign-{run['record_id']}",
        "run_manifest_id": run["record_id"],
        "source_run_ref": {
            "contract_name": "run-manifest",
            "schema_version": "1.0",
            "record_id": run["record_id"],
            "sha256": source_sha256,
            "role": "source-run",
        },
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
            "scientifically_accepted": False,
            "scientific_acceptance": run["scientific_acceptance"],
            "status": outcome_status,
            "accuracy_metrics": accuracy_metrics or {},
            "failure_code": (
                None if outcome_status == "completed-unreviewed" else outcome_status
            ),
        },
        "acceptance_evidence": {
            "calculation_record_ref": None,
            "decision_ref": None,
            "postdecision_claim_map_ref": None,
        },
        "source_manifest_sha256": source_sha256,
        "recorded_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    failures = contract_errors("campaign", record) + privacy_errors(record)
    if failures:
        raise ValueError("generated campaign record is invalid: " + "; ".join(failures))
    return record
