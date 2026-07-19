#!/usr/bin/env python3
"""Validate a weak-model answer envelope and fail closed on unsupported claims.

Exit 0 means an internally consistent envelope with no trust-bearing positive
claim. Exit 2 means invalid or blocked. Exit 3 means internally consistent but
external bundle verification is still required; it is never authentication.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable
import yaml

sys.dont_write_bytecode = True

import environment_profiles  # noqa: E402
import interface_registry  # noqa: E402
import operation_routes  # noqa: E402
import skill_registry  # noqa: E402
import software_registry  # noqa: E402
from strict_json import StrictJSONError, load_object  # noqa: E402


SCHEMA_VERSION = "1.0"
EXIT_INTERNAL_NO_POSITIVE_CLAIM = 0
EXIT_INVALID = 2
EXIT_BUNDLE_VERIFICATION_REQUIRED = 3
CLAIM_ORDER = {name: index for index, name in enumerate(operation_routes.CLAIM_CEILINGS)}
BLOCKING_STATUSES = {"fail", "unresolved", "not_evaluated", "blocked"}
HARD_BLOCKING_STATUSES = {"fail", "blocked"}
MISSING_EVIDENCE_STATUSES = {"unresolved", "not_evaluated"}
TOOL_FAILURE_STATUSES = {"failed", "blocked", "unavailable", "timed_out"}
EXECUTED_TOOL_STATUSES = {"succeeded", "failed", "blocked", "cached_only", "timed_out"}
NO_POSITIVE_GATES = {
    "scientific_plan",
    "official_source_coverage",
    "official_source_resolution",
    "fdf_syntax",
    "fdf_semantics",
    "input_integrity",
    "input_reproducibility",
    "structure_consistency",
    "pseudopotential_provenance",
    "external_data_provenance",
    "evidence_inventory",
    "input_output_binding",
    "input_output_consistency",
    "version_identity",
    "official_version_match",
}
INPUT_ONLY_GATES = {
    "execution_completion",
    "electronic_convergence",
    "ionic_convergence",
    "ionic_or_task_completion",
    "output_warnings",
    "output_observables",
    "runtime_environment",
}
TECHNICAL_ONLY_GATES = {"numerical_convergence"}
NUMERICAL_ONLY_GATES = {"task_specific_validation", "task_specific_validity", "physical_validity"}
PRIVATE_PATH_RE = re.compile(
    r"(?:(?<=^)|(?<=[\s:=\"']))"
    r"(?:/(?:Users|home|private|tmp|var|scratch|gpfs|lustre|mnt|Volumes|work|project)(?:/|$)"
    r"|[A-Za-z]:\\\\)",
    re.IGNORECASE,
)
SECRET_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b(?:password|passwd|api[_-]?key|access[_-]?token|secret[_-]?key)\s*[:=]",
    re.IGNORECASE,
)
RAW_RESTRICTED_RE = re.compile(
    r"parameters from PSCTR are|End of Dataset\s*$|unrestricted POTCAR contents",
    re.IGNORECASE | re.MULTILINE,
)
OFFICIAL_EVIDENCE_ROLES = {
    "official-source-report",
    "official-document",
    "official-manual-entry",
    "official-source-snapshot",
}
HUMAN_DECISION_EVIDENCE_ROLES = {
    "human-expert-decision-record",
    "human-scientific-review-record",
}
AUTHORIZATION_DECISION_EVIDENCE_ROLE = "human-execution-authorization-record"
HANDOFF_MANIFEST_EVIDENCE_ROLE = "handoff-manifest"
HUMAN_DECISION_RECORD = ("decision-record", "scientific-acceptance")
AUTHORIZATION_DECISION_RECORD = ("decision-record", "execution-authorization")
OFFICIAL_SOURCE_RECORD = ("official-source-record", "official-source")
TOOL_RECORD_ROLES = {
    ("tool-execution", "tool-report"),
    ("execution-record", "tool-report"),
}
EXTERNAL_SEMANTIC_OBLIGATIONS = (
    "EVIDENCE_RECORD_CONTENT_HASH_RESOLVES",
    "SCIENTIFIC_DECISION_SUBJECT_OUTCOME_HUMAN_MATCH",
    "AUTHORIZATION_DECISION_SCOPE_HUMAN_MATCH",
    "OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH",
    "TOOL_RECORD_ACTION_EXIT_GATE_MATCH",
    "HANDOFF_RECORD_CONTRACT_ID_HASH_MATCH",
    "UNRESOLVED_BUNDLE_LIMITS_STATUS_TO_INTERNALLY_CONSISTENT",
)
BUNDLE_VERIFICATION_REQUIRED_CODE = "ANSWER_BUNDLE_VERIFICATION_REQUIRED"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def schema_path() -> Path:
    return repo_root() / "contracts" / "agent-action-envelope.schema.json"


def common_schema_path() -> Path:
    return repo_root() / "contracts" / "common-definitions-1.0.schema.json"


def build_schema_validator(schema: dict[str, Any]) -> Draft202012Validator:
    """Build an offline validator with the frozen common-contract URN registered."""

    common_path = common_schema_path()
    common = load_object(common_path, common_path.name)
    common_id = common.get("$id")
    if common_id != "urn:vibe-dft-skills:contract:common-definitions:1.0":
        raise SchemaError("common contract has an unexpected or missing canonical $id")
    registry = Registry().with_resource(common_id, Resource.from_contents(common))
    return Draft202012Validator(schema, registry=registry)


def _finding(code: str, location: str, message: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message}


def _location(parts: Iterable[object]) -> str:
    rendered = "/".join(str(item) for item in parts)
    return rendered or "<root>"


def _normalized_gate_id(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _profile_gate_id(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _index_by_id(items: object, location: str, findings: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(items, list):
        return result
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        identifier = item["id"]
        if identifier in result:
            findings.append(
                _finding("ANSWER_DUPLICATE_ID", f"{location}/{index}/id", f"duplicate id {identifier!r}")
            )
        else:
            result[identifier] = item
    return result


def _iter_strings(value: object, path: tuple[object, ...] = ()) -> Iterable[tuple[tuple[object, ...], str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_strings(item, path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_strings(item, path + (index,))


def _claim_at_most(value: object, ceiling: str) -> bool:
    return isinstance(value, str) and value in CLAIM_ORDER and CLAIM_ORDER[value] <= CLAIM_ORDER[ceiling]


def _canonical_action_state(
    data: dict[str, Any],
    route_entry: dict[str, Any] | None,
    *,
    has_successful_or_official_evidence: bool,
) -> str:
    """Derive the only permitted top-level action state from structured evidence."""

    route = data.get("route")
    if (
        not isinstance(route, dict)
        or route.get("state") != "selected_active"
        or route.get("lifecycle") != "active"
        or not isinstance(route_entry, dict)
        or route_entry.get("lifecycle") != "active"
        or route_entry.get("routable") is not True
    ):
        return "local_gate_blocked"

    tool_runs = data.get("tool_runs")
    if isinstance(tool_runs, list) and any(
        isinstance(tool, dict)
        and tool.get("required") is True
        and tool.get("status") in {"failed", "timed_out"}
        for tool in tool_runs
    ):
        return "failed_recoverable"

    gates = data.get("gates")
    gate_items = [gate for gate in gates if isinstance(gate, dict)] if isinstance(gates, list) else []
    if any(gate.get("status") in HARD_BLOCKING_STATUSES for gate in gate_items):
        return "local_gate_blocked"
    if any(gate.get("status") in MISSING_EVIDENCE_STATUSES for gate in gate_items):
        return "needs_evidence"

    evidence = data.get("evidence")
    if isinstance(evidence, dict):
        missing = evidence.get("missing")
        conflicts = evidence.get("conflicts")
        items = evidence.get("items")
        if (isinstance(missing, list) and missing) or (isinstance(conflicts, list) and conflicts):
            return "needs_evidence"
        if isinstance(items, list) and any(
            isinstance(item, dict) and item.get("status") != "present" for item in items
        ):
            return "needs_evidence"

    authorization = data.get("authorization")
    next_action = data.get("smallest_next_action")
    authorization_is_next = (
        isinstance(next_action, dict) and next_action.get("requires_authorization") is True
    )
    if authorization_is_next:
        if isinstance(authorization, dict) and authorization.get("state") == "granted":
            return "ready_for_authorized_execution"
        return "needs_authorization"

    handoffs = data.get("handoffs")
    if isinstance(handoffs, list) and any(
        isinstance(handoff, dict) and handoff.get("status") == "ready" for handoff in handoffs
    ):
        return "handoff_ready"

    if data.get("scientific_acceptance") in {"accepted", "rejected"}:
        return "complete"
    if has_successful_or_official_evidence:
        return "local_gate_passed_limited"
    return "needs_evidence"


def requires_bundle_verification(data: object) -> bool:
    """Return whether a valid envelope crosses the unauthenticated evidence boundary."""

    if not isinstance(data, dict):
        return False
    claim_ceiling = data.get("claim_ceiling")
    if claim_ceiling in CLAIM_ORDER and CLAIM_ORDER[claim_ceiling] > CLAIM_ORDER["no_positive_claim"]:
        return True
    if isinstance(data.get("claim_scope"), dict):
        return True
    if isinstance(data.get("supported_facts"), list) and data["supported_facts"]:
        return True
    if data.get("scientific_acceptance") in {"accepted", "rejected"}:
        return True
    authorization = data.get("authorization")
    if isinstance(authorization, dict) and (
        authorization.get("state") == "granted"
        or isinstance(authorization.get("decision_ref"), dict)
    ):
        return True
    handoffs = data.get("handoffs")
    if isinstance(handoffs, list) and any(
        isinstance(handoff, dict) and handoff.get("status") in {"ready", "accepted"}
        for handoff in handoffs
    ):
        return True
    evidence = data.get("evidence")
    items = evidence.get("items") if isinstance(evidence, dict) else None
    if not isinstance(items, list):
        return False
    trust_bearing_records = {
        HUMAN_DECISION_RECORD,
        AUTHORIZATION_DECISION_RECORD,
        OFFICIAL_SOURCE_RECORD,
        *TOOL_RECORD_ROLES,
    }
    for item in items:
        if not isinstance(item, dict) or item.get("status") != "present":
            continue
        record_ref = item.get("record_ref")
        if not isinstance(record_ref, dict):
            continue
        if (record_ref.get("contract_name"), record_ref.get("role")) in trust_bearing_records:
            return True
    return False


def _schema_findings(data: object, schema: dict[str, Any]) -> list[dict[str, str]]:
    try:
        Draft202012Validator.check_schema(schema)
        validator = build_schema_validator(schema)
    except (OSError, StrictJSONError, SchemaError) as exc:
        message = exc.message if isinstance(exc, SchemaError) else str(exc)
        return [_finding("ANSWER_SCHEMA_DEFINITION_INVALID", "<schema>", message)]
    findings: list[dict[str, str]] = []
    try:
        errors = sorted(validator.iter_errors(data), key=lambda item: tuple(str(part) for part in item.path))
    except Unresolvable as exc:
        return [_finding("ANSWER_SCHEMA_DEFINITION_INVALID", "<schema>", str(exc))]
    for error in errors:
        findings.append(_finding("ANSWER_SCHEMA_INVALID", _location(error.absolute_path), error.message))
    return findings


def validation_findings(
    data: object,
    *,
    schema: dict[str, Any] | None = None,
    routes: dict[str, Any] | None = None,
    skills: dict[str, Any] | None = None,
    interfaces: dict[str, Any] | None = None,
    software: dict[str, Any] | None = None,
    environments: dict[str, Any] | None = None,
    source_root: Path | None = None,
) -> list[dict[str, str]]:
    """Return schema and semantic findings without mutating the envelope."""

    if schema is None:
        selected_schema_path = schema_path()
        schema = load_object(selected_schema_path, selected_schema_path.name)
    findings = _schema_findings(data, schema)
    if schema.get("x-vibe-semantic-obligations") != list(EXTERNAL_SEMANTIC_OBLIGATIONS):
        findings.append(
            _finding(
                "ANSWER_SCHEMA_SEMANTIC_OBLIGATIONS_INVALID",
                "<schema>/x-vibe-semantic-obligations",
                "weak-model schema must retain the frozen external bundle verification obligations",
            )
        )
    if not isinstance(data, dict):
        return findings

    route_data: dict[str, Any] = {"routes": {}}
    skill_data: dict[str, Any] = {"skills": {}}
    interface_data: dict[str, Any] = {"interfaces": {}}
    software_data: dict[str, Any] = {"software": {}, "planned_software": {}}
    environment_data: dict[str, Any] = {"profiles": {}}
    try:
        route_data = routes if routes is not None else operation_routes.load_registry()
        skill_data = skills if skills is not None else skill_registry.load_registry()
        interface_data = interfaces if interfaces is not None else interface_registry.load_registry()
        software_data = software if software is not None else software_registry.load_registry()
        environment_data = (
            environments if environments is not None else environment_profiles.load_registry()
        )
        route_findings = operation_routes.validation_findings(
            route_data,
            source_root=source_root,
            skill_data=skill_data,
            interface_data=interface_data,
            software_data=software_data,
            environment_data=environment_data,
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        findings.append(_finding("ANSWER_ROUTE_REGISTRY_INVALID", "route", exc.__class__.__name__))
        route_findings = []
    if route_findings:
        findings.append(
            _finding(
                "ANSWER_ROUTE_REGISTRY_INVALID",
                "route",
                ",".join(sorted({item["code"] for item in route_findings})),
            )
        )

    evidence_container = data.get("evidence")
    evidence_items = evidence_container.get("items") if isinstance(evidence_container, dict) else []
    evidence = _index_by_id(evidence_items, "evidence/items", findings)
    gates = _index_by_id(data.get("gates"), "gates", findings)
    tools = _index_by_id(data.get("tool_runs"), "tool_runs", findings)
    facts = _index_by_id(data.get("supported_facts"), "supported_facts", findings)
    blocked_claims = _index_by_id(data.get("blocked_claims"), "blocked_claims", findings)

    def usable_evidence_ids(ids: object) -> set[str]:
        if not isinstance(ids, list):
            return set()
        return {
            evidence_id
            for evidence_id in ids
            if isinstance(evidence_id, str)
            and evidence_id in evidence
            and evidence[evidence_id].get("status") == "present"
            and isinstance(evidence[evidence_id].get("sha256"), str)
        }

    def record_ref_type(item: object) -> tuple[object, object] | None:
        if not isinstance(item, dict):
            return None
        record_ref = item.get("record_ref")
        if not isinstance(record_ref, dict):
            return None
        return record_ref.get("contract_name"), record_ref.get("role")

    def is_human_decision_evidence(item: object) -> bool:
        return (
            isinstance(item, dict)
            and item.get("role") in HUMAN_DECISION_EVIDENCE_ROLES
            and item.get("status") == "present"
            and isinstance(item.get("sha256"), str)
            and record_ref_type(item) == HUMAN_DECISION_RECORD
            and isinstance(item.get("record_ref"), dict)
            and item["record_ref"].get("sha256") == item.get("sha256")
        )

    def is_authorization_decision_evidence(item: object) -> bool:
        return (
            isinstance(item, dict)
            and item.get("role") == AUTHORIZATION_DECISION_EVIDENCE_ROLE
            and item.get("status") == "present"
            and isinstance(item.get("sha256"), str)
            and record_ref_type(item) == AUTHORIZATION_DECISION_RECORD
            and isinstance(item.get("record_ref"), dict)
            and item["record_ref"].get("sha256") == item.get("sha256")
        )

    def is_handoff_manifest_evidence(item: object) -> bool:
        return (
            isinstance(item, dict)
            and item.get("role") == HANDOFF_MANIFEST_EVIDENCE_ROLE
            and item.get("status") == "present"
            and isinstance(item.get("sha256"), str)
            and isinstance(item.get("record_ref"), dict)
            and item["record_ref"].get("role") == "handoff-manifest"
            and item["record_ref"].get("sha256") == item.get("sha256")
        )

    def is_official_source_evidence(item: object) -> bool:
        return (
            isinstance(item, dict)
            and item.get("role") in OFFICIAL_EVIDENCE_ROLES
            and item.get("status") == "present"
            and isinstance(item.get("sha256"), str)
            and record_ref_type(item) == OFFICIAL_SOURCE_RECORD
            and isinstance(item.get("record_ref"), dict)
            and item["record_ref"].get("sha256") == item.get("sha256")
        )

    def is_tool_record_evidence(item: object) -> bool:
        return (
            isinstance(item, dict)
            and item.get("status") == "present"
            and isinstance(item.get("sha256"), str)
            and record_ref_type(item) in TOOL_RECORD_ROLES
            and isinstance(item.get("record_ref"), dict)
            and item["record_ref"].get("sha256") == item.get("sha256")
        )

    def check_evidence_ids(
        ids: object,
        location: str,
        *,
        require_usable: bool = False,
    ) -> list[str]:
        resolved: list[str] = []
        if not isinstance(ids, list):
            return resolved
        for index, evidence_id in enumerate(ids):
            item_location = f"{location}/{index}"
            if not isinstance(evidence_id, str) or evidence_id not in evidence:
                findings.append(
                    _finding("ANSWER_EVIDENCE_LINK_MISSING", item_location, f"unknown evidence id {evidence_id!r}")
                )
                continue
            resolved.append(evidence_id)
            item = evidence[evidence_id]
            if require_usable and (item.get("status") != "present" or not isinstance(item.get("sha256"), str)):
                findings.append(
                    _finding(
                        "ANSWER_EVIDENCE_NOT_USABLE",
                        item_location,
                        "positive claims and ready handoffs require present, hashed evidence",
                    )
                )
        return resolved

    for index, item in enumerate(evidence_items if isinstance(evidence_items, list) else []):
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        sha256 = item.get("sha256")
        if status == "present" and not isinstance(sha256, str):
            findings.append(
                _finding("ANSWER_EVIDENCE_HASH_REQUIRED", f"evidence/items/{index}/sha256", "present evidence needs SHA-256")
            )
        record_ref = item.get("record_ref")
        if isinstance(record_ref, dict) and record_ref.get("sha256") != sha256:
            findings.append(
                _finding(
                    "ANSWER_EVIDENCE_RECORD_HASH_MISMATCH",
                    f"evidence/items/{index}/record_ref/sha256",
                    "record reference hash must equal the evidence item content hash",
                )
            )
        if item.get("role") in HUMAN_DECISION_EVIDENCE_ROLES and not is_human_decision_evidence(item):
            findings.append(
                _finding(
                    "ANSWER_HUMAN_EVIDENCE_RECORD_INVALID",
                    f"evidence/items/{index}/record_ref",
                    "human review evidence needs a decision-record scientific-acceptance reference with the same hash",
                )
            )
        if (
            item.get("role") == AUTHORIZATION_DECISION_EVIDENCE_ROLE
            and not is_authorization_decision_evidence(item)
        ):
            findings.append(
                _finding(
                    "ANSWER_AUTHORIZATION_EVIDENCE_RECORD_INVALID",
                    f"evidence/items/{index}/record_ref",
                    "authorization evidence needs a decision-record execution-authorization reference with the same hash",
                )
            )
        if item.get("role") == HANDOFF_MANIFEST_EVIDENCE_ROLE and not is_handoff_manifest_evidence(item):
            findings.append(
                _finding(
                    "ANSWER_HANDOFF_EVIDENCE_RECORD_INVALID",
                    f"evidence/items/{index}/record_ref",
                    "handoff evidence needs a handoff-manifest record reference with the same hash",
                )
            )
        if item.get("role") in OFFICIAL_EVIDENCE_ROLES and not is_official_source_evidence(item):
            findings.append(
                _finding(
                    "ANSWER_OFFICIAL_EVIDENCE_RECORD_INVALID",
                    f"evidence/items/{index}/record_ref",
                    "official evidence needs an official-source-record authority reference with the same hash",
                )
            )

    for index, gate in enumerate(data.get("gates", []) if isinstance(data.get("gates"), list) else []):
        if not isinstance(gate, dict):
            continue
        check_evidence_ids(gate.get("evidence_ids"), f"gates/{index}/evidence_ids")

    claim_ceiling = data.get("claim_ceiling")
    claim_scope = data.get("claim_scope")
    claim_scope_evidence: set[str] = set()
    if isinstance(claim_scope, dict):
        claim_scope_evidence = set(
            check_evidence_ids(
                claim_scope.get("evidence_ids"),
                "claim_scope/evidence_ids",
                require_usable=True,
            )
        )
    elif claim_ceiling != "no_positive_claim" or facts:
        findings.append(
            _finding(
                "ANSWER_CLAIM_SCOPE_MISSING",
                "claim_scope",
                "every positive claim needs an explicit evidence-linked scope",
            )
        )
    for index, fact in enumerate(data.get("supported_facts", []) if isinstance(data.get("supported_facts"), list) else []):
        if not isinstance(fact, dict):
            continue
        if claim_ceiling in CLAIM_ORDER and not _claim_at_most(fact.get("claim_level"), claim_ceiling):
            findings.append(
                _finding(
                    "ANSWER_CLAIM_EXCEEDS_CEILING",
                    f"supported_facts/{index}/claim_level",
                    f"fact claim {fact.get('claim_level')!r} exceeds envelope ceiling {claim_ceiling!r}",
                )
            )
        check_evidence_ids(fact.get("evidence_ids"), f"supported_facts/{index}/evidence_ids", require_usable=True)
    if claim_ceiling == "no_positive_claim" and facts:
        findings.append(
            _finding("ANSWER_POSITIVE_CLAIM_FORBIDDEN", "supported_facts", "no_positive_claim envelope must contain no supported facts")
        )

    blocked_gate_references: set[str] = set()
    for index, blocked in enumerate(data.get("blocked_claims", []) if isinstance(data.get("blocked_claims"), list) else []):
        if not isinstance(blocked, dict):
            continue
        referenced = blocked.get("gate_ids")
        if not isinstance(referenced, list):
            continue
        linked_codes: set[str] = set()
        for gate_index, gate_id in enumerate(referenced):
            if not isinstance(gate_id, str) or gate_id not in gates:
                findings.append(
                    _finding(
                        "ANSWER_GATE_LINK_MISSING",
                        f"blocked_claims/{index}/gate_ids/{gate_index}",
                        f"unknown gate id {gate_id!r}",
                    )
                )
                continue
            blocked_gate_references.add(gate_id)
            gate_codes = gates[gate_id].get("finding_codes")
            if isinstance(gate_codes, list):
                linked_codes.update(code for code in gate_codes if isinstance(code, str))
        claim_codes = blocked.get("finding_codes")
        if isinstance(claim_codes, list):
            for code in claim_codes:
                if isinstance(code, str) and code not in linked_codes:
                    findings.append(
                        _finding(
                            "ANSWER_BLOCKED_CLAIM_UNLINKED_FINDING",
                            f"blocked_claims/{index}/finding_codes",
                            f"finding code {code!r} is absent from referenced gates",
                        )
                    )

    blocking_gate_ids = {
        gate_id for gate_id, gate in gates.items() if gate.get("status") in BLOCKING_STATUSES
    }
    for gate_id in sorted(blocking_gate_ids.difference(blocked_gate_references)):
        findings.append(
            _finding(
                "ANSWER_BLOCKER_HIDDEN",
                f"gates/{gate_id}",
                "blocking or unevaluated gate must appear in blocked_claims",
            )
        )

    next_action = data.get("smallest_next_action")
    if blocking_gate_ids and not isinstance(next_action, dict):
        findings.append(
            _finding("ANSWER_NEXT_ACTION_MISSING", "smallest_next_action", "blocking gates require a smallest next action")
        )
    if isinstance(next_action, dict):
        gate_id = next_action.get("gate_id")
        if not isinstance(gate_id, str) or gate_id not in gates:
            findings.append(
                _finding("ANSWER_NEXT_ACTION_UNLINKED", "smallest_next_action/gate_id", "next action must reference an existing gate")
            )
        else:
            code = next_action.get("finding_code")
            gate_codes = gates[gate_id].get("finding_codes")
            if not isinstance(gate_codes, list) or code not in gate_codes:
                findings.append(
                    _finding(
                        "ANSWER_NEXT_ACTION_UNLINKED",
                        "smallest_next_action/finding_code",
                        "next-action finding must be emitted by its gate",
                    )
                )

    failed_required_tool = False
    cached_required_tool = False
    for index, tool in enumerate(data.get("tool_runs", []) if isinstance(data.get("tool_runs"), list) else []):
        if not isinstance(tool, dict):
            continue
        status = tool.get("status")
        exit_code = tool.get("exit_code")
        report_hash = tool.get("report_sha256")
        required = tool.get("required") is True
        if status == "succeeded" and (exit_code != 0 or not isinstance(report_hash, str)):
            findings.append(
                _finding(
                    "ANSWER_TOOL_SUCCESS_INVALID",
                    f"tool_runs/{index}",
                    "succeeded tool requires exit 0 and a report SHA-256",
                )
            )
        if status in EXECUTED_TOOL_STATUSES and not isinstance(report_hash, str):
            findings.append(
                _finding(
                    "ANSWER_TOOL_REPORT_HASH_MISSING",
                    f"tool_runs/{index}/report_sha256",
                    "every attempted tool invocation needs a hashed structured report",
                )
            )
        if isinstance(exit_code, int) and exit_code != 0 and status not in TOOL_FAILURE_STATUSES | {"cached_only"}:
            findings.append(
                _finding(
                    "ANSWER_NONZERO_EXIT_MISCLASSIFIED",
                    f"tool_runs/{index}",
                    "nonzero exit must be failed, blocked, unavailable, timed_out, or cached_only",
                )
            )
        if status in {"required", "not_run", "unavailable"} and exit_code is not None:
            findings.append(
                _finding("ANSWER_TOOL_EXIT_INVALID", f"tool_runs/{index}/exit_code", "unexecuted tool must have null exit")
            )
        if status == "cached_only":
            cached_required_tool = cached_required_tool or required
            if not isinstance(exit_code, int) or exit_code == 0 or not isinstance(report_hash, str):
                findings.append(
                    _finding(
                        "ANSWER_CACHED_ONLY_INVALID",
                        f"tool_runs/{index}",
                        "cached-only evidence needs a nonzero exit and report SHA-256",
                    )
                )
        required_failure = required and (
            status in TOOL_FAILURE_STATUSES | {"required", "not_run"}
            or (isinstance(exit_code, int) and exit_code != 0 and status != "cached_only")
        )
        if required_failure:
            failed_required_tool = True
        gate_ids = tool.get("gate_ids")
        if isinstance(gate_ids, list):
            for gate_index, gate_id in enumerate(gate_ids):
                if not isinstance(gate_id, str) or gate_id not in gates:
                    findings.append(
                        _finding(
                            "ANSWER_GATE_LINK_MISSING",
                            f"tool_runs/{index}/gate_ids/{gate_index}",
                            f"unknown gate id {gate_id!r}",
                        )
                    )
            linked_blockers = [
                gate_id
                for gate_id in gate_ids
                if isinstance(gate_id, str)
                and gate_id in gates
                and gates[gate_id].get("status") in BLOCKING_STATUSES
            ]
            if required_failure and (not tool.get("finding_codes") or not linked_blockers):
                findings.append(
                    _finding(
                        "ANSWER_TOOL_FAILURE_BLOCKER_MISSING",
                        f"tool_runs/{index}",
                        "required tool failure needs finding codes and a linked blocking gate",
                    )
                )
    if failed_required_tool:
        if facts or claim_ceiling != "no_positive_claim":
            findings.append(
                _finding(
                    "ANSWER_TOOL_FAILURE_POSITIVE_CLAIM",
                    "supported_facts",
                    "a required tool failure forbids positive claims from this envelope",
                )
            )
        if data.get("scientific_acceptance") == "accepted":
            findings.append(
                _finding("ANSWER_TOOL_FAILURE_ACCEPTED", "scientific_acceptance", "failed tool cannot support acceptance")
            )
        if data.get("action_state") not in {
            "needs_evidence",
            "local_gate_blocked",
            "failed_recoverable",
            "failed_terminal",
        }:
            findings.append(
                _finding(
                    "ANSWER_TOOL_FAILURE_ACTION_STATE_INVALID",
                    "action_state",
                    "required tool failure must remain in a blocked or failed action state",
                )
            )
    if cached_required_tool:
        if claim_ceiling in CLAIM_ORDER and not _claim_at_most(claim_ceiling, "documented_behavior_only"):
            findings.append(
                _finding(
                    "ANSWER_CACHED_ONLY_CLAIM_EXCEEDED",
                    "claim_ceiling",
                    "cached-only official evidence is limited to documented behavior",
                )
            )
        limitations = data.get("limitations")
        disclosure = " ".join(limitations) if isinstance(limitations, list) else ""
        if not re.search(r"cached|offline|离线|缓存", disclosure, re.IGNORECASE):
            findings.append(
                _finding("ANSWER_CACHED_ONLY_UNDISCLOSED", "limitations", "cached-only evidence needs an explicit disclosure")
            )

    route = data.get("route")
    route_skill: str | None = None
    route_entry: dict[str, Any] | None = None
    deterministic_succeeded_tools: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    tool_backed_evidence: set[str] = set()
    strongest_action_ceiling = "no_positive_claim"
    claim_profile: dict[str, Any] | None = None
    if isinstance(route, dict):
        route_skill = route.get("skill") if isinstance(route.get("skill"), str) else None
        all_routes = route_data.get("routes", {}) if isinstance(route_data, dict) else {}
        route_entry = all_routes.get(route_skill) if route_skill and isinstance(all_routes, dict) else None
        if route_skill is None:
            if route.get("state") not in {"ambiguous", "unsupported"}:
                findings.append(_finding("ANSWER_ROUTE_UNKNOWN", "route/skill", "selected route needs a registered skill"))
            if facts or data.get("tool_runs") or claim_ceiling != "no_positive_claim":
                findings.append(
                    _finding("ANSWER_UNROUTED_POSITIVE_CLAIM", "route", "ambiguous or unsupported route cannot act or claim")
                )
        elif not isinstance(route_entry, dict):
            findings.append(_finding("ANSWER_ROUTE_UNKNOWN", "route/skill", f"unknown route {route_skill!r}"))
        else:
            lifecycle = route_entry.get("lifecycle")
            if route.get("lifecycle") != lifecycle:
                findings.append(
                    _finding("ANSWER_ROUTE_LIFECYCLE_MISMATCH", "route/lifecycle", "envelope lifecycle differs from registry")
                )
            expected_state = {
                "active": "selected_active",
                "development": "inactive_development",
                "planned": "inactive_planned",
            }.get(lifecycle, "unsupported")
            if route.get("state") != expected_state:
                findings.append(
                    _finding("ANSWER_ROUTE_STATE_MISMATCH", "route/state", f"expected {expected_state!r}")
                )
            maximum = route_entry.get("maximum_claim")
            if maximum in CLAIM_ORDER and claim_ceiling in CLAIM_ORDER and not _claim_at_most(claim_ceiling, maximum):
                findings.append(
                    _finding("ANSWER_CLAIM_EXCEEDS_ROUTE", "claim_ceiling", "claim exceeds registered route maximum")
                )
            native_mapping = route_entry.get("native_status_mapping")
            if isinstance(native_mapping, dict):
                for gate_id, gate in gates.items():
                    native_status = gate.get("native_status")
                    if native_status not in native_mapping:
                        findings.append(
                            _finding(
                                "ANSWER_NATIVE_STATUS_UNMAPPED",
                                f"gates/{gate_id}/native_status",
                                f"native status {native_status!r} is not declared by the selected route",
                            )
                        )
                    elif native_mapping[native_status] != gate.get("status"):
                        findings.append(
                            _finding(
                                "ANSWER_NATIVE_STATUS_MISMATCH",
                                f"gates/{gate_id}/status",
                                "normalized status differs from the registered native-status mapping",
                            )
                        )
            authorization = data.get("authorization")
            authorized_side_effects = (
                set(authorization.get("side_effects", [])) if isinstance(authorization, dict) else set()
            )
            route_side_effects = set(route_entry.get("side_effects", []))
            if isinstance(authorization, dict) and authorized_side_effects != route_side_effects:
                findings.append(
                    _finding(
                        "ANSWER_SIDE_EFFECT_MISMATCH",
                        "authorization/side_effects",
                        "authorized side-effect capability set differs from the selected route",
                    )
                )
            registered_actions = route_entry.get("actions")
            registered_actions = registered_actions if isinstance(registered_actions, dict) else {}
            action_ids: list[str] = []
            for index, tool in enumerate(data.get("tool_runs", []) if isinstance(data.get("tool_runs"), list) else []):
                if not isinstance(tool, dict):
                    continue
                action_id = tool.get("action_id")
                if not isinstance(action_id, str) or action_id not in registered_actions:
                    findings.append(
                        _finding(
                            "ANSWER_TOOL_ACTION_UNDECLARED",
                            f"tool_runs/{index}/action_id",
                            f"action {action_id!r} is not registered for the selected route",
                        )
                    )
                    continue
                action_ids.append(action_id)
                action = registered_actions[action_id]
                action_side_effects = set(action.get("side_effects", [])) if isinstance(action, dict) else set()
                if action_side_effects.difference(authorized_side_effects):
                    findings.append(
                        _finding(
                            "ANSWER_SIDE_EFFECT_MISMATCH",
                            f"tool_runs/{index}/action_id",
                            "attempted action side effects exceed the envelope authorization capability set",
                        )
                    )
                success_exit_codes = action.get("success_exit_codes") if isinstance(action, dict) else None
                limited_exit_codes = action.get("limited_exit_codes") if isinstance(action, dict) else None
                if tool.get("status") == "succeeded" and (
                    not isinstance(success_exit_codes, list) or tool.get("exit_code") not in success_exit_codes
                ):
                    findings.append(
                        _finding(
                            "ANSWER_ACTION_EXIT_STATUS_MISMATCH",
                            f"tool_runs/{index}",
                            "succeeded status is not permitted by the registered action exit-code contract",
                        )
                    )
                if tool.get("status") == "cached_only" and (
                    not isinstance(limited_exit_codes, list) or tool.get("exit_code") not in limited_exit_codes
                ):
                    findings.append(
                        _finding(
                            "ANSWER_ACTION_EXIT_STATUS_MISMATCH",
                            f"tool_runs/{index}",
                            "cached_only status needs a registered limited exit code",
                        )
                    )
                if (
                    isinstance(action, dict)
                    and tool.get("required") is True
                    and tool.get("status") == "succeeded"
                    and tool.get("exit_code") == 0
                    and isinstance(tool.get("report_sha256"), str)
                ):
                    deterministic_succeeded_tools.append((index, tool, action))
            request = data.get("request")
            request_mode = request.get("mode") if isinstance(request, dict) else None
            first_by_mode = route_entry.get("first_tool")
            sequence_by_mode = route_entry.get("tool_sequence")
            if action_ids:
                if (
                    not isinstance(first_by_mode, dict)
                    or not isinstance(sequence_by_mode, dict)
                    or request_mode not in first_by_mode
                    or request_mode not in sequence_by_mode
                ):
                    findings.append(
                        _finding(
                            "ANSWER_ROUTE_MODE_UNSUPPORTED",
                            "request/mode",
                            "selected route has no deterministic action branch for this request mode",
                        )
                    )
                else:
                    expected_sequence = sequence_by_mode[request_mode]
                    if action_ids[0] != first_by_mode[request_mode]:
                        findings.append(
                            _finding(
                                "ANSWER_FIRST_TOOL_SKIPPED",
                                "tool_runs/0/action_id",
                                "first attempted action differs from the mode-specific route",
                            )
                        )
                    previous_index = -1
                    for index, action_id in enumerate(action_ids):
                        try:
                            sequence_index = expected_sequence.index(action_id, previous_index + 1)
                        except (ValueError, AttributeError):
                            findings.append(
                                _finding(
                                    "ANSWER_TOOL_SEQUENCE_VIOLATION",
                                    f"tool_runs/{index}/action_id",
                                    "action is out of order or absent from the selected mode sequence",
                                )
                            )
                            continue
                        previous_index = sequence_index

            official_documented_claim = False
            if claim_ceiling == "documented_behavior_only" and facts:
                official_documented_claim = all(
                    fact.get("claim_level") == "documented_behavior_only"
                    and any(
                        evidence_id in evidence and is_official_source_evidence(evidence[evidence_id])
                        for evidence_id in usable_evidence_ids(fact.get("evidence_ids"))
                    )
                    for fact in facts.values()
                )

            succeeded_action_ceilings = [
                action.get("maximum_claim")
                for _, _, action in deterministic_succeeded_tools
                if action.get("maximum_claim") in CLAIM_ORDER
            ]
            strongest_action_ceiling = (
                max(succeeded_action_ceilings, key=CLAIM_ORDER.__getitem__)
                if succeeded_action_ceilings
                else "no_positive_claim"
            )
            if claim_ceiling in CLAIM_ORDER and claim_ceiling != "no_positive_claim" and not official_documented_claim:
                if not _claim_at_most(claim_ceiling, strongest_action_ceiling):
                    findings.append(
                        _finding(
                            "ANSWER_ACTION_CLAIM_CEILING_EXCEEDED",
                            "claim_ceiling",
                            "claim exceeds the strongest succeeded required deterministic action",
                        )
                    )

            for _, tool, _ in deterministic_succeeded_tools:
                report_hash = tool.get("report_sha256")
                report_evidence = {
                    evidence_id
                    for evidence_id, item in evidence.items()
                    if item.get("sha256") == report_hash and is_tool_record_evidence(item)
                }
                if not report_evidence:
                    findings.append(
                        _finding(
                            "ANSWER_TOOL_REPORT_EVIDENCE_MISSING",
                            f"tool_runs/{tool.get('id')}/report_sha256",
                            "succeeded deterministic tool report must be bound into the evidence inventory by SHA-256",
                        )
                    )
                    same_hash_evidence = {
                        evidence_id
                        for evidence_id, item in evidence.items()
                        if item.get("status") == "present" and item.get("sha256") == report_hash
                    }
                    if same_hash_evidence:
                        findings.append(
                            _finding(
                                "ANSWER_TOOL_EVIDENCE_RECORD_INVALID",
                                f"tool_runs/{tool.get('id')}/report_sha256",
                                "matching report bytes need a tool-execution or execution-record tool-report reference",
                            )
                        )
                gate_ids = tool.get("gate_ids")
                if not isinstance(gate_ids, list):
                    continue
                for gate_id in gate_ids:
                    gate = gates.get(gate_id) if isinstance(gate_id, str) else None
                    if isinstance(gate, dict) and (
                        gate.get("status") == "pass"
                        or (
                            gate.get("status") == "not_applicable"
                            and data.get("scientific_acceptance") == "accepted"
                        )
                    ):
                        tool_backed_evidence.update(
                            usable_evidence_ids(gate.get("evidence_ids")).intersection(report_evidence)
                        )
            if lifecycle == "active":
                for fact_id, fact in facts.items():
                    fact_evidence = usable_evidence_ids(fact.get("evidence_ids"))
                    documented_official = (
                        fact.get("claim_level") == "documented_behavior_only"
                        and any(
                            evidence_id in evidence and is_official_source_evidence(evidence[evidence_id])
                            for evidence_id in fact_evidence
                        )
                    )
                    if not documented_official and not fact_evidence.intersection(tool_backed_evidence):
                        findings.append(
                            _finding(
                                "ANSWER_POSITIVE_FACT_TOOL_EVIDENCE_MISSING",
                                f"supported_facts/{fact_id}/evidence_ids",
                                "positive fact needs evidence from a passed gate linked to a succeeded required deterministic action",
                            )
                        )

            claim_profile_value = route_entry.get("claim_gate_profile")
            claim_profile = claim_profile_value if isinstance(claim_profile_value, dict) else None
            profile = claim_profile.get(claim_ceiling) if isinstance(claim_profile, dict) else None
            profile_incomplete = False
            normalized_gates = {_profile_gate_id(gate_id): gate for gate_id, gate in gates.items()}

            def profile_gate_passes(gate_id: str) -> bool:
                gate = normalized_gates.get(_profile_gate_id(gate_id))
                if not isinstance(gate, dict):
                    return False
                status = gate.get("status")
                if status == "pass":
                    status_is_sufficient = True
                elif status == "not_applicable" and data.get("scientific_acceptance") == "accepted":
                    gate_codes = gate.get("finding_codes")
                    status_is_sufficient = isinstance(gate_codes, list) and any(
                        isinstance(code, str) and "NOT_APPLICABLE" in code for code in gate_codes
                    )
                else:
                    status_is_sufficient = False
                if not status_is_sufficient:
                    return False
                linked = usable_evidence_ids(gate.get("evidence_ids"))
                if not linked:
                    findings.append(
                        _finding(
                            "ANSWER_CLAIM_GATE_EVIDENCE_MISSING",
                            f"gates/{gate_id}/evidence_ids",
                            "claim-profile gate needs present, hashed evidence",
                        )
                    )
                    return False
                if claim_ceiling != "documented_behavior_only" and not linked.intersection(tool_backed_evidence):
                    findings.append(
                        _finding(
                            "ANSWER_CLAIM_GATE_TOOL_EVIDENCE_MISSING",
                            f"gates/{gate_id}/evidence_ids",
                            "claim-profile gate needs evidence bound to a succeeded required deterministic tool report",
                        )
                    )
                    return False
                return True

            if claim_ceiling in CLAIM_ORDER and claim_ceiling != "no_positive_claim":
                if not isinstance(profile, dict):
                    profile_incomplete = True
                else:
                    all_of = profile.get("all_of")
                    any_of = profile.get("any_of")
                    if not isinstance(all_of, list) or any(
                        not isinstance(gate_id, str) or not profile_gate_passes(gate_id)
                        for gate_id in all_of
                    ):
                        profile_incomplete = True
                    if not isinstance(any_of, list) or (any_of and not any(
                        isinstance(gate_id, str) and profile_gate_passes(gate_id)
                        for gate_id in any_of
                    )):
                        profile_incomplete = True
                if profile_incomplete:
                    findings.append(
                        _finding(
                            "ANSWER_CLAIM_GATE_PROFILE_INCOMPLETE",
                            "gates",
                            f"the {claim_ceiling!r} route profile is not fully satisfied",
                        )
                    )
                    if data.get("scientific_acceptance") == "accepted":
                        findings.append(
                            _finding(
                                "ANSWER_ACCEPTANCE_PROFILE_INCOMPLETE",
                                "scientific_acceptance",
                                "scientific acceptance needs the full applicable route gate profile",
                            )
                        )
            if lifecycle in {"development", "planned"}:
                if data.get("action_state") not in {"needs_evidence", "local_gate_blocked"}:
                    findings.append(
                        _finding(
                            "ANSWER_PLANNED_ACTION_STATE_INVALID",
                            "action_state",
                            "non-active routes may only remain in needs_evidence or local_gate_blocked",
                        )
                    )
                nonactive_authorization = data.get("authorization")
                if isinstance(nonactive_authorization, dict) and nonactive_authorization.get("state") not in {
                    "not_required",
                    "not_requested",
                }:
                    findings.append(
                        _finding(
                            "ANSWER_PLANNED_AUTHORIZATION_INVALID",
                            "authorization/state",
                            "non-active routes cannot request, receive, or use execution authorization",
                        )
                    )
                if (
                    route_entry.get("routable") is not False
                    or claim_ceiling != "no_positive_claim"
                    or facts
                    or data.get("tool_runs")
                    or data.get("handoffs")
                ):
                    findings.append(
                        _finding(
                            "ANSWER_PLANNED_ROUTE_INVOCATION",
                            "route",
                            "non-active skill cannot run tools, hand off artifacts, or make positive claims",
                        )
                    )

    canonical_action_state = _canonical_action_state(
        data,
        route_entry,
        has_successful_or_official_evidence=(
            bool(deterministic_succeeded_tools)
            or any(is_official_source_evidence(item) for item in evidence.values())
        ),
    )
    if data.get("action_state") != canonical_action_state:
        findings.append(
            _finding(
                "ANSWER_ACTION_STATE_NONCANONICAL",
                "action_state",
                f"expected canonical action state {canonical_action_state!r}",
            )
        )

    gate_ceiling = "eligible_for_expert_review"
    for gate in gates.values():
        if gate.get("status") not in BLOCKING_STATUSES:
            continue
        gate_id = _normalized_gate_id(gate.get("id"))
        if gate_id in NO_POSITIVE_GATES:
            gate_ceiling = "no_positive_claim"
            break
        if gate_id in INPUT_ONLY_GATES and CLAIM_ORDER[gate_ceiling] > CLAIM_ORDER["input_gates_only"]:
            gate_ceiling = "input_gates_only"
        elif gate_id in TECHNICAL_ONLY_GATES and CLAIM_ORDER[gate_ceiling] > CLAIM_ORDER["technical_run_gates_only"]:
            gate_ceiling = "technical_run_gates_only"
        elif gate_id in NUMERICAL_ONLY_GATES and CLAIM_ORDER[gate_ceiling] > CLAIM_ORDER["numerical_candidate_only"]:
            gate_ceiling = "numerical_candidate_only"
    if claim_ceiling in CLAIM_ORDER and not _claim_at_most(claim_ceiling, gate_ceiling):
        findings.append(
            _finding(
                "ANSWER_GATE_CEILING_EXCEEDED",
                "claim_ceiling",
                f"blocking gates limit this envelope to {gate_ceiling!r}",
            )
        )

    canonical_claim_ceiling = "no_positive_claim"
    if (
        isinstance(route_entry, dict)
        and route_entry.get("lifecycle") == "active"
        and route_entry.get("routable") is True
        and isinstance(claim_profile, dict)
    ):
        normalized_gates = {_profile_gate_id(gate_id): gate for gate_id, gate in gates.items()}
        official_evidence_ids = {
            evidence_id
            for evidence_id, item in evidence.items()
            if is_official_source_evidence(item)
        }
        route_maximum = route_entry.get("maximum_claim")

        def canonical_profile_gate_passes(gate_id: object, level: str) -> bool:
            if not isinstance(gate_id, str):
                return False
            gate = normalized_gates.get(_profile_gate_id(gate_id))
            if not isinstance(gate, dict):
                return False
            status = gate.get("status")
            if status == "pass":
                status_is_sufficient = True
            elif status == "not_applicable" and data.get("scientific_acceptance") == "accepted":
                gate_codes = gate.get("finding_codes")
                status_is_sufficient = isinstance(gate_codes, list) and any(
                    isinstance(code, str) and "NOT_APPLICABLE" in code for code in gate_codes
                )
            else:
                status_is_sufficient = False
            if not status_is_sufficient:
                return False
            linked = usable_evidence_ids(gate.get("evidence_ids"))
            if level == "documented_behavior_only":
                return bool(linked.intersection(official_evidence_ids))
            return bool(linked.intersection(tool_backed_evidence))

        for level in operation_routes.CLAIM_CEILINGS[1:]:
            profile = claim_profile.get(level)
            if not isinstance(profile, dict):
                continue
            if route_maximum not in CLAIM_ORDER or not _claim_at_most(level, route_maximum):
                continue
            if not _claim_at_most(level, gate_ceiling):
                continue
            if (
                level != "documented_behavior_only"
                and not _claim_at_most(level, strongest_action_ceiling)
            ):
                continue
            all_of = profile.get("all_of")
            any_of = profile.get("any_of")
            if not isinstance(all_of, list) or not isinstance(any_of, list):
                continue
            if any(not canonical_profile_gate_passes(gate_id, level) for gate_id in all_of):
                continue
            if any_of and not any(
                canonical_profile_gate_passes(gate_id, level) for gate_id in any_of
            ):
                continue
            canonical_claim_ceiling = level

    if claim_ceiling != canonical_claim_ceiling:
        findings.append(
            _finding(
                "ANSWER_CLAIM_CEILING_NONCANONICAL",
                "claim_ceiling",
                f"expected highest supported claim ceiling {canonical_claim_ceiling!r}",
            )
        )

    acceptance = data.get("scientific_acceptance")
    human_evidence_ids = {
        evidence_id for evidence_id, item in evidence.items() if is_human_decision_evidence(item)
    }
    scientific_decision_ref = data.get("scientific_decision_ref")
    if acceptance in {"accepted", "rejected"}:
        if record_ref_type({"record_ref": scientific_decision_ref}) != HUMAN_DECISION_RECORD:
            findings.append(
                _finding(
                    "ANSWER_SCIENTIFIC_DECISION_REF_INVALID",
                    "scientific_decision_ref",
                    "a scientific verdict needs a decision-record scientific-acceptance reference",
                )
            )
        elif not any(
            evidence[evidence_id].get("record_ref") == scientific_decision_ref
            for evidence_id in human_evidence_ids
        ):
            findings.append(
                _finding(
                    "ANSWER_SCIENTIFIC_DECISION_EVIDENCE_MISMATCH",
                    "scientific_decision_ref",
                    "scientific decision reference must exactly match a cited human decision evidence record",
                )
            )
    elif scientific_decision_ref is not None:
        findings.append(
            _finding(
                "ANSWER_SCIENTIFIC_DECISION_REF_UNEXPECTED",
                "scientific_decision_ref",
                "non-verdict scientific acceptance states cannot carry a decision reference",
            )
        )
    if acceptance == "accepted":
        if claim_ceiling != "eligible_for_expert_review":
            findings.append(
                _finding(
                    "ANSWER_ACCEPTANCE_CLAIM_CEILING_INVALID",
                    "claim_ceiling",
                    "scientific acceptance requires the eligible_for_expert_review ceiling",
                )
            )
        if not isinstance(claim_scope, dict) or claim_scope.get("scope_kind") != "scientific-claim":
            findings.append(
                _finding(
                    "ANSWER_ACCEPTANCE_CLAIM_SCOPE_INVALID",
                    "claim_scope",
                    "accepted result needs an explicit scientific-claim scope",
                )
            )
        elif not claim_scope_evidence.intersection(human_evidence_ids):
            findings.append(
                _finding(
                    "ANSWER_ACCEPTANCE_CLAIM_SCOPE_INVALID",
                    "claim_scope/evidence_ids",
                    "accepted claim scope must cite the hashed human decision record",
                )
            )
        if not facts:
            findings.append(
                _finding(
                    "ANSWER_ACCEPTANCE_FACT_MISSING",
                    "supported_facts",
                    "accepted status needs at least one explicitly bounded supported fact",
                )
            )
        expert_gate = next(
            (gate for gate in gates.values() if _normalized_gate_id(gate.get("id")) == "expert_scientific_review"),
            None,
        )
        if not isinstance(expert_gate, dict) or expert_gate.get("status") != "pass":
            findings.append(
                _finding(
                    "ANSWER_EXPERT_ACCEPTANCE_MISSING",
                    "scientific_acceptance",
                    "accepted status requires a passing expert_scientific_review gate",
                )
            )
        else:
            expert_evidence_ids = set(
                check_evidence_ids(
                    expert_gate.get("evidence_ids"),
                    "gates/expert_scientific_review/evidence_ids",
                    require_usable=True,
                )
            )
            if not expert_evidence_ids:
                findings.append(
                    _finding(
                        "ANSWER_EXPERT_ACCEPTANCE_MISSING",
                        "gates/expert_scientific_review/evidence_ids",
                        "expert acceptance requires hashed review evidence",
                    )
                )
            elif not expert_evidence_ids.intersection(human_evidence_ids):
                findings.append(
                    _finding(
                        "ANSWER_HUMAN_DECISION_EVIDENCE_MISSING",
                        "gates/expert_scientific_review/evidence_ids",
                        "expert acceptance must cite a dedicated hashed human decision or review record",
                    )
                )
        for gate in gates.values():
            if gate.get("status") in BLOCKING_STATUSES:
                findings.append(
                    _finding(
                        "ANSWER_ACCEPTANCE_WITH_BLOCKER",
                        f"gates/{gate.get('id')}",
                        "scientific acceptance cannot coexist with an unresolved scientific gate",
                    )
                )
    if acceptance == "requires_human_review" and claim_ceiling != "eligible_for_expert_review":
        findings.append(
            _finding(
                "ANSWER_EXPERT_REVIEW_PREMATURE",
                "scientific_acceptance",
                "requires_human_review needs the eligible_for_expert_review claim ceiling",
            )
        )

    authorization = data.get("authorization")
    if isinstance(authorization, dict):
        auth_state = authorization.get("state")
        auth_decision_ref = authorization.get("decision_ref")
        auth_evidence = check_evidence_ids(
            authorization.get("evidence_ids"),
            "authorization/evidence_ids",
            require_usable=auth_state == "granted",
        )
        if auth_state == "granted" and (not authorization.get("scope") or not auth_evidence):
            findings.append(
                _finding(
                    "ANSWER_AUTHORIZATION_EVIDENCE_MISSING",
                    "authorization",
                    "granted authorization needs explicit scope and hashed evidence",
                )
            )
        if auth_state == "granted":
            if record_ref_type({"record_ref": auth_decision_ref}) != AUTHORIZATION_DECISION_RECORD:
                findings.append(
                    _finding(
                        "ANSWER_AUTHORIZATION_DECISION_REF_INVALID",
                        "authorization/decision_ref",
                        "granted authorization needs a decision-record execution-authorization reference",
                    )
                )
            matching_authorization_evidence = [
                evidence_id
                for evidence_id in auth_evidence
                if evidence_id in evidence
                and is_authorization_decision_evidence(evidence[evidence_id])
                and evidence[evidence_id].get("record_ref") == auth_decision_ref
            ]
            if not matching_authorization_evidence:
                findings.append(
                    _finding(
                        "ANSWER_AUTHORIZATION_DECISION_EVIDENCE_MISMATCH",
                        "authorization/evidence_ids",
                        "granted authorization must cite the exact hashed human authorization decision record",
                    )
                )
        elif auth_decision_ref is not None:
            findings.append(
                _finding(
                    "ANSWER_AUTHORIZATION_DECISION_REF_UNEXPECTED",
                    "authorization/decision_ref",
                    "a non-granted authorization state cannot carry an authorization decision reference",
                )
            )
        registered_actions = route_entry.get("actions", {}) if isinstance(route_entry, dict) else {}
        authorization_required_actions: list[str] = []
        for tool in tools.values():
            if tool.get("status") not in EXECUTED_TOOL_STATUSES or not isinstance(registered_actions, dict):
                continue
            action_id = tool.get("action_id")
            action = registered_actions.get(action_id)
            if not isinstance(action, dict):
                continue
            action_side_effects = set(action.get("side_effects", []))
            if action.get("requires_authorization") is True or operation_routes.AUTHORIZATION_REQUIRED_SIDE_EFFECTS.intersection(
                action_side_effects
            ):
                authorization_required_actions.append(str(action_id))
        if authorization_required_actions and auth_state != "granted":
            findings.append(
                _finding(
                    "ANSWER_UNAUTHORIZED_SIDE_EFFECT",
                    "authorization/state",
                    "executed authorization-gated actions require explicit granted authorization: "
                    + ", ".join(sorted(set(authorization_required_actions))),
                )
            )
        if data.get("action_state") in {"ready_for_authorized_execution", "execution_in_progress"} and auth_state != "granted":
            findings.append(
                _finding(
                    "ANSWER_AUTHORIZATION_REQUIRED",
                    "authorization/state",
                    "authorized execution state requires granted authorization",
                )
            )
        if data.get("action_state") == "needs_authorization":
            if auth_state not in {"not_requested", "requested", "denied", "expired"}:
                findings.append(
                    _finding("ANSWER_AUTHORIZATION_STATE_INVALID", "authorization/state", "invalid waiting state")
                )
            if not isinstance(next_action, dict) or next_action.get("requires_authorization") is not True:
                findings.append(
                    _finding(
                        "ANSWER_AUTHORIZATION_NEXT_ACTION_MISSING",
                        "smallest_next_action",
                        "needs_authorization requires an authorization-gated next action",
                    )
                )

    route_handoff = route_entry.get("handoff") if isinstance(route_entry, dict) else None
    for index, handoff in enumerate(data.get("handoffs", []) if isinstance(data.get("handoffs"), list) else []):
        if not isinstance(handoff, dict):
            continue
        if route_skill and handoff.get("producer_skill") != route_skill:
            findings.append(
                _finding("ANSWER_HANDOFF_PRODUCER_MISMATCH", f"handoffs/{index}/producer_skill", "producer differs from route")
            )
        if isinstance(route_handoff, dict):
            if route_handoff.get("status") != "enabled":
                findings.append(_finding("ANSWER_HANDOFF_ROUTE_BLOCKED", f"handoffs/{index}", "route handoff is blocked"))
            if handoff.get("contract") not in route_handoff.get("produces", []):
                findings.append(
                    _finding("ANSWER_HANDOFF_CONTRACT_UNDECLARED", f"handoffs/{index}/contract", "contract is not produced by route")
                )
            consumers = route_handoff.get("consumers", [])
            future_consumers = route_handoff.get("future_consumers", [])
            consumer_name = handoff.get("consumer_skill")
            if consumer_name in future_consumers:
                findings.append(
                    _finding(
                        "ANSWER_HANDOFF_CONSUMER_INACTIVE",
                        f"handoffs/{index}/consumer_skill",
                        "future consumers are roadmap metadata and cannot receive a live handoff",
                    )
                )
            elif consumer_name not in consumers:
                findings.append(
                    _finding("ANSWER_HANDOFF_CONSUMER_UNDECLARED", f"handoffs/{index}/consumer_skill", "consumer is not registered")
                )
            registered_skills = skill_data.get("skills", {}) if isinstance(skill_data, dict) else {}
            consumer = registered_skills.get(consumer_name) if isinstance(registered_skills, dict) else None
            if isinstance(consumer, dict):
                if consumer.get("lifecycle") != "active" and consumer_name not in future_consumers:
                    findings.append(
                        _finding(
                            "ANSWER_HANDOFF_CONSUMER_INACTIVE",
                            f"handoffs/{index}/consumer_skill",
                            "a live handoff requires an active consumer Skill",
                        )
                    )
                consumed_contracts = consumer.get("consumes")
                if not isinstance(consumed_contracts, list) or handoff.get("contract") not in consumed_contracts:
                    findings.append(
                        _finding(
                            "ANSWER_HANDOFF_CONTRACT_NOT_CONSUMED",
                            f"handoffs/{index}/contract",
                            "consumer Skill does not declare this contract in its canonical consumes set",
                        )
                    )
        source_evidence_ids = check_evidence_ids(
            handoff.get("source_evidence_ids"),
            f"handoffs/{index}/source_evidence_ids",
            require_usable=handoff.get("status") in {"ready", "accepted"},
        )
        manifest_ref = handoff.get("manifest_ref")
        contract = handoff.get("contract")
        expected_contract_name: str | None = None
        expected_schema_version: str | None = None
        if isinstance(contract, str) and "@" in contract:
            expected_contract_name, expected_schema_version = contract.rsplit("@", 1)
        if isinstance(manifest_ref, dict) and (
            manifest_ref.get("contract_name") != expected_contract_name
            or manifest_ref.get("schema_version") != expected_schema_version
            or manifest_ref.get("role") != "handoff-manifest"
        ):
            findings.append(
                _finding(
                    "ANSWER_HANDOFF_MANIFEST_REF_MISMATCH",
                    f"handoffs/{index}/manifest_ref",
                    "manifest reference contract name/version/role must match the declared handoff interface",
                )
            )
        if handoff.get("status") in {"ready", "accepted"}:
            matching_manifest_evidence = [
                evidence_id
                for evidence_id in source_evidence_ids
                if evidence_id in evidence
                and is_handoff_manifest_evidence(evidence[evidence_id])
                and evidence[evidence_id].get("record_ref") == manifest_ref
            ]
            if not matching_manifest_evidence:
                findings.append(
                    _finding(
                        "ANSWER_HANDOFF_MANIFEST_EVIDENCE_MISMATCH",
                        f"handoffs/{index}/source_evidence_ids",
                        "ready or accepted handoff must cite the exact hashed manifest record reference",
                    )
                )
        if claim_ceiling in CLAIM_ORDER and not _claim_at_most(handoff.get("claim_ceiling"), claim_ceiling):
            findings.append(
                _finding("ANSWER_HANDOFF_CLAIM_EXCEEDED", f"handoffs/{index}/claim_ceiling", "handoff exceeds producer ceiling")
            )

    handoff_records = [
        handoff
        for handoff in data.get("handoffs", [])
        if isinstance(handoff, dict) and handoff.get("status") in {"ready", "accepted"}
    ] if isinstance(data.get("handoffs"), list) else []
    ready_handoffs = [handoff for handoff in handoff_records if handoff.get("status") == "ready"]
    accepted_handoffs = [handoff for handoff in handoff_records if handoff.get("status") == "accepted"]
    if data.get("action_state") == "handoff_ready" and not handoff_records:
        findings.append(
            _finding(
                "ANSWER_HANDOFF_STATE_MISMATCH",
                "action_state",
                "handoff_ready requires at least one ready or accepted typed handoff manifest",
            )
        )
    if ready_handoffs and data.get("action_state") != "handoff_ready":
        findings.append(
            _finding(
                "ANSWER_HANDOFF_STATE_MISMATCH",
                "action_state",
                "a ready handoff manifest requires the handoff_ready action state",
            )
        )
    if accepted_handoffs and data.get("action_state") not in {"handoff_ready", "complete"}:
        findings.append(
            _finding(
                "ANSWER_HANDOFF_STATE_MISMATCH",
                "action_state",
                "an accepted handoff manifest requires handoff_ready or complete",
            )
        )

    for path, text in _iter_strings(data):
        without_urls = re.sub(r"https?://[^\s]+", "", text)
        if PRIVATE_PATH_RE.search(without_urls):
            findings.append(
                _finding("ANSWER_PRIVATE_PATH_EXPOSED", _location(path), "private absolute path is forbidden")
            )
        if SECRET_RE.search(text):
            findings.append(_finding("ANSWER_SECRET_EXPOSED", _location(path), "credential-like content is forbidden"))
        if RAW_RESTRICTED_RE.search(text):
            findings.append(
                _finding("ANSWER_RESTRICTED_CONTENT_EXPOSED", _location(path), "restricted potential content is forbidden")
            )
    return findings


def validate_file(
    envelope_path: Path,
    *,
    schema_file: Path | None = None,
    route_file: Path | None = None,
    skill_file: Path | None = None,
    interface_file: Path | None = None,
    software_file: Path | None = None,
    environment_file: Path | None = None,
    source_root: Path | None = None,
) -> tuple[int, dict[str, Any]]:
    try:
        data = load_object(envelope_path, envelope_path.name)
    except StrictJSONError as exc:
        finding = _finding("ANSWER_JSON_INVALID", "<root>", str(exc))
        return EXIT_INVALID, {
            "schema_version": SCHEMA_VERSION,
            "decision": "blocked",
            "assurance": "not-established",
            "bundle_validation": "not_performed",
            "unresolved_semantic_obligations": list(EXTERNAL_SEMANTIC_OBLIGATIONS),
            "finding_codes": [finding["code"]],
            "findings": [finding],
        }
    except OSError as exc:
        finding = _finding("ANSWER_READ_FAILED", "<root>", exc.__class__.__name__)
        return EXIT_INVALID, {
            "schema_version": SCHEMA_VERSION,
            "decision": "blocked",
            "assurance": "not-established",
            "bundle_validation": "not_performed",
            "unresolved_semantic_obligations": list(EXTERNAL_SEMANTIC_OBLIGATIONS),
            "finding_codes": [finding["code"]],
            "findings": [finding],
        }
    try:
        selected_schema_file = schema_file or schema_path()
        schema = load_object(selected_schema_file, selected_schema_file.name)
        routes = operation_routes.load_registry(route_file)
        skills = skill_registry.load_registry(skill_file)
        interfaces = interface_registry.load_registry(interface_file)
        software = software_registry.load_registry(software_file)
        environments = environment_profiles.load_registry(environment_file)
        findings = validation_findings(
            data,
            schema=schema,
            routes=routes,
            skills=skills,
            interfaces=interfaces,
            software=software,
            environments=environments,
            source_root=source_root,
        )
    except (OSError, ValueError, StrictJSONError, yaml.YAMLError) as exc:
        finding = _finding("ANSWER_VALIDATOR_DEPENDENCY_INVALID", "<validator>", exc.__class__.__name__)
        return EXIT_INVALID, {
            "schema_version": SCHEMA_VERSION,
            "decision": "blocked",
            "assurance": "not-established",
            "bundle_validation": "not_performed",
            "unresolved_semantic_obligations": list(EXTERNAL_SEMANTIC_OBLIGATIONS),
            "finding_codes": [finding["code"]],
            "findings": [finding],
        }
    if findings:
        return EXIT_INVALID, {
            "schema_version": SCHEMA_VERSION,
            "decision": "blocked",
            "assurance": "not-established",
            "bundle_validation": "not_performed",
            "unresolved_semantic_obligations": list(EXTERNAL_SEMANTIC_OBLIGATIONS),
            "finding_codes": sorted({item["code"] for item in findings}),
            "findings": findings,
        }
    if requires_bundle_verification(data):
        requirement = _finding(
            BUNDLE_VERIFICATION_REQUIRED_CODE,
            "evidence",
            "positive or trust-bearing claims require external content-hash and record-semantic bundle verification",
        )
        return EXIT_BUNDLE_VERIFICATION_REQUIRED, {
            "schema_version": SCHEMA_VERSION,
            "decision": "needs_bundle_verification",
            "assurance": "internally-consistent",
            "bundle_validation": "required",
            "unresolved_semantic_obligations": list(EXTERNAL_SEMANTIC_OBLIGATIONS),
            "finding_codes": [requirement["code"]],
            "findings": [requirement],
        }
    return EXIT_INTERNAL_NO_POSITIVE_CLAIM, {
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "assurance": "internally-consistent",
        "bundle_validation": "not_required",
        "unresolved_semantic_obligations": [],
        "finding_codes": [],
        "findings": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope", type=Path)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--routes", type=Path)
    parser.add_argument("--skill-registry", type=Path)
    parser.add_argument("--interface-registry", type=Path)
    parser.add_argument("--software-registry", type=Path)
    parser.add_argument("--environment-profiles", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    exit_code, result = validate_file(
        args.envelope,
        schema_file=args.schema,
        route_file=args.routes,
        skill_file=args.skill_registry,
        interface_file=args.interface_registry,
        software_file=args.software_registry,
        environment_file=args.environment_profiles,
        source_root=args.root,
    )
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
