#!/usr/bin/env python3
"""Validate official-document corpus, slices, scope, and Skill coverage.

This validator validates four technical records, enforces offline technical
closure, and closes cross-record technical invariants that JSON Schema
cannot express. It is offline-only and reads strict JSON records.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
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
def _pack_source_id(*parts: object) -> str:
    """Mirror the bounded builder ID projection for official inventory units."""

    raw = "-".join(str(item) for item in parts if str(item))
    slug = re.sub(r"[^A-Za-z0-9._:-]+", "-", raw).strip("-.:").lower()
    if len(slug) > 120:
        suffix = hashlib.sha256(slug.encode("utf-8")).hexdigest()[:16]
        slug = f"{slug[:103].rstrip('-.:')}-{suffix}"
    return slug


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
    required_root = {
        "schema_version",
        "default_policy",
        "bindings",
        "processors",
        "resolver_trust",
    }
    for key in data:
        if not isinstance(key, str) or key not in required_root:
            errors.append(f"<root>: unexpected key '{key}'")
    for key in sorted(required_root):
        if key not in data:
            errors.append(f"<root>: missing required field '{key}'")
    if len(errors) > 0:
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


def _excluded_locator_is_safe(url: str) -> bool:
    """Validate inert exclusion metadata without granting content authority."""

    try:
        parsed = urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError):
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and port in (None, 443)
        and "?" not in url
        and "#" not in url
    )


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


def _processor_ceiling_v11(
    processor: dict[str, Any],
    *,
    expected_input_sha256: str,
    expected_output_sha256: str,
    declared_status: str,
    consumer_registry: dict[str, Any],
    root: Path,
    location: str,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> str:
    def _strip_file_bytes(ref: Mapping[str, Any] | None, *, field: str) -> dict[str, Any] | None:
        if not isinstance(ref, Mapping):
            return None
        cleaned = dict(ref)
        expected_bytes = cleaned.get("bytes")
        if isinstance(expected_bytes, int) and expected_bytes > 0:
            raw = _safe_local_bytes(
                root,
                cleaned.get("path"),
                location=f"{location}/{field}/path",
                findings=findings,
                failure_code="PROCESSOR_ARTIFACT_UNAVAILABLE",
                portable_context=portable_context,
            )
            if raw is not None and _artifact_size(raw) != expected_bytes:
                findings.append(
                    _finding(
                        "PROCESSOR_ARTIFACT_BYTES_MISMATCH",
                        f"{location}/{field}/bytes",
                        "processor artifact byte count does not match local bytes",
                    )
                )
        cleaned.pop("bytes", None)
        return cleaned

    assurance = processor.get("assurance_mode")
    if assurance == "unverified":
        hashes_match = (
            processor.get("input_sha256") == expected_input_sha256
            and processor.get("output_sha256") == expected_output_sha256
        )
        if not hashes_match:
            findings.append(
                _finding(
                    "PROCESSOR_IO_MISMATCH",
                    location,
                    "discovery processor input/output identity does not match the exact "
                    "validated record projection",
                )
            )
            return "blocked"
        if declared_status == "complete":
            findings.append(
                _finding(
                    "PROCESSOR_TRUST_UNVERIFIED",
                    f"{location}/assurance_mode",
                    "discovery processor has unverified assurance mode",
                )
            )
        return "partial"
    if assurance not in {"pinned", "attested"}:
        findings.append(
            _finding(
                "CORPUS_PROCESSOR_ASSURANCE_INVALID",
                f"{location}/assurance_mode",
                "discovery processor assurance_mode is not supported for corpus v1.1",
            )
        )
        return "blocked"
    translated = {
        "enumerator_id": processor["processor_id"],
        "enumerator_version": processor["processor_version"],
        "trust_mode": (
            "central-pinned" if assurance == "pinned" else "platform-attested"
        ),
        "implementation_ref": _strip_file_bytes(
            processor.get("implementation_ref"), field="implementation_ref"
        ),
        "configuration_ref": _strip_file_bytes(
            processor.get("configuration_ref"), field="configuration_ref"
        ),
        "dependency_lock_ref": _strip_file_bytes(
            processor.get("dependency_lock_ref"), field="dependency_lock_ref"
        ),
        "input_sha256": processor.get("input_sha256"),
        "output_sha256": processor.get("output_sha256"),
        "attestation_id": processor.get("attestation_id"),
    }
    return _processor_ceiling(
        translated,
        kind="enumerator",
        expected_input_sha256=expected_input_sha256,
        expected_output_sha256=expected_output_sha256,
        declared_status=declared_status,
        consumer_registry=consumer_registry,
        root=root,
        location=location,
        findings=findings,
        portable_context=portable_context,
    )


def _corpus_v11_discovery_inventory(
    discovery: dict[str, Any],
    *,
    authority: dict[str, Any],
    source_root: Path,
    location: str,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> str | None:
    inventory = discovery.get("inventory")
    if not isinstance(inventory, dict):
        findings.append(
            _finding(
                "CORPUS_DISCOVERY_INVENTORY_INVALID",
                f"{location}/discovery/inventory",
                "discovery inventory must be an exact embedded/external/metadata identity",
            )
        )
        return None
    mode = inventory.get("content_mode")
    if mode == "embedded-content":
        if set(inventory) != {
            "content_mode",
            "locator",
            "sha256",
            "bytes",
        }:
            findings.append(
                _finding(
                    "CORPUS_DISCOVERY_INVENTORY_INVALID",
                    f"{location}/discovery/inventory",
                    "embedded discovery inventory must be exact embedded-content identity",
                )
            )
            return None
        if (
            not isinstance(inventory.get("sha256"), str)
            or not _valid_sha256(inventory["sha256"])
            or not isinstance(inventory.get("bytes"), int)
            or isinstance(inventory.get("bytes"), bool)
            or inventory["bytes"] <= 0
        ):
            findings.append(
                _finding(
                    "CORPUS_DISCOVERY_INVENTORY_INVALID",
                    f"{location}/discovery/inventory",
                    "embedded discovery inventory requires valid sha256 and bytes",
                )
            )
            return None
        raw = _safe_local_bytes(
            source_root,
            inventory["locator"],
            location=f"{location}/discovery/inventory/locator",
            findings=findings,
            failure_code="CORPUS_DISCOVERY_INVENTORY_UNAVAILABLE",
            portable_context=portable_context,
        )
        if raw is None:
            return None
        if _artifact_sha256(raw) != inventory["sha256"]:
            findings.append(
                _finding(
                    "CORPUS_DISCOVERY_INVENTORY_HASH_MISMATCH",
                    f"{location}/discovery/inventory/sha256",
                    "discovery inventory sha256 does not match exact embedded inventory bytes",
                )
            )
            return None
        if _artifact_size(raw) != inventory["bytes"]:
            findings.append(
                _finding(
                    "CORPUS_DISCOVERY_INVENTORY_BYTES_MISMATCH",
                    f"{location}/discovery/inventory/bytes",
                    "discovery inventory byte count does not match embedded payload",
                )
                )
            return None
        return inventory["sha256"]
    if mode == "external-content":
        if set(inventory) != {"content_mode", "locator", "receipt"}:
            findings.append(
                _finding(
                    "CORPUS_DISCOVERY_INVENTORY_INVALID",
                    f"{location}/discovery/inventory",
                    "external discovery inventory must be exact external-content identity",
                )
            )
            return None
        if not _url_matches_authority(inventory.get("locator", ""), authority):
            findings.append(
                _finding(
                    "AUTHORITY_DISCOVERY_INVENTORY_LOCATOR_MISMATCH",
                    f"{location}/discovery/inventory/locator",
                    "discovery inventory locator is outside authority policy",
                )
            )
            return None
        receipt = inventory.get("receipt")
        if (
            not isinstance(receipt, dict)
            or set(receipt)
            != {"retrieval_method", "retrieved_utc", "raw_sha256", "raw_bytes"}
            or not _valid_sha256(receipt.get("raw_sha256"))
            or not isinstance(receipt.get("raw_bytes"), int)
            or isinstance(receipt.get("raw_bytes"), bool)
            or receipt.get("raw_bytes") <= 0
        ):
            findings.append(
                _finding(
                    "CORPUS_DISCOVERY_INVENTORY_INVALID",
                    f"{location}/discovery/inventory/receipt",
                    "external discovery inventory requires an exact valid receipt",
                )
            )
            return None
        return str(receipt["raw_sha256"])
    if mode == "metadata-only":
        if set(inventory) != {"content_mode", "locator", "identity"}:
            findings.append(
                _finding(
                    "CORPUS_DISCOVERY_INVENTORY_INVALID",
                    f"{location}/discovery/inventory",
                    "metadata-only discovery inventory must be exact metadata identity",
                )
            )
            return None
        locator = inventory.get("locator")
        if authority and not _url_matches_authority(str(locator), authority):
            findings.append(
                _finding(
                    "AUTHORITY_DISCOVERY_INVENTORY_LOCATOR_MISMATCH",
                    f"{location}/discovery/inventory/locator",
                    "discovery inventory locator is outside authority policy",
                )
            )
            return None
        identity = inventory.get("identity")
        if (
            not isinstance(identity, dict)
            or set(identity) != {"sha256", "bytes"}
            or not _valid_sha256(identity.get("sha256"))
            or not isinstance(identity.get("bytes"), int)
            or isinstance(identity.get("bytes"), bool)
            or identity.get("bytes") <= 0
        ):
            findings.append(
                _finding(
                    "CORPUS_DISCOVERY_INVENTORY_INVALID",
                    f"{location}/discovery/inventory/identity",
                    "metadata discovery inventory requires exact byte identity",
                )
            )
            return None
        return str(identity["sha256"])
    findings.append(
        _finding(
            "CORPUS_DISCOVERY_INVENTORY_FORMAT_INVALID",
            f"{location}/discovery/inventory/content_mode",
            "discovery inventory content mode must be embedded-content, external-content, "
            "or metadata-only",
        )
    )
    return None


def _source_inventory_v11_entries(
    source_inventory: Mapping[str, Any],
    *,
    authority: dict[str, Any],
    location: str,
    source_root: Path,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> tuple[set[str], set[str], bool]:
    if not isinstance(source_inventory, Mapping):
        findings.append(
            _finding(
                "CORPUS_SOURCE_INVENTORY_INVALID",
                f"{location}/source_inventory",
                "source_inventory must be a mapping keyed by source_id",
            )
        )
        return set(), set(), False
    included: set[str] = set()
    excluded: set[str] = set()
    valid = True
    for source_id, source in source_inventory.items():
        source_location = f"{location}/source_inventory/{source_id}"
        if not isinstance(source_id, str):
            findings.append(
                _finding(
                    "CORPUS_SOURCE_ID_INVALID",
                    source_location,
                    "source_inventory key must be a string source_id",
                )
            )
            valid = False
            continue
        if not isinstance(source, dict):
            findings.append(
                _finding(
                    "CORPUS_SOURCE_RECORD_INVALID",
                    source_location,
                    "source_inventory entry must be an object",
                )
            )
            valid = False
            continue
        disposition = source.get("disposition")
        if disposition == "included":
            required = {
                "disposition",
                "title",
                "source_kind",
                "source_identity",
                "subject_ids",
                "loss_ids",
            }
            included.add(source_id)
        elif disposition == "excluded":
            required = {
                "disposition",
                "title",
                "source_kind",
                "source_identity",
                "reason_code",
                "rationale",
            }
            excluded.add(source_id)
        else:
            findings.append(
                _finding(
                    "CORPUS_SOURCE_DISPOSITION_INVALID",
                    f"{source_location}/disposition",
                    "source disposition must be included or excluded",
                )
            )
            valid = False
            continue
        if set(source) != required:
            findings.append(
                _finding(
                    "CORPUS_SOURCE_RECORD_INVALID",
                    source_location,
                    "source inventory entry must contain the exact technical fields",
                )
            )
            valid = False
        source_kind = source.get("source_kind")
        identity = source.get("source_identity")
        if not isinstance(identity, dict):
            findings.append(
                _finding(
                    "CORPUS_SOURCE_IDENTITY_INVALID",
                    f"{source_location}/source_identity",
                    "source_identity must be an explicit identity object",
                )
            )
            valid = False
            continue
        content_mode = identity.get("content_mode")
        if disposition == "excluded":
            if content_mode != "excluded":
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity/content_mode",
                        "excluded sources must use excluded content_mode",
                    )
                )
                valid = False
                continue
            if set(identity) != {
                "content_mode",
                "locator",
                "inventory_entry_identity",
            } or not isinstance(identity.get("inventory_entry_identity"), dict):
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity",
                        "excluded source_identity must be exact excluded identity",
                    )
                )
                valid = False
                continue
            if not _excluded_locator_is_safe(
                str(identity.get("locator")),
            ):
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_LOCATOR_MISMATCH",
                        f"{source_location}/source_identity/locator",
                        "excluded source locator is not safe inert HTTPS metadata",
                    )
                )
                valid = False
            entry_identity = identity["inventory_entry_identity"]
            if (
                set(entry_identity) != {"sha256", "bytes"}
                or not _valid_sha256(entry_identity.get("sha256"))
                or not isinstance(entry_identity.get("bytes"), int)
                or isinstance(entry_identity.get("bytes"), bool)
                or entry_identity.get("bytes") <= 0
            ):
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity/inventory_entry_identity",
                        "excluded inventory_entry_identity must be exact byte identity",
                    )
                )
                valid = False
            continue
        if content_mode not in {
            "embedded-content",
            "external-content",
            "metadata-only",
        }:
            findings.append(
                _finding(
                    "CORPUS_SOURCE_IDENTITY_INVALID",
                    f"{source_location}/source_identity/content_mode",
                    "included sources require embedded/external/metadata-only identity",
                )
            )
            valid = False
            continue
        if content_mode == "embedded-content":
            if set(identity) != {
                "content_mode",
                "locator",
                "sha256",
                "bytes",
            }:
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity",
                        "embedded source_identity must be exact embedded identity",
                    )
                )
                valid = False
                continue
            if (
                not _valid_sha256(identity.get("sha256"))
                or not isinstance(identity.get("bytes"), int)
                or isinstance(identity.get("bytes"), bool)
                or identity.get("bytes") <= 0
            ):
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity",
                        "embedded source_identity requires valid sha256 and bytes",
                    )
                )
                valid = False
                continue
            raw = _safe_local_bytes(
                source_root,
                identity["locator"],
                location=f"{source_location}/source_identity/locator",
                findings=findings,
                failure_code="CORPUS_SOURCE_CONTENT_UNAVAILABLE",
                portable_context=portable_context,
            )
            if raw is None:
                valid = False
            else:
                if _artifact_sha256(raw) != identity["sha256"]:
                    findings.append(
                        _finding(
                            "CORPUS_SOURCE_CONTENT_HASH_MISMATCH",
                            f"{source_location}/source_identity/sha256",
                            "embedded source content sha256 does not match exact bytes",
                        )
                    )
                    valid = False
                if _artifact_size(raw) != identity["bytes"]:
                    findings.append(
                        _finding(
                            "CORPUS_SOURCE_CONTENT_BYTES_MISMATCH",
                            f"{source_location}/source_identity/bytes",
                            "embedded source bytes does not match exact byte count",
                        )
                    )
                    valid = False
        elif content_mode == "external-content":
            if set(identity) != {"content_mode", "locator", "receipt"}:
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity",
                        "external source_identity must be exact external identity",
                    )
                )
                valid = False
                continue
            if authority and not _url_matches_authority(
                str(identity.get("locator")),
                authority,
            ):
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_LOCATOR_MISMATCH",
                        f"{source_location}/source_identity/locator",
                        "external source locator is outside authority policy",
                    )
                )
                valid = False
                continue
            receipt = identity.get("receipt")
            if (
                not isinstance(receipt, dict)
                or set(receipt)
                != {
                    "retrieval_method",
                    "retrieved_utc",
                    "raw_sha256",
                    "raw_bytes",
                }
                or not _valid_sha256(receipt.get("raw_sha256"))
                or not isinstance(receipt.get("raw_bytes"), int)
                or isinstance(receipt.get("raw_bytes"), bool)
                or receipt.get("raw_bytes") <= 0
            ):
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity/receipt",
                        "external source identity requires exact valid receipt",
                    )
                )
                valid = False
        else:
            locator = identity.get("locator")
            if authority and not _url_matches_authority(str(locator), authority):
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_LOCATOR_MISMATCH",
                        f"{source_location}/source_identity/locator",
                        "metadata source locator is outside authority policy",
                    )
                )
                valid = False
            if set(identity) != {"content_mode", "locator", "identity"}:
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity",
                        "metadata source_identity must be exact metadata identity",
                    )
                )
                valid = False
                continue
            metadata_identity = identity.get("identity")
            if (
                not isinstance(metadata_identity, dict)
                or set(metadata_identity) != {"sha256", "bytes"}
                or not _valid_sha256(metadata_identity.get("sha256"))
                or not isinstance(metadata_identity.get("bytes"), int)
                or isinstance(metadata_identity.get("bytes"), bool)
                or metadata_identity.get("bytes") <= 0
            ):
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity/identity",
                        "metadata source_identity requires exact byte identity",
                    )
                )
                valid = False
        if disposition == "included":
            if (
                not isinstance(source.get("subject_ids"), list)
                or not isinstance(source.get("loss_ids"), list)
            ):
                findings.append(
                    _finding(
                        "CORPUS_SOURCE_RECORD_INVALID",
                        source_location,
                        "included source must include subject_ids and loss_ids arrays",
                    )
                )
                valid = False
    return included, excluded, valid


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
    if data.get("schema_version") != "1.1":
        return

    location = f"corpus/{data['corpus_id']}"
    authority = authorities.get(data["authority_id"])
    projection = authority_projection.get(data["authority_id"])
    discovery = data["discovery"]
    maximum = "complete"
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
        if data["provider_id"] != authority["provider_id"]:
            findings.append(
                _finding(
                    "AUTHORITY_PROVIDER_MISMATCH",
                    f"{location}/provider_id",
                    "corpus provider_id differs from the registered authority provider",
                )
            )
            maximum = "blocked"
        if discovery["authority_root"] not in projection["canonical_urls"]:
            findings.append(
                _finding(
                    "AUTHORITY_DISCOVERY_ROOT_MISMATCH",
                    f"{location}/discovery/authority_root",
                    "discovery authority_root is not a registered canonical root",
                )
            )
            maximum = "blocked"
        if not authority_version_scope_compatible(
            data["version_scope"],
            projection["version_scopes"],
        ):
            findings.append(
                _finding(
                    "AUTHORITY_VERSION_SCOPE_MISMATCH",
                    f"{location}/version_scope",
                    "corpus version scope is not registered for this authority",
                )
            )
            maximum = "blocked"

    inventory_ceiling = "complete"
    inventory_sha = None
    if authority is not None:
        inventory_sha = _corpus_v11_discovery_inventory(
            discovery,
            authority=authority,
            source_root=source_root,
            location=location,
            findings=findings,
            portable_context=portable_context,
        )
        if inventory_sha is None:
            inventory_ceiling = "blocked"
    else:
        inventory_ceiling = "blocked"

    included, excluded, records_valid = _source_inventory_v11_entries(
        data.get("source_inventory", {}),
        authority=authority or {},
        location=location,
        source_root=source_root,
        findings=findings,
        portable_context=portable_context,
    )
    if not records_valid:
        maximum = "blocked"

    processor_ceiling = "blocked"
    if authority is not None:
        processor_ceiling = _processor_ceiling_v11(
            discovery["processor"],
            expected_input_sha256=inventory_sha if inventory_sha is not None else "",
            expected_output_sha256=_canonical_json_sha256(
                data.get("source_inventory", {})
            ),
            declared_status=data["status"],
            consumer_registry=consumer_registry,
            root=repository_root,
            location=f"{location}/discovery/processor",
            findings=findings,
            portable_context=portable_context,
        )
    if not discovery["upstream_universe_complete"]:
        maximum = min(maximum, "partial", key=STATUS_RANK.__getitem__)
    if data["blockers"]:
        maximum = "blocked"
    maximum = min(
        (maximum, inventory_ceiling, processor_ceiling),
        key=STATUS_RANK.__getitem__,
    )
    if not included and not excluded:
        findings.append(
            _finding(
                "CORPUS_SOURCE_PARTITION_INVALID",
                f"{location}/source_inventory",
                "source_inventory must partition into included or excluded source ids",
            )
        )
        maximum = "blocked"
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


def _slice_source_identity_projection(
    source_identity: Any,
) -> tuple[str, int] | None:
    if not isinstance(source_identity, Mapping):
        return None
    mode = source_identity.get("content_mode")
    if mode == "embedded-content":
        sha256 = source_identity.get("sha256")
        bytes_value = source_identity.get("bytes")
    elif mode == "external-content":
        receipt = source_identity.get("receipt")
        if not isinstance(receipt, Mapping):
            return None
        sha256 = receipt.get("raw_sha256")
        bytes_value = receipt.get("raw_bytes")
    elif mode == "metadata-only":
        identity = source_identity.get("identity")
        if not isinstance(identity, Mapping):
            return None
        sha256 = identity.get("sha256")
        bytes_value = identity.get("bytes")
    else:
        return None
    if (
        not _valid_sha256(sha256)
        or not isinstance(bytes_value, int)
        or isinstance(bytes_value, bool)
        or bytes_value <= 0
    ):
        return None
    return str(sha256), int(bytes_value)


def _slice_loss_accounting_ceiling(
    accounting: Mapping[str, Any],
    *,
    dimension: str,
    location: str,
    findings: list[Finding],
) -> str:
    if not isinstance(accounting, Mapping):
        findings.append(
            _finding(
                "SLICE_LOSS_ACCOUNTING_INVALID",
                location,
                f"{dimension} loss accounting must be an exact object",
            )
        )
        return "blocked"

    closure_status = accounting.get("closure_status", "partial")
    if not isinstance(closure_status, str) or closure_status not in STATUS_RANK:
        findings.append(
            _finding(
                "SLICE_LOSS_ACCOUNTING_INVALID",
                f"{location}/closure_status",
                f"{dimension} loss accounting closure_status is invalid",
            )
        )
        return "blocked"

    entries = accounting.get("entries", [])
    if not isinstance(entries, list):
        findings.append(
            _finding(
                "SLICE_LOSS_ACCOUNTING_INVALID",
                f"{location}/entries",
                f"{dimension} loss accounting entries must be an exact array",
            )
        )
        return "blocked"
    if len(entries) == 0:
        return closure_status

    seen_loss_ids = set[str]()
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            findings.append(
                _finding(
                    "SLICE_LOSS_ACCOUNTING_ENTRY_INVALID",
                    f"{location}/entries/{index}",
                    "loss accounting entry must be an exact object",
                )
            )
            return "blocked"
        loss_id = entry.get("loss_id")
        if not isinstance(loss_id, str) or not loss_id:
            findings.append(
                _finding(
                    "SLICE_LOSS_ACCOUNTING_ENTRY_INVALID",
                    f"{location}/entries/{index}/loss_id",
                    f"{dimension} loss accounting requires a non-empty loss_id",
                )
            )
            return "blocked"
        if loss_id in seen_loss_ids:
            findings.append(
                _finding(
                    "SLICE_LOSS_ID_DUPLICATE",
                    f"{location}/entries",
                    "loss_id values must be unique",
                )
            )
            return "blocked"
        seen_loss_ids.add(loss_id)
        disposition = entry.get("disposition")
        severity = entry.get("severity")
        if severity == "blocking":
            return "blocked"
        if closure_status == "complete" and disposition == "unresolved":
            findings.append(
                _finding(
                    "SLICE_LOSS_ACCOUNTING_OPEN",
                    f"{location}/entries/{index}",
                    f"{dimension} loss accounting cannot report unresolved losses when "
                    "closure_status is complete",
                )
            )
            return "partial"
    return closure_status


def _slice_processor_ceiling_v11(
    processor: Mapping[str, Any],
    *,
    expected_input_sha256: str,
    expected_output_sha256: str,
    declared_status: str,
    consumer_registry: dict[str, Any],
    root: Path,
    location: str,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> str:
    if not isinstance(processor, Mapping):
        findings.append(
            _finding(
                "PROCESSOR_TRUST_INVALID",
                location,
                "processor must be an exact object",
            )
        )
        return "blocked"

    assurance = processor.get("assurance_mode")
    processor_id = processor.get("processor_id")
    processor_version = processor.get("processor_version")

    if processor.get("input_sha256") != expected_input_sha256 or processor.get(
        "output_sha256"
    ) != expected_output_sha256:
        findings.append(
            _finding(
                "PROCESSOR_IO_MISMATCH",
                location,
                "processor input/output identity does not bind exact source identity "
                "or canonical projection",
            )
        )
        return "blocked"

    if assurance == "unverified":
        if processor.get("attestations"):
            findings.append(
                _finding(
                    "SLICE_PROCESSOR_ATTESTATION_INVALID",
                    f"{location}/assurance_mode",
                    "unverified processor cannot include attestations",
                )
            )
        if declared_status == "complete":
            findings.append(
                _finding(
                    "PROCESSOR_TRUST_UNVERIFIED",
                    f"{location}/assurance_mode",
                    "processor assurance mode is unverified",
                )
            )
        return "partial"

    if assurance not in {"pinned", "attested"}:
        findings.append(
            _finding(
                "PROCESSOR_TRUST_INVALID",
                f"{location}/assurance_mode",
                "processor assurance_mode is unsupported for document-slice-manifest v1.1",
            )
        )
        return "blocked"

    processors = consumer_registry.get("processors")
    if not isinstance(processors, Mapping):
        findings.append(
            _finding(
                "PROCESSOR_TRUST_INVALID",
                f"{location}/assurance_mode",
                "processor trust cannot resolve a consumer processor registry",
            )
        )
        return "blocked"

    if not isinstance(processor_id, str) or not processor_id:
        findings.append(
            _finding(
                "PROCESSOR_TRUST_INVALID",
                f"{location}/processor_id",
                "processor_id must be a non-empty string",
            )
        )
        return "blocked"
    if not isinstance(processor_version, str):
        findings.append(
            _finding(
                "PROCESSOR_TRUST_INVALID",
                f"{location}/processor_version",
                "processor_version must be a non-empty string",
            )
        )
        return "blocked"

    registered = processors.get(processor_id)
    if (
        not isinstance(registered, Mapping)
        or registered.get("kind") != "transformer"
        or registered.get("version") != processor_version
    ):
        findings.append(
            _finding(
                "PROCESSOR_TRUST_INVALID",
                f"{location}/processor_id",
                "processor must exactly match a registered transformer entry",
            )
        )
        return "blocked"

    attestations = processor.get("attestations")
    if not isinstance(attestations, list) or len(attestations) == 0:
        findings.append(
            _finding(
                "PROCESSOR_ATTESTATION_INVALID",
                f"{location}/attestations",
                "processor assurance requires non-empty attestations",
            )
        )
        return "blocked"

    required_refs = {
        "implementation": "implementation_ref",
        "configuration": "configuration_ref",
        "dependency-lock": "dependency_lock_ref",
    }
    artifact_refs: dict[str, Mapping[str, Any]] = {}
    seen_kinds = set[str]()
    seen_attestation_ids = set[str]()

    for index, attestation in enumerate(attestations):
        att_location = f"{location}/attestations/{index}"
        if not isinstance(attestation, Mapping):
            findings.append(
                _finding(
                    "SLICE_PROCESSOR_ATTESTATION_INVALID",
                    att_location,
                    "processor attestation must be an exact implementation/configuration/dependency-lock/execution entry",
                )
            )
            return "blocked"
        attestation_kind = attestation.get("kind")
        if not isinstance(attestation_kind, str) or not attestation_kind:
            findings.append(
                _finding(
                    "SLICE_PROCESSOR_ATTESTATION_INVALID",
                    f"{att_location}/kind",
                    "processor attestation kind must be a non-empty string",
                )
            )
            return "blocked"
        if attestation_kind in seen_kinds:
            findings.append(
                _finding(
                    "SLICE_PROCESSOR_ATTESTATION_DUPLICATE_KIND",
                    att_location,
                    "processor attestation kinds must be unique",
                )
            )
            return "blocked"
        seen_kinds.add(attestation_kind)

        attestation_id = attestation.get("attestation_id")
        if not isinstance(attestation_id, str) or not attestation_id:
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{att_location}/attestation_id",
                    "processor attestation_id must be a non-empty string",
                )
            )
            return "blocked"
        if attestation_id in seen_attestation_ids:
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{att_location}/attestation_id",
                    "processor attestation_id values must be unique",
                )
            )
            return "blocked"
        seen_attestation_ids.add(attestation_id)

        artifact = attestation.get("artifact")
        if not isinstance(artifact, Mapping):
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{att_location}/artifact",
                    "processor attestation artifact must be an exact object",
                )
            )
            return "blocked"

        artifact_path = artifact.get("path")
        artifact_sha256 = artifact.get("sha256")
        artifact_bytes = artifact.get("bytes")
        if (
            not isinstance(artifact_path, str)
            or not isinstance(artifact_bytes, int)
            or isinstance(artifact_bytes, bool)
            or artifact_bytes <= 0
            or not _valid_sha256(artifact_sha256)
        ):
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{att_location}/artifact",
                    "processor attestation artifact must include exact path and sha256 and positive bytes",
                )
            )
            return "blocked"

        raw = _safe_local_bytes(
            root,
            artifact_path,
            location=f"{att_location}/artifact",
            findings=findings,
            failure_code="PROCESSOR_ATTESTATION_UNAVAILABLE",
            portable_context=portable_context,
        )
        if raw is None or _artifact_size(raw) != artifact_bytes:
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_BYTES_MISMATCH",
                    f"{att_location}/artifact",
                    "processor attestation artifact size does not match local bytes",
                )
            )
            return "blocked"
        if _artifact_sha256(raw) != artifact_sha256:
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_HASH_MISMATCH",
                    f"{att_location}/artifact",
                    "processor attestation artifact hash does not match local bytes",
                )
            )
            return "blocked"

        artifact_refs[attestation_kind] = artifact
        registry_key = required_refs.get(attestation_kind)
        if registry_key is None:
            continue
        expected = registered.get(registry_key)
        if (
            not isinstance(expected, Mapping)
            or expected.get("path") != artifact_path
            or expected.get("sha256") != artifact_sha256
        ):
            findings.append(
                _finding(
                    "PROCESSOR_TRUST_INVALID",
                    att_location,
                    "processor attestation identity must exactly match the "
                    "registered transformer identity",
                )
            )
            return "blocked"

    for kind in required_refs:
        if kind not in artifact_refs:
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_MISSING",
                    f"{location}/attestations",
                    "transformer attestation set must include implementation/configuration/dependency-lock",
                )
            )
            return "blocked"

    if assurance == "attested":
        execution_artifact = artifact_refs.get("execution")
        if execution_artifact is None:
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{location}/attestations",
                    "attested processor requires execution attestation",
                )
            )
            return "blocked"

        execution_attestation_id = None
        for attestation in attestations:
            if (
                isinstance(attestation, Mapping)
                and attestation.get("kind") == "execution"
            ):
                execution_attestation_id = attestation.get("attestation_id")
                break
        if not isinstance(execution_attestation_id, str) or not execution_attestation_id:
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{location}/attestations",
                    "execution attestation must include non-empty attestation_id",
                )
            )
            return "blocked"

        attested_runs = registered.get("attested_runs")
        if not isinstance(attested_runs, list):
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{location}/attestations",
                    "processor attested assurance requires attested_runs in registry",
                )
            )
            return "blocked"
        run = None
        for item in attested_runs:
            if (
                isinstance(item, Mapping)
                and item.get("attestation_id") == execution_attestation_id
                and item.get("input_sha256") == expected_input_sha256
                and item.get("output_sha256") == expected_output_sha256
            ):
                run = item
                break
        if run is None:
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{location}/attestations",
                    "no attested run matches execution attestation_id and exact io",
                )
            )
            return "blocked"

        attestation_ref = run.get("attestation_ref")
        if not isinstance(attestation_ref, Mapping):
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{location}/attestations",
                    "matched attestation run must include exact attestation_ref",
                )
            )
            return "blocked"
        if (
            attestation_ref.get("path") != execution_artifact.get("path")
            or attestation_ref.get("sha256") != execution_artifact.get("sha256")
        ):
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_INVALID",
                    f"{location}/attestations",
                    "execution artifact must exactly match run.attestation_ref",
                )
            )
            return "blocked"
        if (
            isinstance(attestation_ref.get("bytes"), int)
            and attestation_ref.get("bytes") > 0
            and attestation_ref.get("bytes") != execution_artifact.get("bytes")
        ):
            findings.append(
                _finding(
                    "PROCESSOR_ATTESTATION_BYTES_MISMATCH",
                    f"{location}/attestations",
                    "execution artifact bytes must match run.attestation_ref",
                )
            )
            return "blocked"

    return "complete"


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
    def _lower_ceiling(current: str, candidate: str) -> str:
        return candidate if STATUS_RANK[candidate] < STATUS_RANK[current] else current

    data = record.data if isinstance(record.data, Mapping) else {}
    manifest_id = data.get("slice_manifest_id")
    if not isinstance(manifest_id, str) or not manifest_id:
        manifest_id = "<unknown>"
    location = f"slices/{manifest_id}"

    declared_status = data.get("status")
    if declared_status not in STATUS_RANK:
        findings.append(
            _finding(
                "SLICE_STATUS_INVALID",
                f"{location}/status",
                "slice manifest status must be complete, partial, or blocked",
            )
        )
        declared_status = "blocked"

    corpus_ref = data.get("corpus_ref")
    if not isinstance(corpus_ref, Mapping):
        findings.append(
            _finding(
                "SLICE_CORPUS_REF_INVALID",
                f"{location}/corpus_ref",
                "corpus_ref must be an exact object",
            )
        )
        corpus = None
        corpus_status = "blocked"
    else:
        corpus = _check_ref(
            corpus_ref,
            id_field="corpus_id",
            records=corpora,
            location=f"{location}/corpus_ref",
            findings=findings,
        )
        if corpus is None:
            corpus_status = "blocked"
        else:
            corpus_ref_sha = corpus_ref.get("sha256")
            if (
                isinstance(corpus_ref_sha, str)
                and corpus_ref_sha != corpus.raw_sha256
            ):
                corpus_status = "blocked"
            else:
                corpus_status = corpus.data.get("status")
                if corpus_status not in STATUS_RANK:
                    findings.append(
                        _finding(
                            "SLICE_CORPUS_STATUS_INVALID",
                            f"corpora/{corpus_ref.get('corpus_id', '<unknown>')}/status",
                            "corpus status must be complete, partial, or blocked",
                        )
                    )
                    corpus_status = "blocked"

    raw_sources = data.get("sources")
    if not isinstance(raw_sources, Mapping):
        findings.append(
            _finding(
                "SLICE_SOURCES_INVALID",
                f"{location}/sources",
                "sources must be an exact source-id to source mapping",
            )
        )
        raw_sources = {}

    blockers = data.get("blockers", [])
    if not isinstance(blockers, list):
        findings.append(
            _finding(
                "SLICE_BLOCKERS_INVALID",
                f"{location}/blockers",
                "blockers must be an exact array",
            )
        )
        blockers = []

    included_by_id: dict[str, dict[str, Any]] = {}
    corpus_source_ids: set[str] = set()
    if corpus is not None:
        source_inventory = corpus.data.get("source_inventory")
        if not isinstance(source_inventory, Mapping):
            findings.append(
                _finding(
                    "SLICE_CORPUS_SOURCE_INVENTORY_INVALID",
                    f"corpora/{corpus.data.get('corpus_id', '<unknown>')}/source_inventory",
                    "corpus source_inventory must be an exact map",
                )
            )
        else:
            for sid, source_entry in source_inventory.items():
                if (
                    isinstance(sid, str)
                    and isinstance(source_entry, Mapping)
                    and source_entry.get("disposition") == "included"
                ):
                    included_by_id[sid] = source_entry
                    corpus_source_ids.add(sid)

    sources: dict[str, Any] = {}
    for sid in raw_sources.keys():
        if not isinstance(sid, str):
            findings.append(
                _finding(
                    "SLICE_SOURCE_ID_INVALID",
                    f"{location}/sources",
                    "source id must be a safe string",
                )
            )
            continue
        sources[sid] = raw_sources[sid]

    manifest_source_ids = set(sources.keys())

    maximum = min((declared_status, corpus_status), key=STATUS_RANK.__getitem__)
    if manifest_source_ids != corpus_source_ids and corpus is not None:
        maximum = _lower_ceiling(maximum, "partial")
        if declared_status == "complete":
            findings.append(
                _finding(
                    "SLICE_SOURCE_COVERAGE_INVALID",
                    f"{location}/sources",
                    "complete manifests must include every included corpus source",
                )
            )
    extras = manifest_source_ids - corpus_source_ids
    if extras:
        maximum = _lower_ceiling(maximum, "partial")
        findings.append(
            _finding(
                "SLICE_SOURCE_COVERAGE_INVALID",
                f"{location}/sources",
                "slice includes source IDs not marked included in referenced corpus",
            )
        )

    global_slice_ids: set[str] = set()
    subject_slice_refs: dict[str, set[str]] = {}

    for source_id, source in sources.items():
        source_location = f"{location}/sources/{source_id}"
        if not isinstance(source, Mapping):
            findings.append(
                _finding(
                    "SLICE_SOURCE_INVALID",
                    source_location,
                    "slice source entry must be an exact object",
                )
            )
            maximum = _lower_ceiling(maximum, "partial")
            continue

        corpus_source = included_by_id.get(source_id)

        source_identity = source.get("source_identity")
        if not isinstance(source_identity, Mapping):
            findings.append(
                _finding(
                    "SLICE_SOURCE_IDENTITY_INVALID",
                    f"{source_location}/source_identity",
                    "source_identity must be an exact object",
                )
            )
            maximum = _lower_ceiling(maximum, "partial")
            source_projection = None
        else:
            if corpus_source is not None and source_identity != corpus_source.get("source_identity"):
                findings.append(
                    _finding(
                        "SLICE_SOURCE_IDENTITY_MISMATCH",
                        f"{source_location}/source_identity",
                        "source identity must exactly match corpus source identity",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")
            source_projection = _slice_source_identity_projection(source_identity)
            if source_projection is None:
                findings.append(
                    _finding(
                        "SLICE_SOURCE_IDENTITY_INVALID",
                        f"{source_location}/source_identity",
                        "source identity must project to non-empty sha256 and positive bytes",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")

        raw_source_extent = source.get("raw_source_extent_bytes")
        if (
            not isinstance(raw_source_extent, int)
            or isinstance(raw_source_extent, bool)
            or raw_source_extent <= 0
        ):
            findings.append(
                _finding(
                    "SLICE_SOURCE_EXTENT_INVALID",
                    f"{source_location}/raw_source_extent_bytes",
                    "raw_source_extent_bytes must be a positive integer",
                )
            )
            raw_source_extent = 0
            maximum = _lower_ceiling(maximum, "partial")
        elif source_projection is not None and source_projection[1] != raw_source_extent:
            findings.append(
                _finding(
                    "SLICE_SOURCE_EXTENT_MISMATCH",
                    f"{source_location}/raw_source_extent_bytes",
                    "raw_source_extent_bytes must equal source_identity bytes",
                )
            )
            maximum = _lower_ceiling(maximum, "partial")

        source_mode = source_identity.get("content_mode") if isinstance(source_identity, Mapping) else None
        source_locator = source_identity.get("locator") if isinstance(source_identity, Mapping) else None

        source_local_raw = None
        if source_mode == "embedded-content" and isinstance(source_locator, str):
            source_local_raw = _safe_local_bytes(
                source_root,
                source_locator,
                location=f"{source_location}/source_identity/locator",
                findings=findings,
                failure_code="SLICE_SOURCE_ARTIFACT_UNAVAILABLE",
                portable_context=portable_context,
            )

        source_slices = source.get("slices")
        source_loss_accounting = source.get("source_loss_accounting")
        source_processor = source.get("processor")
        source_assurance_mode = (
            source_processor.get("assurance_mode")
            if isinstance(source_processor, Mapping)
            else None
        )
        source_is_replayable = isinstance(source_local_raw, bytes)

        source_processor_ceiling = _slice_processor_ceiling_v11(
            source_processor if isinstance(source_processor, Mapping) else {},
            expected_input_sha256=source_projection[0] if source_projection else "",
            expected_output_sha256=_canonical_json_sha256(
                {
                    "slices": source_slices if isinstance(source_slices, list) else [],
                    "source_loss_accounting": source_loss_accounting
                    if isinstance(source_loss_accounting, Mapping)
                    else {},
                }
            ),
            declared_status=declared_status,
            consumer_registry=consumer_registry,
            root=repository_root,
            location=f"{source_location}/processor",
            findings=findings,
            portable_context=portable_context,
        )
        maximum = _lower_ceiling(maximum, source_processor_ceiling)

        source_loss_ceiling = _slice_loss_accounting_ceiling(
            source_loss_accounting if isinstance(source_loss_accounting, Mapping) else {},
            dimension=f"sources/{source_id}/source_loss_accounting",
            location=f"{source_location}/source_loss_accounting",
            findings=findings,
        )
        maximum = _lower_ceiling(maximum, source_loss_ceiling)

        source_loss_entries: dict[str, dict[str, Any]] = {}
        source_loss_ids: set[str] = set()
        if isinstance(source_loss_accounting, Mapping):
            source_loss_raw_entries = source_loss_accounting.get("entries")
            if isinstance(source_loss_raw_entries, list):
                for entry in source_loss_raw_entries:
                    if not isinstance(entry, Mapping):
                        continue
                    loss_id = entry.get("loss_id")
                    if isinstance(loss_id, str) and loss_id:
                        source_loss_entries[loss_id] = dict(entry)
                        source_loss_ids.add(loss_id)

            if corpus_source is not None:
                corpus_loss_ids = {
                    item for item in corpus_source.get("loss_ids", []) if isinstance(item, str)
                }
                if corpus_loss_ids != source_loss_ids:
                    findings.append(
                        _finding(
                            "SLICE_SOURCE_LOSS_LINKAGE_INVALID",
                            f"{source_location}/source_loss_accounting",
                            "source.loss_ids must match corpus source.loss_ids exactly",
                        )
                    )
                    maximum = _lower_ceiling(maximum, "partial")

        if not isinstance(source_slices, list):
            findings.append(
                _finding(
                    "SLICE_SOURCE_SLICES_INVALID",
                    f"{source_location}/slices",
                    "slices must be an exact array",
                )
            )
            maximum = _lower_ceiling(maximum, "partial")
            source_slices = []

        local_slice_ids: set[str] = set()
        local_selector_keys: set[str] = set()
        source_slice_subjects: set[str] = set()
        source_loss_union: set[str] = set()
        valid_ranges: list[tuple[int, int]] = []

        for slice_index, slice_record in enumerate(source_slices):
            slice_location = f"{source_location}/slices/{slice_index}"
            if not isinstance(slice_record, Mapping):
                findings.append(
                    _finding(
                        "SLICE_RECORD_INVALID",
                        slice_location,
                        "slice entry must be an exact object",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")
                continue

            slice_id = slice_record.get("slice_id")
            if not isinstance(slice_id, str) or not slice_id:
                findings.append(
                    _finding(
                        "SLICE_ID_INVALID",
                        f"{slice_location}/slice_id",
                        "slice_id must be a non-empty string",
                    )
                )
                slice_id = f"{source_id}:{slice_index}"
                maximum = _lower_ceiling(maximum, "partial")

            if slice_id in local_slice_ids or slice_id in global_slice_ids:
                findings.append(
                    _finding(
                        "SLICE_ID_DUPLICATE",
                        f"{slice_location}/slice_id",
                        "slice_id values must be globally unique",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")
            local_slice_ids.add(slice_id)
            global_slice_ids.add(slice_id)

            selector = slice_record.get("selector")
            if not isinstance(selector, Mapping):
                findings.append(
                    _finding(
                        "SLICE_SELECTOR_INVALID",
                        f"{slice_location}/selector",
                        "selector must be an exact object",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")
                selector = {}

            selector_kind = selector.get("kind")
            selector_layer = selector.get("layer")
            selector_value = selector.get("value")
            selector_key = json.dumps(
                selector,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            if selector_key in local_selector_keys:
                findings.append(
                    _finding(
                        "SLICE_SELECTOR_DUPLICATE",
                        f"{slice_location}/selector",
                        "slice selectors must be unique within source",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")
            local_selector_keys.add(selector_key)
            if selector_layer not in {"raw-source", "derived-artifact"}:
                findings.append(
                    _finding(
                        "SLICE_SELECTOR_LAYER_INVALID",
                        f"{slice_location}/selector/layer",
                        "selector.layer must be raw-source or derived-artifact",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")

            raw_range = slice_record.get("raw_byte_range")
            if not isinstance(raw_range, Mapping):
                findings.append(
                    _finding(
                        "SLICE_RANGE_INVALID",
                        f"{slice_location}/raw_byte_range",
                        "raw_byte_range must be an exact object",
                    )
                )
                raw_start = 0
                raw_count = 0
                maximum = _lower_ceiling(maximum, "partial")
            else:
                raw_start = raw_range.get("start_byte")
                raw_count = raw_range.get("byte_count")
                if (
                    not isinstance(raw_start, int)
                    or isinstance(raw_start, bool)
                    or not isinstance(raw_count, int)
                    or isinstance(raw_count, bool)
                    or raw_start < 0
                    or raw_count <= 0
                ):
                    findings.append(
                        _finding(
                            "SLICE_RANGE_INVALID",
                            f"{slice_location}/raw_byte_range",
                            "start_byte and byte_count must be positive integers",
                        )
                    )
                    raw_start = 0
                    raw_count = 0
                    maximum = _lower_ceiling(maximum, "partial")
                elif raw_start + raw_count > raw_source_extent:
                    findings.append(
                        _finding(
                            "SLICE_RANGE_INVALID",
                            f"{slice_location}/raw_byte_range",
                            "raw byte range must stay within source extent",
                        )
                    )
                    maximum = _lower_ceiling(maximum, "partial")
                else:
                    valid_ranges.append((raw_start, raw_start + raw_count))

                if selector_kind == "whole-source":
                    if raw_start != 0 or raw_count != raw_source_extent:
                        findings.append(
                            _finding(
                                "SLICE_RANGE_INVALID",
                                f"{slice_location}/raw_byte_range",
                                "whole-source requires start_byte 0 and byte_count equal source extent",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                    if selector_value != "*":
                        findings.append(
                            _finding(
                                "SLICE_SELECTOR_INVALID",
                                f"{slice_location}/selector/value",
                                "whole-source selector value must be '*'",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                if selector_kind == "whole-source" and selector_layer == "derived-artifact":
                    findings.append(
                        _finding(
                            "SLICE_SELECTOR_INVALID",
                            f"{slice_location}/selector",
                            "selector kind \"whole-source\" cannot target derived-artifact output",
                        )
                    )
                    maximum = _lower_ceiling(maximum, "partial")
                elif selector_kind == "byte-range":
                    expected_selector = f"{raw_start}:{raw_count}"
                    if selector_value != expected_selector:
                        findings.append(
                            _finding(
                                "SLICE_SELECTOR_INVALID",
                                f"{slice_location}/selector/value",
                                "byte-range selector value must equal start:byte_count",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")

            content = slice_record.get("content")
            if not isinstance(content, Mapping):
                findings.append(
                    _finding(
                        "SLICE_CONTENT_INVALID",
                        f"{slice_location}/content",
                        "content must be an exact object",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")
            else:
                content_mode = content.get("content_mode")
                if content_mode == "embedded-content":
                    artifact = content.get("artifact")
                    if not isinstance(artifact, Mapping):
                        findings.append(
                            _finding(
                                "SLICE_CONTENT_INVALID",
                                f"{slice_location}/content/artifact",
                                "embedded-content must define artifact",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                    else:
                        artifact_path = artifact.get("path")
                        artifact_sha = artifact.get("sha256")
                        artifact_bytes = artifact.get("bytes")
                        if (
                            not isinstance(artifact_path, str)
                            or not _valid_sha256(artifact_sha)
                            or not isinstance(artifact_bytes, int)
                            or isinstance(artifact_bytes, bool)
                            or artifact_bytes <= 0
                        ):
                            findings.append(
                                _finding(
                                    "SLICE_CONTENT_INVALID",
                                    f"{slice_location}/content/artifact",
                                    "embedded-content artifact must include safe path, sha256, and bytes",
                                )
                            )
                            maximum = _lower_ceiling(maximum, "partial")
                        elif artifact_bytes != raw_count:
                            findings.append(
                                _finding(
                                    "SLICE_CONTENT_RANGE_MISMATCH",
                                    f"{slice_location}/content/artifact/bytes",
                                    "artifact bytes must equal raw_byte_range.byte_count",
                                )
                            )
                            maximum = _lower_ceiling(maximum, "partial")
                        raw_artifact = _safe_local_bytes(
                            source_root,
                            artifact_path,
                            location=f"{slice_location}/content/artifact/path",
                            findings=findings,
                            failure_code="SLICE_ARTIFACT_UNAVAILABLE",
                            portable_context=portable_context,
                        )
                        if raw_artifact is None:
                            maximum = _lower_ceiling(maximum, "partial")
                        else:
                            if _artifact_size(raw_artifact) != artifact_bytes:
                                findings.append(
                                    _finding(
                                        "SLICE_ARTIFACT_SIZE_MISMATCH",
                                        f"{slice_location}/content/artifact/bytes",
                                        "embedded artifact bytes must match local artifact bytes",
                                    )
                                )
                                maximum = _lower_ceiling(maximum, "partial")
                            elif _artifact_sha256(raw_artifact) != artifact_sha:
                                findings.append(
                                    _finding(
                                        "SLICE_ARTIFACT_HASH_MISMATCH",
                                        f"{slice_location}/content/artifact/sha256",
                                        "artifact hash must match local artifact bytes",
                                    )
                                )
                                maximum = _lower_ceiling(maximum, "partial")
                            if source_projection is not None and raw_start == 0 and raw_count == source_projection[1]:
                                if artifact_bytes != source_projection[1]:
                                    findings.append(
                                        _finding(
                                            "SLICE_ARTIFACT_SIZE_MISMATCH",
                                            f"{slice_location}/content/artifact/bytes",
                                            "embedded whole-source artifact bytes must match source projection bytes",
                                        )
                                    )
                                    maximum = _lower_ceiling(maximum, "partial")
                                if artifact_sha != source_projection[0]:
                                    findings.append(
                                        _finding(
                                            "SLICE_ARTIFACT_HASH_MISMATCH",
                                            f"{slice_location}/content/artifact/sha256",
                                            "embedded whole-source artifact hash must match source projection hash",
                                        )
                                    )
                                    maximum = _lower_ceiling(maximum, "partial")

                            if source_is_replayable:
                                if raw_start + raw_count > len(source_local_raw):
                                    findings.append(
                                        _finding(
                                            "SLICE_RANGE_INVALID",
                                            f"{slice_location}/raw_byte_range",
                                            "raw byte range exceeds source raw bytes",
                                        )
                                    )
                                    maximum = _lower_ceiling(maximum, "partial")
                                else:
                                    source_slice = source_local_raw[
                                        raw_start : raw_start + raw_count
                                    ]
                                    if _artifact_size(raw_artifact) != len(source_slice):
                                        findings.append(
                                            _finding(
                                                "SLICE_ARTIFACT_SIZE_MISMATCH",
                                                f"{slice_location}/content/artifact/bytes",
                                                "artifact bytes must match selected source byte range",
                                            )
                                        )
                                        maximum = _lower_ceiling(maximum, "partial")
                                    elif _artifact_sha256(raw_artifact) != _artifact_sha256(
                                        source_slice
                                    ):
                                        findings.append(
                                            _finding(
                                                "SLICE_ARTIFACT_HASH_MISMATCH",
                                                f"{slice_location}/content/artifact/sha256",
                                                "artifact hash must match selected source byte range",
                                            )
                                        )
                                        maximum = _lower_ceiling(maximum, "partial")
                            elif selector_kind != "whole-source" and source_assurance_mode != "attested":
                                maximum = _lower_ceiling(maximum, "partial")

                elif content_mode == "external-content":
                    locator = content.get("locator")
                    receipt = content.get("receipt")
                    if not isinstance(receipt, Mapping):
                        findings.append(
                            _finding(
                                "SLICE_CONTENT_INVALID",
                                f"{slice_location}/content/receipt",
                                "external-content must include receipt",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                        receipt = {}
                    source_raw_sha = None
                    source_raw_bytes = None
                    if source_projection is not None:
                        source_raw_sha, source_raw_bytes = source_projection
                    if source_raw_sha is not None and source_raw_sha != receipt.get(
                        "raw_sha256"
                    ):
                        findings.append(
                            _finding(
                                "SLICE_CONTENT_EXTERNAL_MISMATCH",
                                f"{slice_location}/content/receipt/raw_sha256",
                                "external-content raw_sha256 must match source projection raw_sha256",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                    if source_raw_bytes is not None and source_raw_bytes != receipt.get(
                        "raw_bytes"
                    ):
                        findings.append(
                            _finding(
                                "SLICE_CONTENT_EXTERNAL_MISMATCH",
                                f"{slice_location}/content/receipt/raw_bytes",
                                "external-content raw_bytes must match source projection raw_bytes",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                    if source_mode != "external-content" or locator != source_locator:
                        findings.append(
                            _finding(
                                "SLICE_CONTENT_MODE_MISMATCH",
                                f"{slice_location}/content/locator",
                                "external-content slice must reference the external source locator",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")

                    selected = receipt.get("selected_content") if isinstance(receipt, Mapping) else None
                    selected_sha = selected.get("sha256") if isinstance(selected, Mapping) else None
                    selected_bytes = selected.get("bytes") if isinstance(selected, Mapping) else None
                    if (
                        not _valid_sha256(selected_sha)
                        or not isinstance(selected_bytes, int)
                        or isinstance(selected_bytes, bool)
                        or selected_bytes <= 0
                    ):
                        findings.append(
                            _finding(
                                "SLICE_CONTENT_INVALID",
                                f"{slice_location}/content/receipt/selected_content",
                                "external receipt must include selected_content sha256 and positive bytes",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                    elif selected_bytes != raw_count:
                        findings.append(
                            _finding(
                                "SLICE_CONTENT_RANGE_MISMATCH",
                                f"{slice_location}/raw_byte_range",
                                "selected_content.bytes must equal raw_byte_range.byte_count",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")

                    if selector_kind == "whole-source":
                        source_sha = source_projection[0] if source_projection else None
                        if (
                            source_projection is None
                            or source_sha != selected_sha
                            or (source_projection is not None and source_projection[1] != selected_bytes)
                        ):
                            findings.append(
                                _finding(
                                    "SLICE_CONTENT_EXTERNAL_MISMATCH",
                                    f"{slice_location}/content/receipt/selected_content",
                                    "whole-source selection must match source raw identity",
                                )
                            )
                            maximum = _lower_ceiling(maximum, "partial")
                    elif source_is_replayable:
                        if raw_start + raw_count > len(source_local_raw):
                            findings.append(
                                _finding(
                                    "SLICE_RANGE_INVALID",
                                    f"{slice_location}/raw_byte_range",
                                    "raw byte range exceeds source raw bytes",
                                )
                            )
                            maximum = _lower_ceiling(maximum, "partial")
                        else:
                            source_slice = source_local_raw[
                                raw_start : raw_start + raw_count
                            ]
                            if selected_bytes != len(source_slice):
                                findings.append(
                                    _finding(
                                        "SLICE_CONTENT_RANGE_MISMATCH",
                                        f"{slice_location}/content/receipt/selected_content/bytes",
                                        "selected_content.bytes must match source byte range",
                                    )
                                )
                                maximum = _lower_ceiling(maximum, "partial")
                            elif _artifact_sha256(
                                source_slice
                            ) != selected_sha or (
                                _artifact_size(source_slice) != selected_bytes
                            ):
                                findings.append(
                                    _finding(
                                        "SLICE_CONTENT_EXTERNAL_MISMATCH",
                                        f"{slice_location}/content/receipt/selected_content",
                                        "selected_content must match source byte range",
                                    )
                                )
                                maximum = _lower_ceiling(maximum, "partial")
                    elif source_assurance_mode != "attested":
                        maximum = _lower_ceiling(maximum, "partial")

                elif content_mode == "metadata-only":
                    locator = content.get("locator")
                    identity = content.get("identity")
                    metadata_allowed = source_mode in {"metadata-only", "external-content"}
                    if selector_kind == "whole-source" and source_mode == "external-content":
                        metadata_allowed = False
                    maximum = _lower_ceiling(maximum, "partial")
                    if not metadata_allowed or locator != source_locator:
                        findings.append(
                            _finding(
                                "SLICE_CONTENT_MODE_MISMATCH",
                                f"{slice_location}/content/locator",
                                "metadata-only slice must keep the same locator as source metadata",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                    if not isinstance(identity, Mapping):
                        findings.append(
                            _finding(
                                "SLICE_CONTENT_INVALID",
                                f"{slice_location}/content/identity",
                                "metadata-only content must include identity",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                    else:
                        identity_sha = identity.get("sha256")
                        identity_bytes = identity.get("bytes")
                        if (
                            not _valid_sha256(identity_sha)
                            or not isinstance(identity_bytes, int)
                            or isinstance(identity_bytes, bool)
                            or identity_bytes <= 0
                        ):
                            findings.append(
                                _finding(
                                    "SLICE_CONTENT_INVALID",
                                    f"{slice_location}/content/identity",
                                    "metadata-only identity must include valid sha256 and bytes",
                                )
                            )
                            maximum = _lower_ceiling(maximum, "partial")
                        else:
                            # raw-byte selectors tied to raw-source bind to selected
                            # byte span in the source provenance.
                            if selector_layer == "raw-source":
                                if identity_bytes != raw_count:
                                    findings.append(
                                        _finding(
                                            "SLICE_CONTENT_RANGE_MISMATCH",
                                            f"{slice_location}/content/identity/bytes",
                                            "raw-source metadata identity bytes must equal "
                                            "raw_byte_range.byte_count",
                                        )
                                    )
                                    maximum = _lower_ceiling(maximum, "partial")
                                if source_is_replayable:
                                    if source_local_raw is None:
                                        findings.append(
                                            _finding(
                                                "SLICE_CONTENT_UNAVAILABLE",
                                                f"{slice_location}/source_identity/locator",
                                                "metadata identity cannot verify source byte-range sha256 "
                                                "without replayable source bytes",
                                            )
                                        )
                                        maximum = _lower_ceiling(maximum, "partial")
                                    else:
                                        source_slice = source_local_raw[
                                            raw_start:raw_start + raw_count
                                        ]
                                        if identity_bytes != len(source_slice):
                                            findings.append(
                                                _finding(
                                                    "SLICE_CONTENT_RANGE_MISMATCH",
                                                    f"{slice_location}/content/identity/bytes",
                                                    "raw-source metadata identity bytes must match "
                                                    "source byte range",
                                                )
                                            )
                                            maximum = _lower_ceiling(maximum, "partial")
                                        elif identity_sha != _artifact_sha256(source_slice):
                                            findings.append(
                                                _finding(
                                                    "SLICE_CONTENT_EXTERNAL_MISMATCH",
                                                    f"{slice_location}/content/identity/sha256",
                                                    "raw-source metadata identity sha256 must match "
                                                    "source byte range",
                                        )
                                    )
                                    maximum = _lower_ceiling(maximum, "partial")
                            elif selector_layer == "derived-artifact":
                                if selector_kind == "whole-source":
                                    findings.append(
                                        _finding(
                                            "SLICE_CONTENT_EXTERNAL_MISMATCH",
                                            f"{slice_location}/content/identity",
                                            "derived-artifact whole-source identity cannot "
                                            "represent derived-artifact source slice output",
                                        )
                                    )
                                    maximum = _lower_ceiling(maximum, "partial")
                            if (
                                selector_layer == "raw-source"
                                and selector_kind == "whole-source"
                                and source_projection is not None
                                and (
                                    identity_sha != source_projection[0]
                                    or identity_bytes != source_projection[1]
                                )
                            ):
                                findings.append(
                                    _finding(
                                        "SLICE_CONTENT_EXTERNAL_MISMATCH",
                                        f"{slice_location}/content/identity",
                                        "whole-source raw-source metadata identity must match source projection"
                                        " sha256 and bytes",
                                    )
                                )
                                maximum = _lower_ceiling(maximum, "partial")

                else:
                    findings.append(
                        _finding(
                            "SLICE_CONTENT_MODE_INVALID",
                            f"{slice_location}/content/content_mode",
                            "content_mode must be embedded-content, external-content, or metadata-only",
                        )
                    )
                    maximum = _lower_ceiling(maximum, "partial")

            slice_loss_accounting = slice_record.get("loss_accounting")
            slice_loss_ceiling = _slice_loss_accounting_ceiling(
                slice_loss_accounting if isinstance(slice_loss_accounting, Mapping) else {},
                dimension=f"{source_id}/{slice_id}/loss",
                location=f"{slice_location}/loss_accounting",
                findings=findings,
            )
            maximum = _lower_ceiling(maximum, slice_loss_ceiling)

            if isinstance(slice_loss_accounting, Mapping):
                raw_loss_entries = slice_loss_accounting.get("entries")
                if isinstance(raw_loss_entries, list):
                    for entry in raw_loss_entries:
                        if not isinstance(entry, Mapping):
                            continue
                        loss_id = entry.get("loss_id")
                        if not isinstance(loss_id, str):
                            continue
                        source_loss_union.add(loss_id)
                        if (
                            loss_id in source_loss_entries
                            and source_loss_entries[loss_id] != entry
                        ):
                            findings.append(
                                _finding(
                                    "SLICE_LOSS_ENTRY_MISMATCH",
                                    f"{slice_location}/loss_accounting/entries",
                                    "slice loss entry must exactly equal source loss entry",
                                )
                            )
                            maximum = _lower_ceiling(maximum, "partial")
                        elif loss_id not in source_loss_entries:
                            findings.append(
                                _finding(
                                    "SLICE_LOSS_ENTRY_MISMATCH",
                                    f"{slice_location}/loss_accounting/entries",
                                    "slice loss entry must exactly equal source loss entry",
                                )
                            )
                            maximum = _lower_ceiling(maximum, "partial")

            subject_ids = slice_record.get("subject_ids")
            if not isinstance(subject_ids, list):
                findings.append(
                    _finding(
                        "SLICE_SUBJECT_IDS_INVALID",
                        f"{slice_location}/subject_ids",
                        "subject_ids must be an exact array",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")
                subject_ids = []
            else:
                for subject_id in subject_ids:
                    if not isinstance(subject_id, str) or not subject_id:
                        findings.append(
                            _finding(
                                "SLICE_SUBJECT_ID_INVALID",
                                f"{slice_location}/subject_ids",
                                "subject id must be a non-empty string",
                            )
                        )
                        maximum = _lower_ceiling(maximum, "partial")
                        continue
                    if corpus_source is not None:
                        valid_subject_ids = corpus_source.get("subject_ids", [])
                        if isinstance(valid_subject_ids, list) and subject_id not in valid_subject_ids:
                            findings.append(
                                _finding(
                                    "SLICE_SUBJECT_ID_MISMATCH",
                                    f"{slice_location}/subject_ids",
                                    "slice subject_ids must be subset of corpus source subject_ids",
                                )
                            )
                            maximum = _lower_ceiling(maximum, "partial")
                    source_slice_subjects.add(subject_id)
                    subject_slice_refs.setdefault(subject_id, set()).add(f"{source_id}:{slice_id}")

        if corpus_source is not None and declared_status == "complete":
            corpus_subjects = {
                sid for sid in corpus_source.get("subject_ids", []) if isinstance(sid, str)
            }
            if not corpus_subjects.issubset(source_slice_subjects):
                findings.append(
                    _finding(
                        "SLICE_SUBJECT_COVERAGE_INVALID",
                        f"{source_location}/subject_ids",
                        "complete manifests require every source subject to be covered by at least one slice",
                    )
                )
                maximum = _lower_ceiling(maximum, "partial")

        if (
            isinstance(source_loss_accounting, Mapping)
            and source_loss_accounting.get("closure_status") == "complete"
            and source_loss_union != source_loss_ids
        ):
            findings.append(
                _finding(
                    "SLICE_LOSS_COVERAGE_INCOMPLETE",
                    f"{source_location}/source_loss_accounting",
                    "source loss complete requires slice loss IDs to cover all source losses",
                )
            )
            maximum = _lower_ceiling(maximum, "partial")
        if declared_status == "complete":
            merged_ranges = sorted(valid_ranges)
            if not merged_ranges:
                if raw_source_extent > 0:
                    findings.append(
                        _finding(
                            "SLICE_RANGE_COVERAGE_INCOMPLETE",
                            f"{source_location}/slices",
                            "complete slice manifests must cover source raw byte range exactly",
                        )
                    )
                    maximum = _lower_ceiling(maximum, "partial")
            else:
                cursor = 0
                covered = True
                for start, end in merged_ranges:
                    if start > cursor:
                        covered = False
                        break
                    if end > cursor:
                        cursor = end
                if merged_ranges[0][0] != 0 or cursor < raw_source_extent or not covered:
                    findings.append(
                        _finding(
                            "SLICE_RANGE_COVERAGE_INCOMPLETE",
                            f"{source_location}/slices",
                            "complete slice manifests must cover source raw byte range exactly",
                        )
                    )
                    maximum = _lower_ceiling(maximum, "partial")

    if blockers:
        maximum = _lower_ceiling(maximum, "blocked")

    _status_overclaim(
        declared_status,
        maximum,
        location=f"{location}/status",
        findings=findings,
    )



def _coverage_findings(
    record: LoadedRecord,
    *,
    corpora: dict[str, LoadedRecord],
    slice_manifests: dict[str, LoadedRecord],
    scope_inventories: dict[str, LoadedRecord],
    consumer_registry: dict[str, Any],
    consumer_registry_sha256: str,
    repository_root: Path,
    findings: list[Finding],
    portable_context: PortableValidationContext | None = None,
) -> None:
    data = record.data
    coverage_id = data.get("coverage_id")
    if not isinstance(coverage_id, str) or not coverage_id:
        coverage_id = "<unknown>"
        findings.append(
            _finding(
                "COVERAGE_ID_INVALID",
                "coverage/<unknown>",
                "coverage_id must be a non-empty string",
            )
        )
    location = f"coverage/{coverage_id}"

    declared_coverage_status = (
        data["status"] if isinstance(data.get("status"), Mapping) else {}
    )

    def _status_declared(dimension: str, location_suffix: str) -> str:
        value = declared_coverage_status.get(dimension)
        if value not in STATUS_RANK:
            findings.append(
                _finding(
                    "COVERAGE_STATUS_INVALID",
                    f"{location}/status/{location_suffix}",
                    f"{location_suffix} status must be complete, partial, or blocked",
                )
            )
            return "blocked"
        return value

    def _record_producer_skill(record_ref: LoadedRecord, *, expected: str) -> bool:
        producer = record_ref.data.get("producer", {})
        if not isinstance(producer, Mapping):
            findings.append(
                _finding(
                    "COVERAGE_PRODUCER_INVALID",
                    f"{record_ref.path}:producer",
                    "producer must be an exact object",
                )
            )
            return False
        producer_skill_id = producer.get("skill_id")
        if not isinstance(producer_skill_id, str):
            findings.append(
                _finding(
                    "COVERAGE_PRODUCER_INVALID",
                    f"{record_ref.path}:producer/skill_id",
                    "producer.skill_id must be a non-empty string",
                )
            )
            return False
        if producer_skill_id != expected:
            findings.append(
                _finding(
                    "COVERAGE_PRODUCER_INVALID",
                    f"{record_ref.path}:producer/skill_id",
                    "producer.skill_id must match coverage skill_id",
                )
            )
            return False
        return True

    def _resolve_refs(
        field: str,
        id_field: str,
        records: dict[str, LoadedRecord],
    ) -> tuple[dict[str, LoadedRecord], set[str], bool]:
        refs_raw = data.get(field)
        if not isinstance(refs_raw, list):
            findings.append(
                _finding(
                    "COVERAGE_RECORD_REF_INVALID",
                    f"{location}/{field}",
                    f"{field} must be an exact array",
                )
            )
            return {}, set(), True
        ids: list[str] = []
        resolved: dict[str, LoadedRecord] = {}
        hard = False
        for index, reference in enumerate(refs_raw):
            if not isinstance(reference, Mapping):
                findings.append(
                    _finding(
                        "COVERAGE_RECORD_REF_INVALID",
                        f"{location}/{field}/{index}",
                        f"{field} entry must be an exact object",
                    )
                )
                hard = True
                continue
            record_id = reference.get(id_field)
            if not isinstance(record_id, str):
                findings.append(
                    _finding(
                        "COVERAGE_RECORD_REF_INVALID",
                        f"{location}/{field}/{index}/{id_field}",
                        f"{id_field} must be a valid identifier",
                    )
                )
                hard = True
                continue
            ids.append(record_id)
            target = _check_ref(
                reference,
                id_field=id_field,
                records=records,
                location=f"{location}/{field}/{index}",
                findings=findings,
            )
            if target is None:
                hard = True
            else:
                resolved[record_id] = target
        return resolved, set(ids), hard

    coverage_skill_id = data.get("skill_id")
    if not isinstance(coverage_skill_id, str) or not coverage_skill_id:
        findings.append(
            _finding(
                "COVERAGE_SKILL_ID_INVALID",
                f"{location}/skill_id",
                "coverage skill_id must be a non-empty string",
            )
        )
        coverage_skill_id = "<unknown>"

    hard_error = False
    blockers = data.get("blockers", [])
    blocked_dimensions: set[str] = set()
    if not isinstance(blockers, list):
        findings.append(
            _finding(
                "COVERAGE_BLOCKERS_INVALID",
                f"{location}/blockers",
                "blockers must be an exact array",
            )
        )
        hard_error = True
    else:
        allowed_blocker_dimensions = {"corpus", "slices", "scope", "mappings"}
        for index, blocker in enumerate(blockers):
            if not isinstance(blocker, Mapping):
                findings.append(
                    _finding(
                        "COVERAGE_BLOCKERS_INVALID",
                        f"{location}/blockers/{index}",
                        "blocker entry must be an exact object",
                    )
                )
                hard_error = True
                continue
            raw_dimension = blocker.get("dimension")
            if not isinstance(raw_dimension, str) or not raw_dimension:
                findings.append(
                    _finding(
                        "COVERAGE_BLOCKERS_INVALID",
                        f"{location}/blockers/{index}/dimension",
                        "blocker dimension must be one of corpus, slices, scope, or mappings",
                    )
                )
                hard_error = True
                continue
            blocker_dimensions = {raw_dimension}
            for dimension in blocker_dimensions:
                if dimension not in allowed_blocker_dimensions:
                    findings.append(
                        _finding(
                            "COVERAGE_BLOCKERS_INVALID",
                            f"{location}/blockers/{index}/dimension",
                            "blocker dimension must be one of corpus, slices, scope, or mappings",
                        )
                    )
                    hard_error = True
                else:
                    blocked_dimensions.add(dimension)

    resolved_corpora, corpus_ids, refs_hard_error = _resolve_refs(
        "corpus_refs",
        "corpus_id",
        corpora,
    )
    resolved_slices, slice_manifest_ids, hard_error2 = _resolve_refs(
        "slice_manifest_refs",
        "slice_manifest_id",
        slice_manifests,
    )
    hard_error = hard_error or refs_hard_error or hard_error2

    if set(corpus_ids) != set(corpora):
        findings.append(
            _finding(
                "COVERAGE_RECORD_SET_INVALID",
                f"{location}/corpus_refs",
                "coverage must reference exactly the supplied corpus record set",
            )
        )
        hard_error = True

    if set(slice_manifest_ids) != set(slice_manifests):
        findings.append(
            _finding(
                "COVERAGE_RECORD_SET_INVALID",
                f"{location}/slice_manifest_refs",
                "coverage must reference exactly the supplied slice manifest record "
                "set",
            )
        )
        hard_error = True

    scope_inventory = None
    scope_inventory_id = None
    scope_ref = data.get("scope_inventory_ref")
    scope_ref_path = f"{location}/scope_inventory_ref"
    if not isinstance(scope_ref, Mapping):
        findings.append(
            _finding(
                "COVERAGE_SCOPE_INVENTORY_REF_INVALID",
                scope_ref_path,
                "scope_inventory_ref must be an exact object",
            )
        )
        hard_error = True
    else:
        scope_inventory_id = scope_ref.get("inventory_id")
        if not isinstance(scope_inventory_id, str):
            findings.append(
                _finding(
                    "COVERAGE_SCOPE_INVENTORY_REF_INVALID",
                    f"{scope_ref_path}/inventory_id",
                    "inventory_id must be a valid identifier",
                )
            )
            hard_error = True
        else:
            scope_inventory = _check_ref(
                scope_ref,
                id_field="inventory_id",
                records=scope_inventories,
                location=scope_ref_path,
                findings=findings,
            )
            if scope_inventory is None:
                hard_error = True
    if set(scope_inventories) != {scope_inventory_id}:
        findings.append(
            _finding(
                "COVERAGE_RECORD_SET_INVALID",
                scope_ref_path,
                "coverage must reference exactly the supplied scope inventory",
            )
        )
        hard_error = True

    # coverage.skill_id must match coverage record and related record producer skill ids.
    coverage_producer_ok = _record_producer_skill(
        record,
        expected=coverage_skill_id,
    )
    hard_error = hard_error or not coverage_producer_ok

    if scope_inventory is not None and (
        not isinstance(scope_inventory.data.get("skill_id"), str)
        or scope_inventory.data.get("skill_id") != coverage_skill_id
    ):
        findings.append(
            _finding(
                "COVERAGE_SCOPE_SKILL_MISMATCH",
                f"{location}/skill_id",
                "coverage skill_id must equal scope inventory skill_id",
            )
        )
        hard_error = True

    if scope_inventory is not None:
        scope_producer_ok = _record_producer_skill(
            scope_inventory,
            expected=coverage_skill_id,
        )
        hard_error = hard_error or not scope_producer_ok
    for corpus_id, corpus in sorted(resolved_corpora.items()):
        corpus_producer_ok = _record_producer_skill(
            corpus,
            expected=coverage_skill_id,
        )
        hard_error = hard_error or not corpus_producer_ok
    for manifest_id, manifest in sorted(resolved_slices.items()):
        slice_producer_ok = _record_producer_skill(
            manifest,
            expected=coverage_skill_id,
        )
        hard_error = hard_error or not slice_producer_ok

    # canonical consumer bindings determine expected authority/provider pair set.
    raw_bindings = consumer_registry.get("bindings")
    expected_pairs: set[tuple[str, str]] = set()
    if not isinstance(raw_bindings, list):
        findings.append(
            _finding(
                "COVERAGE_CONSUMER_BINDING_INVALID",
                f"{location}/consumer_registry/bindings",
                "consumer_registry/bindings must be an exact array",
            )
        )
        hard_error = True
    else:
        seen_pairs: set[tuple[str, str]] = set()
        for index, binding in enumerate(raw_bindings):
            if not isinstance(binding, Mapping):
                findings.append(
                    _finding(
                        "COVERAGE_CONSUMER_BINDING_INVALID",
                        f"{location}/consumer_registry/bindings/{index}",
                        "consumer binding must be an exact object",
                    )
                )
                hard_error = True
                continue
            if (
                binding.get("consumer_skill_id") == coverage_skill_id
                and binding.get("purpose") == "official-document-coverage"
                and binding.get("claim_ceiling") == "registered-skill-scope"
            ):
                authority_id = binding.get("authority_id")
                provider_id = binding.get("provider_id")
                if not isinstance(authority_id, str) or not isinstance(
                    provider_id, str
                ):
                    findings.append(
                        _finding(
                            "COVERAGE_CONSUMER_BINDING_INVALID",
                            f"{location}/consumer_registry/bindings/{index}",
                            "consumer binding must expose valid authority_id and "
                            "provider_id",
                        )
                    )
                    hard_error = True
                    continue
                pair = (authority_id, provider_id)
                if pair in seen_pairs:
                    findings.append(
                        _finding(
                            "COVERAGE_CONSUMER_BINDING_INVALID",
                            f"{location}/consumer_registry/bindings/{index}",
                            "consumer binding authority/provider pair is duplicated",
                        )
                    )
                    hard_error = True
                seen_pairs.add(pair)
                expected_pairs.add(pair)

    corpus_pairs = []
    for corpus_id, corpus in resolved_corpora.items():
        authority_id = corpus.data.get("authority_id")
        provider_id = corpus.data.get("provider_id")
        if not isinstance(authority_id, str) or not isinstance(provider_id, str):
            findings.append(
                _finding(
                    "COVERAGE_CORPUS_PAIR_INVALID",
                    f"corpora/{corpus_id}",
                    "corpus must expose valid authority_id and provider_id",
                )
            )
            hard_error = True
            continue
        corpus_pairs.append((authority_id, provider_id))
    if len(corpus_pairs) != len(set(corpus_pairs)):
        findings.append(
            _finding(
                "COVERAGE_CORPUS_PAIR_INVALID",
                f"{location}/corpus_refs",
                "referenced corpora cannot duplicate authority/provider pairs",
            )
        )
        hard_error = True

    referenced_pairs = set(corpus_pairs)
    if referenced_pairs != expected_pairs:
        findings.append(
            _finding(
                "COVERAGE_CONSUMER_BINDING_INVALID",
                f"{location}/consumer-registry/bindings",
                "consumer bindings must exactly match referenced authority/provider pairs",
            )
        )
        hard_error = True

    # exactly one slice manifest per referenced corpus and each manifest must resolve
    # to one of the referenced corpora.
    slice_to_corpus: dict[str, str] = {}
    for manifest_id, manifest in resolved_slices.items():
        corpus_ref = manifest.data.get("corpus_ref")
        if not isinstance(corpus_ref, Mapping):
            findings.append(
                _finding(
                    "COVERAGE_SLICE_CORPUS_LINK_INVALID",
                    f"slices/{manifest_id}/corpus_ref",
                    "slice manifest corpus_ref must be an exact object",
                )
            )
            hard_error = True
            continue
        corpus_id = corpus_ref.get("corpus_id")
        if not isinstance(corpus_id, str):
            findings.append(
                _finding(
                    "COVERAGE_SLICE_CORPUS_LINK_INVALID",
                    f"slices/{manifest_id}/corpus_ref/corpus_id",
                    "slice manifest corpus_ref must include a valid corpus_id",
                )
            )
            hard_error = True
            continue
        if corpus_id not in corpus_ids:
            findings.append(
                _finding(
                    "COVERAGE_SLICE_CORPUS_PARTITION_INVALID",
                    f"slices/{manifest_id}/corpus_ref",
                    "slice manifest points to an unreferenced corpus",
                )
            )
            hard_error = True
            continue
        if corpus_id in slice_to_corpus.values():
            findings.append(
                _finding(
                    "COVERAGE_SLICE_CORPUS_PARTITION_INVALID",
                    f"{location}/slice_manifest_refs",
                    "each referenced corpus must have exactly one slice manifest",
                )
            )
            hard_error = True
        slice_to_corpus[manifest_id] = corpus_id

    if set(slice_to_corpus.values()) != set(corpus_ids):
        findings.append(
            _finding(
                "COVERAGE_SLICE_CORPUS_PARTITION_INVALID",
                f"{location}/slice_manifest_refs",
                "coverage requires exactly one slice manifest per referenced corpus",
            )
        )
        hard_error = True

    # Build slice index for subject checks.
    slice_subject_index: dict[tuple[str, str], set[str]] = {}
    for manifest_id, manifest in resolved_slices.items():
        sources = manifest.data.get("sources")
        if not isinstance(sources, Mapping):
            findings.append(
                _finding(
                    "COVERAGE_SLICE_MANIFEST_SOURCES_INVALID",
                    f"slices/{manifest_id}/sources",
                    "slice manifest sources must be an exact mapping",
                )
            )
            hard_error = True
            continue
        for source_id, source in sources.items():
            source_entry = source if isinstance(source, Mapping) else None
            if source_entry is None:
                findings.append(
                    _finding(
                        "COVERAGE_SLICE_SOURCE_INVALID",
                        f"slices/{manifest_id}/sources/{source_id}",
                        "slice source entry must be an exact object",
                    )
                )
                hard_error = True
                continue
            raw_slices = source_entry.get("slices")
            if not isinstance(raw_slices, list):
                findings.append(
                    _finding(
                        "COVERAGE_SLICE_ENTRIES_INVALID",
                        f"slices/{manifest_id}/sources/{source_id}/slices",
                        "slice source slices must be an exact array",
                    )
                )
                hard_error = True
                continue
            for slice_index, slice_entry in enumerate(raw_slices):
                if not isinstance(slice_entry, Mapping):
                    findings.append(
                        _finding(
                            "COVERAGE_SLICE_ENTRY_INVALID",
                            f"slices/{manifest_id}/sources/{source_id}/{slice_index}",
                            "slice entry must be an exact object",
                        )
                    )
                    hard_error = True
                    continue
                slice_id = slice_entry.get("slice_id")
                if not isinstance(slice_id, str):
                    findings.append(
                        _finding(
                            "COVERAGE_SLICE_ENTRY_INVALID",
                            f"slices/{manifest_id}/sources/{source_id}/{slice_index}/slice_id",
                            "slice entry must include valid slice_id",
                        )
                    )
                    hard_error = True
                    continue
                key = (manifest_id, slice_id)
                if key in slice_subject_index:
                    findings.append(
                        _finding(
                            "COVERAGE_SLICE_ENTRY_DUPLICATE",
                            f"slices/{manifest_id}/{slice_id}",
                            "slice id must be unique per manifest",
                        )
                    )
                    hard_error = True
                raw_subjects = slice_entry.get("subject_ids")
                if not isinstance(raw_subjects, list):
                    findings.append(
                        _finding(
                            "COVERAGE_SLICE_ENTRY_INVALID",
                            f"slices/{manifest_id}/sources/{source_id}/{slice_index}/subject_ids",
                            "slice subject_ids must be an exact array",
                        )
                    )
                    hard_error = True
                    raw_subjects = []
                slice_subject_index[key] = {
                    sid
                    for sid in raw_subjects
                    if isinstance(sid, str)
                }

    raw_scope_subjects = []
    scope_subject_ids: list[str] = []
    scope_subject_by_id: dict[str, Mapping[str, Any]] = {}
    if scope_inventory is not None:
        raw_scope_subjects = scope_inventory.data.get("subjects", [])
        if not isinstance(raw_scope_subjects, list):
            findings.append(
                _finding(
                    "COVERAGE_SCOPE_SUBJECTS_INVALID",
                    f"{scope_inventory.path}:subjects",
                    "scope inventory subjects must be an exact array",
                )
            )
            hard_error = True
            raw_scope_subjects = []
        for index, subject in enumerate(raw_scope_subjects):
            if not isinstance(subject, Mapping):
                findings.append(
                    _finding(
                        "COVERAGE_SCOPE_SUBJECT_INVALID",
                        f"{scope_inventory.path}:subjects/{index}",
                        "scope subject must be an exact object",
                    )
                )
                hard_error = True
                continue
            subject_id = subject.get("subject_id")
            if not isinstance(subject_id, str):
                findings.append(
                    _finding(
                        "COVERAGE_SCOPE_SUBJECT_INVALID",
                        f"{scope_inventory.path}:subjects/{index}/subject_id",
                        "scope subject must include a valid subject_id",
                    )
                )
                hard_error = True
                continue
            scope_subject_ids.append(subject_id)
            scope_subject_by_id[subject_id] = subject
    _check_unique_ids(
        [{"subject_id": sid} for sid in scope_subject_ids],
        "subject_id",
        code="COVERAGE_SUBJECT_ID_DUPLICATE",
        location=f"{location}/scope_subjects",
        findings=findings,
    )

    raw_mappings = data.get("mappings")
    if not isinstance(raw_mappings, Mapping):
        findings.append(
            _finding(
                "COVERAGE_MAPPINGS_INVALID",
                f"{location}/mappings",
                "mappings must be an exact subject-keyed map",
            )
        )
        hard_error = True
        raw_mappings = {}
    mapping_subject_ids = set(raw_mappings.keys()) if isinstance(raw_mappings, Mapping) else set()
    if mapping_subject_ids != set(scope_subject_ids):
        findings.append(
            _finding(
                "COVERAGE_SUBJECT_PARTITION_INVALID",
                f"{location}/mappings",
                "mapping subject key set must exactly equal scope subject_id set",
            )
        )
        hard_error = True

    mapping_status_values: list[str] = []
    for subject_id, mapping in raw_mappings.items():
        mapping_location = f"{location}/mappings/{subject_id}"
        if not isinstance(mapping, Mapping):
            findings.append(
                _finding(
                    "COVERAGE_MAPPING_INVALID",
                    mapping_location,
                    "mapping entry must be an exact object",
                )
            )
            mapping_status_values.append("blocked")
            hard_error = True
            continue
        mapping_status = mapping.get("mapping_status")
        if mapping_status not in STATUS_RANK:
            findings.append(
                _finding(
                    "COVERAGE_MAPPING_STATUS_INVALID",
                    f"{mapping_location}/mapping_status",
                    "mapping_status must be complete, partial, or blocked",
                )
            )
            mapping_status = "blocked"
        mapping_status_values.append(mapping_status)

        disposition = mapping.get("disposition")
        subject = scope_subject_by_id.get(subject_id)
        if subject is None:
            findings.append(
                _finding(
                    "COVERAGE_MAPPING_SCOPE_MISMATCH",
                    mapping_location,
                    "mapping subject_id must exist in scope inventory",
                )
            )
            hard_error = True
            continue
        evidence_class = subject.get("evidence_class")

        if evidence_class == "official-provider-required":
            expected_disposition = {
                "complete": "covered",
                "partial": "partial",
                "blocked": "blocked",
            }.get(mapping_status)
            if disposition != expected_disposition:
                findings.append(
                    _finding(
                        "COVERAGE_EVIDENCE_CLASS_CONFUSION",
                        f"{mapping_location}/disposition",
                        "official-provider-required mappings must be covered/partial/"
                        "blocked with aligned disposition",
                    )
                )
                hard_error = True
            slice_refs = mapping.get("slice_refs")
            if not isinstance(slice_refs, list):
                findings.append(
                    _finding(
                        "COVERAGE_SLICE_REFS_INVALID",
                        f"{mapping_location}/slice_refs",
                        "slice_refs must be an exact array",
                    )
                )
                hard_error = True
                slice_refs = []
            if mapping_status in {"complete", "partial"} and not slice_refs:
                findings.append(
                    _finding(
                        "COVERAGE_SLICE_REF_INVALID",
                        mapping_location,
                        "official-provider-required complete/partial mappings need slice_refs",
                    )
                )
                hard_error = True
            for ref_index, slice_reference in enumerate(slice_refs):
                if not isinstance(slice_reference, Mapping):
                    findings.append(
                        _finding(
                            "COVERAGE_SLICE_REF_INVALID",
                            f"{mapping_location}/slice_refs/{ref_index}",
                            "slice ref must be an exact object",
                        )
                    )
                    hard_error = True
                    continue
                slice_manifest_id = slice_reference.get("slice_manifest_id")
                slice_id = slice_reference.get("slice_id")
                if not isinstance(slice_manifest_id, str) or not isinstance(
                    slice_id, str
                ):
                    findings.append(
                        _finding(
                            "COVERAGE_SLICE_REF_INVALID",
                            f"{mapping_location}/slice_refs/{ref_index}",
                            "slice ref must include valid slice_manifest_id and slice_id",
                        )
                    )
                    hard_error = True
                    continue
                key = (slice_manifest_id, slice_id)
                slice_subjects = slice_subject_index.get(key)
                if slice_subjects is None:
                    findings.append(
                        _finding(
                            "COVERAGE_SLICE_REF_INVALID",
                            f"{mapping_location}/slice_refs/{ref_index}",
                            "coverage slice reference does not resolve",
                        )
                    )
                    hard_error = True
                elif subject_id not in slice_subjects:
                    findings.append(
                        _finding(
                            "COVERAGE_SLICE_REF_SUBJECT_MISMATCH",
                            f"{mapping_location}/slice_refs/{ref_index}",
                            "slice reference must include current subject_id",
                        )
                    )
                    hard_error = True
        else:
            if disposition not in {"not-applicable", "excluded"}:
                findings.append(
                    _finding(
                        "COVERAGE_EVIDENCE_CLASS_CONFUSION",
                        f"{mapping_location}/disposition",
                        "non-official mappings must be not-applicable or excluded",
                    )
                )
                hard_error = True

    corpus_status = min(
        (
            corpus.data.get("status", "blocked")
            if corpus.data.get("status") in STATUS_RANK
            else "blocked"
            for corpus in resolved_corpora.values()
        ),
        key=STATUS_RANK.__getitem__,
        default="blocked",
    )
    slices_status = min(
        (
            manifest.data.get("status", "blocked")
            if manifest.data.get("status") in STATUS_RANK
            else "blocked"
            for manifest in resolved_slices.values()
        ),
        key=STATUS_RANK.__getitem__,
        default="blocked",
    )
    scope_status = "blocked"
    if scope_inventory is not None:
        raw_status = scope_inventory.data.get("status")
        if raw_status in STATUS_RANK:
            scope_status = raw_status
        else:
            findings.append(
                _finding(
                    "COVERAGE_SCOPE_STATUS_INVALID",
                    "scope-inventories/scope/status",
                    "scope status must be complete, partial, or blocked",
                )
            )
    mappings_status = min(
        mapping_status_values,
        key=STATUS_RANK.__getitem__,
        default="blocked",
    )

    corpus_ceiling = (
        "blocked" if "corpus" in blocked_dimensions else corpus_status
    )
    slices_ceiling = (
        "blocked" if "slices" in blocked_dimensions else slices_status
    )
    scope_ceiling = "blocked" if "scope" in blocked_dimensions else scope_status
    mappings_ceiling = (
        "blocked" if "mappings" in blocked_dimensions else mappings_status
    )
    _status_overclaim(
        _status_declared("corpus", "corpus"),
        corpus_ceiling,
        location=f"{location}/status/corpus",
        findings=findings,
    )
    _status_overclaim(
        _status_declared("slices", "slices"),
        slices_ceiling,
        location=f"{location}/status/slices",
        findings=findings,
    )
    _status_overclaim(
        _status_declared("scope", "scope"),
        scope_ceiling,
        location=f"{location}/status/scope",
        findings=findings,
    )
    _status_overclaim(
        _status_declared("mappings", "mappings"),
        mappings_ceiling,
        location=f"{location}/status/mappings",
        findings=findings,
    )

    overall_ceiling = min(
        (
            corpus_ceiling,
            slices_ceiling,
            scope_ceiling,
            mappings_ceiling,
            "blocked" if hard_error else "complete",
        ),
        key=STATUS_RANK.__getitem__,
    )
    _status_overclaim(
        _status_declared("overall", "overall"),
        overall_ceiling,
        location=f"{location}/status/overall",
        findings=findings,
    )


def _technical_authority_snapshot(
    authority_data: object,
    software_data: object,
    repository_root: Path,
    *,
    externalized_receipts: Mapping[str, Mapping[str, object]] | None = None,
    used_externalized_paths: set[str] | None = None,
) -> tuple[
    list[str],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    errors: list[str] = []
    active_authorities: dict[str, dict[str, Any]] = {}
    projection: dict[str, dict[str, Any]] = {}

    if not isinstance(authority_data, dict):
        return ["canonical authority data must be a mapping"], {}, {}
    if authority_data.get("schema_version") != official_source_authorities.SCHEMA_VERSION:
        errors.append("schema_version: expected 1.0")
    authorities = authority_data.get("authorities")
    if not isinstance(authorities, dict):
        errors.append("authorities: expected a mapping")
        return errors, active_authorities, projection

    if not isinstance(software_data, dict):
        errors.append("software_data: expected a mapping")
        return errors, active_authorities, projection
    software_map = software_data.get("software")
    if not isinstance(software_map, dict):
        errors.append("software_data/software: expected a mapping")
        return errors, active_authorities, projection
    software_skill_by_provider: dict[str, str] = {}
    for provider_id, software_entry in software_map.items():
        if (
            isinstance(provider_id, str)
            and official_source_authorities.IDENTIFIER.fullmatch(provider_id)
            and isinstance(software_entry, dict)
        ):
            skill = software_entry.get("calculation_skill")
            if isinstance(skill, str) and skill:
                software_skill_by_provider[provider_id] = skill

    seen_active_authority_ids: set[str] = set()
    for authority_id, entry in authorities.items():
        location = f"authorities/{authority_id}"
        if (
            not isinstance(authority_id, str)
            or official_source_authorities.IDENTIFIER.fullmatch(authority_id)
            is None
        ):
            errors.append(f"{location}: invalid authority identifier")
            continue
        if seen_active_authority_ids and authority_id in seen_active_authority_ids:
            errors.append(f"{location}: duplicate active authority identifier")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{location}: expected a mapping")
            continue
        if entry.get("lifecycle") != "active":
            continue

        provider_id = entry.get("provider_id")
        provider_class = entry.get("provider_class")
        if (
            not isinstance(provider_id, str)
            or official_source_authorities.IDENTIFIER.fullmatch(provider_id) is None
        ):
            errors.append(f"{location}/provider_id: invalid provider identifier")
            continue
        if (
            not isinstance(provider_class, str)
            or provider_class not in official_source_authorities.PROVIDER_CLASSES
        ):
            errors.append(f"{location}/provider_class: unsupported provider class")
            continue

        seen_active_authority_ids.add(authority_id)

        allowed_https_origins = entry.get("allowed_https_origins")
        if (
            not isinstance(allowed_https_origins, list)
            or not allowed_https_origins
        ):
            errors.append(f"{location}/allowed_https_origins: expected nonempty list")
            allowed_https_origins = []
        else:
            if len(allowed_https_origins) != len(set(allowed_https_origins)):
                errors.append(
                    f"{location}/allowed_https_origins: duplicate values are forbidden"
                )
            for index, origin in enumerate(allowed_https_origins):
                if not isinstance(origin, str) or not origin:
                    errors.append(
                        f"{location}/allowed_https_origins/{index}: expected nonempty string"
                    )
                    continue
                if (
                    official_source_authorities._canonical_https_parts(
                        origin,
                        require_path=False,
                    )
                    is None
                ):
                    errors.append(
                        f"{location}/allowed_https_origins/{index}: expected canonical HTTPS origin"
                    )

        version_policy = entry.get("version_policy")
        if not isinstance(version_policy, dict):
            errors.append(f"{location}/version_policy: expected a mapping")
            continue
        allowed_scopes = version_policy.get("allowed_scopes")
        if not isinstance(allowed_scopes, list) or not allowed_scopes:
            errors.append(f"{location}/version_policy/allowed_scopes: expected nonempty list")
            allowed_scopes = []
        if len(allowed_scopes) != len(set(allowed_scopes)):
            errors.append(
                f"{location}/version_policy/allowed_scopes: duplicate values are forbidden"
            )
        for index, scope in enumerate(allowed_scopes):
            if (
                not isinstance(scope, str)
                or scope not in official_source_authorities.VERSION_SCOPES
            ):
                errors.append(
                    f"{location}/version_policy/allowed_scopes/{index}: unsupported scope"
                )

        registered_scopes = version_policy.get("registered_scopes")
        if not isinstance(registered_scopes, list) or not registered_scopes:
            errors.append(
                f"{location}/version_policy/registered_scopes: expected nonempty list"
            )
            registered_scopes = []
        if len(registered_scopes) != len(set(repr(item) for item in registered_scopes)):
            errors.append(
                f"{location}/version_policy/registered_scopes: duplicate scopes are forbidden"
            )
        for index, scope in enumerate(registered_scopes):
            official_source_authorities._valid_version_scope(
                scope,
                f"{location}/version_policy/registered_scopes/{index}",
                errors,
            )
            if (
                isinstance(scope, dict)
                and scope.get("scope") not in allowed_scopes
                and scope.get("scope") is not None
            ):
                errors.append(
                    f"{location}/version_policy/registered_scopes/{index}: scope is not in allowed_scopes"
                )

        content_policy = entry.get("content_policy")
        if not isinstance(content_policy, dict):
            errors.append(f"{location}/content_policy: expected a mapping")
            continue
        source_kinds = content_policy.get("source_kinds")
        if not isinstance(source_kinds, list) or not source_kinds:
            errors.append(f"{location}/content_policy/source_kinds: expected nonempty list")
            source_kinds = []
        else:
            if len(source_kinds) != len(set(source_kinds)):
                errors.append(
                    f"{location}/content_policy/source_kinds: duplicate values are forbidden"
                )
            for index, kind in enumerate(source_kinds):
                if (
                    not isinstance(kind, str)
                    or kind not in official_source_authorities.SOURCE_KINDS
                ):
                    errors.append(
                        f"{location}/content_policy/source_kinds/{index}: unsupported kind"
                    )

        allowed_path_prefixes = content_policy.get("allowed_path_prefixes")
        if not isinstance(allowed_path_prefixes, list) or not allowed_path_prefixes:
            errors.append(
                f"{location}/content_policy/allowed_path_prefixes: expected nonempty list"
            )
            allowed_path_prefixes = []
        else:
            if len(allowed_path_prefixes) != len(set(allowed_path_prefixes)):
                errors.append(
                    f"{location}/content_policy/allowed_path_prefixes: duplicate values are forbidden"
                )
            for index, prefix in enumerate(allowed_path_prefixes):
                if (
                    not isinstance(prefix, str)
                    or not prefix.startswith("/")
                    or not prefix.endswith("/")
                ):
                    errors.append(
                        f"{location}/content_policy/allowed_path_prefixes/{index}: expected absolute path prefix"
                    )
                    continue
                if (
                    "%" in prefix
                    or "\\" in prefix
                    or "//" in prefix
                    or any(part in {".", ".."} for part in prefix.split("/"))
                ):
                    errors.append(
                        f"{location}/content_policy/allowed_path_prefixes/{index}: invalid absolute path prefix"
                    )

        query_policy = content_policy.get("query_policy")
        if query_policy not in {"forbidden", "exact-allowlist"}:
            errors.append(f"{location}/content_policy/query_policy: unsupported policy")
        allowed_query_urls = content_policy.get("allowed_query_urls")
        if not isinstance(allowed_query_urls, list):
            errors.append(
                f"{location}/content_policy/allowed_query_urls: expected list"
            )
            allowed_query_urls = []
        if query_policy == "forbidden":
            if allowed_query_urls:
                errors.append(
                    f"{location}/content_policy/allowed_query_urls: must be empty when query is forbidden"
                )
        else:
            if not allowed_query_urls:
                errors.append(
                    f"{location}/content_policy/allowed_query_urls: expected nonempty list"
                )
            if allowed_query_urls != sorted(allowed_query_urls):
                errors.append(
                    f"{location}/content_policy/allowed_query_urls: must be sorted"
                )
        if len(allowed_query_urls) != len(set(allowed_query_urls)):
            errors.append(
                f"{location}/content_policy/allowed_query_urls: duplicate values are forbidden"
            )
        for index, query_url in enumerate(allowed_query_urls):
            parsed = official_source_authorities._canonical_query_https_parts(query_url)
            if parsed is None:
                errors.append(
                    f"{location}/content_policy/allowed_query_urls/{index}: expected canonical HTTPS query URL"
                )
                continue
            query_origin, query_path = parsed
            if query_origin not in allowed_https_origins or not any(
                query_path.startswith(prefix) for prefix in allowed_path_prefixes
            ):
                errors.append(
                    f"{location}/content_policy/allowed_query_urls/{index}: URL is outside authority locator policy"
                )

        fragment_policy = content_policy.get("fragment_policy")
        if fragment_policy != "forbidden":
            errors.append(f"{location}/content_policy/fragment_policy: must be forbidden")
        resolution_mode = content_policy.get("resolution_mode")
        if resolution_mode not in {
            "platform-verified-only",
            "canonical-pin-or-platform-verified",
        }:
            errors.append(
                f"{location}/content_policy/resolution_mode: unsupported resolution mode"
            )

        identity_policy = entry.get("content_identity_policy")
        if not isinstance(identity_policy, dict):
            errors.append(f"{location}/content_identity_policy: expected mapping")
            continue
        identity_mode = identity_policy.get("mode")
        if identity_mode not in official_source_authorities.CONTENT_IDENTITY_MODES:
            errors.append(f"{location}/content_identity_policy/mode: unsupported mode")
        if identity_policy.get("unpinned_action") != "adapter-required":
            errors.append(
                f"{location}/content_identity_policy/unpinned_action: expected 'adapter-required'"
            )

        canonical_snapshot = None
        if identity_mode in {
            "canonical-pinned-snapshot-or-platform-adapter",
            "canonical-pinned-open-snapshot-or-platform-adapter",
        }:
            if provider_class != "software":
                errors.append(
                    f"{location}/content_identity_policy/mode: canonical pinning requires software provider class"
                )
            else:
                expected_skill = software_skill_by_provider.get(provider_id)
                if expected_skill is None:
                    errors.append(
                        f"{location}/provider_id: active software authority provider missing calculation_skill in software registry"
                    )
                canonical_failures, canonical_projection = (
                    official_source_authorities._canonical_snapshot_projection(
                        authority_id,
                        entry,
                        repository_root,
                        expected_skill,
                        externalized_receipts=externalized_receipts,
                        used_externalized_paths=used_externalized_paths,
                    )
                )
                errors.extend(canonical_failures)
                canonical_snapshot = canonical_projection
                if entry.get("canonical_snapshot") is None:
                    errors.append(
                        f"{location}/canonical_snapshot: canonical-pinned mode requires a canonical snapshot"
                    )
        elif identity_mode == "platform-adapter-only":
            if entry.get("canonical_snapshot") is not None:
                errors.append(
                    f"{location}/canonical_snapshot: platform-adapter-only mode forbids canonical snapshot"
                )
        elif identity_mode == "unresolved":
            if entry.get("canonical_snapshot") is not None:
                errors.append(
                    f"{location}/canonical_snapshot: unresolved mode forbids canonical snapshot"
                )
        else:
            if entry.get("canonical_snapshot") is not None:
                errors.append(
                    f"{location}/canonical_snapshot: unsupported identity mode"
                )

        active_authorities[authority_id] = entry
        projection[authority_id] = {
            "lifecycle": "active",
            "provider_class": provider_class,
            "provider_id": provider_id,
            "allowed_https_origins": list(allowed_https_origins),
            "allowed_path_prefixes": list(allowed_path_prefixes),
            "allowed_query_urls": list(allowed_query_urls),
            "canonical_urls": [
                f"{origin}{prefix}"
                for origin in allowed_https_origins
                for prefix in allowed_path_prefixes
            ],
            "source_kinds": list(source_kinds),
            "version_scopes": list(registered_scopes),
            "content_identity_policy": dict(identity_policy),
            "canonical_snapshot": canonical_snapshot,
        }

    return errors, active_authorities, projection


def validate_files(
    *,
    corpus_paths: Iterable[Path],
    slice_paths: Iterable[Path],
    scope_inventory_path: Path,
    coverage_path: Path,
    source_root: Path | None = None,
    enforce_canonical_pack_closure: bool = False,
    portable_context: PortableValidationContext | None = None,
) -> ValidationResult:
    """Load and validate one closed official-document coverage bundle."""

    corpus_path_list = [Path(item) for item in corpus_paths]
    slice_path_list = [Path(item) for item in slice_paths]
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
        "official-corpus-manifest@1.1",
        "document-slice-manifest@1.1",
        "skill-document-scope-inventory@1.0",
        "skill-document-coverage@1.1",
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
        (
            authority_failures,
            authorities,
            authority_projection,
        ) = _technical_authority_snapshot(
            authority_data,
            software_data,
            repository_root,
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

    corpora_loaded, load_findings = _load_records(
        corpus_path_list,
        catalog=catalog,
        selector="official-corpus-manifest@1.1",
        id_field="corpus_id",
        label="corpus",
    )
    findings.extend(load_findings)
    slices_loaded, load_findings = _load_records(
        slice_path_list,
        catalog=catalog,
        selector="document-slice-manifest@1.1",
        id_field="slice_manifest_id",
        label="slices",
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
        selector="skill-document-coverage@1.1",
        id_field="coverage_id",
        label="coverage",
    )
    findings.extend(load_findings)

    corpora = _index(corpora_loaded, "corpus_id")
    slice_manifests = _index(slices_loaded, "slice_manifest_id")
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
    if len(coverage_loaded) == 1:
        _coverage_findings(
            coverage_loaded[0],
            corpora=corpora,
            slice_manifests=slice_manifests,
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
            for record in (*corpora_loaded, *slices_loaded, *scope_loaded)
        ]
        statuses.append(coverage_loaded[0].data["status"]["overall"])
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
        "PASS: technical corpus partitioning, ordered slices, status closures, "
        "record hashes, and Skill scope coverage are complete"
    )
    return EXIT_PASS


if __name__ == "__main__":
    raise SystemExit(main())
