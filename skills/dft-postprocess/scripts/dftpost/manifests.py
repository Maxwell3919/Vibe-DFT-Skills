from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from . import __version__
from .structure_semantics import (
    analysis_key_from_fields,
    assess_screening_eligibility,
    producer_uses_current_semantics,
)
from .utils import find_repo_root, relative_file, sha256_file, utc_now


REPO_ROOT = find_repo_root(Path(__file__))
TOOLS_ROOT = str(REPO_ROOT / "tools")
if TOOLS_ROOT not in sys.path:
    sys.path.insert(0, TOOLS_ROOT)

from validate_contract import validate_file as catalog_validate_file  # noqa: E402
from validate_contract import validation_errors as catalog_validation_errors  # noqa: E402


SCHEMAS = {
    "run": "run-manifest.schema.json",
    "artifact": "artifact-manifest.schema.json",
    "campaign": "campaign-record.schema.json",
    "recommendation": "recommendation-record.schema.json",
    "dataset": "normalized-dataset.schema.json",
    "plan": "postprocess-plan.schema.json",
    "execution": "tool-execution.schema.json",
    "structure": "structure-manifest.schema.json",
}


def schema_path(kind: str) -> Path:
    return REPO_ROOT / "contracts" / SCHEMAS[kind]


def _screening_cascade_errors(
    structure: dict[str, Any],
    eligibility: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    scopes = eligibility["scopes"]
    property_screening = structure.get("property_screening")
    if property_screening is not None:
        hypotheses = property_screening["hypotheses"]
        if scopes["artifact_generation"]["status"] == "BLOCK":
            if any(
                item["id"] != "property-screening-eligibility"
                or item["status"] != "NOT_ASSESSED"
                for item in hypotheses
            ):
                errors.append(
                    "structure/property_screening: BLOCK artifact eligibility "
                    "must suppress every positive property hypothesis"
                )
        if scopes["symmetry_property_screening"]["status"] != "PASS":
            hypothesis_by_id = {item["id"]: item for item in hypotheses}
            eligibility_hypothesis = hypothesis_by_id.get(
                "property-screening-eligibility"
            )
            if (
                eligibility_hypothesis is None
                or eligibility_hypothesis["status"] != "NOT_ASSESSED"
            ):
                errors.append(
                    "structure/property_screening: unavailable symmetry "
                    "eligibility requires a NOT_ASSESSED gate"
                )
            forbidden_ids = {
                "piezoelectric-symmetry-screen",
                "polar-point-group-screen",
                "bulk-electric-dipole-shg-screen",
            }
            if forbidden_ids.intersection(hypothesis_by_id):
                errors.append(
                    "structure/property_screening: symmetry hypotheses are "
                    "present while their eligibility is not PASS"
                )
            symmetry_payload = property_screening["symmetry"]
            if any(
                symmetry_payload[field] is not None
                for field in (
                    "centrosymmetric",
                    "piezoelectric_symmetry_allowed",
                    "polar_point_group",
                    "bulk_electric_dipole_shg_symmetry_allowed",
                )
            ):
                errors.append(
                    "structure/property_screening/symmetry: derived values "
                    "must be null while symmetry eligibility is not PASS"
                )

    optimization = structure.get("optimization_guidance")
    if (
        optimization is not None
        and scopes["calculation_handoff"]["status"] == "BLOCK"
    ):
        if any(
            item["recommended_for_screening"]
            for item in optimization["starting_points"]
        ):
            errors.append(
                "structure/optimization_guidance: BLOCK calculation handoff "
                "must suppress every screening recommendation"
            )
        if not optimization["blockers"]:
            errors.append(
                "structure/optimization_guidance: BLOCK calculation handoff "
                "requires at least one recorded blocker"
            )
    return errors


def _structure_semantic_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validation = data["validation"]
    checks = validation["checks"]
    if any(item["status"] == "fail" for item in checks):
        expected_validation_status = "block"
    elif any(item["status"] == "warn" for item in checks):
        expected_validation_status = "warn"
    else:
        expected_validation_status = "pass"
    expected_status = {
        "pass": "PASS",
        "warn": "WARN",
        "block": "BLOCK",
    }[expected_validation_status]
    if validation["status"] != expected_validation_status:
        errors.append(
            "validation/status: does not match the recorded check statuses"
        )
    if data["status"] != expected_status:
        errors.append(
            "status: does not match the status derived from validation checks"
        )

    provenance = data["provenance"]
    current_semantics = producer_uses_current_semantics(
        provenance["producer_version"]
    )
    actual_key = data.get("analysis_key")
    if current_semantics and actual_key is None:
        errors.append(
            "analysis_key: required for the current CIF producer semantics"
        )
    if actual_key is not None:
        expected_key = analysis_key_from_fields(
            source_sha256=data["source"]["sha256"],
            data_block=data["document"]["selected_block"],
            command_options=provenance["command_options"],
            dependency_versions=provenance["dependency_versions"],
            producer_version=provenance["producer_version"],
        )
        if actual_key != expected_key:
            errors.append(
                "analysis_key: does not match the recomputed semantic key"
            )

    structure = data["structure"]
    actual_eligibility = structure.get("screening_eligibility")
    current_fields = (
        "quality_analysis",
        "screening_eligibility",
        "connectivity_analysis",
        "property_screening",
        "optimization_guidance",
    )
    if current_semantics:
        for field in current_fields:
            if field not in structure:
                errors.append(
                    f"structure/{field}: required for the current CIF producer semantics"
                )
    if actual_eligibility is not None:
        missing = [
            field
            for field in ("quality_analysis", "connectivity_analysis")
            if field not in structure
        ]
        if missing:
            errors.append(
                "structure/screening_eligibility: cannot be recomputed without "
                + ", ".join(missing)
            )
        else:
            metadata = data["document"]["metadata"]
            expected_eligibility = assess_screening_eligibility(
                checks,
                structure["quality_analysis"],
                structure["symmetry_attempt"],
                structure["connectivity_analysis"],
                structure["nearest_distances"],
                data["flags"]["short_distances"],
                metadata["partial_occupancy_rows"],
                metadata["disorder_rows"],
            )
            if actual_eligibility != expected_eligibility:
                errors.append(
                    "structure/screening_eligibility: does not match recomputed "
                    "scope statuses and reasons"
                )
            errors.extend(
                _screening_cascade_errors(structure, actual_eligibility)
            )
    return errors


def validation_errors(kind: str, data: object) -> list[str]:
    errors = catalog_validation_errors(kind, data, REPO_ROOT / "contracts")
    if errors or kind != "structure" or not isinstance(data, dict):
        return errors
    return [*errors, *_structure_semantic_errors(data)]


def validate_manifest(kind: str, path: Path) -> list[str]:
    errors = catalog_validate_file(kind, path, REPO_ROOT / "contracts")
    if errors or kind != "structure":
        return errors
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"<file>: structure semantic validation failed: {exc}"]
    if not isinstance(data, dict):
        return ["<root>: structure manifest must be an object"]
    return _structure_semantic_errors(data)


def _file_record(root: Path, specification: str) -> dict[str, Any]:
    if "=" not in specification:
        raise ValueError("file specifications must use role=relative/path")
    role, value = specification.split("=", 1)
    if not role or not value:
        raise ValueError("file specifications require nonempty role and path")
    path, relative = relative_file(root, Path(value))
    return {"role": role, "path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def build_artifact_manifest(
    artifact_id: str,
    source_run_ids: list[str],
    code: str,
    artifact_type: str,
    status: str,
    root: Path,
    data_specs: list[str],
    figure_specs: list[str],
    validation_status: str,
    checks: list[str],
    claim_boundary: list[str],
    command: list[str],
) -> dict[str, Any]:
    manifest = {
        "schema_version": "1.0",
        "artifact_id": artifact_id,
        "source_run_ids": source_run_ids,
        "code": code,
        "artifact_type": artifact_type,
        "status": status,
        "data_files": [_file_record(root, item) for item in data_specs],
        "figure_files": [_file_record(root, item) for item in figure_specs],
        "validation": {"status": validation_status, "checks": checks},
        "claim_boundary": claim_boundary,
        "provenance": {"tool": "dftpost", "tool_version": __version__, "generated_utc": utc_now(), "command": command},
    }
    errors = validation_errors("artifact", manifest)
    if errors:
        raise ValueError("artifact manifest is invalid: " + "; ".join(errors))
    return manifest
