"""Pure semantic evaluator for execution/workflow/decision contracts.

The bundle loader owns I/O, UTF-8/JSON parsing, schema validation, and context
construction.  This module is intentionally I/O-free: it consumes only the
frozen, read-only context keys documented by :func:`evaluate`.

Every advertised obligation has a dedicated handler and produces exactly one
result.  A handler returns ``blocked`` when the supplied context is insufficient
to prove or disprove the obligation; missing evidence is never treated as pass.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from statistics import median
from typing import Any, Callable, Iterable, Mapping, Sequence


CONTEXT_KEYS = frozenset(
    {
        "current_record",
        "current_record_index",
        "records_by_identity",
        "artifacts_by_label",
        "core_checks",
        "registry_snapshots",
    }
)

OBLIGATIONS_BY_CONTRACT: dict[str, tuple[str, ...]] = {
    "run-manifest": (
        "LEGACY_RUN_PREDECISION_SCIENTIFIC_STATE",
        "LEGACY_RUN_EVIDENCE_HASH_STATUS_MATCH",
    ),
    "campaign-record": (
        "CAMPAIGN_SOURCE_RUN_BINDING_MATCH",
        "CAMPAIGN_ACCEPTANCE_CHAIN_MATCH",
        "CAMPAIGN_RECORD_REF_DAG_ACYCLIC",
    ),
    "recommendation-record": (
        "RECOMMENDATION_EVIDENCE_CAMPAIGNS_MATCH",
        "RECOMMENDATION_POSITIVE_EVIDENCE_ACCEPTED",
        "RECOMMENDATION_RECORD_REF_DAG_ACYCLIC",
    ),
    "calculation-record-envelope": (
        "CALC_PAYLOAD_REF_HASH_RESOLVES",
        "CALC_DOMAIN_PAYLOAD_CONTRACT_MATCH",
        "CALC_ENGINE_PAYLOAD_ID_MATCH",
        "CALC_PAYLOAD_STATUS_SUPPORTS_ENVELOPE",
        "CALC_PARENT_LINEAGE_RESOLVES",
        "CALC_GATE_EVIDENCE_REFS_RESOLVE",
        "CALC_RECORD_REF_DAG_ACYCLIC",
    ),
    "execution-request": (
        "REQUEST_WORKFLOW_STEP_REF_RESOLVES",
        "REQUEST_WORKFLOW_PLAN_REF_HASH_MATCH",
        "REQUEST_OPERATION_ROUTE_BINDING",
        "REQUEST_AUTHORIZATION_POLICY_MATCH",
        "REQUEST_ARGV_TEMPLATE_BINDING",
        "REQUEST_INPUT_HASH_CONTENT_MATCHES",
        "REQUEST_PARENT_LINEAGE_RESOLVES",
        "REQUEST_RECORD_REF_DAG_ACYCLIC",
    ),
    "execution-lease": (
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
    ),
    "execution-record": (
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
    ),
    "workflow-plan": (
        "WORKFLOW_STEP_IDS_UNIQUE",
        "WORKFLOW_DEPENDENCIES_RESOLVE",
        "WORKFLOW_DAG_ACYCLIC",
        "WORKFLOW_ROUTE_OPERATION_ACTIVE_MATCH",
        "WORKFLOW_AUTHORIZATION_SIDE_EFFECT_ALIGNMENT",
        "WORKFLOW_OUTPUT_HANDOFF_REFS_RESOLVE",
        "WORKFLOW_RECORD_REF_DAG_ACYCLIC",
    ),
    "workflow-event": (
        "EVENT_PLAN_STEP_REF_RESOLVES",
        "EVENT_SEQUENCE_MONOTONIC",
        "EVENT_EVIDENCE_IDS_RESOLVE",
        "EVENT_TYPE_RELATED_RECORD_STATUS_MATCH",
        "EVENT_RELATED_RECORD_HASH_RESOLVES",
        "EVENT_NATIVE_STATUS_EVIDENCE_MATCH",
        "EVENT_RECORD_REF_DAG_ACYCLIC",
    ),
    "decision-record": (
        "DECISION_SUBJECT_REF_HASH_RESOLVES",
        "DECISION_EVIDENCE_IDS_RESOLVE",
        "DECISION_AUTHORIZATION_REQUEST_SCOPE_MATCH",
        "DECISION_SCIENTIFIC_SUBJECT_HASH_OUTCOME_MATCH",
        "DECISION_REFS_PREEXIST_DECISION",
        "DECISION_RECORD_REF_DAG_ACYCLIC",
    ),
    "claim-evidence-map": (
        "CLAIM_EVIDENCE_IDS_UNIQUE",
        "CLAIM_SUPPORTED_EVIDENCE_IDS_RESOLVE_PRESENT_HASHED",
        "CLAIM_GATE_IDS_UNIQUE",
        "CLAIM_SUPPORTED_GATE_IDS_RESOLVE_PASSING",
        "CLAIM_SCIENTIFIC_DECISION_CANDIDATE_HASH_OUTCOME_MATCH",
        "CLAIM_RECORD_REF_DAG_ACYCLIC",
    ),
}

# Consumed by the production dispatcher's fixed-module resolver.  Keeping this
# derived from the obligation catalog prevents a contract from advertising a
# handler set that the dispatcher cannot route.
CONTRACT_NAMES = tuple(OBLIGATIONS_BY_CONTRACT)

RECORD_ID_FIELDS = {
    "calculation-record-envelope": "record_id",
    "execution-request": "request_id",
    "execution-lease": "lease_id",
    "execution-record": "execution_id",
    "workflow-plan": "plan_id",
    "workflow-event": "event_id",
    "decision-record": "decision_id",
    "claim-evidence-map": "map_id",
    "run-manifest": "record_id",
    "campaign-record": "record_id",
    "recommendation-record": "recommendation_id",
}

_HANDLERS: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {}


def _finding_code(obligation_id: str) -> str:
    # ``bundle-validation-report`` requires stable uppercase snake-case codes.
    parts = re.findall(r"[A-Z0-9]+", str(obligation_id).upper())
    normalized = "_".join(parts)
    if not normalized or normalized[0] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        return "SEMANTIC_OBLIGATION_FAILED"
    return normalized


def _result(
    obligation_id: str,
    status: str,
    *,
    location: str = "$",
    message: str,
    finding_codes: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "obligation_id": obligation_id,
        "status": status,
        "finding_codes": list(finding_codes),
        "location": location,
        "message": message,
        "handler_id": f"bundle-semantics-execution.{obligation_id.lower()}",
    }


def _pass(obligation_id: str, message: str = "Semantic obligation satisfied.") -> dict[str, Any]:
    return _result(obligation_id, "pass", message=message)


def _fail(obligation_id: str, location: str, message: str) -> dict[str, Any]:
    return _result(
        obligation_id,
        "fail",
        location=location,
        message=message,
        finding_codes=(_finding_code(obligation_id),),
    )


def _blocked(obligation_id: str, location: str, message: str) -> dict[str, Any]:
    return _result(
        obligation_id,
        "blocked",
        location=location,
        message=message,
        finding_codes=(f"{_finding_code(obligation_id)}_CONTEXT_BLOCKED",),
    )


def _handler(obligation_id: str):
    def decorate(function: Callable[[Mapping[str, Any]], dict[str, Any]]):
        if obligation_id in _HANDLERS:
            raise RuntimeError(f"duplicate semantic handler: {obligation_id}")
        _HANDLERS[obligation_id] = function
        return function

    return decorate


def _entry_data(entry: Any) -> Mapping[str, Any] | None:
    if not isinstance(entry, Mapping):
        return None
    data = entry.get("data")
    return data if isinstance(data, Mapping) else None


def _current_entry(context: Mapping[str, Any]) -> Mapping[str, Any] | None:
    entry = context.get("current_record")
    return entry if isinstance(entry, Mapping) else None


def _current_data(context: Mapping[str, Any]) -> Mapping[str, Any] | None:
    return _entry_data(_current_entry(context))


def _current_index(context: Mapping[str, Any]) -> int | None:
    value = context.get("current_record_index")
    entry = _current_entry(context)
    entry_index = entry.get("index") if entry is not None else None
    if (
        isinstance(value, int)
        and value >= 0
        and isinstance(entry_index, int)
        and value == entry_index
    ):
        return value
    return None


def _identity_from_data(data: Mapping[str, Any]) -> tuple[str, str, str] | None:
    contract_name = data.get("contract_name")
    if not isinstance(contract_name, str):
        if {"code", "scientific_protocol_id", "evidence"}.issubset(data):
            contract_name = "run-manifest"
        else:
            return None
    field = RECORD_ID_FIELDS.get(contract_name)
    record_id = data.get(field) if field is not None else None
    version = data.get("schema_version")
    if not isinstance(record_id, str) or not isinstance(version, str):
        return None
    return contract_name, version, record_id


def _ref_identity(ref: Mapping[str, Any]) -> tuple[str, str, str] | None:
    values = (ref.get("contract_name"), ref.get("schema_version"), ref.get("record_id"))
    return values if all(isinstance(value, str) for value in values) else None


def _same_ref_target(left: Any, right: Any) -> bool:
    return (
        isinstance(left, Mapping)
        and isinstance(right, Mapping)
        and _ref_identity(left) is not None
        and _ref_identity(left) == _ref_identity(right)
        and isinstance(left.get("sha256"), str)
        and left.get("sha256") == right.get("sha256")
    )


def _records(context: Mapping[str, Any]) -> Mapping[Any, Any]:
    records = context.get("records_by_identity")
    return records if isinstance(records, Mapping) else {}


def _lookup_identity(context: Mapping[str, Any], identity: tuple[str, str, str]) -> Mapping[str, Any] | None:
    """Resolve only the frozen canonical identity key.

    The bundle loader is responsible for constructing an unambiguous
    ``(contract_name, schema_version, record_id)`` index.  Accepting aliases here
    would let a wrong-version reference silently bind to another record.
    """

    records = _records(context)
    entry = records.get(identity)
    return entry if isinstance(entry, Mapping) else None


def _resolve_ref(
    context: Mapping[str, Any],
    ref: Any,
    *,
    source_index: int | None = None,
) -> tuple[str, Mapping[str, Any] | None, str]:
    if not isinstance(ref, Mapping):
        return "blocked", None, "recordRef is unavailable or not an object"
    identity = _ref_identity(ref)
    if identity is None:
        return "blocked", None, "recordRef identity is incomplete"
    entry = _lookup_identity(context, identity)
    if entry is None:
        return "fail", None, f"recordRef target {identity!r} is absent from the bundle index"
    data = _entry_data(entry)
    if data is None:
        return "blocked", None, "resolved record entry has no strictly parsed data"
    if entry.get("integrity_verified_active") is not True:
        return "blocked", data, "resolved record target is not integrity-verified active"
    lifecycle = entry.get("lifecycle")
    if not isinstance(lifecycle, str):
        return "blocked", data, "resolved record target lacks lifecycle state"
    if lifecycle != "active":
        return "fail", data, f"recordRef target lifecycle is {lifecycle!r}, not 'active'"
    raw_sha256 = entry.get("raw_sha256")
    if not isinstance(raw_sha256, str):
        return "blocked", data, "resolved record target lacks raw SHA-256"
    if ref.get("sha256") != raw_sha256:
        return "fail", data, "recordRef SHA-256 does not equal target exact raw bytes"
    target_index = entry.get("index")
    if not isinstance(target_index, int):
        return "blocked", data, "resolved record target lacks bundle index"
    if source_index is None:
        source_index = _current_index(context)
    if not isinstance(source_index, int):
        return "blocked", data, "current record lacks bundle index"
    if target_index >= source_index:
        return "fail", data, "recordRef is a self-reference or forward reference"
    return "pass", data, "recordRef resolves to an integrity-verified active earlier target"


def _combine_ref_results(
    obligation_id: str,
    results: Iterable[tuple[str, Mapping[str, Any] | None, str]],
    location: str,
) -> dict[str, Any]:
    values = list(results)
    failed = [message for status, _, message in values if status == "fail"]
    if failed:
        return _fail(obligation_id, location, "; ".join(failed))
    blocked = [message for status, _, message in values if status == "blocked"]
    if blocked:
        return _blocked(obligation_id, location, "; ".join(blocked))
    return _pass(obligation_id)


def _iter_record_refs(node: Any):
    if isinstance(node, Mapping):
        if {"contract_name", "schema_version", "record_id", "sha256", "role"}.issubset(node):
            yield node
        for value in node.values():
            yield from _iter_record_refs(value)
    elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
        for value in node:
            yield from _iter_record_refs(value)


def _bundle_dag_result(obligation_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    records = _records(context)
    if not records:
        return _blocked(obligation_id, "$", "bundle record index is unavailable")
    seen_entries: set[int] = set()
    for entry in records.values():
        if not isinstance(entry, Mapping) or id(entry) in seen_entries:
            continue
        seen_entries.add(id(entry))
        data = _entry_data(entry)
        source_index = entry.get("index")
        if data is None or not isinstance(source_index, int):
            return _blocked(obligation_id, "$", "bundle record entry lacks parsed data or index")
        results = [
            _resolve_ref(context, ref, source_index=source_index)
            for ref in _iter_record_refs(data)
        ]
        combined = _combine_ref_results(obligation_id, results, "$" )
        if combined["status"] != "pass":
            return combined
    return _pass(obligation_id, "All recordRefs form an integrity-verified active backward-only DAG.")


def _artifact_result(context: Mapping[str, Any], file_ref: Mapping[str, Any]) -> tuple[str, str]:
    label = file_ref.get("label")
    artifacts = context.get("artifacts_by_label")
    if not isinstance(label, str) or not isinstance(artifacts, Mapping):
        return "blocked", "artifact label/index is unavailable"
    artifact = artifacts.get(label)
    if not isinstance(artifact, Mapping):
        return "fail", f"artifact {label!r} is absent from the bundle index"
    if artifact.get("integrity_verified") is not True:
        return "blocked", f"artifact {label!r} is not integrity-verified"
    raw_sha256 = artifact.get("raw_sha256")
    if not isinstance(raw_sha256, str):
        return "blocked", f"artifact {label!r} lacks raw SHA-256"
    if file_ref.get("sha256") != raw_sha256:
        return "fail", f"artifact {label!r} raw SHA-256 does not match fileRef"
    expected_bytes = file_ref.get("bytes")
    actual_bytes = artifact.get("bytes")
    if isinstance(expected_bytes, int) and isinstance(actual_bytes, int) and expected_bytes != actual_bytes:
        return "fail", f"artifact {label!r} byte count does not match fileRef"
    return "pass", f"artifact {label!r} is integrity-verified active"


def _combine_artifacts(obligation_id: str, values: Iterable[tuple[str, str]], location: str) -> dict[str, Any]:
    results = list(values)
    failures = [message for status, message in results if status == "fail"]
    if failures:
        return _fail(obligation_id, location, "; ".join(failures))
    blockers = [message for status, message in results if status == "blocked"]
    if blockers:
        return _blocked(obligation_id, location, "; ".join(blockers))
    return _pass(obligation_id)


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _argv_sha256(argv: Any) -> str | None:
    if (
        not isinstance(argv, Sequence)
        or isinstance(argv, (str, bytes, bytearray))
        or not all(isinstance(item, str) for item in argv)
    ):
        return None
    raw = json.dumps(list(argv), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _registry(context: Mapping[str, Any], key: str, default: Any = None) -> Any:
    snapshots = context.get("registry_snapshots")
    return snapshots.get(key, default) if isinstance(snapshots, Mapping) else default


def _operation_route(
    context: Mapping[str, Any], skill_id: Any, operation_id: Any
) -> tuple[str, Mapping[str, Any] | None, str]:
    snapshot = _registry(context, "operation_routes")
    if not isinstance(snapshot, Mapping):
        return "blocked", None, "canonical operation-routes snapshot is unavailable"
    routes = snapshot.get("routes")
    if not isinstance(routes, Mapping):
        return "blocked", None, "canonical operation-routes table is unavailable"
    route = routes.get(skill_id)
    if not isinstance(route, Mapping):
        return "fail", None, "skill route is absent from canonical operation-routes snapshot"
    if route.get("lifecycle") != "active" or route.get("routable") is not True:
        return "fail", None, "skill route is not active and routable"
    actions = route.get("actions")
    if not isinstance(actions, Mapping):
        return "blocked", None, "active skill route has no action table"
    action = actions.get(operation_id)
    if not isinstance(action, Mapping):
        return "fail", None, "operation is absent from the active skill route"
    return "pass", action, "operation resolves in canonical registry snapshot"


def _core(context: Mapping[str, Any], key: str, default: Any = None) -> Any:
    checks = context.get("core_checks")
    return checks.get(key, default) if isinstance(checks, Mapping) else default


def _resolved_data(context: Mapping[str, Any], ref: Any) -> tuple[str, Mapping[str, Any] | None, str]:
    return _resolve_ref(context, ref)


def _current_or_blocked(obligation_id: str, context: Mapping[str, Any]) -> tuple[Mapping[str, Any] | None, dict[str, Any] | None]:
    data = _current_data(context)
    if data is None:
        return None, _blocked(obligation_id, "$", "current_record.data is unavailable")
    return data, None


# Legacy run manifests remain upstream, immutable pre-decision evidence.
@_handler("LEGACY_RUN_PREDECISION_SCIENTIFIC_STATE")
def _legacy_run_predecision(context):
    oid = "LEGACY_RUN_PREDECISION_SCIENTIFIC_STATE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    run_status = data.get("status")
    acceptance = data.get("scientific_acceptance")
    if not isinstance(run_status, str) or not isinstance(acceptance, str):
        return _blocked(oid, "$", "run status/scientific acceptance is unavailable")
    if run_status not in {"planned", "running", "completed", "stopped", "failed"}:
        return _fail(
            oid,
            "$.status",
            "legacy run status exceeds the immutable technical-state vocabulary",
        )
    if acceptance not in {"not_assessed", "requires_human_review"}:
        return _fail(oid, "$.scientific_acceptance", "legacy run scientific state exceeds the pre-decision ceiling")
    if run_status != "completed" and acceptance != "not_assessed":
        return _fail(
            oid,
            "$.scientific_acceptance",
            "only a completed run may be marked requires_human_review",
        )
    return _pass(oid)


@_handler("LEGACY_RUN_EVIDENCE_HASH_STATUS_MATCH")
def _legacy_run_evidence(context):
    oid = "LEGACY_RUN_EVIDENCE_HASH_STATUS_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    evidence = data.get("evidence")
    if (
        not isinstance(evidence, Sequence)
        or isinstance(evidence, (str, bytes, bytearray))
    ):
        return _blocked(oid, "$.evidence", "run evidence array is unavailable or malformed")
    for index, item in enumerate(evidence):
        location = f"$.evidence[{index}]"
        if not isinstance(item, Mapping):
            return _blocked(oid, location, "run evidence entry is unavailable or malformed")
        status = item.get("status")
        if not isinstance(status, str):
            return _blocked(oid, f"{location}.status", "run evidence status is unavailable")
        digest = item.get("sha256")
        if status == "present":
            if not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None:
                return _fail(
                    oid,
                    f"{location}.sha256",
                    "present run evidence must carry a 64-character lowercase SHA-256",
                )
        elif status == "missing" and digest is not None:
            return _fail(
                oid,
                f"{location}.sha256",
                "missing run evidence cannot carry a content hash",
            )
        elif digest is not None and (
            not isinstance(digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", digest) is None
        ):
            return _fail(
                oid,
                f"{location}.sha256",
                "non-null run evidence hashes must be lowercase SHA-256 values",
            )
    return _pass(oid)


# Campaign records may summarize cost, but accepted/rejected science must be
# inherited through a complete downstream human-decision chain.
def _campaign_source(context: Mapping[str, Any], data: Mapping[str, Any]):
    return _resolved_data(context, data.get("source_run_ref"))


@_handler("CAMPAIGN_SOURCE_RUN_BINDING_MATCH")
def _campaign_source_run(context):
    oid = "CAMPAIGN_SOURCE_RUN_BINDING_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    source_ref = data.get("source_run_ref")
    if not isinstance(source_ref, Mapping):
        return _fail(oid, "$.source_run_ref", "campaign source_run_ref is required")
    if _ref_identity(source_ref) is None or source_ref.get("contract_name") != "run-manifest":
        return _fail(oid, "$.source_run_ref", "campaign source must be a versioned run-manifest recordRef")
    status, run, message = _campaign_source(context, data)
    if status != "pass":
        return _blocked(oid, "$.source_run_ref", message) if status == "blocked" else _fail(oid, "$.source_run_ref", message)
    if (
        data.get("run_manifest_id") != source_ref.get("record_id")
        or data.get("source_manifest_sha256") != source_ref.get("sha256")
        or _identity_from_data(run) != _ref_identity(source_ref)
    ):
        return _fail(
            oid,
            "$",
            "campaign redundant run identity/hash fields do not bind the exact source run",
        )
    if data.get("code") != run.get("code"):
        return _fail(oid, "$.code", "campaign code differs from its source run")
    outcome = data.get("outcome")
    if not isinstance(outcome, Mapping):
        return _blocked(oid, "$.outcome", "campaign outcome is unavailable")
    campaign_status = outcome.get("status")
    run_status = run.get("status")
    compatible = {
        "completed-unreviewed": "completed",
        "accepted": "completed",
        "rejected": "completed",
        "failed": "failed",
        "stopped": "stopped",
    }
    if compatible.get(campaign_status) != run_status:
        return _fail(
            oid,
            "$.outcome.status",
            "campaign outcome is incompatible with the source run technical state",
        )
    if run.get("scientific_acceptance") not in {
        "not_assessed",
        "requires_human_review",
    }:
        return _fail(
            oid,
            "$.source_run_ref",
            "source run improperly carries an accepted/rejected scientific verdict",
        )
    return _pass(oid)


def _campaign_acceptance_coherence(outcome: Mapping[str, Any]) -> bool:
    status = outcome.get("status")
    acceptance = outcome.get("scientific_acceptance")
    accepted = outcome.get("scientifically_accepted")
    if status == "accepted":
        return acceptance == "accepted" and accepted is True
    if status == "rejected":
        return acceptance == "rejected" and accepted is False
    if status == "completed-unreviewed":
        return acceptance in {"not_assessed", "requires_human_review"} and accepted is False
    if status in {"failed", "stopped"}:
        return acceptance == "not_assessed" and accepted is False
    return False


@_handler("CAMPAIGN_ACCEPTANCE_CHAIN_MATCH")
def _campaign_acceptance_chain(context):
    oid = "CAMPAIGN_ACCEPTANCE_CHAIN_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    outcome = data.get("outcome")
    chain = data.get("acceptance_evidence")
    if not isinstance(outcome, Mapping) or not isinstance(chain, Mapping):
        return _blocked(oid, "$", "campaign outcome/acceptance evidence is unavailable")
    if not _campaign_acceptance_coherence(outcome):
        return _fail(oid, "$.outcome", "campaign scientific status, verdict, and boolean are incoherent")

    ref_fields = (
        "calculation_record_ref",
        "decision_ref",
        "postdecision_claim_map_ref",
    )
    campaign_status = outcome.get("status")
    if campaign_status not in {"accepted", "rejected"}:
        return _pass(oid) if all(chain.get(field) is None for field in ref_fields) else _fail(
            oid,
            "$.acceptance_evidence",
            "non-decided campaign outcomes cannot carry acceptance-chain references",
        )

    refs = [chain.get(field) for field in ref_fields]
    if not all(isinstance(ref, Mapping) for ref in refs):
        return _fail(
            oid,
            "$.acceptance_evidence",
            "accepted/rejected campaign requires calculation, decision, and post-decision claim refs",
        )
    resolved = [_resolved_data(context, ref) for ref in refs]
    failures = [message for status, _, message in resolved if status == "fail"]
    if failures:
        return _fail(oid, "$.acceptance_evidence", "; ".join(failures))
    blockers = [message for status, _, message in resolved if status == "blocked"]
    if blockers:
        return _blocked(oid, "$.acceptance_evidence", "; ".join(blockers))
    calculation, decision, claim_map = [target for _, target, _ in resolved]
    calculation_ref, decision_ref, claim_ref = refs
    source_ref = data.get("source_run_ref")
    if not _same_ref_target(calculation.get("payload_ref"), source_ref):
        return _fail(
            oid,
            "$.acceptance_evidence.calculation_record_ref",
            "acceptance calculation does not wrap the exact source run",
        )
    calculation_state = calculation.get("status", {})
    if (
        calculation_state.get("scientific_acceptance") != "requires_human_review"
        or calculation.get("scientific_decision_ref") is not None
    ):
        return _fail(
            oid,
            "$.acceptance_evidence.calculation_record_ref",
            "campaign acceptance must start from an immutable pre-decision calculation",
        )
    expected = campaign_status
    if not (
        decision.get("decision_type") == "scientific-acceptance"
        and decision.get("outcome") == expected
        and decision.get("scientific_acceptance") == expected
        and decision.get("decided_by", {}).get("actor_type") == "human"
        and _same_ref_target(decision.get("subject_ref"), calculation_ref)
    ):
        return _fail(
            oid,
            "$.acceptance_evidence.decision_ref",
            "campaign decision is not the coherent human verdict on the exact calculation",
        )
    subject_matches = any(
        _same_ref_target(subject, calculation_ref)
        for subject in claim_map.get("subject_records", [])
    )
    if not (
        claim_map.get("scientific_acceptance") == expected
        and subject_matches
        and _same_ref_target(claim_map.get("scientific_decision_ref"), decision_ref)
    ):
        return _fail(
            oid,
            "$.acceptance_evidence.postdecision_claim_map_ref",
            "post-decision claim map does not bind the same calculation, decision, and verdict",
        )

    entries = [_lookup_identity(context, _ref_identity(ref)) for ref in refs]
    indexes = [entry.get("index") if isinstance(entry, Mapping) else None for entry in entries]
    if not all(isinstance(index, int) for index in indexes):
        return _blocked(oid, "$.acceptance_evidence", "acceptance-chain bundle indexes are unavailable")
    if not indexes[0] < indexes[1] < indexes[2] < _current_index(context):
        return _fail(
            oid,
            "$.acceptance_evidence",
            "acceptance-chain records are not ordered calculation -> decision -> claim -> campaign",
        )
    return _pass(oid)


@_handler("CAMPAIGN_RECORD_REF_DAG_ACYCLIC")
def _campaign_dag(context):
    return _bundle_dag_result("CAMPAIGN_RECORD_REF_DAG_ACYCLIC", context)


# Efficiency recommendations can cite campaign measurements, but positive
# recommendation maturity is recomputed from accepted evidence rather than
# trusted from self-reported IDs or confidence labels.
_APPLICABILITY_FIELDS = (
    "code",
    "code_version",
    "task_type",
    "system_class",
    "atom_count",
    "scientific_protocol_id",
)


def _recommendation_campaigns(
    context: Mapping[str, Any], data: Mapping[str, Any]
) -> tuple[str, list[Mapping[str, Any]], str]:
    ids = data.get("evidence_record_ids")
    refs = data.get("evidence_record_refs")
    if (
        not isinstance(ids, Sequence)
        or isinstance(ids, (str, bytes, bytearray))
        or not isinstance(refs, Sequence)
        or isinstance(refs, (str, bytes, bytearray))
    ):
        return "blocked", [], "recommendation evidence IDs/refs are unavailable"
    if not all(isinstance(item, str) for item in ids) or not all(
        isinstance(ref, Mapping) for ref in refs
    ):
        return "blocked", [], "recommendation evidence IDs/refs are malformed"
    if len(ids) != len(set(ids)) or len(refs) != len(
        {_ref_identity(ref) for ref in refs}
    ):
        return "fail", [], "recommendation evidence IDs/refs are not unique"
    if len(ids) != len(refs) or any(
        evidence_id != ref.get("record_id")
        for evidence_id, ref in zip(ids, refs)
    ):
        return "fail", [], "recommendation evidence IDs and refs are not one-to-one in deterministic order"

    campaigns: list[Mapping[str, Any]] = []
    for ref in refs:
        if ref.get("contract_name") != "campaign-record":
            return "fail", [], "recommendation evidence ref is not campaign-record@1.0"
        status, campaign, message = _resolved_data(context, ref)
        if status != "pass":
            return status, [], message
        if campaign.get("record_id") != ref.get("record_id"):
            return "fail", [], "resolved campaign payload identity differs from its recordRef"
        campaigns.append(campaign)
    return "pass", campaigns, "all recommendation campaign refs resolve"


@_handler("RECOMMENDATION_EVIDENCE_CAMPAIGNS_MATCH")
def _recommendation_evidence(context):
    oid = "RECOMMENDATION_EVIDENCE_CAMPAIGNS_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, campaigns, message = _recommendation_campaigns(context, data)
    if status == "blocked":
        return _blocked(oid, "$.evidence_record_refs", message)
    if status == "fail":
        return _fail(oid, "$.evidence_record_refs", message)
    applicability = data.get("applicability")
    if not isinstance(applicability, Mapping):
        return _blocked(oid, "$.applicability", "recommendation applicability is unavailable")
    for campaign in campaigns:
        if any(campaign.get(field) != applicability.get(field) for field in _APPLICABILITY_FIELDS):
            return _fail(
                oid,
                "$.applicability",
                "referenced campaign does not exactly match all six applicability fields",
            )
    return _pass(oid)


@_handler("RECOMMENDATION_POSITIVE_EVIDENCE_ACCEPTED")
def _recommendation_positive(context):
    oid = "RECOMMENDATION_POSITIVE_EVIDENCE_ACCEPTED"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    recommendation_status = data.get("status")
    if recommendation_status not in {
        "validated-for-this-campaign",
        "cross-campaign-validated",
    }:
        return _pass(oid, "Recommendation is not in a positive validation state.")
    status, campaigns, message = _recommendation_campaigns(context, data)
    if status == "blocked":
        return _blocked(oid, "$.evidence_record_refs", message)
    if status == "fail":
        return _fail(oid, "$.evidence_record_refs", message)
    for campaign in campaigns:
        outcome = campaign.get("outcome")
        if not isinstance(outcome, Mapping):
            return _blocked(oid, "$.evidence_record_refs", "referenced campaign outcome is unavailable")
        if not (
            outcome.get("status") == "accepted"
            and outcome.get("scientific_acceptance") == "accepted"
            and outcome.get("scientifically_accepted") is True
        ):
            return _fail(
                oid,
                "$.evidence_record_refs",
                "positive recommendation cites a campaign without accepted scientific evidence",
            )

    baseline = data.get("baseline_configuration_id")
    recommended = data.get("recommended_configuration_id")
    if not isinstance(baseline, str) or not isinstance(recommended, str) or baseline == recommended:
        return _fail(
            oid,
            "$.[baseline_configuration_id,recommended_configuration_id]",
            "positive recommendation requires two distinct configuration IDs",
        )
    if any(
        campaign.get("configuration_id") not in {baseline, recommended}
        for campaign in campaigns
    ):
        return _fail(
            oid,
            "$.evidence_record_refs",
            "positive recommendation evidence contains an unrelated configuration",
        )
    grouped: dict[str, list[float]] = {baseline: [], recommended: []}
    for campaign in campaigns:
        core_hours = campaign.get("metrics", {}).get("core_hours")
        if not isinstance(core_hours, (int, float)) or isinstance(core_hours, bool):
            return _blocked(
                oid,
                "$.evidence_record_refs",
                "referenced campaign core-hours are unavailable",
            )
        grouped[campaign.get("configuration_id")].append(float(core_hours))
    if any(len(values) < 2 for values in grouped.values()):
        return _fail(
            oid,
            "$.evidence_record_refs",
            "each baseline/recommended configuration requires at least two accepted campaigns",
        )
    baseline_median = median(grouped[baseline])
    recommended_median = median(grouped[recommended])
    if baseline_median <= 0 or recommended_median >= baseline_median:
        return _fail(
            oid,
            "$.estimated_savings_fraction",
            "accepted campaign medians do not show a positive core-hour reduction",
        )
    expected_savings = (baseline_median - recommended_median) / baseline_median
    reported_savings = data.get("estimated_savings_fraction")
    if (
        not isinstance(reported_savings, (int, float))
        or isinstance(reported_savings, bool)
        or abs(float(reported_savings) - expected_savings) > 1e-12
    ):
        return _fail(
            oid,
            "$.estimated_savings_fraction",
            "reported savings does not match medians recomputed from accepted campaigns",
        )
    if recommendation_status == "cross-campaign-validated":
        return _blocked(
            oid,
            "$.status",
            "campaign-record@1.0 has no independent campaign identity, so cross-campaign validation cannot be proven",
        )
    if data.get("confidence") != "campaign":
        return _fail(
            oid,
            "$.confidence",
            "validated-for-this-campaign requires campaign confidence",
        )
    return _pass(oid)


@_handler("RECOMMENDATION_RECORD_REF_DAG_ACYCLIC")
def _recommendation_dag(context):
    return _bundle_dag_result("RECOMMENDATION_RECORD_REF_DAG_ACYCLIC", context)


# Calculation envelope handlers.
@_handler("CALC_PAYLOAD_REF_HASH_RESOLVES")
def _calc_payload_ref(context):
    oid = "CALC_PAYLOAD_REF_HASH_RESOLVES"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, [_resolved_data(context, data.get("payload_ref"))], "$.payload_ref")


@_handler("CALC_DOMAIN_PAYLOAD_CONTRACT_MATCH")
def _calc_domain_payload(context):
    oid = "CALC_DOMAIN_PAYLOAD_CONTRACT_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    # Reviewed domain-to-interface bindings.  Reserved domains deliberately have
    # no active payload binding and therefore block rather than guessing.
    domain_payload_contracts = {"periodic-dft": ("run-manifest",)}
    allowed = domain_payload_contracts.get(data.get("domain"))
    payload_ref = data.get("payload_ref", {})
    contract = payload_ref.get("contract_name")
    if not allowed:
        return _blocked(oid, "$.domain", "domain has no active payload contract")
    if contract not in allowed:
        return _fail(oid, "$.payload_ref.contract_name", "payload contract is not registered for the calculation domain")
    interfaces = _registry(context, "interfaces")
    if not isinstance(interfaces, Mapping) or not isinstance(interfaces.get("interfaces"), Mapping):
        return _blocked(oid, "$.payload_ref", "canonical interface registry snapshot is unavailable")
    interface_key = f"{contract}@{payload_ref.get('schema_version')}"
    interface = interfaces["interfaces"].get(interface_key)
    if not isinstance(interface, Mapping):
        return _fail(oid, "$.payload_ref", "payload interface is absent from the canonical registry snapshot")
    return _pass(oid) if interface.get("lifecycle") == "active" else _fail(
        oid,
        "$.payload_ref",
        "payload interface is not active in the canonical registry snapshot",
    )


@_handler("CALC_ENGINE_PAYLOAD_ID_MATCH")
def _calc_engine_payload(context):
    oid = "CALC_ENGINE_PAYLOAD_ID_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, payload, message = _resolved_data(context, data.get("payload_ref"))
    if status == "blocked":
        return _blocked(oid, "$.payload_ref", message)
    if status == "fail":
        return _fail(oid, "$.payload_ref", message)
    payload_engine = payload.get("code", payload.get("software_id"))
    engine = data.get("engine", {}).get("software_id")
    return _pass(oid) if isinstance(engine, str) and engine == payload_engine else _fail(oid, "$.engine.software_id", "envelope engine does not match payload engine")


@_handler("CALC_PAYLOAD_STATUS_SUPPORTS_ENVELOPE")
def _calc_payload_status(context):
    oid = "CALC_PAYLOAD_STATUS_SUPPORTS_ENVELOPE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, payload, message = _resolved_data(context, data.get("payload_ref"))
    if status == "blocked":
        return _blocked(oid, "$.payload_ref", message)
    if status == "fail":
        return _fail(oid, "$.payload_ref", message)
    envelope_status = data.get("status", {})
    if envelope_status.get("normalized_status") == "completed" and payload.get("status") != "completed":
        return _fail(oid, "$.status.normalized_status", "completed envelope points to a non-completed payload")
    if envelope_status.get("scientific_acceptance") == "requires_human_review" and payload.get("scientific_acceptance") != "not_assessed":
        return _fail(oid, "$.status.scientific_acceptance", "review-ready envelope must point to a pre-decision payload")
    return _pass(oid)


@_handler("CALC_PARENT_LINEAGE_RESOLVES")
def _calc_parents(context):
    oid = "CALC_PARENT_LINEAGE_RESOLVES"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, (_resolved_data(context, ref) for ref in data.get("parent_records", [])), "$.parent_records")


@_handler("CALC_GATE_EVIDENCE_REFS_RESOLVE")
def _calc_gate_refs(context):
    oid = "CALC_GATE_EVIDENCE_REFS_RESOLVE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    refs = [ref for check in data.get("gates", {}).get("checks", []) for ref in check.get("evidence_refs", [])]
    return _combine_ref_results(oid, (_resolved_data(context, ref) for ref in refs), "$.gates.checks")


@_handler("CALC_RECORD_REF_DAG_ACYCLIC")
def _calc_dag(context):
    return _bundle_dag_result("CALC_RECORD_REF_DAG_ACYCLIC", context)


# Execution request handlers.
def _request_plan(context, data):
    return _resolved_data(context, data.get("workflow_plan_ref"))


def _request_step(plan, data):
    return next((step for step in plan.get("steps", []) if step.get("step_id") == data.get("workflow_step_id")), None)


@_handler("REQUEST_WORKFLOW_STEP_REF_RESOLVES")
def _request_step_resolves(context):
    oid = "REQUEST_WORKFLOW_STEP_REF_RESOLVES"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, plan, message = _request_plan(context, data)
    if status == "blocked":
        return _blocked(oid, "$.workflow_plan_ref", message)
    if status == "fail":
        return _fail(oid, "$.workflow_plan_ref", message)
    return _pass(oid) if _request_step(plan, data) is not None else _fail(oid, "$.workflow_step_id", "workflow step does not resolve in referenced plan")


@_handler("REQUEST_WORKFLOW_PLAN_REF_HASH_MATCH")
def _request_plan_hash(context):
    oid = "REQUEST_WORKFLOW_PLAN_REF_HASH_MATCH"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, [_request_plan(context, data)], "$.workflow_plan_ref")


@_handler("REQUEST_OPERATION_ROUTE_BINDING")
def _request_route(context):
    oid = "REQUEST_OPERATION_ROUTE_BINDING"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, plan, message = _request_plan(context, data)
    if status != "pass":
        return _blocked(oid, "$.workflow_plan_ref", message) if status == "blocked" else _fail(oid, "$.workflow_plan_ref", message)
    step = _request_step(plan, data)
    if step is None:
        return _fail(oid, "$.workflow_step_id", "workflow step is absent")
    if step.get("operation_id") != data.get("operation_id") or step.get("route_lifecycle") != "active":
        return _fail(oid, "$.operation_id", "request is not bound to the active step operation")
    route_status, _, route_message = _operation_route(
        context, step.get("skill_id"), step.get("operation_id")
    )
    if route_status == "blocked":
        return _blocked(oid, "$.operation_id", route_message)
    return _pass(oid) if route_status == "pass" else _fail(
        oid, "$.operation_id", route_message
    )


@_handler("REQUEST_AUTHORIZATION_POLICY_MATCH")
def _request_authorization(context):
    oid = "REQUEST_AUTHORIZATION_POLICY_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, plan, message = _request_plan(context, data)
    if status != "pass":
        return _blocked(oid, "$.workflow_plan_ref", message) if status == "blocked" else _fail(oid, "$.workflow_plan_ref", message)
    policy = plan.get("authorization_policy", {})
    requirement = data.get("authorization_requirement", {})
    required = policy.get("human_decision_required") is True and policy.get("lease_required") is True
    matches = (
        requirement.get("required") == required
        and set(requirement.get("side_effects", [])).issubset(set(policy.get("side_effects", [])))
        and set(requirement.get("scope_labels", [])).issubset(set(policy.get("scope_labels", [])))
    )
    return _pass(oid) if matches else _fail(oid, "$.authorization_requirement", "request authorization exceeds or contradicts workflow policy")


@_handler("REQUEST_ARGV_TEMPLATE_BINDING")
def _request_argv_template(context):
    oid = "REQUEST_ARGV_TEMPLATE_BINDING"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, plan, message = _request_plan(context, data)
    if status != "pass":
        return _blocked(oid, "$.workflow_plan_ref", message) if status == "blocked" else _fail(oid, "$.workflow_plan_ref", message)
    step = _request_step(plan, data)
    if step is None:
        return _fail(oid, "$.workflow_step_id", "workflow step is absent")
    route_status, action, route_message = _operation_route(
        context, step.get("skill_id"), data.get("operation_id")
    )
    if route_status != "pass":
        return _blocked(oid, "$.argv", route_message) if route_status == "blocked" else _fail(oid, "$.argv", route_message)
    template = action.get("argv")
    argv = data.get("argv")
    if (
        not isinstance(template, Sequence)
        or isinstance(template, (str, bytes, bytearray))
        or not isinstance(argv, Sequence)
        or isinstance(argv, (str, bytes, bytearray))
    ):
        return _blocked(oid, "$.argv", "operation/request argv sequence is unavailable")
    return _pass(oid) if tuple(template) == tuple(argv) else _fail(
        oid, "$.argv", "argv differs from the canonical registered operation template"
    )


@_handler("REQUEST_INPUT_HASH_CONTENT_MATCHES")
def _request_inputs(context):
    oid = "REQUEST_INPUT_HASH_CONTENT_MATCHES"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    refs = [item for item in data.get("inputs", []) if item.get("availability") == "present"]
    return _combine_artifacts(oid, (_artifact_result(context, item) for item in refs), "$.inputs")


@_handler("REQUEST_PARENT_LINEAGE_RESOLVES")
def _request_parents(context):
    oid = "REQUEST_PARENT_LINEAGE_RESOLVES"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, (_resolved_data(context, ref) for ref in data.get("parent_records", [])), "$.parent_records")


@_handler("REQUEST_RECORD_REF_DAG_ACYCLIC")
def _request_dag(context):
    return _bundle_dag_result("REQUEST_RECORD_REF_DAG_ACYCLIC", context)


# Lease handlers.
def _lease_request(context, data):
    return _resolved_data(context, data.get("request_ref"))


def _lease_decision(context, data):
    return _resolved_data(context, data.get("authorization_decision_ref"))


@_handler("LEASE_TIME_ORDER")
def _lease_time(context):
    oid = "LEASE_TIME_ORDER"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    issued, expires = _parse_time(data.get("issued_utc")), _parse_time(data.get("expires_utc"))
    if issued is None or expires is None:
        return _blocked(oid, "$.issued_utc", "lease timestamps are unavailable")
    duration = (expires - issued).total_seconds()
    return _pass(oid) if duration > 0 and duration == data.get("lease_duration_s") else _fail(oid, "$.lease_duration_s", "lease duration does not match ordered timestamps")


@_handler("LEASE_AUTHORIZATION_TIME_CHAIN")
def _lease_auth_time(context):
    oid = "LEASE_AUTHORIZATION_TIME_CHAIN"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    request_status, request, request_message = _lease_request(context, data)
    decision_status, decision, decision_message = _lease_decision(context, data)
    if "fail" in {request_status, decision_status}:
        return _fail(oid, "$", f"{request_message}; {decision_message}")
    if "blocked" in {request_status, decision_status}:
        return _blocked(oid, "$", f"{request_message}; {decision_message}")
    created = _parse_time(request.get("created_utc"))
    decided = _parse_time(decision.get("decided_utc"))
    issued = _parse_time(data.get("issued_utc"))
    expires = _parse_time(data.get("expires_utc"))
    valid_until = _parse_time(decision.get("valid_until_utc"))
    if None in {created, decided, issued, expires, valid_until}:
        return _blocked(oid, "$", "authorization time chain is incomplete")
    return _pass(oid) if created <= decided <= issued < expires <= valid_until else _fail(oid, "$", "request, decision, lease, and authorization expiry are not ordered")


@_handler("LEASE_REQUEST_REF_HASH_MATCH")
def _lease_request_hash(context):
    oid = "LEASE_REQUEST_REF_HASH_MATCH"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, [_lease_request(context, data)], "$.request_ref")


@_handler("LEASE_AUTHORIZATION_DECISION_REF_HASH_MATCH")
def _lease_decision_hash(context):
    oid = "LEASE_AUTHORIZATION_DECISION_REF_HASH_MATCH"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, [_lease_decision(context, data)], "$.authorization_decision_ref")


@_handler("LEASE_AUTHORIZATION_DECISION_APPROVED_REQUEST_MATCH")
def _lease_decision_request(context):
    oid = "LEASE_AUTHORIZATION_DECISION_APPROVED_REQUEST_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    rs, request, rm = _lease_request(context, data)
    ds, decision, dm = _lease_decision(context, data)
    if "fail" in {rs, ds}:
        return _fail(oid, "$", f"{rm}; {dm}")
    if "blocked" in {rs, ds}:
        return _blocked(oid, "$", f"{rm}; {dm}")
    subject = decision.get("subject_ref", {})
    request_identity = _identity_from_data(request)
    matches = (
        decision.get("decision_type") == "execution-authorization"
        and decision.get("outcome") == "approved"
        and decision.get("decided_by", {}).get("actor_type") == "human"
        and _ref_identity(subject) == request_identity
        and subject.get("sha256") == data.get("request_ref", {}).get("sha256")
        and set(request.get("authorization_requirement", {}).get("scope_labels", [])).issubset(set(decision.get("scope_labels", [])))
    )
    return _pass(oid) if matches else _fail(oid, "$.authorization_decision_ref", "authorization decision does not approve the exact request and scope")


@_handler("LEASE_ARGV_HASH_MATCH")
def _lease_argv(context):
    oid = "LEASE_ARGV_HASH_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, request, message = _lease_request(context, data)
    if status != "pass":
        return _blocked(oid, "$.request_ref", message) if status == "blocked" else _fail(oid, "$.request_ref", message)
    expected = _argv_sha256(request.get("argv"))
    if expected is None:
        return _blocked(oid, "$.grant.argv_sha256", "request argv cannot be hashed")
    return _pass(oid) if data.get("grant", {}).get("argv_sha256") == expected else _fail(oid, "$.grant.argv_sha256", "lease argv hash differs from immutable request argv")


def _lease_subset_handler(oid, context, check, location, message):
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, request, reason = _lease_request(context, data)
    if status != "pass":
        return _blocked(oid, "$.request_ref", reason) if status == "blocked" else _fail(oid, "$.request_ref", reason)
    try:
        matches = check(data, request)
    except (KeyError, TypeError, ValueError):
        return _blocked(oid, location, "required grant/request fields are unavailable")
    return _pass(oid) if matches else _fail(oid, location, message)


@_handler("LEASE_INPUT_HASH_SET_SUBSET")
def _lease_inputs(context):
    return _lease_subset_handler(
        "LEASE_INPUT_HASH_SET_SUBSET", context,
        lambda lease, request: set(lease["grant"]["input_sha256"]).issubset({item["sha256"] for item in request["inputs"] if item["availability"] == "present"}),
        "$.grant.input_sha256", "lease grants unrequested input hashes",
    )


@_handler("LEASE_ENVIRONMENT_PROFILE_SUBSET")
def _lease_environment(context):
    return _lease_subset_handler(
        "LEASE_ENVIRONMENT_PROFILE_SUBSET", context,
        lambda lease, request: set(lease["grant"]["environment_profile_ids"]).issubset({request["environment_profile_id"]}),
        "$.grant.environment_profile_ids", "lease grants an unrequested environment",
    )


@_handler("LEASE_SCHEDULER_PROFILE_SUBSET")
def _lease_scheduler(context):
    return _lease_subset_handler(
        "LEASE_SCHEDULER_PROFILE_SUBSET", context,
        lambda lease, request: set(lease["grant"]["scheduler_profile_ids"]).issubset({request["resources"]["scheduler_profile_id"]} if request["resources"]["scheduler_profile_id"] is not None else set()),
        "$.grant.scheduler_profile_ids", "lease grants an unrequested scheduler profile",
    )


@_handler("LEASE_RESOURCE_CEILING_SUBSET")
def _lease_resources(context):
    names = ("nodes", "mpi_ranks", "threads_per_rank", "gpus", "memory_mb", "walltime_s")
    return _lease_subset_handler(
        "LEASE_RESOURCE_CEILING_SUBSET", context,
        lambda lease, request: all(lease["grant"]["resource_ceiling"][name] <= request["resources"][name] for name in names),
        "$.grant.resource_ceiling", "lease resource ceiling exceeds request",
    )


@_handler("LEASE_SIDE_EFFECT_SUBSET")
def _lease_effects(context):
    return _lease_subset_handler(
        "LEASE_SIDE_EFFECT_SUBSET", context,
        lambda lease, request: set(lease["grant"]["side_effects"]).issubset(set(request["authorization_requirement"]["side_effects"])),
        "$.grant.side_effects", "lease grants unrequested side effects",
    )


@_handler("LEASE_OUTPUT_LABEL_SET_SUBSET")
def _lease_outputs(context):
    return _lease_subset_handler(
        "LEASE_OUTPUT_LABEL_SET_SUBSET", context,
        lambda lease, request: set(lease["grant"]["output_labels"]).issubset({item["label"] for item in request["expected_outputs"]}),
        "$.grant.output_labels", "lease grants unrequested output labels",
    )


@_handler("LEASE_SINGLE_USE_CONSUMPTION")
def _lease_consumption(context):
    oid = "LEASE_SINGLE_USE_CONSUMPTION"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    lease_id = data.get("lease_id")
    consumers = 0
    for entry in _records(context).values():
        record = _entry_data(entry)
        if not isinstance(record, Mapping) or record.get("contract_name") != "execution-record":
            continue
        ref = record.get("lease_ref")
        if isinstance(ref, Mapping) and ref.get("record_id") == lease_id:
            consumers += 1
    maximum = data.get("grant", {}).get("maximum_executions")
    if not isinstance(maximum, int):
        return _blocked(oid, "$.grant.maximum_executions", "lease maximum execution count is unavailable")
    return _pass(oid) if consumers <= maximum else _fail(oid, "$.grant.maximum_executions", "lease has more consumers than authorized")


@_handler("LEASE_RECORD_REF_DAG_ACYCLIC")
def _lease_dag(context):
    return _bundle_dag_result("LEASE_RECORD_REF_DAG_ACYCLIC", context)


# Execution record handlers.
def _exec_request(context, data):
    return _resolved_data(context, data.get("request_ref"))


def _exec_lease(context, data):
    return _resolved_data(context, data.get("lease_ref"))


def _exec_plan(context, data):
    return _resolved_data(context, data.get("workflow_plan_ref"))


@_handler("EXEC_REQUEST_REF_HASH_MATCH")
def _exec_request_hash(context):
    oid = "EXEC_REQUEST_REF_HASH_MATCH"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, [_exec_request(context, data)], "$.request_ref")


@_handler("EXEC_WORKFLOW_PLAN_REF_HASH_MATCH")
def _exec_plan_hash(context):
    oid = "EXEC_WORKFLOW_PLAN_REF_HASH_MATCH"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, [_exec_plan(context, data)], "$.workflow_plan_ref")


@_handler("EXEC_LEASE_ACTIVE_REQUEST_MATCH")
def _exec_lease_request(context):
    oid = "EXEC_LEASE_ACTIVE_REQUEST_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    if data.get("dry_run") is True:
        return _pass(oid) if data.get("lease_ref") is None else _fail(oid, "$.lease_ref", "dry-run must not consume a lease")
    ls, lease, lm = _exec_lease(context, data)
    rs, request, rm = _exec_request(context, data)
    if "fail" in {ls, rs}:
        return _fail(oid, "$", f"{lm}; {rm}")
    if "blocked" in {ls, rs}:
        return _blocked(oid, "$", f"{lm}; {rm}")
    lease_request = lease.get("request_ref", {})
    matches = (
        lease.get("status") == "active"
        and _ref_identity(lease_request) == _identity_from_data(request)
        and lease_request.get("sha256") == data.get("request_ref", {}).get("sha256")
    )
    return _pass(oid) if matches else _fail(oid, "$.lease_ref", "lease is inactive or bound to another request")


def _exec_upstream(context, data):
    rs, request, rm = _exec_request(context, data)
    ls, lease, lm = _exec_lease(context, data)
    if data.get("dry_run") is True:
        return rs, request, None, rm
    if "fail" in {rs, ls}:
        return "fail", request, lease, f"{rm}; {lm}"
    if "blocked" in {rs, ls}:
        return "blocked", request, lease, f"{rm}; {lm}"
    return "pass", request, lease, "upstream request and lease resolve"


@_handler("EXEC_GRANTED_SCOPE_SUBSET")
def _exec_grant(context):
    oid = "EXEC_GRANTED_SCOPE_SUBSET"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    if data.get("dry_run") is True:
        return _pass(oid)
    status, request, lease, message = _exec_upstream(context, data)
    if status != "pass":
        return _blocked(oid, "$", message) if status == "blocked" else _fail(oid, "$", message)
    grant = lease.get("grant", {})
    resources = data.get("resources", {})
    ceiling = grant.get("resource_ceiling", {})
    names = ("nodes", "mpi_ranks", "threads_per_rank", "gpus", "memory_mb", "walltime_s")
    try:
        matches = (
            data.get("environment_profile_id") in grant.get("environment_profile_ids", [])
            and (resources.get("scheduler_profile_id") is None or resources.get("scheduler_profile_id") in grant.get("scheduler_profile_ids", []))
            and {item["sha256"] for item in data.get("inputs", []) if item.get("availability") == "present"}.issubset(set(grant.get("input_sha256", [])))
            and {item["label"] for item in data.get("outputs", [])}.issubset(set(grant.get("output_labels", [])))
            and all(resources[name] <= ceiling[name] for name in names)
        )
    except (KeyError, TypeError):
        return _blocked(oid, "$", "execution/grant scope fields are incomplete")
    return _pass(oid) if matches else _fail(oid, "$", "execution exceeds lease grant")


@_handler("EXEC_WORKFLOW_STEP_MATCH")
def _exec_step(context):
    oid = "EXEC_WORKFLOW_STEP_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    rs, request, rm = _exec_request(context, data)
    ps, plan, pm = _exec_plan(context, data)
    if "fail" in {rs, ps}:
        return _fail(oid, "$", f"{rm}; {pm}")
    if "blocked" in {rs, ps}:
        return _blocked(oid, "$", f"{rm}; {pm}")
    step_id = data.get("workflow_step_id")
    matches = step_id == request.get("workflow_step_id") and any(step.get("step_id") == step_id for step in plan.get("steps", []))
    return _pass(oid) if matches else _fail(oid, "$.workflow_step_id", "execution, request, and plan step identities differ")


@_handler("EXEC_REQUEST_CONTENT_MATCH")
def _exec_request_content(context):
    oid = "EXEC_REQUEST_CONTENT_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, request, message = _exec_request(context, data)
    if status != "pass":
        return _blocked(oid, "$.request_ref", message) if status == "blocked" else _fail(oid, "$.request_ref", message)
    resources, requested = data.get("resources", {}), request.get("resources", {})
    names = ("nodes", "mpi_ranks", "threads_per_rank", "gpus", "memory_mb", "walltime_s")
    try:
        matches = (
            data.get("working_directory_label") == request.get("working_directory_label")
            and data.get("environment_profile_id") == request.get("environment_profile_id")
            and {item["sha256"] for item in data.get("inputs", []) if item.get("availability") == "present"}.issubset({item["sha256"] for item in request.get("inputs", []) if item.get("availability") == "present"})
            and {item["label"] for item in data.get("outputs", [])}.issubset({item["label"] for item in request.get("expected_outputs", [])})
            and all(resources[name] <= requested[name] for name in names)
        )
    except (KeyError, TypeError):
        return _blocked(oid, "$", "execution/request content fields are incomplete")
    return _pass(oid) if matches else _fail(oid, "$", "execution content differs from or exceeds request")


@_handler("EXEC_ARGV_HASH_MATCH")
def _exec_argv(context):
    oid = "EXEC_ARGV_HASH_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    expected = _argv_sha256(data.get("argv"))
    if expected is None:
        return _blocked(oid, "$.argv", "execution argv cannot be hashed")
    if data.get("argv_sha256") != expected:
        return _fail(oid, "$.argv_sha256", "execution argv hash is not self-consistent")
    if data.get("dry_run") is True:
        status, request, message = _exec_request(context, data)
        if status != "pass":
            return _blocked(oid, "$.request_ref", message) if status == "blocked" else _fail(oid, "$.request_ref", message)
        return _pass(oid) if data.get("argv") == request.get("argv") else _fail(
            oid,
            "$.argv",
            "dry-run execution argv differs from its immutable request",
        )
    status, request, lease, message = _exec_upstream(context, data)
    if status != "pass":
        return _blocked(oid, "$", message) if status == "blocked" else _fail(oid, "$", message)
    if data.get("argv") != request.get("argv") or expected != lease.get("grant", {}).get("argv_sha256"):
        return _fail(oid, "$.argv", "execution argv differs from request or lease")
    return _pass(oid)


@_handler("EXEC_TIME_ORDER_AND_TIMINGS_MATCH")
def _exec_timings(context):
    oid = "EXEC_TIME_ORDER_AND_TIMINGS_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    timings = data.get("timings", {})
    if data.get("dry_run") is True:
        values = [data.get("started_utc"), data.get("finished_utc"), *timings.values()]
        return _pass(oid) if all(value is None for value in values) else _fail(oid, "$.timings", "dry-run contains execution timings")
    started, finished = _parse_time(data.get("started_utc")), _parse_time(data.get("finished_utc"))
    if started is None:
        return _blocked(oid, "$.started_utc", "execution start time is unavailable")
    terminal = data.get("status", {}).get("normalized_status") in {"succeeded", "failed", "timed-out", "cancelled"}
    if terminal:
        wall = timings.get("wall_time_s")
        if finished is None or not isinstance(wall, (int, float)):
            return _blocked(oid, "$.timings.wall_time_s", "terminal execution lacks finish/wall time")
        if started > finished or abs(wall - (finished - started).total_seconds()) > 1e-9:
            return _fail(oid, "$.timings.wall_time_s", "wall time does not match ordered timestamps")
    elif finished is not None:
        return _fail(oid, "$.finished_utc", "non-terminal execution has a finish timestamp")
    wall = timings.get("wall_time_s")
    cpu = timings.get("cpu_time_s")
    gpu = timings.get("gpu_time_s")
    resources = data.get("resources", {})
    if isinstance(cpu, (int, float)) and isinstance(wall, (int, float)):
        capacity = wall * resources.get("nodes", 0) * resources.get("mpi_ranks", 0) * resources.get("threads_per_rank", 0)
        if cpu > capacity + 1e-9:
            return _fail(oid, "$.timings.cpu_time_s", "CPU time exceeds allocated capacity")
    if resources.get("gpus") == 0 and gpu is not None:
        return _fail(oid, "$.timings.gpu_time_s", "GPU time reported with zero GPUs")
    return _pass(oid)


@_handler("EXEC_REQUEST_LEASE_EXECUTION_TIME_CHAIN")
def _exec_time_chain(context):
    oid = "EXEC_REQUEST_LEASE_EXECUTION_TIME_CHAIN"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    if data.get("dry_run") is True:
        return _pass(oid)
    status, request, lease, message = _exec_upstream(context, data)
    if status != "pass":
        return _blocked(oid, "$", message) if status == "blocked" else _fail(oid, "$", message)
    created = _parse_time(request.get("created_utc"))
    issued = _parse_time(lease.get("issued_utc"))
    expires = _parse_time(lease.get("expires_utc"))
    started = _parse_time(data.get("started_utc"))
    finished = _parse_time(data.get("finished_utc")) if data.get("finished_utc") is not None else None
    if None in {created, issued, expires, started}:
        return _blocked(oid, "$", "request/lease/execution timestamps are incomplete")
    valid = created <= issued <= started <= expires and (finished is None or started <= finished <= expires)
    return _pass(oid) if valid else _fail(oid, "$", "request, lease, and execution timestamps are not ordered")


@_handler("EXEC_INPUT_OUTPUT_HASH_CONTENT_MATCH")
def _exec_artifacts(context):
    oid = "EXEC_INPUT_OUTPUT_HASH_CONTENT_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    refs = [item for item in [*data.get("inputs", []), *data.get("outputs", [])] if item.get("availability") == "present"]
    return _combine_artifacts(oid, (_artifact_result(context, item) for item in refs), "$.[inputs,outputs]")


@_handler("EXEC_NATIVE_STATUS_EVIDENCE_MATCH")
def _exec_native_status(context):
    oid = "EXEC_NATIVE_STATUS_EVIDENCE_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    observed = _core(context, "native_status_evidence")
    if not isinstance(observed, Mapping):
        return _blocked(oid, "$.status", "native status evidence is unavailable")
    expected = {
        "scheduler": data.get("status", {}).get("native_scheduler_status"),
        "process": data.get("status", {}).get("native_process_status"),
        "application": data.get("status", {}).get("native_application_status"),
    }
    matches = all(value is None or observed.get(layer) == value for layer, value in expected.items())
    return _pass(oid) if matches else _fail(oid, "$.status", "normalized execution status is not backed by native evidence")


@_handler("EXEC_PARENT_LINEAGE_RESOLVES")
def _exec_parents(context):
    oid = "EXEC_PARENT_LINEAGE_RESOLVES"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, (_resolved_data(context, ref) for ref in data.get("parent_records", [])), "$.parent_records")


@_handler("EXEC_RECORD_REF_DAG_ACYCLIC")
def _exec_dag(context):
    return _bundle_dag_result("EXEC_RECORD_REF_DAG_ACYCLIC", context)


# Workflow plan handlers.
@_handler("WORKFLOW_STEP_IDS_UNIQUE")
def _workflow_unique(context):
    oid = "WORKFLOW_STEP_IDS_UNIQUE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    ids = [step.get("step_id") for step in data.get("steps", [])]
    return _pass(oid) if len(ids) == len(set(ids)) else _fail(oid, "$.steps", "workflow step IDs are not unique")


@_handler("WORKFLOW_DEPENDENCIES_RESOLVE")
def _workflow_dependencies(context):
    oid = "WORKFLOW_DEPENDENCIES_RESOLVE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    steps = data.get("steps", [])
    ids = {step.get("step_id") for step in steps}
    return _pass(oid) if all(dep in ids for step in steps for dep in step.get("dependencies", [])) else _fail(oid, "$.steps", "workflow dependency does not resolve")


def _workflow_graph(data):
    return {step.get("step_id"): list(step.get("dependencies", [])) for step in data.get("steps", [])}


@_handler("WORKFLOW_DAG_ACYCLIC")
def _workflow_acyclic(context):
    oid = "WORKFLOW_DAG_ACYCLIC"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    graph = _workflow_graph(data)
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        valid = all(dep not in graph or visit(dep) for dep in graph.get(node, []))
        visiting.remove(node)
        visited.add(node)
        return valid
    return _pass(oid) if all(visit(node) for node in graph) else _fail(oid, "$.steps", "workflow dependency graph is cyclic")


@_handler("WORKFLOW_ROUTE_OPERATION_ACTIVE_MATCH")
def _workflow_routes(context):
    oid = "WORKFLOW_ROUTE_OPERATION_ACTIVE_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    for step in data.get("steps", []):
        if step.get("route_lifecycle") != "active":
            continue
        status, _, message = _operation_route(
            context, step.get("skill_id"), step.get("operation_id")
        )
        if status == "blocked":
            return _blocked(oid, "$.steps", message)
        if status == "fail":
            return _fail(oid, "$.steps", message)
    return _pass(oid)


@_handler("WORKFLOW_AUTHORIZATION_SIDE_EFFECT_ALIGNMENT")
def _workflow_authorization(context):
    oid = "WORKFLOW_AUTHORIZATION_SIDE_EFFECT_ALIGNMENT"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    effects = set(data.get("authorization_policy", {}).get("side_effects", []))
    required = {"authorized-local": "local-execution", "authorized-remote": "remote-write", "scheduler": "scheduler-submit"}
    matches = all(step.get("execution_class") not in required or required[step.get("execution_class")] in effects for step in data.get("steps", []))
    return _pass(oid) if matches else _fail(oid, "$.authorization_policy.side_effects", "workflow authorization misses a step side effect")


@_handler("WORKFLOW_OUTPUT_HANDOFF_REFS_RESOLVE")
def _workflow_handoffs(context):
    oid = "WORKFLOW_OUTPUT_HANDOFF_REFS_RESOLVE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    steps = data.get("steps", [])
    by_id = {step.get("step_id"): step for step in steps}
    for step in steps:
        inputs = {(ref.get("contract_name"), ref.get("role")) for ref in step.get("input_records", [])}
        for dep_id in step.get("dependencies", []):
            dep = by_id.get(dep_id)
            if dep is None:
                continue
            required = {(item.get("contract_name"), item.get("role")) for item in dep.get("output_contracts", []) if item.get("required") is True}
            if not required.issubset(inputs):
                return _fail(oid, "$.steps", "downstream step lacks a required dependency output handoff")
    return _pass(oid)


@_handler("WORKFLOW_RECORD_REF_DAG_ACYCLIC")
def _workflow_record_dag(context):
    return _bundle_dag_result("WORKFLOW_RECORD_REF_DAG_ACYCLIC", context)


# Workflow event handlers.
def _event_plan(context, data):
    return _resolved_data(context, data.get("plan_ref"))


@_handler("EVENT_PLAN_STEP_REF_RESOLVES")
def _event_plan_step(context):
    oid = "EVENT_PLAN_STEP_REF_RESOLVES"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    status, plan, message = _event_plan(context, data)
    if status != "pass":
        return _blocked(oid, "$.plan_ref", message) if status == "blocked" else _fail(oid, "$.plan_ref", message)
    step_id = data.get("step_id")
    return _pass(oid) if step_id is None or any(step.get("step_id") == step_id for step in plan.get("steps", [])) else _fail(oid, "$.step_id", "event step does not resolve in plan")


@_handler("EVENT_SEQUENCE_MONOTONIC")
def _event_sequence(context):
    oid = "EVENT_SEQUENCE_MONOTONIC"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    plan_id = data.get("plan_ref", {}).get("record_id")
    sequence = data.get("sequence")
    current_index = _current_index(context)
    if not isinstance(sequence, int) or current_index is None:
        return _blocked(oid, "$.sequence", "event sequence/index is unavailable")
    earlier = []
    for entry in _records(context).values():
        record = _entry_data(entry)
        if not isinstance(record, Mapping) or record.get("contract_name") != "workflow-event" or entry.get("index") >= current_index:
            continue
        if record.get("plan_ref", {}).get("record_id") == plan_id:
            earlier.append(record.get("sequence"))
    return _pass(oid) if all(isinstance(value, int) and value < sequence for value in earlier) else _fail(oid, "$.sequence", "event sequence is not monotonic")


@_handler("EVENT_EVIDENCE_IDS_RESOLVE")
def _event_evidence(context):
    oid = "EVENT_EVIDENCE_IDS_RESOLVE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    refs = data.get("evidence_refs", [])
    ids = {ref.get("record_id") for ref in refs}
    if not set(data.get("evidence_ids", [])).issubset(ids):
        return _fail(oid, "$.evidence_ids", "event evidence ID has no matching recordRef")
    return _combine_ref_results(oid, (_resolved_data(context, ref) for ref in refs), "$.evidence_refs")


def _event_expected(data):
    related = {
        "execution-requested": ("execution-request", "execution-request"),
        "lease-issued": ("execution-lease", "execution-lease"),
        "scheduler-submitted": ("execution-record", "execution-record"),
        "scheduler-state-observed": ("execution-record", "execution-record"),
        "process-state-observed": ("execution-record", "execution-record"),
        "application-state-observed": ("execution-record", "execution-record"),
        "decision-recorded": ("decision-record", "decision-record"),
        "artifact-produced": ("artifact-manifest", "artifact"),
    }
    statuses = {
        "scheduler-submitted": {"submitted"},
        "scheduler-state-observed": {"submitted", "queued", "running", "succeeded", "failed", "cancelled", "unknown"},
        "process-state-observed": {"running", "succeeded", "failed", "timed-out", "cancelled", "unknown"},
        "application-state-observed": {"running", "completed", "incomplete", "failed", "unknown"},
        "execution-requested": {"submitted"}, "lease-issued": {"approved"},
        "decision-recorded": {"approved", "denied"}, "artifact-produced": {"produced"},
    }
    return related.get(data.get("event_type")), statuses.get(data.get("event_type"))


@_handler("EVENT_TYPE_RELATED_RECORD_STATUS_MATCH")
def _event_type_status(context):
    oid = "EVENT_TYPE_RELATED_RECORD_STATUS_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    expected_ref, expected_statuses = _event_expected(data)
    related_ok = expected_ref is None or any((ref.get("contract_name"), ref.get("role")) == expected_ref for ref in data.get("related_records", []))
    status_ok = expected_statuses is None or data.get("observed_status", {}).get("normalized_status") in expected_statuses
    return _pass(oid) if related_ok and status_ok else _fail(oid, "$", "event type, related record, and normalized status are inconsistent")


@_handler("EVENT_RELATED_RECORD_HASH_RESOLVES")
def _event_related(context):
    oid = "EVENT_RELATED_RECORD_HASH_RESOLVES"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, (_resolved_data(context, ref) for ref in data.get("related_records", [])), "$.related_records")


@_handler("EVENT_NATIVE_STATUS_EVIDENCE_MATCH")
def _event_native(context):
    oid = "EVENT_NATIVE_STATUS_EVIDENCE_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    layer = data.get("observed_status", {}).get("layer")
    if layer not in {"scheduler", "process", "application"}:
        return _pass(oid)
    related = next((ref for ref in data.get("related_records", []) if ref.get("contract_name") == "execution-record"), None)
    status, record, message = _resolved_data(context, related)
    if status != "pass":
        return _blocked(oid, "$.related_records", message) if status == "blocked" else _fail(oid, "$.related_records", message)
    observed = data.get("observed_status", {})
    native = record.get("status", {}).get(f"native_{layer}_status")
    normalized = record.get("status", {}).get(f"{layer}_status")
    alias = {"exited-zero": "succeeded", "exited-nonzero": "failed", "signalled": "failed"}.get(normalized, normalized)
    return _pass(oid) if observed.get("native_status") == native and observed.get("normalized_status") == alias else _fail(oid, "$.observed_status", "event status differs from related native execution evidence")


@_handler("EVENT_RECORD_REF_DAG_ACYCLIC")
def _event_dag(context):
    return _bundle_dag_result("EVENT_RECORD_REF_DAG_ACYCLIC", context)


# Decision handlers.
@_handler("DECISION_SUBJECT_REF_HASH_RESOLVES")
def _decision_subject(context):
    oid = "DECISION_SUBJECT_REF_HASH_RESOLVES"
    data, error = _current_or_blocked(oid, context)
    return error or _combine_ref_results(oid, [_resolved_data(context, data.get("subject_ref"))], "$.subject_ref")


@_handler("DECISION_EVIDENCE_IDS_RESOLVE")
def _decision_evidence(context):
    oid = "DECISION_EVIDENCE_IDS_RESOLVE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    refs = data.get("evidence_refs", [])
    if not set(data.get("evidence_ids", [])).issubset({ref.get("record_id") for ref in refs}):
        return _fail(oid, "$.evidence_ids", "decision evidence ID has no matching recordRef")
    return _combine_ref_results(oid, (_resolved_data(context, ref) for ref in refs), "$.evidence_refs")


@_handler("DECISION_AUTHORIZATION_REQUEST_SCOPE_MATCH")
def _decision_authorization(context):
    oid = "DECISION_AUTHORIZATION_REQUEST_SCOPE_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    if data.get("decision_type") != "execution-authorization":
        return _pass(oid)
    status, request, message = _resolved_data(context, data.get("subject_ref"))
    if status != "pass":
        return _blocked(oid, "$.subject_ref", message) if status == "blocked" else _fail(oid, "$.subject_ref", message)
    created, decided, valid = _parse_time(request.get("created_utc")), _parse_time(data.get("decided_utc")), _parse_time(data.get("valid_until_utc"))
    if None in {created, decided, valid}:
        return _blocked(oid, "$", "authorization timestamps are unavailable")
    matches = (
        data.get("outcome") in {"approved", "denied", "deferred"}
        and data.get("decided_by", {}).get("actor_type") == "human"
        and set(request.get("authorization_requirement", {}).get("scope_labels", [])).issubset(set(data.get("scope_labels", [])))
        and created <= decided < valid
    )
    return _pass(oid) if matches else _fail(oid, "$", "authorization decision scope/time does not match request")


@_handler("DECISION_SCIENTIFIC_SUBJECT_HASH_OUTCOME_MATCH")
def _decision_science(context):
    oid = "DECISION_SCIENTIFIC_SUBJECT_HASH_OUTCOME_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    if data.get("decision_type") != "scientific-acceptance":
        return _pass(oid)
    status, candidate, message = _resolved_data(context, data.get("subject_ref"))
    if status != "pass":
        return _blocked(oid, "$.subject_ref", message) if status == "blocked" else _fail(oid, "$.subject_ref", message)
    contract = data.get("subject_ref", {}).get("contract_name")
    ready = (
        contract == "calculation-record-envelope" and candidate.get("status", {}).get("scientific_acceptance") == "requires_human_review"
    ) or (
        contract == "claim-evidence-map" and candidate.get("scientific_acceptance") == "requires_human_review" and candidate.get("claim_ceiling") == "eligible_for_expert_review"
    )
    outcome = data.get("outcome")
    acceptance = data.get("scientific_acceptance")
    outcome_ok = (outcome == "accepted" and acceptance == "accepted") or (outcome == "rejected" and acceptance == "rejected") or (outcome == "deferred" and acceptance == "not_assessed")
    matches = ready and outcome_ok and data.get("decided_by", {}).get("actor_type") == "human"
    return _pass(oid) if matches else _fail(oid, "$", "scientific decision is not bound to a review-ready candidate and coherent outcome")


@_handler("DECISION_REFS_PREEXIST_DECISION")
def _decision_preexists(context):
    oid = "DECISION_REFS_PREEXIST_DECISION"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    decided = _parse_time(data.get("decided_utc"))
    if decided is None:
        return _blocked(oid, "$.decided_utc", "decision timestamp is unavailable")
    for ref in [data.get("subject_ref"), *data.get("evidence_refs", [])]:
        status, target, message = _resolved_data(context, ref)
        if status == "fail":
            return _fail(oid, "$", message)
        if status == "blocked":
            return _blocked(oid, "$", message)
        generated = _parse_time(target.get("producer", {}).get("generated_utc") or target.get("provenance", {}).get("generated_utc"))
        if generated is None:
            return _blocked(oid, "$", "referenced record generation time is unavailable")
        if generated > decided:
            return _fail(oid, "$.decided_utc", "decision points to evidence created after the decision")
    return _pass(oid)


@_handler("DECISION_RECORD_REF_DAG_ACYCLIC")
def _decision_dag(context):
    return _bundle_dag_result("DECISION_RECORD_REF_DAG_ACYCLIC", context)


# Claim map handlers.
@_handler("CLAIM_EVIDENCE_IDS_UNIQUE")
def _claim_evidence_unique(context):
    oid = "CLAIM_EVIDENCE_IDS_UNIQUE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    ids = [item.get("evidence_id") for item in data.get("evidence", [])]
    return _pass(oid) if len(ids) == len(set(ids)) else _fail(oid, "$.evidence", "claim evidence IDs are not unique")


@_handler("CLAIM_SUPPORTED_EVIDENCE_IDS_RESOLVE_PRESENT_HASHED")
def _claim_evidence_resolves(context):
    oid = "CLAIM_SUPPORTED_EVIDENCE_IDS_RESOLVE_PRESENT_HASHED"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    evidence = {item.get("evidence_id"): item for item in data.get("evidence", [])}
    for claim in data.get("claims", []):
        if claim.get("status") != "supported":
            continue
        for evidence_id in claim.get("evidence_ids", []):
            item = evidence.get(evidence_id)
            if not isinstance(item, Mapping) or item.get("status") != "present":
                return _fail(oid, "$.claims", "supported claim references absent evidence")
            if item.get("kind") == "record":
                status, _, message = _resolved_data(context, item.get("record_ref"))
                if status == "blocked":
                    return _blocked(oid, "$.evidence", message)
                if status == "fail":
                    return _fail(oid, "$.evidence", message)
            else:
                status, message = _artifact_result(context, item.get("file_ref", {}))
                if status == "blocked":
                    return _blocked(oid, "$.evidence", message)
                if status == "fail":
                    return _fail(oid, "$.evidence", message)
    return _pass(oid)


@_handler("CLAIM_GATE_IDS_UNIQUE")
def _claim_gate_unique(context):
    oid = "CLAIM_GATE_IDS_UNIQUE"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    ids = [item.get("check_id") for item in data.get("gates", [])]
    return _pass(oid) if len(ids) == len(set(ids)) else _fail(oid, "$.gates", "claim gate IDs are not unique")


@_handler("CLAIM_SUPPORTED_GATE_IDS_RESOLVE_PASSING")
def _claim_gate_resolves(context):
    oid = "CLAIM_SUPPORTED_GATE_IDS_RESOLVE_PASSING"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    gates = {item.get("check_id"): item for item in data.get("gates", [])}
    for claim in data.get("claims", []):
        if claim.get("status") != "supported":
            continue
        if any(gates.get(gate_id, {}).get("status") != "pass" for gate_id in claim.get("gate_ids", [])):
            return _fail(oid, "$.claims", "supported claim references a missing or non-passing gate")
    return _pass(oid)


@_handler("CLAIM_SCIENTIFIC_DECISION_CANDIDATE_HASH_OUTCOME_MATCH")
def _claim_science(context):
    oid = "CLAIM_SCIENTIFIC_DECISION_CANDIDATE_HASH_OUTCOME_MATCH"
    data, error = _current_or_blocked(oid, context)
    if error:
        return error
    acceptance = data.get("scientific_acceptance")
    if acceptance not in {"accepted", "rejected"}:
        return _pass(oid) if data.get("scientific_decision_ref") is None else _fail(oid, "$.scientific_decision_ref", "pre-decision claim map points to a decision")
    status, decision, message = _resolved_data(context, data.get("scientific_decision_ref"))
    if status != "pass":
        return _blocked(oid, "$.scientific_decision_ref", message) if status == "blocked" else _fail(oid, "$.scientific_decision_ref", message)
    subject = decision.get("subject_ref", {})
    subject_identity = _ref_identity(subject)
    mapped = {_ref_identity(ref) for ref in data.get("subject_records", [])}
    outcome_ok = decision.get("decision_type") == "scientific-acceptance" and decision.get("outcome") == acceptance and decision.get("scientific_acceptance") == acceptance and decision.get("decided_by", {}).get("actor_type") == "human"
    return _pass(oid) if subject_identity in mapped and outcome_ok and subject.get("record_id") != data.get("map_id") else _fail(oid, "$", "post-decision claim map is not bound to the pre-decision candidate and human outcome")


@_handler("CLAIM_RECORD_REF_DAG_ACYCLIC")
def _claim_dag(context):
    return _bundle_dag_result("CLAIM_RECORD_REF_DAG_ACYCLIC", context)


def evaluate(obligation_ids: Sequence[str], context: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Evaluate distinct obligations against a pre-built read-only bundle context.

    ``context`` may contain only these keys: ``current_record``,
    ``current_record_index``, ``records_by_identity``, ``artifacts_by_label``,
    ``core_checks``, and ``registry_snapshots``.  Record entries contain strict
    pre-parsed ``data`` plus ``raw_sha256``, ``index``, ``lifecycle``, and
    ``integrity_verified_active``.  Artifact entries contain ``metadata`` plus
    ``raw_sha256``, ``bytes``, ``integrity_verified``, and built-in
    ``parser_observations``; artifacts have no interface lifecycle.  This
    function performs no I/O and does not reparse or project record bytes.
    """

    if not isinstance(context, Mapping):
        context = {}
    extra_keys = sorted(set(context) - CONTEXT_KEYS)
    distinct = list(dict.fromkeys(obligation_ids))
    results: list[dict[str, Any]] = []
    for obligation_id in distinct:
        if extra_keys:
            results.append(
                _blocked(
                    obligation_id,
                    "$",
                    f"context contains unsupported keys: {', '.join(extra_keys)}",
                )
            )
            continue
        handler = _HANDLERS.get(obligation_id)
        if handler is None:
            results.append(
                _result(
                    obligation_id,
                    "blocked",
                    message="No production handler is registered for this obligation.",
                    finding_codes=("SEMANTIC_OBLIGATION_HANDLER_MISSING",),
                )
            )
            continue
        try:
            result = handler(context)
        except Exception as exc:  # fail closed at the pure evaluator boundary
            result = _blocked(
                obligation_id,
                "$",
                f"handler could not evaluate supplied strict context: {type(exc).__name__}",
            )
        results.append(result)
    return results


if set(_HANDLERS) != {
    obligation
    for obligations in OBLIGATIONS_BY_CONTRACT.values()
    for obligation in obligations
}:
    raise RuntimeError("execution semantic handler registry is incomplete")
