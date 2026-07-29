#!/usr/bin/env python3
"""Validate and query lifecycle-safe weak-model operation routes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml

sys.dont_write_bytecode = True

import environment_profiles  # noqa: E402
import interface_registry  # noqa: E402
from registry_yaml import load_yaml_strict  # noqa: E402
import skill_registry  # noqa: E402
import software_registry  # noqa: E402
from strict_json import StrictJSONError, load_object  # noqa: E402


SCHEMA_VERSION = "1.0"
SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INTERFACE_ID = re.compile(r"^[a-z][a-z0-9-]*@[1-9][0-9]*\.[0-9]+$")
LIFECYCLES = {"active", "development", "planned"}
NON_ROUTABLE_LIFECYCLES = {"development", "planned"}
COMMON_DEFINITIONS_PATH = Path(__file__).resolve().parents[1] / "contracts" / "common-definitions-1.0.schema.json"


def _load_common_side_effects() -> tuple[tuple[str, ...], str | None]:
    try:
        common = load_object(COMMON_DEFINITIONS_PATH, COMMON_DEFINITIONS_PATH.name)
        values = common["$defs"]["sideEffect"]["enum"]
    except (OSError, StrictJSONError, KeyError, TypeError) as exc:
        return (), f"{exc.__class__.__name__}: cannot load common sideEffect"
    if (
        not isinstance(values, list)
        or not values
        or any(not isinstance(value, str) or not value for value in values)
        or len(values) != len(set(values))
    ):
        return (), "common sideEffect must be a nonempty unique string enum"
    return tuple(values), None


SIDE_EFFECTS, COMMON_DEFINITIONS_ERROR = _load_common_side_effects()
SIDE_EFFECT_SET = frozenset(SIDE_EFFECTS)
SIDE_EFFECT_ORDER = {name: index for index, name in enumerate(SIDE_EFFECTS)}
AUTHORIZATION_REQUIRED_SIDE_EFFECTS = frozenset(
    {
        "remote-write",
        "scheduler-submit",
        "scheduler-control",
        "external-publish",
        "destructive-delete",
    }
)
NORMALIZED_STATUSES = {
    "pass",
    "warn",
    "fail",
    "unresolved",
    "not_applicable",
    "not_evaluated",
    "blocked",
}
CLAIM_CEILINGS = (
    "no_positive_claim",
    "documented_behavior_only",
    "input_gates_only",
    "technical_run_gates_only",
    "numerical_candidate_only",
    "eligible_for_expert_review",
)
REQUEST_MODES = {
    "explain",
    "structure_analysis",
    "design",
    "audit_input",
    "audit_run",
    "convergence",
    "postprocess",
    "figure",
    "efficiency",
    "execute",
    "handoff",
}
ACTION_ID = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
GATE_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
ACTION_FIELDS = {
    "argv",
    "success_exit_codes",
    "limited_exit_codes",
    "side_effects",
    "requires_authorization",
    "maximum_claim",
}
CLAIM_PROFILE_FIELDS = {"all_of", "any_of"}
HANDOFF_STATUSES = {"enabled", "blocked"}
ROUTE_FIELDS = {
    "lifecycle",
    "routable",
    "required_reads",
    "first_tool",
    "tool_sequence",
    "side_effects",
    "minimum_evidence",
    "native_status_mapping",
    "maximum_claim",
    "actions",
    "claim_gate_profile",
    "handoff",
}
HANDOFF_FIELDS = {"status", "produces", "consumers", "future_consumers", "requirements"}
TERMINAL_READINESS_CLASSES = {
    "missing-route",
    "human-boundary",
    "intentionally-disabled",
}
TERMINAL_NULL_ONLY_CLASSES = {"human-boundary", "intentionally-disabled"}
TERMINAL_ACTION_REQUIREMENT_FIELDS = {
    "readiness_class",
    "required_action_side_effect",
}
TERMINAL_SKILL_REQUIREMENT_FIELDS = {
    "readiness_class",
    "required_skill_kind",
    "required_produced_interface",
}
TERMINAL_NULL_REQUIREMENT_FIELDS = {"readiness_class", "target_policy"}
RESPONSE_POLICY: dict[str, object] = {
    "natural_language_evidence": "unverified-inventory-only",
    "positive_evidence_requirement": "bundle-verified-hash-bound-gate-evidence",
    "route_selection": "requested-terminal-intent",
    "canonical_route_output": "registered-skill-id-or-null",
    "terminal_intent_routes": {
        "external-publish": None,
        "destructive-delete": None,
        "scheduler-submit": None,
        "scheduler-control": None,
        "execution-authorization": None,
        "scientific-acceptance-decision": None,
        "structure-export": None,
        "structure-transformation": None,
        "scientific-report": None,
        "review-response": None,
        "literature-plan": None,
    },
    "terminal_intent_requirements": {
        "external-publish": {
            "readiness_class": "intentionally-disabled",
            "target_policy": "null-only",
        },
        "destructive-delete": {
            "readiness_class": "intentionally-disabled",
            "target_policy": "null-only",
        },
        "scheduler-submit": {
            "readiness_class": "missing-route",
            "required_action_side_effect": "scheduler-submit",
        },
        "scheduler-control": {
            "readiness_class": "missing-route",
            "required_action_side_effect": "scheduler-control",
        },
        "execution-authorization": {
            "readiness_class": "human-boundary",
            "target_policy": "null-only",
        },
        "scientific-acceptance-decision": {
            "readiness_class": "human-boundary",
            "target_policy": "null-only",
        },
        "structure-export": {
            "readiness_class": "missing-route",
            "required_skill_kind": "structure",
            "required_produced_interface": "structure-export-manifest@1.0",
        },
        "structure-transformation": {
            "readiness_class": "missing-route",
            "required_skill_kind": "structure",
            "required_produced_interface": "structure-transformation-manifest@1.0",
        },
        "scientific-report": {
            "readiness_class": "missing-route",
            "required_skill_kind": "reporting",
            "required_produced_interface": "scientific-report@1.0",
        },
        "review-response": {
            "readiness_class": "missing-route",
            "required_skill_kind": "reporting",
            "required_produced_interface": "review-evidence-map@1.0",
        },
        "literature-plan": {
            "readiness_class": "missing-route",
            "required_skill_kind": "advisory",
            "required_produced_interface": "literature-evidence-plan@1.0",
        },
    },
    "terminal_intent_blocked_reasons": {
        "external-publish": "external-publish-not-routable",
        "destructive-delete": "destructive-delete-not-routable",
        "scheduler-submit": "runtime-route-not-active",
        "scheduler-control": "runtime-route-not-active",
        "execution-authorization": "human-authorization-required",
        "scientific-acceptance-decision": "human-scientific-decision-required",
        "structure-export": "structure-preparation-route-not-active",
        "structure-transformation": "structure-preparation-route-not-active",
        "scientific-report": "reporting-route-not-active",
        "review-response": "review-response-route-not-active",
        "literature-plan": "literature-planning-route-not-active",
    },
    "claim_ceiling_basis": "highest-fully-satisfied-gate-profile",
    "unverified_claim_ceiling": "no_positive_claim",
    "canonical_status_output": "action-state",
    "hard_block_action_state": "local_gate_blocked",
    "missing_evidence_action_state": "needs_evidence",
    "native_status_reporting": "preserve-in-gates-and-finding-codes",
    "action_state_precedence": [
        "failed_terminal",
        "failed_recoverable",
        "local_gate_blocked",
        "needs_evidence",
        "needs_authorization",
        "ready_for_deterministic_check",
        "deterministic_check_running",
        "ready_for_authorized_execution",
        "execution_in_progress",
        "handoff_ready",
        "local_gate_passed_limited",
        "complete",
    ],
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def registry_path() -> Path:
    return repo_root() / "registry" / "operation-routes.yaml"


def _finding(code: str, location: str, message: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message}


def load_registry(path: Path | None = None) -> dict[str, Any]:
    selected = path or registry_path()
    return load_yaml_strict(selected, "operation-routes.yaml")


def _safe_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in value


def _nonroutable_required_reads(skill_id: str, lifecycle: str) -> list[str]:
    """Return maintenance reads without treating source-backed development as active."""

    reads = [
        "registry/skill-registry.yaml",
        "registry/operation-routes.yaml",
    ]
    if lifecycle == "development":
        reads.extend(
            (
                f"skills/{skill_id}/SKILL.md",
                f"skills/{skill_id}/references/weak-model-decision-table.json",
            )
        )
    return reads


def _string_list(
    value: object,
    location: str,
    findings: list[dict[str, str]],
    *,
    allow_empty: bool = False,
    interface_ids: bool = False,
    skill_ids: bool = False,
) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        findings.append(
            _finding(
                "ROUTE_ENTRY_INVALID",
                location,
                "expected a list" + ("" if allow_empty else " with at least one item"),
            )
        )
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        item_location = f"{location}/{index}"
        if not isinstance(item, str) or not item.strip():
            findings.append(_finding("ROUTE_ENTRY_INVALID", item_location, "expected a nonempty string"))
            continue
        if interface_ids and not INTERFACE_ID.fullmatch(item):
            findings.append(_finding("ROUTE_HANDOFF_INVALID", item_location, "invalid interface identifier"))
        if skill_ids and not SKILL_ID.fullmatch(item):
            findings.append(_finding("ROUTE_HANDOFF_INVALID", item_location, "invalid skill identifier"))
        result.append(item)
    if len(result) != len(set(result)):
        findings.append(_finding("ROUTE_ENTRY_INVALID", location, "duplicate list items are forbidden"))
    return result


def _side_effect_list(
    value: object,
    location: str,
    findings: list[dict[str, str]],
    *,
    finding_code: str,
) -> list[str]:
    """Validate one canonical, deterministic common sideEffectSet representation."""

    values = _string_list(value, location, findings)
    invalid = [item for item in values if item not in SIDE_EFFECT_SET]
    for index, item in enumerate(values):
        if item not in SIDE_EFFECT_SET:
            findings.append(
                _finding(finding_code, f"{location}/{index}", f"unsupported canonical side effect {item!r}")
            )
    if invalid:
        return values
    if values != sorted(values, key=SIDE_EFFECT_ORDER.__getitem__):
        findings.append(
            _finding(
                finding_code,
                location,
                "side effects must follow the canonical common-contract order",
            )
        )
    if "read-only" in values and len(values) != 1:
        findings.append(
            _finding(
                finding_code,
                location,
                "read-only is exclusive and cannot accompany an effectful capability",
            )
        )
    return values


def terminal_intent_findings(
    data: object,
    *,
    skill_data: object,
) -> list[dict[str, str]]:
    """Enforce that every non-null terminal target is actually executable."""

    findings: list[dict[str, str]] = []
    if not isinstance(data, dict):
        return [
            _finding(
                "ROUTE_TERMINAL_POLICY_INVALID",
                "response_policy",
                "operation-route registry must be a mapping",
            )
        ]
    policy = data.get("response_policy")
    routes = data.get("routes")
    registered = (
        skill_data.get("skills")
        if isinstance(skill_data, dict)
        else None
    )
    if (
        not isinstance(policy, dict)
        or not isinstance(routes, dict)
        or not isinstance(registered, dict)
    ):
        return [
            _finding(
                "ROUTE_TERMINAL_POLICY_INVALID",
                "response_policy",
                "terminal validation requires response policy, routes, and Skills",
            )
        ]
    targets = policy.get("terminal_intent_routes")
    requirements = policy.get("terminal_intent_requirements")
    reasons = policy.get("terminal_intent_blocked_reasons")
    if not isinstance(targets, dict) or not targets:
        return [
            _finding(
                "ROUTE_TERMINAL_POLICY_INVALID",
                "response_policy/terminal_intent_routes",
                "terminal intent routes must be a nonempty mapping",
            )
        ]
    if not isinstance(requirements, dict) or set(requirements) != set(targets):
        findings.append(
            _finding(
                "ROUTE_TERMINAL_REQUIREMENT_INVALID",
                "response_policy/terminal_intent_requirements",
                "requirements must be a mapping with exactly the terminal intent keys",
            )
        )
        requirements = requirements if isinstance(requirements, dict) else {}
    if not isinstance(reasons, dict):
        reasons = {}
        findings.append(
            _finding(
                "ROUTE_TERMINAL_BLOCKED_REASON_MISSING",
                "response_policy/terminal_intent_blocked_reasons",
                "blocked-reason mapping is required",
            )
        )

    null_intents: set[str] = set()
    for intent, target in targets.items():
        location = f"response_policy/terminal_intent_routes/{intent}"
        if not isinstance(intent, str) or GATE_ID.fullmatch(intent) is None:
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_INTENT_INVALID",
                    location,
                    "terminal intent must be a stable identifier",
                )
            )
            continue
        requirement = requirements.get(intent)
        requirement_location = (
            f"response_policy/terminal_intent_requirements/{intent}"
        )
        readiness_class = (
            requirement.get("readiness_class")
            if isinstance(requirement, dict)
            else None
        )
        requirement_valid = True
        if not isinstance(requirement, dict):
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_REQUIREMENT_INVALID",
                    requirement_location,
                    "terminal intent requirement must be a mapping",
                )
            )
            requirement_valid = False
        elif readiness_class not in TERMINAL_READINESS_CLASSES:
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_REQUIREMENT_INVALID",
                    f"{requirement_location}/readiness_class",
                    "unsupported terminal readiness class",
                )
            )
            requirement_valid = False
        elif readiness_class in TERMINAL_NULL_ONLY_CLASSES:
            if (
                set(requirement) != TERMINAL_NULL_REQUIREMENT_FIELDS
                or requirement.get("target_policy") != "null-only"
            ):
                findings.append(
                    _finding(
                        "ROUTE_TERMINAL_REQUIREMENT_INVALID",
                        requirement_location,
                        "human-boundary and intentionally-disabled intents require target_policy=null-only",
                    )
                )
                requirement_valid = False
        elif set(requirement) == TERMINAL_ACTION_REQUIREMENT_FIELDS:
            required_effect = requirement.get("required_action_side_effect")
            if required_effect not in SIDE_EFFECT_SET:
                findings.append(
                    _finding(
                        "ROUTE_TERMINAL_REQUIREMENT_INVALID",
                        f"{requirement_location}/required_action_side_effect",
                        "required action side effect is not canonical",
                    )
                )
                requirement_valid = False
        elif set(requirement) == TERMINAL_SKILL_REQUIREMENT_FIELDS:
            required_kind = requirement.get("required_skill_kind")
            required_interface = requirement.get("required_produced_interface")
            if not isinstance(required_kind, str) or not required_kind:
                findings.append(
                    _finding(
                        "ROUTE_TERMINAL_REQUIREMENT_INVALID",
                        f"{requirement_location}/required_skill_kind",
                        "required Skill kind must be a nonempty string",
                    )
                )
                requirement_valid = False
            if (
                not isinstance(required_interface, str)
                or INTERFACE_ID.fullmatch(required_interface) is None
            ):
                findings.append(
                    _finding(
                        "ROUTE_TERMINAL_REQUIREMENT_INVALID",
                        f"{requirement_location}/required_produced_interface",
                        "required produced interface must be a canonical interface identifier",
                    )
                )
                requirement_valid = False
        else:
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_REQUIREMENT_INVALID",
                    requirement_location,
                    "missing-route intent requires an action-side-effect or Skill-kind/interface binding",
                )
            )
            requirement_valid = False
        if target is None:
            null_intents.add(intent)
            reason = reasons.get(intent)
            if not isinstance(reason, str) or GATE_ID.fullmatch(reason) is None:
                findings.append(
                    _finding(
                        "ROUTE_TERMINAL_BLOCKED_REASON_MISSING",
                        f"response_policy/terminal_intent_blocked_reasons/{intent}",
                        "null terminal target requires a stable blocked reason",
                    )
                )
            continue
        if readiness_class in TERMINAL_NULL_ONLY_CLASSES:
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_TARGET_CAPABILITY_MISMATCH",
                    location,
                    f"{readiness_class} intent requires a null terminal target",
                )
            )
        if not isinstance(target, str) or SKILL_ID.fullmatch(target) is None:
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_TARGET_INVALID",
                    location,
                    "terminal target must be a registered Skill ID or null",
                )
            )
            continue
        registered_target = registered.get(target)
        route = routes.get(target)
        if (
            not isinstance(registered_target, dict)
            or registered_target.get("lifecycle") != "active"
            or not isinstance(route, dict)
            or route.get("lifecycle") != "active"
        ):
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_TARGET_NOT_ACTIVE",
                    location,
                    "non-null terminal target must have active lifecycle",
                )
            )
        if not isinstance(route, dict) or route.get("routable") is not True:
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_TARGET_NOT_ROUTABLE",
                    location,
                    "non-null terminal target must be routable",
                )
            )
            continue
        actions = route.get("actions")
        if not isinstance(actions, dict) or not actions:
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_TARGET_ACTIONLESS",
                    location,
                    "non-null terminal target must expose at least one action",
                )
            )
            continue
        sequences = route.get("tool_sequence")
        reachable = {
            action_id
            for sequence in sequences.values()
            if isinstance(sequence, list)
            for action_id in sequence
            if isinstance(action_id, str) and action_id in actions
        } if isinstance(sequences, dict) else set()
        if not reachable:
            findings.append(
                _finding(
                    "ROUTE_TERMINAL_TARGET_ACTION_UNREACHABLE",
                    location,
                    "non-null terminal target needs a reachable registered action",
                )
            )
            continue
        if not requirement_valid or not isinstance(requirement, dict):
            continue
        if "required_action_side_effect" in requirement:
            required_effect = requirement["required_action_side_effect"]
            capable_actions = {
                action_id
                for action_id in reachable
                if isinstance(actions.get(action_id), dict)
                and isinstance(actions[action_id].get("side_effects"), list)
                and required_effect in actions[action_id]["side_effects"]
            }
            if not capable_actions:
                findings.append(
                    _finding(
                        "ROUTE_TERMINAL_TARGET_CAPABILITY_MISMATCH",
                        location,
                        f"no reachable action declares required side effect {required_effect!r}",
                    )
                )
        elif "required_skill_kind" in requirement:
            required_kind = requirement["required_skill_kind"]
            required_interface = requirement["required_produced_interface"]
            produced = (
                registered_target.get("produces")
                if isinstance(registered_target, dict)
                else None
            )
            if (
                not isinstance(registered_target, dict)
                or registered_target.get("kind") != required_kind
                or not isinstance(produced, list)
                or required_interface not in produced
            ):
                findings.append(
                    _finding(
                        "ROUTE_TERMINAL_TARGET_CAPABILITY_MISMATCH",
                        location,
                        "target Skill does not match the required kind and produced interface",
                    )
                )

    for intent in sorted(set(reasons).difference(null_intents)):
        findings.append(
            _finding(
                "ROUTE_TERMINAL_BLOCKED_REASON_UNEXPECTED",
                f"response_policy/terminal_intent_blocked_reasons/{intent}",
                "blocked reason is allowed only for a null terminal target",
            )
        )
    return sorted(findings, key=lambda item: (
        item["code"],
        item["location"],
        item["message"],
    ))


def validation_findings(
    data: object,
    *,
    source_root: Path | None = None,
    skill_data: dict[str, Any] | None = None,
    interface_data: dict[str, Any] | None = None,
    software_data: dict[str, Any] | None = None,
    environment_data: dict[str, Any] | None = None,
    dependency_source_validation: bool = True,
) -> list[dict[str, str]]:
    """Return stable finding records for an operation-route registry."""

    findings: list[dict[str, str]] = []
    if not isinstance(data, dict):
        return [_finding("ROUTE_REGISTRY_NOT_MAPPING", "<root>", "registry must be a mapping")]
    if COMMON_DEFINITIONS_ERROR is not None:
        findings.append(
            _finding(
                "ROUTE_COMMON_CONTRACT_INVALID",
                "contracts/common-definitions-1.0.schema.json",
                COMMON_DEFINITIONS_ERROR,
            )
        )
    expected_root = {"schema_version", "response_policy", "routes"}
    if set(data) != expected_root:
        findings.append(
            _finding(
                "ROUTE_FIELDS_INVALID",
                "<root>",
                f"expected fields {sorted(expected_root)!r}, found {sorted(map(str, data))!r}",
            )
        )
    if data.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            _finding(
                "ROUTE_SCHEMA_VERSION_UNSUPPORTED",
                "schema_version",
                f"expected {SCHEMA_VERSION!r}",
            )
        )
    if data.get("response_policy") != RESPONSE_POLICY:
        findings.append(
            _finding(
                "ROUTE_RESPONSE_POLICY_INVALID",
                "response_policy",
                "weak-model response projection policy differs from the frozen canonical policy",
            )
        )

    root = (source_root or repo_root()).resolve()
    if skill_data is None:
        try:
            skill_data = skill_registry.load_registry()
        except (OSError, ValueError, yaml.YAMLError) as exc:
            findings.append(_finding("ROUTE_SKILL_REGISTRY_INVALID", "skill-registry", str(exc)))
            skill_data = {"skills": {}}
    if interface_data is None:
        try:
            interface_data = interface_registry.load_registry()
        except (OSError, ValueError, yaml.YAMLError) as exc:
            findings.append(_finding("ROUTE_INTERFACE_REGISTRY_INVALID", "interface-registry", str(exc)))
            interface_data = {"interfaces": {}}
    if software_data is None:
        try:
            software_data = software_registry.load_registry()
        except (OSError, ValueError, yaml.YAMLError) as exc:
            findings.append(_finding("ROUTE_SOFTWARE_REGISTRY_INVALID", "software-registry", str(exc)))
            software_data = {"software": {}, "planned_software": {}}
    if environment_data is None:
        try:
            environment_data = environment_profiles.load_registry()
        except (OSError, ValueError, yaml.YAMLError) as exc:
            findings.append(_finding("ROUTE_ENVIRONMENT_REGISTRY_INVALID", "environment-profiles", str(exc)))
            environment_data = {"profiles": {}}

    dependency_checks = (
        (
            "ROUTE_ENVIRONMENT_REGISTRY_INVALID",
            "environment-profiles",
            lambda: environment_profiles.validation_errors(environment_data),
        ),
        (
            "ROUTE_SOFTWARE_REGISTRY_INVALID",
            "software-registry",
            lambda: software_registry.validation_errors(
                software_data,
                root,
                environment_data,
            ),
        ),
        (
            "ROUTE_INTERFACE_REGISTRY_INVALID",
            "interface-registry",
            lambda: interface_registry.validation_errors(interface_data, root),
        ),
        (
            "ROUTE_SKILL_REGISTRY_INVALID",
            "skill-registry",
            lambda: skill_registry.validation_errors(
                skill_data,
                root if dependency_source_validation else None,
                software_data,
                interface_data,
                environment_data,
            ),
        ),
    )
    for finding_code, location, check in dependency_checks:
        try:
            dependency_errors = check()
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
            dependency_errors = [f"{exc.__class__.__name__}: registry validation failed"]
        for error in dependency_errors:
            findings.append(_finding(finding_code, location, error))

    # Never interpret a route/action graph from invalid dependency snapshots.
    # Source-tree hash and hygiene failures are trust blockers, not warnings that
    # route-local consistency can override.
    dependency_codes = {
        "ROUTE_COMMON_CONTRACT_INVALID",
        "ROUTE_ENVIRONMENT_REGISTRY_INVALID",
        "ROUTE_SOFTWARE_REGISTRY_INVALID",
        "ROUTE_INTERFACE_REGISTRY_INVALID",
        "ROUTE_SKILL_REGISTRY_INVALID",
    }
    if any(item["code"] in dependency_codes for item in findings):
        return findings

    routes = data.get("routes")
    if not isinstance(routes, dict) or not routes:
        findings.append(_finding("ROUTE_REGISTRY_NOT_MAPPING", "routes", "routes must be a nonempty mapping"))
        return findings
    registered_skills = skill_data.get("skills", {}) if isinstance(skill_data, dict) else {}
    findings.extend(
        terminal_intent_findings(
            data,
            skill_data=skill_data,
        )
    )
    registered_interfaces = interface_data.get("interfaces", {}) if isinstance(interface_data, dict) else {}
    if set(routes) != set(registered_skills):
        missing = sorted(set(registered_skills).difference(routes))
        extra = sorted(set(routes).difference(registered_skills))
        findings.append(
            _finding(
                "ROUTE_SET_MISMATCH",
                "routes",
                f"missing registered skills {missing!r}; unexpected routes {extra!r}",
            )
        )

    for name, route in routes.items():
        location = f"routes/{name}"
        if not isinstance(name, str) or not SKILL_ID.fullmatch(name):
            findings.append(_finding("ROUTE_ENTRY_INVALID", location, "invalid skill identifier"))
        if not isinstance(route, dict):
            findings.append(_finding("ROUTE_ENTRY_INVALID", location, "route must be a mapping"))
            continue
        if set(route) != ROUTE_FIELDS:
            findings.append(
                _finding(
                    "ROUTE_FIELDS_INVALID",
                    location,
                    f"expected fields {sorted(ROUTE_FIELDS)!r}, found {sorted(map(str, route))!r}",
                )
            )

        registered = registered_skills.get(name)
        registered = registered if isinstance(registered, dict) else {}
        lifecycle = route.get("lifecycle")
        if lifecycle not in LIFECYCLES:
            findings.append(_finding("ROUTE_ENTRY_INVALID", f"{location}/lifecycle", "unsupported lifecycle"))
        elif lifecycle != registered.get("lifecycle"):
            findings.append(
                _finding(
                    "ROUTE_LIFECYCLE_MISMATCH",
                    f"{location}/lifecycle",
                    f"route {lifecycle!r} != skill registry {registered.get('lifecycle')!r}",
                )
            )
        routable = route.get("routable")
        if not isinstance(routable, bool):
            findings.append(_finding("ROUTE_ENTRY_INVALID", f"{location}/routable", "expected boolean"))
        if lifecycle == "active" and routable is not True:
            findings.append(_finding("ROUTE_ACTIVE_DISABLED", location, "active route must be routable"))
        if lifecycle in NON_ROUTABLE_LIFECYCLES and routable is not False:
            findings.append(
                _finding("ROUTE_PLANNED_ROUTABLE", location, "non-active route must not be routable")
            )

        reads = _string_list(route.get("required_reads"), f"{location}/required_reads", findings)
        if lifecycle in NON_ROUTABLE_LIFECYCLES and reads != _nonroutable_required_reads(name, lifecycle):
            findings.append(
                _finding(
                    "ROUTE_PLANNED_READ_SET_INVALID",
                    f"{location}/required_reads",
                    "non-active route must use its lifecycle-specific maintenance read set",
                )
            )
        for index, read in enumerate(reads):
            read_location = f"{location}/required_reads/{index}"
            if not _safe_relative_path(read):
                findings.append(_finding("ROUTE_READ_UNSAFE", read_location, "expected a safe relative path"))
            elif lifecycle in LIFECYCLES and not root.joinpath(read).is_file():
                findings.append(_finding("ROUTE_READ_MISSING", read_location, f"missing required read {read!r}"))

        route_side_effects = _side_effect_list(
            route.get("side_effects"),
            f"{location}/side_effects",
            findings,
            finding_code="ROUTE_ENTRY_INVALID",
        )

        actions = route.get("actions")
        if not isinstance(actions, dict):
            findings.append(_finding("ROUTE_ACTION_INVALID", f"{location}/actions", "expected an action mapping"))
            actions = {}
        for action_id, action in actions.items():
            action_location = f"{location}/actions/{action_id}"
            if not isinstance(action_id, str) or not ACTION_ID.fullmatch(action_id):
                findings.append(_finding("ROUTE_ACTION_INVALID", action_location, "invalid action identifier"))
            if not isinstance(action, dict) or set(action) != ACTION_FIELDS:
                findings.append(
                    _finding(
                        "ROUTE_ACTION_INVALID",
                        action_location,
                        f"expected fields {sorted(ACTION_FIELDS)!r}",
                    )
                )
                continue
            argv = _string_list(action.get("argv"), f"{action_location}/argv", findings)
            for index, token in enumerate(argv):
                if re.search(r"\s|[|;&`$]", token):
                    findings.append(
                        _finding(
                            "ROUTE_ACTION_NOT_DETERMINISTIC",
                            f"{action_location}/argv/{index}",
                            "argv tokens cannot contain whitespace, prose fragments, or shell metacharacters",
                        )
                    )
            if len(argv) < 2 or argv[:2] != ["python3", "-B"]:
                findings.append(
                    _finding(
                        "ROUTE_ACTION_NOT_DETERMINISTIC",
                        f"{action_location}/argv",
                        "deterministic repository actions must start with python3 -B",
                    )
                )
            if len(argv) < 3 or not _safe_relative_path(argv[2]) or not root.joinpath(argv[2]).is_file():
                findings.append(
                    _finding(
                        "ROUTE_ACTION_SCRIPT_INVALID",
                        f"{action_location}/argv/2",
                        "repository action must name an existing safe relative Python script",
                    )
                )
            success_codes = action.get("success_exit_codes")
            limited_codes = action.get("limited_exit_codes")
            for key, codes, allow_empty in (
                ("success_exit_codes", success_codes, False),
                ("limited_exit_codes", limited_codes, True),
            ):
                if (
                    not isinstance(codes, list)
                    or (not allow_empty and not codes)
                    or any(not isinstance(code, int) for code in codes)
                    or len(codes) != len(set(codes))
                ):
                    findings.append(
                        _finding("ROUTE_ACTION_INVALID", f"{action_location}/{key}", "invalid exit-code list")
                    )
            if isinstance(success_codes, list) and isinstance(limited_codes, list) and set(success_codes).intersection(limited_codes):
                findings.append(
                    _finding(
                        "ROUTE_ACTION_INVALID",
                        action_location,
                        "success and limited exit codes must be disjoint",
                    )
                )
            if isinstance(success_codes, list) and success_codes != [0]:
                findings.append(
                    _finding(
                        "ROUTE_ACTION_INVALID",
                        f"{action_location}/success_exit_codes",
                        "repository wrappers must normalize successful execution to exit code 0",
                    )
                )
            if isinstance(limited_codes, list) and any(code <= 0 or code > 255 for code in limited_codes):
                findings.append(
                    _finding(
                        "ROUTE_ACTION_INVALID",
                        f"{action_location}/limited_exit_codes",
                        "limited exit codes must be distinct process codes from 1 through 255",
                    )
                )
            action_side_effects = _side_effect_list(
                action.get("side_effects"),
                f"{action_location}/side_effects",
                findings,
                finding_code="ROUTE_ACTION_INVALID",
            )
            if set(action_side_effects).difference(route_side_effects):
                findings.append(
                    _finding(
                        "ROUTE_ACTION_INVALID",
                        f"{action_location}/side_effects",
                        "action side effects exceed the registered route capability set",
                    )
                )
            if argv and argv[0] == "python3" and "local-execution" not in action_side_effects:
                findings.append(
                    _finding(
                        "ROUTE_ACTION_INVALID",
                        f"{action_location}/side_effects",
                        "a Python entrypoint must declare local-execution",
                    )
                )
            if "--live-check" in argv and "network-read" not in action_side_effects:
                findings.append(
                    _finding(
                        "ROUTE_ACTION_INVALID",
                        f"{action_location}/side_effects",
                        "a live source check must declare network-read",
                    )
                )
            output_flags = {"--out", "--json", "--markdown"}
            if output_flags.intersection(argv) and "local-write" not in action_side_effects:
                findings.append(
                    _finding(
                        "ROUTE_ACTION_INVALID",
                        f"{action_location}/side_effects",
                        "an action with an explicit output path must declare local-write",
                    )
                )
            if not isinstance(action.get("requires_authorization"), bool):
                findings.append(
                    _finding("ROUTE_ACTION_INVALID", f"{action_location}/requires_authorization", "expected boolean")
                )
            elif AUTHORIZATION_REQUIRED_SIDE_EFFECTS.intersection(action_side_effects) and action.get(
                "requires_authorization"
            ) is not True:
                findings.append(
                    _finding(
                        "ROUTE_ACTION_INVALID",
                        f"{action_location}/requires_authorization",
                        "mutation of remote, scheduler, publication, or deletion state requires explicit authorization",
                    )
                )
            if action.get("maximum_claim") not in CLAIM_CEILINGS:
                findings.append(_finding("ROUTE_CLAIM_INVALID", f"{action_location}/maximum_claim", "invalid claim ceiling"))
            elif route.get("maximum_claim") in CLAIM_CEILINGS and CLAIM_CEILINGS.index(
                action["maximum_claim"]
            ) > CLAIM_CEILINGS.index(route["maximum_claim"]):
                findings.append(
                    _finding(
                        "ROUTE_CLAIM_INVALID",
                        f"{action_location}/maximum_claim",
                        "action claim ceiling exceeds the route ceiling",
                    )
                )

        first_tool = route.get("first_tool")
        sequences = route.get("tool_sequence")
        if not isinstance(first_tool, dict) or not isinstance(sequences, dict):
            findings.append(
                _finding(
                    "ROUTE_TOOL_SEQUENCE_INVALID",
                    f"{location}/first_tool",
                    "first_tool and tool_sequence must be mode-to-action mappings",
                )
            )
            first_tool = {}
            sequences = {}
        if set(first_tool).difference(REQUEST_MODES) or set(sequences).difference(REQUEST_MODES):
            findings.append(
                _finding("ROUTE_TOOL_SEQUENCE_INVALID", location, "unsupported request mode in tool routing")
            )
        if set(first_tool) != set(sequences):
            findings.append(
                _finding("ROUTE_TOOL_SEQUENCE_INVALID", location, "first_tool and tool_sequence modes must match")
            )
        for mode, first_action in first_tool.items():
            mode_location = f"{location}/first_tool/{mode}"
            sequence = sequences.get(mode)
            if not isinstance(first_action, str) or first_action not in actions:
                findings.append(_finding("ROUTE_TOOL_SEQUENCE_INVALID", mode_location, "unknown first action"))
            if not isinstance(sequence, list) or not sequence or sequence[0] != first_action:
                findings.append(
                    _finding(
                        "ROUTE_TOOL_SEQUENCE_INVALID",
                        f"{location}/tool_sequence/{mode}",
                        "sequence must start with the selected first action",
                    )
                )
                continue
            if len(sequence) != len(set(sequence)):
                findings.append(
                    _finding(
                        "ROUTE_TOOL_SEQUENCE_INVALID",
                        f"{location}/tool_sequence/{mode}",
                        "mode sequence cannot repeat an action",
                    )
                )
            for index, action_id in enumerate(sequence):
                if not isinstance(action_id, str) or action_id not in actions:
                    findings.append(
                        _finding(
                            "ROUTE_TOOL_SEQUENCE_INVALID",
                            f"{location}/tool_sequence/{mode}/{index}",
                            "unknown action identifier",
                        )
                    )
        referenced_actions = {
            action_id
            for sequence in sequences.values()
            if isinstance(sequence, list)
            for action_id in sequence
            if isinstance(action_id, str)
        }
        for action_id in sorted(set(actions).difference(referenced_actions)):
            findings.append(
                _finding(
                    "ROUTE_ACTION_UNREACHABLE",
                    f"{location}/actions/{action_id}",
                    "registered action must be reachable from at least one request-mode sequence",
                )
            )
        if lifecycle == "active" and (not actions or not first_tool):
            findings.append(_finding("ROUTE_TOOL_SEQUENCE_INVALID", location, "active route needs mode-specific actions"))
        if lifecycle in NON_ROUTABLE_LIFECYCLES and (actions or first_tool or sequences):
            findings.append(
                _finding(
                    "ROUTE_PLANNED_ROUTABLE",
                    location,
                    "non-active route must not declare executable actions",
                )
            )

        if lifecycle == "active" and isinstance(actions, dict):
            action_effect_union = {
                effect
                for action in actions.values()
                if isinstance(action, dict) and isinstance(action.get("side_effects"), list)
                for effect in action["side_effects"]
                if isinstance(effect, str)
            }
            if set(route_side_effects) != action_effect_union:
                findings.append(
                    _finding(
                        "ROUTE_SIDE_EFFECT_MISMATCH",
                        f"{location}/side_effects",
                        "active route side effects must equal the union of its reachable action effects",
                    )
                )
        registered_side_effects = registered.get("side_effects")
        if (
            not isinstance(registered_side_effects, list)
            or not registered_side_effects
            or any(item not in SIDE_EFFECT_SET for item in registered_side_effects)
            or len(registered_side_effects) != len(set(registered_side_effects))
        ):
            findings.append(
                _finding(
                    "ROUTE_SKILL_REGISTRY_INVALID",
                    f"skill-registry/skills/{name}/side_effects",
                    "skill registry side effects must be a nonempty canonical common sideEffectSet",
                )
            )
        elif route_side_effects != registered_side_effects:
            findings.append(
                _finding(
                    "ROUTE_SIDE_EFFECT_MISMATCH",
                    f"{location}/side_effects",
                    f"route {route_side_effects!r} != skill registry {registered_side_effects!r}",
                )
            )
        _string_list(route.get("minimum_evidence"), f"{location}/minimum_evidence", findings)

        mapping = route.get("native_status_mapping")
        if not isinstance(mapping, dict) or not mapping:
            findings.append(
                _finding("ROUTE_NATIVE_MAPPING_INVALID", f"{location}/native_status_mapping", "expected mapping")
            )
        else:
            for native, normalized in mapping.items():
                item_location = f"{location}/native_status_mapping/{native}"
                if not isinstance(native, str) or not native.strip():
                    findings.append(_finding("ROUTE_NATIVE_MAPPING_INVALID", item_location, "invalid native status"))
                if normalized not in NORMALIZED_STATUSES:
                    findings.append(
                        _finding("ROUTE_NATIVE_MAPPING_INVALID", item_location, "invalid normalized status")
                    )

        maximum_claim = route.get("maximum_claim")
        if maximum_claim not in CLAIM_CEILINGS:
            findings.append(_finding("ROUTE_CLAIM_INVALID", f"{location}/maximum_claim", "invalid claim ceiling"))
        if lifecycle in NON_ROUTABLE_LIFECYCLES and maximum_claim != "no_positive_claim":
            findings.append(
                _finding(
                    "ROUTE_PLANNED_ROUTABLE",
                    f"{location}/maximum_claim",
                    "non-active route must allow no positive claim",
                )
            )

        claim_profile = route.get("claim_gate_profile")
        expected_profile_levels = (
            {"no_positive_claim"}
            if lifecycle in NON_ROUTABLE_LIFECYCLES
            else {
                level
                for level in CLAIM_CEILINGS
                if maximum_claim in CLAIM_CEILINGS
                and CLAIM_CEILINGS.index(level) <= CLAIM_CEILINGS.index(maximum_claim)
            }
        )
        if not isinstance(claim_profile, dict) or set(claim_profile) != expected_profile_levels:
            findings.append(
                _finding(
                    "ROUTE_CLAIM_PROFILE_INVALID",
                    f"{location}/claim_gate_profile",
                    f"expected levels {sorted(expected_profile_levels)!r}",
                )
            )
        else:
            for level, profile in claim_profile.items():
                profile_location = f"{location}/claim_gate_profile/{level}"
                if not isinstance(profile, dict) or set(profile) != CLAIM_PROFILE_FIELDS:
                    findings.append(
                        _finding("ROUTE_CLAIM_PROFILE_INVALID", profile_location, "expected all_of and any_of")
                    )
                    continue
                all_of = _string_list(profile.get("all_of"), f"{profile_location}/all_of", findings, allow_empty=True)
                any_of = _string_list(profile.get("any_of"), f"{profile_location}/any_of", findings, allow_empty=True)
                for gate_id in all_of + any_of:
                    if not GATE_ID.fullmatch(gate_id):
                        findings.append(
                            _finding("ROUTE_CLAIM_PROFILE_INVALID", profile_location, f"invalid gate id {gate_id!r}")
                        )
                if level != "no_positive_claim" and not all_of and not any_of:
                    findings.append(
                        _finding("ROUTE_CLAIM_PROFILE_INVALID", profile_location, "positive claim needs gate requirements")
                    )

        handoff = route.get("handoff")
        if not isinstance(handoff, dict):
            findings.append(_finding("ROUTE_HANDOFF_INVALID", f"{location}/handoff", "expected mapping"))
            continue
        if set(handoff) != HANDOFF_FIELDS:
            findings.append(
                _finding(
                    "ROUTE_HANDOFF_INVALID",
                    f"{location}/handoff",
                    f"expected fields {sorted(HANDOFF_FIELDS)!r}",
                )
            )
        status = handoff.get("status")
        if status not in HANDOFF_STATUSES:
            findings.append(_finding("ROUTE_HANDOFF_INVALID", f"{location}/handoff/status", "invalid status"))
        if lifecycle == "active" and status != "enabled":
            findings.append(_finding("ROUTE_HANDOFF_INVALID", f"{location}/handoff/status", "active handoff must be enabled"))
        if lifecycle in NON_ROUTABLE_LIFECYCLES and status != "blocked":
            findings.append(
                _finding(
                    "ROUTE_PLANNED_ROUTABLE",
                    f"{location}/handoff/status",
                    "non-active handoff must be blocked",
                )
            )
        produces = _string_list(
            handoff.get("produces"),
            f"{location}/handoff/produces",
            findings,
            allow_empty=True,
            interface_ids=True,
        )
        consumers = _string_list(
            handoff.get("consumers"),
            f"{location}/handoff/consumers",
            findings,
            allow_empty=True,
            skill_ids=True,
        )
        future_consumers = _string_list(
            handoff.get("future_consumers"),
            f"{location}/handoff/future_consumers",
            findings,
            allow_empty=True,
            skill_ids=True,
        )
        if set(consumers).intersection(future_consumers):
            findings.append(
                _finding(
                    "ROUTE_HANDOFF_INVALID",
                    f"{location}/handoff",
                    "active and future consumer sets must be disjoint",
                )
            )
        registered_produces = registered.get("produces")
        if isinstance(registered_produces, list) and set(produces) != set(registered_produces):
            findings.append(
                _finding(
                    "ROUTE_HANDOFF_REGISTRY_MISMATCH",
                    f"{location}/handoff/produces",
                    "route produces must exactly match the canonical skill registry",
                )
            )
        for index, interface_id in enumerate(produces):
            interface = registered_interfaces.get(interface_id)
            interface_location = f"{location}/handoff/produces/{index}"
            if not isinstance(interface, dict):
                findings.append(
                    _finding(
                        "ROUTE_HANDOFF_INTERFACE_UNKNOWN",
                        interface_location,
                        f"interface {interface_id!r} is not registered",
                    )
                )
            elif lifecycle == "active" and interface.get("lifecycle") != "active":
                findings.append(
                    _finding(
                        "ROUTE_HANDOFF_INTERFACE_INACTIVE",
                        interface_location,
                        "active routes may produce only active interfaces",
                    )
                )
            classification = interface.get("classification") if isinstance(interface, dict) else None
            if (
                isinstance(classification, dict)
                and classification.get("routing_scope") == "governance-only"
            ):
                findings.append(
                    _finding(
                        "ROUTE_HANDOFF_INTERFACE_GOVERNANCE_ONLY",
                        interface_location,
                        "governance-only records cannot enter normal Skill handoff routing",
                    )
                )
        for consumer_kind, consumer_names, expected_lifecycles in (
            ("consumers", consumers, {"active"}),
            ("future_consumers", future_consumers, NON_ROUTABLE_LIFECYCLES),
        ):
            for index, consumer_name in enumerate(consumer_names):
                consumer_location = f"{location}/handoff/{consumer_kind}/{index}"
                consumer = registered_skills.get(consumer_name)
                if not isinstance(consumer, dict):
                    findings.append(
                        _finding(
                            "ROUTE_HANDOFF_CONSUMER_UNKNOWN",
                            consumer_location,
                            f"consumer {consumer_name!r} is not registered",
                        )
                    )
                    continue
                if consumer.get("lifecycle") not in expected_lifecycles:
                    findings.append(
                        _finding(
                            "ROUTE_HANDOFF_CONSUMER_LIFECYCLE_INVALID",
                            consumer_location,
                            f"{consumer_kind} must contain only {sorted(expected_lifecycles)!r} skills",
                        )
                    )
                consumed_interfaces = consumer.get("consumes")
                if isinstance(consumed_interfaces, list) and not set(produces).intersection(consumed_interfaces):
                    findings.append(
                        _finding(
                            "ROUTE_HANDOFF_INTERFACE_MISMATCH",
                            consumer_location,
                            "consumer does not declare any interface produced by this route",
                        )
                    )
        _string_list(handoff.get("requirements"), f"{location}/handoff/requirements", findings)

    active_graph: dict[str, set[str]] = {}
    for name, route in routes.items():
        if not isinstance(route, dict) or route.get("lifecycle") != "active":
            continue
        handoff = route.get("handoff")
        consumers = handoff.get("consumers") if isinstance(handoff, dict) else None
        active_graph[name] = {
            consumer
            for consumer in consumers if isinstance(consumer, str) and consumer in routes
        } if isinstance(consumers, list) else set()
    indegree = {name: 0 for name in active_graph}
    for consumers in active_graph.values():
        for consumer in consumers:
            if consumer in indegree:
                indegree[consumer] += 1
    ready = sorted(name for name, degree in indegree.items() if degree == 0)
    visited: list[str] = []
    while ready:
        name = ready.pop(0)
        visited.append(name)
        for consumer in sorted(active_graph[name]):
            if consumer not in indegree:
                continue
            indegree[consumer] -= 1
            if indegree[consumer] == 0:
                ready.append(consumer)
                ready.sort()
    if len(visited) != len(active_graph):
        cycle_nodes = sorted(set(active_graph).difference(visited))
        findings.append(
            _finding(
                "ROUTE_HANDOFF_CYCLE",
                "routes",
                f"active automatic handoff graph must be acyclic; cyclic nodes {cycle_nodes!r}",
            )
        )
    return findings


def route_decision(
    skill_name: str,
    *,
    data: dict[str, Any] | None = None,
    source_root: Path | None = None,
    skill_data: dict[str, Any] | None = None,
    interface_data: dict[str, Any] | None = None,
    software_data: dict[str, Any] | None = None,
    environment_data: dict[str, Any] | None = None,
    dependency_source_validation: bool = True,
) -> tuple[int, dict[str, Any]]:
    """Return an exit code and a stable JSON route decision."""

    selected = data if data is not None else load_registry()
    findings = validation_findings(
        selected,
        source_root=source_root,
        skill_data=skill_data,
        interface_data=interface_data,
        software_data=software_data,
        environment_data=environment_data,
        dependency_source_validation=dependency_source_validation,
    )
    if findings:
        return 2, {
            "schema_version": SCHEMA_VERSION,
            "decision": "blocked",
            "skill": skill_name,
            "response_policy": selected.get("response_policy"),
            "finding_codes": sorted({item["code"] for item in findings}),
            "findings": findings,
            "route": None,
        }
    route = selected["routes"].get(skill_name)
    if route is None:
        finding = _finding("ROUTE_UNKNOWN_SKILL", f"routes/{skill_name}", "skill has no operation route")
        return 2, {
            "schema_version": SCHEMA_VERSION,
            "decision": "blocked",
            "skill": skill_name,
            "response_policy": selected["response_policy"],
            "finding_codes": [finding["code"]],
            "findings": [finding],
            "route": None,
        }
    if route["lifecycle"] != "active" or route["routable"] is not True:
        finding = _finding(
            "ROUTE_PLANNED_NOT_ROUTABLE",
            f"routes/{skill_name}",
            f"{route['lifecycle']} route is non-routable and cannot be invoked",
        )
        return 2, {
            "schema_version": SCHEMA_VERSION,
            "decision": "blocked",
            "skill": skill_name,
            "response_policy": selected["response_policy"],
            "finding_codes": [finding["code"]],
            "findings": [finding],
            "route": route,
        }
    return 0, {
        "schema_version": SCHEMA_VERSION,
        "decision": "route_selected",
        "skill": skill_name,
        "response_policy": selected["response_policy"],
        "finding_codes": [],
        "findings": [],
        "route": route,
    }


def _print_result(result: dict[str, Any], pretty: bool) -> None:
    print(json.dumps(result, indent=2 if pretty else None, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--skill-registry", type=Path)
    parser.add_argument("--interface-registry", type=Path)
    parser.add_argument("--software-registry", type=Path)
    parser.add_argument("--environment-profiles", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--pretty", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="Validate every route against the skill registry")
    route_parser = subparsers.add_parser("route", help="Return one lifecycle-safe route decision")
    route_parser.add_argument("skill")
    subparsers.add_parser("list", help="List active, development, and planned routes without activating them")
    args = parser.parse_args()
    selected_root = (args.root or repo_root()).resolve()

    try:
        data = load_registry(args.registry)
        skills = skill_registry.load_registry(args.skill_registry)
        interfaces = interface_registry.load_registry(args.interface_registry)
        software = software_registry.load_registry(args.software_registry)
        environments = environment_profiles.load_registry(args.environment_profiles)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        result = {
            "schema_version": SCHEMA_VERSION,
            "decision": "blocked",
            "finding_codes": ["ROUTE_REGISTRY_LOAD_FAILED"],
            "findings": [_finding("ROUTE_REGISTRY_LOAD_FAILED", "<registry>", str(exc))],
        }
        _print_result(result, args.pretty)
        return 2

    if args.command == "route":
        exit_code, result = route_decision(
            args.skill,
            data=data,
            source_root=selected_root,
            skill_data=skills,
            interface_data=interfaces,
            software_data=software,
            environment_data=environments,
        )
        _print_result(result, args.pretty)
        return exit_code

    findings = validation_findings(
        data,
        source_root=selected_root,
        skill_data=skills,
        interface_data=interfaces,
        software_data=software,
        environment_data=environments,
    )
    if findings:
        result = {
            "schema_version": SCHEMA_VERSION,
            "decision": "blocked",
            "finding_codes": sorted({item["code"] for item in findings}),
            "findings": findings,
        }
        _print_result(result, args.pretty)
        return 2
    routes = data["routes"]
    active = [name for name, route in routes.items() if route["lifecycle"] == "active"]
    development = [name for name, route in routes.items() if route["lifecycle"] == "development"]
    planned = [name for name, route in routes.items() if route["lifecycle"] == "planned"]
    result = {
        "schema_version": SCHEMA_VERSION,
        "decision": "pass",
        "response_policy": data["response_policy"],
        "finding_codes": [],
        "findings": [],
        "active": active,
        "development": development,
        "planned": planned,
    }
    _print_result(result, args.pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
