from __future__ import annotations

import hashlib
import json
from typing import Any


SCOPES = (
    "artifact_generation",
    "geometry_screening",
    "symmetry_property_screening",
    "connectivity_screening",
    "calculation_handoff",
)
CURRENT_CIF_SEMANTIC_MAJOR = 3


def producer_uses_current_semantics(version: str) -> bool:
    try:
        return int(version.split(".", 1)[0]) >= CURRENT_CIF_SEMANTIC_MAJOR
    except (AttributeError, TypeError, ValueError):
        return False


def analysis_key_from_fields(
    *,
    source_sha256: str,
    data_block: dict[str, Any],
    command_options: dict[str, Any],
    dependency_versions: dict[str, str],
    producer_version: str,
) -> str:
    payload = {
        "contract": "cif-analysis-key-v1",
        "schema_version": "1.0",
        "producer": "cif-structure-analysis",
        "producer_version": producer_version,
        "source_sha256": source_sha256,
        "data_block": data_block,
        "command_options": command_options,
        "dependency_versions": dependency_versions,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def assess_screening_eligibility(
    diagnostics: list[dict[str, str]],
    quality: dict[str, Any],
    symmetry: dict[str, Any],
    connectivity: dict[str, Any],
    neighbor_summary: dict[str, Any],
    short_flags: list[dict[str, Any]],
    partial_occupancy_rows: list[int],
    disorder_rows: list[int],
) -> dict[str, Any]:
    """Frozen consumer for cif-screening-eligibility-v1."""

    reasons: list[dict[str, Any]] = []

    def add(
        reason_id: str,
        severity: str,
        scopes: tuple[str, ...],
        message: str,
    ) -> None:
        reasons.append(
            {
                "id": reason_id,
                "severity": severity,
                "scopes": list(scopes),
                "message": message,
            }
        )

    if any(item.get("status") == "fail" for item in diagnostics):
        add(
            "artifact-consistency-failed",
            "blocker",
            SCOPES,
            "one or more fail-closed parser, adapter, or structure consistency checks failed",
        )
    if quality.get("status") == "FAIL":
        add(
            "structure-quality-failed",
            "blocker",
            ("geometry_screening", "calculation_handoff"),
            "the materialized structure failed a numerical or consistency quality gate",
        )
    elif quality.get("status") == "WARN":
        add(
            "structure-quality-review-required",
            "warning",
            ("geometry_screening", "calculation_handoff"),
            "one or more structure-quality checks require review",
        )
    if partial_occupancy_rows:
        add(
            "partial-occupancy-model-unresolved",
            "blocker",
            ("symmetry_property_screening", "calculation_handoff"),
            "partial occupancy is not resolved into a physical ordered or ensemble model",
        )
        add(
            "representative-geometry-only",
            "warning",
            ("geometry_screening",),
            "geometry describes only the representative materialized model",
        )
    if disorder_rows:
        add(
            "disorder-model-unresolved",
            "blocker",
            ("symmetry_property_screening", "calculation_handoff"),
            "disorder metadata is not resolved into a physical ordered or ensemble model",
        )
        if not partial_occupancy_rows:
            add(
                "representative-geometry-only",
                "warning",
                ("geometry_screening",),
                "geometry describes only the representative materialized model",
            )
    if short_flags:
        add(
            "short-contact-review-required",
            "blocker",
            ("calculation_handoff",),
            "configured short-distance flags must be resolved before calculation handoff",
        )
        add(
            "short-contact-geometry-warning",
            "warning",
            ("geometry_screening",),
            "geometry contains one or more configured short-distance flags",
        )
    if not neighbor_summary.get("neighbor_search_complete"):
        add(
            "neighbor-search-incomplete",
            "blocker",
            ("geometry_screening", "calculation_handoff"),
            "periodic neighbor search did not find a candidate for every site",
        )
    if symmetry.get("status") != "DETECTED":
        add(
            "symmetry-evidence-unavailable",
            "blocker",
            ("symmetry_property_screening",),
            "a detected crystallographic point group is unavailable",
        )
    elif symmetry.get("tolerance_sensitive"):
        add(
            "symmetry-tolerance-sensitive",
            "blocker",
            ("symmetry_property_screening",),
            "the detected symmetry changes across the configured tolerance sweep",
        )
        add(
            "symmetry-review-required",
            "warning",
            ("calculation_handoff",),
            "symmetry-sensitive idealization requires a source-structure control",
        )
    dimensionality = connectivity.get("dimensionality_candidate")
    if dimensionality in {"SENSITIVE", "MIXED"}:
        add(
            "connectivity-classification-sensitive",
            "warning",
            ("connectivity_screening", "calculation_handoff"),
            f"periodic connectivity is reported as {dimensionality}",
        )

    scope_payload: dict[str, dict[str, Any]] = {}
    for scope in SCOPES:
        scoped = [item for item in reasons if scope in item["scopes"]]
        blockers = [item for item in scoped if item["severity"] == "blocker"]
        warnings = [item for item in scoped if item["severity"] == "warning"]
        if scope == "symmetry_property_screening" and blockers:
            status = "NOT_ASSESSED"
        elif blockers:
            status = "BLOCK"
        elif warnings:
            status = "WARN"
        else:
            status = "PASS"
        scope_payload[scope] = {
            "status": status,
            "reason_ids": [item["id"] for item in scoped],
        }

    return {
        "method_version": "cif-screening-eligibility-v1",
        "scopes": scope_payload,
        "reasons": reasons,
        "claim_boundary": (
            "Eligibility separates artifact generation, geometric screening, "
            "symmetry-only hypotheses, connectivity review, and calculation "
            "handoff. It does not rank energies or establish stability."
        ),
    }
