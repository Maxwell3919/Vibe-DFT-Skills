#!/usr/bin/env python3
"""Validate official-document corpus, slices, licensing, and Skill coverage.

The five JSON contracts are deliberately split so that source discovery,
document transformation, redistribution review, and Skill claim coverage
remain separate gates.  This validator closes the cross-record invariants
which JSON Schema cannot express.  It is offline-only and reads strict JSON.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from pathlib import PurePosixPath
import re
import stat
import sys
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

import official_source_authorities
import interface_registry
import skill_registry
import software_registry
import strict_json
import validate_contract
from registry_yaml import load_yaml_strict


EXIT_PASS = 0
EXIT_INVALID = 2
EXIT_INCOMPLETE = 3
MAX_RECORD_BYTES = 64 * 1024 * 1024
MAX_CONTENT_BYTES = 64 * 1024 * 1024
STATUS_RANK = {"blocked": 0, "partial": 1, "complete": 2}
PROCESSOR_KINDS = {"enumerator", "transformer", "extractor"}
PROCESSOR_REF_FIELDS = (
    "implementation_ref",
    "configuration_ref",
    "dependency_lock_ref",
)
SELECTOR_KINDS = {
    "heading",
    "byte-range",
    "json-pointer",
    "line-range",
    "page-range",
    "whole-source",
    "source-symbol",
    "other",
}
LICENSE_OBLIGATION_FIELDS = (
    "attribution_required",
    "notice_required",
    "modified_content_marking_required",
    "share_alike_required",
    "source_offer_required",
)
SOURCE_IDENTITY_AGGREGATE_DOMAIN = (
    b"VIBE-OFFICIAL-SOURCE-IDENTITY-AGGREGATE-v1\0"
)


def _pack_source_id(*parts: object) -> str:
    """Mirror the bounded builder ID projection for official inventory units."""

    raw = "-".join(str(item) for item in parts if str(item))
    slug = re.sub(r"[^A-Za-z0-9._:-]+", "-", raw).strip("-.:").lower()
    if len(slug) > 120:
        suffix = hashlib.sha256(slug.encode("utf-8")).hexdigest()[:16]
        slug = f"{slug[:103].rstrip('-.:')}-{suffix}"
    return slug


def _source_identity_aggregate_sha256(
    corpus: dict[str, Any],
) -> str:
    """Recompute a rolling declarative corpus identity from record evidence."""

    projection = {
        "authority_id": corpus["authority_id"],
        "provider_id": corpus["provider_id"],
        "retrieved_utc": corpus["version_scope"]["retrieved_utc"],
        "included_sources": sorted(
            (
                {
                    "source_id": source["source_id"],
                    "locator": source["locator"],
                    "identity": {
                        "kind": source["identity"]["kind"],
                        "value": source["identity"]["value"],
                        "raw_sha256": source["identity"]["raw_sha256"],
                        "raw_bytes": source["identity"]["raw_bytes"],
                    },
                }
                for source in corpus["included_sources"]
            ),
            key=lambda source: source["source_id"],
        ),
        "reviewed_exclusions": sorted(
            (
                {
                    "source_id": exclusion["source_id"],
                    "reason_code": exclusion["reason_code"],
                }
                for exclusion in corpus["reviewed_exclusions"]
            ),
            key=lambda exclusion: exclusion["source_id"],
        ),
    }
    raw = json.dumps(
        projection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(
        SOURCE_IDENTITY_AGGREGATE_DOMAIN + raw
    ).hexdigest()


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    location: str
    message: str


@dataclass(frozen=True)
class LoadedRecord:
    path: Path
    raw_sha256: str
    data: dict[str, Any]


@dataclass(frozen=True)
class ValidationResult:
    findings: tuple[Finding, ...]
    assurance_status: str
    externalized_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class PortableValidationContext:
    """Explicit roots and missing-byte receipts for an unpacked distribution."""

    repository_root: Path
    contracts_directory: Path
    interface_registry_path: Path
    authority_registry_path: Path
    software_registry_path: Path
    skill_registry_path: Path
    consumer_registry_path: Path
    externalized_receipts: Mapping[str, Mapping[str, object]]
    used_externalized_paths: set[str] = field(
        default_factory=set,
        compare=False,
        repr=False,
    )


@dataclass(frozen=True)
class ExternalizedArtifact:
    path: str
    sha256: str
    size: int


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _finding(code: str, location: str, message: str) -> Finding:
    return Finding(code=code, location=location, message=message)


def _deduplicate_findings(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    return tuple(sorted(set(findings)))


def authority_version_scope_compatible(
    corpus_scope: object,
    registered_scopes: object,
) -> bool:
    """Return whether an output corpus scope has an exact registry witness.

    The corpus contract and central authority registry intentionally use
    different names for two equivalent identity classes: an immutable
    ``revision`` is registered as ``exact``, while a ``release-line`` is
    registered as ``release-series``.  Compatibility is value-exact; this
    function never guesses aliases, parses versions, or treats a range as an
    exact identity.
    """

    if not isinstance(corpus_scope, dict) or not isinstance(
        registered_scopes, list
    ):
        return False
    kind = corpus_scope.get("kind")
    value = corpus_scope.get("value")
    if kind in {"exact", "revision"}:
        expected_scope = "exact"
        expected_field = "exact_version"
    elif kind == "release-line":
        expected_scope = "release-series"
        expected_field = "release_series"
    elif kind in {"latest-at-retrieval", "unversioned"}:
        expected_scope = kind
        expected_field = None
    else:
        return False
    for registered in registered_scopes:
        if (
            not isinstance(registered, dict)
            or registered.get("scope") != expected_scope
        ):
            continue
        if expected_field is None:
            return value is None
        if (
            isinstance(value, str)
            and value
            and registered.get(expected_field) == value
        ):
            return True
    return False


def source_version_scope_compatible(
    source_scope: object,
    corpus_scope: object,
    *,
    raw_sha256: object,
) -> bool:
    """Require an exact static scope or a byte-bound rolling source scope."""

    if not isinstance(source_scope, dict) or not isinstance(corpus_scope, dict):
        return False
    kind = corpus_scope.get("kind")
    if kind in {"exact", "revision", "release-line", "unversioned"}:
        return source_scope == corpus_scope
    if kind != "latest-at-retrieval":
        return False
    snapshot = source_scope.get("snapshot_identity")
    return (
        source_scope.get("kind") == "latest-at-retrieval"
        and source_scope.get("value") is None
        and source_scope.get("retrieved_utc")
        == corpus_scope.get("retrieved_utc")
        and isinstance(snapshot, dict)
        and isinstance(raw_sha256, str)
        and snapshot.get("content_sha256") == raw_sha256
    )


def _externalized_artifact(
    root: Path,
    relative: str,
    portable_context: PortableValidationContext | None,
) -> ExternalizedArtifact | None:
    if portable_context is None:
        return None
    try:
        if root.resolve(strict=True) != portable_context.repository_root.resolve(
            strict=True
        ):
            return None
    except OSError:
        return None
    receipt = portable_context.externalized_receipts.get(relative)
    if (
        not isinstance(receipt, Mapping)
        or set(receipt) != {"path", "sha256", "size"}
        or receipt.get("path") != relative
        or not _valid_sha256(receipt.get("sha256"))
        or not isinstance(receipt.get("size"), int)
        or isinstance(receipt.get("size"), bool)
        or receipt["size"] < 0
        or receipt["size"] > MAX_CONTENT_BYTES
    ):
        return None
    portable_context.used_externalized_paths.add(relative)
    return ExternalizedArtifact(
        path=relative,
        sha256=str(receipt["sha256"]),
        size=int(receipt["size"]),
    )


def _artifact_sha256(raw: bytes | ExternalizedArtifact) -> str:
    if isinstance(raw, ExternalizedArtifact):
        return raw.sha256
    return hashlib.sha256(raw).hexdigest()


def _artifact_size(raw: bytes | ExternalizedArtifact) -> int:
    if isinstance(raw, ExternalizedArtifact):
        return raw.size
    return len(raw)


def _externalized_slice_selection_error(
    artifact: ExternalizedArtifact,
    *,
    selector_kind: object,
    start: int | None,
    end: int | None,
    content_sha256: object,
) -> str | None:
    if selector_kind == "byte-range":
        if (
            start is None
            or end is None
            or start >= end
            or end > artifact.size
        ):
            return "SLICE_RANGE_INVALID"
    elif (
        selector_kind == "whole-source"
        and content_sha256 != artifact.sha256
    ):
        return "SLICE_CONTENT_HASH_MISMATCH"
    return None


def _safe_local_bytes(
    root: Path,
    relative: object,
    *,
    location: str,
    findings: list[Finding],
    failure_code: str,
    portable_context: PortableValidationContext | None = None,
) -> bytes | ExternalizedArtifact | None:
    if not isinstance(relative, str):
        findings.append(
            _finding(failure_code, location, "local locator must be a relative path")
        )
        return None
    pure = PurePosixPath(relative)
    if (
        pure.is_absolute()
        or not pure.parts
        or "\\" in relative
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        findings.append(
            _finding(failure_code, location, "local locator escapes its source root")
        )
        return None
    try:
        root_resolved = root.resolve(strict=True)
        current = root_resolved
        for part in pure.parts:
            current = current / part
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ValueError("symlink path component is forbidden")
        resolved = current.resolve(strict=True)
        if not resolved.is_relative_to(root_resolved):
            raise ValueError("resolved path escapes its source root")
        raw = strict_json.read_bytes_bounded(
            resolved,
            relative,
            max_bytes=MAX_CONTENT_BYTES,
        )
    except FileNotFoundError as exc:
        externalized = _externalized_artifact(
            root,
            relative,
            portable_context,
        )
        if externalized is not None:
            return externalized
        findings.append(
            _finding(
                failure_code,
                location,
                "local artifact is unavailable or unsafe "
                f"({exc.__class__.__name__})",
            )
        )
        return None
    except (OSError, ValueError, strict_json.StrictJSONError) as exc:
        findings.append(
            _finding(
                failure_code,
                location,
                "local artifact is unavailable or unsafe "
                f"({exc.__class__.__name__})",
            )
        )
        return None
    return raw


def _valid_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_json_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _central_file_ref_errors(
    reference: object,
    *,
    location: str,
    root: Path,
    portable_context: PortableValidationContext | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        return [f"{location}: expected exactly path and sha256"]
    path = reference.get("path")
    expected = reference.get("sha256")
    if not isinstance(path, str) or not _valid_sha256(expected):
        return [f"{location}: invalid path or sha256"]
    local_findings: list[Finding] = []
    raw = _safe_local_bytes(
        root,
        path,
        location=location,
        findings=local_findings,
        failure_code="CENTRAL_TRUST_ARTIFACT_INVALID",
        portable_context=portable_context,
    )
    if local_findings or raw is None:
        errors.append(f"{location}: local artifact is unavailable or unsafe")
    elif _artifact_sha256(raw) != expected:
        errors.append(f"{location}: sha256 does not match exact local bytes")
    return errors


def _is_license_terms_content_path(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parts = PurePosixPath(value).parts
    return (
        len(parts) >= 6
        and parts[0] == "skills"
        and bool(parts[1])
        and all(
            character.islower()
            or character.isdigit()
            or character == "-"
            for character in parts[1]
        )
        and parts[1][0].isalnum()
        and parts[1][-1].isalnum()
        and parts[2:5]
        == ("references", "official-source-pack", "license-terms")
    )


def _consumer_registry_errors(
    data: object,
    *,
    skills: dict[str, Any],
    authorities: dict[str, dict[str, Any]],
    root: Path,
    portable_context: PortableValidationContext | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: expected a mapping"]
    expected_root = {
        "schema_version",
        "default_policy",
        "bindings",
        "processors",
        "resolver_trust",
        "license_trust",
    }
    if set(data) != expected_root:
        errors.append("<root>: fields must exactly match the registry contract")
        return errors
    if data["schema_version"] != "1.0":
        errors.append("schema_version: expected '1.0'")
    if data["default_policy"] != "deny":
        errors.append("default_policy: only deny is supported")

    bindings = data["bindings"]
    if not isinstance(bindings, list):
        errors.append("bindings: expected a list")
    else:
        expected_binding_fields = {
            "binding_id",
            "consumer_skill_id",
            "consumer_lifecycle",
            "consumer_path",
            "authority_id",
            "provider_id",
            "purpose",
            "claim_ceiling",
        }
        seen_ids: set[str] = set()
        seen_pairs: set[tuple[str, str, str]] = set()
        valid_bound_active_authorities: set[str] = set()
        for index, binding in enumerate(bindings):
            location = f"bindings/{index}"
            if not isinstance(binding, dict) or set(binding) != expected_binding_fields:
                errors.append(f"{location}: fields must exactly match the binding contract")
                continue
            binding_id = binding["binding_id"]
            binding_id_valid = (
                isinstance(binding_id, str)
                and bool(binding_id)
                and binding_id not in seen_ids
            )
            if not binding_id_valid:
                errors.append(f"{location}/binding_id: invalid or duplicate")
            else:
                seen_ids.add(binding_id)
            skill_id = binding["consumer_skill_id"]
            skill = skills.get(skill_id)
            consumer_valid = not (
                skill is None
                or binding["consumer_lifecycle"] != skill.get("lifecycle")
                or binding["consumer_path"] != skill.get("path")
                or skill.get("lifecycle") not in {"active", "development"}
            )
            if not consumer_valid:
                errors.append(
                    f"{location}: consumer does not match an active or development "
                    "skill-registry entry"
                )
            authority = authorities.get(binding["authority_id"])
            authority_valid = not (
                authority is None
                or binding["provider_id"] != authority.get("provider_id")
                or authority.get("lifecycle") != "active"
            )
            if not authority_valid:
                errors.append(
                    f"{location}: authority/provider does not match an active "
                    "official-source authority"
                )
            pair = (
                str(skill_id),
                str(binding["authority_id"]),
                str(binding["provider_id"]),
            )
            pair_valid = pair not in seen_pairs
            if not pair_valid:
                errors.append(f"{location}: duplicate consumer/authority/provider binding")
            seen_pairs.add(pair)
            purpose_valid = binding["purpose"] == "official-document-coverage"
            if not purpose_valid:
                errors.append(f"{location}/purpose: unsupported purpose")
            claim_ceiling_valid = (
                binding["claim_ceiling"] == "registered-skill-scope"
            )
            if not claim_ceiling_valid:
                errors.append(
                    f"{location}/claim_ceiling: binding cannot widen Skill scope"
                )
            if (
                binding_id_valid
                and consumer_valid
                and authority_valid
                and pair_valid
                and purpose_valid
                and claim_ceiling_valid
            ):
                valid_bound_active_authorities.add(binding["authority_id"])

        active_authority_ids = {
            authority_id
            for authority_id, authority in authorities.items()
            if isinstance(authority, dict)
            and authority.get("lifecycle") == "active"
        }
        dangling_active_authorities = (
            active_authority_ids - valid_bound_active_authorities
        )
        if dangling_active_authorities:
            errors.append(
                "bindings: every active official-source authority must be used "
                "by at least one fully valid central consumer binding "
                f"(unbound count={len(dangling_active_authorities)})"
            )

    processors = data["processors"]
    if not isinstance(processors, dict):
        errors.append("processors: expected a mapping")
    else:
        expected_processor_fields = {
            "kind",
            "version",
            *PROCESSOR_REF_FIELDS,
            "attested_runs",
        }
        for processor_id, processor in processors.items():
            location = f"processors/{processor_id}"
            if (
                not isinstance(processor_id, str)
                or not isinstance(processor, dict)
                or set(processor) != expected_processor_fields
            ):
                errors.append(f"{location}: invalid processor entry")
                continue
            if processor["kind"] not in PROCESSOR_KINDS:
                errors.append(f"{location}/kind: unsupported processor kind")
            if not isinstance(processor["version"], str) or not processor["version"]:
                errors.append(f"{location}/version: expected a nonempty string")
            for field in PROCESSOR_REF_FIELDS:
                errors.extend(
                    _central_file_ref_errors(
                        processor[field],
                        location=f"{location}/{field}",
                        root=root,
                        portable_context=portable_context,
                    )
                )
            runs = processor["attested_runs"]
            run_ids: list[object] = []
            if not isinstance(runs, list):
                errors.append(f"{location}/attested_runs: expected a list")
                continue
            for run_index, run in enumerate(runs):
                run_location = f"{location}/attested_runs/{run_index}"
                if (
                    not isinstance(run, dict)
                    or set(run)
                    != {
                        "attestation_id",
                        "input_sha256",
                        "output_sha256",
                        "attestation_ref",
                    }
                    or not isinstance(run.get("attestation_id"), str)
                    or not run["attestation_id"]
                    or not _valid_sha256(run.get("input_sha256"))
                    or not _valid_sha256(run.get("output_sha256"))
                ):
                    errors.append(f"{run_location}: invalid attested input/output run")
                    continue
                run_ids.append(run["attestation_id"])
                errors.extend(
                    _central_file_ref_errors(
                        run["attestation_ref"],
                        location=f"{run_location}/attestation_ref",
                        root=root,
                        portable_context=portable_context,
                    )
                )
            if len(run_ids) != len(set(run_ids)):
                errors.append(f"{location}/attested_runs: duplicate attestation IDs")

    resolver_trust = data["resolver_trust"]
    if not isinstance(resolver_trust, dict):
        errors.append("resolver_trust: expected a mapping")
    else:
        expected_resolver_fields = {
            "authority_id",
            "resolver_id",
            "trust_mode",
            "evidence_sha256",
            *PROCESSOR_REF_FIELDS,
            "platform_attestation_ref",
            "attested_selections",
        }
        for trust_id, trust in resolver_trust.items():
            location = f"resolver_trust/{trust_id}"
            if (
                not isinstance(trust_id, str)
                or not isinstance(trust, dict)
                or set(trust) != expected_resolver_fields
            ):
                errors.append(f"{location}: invalid resolver trust entry")
                continue
            if trust["authority_id"] not in authorities:
                errors.append(f"{location}/authority_id: unknown authority")
            if (
                not isinstance(trust["resolver_id"], str)
                or not trust["resolver_id"]
                or trust["trust_mode"]
                not in {"central-pinned", "platform-attested"}
            ):
                errors.append(f"{location}: invalid resolver identity or trust mode")
            evidence = trust["evidence_sha256"]
            if (
                not isinstance(evidence, list)
                or not evidence
                or len(evidence) != len(set(evidence))
                or not all(_valid_sha256(item) for item in evidence)
            ):
                errors.append(f"{location}/evidence_sha256: invalid evidence allowlist")
            for field in PROCESSOR_REF_FIELDS:
                errors.extend(
                    _central_file_ref_errors(
                        trust[field],
                        location=f"{location}/{field}",
                        root=root,
                        portable_context=portable_context,
                    )
                )
            attestation = trust["platform_attestation_ref"]
            if trust["trust_mode"] == "platform-attested":
                errors.extend(
                    _central_file_ref_errors(
                        attestation,
                        location=f"{location}/platform_attestation_ref",
                        root=root,
                        portable_context=portable_context,
                    )
                )
            elif attestation is not None:
                errors.append(
                    f"{location}/platform_attestation_ref: central-pinned resolver "
                    "must not claim a platform attestation"
                )
            selections = trust["attested_selections"]
            selection_ids: list[object] = []
            expected_selection_fields = {
                "attestation_id",
                "source_id",
                "raw_sha256",
                "raw_bytes",
                "selector",
                "selected_sha256",
                "selected_bytes",
                "attestation_ref",
            }
            if not isinstance(selections, list):
                errors.append(f"{location}/attested_selections: expected a list")
                continue
            for selection_index, selection in enumerate(selections):
                selection_location = (
                    f"{location}/attested_selections/{selection_index}"
                )
                selector = (
                    selection.get("selector")
                    if isinstance(selection, dict)
                    else None
                )
                if (
                    not isinstance(selection, dict)
                    or set(selection) != expected_selection_fields
                    or not isinstance(selection.get("attestation_id"), str)
                    or not selection["attestation_id"]
                    or not isinstance(selection.get("source_id"), str)
                    or not selection["source_id"]
                    or not _valid_sha256(selection.get("raw_sha256"))
                    or not isinstance(selection.get("raw_bytes"), int)
                    or isinstance(selection.get("raw_bytes"), bool)
                    or selection["raw_bytes"] < 1
                    or not isinstance(selector, dict)
                    or set(selector) != {"layer", "kind", "value"}
                    or selector["layer"] not in {"raw-source", "derived-artifact"}
                    or selector["kind"] not in SELECTOR_KINDS
                    or not isinstance(selector["value"], str)
                    or not selector["value"]
                    or not _valid_sha256(selection.get("selected_sha256"))
                    or not isinstance(selection.get("selected_bytes"), int)
                    or isinstance(selection.get("selected_bytes"), bool)
                    or selection["selected_bytes"] < 1
                ):
                    errors.append(
                        f"{selection_location}: invalid exact selection attestation"
                    )
                    continue
                selection_ids.append(selection["attestation_id"])
                errors.extend(
                    _central_file_ref_errors(
                        selection["attestation_ref"],
                        location=f"{selection_location}/attestation_ref",
                        root=root,
                        portable_context=portable_context,
                    )
                )
            if len(selection_ids) != len(set(selection_ids)):
                errors.append(
                    f"{location}/attested_selections: duplicate attestation IDs"
                )

    license_trust = data["license_trust"]
    if not isinstance(license_trust, dict):
        errors.append("license_trust: expected a mapping")
    else:
        expected_trust_fields = {
            "authority_id",
            "reviewer_ids",
            "evidence",
            "platform_attestation_ref",
        }
        for trust_id, trust in license_trust.items():
            location = f"license_trust/{trust_id}"
            if (
                not isinstance(trust_id, str)
                or not isinstance(trust, dict)
                or set(trust) != expected_trust_fields
            ):
                errors.append(f"{location}: invalid license trust entry")
                continue
            if trust["authority_id"] not in authorities:
                errors.append(f"{location}/authority_id: unknown authority")
            reviewer_ids = trust["reviewer_ids"]
            if (
                not isinstance(reviewer_ids, list)
                or not reviewer_ids
                or len(reviewer_ids) != len(set(reviewer_ids))
                or not all(isinstance(item, str) and item for item in reviewer_ids)
            ):
                errors.append(f"{location}/reviewer_ids: expected unique authorized IDs")
            evidence = trust["evidence"]
            if (
                not isinstance(evidence, list)
                or not evidence
                or not all(
                    isinstance(item, dict)
                    and set(item)
                    == {
                        "evidence_id",
                        "locator",
                        "revision",
                        "sha256",
                        "hash_basis",
                        "terms_content_ref",
                    }
                    and isinstance(item["evidence_id"], str)
                    and isinstance(item["locator"], str)
                    and item["locator"].startswith("https://")
                    and isinstance(item["revision"], str)
                    and bool(item["revision"])
                    and _valid_sha256(item["sha256"])
                    and item["hash_basis"] == "exact-terms-content-bytes"
                    and isinstance(item["terms_content_ref"], dict)
                    and item["terms_content_ref"].get("sha256")
                    == item["sha256"]
                    for item in evidence
                )
            ):
                errors.append(f"{location}/evidence: invalid pinned evidence")
            else:
                for evidence_index, item in enumerate(evidence):
                    evidence_location = (
                        f"{location}/evidence/{evidence_index}/"
                        "terms_content_ref"
                    )
                    if not _is_license_terms_content_path(
                        item["terms_content_ref"]["path"]
                    ):
                        errors.append(
                            f"{evidence_location}/path: exact license terms "
                            "must live under a skill official-source-pack "
                            "license-terms directory"
                        )
                    errors.extend(
                        _central_file_ref_errors(
                            item["terms_content_ref"],
                            location=evidence_location,
                            root=root,
                            portable_context=portable_context,
                        )
                    )
            attestation = trust["platform_attestation_ref"]
            if attestation is not None:
                errors.extend(
                    _central_file_ref_errors(
                        attestation,
                        location=f"{location}/platform_attestation_ref",
                        root=root,
                        portable_context=portable_context,
                    )
                )
    return errors


def consumer_registry_validation_errors(
    data: object,
    *,
    skills: dict[str, Any],
    authorities: dict[str, dict[str, Any]],
    root: Path,
    portable_context: PortableValidationContext | None = None,
) -> list[str]:
    """Validate the canonical default-deny consumer and trust registry."""

    return _consumer_registry_errors(
        data,
        skills=skills,
        authorities=authorities,
        root=root,
        portable_context=portable_context,
    )


def _canonical_pack_json_object(
    root: Path,
    relative_path: str,
    *,
    location: str,
    findings: list[Finding],
) -> dict[str, Any] | None:
    raw = _safe_local_bytes(
        root,
        relative_path,
        location=location,
        findings=findings,
        failure_code="GLOBAL_PACK_BINDING_CLOSURE_INVALID",
    )
    if raw is None:
        return None
    try:
        return strict_json.loads_object(
            raw,
            relative_path,
            max_bytes=MAX_RECORD_BYTES,
        )
    except strict_json.StrictJSONError as exc:
        findings.append(
            _finding(
                "GLOBAL_PACK_BINDING_CLOSURE_INVALID",
                location,
                "canonical pack JSON is malformed "
                f"({exc.__class__.__name__})",
            )
        )
        return None


def canonical_pack_binding_closure_findings(
    *,
    root: Path,
    skills: dict[str, Any],
    consumer_registry: dict[str, Any],
) -> tuple[Finding, ...]:
    """Close central consumer pairs against every canonical source-backed pack.

    This repository-wide gate is intentionally separate from
    :func:`validate_files`: the deterministic pack builder validates staged
    output before replacing canonical packs, so consulting the old canonical
    pack set during that transaction would create a migration deadlock.  The
    bundle audit explicitly enables this gate after canonical pack discovery.
    """

    findings: list[Finding] = []
    source_skills: dict[str, str] = {}
    for skill_id, skill in skills.items():
        if (
            isinstance(skill_id, str)
            and isinstance(skill, dict)
            and skill.get("lifecycle") in {"active", "development"}
            and isinstance(skill.get("path"), str)
            and skill["path"] == f"skills/{skill_id}"
        ):
            source_skills[skill_id] = skill["path"]

    bindings = consumer_registry.get("bindings")
    if not isinstance(bindings, list):
        return (
            _finding(
                "GLOBAL_PACK_BINDING_CLOSURE_INVALID",
                "registry/official-document-consumers.yaml/bindings",
                "central consumer bindings are unavailable",
            ),
        )

    central_pairs_by_skill: dict[str, set[tuple[str, str]]] = {
        skill_id: set() for skill_id in source_skills
    }
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        skill_id = binding.get("consumer_skill_id")
        authority_id = binding.get("authority_id")
        provider_id = binding.get("provider_id")
        if (
            skill_id in central_pairs_by_skill
            and isinstance(authority_id, str)
            and isinstance(provider_id, str)
        ):
            central_pairs_by_skill[skill_id].add(
                (authority_id, provider_id)
            )

    pack_pairs_by_skill: dict[str, set[tuple[str, str]]] = {}
    for skill_id, skill_path in sorted(source_skills.items()):
        pack_prefix = (
            f"{skill_path}/references/official-source-pack"
        )
        bundle_path = f"{pack_prefix}/bundle.json"
        bundle_location = f"canonical-packs/{skill_id}/bundle.json"
        bundle = _canonical_pack_json_object(
            root,
            bundle_path,
            location=bundle_location,
            findings=findings,
        )
        if bundle is None:
            continue
        records = bundle.get("records")
        corpus_paths = (
            records.get("corpora") if isinstance(records, dict) else None
        )
        if (
            bundle.get("bundle_type") != "official-document-coverage"
            or bundle.get("schema_version") != "1.0"
            or bundle.get("skill_id") != skill_id
            or not isinstance(corpus_paths, list)
            or not corpus_paths
        ):
            findings.append(
                _finding(
                    "GLOBAL_PACK_BINDING_CLOSURE_INVALID",
                    bundle_location,
                    "canonical pack registration does not expose a nonempty "
                    "corpus set for its registered Skill",
                )
            )
            continue

        pack_pairs: set[tuple[str, str]] = set()
        corpus_pair_count = 0
        for index, corpus_name in enumerate(corpus_paths):
            corpus_location = (
                f"canonical-packs/{skill_id}/corpora/{index}"
            )
            if (
                not isinstance(corpus_name, str)
                or not corpus_name
                or "\\" in corpus_name
            ):
                findings.append(
                    _finding(
                        "GLOBAL_PACK_BINDING_CLOSURE_INVALID",
                        corpus_location,
                        "canonical corpus path is not a safe relative POSIX path",
                    )
                )
                continue
            corpus_pure = PurePosixPath(corpus_name)
            if (
                corpus_pure.is_absolute()
                or corpus_pure.as_posix() != corpus_name
                or any(
                    part in {"", ".", ".."} for part in corpus_pure.parts
                )
            ):
                findings.append(
                    _finding(
                        "GLOBAL_PACK_BINDING_CLOSURE_INVALID",
                        corpus_location,
                        "canonical corpus path escapes or aliases its pack",
                    )
                )
                continue
            corpus = _canonical_pack_json_object(
                root,
                f"{pack_prefix}/{corpus_name}",
                location=corpus_location,
                findings=findings,
            )
            if corpus is None:
                continue
            authority_id = corpus.get("authority_id")
            provider_id = corpus.get("provider_id")
            if not isinstance(authority_id, str) or not isinstance(
                provider_id, str
            ):
                findings.append(
                    _finding(
                        "GLOBAL_PACK_BINDING_CLOSURE_INVALID",
                        corpus_location,
                        "canonical corpus lacks an authority/provider pair",
                    )
                )
                continue
            corpus_pair_count += 1
            pack_pairs.add((authority_id, provider_id))

        if corpus_pair_count != len(pack_pairs):
            findings.append(
                _finding(
                    "GLOBAL_PACK_BINDING_CLOSURE_INVALID",
                    f"canonical-packs/{skill_id}/corpora",
                    "canonical pack repeats an authority/provider pair",
                )
            )
        pack_pairs_by_skill[skill_id] = pack_pairs
        central_pairs = central_pairs_by_skill[skill_id]
        if pack_pairs != central_pairs:
            findings.append(
                _finding(
                    "GLOBAL_PACK_BINDING_SET_MISMATCH",
                    f"canonical-packs/{skill_id}/corpora",
                    "canonical corpus authority/provider pairs must exactly "
                    "equal all central binding pairs for this Skill "
                    f"(pack={len(pack_pairs)}, central={len(central_pairs)})",
                )
            )

    missing_pack_skills = set(source_skills) - set(pack_pairs_by_skill)
    if missing_pack_skills:
        findings.append(
            _finding(
                "GLOBAL_PACK_BINDING_CLOSURE_INVALID",
                "canonical-packs",
                "every source-backed Skill must expose a readable canonical "
                f"corpus pair set (missing count={len(missing_pack_skills)})",
            )
        )

    central_global = {
        (skill_id, authority_id, provider_id)
        for skill_id, pairs in central_pairs_by_skill.items()
        for authority_id, provider_id in pairs
    }
    pack_global = {
        (skill_id, authority_id, provider_id)
        for skill_id, pairs in pack_pairs_by_skill.items()
        for authority_id, provider_id in pairs
    }
    if pack_global != central_global:
        findings.append(
            _finding(
                "GLOBAL_PACK_BINDING_SET_MISMATCH",
                "registry/official-document-consumers.yaml/bindings",
                "global canonical pack and central consumer pair sets must "
                "be exactly equal "
                f"(pack={len(pack_global)}, central={len(central_global)})",
            )
        )
    return _deduplicate_findings(findings)


def _processor_ceiling(
    processor: dict[str, Any],
    *,
    kind: str,
    expected_input_sha256: str,
    expected_output_sha256: str,
    declared_status: str,
    consumer_registry: dict[str, Any],
    root: Path,
    location: str,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> str:
    declared_input_sha256 = processor.get(
        "input_sha256",
        processor.get("input_raw_sha256"),
    )
    if (
        declared_input_sha256 != expected_input_sha256
        or processor["output_sha256"] != expected_output_sha256
    ):
        findings.append(
            _finding(
                "PROCESSOR_IO_MISMATCH",
                location,
                f"{kind} input/output identity does not match the exact validated "
                "record projection",
            )
        )
        return "blocked"
    if processor["trust_mode"] == "unverified":
        if declared_status == "complete":
            findings.append(
                _finding(
                    "PROCESSOR_TRUST_UNVERIFIED",
                    f"{location}/trust_mode",
                    f"{kind} has no centrally governed execution evidence",
                )
            )
        return "partial"

    registered = consumer_registry["processors"].get(
        processor.get(f"{kind}_id", processor.get("tool_id"))
    )
    expected_identity = {
        "kind": kind,
        "version": processor.get(f"{kind}_version", processor.get("tool_version")),
        **{field: processor[field] for field in PROCESSOR_REF_FIELDS},
    }
    if (
        registered is None
        or {
            key: registered[key]
            for key in ("kind", "version", *PROCESSOR_REF_FIELDS)
        }
        != expected_identity
    ):
        findings.append(
            _finding(
                "PROCESSOR_TRUST_INVALID",
                location,
                f"{kind} does not exactly match a centrally governed processor entry",
            )
        )
        return "blocked"

    valid = True
    for field in PROCESSOR_REF_FIELDS:
        reference = processor[field]
        raw = _safe_local_bytes(
            root,
            reference["path"],
            location=f"{location}/{field}/path",
            findings=findings,
            failure_code="PROCESSOR_ARTIFACT_UNAVAILABLE",
            portable_context=portable_context,
        )
        if raw is None:
            valid = False
        elif _artifact_sha256(raw) != reference["sha256"]:
            valid = False
            findings.append(
                _finding(
                    "PROCESSOR_ARTIFACT_HASH_MISMATCH",
                    f"{location}/{field}/sha256",
                    "processor artifact sha256 does not match exact repository bytes",
                )
            )
    if not valid:
        return "blocked"
    if processor["trust_mode"] == "central-pinned":
        if declared_status == "complete":
            findings.append(
                _finding(
                    "PROCESSOR_EXECUTION_UNATTESTED",
                    f"{location}/trust_mode",
                    f"{kind} implementation hashes alone do not prove that the "
                    "declared input produced the declared output",
                )
            )
        return "partial"

    attestation = next(
        (
            run
            for run in registered["attested_runs"]
            if run["attestation_id"] == processor["attestation_id"]
        ),
        None,
    )
    if (
        processor["trust_mode"] != "platform-attested"
        or attestation is None
        or attestation["input_sha256"] != expected_input_sha256
        or attestation["output_sha256"] != expected_output_sha256
    ):
        findings.append(
            _finding(
                "PROCESSOR_ATTESTATION_INVALID",
                f"{location}/attestation_id",
                f"{kind} has no exact central input/output attestation",
            )
        )
        return "blocked"
    reference = attestation["attestation_ref"]
    raw = _safe_local_bytes(
        root,
        reference["path"],
        location=f"{location}/attestation_id",
        findings=findings,
        failure_code="PROCESSOR_ATTESTATION_UNAVAILABLE",
        portable_context=portable_context,
    )
    if raw is None or _artifact_sha256(raw) != reference["sha256"]:
        findings.append(
            _finding(
                "PROCESSOR_ATTESTATION_HASH_MISMATCH",
                f"{location}/attestation_id",
                "processor attestation hash does not match exact local bytes",
            )
        )
        return "blocked"
    return "complete"


def _resolver_receipt_ceiling(
    receipt: dict[str, Any],
    *,
    authority_id: str,
    selection_binding: dict[str, Any] | None = None,
    consumer_registry: dict[str, Any],
    consumer_registry_sha256: str,
    repository_root: Path,
    location: str,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> str:
    """Resolve a receipt against the central trust root.

    A syntactically valid record-carried receipt is evidence only. It reaches
    complete assurance solely when its resolver, evidence digest, exact
    implementation/configuration/lock files, and optional platform attestation
    exactly match a central trust entry.
    """

    if (
        receipt["registry_sha256"] != consumer_registry_sha256
        or receipt["verification_status"] != receipt["trust_mode"]
    ):
        findings.append(
            _finding(
                "RESOLVER_TRUST_INVALID",
                location,
                "resolver receipt does not consistently bind the exact canonical "
                "consumer registry and trust mode",
            )
        )
        return "blocked"
    if receipt["trust_mode"] == "unverified":
        return "partial"

    trust = consumer_registry["resolver_trust"].get(receipt["trust_id"])
    if (
        trust is None
        or trust["authority_id"] != authority_id
        or trust["resolver_id"] != receipt["resolver_id"]
        or trust["trust_mode"] != receipt["trust_mode"]
        or receipt["evidence_sha256"] not in trust["evidence_sha256"]
    ):
        findings.append(
            _finding(
                "RESOLVER_TRUST_INVALID",
                location,
                "resolver receipt does not exactly match a central trust entry",
            )
        )
        return "blocked"

    valid = True
    refs = list(PROCESSOR_REF_FIELDS)
    if trust["trust_mode"] == "platform-attested":
        refs.append("platform_attestation_ref")
    for field in refs:
        reference = trust[field]
        raw = _safe_local_bytes(
            repository_root,
            reference["path"],
            location=f"{location}/{field}/path",
            findings=findings,
            failure_code="RESOLVER_TRUST_ARTIFACT_UNAVAILABLE",
            portable_context=portable_context,
        )
        if raw is None:
            valid = False
        elif _artifact_sha256(raw) != reference["sha256"]:
            valid = False
            findings.append(
                _finding(
                    "RESOLVER_TRUST_ARTIFACT_HASH_MISMATCH",
                    f"{location}/{field}/sha256",
                    "resolver trust artifact hash does not match exact local bytes",
                )
            )
    if selection_binding is not None:
        expected_selection = {
            "attestation_id": receipt["selection_attestation_id"],
            "source_id": selection_binding["source_id"],
            "raw_sha256": selection_binding["raw_sha256"],
            "raw_bytes": selection_binding["raw_bytes"],
            "selector": selection_binding["selector"],
            "selected_sha256": selection_binding["selected_sha256"],
            "selected_bytes": selection_binding["selected_bytes"],
        }
        selection = next(
            (
                item
                for item in trust["attested_selections"]
                if item["attestation_id"]
                == receipt["selection_attestation_id"]
            ),
            None,
        )
        if (
            receipt["selected_sha256"]
            != selection_binding["selected_sha256"]
            or receipt["selected_bytes"]
            != selection_binding["selected_bytes"]
            or selection is None
            or {
                key: selection[key]
                for key in expected_selection
            }
            != expected_selection
        ):
            findings.append(
                _finding(
                    "RESOLVER_SELECTION_ATTESTATION_INVALID",
                    f"{location}/selection_attestation_id",
                    "resolver selection attestation does not exactly bind source_id, "
                    "raw source identity, selector, selected hash, and selected length",
                )
            )
            valid = False
        else:
            reference = selection["attestation_ref"]
            raw = _safe_local_bytes(
                repository_root,
                reference["path"],
                location=f"{location}/selection_attestation_id",
                findings=findings,
                failure_code="RESOLVER_SELECTION_ATTESTATION_UNAVAILABLE",
                portable_context=portable_context,
            )
            if (
                raw is None
                or _artifact_sha256(raw) != reference["sha256"]
            ):
                findings.append(
                    _finding(
                        "RESOLVER_SELECTION_ATTESTATION_HASH_MISMATCH",
                        f"{location}/selection_attestation_id",
                        "selection attestation hash does not match exact local bytes",
                    )
                )
                valid = False
    return "complete" if valid else "blocked"


def _url_matches_authority(
    url: str,
    authority: dict[str, Any],
) -> bool:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
    ):
        return False
    origin = f"https://{parsed.hostname}" if parsed.hostname else ""
    if origin not in authority["allowed_https_origins"]:
        return False
    content_policy = authority["content_policy"]
    if not any(
        parsed.path.startswith(prefix)
        for prefix in content_policy["allowed_path_prefixes"]
    ):
        return False
    if content_policy["fragment_policy"] == "forbidden" and parsed.fragment:
        return False
    if parsed.query:
        return (
            content_policy["query_policy"] == "exact-allowlist"
            and url in content_policy.get("allowed_query_urls", [])
        )
    if content_policy["query_policy"] not in {
        "forbidden",
        "exact-allowlist",
    }:
        return False
    return True


def _load_records(
    paths: Iterable[Path],
    *,
    catalog: validate_contract.ContractCatalog,
    selector: str,
    id_field: str,
    label: str,
) -> tuple[list[LoadedRecord], list[Finding]]:
    loaded: list[LoadedRecord] = []
    findings: list[Finding] = []
    seen_ids: dict[str, Path] = {}
    for index, requested in enumerate(paths):
        path = Path(requested)
        location = f"{label}[{index}]"
        try:
            raw = strict_json.read_bytes_bounded(
                path,
                path.name or label,
                max_bytes=MAX_RECORD_BYTES,
            )
            data = strict_json.loads_object(
                raw,
                path.name or label,
                max_bytes=MAX_RECORD_BYTES,
            )
        except (OSError, strict_json.StrictJSONError) as exc:
            findings.append(
                _finding(
                    "STRICT_JSON_INVALID",
                    location,
                    f"strict JSON record is unavailable or invalid: {exc}",
                )
            )
            continue

        contract = catalog.resolve(selector)
        validator = Draft202012Validator(
            contract.schema,
            registry=catalog.registry,
            format_checker=validate_contract.FORMAT_CHECKER,
        )
        schema_errors = [
            (
                "/".join(str(part) for part in error.absolute_path) or "<root>"
            )
            + f": {error.message}"
            for error in sorted(
                validator.iter_errors(data),
                key=lambda item: tuple(str(part) for part in item.absolute_path),
            )
        ]
        if schema_errors:
            findings.extend(
                _finding("RECORD_SCHEMA_INVALID", location, item)
                for item in schema_errors
            )
            continue

        record_id = data[id_field]
        previous = seen_ids.get(record_id)
        if previous is not None:
            findings.append(
                _finding(
                    "DUPLICATE_RECORD_ID",
                    location,
                    f"{id_field} duplicates another {label} record",
                )
            )
            continue
        seen_ids[record_id] = path
        loaded.append(
            LoadedRecord(
                path=path,
                raw_sha256=hashlib.sha256(raw).hexdigest(),
                data=data,
            )
        )
    return loaded, findings


def _index(
    records: Iterable[LoadedRecord],
    id_field: str,
) -> dict[str, LoadedRecord]:
    return {record.data[id_field]: record for record in records}


def _ids(
    items: Iterable[dict[str, Any]],
    field: str,
) -> list[str]:
    return [item[field] for item in items]


def _check_unique_ids(
    items: Iterable[dict[str, Any]],
    field: str,
    *,
    code: str,
    location: str,
    findings: list[Finding],
) -> None:
    values = _ids(items, field)
    if len(values) != len(set(values)):
        findings.append(
            _finding(code, location, f"{field} values must be unique")
        )


def _check_ref(
    reference: dict[str, Any],
    *,
    id_field: str,
    records: dict[str, LoadedRecord],
    location: str,
    findings: list[Finding],
) -> LoadedRecord | None:
    record_id = reference[id_field]
    target = records.get(record_id)
    if target is None:
        findings.append(
            _finding(
                "RECORD_REF_UNRESOLVED",
                location,
                f"{id_field} does not resolve in this validation bundle",
            )
        )
        return None
    if reference["sha256"] != target.raw_sha256:
        findings.append(
            _finding(
                "RECORD_REF_HASH_MISMATCH",
                location,
                "declared sha256 does not match exact referenced record bytes",
            )
        )
    return target


def _status_overclaim(
    declared: str,
    maximum: str,
    *,
    location: str,
    findings: list[Finding],
) -> None:
    if STATUS_RANK[declared] > STATUS_RANK[maximum]:
        findings.append(
            _finding(
                "COMPLETENESS_STATUS_OVERCLAIM",
                location,
                f"declared status {declared!r} exceeds computed ceiling {maximum!r}",
            )
        )


def _corpus_findings(
    record: LoadedRecord,
    *,
    authorities: dict[str, dict[str, Any]],
    authority_projection: dict[str, dict[str, Any]],
    consumer_registry: dict[str, Any],
    consumer_registry_sha256: str,
    source_root: Path,
    repository_root: Path,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> None:
    data = record.data
    location = f"corpus/{data['corpus_id']}"
    discovered = data["discovery"]["discovered_source_ids"]
    included = _ids(data["included_sources"], "source_id")
    excluded = _ids(data["reviewed_exclusions"], "source_id")
    discovered_set = set(discovered)
    included_set = set(included)
    excluded_set = set(excluded)

    _check_unique_ids(
        data["included_sources"],
        "source_id",
        code="CORPUS_SOURCE_ID_DUPLICATE",
        location=f"{location}/included_sources",
        findings=findings,
    )
    _check_unique_ids(
        data["reviewed_exclusions"],
        "source_id",
        code="CORPUS_SOURCE_ID_DUPLICATE",
        location=f"{location}/reviewed_exclusions",
        findings=findings,
    )
    if (
        included_set.intersection(excluded_set)
        or discovered_set != included_set.union(excluded_set)
        or len(discovered) != len(discovered_set)
    ):
        findings.append(
            _finding(
                "CORPUS_PARTITION_INVALID",
                f"{location}/discovery",
                "discovered_source_ids must be exactly the disjoint union of "
                "included source IDs and reviewed exclusion source IDs",
            )
        )

    discovery = data["discovery"]
    inventory_ceiling = "complete"
    if discovery["inventory_format"] == "declarative-source-catalog-v1":
        if (
            discovery["upstream_universe_complete"]
            or discovery["inventory_scope"] != "bounded-authority-subset"
        ):
            findings.append(
                _finding(
                    "CORPUS_CATALOG_SELF_ASSERTED_UNIVERSE",
                    f"{location}/discovery/upstream_universe_complete",
                    "a declarative source catalog is the bounded claim being "
                    "checked and cannot independently prove an upstream "
                    "universe",
                )
            )
            inventory_ceiling = "blocked"
        if data["version_scope"]["kind"] == "latest-at-retrieval":
            expected_snapshot = _source_identity_aggregate_sha256(data)
            snapshot = data["version_scope"]["snapshot_identity"]
            if (
                not isinstance(snapshot, dict)
                or snapshot.get("kind") != "sha256"
                or snapshot.get("value") != expected_snapshot
                or snapshot.get("content_sha256") != expected_snapshot
            ):
                findings.append(
                    _finding(
                        "ROLLING_SNAPSHOT_IDENTITY_MISMATCH",
                        f"{location}/version_scope/snapshot_identity",
                        "rolling declarative corpus identity must equal the "
                        "domain-separated aggregate independently recomputed "
                        "from included source identities and reviewed "
                        "exclusions",
                    )
                )
                inventory_ceiling = "blocked"
    processor_ceiling = _processor_ceiling(
        discovery["enumerator"],
        kind="enumerator",
        expected_input_sha256=discovery["inventory_sha256"],
        expected_output_sha256=_canonical_json_sha256(
            {"discovered_source_ids": discovered}
        ),
        declared_status=data["status"],
        consumer_registry=consumer_registry,
        root=repository_root,
        location=f"{location}/discovery/enumerator",
        findings=findings,
        portable_context=portable_context,
    )
    if discovery["inventory_storage_mode"] == "embedded-open":
        inventory_raw = _safe_local_bytes(
            source_root,
            discovery["inventory_locator"],
            location=f"{location}/discovery/inventory_locator",
            findings=findings,
            failure_code="CORPUS_INVENTORY_UNAVAILABLE",
            portable_context=portable_context,
        )
        if inventory_raw is None:
            inventory_ceiling = "blocked"
        else:
            actual_inventory_hash = _artifact_sha256(inventory_raw)
            if actual_inventory_hash != discovery["inventory_sha256"]:
                findings.append(
                    _finding(
                        "CORPUS_INVENTORY_HASH_MISMATCH",
                        f"{location}/discovery/inventory_sha256",
                        "inventory_sha256 does not match exact inventory artifact bytes",
                    )
                )
                inventory_ceiling = "blocked"
            if isinstance(inventory_raw, ExternalizedArtifact):
                pass
            else:
                inventory_ids: set[str] | None = None
                try:
                    inventory_data = strict_json.loads_object(
                        inventory_raw,
                        discovery["inventory_locator"],
                        max_bytes=MAX_CONTENT_BYTES,
                    )
                except strict_json.StrictJSONError:
                    inventory_data = {}
                if (
                    discovery["inventory_format"]
                    == "cp2k-canonical-manifest-v1"
                    and isinstance(inventory_data.get("pages"), dict)
                ):
                    if all(
                        isinstance(item, dict)
                        and isinstance(item.get("source_path"), str)
                        for item in inventory_data["pages"].values()
                    ):
                        inventory_ids = {
                            official_source_authorities.cp2k_source_id(
                                item["source_path"]
                            )
                            for item in inventory_data["pages"].values()
                        }
                elif (
                    discovery["inventory_format"] == "cp2k-official-index-v1"
                    and set(inventory_data)
                    == official_source_authorities.CP2K_INDEX_FIELDS
                    and inventory_data.get("schema_version") == "1.0"
                    and isinstance(inventory_data.get("pages"), list)
                    and all(
                        isinstance(item, str)
                        for item in inventory_data["pages"]
                    )
                ):
                    inventory_ids = {
                        official_source_authorities.cp2k_source_id(item)
                        for item in inventory_data["pages"]
                    }
                elif (
                    discovery["inventory_format"] == "source-id-list-v1"
                    and set(inventory_data) == {"schema_version", "source_ids"}
                    and inventory_data["schema_version"] == "1.0"
                    and isinstance(inventory_data["source_ids"], list)
                    and all(
                        isinstance(item, str)
                        for item in inventory_data["source_ids"]
                    )
                ):
                    inventory_ids = set(inventory_data["source_ids"])
                elif (
                    discovery["inventory_format"]
                    == "declarative-source-catalog-v1"
                    and set(inventory_data)
                    == {
                        "schema_version",
                        "contract_name",
                        "version_scope",
                        "upstream_universe_complete",
                        "inventory_locator",
                        "sources",
                        "subjects",
                        "reviewed_exclusions",
                        "losses",
                        "license",
                        "limitations",
                        "blockers",
                    }
                    and inventory_data.get("schema_version") == "1.0"
                    and inventory_data.get("contract_name")
                    == "official-document-source-catalog"
                    and isinstance(inventory_data.get("sources"), list)
                    and isinstance(
                        inventory_data.get("reviewed_exclusions"), list
                    )
                    and all(
                        isinstance(item, dict)
                        and isinstance(item.get("source_id"), str)
                        for item in [
                            *inventory_data["sources"],
                            *inventory_data["reviewed_exclusions"],
                        ]
                    )
                ):
                    inventory_ids = {
                        item["source_id"]
                        for item in [
                            *inventory_data["sources"],
                            *inventory_data["reviewed_exclusions"],
                        ]
                    }
                elif (
                    discovery["inventory_format"]
                    == "qe-official-manifest-v1"
                    and set(inventory_data)
                    == {
                        "schema_version",
                        "contract_name",
                        "catalog_type",
                        "skill_id",
                        "source_root",
                        "retrieved_utc",
                        "legacy_manifest_sha256",
                        "manuals",
                        "limitations",
                    }
                    and inventory_data.get("schema_version") == "1.0"
                    and inventory_data.get("contract_name")
                    == "qe-source-pack-input"
                    and inventory_data.get("catalog_type")
                    == "qe-input-manifest-metadata-v1"
                    and isinstance(inventory_data.get("manuals"), list)
                    and all(
                        isinstance(item, dict)
                        and set(item)
                        == {
                            "name",
                            "version",
                            "url",
                            "retrieved_utc",
                            "raw_sha256",
                            "raw_bytes",
                            "sections",
                        }
                        and isinstance(item.get("name"), str)
                        for item in inventory_data["manuals"]
                    )
                ):
                    inventory_ids = {
                        _pack_source_id("qe-input", item["name"])
                        for item in inventory_data["manuals"]
                    }
                elif (
                    discovery["inventory_format"]
                    == "vasp-wiki-manifest-v1"
                    and set(inventory_data)
                    == {
                        "schema_version",
                        "contract_name",
                        "catalog_type",
                        "skill_id",
                        "official_root",
                        "api_url",
                        "pages",
                        "retrieved_utc",
                        "legacy_manifest_sha256",
                        "limitations",
                    }
                    and inventory_data.get("schema_version") == "1.0"
                    and inventory_data.get("contract_name")
                    == "vasp-source-pack-input"
                    and inventory_data.get("catalog_type")
                    == "vasp-wiki-page-metadata-v1"
                    and isinstance(inventory_data.get("pages"), list)
                    and len(inventory_data["pages"]) == 81
                    and all(
                        isinstance(item, dict)
                        and set(item)
                        == {
                            "pageid",
                            "revid",
                            "title",
                            "url",
                            "api_request_url",
                            "raw_json_sha256",
                            "raw_json_bytes",
                            "wikitext_sha256",
                            "wikitext_bytes",
                        }
                        and isinstance(item.get("pageid"), int)
                        and not isinstance(item.get("pageid"), bool)
                        for item in inventory_data["pages"]
                    )
                ):
                    inventory_ids = {
                        _pack_source_id(
                            "vasp-page", item["pageid"], representation
                        )
                        for item in inventory_data["pages"]
                        for representation in ("api-json", "wikitext")
                    }
                if inventory_ids is None:
                    findings.append(
                        _finding(
                            "CORPUS_INVENTORY_FORMAT_INVALID",
                            f"{location}/discovery/inventory_locator",
                            "inventory artifact does not match its declared strict format",
                        )
                    )
                    inventory_ceiling = "blocked"
                elif inventory_ids != discovered_set:
                    findings.append(
                        _finding(
                            "CORPUS_INVENTORY_SET_MISMATCH",
                            f"{location}/discovery/discovered_source_ids",
                            "discovered_source_ids must exactly equal IDs parsed from "
                            "the hashed inventory artifact",
                        )
                    )
                    inventory_ceiling = "blocked"
    else:
        receipt = discovery["inventory_receipt"]
        if (
            receipt is None
            or receipt["canonical_url"] != discovery["inventory_locator"]
            or receipt["raw_sha256"] != discovery["inventory_sha256"]
            or receipt["selected_sha256"] != receipt["raw_sha256"]
            or receipt["selected_bytes"] != receipt["raw_bytes"]
        ):
            findings.append(
                _finding(
                    "CORPUS_INVENTORY_RECEIPT_INVALID",
                    f"{location}/discovery/inventory_receipt",
                    "external inventory locator/hash does not match its resolver receipt",
                )
            )
            inventory_ceiling = "blocked"
        else:
            inventory_ceiling = _resolver_receipt_ceiling(
                receipt,
                authority_id=data["authority_id"],
                consumer_registry=consumer_registry,
                consumer_registry_sha256=consumer_registry_sha256,
                repository_root=repository_root,
                location=f"{location}/discovery/inventory_receipt",
                findings=findings,
                portable_context=portable_context,
            )

    authority_id = data["authority_id"]
    authority = authorities.get(authority_id)
    projection = authority_projection.get(authority_id)
    if authority is None or projection is None:
        findings.append(
            _finding(
                "AUTHORITY_REF_UNRESOLVED",
                f"{location}/authority_id",
                "authority_id is not an active official-source authority",
            )
        )
        maximum = "blocked"
    else:
        maximum = "complete"
        if data["provider_id"] != authority["provider_id"]:
            findings.append(
                _finding(
                    "AUTHORITY_PROVIDER_MISMATCH",
                    f"{location}/provider_id",
                    "corpus provider_id differs from the registered authority provider",
                )
            )
        if discovery["authority_root"] not in projection["canonical_urls"]:
            findings.append(
                _finding(
                    "AUTHORITY_DISCOVERY_ROOT_MISMATCH",
                    f"{location}/discovery/authority_root",
                    "discovery authority_root is not a registered canonical root",
                )
            )
        if (
            data["version_scope"]["kind"]
            in {"exact", "revision", "release-line"}
            and discovery["authority_revision"]
            != data["version_scope"]["value"]
        ):
            findings.append(
                _finding(
                    "AUTHORITY_DISCOVERY_REVISION_MISMATCH",
                    f"{location}/discovery/authority_revision",
                    "discovery revision differs from the static corpus identity",
                )
            )
        version_scope = data["version_scope"]
        registered = authority["version_policy"]["registered_scopes"]
        version_match = authority_version_scope_compatible(
            version_scope,
            registered,
        )
        if not version_match:
            findings.append(
                _finding(
                    "AUTHORITY_VERSION_SCOPE_MISMATCH",
                    f"{location}/version_scope",
                    "corpus version scope is not registered for this authority",
                )
            )
            maximum = "blocked"

        canonical = projection["canonical_snapshot"]
        if canonical is not None:
            canonical_externalized = (
                canonical.get("portable_externalized") is True
            )
            inventory_format = data["discovery"]["inventory_format"]
            if inventory_format == "cp2k-official-index-v1":
                expected_inventory_hash = canonical["index_raw_sha256"]
                expected_inventory_ids = set(canonical["upstream_sources_by_id"])
                expected_scope = "upstream-universe"
            elif inventory_format == "cp2k-canonical-manifest-v1":
                expected_inventory_hash = canonical["manifest_raw_sha256"]
                expected_inventory_ids = set(canonical["sources_by_id"])
                expected_scope = "bounded-authority-subset"
            else:
                expected_inventory_hash = None
                expected_inventory_ids = set()
                expected_scope = None
            if (
                data["discovery"]["inventory_sha256"] != expected_inventory_hash
                or data["discovery"]["inventory_scope"] != expected_scope
                or (
                    not canonical_externalized
                    and discovered_set != expected_inventory_ids
                )
            ):
                findings.append(
                    _finding(
                        "AUTHORITY_CANONICAL_INVENTORY_MISMATCH",
                        f"{location}/discovery",
                        "canonical-pinned corpus must use the exact registered "
                        "upstream index or explicitly bounded curated manifest",
                    )
                )
                maximum = "blocked"
            if (
                not canonical_externalized
                and
                data["discovery"]["upstream_universe_complete"]
                and (
                    expected_scope != "upstream-universe"
                    or not canonical["upstream_universe_complete"]
                )
            ):
                findings.append(
                    _finding(
                        "CORPUS_UPSTREAM_UNIVERSE_OVERCLAIM",
                        f"{location}/discovery/upstream_universe_complete",
                        "a bounded curated snapshot cannot be relabeled as the "
                        "complete upstream source universe",
                    )
                )
                maximum = "blocked"

        canonical_sources = (
            canonical["sources_by_id"]
            if canonical is not None
            and canonical.get("portable_externalized") is not True
            else {}
        )
        for source_index, source in enumerate(data["included_sources"]):
            source_location = f"{location}/included_sources/{source_index}"
            if not _url_matches_authority(source["locator"], authority):
                findings.append(
                    _finding(
                        "AUTHORITY_LOCATOR_MISMATCH",
                        f"{source_location}/locator",
                        "source locator is outside the registered authority policy",
                    )
                )
            source_scope = source["version_scope"]
            version_compatible = source_version_scope_compatible(
                source_scope,
                version_scope,
                raw_sha256=source["identity"]["raw_sha256"],
            )
            if not version_compatible:
                findings.append(
                    _finding(
                        "SOURCE_VERSION_SCOPE_MISMATCH",
                        f"{source_location}/version_scope",
                        "source version identity is incompatible with the corpus scope",
                    )
                )

            identity = source["identity"]
            receipt = identity["resolver_receipt"]
            if (
                identity["kind"] == "sha256"
                and identity["value"] != identity["raw_sha256"]
            ):
                findings.append(
                    _finding(
                        "SOURCE_CONTENT_IDENTITY_INVALID",
                        f"{source_location}/identity",
                        "sha256 identity value must equal raw_sha256",
                    )
                )
            source_identity_ceiling = "complete"
            if identity["kind"] not in {
                "sha256",
                "canonical-manifest-metadata",
            }:
                if (
                    receipt is None
                    or receipt["raw_sha256"] != identity["raw_sha256"]
                    or receipt["raw_bytes"] != identity["raw_bytes"]
                    or receipt["selected_sha256"]
                    != identity["raw_sha256"]
                    or receipt["selected_bytes"] != identity["raw_bytes"]
                    or receipt["canonical_url"] != source["locator"]
                    or (
                        identity["kind"] == "external-receipt"
                        and identity["value"] != receipt["receipt_id"]
                    )
                ):
                    findings.append(
                        _finding(
                            "SOURCE_RECEIPT_INVALID",
                            f"{source_location}/identity/resolver_receipt",
                            "external identity does not match its verified resolver receipt",
                        )
                    )
                    maximum = "blocked"
                else:
                    source_identity_ceiling = _resolver_receipt_ceiling(
                        receipt,
                        authority_id=authority_id,
                        selection_binding={
                            "source_id": source["source_id"],
                            "raw_sha256": identity["raw_sha256"],
                            "raw_bytes": identity["raw_bytes"],
                            "selector": {
                                "layer": "raw-source",
                                "kind": "whole-source",
                                "value": "*",
                            },
                            "selected_sha256": identity["raw_sha256"],
                            "selected_bytes": identity["raw_bytes"],
                        },
                        consumer_registry=consumer_registry,
                        consumer_registry_sha256=consumer_registry_sha256,
                        repository_root=repository_root,
                        location=f"{source_location}/identity/resolver_receipt",
                        findings=findings,
                        portable_context=portable_context,
                    )
            elif identity["kind"] == "canonical-manifest-metadata":
                source_identity_ceiling = "partial"

            if (
                canonical is not None
                and canonical.get("portable_externalized") is not True
            ):
                canonical_source = canonical_sources.get(source["source_id"])
                if (
                    canonical_source is not None
                    and identity["raw_sha256"]
                    == canonical_source["derived_snapshot"]["sha256"]
                    and identity["raw_sha256"] != canonical_source["raw_sha256"]
                ):
                    findings.append(
                        _finding(
                            "SOURCE_RAW_DERIVED_IDENTITY_CONFUSED",
                            f"{source_location}/identity/raw_sha256",
                            "derived Markdown snapshot bytes cannot stand in for the "
                            "upstream raw source identity",
                        )
                    )
                    maximum = "blocked"
                if (
                    canonical_source is None
                    or canonical_source["canonical_url"] != source["locator"]
                    or canonical_source["raw_sha256"]
                    != identity["raw_sha256"]
                    or canonical_source["raw_bytes"] != identity["raw_bytes"]
                ):
                    findings.append(
                        _finding(
                            "AUTHORITY_CANONICAL_SNAPSHOT_MISMATCH",
                            source_location,
                            "included source does not match the registered canonical "
                            "snapshot URL and exact bytes",
                        )
                    )
                    maximum = "blocked"
                elif (
                    not canonical_source["raw_integrity_verified"]
                    and receipt is None
                ):
                    # The local Markdown snapshot verifies a derived transform,
                    # not the exact upstream HTML bytes declared in the manifest.
                    source_identity_ceiling = "partial"
            elif (
                authority["content_identity_policy"]["mode"]
                == "platform-adapter-only"
            ):
                # A record-carried receipt is evidence, not the external adapter
                # trust root.  Inventory closure may still be represented, but
                # complete content assurance remains unavailable offline.
                maximum = "partial"
            maximum = min(
                (maximum, source_identity_ceiling),
                key=STATUS_RANK.__getitem__,
            )

    if data["blockers"]:
        maximum = "blocked"
    elif (
        not data["discovery"]["upstream_universe_complete"]
        or data["reviewed_exclusions"]
    ):
        maximum = "partial"
    maximum = min(
        (maximum, inventory_ceiling, processor_ceiling),
        key=STATUS_RANK.__getitem__,
    )
    _status_overclaim(
        data["status"],
        maximum,
        location=f"{location}/status",
        findings=findings,
    )


def _scope_inventory_findings(
    record: LoadedRecord,
    *,
    repository_root: Path,
    skill_registry_data: dict[str, Any],
    skill_registry_sha256: str,
    consumer_registry: dict[str, Any],
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> None:
    data = record.data
    location = f"scope-inventory/{data['inventory_id']}"
    _check_unique_ids(
        data["skill_source_refs"],
        "path",
        code="SCOPE_SOURCE_REF_DUPLICATE",
        location=f"{location}/skill_source_refs",
        findings=findings,
    )
    _check_unique_ids(
        data["subjects"],
        "subject_id",
        code="SCOPE_SUBJECT_ID_DUPLICATE",
        location=f"{location}/subjects",
        findings=findings,
    )
    skill = skill_registry_data["skills"].get(data["skill_id"])
    binding = data["skill_registry_binding"]
    skill_binding_valid = True
    if skill is None or skill.get("path") is None:
        findings.append(
            _finding(
                "SCOPE_SKILL_UNREGISTERED",
                f"{location}/skill_id",
                "skill_id does not resolve to a source-backed skill-registry entry",
            )
        )
        skill_binding_valid = False
        skill_path = None
    else:
        skill_path = skill["path"]
        expected_binding = {
            "registry_path": "registry/skill-registry.yaml",
            "registry_sha256": skill_registry_sha256,
            "skill_path": skill["path"],
            "lifecycle": skill["lifecycle"],
            "source_tree_hash_domain": skill_registry.TREE_HASH_DOMAIN_NAME,
            "source_tree_sha256": skill["source_tree_sha256"],
        }
        if binding != expected_binding:
            findings.append(
                _finding(
                    "SCOPE_SKILL_REGISTRY_BINDING_INVALID",
                    f"{location}/skill_registry_binding",
                    "scope inventory does not exactly bind the canonical skill "
                    "registry bytes, path, lifecycle, and source-tree identity",
                )
            )
            skill_binding_valid = False

    source_valid = True
    externalized_source_refs = False
    source_ref_pairs = {
        (item["path"], item["sha256"])
        for item in data["skill_source_refs"]
    }
    for index, reference in enumerate(data["skill_source_refs"]):
        if (
            skill_path is None
            or not PurePosixPath(reference["path"]).is_relative_to(
                PurePosixPath(skill_path)
            )
            or PurePosixPath(reference["path"]) == PurePosixPath(skill_path)
        ):
            source_valid = False
            findings.append(
                _finding(
                    "SCOPE_SOURCE_SCOPE_MISMATCH",
                    f"{location}/skill_source_refs/{index}/path",
                    "scope source must be a regular file inside the registered Skill path",
                )
            )
            continue
        skill_relative = PurePosixPath(reference["path"]).relative_to(
            PurePosixPath(skill_path)
        )
        if skill_registry.source_tree_hash_path_excluded(skill_relative):
            source_valid = False
            findings.append(
                _finding(
                    "SCOPE_SOURCE_HASH_DOMAIN_INVALID",
                    f"{location}/skill_source_refs/{index}/path",
                    "official-source-pack records belong to the independent bundle "
                    "hash domain and cannot be included in Skill scope-tree refs",
                )
            )
            continue
        raw = _safe_local_bytes(
            repository_root,
            reference["path"],
            location=f"{location}/skill_source_refs/{index}/path",
            findings=findings,
            failure_code="SCOPE_SOURCE_UNAVAILABLE",
            portable_context=portable_context,
        )
        if raw is None:
            source_valid = False
        elif _artifact_sha256(raw) != reference["sha256"]:
            source_valid = False
            findings.append(
                _finding(
                    "SCOPE_SOURCE_HASH_MISMATCH",
                    f"{location}/skill_source_refs/{index}/sha256",
                    "scope source sha256 does not match exact source bytes",
                )
            )
        elif isinstance(raw, ExternalizedArtifact):
            externalized_source_refs = True

    for subject_index, subject in enumerate(data["subjects"]):
        for origin_index, origin in enumerate(subject["origin_refs"]):
            origin_location = (
                f"{location}/subjects/{subject_index}/origin_refs/{origin_index}"
            )
            selector = origin["selector"]
            selector_valid = not (
                selector["kind"] == "whole-file"
                and selector["value"] != "*"
            )
            if (
                (origin["path"], origin["sha256"]) not in source_ref_pairs
                or not selector_valid
            ):
                source_valid = False
                findings.append(
                    _finding(
                        "SCOPE_SUBJECT_ORIGIN_INVALID",
                        origin_location,
                        "subject origin must exactly reference a hashed scope-source "
                        "file and a valid local selector",
                    )
                )

    enumeration = data["enumeration"]
    if enumeration["method"] == "canonical-reviewed-inventory":
        processor_ceiling = "partial"
        if data["status"] == "complete":
            findings.append(
                _finding(
                    "SCOPE_INVENTORY_TRUST_UNVERIFIED",
                    f"{location}/enumeration/method",
                    "manual canonical review is not a replayable complete "
                    "claim-source inventory",
                )
            )
    else:
        processor_ceiling = _processor_ceiling(
            enumeration["extractor"],
            kind="extractor",
            expected_input_sha256=binding["source_tree_sha256"],
            expected_output_sha256=_canonical_json_sha256(data["subjects"]),
            declared_status=data["status"],
            consumer_registry=consumer_registry,
            root=repository_root,
            location=f"{location}/enumeration/extractor",
            findings=findings,
            portable_context=portable_context,
        )
        if skill_path is not None and not externalized_source_refs:
            try:
                digest = skill_registry.source_tree_digest(
                    repository_root / skill_path
                )
            except ValueError as exc:
                findings.append(
                    _finding(
                        "SCOPE_SOURCE_TREE_UNAVAILABLE",
                        f"{location}/skill_registry_binding/skill_path",
                        f"registered Skill source tree cannot be inventoried: {exc}",
                    )
                )
                source_valid = False
            else:
                if digest.sha256 != binding["source_tree_sha256"]:
                    source_valid = False
                    findings.append(
                        _finding(
                            "SCOPE_SOURCE_TREE_IDENTITY_MISMATCH",
                            f"{location}/skill_registry_binding/source_tree_sha256",
                            "registered source-tree hash does not match the current "
                            "complete Skill tree",
                        )
                    )
                expected_refs = {
                    (
                        f"{skill_path}/{item.path}",
                        item.sha256,
                    )
                    for item in digest.files
                }
                actual_refs = {
                    (item["path"], item["sha256"])
                    for item in data["skill_source_refs"]
                }
                if actual_refs != expected_refs:
                    source_valid = False
                    findings.append(
                        _finding(
                            "SCOPE_SOURCE_SET_INCOMPLETE",
                            f"{location}/skill_source_refs",
                            "deterministic complete scope inventory must bind every "
                            "regular file in the registered Skill source tree",
                        )
                    )

    if data["blockers"] or not source_valid or not skill_binding_valid:
        maximum = "blocked"
    elif not enumeration["scope_complete"]:
        maximum = "partial"
    else:
        maximum = processor_ceiling
    _status_overclaim(
        data["status"],
        maximum,
        location=f"{location}/status",
        findings=findings,
    )


def _slice_manifest_findings(
    record: LoadedRecord,
    *,
    corpora: dict[str, LoadedRecord],
    authorities: dict[str, dict[str, Any]],
    authority_projection: dict[str, dict[str, Any]],
    consumer_registry: dict[str, Any],
    consumer_registry_sha256: str,
    source_root: Path,
    repository_root: Path,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> None:
    data = record.data
    manifest_id = data["slice_manifest_id"]
    location = f"slices/{manifest_id}"
    corpus = _check_ref(
        data["corpus_ref"],
        id_field="corpus_id",
        records=corpora,
        location=f"{location}/corpus_ref",
        findings=findings,
    )
    sources = data["sources"]
    _check_unique_ids(
        sources,
        "source_id",
        code="SLICE_SOURCE_ID_DUPLICATE",
        location=f"{location}/sources",
        findings=findings,
    )
    source_ids = set(_ids(sources, "source_id"))
    maximum = "complete"
    included_by_id: dict[str, dict[str, Any]] = {}
    authority: dict[str, Any] | None = None
    projection: dict[str, Any] | None = None
    if corpus is not None:
        included_by_id = {
            item["source_id"]: item
            for item in corpus.data["included_sources"]
        }
        included_ids = set(included_by_id)
        if not source_ids.issubset(included_ids):
            findings.append(
                _finding(
                    "SLICE_SOURCE_COVERAGE_INVALID",
                    f"{location}/sources",
                    "slice sources include IDs which are not included corpus sources",
                )
            )
        if source_ids != included_ids:
            maximum = "partial"
            if data["status"] == "complete":
                findings.append(
                    _finding(
                        "SLICE_SOURCE_COVERAGE_INVALID",
                        f"{location}/sources",
                        "a complete slice manifest must cover every included corpus source",
                    )
                )
        if corpus.data["status"] != "complete":
            maximum = corpus.data["status"]
        authority = authorities.get(corpus.data["authority_id"])
        projection = authority_projection.get(corpus.data["authority_id"])
        for source_index, source in enumerate(sources):
            corpus_source = included_by_id.get(source["source_id"])
            if (
                corpus_source is not None
                and source["source_identity"] != corpus_source["identity"]
            ):
                findings.append(
                    _finding(
                        "SLICE_SOURCE_IDENTITY_MISMATCH",
                        f"{location}/sources/{source_index}/source_identity",
                        "slice source identity differs from the corpus source identity",
                    )
                )
    else:
        maximum = "blocked"

    global_slice_ids: set[str] = set()
    material_unresolved = False
    blocking_loss_present = False
    external_receipt_ceiling = "complete"
    non_byte_selector = False
    derived_selector = False
    processor_ceiling = "complete"
    preservation_unverified = False
    for source_index, source in enumerate(sources):
        source_location = f"{location}/sources/{source_index}"
        source_processor_ceiling = _processor_ceiling(
            source["transformer"],
            kind="transformer",
            expected_input_sha256=source["source_identity"]["raw_sha256"],
            expected_output_sha256=_canonical_json_sha256(
                {
                    "slices": source["slices"],
                    "reviewed_overlaps": source["reviewed_overlaps"],
                    "preserved_ranges": source["preserved_ranges"],
                    "reviewed_orphans": source["reviewed_orphans"],
                    "loss_ledger": source["loss_ledger"],
                }
            ),
            declared_status=data["status"],
            consumer_registry=consumer_registry,
            root=repository_root,
            location=f"{source_location}/transformer",
            findings=findings,
            portable_context=portable_context,
        )
        processor_ceiling = min(
            (processor_ceiling, source_processor_ceiling),
            key=STATUS_RANK.__getitem__,
        )
        corpus_source = included_by_id.get(source["source_id"])
        if (
            corpus_source is not None
            and source["transformer"]["input_raw_sha256"]
            != corpus_source["identity"]["raw_sha256"]
        ):
            findings.append(
                _finding(
                    "SLICE_TRANSFORMER_INPUT_MISMATCH",
                    f"{source_location}/transformer/input_raw_sha256",
                    "transformer input hash differs from the exact corpus source content",
                )
            )
        slices = source["slices"]
        slice_ids = _ids(slices, "slice_id")
        if len(slice_ids) != len(set(slice_ids)):
            findings.append(
                _finding(
                    "SLICE_ID_DUPLICATE",
                    f"{source_location}/slices",
                    "slice_id values must be unique within a source",
                )
            )
        duplicates = global_slice_ids.intersection(slice_ids)
        if duplicates:
            findings.append(
                _finding(
                    "SLICE_ID_DUPLICATE",
                    f"{source_location}/slices",
                    "slice_id values must be globally unique in a slice manifest",
                )
            )
        global_slice_ids.update(slice_ids)
        ordinals = [item["ordinal"] for item in slices]
        if ordinals != list(range(len(slices))):
            findings.append(
                _finding(
                    "SLICE_ORDER_INVALID",
                    f"{source_location}/slices",
                    "slice ordinals must be contiguous, array-ordered, and start at zero",
                )
            )

        selectors = [
            (
                item["selector"]["layer"],
                item["selector"]["kind"],
                item["selector"]["value"],
            )
            for item in slices
        ]
        if len(selectors) != len(set(selectors)):
            findings.append(
                _finding(
                    "SLICE_SELECTOR_DUPLICATE",
                    f"{source_location}/slices",
                    "slice selectors must be unique within a source",
                )
            )

        extent = source["raw_source_extent_bytes"]
        if extent != source["source_identity"]["raw_bytes"]:
            findings.append(
                _finding(
                    "SLICE_SOURCE_EXTENT_MISMATCH",
                    f"{source_location}/raw_source_extent_bytes",
                    "raw source extent differs from the bound corpus raw identity",
                )
            )
            maximum = "blocked"
        valid_ranges: list[tuple[int, int, str]] = []
        source_raw: bytes | None = None
        source_bytes_externalized = False
        source_byte_closure = True
        for slice_index, item in enumerate(slices):
            item_location = f"{source_location}/slices/{slice_index}"
            selector = item["selector"]
            byte_range = item["byte_range"]
            start: int | None = None
            end: int | None = None
            if selector["kind"] == "byte-range":
                start = byte_range["start_byte"]
                end = byte_range["end_byte_exclusive"]
                if start >= end or (
                    selector["layer"] == "raw-source" and end > extent
                ):
                    findings.append(
                        _finding(
                            "SLICE_RANGE_INVALID",
                            f"{item_location}/byte_range",
                            "byte range must be nonempty and within its selected layer",
                        )
                    )
                elif selector["layer"] == "raw-source":
                    valid_ranges.append((start, end, item["slice_id"]))
                if selector["value"] != f"{start}:{end}":
                    findings.append(
                        _finding(
                            "SLICE_SELECTOR_INVALID",
                            f"{item_location}/selector",
                            "byte-range selector must exactly match byte_range",
                        )
                    )
            else:
                non_byte_selector = True
                source_byte_closure = False
                if (
                    data["status"] == "complete"
                    and source_processor_ceiling != "complete"
                ):
                    findings.append(
                        _finding(
                            "SLICE_SELECTOR_NO_BYTE_CLOSURE",
                            f"{item_location}/selector",
                            "non-byte selectors require an exact platform-attested "
                            "transformer input/output run for complete assurance",
                        )
                    )
            if selector["layer"] == "derived-artifact":
                derived_selector = True
                source_byte_closure = False

            storage_mode = item["storage_mode"]
            if storage_mode == "embedded-open":
                if authority is None:
                    findings.append(
                        _finding(
                            "AUTHORITY_REF_UNRESOLVED",
                            f"{item_location}/storage_mode",
                            "embedded content has no resolved authority policy",
                        )
                    )
                else:
                    bundle_policy = authority["redistribution_policy"][
                        "bundle_content"
                    ]
                    if bundle_policy == "forbidden":
                        findings.append(
                            _finding(
                                "AUTHORITY_STORAGE_CEILING_EXCEEDED",
                                f"{item_location}/storage_mode",
                                "central authority policy forbids bundled content; "
                                "a license review cannot widen that ceiling",
                            )
                        )
                    elif bundle_policy == "canonical-pinned-open-only":
                        canonical = (
                            projection["canonical_snapshot"]
                            if projection is not None
                            else None
                        )
                        canonical_source = (
                            canonical["sources_by_id"].get(source["source_id"])
                            if canonical is not None
                            and canonical.get("portable_externalized") is not True
                            else None
                        )
                        if (
                            canonical is None
                            or (
                                canonical.get("portable_externalized") is not True
                                and (
                                    canonical_source is None
                                    or canonical_source["raw_sha256"]
                                    != item["artifact_sha256"]
                                )
                            )
                        ):
                            findings.append(
                                _finding(
                                    "AUTHORITY_CANONICAL_SNAPSHOT_MISMATCH",
                                    item_location,
                                    "embedded artifact is not an exact registered "
                                    "canonical-pinned open snapshot",
                                )
                            )
                raw = _safe_local_bytes(
                    source_root,
                    item["content_locator"],
                    location=f"{item_location}/content_locator",
                    findings=findings,
                    failure_code="SLICE_ARTIFACT_UNAVAILABLE",
                    portable_context=portable_context,
                )
                if raw is not None:
                    if (
                        selector["layer"] == "raw-source"
                        and isinstance(raw, bytes)
                    ):
                        source_raw = raw
                    elif (
                        selector["layer"] == "raw-source"
                        and isinstance(raw, ExternalizedArtifact)
                    ):
                        source_bytes_externalized = True
                    if (
                        selector["layer"] == "raw-source"
                        and _artifact_size(raw) != extent
                    ):
                        findings.append(
                            _finding(
                                "SLICE_SOURCE_EXTENT_MISMATCH",
                                f"{source_location}/raw_source_extent_bytes",
                                "raw source extent does not match exact local artifact bytes",
                            )
                        )
                    actual_artifact_hash = _artifact_sha256(raw)
                    if actual_artifact_hash != item["artifact_sha256"]:
                        findings.append(
                            _finding(
                                "SLICE_ARTIFACT_HASH_MISMATCH",
                                f"{item_location}/artifact_sha256",
                                "artifact_sha256 does not match exact local file bytes",
                            )
                        )
                    if isinstance(raw, ExternalizedArtifact):
                        selection_error = (
                            _externalized_slice_selection_error(
                                raw,
                                selector_kind=selector["kind"],
                                start=start,
                                end=end,
                                content_sha256=item["content_sha256"],
                            )
                        )
                        if selection_error == "SLICE_RANGE_INVALID":
                            findings.append(
                                _finding(
                                    "SLICE_RANGE_INVALID",
                                    f"{item_location}/byte_range",
                                    "slice byte range exceeds the externalized "
                                    "artifact receipt size",
                                )
                            )
                        elif (
                            selection_error
                            == "SLICE_CONTENT_HASH_MISMATCH"
                        ):
                            findings.append(
                                _finding(
                                    "SLICE_CONTENT_HASH_MISMATCH",
                                    f"{item_location}/content_sha256",
                                    "whole-source content hash differs from the "
                                    "externalized artifact receipt",
                                )
                            )
                    elif selector["kind"] == "byte-range":
                        if (
                            start is not None
                            and end is not None
                            and end <= len(raw)
                            and start < end
                        ):
                            payload_hash = hashlib.sha256(
                                raw[start:end]
                            ).hexdigest()
                            if payload_hash != item["content_sha256"]:
                                findings.append(
                                    _finding(
                                        "SLICE_CONTENT_HASH_MISMATCH",
                                        f"{item_location}/content_sha256",
                                        "content_sha256 does not match exact ranged payload bytes",
                                    )
                                )
                        else:
                            findings.append(
                                _finding(
                                    "SLICE_RANGE_INVALID",
                                    f"{item_location}/byte_range",
                                    "slice byte range exceeds the local artifact bytes",
                                )
                            )
                    else:
                        payload_hash = hashlib.sha256(raw).hexdigest()
                        if payload_hash != item["content_sha256"]:
                            findings.append(
                                _finding(
                                    "SLICE_CONTENT_HASH_MISMATCH",
                                    f"{item_location}/content_sha256",
                                    "content_sha256 does not match exact selected artifact bytes",
                                )
                            )
            else:
                receipt = item["content_receipt"]
                if (
                    receipt is None
                    or receipt["canonical_url"] != item["content_locator"]
                    or receipt["raw_sha256"]
                    != source["source_identity"]["raw_sha256"]
                    or receipt["raw_bytes"]
                    != source["source_identity"]["raw_bytes"]
                    or item["content_sha256"]
                    != receipt["selected_sha256"]
                    or (
                        selector["kind"] == "byte-range"
                        and receipt["selected_bytes"] != end - start
                    )
                    or (
                        selector["kind"] == "whole-source"
                        and (
                            receipt["selected_sha256"]
                            != receipt["raw_sha256"]
                            or receipt["selected_bytes"]
                            != receipt["raw_bytes"]
                        )
                    )
                ):
                    findings.append(
                        _finding(
                            "SLICE_EXTERNAL_RECEIPT_INVALID",
                            f"{item_location}/content_receipt",
                            "external slice locator and content hash do not match "
                            "the resolver receipt",
                        )
                    )
                    canonical = (
                        projection["canonical_snapshot"]
                        if projection is not None
                        else None
                    )
                    canonical_source = (
                        canonical["sources_by_id"].get(source["source_id"])
                        if canonical is not None
                        else None
                    )
                    if (
                        receipt is not None
                        and canonical_source is not None
                        and receipt["raw_sha256"]
                        == canonical_source["derived_snapshot"]["sha256"]
                    ):
                        findings.append(
                            _finding(
                                "SOURCE_RAW_DERIVED_IDENTITY_CONFUSED",
                                f"{item_location}/content_receipt/raw_sha256",
                                "external source receipt binds derived Markdown bytes "
                                "instead of upstream raw source bytes",
                            )
                        )
                    external_receipt_ceiling = "blocked"
                else:
                    receipt_ceiling = _resolver_receipt_ceiling(
                        receipt,
                        authority_id=(
                            corpus.data["authority_id"]
                            if corpus is not None
                            else ""
                        ),
                        consumer_registry=consumer_registry,
                        consumer_registry_sha256=consumer_registry_sha256,
                        selection_binding={
                            "source_id": source["source_id"],
                            "raw_sha256": source["source_identity"][
                                "raw_sha256"
                            ],
                            "raw_bytes": source["source_identity"][
                                "raw_bytes"
                            ],
                            "selector": selector,
                            "selected_sha256": item["content_sha256"],
                            "selected_bytes": receipt["selected_bytes"],
                        },
                        repository_root=repository_root,
                        location=f"{item_location}/content_receipt",
                        findings=findings,
                        portable_context=portable_context,
                    )
                    external_receipt_ceiling = min(
                        (external_receipt_ceiling, receipt_ceiling),
                        key=STATUS_RANK.__getitem__,
                    )

        preserved_ranges: list[tuple[int, int, str]] = []
        preservation_ids: set[str] = set()
        for preserved_index, preserved in enumerate(source["preserved_ranges"]):
            preserved_location = (
                f"{source_location}/preserved_ranges/{preserved_index}"
            )
            preservation_id = preserved["preservation_id"]
            if preservation_id in preservation_ids:
                findings.append(
                    _finding(
                        "SLICE_PRESERVATION_ID_DUPLICATE",
                        preserved_location,
                        "preservation_id values must be unique within a source",
                    )
                )
            preservation_ids.add(preservation_id)
            start = preserved["start_byte"]
            end = preserved["end_byte_exclusive"]
            if start >= end or end > extent:
                findings.append(
                    _finding(
                        "SLICE_PRESERVED_RANGE_INVALID",
                        preserved_location,
                        "preserved byte range must be nonempty and within source extent",
                    )
                )
                continue
            preserved_ranges.append((start, end, preservation_id))
            if source_raw is None:
                if not source_bytes_externalized:
                    preservation_unverified = True
                if (
                    data["status"] == "complete"
                    and not source_bytes_externalized
                ):
                    findings.append(
                        _finding(
                            "SLICE_PRESERVED_RANGE_UNVERIFIED",
                            preserved_location,
                            "complete preservation requires exact local source bytes",
                        )
                    )
            else:
                actual_hash = hashlib.sha256(source_raw[start:end]).hexdigest()
                if actual_hash != preserved["content_sha256"]:
                    findings.append(
                        _finding(
                            "SLICE_PRESERVED_HASH_MISMATCH",
                            f"{preserved_location}/content_sha256",
                            "preserved range hash does not match exact source bytes",
                        )
                    )

        for left_index, (left_start, left_end, _left_id) in enumerate(
            preserved_ranges
        ):
            competing = valid_ranges + preserved_ranges[left_index + 1 :]
            if any(
                max(left_start, right_start) < min(left_end, right_end)
                for right_start, right_end, _right_id in competing
            ):
                findings.append(
                    _finding(
                        "SLICE_PRESERVED_RANGE_INVALID",
                        f"{source_location}/preserved_ranges/{left_index}",
                        "preserved ranges must not overlap slices or one another",
                    )
                )

        actual_overlaps: set[tuple[str, str]] = set()
        for left_index, (left_start, left_end, left_id) in enumerate(valid_ranges):
            for right_start, right_end, right_id in valid_ranges[left_index + 1 :]:
                if max(left_start, right_start) < min(left_end, right_end):
                    actual_overlaps.add(tuple(sorted((left_id, right_id))))
        reviewed_overlaps = {
            tuple(sorted((item["left_slice_id"], item["right_slice_id"])))
            for item in source["reviewed_overlaps"]
        }
        if (
            len(reviewed_overlaps) != len(source["reviewed_overlaps"])
            or actual_overlaps != reviewed_overlaps
        ):
            findings.append(
                _finding(
                    "SLICE_OVERLAP_INVALID",
                    f"{source_location}/reviewed_overlaps",
                    "reviewed overlap pairs must exactly match calculated byte-range overlaps",
                )
            )

        actual_orphans: list[tuple[int, int]] = []
        if source_byte_closure:
            cursor = 0
            for start, end, _range_id in sorted(valid_ranges + preserved_ranges):
                if start > cursor:
                    actual_orphans.append((cursor, start))
                cursor = max(cursor, end)
            if cursor < extent:
                actual_orphans.append((cursor, extent))
        elif source["preserved_ranges"] or source["reviewed_orphans"]:
            findings.append(
                _finding(
                    "SLICE_SELECTOR_LAYER_PARTITION_INVALID",
                    source_location,
                    "raw-source preservation and orphan ledgers are unavailable "
                    "when selectors do not establish raw byte closure",
                )
            )
        reviewed_orphans = [
            (item["start_byte"], item["end_byte_exclusive"])
            for item in source["reviewed_orphans"]
        ]
        if (
            len(set(reviewed_orphans)) != len(reviewed_orphans)
            or sorted(set(actual_orphans)) != sorted(set(reviewed_orphans))
        ):
            findings.append(
                _finding(
                    "SLICE_ORPHAN_RANGE_INVALID",
                    f"{source_location}/reviewed_orphans",
                    "reviewed orphan ranges must exactly match uncovered source bytes",
                )
            )

        losses = source["loss_ledger"]
        _check_unique_ids(
            losses,
            "loss_id",
            code="SLICE_LOSS_ID_DUPLICATE",
            location=f"{source_location}/loss_ledger",
            findings=findings,
        )
        loss_ids = set(_ids(losses, "loss_id"))
        losses_by_id = {item["loss_id"]: item for item in losses}
        if source["reviewed_orphans"]:
            material_unresolved = True
            if data["status"] == "complete":
                findings.append(
                    _finding(
                        "SLICE_ORPHAN_PRESENT",
                        f"{source_location}/reviewed_orphans",
                        "any source-byte orphan limits slicing assurance to partial",
                    )
                )
        for orphan_index, orphan in enumerate(source["reviewed_orphans"]):
            loss = losses_by_id.get(orphan["loss_id"])
            if (
                loss is None
                or loss["disposition"] != orphan["disposition"]
                or loss["disposition"] not in {
                    "external-only",
                    "omitted",
                    "unresolved",
                }
            ):
                findings.append(
                    _finding(
                        "SLICE_ORPHAN_LOSS_INVALID",
                        f"{source_location}/reviewed_orphans/{orphan_index}",
                        "every orphan must resolve to a loss with the same non-preserved "
                        "disposition",
                    )
                )
            elif loss["severity"] == "blocking":
                blocking_loss_present = True
        slice_links_by_loss: dict[str, set[str]] = {}
        for slice_index, item in enumerate(slices):
            if not set(item["loss_ids"]).issubset(loss_ids):
                findings.append(
                    _finding(
                        "SLICE_LOSS_REF_INVALID",
                        f"{source_location}/slices/{slice_index}/loss_ids",
                        "slice loss_ids contain an unresolved loss ledger reference",
                    )
                )
            for loss_id in item["loss_ids"]:
                if loss_id in loss_ids:
                    slice_links_by_loss.setdefault(loss_id, set()).add(
                        item["slice_id"]
                    )
        slice_id_set = set(slice_ids)
        for loss_index, loss in enumerate(losses):
            affected_slice_ids = set(loss["affected_slice_ids"])
            if not affected_slice_ids.issubset(slice_id_set):
                findings.append(
                    _finding(
                        "LOSS_SLICE_REF_INVALID",
                        f"{source_location}/loss_ledger/{loss_index}/affected_slice_ids",
                        "loss ledger entry references a slice outside its source",
                    )
                )
            if affected_slice_ids != slice_links_by_loss.get(
                loss["loss_id"], set()
            ):
                findings.append(
                    _finding(
                        "SLICE_LOSS_LINKAGE_MISMATCH",
                        f"{source_location}/loss_ledger/{loss_index}",
                        "loss affected_slice_ids must exactly equal the reverse "
                        "slice loss_ids linkage",
                    )
                )
            if loss["severity"] == "blocking":
                blocking_loss_present = True
            unresolved = loss["disposition"] in {"omitted", "unresolved"}
            if unresolved and loss["severity"] == "material":
                material_unresolved = True

    if data["blockers"] or blocking_loss_present:
        maximum = "blocked"
    elif (
        material_unresolved
        or preservation_unverified
        or (
            non_byte_selector
            and processor_ceiling != "complete"
        )
        or derived_selector
    ) and maximum == "complete":
        maximum = "partial"
    maximum = min(
        (maximum, processor_ceiling, external_receipt_ceiling),
        key=STATUS_RANK.__getitem__,
    )
    _status_overclaim(
        data["status"],
        maximum,
        location=f"{location}/status",
        findings=findings,
    )


def _license_review_findings(
    record: LoadedRecord,
    *,
    corpora: dict[str, LoadedRecord],
    slice_manifests: Iterable[LoadedRecord],
    authorities: dict[str, dict[str, Any]],
    consumer_registry: dict[str, Any],
    consumer_registry_sha256: str,
    repository_root: Path,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> None:
    data = record.data
    review_id = data["license_review_id"]
    location = f"license/{review_id}"
    corpus = _check_ref(
        data["corpus_ref"],
        id_field="corpus_id",
        records=corpora,
        location=f"{location}/corpus_ref",
        findings=findings,
    )
    authority = authorities.get(data["authority_id"])
    if corpus is not None and data["authority_id"] != corpus.data["authority_id"]:
        findings.append(
            _finding(
                "LICENSE_AUTHORITY_MISMATCH",
                f"{location}/authority_id",
                "license review authority_id differs from the corpus authority_id",
            )
        )
    if authority is None:
        findings.append(
            _finding(
                "AUTHORITY_REF_UNRESOLVED",
                f"{location}/authority_id",
                "license review authority_id is not active",
            )
        )

    evidence_ceiling = "complete"
    for evidence_index, evidence in enumerate(data["evidence"]):
        evidence_location = f"{location}/evidence/{evidence_index}"
        if evidence["hash_basis"] == "unattested-external-locator":
            evidence_ceiling = "partial"
            if data["status"] == "complete":
                findings.append(
                    _finding(
                        "LICENSE_TERMS_EVIDENCE_UNATTESTED",
                        f"{evidence_location}/hash_basis",
                        "an external terms locator without exact local terms "
                        "bytes cannot support complete license assurance",
                    )
                )
            continue
        reference = evidence["terms_content_ref"]
        if (
            reference["sha256"] != evidence["sha256"]
        ):
            findings.append(
                _finding(
                    "LICENSE_TERMS_CONTENT_REF_MISMATCH",
                    f"{evidence_location}/terms_content_ref/sha256",
                    "terms_content_ref must bind the same exact terms bytes as "
                    "the evidence sha256",
                )
            )
            evidence_ceiling = "blocked"
            continue
        if not _is_license_terms_content_path(reference["path"]):
            findings.append(
                _finding(
                    "LICENSE_TERMS_CONTENT_NAMESPACE_INVALID",
                    f"{evidence_location}/terms_content_ref/path",
                    "exact license terms must live under a skill "
                    "official-source-pack license-terms directory",
                )
            )
            evidence_ceiling = "blocked"
            continue
        raw = _safe_local_bytes(
            repository_root,
            reference["path"],
            location=f"{evidence_location}/terms_content_ref/path",
            findings=findings,
            failure_code="LICENSE_TERMS_CONTENT_UNAVAILABLE",
            portable_context=portable_context,
        )
        if (
            raw is None
            or _artifact_sha256(raw) != evidence["sha256"]
        ):
            findings.append(
                _finding(
                    "LICENSE_TERMS_CONTENT_HASH_MISMATCH",
                    f"{evidence_location}/sha256",
                    "declared exact terms hash does not match the bytes at "
                    "terms_content_ref",
                )
            )
            evidence_ceiling = "blocked"

    trust = data["trust_attestation"]
    trust_ceiling = "complete"
    if trust["registry_sha256"] != consumer_registry_sha256:
        findings.append(
            _finding(
                "LICENSE_TRUST_REGISTRY_HASH_MISMATCH",
                f"{location}/trust_attestation/registry_sha256",
                "license trust does not bind the exact canonical consumer registry bytes",
            )
        )
        trust_ceiling = "blocked"
    elif trust["trust_mode"] == "unverified":
        trust_ceiling = "partial"
        if data["status"] == "complete":
            findings.append(
                _finding(
                    "LICENSE_TRUST_UNVERIFIED",
                    f"{location}/trust_attestation/trust_mode",
                    "self-declared evidence and reviewer identity cannot support "
                    "complete license assurance",
                )
            )
    else:
        central_trust = consumer_registry["license_trust"].get(trust["trust_id"])
        if (
            central_trust is None
            or central_trust["authority_id"] != data["authority_id"]
            or data["reviewer"]["reviewer_id"]
            not in central_trust["reviewer_ids"]
            or data["evidence"] != central_trust["evidence"]
        ):
            findings.append(
                _finding(
                    "LICENSE_TRUST_INVALID",
                    f"{location}/trust_attestation",
                    "license evidence and reviewer do not exactly match a central "
                    "pinned trust entry",
                )
            )
            trust_ceiling = "blocked"
        elif trust["trust_mode"] == "platform-attested":
            reference = trust["attestation_ref"]
            if reference != central_trust["platform_attestation_ref"]:
                findings.append(
                    _finding(
                        "LICENSE_TRUST_INVALID",
                        f"{location}/trust_attestation/attestation_ref",
                        "platform attestation differs from the central pinned entry",
                    )
                )
                trust_ceiling = "blocked"
            else:
                raw = _safe_local_bytes(
                    repository_root,
                    reference["path"],
                    location=f"{location}/trust_attestation/attestation_ref/path",
                    findings=findings,
                    failure_code="LICENSE_ATTESTATION_UNAVAILABLE",
                    portable_context=portable_context,
                )
                if (
                    raw is None
                    or _artifact_sha256(raw) != reference["sha256"]
                ):
                    findings.append(
                        _finding(
                            "LICENSE_ATTESTATION_HASH_MISMATCH",
                            f"{location}/trust_attestation/attestation_ref/sha256",
                            "platform attestation hash does not match exact local bytes",
                        )
                    )
                    trust_ceiling = "blocked"
        else:
            trust_ceiling = "partial"
            if data["status"] == "complete":
                findings.append(
                    _finding(
                        "LICENSE_PLATFORM_ATTESTATION_REQUIRED",
                        f"{location}/trust_attestation/trust_mode",
                        "central pinning without a matching platform "
                        "attestation cannot support complete license assurance",
                    )
                )

    rules = data["storage_rules"]
    rule_keys = [
        (item["artifact_kind"], item["source_material_class"])
        for item in rules
    ]
    if len(rule_keys) != len(set(rule_keys)):
        findings.append(
            _finding(
                "LICENSE_STORAGE_RULE_DUPLICATE",
                f"{location}/storage_rules",
                "artifact_kind and source_material_class rule keys must be unique",
            )
        )
    _check_unique_ids(
        data["evidence"],
        "evidence_id",
        code="LICENSE_EVIDENCE_ID_DUPLICATE",
        location=f"{location}/evidence",
        findings=findings,
    )
    evidence_ids = set(_ids(data["evidence"], "evidence_id"))
    rule_by_kind = {
        (item["artifact_kind"], item["source_material_class"]): item
        for item in rules
    }
    protected_invalid = False
    obligation_unknown = False
    obligation_false_certainty = False
    for rule_index, rule in enumerate(rules):
        if not set(rule["license_evidence_refs"]).issubset(evidence_ids):
            findings.append(
                _finding(
                    "LICENSE_EVIDENCE_REF_INVALID",
                    f"{location}/storage_rules/{rule_index}/license_evidence_refs",
                    "storage rule references missing license evidence",
                )
            )
        material = rule["source_material_class"]
        modes = set(rule["allowed_storage_modes"])
        rule_unknown = any(
            rule[field] == "unknown"
            for field in LICENSE_OBLIGATION_FIELDS
        )
        obligation_unknown = obligation_unknown or rule_unknown
        if rule_unknown and not rule["limitations"]:
            findings.append(
                _finding(
                    "LICENSE_OBLIGATION_LIMITATION_MISSING",
                    f"{location}/storage_rules/{rule_index}/limitations",
                    "unknown license obligations require an explicit limitation",
                )
            )
        if material in {"credential", "private-artifact"} and modes != {"excluded"}:
            protected_invalid = True
        if material == "restricted-potential" and not modes.issubset(
            {"metadata-only", "external-runtime-only", "excluded"}
        ):
            protected_invalid = True
        if protected_invalid:
            findings.append(
                _finding(
                    "LICENSE_PROTECTED_MATERIAL_INVALID",
                    f"{location}/storage_rules/{rule_index}",
                    "restricted potentials, credentials, and private artifacts "
                    "cannot be generically embedded or cached",
                )
            )
            protected_invalid = False

    authority_ceiling_invalid = False
    if authority is not None:
        central_license = authority["license_policy"]
        identity = data["license_identity"]
        if central_license["status"] == "unknown":
            if (
                identity["verification"] == "verified"
                or identity["identifier"] is not None
                or identity["terms_urls"]
            ):
                authority_ceiling_invalid = True
            if trust["trust_mode"] == "unverified":
                for rule_index, rule in enumerate(rules):
                    if any(
                        rule[field] != "unknown"
                        for field in LICENSE_OBLIGATION_FIELDS
                    ):
                        obligation_false_certainty = True
                        findings.append(
                            _finding(
                                "LICENSE_OBLIGATION_FALSE_CERTAINTY",
                                f"{location}/storage_rules/{rule_index}",
                                "unknown central license evidence cannot support "
                                "self-declared true or false obligation values",
                            )
                        )
        elif identity["verification"] == "verified":
            if (
                identity["identifier"] != central_license["identifier"]
                or set(identity["terms_urls"])
                != set(central_license["terms_urls"])
            ):
                authority_ceiling_invalid = True
        elif identity["identifier"] is not None or identity["terms_urls"]:
            authority_ceiling_invalid = True
        if identity["verification"] == "verified":
            for evidence_index, evidence in enumerate(data["evidence"]):
                if (
                    evidence["hash_basis"] == "exact-terms-content-bytes"
                    and evidence["locator"] not in identity["terms_urls"]
                ):
                    authority_ceiling_invalid = True
                    findings.append(
                        _finding(
                            "LICENSE_TERMS_LOCATOR_IDENTITY_MISMATCH",
                            f"{location}/evidence/{evidence_index}/locator",
                            "exact terms bytes must be located by one of the "
                            "verified license identity terms URLs",
                        )
                    )
        bundle_policy = authority["redistribution_policy"]["bundle_content"]
        if bundle_policy == "forbidden" and any(
            "embedded-open" in rule["allowed_storage_modes"] for rule in rules
        ):
            authority_ceiling_invalid = True
        if authority_ceiling_invalid:
            findings.append(
                _finding(
                    "LICENSE_AUTHORITY_CEILING_EXCEEDED",
                    location,
                    "license review contradicts or widens the central authority "
                    "license and redistribution ceiling",
                )
            )

    corpus_id = data["corpus_ref"]["corpus_id"]
    for manifest in slice_manifests:
        if manifest.data["corpus_ref"]["corpus_id"] != corpus_id:
            continue
        for source_index, source in enumerate(manifest.data["sources"]):
            for slice_index, item in enumerate(source["slices"]):
                slice_location = (
                    f"slices/{manifest.data['slice_manifest_id']}/sources/"
                    f"{source_index}/slices/{slice_index}"
                )
                rule = rule_by_kind.get(
                    (item["artifact_kind"], item["source_material_class"])
                )
                if rule is None:
                    findings.append(
                        _finding(
                            "LICENSE_STORAGE_RULE_MISSING",
                            f"{slice_location}/artifact_kind",
                            "used artifact/material lane has no explicit license storage rule",
                        )
                    )
                    continue
                if item["storage_mode"] not in rule["allowed_storage_modes"]:
                    findings.append(
                        _finding(
                            "LICENSE_STORAGE_MODE_FORBIDDEN",
                            f"{slice_location}/storage_mode",
                            "slice storage mode is not explicitly allowed by the "
                            "applicable license review rule",
                        )
                    )

    expired = False
    if data["review_expires_utc"] is not None:
        expires = datetime.fromisoformat(
            data["review_expires_utc"]
            .replace("Z", "+00:00")
            .replace("z", "+00:00")
        )
        expired = expires <= datetime.now(timezone.utc)
    if data["license_review_id"] in data["supersedes_review_ids"]:
        findings.append(
            _finding(
                "LICENSE_SUPERSESSION_INVALID",
                f"{location}/supersedes_review_ids",
                "a license review cannot supersede itself",
            )
        )

    if (
        data["blockers"]
        or authority_ceiling_invalid
        or obligation_false_certainty
    ):
        maximum = "blocked"
    elif (
        data["license_identity"]["verification"] != "verified"
        or any(rule["assessment"] == "unresolved" for rule in rules)
        or obligation_unknown
        or expired
    ):
        maximum = "partial"
    else:
        maximum = "complete"
    maximum = min(
        (maximum, trust_ceiling, evidence_ceiling),
        key=STATUS_RANK.__getitem__,
    )
    _status_overclaim(
        data["status"],
        maximum,
        location=f"{location}/status",
        findings=findings,
    )


def _coverage_findings(
    record: LoadedRecord,
    *,
    corpora: dict[str, LoadedRecord],
    slice_manifests: dict[str, LoadedRecord],
    license_reviews: dict[str, LoadedRecord],
    scope_inventories: dict[str, LoadedRecord],
    consumer_registry: dict[str, Any],
    consumer_registry_sha256: str,
    repository_root: Path,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> None:
    data = record.data
    location = f"coverage/{data['coverage_id']}"
    binding_valid = True
    binding_ids: list[str] = []
    central_bindings = {
        item["binding_id"]: item for item in consumer_registry["bindings"]
    }
    resolved_binding_pairs: set[tuple[str, str]] = set()
    for index, reference in enumerate(data["consumer_binding_refs"]):
        binding_id = reference["binding_id"]
        binding_ids.append(binding_id)
        if reference["registry_sha256"] != consumer_registry_sha256:
            findings.append(
                _finding(
                    "COVERAGE_CONSUMER_REGISTRY_HASH_MISMATCH",
                    f"{location}/consumer_binding_refs/{index}/registry_sha256",
                    "consumer binding does not reference exact canonical registry bytes",
                )
            )
            binding_valid = False
        binding = central_bindings.get(binding_id)
        if (
            binding is None
            or binding["consumer_skill_id"] != data["skill_id"]
            or binding["purpose"] != "official-document-coverage"
            or binding["claim_ceiling"] != "registered-skill-scope"
        ):
            findings.append(
                _finding(
                    "COVERAGE_CONSUMER_BINDING_INVALID",
                    f"{location}/consumer_binding_refs/{index}",
                    "binding does not centrally allow this Skill as a documentation "
                    "consumer",
                )
            )
            binding_valid = False
        else:
            resolved_binding_pairs.add(
                (binding["authority_id"], binding["provider_id"])
            )
    if len(binding_ids) != len(set(binding_ids)):
        findings.append(
            _finding(
                "COVERAGE_CONSUMER_BINDING_INVALID",
                f"{location}/consumer_binding_refs",
                "consumer binding IDs must be unique",
            )
        )
        binding_valid = False

    references = (
        ("corpus_refs", "corpus_id", corpora),
        ("slice_manifest_refs", "slice_manifest_id", slice_manifests),
        ("license_review_refs", "license_review_id", license_reviews),
    )
    resolved: list[LoadedRecord] = []
    for field, id_field, records in references:
        _check_unique_ids(
            data[field],
            id_field,
            code="COVERAGE_RECORD_REF_DUPLICATE",
            location=f"{location}/{field}",
            findings=findings,
        )
        for index, reference in enumerate(data[field]):
            target = _check_ref(
                reference,
                id_field=id_field,
                records=records,
                location=f"{location}/{field}/{index}",
                findings=findings,
            )
            if target is not None:
                resolved.append(target)
        if set(_ids(data[field], id_field)) != set(records):
            findings.append(
                _finding(
                    "COVERAGE_RECORD_SET_INVALID",
                    f"{location}/{field}",
                    "coverage references must exactly identify the supplied record set",
                )
            )

    scope_inventory = _check_ref(
        data["scope_inventory_ref"],
        id_field="inventory_id",
        records=scope_inventories,
        location=f"{location}/scope_inventory_ref",
        findings=findings,
    )
    if set(scope_inventories) != {data["scope_inventory_ref"]["inventory_id"]}:
        findings.append(
            _finding(
                "COVERAGE_RECORD_SET_INVALID",
                f"{location}/scope_inventory_ref",
                "coverage must reference exactly the supplied scope inventory",
            )
        )
    if scope_inventory is not None:
        resolved.append(scope_inventory)
        if scope_inventory.data["skill_id"] != data["skill_id"]:
            findings.append(
                _finding(
                    "COVERAGE_SCOPE_SKILL_MISMATCH",
                    f"{location}/skill_id",
                    "coverage skill_id differs from its canonical scope inventory",
                )
            )
        if data["declared_scope"] != scope_inventory.data["subjects"]:
            findings.append(
                _finding(
                    "COVERAGE_SCOPE_INVENTORY_MISMATCH",
                    f"{location}/declared_scope",
                    "declared_scope must exactly equal the independent canonical "
                    "scope inventory subjects",
                )
            )

    corpus_ids = set(_ids(data["corpus_refs"], "corpus_id"))
    required_binding_pairs = {
        (item.data["authority_id"], item.data["provider_id"])
        for item in corpora.values()
    }
    if resolved_binding_pairs != required_binding_pairs:
        findings.append(
            _finding(
                "COVERAGE_CONSUMER_BINDING_INVALID",
                f"{location}/consumer_binding_refs",
                "consumer bindings must exactly cover every referenced "
                "authority/provider pair; default policy is deny",
            )
        )
        binding_valid = False
    for index, manifest in enumerate(slice_manifests.values()):
        if manifest.data["corpus_ref"]["corpus_id"] not in corpus_ids:
            findings.append(
                _finding(
                    "COVERAGE_CORPUS_LINK_INVALID",
                    f"{location}/slice_manifest_refs/{index}",
                    "slice manifest points to an unreferenced corpus",
                )
            )
    slice_corpus_ids = [
        manifest.data["corpus_ref"]["corpus_id"]
        for manifest in slice_manifests.values()
    ]
    if (
        len(slice_corpus_ids) != len(set(slice_corpus_ids))
        or set(slice_corpus_ids) != corpus_ids
    ):
        findings.append(
            _finding(
                "COVERAGE_SLICE_CORPUS_PARTITION_INVALID",
                f"{location}/slice_manifest_refs",
                "coverage requires exactly one slice manifest for every corpus",
            )
        )
    license_corpus_ids = [
        item.data["corpus_ref"]["corpus_id"] for item in license_reviews.values()
    ]
    if len(license_corpus_ids) != len(set(license_corpus_ids)):
        findings.append(
            _finding(
                "COVERAGE_LICENSE_AMBIGUOUS",
                f"{location}/license_review_refs",
                "MVP coverage requires exactly one license review per corpus",
            )
        )
    if set(license_corpus_ids) != corpus_ids:
        findings.append(
            _finding(
                "COVERAGE_LICENSE_SET_INVALID",
                f"{location}/license_review_refs",
                "license reviews must cover every referenced corpus exactly once",
            )
        )

    subjects = data["declared_scope"]
    mappings = data["mappings"]
    _check_unique_ids(
        subjects,
        "subject_id",
        code="COVERAGE_SUBJECT_ID_DUPLICATE",
        location=f"{location}/declared_scope",
        findings=findings,
    )
    _check_unique_ids(
        mappings,
        "subject_id",
        code="COVERAGE_SUBJECT_ID_DUPLICATE",
        location=f"{location}/mappings",
        findings=findings,
    )
    subject_ids = set(_ids(subjects, "subject_id"))
    mapping_ids = set(_ids(mappings, "subject_id"))
    if subject_ids != mapping_ids:
        findings.append(
            _finding(
                "COVERAGE_SUBJECT_PARTITION_INVALID",
                f"{location}/mappings",
                "every declared scope subject must have exactly one mapping and "
                "undeclared mapping subjects are forbidden",
            )
        )

    mapping_valid = True
    subjects_by_id = {
        item["subject_id"]: item
        for item in subjects
    }
    official_mappings: list[dict[str, Any]] = []
    skill_path = (
        scope_inventory.data["skill_registry_binding"]["skill_path"]
        if scope_inventory is not None
        else None
    )
    scope_source_pairs = (
        {
            (item["path"], item["sha256"])
            for item in scope_inventory.data["skill_source_refs"]
        }
        if scope_inventory is not None
        else set()
    )
    for mapping_index, mapping in enumerate(mappings):
        mapping_location = f"{location}/mappings/{mapping_index}"
        subject = subjects_by_id.get(mapping["subject_id"])
        if subject is None:
            continue
        evidence_class = subject["evidence_class"]
        if evidence_class == "official-provider-required":
            official_mappings.append(mapping)
            expected_disposition = {
                "complete": "covered",
                "partial": "partial",
                "blocked": "blocked",
            }[mapping["coverage_status"]]
            if (
                mapping["official_disposition"] != expected_disposition
                or mapping["local_evidence_refs"]
                or (
                    mapping["coverage_status"] in {"complete", "partial"}
                    and not mapping["slice_refs"]
                )
                or (
                    mapping["coverage_status"] == "blocked"
                    and (
                        not mapping["rationale"]
                        or not mapping["limitations"]
                    )
                )
            ):
                mapping_valid = False
                findings.append(
                    _finding(
                        "COVERAGE_EVIDENCE_CLASS_CONFUSION",
                        mapping_location,
                        "covered or partial official subjects need official "
                        "slice references; blocked subjects need an explicit "
                        "gap rationale; local evidence cannot substitute either",
                    )
                )
        else:
            if (
                mapping["official_disposition"]
                not in {"not-applicable", "excluded"}
                or mapping["slice_refs"]
                or not mapping["local_evidence_refs"]
                or not mapping["rationale"]
            ):
                mapping_valid = False
                findings.append(
                    _finding(
                        "COVERAGE_EVIDENCE_CLASS_CONFUSION",
                        mapping_location,
                        "non-official subjects must be explicitly not-applicable or "
                        "excluded from official coverage and cite local evidence",
                    )
                )
            for ref_index, reference in enumerate(mapping["local_evidence_refs"]):
                ref_location = (
                    f"{mapping_location}/local_evidence_refs/{ref_index}"
                )
                path = PurePosixPath(reference["path"])
                if (
                    skill_path is None
                    or not path.is_relative_to(PurePosixPath(skill_path))
                    or (reference["path"], reference["sha256"])
                    not in scope_source_pairs
                    or skill_registry.source_tree_hash_path_excluded(
                        path.relative_to(PurePosixPath(skill_path))
                    )
                ):
                    mapping_valid = False
                    findings.append(
                        _finding(
                            "COVERAGE_LOCAL_EVIDENCE_INVALID",
                            ref_location,
                            "local evidence must exactly reuse a hashed non-pack "
                            "scope-source reference",
                        )
                    )
                    continue
                raw = _safe_local_bytes(
                    repository_root,
                    reference["path"],
                    location=ref_location,
                    findings=findings,
                    failure_code="COVERAGE_LOCAL_EVIDENCE_INVALID",
                    portable_context=portable_context,
                )
                if (
                    raw is None
                    or _artifact_sha256(raw) != reference["sha256"]
                ):
                    mapping_valid = False
                    findings.append(
                        _finding(
                            "COVERAGE_LOCAL_EVIDENCE_INVALID",
                            ref_location,
                            "local evidence hash does not match exact repository bytes",
                        )
                    )

    slices_by_manifest: dict[str, set[str]] = {}
    for manifest_id, manifest in slice_manifests.items():
        slices_by_manifest[manifest_id] = {
            item["slice_id"]
            for source in manifest.data["sources"]
            for item in source["slices"]
        }
    for mapping_index, mapping in enumerate(mappings):
        for ref_index, reference in enumerate(mapping["slice_refs"]):
            slice_ids = slices_by_manifest.get(reference["slice_manifest_id"])
            if (
                slice_ids is None
                or reference["slice_id"] not in slice_ids
            ):
                findings.append(
                    _finding(
                        "COVERAGE_SLICE_REF_INVALID",
                        f"{location}/mappings/{mapping_index}/slice_refs/{ref_index}",
                        "coverage slice reference does not resolve",
                    )
                )

    if data["blockers"] or not binding_valid or not mapping_valid:
        maximum = "blocked"
    elif any(item.data["status"] == "blocked" for item in resolved) or any(
        item["coverage_status"] == "blocked" for item in official_mappings
    ):
        maximum = "blocked"
    elif any(item.data["status"] != "complete" for item in resolved) or any(
        item["coverage_status"] != "complete" for item in official_mappings
    ):
        maximum = "partial"
    elif not official_mappings:
        maximum = "partial"
    else:
        maximum = "complete"
    _status_overclaim(
        data["status"],
        maximum,
        location=f"{location}/status",
        findings=findings,
    )


def validate_files(
    *,
    corpus_paths: Iterable[Path],
    slice_paths: Iterable[Path],
    license_review_paths: Iterable[Path],
    scope_inventory_path: Path,
    coverage_path: Path,
    source_root: Path | None = None,
    enforce_canonical_pack_closure: bool = False,
    portable_context: PortableValidationContext | None = None,
) -> ValidationResult:
    """Load and validate one closed official-document coverage bundle."""

    corpus_path_list = [Path(item) for item in corpus_paths]
    slice_path_list = [Path(item) for item in slice_paths]
    license_path_list = [Path(item) for item in license_review_paths]
    findings: list[Finding] = []
    if portable_context is None:
        repository_root = repo_root()
        contracts_directory = repository_root / "contracts"
        authority_registry_path = (
            repository_root / "registry" / "official-source-authorities.yaml"
        )
        interface_registry_path = (
            repository_root / "registry" / "interface-registry.yaml"
        )
        software_registry_path = (
            repository_root / "registry" / "software-registry.yaml"
        )
        skill_registry_path = (
            repository_root / "registry" / "skill-registry.yaml"
        )
        consumer_registry_path = (
            repository_root / "registry" / "official-document-consumers.yaml"
        )
        content_root = (
            Path(source_root) if source_root is not None else repository_root
        )
    else:
        try:
            repository_root = portable_context.repository_root.resolve(strict=True)
            contracts_directory = portable_context.contracts_directory.resolve(
                strict=True
            )
            interface_registry_path = (
                portable_context.interface_registry_path.resolve(strict=True)
            )
            authority_registry_path = (
                portable_context.authority_registry_path.resolve(strict=True)
            )
            software_registry_path = (
                portable_context.software_registry_path.resolve(strict=True)
            )
            skill_registry_path = (
                portable_context.skill_registry_path.resolve(strict=True)
            )
            consumer_registry_path = (
                portable_context.consumer_registry_path.resolve(strict=True)
            )
            if not contracts_directory.is_relative_to(repository_root):
                raise ValueError("contracts_directory escapes repository_root")
            for registry_path in (
                interface_registry_path,
                authority_registry_path,
                software_registry_path,
                skill_registry_path,
                consumer_registry_path,
            ):
                if not registry_path.is_relative_to(repository_root):
                    raise ValueError("registry path escapes repository_root")
            content_root = (
                Path(source_root).resolve(strict=True)
                if source_root is not None
                else repository_root
            )
            if content_root != repository_root:
                raise ValueError(
                    "portable source_root must equal portable repository_root"
                )
            if not isinstance(portable_context.externalized_receipts, Mapping):
                raise ValueError("externalized_receipts must be a mapping")
            for receipt_path, receipt in (
                portable_context.externalized_receipts.items()
            ):
                pure = (
                    PurePosixPath(receipt_path)
                    if isinstance(receipt_path, str)
                    else None
                )
                if (
                    pure is None
                    or pure.is_absolute()
                    or not pure.parts
                    or "\\" in receipt_path
                    or any(part in {"", ".", ".."} for part in pure.parts)
                    or not isinstance(receipt, Mapping)
                    or set(receipt) != {"path", "sha256", "size"}
                    or receipt.get("path") != receipt_path
                    or not _valid_sha256(receipt.get("sha256"))
                    or not isinstance(receipt.get("size"), int)
                    or isinstance(receipt.get("size"), bool)
                    or receipt["size"] < 0
                    or receipt["size"] > MAX_CONTENT_BYTES
                ):
                    raise ValueError(
                        f"invalid externalized receipt for {receipt_path!r}"
                    )
            portable_context = PortableValidationContext(
                repository_root=repository_root,
                contracts_directory=contracts_directory,
                interface_registry_path=interface_registry_path,
                authority_registry_path=authority_registry_path,
                software_registry_path=software_registry_path,
                skill_registry_path=skill_registry_path,
                consumer_registry_path=consumer_registry_path,
                externalized_receipts=portable_context.externalized_receipts,
            )
        except (OSError, ValueError) as exc:
            return ValidationResult(
                findings=(
                    _finding(
                        "PORTABLE_VALIDATION_CONTEXT_INVALID",
                        "portable-context",
                        f"portable validation context is invalid: {exc}",
                    ),
                ),
                assurance_status="invalid",
            )
    selectors = (
        "official-corpus-manifest@1.0",
        "document-slice-manifest@1.0",
        "official-source-license-review@1.0",
        "skill-document-scope-inventory@1.0",
        "skill-document-coverage@1.0",
    )
    try:
        catalog = validate_contract.load_catalog(contracts_directory)
        for selector in selectors:
            contract = catalog.resolve(selector)
            lifecycle = validate_contract.runtime_interface_lifecycle(
                contract,
                catalog,
                registry_file=interface_registry_path,
                repository_root=repository_root,
            )
            if lifecycle != "active":
                findings.append(
                    _finding(
                        "CONTRACT_LIFECYCLE_INVALID",
                        selector,
                        f"official-document contract lifecycle is {lifecycle!r}, not active",
                    )
                )
    except (
        validate_contract.CatalogError,
        validate_contract.ContractSelectionError,
    ) as exc:
        return ValidationResult(
            findings=(
                _finding(
                    "CONTRACT_CATALOG_INVALID",
                    "contracts",
                    f"canonical offline contract catalog is invalid: {exc}",
                ),
            ),
            assurance_status="invalid",
        )
    try:
        authority_data = official_source_authorities.load_registry(
            authority_registry_path
        )
        software_data = load_yaml_strict(
            software_registry_path,
            "software-registry.yaml",
        )
        software_failures = software_registry.validation_errors(software_data)
        if software_failures:
            raise ValueError("; ".join(software_failures))
        authority_failures = official_source_authorities.validation_errors(
            authority_data,
            software_data=software_data,
            source_root=repository_root,
            externalized_receipts=(
                portable_context.externalized_receipts
                if portable_context is not None
                else None
            ),
            used_externalized_paths=(
                portable_context.used_externalized_paths
                if portable_context is not None
                else None
            ),
        )
        if authority_failures:
            raise ValueError("; ".join(authority_failures))
        authority_projection = (
            official_source_authorities.active_authority_snapshot(
                authority_data,
                software_data=software_data,
                source_root=repository_root,
                externalized_receipts=(
                    portable_context.externalized_receipts
                    if portable_context is not None
                    else None
                ),
                used_externalized_paths=(
                    portable_context.used_externalized_paths
                    if portable_context is not None
                    else None
                ),
            )
        )
        authorities = {
            authority_id: entry
            for authority_id, entry in authority_data["authorities"].items()
            if entry["lifecycle"] == "active"
        }
    except (OSError, ValueError) as exc:
        return ValidationResult(
            findings=(
                _finding(
                    "AUTHORITY_REGISTRY_INVALID",
                    "registry/official-source-authorities.yaml",
                    f"canonical authority registry is invalid: {exc}",
                ),
            ),
            assurance_status="invalid",
        )
    try:
        skill_registry_raw = strict_json.read_bytes_bounded(
            skill_registry_path,
            "skill-registry.yaml",
            max_bytes=MAX_CONTENT_BYTES,
        )
        skill_registry_data = load_yaml_strict(
            skill_registry_path,
            "skill-registry.yaml",
        )
        if (
            not isinstance(skill_registry_data, dict)
            or set(skill_registry_data) != {"schema_version", "skills"}
            or skill_registry_data["schema_version"] != "1.0"
            or not isinstance(skill_registry_data["skills"], dict)
        ):
            raise ValueError("skill registry has an invalid root contract")
        interface_registry_data = load_yaml_strict(
            interface_registry_path,
            "interface-registry.yaml",
        )
        interface_failures = interface_registry.validation_errors(
            interface_registry_data,
            repository_root,
        )
        if interface_failures:
            raise ValueError("; ".join(interface_failures))
        skill_failures = skill_registry.validation_errors(
            skill_registry_data,
            software_data=software_data,
            interface_data=interface_registry_data,
        )
        if skill_failures:
            raise ValueError("; ".join(skill_failures))
        skill_registry_sha256 = hashlib.sha256(skill_registry_raw).hexdigest()

        consumer_registry_raw = strict_json.read_bytes_bounded(
            consumer_registry_path,
            "official-document-consumers.yaml",
            max_bytes=MAX_CONTENT_BYTES,
        )
        consumer_registry = load_yaml_strict(
            consumer_registry_path,
            "official-document-consumers.yaml",
        )
        consumer_failures = consumer_registry_validation_errors(
            consumer_registry,
            skills=skill_registry_data["skills"],
            authorities=authorities,
            root=repository_root,
            portable_context=portable_context,
        )
        if consumer_failures:
            raise ValueError("; ".join(consumer_failures))
        consumer_registry_sha256 = hashlib.sha256(
            consumer_registry_raw
        ).hexdigest()
    except (
        OSError,
        ValueError,
        strict_json.StrictJSONError,
    ) as exc:
        return ValidationResult(
            findings=(
                _finding(
                    "OFFICIAL_DOCUMENT_TRUST_REGISTRY_INVALID",
                    "registry/official-document-consumers.yaml",
                    f"canonical Skill/consumer trust registry is invalid: {exc}",
                ),
            ),
            assurance_status="invalid",
        )
    if enforce_canonical_pack_closure:
        findings.extend(
            canonical_pack_binding_closure_findings(
                root=repository_root,
                skills=skill_registry_data["skills"],
                consumer_registry=consumer_registry,
            )
        )
    if not corpus_path_list:
        findings.append(
            _finding("REQUIRED_RECORD_MISSING", "corpora", "at least one corpus is required")
        )
    if not slice_path_list:
        findings.append(
            _finding(
                "REQUIRED_RECORD_MISSING",
                "slice_manifests",
                "at least one slice manifest is required",
            )
        )
    if not license_path_list:
        findings.append(
            _finding(
                "REQUIRED_RECORD_MISSING",
                "license_reviews",
                "at least one license review is required",
            )
        )

    corpora_loaded, load_findings = _load_records(
        corpus_path_list,
        catalog=catalog,
        selector="official-corpus-manifest@1.0",
        id_field="corpus_id",
        label="corpus",
    )
    findings.extend(load_findings)
    slices_loaded, load_findings = _load_records(
        slice_path_list,
        catalog=catalog,
        selector="document-slice-manifest@1.0",
        id_field="slice_manifest_id",
        label="slices",
    )
    findings.extend(load_findings)
    licenses_loaded, load_findings = _load_records(
        license_path_list,
        catalog=catalog,
        selector="official-source-license-review@1.0",
        id_field="license_review_id",
        label="license",
    )
    findings.extend(load_findings)
    scope_loaded, load_findings = _load_records(
        [Path(scope_inventory_path)],
        catalog=catalog,
        selector="skill-document-scope-inventory@1.0",
        id_field="inventory_id",
        label="scope-inventory",
    )
    findings.extend(load_findings)
    coverage_loaded, load_findings = _load_records(
        [Path(coverage_path)],
        catalog=catalog,
        selector="skill-document-coverage@1.0",
        id_field="coverage_id",
        label="coverage",
    )
    findings.extend(load_findings)

    corpora = _index(corpora_loaded, "corpus_id")
    slice_manifests = _index(slices_loaded, "slice_manifest_id")
    license_reviews = _index(licenses_loaded, "license_review_id")
    scope_inventories = _index(scope_loaded, "inventory_id")

    for corpus in corpora_loaded:
        _corpus_findings(
            corpus,
            authorities=authorities,
            authority_projection=authority_projection,
            consumer_registry=consumer_registry,
            consumer_registry_sha256=consumer_registry_sha256,
            source_root=content_root,
            repository_root=repository_root,
            findings=findings,
            portable_context=portable_context,
        )
    for inventory in scope_loaded:
        _scope_inventory_findings(
            inventory,
            repository_root=repository_root,
            skill_registry_data=skill_registry_data,
            skill_registry_sha256=skill_registry_sha256,
            consumer_registry=consumer_registry,
            findings=findings,
            portable_context=portable_context,
        )
    for manifest in slices_loaded:
        _slice_manifest_findings(
            manifest,
            corpora=corpora,
            authorities=authorities,
            authority_projection=authority_projection,
            consumer_registry=consumer_registry,
            consumer_registry_sha256=consumer_registry_sha256,
            source_root=content_root,
            repository_root=repository_root,
            findings=findings,
            portable_context=portable_context,
        )
    for review in licenses_loaded:
        _license_review_findings(
            review,
            corpora=corpora,
            slice_manifests=slices_loaded,
            authorities=authorities,
            consumer_registry=consumer_registry,
            consumer_registry_sha256=consumer_registry_sha256,
            repository_root=repository_root,
            findings=findings,
            portable_context=portable_context,
        )
    if len(coverage_loaded) == 1:
        _coverage_findings(
            coverage_loaded[0],
            corpora=corpora,
            slice_manifests=slice_manifests,
            license_reviews=license_reviews,
            scope_inventories=scope_inventories,
            consumer_registry=consumer_registry,
            consumer_registry_sha256=consumer_registry_sha256,
            repository_root=repository_root,
            findings=findings,
            portable_context=portable_context,
        )

    normalized = _deduplicate_findings(findings)
    if normalized or len(coverage_loaded) != 1:
        assurance_status = "invalid"
    else:
        statuses = [
            record.data["status"]
            for record in (
                *corpora_loaded,
                *slices_loaded,
                *licenses_loaded,
                *scope_loaded,
                coverage_loaded[0],
            )
        ]
        if (
            portable_context is not None
            and portable_context.used_externalized_paths
        ):
            statuses.append("partial")
        assurance_status = min(statuses, key=STATUS_RANK.__getitem__)
    return ValidationResult(
        findings=normalized,
        assurance_status=assurance_status,
        externalized_paths=(
            tuple(sorted(portable_context.used_externalized_paths))
            if portable_context is not None
            else ()
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        action="append",
        required=True,
        help="official-corpus-manifest JSON; repeat for multiple corpora",
    )
    parser.add_argument(
        "--slices",
        type=Path,
        action="append",
        required=True,
        help="document-slice-manifest JSON; repeat for multiple manifests",
    )
    parser.add_argument(
        "--license-review",
        type=Path,
        action="append",
        required=True,
        help="official-source-license-review JSON; repeat for multiple reviews",
    )
    parser.add_argument(
        "--scope-inventory",
        type=Path,
        required=True,
        help="one canonical skill-document-scope-inventory JSON",
    )
    parser.add_argument(
        "--coverage",
        type=Path,
        required=True,
        help="one skill-document-coverage JSON",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=repo_root(),
        help=(
            "root for embedded corpus and slice artifacts; Skill scope and "
            "central trust paths always resolve against the canonical repository "
            "(default: repository root)"
        ),
    )
    parser.add_argument(
        "--enforce-canonical-pack-closure",
        action="store_true",
        help=(
            "require the repository-wide canonical pack authority/provider "
            "pair set to exactly equal the central consumer binding set"
        ),
    )
    args = parser.parse_args()

    result = validate_files(
        corpus_paths=args.corpus,
        slice_paths=args.slices,
        license_review_paths=args.license_review,
        scope_inventory_path=args.scope_inventory,
        coverage_path=args.coverage,
        source_root=args.source_root,
        enforce_canonical_pack_closure=args.enforce_canonical_pack_closure,
    )
    if result.findings:
        for finding in result.findings:
            print(
                f"ERROR {finding.code} {finding.location}: {finding.message}",
                file=sys.stderr,
            )
        return EXIT_INVALID
    if result.assurance_status != "complete":
        print(
            "BLOCKED: official-document bundle is structurally and semantically "
            f"valid but assurance_status={result.assurance_status}; "
            "no complete-coverage claim is allowed"
        )
        return EXIT_INCOMPLETE
    print(
        "PASS: official-document corpus partition, ordered slices, loss ledger, "
        "license storage policy, record hashes, and Skill scope coverage are complete"
    )
    return EXIT_PASS


if __name__ == "__main__":
    raise SystemExit(main())
