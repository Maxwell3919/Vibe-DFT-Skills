#!/usr/bin/env python3
"""Build a deterministic, conservative official-document completeness dashboard.

The dashboard consumes the public repository bundle-audit result and the
documented registration record.  It reports corpus, slice, scope, license,
storage, and freshness independently.  Bundle semantic state remains an
additional cap: a partial bundle can never be presented as complete merely
because a dimension projection is incomplete or optimistic.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any, Iterable, Mapping

from registry_yaml import load_yaml_strict
import strict_json
import validate_official_document_bundles as bundle_audit
import validate_official_document_storage as storage_audit


SCHEMA_VERSION = "1.0"
DIMENSION_ORDER = (
    "corpus",
    "slice",
    "scope",
    "license",
    "storage",
    "freshness",
)
ASSURANCE_LAYER_ORDER = (
    "registration",
    "inventory",
    "content_materialized",
    "semantic_slice",
)
STATUS_ORDER = (
    "complete",
    "unknown",
    "partial",
    "missing",
    "blocked",
    "invalid",
)
STATUS_PRECEDENCE = {
    "complete": 0,
    "unknown": 1,
    "partial": 2,
    "missing": 3,
    "blocked": 4,
    "invalid": 5,
}
RECORD_FIELDS = {
    "corpora",
    "slice_manifests",
    "license_reviews",
    "scope_inventory",
    "coverage",
}
SEMANTIC_SELECTOR_KINDS = frozenset(
    {
        "heading",
        "byte-range",
        "json-pointer",
        "line-range",
        "page-range",
        "source-symbol",
    }
)
SELECTOR_KINDS = frozenset(
    {*SEMANTIC_SELECTOR_KINDS, "whole-source", "other"}
)
STORAGE_MODES = frozenset(
    {
        "embedded-open",
        "external-cache",
        "external-runtime-only",
        "metadata-only",
    }
)
ARTIFACT_KINDS = frozenset(
    {
        "raw-source",
        "derived-text",
        "image",
        "pdf",
        "metadata",
        "code-example",
        "other",
    }
)
FRESHNESS_OVERLAY_FIELDS = frozenset(
    {
        "authority_statuses",
        "observed_utc",
        "trust_id",
        "trust_mode",
        "valid_until_utc",
    }
)
AUTHORITY_FRESHNESS_STATUSES = frozenset(
    {"complete", "unknown", "blocked"}
)
FRESHNESS_TRUST_MODES = frozenset({"unverified", "platform-attested"})
UTC_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)


class DashboardError(ValueError):
    """One fail-closed dashboard input or projection error."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def aggregate_statuses(statuses: Iterable[str]) -> str:
    """Return the most conservative nonempty aggregate status."""

    values = tuple(statuses)
    if not values:
        raise DashboardError("cannot aggregate an empty status set")
    unsupported = sorted(set(values) - set(STATUS_PRECEDENCE))
    if unsupported:
        raise DashboardError(f"unsupported dashboard status: {unsupported[0]}")
    return max(values, key=STATUS_PRECEDENCE.__getitem__)


def _parse_utc_timestamp(value: object, location: str) -> datetime:
    if not isinstance(value, str) or UTC_TIMESTAMP.fullmatch(value) is None:
        raise DashboardError(
            f"{location}: expected a whole-second UTC timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DashboardError(f"{location}: timestamp is invalid") from exc
    if parsed.tzinfo != timezone.utc:
        raise DashboardError(f"{location}: timestamp must be UTC")
    return parsed


def _apply_freshness_overlay(
    base_status: str,
    overlay: Mapping[str, object],
    required_authority_ids: Iterable[str],
    *,
    as_of_utc: str,
) -> str:
    """Apply one evidence-qualified freshness projection.

    ``unknown`` is replaceable only by a complete, current, platform-attested
    observation of the exact authority set used by the row.  An incomplete,
    expired, or unverified observation proves no positive freshness state.
    A reported blocker remains a conservative cap even when the observation
    does not cover every authority.
    """

    if base_status not in STATUS_PRECEDENCE:
        raise DashboardError("freshness base status is unsupported")
    if not isinstance(overlay, Mapping) or set(overlay) != FRESHNESS_OVERLAY_FIELDS:
        raise DashboardError("freshness overlay fields are not exact")
    expected = frozenset(required_authority_ids)
    if not expected or any(
        not isinstance(authority_id, str) or not authority_id
        for authority_id in expected
    ):
        raise DashboardError("freshness row authority set is invalid")
    statuses = overlay.get("authority_statuses")
    if not isinstance(statuses, dict) or not statuses:
        raise DashboardError(
            "freshness overlay authority_statuses must be a nonempty mapping"
        )
    if any(
        not isinstance(authority_id, str)
        or not authority_id
        or not authority_id.isprintable()
        for authority_id in statuses
    ):
        raise DashboardError("freshness overlay contains an invalid authority ID")
    if set(statuses) - expected:
        raise DashboardError("freshness overlay names an unrelated authority")
    if any(
        not isinstance(status, str)
        or status not in AUTHORITY_FRESHNESS_STATUSES
        for status in statuses.values()
    ):
        raise DashboardError(
            "freshness overlay contains an unsupported authority status"
        )
    observed = _parse_utc_timestamp(
        overlay.get("observed_utc"),
        "freshness overlay observed_utc",
    )
    valid_until = _parse_utc_timestamp(
        overlay.get("valid_until_utc"),
        "freshness overlay valid_until_utc",
    )
    as_of = _parse_utc_timestamp(as_of_utc, "freshness overlay as_of_utc")
    if valid_until < observed:
        raise DashboardError(
            "freshness overlay validity interval is reversed"
        )
    trust_mode = overlay.get("trust_mode")
    trust_id = overlay.get("trust_id")
    if trust_mode not in FRESHNESS_TRUST_MODES:
        raise DashboardError("freshness overlay trust_mode is unsupported")
    if trust_mode == "platform-attested":
        if (
            not isinstance(trust_id, str)
            or not trust_id
            or not trust_id.isprintable()
        ):
            raise DashboardError(
                "platform-attested freshness overlay requires trust_id"
            )
    elif trust_id is not None:
        raise DashboardError(
            "unverified freshness overlay cannot claim trust_id"
        )

    if "blocked" in statuses.values():
        return aggregate_statuses((base_status, "blocked"))
    qualified_complete = (
        set(statuses) == expected
        and set(statuses.values()) == {"complete"}
        and observed <= as_of <= valid_until
        and trust_mode == "platform-attested"
    )
    if base_status == "unknown" and qualified_complete:
        return "complete"
    return base_status


def make_skill_row(
    *,
    skill_id: str,
    entrypoint: str,
    bundle_semantic_state: str,
    dimensions: Mapping[str, str],
    assurance_layers: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    if set(dimensions) != set(DIMENSION_ORDER):
        raise DashboardError(f"{skill_id}: dashboard dimensions are not exact")
    if bundle_semantic_state not in {"complete", "partial", "missing", "invalid"}:
        raise DashboardError(f"{skill_id}: unsupported bundle semantic state")
    if set(assurance_layers) != set(ASSURANCE_LAYER_ORDER):
        raise DashboardError(f"{skill_id}: assurance layers are not exact")
    ordered_dimensions = {
        name: dimensions[name] for name in DIMENSION_ORDER
    }
    ordered_layers: dict[str, dict[str, object]] = {}
    for name in ASSURANCE_LAYER_ORDER:
        layer = assurance_layers[name]
        status = layer.get("status")
        if status not in {"complete", "partial", "blocked", "missing", "invalid"}:
            raise DashboardError(
                f"{skill_id}: unsupported {name} assurance status"
            )
        ordered_layers[name] = dict(layer)
    assurance_status = aggregate_statuses(
        layer["status"] for layer in ordered_layers.values()
    )
    overall = aggregate_statuses(
        (
            bundle_semantic_state,
            *ordered_dimensions.values(),
            assurance_status,
        )
    )
    return {
        "assurance_layers": ordered_layers,
        "assurance_status": assurance_status,
        "bundle_entrypoint": entrypoint,
        "bundle_semantic_state": bundle_semantic_state,
        "dimensions": ordered_dimensions,
        "overall_status": overall,
        "skill_id": skill_id,
    }


def _safe_relative_path(value: object, location: str) -> PurePosixPath:
    if (
        not isinstance(value, str)
        or not value
        or not value.isprintable()
        or "\\" in value
    ):
        raise DashboardError(f"{location}: expected a canonical relative POSIX path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise DashboardError(f"{location}: expected a canonical relative POSIX path")
    return path


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        return strict_json.load_object(
            path,
            label,
            max_bytes=64 * 1024 * 1024,
            max_nodes=1_000_000,
            max_depth=128,
            max_string_chars=8 * 1024 * 1024,
        )
    except (OSError, strict_json.StrictJSONError) as exc:
        raise DashboardError(f"{label}: malformed or unsafe JSON ({exc})") from exc


def _registered_paths(
    value: object,
    location: str,
    *,
    multiple: bool,
) -> tuple[PurePosixPath, ...]:
    if multiple:
        if not isinstance(value, list) or not value:
            raise DashboardError(f"{location}: expected a nonempty path list")
        raw_values = value
    else:
        raw_values = [value]
    paths = tuple(
        _safe_relative_path(item, f"{location}/{index}")
        for index, item in enumerate(raw_values)
    )
    if len(paths) != len(set(paths)):
        raise DashboardError(f"{location}: duplicate paths are forbidden")
    return paths


def _record_statuses(
    pack: Path,
    paths: Iterable[PurePosixPath],
    label: str,
) -> tuple[str, ...]:
    statuses: list[str] = []
    for path in paths:
        absolute = pack.joinpath(*path.parts)
        record = _load_json_object(absolute, f"{label}/{path.as_posix()}")
        status = record.get("status")
        if status not in {"complete", "partial", "blocked"}:
            raise DashboardError(
                f"{label}/{path.as_posix()}: unsupported completeness status"
            )
        statuses.append(status)
    return tuple(statuses)


def _record_objects(
    pack: Path,
    paths: Iterable[PurePosixPath],
    label: str,
) -> tuple[dict[str, Any], ...]:
    return tuple(
        _load_json_object(
            pack.joinpath(*path.parts),
            f"{label}/{path.as_posix()}",
        )
        for path in paths
    )


def _record_status(
    record: Mapping[str, Any],
    location: str,
) -> str:
    status = record.get("status")
    if status not in {"complete", "partial", "blocked"}:
        raise DashboardError(
            f"{location}: unsupported completeness status"
        )
    return status


def _required_list(
    record: Mapping[str, Any],
    key: str,
    location: str,
) -> list[Any]:
    value = record.get(key)
    if not isinstance(value, list):
        raise DashboardError(f"{location}/{key}: expected a list")
    return value


def _attainment_status(achieved: int, total: int) -> str:
    if total < 0 or achieved < 0 or achieved > total:
        raise DashboardError("assurance attainment counts are invalid")
    if total == 0 or achieved == 0:
        return "missing"
    if achieved == total:
        return "complete"
    return "partial"


def _pack_assurance_layers(
    *,
    skill_id: str,
    record_count: int,
    corpus_records: tuple[dict[str, Any], ...],
    slice_records: tuple[dict[str, Any], ...],
    corpus_status: str,
    slice_status: str,
) -> dict[str, dict[str, object]]:
    discovered_count = 0
    included_count = 0
    exclusion_count = 0
    upstream_complete_count = 0
    for corpus_index, corpus in enumerate(corpus_records):
        location = f"{skill_id}/corpus/{corpus_index}"
        discovery = corpus.get("discovery")
        if not isinstance(discovery, dict):
            raise DashboardError(f"{location}/discovery: expected an object")
        discovered_count += len(
            _required_list(
                discovery,
                "discovered_source_ids",
                f"{location}/discovery",
            )
        )
        included_count += len(
            _required_list(corpus, "included_sources", location)
        )
        exclusion_count += len(
            _required_list(corpus, "reviewed_exclusions", location)
        )
        upstream_complete = discovery.get("upstream_universe_complete")
        if not isinstance(upstream_complete, bool):
            raise DashboardError(
                f"{location}/discovery/upstream_universe_complete: "
                "expected a boolean"
            )
        upstream_complete_count += int(upstream_complete)

    total_slices = 0
    metadata_only_count = 0
    metadata_artifact_count = 0
    repository_materialized_count = 0
    external_cache_count = 0
    external_runtime_count = 0
    semantic_count = 0
    whole_source_count = 0
    other_selector_count = 0
    whole_source_metadata_only_count = 0
    fine_grained_materialized_count = 0
    for manifest_index, manifest in enumerate(slice_records):
        manifest_location = f"{skill_id}/slice/{manifest_index}"
        for source_index, source in enumerate(
            _required_list(manifest, "sources", manifest_location)
        ):
            source_location = (
                f"{manifest_location}/sources/{source_index}"
            )
            if not isinstance(source, dict):
                raise DashboardError(f"{source_location}: expected an object")
            for slice_index, item in enumerate(
                _required_list(source, "slices", source_location)
            ):
                location = f"{source_location}/slices/{slice_index}"
                if not isinstance(item, dict):
                    raise DashboardError(f"{location}: expected an object")
                selector = item.get("selector")
                if not isinstance(selector, dict):
                    raise DashboardError(
                        f"{location}/selector: expected an object"
                    )
                selector_kind = selector.get("kind")
                storage_mode = item.get("storage_mode")
                artifact_kind = item.get("artifact_kind")
                if selector_kind not in SELECTOR_KINDS:
                    raise DashboardError(
                        f"{location}/selector/kind: unsupported selector"
                    )
                if storage_mode not in STORAGE_MODES:
                    raise DashboardError(
                        f"{location}/storage_mode: unsupported storage mode"
                    )
                if artifact_kind not in ARTIFACT_KINDS:
                    raise DashboardError(
                        f"{location}/artifact_kind: unsupported artifact kind"
                    )
                total_slices += 1
                is_metadata_only = storage_mode == "metadata-only"
                is_content_artifact = artifact_kind != "metadata"
                is_repository_materialized = (
                    storage_mode == "embedded-open"
                    and is_content_artifact
                )
                is_semantic = selector_kind in SEMANTIC_SELECTOR_KINDS
                metadata_only_count += int(is_metadata_only)
                metadata_artifact_count += int(not is_content_artifact)
                repository_materialized_count += int(
                    is_repository_materialized
                )
                external_cache_count += int(
                    storage_mode == "external-cache"
                    and is_content_artifact
                )
                external_runtime_count += int(
                    storage_mode == "external-runtime-only"
                    and is_content_artifact
                )
                semantic_count += int(is_semantic)
                whole_source_count += int(selector_kind == "whole-source")
                other_selector_count += int(selector_kind == "other")
                whole_source_metadata_only_count += int(
                    selector_kind == "whole-source" and is_metadata_only
                )
                fine_grained_materialized_count += int(
                    is_semantic and is_repository_materialized
                )

    materialization_attainment = _attainment_status(
        repository_materialized_count,
        total_slices,
    )
    semantic_attainment = _attainment_status(
        semantic_count,
        total_slices,
    )
    return {
        "registration": {
            "status": "complete",
            "bundle_index_registered": True,
            "record_count": record_count,
        },
        "inventory": {
            "status": corpus_status,
            "corpus_count": len(corpus_records),
            "discovered_source_count": discovered_count,
            "included_source_count": included_count,
            "reviewed_exclusion_count": exclusion_count,
            "upstream_universe_complete_corpus_count": (
                upstream_complete_count
            ),
        },
        "content_materialized": {
            "status": aggregate_statuses(
                (slice_status, materialization_attainment)
            ),
            "slice_count": total_slices,
            "repository_materialized_slice_count": (
                repository_materialized_count
            ),
            "external_cache_content_slice_count": external_cache_count,
            "external_runtime_content_slice_count": external_runtime_count,
            "metadata_only_slice_count": metadata_only_count,
            "metadata_artifact_slice_count": metadata_artifact_count,
        },
        "semantic_slice": {
            "status": aggregate_statuses(
                (slice_status, semantic_attainment)
            ),
            "slice_count": total_slices,
            "fine_grained_slice_count": semantic_count,
            "whole_source_slice_count": whole_source_count,
            "other_selector_slice_count": other_selector_count,
            "whole_source_metadata_only_slice_count": (
                whole_source_metadata_only_count
            ),
            "fine_grained_materialized_slice_count": (
                fine_grained_materialized_count
            ),
        },
    }


def _load_pack_projection(
    root: Path,
    result: bundle_audit.BundleResult,
) -> tuple[
    dict[str, str],
    dict[str, dict[str, object]],
    tuple[str, ...],
]:
    entrypoint_relative = _safe_relative_path(
        result.entrypoint,
        f"{result.skill_id}/entrypoint",
    )
    expected = PurePosixPath(
        f"skills/{result.skill_id}/references/official-source-pack/bundle.json"
    )
    if entrypoint_relative != expected:
        raise DashboardError(f"{result.skill_id}: noncanonical bundle entrypoint")
    entrypoint = root.joinpath(*entrypoint_relative.parts)
    index = _load_json_object(entrypoint, f"{result.skill_id}/bundle.json")
    if (
        index.get("schema_version") != SCHEMA_VERSION
        or index.get("bundle_type") != "official-document-coverage"
        or index.get("skill_id") != result.skill_id
    ):
        raise DashboardError(f"{result.skill_id}: bundle registration identity is invalid")
    records = index.get("records")
    if not isinstance(records, dict) or set(records) != RECORD_FIELDS:
        raise DashboardError(f"{result.skill_id}: bundle record map is invalid")
    corpora = _registered_paths(
        records["corpora"],
        f"{result.skill_id}/records/corpora",
        multiple=True,
    )
    slices = _registered_paths(
        records["slice_manifests"],
        f"{result.skill_id}/records/slice_manifests",
        multiple=True,
    )
    licenses = _registered_paths(
        records["license_reviews"],
        f"{result.skill_id}/records/license_reviews",
        multiple=True,
    )
    scope = _registered_paths(
        records["scope_inventory"],
        f"{result.skill_id}/records/scope_inventory",
        multiple=False,
    )
    coverage = _registered_paths(
        records["coverage"],
        f"{result.skill_id}/records/coverage",
        multiple=False,
    )
    all_paths = (*corpora, *slices, *licenses, *scope, *coverage)
    if len(all_paths) != len(set(all_paths)):
        raise DashboardError(f"{result.skill_id}: one record is registered twice")
    pack = entrypoint.parent
    corpus_records = _record_objects(
        pack,
        corpora,
        f"{result.skill_id}/corpus",
    )
    authority_ids: list[str] = []
    for index, record in enumerate(corpus_records):
        authority_id = record.get("authority_id")
        if (
            not isinstance(authority_id, str)
            or not authority_id
            or not authority_id.isprintable()
        ):
            raise DashboardError(
                f"{result.skill_id}/corpus/{index}: invalid authority_id"
            )
        authority_ids.append(authority_id)
    if len(authority_ids) != len(set(authority_ids)):
        raise DashboardError(
            f"{result.skill_id}: duplicate corpus authority_id"
        )
    slice_records = _record_objects(
        pack,
        slices,
        f"{result.skill_id}/slice",
    )
    corpus_status = aggregate_statuses(
        _record_status(record, f"{result.skill_id}/corpus/{index}")
        for index, record in enumerate(corpus_records)
    )
    slice_status = aggregate_statuses(
        _record_status(record, f"{result.skill_id}/slice/{index}")
        for index, record in enumerate(slice_records)
    )
    license_status = aggregate_statuses(
        _record_statuses(pack, licenses, f"{result.skill_id}/license")
    )
    scope_status = aggregate_statuses(
        _record_statuses(pack, scope, f"{result.skill_id}/scope")
    )
    coverage_status = aggregate_statuses(
        _record_statuses(pack, coverage, f"{result.skill_id}/coverage")
    )
    # Coverage is a cross-record semantic projection rather than a seventh
    # dashboard dimension.  It therefore caps scope, which is the Skill-side
    # declared-subject surface, while bundle semantic state remains the final
    # independent cap.
    scope_status = aggregate_statuses((scope_status, coverage_status))
    dimensions = {
        "corpus": corpus_status,
        "slice": slice_status,
        "scope": scope_status,
        "license": license_status,
        # A complete license-review record includes resolved storage rules;
        # repository-local legacy storage is independently overlaid below.
        "storage": license_status,
        # Static bundle records do not establish current upstream freshness.
        # A live drift report may supply a conservative per-Skill overlay.
        "freshness": "unknown",
    }
    assurance_layers = _pack_assurance_layers(
        skill_id=result.skill_id,
        record_count=len(all_paths),
        corpus_records=corpus_records,
        slice_records=slice_records,
        corpus_status=corpus_status,
        slice_status=slice_status,
    )
    return dimensions, assurance_layers, tuple(sorted(authority_ids))


def _expected_skills(root: Path) -> dict[str, str]:
    try:
        skill_data = load_yaml_strict(
            root / "registry" / "skill-registry.yaml",
            "skill-registry.yaml",
        )
        expectation_data = load_yaml_strict(
            root / "registry" / "official-document-bundle-expectations.yaml",
            "official-document-bundle-expectations.yaml",
        )
    except (OSError, ValueError) as exc:
        raise DashboardError(
            f"official-document registry input is invalid ({exc})"
        ) from exc
    failures = bundle_audit.expectation_registry_validation_errors(
        expectation_data,
        skill_data,
    )
    if failures:
        raise DashboardError(
            "official-document expectation/Skill registry mismatch "
            f"({'; '.join(failures)})"
        )
    skills = expectation_data["skills"]
    result: dict[str, str] = {}
    for skill_id, entry in skills.items():
        if not isinstance(skill_id, str) or not isinstance(entry, dict):
            raise DashboardError("bundle expectation record is invalid")
        entrypoint = entry.get("entrypoint")
        expected = (
            f"skills/{skill_id}/references/official-source-pack/bundle.json"
        )
        if entrypoint != expected:
            raise DashboardError(f"{skill_id}: expectation entrypoint is noncanonical")
        result[skill_id] = expected
    return dict(sorted(result.items()))


def _selector_skill_ids(
    configuration: storage_audit.StorageConfiguration,
) -> dict[str, frozenset[str]]:
    result: dict[str, frozenset[str]] = {}
    for rule in configuration.artifact_sets:
        skill_ids: set[str] = set()
        for selector in rule.selectors:
            parts = PurePosixPath(selector.value).parts
            if len(parts) >= 2 and parts[0] == "skills":
                skill_ids.add(parts[1])
        result[rule.set_id] = frozenset(skill_ids)
    return result


def storage_statuses(
    root: Path,
    expected_skill_ids: Iterable[str],
) -> dict[str, str]:
    """Project the public central storage report to affected Skill IDs."""

    expected = frozenset(expected_skill_ids)
    report = storage_audit.audit_repository(root)
    if report.invalid_findings:
        return {skill_id: "invalid" for skill_id in expected}
    try:
        configuration = storage_audit.load_configuration(root)
    except (OSError, ValueError, storage_audit.StorageAuditError) as exc:
        raise DashboardError(f"storage configuration is invalid ({exc})") from exc
    affected = _selector_skill_ids(configuration)
    projected: dict[str, str] = {}
    for result in report.artifact_sets:
        if result.forbidden_path_count:
            for skill_id in affected.get(result.set_id, ()):
                if skill_id in expected:
                    projected[skill_id] = "blocked"
    if report.worktree_drift_findings:
        # Drift strings are diagnostics, not a stable machine interface for
        # path attribution. Conservatively cap every centrally governed Skill.
        for skill_ids in affected.values():
            for skill_id in skill_ids:
                if skill_id in expected:
                    projected[skill_id] = "blocked"
    return projected


def _empty_dimensions(status: str) -> dict[str, str]:
    return {name: status for name in DIMENSION_ORDER}


def _empty_assurance_layers(
    status: str,
) -> dict[str, dict[str, object]]:
    if status not in {"missing", "invalid"}:
        raise DashboardError("empty assurance layers must be missing or invalid")
    return {
        name: {"status": status}
        for name in ASSURANCE_LAYER_ORDER
    }


def _summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, object]:
    selected = tuple(rows)
    semantic = {
        status: sum(row["bundle_semantic_state"] == status for row in selected)
        for status in ("complete", "partial", "missing", "invalid")
    }
    dimensions = {
        dimension: {
            status: sum(
                row["dimensions"][dimension] == status for row in selected
            )
            for status in STATUS_ORDER
        }
        for dimension in DIMENSION_ORDER
    }
    overall = {
        status: sum(row["overall_status"] == status for row in selected)
        for status in STATUS_ORDER
    }
    assurance_layers = {
        layer: {
            status: sum(
                row["assurance_layers"][layer]["status"] == status
                for row in selected
            )
            for status in STATUS_ORDER
        }
        for layer in ASSURANCE_LAYER_ORDER
    }
    assurance_overall = {
        status: sum(row["assurance_status"] == status for row in selected)
        for status in STATUS_ORDER
    }
    return {
        "assurance_layers": assurance_layers,
        "assurance_overall": assurance_overall,
        "bundle_semantic": semantic,
        "dimensions": dimensions,
        "overall": overall,
    }


def build_dashboard(
    root: Path,
    *,
    bundle_report: bundle_audit.AuditReport | None = None,
    storage_status_by_skill: Mapping[str, str] | None = None,
    freshness_status_by_skill: (
        Mapping[str, Mapping[str, object]] | None
    ) = None,
    freshness_as_of_utc: str | None = None,
) -> dict[str, object]:
    try:
        selected_root = Path(root).resolve(strict=True)
    except OSError as exc:
        raise DashboardError(
            f"repository root is unavailable ({exc.__class__.__name__})"
        ) from exc
    expected = _expected_skills(selected_root)
    report = bundle_report or bundle_audit.audit_repository(selected_root)
    results = {result.skill_id: result for result in report.results}
    if len(results) != len(report.results) or set(results) != set(expected):
        raise DashboardError(
            "bundle audit does not contain the exact expected Skill set"
        )
    storage_overlay = (
        dict(storage_status_by_skill)
        if storage_status_by_skill is not None
        else storage_statuses(selected_root, expected)
    )
    freshness_overlay = dict(freshness_status_by_skill or {})
    if set(storage_overlay) - set(expected):
        raise DashboardError("storage overlay names an unknown Skill")
    if set(storage_overlay.values()) - set(STATUS_PRECEDENCE):
        raise DashboardError("storage overlay contains an unsupported status")
    if set(freshness_overlay) - set(expected):
        raise DashboardError("freshness overlay names an unknown Skill")
    if freshness_overlay and freshness_as_of_utc is None:
        raise DashboardError(
            "freshness overlay requires an explicit deterministic as-of time"
        )

    rows: list[dict[str, object]] = []
    for skill_id, entrypoint in expected.items():
        result = results[skill_id]
        if result.entrypoint != entrypoint:
            raise DashboardError(f"{skill_id}: audit entrypoint differs from expectation")
        if result.state in {"complete", "partial"}:
            dimensions, assurance_layers, authority_ids = _load_pack_projection(
                selected_root,
                result,
            )
        elif result.state == "missing":
            dimensions = _empty_dimensions("missing")
            assurance_layers = _empty_assurance_layers("missing")
            authority_ids = ()
        elif result.state == "invalid":
            dimensions = _empty_dimensions("invalid")
            assurance_layers = _empty_assurance_layers("invalid")
            authority_ids = ()
        else:
            raise DashboardError(f"{skill_id}: unsupported bundle audit state")
        if skill_id in storage_overlay:
            dimensions["storage"] = aggregate_statuses(
                (dimensions["storage"], storage_overlay[skill_id])
            )
        if skill_id in freshness_overlay:
            assert freshness_as_of_utc is not None
            dimensions["freshness"] = _apply_freshness_overlay(
                dimensions["freshness"],
                freshness_overlay[skill_id],
                authority_ids,
                as_of_utc=freshness_as_of_utc,
            )
        rows.append(
            make_skill_row(
                skill_id=skill_id,
                entrypoint=entrypoint,
                bundle_semantic_state=result.state,
                dimensions=dimensions,
                assurance_layers=assurance_layers,
            )
        )
    return {
        "assurance_layer_definitions": {
            "registration": (
                "The canonical bundle index exists, has the exact Skill "
                "identity and record families, and passed bundle registration "
                "audit. It does not claim document body availability."
            ),
            "inventory": (
                "Counts and status come from validated corpus manifests: "
                "discovered, included, and reviewed-excluded source units plus "
                "the recorded upstream-universe boundary."
            ),
            "content_materialized": (
                "Only a non-metadata artifact with storage_mode=embedded-open "
                "counts as repository-materialized content. Metadata-only, "
                "external-cache, and external-runtime-only records are shown "
                "separately and never upgraded by inference."
            ),
            "semantic_slice": (
                "Fine-grained slices require a heading, byte-range, "
                "json-pointer, line-range, page-range, or source-symbol "
                "selector. whole-source and other selectors are not counted "
                "as fine-grained; the dashboard separately counts the "
                "fine-grained slices that are also repository-materialized."
            ),
        },
        "assurance_layers": list(ASSURANCE_LAYER_ORDER),
        "claim_boundary": (
            "This dashboard reports document-assurance inputs only. It does not "
            "establish native execution, numerical convergence, physical "
            "validity, or scientific acceptance."
        ),
        "dimensions": list(DIMENSION_ORDER),
        "expected_bundle_count": len(expected),
        "report_type": "official-document-completeness-dashboard",
        "schema_version": SCHEMA_VERSION,
        "skills": rows,
        "summary": _summary(rows),
    }


def dashboard_bytes(report: Mapping[str, object]) -> bytes:
    return (
        json.dumps(
            report,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_output(path: Path, raw: bytes, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise DashboardError(f"output already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
        if path.exists() and not overwrite:
            raise DashboardError(f"output appeared during write: {path.name}")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = build_dashboard(args.root)
        raw = dashboard_bytes(report)
        if args.output is None:
            sys.stdout.buffer.write(raw)
        else:
            _write_output(args.output, raw, overwrite=args.force)
            summary = report["summary"]
            assert isinstance(summary, dict)
            print(
                "OFFICIAL_DOC_DASHBOARD "
                f"skills={report['expected_bundle_count']} "
                f"complete={summary['overall']['complete']} "
                f"output={args.output}"
            )
    except (DashboardError, OSError, ValueError) as exc:
        print(f"ERROR OFFICIAL_DOC_DASHBOARD {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
