#!/usr/bin/env python3
"""Pure v1.0 to v1.1 official-document-source-catalog converter.

The converter is deterministic, side-effect free, and projection-only. It only
transforms already-parsed records and does not enumerate files, write seeds,
resolve network resources, or build packs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any


SCHEMA_VERSION = "1.1"
CONTRACT_NAME = "official-document-source-catalog"
VERSION_SCOPE_KINDS = {
    "exact",
    "revision",
    "release-line",
    "latest-at-retrieval",
    "unversioned",
}

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
SOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
HTTPS_URL_RE = re.compile(r"^https://")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

LEGAL_BLOCKER_DROP = {
    "LICENSE.DOCUMENTATION.RIGHTS.UNRESOLVED",
    "LICENSE.DERIVATIVE.RIGHTS.UNRESOLVED",
    "LICENSE.COMPONENT.ARTIFACT.CLOSURE.MISSING",
}
BLOCKER_RENAME = {
    "MODEL.DATA.LICENSE.IDENTITY.MISSING": "MODEL.DATA.IDENTITY.MISSING",
}

LOSS_DROP = {
    "documentation-license-unresolved",
    "custom-license-derivative-rights-unresolved",
}

LOSS_RENAME = {
    "MODEL.DATA.LICENSE.IDENTITY.MISSING": "MODEL.DATA.IDENTITY.MISSING",
    "third-party-and-artifact-license-closure-external": "third-party-and-artifact-provenance-closure-external",
}

LOSS_ID_FIXED_DESCRIPTION = {
    "MODEL.DATA.IDENTITY.MISSING": "The data-identity migration lane is closed for this projection.",
    "third-party-and-artifact-provenance-closure-external": "The external provenance and artifact-closure path is recorded with exact byte-identity boundaries.",
    "LICENSE.COMPONENT.IDENTITY.CLOSURE.MISSING": "No byte-identity closure for this component artifact has been provided.",
}

BLOCKER_ID_FIXED_DESCRIPTION = {
    "MODEL.DATA.IDENTITY.MISSING": "Model-data identity is represented by stable byte-identity records only; this projection does not infer legal conclusions.",
}

SELECTOR_LAYER_FIXES = {"raw-source"}

LIMITATION_CLEAN_TEXT = "Selector kind json-pointer is retained; no virtual selector body bytes are introduced by migration."

TECHNICAL_TEXT_BY_EXACT_TEXT = {
    "VASPkit technical execution constraint: runtime or binary closure remains external to this projection.",
    "Multiwfn runtime support evidence is bounded to exact references and technical command-surface metadata.",
}


class MigrationError(ValueError):
    """Structured conversion failure with machine-readable context."""

    def __init__(self, code: str, location: str, message: str) -> None:
        super().__init__(f"{code}: {location}: {message}")
        self.code = code
        self.location = location
        self.message = message


def canonical_json_bytes(value: Any) -> bytes:
    """Return repository canonical JSON bytes."""
    return canonical_projection_bytes(value) + b"\n"


def canonical_projection_bytes(value: Any) -> bytes:
    """Return repository canonical bytes used for hash identity."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    ).encode("utf-8")


def _assert_selector_id_unique(
    selector_id: str,
    seen_selector_ids: set[str],
    location: str,
) -> None:
    _require(selector_id not in seen_selector_ids, "SLICE_ID_DUPLICATE", location, "slice_id must be unique globally")
    seen_selector_ids.add(selector_id)


def _require_distinct_strings(values: list[Any], code: str, location: str) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if not _is_str(value):
            _require(False, code, location, "entries must be strings")
        normalized_value = str(value)
        _require(
            normalized_value not in normalized,
            "RECORD_DUPLICATE_VALUE",
            location,
            "duplicate entries are not allowed",
        )
        normalized.append(normalized_value)
    return normalized


def _subject_from_catalog(subject: dict[str, Any], subject_id: str) -> dict[str, Any]:
    title = _require_non_empty(subject.get("title"), "OLD_SUBJECT_TITLE_MISSING", f"/catalog/subjects/{subject_id}/title", "title required")
    category = _require_non_empty(subject.get("category"), "OLD_SUBJECT_CATEGORY_MISSING", f"/catalog/subjects/{subject_id}/category", "category required")
    requirement_strength = _require_non_empty(
        subject.get("requirement_strength"),
        "OLD_SUBJECT_REQUIREMENT_STRENGTH_MISSING",
        f"/catalog/subjects/{subject_id}/requirement_strength",
        "requirement_strength required",
    )
    return {
        "title": title[:500],
        "category": category,
        "requirement_strength": requirement_strength,
    }


def _verify_raw_bytes(raw_bytes: Any, location: str) -> int:
    _require(isinstance(raw_bytes, int) and not isinstance(raw_bytes, bool), "SOURCE_BYTES_TYPE", location, "bytes must be non-boolean int")
    _require(raw_bytes > 0, "SOURCE_BYTES_INVALID", location, "bytes must be positive int")
    return int(raw_bytes)


def _normalize_preimage_bytes(preimage: Any, location: str) -> bytes:
    if isinstance(preimage, bytes):
        return preimage
    if isinstance(preimage, bytearray):
        return bytes(preimage)
    _require(_is_str(preimage), "INVENTORY_PREIMAGE_TYPE", location, "canonical preimage must be bytes or text")
    return str(preimage).encode("utf-8")


def _normalize_text(value: Any) -> str:
    _require_non_empty(value, "TYPE_TEXT_EMPTY", "/statement", "text must be non-empty")
    text = str(value).strip()
    return text[:2000]


def _coerce_exact_description(
    value: Any,
    fixed_map: dict[str, str],
    fallback: str,
) -> str:
    if _is_str(value):
        candidate = str(value).strip()
        if candidate in TECHNICAL_TEXT_BY_EXACT_TEXT:
            return candidate
        if candidate in fixed_map:
            return fixed_map[candidate]
        if candidate != "":
            return candidate[:2000]
    return _normalize_text(fallback)


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _make_identity(payload: Any) -> dict[str, Any]:
    raw = canonical_json_bytes(payload)
    return {"sha256": _sha256_hex(raw), "bytes": len(raw)}


def _require(condition: bool, code: str, location: str, message: str) -> None:
    if not condition:
        raise MigrationError(code, location, message)


def _is_str(value: Any) -> bool:
    return isinstance(value, str)


def _require_non_empty(value: Any, code: str, location: str, message: str) -> str:
    _require(_is_str(value) and value.strip() != "", code, location, message)
    return value.strip()


def _safe_copy(value: Any) -> Any:
    return copy.deepcopy(value)


def _require_mapping(value: Any, code: str, location: str) -> dict[str, Any]:
    _require(isinstance(value, dict), code, location, "must be a mapping")
    return value


def _require_list(value: Any, code: str, location: str) -> list[Any]:
    _require(isinstance(value, list), code, location, "must be an array")
    return value


def _extract_provider(input_value: Any) -> tuple[str, str]:
    provider = _require_mapping(input_value, "PROVIDER_TYPE", "/provider")
    provider_id = _require_non_empty(
        provider.get("provider_id"),
        "PROVIDER_ID_MISSING",
        "/provider/provider_id",
        "provider_id required",
    )
    provider_input_id = _require_non_empty(
        provider.get("provider_input_id") or provider.get("input_id"),
        "PROVIDER_INPUT_ID_MISSING",
        "/provider/provider_input_id",
        "provider_input_id or input_id required",
    )
    _require(SAFE_ID_RE.fullmatch(provider_id) is not None, "PROVIDER_ID_INVALID", "/provider/provider_id", "provider_id must be hyphen-safe id")
    _require(
        SAFE_ID_RE.fullmatch(provider_input_id) is not None,
        "PROVIDER_INPUT_ID_INVALID",
        "/provider/provider_input_id",
        "provider_input_id must be safe id",
    )
    return provider_id, provider_input_id


def _extract_authority(input_value: Any) -> str:
    if isinstance(input_value, str):
        authority_id = input_value
    else:
        authority = _require_mapping(input_value, "AUTHORITY_TYPE", "/authority")
        authority_id = authority.get("authority_id")
    authority_id = _require_non_empty(
        authority_id,
        "AUTHORITY_ID_MISSING",
        "/authority/authority_id",
        "authority_id required",
    )
    _require(SAFE_ID_RE.fullmatch(authority_id) is not None, "AUTHORITY_ID_INVALID", "/authority/authority_id", "authority_id must be hyphen-safe id")
    return authority_id


def _extract_authority_root(
    authority_projection: Any,
    inventory_locator: str,
) -> str:
    projection = _require_mapping(authority_projection, "AUTHORITY_PROJECTION_TYPE", "/authority_projection")
    canonical_urls = _require_list(
        projection.get("canonical_urls"),
        "AUTHORITY_CANONICAL_URLS_TYPE",
        "/authority_projection/canonical_urls",
    )
    canonical_urls = [
        str(item)
        for item in canonical_urls
        if isinstance(item, str) and HTTPS_URL_RE.match(item) is not None
    ]
    _require(canonical_urls, "AUTHORITY_CANONICAL_URLS_MISSING", "/authority_projection/canonical_urls", "non-empty canonical_urls required")

    candidates = [url for url in canonical_urls if inventory_locator.startswith(url)]
    _require(
        len(candidates) > 0,
        "AUTHORITY_ROOT_MISSING",
        "/authority_projection/canonical_urls",
        "inventory_projection locator is not covered by canonical_urls",
    )
    max_len = max(len(item) for item in candidates)
    longest = [item for item in candidates if len(item) == max_len]
    _require(
        len(longest) == 1,
        "AUTHORITY_ROOT_AMBIGUOUS",
        "/authority_projection/canonical_urls",
        "inventory_projection locator has multiple longest canonical URL prefixes",
    )
    return longest[0]


def _require_locator_in_authority_urls(
    canonical_urls: list[str],
    locator: str,
    location: str,
) -> None:
    _require(
        any(locator.startswith(url) for url in canonical_urls),
        "AUTHORITY_ROOT_MISSING",
        location,
        "locator is not covered by authority canonical_urls",
    )


def _require_registered_version_scope(
    scope: dict[str, Any],
    authority_projection: dict[str, Any],
) -> tuple[str, Any]:
    _require(
        isinstance(scope.get("kind"), str) and scope["kind"] in VERSION_SCOPE_KINDS,
        "VERSION_SCOPE_KIND_INVALID",
        "/version_scope/kind",
        "unsupported version_scope kind",
    )
    kind = scope["kind"]

    registered = _require_list(
        authority_projection.get("version_scopes"),
        "VERSION_SCOPE_REGISTRY_TYPE",
        "/authority_projection/version_scopes",
    )

    def match(record: dict[str, Any]) -> bool:
        if not isinstance(record, dict):
            return False
        if kind in {"exact", "revision"}:
            if record.get("scope") not in {"exact", "revision"}:
                return False
            exact_version = record.get("exact_version")
            return isinstance(exact_version, str) and exact_version == scope.get("value")
        if kind == "release-line":
            return (
                record.get("scope") in {"release-series", "release_series", "release-line"}
                and record.get("release_series") == scope.get("value")
            )
        if kind == "latest-at-retrieval":
            return record.get("scope") == "latest-at-retrieval"
        if kind == "unversioned":
            return record.get("scope") == "unversioned"
        return False

    candidates = [item for item in registered if match(item)]
    _require(len(candidates) == 1, "VERSION_SCOPE_UNIQUE_MISMATCH", "/version_scope", "version_scope must have exactly one registry match")
    return kind, _safe_copy(candidates[0])


def _project_version_scope(scope: Any, authority_projection: Any) -> dict[str, Any]:
    version_scope = _require_mapping(scope, "VERSION_SCOPE_TYPE", "/version_scope")
    input_kind = version_scope.get("kind")
    kind, _matched_scope = _require_registered_version_scope(
        version_scope,
        _require_mapping(authority_projection, "AUTHORITY_PROJECTION_TYPE", "/authority_projection"),
    )
    if input_kind == "revision" and kind == "revision":
        exact_version = _matched_scope.get("exact_version")
        value = version_scope.get("value")
        if exact_version is not None and str(value) == str(exact_version):
            kind = "exact"

    value = version_scope.get("value")
    retrieved_utc = version_scope.get("retrieved_utc")

    if kind in {"exact", "revision", "release-line"}:
        _require(_is_str(value) and value.strip() != "", "VERSION_SCOPE_VALUE_MISSING", "/version_scope/value", "value required")
        return {
            "kind": kind,
            "value": str(value),
            "retrieved_utc": None,
            "snapshot_identity": None,
        }

    if kind == "unversioned":
        return {
            "kind": "unversioned",
            "value": None,
            "retrieved_utc": None,
            "snapshot_identity": None,
        }

    _require(kind == "latest-at-retrieval", "VERSION_SCOPE_KIND_INVALID", "/version_scope/kind", "latest-at-retrieval required")
    _require(_is_str(retrieved_utc) and retrieved_utc.strip() != "", "VERSION_SCOPE_RETRIEVED_UTC_MISSING", "/version_scope/retrieved_utc", "latest-at-retrieval requires retrieved_utc")

    return {
        "kind": "latest-at-retrieval",
        "value": None,
        "retrieved_utc": str(retrieved_utc).strip(),
        "snapshot_identity": None,
    }


def _subject_category_from_scope(value: str) -> str:
    mapping = {
        "claim": "scientific-limitation",
        "documented-claim": "scientific-limitation",
        "capability": "workflow",
        "task": "workflow",
        "workflow": "workflow",
        "executable": "workflow",
        "parameter": "input-parameter",
        "input-keyword": "input-parameter",
        "output-field": "output-observable",
        "observable": "output-observable",
        "backend": "provenance",
        "limitation": "scientific-limitation",
    }
    return mapping.get(value, "other")


def _subject_requirement_strength(disposition: Any) -> str:
    value = str(disposition) if _is_str(disposition) else "covered"
    if value == "partial":
        return "supporting"
    if value == "blocked":
        return "required"
    return "required"


def _build_scope_subjects(scope_catalog: Any, provider_input_id: str) -> dict[str, dict[str, Any]]:
    scope = _require_mapping(scope_catalog, "SCOPE_CATALOG_TYPE", "/scope_catalog")
    subjects = _require_list(scope.get("subjects"), "SCOPE_SUBJECTS_TYPE", "/scope_catalog/subjects")

    output: dict[str, dict[str, Any]] = {}
    for subject in subjects:
        if not isinstance(subject, dict):
            continue
        if subject.get("evidence_class") != "official-provider-required":
            continue
        provider_input_ids = _require_list(subject.get("provider_input_ids"), "SCOPE_PROVIDER_INPUT_IDS_TYPE", "/scope_catalog/subjects/provider_input_ids")
        provider_ids = [str(item) for item in provider_input_ids if _is_str(item)]
        if provider_input_id not in provider_ids:
            continue
        subject_id = _require_non_empty(subject.get("subject_id"), "SCOPE_SUBJECT_ID_MISSING", "/scope_catalog/subjects/subject_id", "subject_id required")
        _require(SAFE_ID_RE.fullmatch(subject_id) is not None, "SCOPE_SUBJECT_ID_INVALID", f"/scope_catalog/subjects/{subject_id}", "subject_id must be safe id")
        statement = _require_non_empty(subject.get("statement"), "SCOPE_SUBJECT_STATEMENT_MISSING", f"/scope_catalog/subjects/{subject_id}/statement", "statement required")
        output[subject_id] = {
            "statement": _normalize_text(statement),
            "_provider_input_ids": provider_ids,
            "_subject_id": subject_id,
        }
    return output


def _normalize_receipt(kind: str, identity: Any, location: str) -> dict[str, Any]:
    source = _require_mapping(identity, "SOURCE_IDENTITY_TYPE", location)
    method = source.get("retrieval_method")
    if method not in {"https-get", "official-api", "git-object", "other"}:
        # deterministic fallback from legacy schema kind
        legacy = source.get("kind")
        if legacy == "external-receipt":
            method = "https-get"
        elif legacy == "revision":
            method = "git-object"
        else:
            method = "other"
    raw_sha256 = source.get("raw_sha256")
    raw_bytes = source.get("raw_bytes")
    retrieved_utc = source.get("retrieved_utc")
    _require(_is_str(raw_sha256) and SHA256_RE.fullmatch(raw_sha256), "SOURCE_IDENTITY_SHA256_INVALID", f"{location}/raw_sha256", "raw_sha256 must be sha256")
    raw_bytes = _verify_raw_bytes(raw_bytes, f"{location}/raw_bytes")
    _require(
        _is_str(retrieved_utc) and retrieved_utc.strip() != "",
        "SOURCE_IDENTITY_UTC_INVALID",
        f"{location}/retrieved_utc",
        "retrieved_utc required",
    )
    return {
        "retrieval_method": method,
        "retrieved_utc": str(retrieved_utc).strip(),
        "raw_sha256": str(raw_sha256),
        "raw_bytes": int(raw_bytes),
    }


def _as_content(source: dict[str, Any], source_id: str) -> dict[str, Any]:
    locator = source.get("locator")
    _require(
        _is_str(locator) and HTTPS_URL_RE.match(locator) is not None,
        "SOURCE_LOCATOR_INVALID",
        f"/sources/{source_id}/locator",
        "locator must be HTTPS URL",
    )
    if source.get("external_identity") is not None:
        receipt = _normalize_receipt("external-content", source["external_identity"], f"/sources/{source_id}/external_identity")
        return {
            "content_mode": "external-content",
            "locator": locator,
            "receipt": receipt,
        }
    if source.get("metadata_evidence_ref") is not None:
        evidence = _require_mapping(source.get("metadata_evidence_ref"), "SOURCE_METADATA_REF_TYPE", f"/sources/{source_id}/metadata_evidence_ref")
        sha = evidence.get("sha256")
        bytes_count = evidence.get("bytes")
        _require(_is_str(sha) and SHA256_RE.fullmatch(sha), "SOURCE_METADATA_REF_SHA256", f"/sources/{source_id}/metadata_evidence_ref/sha256", "sha256 invalid")
        bytes_count = _verify_raw_bytes(bytes_count, f"/sources/{source_id}/metadata_evidence_ref/bytes")
        return {
            "content_mode": "metadata-only",
            "locator": locator,
            "identity": {"sha256": str(sha), "bytes": int(bytes_count)},
        }
    content_ref = _require_mapping(source.get("content_ref"), "SOURCE_CONTENT_REF_MISSING", f"/sources/{source_id}/content_ref")
    sha = content_ref.get("sha256")
    bytes_count = content_ref.get("bytes")
    path = content_ref.get("path")
    _require(_is_str(path) and path.strip() != "", "SOURCE_CONTENT_PATH_MISSING", f"/sources/{source_id}/content_ref/path", "path required")
    _require(_is_str(sha) and SHA256_RE.fullmatch(sha), "SOURCE_CONTENT_SHA256_INVALID", f"/sources/{source_id}/content_ref/sha256", "sha256 invalid")
    bytes_count = _verify_raw_bytes(bytes_count, f"/sources/{source_id}/content_ref/bytes")
    return {
        "content_mode": "embedded-content",
        "locator": path,
        "sha256": str(sha),
        "bytes": int(bytes_count),
    }


def _project_authority_revision(
    legacy_authority_revision: Any,
    version_scope_kind: str,
    inventory_identity: dict[str, Any],
    snapshot_identity: dict[str, Any] | None = None,
) -> str:
    def _coerce_identity(value: Any) -> str | None:
        if isinstance(value, str):
            candidate = value.strip()
            return candidate or None
        if not isinstance(value, dict):
            return None
        for key in ("value", "revision", "content_sha256", "sha256", "sha"):
            candidate = _coerce_identity(value.get(key))
            if candidate is not None:
                return candidate
        nested = value.get("snapshot_identity")
        if isinstance(nested, dict):
            for key in ("value", "content_sha256", "sha256", "sha"):
                candidate = _coerce_identity(nested.get(key))
                if candidate is not None:
                    return candidate
        return None

    if version_scope_kind == "latest-at-retrieval":
        legacy_snapshot = _coerce_identity(legacy_authority_revision)
        if legacy_snapshot is not None:
            return legacy_snapshot
        _require(
            snapshot_identity is not None,
            "AUTHORITY_REVISION_MISSING",
            "/authority_revision",
            "authority_revision required for latest-at-retrieval when legacy snapshot is unavailable",
        )
        return str(snapshot_identity["sha256"])

    if version_scope_kind == "unversioned":
        legacy_revision = _coerce_identity(legacy_authority_revision)
        if legacy_revision is not None:
            return legacy_revision
        return str(inventory_identity["sha256"])

    legacy_revision = _coerce_identity(legacy_authority_revision)
    if legacy_revision is not None:
        return legacy_revision
    return str(inventory_identity["sha256"])


def _project_selector(
    source_id: str,
    slice_record: dict[str, Any],
    loss_renames: dict[str, str],
    loss_drop: set[str],
    seen_selector_ids: set[str],
    source_external_receipt: dict[str, Any] | None,
) -> tuple[dict[str, Any], bool]:
    selector = _require_mapping(slice_record.get("selector"), "SLICE_SELECTOR_TYPE", f"/sources/{source_id}/slices/selector")
    selector_id = _require_non_empty(
        slice_record.get("slice_id") or slice_record.get("selector_id"),
        "SLICE_ID_MISSING",
        f"/sources/{source_id}/slices/slice_id",
        "slice_id required",
    )
    _require(SAFE_ID_RE.fullmatch(selector_id) is not None, "SLICE_ID_INVALID", f"/sources/{source_id}/slices/{selector_id}/slice_id", "slice_id must be safe id")
    _assert_selector_id_unique(selector_id, seen_selector_ids, f"/sources/{source_id}/slices/{selector_id}/slice_id")
    kind = _require_non_empty(
        selector.get("kind"),
        "SLICE_KIND_MISSING",
        f"/sources/{source_id}/slices/{selector_id}/kind",
        "selector kind required",
    )
    layer = _require_non_empty(
        selector.get("layer"),
        "SLICE_LAYER_MISSING",
        f"/sources/{source_id}/slices/{selector_id}/layer",
        "slice layer required",
    )
    _require(layer in {"raw-source", "derived-artifact"}, "SLICE_LAYER_INVALID", f"/sources/{source_id}/slices/{selector_id}/layer", "layer invalid")
    if kind == "json-pointer" and layer in SELECTOR_LAYER_FIXES:
        layer = "derived-artifact"
    _require(kind in {"heading", "byte-range", "json-pointer", "line-range", "page-range", "whole-source", "source-symbol", "other"}, "SLICE_KIND_INVALID", f"/sources/{source_id}/slices/{selector_id}/kind", "selector kind invalid")
    if kind == "whole-source":
        _require(selector.get("value") == "*", "SLICE_WHOLE_SOURCE_VALUE", f"/sources/{source_id}/slices/{selector_id}/value", "whole-source value must be '*'")
    if kind == "byte-range":
        value = _require_non_empty(
            selector.get("value"),
            "SLICE_VALUE_MISSING",
            f"/sources/{source_id}/slices/{selector_id}/value",
            "byte-range value required",
        )
        _require(
            isinstance(value, str) and re.fullmatch(r"^(?:0|[1-9][0-9]*):[1-9][0-9]*$", value) is not None,
            "SLICE_BYTE_RANGE_VALUE_INVALID",
            f"/sources/{source_id}/slices/{selector_id}/value",
            "byte-range requires start:end",
        )
    else:
        value = _require_non_empty(
            selector.get("value"),
            "SLICE_VALUE_MISSING",
            f"/sources/{source_id}/slices/{selector_id}/value",
            "selector value required",
        )

    subject_ids = _require_list(
        slice_record.get("subject_ids"),
        "SLICE_SUBJECT_IDS_TYPE",
        f"/sources/{source_id}/slices/{selector_id}/subject_ids",
    )
    loss_ids = _require_list(
        slice_record.get("loss_ids", []),
        "SLICE_LOSS_IDS_TYPE",
        f"/sources/{source_id}/slices/{selector_id}/loss_ids",
    )

    normalized_subject_ids = _require_distinct_strings(subject_ids, "SLICE_SUBJECT_ID_DUPLICATE", f"/sources/{source_id}/slices/{selector_id}/subject_ids")

    normalized_losses: list[str] = []
    for loss_id in loss_ids:
        _require(_is_str(loss_id), "SLICE_LOSS_ID_INVALID", f"/sources/{source_id}/slices/{selector_id}/loss_ids", "loss id must be string")
        normalized = loss_renames.get(str(loss_id), str(loss_id))
        if normalized in loss_drop:
            continue
        _require(
            normalized not in normalized_losses,
            "SLICE_LOSS_ID_DUPLICATE",
            f"/sources/{source_id}/slices/{selector_id}/loss_ids",
            "loss_ids must not contain duplicates",
        )
        normalized_losses.append(normalized)

    external_receipt = slice_record.get("external_receipt")
    selected_identity: dict[str, Any] | None = None
    if external_receipt is not None:
        receipt = _require_mapping(
            external_receipt,
            "SLICE_EXTERNAL_RECEIPT_TYPE",
            f"/sources/{source_id}/slices/{selector_id}/external_receipt",
        )
        selected_sha = _require_non_empty(
            receipt.get("selected_sha256"),
            "SLICE_SELECTED_SHA256_MISSING",
            f"/sources/{source_id}/slices/{selector_id}/external_receipt/selected_sha256",
            "selected_sha256 required",
        )
        selected_bytes = _verify_raw_bytes(
            receipt.get("selected_bytes"),
            f"/sources/{source_id}/slices/{selector_id}/external_receipt/selected_bytes",
        )
        _require(
            source_external_receipt is not None and selected_sha == source_external_receipt.get("raw_sha256"),
            "SLICE_SELECTED_SHA256_MISMATCH",
            f"/sources/{source_id}/slices/{selector_id}/external_receipt",
            "selected_sha256 must match source external identity raw_sha256",
        )
        _require(
            selected_bytes == source_external_receipt.get("raw_bytes"),
            "SLICE_SELECTED_BYTES_MISMATCH",
            f"/sources/{source_id}/slices/{selector_id}/external_receipt",
            "selected_bytes must match source external identity raw_bytes",
        )
        selected_identity = {"sha256": str(selected_sha), "bytes": int(selected_bytes)}

    return (
        {
            "selector_id": selector_id,
            "layer": layer,
            "kind": kind,
            "value": str(value),
            "subject_ids": normalized_subject_ids,
            "loss_ids": normalized_losses,
            **({"selected_identity": selected_identity} if selected_identity is not None else {}),
        },
        kind == "json-pointer",
    )


def _project_loss(loss: dict[str, Any], loss_renames: dict[str, str]) -> tuple[str, dict[str, Any]] | None:
    loss_id = _require_non_empty(loss.get("loss_id"), "LOSS_ID_MISSING", "/losses/loss_id", "loss_id required")
    if loss_id in LOSS_DROP:
        return None
    mapped_id = loss_renames.get(loss_id, loss_id)
    _require(SAFE_ID_RE.fullmatch(mapped_id) is not None, "LOSS_ID_INVALID", "/losses/loss_id", "loss_id must be safe id")

    stage = loss.get("stage")
    materiality = loss.get("materiality")
    disposition = loss.get("disposition")
    affected_source_ids = _require_list(loss.get("affected_source_ids"), "LOSS_AFFECTED_SOURCE_IDS_TYPE", "/losses/affected_source_ids")
    _require(stage in {"discovery", "retrieval", "extraction", "normalization", "storage", "mapping", "other"}, "LOSS_STAGE_INVALID", "/losses/stage", "invalid loss stage")
    _require(materiality in {"none", "non-material", "material", "unknown"}, "LOSS_MATERIALITY_INVALID", "/losses/materiality", "invalid materiality")
    _require(disposition in {"accepted", "preserved", "external-only", "blocked"}, "LOSS_DISPOSITION_INVALID", "/losses/disposition", "invalid disposition")
    _require(affected_source_ids, "LOSS_AFFECTED_SOURCE_IDS_EMPTY", "/losses/affected_source_ids", "affected_source_ids must be non-empty")

    description = _coerce_exact_description(
        loss.get("description"),
        LOSS_ID_FIXED_DESCRIPTION,
        "The source-conversion loss is recorded as technical evidence limitation.",
    )
    if mapped_id in LOSS_ID_FIXED_DESCRIPTION:
        description = LOSS_ID_FIXED_DESCRIPTION[mapped_id]

    mapped_sources = _require_distinct_strings(affected_source_ids, "LOSS_AFFECTED_SOURCE_ID_INVALID", "/losses/affected_source_ids")

    return mapped_id, {
        "stage": stage,
        "description": description,
        "materiality": materiality,
        "disposition": disposition,
        "affected_source_ids": sorted(mapped_sources),
    }


def _project_blockers(blockers: Any) -> list[dict[str, Any]]:
    if not isinstance(blockers, list):
        return []
    normalized: list[dict[str, Any]] = []
    for blocker in blockers:
        if not isinstance(blocker, dict):
            continue
        code = blocker.get("code")
        if code in LEGAL_BLOCKER_DROP:
            continue
        _require(_is_str(code), "BLOCKER_CODE_MISSING", "/blockers/code", "blocker code required")
        code = BLOCKER_RENAME.get(str(code), str(code))
        if code in LEGAL_BLOCKER_DROP:
            continue
        description = _coerce_exact_description(
            blocker.get("description"),
            BLOCKER_ID_FIXED_DESCRIPTION,
            "Technical limitation remains in conversion-only record",
        )
        description = BLOCKER_ID_FIXED_DESCRIPTION.get(code, description)
        dimensions = blocker.get("dimensions")
        if isinstance(dimensions, list):
            dimensions = [str(item) for item in dimensions if _is_str(item)]
            dimensions = sorted(set(dimensions))
        else:
            dimensions = []
        _require(len(dimensions) >= 1, "BLOCKER_DIMENSIONS_EMPTY", "/blockers/dimensions", "dimensions must be non-empty")
        normalized.append({"code": str(code), "description": description[:2000], "dimensions": dimensions})
    return normalized


def _project_limitation_from_exclusion(source_id: str, exclusion: dict[str, Any]) -> str:
    rationale = _require_non_empty(
        exclusion.get("rationale"),
        "EXCLUSION_RATIONALE_MISSING",
        f"/reviewed_exclusions/{source_id}/rationale",
        "rationale required",
    )
    return _coerce_exact_description(rationale, {}, "Reviewed exclusion rationale is technical and non-legal.")


def _build_catalog_subjects(catalog_subjects: Any) -> dict[str, dict[str, str]]:
    if catalog_subjects is None:
        return {}
    subjects = _require_list(catalog_subjects, "CATALOG_SUBJECTS_TYPE", "/subjects")
    output: dict[str, dict[str, str]] = {}
    for subject in subjects:
        if not isinstance(subject, dict):
            continue
        subject_id = _require_non_empty(subject.get("subject_id"), "CATALOG_SUBJECT_ID_MISSING", "/subjects/subject_id", "subject_id required")
        _require(SAFE_ID_RE.fullmatch(subject_id) is not None, "CATALOG_SUBJECT_ID_INVALID", f"/subjects/{subject_id}", "subject_id must be safe id")
        _require(subject_id not in output, "CATALOG_SUBJECT_DUPLICATE", f"/subjects/{subject_id}", "subject_id duplicate")
        output[subject_id] = _subject_from_catalog(_require_mapping(subject, "CATALOG_SUBJECT_TYPE", f"/subjects/{subject_id}"), subject_id)
    return output


def _project_inventory_projection(inventory_projection: Any, authority_root: str) -> tuple[str, dict[str, Any]]:
    projection = _require_mapping(inventory_projection, "INVENTORY_PROJECTION_TYPE", "/inventory_projection")
    locator = _require_non_empty(projection.get("locator"), "INVENTORY_PROJECTION_LOCATOR_MISSING", "/inventory_projection/locator", "locator required")
    _require(HTTPS_URL_RE.match(locator) is not None, "INVENTORY_PROJECTION_LOCATOR_INVALID", "/inventory_projection/locator", "inventory_projection locator must be https URL")
    _require(locator.startswith(authority_root), "INVENTORY_PROJECTION_LOCATOR_SCOPE", "/inventory_projection/locator", "inventory_locator must match chosen authority_root prefix")

    provided_identity = _require_mapping(
        projection.get("identity"),
        "INVENTORY_PROJECTION_IDENTITY_MISSING",
        "/inventory_projection/identity",
    )
    identity_sha = _require_non_empty(
        provided_identity.get("sha256"),
        "INVENTORY_PROJECTION_IDENTITY_SHA256_MISSING",
        "/inventory_projection/identity/sha256",
        "identity.sha256 required",
    )
    _require(SHA256_RE.fullmatch(identity_sha), "INVENTORY_PROJECTION_IDENTITY_SHA256_INVALID", "/inventory_projection/identity/sha256", "identity.sha256 must be sha256")
    provided_bytes = _verify_raw_bytes(
        provided_identity.get("bytes"),
        "/inventory_projection/identity/bytes",
    )
    preimage = projection.get("canonical_preimage_bytes")
    _require(_is_str(preimage) or isinstance(preimage, (bytes, bytearray)), "INVENTORY_PROJECTION_PREIMAGE_MISSING", "/inventory_projection/canonical_preimage_bytes", "canonical_preimage_bytes required")
    preimage_bytes = _normalize_preimage_bytes(preimage, "/inventory_projection/canonical_preimage_bytes")
    _require(len(preimage_bytes) == provided_bytes, "INVENTORY_PREIMAGE_BYTES_MISMATCH", "/inventory_projection/canonical_preimage_bytes", "canonical_preimage_bytes length mismatch")
    _require(_sha256_hex(preimage_bytes) == identity_sha, "INVENTORY_PREIMAGE_SHA256_MISMATCH", "/inventory_projection/identity", "identity does not match canonical preimage bytes")
    return locator, {"sha256": identity_sha, "bytes": provided_bytes}


def _snapshot_from_sources_and_exclusions(
    discovered_sources: dict[str, Any],
) -> dict[str, Any]:
    aggregate_entries: list[dict[str, Any]] = []
    for source_id in sorted(discovered_sources):
        source = discovered_sources[source_id]
        if source["disposition"] != "included":
            aggregate_entries.append(
                {
                    "source_id": source_id,
                    "disposition": "excluded",
                    "inventory_entry_identity": source["content"]["inventory_entry_identity"],
                }
            )
            continue
        _require(
            source["content"]["content_mode"] == "external-content",
            "SOURCE_SNAPSHOT_SOURCE_MODE",
            f"/discovered_sources/{source_id}/content/content_mode",
            "latest-at-retrieval snapshot requires exact external-content sources",
        )
        aggregate_entries.append(
            {
                "source_id": source_id,
                "disposition": source["disposition"],
                "locator": source["content"]["locator"],
                "receipt": source["content"]["receipt"],
            }
        )
    return _canonical_snapshot_identity(aggregate_entries)


def _canonical_snapshot_identity(values: Any) -> dict[str, Any]:
    projection = canonical_projection_bytes(values)
    return {"sha256": _sha256_hex(projection), "bytes": len(projection)}


def _project_sources(
    sources: list[Any],
    loss_renames: dict[str, str],
    loss_drop: set[str],
    valid_subjects: set[str],
    valid_losses: set[str],
) -> tuple[dict[str, Any], set[str], bool]:
    projected: dict[str, Any] = {}
    referenced_losses: set[str] = set()
    has_json_pointer = False

    seen_ids: set[str] = set()
    seen_selector_ids: set[str] = set()
    for source in sources:
        _require(isinstance(source, dict), "SOURCE_TYPE", "/sources", "each source must be mapping")
        source_id = _require_non_empty(source.get("source_id"), "SOURCE_ID_MISSING", "/sources/source_id", "source_id required")
        _require(source_id not in seen_ids, "SOURCE_ID_DUPLICATE", f"/sources/{source_id}", "source_id duplicate")
        _require(SOURCE_ID_RE.fullmatch(source_id) is not None, "SOURCE_ID_INVALID", f"/sources/{source_id}", "source_id must be source-id pattern")
        seen_ids.add(source_id)

        disposition = source.get("disposition")
        title = _require_non_empty(
            source.get("title"),
            "SOURCE_TITLE_MISSING",
            f"/sources/{source_id}/title",
            "title required",
        )
        source_kind = _require_non_empty(
            source.get("source_kind"),
            "SOURCE_KIND_MISSING",
            f"/sources/{source_id}/source_kind",
            "source_kind required",
        )

        if disposition == "excluded":
            reason_code = _require_non_empty(
                source.get("reason_code"),
                "SOURCE_REASON_CODE_MISSING",
                f"/sources/{source_id}/reason_code",
                "reason_code required",
            )
            _require(
                reason_code in {
                    "duplicate",
                    "out-of-scope",
                    "navigation-only",
                    "obsolete",
                    "generated-alias",
                    "unavailable",
                    "other",
                },
                "SOURCE_REASON_CODE_INVALID",
                f"/sources/{source_id}/reason_code",
                "invalid reason code",
            )
            projected[source_id] = {
                "disposition": "excluded",
                "title": title[:500],
                "source_kind": source_kind,
                "content": {
                    "content_mode": "excluded",
                    "locator": _require_non_empty(
                        source.get("locator"),
                        "SOURCE_EXCLUDED_LOCATOR_MISSING",
                        f"/sources/{source_id}/locator",
                        "locator required",
                    ),
                    "inventory_entry_identity": _make_identity(
                        {
                            "source_id": source_id,
                            "title": title,
                            "rationale": source.get("rationale"),
                        }
                    ),
                },
                "reason_code": reason_code,
                "rationale": _project_limitation_from_exclusion(source_id, source),
            }
            continue

        _require(disposition == "included", "SOURCE_DISPOSITION_INVALID", f"/sources/{source_id}/disposition", "disposition must be included or excluded")
        slices = _require_list(source.get("slices"), f"/sources/{source_id}/slices", "included source must have slices")
        _require(slices, "SOURCE_SLICES_EMPTY", f"/sources/{source_id}/slices", "included source must have non-empty slices")

        selectors: list[dict[str, Any]] = []
        source_external_identity = source.get("external_identity")
        external_identity = None
        if source_external_identity is not None:
            external_identity = _normalize_receipt("external-content", source_external_identity, f"/sources/{source_id}/external_identity")
            _require(external_identity["retrieval_method"] is not None, "SOURCE_EXTERNAL_RECEIPT_INVALID", f"/sources/{source_id}/external_identity", "external identity must contain retrieval metadata")
        source_subject_ids: list[str] = []
        source_losses: list[str] = []
        external_selector_count = 0
        for slice_record in slices:
            selector, is_json_pointer = _project_selector(
                source_id,
                _require_mapping(slice_record, "SLICE_TYPE", f"/sources/{source_id}/slices"),
                loss_renames,
                loss_drop,
                seen_selector_ids,
                source_external_identity,
            )
            if "selected_identity" in selector:
                external_selector_count += 1
            has_json_pointer = has_json_pointer or is_json_pointer
            for sid in selector["subject_ids"]:
                _require(sid in valid_subjects, "SLICE_SUBJECT_UNKNOWN", f"/sources/{source_id}/selectors/{selector['selector_id']}/subject_ids/{sid}", "subject id missing in scope-bound subjects")
                _require(
                    sid not in source_subject_ids,
                    "SOURCE_SUBJECT_ID_DUPLICATE",
                    f"/sources/{source_id}/selectors/{selector['selector_id']}/subject_ids/{sid}",
                    "source subject_ids contains duplicates",
                )
                source_subject_ids.append(sid)
            for lid in selector["loss_ids"]:
                if lid in LOSS_DROP:
                    continue
                _require(lid in valid_losses, "SLICE_LOSS_UNKNOWN", f"/sources/{source_id}/selectors/{selector['selector_id']}/loss_ids/{lid}", "loss id unknown")
                _require(
                    lid not in source_losses,
                    "SOURCE_LOSS_ID_DUPLICATE",
                    f"/sources/{source_id}/selectors/{selector['selector_id']}/loss_ids/{lid}",
                    "source loss_ids contains duplicates",
                )
                source_losses.append(lid)
            selectors.append(selector)
        if external_identity is not None:
            _require(
                external_selector_count in {0, 1},
                "SOURCE_SELECTOR_EXTERNAL_RECEIPT_MISMATCH",
                f"/sources/{source_id}/slices",
                "exact source with external identity must have zero or one selected_identity",
            )

        content = _as_content(source, source_id)
        if content["content_mode"] == "metadata-only":
            _require(not selectors, "SOURCE_SELECTOR_MISMATCH", f"/sources/{source_id}/selectors", "metadata-only sources must not have selectors")
        else:
            _require(selectors, "SOURCE_SELECTOR_MISSING", f"/sources/{source_id}/selectors", "non-metadata sources require selectors")
            _require(content["content_mode"] == "external-content", "SOURCE_CONTENT_MODE_INVALID", f"/sources/{source_id}/content_mode", "non-metadata source must be external-content")

            if external_identity is not None:
                if content["receipt"]["raw_sha256"] != external_identity["raw_sha256"]:
                    _require(False, "SOURCE_EXTERNAL_IDENTITY_MISMATCH", f"/sources/{source_id}/external_identity", "external_identity raw_sha256 mismatch with source external_content raw_sha256")
                if content["receipt"]["raw_bytes"] != external_identity["raw_bytes"]:
                    _require(False, "SOURCE_EXTERNAL_IDENTITY_MISMATCH", f"/sources/{source_id}/external_identity", "external_identity raw_bytes mismatch with source external_content raw_bytes")
                _require(
                    source.get("external_receipt") is None,
                    "SOURCE_EXTERNAL_IDENTITY_DUPLICATE",
                    f"/sources/{source_id}/external_identity",
                    "source external_identity must be used by slice selected_identity, not duplicated",
                )

        projected[source_id] = {
            "disposition": "included",
            "title": title[:500],
            "source_kind": source_kind,
            "content": content,
            "selectors": selectors,
            "subject_ids": source_subject_ids,
            "loss_ids": source_losses,
        }
        referenced_losses.update(source_losses)

    return projected, referenced_losses, has_json_pointer


def convert_catalog_v10_to_v11(
    catalog: Any,
    *,
    provider: Any,
    authority: Any,
    authority_projection: Any,
    scope_catalog: Any,
    inventory_projection: Any,
) -> dict[str, Any]:
    """Convert a parsed official-document-source-catalog@1.0 payload to @1.1."""

    input_catalog = _safe_copy(_require_mapping(catalog, "CATALOG_TYPE", "/catalog"))

    _require(input_catalog.get("schema_version") == "1.0", "CATALOG_VERSION_MISMATCH", "/catalog/schema_version", "catalog must be schema 1.0")
    _require(input_catalog.get("contract_name") == CONTRACT_NAME, "CATALOG_CONTRACT_MISMATCH", "/catalog/contract_name", "contract_name mismatch")

    sources = _require_list(input_catalog.get("sources"), "CATALOG_SOURCES_TYPE", "/sources")
    reviewed_exclusions = _require_list(input_catalog.get("reviewed_exclusions"), "CATALOG_REVIEWED_EXCLUSIONS_TYPE", "/reviewed_exclusions")
    losses = _require_list(input_catalog.get("losses"), "CATALOG_LOSSES_TYPE", "/losses")
    limitations = _require_list(input_catalog.get("limitations"), "CATALOG_LIMITATIONS_TYPE", "/limitations")
    blockers = _require_list(input_catalog.get("blockers"), "CATALOG_BLOCKERS_TYPE", "/blockers")
    version_scope_input = input_catalog.get("version_scope")
    _require(version_scope_input is not None, "CATALOG_VERSION_SCOPE_MISSING", "/version_scope", "version_scope required")
    inventory_locator = _require_non_empty(input_catalog.get("inventory_locator"), "CATALOG_INVENTORY_LOCATOR_MISSING", "/inventory_locator", "inventory_locator required")
    _require(HTTPS_URL_RE.match(inventory_locator) is not None, "CATALOG_INVENTORY_LOCATOR_INVALID", "/inventory_locator", "inventory_locator must be https URL")
    _require(isinstance(input_catalog.get("upstream_universe_complete"), bool), "CATALOG_UPSTREAM_TYPE", "/upstream_universe_complete", "must be bool")

    authority_id = _extract_authority(authority)
    provider_id, provider_input_id = _extract_provider(provider)
    authority_projection = _require_mapping(authority_projection, "AUTHORITY_PROJECTION_TYPE", "/authority_projection")
    canonical_urls = _require_list(
        authority_projection.get("canonical_urls"),
        "AUTHORITY_CANONICAL_URLS_TYPE",
        "/authority_projection/canonical_urls",
    )
    canonical_urls = [
        str(item)
        for item in canonical_urls
        if isinstance(item, str) and HTTPS_URL_RE.match(item) is not None
    ]
    _require(canonical_urls, "AUTHORITY_CANONICAL_URLS_MISSING", "/authority_projection/canonical_urls", "non-empty canonical_urls required")
    inventory_projection_map = _require_mapping(inventory_projection, "INVENTORY_PROJECTION_TYPE", "/inventory_projection")
    projected_locator = _require_non_empty(
        inventory_projection_map.get("locator"),
        "INVENTORY_PROJECTION_LOCATOR_MISSING",
        "/inventory_projection/locator",
        "locator required",
    )
    _require(
        HTTPS_URL_RE.match(projected_locator) is not None,
        "INVENTORY_PROJECTION_LOCATOR_INVALID",
        "/inventory_projection/locator",
        "inventory_projection locator must be https URL",
    )
    authority_root = _extract_authority_root(authority_projection, projected_locator)

    for source in sources:
        if not isinstance(source, dict):
            continue
        source_locator = source.get("locator")
        _require(
            _is_str(source_locator),
            "SOURCE_LOCATOR_MISSING",
            "/sources/locator",
            "source locator required",
        )
        _require_locator_in_authority_urls(
            canonical_urls,
            source_locator,
            f"/sources/{source.get('source_id')}/locator",
        )

    for exclusion in reviewed_exclusions:
        if not isinstance(exclusion, dict):
            continue
        exclusion_locator = exclusion.get("locator")
        source_id = exclusion.get("source_id")
        _require(
            _is_str(exclusion_locator),
            "REVIEWED_EXCLUSION_LOCATOR_MISSING",
            "/reviewed_exclusions/locator",
            "reviewed exclusion locator required",
        )
        _require_locator_in_authority_urls(
            canonical_urls,
            exclusion_locator,
            f"/reviewed_exclusions/{source_id}/locator",
        )

    version_scope = _project_version_scope(
        _safe_copy(version_scope_input),
        _safe_copy(authority_projection),
    )

    # Scope-bound subjects only. Catalog subjects are ignored unless provider-bound.
    scope_subjects = _build_scope_subjects(scope_catalog, provider_input_id)
    catalog_subjects = _build_catalog_subjects(input_catalog.get("subjects"))
    _require(
        set(catalog_subjects.keys()) == set(scope_subjects.keys()),
        "SUBJECT_SET_MISMATCH",
        "/subjects",
        "catalog subjects and scope provider subjects must match exactly",
    )

    output_subjects: dict[str, Any] = {}
    for subject_id in scope_subjects:
        output_subjects[subject_id] = {
            "title": catalog_subjects[subject_id]["title"],
            "category": catalog_subjects[subject_id]["category"],
            "requirement_strength": catalog_subjects[subject_id]["requirement_strength"],
            "statement": scope_subjects[subject_id]["statement"],
        }

    projected_inventory_locator, projected_inventory_identity = _project_inventory_projection(inventory_projection, authority_root)
    _require(projected_inventory_locator == projected_locator, "INVENTORY_LOCATOR_MISMATCH", "/inventory_projection/locator", "inventory_projection locator does not match projected authority root")

    # Convert losses first to build references and renamed identifiers.
    projected_losses: dict[str, Any] = {}
    for loss in losses:
        projected = _project_loss(_require_mapping(loss, "LOSS_TYPE", "/losses"), LOSS_RENAME)
        if projected is None:
            continue
        loss_id, payload = projected
        _require(loss_id not in projected_losses, "LOSS_ID_DUPLICATE", f"/losses/{loss_id}", "duplicate loss_id after mapping")
        projected_losses[loss_id] = payload

    # Convert catalog exclusions to map entries and add duplicate detection.
    excluded: dict[str, Any] = {}
    for exclusion in reviewed_exclusions:
        exc = _require_mapping(exclusion, "REVIEWED_EXCLUSION_TYPE", "/reviewed_exclusions")
        source_id = _require_non_empty(exc.get("source_id"), "REVIEWED_EXCLUSION_SOURCE_ID_MISSING", "/reviewed_exclusions/source_id", "source_id required")
        _require(SOURCE_ID_RE.fullmatch(source_id) is not None, "REVIEWED_EXCLUSION_SOURCE_ID_INVALID", f"/reviewed_exclusions/{source_id}", "source_id must be source-id pattern")
        _require(source_id not in excluded, "REVIEWED_EXCLUSION_SOURCE_ID_DUPLICATE", f"/reviewed_exclusions/{source_id}", "duplicate reviewed_exclusion source_id")
        reason_code = _require_non_empty(
            exc.get("reason_code"),
            "REVIEWED_EXCLUSION_REASON_MISSING",
            f"/reviewed_exclusions/{source_id}/reason_code",
            "reason_code required",
        )
        _require(
            reason_code in {
                "duplicate",
                "out-of-scope",
                "navigation-only",
                "obsolete",
                "generated-alias",
                "unavailable",
                "other",
            },
            "REVIEWED_EXCLUSION_REASON_INVALID",
            f"/reviewed_exclusions/{source_id}/reason_code",
            "invalid exclusion reason_code",
        )
        title = _require_non_empty(
            exc.get("title"),
            "REVIEWED_EXCLUSION_TITLE_MISSING",
            f"/reviewed_exclusions/{source_id}/title",
            "title required",
        )
        locator = _require_non_empty(
            exc.get("locator"),
            "REVIEWED_EXCLUSION_LOCATOR_MISSING",
            f"/reviewed_exclusions/{source_id}/locator",
            "locator required",
        )
        _require(HTTPS_URL_RE.match(locator) is not None, "REVIEWED_EXCLUSION_LOCATOR_INVALID", f"/reviewed_exclusions/{source_id}/locator", "locator must be https URL")

        excluded[source_id] = {
            "disposition": "excluded",
            "title": title[:500],
            "source_kind": "other",
            "content": {
                "content_mode": "excluded",
                "locator": locator,
                "inventory_entry_identity": _make_identity(
                    {
                        "source_id": source_id,
                        "title": title,
                        "reason_code": reason_code,
                        "rationale": _project_limitation_from_exclusion(source_id, exc),
                    }
                ),
            },
            "reason_code": reason_code,
            "rationale": _project_limitation_from_exclusion(source_id, exc),
        }

    # Validate source ids and duplicate closure across included+excluded.
    seen_source_ids: set[str] = set(excluded)
    for source in sources:
        sid = source.get("source_id") if isinstance(source, dict) else None
        _require(_is_str(sid), "SOURCE_ID_MISSING", "/sources/source_id", "source_id required")
        _require(sid not in seen_source_ids, "SOURCE_ID_DUPLICATE", f"/sources/{sid}", "source_id duplicate with exclusions")
        _require(SOURCE_ID_RE.fullmatch(sid) is not None, "SOURCE_ID_INVALID", f"/sources/{sid}", "source_id must be source-id pattern")
        seen_source_ids.add(sid)

    projected_sources, selector_losses, has_json_pointer = _project_sources(
        sources,
        LOSS_RENAME,
        LOSS_DROP,
        valid_subjects=set(scope_subjects),
        valid_losses=set(projected_losses),
    )

    projected_sources.update(excluded)

    # subject and loss closure checks (bidirectional)
    for source_id, source_payload in projected_sources.items():
        if source_payload["disposition"] != "included":
            continue
        _require(source_payload["subject_ids"], "SOURCE_SUBJECTS_EMPTY", f"/discovered_sources/{source_id}/subject_ids", "included source must have subject bindings")
        selector_subject_union: set[str] = set()
        for selector in source_payload["selectors"]:
            selector_subject_union.update(selector["subject_ids"])
        _require(
            selector_subject_union == set(source_payload["subject_ids"]),
            "SOURCE_SUBJECT_CLOSURE_MISMATCH",
            f"/discovered_sources/{source_id}/subject_ids",
            "source.subject_ids must equal selector subject closure",
        )
        for selector in source_payload["selectors"]:
            for lid in selector["loss_ids"]:
                _require(lid in projected_losses, "SOURCE_SELECTOR_LOSS_MISSING", f"/discovered_sources/{source_id}/selectors/{selector['selector_id']}/loss_ids", "selector loss_id missing")
        for lid in source_payload["loss_ids"]:
            _require(lid in projected_losses, "SOURCE_LOSS_MISSING", f"/discovered_sources/{source_id}/loss_ids/{lid}", "source loss_id not projected")

    # All scope-bound subject refs in losses must also exist as declared subjects.
    for loss_payload in projected_losses.values():
        for source_ref in loss_payload["affected_source_ids"]:
            _require(source_ref in projected_sources, "LOSS_AFFECTED_SOURCE_MISSING", "/losses/affected_source_ids", "loss references missing source")
            _require(loss_payload["affected_source_ids"].count(source_ref) == 1, "LOSS_AFFECTED_SOURCE_DUPLICATE", "/losses/affected_source_ids", "affected_source_ids contains duplicates")

    # selector/loss ids referenced by any source must exist and duplicate closure is an error by construction.
    for lid in selector_losses:
        _require(lid in projected_losses, "LOSS_REFERENCE_MISSING", "/losses", "loss references required by selectors must exist")

    out_limitations = [_normalize_text(item) for item in limitations if _is_str(item)]
    if has_json_pointer:
        if LIMITATION_CLEAN_TEXT not in out_limitations:
            out_limitations.append(LIMITATION_CLEAN_TEXT)

    inventory_identity = _safe_copy(projected_inventory_identity)
    projected_snapshot_identity: dict[str, Any] | None = None

    if version_scope["kind"] == "latest-at-retrieval":
        projected_snapshot_identity = _snapshot_from_sources_and_exclusions(projected_sources)
        version_scope["snapshot_identity"] = projected_snapshot_identity
    if version_scope["kind"] != "latest-at-retrieval":
        version_scope["snapshot_identity"] = None
        version_scope["retrieved_utc"] = None

    projected_authority_revision = _project_authority_revision(
        input_catalog.get("authority_revision"),
        version_scope["kind"],
        projected_inventory_identity,
        projected_snapshot_identity,
    )

    discovered_sources_payload = canonical_projection_bytes({sid: projected_sources[sid] for sid in sorted(projected_sources)})
    discovery_processor = {
        "processor_id": "official-document-source-catalog-migrator",
        "processor_version": "2026.07",
        "assurance_mode": "unverified",
        "implementation_ref": None,
        "configuration_ref": None,
        "dependency_lock_ref": None,
        "input_sha256": inventory_identity["sha256"],
        "output_sha256": _sha256_hex(discovered_sources_payload),
        "attestation_id": None,
        "deterministic": True,
    }

    output: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "authority_id": authority_id,
        "provider_id": provider_id,
        "authority_root": authority_root,
        "version_scope": version_scope,
        "authority_revision": projected_authority_revision,
        "upstream_universe_complete": bool(input_catalog["upstream_universe_complete"]),
        "inventory_locator": projected_inventory_locator,
        "inventory_identity": inventory_identity,
        "discovery_processor": discovery_processor,
        "discovered_sources": {sid: projected_sources[sid] for sid in sorted(projected_sources)},
        "subjects": output_subjects,
        "losses": projected_losses,
        "limitations": out_limitations,
        "blockers": _project_blockers(blockers),
    }

    _require(output["authority_revision"] != "", "AUTHORITY_REVISION_MISSING", "/authority_revision", "authority_revision cannot be empty")
    return output
