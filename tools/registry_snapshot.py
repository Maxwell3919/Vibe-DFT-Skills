#!/usr/bin/env python3
"""Load the nine canonical registries once and validate one shared snapshot."""

from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
from pathlib import Path
from typing import Any

from environment_profiles import validation_errors as environment_validation_errors
from interface_registry import validation_errors as interface_validation_errors
from official_source_authorities import (
    validate_and_project_technical as validate_and_project_authorities,
)
from validate_official_document_coverage import (
    consumer_registry_validation_errors,
)
from validate_official_document_bundles import (
    expectation_registry_validation_errors,
)
from validate_official_document_storage import (
    configuration_validation_errors as storage_discovery_validation_errors,
)
from operation_routes import validation_findings as operation_validation_findings
from registry_yaml import RegistryYAMLError, load_yaml_strict_with_raw
from skill_registry import validation_errors as skill_validation_errors
from software_registry import validation_errors as software_validation_errors


class RegistrySnapshotError(ValueError):
    """Stable failure raised before any consumer can use a partial snapshot."""


@dataclass(frozen=True)
class RegistrySnapshot:
    root: Path
    skills: dict[str, Any]
    software: dict[str, Any]
    interfaces: dict[str, Any]
    environments: dict[str, Any]
    operation_routes: dict[str, Any]
    official_source_authorities: dict[str, Any]
    official_source_authority_projection: dict[str, dict[str, Any]]
    official_document_consumers: dict[str, Any]
    official_document_bundle_expectations: dict[str, Any]
    official_document_storage_discovery: dict[str, Any]
    registry_sha256: dict[str, str]
    registry_raw: dict[str, bytes]

    def calculation_codes(self) -> tuple[str, ...]:
        return tuple(
            code
            for code, specification in self.software["software"].items()
            if specification["lifecycle"] == "active"
        )

    def aggregate_codes(self) -> tuple[str, ...]:
        return tuple(self.software["aggregate_codes"])

    def active_official_source_authorities(self) -> dict[str, dict[str, Any]]:
        return copy.deepcopy(self.official_source_authority_projection)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_registry_snapshot(
    root: Path | None = None,
    *,
    validate_sources: bool = False,
) -> RegistrySnapshot:
    """Return one strict cross-validated snapshot or fail without partial data."""

    selected_root = (root or repo_root()).resolve()
    filenames = {
        "skills": "skill-registry.yaml",
        "software": "software-registry.yaml",
        "interfaces": "interface-registry.yaml",
        "environments": "environment-profiles.yaml",
        "operation_routes": "operation-routes.yaml",
        "official_source_authorities": "official-source-authorities.yaml",
        "official_document_consumers": "official-document-consumers.yaml",
        "official_document_bundle_expectations": (
            "official-document-bundle-expectations.yaml"
        ),
        "official_document_storage_discovery": (
            "official-document-storage-discovery.yaml"
        ),
    }
    loaded: dict[str, dict[str, Any]] = {}
    digests: dict[str, str] = {}
    raw_documents: dict[str, bytes] = {}
    for key, filename in filenames.items():
        try:
            loaded[key], raw = load_yaml_strict_with_raw(
                selected_root / "registry" / filename,
                filename,
            )
            digests[filename] = hashlib.sha256(raw).hexdigest()
            raw_documents[filename] = raw
        except RegistryYAMLError as exc:
            raise RegistrySnapshotError(f"{key}: {exc}") from None

    source_root = selected_root if validate_sources else None
    failures: list[str] = []
    failures.extend(
        f"environments: {failure}"
        for failure in environment_validation_errors(loaded["environments"])
    )
    failures.extend(
        f"software: {failure}"
        for failure in software_validation_errors(
            loaded["software"],
            source_root,
            loaded["environments"],
        )
    )
    failures.extend(
        f"interfaces: {failure}"
        for failure in interface_validation_errors(loaded["interfaces"], selected_root)
    )
    failures.extend(
        f"skills: {failure}"
        for failure in skill_validation_errors(
            loaded["skills"],
            source_root,
            loaded["software"],
            loaded["interfaces"],
            loaded["environments"],
        )
    )
    authority_failures, authority_projection = validate_and_project_authorities(
        loaded["official_source_authorities"],
        software_data=loaded["software"],
        source_root=selected_root,
    )
    failures.extend(
        f"official-source-authorities: {failure}"
        for failure in authority_failures
    )
    failures.extend(
        f"official-document-consumers: {failure}"
        for failure in consumer_registry_validation_errors(
            loaded["official_document_consumers"],
            skills=loaded["skills"]["skills"],
            authorities=loaded["official_source_authorities"]["authorities"],
            root=selected_root,
        )
    )
    failures.extend(
        f"official-document-bundle-expectations: {failure}"
        for failure in expectation_registry_validation_errors(
            loaded["official_document_bundle_expectations"],
            loaded["skills"],
        )
    )
    failures.extend(
        f"official-document-storage-discovery: {failure}"
        for failure in storage_discovery_validation_errors(
            loaded["official_document_storage_discovery"]
        )
    )
    if not failures:
        for finding in operation_validation_findings(
            loaded["operation_routes"],
            source_root=selected_root,
            skill_data=loaded["skills"],
            interface_data=loaded["interfaces"],
            software_data=loaded["software"],
            environment_data=loaded["environments"],
            dependency_source_validation=False,
        ):
            failures.append(
                "operation-routes: "
                f"{finding.get('code', 'ROUTE_INVALID')} "
                f"{finding.get('location', '<root>')}: {finding.get('message', '')}"
            )
    if failures:
        raise RegistrySnapshotError("invalid registry snapshot: " + "; ".join(failures))
    return RegistrySnapshot(
        root=selected_root,
        skills=loaded["skills"],
        software=loaded["software"],
        interfaces=loaded["interfaces"],
        environments=loaded["environments"],
        operation_routes=loaded["operation_routes"],
        official_source_authorities=loaded["official_source_authorities"],
        official_source_authority_projection=authority_projection,
        official_document_consumers=loaded["official_document_consumers"],
        official_document_bundle_expectations=(
            loaded["official_document_bundle_expectations"]
        ),
        official_document_storage_discovery=(
            loaded["official_document_storage_discovery"]
        ),
        registry_sha256=digests,
        registry_raw=raw_documents,
    )
