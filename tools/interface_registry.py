#!/usr/bin/env python3
"""Validate and resolve versioned Vibe-DFT handoff interfaces fail closed."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
import yaml

from registry_yaml import load_yaml_strict
from strict_json import StrictJSONError, load_object
from validate_contract import CatalogError, load_catalog


SCHEMA_VERSION = "1.0"
DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
INTERFACE_ID = re.compile(
    r"^(?P<name>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)@(?P<major>[1-9][0-9]*)\.(?P<minor>[0-9]+)$"
)
DOMAIN_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
LIFECYCLES = {"active", "planned"}
PRODUCER_POLICIES = {"skill", "external-input", "registry", "mixed"}
INTERFACE_REQUIRED_FIELDS = {
    "display_name",
    "lifecycle",
    "domain",
    "schema_path",
    "schema_sha256",
    "producer_policy",
}
INTERFACE_OPTIONAL_FIELDS = {"classification"}
CLASSIFICATION_FIELDS = {"document_kind", "routing_scope"}
DOCUMENT_KINDS = {"content-addressed-record", "projection", "definition-library"}
ROUTING_SCOPES = {"shared-handoff", "governance-only"}
GOVERNANCE_SCHEMAS = {
    "task-maturity": "task-maturity.schema.json",
    "activation-checklist": "activation-checklist.schema.json",
    "promotion-delta": "promotion-delta.schema.json",
}
MATURITY_LEVELS = (
    "design-only",
    "synthetic-validated",
    "format-fixture-validated",
    "real-artifact-validated",
    "tool-integration-validated",
)
MATURITY_RANK = {name: index for index, name in enumerate(MATURITY_LEVELS)}
MATURITY_AXES = {
    "invocation": "invocation_maturity",
    "parser": "parser_maturity",
    "scientific_validation": "scientific_validation_maturity",
}
CLAIM_LEVELS = (
    "no_positive_claim",
    "documented_behavior_only",
    "input_gates_only",
    "technical_run_gates_only",
    "numerical_candidate_only",
    "eligible_for_expert_review",
)
MAX_CLAIM_BY_MATURITY = {
    "design-only": "no_positive_claim",
    "synthetic-validated": "documented_behavior_only",
    "format-fixture-validated": "input_gates_only",
    "real-artifact-validated": "numerical_candidate_only",
    "tool-integration-validated": "eligible_for_expert_review",
}
PRIMARY_EVIDENCE_KIND_BY_AXIS = {
    "invocation": {
        "synthetic-validated": "invocation-synthetic-test",
        "format-fixture-validated": "invocation-format-fixture-test",
        "real-artifact-validated": "invocation-real-artifact-test",
        "tool-integration-validated": "invocation-tool-integration-test",
    },
    "parser": {
        "synthetic-validated": "parser-synthetic-test",
        "format-fixture-validated": "parser-format-fixture-test",
        "real-artifact-validated": "parser-real-artifact-test",
        "tool-integration-validated": "parser-tool-integration-test",
    },
    "scientific_validation": {
        "synthetic-validated": "scientific-synthetic-validation",
        "format-fixture-validated": "scientific-format-fixture-validation",
        "real-artifact-validated": "scientific-real-artifact-validation",
        "tool-integration-validated": "task-specific-scientific-validation",
    },
}
REQUIRED_PROMOTION_SHARED = {
    "registry/skill-registry.yaml",
    "registry/interface-registry.yaml",
    "registry/operation-routes.yaml",
}
SOFTWARE_PROMOTION_SHARED = {
    "registry/software-registry.yaml",
    "registry/environment-profiles.yaml",
}
UNRESOLVED_VERSION_LABELS = {
    "unknown",
    "unresolved",
    "any",
    "n/a",
    "na",
    "none",
    "latest",
    "dev",
    "development",
    "head",
    "main",
    "x",
}


class PlannedInterfaceError(ValueError):
    """A known interface was queried through the active routing gate."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def registry_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "registry" / "interface-registry.yaml"


def load_registry(path: Path | None = None) -> dict[str, Any]:
    selected = path or registry_path()
    return load_yaml_strict(selected, "interface-registry.yaml")


def _safe_schema_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and len(path.parts) == 2
        and path.parts[0] == "contracts"
        and path.name.endswith(".schema.json")
    )


def _is_exact_provider_version(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in UNRESOLVED_VERSION_LABELS:
        return False
    if any(marker in value for marker in ("*", ">", "<", "^", "~", ",", "|", "/")):
        return False
    if re.search(r"(?:^|[._\s-])(?:x|latest)(?:[0-9]*)(?:$|[._\s-])", normalized):
        return False
    if re.search(r"(?<![a-z])dev(?:elopment)?[0-9]*(?:$|[._\s-])", normalized):
        return False
    if re.search(r"\S+\s+(?:-|to|through|or|and)\s+\S+", normalized):
        return False
    if re.search(r"\d[\w.+-]*\s+\d[\w.+-]*", normalized):
        return False
    return True


def _planned_software_for_skill(root: Path, skill_id: str) -> tuple[set[str], str | None]:
    path = root / "registry" / "software-registry.yaml"
    try:
        value = load_yaml_strict(path, "software-registry.yaml")
    except (OSError, yaml.YAMLError) as exc:
        return set(), f"software-registry: cannot derive promotion ownership: {exc}"
    if not isinstance(value, dict) or not isinstance(value.get("planned_software"), dict):
        return set(), "software-registry: planned_software must be a mapping"
    expected = {
        software_id
        for software_id, item in value["planned_software"].items()
        if isinstance(software_id, str)
        and isinstance(item, dict)
        and item.get("intended_skill") == skill_id
    }
    return expected, None


def _skill_local_validation_prefix(root: Path, skill_id: str) -> tuple[str | None, str | None]:
    try:
        registry = load_yaml_strict(root / "registry" / "skill-registry.yaml", "skill-registry.yaml")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return None, f"skill-registry: cannot resolve evidence scope: {exc}"
    skills = registry.get("skills")
    entry = skills.get(skill_id) if isinstance(skills, dict) else None
    if not isinstance(entry, dict):
        return None, f"skill-registry: unknown evidence owner {skill_id!r}"
    lifecycle = entry.get("lifecycle")
    if lifecycle in {"active", "development"}:
        return f"skills/{skill_id}/validation/", None
    if lifecycle == "planned":
        return f"candidates/{skill_id}/validation/", None
    return None, f"skill-registry: unsupported lifecycle for evidence owner {skill_id!r}"


def validation_errors(data: object, root: Path | None = None) -> list[str]:
    """Return deterministic registry failures without accepting unknown fields."""

    selected_root = (root or repo_root()).resolve()
    failures: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: registry must be a mapping"]
    if set(data) != {"schema_version", "interfaces"}:
        failures.append(
            f"<root>: expected fields ['interfaces', 'schema_version'], found {sorted(map(str, data))}"
        )
    if data.get("schema_version") != SCHEMA_VERSION:
        failures.append(f"schema_version: expected {SCHEMA_VERSION!r}")
    interfaces = data.get("interfaces")
    if not isinstance(interfaces, dict) or not interfaces:
        failures.append("interfaces: expected a nonempty mapping")
        return failures

    try:
        contract_catalog = load_catalog(selected_root / "contracts")
    except (OSError, ValueError, CatalogError) as exc:
        failures.append(f"contract-catalog: {exc}")
        contract_catalog = None

    for interface_id, specification in interfaces.items():
        location = f"interfaces/{interface_id}"
        if not isinstance(interface_id, str) or INTERFACE_ID.fullmatch(interface_id) is None:
            failures.append(f"{location}: invalid versioned interface identifier")
        if not isinstance(specification, dict):
            failures.append(f"{location}: expected a mapping")
            continue
        present_fields = set(specification)
        missing_fields = INTERFACE_REQUIRED_FIELDS - present_fields
        unexpected_fields = present_fields - INTERFACE_REQUIRED_FIELDS - INTERFACE_OPTIONAL_FIELDS
        if missing_fields or unexpected_fields:
            failures.append(
                f"{location}: required fields {sorted(INTERFACE_REQUIRED_FIELDS)}, "
                f"optional fields {sorted(INTERFACE_OPTIONAL_FIELDS)}, "
                f"found {sorted(map(str, specification))}"
            )
        display_name = specification.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            failures.append(f"{location}/display_name: expected a nonempty string")
        lifecycle = specification.get("lifecycle")
        if lifecycle not in LIFECYCLES:
            failures.append(f"{location}/lifecycle: expected active or planned")
        domain = specification.get("domain")
        if not isinstance(domain, str) or DOMAIN_ID.fullmatch(domain) is None:
            failures.append(f"{location}/domain: invalid domain identifier")
        if specification.get("producer_policy") not in PRODUCER_POLICIES:
            failures.append(f"{location}/producer_policy: unsupported producer policy")

        classification = specification.get("classification")
        if classification is not None:
            if not isinstance(classification, dict) or set(classification) != CLASSIFICATION_FIELDS:
                failures.append(
                    f"{location}/classification: expected fields {sorted(CLASSIFICATION_FIELDS)}"
                )
            else:
                if classification.get("document_kind") not in DOCUMENT_KINDS:
                    failures.append(
                        f"{location}/classification/document_kind: unsupported document kind"
                    )
                if classification.get("routing_scope") not in ROUTING_SCOPES:
                    failures.append(
                        f"{location}/classification/routing_scope: unsupported routing scope"
                    )

        schema_path = specification.get("schema_path")
        declared_hash = specification.get("schema_sha256")
        if lifecycle == "planned":
            if schema_path is not None or declared_hash is not None:
                failures.append(f"{location}: planned interfaces require null schema_path and schema_sha256")
            continue
        if lifecycle != "active":
            continue
        if not _safe_schema_path(schema_path):
            failures.append(f"{location}/schema_path: expected contracts/<name>.schema.json")
            continue
        if not isinstance(declared_hash, str) or SHA256.fullmatch(declared_hash) is None:
            failures.append(f"{location}/schema_sha256: expected 64 lowercase hexadecimal characters")
            continue
        path = selected_root / schema_path
        if not path.is_file():
            failures.append(f"{location}/schema_path: missing {schema_path}")
            continue
        if contract_catalog is None:
            continue
        contract = contract_catalog.by_filename.get(path.name)
        if contract is None:
            failures.append(f"{location}/schema_path: schema is absent from the validated contract catalog")
            continue
        if contract.raw_sha256 != declared_hash:
            failures.append(
                f"{location}/schema_sha256: declared {declared_hash} "
                f"!= actual catalog bytes {contract.raw_sha256}"
            )
        if (
            isinstance(classification, dict)
            and set(classification) == CLASSIFICATION_FIELDS
            and classification.get("document_kind") in DOCUMENT_KINDS
            and classification["document_kind"] != contract.document_kind
        ):
            failures.append(
                f"{location}/classification/document_kind: declared "
                f"{classification['document_kind']} != catalog {contract.document_kind}"
            )
        match = INTERFACE_ID.fullmatch(str(interface_id))
        if match is None:
            continue
        expected_name = match.group("name")
        expected_version = f"{match.group('major')}.{match.group('minor')}"
        if contract.name != expected_name or contract.version != expected_version:
            failures.append(
                f"{location}/schema_path: catalog identity {contract.name}@{contract.version} "
                f"!= {expected_name}@{expected_version}"
            )
    return failures


def _validated(path: Path | None = None, root: Path | None = None) -> dict[str, Any]:
    data = load_registry(path)
    failures = validation_errors(data, root)
    if failures:
        raise ValueError("invalid interface registry: " + "; ".join(failures))
    return data


def get_interface(
    interface_id: str,
    path: Path | None = None,
    root: Path | None = None,
    *,
    require_active: bool = True,
) -> dict[str, Any]:
    """Resolve one known interface; never infer an unregistered contract."""

    data = _validated(path, root)
    try:
        value = data["interfaces"][interface_id]
    except KeyError as exc:
        raise KeyError(f"unknown interface: {interface_id}") from exc
    if require_active and value["lifecycle"] != "active":
        raise PlannedInterfaceError(f"interface is not active: {interface_id}")
    return value


def active_interface_ids(path: Path | None = None, root: Path | None = None) -> tuple[str, ...]:
    data = _validated(path, root)
    return tuple(name for name, item in data["interfaces"].items() if item["lifecycle"] == "active")


def planned_interface_ids(path: Path | None = None, root: Path | None = None) -> tuple[str, ...]:
    data = _validated(path, root)
    return tuple(name for name, item in data["interfaces"].items() if item["lifecycle"] == "planned")


def load_governance_schema(kind: str, root: Path | None = None) -> dict[str, Any]:
    if kind not in GOVERNANCE_SCHEMAS:
        raise KeyError(f"unknown governance contract: {kind}")
    path = (root or repo_root()) / "contracts" / GOVERNANCE_SCHEMAS[kind]
    value = load_object(path, path.name, max_bytes=8 * 1024 * 1024)
    Draft202012Validator.check_schema(value)
    return value


def governance_validation_errors(kind: str, data: object, root: Path | None = None) -> list[str]:
    """Validate schema and intra-record semantics; a promotion validator must read referenced files."""

    selected_root = (root or repo_root()).resolve()
    try:
        schema = load_governance_schema(kind, selected_root)
    except OSError as exc:
        return [f"<schema>: governance schema is unavailable ({exc.__class__.__name__})"]
    except (KeyError, ValueError, StrictJSONError, SchemaError) as exc:
        return [f"<schema>: {exc}"]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        failures.append(f"{location}: {error.message}")
    if failures or not isinstance(data, dict):
        return failures

    if kind == "task-maturity":
        evidence_prefix, scope_error = _skill_local_validation_prefix(
            selected_root, data["skill_id"]
        )
        if scope_error:
            failures.append(scope_error)
            evidence_prefix = f"candidates/{data['skill_id']}/validation/"
        routes = data["routes"]
        route_ids = [route["route_id"] for route in routes]
        if len(route_ids) != len(set(route_ids)):
            failures.append("routes: route_id values must be unique")
        route_keys = []
        local_parents: dict[str, str] = {}
        route_id_set = set(route_ids)
        for index, route in enumerate(routes):
            parent = route["parent_route"]
            if parent is None:
                parent_key: object = None
            elif parent["scope"] == "catalog":
                parent_id = parent["route_id"]
                parent_key = ("catalog", parent_id)
                if parent_id not in route_id_set:
                    failures.append(
                        f"routes/{index}/parent_route/route_id: local parent does not exist in catalog"
                    )
                local_parents[route["route_id"]] = parent_id
            else:
                record_ref = parent["record_ref"]
                parent_key = (
                    "external-record",
                    record_ref["contract_name"],
                    record_ref["schema_version"],
                    record_ref["record_id"],
                    record_ref["sha256"],
                    record_ref["role"],
                )
            route_keys.append(
                (
                    route["provider_id"],
                    route["task_id"],
                    route["provider_version"],
                    parent_key,
                )
            )
        if len(route_keys) != len(set(route_keys)):
            failures.append("routes: provider/task/version/parent routes must be unique")
        reported_cycles: set[tuple[str, ...]] = set()
        for start in sorted(local_parents):
            order: list[str] = []
            positions: dict[str, int] = {}
            current = start
            while current in local_parents:
                if current in positions:
                    cycle = tuple(sorted(order[positions[current] :]))
                    if cycle not in reported_cycles:
                        failures.append(
                            "routes: local parent graph contains a cycle involving "
                            + ", ".join(cycle)
                        )
                        reported_cycles.add(cycle)
                    break
                positions[current] = len(order)
                order.append(current)
                current = local_parents[current]
        providers = {route["provider_id"] for route in routes}
        if not data["aggregate"] and len(providers) != 1:
            failures.append("routes: a non-aggregate catalog must use exactly one provider")
        claim_rank = {name: index for index, name in enumerate(CLAIM_LEVELS)}
        catalog_evidence_ids: set[str] = set()
        evidence_artifact_owners: dict[tuple[str, str], int] = {}
        for index, route in enumerate(routes):
            location = f"routes/{index}"
            provider_version = route["provider_version"]
            if isinstance(provider_version, str) and not _is_exact_provider_version(provider_version):
                failures.append(
                    f"{location}/provider_version: expected an exact version, not a placeholder or range"
                )

            axis_levels = {
                axis: route[field_name] for axis, field_name in MATURITY_AXES.items()
            }
            expected_overall = min(axis_levels.values(), key=MATURITY_RANK.__getitem__)
            for source in ("declared", "computed"):
                if route["overall_maturity"][source] != expected_overall:
                    failures.append(
                        f"{location}/overall_maturity/{source}: expected the three-axis minimum "
                        f"{expected_overall!r}"
                    )

            maximum_claim = MAX_CLAIM_BY_MATURITY[expected_overall]
            if claim_rank[route["claim_ceiling"]] > claim_rank[maximum_claim]:
                failures.append(
                    f"{location}/claim_ceiling: exceeds {maximum_claim!r} for overall maturity "
                    f"{expected_overall!r}"
                )

            evidence = route["evidence"]
            evidence_ids = [item["evidence_id"] for item in evidence]
            if len(evidence_ids) != len(set(evidence_ids)):
                failures.append(f"{location}/evidence: evidence_id values must be unique")
            for evidence_index, item in enumerate(evidence):
                evidence_id = item["evidence_id"]
                if evidence_id in catalog_evidence_ids:
                    failures.append(
                        f"{location}/evidence/{evidence_index}/evidence_id: cannot be reused "
                        "across task/provider/version routes"
                    )
                catalog_evidence_ids.add(evidence_id)
                if item["source"] == "skill-local":
                    if not item["path"].startswith(evidence_prefix):
                        failures.append(
                            f"{location}/evidence/{evidence_index}/path: local evidence must be "
                            f"below {evidence_prefix}"
                        )
                    artifact_locator = item["path"]
                else:
                    record_ref = item["external_record_ref"]
                    if item["sha256"] != record_ref["sha256"]:
                        failures.append(
                            f"{location}/evidence/{evidence_index}/external_record_ref: sha256 "
                            "must equal the evidence sha256"
                        )
                    artifact_locator = json.dumps(record_ref, sort_keys=True, separators=(",", ":"))
                artifact_key = (artifact_locator, item["sha256"])
                previous_owner = evidence_artifact_owners.get(artifact_key)
                if previous_owner is not None and previous_owner != index:
                    failures.append(
                        f"{location}/evidence/{evidence_index}: a hashed evidence artifact cannot "
                        "be borrowed from another task/provider/version route"
                    )
                evidence_artifact_owners[artifact_key] = index
            for axis, level in axis_levels.items():
                if level == "design-only":
                    continue
                if not any(
                    item["axis"] == axis
                    and item["maturity_level"] == level
                    and item["kind"] == PRIMARY_EVIDENCE_KIND_BY_AXIS[axis][level]
                    for item in evidence
                ):
                    failures.append(
                        f"{location}/evidence: missing hashed evidence of the primary kind matching "
                        f"axis {axis!r} at level {level!r}"
                    )
            for evidence_index, item in enumerate(evidence):
                evidence_version = item["provider_version"]
                if evidence_version is not None and evidence_version != route["provider_version"]:
                    failures.append(
                        f"{location}/evidence/{evidence_index}/provider_version: must equal the "
                        "route provider_version"
                    )
                if (
                    MATURITY_RANK[item["maturity_level"]]
                    >= MATURITY_RANK["format-fixture-validated"]
                    and evidence_version != route["provider_version"]
                ):
                    failures.append(
                        f"{location}/evidence/{evidence_index}: format, real, and tool evidence "
                        "must bind the exact route provider_version"
                    )
            if claim_rank[route["claim_ceiling"]] >= claim_rank["documented_behavior_only"]:
                if not any(item["kind"] == "official-source-evidence" for item in evidence):
                    failures.append(
                        f"{location}/evidence: documented or stronger claims require "
                        "official-source-evidence"
                    )
            if route["claim_ceiling"] == "eligible_for_expert_review":
                if not any(
                    item["axis"] == "scientific_validation"
                    and item["kind"] == "task-specific-scientific-validation"
                    for item in evidence
                ):
                    failures.append(
                        f"{location}/evidence: expert-review eligibility requires task-specific "
                        "scientific validation"
                    )
                if not any(
                    item["axis"] == "scientific_validation"
                    and item["kind"] == "expert-readiness-review"
                    for item in evidence
                ):
                    failures.append(
                        f"{location}/evidence: expert-review eligibility requires an "
                        "expert-readiness-review"
                    )

    elif kind == "activation-checklist":
        blocker_ids = set(data["summary"]["blocker_check_ids"])
        actual_blockers = {
            check["check_id"] for check in data["checks"] if check["status"] in {"fail", "not-assessed"}
        }
        if blocker_ids != actual_blockers:
            failures.append("summary/blocker_check_ids: must exactly match fail and not-assessed checks")
        evidence_prefix, scope_error = _skill_local_validation_prefix(
            selected_root, data["subject"]["skill_id"]
        )
        if scope_error:
            failures.append(scope_error)
            evidence_prefix = f"candidates/{data['subject']['skill_id']}/validation/"
        for check_index, check in enumerate(data["checks"]):
            for evidence_index, item in enumerate(check["evidence"]):
                if not item["path"].startswith(evidence_prefix):
                    failures.append(
                        f"checks/{check_index}/evidence/{evidence_index}/path: must be located "
                        f"below {evidence_prefix}"
                    )

    elif kind == "promotion-delta":
        skill_id = data["skill_id"]
        if data["base_commit"] == data["candidate_commit"]:
            failures.append("candidate_commit: must differ from base_commit")
        installer = data["installer_set"]
        before = set(installer["before"])
        after = set(installer["after"])
        if installer["added"] != [skill_id]:
            failures.append("installer_set/added: atomic promotion must add exactly skill_id")
        if installer["removed"]:
            failures.append("installer_set/removed: atomic promotion cannot remove installed skills")
        if after != before | {skill_id}:
            failures.append("installer_set/after: must equal before plus skill_id")
        expected_prefix = f"skills/{skill_id}/"
        saw_skill_source = False
        for index, value in enumerate(data["domain_owned_files_changed"]):
            if value.startswith(expected_prefix):
                saw_skill_source = True
            else:
                failures.append(
                    f"domain_owned_files_changed/{index}: expected a path below "
                    f"skills/{skill_id}/"
                )
        if not saw_skill_source:
            failures.append(
                "domain_owned_files_changed: promotion must include development Skill evidence"
            )
        for index, value in enumerate(data["shared_files_changed"]):
            if value.startswith("skills/"):
                failures.append(
                    f"shared_files_changed/{index}: Skill-owned paths belong in a domain-owned delta"
                )
        if data["path_transition"]["from"] != f"skills/{skill_id}":
            failures.append("path_transition/from: must equal skills/<skill_id>")
        if data["path_transition"]["to"] != f"skills/{skill_id}":
            failures.append("path_transition/to: must equal skills/<skill_id>")
        task_catalog_path = data["task_maturity_catalog"]["path"]
        post_promotion_validation_prefix = f"skills/{skill_id}/validation/"
        if not task_catalog_path.startswith(post_promotion_validation_prefix):
            failures.append(
                "task_maturity_catalog/path: must be located below the promoted Skill validation tree"
            )
        validation_prefix = post_promotion_validation_prefix
        if not data["activation_checklist"]["path"].startswith(validation_prefix):
            failures.append(
                f"activation_checklist/path: must be located below {validation_prefix}"
            )
        for index, item in enumerate(data["observable_route_decisions"]):
            if not item["evidence"]["path"].startswith(validation_prefix):
                failures.append(
                    f"observable_route_decisions/{index}/evidence/path: must be located below "
                    f"{validation_prefix}"
                )
        report_refs = [data["reports"]["privacy_license"], *data["reports"]["forward_tests"]]
        for index, item in enumerate(report_refs):
            if not item["path"].startswith(validation_prefix):
                failures.append(
                    f"reports/{index}/path: must be located below {validation_prefix}"
                )

        intended_software, software_registry_error = _planned_software_for_skill(
            selected_root, skill_id
        )
        if software_registry_error:
            failures.append(software_registry_error)
        moved_software = {item["software_id"] for item in data["software_entries_moved"]}
        if intended_software:
            if not data["software_backed"]:
                failures.append(
                    "software_backed: actual software-registry ownership requires true"
                )
            if not moved_software.intersection(intended_software):
                failures.append(
                    "software_entries_moved: must promote at least one software-registry entry "
                    "owned by the Skill"
                )
        unexpected_software = moved_software - intended_software
        if unexpected_software:
            failures.append(
                "software_entries_moved: entries are not owned by the promoted Skill: "
                + ", ".join(sorted(unexpected_software))
            )

        shared = set(data["shared_files_changed"])
        if data["decision"] == "eligible":
            missing_shared = REQUIRED_PROMOTION_SHARED - shared
            if missing_shared:
                failures.append(
                    "shared_files_changed: eligible promotion is missing "
                    + ", ".join(sorted(missing_shared))
                )
            if data["software_backed"]:
                missing_software = SOFTWARE_PROMOTION_SHARED - shared
                if missing_software:
                    failures.append(
                        "shared_files_changed: software-backed promotion is missing "
                        + ", ".join(sorted(missing_software))
                    )
        if data["software_entries_moved"] and not data["software_backed"]:
            failures.append(
                "software_backed: must be true when software registry entries are promoted"
            )

        contract_entries = data["contracts_changed"]
        contract_paths = [item["path"] for item in contract_entries]
        if len(contract_paths) != len(set(contract_paths)):
            failures.append("contracts_changed: contract paths must be unique")
        contract_hashes = {item["path"]: item["sha256"] for item in contract_entries}
        interface_ids = [item["interface_id"] for item in data["interface_changes"]]
        if len(interface_ids) != len(set(interface_ids)):
            failures.append("interface_changes: interface_id values must be unique")
        for index, item in enumerate(data["interface_changes"]):
            if item["action"] == "register-planned":
                continue
            schema_ref = item["schema_ref"]
            if contract_hashes.get(schema_ref["path"]) != schema_ref["sha256"]:
                failures.append(
                    f"interface_changes/{index}/schema_ref: must match a contracts_changed path/hash"
                )

        software_ids = [item["software_id"] for item in data["software_entries_moved"]]
        if len(software_ids) != len(set(software_ids)):
            failures.append("software_entries_moved: software_id values must be unique")
        report_ids = [item["report_id"] for item in report_refs]
        report_paths = [item["path"] for item in report_refs]
        if len(report_ids) != len(set(report_ids)):
            failures.append("reports: report_id values must be unique")
        if len(report_paths) != len(set(report_paths)):
            failures.append("reports: report paths must be unique")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--interface")
    parser.add_argument(
        "--require-active",
        action="store_true",
        help="compatibility alias; active resolution is already the default",
    )
    parser.add_argument(
        "--allow-planned-metadata",
        action="store_true",
        help="inspect a planned registry entry without making it routable",
    )
    parser.add_argument("--validate-governance", choices=sorted(GOVERNANCE_SCHEMAS))
    parser.add_argument("--json-file", type=Path)
    args = parser.parse_args()
    if args.require_active and args.allow_planned_metadata:
        parser.error("--require-active conflicts with --allow-planned-metadata")
    selected_root = (args.root or repo_root()).resolve()
    try:
        if args.validate_governance:
            if args.json_file is None:
                parser.error("--validate-governance requires --json-file")
            value = load_object(
                args.json_file,
                "governance JSON input",
                max_bytes=8 * 1024 * 1024,
            )
            failures = governance_validation_errors(args.validate_governance, value, selected_root)
            active = planned = None
        else:
            data = load_registry(args.registry)
            failures = validation_errors(data, selected_root)
            if not failures and args.interface:
                get_interface(
                    args.interface,
                    args.registry,
                    selected_root,
                    require_active=not args.allow_planned_metadata,
                )
            interfaces = data.get("interfaces", {}) if isinstance(data, dict) else {}
            active = sum(item.get("lifecycle") == "active" for item in interfaces.values() if isinstance(item, dict))
            planned = sum(item.get("lifecycle") == "planned" for item in interfaces.values() if isinstance(item, dict))
    except PlannedInterfaceError:
        print(f"status=planned-not-active interface={args.interface}", file=sys.stderr)
        return 3
    except StrictJSONError as exc:
        failures = [f"<json>: {exc}"]
        active = planned = None
    except ValueError as exc:
        failures = [f"<registry>: {exc}"]
        active = planned = None
    except OSError as exc:
        failures = [f"<input>: input is unavailable ({exc.__class__.__name__})"]
        active = planned = None
    except (KeyError, yaml.YAMLError) as exc:
        failures = [f"<registry>: {exc}"]
        active = planned = None
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 2
    if args.validate_governance:
        print(f"PASS: governance JSON matches {args.validate_governance}@1.0")
    elif args.interface:
        status = "planned-metadata-only" if args.allow_planned_metadata else "active"
        print(f"status={status} interface={args.interface}")
    else:
        print(f"VALID: active interfaces={active}; planned metadata entries={planned}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
