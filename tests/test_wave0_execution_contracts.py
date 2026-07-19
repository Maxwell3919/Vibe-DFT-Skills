from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from tools.bundle_semantics_execution import (
    CONTRACT_NAMES as PRODUCTION_CONTRACT_NAMES,
    OBLIGATIONS_BY_CONTRACT as PRODUCTION_OBLIGATIONS,
    evaluate as evaluate_execution_semantics,
)
from tools.bundle_semantics import (
    builtin_evaluator as production_builtin_evaluator,
    read_only_context as production_read_only_context,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
SCHEMA_NAMES = (
    "calculation-record-envelope",
    "execution-request",
    "execution-lease",
    "execution-record",
    "workflow-plan",
    "workflow-event",
    "decision-record",
    "claim-evidence-map",
)
SHA_A = "a" * 64
SHA_B = "b" * 64
NOW = "2026-07-18T12:00:00Z"
FINISHED = "2026-07-18T12:00:30Z"
LATER = "2026-07-18T13:00:00Z"


def record_ref(contract_name: str, record_id: str, role: str = "source") -> dict:
    return {
        "contract_name": contract_name,
        "schema_version": "1.0",
        "record_id": record_id,
        "sha256": SHA_A,
        "role": role,
    }


def file_ref(
    role: str = "input",
    label: str = "synthetic-input.dat",
    availability: str = "present",
) -> dict:
    present = availability == "present"
    return {
        "role": role,
        "label": label,
        "media_type": "application/octet-stream",
        "format": "synthetic-data",
        "format_version": "1.0",
        "availability": availability,
        "sha256": SHA_B if present else None,
        "bytes": 128 if present else None,
        "sensitivity": "public",
        "redistribution": "redistributable",
    }


def actor(
    actor_type: str = "deterministic-tool",
    actor_id: str = "synthetic-tool",
    role: str = "validator",
) -> dict:
    return {"actor_type": actor_type, "actor_id": actor_id, "role": role}


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


RECORD_ID_FIELDS = {
    "run-manifest": "record_id",
    "calculation-record-envelope": "record_id",
    "execution-request": "request_id",
    "execution-lease": "lease_id",
    "execution-record": "execution_id",
    "workflow-plan": "plan_id",
    "workflow-event": "event_id",
    "decision-record": "decision_id",
    "claim-evidence-map": "map_id",
}


def record_key(data: dict) -> tuple[str, str]:
    contract_name = data.get("contract_name")
    if contract_name is None and {"code", "scientific_protocol_id", "evidence"}.issubset(data):
        contract_name = "run-manifest"
    return contract_name, data[RECORD_ID_FIELDS[contract_name]]


def exact_raw_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def exact_record_ref(data: dict, raw: bytes, role: str) -> dict:
    contract_name, record_id = record_key(data)
    return {
        "contract_name": contract_name,
        "schema_version": data["schema_version"],
        "record_id": record_id,
        "sha256": exact_raw_sha256(raw),
        "role": role,
    }


def iter_record_refs(node: object):
    if isinstance(node, dict):
        if {
            "contract_name",
            "schema_version",
            "record_id",
            "sha256",
            "role",
        }.issubset(node):
            yield node
        for value in node.values():
            yield from iter_record_refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from iter_record_refs(value)


def record_graph_findings(
    records: list[dict], raw_by_key: dict[tuple[str, str], bytes]
) -> list[str]:
    """Resolve every recordRef against exact UTF-8 file bytes and reject cycles."""

    by_key = {record_key(record): record for record in records}
    graph: dict[tuple[str, str], set[tuple[str, str]]] = {
        key: set() for key in by_key
    }
    findings: list[str] = []
    for record in records:
        source = record_key(record)
        for ref in iter_record_refs(record):
            target = (ref["contract_name"], ref["record_id"])
            if target not in by_key or target not in raw_by_key:
                findings.append("RECORD_REF_UNRESOLVED")
                continue
            if ref["sha256"] != exact_raw_sha256(raw_by_key[target]):
                findings.append("RECORD_REF_EXACT_RAW_SHA256_MISMATCH")
            graph[source].add(target)
            if source == target:
                findings.append("RECORD_REF_SELF_REFERENCE")

    visiting: set[tuple[str, str]] = set()
    visited: set[tuple[str, str]] = set()

    def cyclic(node: tuple[str, str]) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        found = any(cyclic(target) for target in graph[node])
        visiting.remove(node)
        visited.add(node)
        return found

    if any(cyclic(node) for node in graph):
        findings.append("RECORD_REF_GRAPH_CYCLIC")
    return sorted(set(findings))


def producer() -> dict:
    return {
        "skill_id": "wave0-contracts",
        "skill_version": "1.0",
        "tool_id": "synthetic-fixture-builder",
        "tool_version": "1.0",
        "generated_utc": NOW,
    }


def gates(
    *,
    blocked: bool = False,
    claim_ceiling: str = "technical_run_gates_only",
    maximum_action: str = "execute-approved-request",
) -> dict:
    return {
        "status": "blocked" if blocked else "pass",
        "maximum_action": "inspect-only" if blocked else maximum_action,
        "claim_ceiling": "no_positive_claim" if blocked else claim_ceiling,
        "checks": [
            {
                "check_id": "synthetic-gate",
                "status": "blocked" if blocked else "pass",
                "decisive": True,
                "finding_codes": ["missing-evidence"] if blocked else [],
                "evidence_refs": [record_ref("evidence-record", "evidence-001")],
                "validated_by": actor(),
                "validated_utc": NOW,
                "limitations": ["Synthetic fixture only."],
            }
        ],
    }


def review_gates() -> dict:
    def review_check(
        check_id: str,
        role: str,
    ) -> dict:
        return {
            "check_id": check_id,
            "status": "pass",
            "decisive": True,
            "finding_codes": [],
            "evidence_refs": [record_ref("evidence-record", f"{check_id}-evidence")],
            "validated_by": actor("deterministic-tool", f"{check_id}-actor", role),
            "validated_utc": NOW,
            "limitations": ["Synthetic pre-decision review-readiness fixture only."],
        }

    return {
        "status": "pass",
        "maximum_action": "eligible-for-expert-review",
        "claim_ceiling": "eligible_for_expert_review",
        "checks": [
            review_check("technical-completion", "technical-validator"),
            review_check("numerical-evidence", "numerical-validator"),
            review_check("expert-review-readiness", "review-readiness-validator"),
        ],
    }


def software_identity() -> dict:
    return {
        "software_id": "qe",
        "version": "7.5-synthetic",
        "build_id": "synthetic-build",
        "executable_sha256": SHA_A,
        "identity_status": "exact-match",
        "version_evidence": [file_ref("version-evidence", "qe-version.txt")],
        "capability_profile_id": "qe-profile-001",
    }


def resources() -> dict:
    return {
        "scheduler_profile_id": "local-profile-001",
        "nodes": 1,
        "mpi_ranks": 2,
        "threads_per_rank": 1,
        "gpus": 0,
        "memory_mb": 2048,
        "walltime_s": 600,
    }


def resource_ceiling() -> dict:
    data = resources()
    data.pop("scheduler_profile_id")
    return data


def calculation_envelope() -> dict:
    return {
        "schema_version": "1.0",
        "contract_name": "calculation-record-envelope",
        "record_id": "calculation-001",
        "domain": "periodic-dft",
        "record_kind": "run",
        "case_id": "case-001",
        "scientific_protocol_id": "protocol-001",
        "task_type": "single-point",
        "engine": software_identity(),
        "environment_profile_id": "env-profile-001",
        "payload_ref": record_ref("run-manifest", "payload-001", "payload"),
        "parent_records": [record_ref("structure-snapshot", "structure-001", "parent")],
        "inputs": [file_ref()],
        "outputs": [file_ref("main-output", "synthetic-output.log")],
        "status": {
            "native_status": "JOB DONE",
            "normalized_status": "completed",
            "scheduler_status": "succeeded",
            "process_status": "exited-zero",
            "application_status": "completed",
            "scientific_acceptance": "not_assessed",
        },
        "scientific_decision_ref": None,
        "gates": gates(),
        "limitations": ["Scientific acceptance has not been assessed."],
        "producer": producer(),
    }


def periodic_run_manifest(
    *,
    output_sha256: str = SHA_B,
    generated_utc: str = NOW,
) -> dict:
    return {
        "schema_version": "1.0",
        "record_id": "payload-001",
        "code": "qe",
        "code_version": "7.5-synthetic",
        "task_type": "single-point",
        "case_id": "case-001",
        "scientific_protocol_id": "protocol-001",
        "status": "completed",
        "scientific_acceptance": "not_assessed",
        "configuration": {
            "input_label": "synthetic-input.dat",
            "execution_record_id": "execution-001",
        },
        "metrics": {
            "wall_time_s": 30.0,
            "core_hours": 1.0 / 60.0,
            "queue_wait_s": 0.0,
            "peak_memory_mb": None,
            "retained_storage_mb": None,
            "scf_iterations": None,
            "ionic_steps": None,
            "restarts": 0,
        },
        "evidence": [
            {
                "role": "main-output",
                "label": "synthetic-output.log",
                "sha256": output_sha256,
                "status": "present",
            }
        ],
        "limitations": [
            "Technical completion and output evidence do not establish scientific acceptance."
        ],
        "provenance": {
            "collector": "synthetic-run-manifest-builder",
            "collector_version": "1.0",
            "generated_utc": generated_utc,
        },
    }


def review_ready_calculation_envelope() -> dict:
    data = calculation_envelope()
    data["status"]["scientific_acceptance"] = "requires_human_review"
    data["gates"] = review_gates()
    return data


def execution_request() -> dict:
    return {
        "schema_version": "1.0",
        "contract_name": "execution-request",
        "request_id": "request-001",
        "created_utc": NOW,
        "requested_by": actor("agent", "routing-agent"),
        "workflow_plan_ref": record_ref("workflow-plan", "plan-001", "workflow-plan"),
        "workflow_step_id": "step-001",
        "operation_id": "run-periodic-dft",
        "execution_mode": "execute",
        "command_kind": "argv",
        "shell": False,
        "argv": ["pw.x", "-in", "inputs/scf.in"],
        "working_directory_label": "campaign-001/run-001",
        "environment_profile_id": "env-profile-001",
        "resources": resources(),
        "inputs": [file_ref()],
        "expected_outputs": [file_ref("main-output", "synthetic-output.log", "missing")],
        "parent_records": [record_ref("calculation-record-envelope", "calculation-001", "plan")],
        "timeout_s": 900,
        "retry_policy": {
            "maximum_attempts": 1,
            "automatic_retry": False,
            "retryable_finding_codes": [],
        },
        "authorization_requirement": {
            "required": True,
            "side_effects": ["scheduler-submit"],
            "scope_labels": ["campaign-001/run-001"],
            "reason": "Run the synthetic staged calculation.",
        },
        "state": "prepared",
        "blocker_codes": [],
        "gates": gates(maximum_action="request-execution-authorization"),
        "producer": producer(),
    }


def execution_lease() -> dict:
    return {
        "schema_version": "1.0",
        "contract_name": "execution-lease",
        "lease_id": "lease-001",
        "request_ref": record_ref("execution-request", "request-001", "execution-request"),
        "authorization_decision_ref": record_ref(
            "decision-record", "decision-001", "execution-authorization"
        ),
        "issued_by": actor("deterministic-tool", "lease-issuer", "lease-issuer"),
        "issued_utc": NOW,
        "expires_utc": LATER,
        "lease_duration_s": 3600,
        "status": "active",
        "single_use": True,
        "grant": {
            "side_effects": ["scheduler-submit"],
            "environment_profile_ids": ["env-profile-001"],
            "scheduler_profile_ids": ["local-profile-001"],
            "argv_sha256": canonical_sha256(["pw.x", "-in", "inputs/scf.in"]),
            "input_sha256": [SHA_B],
            "output_labels": ["synthetic-output.log"],
            "resource_ceiling": resource_ceiling(),
            "maximum_executions": 1,
        },
        "constraints": ["Lease is bound to the immutable request hash."],
        "producer": producer(),
    }


def execution_record() -> dict:
    resource_data = resources()
    return {
        "schema_version": "1.0",
        "contract_name": "execution-record",
        "execution_id": "execution-001",
        "request_ref": record_ref("execution-request", "request-001", "execution-request"),
        "lease_ref": record_ref("execution-lease", "lease-001", "execution-lease"),
        "workflow_plan_ref": record_ref("workflow-plan", "plan-001", "workflow-plan"),
        "workflow_step_id": "step-001",
        "parent_records": [record_ref("calculation-record-envelope", "calculation-001", "plan")],
        "dry_run": False,
        "executor": actor("deterministic-tool", "execution-runner"),
        "engine": software_identity(),
        "environment_profile_id": "env-profile-001",
        "command_kind": "argv",
        "shell": False,
        "argv": ["pw.x", "-in", "inputs/scf.in"],
        "argv_sha256": canonical_sha256(["pw.x", "-in", "inputs/scf.in"]),
        "working_directory_label": "campaign-001/run-001",
        "resources": resource_data,
        "inputs": [file_ref()],
        "outputs": [file_ref("main-output", "synthetic-output.log")],
        "started_utc": NOW,
        "finished_utc": FINISHED,
        "timings": {"queue_wait_s": 0.0, "wall_time_s": 30.0, "cpu_time_s": 60.0, "gpu_time_s": None},
        "status": {
            "native_scheduler_status": "COMPLETED",
            "scheduler_status": "succeeded",
            "native_process_status": "exit 0",
            "process_status": "exited-zero",
            "native_application_status": "JOB DONE",
            "application_status": "completed",
            "normalized_status": "succeeded",
        },
        "return_code": 0,
        "tool_failure": {
            "occurred": False,
            "phase": "none",
            "finding_code": None,
            "detail": None,
            "evidence_refs": [],
        },
        "scientific_acceptance": "not_assessed",
        "claim_ceiling": "technical_run_gates_only",
        "gates": gates(),
        "limitations": ["Technical completion does not establish scientific acceptance."],
        "producer": producer(),
    }


def workflow_step() -> dict:
    return {
        "step_id": "step-001",
        "skill_id": "qe-rigorous-calculations",
        "operation_id": "audit-and-run-scf",
        "route_lifecycle": "active",
        "state": "ready",
        "execution_class": "scheduler",
        "dependencies": [],
        "input_records": [record_ref("structure-snapshot", "structure-001", "input")],
        "output_contracts": [
            {
                "contract_name": "calculation-record-envelope",
                "schema_version": "1.0",
                "role": "calculation-record",
                "required": True,
            }
        ],
        "calculation_envelope_ref": record_ref(
            "calculation-record-envelope", "calculation-001", "calculation-plan"
        ),
        "execution_request_ref": None,
        "maturity": {
            "implementation": "implemented",
            "validation": "synthetic-validated",
            "claim_ceiling": "input_gates_only",
        },
        "gates": gates(claim_ceiling="input_gates_only", maximum_action="request-execution-authorization"),
        "blocker_codes": [],
    }


def workflow_plan() -> dict:
    return {
        "schema_version": "1.0",
        "contract_name": "workflow-plan",
        "plan_id": "plan-001",
        "title": "Synthetic periodic DFT validation plan",
        "objective": "Validate an anonymized synthetic SCF workflow without asserting a scientific result.",
        "case_id": "case-001",
        "scientific_protocol_id": "protocol-001",
        "status": "ready",
        "domains": ["structure", "periodic-dft"],
        "source_records": [record_ref("structure-snapshot", "structure-001")],
        "steps": [workflow_step()],
        "authorization_policy": {
            "human_decision_required": True,
            "lease_required": True,
            "side_effects": ["scheduler-submit"],
            "scope_labels": ["campaign-001/run-001"],
        },
        "required_decisions": [],
        "scientific_acceptance": "not_assessed",
        "scientific_decision_ref": None,
        "claim_ceiling": "input_gates_only",
        "gates": gates(claim_ceiling="input_gates_only", maximum_action="request-execution-authorization"),
        "blocker_codes": [],
        "limitations": ["Execution still requires a separate human decision and lease."],
        "producer": producer(),
    }


def workflow_event() -> dict:
    return {
        "schema_version": "1.0",
        "contract_name": "workflow-event",
        "event_id": "event-001",
        "plan_ref": record_ref("workflow-plan", "plan-001", "workflow-plan"),
        "step_id": "step-001",
        "sequence": 4,
        "event_type": "scheduler-state-observed",
        "occurred_utc": NOW,
        "emitted_by": actor(),
        "observed_status": {
            "layer": "scheduler",
            "native_status": "COMPLETED",
            "normalized_status": "succeeded",
        },
        "related_records": [
            record_ref("execution-record", "execution-001", "execution-record")
        ],
        "evidence_ids": ["scheduler-log-001"],
        "evidence_refs": [record_ref("evidence-record", "scheduler-log-001", "scheduler-observation")],
        "finding_codes": [],
        "message": "The scheduler reported completion; application completion remains independently assessed.",
        "claim_ceiling": "technical_run_gates_only",
        "scientific_acceptance": "not_assessed",
        "producer": producer(),
    }


def decision_record(decision_type: str = "execution-authorization") -> dict:
    if decision_type == "scientific-acceptance":
        return {
            "schema_version": "1.0",
            "contract_name": "decision-record",
            "decision_id": "decision-002",
            "decision_type": decision_type,
            "subject_ref": record_ref(
                "claim-evidence-map", "claim-map-001", "scientific-subject"
            ),
            "outcome": "accepted",
            "scientific_acceptance": "accepted",
            "decided_by": actor("human", "scientific-reviewer"),
            "decided_utc": NOW,
            "evidence_ids": ["claim-map-001"],
            "evidence_refs": [record_ref("claim-evidence-map", "claim-map-001", "evidence")],
            "rationale": "A human reviewer accepted only the explicitly mapped synthetic claim.",
            "scope_labels": ["synthetic-claim-set"],
            "valid_until_utc": None,
            "claim_ceiling": "eligible_for_expert_review",
            "limitations": ["Synthetic acceptance fixture only."],
            "producer": producer(),
        }
    return {
        "schema_version": "1.0",
        "contract_name": "decision-record",
        "decision_id": "decision-001",
        "decision_type": decision_type,
        "subject_ref": record_ref("execution-request", "request-001", "execution-subject"),
        "outcome": "approved",
        "scientific_acceptance": "not_assessed",
        "decided_by": actor("human", "request-owner"),
        "decided_utc": NOW,
        "evidence_ids": ["request-001"],
        "evidence_refs": [record_ref("execution-request", "request-001", "evidence")],
        "rationale": "Approve the exact synthetic request under the stated resource ceiling.",
        "scope_labels": ["campaign-001/run-001"],
        "valid_until_utc": LATER,
        "claim_ceiling": "input_gates_only",
        "limitations": ["This decision is not scientific acceptance."],
        "producer": producer(),
    }


def claim_map() -> dict:
    return {
        "schema_version": "1.0",
        "contract_name": "claim-evidence-map",
        "map_id": "claim-map-001",
        "subject_records": [record_ref("execution-record", "execution-001", "subject")],
        "status": "complete",
        "claim_ceiling": "technical_run_gates_only",
        "scientific_acceptance": "not_assessed",
        "scientific_decision_ref": None,
        "evidence": [
            {
                "evidence_id": "evidence-001",
                "kind": "record",
                "record_ref": record_ref("execution-record", "execution-001", "evidence"),
                "file_ref": None,
                "status": "present",
                "limitations": ["Supports technical execution status only."],
            }
        ],
        "gates": gates()["checks"],
        "claims": [
            {
                "claim_id": "claim-001",
                "statement": "The synthetic process exited with return code zero and the application completion gate passed.",
                "claim_level": "technical_run_gates_only",
                "status": "supported",
                "evidence_ids": ["evidence-001"],
                "gate_ids": ["synthetic-gate"],
                "blocker_codes": [],
            }
        ],
        "limitations": ["No scientific property is accepted by this map."],
        "producer": producer(),
    }


def accepted_claim_map() -> dict:
    data = claim_map()
    data["map_id"] = "claim-map-accepted-001"
    data["subject_records"] = [
        record_ref("claim-evidence-map", "claim-map-001", "scientific-candidate")
    ]
    data["claim_ceiling"] = "eligible_for_expert_review"
    data["scientific_acceptance"] = "accepted"
    data["scientific_decision_ref"] = record_ref(
        "decision-record", "decision-002", "scientific-acceptance"
    )
    data["claims"][0]["claim_level"] = "eligible_for_expert_review"
    data["limitations"] = [
        "Acceptance is represented only by the separate, hash-linked human decision."
    ]
    return data


def semantic_findings(kind: str, data: dict, context: dict | None = None) -> list[str]:
    """Minimal executable oracle for relationships JSON Schema cannot express.

    Production validators must implement the same stable obligations advertised by
    each schema. This test oracle deliberately consumes only synthetic records.
    """

    context = context or {}
    findings: list[str] = []

    if kind == "execution-lease":
        issued = datetime.fromisoformat(data["issued_utc"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(data["expires_utc"].replace("Z", "+00:00"))
        duration = int((expires - issued).total_seconds())
        if duration <= 0 or duration != data["lease_duration_s"]:
            findings.append("LEASE_TIME_ORDER")

        request = context.get("request")
        decision = context.get("decision")
        record_hashes = context.get("record_hashes", {})
        if request is not None:
            grant = data["grant"]
            expected_request_hash = record_hashes.get(
                ("execution-request", request["request_id"])
            )
            if (
                expected_request_hash is not None
                and data["request_ref"]["sha256"] != expected_request_hash
            ):
                findings.append("LEASE_REQUEST_REF_HASH_MATCH")
            if grant["argv_sha256"] != canonical_sha256(request["argv"]):
                findings.append("LEASE_ARGV_HASH_MATCH")
            request_hashes = {
                item["sha256"] for item in request["inputs"] if item["availability"] == "present"
            }
            if not set(grant["input_sha256"]).issubset(request_hashes):
                findings.append("LEASE_INPUT_HASH_SET_SUBSET")
            if not set(grant["environment_profile_ids"]).issubset(
                {request["environment_profile_id"]}
            ):
                findings.append("LEASE_ENVIRONMENT_PROFILE_SUBSET")
            scheduler_id = request["resources"]["scheduler_profile_id"]
            allowed_scheduler = {scheduler_id} if scheduler_id is not None else set()
            if not set(grant["scheduler_profile_ids"]).issubset(allowed_scheduler):
                findings.append("LEASE_SCHEDULER_PROFILE_SUBSET")
            requested_resources = request["resources"]
            if any(
                grant["resource_ceiling"][name] > requested_resources[name]
                for name in ("nodes", "mpi_ranks", "threads_per_rank", "gpus", "memory_mb", "walltime_s")
            ):
                findings.append("LEASE_RESOURCE_CEILING_SUBSET")
            requested_effects = set(request["authorization_requirement"]["side_effects"])
            if not set(grant["side_effects"]).issubset(requested_effects):
                findings.append("LEASE_SIDE_EFFECT_SUBSET")
            requested_outputs = {item["label"] for item in request["expected_outputs"]}
            if not set(grant["output_labels"]).issubset(requested_outputs):
                findings.append("LEASE_OUTPUT_LABEL_SET_SUBSET")
        if decision is not None:
            subject = decision["subject_ref"]
            request_ref = data["request_ref"]
            decision_ref = data["authorization_decision_ref"]
            expected_decision_hash = record_hashes.get(
                ("decision-record", decision["decision_id"])
            )
            if (
                expected_decision_hash is not None
                and decision_ref["sha256"] != expected_decision_hash
            ):
                findings.append("LEASE_AUTHORIZATION_DECISION_REF_HASH_MATCH")
            requested_scopes = set(
                request["authorization_requirement"]["scope_labels"]
            ) if request is not None else set()
            decision_matches = (
                decision["decision_type"] == "execution-authorization"
                and decision["outcome"] == "approved"
                and decision["decided_by"]["actor_type"] == "human"
                and decision["decision_id"] == decision_ref["record_id"]
                and requested_scopes.issubset(set(decision["scope_labels"]))
                and subject["contract_name"] == request_ref["contract_name"]
                and subject["schema_version"] == request_ref["schema_version"]
                and subject["record_id"] == request_ref["record_id"]
                and subject["sha256"] == request_ref["sha256"]
            )
            if not decision_matches:
                findings.append("LEASE_AUTHORIZATION_DECISION_APPROVED_REQUEST_MATCH")
            request_created = datetime.fromisoformat(
                request["created_utc"].replace("Z", "+00:00")
            ) if request is not None else None
            decided = datetime.fromisoformat(decision["decided_utc"].replace("Z", "+00:00"))
            valid_until_raw = decision["valid_until_utc"]
            valid_until = (
                datetime.fromisoformat(valid_until_raw.replace("Z", "+00:00"))
                if valid_until_raw is not None
                else None
            )
            if request_created is None or not (
                request_created <= decided <= issued < expires
                and (valid_until is None or expires <= valid_until)
            ):
                findings.append("LEASE_AUTHORIZATION_TIME_CHAIN")
        executions = context.get("execution_records")
        if executions is not None:
            consumers = [
                item
                for item in executions
                if item.get("lease_ref") is not None
                and item["lease_ref"]["record_id"] == data["lease_id"]
            ]
            if len(consumers) > data["grant"]["maximum_executions"]:
                findings.append("LEASE_SINGLE_USE_CONSUMPTION")
        if context.get("resolve_all_refs") and record_graph_findings(
            context.get("record_bundle", []), context.get("raw_by_key", {})
        ):
            findings.append("LEASE_RECORD_REF_DAG_ACYCLIC")

    elif kind == "calculation-record-envelope":
        payload_contracts = context.get(
            "domain_payload_contracts", {"periodic-dft": {"run-manifest"}}
        )
        allowed_contracts = payload_contracts.get(data["domain"])
        if (
            not allowed_contracts
            or data["payload_ref"]["contract_name"] not in allowed_contracts
        ):
            findings.append("CALC_DOMAIN_PAYLOAD_CONTRACT_MATCH")
        payload = context.get("payload")
        if payload is not None:
            record_hashes = context.get("record_hashes", {})
            expected_hash = record_hashes.get(record_key(payload))
            if (
                data["payload_ref"]["record_id"] != payload["record_id"]
                or expected_hash is None
                or data["payload_ref"]["sha256"] != expected_hash
            ):
                findings.append("CALC_PAYLOAD_REF_HASH_RESOLVES")
            if data["engine"]["software_id"] != payload["code"]:
                findings.append("CALC_ENGINE_PAYLOAD_ID_MATCH")
            if (
                data["status"]["normalized_status"] == "completed"
                and payload["status"] != "completed"
            ) or (
                data["status"]["scientific_acceptance"]
                == "requires_human_review"
                and payload["scientific_acceptance"] != "not_assessed"
            ):
                findings.append("CALC_PAYLOAD_STATUS_SUPPORTS_ENVELOPE")
        if context.get("resolve_all_refs"):
            record_hashes = context.get("record_hashes", {})
            if any(
                record_hashes.get((ref["contract_name"], ref["record_id"]))
                != ref["sha256"]
                for ref in data["parent_records"]
            ):
                findings.append("CALC_PARENT_LINEAGE_RESOLVES")
            gate_refs = [
                ref
                for check in data["gates"]["checks"]
                for ref in check["evidence_refs"]
            ]
            if any(
                record_hashes.get((ref["contract_name"], ref["record_id"]))
                != ref["sha256"]
                for ref in gate_refs
            ):
                findings.append("CALC_GATE_EVIDENCE_REFS_RESOLVE")
            if record_graph_findings(
                context.get("record_bundle", []), context.get("raw_by_key", {})
            ):
                findings.append("CALC_RECORD_REF_DAG_ACYCLIC")

    elif kind == "claim-evidence-map":
        evidence_by_id: dict[str, dict] = {}
        for item in data["evidence"]:
            evidence_id = item["evidence_id"]
            if evidence_id in evidence_by_id:
                findings.append("CLAIM_EVIDENCE_IDS_UNIQUE")
            evidence_by_id[evidence_id] = item
        gates_by_id: dict[str, dict] = {}
        for item in data["gates"]:
            gate_id = item["check_id"]
            if gate_id in gates_by_id:
                findings.append("CLAIM_GATE_IDS_UNIQUE")
            gates_by_id[gate_id] = item
        for claim in data["claims"]:
            if claim["status"] != "supported":
                continue
            for evidence_id in claim["evidence_ids"]:
                item = evidence_by_id.get(evidence_id)
                present_and_hashed = False
                if item is not None and item["status"] == "present":
                    ref = item["record_ref"] if item["kind"] == "record" else item["file_ref"]
                    present_and_hashed = (
                        ref is not None
                        and isinstance(ref.get("sha256"), str)
                        and len(ref["sha256"]) == 64
                        and (item["kind"] == "record" or ref["availability"] == "present")
                    )
                if not present_and_hashed:
                    findings.append("CLAIM_SUPPORTED_EVIDENCE_IDS_RESOLVE_PRESENT_HASHED")
            for gate_id in claim["gate_ids"]:
                gate = gates_by_id.get(gate_id)
                if gate is None or gate["status"] != "pass":
                    findings.append("CLAIM_SUPPORTED_GATE_IDS_RESOLVE_PASSING")
        decision = context.get("decision")
        record_hashes = context.get("record_hashes", {})
        acceptance = data["scientific_acceptance"]
        if acceptance in {"accepted", "rejected"} and decision is None:
            findings.append("CLAIM_SCIENTIFIC_DECISION_CANDIDATE_HASH_OUTCOME_MATCH")
        elif acceptance in {"accepted", "rejected"}:
            subject = decision["subject_ref"]
            subject_key = (subject["contract_name"], subject["record_id"])
            expected_subject_hash = record_hashes.get(subject_key)
            expected_decision_hash = record_hashes.get(
                ("decision-record", decision["decision_id"])
            )
            mapped_subjects = {
                (
                    ref["contract_name"],
                    ref["schema_version"],
                    ref["record_id"],
                    ref["sha256"],
                )
                for ref in data["subject_records"]
            }
            decision_ref = data["scientific_decision_ref"]
            matches = (
                decision["decision_type"] == "scientific-acceptance"
                and decision["outcome"] == acceptance
                and decision["scientific_acceptance"] == acceptance
                and decision["decided_by"]["actor_type"] == "human"
                and subject["schema_version"] == "1.0"
                and expected_subject_hash is not None
                and subject["sha256"] == expected_subject_hash
                and (
                    subject["contract_name"],
                    subject["schema_version"],
                    subject["record_id"],
                    subject["sha256"],
                ) in mapped_subjects
                and decision_ref is not None
                and decision_ref["record_id"] == decision["decision_id"]
                and expected_decision_hash is not None
                and decision_ref["sha256"] == expected_decision_hash
                and data["map_id"] != subject["record_id"]
            )
            if not matches:
                findings.append("CLAIM_SCIENTIFIC_DECISION_CANDIDATE_HASH_OUTCOME_MATCH")
        if context.get("resolve_all_refs") and record_graph_findings(
            context.get("record_bundle", []), context.get("raw_by_key", {})
        ):
            findings.append("CLAIM_RECORD_REF_DAG_ACYCLIC")

    elif kind == "workflow-plan":
        steps = data["steps"]
        ids = [step["step_id"] for step in steps]
        if len(ids) != len(set(ids)):
            findings.append("WORKFLOW_STEP_IDS_UNIQUE")
        id_set = set(ids)
        if any(dep not in id_set for step in steps for dep in step["dependencies"]):
            findings.append("WORKFLOW_DEPENDENCIES_RESOLVE")

        graph = {step["step_id"]: list(step["dependencies"]) for step in steps}
        visiting: set[str] = set()
        visited: set[str] = set()

        def has_cycle(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            cyclic = any(dep in graph and has_cycle(dep) for dep in graph.get(node, []))
            visiting.remove(node)
            visited.add(node)
            return cyclic

        if any(has_cycle(node) for node in graph):
            findings.append("WORKFLOW_DAG_ACYCLIC")

        known_operations = context.get("known_operations", set())
        if any(
            step["route_lifecycle"] == "active"
            and (step["skill_id"], step["operation_id"]) not in known_operations
            for step in steps
        ):
            findings.append("WORKFLOW_ROUTE_OPERATION_ACTIVE_MATCH")

        effects = set(data["authorization_policy"]["side_effects"])
        required_effect = {
            "authorized-local": "local-execution",
            "authorized-remote": "remote-write",
            "scheduler": "scheduler-submit",
        }
        if any(
            step["execution_class"] in required_effect
            and required_effect[step["execution_class"]] not in effects
            for step in steps
        ):
            findings.append("WORKFLOW_AUTHORIZATION_SIDE_EFFECT_ALIGNMENT")
        step_by_id = {step["step_id"]: step for step in steps}
        for step in steps:
            input_contracts = {
                (ref["contract_name"], ref["role"])
                for ref in step["input_records"]
            }
            for dependency_id in step["dependencies"]:
                dependency = step_by_id.get(dependency_id)
                if dependency is None:
                    continue
                required_outputs = {
                    (item["contract_name"], item["role"])
                    for item in dependency["output_contracts"]
                    if item["required"]
                }
                if not required_outputs.issubset(input_contracts):
                    findings.append("WORKFLOW_OUTPUT_HANDOFF_REFS_RESOLVE")
        if context.get("resolve_all_refs") and record_graph_findings(
            context.get("record_bundle", []), context.get("raw_by_key", {})
        ):
            findings.append("WORKFLOW_RECORD_REF_DAG_ACYCLIC")

    elif kind == "execution-request":
        workflow = context.get("workflow")
        templates = context.get("operation_templates", {})
        record_hashes = context.get("record_hashes", {})
        if workflow is not None:
            expected_plan_hash = record_hashes.get(
                ("workflow-plan", workflow["plan_id"])
            )
            if (
                expected_plan_hash is not None
                and data["workflow_plan_ref"]["sha256"] != expected_plan_hash
            ):
                findings.append("REQUEST_WORKFLOW_PLAN_REF_HASH_MATCH")
            step = next(
                (item for item in workflow["steps"] if item["step_id"] == data["workflow_step_id"]),
                None,
            )
            if step is None:
                findings.append("REQUEST_WORKFLOW_STEP_REF_RESOLVES")
            elif step["operation_id"] != data["operation_id"] or step["route_lifecycle"] != "active":
                findings.append("REQUEST_OPERATION_ROUTE_BINDING")
            policy = workflow["authorization_policy"]
            requirement = data["authorization_requirement"]
            if (
                requirement["required"]
                != (policy["human_decision_required"] and policy["lease_required"])
                or not set(requirement["side_effects"]).issubset(
                    set(policy["side_effects"])
                )
                or not set(requirement["scope_labels"]).issubset(
                    set(policy["scope_labels"])
                )
            ):
                findings.append("REQUEST_AUTHORIZATION_POLICY_MATCH")
        expected_argv = templates.get(data["operation_id"])
        if expected_argv is None or data["argv"] != expected_argv:
            findings.append("REQUEST_ARGV_TEMPLATE_BINDING")
        if context.get("resolve_all_refs"):
            record_hashes = context.get("record_hashes", {})
            if any(
                record_hashes.get((ref["contract_name"], ref["record_id"]))
                != ref["sha256"]
                for ref in data["parent_records"]
            ):
                findings.append("REQUEST_PARENT_LINEAGE_RESOLVES")
            file_hashes = context.get("file_hashes", {})
            if any(
                item["availability"] == "present"
                and file_hashes.get(item["label"]) != item["sha256"]
                for item in data["inputs"]
            ):
                findings.append("REQUEST_INPUT_HASH_CONTENT_MATCHES")
            if record_graph_findings(
                context.get("record_bundle", []), context.get("raw_by_key", {})
            ):
                findings.append("REQUEST_RECORD_REF_DAG_ACYCLIC")

    elif kind == "execution-record":
        if data["argv_sha256"] != canonical_sha256(data["argv"]):
            findings.append("EXEC_ARGV_HASH_MATCH")
        if data["dry_run"]:
            if any(
                value is not None
                for value in (
                    data["started_utc"],
                    data["finished_utc"],
                    data["timings"]["queue_wait_s"],
                    data["timings"]["wall_time_s"],
                    data["timings"]["cpu_time_s"],
                    data["timings"]["gpu_time_s"],
                )
            ):
                findings.append("EXEC_TIME_ORDER_AND_TIMINGS_MATCH")
        else:
            started = datetime.fromisoformat(data["started_utc"].replace("Z", "+00:00"))
            finished_raw = data["finished_utc"]
            finished = (
                datetime.fromisoformat(finished_raw.replace("Z", "+00:00"))
                if finished_raw is not None
                else None
            )
            wall_time = data["timings"]["wall_time_s"]
            terminal = data["status"]["normalized_status"] in {
                "succeeded", "failed", "timed-out", "cancelled"
            }
            timing_matches = (
                (not terminal and finished is None)
                or (
                    terminal
                    and finished is not None
                    and started <= finished
                    and wall_time is not None
                    and abs(wall_time - (finished - started).total_seconds()) < 1e-9
                )
            )
            if not timing_matches:
                findings.append("EXEC_TIME_ORDER_AND_TIMINGS_MATCH")
            cpu_time = data["timings"]["cpu_time_s"]
            gpu_time = data["timings"]["gpu_time_s"]
            resources_used = data["resources"]
            allocated_cpu_seconds = (
                wall_time
                * resources_used["nodes"]
                * resources_used["mpi_ranks"]
                * resources_used["threads_per_rank"]
            ) if wall_time is not None else None
            cpu_consistent = (
                cpu_time is None
                or (
                    allocated_cpu_seconds is not None
                    and cpu_time <= allocated_cpu_seconds + 1e-9
                )
            )
            gpu_consistent = (
                (resources_used["gpus"] == 0 and gpu_time is None)
                or (
                    resources_used["gpus"] > 0
                    and (
                        gpu_time is None
                        or (
                            wall_time is not None
                            and gpu_time <= wall_time * resources_used["gpus"] + 1e-9
                        )
                    )
                )
            )
            if not cpu_consistent or not gpu_consistent:
                findings.append("EXEC_TIME_ORDER_AND_TIMINGS_MATCH")

            request = context.get("request")
            lease = context.get("lease")
            workflow = context.get("workflow")
            record_hashes = context.get("record_hashes", {})
            if request is not None and lease is not None:
                expected_request_hash = record_hashes.get(
                    ("execution-request", request["request_id"])
                )
                if (
                    expected_request_hash is not None
                    and data["request_ref"]["sha256"] != expected_request_hash
                ):
                    findings.append("EXEC_REQUEST_REF_HASH_MATCH")
                expected_lease_hash = record_hashes.get(
                    ("execution-lease", lease["lease_id"])
                )
                lease_request = lease["request_ref"]
                active_request_match = (
                    lease["status"] == "active"
                    and lease_request["contract_name"] == data["request_ref"]["contract_name"]
                    and lease_request["record_id"] == data["request_ref"]["record_id"]
                    and lease_request["sha256"] == data["request_ref"]["sha256"]
                    and (
                        expected_lease_hash is None
                        or data["lease_ref"]["sha256"] == expected_lease_hash
                    )
                )
                if not active_request_match:
                    findings.append("EXEC_LEASE_ACTIVE_REQUEST_MATCH")

                if (
                    data["argv"] != request["argv"]
                    or data["argv_sha256"] != lease["grant"]["argv_sha256"]
                ):
                    findings.append("EXEC_ARGV_HASH_MATCH")

                grant = lease["grant"]
                input_hashes = {
                    item["sha256"] for item in data["inputs"]
                    if item["availability"] == "present"
                }
                output_labels = {item["label"] for item in data["outputs"]}
                ceiling = grant["resource_ceiling"]
                scope_matches = (
                    data["environment_profile_id"] in grant["environment_profile_ids"]
                    and (
                        data["resources"]["scheduler_profile_id"] is None
                        or data["resources"]["scheduler_profile_id"]
                        in grant["scheduler_profile_ids"]
                    )
                    and input_hashes.issubset(set(grant["input_sha256"]))
                    and output_labels.issubset(set(grant["output_labels"]))
                    and all(
                        data["resources"][name] <= ceiling[name]
                        for name in (
                            "nodes", "mpi_ranks", "threads_per_rank", "gpus",
                            "memory_mb", "walltime_s",
                        )
                    )
                )
                if not scope_matches:
                    findings.append("EXEC_GRANTED_SCOPE_SUBSET")
                request_input_hashes = {
                    item["sha256"] for item in request["inputs"]
                    if item["availability"] == "present"
                }
                expected_output_labels = {
                    item["label"] for item in request["expected_outputs"]
                }
                request_content_matches = (
                    data["working_directory_label"]
                    == request["working_directory_label"]
                    and data["environment_profile_id"]
                    == request["environment_profile_id"]
                    and input_hashes.issubset(request_input_hashes)
                    and output_labels.issubset(expected_output_labels)
                    and all(
                        data["resources"][name] <= request["resources"][name]
                        for name in (
                            "nodes", "mpi_ranks", "threads_per_rank", "gpus",
                            "memory_mb", "walltime_s",
                        )
                    )
                )
                if not request_content_matches:
                    findings.append("EXEC_REQUEST_CONTENT_MATCH")
                if data["workflow_step_id"] != request["workflow_step_id"]:
                    findings.append("EXEC_WORKFLOW_STEP_MATCH")
                created = datetime.fromisoformat(request["created_utc"].replace("Z", "+00:00"))
                issued = datetime.fromisoformat(lease["issued_utc"].replace("Z", "+00:00"))
                expires = datetime.fromisoformat(lease["expires_utc"].replace("Z", "+00:00"))
                if not (
                    created <= issued <= started
                    and (finished is None or finished <= expires)
                ):
                    findings.append("EXEC_REQUEST_LEASE_EXECUTION_TIME_CHAIN")
            if workflow is not None:
                expected_plan_hash = record_hashes.get(
                    ("workflow-plan", workflow["plan_id"])
                )
                if (
                    expected_plan_hash is not None
                    and data["workflow_plan_ref"]["sha256"] != expected_plan_hash
                ):
                    findings.append("EXEC_WORKFLOW_PLAN_REF_HASH_MATCH")
                if not any(
                    step["step_id"] == data["workflow_step_id"]
                    for step in workflow["steps"]
                ):
                    findings.append("EXEC_WORKFLOW_STEP_MATCH")
            if context.get("resolve_all_refs"):
                file_hashes = context.get("file_hashes", {})
                present_files = [
                    item for item in data["inputs"] + data["outputs"]
                    if item["availability"] == "present"
                ]
                if any(
                    file_hashes.get(item["label"]) != item["sha256"]
                    for item in present_files
                ):
                    findings.append("EXEC_INPUT_OUTPUT_HASH_CONTENT_MATCH")
                record_hashes = context.get("record_hashes", {})
                if any(
                    record_hashes.get((ref["contract_name"], ref["record_id"]))
                    != ref["sha256"]
                    for ref in data["parent_records"]
                ):
                    findings.append("EXEC_PARENT_LINEAGE_RESOLVES")
                native_evidence = context.get("native_status_evidence", {})
                native_pairs = {
                    "scheduler": data["status"]["native_scheduler_status"],
                    "process": data["status"]["native_process_status"],
                    "application": data["status"]["native_application_status"],
                }
                if any(
                    observed is not None
                    and native_evidence.get(layer) != observed
                    for layer, observed in native_pairs.items()
                ):
                    findings.append("EXEC_NATIVE_STATUS_EVIDENCE_MATCH")
                if record_graph_findings(
                    context.get("record_bundle", []), context.get("raw_by_key", {})
                ):
                    findings.append("EXEC_RECORD_REF_DAG_ACYCLIC")

    elif kind == "decision-record":
        evidence_record_ids = {ref["record_id"] for ref in data["evidence_refs"]}
        if any(evidence_id not in evidence_record_ids for evidence_id in data["evidence_ids"]):
            findings.append("DECISION_EVIDENCE_IDS_RESOLVE")
        record_hashes = context.get("record_hashes", {})
        subject = data["subject_ref"]
        expected_subject_hash = record_hashes.get(
            (subject["contract_name"], subject["record_id"])
        )
        if (
            expected_subject_hash is not None
            and subject["sha256"] != expected_subject_hash
        ):
            findings.append("DECISION_SUBJECT_REF_HASH_RESOLVES")
        if data["decision_type"] == "execution-authorization":
            request = context.get("request")
            if request is not None:
                required_scopes = set(
                    request["authorization_requirement"]["scope_labels"]
                )
                created = datetime.fromisoformat(
                    request["created_utc"].replace("Z", "+00:00")
                )
                decided = datetime.fromisoformat(
                    data["decided_utc"].replace("Z", "+00:00")
                )
                valid_until = datetime.fromisoformat(
                    data["valid_until_utc"].replace("Z", "+00:00")
                )
                subject_matches = (
                    subject["contract_name"] == "execution-request"
                    and subject["record_id"] == request["request_id"]
                    and expected_subject_hash is not None
                    and subject["sha256"] == expected_subject_hash
                    and required_scopes.issubset(set(data["scope_labels"]))
                    and created <= decided < valid_until
                )
                if not subject_matches:
                    findings.append("DECISION_AUTHORIZATION_REQUEST_SCOPE_MATCH")
        if data["decision_type"] == "scientific-acceptance":
            records_by_key = context.get("records_by_key", {})
            candidate = records_by_key.get(
                (subject["contract_name"], subject["record_id"])
            )
            candidate_ready = False
            if candidate is not None:
                if subject["contract_name"] == "calculation-record-envelope":
                    candidate_ready = (
                        candidate["status"]["scientific_acceptance"]
                        == "requires_human_review"
                    )
                elif subject["contract_name"] == "claim-evidence-map":
                    candidate_ready = (
                        candidate["scientific_acceptance"]
                        == "requires_human_review"
                        and candidate["claim_ceiling"]
                        == "eligible_for_expert_review"
                    )
            if context.get("resolve_all_refs") and not candidate_ready:
                findings.append("DECISION_SCIENTIFIC_SUBJECT_HASH_OUTCOME_MATCH")
        if context.get("resolve_all_refs"):
            record_hashes = context.get("record_hashes", {})
            if any(
                record_hashes.get((ref["contract_name"], ref["record_id"]))
                != ref["sha256"]
                for ref in data["evidence_refs"]
            ):
                findings.append("DECISION_EVIDENCE_IDS_RESOLVE")
            record_times = context.get("record_times", {})
            decided = datetime.fromisoformat(
                data["decided_utc"].replace("Z", "+00:00")
            )
            refs = [data["subject_ref"], *data["evidence_refs"]]
            if any(
                (timestamp := record_times.get((ref["contract_name"], ref["record_id"])))
                is None
                or timestamp > decided
                for ref in refs
            ):
                findings.append("DECISION_REFS_PREEXIST_DECISION")
            if record_graph_findings(
                context.get("record_bundle", []), context.get("raw_by_key", {})
            ):
                findings.append("DECISION_RECORD_REF_DAG_ACYCLIC")

    elif kind == "workflow-event":
        evidence_record_ids = {ref["record_id"] for ref in data["evidence_refs"]}
        if any(evidence_id not in evidence_record_ids for evidence_id in data["evidence_ids"]):
            findings.append("EVENT_EVIDENCE_IDS_RESOLVE")

        expected_related = {
            "execution-requested": ("execution-request", "execution-request"),
            "lease-issued": ("execution-lease", "execution-lease"),
            "scheduler-submitted": ("execution-record", "execution-record"),
            "scheduler-state-observed": ("execution-record", "execution-record"),
            "process-state-observed": ("execution-record", "execution-record"),
            "application-state-observed": ("execution-record", "execution-record"),
            "decision-recorded": ("decision-record", "decision-record"),
            "artifact-produced": ("artifact-manifest", "artifact"),
        }
        expected = expected_related.get(data["event_type"])
        status_by_event = {
            "scheduler-submitted": {"submitted"},
            "scheduler-state-observed": {
                "submitted", "queued", "running", "succeeded", "failed", "cancelled", "unknown"
            },
            "process-state-observed": {
                "running", "succeeded", "failed", "timed-out", "cancelled", "unknown"
            },
            "application-state-observed": {
                "running", "completed", "incomplete", "failed", "unknown"
            },
            "execution-requested": {"submitted"},
            "lease-issued": {"approved"},
            "decision-recorded": {"approved", "denied"},
            "artifact-produced": {"produced"},
        }
        related_matches = expected is None or any(
            ref["contract_name"] == expected[0] and ref["role"] == expected[1]
            for ref in data["related_records"]
        )
        status_matches = (
            data["event_type"] not in status_by_event
            or data["observed_status"]["normalized_status"] in status_by_event[data["event_type"]]
        )
        if not related_matches or not status_matches:
            findings.append("EVENT_TYPE_RELATED_RECORD_STATUS_MATCH")

        workflow = context.get("workflow")
        if workflow is not None:
            plan_ref = data["plan_ref"]
            record_hashes = context.get("record_hashes", {})
            plan_matches = (
                plan_ref["record_id"] == workflow["plan_id"]
                and (
                    not record_hashes
                    or plan_ref["sha256"]
                    == record_hashes.get(("workflow-plan", workflow["plan_id"]))
                )
                and (
                    data["step_id"] is None
                    or any(
                        step["step_id"] == data["step_id"]
                        for step in workflow["steps"]
                    )
                )
            )
            if not plan_matches:
                findings.append("EVENT_PLAN_STEP_REF_RESOLVES")
        prior_events = context.get("prior_events")
        if prior_events is not None and any(
            event["plan_ref"]["record_id"] == data["plan_ref"]["record_id"]
            and event["sequence"] >= data["sequence"]
            for event in prior_events
        ):
            findings.append("EVENT_SEQUENCE_MONOTONIC")
        if context.get("resolve_all_refs"):
            record_hashes = context.get("record_hashes", {})
            if any(
                record_hashes.get((ref["contract_name"], ref["record_id"]))
                != ref["sha256"]
                for ref in data["related_records"]
            ):
                findings.append("EVENT_RELATED_RECORD_HASH_RESOLVES")
            related_record = context.get("related_record")
            if related_record is not None and data["observed_status"]["layer"] in {
                "scheduler", "process", "application"
            }:
                layer = data["observed_status"]["layer"]
                native_key = f"native_{layer}_status"
                normalized_key = f"{layer}_status"
                normalized = related_record["status"][normalized_key]
                normalized_alias = {
                    "exited-zero": "succeeded",
                    "exited-nonzero": "failed",
                    "signalled": "failed",
                }.get(normalized, normalized)
                if (
                    data["observed_status"]["native_status"]
                    != related_record["status"][native_key]
                    or data["observed_status"]["normalized_status"]
                    != normalized_alias
                ):
                    findings.append("EVENT_NATIVE_STATUS_EVIDENCE_MATCH")
            if record_graph_findings(
                context.get("record_bundle", []), context.get("raw_by_key", {})
            ):
                findings.append("EVENT_RECORD_REF_DAG_ACYCLIC")

    return sorted(set(findings))


class Wave0ExecutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas: dict[str, dict] = {}
        registry = Registry()
        for path in sorted(CONTRACTS.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            if "$id" in schema:
                registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
            cls.schemas[path.stem.removesuffix(".schema")] = schema
        cls.registry = registry

    def errors(self, schema_name: str, instance: object) -> list[str]:
        validator = Draft202012Validator(
            self.schemas[schema_name],
            registry=self.registry,
            format_checker=FormatChecker(),
        )
        return [
            f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
            for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
        ]

    def assert_valid(self, schema_name: str, instance: object) -> None:
        self.assertEqual(self.errors(schema_name, instance), [])

    def assert_invalid(self, schema_name: str, instance: object) -> None:
        self.assertTrue(self.errors(schema_name, instance))

    def test_production_evaluator_requires_canonical_versioned_identity_and_data_wrappers(self) -> None:
        target_sha = "c" * 64
        target_identity = ("run-manifest", "1.0", "run-canonical-001")
        target = {
            "data": {
                "schema_version": "1.0",
                "record_id": "run-canonical-001",
                "code": "qe",
            },
            "raw_sha256": target_sha,
            "index": 0,
            "lifecycle": "active",
            "integrity_verified_active": True,
        }
        current_data = {
            "contract_name": "calculation-record-envelope",
            "schema_version": "1.0",
            "record_id": "calculation-canonical-001",
            "payload_ref": {
                "contract_name": "run-manifest",
                "schema_version": "1.0",
                "record_id": "run-canonical-001",
                "sha256": target_sha,
                "role": "payload",
            },
        }
        current = {
            "data": current_data,
            "raw_sha256": "d" * 64,
            "index": 1,
            "lifecycle": "active",
            "integrity_verified_active": True,
        }

        def context(records: dict) -> dict:
            return {
                "current_record": current,
                "current_record_index": 1,
                "records_by_identity": records,
                "artifacts_by_label": {},
                "core_checks": {},
                "registry_snapshots": {},
            }

        result = evaluate_execution_semantics(
            ["CALC_PAYLOAD_REF_HASH_RESOLVES"],
            context({target_identity: target}),
        )[0]
        self.assertEqual(result["status"], "pass")

        mismatched_index_context = context({target_identity: target})
        mismatched_index_context["current_record_index"] = 2
        result = evaluate_execution_semantics(
            ["CALC_PAYLOAD_REF_HASH_RESOLVES"], mismatched_index_context
        )[0]
        self.assertEqual(result["status"], "blocked")

        # Tuple-2 and string aliases must not resolve a versioned recordRef.
        for alias in (
            ("run-manifest", "run-canonical-001"),
            "run-manifest@1.0:run-canonical-001",
            "run-manifest:run-canonical-001",
        ):
            result = evaluate_execution_semantics(
                ["CALC_PAYLOAD_REF_HASH_RESOLVES"], context({alias: target})
            )[0]
            self.assertEqual(result["status"], "fail", alias)

        wrong_version = copy.deepcopy(current)
        wrong_version["data"]["payload_ref"]["schema_version"] = "2.0"
        wrong_version_context = context({target_identity: target})
        wrong_version_context["current_record"] = wrong_version
        result = evaluate_execution_semantics(
            ["CALC_PAYLOAD_REF_HASH_RESOLVES"], wrong_version_context
        )[0]
        self.assertEqual(result["status"], "fail")

        # A document-shaped wrapper without ``data`` is missing context, not a document.
        unwrapped_context = context({target_identity: target})
        unwrapped_context["current_record"] = current_data
        result = evaluate_execution_semantics(
            ["CALC_PAYLOAD_REF_HASH_RESOLVES"], unwrapped_context
        )[0]
        self.assertEqual(result["status"], "blocked")

        target_without_data = copy.deepcopy(target)
        target_without_data.pop("data")
        result = evaluate_execution_semantics(
            ["CALC_PAYLOAD_REF_HASH_RESOLVES"],
            context({target_identity: target_without_data}),
        )[0]
        self.assertEqual(result["status"], "blocked")

        nonactive_target = copy.deepcopy(target)
        nonactive_target["lifecycle"] = "planned"
        result = evaluate_execution_semantics(
            ["CALC_PAYLOAD_REF_HASH_RESOLVES"],
            context({target_identity: nonactive_target}),
        )[0]
        self.assertEqual(result["status"], "fail")

    def test_production_results_are_unique_complete_and_report_schema_compatible(self) -> None:
        self.assertEqual(PRODUCTION_CONTRACT_NAMES, tuple(PRODUCTION_OBLIGATIONS))
        obligations = [
            obligation
            for contract_obligations in PRODUCTION_OBLIGATIONS.values()
            for obligation in contract_obligations
        ]
        context = {
            "current_record": {},
            "current_record_index": 0,
            "records_by_identity": {},
            "artifacts_by_label": {},
            "core_checks": {},
            "registry_snapshots": {},
        }
        unknown_obligation = "unknown execution-obligation"
        requested = [*obligations, obligations[0], unknown_obligation]
        results = evaluate_execution_semantics(requested, context)
        self.assertEqual(len(results), len(obligations) + 1)
        self.assertEqual(
            [result["obligation_id"] for result in results],
            [*obligations, unknown_obligation],
        )
        self.assertEqual(len(obligations), len(set(obligations)))

        result_validator = Draft202012Validator(
            {
                "$ref": (
                    self.schemas["bundle-validation-report"]["$id"]
                    + "#/$defs/obligationResult"
                )
            },
            registry=self.registry,
            format_checker=FormatChecker(),
        )
        exact_keys = {
            "obligation_id",
            "status",
            "finding_codes",
            "location",
            "message",
            "handler_id",
        }
        for result in results:
            self.assertEqual(set(result), exact_keys)
            enriched = {
                "source_contract_name": "synthetic-source-contract",
                "source_record_id": "synthetic-source-001",
                **result,
            }
            errors = list(result_validator.iter_errors(enriched))
            self.assertEqual(errors, [], (result, [error.message for error in errors]))

    def test_migrated_run_campaign_and_recommendation_route_to_execution_evaluator(self) -> None:
        tools_path = str(ROOT / "tools")
        if tools_path not in sys.path:
            sys.path.insert(0, tools_path)
        for contract_name in (
            "run-manifest",
            "campaign-record",
            "recommendation-record",
        ):
            evaluator = production_builtin_evaluator(contract_name)
            self.assertIsNotNone(evaluator, contract_name)
            self.assertEqual(evaluator.__module__, "bundle_semantics_execution")
            self.assertIn(contract_name, evaluator.__globals__["CONTRACT_NAMES"])

    def test_legacy_run_manifest_production_gate_is_strictly_predecision(self) -> None:
        def evaluate_state(
            status: str,
            acceptance: str,
            evidence: object | None = None,
            obligation: str = "LEGACY_RUN_PREDECISION_SCIENTIFIC_STATE",
        ) -> dict:
            data = {
                "schema_version": "1.0",
                "record_id": "run-predecision-001",
                "code": "qe",
                "status": status,
                "scientific_acceptance": acceptance,
                "evidence": [] if evidence is None else evidence,
            }
            context = {
                "current_record": {
                    "data": data,
                    "raw_sha256": "e" * 64,
                    "index": 0,
                    "lifecycle": "active",
                    "integrity_verified_active": True,
                },
                "current_record_index": 0,
                "records_by_identity": {},
                "artifacts_by_label": {},
                "core_checks": {},
                "registry_snapshots": {},
            }
            return evaluate_execution_semantics(
                [obligation], context
            )[0]

        self.assertEqual(evaluate_state("completed", "not_assessed")["status"], "pass")
        self.assertEqual(
            evaluate_state("completed", "requires_human_review")["status"], "pass"
        )
        self.assertEqual(evaluate_state("accepted", "accepted")["status"], "fail")
        self.assertEqual(evaluate_state("failed", "accepted")["status"], "fail")
        self.assertEqual(evaluate_state("completed", "rejected")["status"], "fail")
        self.assertEqual(
            evaluate_state("running", "requires_human_review")["status"], "fail"
        )

        evidence_obligation = "LEGACY_RUN_EVIDENCE_HASH_STATUS_MATCH"
        present = [{"status": "present", "sha256": "f" * 64}]
        self.assertEqual(
            evaluate_state(
                "completed", "not_assessed", present, evidence_obligation
            )["status"],
            "pass",
        )
        present[0]["sha256"] = None
        self.assertEqual(
            evaluate_state(
                "completed", "not_assessed", present, evidence_obligation
            )["status"],
            "fail",
        )
        missing_hashed = [{"status": "missing", "sha256": "f" * 64}]
        self.assertEqual(
            evaluate_state(
                "completed",
                "not_assessed",
                missing_hashed,
                evidence_obligation,
            )["status"],
            "fail",
        )
        self.assertEqual(
            evaluate_state(
                "completed", "not_assessed", {}, evidence_obligation
            )["status"],
            "blocked",
        )

    def test_campaign_production_handlers_require_exact_human_acceptance_chain(self) -> None:
        hashes = {
            "run": "1" * 64,
            "calculation": "2" * 64,
            "decision": "3" * 64,
            "claim": "4" * 64,
            "campaign": "5" * 64,
        }

        def ref(contract_name: str, record_id: str, digest: str, role: str) -> dict:
            return {
                "contract_name": contract_name,
                "schema_version": "1.0",
                "record_id": record_id,
                "sha256": digest,
                "role": role,
            }

        run = {
            "schema_version": "1.0",
            "record_id": "run-campaign-source-001",
            "code": "qe",
            "scientific_protocol_id": "protocol-campaign-001",
            "status": "completed",
            "scientific_acceptance": "not_assessed",
            "evidence": [],
        }
        source_ref = ref(
            "run-manifest", run["record_id"], hashes["run"], "source-run"
        )
        calculation = {
            "contract_name": "calculation-record-envelope",
            "schema_version": "1.0",
            "record_id": "calculation-campaign-001",
            "payload_ref": copy.deepcopy(source_ref) | {"role": "payload"},
            "status": {"scientific_acceptance": "requires_human_review"},
            "scientific_decision_ref": None,
        }
        calculation_ref = ref(
            "calculation-record-envelope",
            calculation["record_id"],
            hashes["calculation"],
            "scientific-candidate",
        )
        decision = {
            "contract_name": "decision-record",
            "schema_version": "1.0",
            "decision_id": "decision-campaign-001",
            "decision_type": "scientific-acceptance",
            "outcome": "accepted",
            "scientific_acceptance": "accepted",
            "decided_by": {"actor_type": "human"},
            "subject_ref": copy.deepcopy(calculation_ref),
        }
        decision_ref = ref(
            "decision-record",
            decision["decision_id"],
            hashes["decision"],
            "scientific-acceptance",
        )
        claim = {
            "contract_name": "claim-evidence-map",
            "schema_version": "1.0",
            "map_id": "claim-campaign-accepted-001",
            "scientific_acceptance": "accepted",
            "subject_records": [copy.deepcopy(calculation_ref)],
            "scientific_decision_ref": copy.deepcopy(decision_ref),
        }
        claim_ref = ref(
            "claim-evidence-map",
            claim["map_id"],
            hashes["claim"],
            "postdecision-claim-map",
        )
        campaign = {
            "schema_version": "1.0",
            "record_id": "campaign-accepted-001",
            "run_manifest_id": run["record_id"],
            "source_manifest_sha256": hashes["run"],
            "source_run_ref": copy.deepcopy(source_ref),
            "code": "qe",
            "outcome": {
                "status": "accepted",
                "scientific_acceptance": "accepted",
                "scientifically_accepted": True,
            },
            "acceptance_evidence": {
                "calculation_record_ref": copy.deepcopy(calculation_ref),
                "decision_ref": copy.deepcopy(decision_ref),
                "postdecision_claim_map_ref": copy.deepcopy(claim_ref),
            },
        }
        documents = [run, calculation, decision, claim, campaign]
        identities = [
            ("run-manifest", "1.0", run["record_id"]),
            ("calculation-record-envelope", "1.0", calculation["record_id"]),
            ("decision-record", "1.0", decision["decision_id"]),
            ("claim-evidence-map", "1.0", claim["map_id"]),
            ("campaign-record", "1.0", campaign["record_id"]),
        ]
        digests = list(hashes.values())
        records = {
            identity: {
                "contract_name": identity[0],
                "schema_version": identity[1],
                "record_id": identity[2],
                "index": index,
                "data": document,
                "raw_sha256": digests[index],
                "lifecycle": "active",
                "integrity_verified_active": True,
            }
            for index, (identity, document) in enumerate(zip(identities, documents))
        }

        def evaluate_campaign(value: dict, records_override: dict | None = None) -> dict[str, dict]:
            current = copy.deepcopy(records[identities[-1]])
            current["data"] = value
            selected_records = copy.deepcopy(records if records_override is None else records_override)
            selected_records[identities[-1]] = current
            context = production_read_only_context(
                {
                    "current_record": current,
                    "current_record_index": 4,
                    "records_by_identity": selected_records,
                    "artifacts_by_label": {},
                    "core_checks": {},
                    "registry_snapshots": {},
                }
            )
            results = evaluate_execution_semantics(
                PRODUCTION_OBLIGATIONS["campaign-record"], context
            )
            return {result["obligation_id"]: result for result in results}

        results = evaluate_campaign(campaign)
        self.assertTrue(all(result["status"] == "pass" for result in results.values()))

        wrong_source_hash = copy.deepcopy(campaign)
        wrong_source_hash["source_manifest_sha256"] = "9" * 64
        self.assertEqual(
            evaluate_campaign(wrong_source_hash)["CAMPAIGN_SOURCE_RUN_BINDING_MATCH"]["status"],
            "fail",
        )

        missing_chain = copy.deepcopy(campaign)
        missing_chain["acceptance_evidence"]["decision_ref"] = None
        self.assertEqual(
            evaluate_campaign(missing_chain)["CAMPAIGN_ACCEPTANCE_CHAIN_MATCH"]["status"],
            "fail",
        )

        wrong_decision_hash = copy.deepcopy(campaign)
        wrong_decision_hash["acceptance_evidence"]["decision_ref"]["sha256"] = "9" * 64
        self.assertEqual(
            evaluate_campaign(wrong_decision_hash)["CAMPAIGN_ACCEPTANCE_CHAIN_MATCH"]["status"],
            "fail",
        )

        wrong_decision_outcome_records = copy.deepcopy(records)
        wrong_decision_outcome_records[identities[2]]["data"]["outcome"] = "rejected"
        wrong_decision_outcome_records[identities[2]]["data"]["scientific_acceptance"] = "rejected"
        self.assertEqual(
            evaluate_campaign(campaign, wrong_decision_outcome_records)["CAMPAIGN_ACCEPTANCE_CHAIN_MATCH"]["status"],
            "fail",
        )

        nonhuman_records = copy.deepcopy(records)
        nonhuman_records[identities[2]]["data"]["decided_by"]["actor_type"] = "agent"
        self.assertEqual(
            evaluate_campaign(campaign, nonhuman_records)["CAMPAIGN_ACCEPTANCE_CHAIN_MATCH"]["status"],
            "fail",
        )

        unreviewed = copy.deepcopy(campaign)
        unreviewed["outcome"] = {
            "status": "completed-unreviewed",
            "scientific_acceptance": "requires_human_review",
            "scientifically_accepted": False,
        }
        unreviewed["acceptance_evidence"] = {
            "calculation_record_ref": None,
            "decision_ref": None,
            "postdecision_claim_map_ref": None,
        }
        results = evaluate_campaign(unreviewed)
        self.assertEqual(results["CAMPAIGN_SOURCE_RUN_BINDING_MATCH"]["status"], "pass")
        self.assertEqual(results["CAMPAIGN_ACCEPTANCE_CHAIN_MATCH"]["status"], "pass")

    def test_recommendation_production_handlers_recompute_accepted_campaign_savings(self) -> None:
        applicability = {
            "code": "qe",
            "code_version": "7.5-synthetic",
            "task_type": "scf",
            "system_class": "anonymous-small-periodic",
            "atom_count": 12,
            "scientific_protocol_id": "protocol-recommendation-001",
        }
        configurations = ("baseline", "baseline", "recommended", "recommended")
        core_hours = (12.0, 10.0, 7.0, 5.0)
        campaigns = []
        refs = []
        records = {}
        for index, (configuration, cost) in enumerate(
            zip(configurations, core_hours)
        ):
            record_id = f"campaign-recommendation-{index + 1:03d}"
            campaign = {
                "schema_version": "1.0",
                "record_id": record_id,
                **applicability,
                "configuration_id": configuration,
                "metrics": {"core_hours": cost},
                "outcome": {
                    "status": "accepted",
                    "scientific_acceptance": "accepted",
                    "scientifically_accepted": True,
                },
            }
            digest = f"{index + 6:x}" * 64
            reference = {
                "contract_name": "campaign-record",
                "schema_version": "1.0",
                "record_id": record_id,
                "sha256": digest,
                "role": "efficiency-evidence",
            }
            identity = ("campaign-record", "1.0", record_id)
            records[identity] = {
                "contract_name": identity[0],
                "schema_version": identity[1],
                "record_id": identity[2],
                "index": index,
                "data": campaign,
                "raw_sha256": digest,
                "lifecycle": "active",
                "integrity_verified_active": True,
            }
            campaigns.append(campaign)
            refs.append(reference)

        recommendation = {
            "schema_version": "1.0",
            "recommendation_id": "recommendation-validated-001",
            "status": "validated-for-this-campaign",
            "applicability": copy.deepcopy(applicability),
            "baseline_configuration_id": "baseline",
            "recommended_configuration_id": "recommended",
            "evidence_record_ids": [campaign["record_id"] for campaign in campaigns],
            "evidence_record_refs": copy.deepcopy(refs),
            "estimated_savings_fraction": 5.0 / 11.0,
            "confidence": "campaign",
        }
        recommendation_identity = (
            "recommendation-record",
            "1.0",
            recommendation["recommendation_id"],
        )
        current = {
            "contract_name": recommendation_identity[0],
            "schema_version": recommendation_identity[1],
            "record_id": recommendation_identity[2],
            "index": 4,
            "data": recommendation,
            "raw_sha256": "a" * 64,
            "lifecycle": "active",
            "integrity_verified_active": True,
        }
        records[recommendation_identity] = current

        def evaluate_recommendation(
            value: dict, records_override: dict | None = None
        ) -> dict[str, dict]:
            selected_current = copy.deepcopy(current)
            selected_current["data"] = value
            selected_records = copy.deepcopy(
                records if records_override is None else records_override
            )
            selected_records[recommendation_identity] = selected_current
            context = production_read_only_context(
                {
                    "current_record": selected_current,
                    "current_record_index": 4,
                    "records_by_identity": selected_records,
                    "artifacts_by_label": {},
                    "core_checks": {},
                    "registry_snapshots": {},
                }
            )
            results = evaluate_execution_semantics(
                PRODUCTION_OBLIGATIONS["recommendation-record"], context
            )
            return {result["obligation_id"]: result for result in results}

        results = evaluate_recommendation(recommendation)
        self.assertTrue(all(result["status"] == "pass" for result in results.values()))

        wrong_order = copy.deepcopy(recommendation)
        wrong_order["evidence_record_ids"][0:2] = reversed(
            wrong_order["evidence_record_ids"][0:2]
        )
        self.assertEqual(
            evaluate_recommendation(wrong_order)["RECOMMENDATION_EVIDENCE_CAMPAIGNS_MATCH"]["status"],
            "fail",
        )

        mismatched_applicability_records = copy.deepcopy(records)
        first_identity = ("campaign-record", "1.0", campaigns[0]["record_id"])
        mismatched_applicability_records[first_identity]["data"]["atom_count"] = 13
        self.assertEqual(
            evaluate_recommendation(recommendation, mismatched_applicability_records)["RECOMMENDATION_EVIDENCE_CAMPAIGNS_MATCH"]["status"],
            "fail",
        )

        unreviewed_records = copy.deepcopy(records)
        unreviewed_records[first_identity]["data"]["outcome"] = {
            "status": "completed-unreviewed",
            "scientific_acceptance": "requires_human_review",
            "scientifically_accepted": False,
        }
        self.assertEqual(
            evaluate_recommendation(recommendation, unreviewed_records)["RECOMMENDATION_POSITIVE_EVIDENCE_ACCEPTED"]["status"],
            "fail",
        )

        wrong_savings = copy.deepcopy(recommendation)
        wrong_savings["estimated_savings_fraction"] = 0.9
        self.assertEqual(
            evaluate_recommendation(wrong_savings)["RECOMMENDATION_POSITIVE_EVIDENCE_ACCEPTED"]["status"],
            "fail",
        )

        cross_campaign = copy.deepcopy(recommendation)
        cross_campaign["status"] = "cross-campaign-validated"
        cross_campaign["confidence"] = "cross-campaign"
        self.assertEqual(
            evaluate_recommendation(cross_campaign)["RECOMMENDATION_POSITIVE_EVIDENCE_ACCEPTED"]["status"],
            "blocked",
        )

    def test_schemas_are_draft_202012_strict_and_use_stable_external_urns(self) -> None:
        for name in SCHEMA_NAMES:
            schema = self.schemas[name]
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["$id"], f"urn:vibe-dft-skills:contract:{name}:1.0")
            Draft202012Validator.check_schema(schema)

            def walk(node: object) -> None:
                if isinstance(node, dict):
                    if node.get("type") == "object":
                        self.assertIs(node.get("additionalProperties"), False, f"open object in {name}")
                    ref = node.get("$ref")
                    if isinstance(ref, str) and not ref.startswith("#"):
                        self.assertTrue(ref.startswith("urn:vibe-dft-skills:contract:"), ref)
                    for value in node.values():
                        walk(value)
                elif isinstance(node, list):
                    for value in node:
                        walk(value)

            walk(schema)

    def test_machine_readable_semantic_obligations_are_complete(self) -> None:
        expected = {
            "calculation-record-envelope": {
                "CALC_PAYLOAD_REF_HASH_RESOLVES",
                "CALC_DOMAIN_PAYLOAD_CONTRACT_MATCH",
                "CALC_ENGINE_PAYLOAD_ID_MATCH",
                "CALC_PAYLOAD_STATUS_SUPPORTS_ENVELOPE",
                "CALC_PARENT_LINEAGE_RESOLVES",
                "CALC_GATE_EVIDENCE_REFS_RESOLVE",
                "CALC_RECORD_REF_DAG_ACYCLIC",
            },
            "execution-request": {
                "REQUEST_WORKFLOW_STEP_REF_RESOLVES",
                "REQUEST_WORKFLOW_PLAN_REF_HASH_MATCH",
                "REQUEST_OPERATION_ROUTE_BINDING",
                "REQUEST_AUTHORIZATION_POLICY_MATCH",
                "REQUEST_ARGV_TEMPLATE_BINDING",
                "REQUEST_INPUT_HASH_CONTENT_MATCHES",
                "REQUEST_PARENT_LINEAGE_RESOLVES",
                "REQUEST_RECORD_REF_DAG_ACYCLIC",
            },
            "execution-lease": {
                "LEASE_TIME_ORDER",
                "LEASE_AUTHORIZATION_TIME_CHAIN",
                "LEASE_REQUEST_REF_HASH_MATCH",
                "LEASE_AUTHORIZATION_DECISION_REF_HASH_MATCH",
                "LEASE_AUTHORIZATION_DECISION_APPROVED_REQUEST_MATCH",
                "LEASE_ARGV_HASH_MATCH",
                "LEASE_INPUT_HASH_SET_SUBSET",
                "LEASE_ENVIRONMENT_PROFILE_SUBSET",
                "LEASE_SCHEDULER_PROFILE_SUBSET",
                "LEASE_RESOURCE_CEILING_SUBSET",
                "LEASE_SIDE_EFFECT_SUBSET",
                "LEASE_OUTPUT_LABEL_SET_SUBSET",
                "LEASE_SINGLE_USE_CONSUMPTION",
                "LEASE_RECORD_REF_DAG_ACYCLIC",
            },
            "execution-record": {
                "EXEC_REQUEST_REF_HASH_MATCH",
                "EXEC_WORKFLOW_PLAN_REF_HASH_MATCH",
                "EXEC_LEASE_ACTIVE_REQUEST_MATCH",
                "EXEC_GRANTED_SCOPE_SUBSET",
                "EXEC_WORKFLOW_STEP_MATCH",
                "EXEC_REQUEST_CONTENT_MATCH",
                "EXEC_ARGV_HASH_MATCH",
                "EXEC_TIME_ORDER_AND_TIMINGS_MATCH",
                "EXEC_REQUEST_LEASE_EXECUTION_TIME_CHAIN",
                "EXEC_INPUT_OUTPUT_HASH_CONTENT_MATCH",
                "EXEC_NATIVE_STATUS_EVIDENCE_MATCH",
                "EXEC_PARENT_LINEAGE_RESOLVES",
                "EXEC_RECORD_REF_DAG_ACYCLIC",
            },
            "workflow-plan": {
                "WORKFLOW_STEP_IDS_UNIQUE",
                "WORKFLOW_DEPENDENCIES_RESOLVE",
                "WORKFLOW_DAG_ACYCLIC",
                "WORKFLOW_ROUTE_OPERATION_ACTIVE_MATCH",
                "WORKFLOW_AUTHORIZATION_SIDE_EFFECT_ALIGNMENT",
                "WORKFLOW_OUTPUT_HANDOFF_REFS_RESOLVE",
                "WORKFLOW_RECORD_REF_DAG_ACYCLIC",
            },
            "workflow-event": {
                "EVENT_PLAN_STEP_REF_RESOLVES",
                "EVENT_SEQUENCE_MONOTONIC",
                "EVENT_EVIDENCE_IDS_RESOLVE",
                "EVENT_TYPE_RELATED_RECORD_STATUS_MATCH",
                "EVENT_RELATED_RECORD_HASH_RESOLVES",
                "EVENT_NATIVE_STATUS_EVIDENCE_MATCH",
                "EVENT_RECORD_REF_DAG_ACYCLIC",
            },
            "decision-record": {
                "DECISION_SUBJECT_REF_HASH_RESOLVES",
                "DECISION_EVIDENCE_IDS_RESOLVE",
                "DECISION_AUTHORIZATION_REQUEST_SCOPE_MATCH",
                "DECISION_SCIENTIFIC_SUBJECT_HASH_OUTCOME_MATCH",
                "DECISION_REFS_PREEXIST_DECISION",
                "DECISION_RECORD_REF_DAG_ACYCLIC",
            },
            "claim-evidence-map": {
                "CLAIM_EVIDENCE_IDS_UNIQUE",
                "CLAIM_SUPPORTED_EVIDENCE_IDS_RESOLVE_PRESENT_HASHED",
                "CLAIM_GATE_IDS_UNIQUE",
                "CLAIM_SUPPORTED_GATE_IDS_RESOLVE_PASSING",
                "CLAIM_SCIENTIFIC_DECISION_CANDIDATE_HASH_OUTCOME_MATCH",
                "CLAIM_RECORD_REF_DAG_ACYCLIC",
            },
        }
        for schema_name, obligations in expected.items():
            self.assertEqual(
                set(self.schemas[schema_name]["x-vibe-semantic-obligations"]),
                obligations,
            )

    def test_exact_raw_byte_hash_bundle_is_a_constructible_immutable_dag(self) -> None:
        """Build the real plan->request->decision->lease->run->science DAG.

        recordRef.sha256 is the SHA-256 of the target JSON file's exact UTF-8 raw
        bytes. No projection hash, ignored field, or preselected fixture digest is
        used here.
        """

        times = {
            "plan": "2026-07-18T12:00:00Z",
            "request": "2026-07-18T12:01:00Z",
            "authorization": "2026-07-18T12:02:00Z",
            "lease": "2026-07-18T12:03:00Z",
            "started": "2026-07-18T12:04:00Z",
            "finished": "2026-07-18T12:04:30Z",
            "execution": "2026-07-18T12:05:00Z",
            "event": "2026-07-18T12:05:10Z",
            "payload": "2026-07-18T12:05:30Z",
            "calculation": "2026-07-18T12:06:00Z",
            "candidate": "2026-07-18T12:07:00Z",
            "scientific_decision": "2026-07-18T12:08:00Z",
            "accepted_map": "2026-07-18T12:09:00Z",
        }

        def clear_gate_refs(summary: dict) -> None:
            for check in summary["checks"]:
                check["evidence_refs"] = []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records: list[dict] = []
            raw_by_key: dict[tuple[str, str], bytes] = {}

            def write_record(data: dict) -> tuple[dict, bytes]:
                contract_name, record_id = record_key(data)
                self.assert_valid(contract_name, data)
                raw = (
                    json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)
                    + "\n"
                ).encode("utf-8")
                path = root / f"{len(records):02d}-{contract_name}-{record_id}.json"
                path.write_bytes(raw)
                self.assertEqual(path.read_bytes(), raw)
                loaded = json.loads(raw.decode("utf-8"))
                self.assert_valid(contract_name, loaded)
                records.append(loaded)
                raw_by_key[record_key(loaded)] = raw
                return loaded, raw

            input_raw = b"synthetic qe input\n"
            output_raw = b"JOB DONE\n"
            input_ref = file_ref()
            input_ref["sha256"] = exact_raw_sha256(input_raw)
            input_ref["bytes"] = len(input_raw)
            output_ref = file_ref("main-output", "synthetic-output.log")
            output_ref["sha256"] = exact_raw_sha256(output_raw)
            output_ref["bytes"] = len(output_raw)
            (root / "synthetic-input.dat").write_bytes(input_raw)
            (root / "synthetic-output.log").write_bytes(output_raw)

            plan = workflow_plan()
            plan["source_records"] = []
            plan["steps"][0]["input_records"] = []
            plan["steps"][0]["calculation_envelope_ref"] = None
            plan["steps"][0]["execution_request_ref"] = None
            clear_gate_refs(plan["steps"][0]["gates"])
            clear_gate_refs(plan["gates"])
            plan["producer"]["generated_utc"] = times["plan"]
            plan, plan_raw = write_record(plan)

            request = execution_request()
            request["workflow_plan_ref"] = exact_record_ref(
                plan, plan_raw, "workflow-plan"
            )
            request["operation_id"] = plan["steps"][0]["operation_id"]
            request["parent_records"] = []
            request["inputs"] = [copy.deepcopy(input_ref)]
            request["created_utc"] = times["request"]
            request["producer"]["generated_utc"] = times["request"]
            clear_gate_refs(request["gates"])
            request, request_raw = write_record(request)

            authorization = decision_record()
            authorization["subject_ref"] = exact_record_ref(
                request, request_raw, "execution-subject"
            )
            authorization["evidence_refs"] = [
                exact_record_ref(request, request_raw, "evidence")
            ]
            authorization["decided_utc"] = times["authorization"]
            authorization["valid_until_utc"] = "2026-07-18T13:03:00Z"
            authorization["producer"]["generated_utc"] = times["authorization"]
            authorization, authorization_raw = write_record(authorization)

            lease = execution_lease()
            lease["request_ref"] = exact_record_ref(
                request, request_raw, "execution-request"
            )
            lease["authorization_decision_ref"] = exact_record_ref(
                authorization, authorization_raw, "execution-authorization"
            )
            lease["issued_utc"] = times["lease"]
            lease["expires_utc"] = "2026-07-18T13:03:00Z"
            lease["grant"]["input_sha256"] = [input_ref["sha256"]]
            lease["producer"]["generated_utc"] = times["lease"]
            lease, lease_raw = write_record(lease)

            execution = execution_record()
            execution["request_ref"] = exact_record_ref(
                request, request_raw, "execution-request"
            )
            execution["lease_ref"] = exact_record_ref(
                lease, lease_raw, "execution-lease"
            )
            execution["workflow_plan_ref"] = exact_record_ref(
                plan, plan_raw, "workflow-plan"
            )
            execution["parent_records"] = []
            execution["inputs"] = [copy.deepcopy(input_ref)]
            execution["outputs"] = [copy.deepcopy(output_ref)]
            execution["started_utc"] = times["started"]
            execution["finished_utc"] = times["finished"]
            execution["producer"]["generated_utc"] = times["execution"]
            clear_gate_refs(execution["gates"])
            execution, execution_raw = write_record(execution)

            event = workflow_event()
            event["plan_ref"] = exact_record_ref(plan, plan_raw, "workflow-plan")
            event["related_records"] = [
                exact_record_ref(execution, execution_raw, "execution-record")
            ]
            event["evidence_ids"] = [execution["execution_id"]]
            event["evidence_refs"] = [
                exact_record_ref(execution, execution_raw, "scheduler-observation")
            ]
            event["occurred_utc"] = times["event"]
            event["producer"]["generated_utc"] = times["event"]
            event, event_raw = write_record(event)

            payload = periodic_run_manifest(
                output_sha256=output_ref["sha256"],
                generated_utc=times["payload"],
            )
            payload["configuration"]["execution_record_sha256"] = exact_raw_sha256(
                execution_raw
            )
            payload["evidence"].append(
                {
                    "role": "execution-record",
                    "label": "execution-001.json",
                    "sha256": exact_raw_sha256(execution_raw),
                    "status": "present",
                }
            )
            payload, payload_raw = write_record(payload)

            calculation = review_ready_calculation_envelope()
            calculation["payload_ref"] = exact_record_ref(
                payload, payload_raw, "payload"
            )
            calculation["parent_records"] = [
                exact_record_ref(execution, execution_raw, "parent")
            ]
            calculation["inputs"] = [copy.deepcopy(input_ref)]
            calculation["outputs"] = [copy.deepcopy(output_ref)]
            for check in calculation["gates"]["checks"]:
                evidence_record, evidence_raw = (
                    (execution, execution_raw)
                    if check["check_id"] == "technical-completion"
                    else (payload, payload_raw)
                )
                check["evidence_refs"] = [
                    exact_record_ref(evidence_record, evidence_raw, "gate-evidence")
                ]
            calculation["producer"]["generated_utc"] = times["calculation"]
            calculation, calculation_raw = write_record(calculation)

            candidate = claim_map()
            candidate["subject_records"] = [
                exact_record_ref(calculation, calculation_raw, "scientific-candidate")
            ]
            candidate["claim_ceiling"] = "eligible_for_expert_review"
            candidate["scientific_acceptance"] = "requires_human_review"
            candidate["evidence"][0]["record_ref"] = exact_record_ref(
                calculation, calculation_raw, "evidence"
            )
            candidate["claims"][0]["claim_level"] = "eligible_for_expert_review"
            for check in candidate["gates"]:
                check["evidence_refs"] = [
                    exact_record_ref(calculation, calculation_raw, "gate-evidence")
                ]
            candidate["producer"]["generated_utc"] = times["candidate"]
            candidate, candidate_raw = write_record(candidate)

            scientific_decision = decision_record("scientific-acceptance")
            scientific_decision["subject_ref"] = exact_record_ref(
                candidate, candidate_raw, "scientific-subject"
            )
            scientific_decision["evidence_refs"] = [
                exact_record_ref(candidate, candidate_raw, "evidence")
            ]
            scientific_decision["decided_utc"] = times["scientific_decision"]
            scientific_decision["producer"]["generated_utc"] = times[
                "scientific_decision"
            ]
            scientific_decision, scientific_decision_raw = write_record(
                scientific_decision
            )

            accepted = accepted_claim_map()
            accepted["subject_records"] = [
                exact_record_ref(candidate, candidate_raw, "scientific-candidate")
            ]
            accepted["scientific_decision_ref"] = exact_record_ref(
                scientific_decision,
                scientific_decision_raw,
                "scientific-acceptance",
            )
            accepted["evidence"][0]["record_ref"] = exact_record_ref(
                calculation, calculation_raw, "evidence"
            )
            for check in accepted["gates"]:
                check["evidence_refs"] = [
                    exact_record_ref(calculation, calculation_raw, "gate-evidence")
                ]
            accepted["producer"]["generated_utc"] = times["accepted_map"]
            accepted, accepted_raw = write_record(accepted)

            self.assertEqual(record_graph_findings(records, raw_by_key), [])
            positions = {record_key(record): index for index, record in enumerate(records)}
            for record in records:
                for ref in iter_record_refs(record):
                    target = (ref["contract_name"], ref["record_id"])
                    self.assertLess(positions[target], positions[record_key(record)])
                    self.assertEqual(ref["sha256"], exact_raw_sha256(raw_by_key[target]))

            self.assertNotEqual(
                exact_raw_sha256(accepted_raw), canonical_sha256(accepted)
            )
            record_hashes = {
                key: exact_raw_sha256(raw) for key, raw in raw_by_key.items()
            }
            records_by_key = {record_key(record): record for record in records}
            record_times = {}
            for key, record in records_by_key.items():
                generated = (
                    record.get("producer", {}).get("generated_utc")
                    or record.get("provenance", {}).get("generated_utc")
                )
                self.assertIsNotNone(generated)
                record_times[key] = datetime.fromisoformat(
                    generated.replace("Z", "+00:00")
                )
            shared_context = {
                "resolve_all_refs": True,
                "record_hashes": record_hashes,
                "records_by_key": records_by_key,
                "record_times": record_times,
                "record_bundle": records,
                "raw_by_key": raw_by_key,
                "file_hashes": {
                    input_ref["label"]: exact_raw_sha256(input_raw),
                    output_ref["label"]: exact_raw_sha256(output_raw),
                },
            }

            # Exercise every production execution handler against the same exact-byte
            # immutable DAG.  The production API consumes only strict pre-parsed views
            # indexed by the canonical versioned identity triple.
            record_views: dict[tuple[str, str, str], dict] = {}
            for index, record in enumerate(records):
                contract_name, record_id = record_key(record)
                record_views[(contract_name, record["schema_version"], record_id)] = {
                    "contract_name": contract_name,
                    "schema_version": record["schema_version"],
                    "record_id": record_id,
                    "data": record,
                    "raw_sha256": record_hashes[(contract_name, record_id)],
                    "index": index,
                    "lifecycle": "active",
                    "integrity_verified_active": True,
                }
            artifact_views = {
                input_ref["label"]: {
                    "label": input_ref["label"],
                    "raw_sha256": exact_raw_sha256(input_raw),
                    "bytes": len(input_raw),
                    "index": 0,
                    "metadata": copy.deepcopy(input_ref),
                    "integrity_verified": True,
                    "parser_observations": (),
                },
                output_ref["label"]: {
                    "label": output_ref["label"],
                    "raw_sha256": exact_raw_sha256(output_raw),
                    "bytes": len(output_raw),
                    "index": 1,
                    "metadata": copy.deepcopy(output_ref),
                    "integrity_verified": True,
                    "parser_observations": (),
                },
            }
            production_base = {
                "records_by_identity": record_views,
                "artifacts_by_label": artifact_views,
                "core_checks": {
                    "native_status_evidence": {
                        "scheduler": "COMPLETED",
                        "process": "exit 0",
                        "application": "JOB DONE",
                    }
                },
                "registry_snapshots": {
                    "interfaces": {
                        "schema_version": "1.0",
                        "interfaces": {
                            "run-manifest@1.0": {"lifecycle": "active"}
                        },
                    },
                    "operation_routes": {
                        "schema_version": "1.0",
                        "routes": {
                            plan["steps"][0]["skill_id"]: {
                                "lifecycle": "active",
                                "routable": True,
                                "actions": {
                                    request["operation_id"]: {
                                        "argv": request["argv"]
                                    }
                                },
                            }
                        },
                    },
                },
            }
            for index, record in enumerate(records):
                contract_name, record_id = record_key(record)
                obligations = PRODUCTION_OBLIGATIONS.get(contract_name, ())
                if not obligations:
                    continue
                current = record_views[
                    (contract_name, record["schema_version"], record_id)
                ]
                results = evaluate_execution_semantics(
                    obligations,
                    production_read_only_context(
                        production_base
                        | {
                            "current_record": current,
                            "current_record_index": index,
                        }
                    ),
                )
                nonpassing = [
                    (result["obligation_id"], result["status"], result["message"])
                    for result in results
                    if result["status"] != "pass"
                ]
                self.assertEqual(nonpassing, [], (contract_name, record_id))

            self.assertEqual(
                semantic_findings(
                    "workflow-plan", plan, shared_context | {
                        "known_operations": {
                            (plan["steps"][0]["skill_id"], plan["steps"][0]["operation_id"])
                        }
                    }
                ),
                [],
            )
            self.assertEqual(
                semantic_findings(
                    "workflow-event",
                    event,
                    shared_context | {
                        "workflow": plan,
                        "prior_events": [],
                        "related_record": execution,
                    },
                ),
                [],
            )
            self.assertEqual(
                semantic_findings(
                    "decision-record",
                    authorization,
                    shared_context | {"request": request},
                ),
                [],
            )
            self.assertEqual(
                semantic_findings(
                    "calculation-record-envelope",
                    calculation,
                    shared_context | {"payload": payload},
                ),
                [],
            )
            self.assertEqual(
                semantic_findings(
                    "execution-request",
                    request,
                    shared_context | {
                        "workflow": plan,
                        "operation_templates": {
                            request["operation_id"]: request["argv"]
                        },
                    },
                ),
                [],
            )
            self.assertEqual(
                semantic_findings(
                    "execution-lease",
                    lease,
                    shared_context | {
                        "request": request,
                        "decision": authorization,
                        "execution_records": [execution],
                    },
                ),
                [],
            )
            self.assertEqual(
                semantic_findings(
                    "execution-record",
                    execution,
                    shared_context | {
                        "request": request,
                        "lease": lease,
                        "workflow": plan,
                        "native_status_evidence": {
                            "scheduler": "COMPLETED",
                            "process": "exit 0",
                            "application": "JOB DONE",
                        },
                    },
                ),
                [],
            )
            self.assertEqual(
                semantic_findings(
                    "claim-evidence-map",
                    accepted,
                    shared_context | {"decision": scientific_decision},
                ),
                [],
            )
            self.assertEqual(
                semantic_findings(
                    "decision-record",
                    scientific_decision,
                    shared_context,
                ),
                [],
            )

    def test_fixed_fixture_hashes_cannot_hide_self_reference_or_two_record_cycle(self) -> None:
        self_ref = decision_record()
        self_ref["decision_type"] = "workflow-change"
        self_ref["subject_ref"] = record_ref(
            "decision-record", self_ref["decision_id"], "workflow-subject"
        )
        self_ref["evidence_ids"] = [self_ref["decision_id"]]
        self_ref["evidence_refs"] = [
            record_ref("decision-record", self_ref["decision_id"], "evidence")
        ]
        self_ref["scope_labels"] = []
        self.assert_valid("decision-record", self_ref)
        raw = (
            json.dumps(self_ref, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8")
        findings = record_graph_findings([self_ref], {record_key(self_ref): raw})
        self.assertIn("RECORD_REF_SELF_REFERENCE", findings)
        self.assertIn("RECORD_REF_GRAPH_CYCLIC", findings)

        plan = workflow_plan()
        plan["source_records"] = []
        plan["steps"][0]["input_records"] = []
        plan["steps"][0]["calculation_envelope_ref"] = None
        clear_plan_checks = [plan["gates"], plan["steps"][0]["gates"]]
        for summary in clear_plan_checks:
            for check in summary["checks"]:
                check["evidence_refs"] = []
        cycle_decision = decision_record()
        cycle_decision["decision_type"] = "workflow-change"
        cycle_decision["subject_ref"] = record_ref(
            "workflow-plan", plan["plan_id"], "workflow-subject"
        )
        cycle_decision["evidence_ids"] = [plan["plan_id"]]
        cycle_decision["evidence_refs"] = [
            record_ref("workflow-plan", plan["plan_id"], "evidence")
        ]
        cycle_decision["scope_labels"] = []
        plan["required_decisions"] = [
            record_ref("decision-record", cycle_decision["decision_id"], "required-decision")
        ]
        self.assert_valid("workflow-plan", plan)
        self.assert_valid("decision-record", cycle_decision)
        pair = [plan, cycle_decision]
        pair_raw = {
            record_key(item): (
                json.dumps(item, sort_keys=True, indent=2) + "\n"
            ).encode("utf-8")
            for item in pair
        }
        self.assertIn(
            "RECORD_REF_GRAPH_CYCLIC", record_graph_findings(pair, pair_raw)
        )
        cyclic_context = {
            "resolve_all_refs": True,
            "record_hashes": {},
            "record_times": {},
            "record_bundle": pair,
            "raw_by_key": pair_raw,
            "file_hashes": {},
        }
        dag_cases = {
            "calculation-record-envelope": (
                calculation_envelope(), "CALC_RECORD_REF_DAG_ACYCLIC"
            ),
            "execution-request": (
                execution_request(), "REQUEST_RECORD_REF_DAG_ACYCLIC"
            ),
            "execution-lease": (
                execution_lease(), "LEASE_RECORD_REF_DAG_ACYCLIC"
            ),
            "execution-record": (
                execution_record(), "EXEC_RECORD_REF_DAG_ACYCLIC"
            ),
            "workflow-plan": (
                workflow_plan(), "WORKFLOW_RECORD_REF_DAG_ACYCLIC"
            ),
            "workflow-event": (
                workflow_event(), "EVENT_RECORD_REF_DAG_ACYCLIC"
            ),
            "decision-record": (
                decision_record(), "DECISION_RECORD_REF_DAG_ACYCLIC"
            ),
            "claim-evidence-map": (
                claim_map(), "CLAIM_RECORD_REF_DAG_ACYCLIC"
            ),
        }
        for kind, (instance, obligation) in dag_cases.items():
            self.assertIn(obligation, semantic_findings(kind, instance, cyclic_context))

    def test_all_records_self_identify_with_required_constant_contract_name(self) -> None:
        factories = {
            "calculation-record-envelope": calculation_envelope,
            "execution-request": execution_request,
            "execution-lease": execution_lease,
            "execution-record": execution_record,
            "workflow-plan": workflow_plan,
            "workflow-event": workflow_event,
            "decision-record": decision_record,
            "claim-evidence-map": claim_map,
        }
        for schema_name, factory in factories.items():
            valid = factory()
            self.assert_valid(schema_name, valid)
            missing = copy.deepcopy(valid)
            missing.pop("contract_name")
            self.assert_invalid(schema_name, missing)
            wrong = copy.deepcopy(valid)
            wrong["contract_name"] = "wrong-contract"
            self.assert_invalid(schema_name, wrong)

    def test_catalog_identity_metadata_matches_required_top_level_record_ids(self) -> None:
        expected = {
            "calculation-record-envelope": "record_id",
            "execution-request": "request_id",
            "execution-lease": "lease_id",
            "execution-record": "execution_id",
            "workflow-plan": "plan_id",
            "workflow-event": "event_id",
            "decision-record": "decision_id",
            "claim-evidence-map": "map_id",
        }
        for schema_name, id_field in expected.items():
            schema = self.schemas[schema_name]
            self.assertEqual(
                schema["x-vibe-document-kind"], "content-addressed-record"
            )
            self.assertEqual(schema["x-vibe-record-id-field"], id_field)
            self.assertIn(id_field, schema["required"])
            self.assertIn(id_field, schema["properties"])

    def test_scientific_acceptance_uses_only_canonical_common_snake_case(self) -> None:
        review = review_ready_calculation_envelope()
        self.assert_valid("calculation-record-envelope", review)
        for legacy in ("not-assessed", "requires-human-review", "requires_expert_review"):
            data = calculation_envelope()
            data["status"]["scientific_acceptance"] = legacy
            self.assert_invalid("calculation-record-envelope", data)

        event = workflow_event()
        event["scientific_acceptance"] = "not-assessed"
        self.assert_invalid("workflow-event", event)

    def test_calculation_domain_interface_is_reserved_but_unregistered_payloads_block(self) -> None:
        periodic = calculation_envelope()
        self.assert_valid("calculation-record-envelope", periodic)
        self.assertNotIn(
            "CALC_DOMAIN_PAYLOAD_CONTRACT_MATCH",
            semantic_findings("calculation-record-envelope", periodic),
        )
        for domain in (
            "quantum-chemistry",
            "molecular-dynamics",
            "machine-learned-potential",
        ):
            data = calculation_envelope()
            data["domain"] = domain
            self.assert_valid("calculation-record-envelope", data)
            self.assertIn(
                "CALC_DOMAIN_PAYLOAD_CONTRACT_MATCH",
                semantic_findings("calculation-record-envelope", data),
            )
        legacy = json.loads((CONTRACTS / "run-manifest.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(legacy["properties"]["code"]["enum"], ["qe", "vasp", "cp2k", "siesta"])

    def test_periodic_calculation_payload_engine_and_status_are_bound(self) -> None:
        wrong_contract = calculation_envelope()
        wrong_contract["payload_ref"]["contract_name"] = "execution-record"
        self.assert_invalid("calculation-record-envelope", wrong_contract)

        payload = periodic_run_manifest()
        payload_raw = (
            json.dumps(payload, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8")
        data = calculation_envelope()
        data["payload_ref"] = exact_record_ref(payload, payload_raw, "payload")
        context = {
            "payload": payload,
            "record_hashes": {record_key(payload): exact_raw_sha256(payload_raw)},
        }
        self.assertEqual(
            semantic_findings("calculation-record-envelope", data, context), []
        )

        wrong_payload_hash = copy.deepcopy(data)
        wrong_payload_hash["payload_ref"]["sha256"] = SHA_A
        self.assertIn(
            "CALC_PAYLOAD_REF_HASH_RESOLVES",
            semantic_findings(
                "calculation-record-envelope", wrong_payload_hash, context
            ),
        )

        wrong_engine = copy.deepcopy(data)
        wrong_engine["engine"]["software_id"] = "vasp"
        self.assertIn(
            "CALC_ENGINE_PAYLOAD_ID_MATCH",
            semantic_findings("calculation-record-envelope", wrong_engine, context),
        )
        unfinished_payload = copy.deepcopy(payload)
        unfinished_payload["status"] = "running"
        unfinished = context | {"payload": unfinished_payload}
        self.assertIn(
            "CALC_PAYLOAD_STATUS_SUPPORTS_ENVELOPE",
            semantic_findings("calculation-record-envelope", data, unfinished),
        )

        unresolved_refs = context | {
            "resolve_all_refs": True,
            "record_bundle": [],
            "raw_by_key": {},
        }
        unresolved_findings = semantic_findings(
            "calculation-record-envelope", data, unresolved_refs
        )
        self.assertIn("CALC_PARENT_LINEAGE_RESOLVES", unresolved_findings)
        self.assertIn("CALC_GATE_EVIDENCE_REFS_RESOLVE", unresolved_findings)

    def test_scheduler_success_does_not_imply_application_or_scientific_success(self) -> None:
        data = calculation_envelope()
        data["status"].update(
            normalized_status="failed",
            scheduler_status="succeeded",
            process_status="exited-zero",
            application_status="incomplete",
            scientific_acceptance="not_assessed",
        )
        self.assert_valid("calculation-record-envelope", data)
        data["status"]["normalized_status"] = "completed"
        self.assert_invalid("calculation-record-envelope", data)

    def test_calculation_plan_cannot_impersonate_a_submitted_or_completed_run(self) -> None:
        data = calculation_envelope()
        data["record_kind"] = "plan"
        data["status"] = {
            "native_status": "synthetic plan",
            "normalized_status": "planned",
            "scheduler_status": "not-submitted",
            "process_status": "not-started",
            "application_status": "not-started",
            "scientific_acceptance": "not_assessed",
        }
        data["outputs"] = [file_ref("main-output", "synthetic-output.log", "missing")]
        self.assert_valid("calculation-record-envelope", data)
        data["status"]["scheduler_status"] = "queued"
        self.assert_invalid("calculation-record-envelope", data)

    def test_calculation_stops_at_review_required_and_never_backrefs_decision(self) -> None:
        data = review_ready_calculation_envelope()
        self.assert_valid("calculation-record-envelope", data)
        for terminal_decision in ("accepted", "rejected"):
            rewritten = review_ready_calculation_envelope()
            rewritten["status"]["scientific_acceptance"] = terminal_decision
            self.assert_invalid("calculation-record-envelope", rewritten)
        backref = review_ready_calculation_envelope()
        backref["scientific_decision_ref"] = record_ref(
            "decision-record", "decision-002", "scientific-acceptance"
        )
        self.assert_invalid("calculation-record-envelope", backref)

    def test_review_ready_envelope_rejects_generic_or_non_deterministic_readiness_gates(self) -> None:
        generic = review_ready_calculation_envelope()
        generic["gates"] = gates(
            claim_ceiling="eligible_for_expert_review",
            maximum_action="eligible-for-expert-review",
        )
        self.assert_invalid("calculation-record-envelope", generic)

        agent_asserted = review_ready_calculation_envelope()
        readiness = next(
            check for check in agent_asserted["gates"]["checks"]
            if check["check_id"] == "expert-review-readiness"
        )
        readiness["validated_by"]["actor_type"] = "agent"
        self.assert_invalid("calculation-record-envelope", agent_asserted)

        missing_numerical = review_ready_calculation_envelope()
        missing_numerical["gates"]["checks"] = [
            check for check in missing_numerical["gates"]["checks"]
            if check["check_id"] != "numerical-evidence"
        ]
        self.assert_invalid("calculation-record-envelope", missing_numerical)

    def test_review_ready_envelope_requires_run_coherent_status_and_present_hashed_output(self) -> None:
        mutations = []
        planned = review_ready_calculation_envelope()
        planned["record_kind"] = "plan"
        mutations.append(planned)
        scheduler_failed = review_ready_calculation_envelope()
        scheduler_failed["status"]["scheduler_status"] = "failed"
        mutations.append(scheduler_failed)
        scheduler_cancelled = review_ready_calculation_envelope()
        scheduler_cancelled["status"]["scheduler_status"] = "cancelled"
        mutations.append(scheduler_cancelled)
        process_failed = review_ready_calculation_envelope()
        process_failed["status"]["process_status"] = "exited-nonzero"
        mutations.append(process_failed)
        empty_outputs = review_ready_calculation_envelope()
        empty_outputs["outputs"] = []
        mutations.append(empty_outputs)
        only_external = review_ready_calculation_envelope()
        only_external["outputs"] = [file_ref("main-output", "synthetic-output.log", "external")]
        mutations.append(only_external)
        missing_hash = review_ready_calculation_envelope()
        missing_hash["outputs"][0]["sha256"] = None
        mutations.append(missing_hash)
        for data in mutations:
            self.assert_invalid("calculation-record-envelope", data)

    def test_calculation_plan_outputs_are_missing_and_completed_run_has_outputs(self) -> None:
        plan = calculation_envelope()
        plan["record_kind"] = "plan"
        plan["status"].update(
            native_status="synthetic plan",
            normalized_status="planned",
            scheduler_status="not-submitted",
            process_status="not-started",
            application_status="not-started",
        )
        plan["outputs"] = [file_ref("main-output", "synthetic-output.log", "present")]
        self.assert_invalid("calculation-record-envelope", plan)
        completed = calculation_envelope()
        completed["outputs"] = []
        self.assert_invalid("calculation-record-envelope", completed)

    def test_execution_request_is_non_shell_hash_complete_and_not_authorization(self) -> None:
        self.assert_valid("execution-request", execution_request())
        shell = execution_request()
        shell["shell"] = True
        self.assert_invalid("execution-request", shell)
        shell_binary = execution_request()
        shell_binary["argv"] = ["bash", "-c", "pw.x -in inputs/scf.in"]
        self.assert_invalid("execution-request", shell_binary)
        indirect_shell = execution_request()
        indirect_shell["argv"] = ["env", "bash", "-c", "pw.x -in inputs/scf.in"]
        self.assert_invalid("execution-request", indirect_shell)
        embedded_grant = execution_request()
        embedded_grant["authorization_ref"] = record_ref("decision-record", "decision-001")
        self.assert_invalid("execution-request", embedded_grant)
        missing_hash = execution_request()
        missing_hash["inputs"][0]["sha256"] = None
        self.assert_invalid("execution-request", missing_hash)

    def test_privacy_unsafe_or_traversing_execution_paths_are_rejected(self) -> None:
        for unsafe in (
            "/Users/example/private/run",
            "../../private/run",
            "--input=/home/user/scf.in",
            "note /Users/example/private/run",
            "note /home/example/private/run",
            r"C:\\Users\\example\\private\\run",
            r"--input=C:\\Users\\example\\private\\scf.in",
            r"\\\\server\\private-share",
            "arg(/private/run)",
            "arg,/tmp/run",
            "arg;/var/run",
            "arg[/Volumes/data]",
            "arg{/scratch/job}",
            "arg,/gpfs/job",
            "arg(/lustre/job)",
            "arg,/mnt/data",
            "arg(/work/job)",
            "arg,/project/job",
            "arg(C:/private/run)",
        ):
            data = execution_request()
            if unsafe.startswith("--"):
                data["argv"][2] = unsafe
            else:
                data["working_directory_label"] = unsafe
            self.assert_invalid("execution-request", data)

    def test_inline_interpreters_are_blocked_but_registered_module_invocation_is_structurally_allowed(self) -> None:
        for argv in (
            ["python3", "-c", "print('unsafe')"],
            ["env", "python3", "-c", "print('unsafe')"],
            ["perl", "-e", "print 'unsafe'"],
            ["ruby", "-e", "puts 'unsafe'"],
            ["node", "--eval", "console.log('unsafe')"],
        ):
            data = execution_request()
            data["argv"] = argv
            self.assert_invalid("execution-request", data)
        module = execution_request()
        module["argv"] = ["python3", "-m", "registered_module", "--input", "inputs/scf.in"]
        self.assert_valid("execution-request", module)

    def test_prepared_execute_request_requires_present_inputs_and_missing_expected_outputs(self) -> None:
        missing_input = execution_request()
        missing_input["inputs"] = [file_ref("input", "synthetic-input.dat", "missing")]
        self.assert_invalid("execution-request", missing_input)
        external_input = execution_request()
        external_input["inputs"] = [file_ref("input", "synthetic-input.dat", "external")]
        self.assert_invalid("execution-request", external_input)
        present_output = execution_request()
        present_output["expected_outputs"] = [file_ref("main-output", "synthetic-output.log")]
        self.assert_invalid("execution-request", present_output)
        no_outputs = execution_request()
        no_outputs["expected_outputs"] = []
        self.assert_invalid("execution-request", no_outputs)

        dry = execution_request()
        dry["execution_mode"] = "dry-run"
        dry["authorization_requirement"]["required"] = False
        dry["inputs"] = [file_ref("input", "synthetic-input.dat", "missing")]
        self.assert_valid("execution-request", dry)

    def test_side_effects_use_only_the_canonical_common_vocabulary(self) -> None:
        legacy = execution_request()
        legacy["authorization_requirement"]["side_effects"] = ["remote-execution"]
        self.assert_invalid("execution-request", legacy)
        canonical = execution_request()
        canonical["authorization_requirement"]["side_effects"] = [
            "remote-read", "remote-write"
        ]
        self.assert_valid("execution-request", canonical)

    def test_execute_request_requires_authorization_but_dry_run_can_only_declare_it(self) -> None:
        data = execution_request()
        data["authorization_requirement"]["required"] = False
        self.assert_invalid("execution-request", data)
        data["execution_mode"] = "dry-run"
        self.assert_valid("execution-request", data)

    def test_request_semantics_bind_workflow_operation_and_registered_argv_template(self) -> None:
        data = execution_request()
        context = {
            "workflow": workflow_plan(),
            "operation_templates": {
                "run-periodic-dft": ["pw.x", "-in", "inputs/scf.in"]
            },
        }
        # The fixture workflow intentionally uses a different operation, so it is blocked.
        self.assertIn(
            "REQUEST_OPERATION_ROUTE_BINDING",
            semantic_findings("execution-request", data, context),
        )
        context["workflow"]["steps"][0]["operation_id"] = "run-periodic-dft"
        self.assertEqual(semantic_findings("execution-request", data, context), [])

        changed_argv = copy.deepcopy(data)
        changed_argv["argv"] = ["python3", "-m", "registered_module"]
        self.assert_valid("execution-request", changed_argv)
        self.assertIn(
            "REQUEST_ARGV_TEMPLATE_BINDING",
            semantic_findings("execution-request", changed_argv, context),
        )

        missing_step = copy.deepcopy(data)
        missing_step["workflow_step_id"] = "step-999"
        self.assertIn(
            "REQUEST_WORKFLOW_STEP_REF_RESOLVES",
            semantic_findings("execution-request", missing_step, context),
        )

        overbroad_authorization = copy.deepcopy(data)
        overbroad_authorization["authorization_requirement"]["side_effects"] = [
            "scheduler-submit", "external-publish"
        ]
        self.assert_valid("execution-request", overbroad_authorization)
        self.assertIn(
            "REQUEST_AUTHORIZATION_POLICY_MATCH",
            semantic_findings("execution-request", overbroad_authorization, context),
        )

        wrong_plan_hash_context = context | {
            "record_hashes": {("workflow-plan", "plan-001"): SHA_B}
        }
        self.assertIn(
            "REQUEST_WORKFLOW_PLAN_REF_HASH_MATCH",
            semantic_findings(
                "execution-request", data, wrong_plan_hash_context
            ),
        )

        unresolved_content_context = context | {
            "resolve_all_refs": True,
            "record_hashes": {("workflow-plan", "plan-001"): SHA_A},
            "file_hashes": {"synthetic-input.dat": SHA_A},
            "record_bundle": [],
            "raw_by_key": {},
        }
        unresolved_content = semantic_findings(
            "execution-request", data, unresolved_content_context
        )
        self.assertIn("REQUEST_INPUT_HASH_CONTENT_MATCHES", unresolved_content)
        self.assertIn("REQUEST_PARENT_LINEAGE_RESOLVES", unresolved_content)

    def test_lease_is_single_use_hash_bound_and_requires_separate_decision(self) -> None:
        data = execution_lease()
        self.assert_valid("execution-lease", data)
        reusable = copy.deepcopy(data)
        reusable["single_use"] = False
        self.assert_invalid("execution-lease", reusable)
        bad_hash = copy.deepcopy(data)
        bad_hash["grant"]["argv_sha256"] = "not-a-hash"
        self.assert_invalid("execution-lease", bad_hash)
        no_decision = copy.deepcopy(data)
        no_decision.pop("authorization_decision_ref")
        self.assert_invalid("execution-lease", no_decision)
        embedded_decision = copy.deepcopy(data)
        embedded_decision["authorization"] = {"outcome": "approved"}
        self.assert_invalid("execution-lease", embedded_decision)

    def test_lease_requires_authorization_role_and_deterministic_issuer(self) -> None:
        wrong_role = execution_lease()
        wrong_role["authorization_decision_ref"]["role"] = "source"
        self.assert_invalid("execution-lease", wrong_role)
        human_issuer = execution_lease()
        human_issuer["issued_by"] = actor("human", "request-owner", "lease-issuer")
        self.assert_invalid("execution-lease", human_issuer)

    def test_lease_semantics_enforce_time_order_decision_and_grant_subsets(self) -> None:
        context = {"request": execution_request(), "decision": decision_record()}
        self.assertEqual(semantic_findings("execution-lease", execution_lease(), context), [])

        reversed_time = execution_lease()
        reversed_time["issued_utc"], reversed_time["expires_utc"] = (
            reversed_time["expires_utc"],
            reversed_time["issued_utc"],
        )
        self.assertIn("LEASE_TIME_ORDER", semantic_findings("execution-lease", reversed_time, context))

        wrong_duration = execution_lease()
        wrong_duration["lease_duration_s"] = 60
        self.assertIn("LEASE_TIME_ORDER", semantic_findings("execution-lease", wrong_duration, context))

        late_decision = decision_record()
        late_decision["decided_utc"] = "2026-07-18T12:05:00Z"
        self.assertIn(
            "LEASE_AUTHORIZATION_TIME_CHAIN",
            semantic_findings(
                "execution-lease",
                execution_lease(),
                {"request": execution_request(), "decision": late_decision},
            ),
        )

        short_authorization = decision_record()
        short_authorization["valid_until_utc"] = "2026-07-18T12:30:00Z"
        self.assertIn(
            "LEASE_AUTHORIZATION_TIME_CHAIN",
            semantic_findings(
                "execution-lease",
                execution_lease(),
                {"request": execution_request(), "decision": short_authorization},
            ),
        )

        expanded_env = execution_lease()
        expanded_env["grant"]["environment_profile_ids"].append("unrequested-env-001")
        self.assertIn(
            "LEASE_ENVIRONMENT_PROFILE_SUBSET",
            semantic_findings("execution-lease", expanded_env, context),
        )

        expanded_resources = execution_lease()
        expanded_resources["grant"]["resource_ceiling"]["nodes"] = 2
        self.assertIn(
            "LEASE_RESOURCE_CEILING_SUBSET",
            semantic_findings("execution-lease", expanded_resources, context),
        )

        expanded_inputs = execution_lease()
        expanded_inputs["grant"]["input_sha256"].append(SHA_A)
        self.assertIn(
            "LEASE_INPUT_HASH_SET_SUBSET",
            semantic_findings("execution-lease", expanded_inputs, context),
        )

        expanded_scheduler = execution_lease()
        expanded_scheduler["grant"]["scheduler_profile_ids"].append("other-scheduler-001")
        self.assertIn(
            "LEASE_SCHEDULER_PROFILE_SUBSET",
            semantic_findings("execution-lease", expanded_scheduler, context),
        )

        expanded_effects = execution_lease()
        expanded_effects["grant"]["side_effects"].append("external-publish")
        self.assertIn(
            "LEASE_SIDE_EFFECT_SUBSET",
            semantic_findings("execution-lease", expanded_effects, context),
        )

        expanded_outputs = execution_lease()
        expanded_outputs["grant"]["output_labels"].append("unrequested.log")
        self.assertIn(
            "LEASE_OUTPUT_LABEL_SET_SUBSET",
            semantic_findings("execution-lease", expanded_outputs, context),
        )

        wrong_ref_hashes = context | {
            "record_hashes": {
                ("execution-request", "request-001"): SHA_B,
                ("decision-record", "decision-001"): SHA_B,
            }
        }
        ref_findings = semantic_findings(
            "execution-lease", execution_lease(), wrong_ref_hashes
        )
        self.assertIn("LEASE_REQUEST_REF_HASH_MATCH", ref_findings)
        self.assertIn("LEASE_AUTHORIZATION_DECISION_REF_HASH_MATCH", ref_findings)

        duplicate_consumers = context | {
            "execution_records": [execution_record(), execution_record()]
        }
        self.assertIn(
            "LEASE_SINGLE_USE_CONSUMPTION",
            semantic_findings(
                "execution-lease", execution_lease(), duplicate_consumers
            ),
        )

        wrong_argv = execution_lease()
        wrong_argv["grant"]["argv_sha256"] = SHA_A
        self.assertIn("LEASE_ARGV_HASH_MATCH", semantic_findings("execution-lease", wrong_argv, context))

        denied = decision_record()
        denied["outcome"] = "denied"
        self.assertIn(
            "LEASE_AUTHORIZATION_DECISION_APPROVED_REQUEST_MATCH",
            semantic_findings(
                "execution-lease",
                execution_lease(),
                {"request": execution_request(), "decision": denied},
            ),
        )

    def test_execution_record_accepts_authorized_success_and_dry_run(self) -> None:
        self.assert_valid("execution-record", execution_record())
        dry = execution_record()
        dry["dry_run"] = True
        dry["lease_ref"] = None
        dry["started_utc"] = None
        dry["finished_utc"] = None
        dry["return_code"] = None
        dry["outputs"] = [file_ref("main-output", "synthetic-output.log", "missing")]
        dry["timings"] = {"queue_wait_s": None, "wall_time_s": None, "cpu_time_s": None, "gpu_time_s": None}
        dry["status"] = {
            "native_scheduler_status": None,
            "scheduler_status": "not-submitted",
            "native_process_status": None,
            "process_status": "not-started",
            "native_application_status": None,
            "application_status": "not-started",
            "normalized_status": "dry-run",
        }
        self.assert_valid("execution-record", dry)

    def test_zero_return_code_with_incomplete_application_is_not_success(self) -> None:
        data = execution_record()
        data["status"]["native_application_status"] = "completion marker absent"
        data["status"]["application_status"] = "incomplete"
        data["status"]["normalized_status"] = "failed"
        self.assert_valid("execution-record", data)
        data["status"]["normalized_status"] = "succeeded"
        self.assert_invalid("execution-record", data)

    def test_succeeded_execution_rejects_failed_scheduler_or_process_states(self) -> None:
        for scheduler_status in ("failed", "cancelled"):
            data = execution_record()
            data["status"]["scheduler_status"] = scheduler_status
            self.assert_invalid("execution-record", data)
        for process_status in ("exited-nonzero", "timed-out", "signalled"):
            data = execution_record()
            data["status"]["process_status"] = process_status
            self.assert_invalid("execution-record", data)

    def test_execution_record_rejects_wrong_request_lease_or_plan_roles(self) -> None:
        for field in ("request_ref", "lease_ref", "workflow_plan_ref"):
            data = execution_record()
            data[field]["role"] = "source"
            self.assert_invalid("execution-record", data)

    def test_execution_semantics_verify_argv_hash_timings_and_lease_time_chain(self) -> None:
        context = {"request": execution_request(), "lease": execution_lease()}
        self.assertEqual(semantic_findings("execution-record", execution_record(), context), [])

        argv_mismatch = execution_record()
        argv_mismatch["argv_sha256"] = SHA_A
        self.assertIn(
            "EXEC_ARGV_HASH_MATCH",
            semantic_findings("execution-record", argv_mismatch, context),
        )

        changed_but_self_consistent_argv = execution_record()
        changed_but_self_consistent_argv["argv"] = [
            "pw.x", "-in", "inputs/other.in"
        ]
        changed_but_self_consistent_argv["argv_sha256"] = canonical_sha256(
            changed_but_self_consistent_argv["argv"]
        )
        self.assertIn(
            "EXEC_ARGV_HASH_MATCH",
            semantic_findings(
                "execution-record", changed_but_self_consistent_argv, context
            ),
        )

        wrong_step = execution_record()
        wrong_step["workflow_step_id"] = "step-999"
        self.assertIn(
            "EXEC_WORKFLOW_STEP_MATCH",
            semantic_findings("execution-record", wrong_step, context),
        )

        wrong_directory = execution_record()
        wrong_directory["working_directory_label"] = "campaign-001/run-002"
        self.assertIn(
            "EXEC_REQUEST_CONTENT_MATCH",
            semantic_findings("execution-record", wrong_directory, context),
        )

        wrong_ref_context = context | {
            "workflow": workflow_plan(),
            "record_hashes": {
                ("execution-request", "request-001"): SHA_B,
                ("execution-lease", "lease-001"): SHA_B,
                ("workflow-plan", "plan-001"): SHA_B,
            },
        }
        wrong_ref_findings = semantic_findings(
            "execution-record", execution_record(), wrong_ref_context
        )
        self.assertIn("EXEC_REQUEST_REF_HASH_MATCH", wrong_ref_findings)
        self.assertIn("EXEC_WORKFLOW_PLAN_REF_HASH_MATCH", wrong_ref_findings)
        self.assertIn("EXEC_LEASE_ACTIVE_REQUEST_MATCH", wrong_ref_findings)

        outside_grant = execution_record()
        outside_grant["environment_profile_id"] = "env-profile-002"
        self.assertIn(
            "EXEC_GRANTED_SCOPE_SUBSET",
            semantic_findings("execution-record", outside_grant, context),
        )

        unresolved_evidence_context = context | {
            "resolve_all_refs": True,
            "record_hashes": {},
            "file_hashes": {
                "synthetic-input.dat": SHA_A,
                "synthetic-output.log": SHA_A,
            },
            "native_status_evidence": {
                "scheduler": "FAILED",
                "process": "exit 1",
                "application": "incomplete",
            },
            "record_bundle": [],
            "raw_by_key": {},
        }
        unresolved_evidence = semantic_findings(
            "execution-record", execution_record(), unresolved_evidence_context
        )
        self.assertIn("EXEC_INPUT_OUTPUT_HASH_CONTENT_MATCH", unresolved_evidence)
        self.assertIn("EXEC_NATIVE_STATUS_EVIDENCE_MATCH", unresolved_evidence)
        self.assertIn("EXEC_PARENT_LINEAGE_RESOLVES", unresolved_evidence)

        reversed_time = execution_record()
        reversed_time["started_utc"] = FINISHED
        reversed_time["finished_utc"] = NOW
        self.assertIn(
            "EXEC_TIME_ORDER_AND_TIMINGS_MATCH",
            semantic_findings("execution-record", reversed_time, context),
        )

        wrong_wall = execution_record()
        wrong_wall["timings"]["wall_time_s"] = 29.0
        self.assertIn(
            "EXEC_TIME_ORDER_AND_TIMINGS_MATCH",
            semantic_findings("execution-record", wrong_wall, context),
        )

        impossible_cpu = execution_record()
        impossible_cpu["timings"]["cpu_time_s"] = 61.0
        self.assertIn(
            "EXEC_TIME_ORDER_AND_TIMINGS_MATCH",
            semantic_findings("execution-record", impossible_cpu, context),
        )

        impossible_gpu = execution_record()
        impossible_gpu["timings"]["gpu_time_s"] = 1.0
        self.assertIn(
            "EXEC_TIME_ORDER_AND_TIMINGS_MATCH",
            semantic_findings("execution-record", impossible_gpu, context),
        )

        expired_context = {"request": execution_request(), "lease": execution_lease()}
        expired_context["lease"]["expires_utc"] = "2026-07-18T12:00:10Z"
        self.assertIn(
            "EXEC_REQUEST_LEASE_EXECUTION_TIME_CHAIN",
            semantic_findings("execution-record", execution_record(), expired_context),
        )

    def test_tool_failure_requires_phase_code_detail_and_evidence(self) -> None:
        data = execution_record()
        data["status"].update(
            native_scheduler_status=None,
            scheduler_status="not-applicable",
            native_process_status="exit 2",
            process_status="exited-nonzero",
            native_application_status="adapter failed",
            application_status="failed",
            normalized_status="failed",
        )
        data["return_code"] = 2
        data["tool_failure"] = {
            "occurred": True,
            "phase": "collection",
            "finding_code": "adapter-failed",
            "detail": "Synthetic adapter returned a non-zero status.",
            "evidence_refs": [record_ref("evidence-record", "diagnostic-001", "failure-evidence")],
        }
        self.assert_valid("execution-record", data)
        data["tool_failure"]["evidence_refs"] = []
        self.assert_invalid("execution-record", data)

    def test_execution_record_rejects_scientific_acceptance_extra_fields_and_unsafe_path(self) -> None:
        science = execution_record()
        science["scientific_acceptance"] = "accepted"
        self.assert_invalid("execution-record", science)
        extra = execution_record()
        extra["scientific_result"] = "valid"
        self.assert_invalid("execution-record", extra)
        unsafe = execution_record()
        unsafe["working_directory_label"] = "/scratch/private/case"
        self.assert_invalid("execution-record", unsafe)

    def test_workflow_plan_routes_active_steps_but_fail_closes_nonactive_routes(self) -> None:
        self.assert_valid("workflow-plan", workflow_plan())
        for lifecycle in ("development", "planned"):
            with self.subTest(lifecycle=lifecycle):
                nonactive = workflow_plan()
                nonactive["status"] = "blocked"
                nonactive["blocker_codes"] = ["nonactive-route"]
                nonactive["gates"] = gates(blocked=True)
                step = nonactive["steps"][0]
                step["route_lifecycle"] = lifecycle
                step["state"] = "blocked"
                step["execution_request_ref"] = None
                step["maturity"] = {
                    "implementation": "contract-only",
                    "validation": "design-only",
                    "claim_ceiling": "no_positive_claim",
                }
                step["gates"] = gates(blocked=True)
                step["blocker_codes"] = ["nonactive-route"]
                self.assert_valid("workflow-plan", nonactive)
                step["execution_request_ref"] = record_ref("execution-request", "request-001", "request")
                self.assert_invalid("workflow-plan", nonactive)

    def test_workflow_step_rejects_open_ended_fields(self) -> None:
        data = workflow_plan()
        data["steps"][0]["agent_guess"] = "run anyway"
        self.assert_invalid("workflow-plan", data)

    def test_ready_workflow_cannot_hide_planned_or_blocked_steps(self) -> None:
        planned = workflow_plan()
        planned["steps"][0]["route_lifecycle"] = "planned"
        planned["steps"][0]["state"] = "blocked"
        planned["steps"][0]["blocker_codes"] = ["planned-route"]
        planned["steps"][0]["gates"] = gates(blocked=True)
        planned["steps"][0]["maturity"] = {
            "implementation": "contract-only",
            "validation": "design-only",
            "claim_ceiling": "no_positive_claim",
        }
        self.assert_invalid("workflow-plan", planned)

        blocked = workflow_plan()
        blocked["steps"][0]["state"] = "blocked"
        blocked["steps"][0]["blocker_codes"] = ["missing-evidence"]
        blocked["steps"][0]["gates"] = gates(blocked=True)
        self.assert_invalid("workflow-plan", blocked)

    def test_workflow_semantics_enforce_unique_dag_routes_and_authorization_alignment(self) -> None:
        known = {("qe-rigorous-calculations", "audit-and-run-scf")}
        context = {"known_operations": known}
        self.assertEqual(semantic_findings("workflow-plan", workflow_plan(), context), [])

        duplicate = workflow_plan()
        duplicate["steps"].append(copy.deepcopy(duplicate["steps"][0]))
        self.assert_valid("workflow-plan", duplicate)
        self.assertIn("WORKFLOW_STEP_IDS_UNIQUE", semantic_findings("workflow-plan", duplicate, context))

        unresolved = workflow_plan()
        unresolved["steps"][0]["dependencies"] = ["step-999"]
        self.assertIn(
            "WORKFLOW_DEPENDENCIES_RESOLVE",
            semantic_findings("workflow-plan", unresolved, context),
        )

        cyclic = workflow_plan()
        second = copy.deepcopy(cyclic["steps"][0])
        second["step_id"] = "step-002"
        second["dependencies"] = ["step-001"]
        cyclic["steps"][0]["dependencies"] = ["step-002"]
        cyclic["steps"].append(second)
        self.assert_valid("workflow-plan", cyclic)
        self.assertIn("WORKFLOW_DAG_ACYCLIC", semantic_findings("workflow-plan", cyclic, context))

        unknown_route = workflow_plan()
        unknown_route["steps"][0]["operation_id"] = "unregistered-operation"
        self.assertIn(
            "WORKFLOW_ROUTE_OPERATION_ACTIVE_MATCH",
            semantic_findings("workflow-plan", unknown_route, context),
        )

        misaligned_auth = workflow_plan()
        misaligned_auth["authorization_policy"]["side_effects"] = ["local-execution"]
        self.assert_valid("workflow-plan", misaligned_auth)
        self.assertIn(
            "WORKFLOW_AUTHORIZATION_SIDE_EFFECT_ALIGNMENT",
            semantic_findings("workflow-plan", misaligned_auth, context),
        )

        missing_handoff = workflow_plan()
        downstream = copy.deepcopy(missing_handoff["steps"][0])
        downstream["step_id"] = "step-002"
        downstream["dependencies"] = ["step-001"]
        downstream["input_records"] = []
        missing_handoff["steps"].append(downstream)
        self.assert_valid("workflow-plan", missing_handoff)
        self.assertIn(
            "WORKFLOW_OUTPUT_HANDOFF_REFS_RESOLVE",
            semantic_findings("workflow-plan", missing_handoff, context),
        )

    def test_read_only_workflow_does_not_require_authorization_or_lease(self) -> None:
        data = workflow_plan()
        data["steps"][0]["execution_class"] = "inspect-only"
        data["authorization_policy"] = {
            "human_decision_required": False,
            "lease_required": False,
            "side_effects": [],
            "scope_labels": [],
        }
        self.assert_valid("workflow-plan", data)
        data["authorization_policy"]["lease_required"] = True
        self.assert_invalid("workflow-plan", data)

    def test_scheduler_event_preserves_native_status_and_cannot_claim_science(self) -> None:
        self.assert_valid("workflow-event", workflow_event())
        wrong_layer = workflow_event()
        wrong_layer["observed_status"]["layer"] = "application"
        self.assert_invalid("workflow-event", wrong_layer)
        overclaim = workflow_event()
        overclaim["claim_ceiling"] = "numerical_candidate_only"
        self.assert_invalid("workflow-event", overclaim)
        science = workflow_event()
        science["scientific_acceptance"] = "accepted"
        self.assert_invalid("workflow-event", science)

    def test_workflow_completion_event_still_has_no_scientific_acceptance(self) -> None:
        data = workflow_event()
        data["event_type"] = "workflow-completed"
        data["step_id"] = None
        data["observed_status"] = {
            "layer": "workflow",
            "native_status": "all technical steps complete",
            "normalized_status": "completed",
        }
        self.assert_valid("workflow-event", data)

    def test_event_semantics_resolve_evidence_and_match_type_related_record_and_status(self) -> None:
        self.assertEqual(semantic_findings("workflow-event", workflow_event()), [])
        unknown_evidence = workflow_event()
        unknown_evidence["evidence_ids"] = ["unknown-evidence-001"]
        self.assert_valid("workflow-event", unknown_evidence)
        self.assertIn(
            "EVENT_EVIDENCE_IDS_RESOLVE",
            semantic_findings("workflow-event", unknown_evidence),
        )
        wrong_related = workflow_event()
        wrong_related["related_records"][0]["contract_name"] = "decision-record"
        wrong_related["related_records"][0]["role"] = "decision-record"
        self.assert_valid("workflow-event", wrong_related)
        self.assertIn(
            "EVENT_TYPE_RELATED_RECORD_STATUS_MATCH",
            semantic_findings("workflow-event", wrong_related),
        )
        wrong_status = workflow_event()
        wrong_status["observed_status"]["normalized_status"] = "approved"
        self.assert_valid("workflow-event", wrong_status)
        self.assertIn(
            "EVENT_TYPE_RELATED_RECORD_STATUS_MATCH",
            semantic_findings("workflow-event", wrong_status),
        )

        workflow_context = {
            "workflow": workflow_plan(),
            "record_hashes": {("workflow-plan", "plan-001"): SHA_A},
        }
        wrong_step = workflow_event()
        wrong_step["step_id"] = "step-999"
        self.assertIn(
            "EVENT_PLAN_STEP_REF_RESOLVES",
            semantic_findings("workflow-event", wrong_step, workflow_context),
        )

        self.assertIn(
            "EVENT_SEQUENCE_MONOTONIC",
            semantic_findings(
                "workflow-event",
                workflow_event(),
                workflow_context | {"prior_events": [workflow_event()]},
            ),
        )

        related_hash_context = workflow_context | {
            "resolve_all_refs": True,
            "record_hashes": {
                ("workflow-plan", "plan-001"): SHA_A,
                ("execution-record", "execution-001"): SHA_B,
                ("evidence-record", "scheduler-log-001"): SHA_A,
            },
            "related_record": execution_record(),
            "record_bundle": [],
            "raw_by_key": {},
        }
        self.assertIn(
            "EVENT_RELATED_RECORD_HASH_RESOLVES",
            semantic_findings(
                "workflow-event", workflow_event(), related_hash_context
            ),
        )

        native_mismatch = execution_record()
        native_mismatch["status"]["native_scheduler_status"] = "FAILED"
        native_context = related_hash_context | {
            "record_hashes": {
                ("workflow-plan", "plan-001"): SHA_A,
                ("execution-record", "execution-001"): SHA_A,
                ("evidence-record", "scheduler-log-001"): SHA_A,
            },
            "related_record": native_mismatch,
        }
        self.assertIn(
            "EVENT_NATIVE_STATUS_EVIDENCE_MATCH",
            semantic_findings("workflow-event", workflow_event(), native_context),
        )

    def test_execution_authorization_and_scientific_acceptance_require_human(self) -> None:
        self.assert_valid("decision-record", decision_record())
        self.assert_valid("decision-record", decision_record("scientific-acceptance"))
        for decision_type in ("execution-authorization", "scientific-acceptance"):
            data = decision_record(decision_type)
            data["decided_by"] = actor("agent", "fast-agent")
            self.assert_invalid("decision-record", data)
        no_expiry = decision_record()
        no_expiry["valid_until_utc"] = None
        self.assert_invalid("decision-record", no_expiry)

    def test_decision_semantics_resolve_evidence_ids_to_hashed_record_refs(self) -> None:
        self.assertEqual(semantic_findings("decision-record", decision_record()), [])
        data = decision_record()
        data["evidence_ids"] = ["unknown-evidence-001"]
        self.assert_valid("decision-record", data)
        self.assertIn(
            "DECISION_EVIDENCE_IDS_RESOLVE",
            semantic_findings("decision-record", data),
        )

        expired = decision_record()
        expired["valid_until_utc"] = "2026-07-18T11:59:59Z"
        context = {
            "request": execution_request(),
            "record_hashes": {("execution-request", "request-001"): SHA_A},
        }
        self.assertIn(
            "DECISION_AUTHORIZATION_REQUEST_SCOPE_MATCH",
            semantic_findings("decision-record", expired, context),
        )

        wrong_subject_hash = decision_record()
        wrong_subject_hash["subject_ref"]["sha256"] = SHA_B
        self.assertIn(
            "DECISION_SUBJECT_REF_HASH_RESOLVES",
            semantic_findings("decision-record", wrong_subject_hash, context),
        )

        scientific = decision_record("scientific-acceptance")
        not_ready_candidate = claim_map()
        candidate_key = ("claim-evidence-map", "claim-map-001")
        future = datetime.fromisoformat("2026-07-18T13:00:00+00:00")
        scientific_context = {
            "resolve_all_refs": True,
            "record_hashes": {candidate_key: SHA_A},
            "records_by_key": {candidate_key: not_ready_candidate},
            "record_times": {candidate_key: future},
            "record_bundle": [],
            "raw_by_key": {},
        }
        scientific_findings = semantic_findings(
            "decision-record", scientific, scientific_context
        )
        self.assertIn(
            "DECISION_SCIENTIFIC_SUBJECT_HASH_OUTCOME_MATCH",
            scientific_findings,
        )
        self.assertIn("DECISION_REFS_PREEXIST_DECISION", scientific_findings)

    def test_scientific_decision_rejects_missing_evidence_or_mismatched_outcome(self) -> None:
        data = decision_record("scientific-acceptance")
        data["evidence_ids"] = []
        self.assert_invalid("decision-record", data)
        mismatch = decision_record("scientific-acceptance")
        mismatch["scientific_acceptance"] = "rejected"
        self.assert_invalid("decision-record", mismatch)

        wrong_subject_role = decision_record("scientific-acceptance")
        wrong_subject_role["subject_ref"]["role"] = "source"
        self.assert_invalid("decision-record", wrong_subject_role)

    def test_scientific_decision_subject_is_a_predecision_calculation_or_claim_candidate(self) -> None:
        claim_subject = decision_record("scientific-acceptance")
        self.assert_valid("decision-record", claim_subject)
        calculation_subject = decision_record("scientific-acceptance")
        calculation_subject["subject_ref"] = record_ref(
            "calculation-record-envelope", "calculation-001", "scientific-subject"
        )
        self.assert_valid("decision-record", calculation_subject)
        downstream_or_untyped = decision_record("scientific-acceptance")
        downstream_or_untyped["subject_ref"] = record_ref(
            "execution-record", "execution-001", "scientific-subject"
        )
        self.assert_invalid("decision-record", downstream_or_untyped)

    def test_claim_map_requires_evidence_ids_for_supported_claims(self) -> None:
        self.assert_valid("claim-evidence-map", claim_map())
        data = claim_map()
        data["claims"][0]["evidence_ids"] = []
        self.assert_invalid("claim-evidence-map", data)

    def test_claim_map_enforces_ceiling_and_human_decision_reference(self) -> None:
        data = claim_map()
        data["claim_ceiling"] = "input_gates_only"
        self.assert_invalid("claim-evidence-map", data)
        accepted = accepted_claim_map()
        accepted["scientific_decision_ref"] = None
        self.assert_invalid("claim-evidence-map", accepted)
        accepted = accepted_claim_map()
        self.assert_valid("claim-evidence-map", accepted)
        accepted["status"] = "partial"
        self.assert_invalid("claim-evidence-map", accepted)

        no_supported_scientific_claim = accepted_claim_map()
        no_supported_scientific_claim["claims"][0]["status"] = "rejected"
        self.assert_invalid("claim-evidence-map", no_supported_scientific_claim)

        review_required = claim_map()
        review_required["scientific_acceptance"] = "requires_human_review"
        self.assert_invalid("claim-evidence-map", review_required)
        review_required["claim_ceiling"] = "eligible_for_expert_review"
        review_required["claims"][0]["claim_level"] = "eligible_for_expert_review"
        self.assert_valid("claim-evidence-map", review_required)

        rejected = accepted_claim_map()
        rejected["scientific_acceptance"] = "rejected"
        rejected["claims"][0]["status"] = "rejected"
        self.assert_valid("claim-evidence-map", rejected)

    def test_claim_map_rejects_open_fields_and_malformed_hashes(self) -> None:
        extra = claim_map()
        extra["claims"][0]["confidence"] = 1.0
        self.assert_invalid("claim-evidence-map", extra)
        bad_hash = claim_map()
        bad_hash["evidence"][0]["record_ref"]["sha256"] = "abc"
        self.assert_invalid("claim-evidence-map", bad_hash)

    def test_claim_semantics_resolve_supported_evidence_and_gate_ids(self) -> None:
        self.assertEqual(semantic_findings("claim-evidence-map", claim_map()), [])

        unknown_evidence = claim_map()
        unknown_evidence["claims"][0]["evidence_ids"] = ["evidence-999"]
        self.assert_valid("claim-evidence-map", unknown_evidence)
        self.assertIn(
            "CLAIM_SUPPORTED_EVIDENCE_IDS_RESOLVE_PRESENT_HASHED",
            semantic_findings("claim-evidence-map", unknown_evidence),
        )

        missing_evidence = claim_map()
        missing_evidence["evidence"][0]["status"] = "missing"
        self.assert_valid("claim-evidence-map", missing_evidence)
        self.assertIn(
            "CLAIM_SUPPORTED_EVIDENCE_IDS_RESOLVE_PRESENT_HASHED",
            semantic_findings("claim-evidence-map", missing_evidence),
        )

        unknown_gate = claim_map()
        unknown_gate["claims"][0]["gate_ids"] = ["gate-999"]
        self.assert_valid("claim-evidence-map", unknown_gate)
        self.assertIn(
            "CLAIM_SUPPORTED_GATE_IDS_RESOLVE_PASSING",
            semantic_findings("claim-evidence-map", unknown_gate),
        )

        failed_gate = claim_map()
        failed_gate["gates"][0]["status"] = "fail"
        self.assert_valid("claim-evidence-map", failed_gate)
        self.assertIn(
            "CLAIM_SUPPORTED_GATE_IDS_RESOLVE_PASSING",
            semantic_findings("claim-evidence-map", failed_gate),
        )

        duplicate_evidence = claim_map()
        duplicate = copy.deepcopy(duplicate_evidence["evidence"][0])
        duplicate["limitations"] = ["Distinct object with a duplicate stable ID."]
        duplicate_evidence["evidence"].append(duplicate)
        self.assert_valid("claim-evidence-map", duplicate_evidence)
        self.assertIn(
            "CLAIM_EVIDENCE_IDS_UNIQUE",
            semantic_findings("claim-evidence-map", duplicate_evidence),
        )

        duplicate_gate_map = claim_map()
        duplicate_gate = copy.deepcopy(duplicate_gate_map["gates"][0])
        duplicate_gate["limitations"] = ["Duplicate stable gate ID."]
        duplicate_gate_map["gates"].append(duplicate_gate)
        self.assert_valid("claim-evidence-map", duplicate_gate_map)
        self.assertIn(
            "CLAIM_GATE_IDS_UNIQUE",
            semantic_findings("claim-evidence-map", duplicate_gate_map),
        )

    def test_accepted_claim_map_requires_scientific_acceptance_decision_role(self) -> None:
        data = accepted_claim_map()
        data["scientific_decision_ref"]["role"] = "source"
        self.assert_invalid("claim-evidence-map", data)

    def test_accepted_claim_map_semantics_bind_predecision_candidate_and_later_decision(self) -> None:
        data = accepted_claim_map()
        decision = decision_record("scientific-acceptance")
        context = {
            "decision": decision,
            "record_hashes": {
                ("claim-evidence-map", "claim-map-001"): SHA_A,
                ("decision-record", "decision-002"): SHA_A,
            },
        }
        self.assertEqual(semantic_findings("claim-evidence-map", data, context), [])
        decision["subject_ref"]["record_id"] = "claim-map-999"
        self.assertIn(
            "CLAIM_SCIENTIFIC_DECISION_CANDIDATE_HASH_OUTCOME_MATCH",
            semantic_findings("claim-evidence-map", data, context),
        )

        self_subject = accepted_claim_map()
        self_subject["map_id"] = "claim-map-001"
        self.assertIn(
            "CLAIM_SCIENTIFIC_DECISION_CANDIDATE_HASH_OUTCOME_MATCH",
            semantic_findings(
                "claim-evidence-map",
                self_subject,
                context | {"decision": decision_record("scientific-acceptance")},
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
