#!/usr/bin/env python3
"""Build deterministic official-document packs from strict source-tree seeds.

The stable public interface is:

* seed: ``skills/<skill-id>/references/source-pack-seed.json``;
* generated pack: ``references/official-source-pack``;
* CLI: ``--all`` or one-or-more ``--skill`` selectors, plus ``--check``;
* adapters: a static allowlist owned by this module.

Seeds are ordinary Skill sources and therefore participate in the canonical
Skill source-tree digest.  Generated packs are the one independently governed
exception.  A seed supplies bounded inputs and an assurance ceiling; this
builder computes all record identities, registry bindings, source-tree
closure, and final status.
"""

from __future__ import annotations

import argparse
import ast
import copy
from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
from typing import Any, Callable, Sequence

from jsonschema import Draft202012Validator, FormatChecker

from registry_snapshot import RegistrySnapshot, load_registry_snapshot
import extract_official_document_pack_inputs
import skill_registry
import strict_json
import validate_official_document_coverage


SEED_RELATIVE_PATH = PurePosixPath("references", "source-pack-seed.json")
PACK_RELATIVE_PATH = PurePosixPath("references", "official-source-pack")
SEED_SCHEMA_PATH = PurePosixPath(
    "contracts", "official-document-pack-seed.schema.json"
)
CATALOG_SCHEMA_PATH = PurePosixPath(
    "contracts", "official-document-source-catalog-1.1.schema.json"
)
SCOPE_CATALOG_SCHEMA_PATH = PurePosixPath(
    "contracts", "official-document-scope-catalog.schema.json"
)
QE_INPUT_SCHEMA_PATH = PurePosixPath(
    "contracts", "qe-source-pack-input.schema.json"
)
VASP_INPUT_SCHEMA_PATH = PurePosixPath(
    "contracts", "vasp-source-pack-input.schema.json"
)
DEPENDENCY_LOCK_PATH = PurePosixPath(
    "contracts", "official-document-pack-builder-lock.json"
)
CONSUMER_REGISTRY_NAME = "official-document-consumers.yaml"
SKILL_REGISTRY_NAME = "skill-registry.yaml"
BUILDER_VERSION = "1.0"
DEFAULT_GENERATED_UTC = "2026-07-24T00:00:00Z"
MAX_SEED_BYTES = 4 * 1024 * 1024
MAX_CATALOG_BYTES = 64 * 1024 * 1024
SOURCE_IDENTITY_AGGREGATE_DOMAIN = (
    b"VIBE-OFFICIAL-SOURCE-IDENTITY-AGGREGATE-v1\0"
)
SUPPORTED_ADAPTERS = frozenset(
    {
        "declarative-catalog-v1",
        "qe-input-manifest-v1",
        "vasp-wiki-manifest-v1",
    }
)


class PackBuildError(ValueError):
    """Stable fail-closed error for invalid seeds or build inputs."""


@dataclass(frozen=True)
class BuildContext:
    root: Path
    snapshot: RegistrySnapshot
    skill_id: str
    skill_root: Path
    seed_path: Path
    seed: dict[str, Any]


@dataclass(frozen=True)
class BuildSummary:
    selected_skills: tuple[str, ...]
    changed_paths: tuple[str, ...]
    checked: bool


@dataclass(frozen=True)
class ProviderBuild:
    input_id: str
    authority_id: str
    provider_id: str
    version_scope: dict[str, Any]
    retrieved_utc: str
    authority_root: str
    authority_revision: str
    inventory: dict[str, Any]
    source_inventory: dict[str, dict[str, Any]]
    slice_sources: dict[str, dict[str, Any]]
    upstream_universe_complete: bool
    subject_slice_ids: dict[str, tuple[str, ...]]
    limitations: tuple[str, ...]
    blockers: tuple[dict[str, Any], ...]


Adapter = Callable[[BuildContext, dict[str, Any]], ProviderBuild]
ADAPTERS: dict[str, Adapter] = {}


def canonical_json_bytes(value: Any) -> bytes:
    """Return the repository canonical JSON serialization."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _load_json_object(
    path: Path,
    label: str,
    *,
    max_bytes: int = MAX_CATALOG_BYTES,
) -> dict[str, Any]:
    try:
        return strict_json.load_object(path, label, max_bytes=max_bytes)
    except strict_json.StrictJSONError as exc:
        raise PackBuildError(f"{label}: cannot load strict JSON: {exc}") from None


def _schema_validator(
    root: Path,
    relative_path: PurePosixPath,
) -> Draft202012Validator:
    schema_path = root / relative_path
    schema = _load_json_object(
        schema_path,
        str(relative_path),
        max_bytes=MAX_SEED_BYTES,
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _validate_object_schema(
    value: dict[str, Any],
    validator: Draft202012Validator,
    *,
    label: str,
) -> None:
    errors = sorted(
        validator.iter_errors(value),
        key=lambda item: (
            tuple(str(part) for part in item.absolute_path),
            item.message,
        ),
    )
    if errors:
        rendered = "; ".join(
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: "
            f"{error.message}"
            for error in errors
        )
        raise PackBuildError(f"{label}: schema validation failed: {rendered}")


def _skill_entry(snapshot: RegistrySnapshot, skill_id: str) -> dict[str, Any]:
    entry = snapshot.skills["skills"].get(skill_id)
    if not isinstance(entry, dict) or not entry.get("path"):
        raise PackBuildError(f"{skill_id}: not a source-backed registered Skill")
    return entry


def _resolve_skill_ref(
    context: BuildContext,
    ref: dict[str, str],
    *,
    label: str,
) -> Path:
    relative = PurePosixPath(ref["path"])
    expected_prefix = PurePosixPath("skills", context.skill_id)
    if relative.parts[:2] != expected_prefix.parts:
        raise PackBuildError(
            f"{label}: path must remain below skills/{context.skill_id}"
        )
    skill_relative = PurePosixPath(*relative.parts[2:])
    if skill_registry.source_tree_hash_path_excluded(skill_relative):
        raise PackBuildError(f"{label}: generated pack paths are not seed inputs")
    candidate = context.root
    for part in relative.parts:
        candidate = candidate / part
        try:
            if candidate.is_symlink():
                raise PackBuildError(f"{label}: symlink path component is forbidden")
        except OSError as exc:
            raise PackBuildError(
                f"{label}: path component is unsafe ({exc.__class__.__name__})"
            ) from None
    try:
        candidate.resolve(strict=True).relative_to(context.skill_root.resolve())
    except (OSError, ValueError):
        raise PackBuildError(f"{label}: path is absent or escapes the Skill root") from None
    try:
        metadata = candidate.lstat()
    except OSError as exc:
        raise PackBuildError(f"{label}: input is unreadable ({exc.__class__.__name__})") from None
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or metadata.st_nlink != 1
    ):
        raise PackBuildError(f"{label}: path must be a regular non-symlink file")
    try:
        raw = strict_json.read_bytes_bounded(
            candidate,
            label,
            max_bytes=MAX_CATALOG_BYTES,
        )
    except strict_json.StrictJSONError as exc:
        raise PackBuildError(str(exc)) from None
    after = candidate.lstat()
    if (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise PackBuildError(f"{label}: input changed while being hashed")
    actual = sha256_bytes(raw)
    if actual != ref["sha256"]:
        raise PackBuildError(
            f"{label}: sha256 mismatch (recorded {ref['sha256']}, actual {actual})"
        )
    return candidate


def load_seed(
    root: Path,
    snapshot: RegistrySnapshot,
    skill_id: str,
) -> BuildContext:
    entry = _skill_entry(snapshot, skill_id)
    skill_root = root / entry["path"]
    seed_path = skill_root.joinpath(*SEED_RELATIVE_PATH.parts)
    seed = _load_json_object(
        seed_path,
        f"{skill_id} seed",
        max_bytes=MAX_SEED_BYTES,
    )
    _validate_object_schema(
        seed,
        _schema_validator(root, SEED_SCHEMA_PATH),
        label=f"{skill_id} seed",
    )
    if seed["skill_id"] != skill_id:
        raise PackBuildError(
            f"{skill_id} seed: embedded skill_id is {seed['skill_id']!r}"
        )
    _reject_registration_state_blockers(
        seed_blockers=seed["blockers"],
        catalog_blockers=[],
        label=f"{skill_id} seed",
    )
    context = BuildContext(
        root=root,
        snapshot=snapshot,
        skill_id=skill_id,
        skill_root=skill_root,
        seed_path=seed_path,
        seed=seed,
    )
    _resolve_skill_ref(
        context,
        seed["scope_catalog_ref"],
        label=f"{skill_id}:scope_catalog_ref",
    )
    seen_inputs: set[str] = set()
    for provider in seed["providers"]:
        input_id = provider["input_id"]
        if input_id in seen_inputs:
            raise PackBuildError(f"{skill_id} seed: duplicate input_id {input_id!r}")
        seen_inputs.add(input_id)
        if provider["adapter_id"] not in SUPPORTED_ADAPTERS:
            raise PackBuildError(
                f"{skill_id} seed: unsupported adapter {provider['adapter_id']!r}"
            )
        _resolve_skill_ref(
            context,
            provider["source_ref"],
            label=f"{skill_id}:{input_id}:source_ref",
        )
        if "options_ref" in provider:
            _resolve_skill_ref(
                context,
                provider["options_ref"],
                label=f"{skill_id}:{input_id}:options_ref",
            )
    return context


def seeded_skill_ids(root: Path, snapshot: RegistrySnapshot) -> tuple[str, ...]:
    result: list[str] = []
    for skill_id in sorted(snapshot.skills["skills"]):
        entry = snapshot.skills["skills"][skill_id]
        path = entry.get("path") if isinstance(entry, dict) else None
        if path and (root / path).joinpath(*SEED_RELATIVE_PATH.parts).is_file():
            result.append(skill_id)
    return tuple(result)


def canonical_projection_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _safe_id(*parts: object) -> str:
    raw = "-".join(str(item) for item in parts if str(item))
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-.").lower()
    if not slug:
        slug = "record"
    if len(slug) > 128:
        suffix = hashlib.sha256(slug.encode("utf-8")).hexdigest()[:16]
        slug = f"{slug[:111].rstrip('-.')}-{suffix}"
    return slug


def _output_blockers(
    blockers: Sequence[dict[str, Any]],
    *,
    label: str,
    dimension: str | None = None,
) -> list[dict[str, str]]:
    """Project input diagnostic codes into the stricter output ID domain."""

    projected: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for blocker in blockers:
        if dimension is not None and dimension not in blocker["dimensions"]:
            continue
        original = blocker["code"]
        code = _safe_id(original)
        if len(code) < 3:
            code = _safe_id("blocker", code)
        previous = seen.get(code)
        if previous is not None:
            raise PackBuildError(
                f"{label}: blocker codes {previous!r} and {original!r} "
                f"collide after safe output projection as {code!r}"
            )
        seen[code] = original
        projected.append(
            {
                "code": code,
                "description": blocker["description"],
            }
        )
    return projected


def _reject_registration_state_blockers(
    *,
    seed_blockers: Sequence[str],
    catalog_blockers: Sequence[dict[str, Any]],
    label: str,
) -> None:
    """Keep central registration state out of evidence-gap blocker ledgers."""

    absence = re.compile(
        r"\b(?:absent|unregistered|not present|not registered|"
        r"not landed|have not landed|not reviewed|not activated|"
        r"not been reviewed|not been activated)\b",
        re.IGNORECASE,
    )
    for description in seed_blockers:
        folded = description.casefold()
        if (
            "central" in folded
            and any(
                token in folded
                for token in ("authority", "authorities", "binding", "bindings")
            )
            and absence.search(description)
        ):
            raise PackBuildError(
                f"{label}: blocker duplicates central registration state; "
                "authority and binding presence is enforced structurally"
            )
    for blocker in catalog_blockers:
        normalized = re.sub(
            r"[^a-z0-9]+",
            "-",
            blocker["code"].casefold(),
        ).strip("-")
        if (
            "authority-unregistered" in normalized
            or "binding-unregistered" in normalized
        ):
            raise PackBuildError(
                f"{label}: blocker duplicates central registration state; "
                "resolved authority and binding records cannot remain "
                "UNREGISTERED blockers"
            )


def _output_id_map(
    values: Sequence[str],
    *,
    label: str,
) -> dict[str, str]:
    """Create a collision-free projection into the output contract ID domain."""

    projected: dict[str, str] = {}
    reverse: dict[str, str] = {}
    for original in values:
        output = _safe_id(original)
        if len(output) < 3:
            output = _safe_id("record", output)
        previous = reverse.get(output)
        if previous is not None:
            raise PackBuildError(
                f"{label}: IDs {previous!r} and {original!r} collide after "
                f"safe output projection as {output!r}"
            )
        projected[original] = output
        reverse[output] = original
    return projected


def _output_version_scope(
    value: dict[str, Any],
    *,
    rolling_snapshot_sha256: str | None = None,
) -> dict[str, Any]:
    """Project permissive catalog evidence into the strict corpus contract."""

    kind = value["kind"]
    if kind == "latest-at-retrieval":
        if value.get("snapshot_identity") is not None:
            raise PackBuildError(
                "catalog-provided rolling snapshot identity is not independent "
                "evidence and cannot be promoted into the corpus contract"
            )
        if (
            not isinstance(rolling_snapshot_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", rolling_snapshot_sha256) is None
        ):
            raise PackBuildError(
                "latest-at-retrieval requires an independent rolling snapshot "
                "identity derived from the included source identities"
            )
        return {
            "kind": kind,
            "value": None,
            "retrieved_utc": _utc(value["retrieved_utc"]),
            "snapshot_identity": {
                "kind": "sha256",
                "value": rolling_snapshot_sha256,
                "content_sha256": rolling_snapshot_sha256,
            },
        }
    return {
        "kind": kind,
        "value": None if kind == "unversioned" else value["value"],
        "retrieved_utc": None,
        "snapshot_identity": None,
    }


def _source_identity_aggregate_sha256(
    *,
    authority_id: str,
    provider_id: str,
    retrieved_utc: str,
    included_sources: Sequence[dict[str, Any]],
    reviewed_exclusions: Sequence[dict[str, Any]],
) -> str:
    """Hash the rolling corpus identity independently from its source catalog."""

    projection = {
        "authority_id": authority_id,
        "provider_id": provider_id,
        "retrieved_utc": retrieved_utc,
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
                for source in included_sources
            ),
            key=lambda source: source["source_id"],
        ),
        "reviewed_exclusions": sorted(
            (
                {
                    "source_id": exclusion["source_id"],
                    "reason_code": exclusion["reason_code"],
                }
                for exclusion in reviewed_exclusions
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
    return hashlib.sha256(SOURCE_IDENTITY_AGGREGATE_DOMAIN + raw).hexdigest()


def _source_version_scope(
    corpus_scope: dict[str, Any],
    *,
    raw_sha256: str,
) -> dict[str, Any]:
    """Bind rolling source identity to its own bytes, not the catalog bytes."""

    if corpus_scope["kind"] != "latest-at-retrieval":
        return copy.deepcopy(corpus_scope)
    return {
        "kind": "latest-at-retrieval",
        "value": None,
        "retrieved_utc": corpus_scope["retrieved_utc"],
        "snapshot_identity": {
            "kind": "sha256",
            "value": raw_sha256,
            "content_sha256": raw_sha256,
        },
    }


def _require_registered_version_scope(
    *,
    skill_id: str,
    input_id: str,
    version_scope: dict[str, Any],
    registered_scopes: object,
) -> None:
    """Fail rather than normalize an unproven catalog/authority version."""

    if (
        validate_official_document_coverage
        .authority_version_scope_compatible(
            version_scope,
            registered_scopes,
        )
    ):
        return
    raise PackBuildError(
        f"{skill_id}:{input_id}: output version scope "
        f"{version_scope['kind']!r} with value {version_scope['value']!r} "
        "has no exact compatible central authority registration; aliases and "
        "version normalization are not inferred"
    )


def _declarative_inventory_projection(
    context: BuildContext,
    provider: dict[str, Any],
    *,
    authority_entry: dict[str, Any],
    authority_projection: dict[str, Any],
    mapped_discovered_ids: set[str],
    upstream_universe_complete: bool,
) -> tuple[str, str, str, bool]:
    """Bind a declarative corpus to the strongest exact local inventory.

    Most declarative catalogs are their own bounded inventory. A centrally
    pinned CP2K snapshot is different: its canonical index is the exact
    upstream universe, while its manifest is the exact curated subset. Never
    relabel the catalog file as either canonical artifact.
    """

    canonical = authority_projection.get("canonical_snapshot")
    if canonical is None:
        return (
            "declarative-source-catalog-v1",
            provider["source_ref"]["path"],
            provider["source_ref"]["sha256"],
            False,
        )
    if not (
        isinstance(canonical, dict)
        and isinstance(canonical.get("upstream_sources_by_id"), dict)
        and isinstance(canonical.get("sources_by_id"), dict)
        and isinstance(canonical.get("index_raw_sha256"), str)
        and isinstance(canonical.get("manifest_raw_sha256"), str)
    ):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: unsupported canonical "
            "snapshot projection for declarative inventory binding"
        )
    central_snapshot = authority_entry.get("canonical_snapshot")
    manifest_path = (
        central_snapshot.get("manifest_path")
        if isinstance(central_snapshot, dict)
        else None
    )
    if not isinstance(manifest_path, str):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: canonical snapshot "
            "manifest path is unavailable"
        )
    upstream_ids = set(canonical["upstream_sources_by_id"])
    curated_ids = set(canonical["sources_by_id"])
    if upstream_universe_complete:
        if mapped_discovered_ids != upstream_ids:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: declared complete "
                "source universe does not exactly equal the canonical index"
            )
        inventory_path = (
            PurePosixPath(manifest_path).parent / "index.json"
        ).as_posix()
        return (
            "cp2k-official-index-v1",
            inventory_path,
            canonical["index_raw_sha256"],
            True,
        )
    if mapped_discovered_ids != curated_ids:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: declared bounded "
            "source universe does not exactly equal the canonical manifest"
        )
    return (
        "cp2k-canonical-manifest-v1",
        manifest_path,
        canonical["manifest_raw_sha256"],
        False,
    )


def _utc(value: str | None) -> str:
    if not value:
        return DEFAULT_GENERATED_UTC
    if value.endswith("+00:00"):
        return value[:-6] + "Z"
    return value


def _read_regular_bytes(
    path: Path,
    *,
    label: str,
    maximum: int = MAX_CATALOG_BYTES,
) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise PackBuildError(f"{label}: unavailable ({exc.__class__.__name__})") from None
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or before.st_nlink != 1
    ):
        raise PackBuildError(
            f"{label}: expected one regular, non-symlink, non-hard-linked file"
        )
    try:
        raw = strict_json.read_bytes_bounded(path, label, max_bytes=maximum)
        after = path.lstat()
    except (OSError, strict_json.StrictJSONError) as exc:
        raise PackBuildError(f"{label}: unsafe read ({exc})") from None
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise PackBuildError(f"{label}: file changed while being read")
    return raw


def _read_catalog_ref(
    context: BuildContext,
    ref: dict[str, Any],
    *,
    label: str,
) -> tuple[Path, bytes]:
    path = _resolve_skill_ref(context, ref, label=label)
    raw = _read_regular_bytes(path, label=label)
    if sha256_bytes(raw) != ref["sha256"]:
        raise PackBuildError(f"{label}: hash changed after reference validation")
    return path, raw


def _validate_content_ref(
    context: BuildContext,
    ref: dict[str, Any],
    *,
    label: str,
) -> bytes:
    path, raw = _read_catalog_ref(context, ref, label=label)
    if len(raw) != ref["bytes"]:
        raise PackBuildError(
            f"{label}: byte count mismatch (recorded {ref['bytes']}, actual {len(raw)})"
        )
    if path.is_symlink():
        raise PackBuildError(f"{label}: symlink inputs are forbidden")
    return raw


def _load_schema_bound_ref(
    context: BuildContext,
    ref: dict[str, Any],
    *,
    label: str,
    schema_path: PurePosixPath,
) -> dict[str, Any]:
    path, raw = _read_catalog_ref(context, ref, label=label)
    try:
        value = strict_json.loads_object(raw, label, max_bytes=MAX_CATALOG_BYTES)
    except strict_json.StrictJSONError as exc:
        raise PackBuildError(str(exc)) from None
    _validate_object_schema(
        value,
        _schema_validator(context.root, schema_path),
        label=label,
    )
    if path.is_symlink():
        raise PackBuildError(f"{label}: symlink inputs are forbidden")
    return value


def _attest_replayed_catalog(
    context: BuildContext,
    provider: dict[str, Any],
    *,
    catalog_path: Path,
    catalog_raw: bytes,
    catalog: dict[str, Any],
) -> None:
    """Replay one specialized legacy mirror into its compact projection.

    The compact catalog is the generated pack's inventory and is safe for an
    active-only distribution.  In the full source repository, however, a
    production build must also prove that the exact legacy manifest and every
    raw/wrapper/payload file still derive that catalog byte-for-byte.
    """

    options_ref = provider.get("options_ref")
    if not isinstance(options_ref, dict):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: specialized adapter "
            "requires a hashed options_ref legacy manifest"
        )
    options_path, options_raw = _read_catalog_ref(
        context,
        options_ref,
        label=f"{context.skill_id}:{provider['input_id']}:options_ref",
    )
    if catalog.get("legacy_manifest_sha256") != sha256_bytes(options_raw):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: compact catalog does "
            "not bind the exact options_ref legacy manifest"
        )
    adapter_id = provider["adapter_id"]
    if adapter_id == "qe-input-manifest-v1":
        expected_options = (
            context.skill_root / "references" / "official-manifest.json"
        )
        replay = extract_official_document_pack_inputs.qe_catalog
    elif adapter_id == "vasp-wiki-manifest-v1":
        expected_options = (
            context.skill_root
            / "references"
            / "official-wiki"
            / "manifest.json"
        )
        replay = extract_official_document_pack_inputs.vasp_catalog
    else:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: adapter has no "
            "specialized replay contract"
        )
    try:
        if options_path.resolve(strict=True) != expected_options.resolve(
            strict=True
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: options_ref is not "
                "the adapter's canonical legacy manifest"
            )
        replay_path, replay_raw = replay(context.root)
        if replay_path.resolve(strict=True) != catalog_path.resolve(strict=True):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: replay target does "
                "not equal source_ref"
            )
    except extract_official_document_pack_inputs.ExtractionError as exc:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: legacy replay failed: {exc}"
        ) from None
    except OSError as exc:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: legacy replay path is "
            f"unsafe ({exc.__class__.__name__})"
        ) from None
    if replay_raw != catalog_raw:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: compact source_ref is "
            "not the byte-exact deterministic projection of the legacy mirror"
        )


def _validate_dependency_lock(context: BuildContext) -> None:
    """Verify the exact adapter/schema/runtime dependency lock."""

    path = context.root.joinpath(*DEPENDENCY_LOCK_PATH.parts)
    raw = _read_regular_bytes(
        path,
        label=DEPENDENCY_LOCK_PATH.as_posix(),
        maximum=MAX_SEED_BYTES,
    )
    try:
        lock = strict_json.loads_object(
            raw,
            DEPENDENCY_LOCK_PATH.as_posix(),
            max_bytes=MAX_SEED_BYTES,
        )
    except strict_json.StrictJSONError as exc:
        raise PackBuildError(str(exc)) from None
    if (
        set(lock)
        != {
            "schema_version",
            "contract_name",
            "builder_version",
            "python_major_minor_allowlist",
            "dependency_manifest_ref",
            "python_dependencies",
            "configuration_contract_refs",
            "adapters",
            "runtime_refs",
            "output_contract_refs",
        }
        or lock["schema_version"] != "1.0"
        or lock["contract_name"]
        != "official-document-pack-builder-lock"
        or lock["builder_version"] != BUILDER_VERSION
        or lock["python_major_minor_allowlist"] != ["3.12", "3.14"]
    ):
        raise PackBuildError("official-document pack dependency lock root is invalid")
    running_python = f"{sys.version_info.major}.{sys.version_info.minor}"
    if running_python not in lock["python_major_minor_allowlist"]:
        raise PackBuildError(
            f"Python {running_python} is outside the exact pack-builder "
            "runtime allowlist"
        )

    expected_configuration = {
        SEED_SCHEMA_PATH.as_posix(),
        SCOPE_CATALOG_SCHEMA_PATH.as_posix(),
    }
    expected_adapter_contracts = {
        "declarative-catalog-v1": CATALOG_SCHEMA_PATH.as_posix(),
        "qe-input-manifest-v1": QE_INPUT_SCHEMA_PATH.as_posix(),
        "vasp-wiki-manifest-v1": VASP_INPUT_SCHEMA_PATH.as_posix(),
    }
    expected_replay = {
        "declarative-catalog-v1": (),
        "qe-input-manifest-v1": (
            "tools/extract_official_document_pack_inputs.py",
            "skills/qe-rigorous-calculations/scripts/qe_guard.py",
        ),
        "vasp-wiki-manifest-v1": (
            "tools/extract_official_document_pack_inputs.py",
        ),
    }
    tools_root = context.root / "tools"
    pending = [tools_root / "build_official_document_packs.py"]
    visited: set[Path] = set()
    expected_runtime: set[str] = set()
    while pending:
        module_path = pending.pop()
        resolved_module = module_path.resolve(strict=True)
        if resolved_module in visited:
            continue
        visited.add(resolved_module)
        try:
            syntax = ast.parse(
                _read_regular_bytes(
                    module_path,
                    label=f"dependency AST {module_path.name}",
                ),
                filename=module_path.as_posix(),
            )
        except SyntaxError as exc:
            raise PackBuildError(
                f"dependency AST {module_path.name}: invalid Python source"
            ) from exc
        imported_names: set[str] = set()
        for node in ast.walk(syntax):
            if isinstance(node, ast.Import):
                imported_names.update(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif (
                isinstance(node, ast.ImportFrom)
                and node.level == 0
                and node.module
            ):
                imported_names.add(node.module.split(".", 1)[0])
        for module_name in imported_names:
            candidate = tools_root / f"{module_name}.py"
            if candidate.is_file() and candidate.resolve() not in visited:
                expected_runtime.add(
                    candidate.relative_to(context.root).as_posix()
                )
                pending.append(candidate)
    # qe_guard is loaded dynamically by the QE replay adapter and therefore is
    # intentionally added to the statically discovered tools closure.
    expected_runtime.add(
        "skills/qe-rigorous-calculations/scripts/qe_guard.py"
    )
    expected_outputs = {
        "contracts/common-definitions-1.0.schema.json",
        "contracts/skill-document-scope-inventory.schema.json",
        "contracts/official-corpus-manifest-1.1.schema.json",
        "contracts/document-slice-manifest-1.1.schema.json",
        "contracts/skill-document-coverage-1.1.schema.json",
    }

    def verify_ref(value: Any, *, label: str) -> str:
        if (
            not isinstance(value, dict)
            or set(value) != {"path", "sha256"}
            or not isinstance(value["path"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", value["sha256"])
        ):
            raise PackBuildError(f"{label}: invalid dependency file reference")
        relative = PurePosixPath(value["path"])
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in value["path"]
        ):
            raise PackBuildError(f"{label}: unsafe dependency path")
        target = context.root
        for part in relative.parts:
            target = target / part
            try:
                if target.is_symlink():
                    raise PackBuildError(
                        f"{label}: symlink dependency path component"
                    )
            except OSError as exc:
                raise PackBuildError(
                    f"{label}: unsafe dependency path "
                    f"({exc.__class__.__name__})"
                ) from None
        try:
            target.resolve(strict=True).relative_to(
                context.root.resolve(strict=True)
            )
        except (OSError, ValueError):
            raise PackBuildError(
                f"{label}: dependency path escapes or is unavailable"
            ) from None
        payload = _read_regular_bytes(target, label=label)
        if sha256_bytes(payload) != value["sha256"]:
            raise PackBuildError(f"{label}: dependency hash mismatch")
        return relative.as_posix()

    def verify_ref_list(
        value: Any,
        *,
        label: str,
    ) -> list[str]:
        if not isinstance(value, list):
            raise PackBuildError(f"{label}: dependency references must be a list")
        paths = [
            verify_ref(item, label=f"{label}[{index}]")
            for index, item in enumerate(value)
        ]
        if len(paths) != len(set(paths)):
            raise PackBuildError(f"{label}: duplicate dependency path")
        return paths

    manifest_path = verify_ref(
        lock["dependency_manifest_ref"],
        label="dependency lock Python manifest",
    )
    if manifest_path != "requirements-dev.txt":
        raise PackBuildError("dependency lock Python manifest is not canonical")
    if lock["python_dependencies"] != [
        {"distribution": "PyYAML", "version": "6.0.3"},
        {"distribution": "jsonschema", "version": "4.26.0"},
    ]:
        raise PackBuildError(
            "dependency lock Python dependency record is not exact"
        )
    requirements_text = _read_regular_bytes(
        context.root / manifest_path,
        label="dependency lock requirements-dev.txt",
        maximum=MAX_SEED_BYTES,
    ).decode("utf-8", errors="strict").splitlines()
    if (
        "PyYAML==6.0.3" not in requirements_text
        or "jsonschema==4.26.0" not in requirements_text
    ):
        raise PackBuildError(
            "dependency lock Python dependency declarations are absent"
        )
    for dependency in lock["python_dependencies"]:
        try:
            observed_version = importlib.metadata.version(
                dependency["distribution"]
            )
        except importlib.metadata.PackageNotFoundError:
            raise PackBuildError(
                f"dependency lock Python distribution "
                f"{dependency['distribution']!r} is unavailable"
            ) from None
        if observed_version != dependency["version"]:
            raise PackBuildError(
                f"dependency lock Python distribution "
                f"{dependency['distribution']!r} requires "
                f"{dependency['version']}, observed {observed_version}"
            )

    configuration_paths = set(
        verify_ref_list(
            lock["configuration_contract_refs"],
            label="dependency lock configuration",
        )
    )
    if configuration_paths != expected_configuration:
        raise PackBuildError(
            "dependency lock configuration contract set is not exact"
        )
    if (
        not isinstance(lock["adapters"], dict)
        or set(lock["adapters"]) != set(expected_adapter_contracts)
    ):
        raise PackBuildError("dependency lock adapter set is not exact")
    for adapter_id, expected_contract in expected_adapter_contracts.items():
        adapter = lock["adapters"][adapter_id]
        if (
            not isinstance(adapter, dict)
            or set(adapter)
            != {
                "input_contract_ref",
                "replay_required",
                "replay_runtime_paths",
            }
            or adapter["replay_required"]
            != bool(expected_replay[adapter_id])
            or adapter["replay_runtime_paths"]
            != list(expected_replay[adapter_id])
            or verify_ref(
                adapter["input_contract_ref"],
                label=f"dependency lock adapter {adapter_id}",
            )
            != expected_contract
        ):
            raise PackBuildError(
                f"dependency lock adapter {adapter_id!r} is not exact"
            )
    runtime_paths = set(
        verify_ref_list(
            lock["runtime_refs"],
            label="dependency lock runtime",
        )
    )
    if runtime_paths != expected_runtime:
        raise PackBuildError("dependency lock runtime set is not exact")
    output_paths = set(
        verify_ref_list(
            lock["output_contract_refs"],
            label="dependency lock output",
        )
    )
    if output_paths != expected_outputs:
        raise PackBuildError("dependency lock output contract set is not exact")


def _processor_refs(context: BuildContext) -> dict[str, dict[str, str]]:
    paths = {
        "implementation_ref": PurePosixPath(
            "tools", "build_official_document_packs.py"
        ),
        "configuration_ref": SEED_SCHEMA_PATH,
        "dependency_lock_ref": DEPENDENCY_LOCK_PATH,
    }
    return {
        field: {
            "path": path.as_posix(),
            "sha256": sha256_file(context.root.joinpath(*path.parts)),
        }
        for field, path in paths.items()
    }


def _processor_refs_v11(context: BuildContext) -> dict[str, dict[str, Any]]:
    paths = {
        "implementation_ref": PurePosixPath(
            "tools", "build_official_document_packs.py"
        ),
        "configuration_ref": SEED_SCHEMA_PATH,
        "dependency_lock_ref": DEPENDENCY_LOCK_PATH,
    }
    return {
        field: {
            "path": path.as_posix(),
            "sha256": sha256_file(context.root.joinpath(*path.parts)),
            "bytes": context.root.joinpath(*path.parts).stat().st_size,
        }
        for field, path in paths.items()
    }


def _processor(
    context: BuildContext,
    *,
    kind: str,
    input_sha256: str,
    output_sha256: str,
) -> dict[str, Any]:
    identifiers = {
        "enumerator": ("enumerator_id", "enumerator_version"),
        "transformer": ("transformer_id", "transformer_version"),
        "extractor": ("tool_id", "tool_version"),
    }
    id_field, version_field = identifiers[kind]
    identity = {
        "enumerator": "official-document-pack-enumerator",
        "transformer": "official-document-pack-transformer",
        "extractor": "official-document-pack-scope-extractor",
    }[kind]
    result: dict[str, Any] = {
        id_field: identity,
        version_field: BUILDER_VERSION,
        "trust_mode": "central-pinned",
        **_processor_refs(context),
        "output_sha256": output_sha256,
        "attestation_id": None,
    }
    result[
        "input_raw_sha256" if kind == "transformer" else "input_sha256"
    ] = input_sha256
    if kind == "transformer":
        result["deterministic"] = True
    return result


def _processor_v11(
    context: BuildContext,
    *,
    processor_id: str,
    processor_version: str,
    assurance_mode: str,
    input_sha256: str,
    output_sha256: str,
    attestation_id: str | None = None,
) -> dict[str, Any]:
    if assurance_mode not in {"unverified", "pinned", "attested"}:
        raise PackBuildError(
            f"{context.skill_id}: unsupported assurance mode {assurance_mode!r}"
        )
    if assurance_mode in {"unverified", "pinned"}:
        if attestation_id is not None:
            raise PackBuildError(
                f"{context.skill_id}: {assurance_mode} processors require "
                "attestation_id to be None"
            )
    else:
        if not isinstance(attestation_id, str) or not attestation_id:
            raise PackBuildError(
                f"{context.skill_id}: attested processors require an "
                "explicit non-empty attestation_id"
            )
    refs = (
        None
        if assurance_mode == "unverified"
        else _processor_refs_v11(context)
    )
    return {
        "processor_id": processor_id,
        "processor_version": processor_version,
        "assurance_mode": assurance_mode,
        "implementation_ref": (
            None
            if refs is None
            else refs["implementation_ref"]
        ),
        "configuration_ref": (
            None
            if refs is None
            else refs["configuration_ref"]
        ),
        "dependency_lock_ref": (
            None
            if refs is None
            else refs["dependency_lock_ref"]
        ),
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "attestation_id": None if assurance_mode != "attested" else attestation_id,
        "deterministic": True,
    }


def _receipt(
    context: BuildContext,
    *,
    receipt_id: str,
    canonical_url: str,
    retrieved_utc: str,
    raw_sha256: str,
    raw_bytes: int,
    selected_sha256: str,
    selected_bytes: int,
    evidence_sha256: str,
) -> dict[str, Any]:
    return {
        "receipt_id": _safe_id(receipt_id),
        "resolver_id": "official-document-pack-builder",
        "canonical_url": canonical_url,
        "retrieved_utc": _utc(retrieved_utc),
        "raw_sha256": raw_sha256,
        "raw_bytes": raw_bytes,
        "selected_sha256": selected_sha256,
        "selected_bytes": selected_bytes,
        "selection_attestation_id": None,
        "evidence_sha256": evidence_sha256,
        "trust_mode": "unverified",
        "registry_path": "registry/official-document-consumers.yaml",
        "registry_sha256": context.snapshot.registry_sha256[
            CONSUMER_REGISTRY_NAME
        ],
        "trust_id": None,
        "verification_status": "unverified",
    }


def _central_binding(
    context: BuildContext,
    provider: dict[str, Any],
) -> dict[str, Any]:
    matches = [
        item
        for item in context.snapshot.official_document_consumers["bindings"]
        if item["consumer_skill_id"] == context.skill_id
        and item["authority_id"] == provider["authority_id"]
        and item["provider_id"] == provider["provider_id"]
    ]
    if len(matches) != 1:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: expected exactly one "
            "consumer binding for the Skill/authority/provider tuple"
        )
    return matches[0]


def _authority(
    context: BuildContext,
    provider: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    authority = context.snapshot.official_source_authorities["authorities"].get(
        provider["authority_id"]
    )
    projection = context.snapshot.official_source_authority_projection.get(
        provider["authority_id"]
    )
    if (
        not isinstance(authority, dict)
        or authority.get("lifecycle") != "active"
        or authority.get("provider_id") != provider["provider_id"]
        or not isinstance(projection, dict)
    ):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: authority/provider is "
            "not an exact active central match"
        )
    _central_binding(context, provider)
    return authority, projection


def _scope_catalog(context: BuildContext) -> dict[str, Any]:
    value = _load_schema_bound_ref(
        context,
        context.seed["scope_catalog_ref"],
        label=f"{context.skill_id}:scope_catalog_ref",
        schema_path=SCOPE_CATALOG_SCHEMA_PATH,
    )
    if value["skill_id"] != context.skill_id:
        raise PackBuildError(
            f"{context.skill_id}: scope catalog skill_id does not match the seed"
        )
    if value["extractor_id"] != context.seed["scope_extractor_id"]:
        raise PackBuildError(
            f"{context.skill_id}: seed scope_extractor_id does not exactly match "
            "the hashed scope catalog"
        )
    provider_ids = {item["input_id"] for item in context.seed["providers"]}
    seen_subjects: set[str] = set()
    for index, subject in enumerate(value["subjects"]):
        subject_id = subject["subject_id"]
        if subject_id in seen_subjects:
            raise PackBuildError(
                f"{context.skill_id}: duplicate scope subject_id {subject_id!r}"
            )
        seen_subjects.add(subject_id)
        if not set(subject["provider_input_ids"]).issubset(provider_ids):
            raise PackBuildError(
                f"{context.skill_id}: scope subject {subject_id!r} names an "
                "unknown provider input"
            )
        for origin_index, origin in enumerate(subject["origin_refs"]):
            _resolve_skill_ref(
                context,
                origin,
                label=(
                    f"{context.skill_id}:scope:{index}:origin:{origin_index}"
                ),
            )
    return value


def _source_identity_from_catalog(
    context: BuildContext,
    provider: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    content = source["content"]
    content_mode = content["content_mode"]
    if content_mode == "embedded-content":
        content_ref = {
            "path": content["locator"],
            "sha256": content["sha256"],
        }
        content_path = _resolve_skill_ref(
            context,
            content_ref,
            label=(
                f"{context.skill_id}:{provider['input_id']}:"
                f"{source['source_id']}:embedded-content"
            ),
        )
        raw = _read_regular_bytes(
            content_path,
            label=(
                f"{context.skill_id}:{provider['input_id']}:"
                f"{source['source_id']}:embedded-content"
            ),
            maximum=MAX_CATALOG_BYTES,
        )
        if len(raw) != content["bytes"]:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: "
                f"{source['source_id']}: embedded source bytes mismatch"
            )
        if sha256_bytes(raw) != content["sha256"]:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: "
                f"{source['source_id']}: embedded source identity mismatch"
            )
        return {
            "content_mode": "embedded-content",
            "locator": content["locator"],
            "sha256": content["sha256"],
            "bytes": content["bytes"],
        }
    if content_mode == "external-content":
        return {
            "content_mode": "external-content",
            "locator": content["locator"],
            "receipt": copy.deepcopy(content["receipt"]),
        }
    if content_mode == "metadata-only":
        return {
            "content_mode": "metadata-only",
            "locator": content["locator"],
            "identity": copy.deepcopy(content["identity"]),
        }
    if content_mode == "excluded":
        return {
            "content_mode": "excluded",
            "locator": content["locator"],
            "inventory_entry_identity": copy.deepcopy(
                content["inventory_entry_identity"]
            ),
        }
    raise PackBuildError(
        f"{context.skill_id}:{provider['input_id']}: "
        f"{source['source_id']}: unsupported content mode {content_mode!r}"
    )


def _output_loss(loss: dict[str, Any], slice_ids: list[str]) -> dict[str, Any]:
    severity = {
        "none": "informational",
        "non-material": "informational",
        "material": "material",
        "unknown": "material",
    }[loss["materiality"]]
    disposition = {
        "accepted": "normalized",
        "preserved": "preserved",
        "external-only": "external-only",
        "blocked": "unresolved",
    }[loss["disposition"]]
    if loss["disposition"] == "blocked":
        severity = "blocking"
    return {
        "loss_id": loss["loss_id"],
        "category": {
            "discovery": "metadata",
            "retrieval": "asset",
            "extraction": "code",
            "normalization": "encoding",
            "storage": "other",
            "mapping": "metadata",
            "other": "other",
        }[loss["stage"]],
        "severity": severity,
        "disposition": disposition,
        "description": loss["description"],
    }


def _blocking_loss_blockers(
    losses: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Promote explicit blocking losses into provider-level status evidence."""

    return [
        {
            "code": _safe_id("loss", loss["loss_id"]),
            "description": (
                "The provider document projection has an unresolved blocking "
                f"official-document loss: {loss['loss_id']}."
            ),
            "dimensions": ["slices"],
        }
        for loss in losses
        if loss["disposition"] == "blocked"
    ]


def _slice_from_catalog(
    context: BuildContext,
    provider: dict[str, Any],
    source: dict[str, Any],
    identity: dict[str, Any],
    selector: dict[str, Any],
    raw_source_extent_bytes: int,
) -> dict[str, Any]:
    selector = copy.deepcopy(selector)
    selector_identity = selector.get("selected_identity")
    if selector_identity is None:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
            f"{selector['selector_id']}: selected_identity missing and must be required"
        )
    if (
        not isinstance(selector_identity, dict)
        or set(selector_identity) != {"sha256", "bytes"}
        or not isinstance(selector_identity["sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", selector_identity["sha256"])
        or isinstance(selector_identity["bytes"], bool)
        or not isinstance(selector_identity["bytes"], int)
        or selector_identity["bytes"] <= 0
    ):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
            f"{selector['selector_id']}: selected_identity must be byteIdentity"
        )

    if selector["kind"] == "byte-range":
        start, byte_count = (
            int(value) for value in selector["value"].split(":", 1)
        )
        if start < 0 or byte_count <= 0:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
                f"{selector['selector_id']}: byte-range must be non-negative and "
                "non-zero"
            )
        if start + byte_count > raw_source_extent_bytes:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
                f"{selector['selector_id']}: byte-range exceeds source extent"
            )
        raw_byte_range = {
            "start_byte": start,
            "byte_count": byte_count,
        }
        if selector["layer"] == "derived-artifact":
            raw_byte_range = {
                "start_byte": 0,
                "byte_count": raw_source_extent_bytes,
            }
    else:
        raw_byte_range = {
            "start_byte": 0,
            "byte_count": raw_source_extent_bytes,
        }

    selector_emitted = {
        "layer": selector["layer"],
        "kind": selector["kind"],
        "value": selector["value"],
    }
    if identity["content_mode"] == "embedded-content":
        if (
            selector["layer"] != "raw-source"
            or selector["kind"] != "whole-source"
            or selector_identity["sha256"] != identity["sha256"]
            or selector_identity["bytes"] != identity["bytes"]
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
                f"{selector['selector_id']}: embedded selector must be raw whole-source "
                "and selected_identity must equal embedded source identity"
            )
        is_complete_range = (
            selector["kind"] != "byte-range"
            or (
                raw_byte_range["start_byte"] == 0
                and raw_byte_range["byte_count"] == raw_source_extent_bytes
            )
        )
        if not is_complete_range:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
                f"{selector['selector_id']}: embedded-content cannot be claimed by partial selector"
            )
        content = {
            "content_mode": "embedded-content",
            "artifact": {
                "path": identity["locator"],
                "sha256": identity["sha256"],
                "bytes": identity["bytes"],
            },
            "hash_basis": "exact-artifact-bytes",
        }
    elif identity["content_mode"] == "external-content":
        if selector["kind"] == "whole-source":
            if (
                selector_identity["sha256"] != identity["receipt"]["raw_sha256"]
                or selector_identity["bytes"] != identity["receipt"]["raw_bytes"]
            ):
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
                    f"{selector['selector_id']}: external whole-source selector selected_identity "
                    "must match source receipt identity"
                )
            content = {
                "content_mode": "external-content",
                "locator": identity["locator"],
                "receipt": {
                    **identity["receipt"],
                    "selected_content": {
                        "sha256": identity["receipt"]["raw_sha256"],
                        "bytes": identity["receipt"]["raw_bytes"],
                    },
                },
                "hash_basis": "external-receipt-bytes",
            }
        elif selector["layer"] == "raw-source":
            if selector["kind"] != "byte-range":
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
                    f"{selector['selector_id']}: non-whole external selectors on raw "
                    "source must be byte-range"
                )
            if selector_identity["bytes"] != raw_byte_range["byte_count"]:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
                    f"{selector['selector_id']}: selected_identity bytes must equal "
                    "selector byte-range byte_count"
                )
            content = {
                "content_mode": "metadata-only",
                "locator": identity["locator"],
                "identity": copy.deepcopy(selector_identity),
                "hash_basis": "metadata-identity-bytes",
            }
        else:
            content = {
                "content_mode": "metadata-only",
                "locator": identity["locator"],
                "identity": {
                    "sha256": selector_identity["sha256"],
                    "bytes": selector_identity["bytes"],
                },
                "hash_basis": "metadata-identity-bytes",
            }
    else:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}:{source['source_id']}:"
            f"unsupported source content mode {identity['content_mode']!r}"
        )
    return {
        "slice_id": selector["selector_id"],
        "selector": selector_emitted,
        "raw_byte_range": raw_byte_range,
        "content": content,
        "subject_ids": list(selector["subject_ids"]),
        "loss_accounting": {},
    }


def _slice_processor_v11(
    context: BuildContext,
    *,
    source_identity: dict[str, Any],
    output_slices: list[dict[str, Any]],
    source_loss_accounting: dict[str, Any],
) -> dict[str, Any]:
    refs = _processor_refs_v11(context)
    attestations = [
        {
            "attestation_id": _safe_id(
                "official-document-pack-transformer",
                "implementation",
            ),
            "kind": "implementation",
            "artifact": refs["implementation_ref"],
        },
        {
            "attestation_id": _safe_id(
                "official-document-pack-transformer",
                "configuration",
            ),
            "kind": "configuration",
            "artifact": refs["configuration_ref"],
        },
        {
            "attestation_id": _safe_id(
                "official-document-pack-transformer",
                "dependency-lock",
            ),
            "kind": "dependency-lock",
            "artifact": refs["dependency_lock_ref"],
        },
    ]
    if source_identity["content_mode"] == "embedded-content":
        input_sha256 = source_identity["sha256"]
    elif source_identity["content_mode"] == "external-content":
        input_sha256 = source_identity["receipt"]["raw_sha256"]
    elif source_identity["content_mode"] == "metadata-only":
        input_sha256 = source_identity["identity"]["sha256"]
    elif source_identity["content_mode"] == "excluded":
        input_sha256 = source_identity["inventory_entry_identity"]["sha256"]
    else:
        raise PackBuildError(
            f"{context.skill_id}: unsupported source identity mode for "
            f"{source_identity['content_mode']!r}"
        )
    return {
        "processor_id": "official-document-pack-transformer",
        "processor_version": BUILDER_VERSION,
        "assurance_mode": "pinned",
        "input_sha256": input_sha256,
        "output_sha256": canonical_projection_sha256(
            {
                "slices": output_slices,
                "source_loss_accounting": source_loss_accounting,
            }
        ),
        "attestations": attestations,
        "deterministic": True,
    }


def _declarative_adapter(
    context: BuildContext,
    provider: dict[str, Any],
) -> ProviderBuild:
    authority_entry, authority_projection = _authority(context, provider)
    catalog = _load_schema_bound_ref(
        context,
        provider["source_ref"],
        label=f"{context.skill_id}:{provider['input_id']}:source_ref",
        schema_path=CATALOG_SCHEMA_PATH,
    )
    _reject_registration_state_blockers(
        seed_blockers=[],
        catalog_blockers=catalog["blockers"],
        label=f"{context.skill_id}:{provider['input_id']}:source_ref",
    )

    if catalog["authority_id"] != provider["authority_id"]:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: catalog authority_id "
            "must match provider authority_id"
        )
    if catalog["provider_id"] != provider["provider_id"]:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: catalog provider_id "
            "must match provider provider_id"
        )
    discovery = catalog["discovery_processor"]
    if discovery["input_sha256"] != catalog["inventory_identity"]["sha256"]:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: discovery processor "
            "input_sha256 must equal catalog inventory_identity.sha256"
        )
    if discovery["output_sha256"] != canonical_projection_sha256(
        catalog["discovered_sources"]
    ):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: discovery processor "
            "output_sha256 must equal canonical hash of discovered_sources"
        )

    discovered_sources = catalog["discovered_sources"]
    losses = catalog["losses"]
    catalog_subjects = catalog["subjects"]

    if not isinstance(discovered_sources, dict):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: discovered_sources must "
            "be a source-id map"
        )
    if not isinstance(losses, dict):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: losses must be a map"
        )
    if not isinstance(catalog_subjects, dict):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: subjects must be a map"
        )

    scope_catalog = _scope_catalog(context)
    expected_subjects = {
        item["subject_id"]: item
        for item in scope_catalog["subjects"]
        if item["evidence_class"] == "official-provider-required"
        and provider["input_id"] in item["provider_input_ids"]
    }
    if set(catalog_subjects) != set(expected_subjects):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: declarative catalog subject "
            "ids must exactly match canonical provider scope"
        )
    for subject_id, expected in expected_subjects.items():
        if catalog_subjects[subject_id]["statement"] != expected["statement"]:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{subject_id}: "
                "declarative subject statement must exactly match canonical scope statement"
            )

    source_ids = list(discovered_sources)
    if not source_ids:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: discovered_sources cannot be empty"
        )
    scope_subject_id_map = _output_id_map(
        [item["subject_id"] for item in scope_catalog["subjects"]],
        label=f"{context.skill_id}:{provider['input_id']}:scope subjects",
    )

    source_id_map = _output_id_map(
        source_ids,
        label=f"{context.skill_id}:{provider['input_id']}:source IDs",
    )
    loss_id_map = _output_id_map(
        list(losses),
        label=f"{context.skill_id}:{provider['input_id']}:loss IDs",
    )

    selector_ids: list[str] = []
    for source_id, source in discovered_sources.items():
        if not isinstance(source, dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: source {source_id!r} "
                "must be a mapping"
            )
        if source["disposition"] != "included":
            continue
        if source["content"]["content_mode"] != "metadata-only":
            selector_ids.extend(item["selector_id"] for item in source["selectors"])
    selector_id_map = _output_id_map(
        selector_ids,
        label=f"{context.skill_id}:{provider['input_id']}:selector IDs",
    )

    def _source_raw_extent_bytes(source_identity: dict[str, Any]) -> int:
        if source_identity["content_mode"] == "embedded-content":
            return source_identity["bytes"]
        if source_identity["content_mode"] == "external-content":
            return source_identity["receipt"]["raw_bytes"]
        if source_identity["content_mode"] == "metadata-only":
            return source_identity["identity"]["bytes"]
        if source_identity["content_mode"] == "excluded":
            return source_identity["inventory_entry_identity"]["bytes"]
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: unsupported source content mode"
        )

    source_identity_by_id = {
        source_id: _source_identity_from_catalog(
            context,
            provider,
            {**source, "source_id": source_id},
        )
        for source_id, source in discovered_sources.items()
    }

    included_source_ids = {
        source_id for source_id in source_ids if discovered_sources[source_id]["disposition"] == "included"
    }
    for loss_id, loss in losses.items():
        if not isinstance(loss, dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: loss {loss_id!r} "
                "must be a mapping"
            )
        if not set(loss["affected_source_ids"]).issubset(source_ids):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: loss {loss_id!r} "
                "references non-existent discovered source"
            )
        for affected_source_id in loss["affected_source_ids"]:
            if affected_source_id not in included_source_ids:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}: "
                    f"loss {loss_id!r} references non-included source "
                    f"{affected_source_id!r}"
                )
            if loss_id not in discovered_sources[affected_source_id].get(
                "loss_ids", []
            ):
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}: "
                    f"loss {loss_id!r} is not declared on source "
                    f"{affected_source_id!r}"
                )

    loss_output_by_original: dict[str, dict[str, Any]] = {}
    for loss_id, loss in losses.items():
        loss_output_by_original[loss_id] = _output_loss(
            {
                **loss,
                "loss_id": loss_id_map[loss_id],
            },
            [],
        )

    source_inventory: dict[str, dict[str, Any]] = {}
    slice_sources: dict[str, dict[str, Any]] = {}
    subject_slice_ids: dict[str, set[str]] = {
        scope_subject_id_map[subject_id]: set()
        for subject_id in expected_subjects
    }
    global_slice_ids: set[str] = set()
    limitations: list[str] = list(catalog["limitations"])
    included_selector_bearing_sources = 0

    for source_id, source in discovered_sources.items():
        if not isinstance(source, dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: source {source_id!r} "
                "must be a mapping"
            )
        disposition = source["disposition"]
        if disposition not in {"included", "excluded"}:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "disposition must be exactly included or excluded"
            )
        mapped_source_id = source_id_map[source_id]
        source_identity = source_identity_by_id[source_id]
        source_with_id = {**source, "source_id": source_id}

        if disposition == "excluded":
            source_inventory[mapped_source_id] = {
                "disposition": "excluded",
                "title": source["title"],
                "source_kind": source["source_kind"],
                "source_identity": source_identity,
                "reason_code": source["reason_code"],
                "rationale": source["rationale"],
            }
            continue

        source_subject_ids = source["subject_ids"]
        if not isinstance(source_subject_ids, list):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "source subject_ids must be a list"
            )
        if not set(source_subject_ids).issubset(expected_subjects):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "source subject_ids must resolve to canonical provider scope"
            )
        mapped_source_subject_ids = [
            scope_subject_id_map[subject_id] for subject_id in source_subject_ids
        ]
        if len(mapped_source_subject_ids) != len(set(mapped_source_subject_ids)):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "source subject_ids must not contain duplicates"
            )

        source_loss_ids = source["loss_ids"]
        if not isinstance(source_loss_ids, list):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "source loss_ids must be a list"
            )
        source_loss_seen: set[str] = set()
        source_loss_output_ids: list[str] = []
        source_loss_entries: list[dict[str, Any]] = []
        for source_loss_id in source_loss_ids:
            mapped_loss_id = loss_id_map.get(source_loss_id)
            if mapped_loss_id is None:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    f"unknown source loss_id {source_loss_id!r}"
                )
            if source_loss_id in source_loss_seen:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    f"duplicate source loss_id {source_loss_id!r}"
                )
            if source_id not in losses[source_loss_id]["affected_source_ids"]:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    f"loss {source_loss_id!r} does not include this source"
                )
            source_loss_seen.add(source_loss_id)
            source_loss_output_ids.append(mapped_loss_id)
            source_loss_entries.append(loss_output_by_original[source_loss_id])

        if source["content"]["content_mode"] == "metadata-only":
            if source["selectors"]:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    "metadata-only source must not expose selectors"
                )
            limitations.append(
                f"Source {source_id!r} is metadata-only and intentionally "
                "omits selector coverage; only source identity is retained."
            )
            source_inventory[mapped_source_id] = {
                "disposition": "included",
                "title": source["title"],
                "source_kind": source["source_kind"],
                "subject_ids": mapped_source_subject_ids,
                "loss_ids": sorted(source_loss_output_ids),
                "source_identity": source_identity,
            }
            continue

        selectors = source["selectors"]
        if not selectors:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "embedded/external included source must have selectors"
            )
        output_slices: list[dict[str, Any]] = []
        covered_losses: set[str] = set()
        selector_subject_ids: set[str] = set()
        has_nonwhole_external_selector = False
        for selector in selectors:
            selector_loss_ids = selector["loss_ids"]
            if not isinstance(selector_loss_ids, list):
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    "selector loss_ids must be a list"
                )
            selector_loss_entries: list[dict[str, Any]] = []
            selector_loss_output_ids: list[str] = []
            selector_loss_seen: set[str] = set()
            for selector_loss_id in selector_loss_ids:
                mapped_selector_loss_id = loss_id_map.get(selector_loss_id)
                if mapped_selector_loss_id is None:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                        f"unknown selector loss_id {selector_loss_id!r}"
                    )
                if selector_loss_id in selector_loss_seen:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                        f"duplicate selector loss_id {selector_loss_id!r}"
                    )
                if selector_loss_id not in source_loss_ids:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                        f"selector references loss {selector_loss_id!r} "
                        "not declared on the source"
                    )
                if source_id not in losses[selector_loss_id]["affected_source_ids"]:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                        f"selector references loss {selector_loss_id!r} "
                        "that does not include this source"
                    )
                selector_loss_seen.add(selector_loss_id)
                selector_loss_output_ids.append(mapped_selector_loss_id)
                selector_loss_entries.append(loss_output_by_original[selector_loss_id])

            mapped_selector_id = selector_id_map.get(selector["selector_id"])
            if mapped_selector_id is None:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    f"unknown selector id {selector['selector_id']!r}"
                )
            if mapped_selector_id in global_slice_ids:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    f"selector id collision after output projection {selector['selector_id']!r}"
                )
            global_slice_ids.add(mapped_selector_id)

            slice_record = _slice_from_catalog(
                context=context,
                provider=provider,
                source=source_with_id,
                identity=source_identity,
                selector={
                    **copy.deepcopy(selector),
                    "selector_id": mapped_selector_id,
                },
                raw_source_extent_bytes=_source_raw_extent_bytes(source_identity),
            )
            slice_record["slice_id"] = mapped_selector_id
            non_whole_external_selector = (
                source_identity["content_mode"] == "external-content"
                and selector["kind"] != "whole-source"
            )
            has_nonwhole_external_selector = (
                has_nonwhole_external_selector or non_whole_external_selector
            )
            if non_whole_external_selector:
                limitations.append(
                    f"Selector {selector['selector_id']!r} for source {source_id!r} "
                    "uses non-whole external projection and cannot claim exact upstream bytes."
                )
            raw_selector_subject_ids = selector["subject_ids"]
            if not isinstance(raw_selector_subject_ids, list):
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    "selector subject_ids must be a list"
                )
            if not set(raw_selector_subject_ids).issubset(expected_subjects):
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    "selector subject_ids must resolve to canonical provider scope"
                )
            mapped_selector_subject_ids = [
                scope_subject_id_map[subject_id]
                for subject_id in raw_selector_subject_ids
            ]
            if len(mapped_selector_subject_ids) != len(set(mapped_selector_subject_ids)):
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    "selector subject_ids must not contain duplicates"
                )
            if any(
                loss["disposition"] == "unresolved"
                for loss in selector_loss_entries
            ):
                selector_closure = "blocked"
            elif non_whole_external_selector:
                selector_closure = "partial"
            else:
                selector_closure = "complete"
            slice_record["loss_accounting"] = {
                "entries": sorted(
                    selector_loss_entries,
                    key=lambda item: item["loss_id"],
                ),
                "closure_status": selector_closure,
            }
            slice_record["subject_ids"] = mapped_selector_subject_ids
            output_slices.append(slice_record)
            covered_losses.update(selector_loss_output_ids)
            selector_subject_ids.update(mapped_selector_subject_ids)
            for subject_id in mapped_selector_subject_ids:
                subject_slice_ids[subject_id].add(mapped_selector_id)
        if set(selector_subject_ids) != set(mapped_source_subject_ids):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "selector subject coverage must exactly match source subject_ids"
            )

        if any(
            loss["disposition"] == "unresolved" for loss in source_loss_entries
        ):
            source_loss_status_override = "blocked"
        elif has_nonwhole_external_selector:
            source_loss_status_override = "partial"
        elif not set(source_loss_output_ids).issubset(covered_losses):
            source_loss_status_override = "partial"
        else:
            source_loss_status_override = "complete"

        source_inventory[mapped_source_id] = {
            "disposition": "included",
            "title": source["title"],
            "source_kind": source["source_kind"],
            "subject_ids": mapped_source_subject_ids,
            "loss_ids": sorted(source_loss_output_ids),
            "source_identity": source_identity,
        }

        output_slices_sorted = sorted(
            output_slices,
            key=lambda item: item["slice_id"],
        )
        source_loss_accounting = {
            "entries": sorted(
                source_loss_entries,
                key=lambda item: item["loss_id"],
            ),
            "closure_status": source_loss_status_override,
        }
        slice_sources[mapped_source_id] = {
            "source_identity": source_identity,
            "raw_source_extent_bytes": _source_raw_extent_bytes(source_identity),
            "processor": _slice_processor_v11(
                context=context,
                source_identity=source_identity,
                output_slices=output_slices_sorted,
                source_loss_accounting=source_loss_accounting,
            ),
            "slices": output_slices_sorted,
            "source_loss_accounting": source_loss_accounting,
        }
        included_selector_bearing_sources += 1

    if included_selector_bearing_sources == 0:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: at least one included "
            "selector-bearing source is required"
        )

    version_scope = copy.deepcopy(catalog["version_scope"])
    _require_registered_version_scope(
        skill_id=context.skill_id,
        input_id=provider["input_id"],
        version_scope=version_scope,
        registered_scopes=authority_projection["version_scopes"],
    )

    provider_build = ProviderBuild(
        input_id=provider["input_id"],
        authority_id=provider["authority_id"],
        provider_id=provider["provider_id"],
        version_scope=version_scope,
        retrieved_utc=_utc(catalog["version_scope"].get("retrieved_utc")),
        authority_root=catalog["authority_root"],
        authority_revision=str(catalog["authority_revision"]),
        inventory={
            "content_mode": "metadata-only",
            "locator": catalog["inventory_locator"],
            "identity": copy.deepcopy(catalog["inventory_identity"]),
        },
        source_inventory=source_inventory,
        slice_sources=slice_sources,
        upstream_universe_complete=catalog["upstream_universe_complete"],
        subject_slice_ids={
            subject_id: tuple(sorted(subject_slice_ids[subject_id]))
            for subject_id in sorted(subject_slice_ids)
        },
        limitations=tuple(sorted(set(limitations))),
        blockers=tuple(
            [
                *copy.deepcopy(catalog["blockers"]),
                *_blocking_loss_blockers(
                    [
                        {
                            **loss,
                            "loss_id": loss_id_map[loss_id],
                        }
                        for loss_id, loss in losses.items()
                    ]
                ),
            ]
        ),
    )
    _validate_provider_projection(context, provider_build)
    return provider_build


def _qe_adapter(
    context: BuildContext,
    provider: dict[str, Any],
) -> ProviderBuild:
    from urllib.parse import urlparse

    authority_entry, authority_projection = _authority(context, provider)
    catalog_path, catalog_raw = _read_catalog_ref(
        context,
        provider["source_ref"],
        label=f"{context.skill_id}:{provider['input_id']}:source_ref",
    )
    try:
        manifest = strict_json.loads_object(
            catalog_raw,
            f"{context.skill_id} QE compact catalog",
            max_bytes=MAX_CATALOG_BYTES,
        )
    except strict_json.StrictJSONError as exc:
        raise PackBuildError(str(exc)) from None
    _validate_object_schema(
        manifest,
        _schema_validator(context.root, QE_INPUT_SCHEMA_PATH),
        label=f"{context.skill_id} QE compact catalog",
    )
    _attest_replayed_catalog(
        context,
        provider,
        catalog_path=catalog_path,
        catalog_raw=catalog_raw,
        catalog=manifest,
    )
    if not isinstance(manifest, dict):
        raise PackBuildError("QE compact catalog must be an object")
    expected_root = {
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
    if (
        set(manifest) != expected_root
        or manifest["schema_version"] != "1.0"
        or manifest["contract_name"] != "qe-source-pack-input"
        or manifest["catalog_type"] != "qe-input-manifest-metadata-v1"
        or manifest["skill_id"] != context.skill_id
    ):
        raise PackBuildError(
            "QE compact catalog root does not match the exact v1 adapter"
        )
    if (
        not isinstance(manifest["manuals"], list)
        or not isinstance(manifest["source_root"], str)
        or not isinstance(manifest["retrieved_utc"], str)
        or not isinstance(manifest["limitations"], list)
    ):
        raise PackBuildError("QE compact catalog has invalid top-level typing")
    if not all(isinstance(item, str) for item in manifest["limitations"]):
        raise PackBuildError(
            "QE compact catalog limitations must be a list of strings"
        )
    source_root = manifest["source_root"]
    expected_source_root = "https://www.quantum-espresso.org/Doc/"
    if source_root != expected_source_root:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: QE source_root must be "
            f"{expected_source_root!r}"
        )

    def _validate_qe_url(url: str) -> None:
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc == ""
            or parsed.hostname != "www.quantum-espresso.org"
            or parsed.username is not None
            or parsed.password is not None
            or (parsed.port not in (None, 443))
            or parsed.query
            or parsed.fragment
            or not url.startswith(expected_source_root)
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: "
                f"manual URL {url!r} violates strict QE docs constraints"
            )

    scope_catalog = _scope_catalog(context)
    expected_subjects = {
        item["subject_id"]
        for item in scope_catalog["subjects"]
        if item["evidence_class"] == "official-provider-required"
        and provider["input_id"] in item["provider_input_ids"]
    }
    if not expected_subjects:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: QE provider scope "
            "must define at least one required subject"
        )
    subject_slice_ids: dict[str, set[str]] = {
        subject_id: set() for subject_id in expected_subjects
    }

    source_payloads: dict[str, dict[str, Any]] = {}
    selector_payloads: list[dict[str, Any]] = []
    loss_payloads: dict[str, dict[str, Any]] = {}
    total_sections = 0
    included_manuals = 0
    has_excluded_ld1 = False
    seen_manual_names: set[str] = set()

    for manual in manifest["manuals"]:
        expected_manual = {
            "name",
            "version",
            "url",
            "retrieved_utc",
            "raw_sha256",
            "raw_bytes",
            "sections",
        }
        if (
            not isinstance(manual, dict)
            or set(manual) != expected_manual
            or not isinstance(manual["name"], str)
            or not isinstance(manual["version"], str)
            or not isinstance(manual["url"], str)
            or not isinstance(manual["retrieved_utc"], str)
            or not isinstance(manual["raw_sha256"], str)
            or not isinstance(manual["raw_bytes"], int)
            or not isinstance(manual["sections"], list)
        ):
            raise PackBuildError("QE input manual does not match the exact adapter")

        manual_name = manual["name"]
        if manual_name in seen_manual_names:
            raise PackBuildError(
                f"QE catalog has duplicate manual {manual_name!r}"
            )
        seen_manual_names.add(manual_name)
        _validate_qe_url(manual["url"])
        source_id = _safe_id("qe", manual_name)

        if manual["version"] == "7.5":
            included_manuals += 1
            section_ids: set[str] = set()
            loss_ids: list[str] = []
            for ordinal, section in enumerate(manual["sections"], start=0):
                expected_section = {
                    "order",
                    "section_id",
                    "title",
                    "selected_sha256",
                    "selected_bytes",
                    "payload_hash_basis",
                    "wrapper_sha256",
                    "wrapper_bytes",
                }
                if (
                    not isinstance(section, dict)
                    or set(section) != expected_section
                    or not isinstance(section["order"], int)
                    or not isinstance(section["section_id"], str)
                    or not isinstance(section["title"], str)
                    or not isinstance(section["selected_sha256"], str)
                    or not isinstance(section["selected_bytes"], int)
                    or not isinstance(section["payload_hash_basis"], str)
                    or not isinstance(section["wrapper_sha256"], str)
                    or not isinstance(section["wrapper_bytes"], int)
                ):
                    raise PackBuildError(
                        f"QE manual {manual_name!r} section does not match the "
                        "exact adapter"
                    )
                if section["payload_hash_basis"] != (
                    "utf-8 bytes of the fenced text payload after removing "
                    "the single wrapper separator newline"
                ):
                    raise PackBuildError(
                        f"QE {manual_name!r} section {section['section_id']!r} "
                        "uses unsupported payload hash basis"
                    )
                if section["order"] != ordinal:
                    raise PackBuildError(
                        f"QE {manual_name!r} section {section['section_id']!r} "
                        f"must keep order {ordinal}, found {section['order']}"
                    )
                if section["selected_bytes"] <= 0:
                    raise PackBuildError(
                        f"QE {manual_name!r} section {section['section_id']!r} "
                        "requires selected_bytes > 0"
                    )
                section_id = section["section_id"]
                if section_id in section_ids:
                    raise PackBuildError(
                        f"QE manual {manual_name!r} has duplicate section_id "
                        f"{section_id!r}"
                    )
                section_ids.add(section_id)
                loss_id = _safe_id(
                    "qe",
                    source_id,
                    section_id,
                    "metadata-only",
                )
                if loss_id in loss_payloads:
                    raise PackBuildError(
                        f"QE manual {manual_name!r} has duplicate section loss id "
                        f"{loss_id!r}"
                    )
                loss_payloads[loss_id] = {
                    "description": (
                        f"Section {section_id!r} in {manual_name!r} is "
                        "projected from catalog metadata only; byte "
                        "offset is unknown."
                    ),
                }
                loss_ids.append(loss_id)
                selector_id = _safe_id(
                    "qe",
                    source_id,
                    section_id,
                    "selector",
                )
                selector_payloads.append(
                    {
                        "source_id": source_id,
                        "identity": {
                            "selected_sha256": section["selected_sha256"],
                            "selected_bytes": section["selected_bytes"],
                        },
                        "selector": {
                            "selector_id": selector_id,
                            "layer": "derived-artifact",
                            "kind": "source-symbol",
                            "value": section_id,
                            "subject_ids": sorted(expected_subjects),
                            "loss_ids": [loss_id],
                            "selected_identity": {
                                "sha256": section["selected_sha256"],
                                "bytes": section["selected_bytes"],
                            },
                            "selected_sha256": section["selected_sha256"],
                            "selected_bytes": section["selected_bytes"],
                        },
                    }
                )
                total_sections += 1
            source_payloads[source_id] = {
                "title": manual_name,
                "source_kind": "manual-page",
                "disposition": "included",
                "raw_bytes": manual["raw_bytes"],
                "source_identity": {
                    "content_mode": "external-content",
                    "locator": manual["url"],
                    "receipt": {
                        "retrieval_method": "https-get",
                        "retrieved_utc": _utc(manual["retrieved_utc"]),
                        "raw_sha256": manual["raw_sha256"],
                        "raw_bytes": manual["raw_bytes"],
                    },
                },
                "loss_ids": loss_ids,
            }
            continue

        if manual_name == "INPUT_LD1" and manual["version"] == "7.4":
            has_excluded_ld1 = True
            excluded_identity_payload = canonical_json_bytes(manual)
            source_payloads[source_id] = {
                "title": manual_name,
                "source_kind": "reference-page",
                "disposition": "excluded",
                "source_identity": {
                    "content_mode": "excluded",
                    "locator": manual["url"],
                    "inventory_entry_identity": {
                        "sha256": sha256_bytes(excluded_identity_payload),
                        "bytes": len(excluded_identity_payload),
                    },
                },
                "reason_code": "obsolete",
                "rationale": (
                    "INPUT_LD1 is explicitly version 7.4 and excluded from "
                    "the QE 7.5-only projection."
                ),
            }
            continue

        raise PackBuildError(
            f"QE catalog has unsupported manual {manual_name!r} "
            f"at version {manual['version']!r}"
        )

    if included_manuals != 35 or total_sections != 1159:
        raise PackBuildError(
            "QE adapter requires exactly 35 QE 7.5 manuals and 1159 sections "
            f"(found {included_manuals} and {total_sections})"
        )
    if not has_excluded_ld1:
        raise PackBuildError(
            "QE adapter requires INPUT_LD1 7.4 explicit exclusion gate"
        )

    source_ids = sorted(source_payloads)
    source_id_map = _output_id_map(
        source_ids,
        label=f"{context.skill_id}:{provider['input_id']}:source IDs",
    )
    selector_id_map = _output_id_map(
        [item["selector"]["selector_id"] for item in selector_payloads],
        label=f"{context.skill_id}:{provider['input_id']}:selector IDs",
    )
    loss_id_map = _output_id_map(
        list(loss_payloads),
        label=f"{context.skill_id}:{provider['input_id']}:loss IDs",
    )

    section_loss_output: dict[str, dict[str, Any]] = {}
    for original_loss_id, loss_payload in loss_payloads.items():
        mapped_loss_id = loss_id_map[original_loss_id]
        section_loss_output[original_loss_id] = {
            "loss_id": mapped_loss_id,
            "category": "metadata",
            "severity": "material",
            "disposition": "external-only",
            "description": loss_payload["description"],
        }

    source_inventory: dict[str, dict[str, Any]] = {}
    slice_sources: dict[str, dict[str, Any]] = {}
    included_selector_sources = 0
    global_slice_ids: set[str] = set()

    for source_id in source_ids:
        source_payload = source_payloads[source_id]
        mapped_source_id = source_id_map[source_id]
        source_identity = copy.deepcopy(source_payload["source_identity"])

        if source_payload["disposition"] == "excluded":
            source_inventory[mapped_source_id] = {
                "disposition": "excluded",
                "title": source_payload["title"],
                "source_kind": source_payload["source_kind"],
                "source_identity": source_identity,
                "reason_code": source_payload["reason_code"],
                "rationale": source_payload["rationale"],
            }
            continue

        selectors = [
            item for item in selector_payloads if item["source_id"] == source_id
        ]
        if not selectors:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "included manual requires at least one selector"
            )

        source_slice_loss_ids: set[str] = set()
        output_slices: list[dict[str, Any]] = []
        for selector_record in selectors:
            selector = copy.deepcopy(selector_record["selector"])
            selector_identity = selector_record["identity"]
            if selector_identity["selected_bytes"] <= 0:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    "selector selected_bytes must be strictly positive"
                )
            selector_entries: list[dict[str, Any]] = []
            selector_loss_ids: list[str] = []
            for original_loss_id in selector["loss_ids"]:
                loss_entry = section_loss_output.get(original_loss_id)
                if loss_entry is None:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                        f"unknown section loss id {original_loss_id!r}"
                    )
                selector_loss_ids.append(loss_entry["loss_id"])
                selector_entries.append(loss_entry)
                source_slice_loss_ids.add(loss_entry["loss_id"])
            selector["loss_ids"] = sorted(selector_loss_ids)
            slice_record = _slice_from_catalog(
                context=context,
                provider=provider,
                source={
                    "source_id": source_id,
                    "disposition": "included",
                    "source_identity": source_identity,
                },
                identity=source_identity,
                selector=selector,
                raw_source_extent_bytes=source_payload["raw_bytes"],
            )
            mapped_selector_id = selector_id_map[selector_record["selector"]["selector_id"]]
            if mapped_selector_id in global_slice_ids:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}: "
                    f"selector id collision after output projection {mapped_selector_id!r}"
                )
            global_slice_ids.add(mapped_selector_id)
            slice_record["content"] = {
                "content_mode": "metadata-only",
                "locator": source_payload["source_identity"]["locator"],
                "identity": {
                    "sha256": selector_identity["selected_sha256"],
                    "bytes": selector_identity["selected_bytes"],
                },
                "hash_basis": "metadata-identity-bytes",
            }
            slice_record["raw_byte_range"] = {
                "start_byte": 0,
                "byte_count": source_payload["raw_bytes"],
            }
            output_slices.append(
                {
                    **slice_record,
                    "slice_id": mapped_selector_id,
                    "loss_accounting": {
                        "closure_status": "partial",
                        "entries": sorted(
                            selector_entries,
                            key=lambda item: item["loss_id"],
                        ),
                    },
                }
            )
            for subject_id in selector["subject_ids"]:
                if subject_id not in subject_slice_ids:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                        f"unknown scope subject {subject_id!r}"
                    )
                subject_slice_ids[subject_id].add(mapped_selector_id)

        source_loss_ids = []
        source_loss_output: list[dict[str, Any]] = []
        for original_loss_id in source_payload["loss_ids"]:
            loss_entry = section_loss_output[original_loss_id]
            mapped_loss_id = loss_entry["loss_id"]
            if mapped_loss_id not in source_slice_loss_ids:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    "source loss ids are not represented by its slice loss-accounting"
                )
            source_loss_ids.append(mapped_loss_id)
            source_loss_output.append(loss_entry)
        if set(source_loss_ids) != source_slice_loss_ids:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "source and slice loss-accounting are not closed"
            )
        output_slices_sorted = sorted(
            output_slices,
            key=lambda item: item["slice_id"],
        )
        source_loss_accounting = {
            "closure_status": "partial",
            "entries": sorted(source_loss_output, key=lambda item: item["loss_id"]),
        }
        slice_sources[mapped_source_id] = {
            "source_identity": source_identity,
            "raw_source_extent_bytes": source_payload["raw_bytes"],
            "source_loss_accounting": source_loss_accounting,
            "processor": _slice_processor_v11(
                context=context,
                source_identity=source_identity,
                output_slices=output_slices_sorted,
                source_loss_accounting=copy.deepcopy(source_loss_accounting),
            ),
            "slices": output_slices_sorted,
        }
        source_inventory[mapped_source_id] = {
            "disposition": "included",
            "title": source_payload["title"],
            "source_kind": source_payload["source_kind"],
            "subject_ids": sorted(expected_subjects),
            "loss_ids": sorted(source_loss_ids),
            "source_identity": source_identity,
        }
        included_selector_sources += 1

    if included_selector_sources == 0:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: at least one included "
            "selector-bearing manual is required"
        )
    if set(source_inventory) != set(source_id_map.values()):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: source inventory projection "
            "must include all discovered manual IDs"
        )

    version_scope = {
        "kind": "exact",
        "value": "7.5",
        "retrieved_utc": None,
        "snapshot_identity": None,
    }
    _require_registered_version_scope(
        skill_id=context.skill_id,
        input_id=provider["input_id"],
        version_scope=version_scope,
        registered_scopes=authority_projection["version_scopes"],
    )

    if authority_entry["provider_id"] != provider["provider_id"]:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: authority provider "
            "does not match QE adapter provider tuple"
        )
    if authority_entry.get("lifecycle") != "active":
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: authority must be active"
        )

    provider_build = ProviderBuild(
        input_id=provider["input_id"],
        authority_id=provider["authority_id"],
        provider_id=provider["provider_id"],
        version_scope=version_scope,
        retrieved_utc=_utc(manifest["retrieved_utc"]),
        authority_root=manifest["source_root"],
        authority_revision="7.5",
        inventory={
            "content_mode": "metadata-only",
            "locator": manifest["source_root"],
            "identity": {
                "sha256": sha256_bytes(catalog_raw),
                "bytes": len(catalog_raw),
            },
        },
        source_inventory=source_inventory,
        slice_sources=copy.deepcopy(slice_sources),
        upstream_universe_complete=False,
        subject_slice_ids={
            key: tuple(sorted(value)) for key, value in subject_slice_ids.items()
        },
        limitations=tuple(
            sorted(
                set(
                    manifest["limitations"]
                    + [
                        "Section projections are metadata-only; no validated upstream byte offsets were "
                        "available in the compact catalog.",
                        "INPUT_LD1 (7.4) is excluded by explicit scope gate.",
                        "Technical projection is metadata-only and does not include "
                        "root body hash contents.",
                    ]
                )
            )
        ),
        blockers=tuple(
            _blocking_loss_blockers(
                [
                    {
                        **loss,
                        "loss_id": section_loss_output[loss_id]["loss_id"],
                    }
                    for loss_id, loss in section_loss_output.items()
                ]
            )
        ),
    )
    _validate_provider_projection(context, provider_build)
    return provider_build


def _vasp_adapter(
    context: BuildContext,
    provider: dict[str, Any],
) -> ProviderBuild:
    authority_entry, authority_projection = _authority(context, provider)
    catalog_path, catalog_raw = _read_catalog_ref(
        context,
        provider["source_ref"],
        label=f"{context.skill_id}:{provider['input_id']}:source_ref",
    )
    try:
        manifest = strict_json.loads_object(
            catalog_raw,
            f"{context.skill_id} VASP compact catalog",
            max_bytes=MAX_CATALOG_BYTES,
        )
    except strict_json.StrictJSONError as exc:
        raise PackBuildError(str(exc)) from None
    _validate_object_schema(
        manifest,
        _schema_validator(context.root, VASP_INPUT_SCHEMA_PATH),
        label=f"{context.skill_id} VASP compact catalog",
    )
    _attest_replayed_catalog(
        context,
        provider,
        catalog_path=catalog_path,
        catalog_raw=catalog_raw,
        catalog=manifest,
    )
    expected_root = {
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
    if (
        set(manifest) != expected_root
        or manifest["schema_version"] != "1.0"
        or manifest["contract_name"] != "vasp-source-pack-input"
        or manifest["catalog_type"] != "vasp-wiki-page-metadata-v1"
        or manifest["skill_id"] != context.skill_id
        or len(manifest["pages"]) != 81
    ):
        raise PackBuildError(
            "VASP compact catalog is not the exact 81-page adapter input"
        )
    retrieved = _utc(manifest["retrieved_utc"])
    source_inventory: dict[str, dict[str, Any]] = {}
    slice_sources: dict[str, dict[str, Any]] = {}
    subject_slices: dict[str, set[str]] = {}
    expected_provider_subjects = {
        item["subject_id"]
        for item in _scope_catalog(context)["subjects"]
        if item["evidence_class"] == "official-provider-required"
        and provider["input_id"] in item["provider_input_ids"]
    }
    if not expected_provider_subjects:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: VASP provider scope "
            "must define at least one required official-provider subject"
        )
    for subject_id in expected_provider_subjects:
        subject_slices[subject_id] = set()
    pageids: set[int] = set()
    revids: set[int] = set()
    version_scope_projection: list[dict[str, Any]] = []
    for page in sorted(manifest["pages"], key=lambda item: item["pageid"]):
        expected_page = {
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
        if not isinstance(page, dict) or set(page) != expected_page:
            raise PackBuildError("VASP page does not match the exact adapter")
        pageid = page["pageid"]
        revid = page["revid"]
        if pageid in pageids:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: duplicate pageid "
                f"{pageid!r}"
            )
        if revid in revids:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: duplicate revid "
                f"{revid!r}"
            )
        pageids.add(pageid)
        revids.add(revid)
        representations = (
            (
                "api-json",
                page["raw_json_sha256"],
                page["raw_json_bytes"],
            ),
            (
                "wikitext",
                page["wikitext_sha256"],
                page["wikitext_bytes"],
            ),
        )
        for representation, digest, extent in representations:
            source_id = _safe_id("vasp-page", pageid, representation)
            if extent <= 0:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}: source "
                    f"{source_id}: extent must be positive"
                )
            source_kind = (
                "api-record"
                if representation == "api-json"
            else "reference-page"
            )
            locator = (
                page["api_request_url"]
                if representation == "api-json"
                else page["url"]
            )
            source_receipt = {
                "retrieval_method": "official-api",
                "retrieved_utc": retrieved,
                "raw_sha256": digest,
                "raw_bytes": extent,
            }
            source_identity = {
                "content_mode": "external-content",
                "locator": locator,
                "receipt": source_receipt,
            }
            loss_id = _safe_id(source_id, "page-link-asset-closure")
            selector_subject_ids: list[str] = []
            tag_subject = _safe_id("vasp-safe-tag", page["title"])
            if representation == "wikitext" and tag_subject in expected_provider_subjects:
                selector_subject_ids = [tag_subject]
                subject_slices[tag_subject].add(_safe_id(source_id, "whole"))
            selector = {
                "selector_id": _safe_id(source_id, "whole"),
                "layer": "raw-source",
                "kind": "whole-source",
                "value": "*",
                "subject_ids": selector_subject_ids,
                "selected_identity": {
                    "sha256": digest,
                    "bytes": extent,
                },
            }
            mapped_loss = _output_loss(
                {
                    "loss_id": loss_id,
                    "materiality": "material",
                    "disposition": "external-only",
                    "stage": "storage",
                    "description": (
                        "Linked Wiki pages, rendered media, and third-party "
                        "assets are outside this exact page identity."
                    ),
                },
                [selector["selector_id"]],
            )
            output_slice = _slice_from_catalog(
                context=context,
                provider=provider,
                source={"source_id": source_id, "source_identity": source_identity},
                identity=source_identity,
                selector=selector,
                raw_source_extent_bytes=extent,
            )
            slice_record = {
                **output_slice,
                "loss_accounting": {
                    "closure_status": "complete",
                    "entries": [mapped_loss],
                },
            }
            source_loss_accounting = {
                "closure_status": "complete",
                "entries": [mapped_loss],
            }
            slice_sources[source_id] = {
                "source_identity": source_identity,
                "raw_source_extent_bytes": extent,
                "source_loss_accounting": source_loss_accounting,
                "processor": _slice_processor_v11(
                    context=context,
                    source_identity=source_identity,
                    output_slices=[slice_record],
                    source_loss_accounting=copy.deepcopy(source_loss_accounting),
                ),
                "slices": [slice_record],
            }
            source_inventory[source_id] = {
                "disposition": "included",
                "title": page["title"],
                "source_kind": source_kind,
                "subject_ids": selector_subject_ids,
                "loss_ids": [loss_id],
                "source_identity": source_identity,
            }
            version_scope_projection.append(
                {
                    "source_id": source_id,
                    "pageid": pageid,
                    "revid": revid,
                    "representation": representation,
                    "locator": locator,
                    "sha256": digest,
                    "bytes": extent,
                }
            )
    if len(source_inventory) != 162 or len(slice_sources) != 162:
        raise PackBuildError("VASP adapter must emit 81 API + 81 wikitext identities")
    if (
        set(subject_slices) != expected_provider_subjects
        or any(not values for values in subject_slices.values())
    ):
        raise PackBuildError(
            "VASP adapter safe-tag mappings do not exactly equal canonical "
            "provider scope subjects"
        )
    version_projection = canonical_json_bytes(
        {
            item["source_id"]: {
                "pageid": item["pageid"],
                "revid": item["revid"],
                "representation": item["representation"],
                "locator": item["locator"],
                "sha256": item["sha256"],
                "bytes": item["bytes"],
            }
            for item in sorted(
                version_scope_projection, key=lambda item: item["source_id"]
            )
        }
    )
    version_scope = {
        "kind": "latest-at-retrieval",
        "value": None,
        "retrieved_utc": retrieved,
        "snapshot_identity": {
            "sha256": sha256_bytes(version_projection),
            "bytes": len(version_projection),
        },
    }
    _require_registered_version_scope(
        skill_id=context.skill_id,
        input_id=provider["input_id"],
        version_scope=version_scope,
        registered_scopes=authority_projection["version_scopes"],
    )
    if authority_entry["provider_id"] != provider["provider_id"]:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: authority provider "
            "does not match VASP adapter provider tuple"
        )
    if authority_entry.get("lifecycle") != "active":
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: authority must be active"
        )
    manifest_digest = provider["source_ref"]["sha256"]
    inventory_locator = provider["source_ref"]["path"]
    if not isinstance(inventory_locator, str):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: source_ref path must be "
            "a string"
        )
    if not inventory_locator.startswith("https://"):
        inventory_locator = manifest["official_root"]
    if not inventory_locator.startswith("https://"):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: inventory locator "
            "must be HTTPS"
        )
    provider_build = ProviderBuild(
        input_id=provider["input_id"],
        authority_id=provider["authority_id"],
        provider_id=provider["provider_id"],
        version_scope=version_scope,
        retrieved_utc=retrieved,
        authority_root=manifest["official_root"],
        authority_revision=manifest_digest,
        inventory={
            "content_mode": "metadata-only",
            "locator": inventory_locator,
            "identity": {
                "sha256": manifest_digest,
                "bytes": len(catalog_raw),
            },
        },
        upstream_universe_complete=False,
        source_inventory=source_inventory,
        slice_sources=copy.deepcopy(slice_sources),
        subject_slice_ids={
            key: tuple(sorted(value)) for key, value in subject_slices.items()
        },
        limitations=(
            "The 81-page curated Wiki set is a bounded subset, not full site closure.",
            "API JSON and extracted wikitext are separate exact identities; rendered Markdown is not substituted for either.",
            "Portal downloads, link closure, images, templates, and third-party assets remain external.",
            "Source-specific closure is implemented with exact whole-source selectors and complete loss-accounting.",
        ),
        blockers=(),
    )
    _validate_provider_projection(context, provider_build)
    return provider_build


ADAPTERS.update(
    {
        "declarative-catalog-v1": _declarative_adapter,
        "qe-input-manifest-v1": _qe_adapter,
        "vasp-wiki-manifest-v1": _vasp_adapter,
    }
)


def _validate_provider_projection(
    context: BuildContext,
    provider: ProviderBuild,
) -> None:
    """Validate fail-closed 1.1 source projection closure."""

    source_inventory = provider.source_inventory
    if not isinstance(source_inventory, dict) or not source_inventory:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: source inventory must be "
            "a non-empty mapping"
        )
    slice_sources = provider.slice_sources
    if not isinstance(slice_sources, dict) or not slice_sources:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: slice-source map must be "
            "a non-empty mapping"
        )
    subject_slice_ids = provider.subject_slice_ids
    if not isinstance(subject_slice_ids, dict):
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: subject_slice_ids must be "
            "a mapping"
        )

    included_ids: set[str] = set()
    source_disposition: dict[str, str] = {}
    included_source_loss_ids: dict[str, set[str]] = {}
    has_metadata_only_included_source = False
    for source_id, source_entry in source_inventory.items():
        if not isinstance(source_id, str) or not source_id:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: source inventory key "
                "must be a non-empty source_id"
            )
        if not isinstance(source_entry, dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "source inventory entry is not a mapping"
            )
        disposition = source_entry.get("disposition")
        if disposition not in {"included", "excluded"}:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "source disposition must be exactly included or excluded"
            )
        source_disposition[source_id] = disposition
        if not isinstance(source_entry.get("source_identity"), dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "source_identity must be a mapping"
            )
        if disposition == "included":
            included_ids.add(source_id)
            if source_entry["source_identity"].get("content_mode") == "metadata-only":
                has_metadata_only_included_source = True
            subject_ids = source_entry.get("subject_ids")
            if not isinstance(subject_ids, list):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "included source entries require subject_ids list"
                )
            for subject_id in subject_ids:
                if not isinstance(subject_id, str) or not subject_id:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "subject_ids must be non-empty strings"
                    )
            loss_ids = source_entry.get("loss_ids")
            if not isinstance(loss_ids, list):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "included source entries require loss_ids list"
                )
            source_loss_ids: set[str] = set()
            for loss_id in loss_ids:
                if not isinstance(loss_id, str) or not loss_id:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "loss_id must be a non-empty string"
                    )
                if loss_id in source_loss_ids:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "loss_ids contain duplicates"
                    )
                source_loss_ids.add(loss_id)
            included_source_loss_ids[source_id] = source_loss_ids
            if len(loss_ids) != len(source_loss_ids):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "loss_ids contain duplicates"
                )

    if not included_ids:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: source inventory "
            "must include at least one source"
        )
    for source_id in slice_sources:
        if not isinstance(source_id, str) or not source_id:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "slice-source key must be a non-empty source_id"
            )
    slice_source_ids = set(slice_sources)
    if not slice_source_ids.issubset(included_ids):
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: slice-source keys must "
            "be subset of included source IDs"
        )
    missing_included_ids = included_ids.difference(slice_source_ids)
    if missing_included_ids:
        if not has_metadata_only_included_source:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: slice-source "
                "projection omits one or more included sources"
            )
        if not any(
            isinstance(item, str) and item.strip()
            for item in provider.limitations
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: omitted "
                "metadata-only source slices require explicit limitation text"
            )
        for source_id in missing_included_ids:
            source_entry = source_inventory[source_id]
            source_identity = source_entry["source_identity"]
            if source_identity.get("content_mode") != "metadata-only":
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "slice-source projection cannot omit embedded/external sources"
                )

    all_slice_ids: set[str] = set()
    reconstructed_subject_slice_ids: dict[str, set[str]] = {
        subject_id: set()
        for subject_id in subject_slice_ids
        if isinstance(subject_id, str) and subject_id
    }
    for source_id, source_record in slice_sources.items():
        source_inventory_entry = source_inventory.get(source_id)
        if not isinstance(source_record, dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "slice-source entry is not a mapping"
            )
        if not isinstance(source_inventory_entry, dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "slice-source entry is not in source inventory"
            )
        if source_disposition.get(source_id) != "included":
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "slice-source keys must point to included sources"
            )
        if source_record.get("source_identity") != source_inventory_entry.get(
            "source_identity"
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "slice source identity does not equal corpus source_identity"
            )

        source_losses_expected = source_inventory_entry.get("loss_ids")
        if not isinstance(source_losses_expected, list):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "included source entries require list loss_ids"
            )
        source_loss_ids = included_source_loss_ids.get(source_id)
        if source_loss_ids is None:
            source_loss_ids = set()
            for loss_id in source_losses_expected:
                if not isinstance(loss_id, str) or not loss_id:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "loss_ids must contain non-empty strings"
                    )
                if loss_id in source_loss_ids:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "loss_ids contain duplicates"
                    )
                source_loss_ids.add(loss_id)
            if len(source_losses_expected) != len(source_loss_ids):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "loss_ids contain duplicates"
                )

        source_loss_accounting = source_record.get("source_loss_accounting")
        if not isinstance(source_loss_accounting, dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "source_loss_accounting must be a mapping"
            )
        if (
            not isinstance(source_loss_accounting.get("closure_status"), str)
            or not isinstance(source_loss_accounting.get("entries"), list)
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "source_loss_accounting must include closure_status and entries"
            )
        closure_status = source_loss_accounting["closure_status"]
        if closure_status not in {"complete", "partial", "blocked"}:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "invalid source-loss closure status"
            )
        source_accounting_entries: dict[str, dict[str, Any]] = {}
        for accounting_entry in source_loss_accounting["entries"]:
            if not isinstance(accounting_entry, dict):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "source loss-accounting entry is not a mapping"
                )
            loss_id = accounting_entry.get("loss_id")
            if not isinstance(loss_id, str) or not loss_id:
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "source loss-accounting entry loss_id must be a non-empty string"
                )
            if loss_id in source_accounting_entries:
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    f"duplicated source loss_id {loss_id!r}"
                )
            source_accounting_entries[loss_id] = accounting_entry
        if source_loss_ids != set(source_accounting_entries):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "source loss_ids must exactly match source_loss_accounting IDs"
            )

        slices = source_record.get("slices")
        if not isinstance(slices, list) or not slices:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "slices must be a non-empty list"
            )
        slice_ids: list[str] = []
        for item in slices:
            if not isinstance(item, dict):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "slice entry is not a mapping"
                )
            slice_id = item.get("slice_id")
            if not isinstance(slice_id, str) or not slice_id:
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "slice_id must be a non-empty string"
                )
            slice_ids.append(slice_id)
        if len(slice_ids) != len(set(slice_ids)):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "slice IDs are not unique for this source"
            )
        overlapping = all_slice_ids.intersection(slice_ids)
        if overlapping:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                f"slice IDs are not globally unique: "
                f"{', '.join(sorted(overlapping))}"
            )
        source_slice_loss_ids: set[str] = set()
        source_slice_subject_ids: set[str] = set()
        for item in slices:
            slice_id = item.get("slice_id")
            if not isinstance(slice_id, str) or not slice_id:
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "slice_id must be a non-empty string"
                )
            slice_loss_accounting = item.get("loss_accounting")
            if not isinstance(slice_loss_accounting, dict):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "slice loss_accounting must be a mapping"
                )
            if (
                not isinstance(slice_loss_accounting.get("closure_status"), str)
                or not isinstance(slice_loss_accounting.get("entries"), list)
            ):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "slice loss_accounting must include closure_status and entries"
                )
            if slice_loss_accounting["closure_status"] not in {
                "complete",
                "partial",
                "blocked",
            }:
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    f"{slice_id}: invalid slice loss-accounting closure status"
                )
            slice_loss_entry_ids: set[str] = set()
            for loss_entry in slice_loss_accounting["entries"]:
                if not isinstance(loss_entry, dict):
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "slice loss-accounting entry is not a mapping"
                    )
                loss_id = loss_entry.get("loss_id")
                if not isinstance(loss_id, str) or not loss_id:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "slice loss-accounting entry loss_id must be a non-empty "
                        "string"
                    )
                if loss_id in slice_loss_entry_ids:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        f"duplicated slice loss_id {loss_id!r}"
                    )
                accounting_entry = source_accounting_entries.get(loss_id)
                if accounting_entry is None:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        f"slice loss_id {loss_id!r} is not in source loss-accounting "
                        "entries"
                    )
                if loss_entry != accounting_entry:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "slice loss entry does not exactly match source loss-accounting "
                        "entry"
                    )
                slice_loss_entry_ids.add(loss_id)
            source_slice_loss_ids.update(slice_loss_entry_ids)
            slice_subject_ids = item.get("subject_ids")
            if not isinstance(slice_subject_ids, list):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "slice subject_ids must be a list"
                )
            slice_subject_set: set[str] = set()
            for subject_id in slice_subject_ids:
                if not isinstance(subject_id, str) or not subject_id:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "slice subject_ids must be non-empty strings"
                    )
                if subject_id in slice_subject_set:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "slice subject_ids must not contain duplicates"
                    )
                slice_subject_set.add(subject_id)
                if subject_id not in reconstructed_subject_slice_ids:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        "slice subject_id is not declared in subject_slice_ids"
                    )
                reconstructed_subject_slice_ids[subject_id].add(slice_id)
            source_slice_subject_ids.update(slice_subject_set)
        if (
            source_inventory_entry["source_identity"].get("content_mode")
            == "metadata-only"
        ):
            if source_slice_subject_ids:
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "metadata-only sources cannot include slice subject_ids"
                )
        else:
            if source_slice_subject_ids != set(source_inventory_entry["subject_ids"]):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "included selector-bearing source subject_ids must equal the "
                    "union of its slice subject_ids"
                )
        if closure_status == "complete" and source_slice_loss_ids != source_loss_ids:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "complete source loss closure is not exactly represented by "
                "slice losses"
            )
        all_slice_ids.update(slice_ids)

    for subject_id, subject_slices in subject_slice_ids.items():
        if not isinstance(subject_id, str) or not subject_id:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: subject_slice_ids key "
                "must be a non-empty subject ID"
            )
        if not isinstance(subject_slices, (list, tuple)):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{subject_id}: "
                "subject slices must be a list or tuple"
            )
        subject_slice_ids_set: set[str] = set()
        for slice_id in subject_slices:
            if not isinstance(slice_id, str) or not slice_id:
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{subject_id}: "
                    "subject slice ids must all be non-empty strings"
                )
            if slice_id in subject_slice_ids_set:
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{subject_id}: "
                    "subject slice mapping has duplicate slice ids"
                )
            subject_slice_ids_set.add(slice_id)
        if len(subject_slices) != len(subject_slice_ids_set):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{subject_id}: "
                "subject slice mapping has duplicate slice ids"
            )
        if not subject_slice_ids_set.issubset(all_slice_ids):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{subject_id}: "
                "subject slice mapping has dangling slice ids"
            )
        if subject_slice_ids_set != reconstructed_subject_slice_ids.get(subject_id, set()):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{subject_id}: "
                "subject_slice_ids must exactly equal reconstructed slice-based "
                "mapping"
            )

    if set(reconstructed_subject_slice_ids) != set(subject_slice_ids):
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: reconstructed subject-to-slice "
            "mapping keys are not identical to declared subject_slice_ids"
        )


def _provider_records_v11(
    context: BuildContext,
    provider_input: dict[str, Any],
    provider: ProviderBuild,
    *,
    producer: dict[str, Any],
    seed_limitations: tuple[str, ...],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build version 1.1 corpus and slice manifests from validated provider projection."""

    adapter_projection = {
        "declarative-catalog-v1": (
            "manual-inventory",
            "official-document-source-catalog-1.1",
            "unverified",
        ),
        "qe-input-manifest-v1": (
            "official-index",
            "qe-source-pack-input-1.0",
            "pinned",
        ),
        "vasp-wiki-manifest-v1": (
            "official-api",
            "vasp-source-pack-input-1.0",
            "pinned",
        ),
    }
    adapter_id = provider_input["adapter_id"]
    discovery = adapter_projection.get(adapter_id)
    if discovery is None:
        raise PackBuildError(
            f"{context.skill_id}:{provider_input['input_id']}: unsupported adapter "
            f"{adapter_id!r} for official-document-records v1.1"
        )
    discovery_method, inventory_format, assurance_mode = discovery

    source_inventory = copy.deepcopy(provider.source_inventory)
    if not isinstance(source_inventory, dict) or not source_inventory:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: source_inventory must be a "
            "non-empty mapping"
        )
    included_ids = [
        source_id
        for source_id, item in source_inventory.items()
        if item.get("disposition") == "included"
    ]
    if not included_ids:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: source partition must "
            "contain at least one included source"
        )
    for source_id in source_inventory:
        if not isinstance(source_id, str) or not source_id:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: source_inventory keys "
                "must be non-empty source IDs"
            )
        if not isinstance(source_inventory[source_id], dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "source_inventory entry must be a mapping"
            )
        if source_inventory[source_id].get("disposition") not in {
            "included",
            "excluded",
        }:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: "
                "source disposition must be included or excluded"
            )

    slice_sources = copy.deepcopy(provider.slice_sources)
    if not isinstance(slice_sources, dict) or not slice_sources:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: slice_sources must be a "
            "non-empty mapping"
        )
    slice_source_ids = set(slice_sources)
    if not slice_source_ids.issubset(set(included_ids)):
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: slice source ids must be a "
            "subset of included source ids"
        )
    if not slice_source_ids:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: slice partition must be non-empty"
        )
    for source_id in slice_source_ids:
        if not isinstance(source_id, str) or not source_id:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: slice source key must "
                "be a non-empty source ID"
            )

    catalog_inventory = provider.inventory
    if not isinstance(catalog_inventory, dict):
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: provider inventory must be a "
            "mapping"
        )
    inventory_content_mode = catalog_inventory.get("content_mode")
    if inventory_content_mode == "embedded-content":
        expected_keys = {"content_mode", "locator", "sha256", "bytes"}
        if set(catalog_inventory.keys()) != expected_keys:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: embedded-content "
                "inventory must only include content_mode, locator, sha256, and bytes"
            )
        if not isinstance(catalog_inventory.get("sha256"), str) or re.fullmatch(
            r"[0-9a-f]{64}", catalog_inventory["sha256"]
        ) is None:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: embedded-content "
                "inventory sha256 must be a 64-char hex string"
            )
        if (
            not isinstance(catalog_inventory.get("bytes"), int)
            or catalog_inventory["bytes"] <= 0
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: embedded-content "
                "inventory bytes must be a positive integer"
            )
        input_sha256 = catalog_inventory["sha256"]
    elif inventory_content_mode == "external-content":
        expected_keys = {"content_mode", "locator", "receipt"}
        if set(catalog_inventory.keys()) != expected_keys:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: external-content "
                "inventory must only include content_mode, locator, and receipt"
            )
        receipt = catalog_inventory.get("receipt")
        if not isinstance(receipt, dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: external-content "
                "inventory receipt must be a mapping"
            )
        if set(receipt.keys()) != {
            "retrieval_method",
            "retrieved_utc",
            "raw_sha256",
            "raw_bytes",
        }:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: external-content "
                "inventory receipt must only include retrieval_method, "
                "retrieved_utc, raw_sha256, and raw_bytes"
            )
        if (
            not isinstance(receipt.get("raw_sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", receipt["raw_sha256"]) is None
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: external-content "
                "inventory receipt raw_sha256 must be a 64-char hex string"
            )
        if (
            not isinstance(receipt.get("raw_bytes"), int)
            or receipt["raw_bytes"] <= 0
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: external-content "
                "inventory receipt raw_bytes must be a positive integer"
            )
        input_sha256 = receipt["raw_sha256"]
    elif inventory_content_mode == "metadata-only":
        expected_keys = {"content_mode", "locator", "identity"}
        if set(catalog_inventory.keys()) != expected_keys:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: metadata-only inventory "
                "must only include content_mode, locator, and identity"
            )
        identity = catalog_inventory.get("identity")
        if not isinstance(identity, dict):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: metadata-only inventory "
                "identity must be a mapping"
            )
        if set(identity.keys()) != {"sha256", "bytes"}:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: metadata-only inventory "
                "identity must only include sha256 and bytes"
            )
        if (
            not isinstance(identity.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", identity["sha256"]) is None
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: metadata-only inventory "
                "identity sha256 must be a 64-char hex string"
            )
        if not isinstance(identity.get("bytes"), int) or identity["bytes"] <= 0:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: metadata-only inventory "
                "identity bytes must be a positive integer"
            )
        input_sha256 = identity["sha256"]
    else:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: unsupported inventory "
            f"content_mode {inventory_content_mode!r}"
        )

    corpus_id = _safe_id(context.skill_id, provider.input_id, "official-corpus")
    source_projection_sha256 = canonical_projection_sha256(source_inventory)
    corpus_discovery = {
        "method": discovery_method,
        "upstream_universe_complete": provider.upstream_universe_complete,
        "inventory_scope": (
            "upstream-universe"
            if provider.upstream_universe_complete
            else "bounded-authority-subset"
        ),
        "authority_root": provider.authority_root,
        "authority_revision": provider.authority_revision,
        "inventory_format": inventory_format,
        "inventory": copy.deepcopy(catalog_inventory),
        "processor": _processor_v11(
            context=context,
            processor_id="official-document-pack-enumerator",
            processor_version=BUILDER_VERSION,
            assurance_mode=assurance_mode,
            input_sha256=input_sha256,
            output_sha256=source_projection_sha256,
        ),
    }

    corpus_blockers = [
        {**blocker, "dimension": "inventory"}
        for blocker in _output_blockers(
            provider.blockers,
            label=f"{context.skill_id}:{provider.input_id}:corpus",
            dimension="corpus",
        )
    ]
    slice_blockers = [
        {**blocker, "dimension": "loss-closure"}
        for blocker in _output_blockers(
            provider.blockers,
            label=f"{context.skill_id}:{provider.input_id}:slices",
            dimension="slices",
        )
    ]
    corpus_status = "blocked" if corpus_blockers else "partial"
    slice_status = "blocked" if slice_blockers else "partial"

    corpus_limitations = sorted(
        set(
            [
                *seed_limitations,
                *provider.limitations,
                "Inventory and source identities are projected as technical artifacts only.",
            ]
        )
    )
    slice_limitations = sorted(
        set(
            [
                *seed_limitations,
                *provider.limitations,
                "Slice projections are validated against the provider source partition.",
            ]
        )
    )

    corpus = {
        "schema_version": "1.1",
        "contract_name": "official-corpus-manifest",
        "corpus_id": corpus_id,
        "authority_id": provider.authority_id,
        "provider_id": provider.provider_id,
        "version_scope": copy.deepcopy(provider.version_scope),
        "status": corpus_status,
        "discovery": corpus_discovery,
        "source_inventory": source_inventory,
        "blockers": corpus_blockers,
        "limitations": corpus_limitations,
        "producer": copy.deepcopy(producer),
    }

    corpus_sha = sha256_bytes(canonical_json_bytes(corpus))
    slice_id = _safe_id(context.skill_id, provider.input_id, "official-slices")
    slices = {
        "schema_version": "1.1",
        "contract_name": "document-slice-manifest",
        "slice_manifest_id": slice_id,
        "corpus_ref": {
            "corpus_id": corpus_id,
            "sha256": corpus_sha,
        },
        "status": slice_status,
        "sources": slice_sources,
        "blockers": slice_blockers,
        "limitations": slice_limitations,
        "producer": copy.deepcopy(producer),
    }
    return corpus, slices


def _build_one(context: BuildContext) -> dict[str, bytes]:
    """Return one complete byte-stable pack without mutating the repository."""

    _validate_dependency_lock(context)
    scope_catalog = _scope_catalog(context)
    scope_subject_id_map = _output_id_map(
        [item["subject_id"] for item in scope_catalog["subjects"]],
        label=f"{context.skill_id}:scope subjects",
    )
    providers: list[tuple[dict[str, Any], ProviderBuild]] = []
    for provider_input in context.seed["providers"]:
        adapter = ADAPTERS.get(provider_input["adapter_id"])
        if adapter is None:
            raise PackBuildError(
                f"{context.skill_id}:{provider_input['input_id']}: adapter is unavailable"
            )
        built = adapter(context, provider_input)
        _validate_provider_projection(context, built)
        authority, _projection = _authority(context, provider_input)
        _require_registered_version_scope(
            skill_id=context.skill_id,
            input_id=provider_input["input_id"],
            version_scope=built.version_scope,
            registered_scopes=authority["version_policy"][
                "registered_scopes"
            ],
        )
        expected_subjects = {
            item["subject_id"]
            for item in scope_catalog["subjects"]
            if item["evidence_class"] == "official-provider-required"
            and provider_input["input_id"] in item["provider_input_ids"]
        }
        expected_mapped_subjects = {
            scope_subject_id_map[item] for item in expected_subjects
        }
        if set(built.subject_slice_ids) != expected_mapped_subjects:
            raise PackBuildError(
                f"{context.skill_id}:{provider_input['input_id']}: adapter "
                "subject mappings do not exactly equal canonical provider scope"
            )
        providers.append((provider_input, built))

    generated_utc = max(
        (item.retrieved_utc for _, item in providers),
        default=DEFAULT_GENERATED_UTC,
    )
    producer = {
        "skill_id": context.skill_id,
        "skill_version": "1.0",
        "tool_id": "official-document-pack-builder",
        "tool_version": BUILDER_VERSION,
        "generated_utc": generated_utc,
    }
    seed_blockers = [
        {
            "code": _safe_id("seed", index, "blocked"),
            "description": description,
        }
        for index, description in enumerate(context.seed["blockers"])
    ]

    records: dict[str, bytes] = {}
    corpus_records: list[tuple[dict[str, Any], str, str]] = []
    slice_records: list[tuple[dict[str, Any], str, str]] = []
    provider_by_input: dict[str, ProviderBuild] = {}
    slice_manifest_id_by_input: dict[str, str] = {}

    for provider_input, provider in providers:
        corpus, slices = _provider_records_v11(
            context,
            provider_input,
            provider,
            producer=producer,
            seed_limitations=tuple(context.seed["limitations"]),
        )
        corpus_name = f"corpus-{provider.input_id}.json"
        corpus_raw = canonical_json_bytes(corpus)
        corpus_sha = sha256_bytes(corpus_raw)
        records[corpus_name] = corpus_raw
        corpus_records.append((corpus, corpus_name, corpus_sha))
        slice_name = f"slices-{provider.input_id}.json"
        slice_raw = canonical_json_bytes(slices)
        slice_sha = sha256_bytes(slice_raw)
        records[slice_name] = slice_raw
        slice_records.append((slices, slice_name, slice_sha))
        provider_by_input[provider_input["input_id"]] = provider
        slice_manifest_id_by_input[provider_input["input_id"]] = slices[
            "slice_manifest_id"
        ]

    try:
        tree = skill_registry.source_tree_digest(context.skill_root)
    except ValueError as exc:
        raise PackBuildError(
            f"{context.skill_id}: cannot bind complete source tree: {exc}"
        ) from None
    entry = _skill_entry(context.snapshot, context.skill_id)
    if tree.sha256 != entry["source_tree_sha256"]:
        raise PackBuildError(
            f"{context.skill_id}: source_tree_sha256 is stale after seed/catalog "
            "changes; refresh registry/skill-registry.yaml before building "
            f"(recorded {entry['source_tree_sha256']}, actual {tree.sha256})"
        )
    source_refs = [
        {
            "path": f"{entry['path']}/{item.path}",
            "sha256": item.sha256,
        }
        for item in tree.files
    ]
    source_ref_pairs = {
        (item["path"], item["sha256"]) for item in source_refs
    }

    scope_subjects: list[dict[str, Any]] = []
    scope_meta: dict[str, dict[str, Any]] = {}
    for item in scope_catalog["subjects"]:
        origins = [
            {
                "path": origin["path"],
                "sha256": origin["sha256"],
                "selector": {
                    "kind": "whole-file",
                    "value": "*",
                },
            }
            for origin in item["origin_refs"]
        ]
        if any(
            (origin["path"], origin["sha256"]) not in source_ref_pairs
            for origin in origins
        ):
            raise PackBuildError(
                f"{context.skill_id}: scope subject {item['subject_id']!r} "
                "has an origin outside the complete source-tree inventory"
            )
        subject_id = scope_subject_id_map[item["subject_id"]]
        subject = {
            "subject_id": subject_id,
            "subject_kind": item["subject_kind"],
            "evidence_class": item["evidence_class"],
            "origin_refs": origins,
            "statement": item["statement"],
        }
        scope_subjects.append(subject)
        scope_meta[subject_id] = item
    scope_subjects.sort(key=lambda item: item["subject_id"])

    scope_blockers = list(seed_blockers)
    if context.seed["status_ceiling"] == "blocked" and not scope_blockers:
        scope_blockers.append(
            {
                "code": "seed-status-blocked",
                "description": "The strict seed caps this generated pack at blocked.",
            }
        )
    scope_status = "blocked" if scope_blockers else "partial"
    scope_limitations = sorted(
        set(
            [
                *context.seed["limitations"],
                "Semantic claim-set completeness remains explicitly unproven; exact full-file enumeration is not treated as claim closure.",
                "The deterministic scope extractor is centrally pinned but this exact run is not platform attested.",
            ]
        )
    )
    scope_id = _safe_id(context.skill_id, "official-document-scope")
    extractor = _processor(
        context,
        kind="extractor",
        input_sha256=tree.sha256,
        output_sha256=canonical_projection_sha256(scope_subjects),
    )
    scope_record = {
        "schema_version": "1.0",
        "contract_name": "skill-document-scope-inventory",
        "inventory_id": scope_id,
        "skill_id": context.skill_id,
        "skill_registry_binding": {
            "registry_path": "registry/skill-registry.yaml",
            "registry_sha256": context.snapshot.registry_sha256[
                SKILL_REGISTRY_NAME
            ],
            "skill_path": entry["path"],
            "lifecycle": entry["lifecycle"],
            "source_tree_hash_domain": skill_registry.TREE_HASH_DOMAIN_NAME,
            "source_tree_sha256": tree.sha256,
        },
        "status": scope_status,
        "skill_source_refs": source_refs,
        "enumeration": {
            "method": "deterministic-extractor",
            "scope_complete": False,
            "extractor": extractor,
            "reviewed_by": "official-document-pack-builder",
            "reviewed_utc": generated_utc,
        },
        "subjects": scope_subjects,
        "blockers": scope_blockers,
        "limitations": scope_limitations,
        "producer": producer,
    }
    scope_raw = canonical_json_bytes(scope_record)
    scope_sha = sha256_bytes(scope_raw)
    records["scope-inventory.json"] = scope_raw

    mappings: dict[str, dict[str, Any]] = {}
    mapping_statuses: set[str] = set()
    for subject in scope_subjects:
        meta = scope_meta[subject["subject_id"]]
        if subject["evidence_class"] == "official-provider-required":
            refs: list[dict[str, str]] = []
            for input_id in meta["provider_input_ids"]:
                provider = provider_by_input[input_id]
                for slice_id in provider.subject_slice_ids.get(
                    subject["subject_id"], ()
                ):
                    refs.append(
                        {
                            "slice_manifest_id": slice_manifest_id_by_input[
                                input_id
                            ],
                            "slice_id": slice_id,
                        }
                    )
            refs = sorted(
                {json.dumps(item, sort_keys=True): item for item in refs}.values(),
                key=lambda item: (
                    item["slice_manifest_id"],
                    item["slice_id"],
                ),
            )
            if meta["expected_disposition"] == "blocked":
                mapping_status = "blocked"
                mapping_rationale = (
                    "The canonical scope marks this official subject as blocked."
                )
                mapping_limitations = [
                    "Official-provider mapping is intentionally blocked for this scope subject."
                ]
                refs = []
            else:
                if not refs:
                    raise PackBuildError(
                        f"{context.skill_id}: official scope subject "
                        f"{subject['subject_id']!r} has no exact provider slice"
                    )
                mapping_status = "partial"
                mapping_rationale = (
                    "Exact official slices are available for this canonical "
                    "scope subject."
                )
                mapping_limitations = [
                    "Slice references are exact and derived from the provider manifest."
                ]
            mappings[subject["subject_id"]] = {
                "mapping_status": mapping_status,
                "disposition": "blocked"
                if mapping_status == "blocked"
                else "partial",
                "slice_refs": refs,
                "rationale": mapping_rationale,
                "limitations": mapping_limitations,
            }
        else:
            mappings[subject["subject_id"]] = {
                "mapping_status": "complete",
                "disposition": meta["expected_disposition"]
                if meta["expected_disposition"] in {"not-applicable", "excluded"}
                else "not-applicable",
                "slice_refs": [],
                "rationale": (
                    "This subject is established by local Skill scope and is "
                    "outside official-provider coverage."
                ),
                "limitations": [],
            }
            mapping_status = "complete"
        mapping_statuses.add(mapping_status)

    coverage_status: dict[str, str] = {
        "corpus": "partial",
        "slices": "partial",
        "scope": scope_status,
        "mappings": "partial",
    }
    if any(record["status"] == "blocked" for record, _, _ in corpus_records):
        coverage_status["corpus"] = "blocked"
    if any(record["status"] == "blocked" for record, _, _ in slice_records):
        coverage_status["slices"] = "blocked"
    if "blocked" in mapping_statuses:
        coverage_status["mappings"] = "blocked"
    elif "partial" in mapping_statuses:
        coverage_status["mappings"] = "partial"
    else:
        coverage_status["mappings"] = "complete"
    coverage_status["overall"] = (
        "blocked"
        if "blocked" in coverage_status.values()
        else (
            "complete"
            if all(
                status == "complete"
                for status in coverage_status.values()
            )
            else "partial"
        )
    )

    coverage_blockers = []
    if coverage_status["corpus"] == "blocked":
        coverage_blockers.append(
            {
                "code": "corpus-blocked",
                "description": (
                    "Corpus projection is blocked by seeded provider blockers."
                ),
                "dimension": "corpus",
            }
        )
    if coverage_status["slices"] == "blocked":
        coverage_blockers.append(
            {
                "code": "slices-blocked",
                "description": (
                    "Slice projection is blocked by seeded provider blockers."
                ),
                "dimension": "slices",
            }
        )
    if coverage_status["scope"] == "blocked":
        coverage_blockers.append(
            {
                "code": "scope-blocked",
                "description": "Scope is blocked by seed ceiling or blockers.",
                "dimension": "scope",
            }
        )
    if coverage_status["mappings"] == "blocked":
        coverage_blockers.append(
            {
                "code": "mappings-blocked",
                "description": (
                    "At least one canonical scope subject mapping is blocked."
                ),
                "dimension": "mappings",
            }
        )

    coverage = {
        "schema_version": "1.1",
        "contract_name": "skill-document-coverage",
        "coverage_id": _safe_id(
            context.skill_id, "official-document-coverage"
        ),
        "skill_id": context.skill_id,
        "status": coverage_status,
        "corpus_refs": [
            {
                "corpus_id": record["corpus_id"],
                "sha256": digest,
            }
            for record, _, digest in corpus_records
        ],
        "slice_manifest_refs": [
            {
                "slice_manifest_id": record["slice_manifest_id"],
                "sha256": digest,
            }
            for record, _, digest in slice_records
        ],
        "scope_inventory_ref": {
            "inventory_id": scope_id,
            "sha256": scope_sha,
        },
        "mappings": mappings,
        "blockers": coverage_blockers,
        "limitations": sorted(
            set(
                [
                    *context.seed["limitations"],
                    "Technical official-document coverage metadata is partial unless all dimensions are complete.",
                ]
            )
        ),
        "producer": producer,
    }
    records["coverage.json"] = canonical_json_bytes(coverage)

    bundle = {
        "bundle_type": "official-document-coverage",
        "schema_version": "1.0",
        "skill_id": context.skill_id,
        "records": {
            "corpora": sorted(name for _, name, _ in corpus_records),
            "slice_manifests": sorted(name for _, name, _ in slice_records),
            "scope_inventory": "scope-inventory.json",
            "coverage": "coverage.json",
        },
    }
    records["bundle.json"] = canonical_json_bytes(bundle)
    return records


def _expected_output_names(context: BuildContext) -> set[str]:
    names = {
        "bundle.json",
        "scope-inventory.json",
        "coverage.json",
    }
    for provider in context.seed["providers"]:
        input_id = provider["input_id"]
        names.update(
            {
                f"corpus-{input_id}.json",
                f"slices-{input_id}.json",
            }
        )
    return names


def _validate_output_closure(
    context: BuildContext,
    outputs: dict[str, bytes],
) -> None:
    expected = _expected_output_names(context)
    if set(outputs) != expected:
        raise PackBuildError(
            f"{context.skill_id}: builder output set differs from the fixed "
            "pack contract"
        )

    bundle_bytes = outputs.get("bundle.json")
    bundle = strict_json.loads_object(
        bundle_bytes,
        f"{context.skill_id}:bundle.json",
        max_bytes=MAX_CATALOG_BYTES,
    )
    if not isinstance(bundle, dict):
        raise PackBuildError(f"{context.skill_id}: bundle.json must be an object")
    if bundle.get("bundle_type") != "official-document-coverage":
        raise PackBuildError(
            f"{context.skill_id}: bundle.json bundle_type must be "
            "'official-document-coverage'"
        )
    if bundle.get("schema_version") != "1.0":
        raise PackBuildError(
            f"{context.skill_id}: bundle.json schema_version must be '1.0'"
        )
    if bundle.get("skill_id") != context.skill_id:
        raise PackBuildError(
            f"{context.skill_id}: bundle.json skill_id mismatch"
        )

    records = bundle.get("records")
    if not isinstance(records, dict):
        raise PackBuildError(f"{context.skill_id}: bundle.json records must be an object")
    required_record_keys = {
        "corpora",
        "slice_manifests",
        "scope_inventory",
        "coverage",
    }
    if set(records) != required_record_keys:
        raise PackBuildError(
            f"{context.skill_id}: bundle.json records keys must be exactly "
            f"{sorted(required_record_keys)!r}"
        )

    corpora = records["corpora"]
    slice_manifests = records["slice_manifests"]
    scope_inventory = records["scope_inventory"]
    coverage = records["coverage"]

    if not isinstance(corpora, list) or not isinstance(slice_manifests, list):
        raise PackBuildError(
            f"{context.skill_id}: bundle.json records corpora/slice_manifests "
            "must be lists"
        )
    if not isinstance(scope_inventory, str) or not isinstance(coverage, str):
        raise PackBuildError(
            f"{context.skill_id}: bundle.json records scope_inventory and coverage "
            "must be strings"
        )

    provider_input_ids = tuple(sorted(item["input_id"] for item in context.seed["providers"]))
    expected_corpora = [f"corpus-{input_id}.json" for input_id in provider_input_ids]
    expected_slices = [f"slices-{input_id}.json" for input_id in provider_input_ids]

    if len(set(corpora)) != len(corpora):
        raise PackBuildError(
            f"{context.skill_id}: bundle.json records contains duplicate corpus entries"
        )
    if len(set(slice_manifests)) != len(slice_manifests):
        raise PackBuildError(
            f"{context.skill_id}: bundle.json records contains duplicate slice entries"
        )

    referenced = (
        {scope_inventory, coverage}
        | set(corpora)
        | set(slice_manifests)
    )
    if referenced != (expected - {"bundle.json"}):
        raise PackBuildError(
            f"{context.skill_id}: bundle.json records referenced files do not "
            "match generated outputs"
        )
    if corpora != expected_corpora or slice_manifests != expected_slices:
        raise PackBuildError(
            f"{context.skill_id}: bundle.json records corpus/slice files are not the "
            "exact ordered provider set"
        )
    if scope_inventory != "scope-inventory.json" or coverage != "coverage.json":
        raise PackBuildError(
            f"{context.skill_id}: bundle.json records scope/coverage filenames are "
            "incorrect"
        )

    for name, raw in outputs.items():
        if (
            PurePosixPath(name).name != name
            or not re.fullmatch(
                r"(?:bundle|scope-inventory|coverage|"
                r"(?:corpus|slices)-[a-z0-9]+(?:-[a-z0-9]+)*)\.json",
                name,
            )
            or not isinstance(raw, bytes)
        ):
            raise PackBuildError(
                f"{context.skill_id}: unsafe generated output name or bytes {name!r}"
            )
        try:
            strict_json.loads_object(
                raw,
                f"{context.skill_id}:{name}",
                max_bytes=MAX_CATALOG_BYTES,
            )
        except strict_json.StrictJSONError as exc:
            raise PackBuildError(str(exc)) from None


def _write_staged_files(stage: Path, outputs: dict[str, bytes]) -> None:
    for name in sorted(outputs):
        target = stage / name
        descriptor = os.open(
            target,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o644,
        )
        try:
            view = memoryview(outputs[name])
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("short write")
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        metadata = target.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_nlink != 1
        ):
            raise PackBuildError(f"unsafe staged pack file {name!r}")
    directory_descriptor = os.open(stage, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def _semantic_validate_outputs(
    context: BuildContext,
    outputs: dict[str, bytes],
) -> None:
    with tempfile.TemporaryDirectory(
        prefix=f"vibe-pack-validate-{context.skill_id}-"
    ) as directory:
        stage = Path(directory)
        _write_staged_files(stage, outputs)
        provider_ids = [
            item["input_id"] for item in context.seed["providers"]
        ]
        result = validate_official_document_coverage.validate_files(
            corpus_paths=[
                stage / f"corpus-{input_id}.json"
                for input_id in provider_ids
            ],
            slice_paths=[
                stage / f"slices-{input_id}.json"
                for input_id in provider_ids
            ],
            scope_inventory_path=stage / "scope-inventory.json",
            coverage_path=stage / "coverage.json",
            source_root=context.root,
        )
    if result.findings:
        excerpt = "; ".join(
            f"{item.code} {item.location}: {item.message}"
            for item in result.findings[:8]
        )
        raise PackBuildError(
            f"{context.skill_id}: generated pack failed semantic validation: "
            f"{excerpt}"
        )
    if result.assurance_status not in {"partial", "blocked"}:
        raise PackBuildError(
            f"{context.skill_id}: seed illegally produced assurance "
            f"{result.assurance_status!r}; seed ceiling forbids complete"
        )


def _pack_inventory(
    pack_root: Path,
    *,
    label: str,
) -> dict[str, bytes] | None:
    if not pack_root.exists() and not pack_root.is_symlink():
        return None
    root_stat = pack_root.lstat()
    if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
        raise PackBuildError(f"{label}: pack root must be a real directory")
    result: dict[str, bytes] = {}
    seen_inodes: set[tuple[int, int]] = set()
    for item in sorted(pack_root.iterdir(), key=lambda path: path.name):
        metadata = item.lstat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_nlink != 1
        ):
            raise PackBuildError(
                f"{label}: pack contains a symlink, hard link, directory, or "
                f"special entry: {item.name}"
            )
        inode = (metadata.st_dev, metadata.st_ino)
        if inode in seen_inodes:
            raise PackBuildError(f"{label}: pack contains aliased file identities")
        seen_inodes.add(inode)
        result[item.name] = _read_regular_bytes(
            item,
            label=f"{label}:{item.name}",
        )
    return result


def _changed_paths(
    context: BuildContext,
    outputs: dict[str, bytes],
    current: dict[str, bytes] | None,
) -> list[str]:
    pack_root = context.skill_root.joinpath(*PACK_RELATIVE_PATH.parts)
    names = sorted(set(outputs).union(current or {}))
    return [
        (pack_root / name).relative_to(context.root).as_posix()
        for name in names
        if current is None or current.get(name) != outputs.get(name)
    ]


def _atomic_replace_pack(
    context: BuildContext,
    outputs: dict[str, bytes],
) -> None:
    _atomic_replace_packs(((context, outputs),))


@dataclass
class _PackSwap:
    context: BuildContext
    outputs: dict[str, bytes]
    references: Path
    pack_root: Path
    stage: Path
    backup: Path | None = None
    installed: bool = False


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _new_empty_swap_path(references: Path, *, prefix: str) -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=references))
    path.rmdir()
    return path


def _rollback_pack_swaps(states: Sequence[_PackSwap]) -> None:
    """Restore every old pack in reverse command order."""

    rollback_errors: list[str] = []
    for state in reversed(states):
        tombstone: Path | None = None
        preserve_tombstone = False
        try:
            if state.installed:
                try:
                    current = _pack_inventory(
                        state.pack_root,
                        label=f"{state.context.skill_id}:rollback-new",
                    )
                    preserve_tombstone = current != state.outputs
                except PackBuildError:
                    # Rename the generated namespace as one opaque directory;
                    # never traverse or delete an unrecognized concurrent value.
                    preserve_tombstone = True
                tombstone = _new_empty_swap_path(
                    state.references,
                    prefix=(
                        ".source-pack-conflict-"
                        if preserve_tombstone
                        else ".source-pack-rollback-"
                    ),
                )
                os.replace(state.pack_root, tombstone)
                state.installed = False
            if state.backup is not None:
                if state.pack_root.exists() or state.pack_root.is_symlink():
                    raise PackBuildError(
                        f"{state.context.skill_id}: rollback target is occupied"
                    )
                os.replace(state.backup, state.pack_root)
                state.backup = None
            _fsync_directory(state.references)
            if tombstone is not None and not preserve_tombstone:
                shutil.rmtree(tombstone)
                tombstone = None
                _fsync_directory(state.references)
        except BaseException as exc:
            rollback_errors.append(
                f"{state.context.skill_id}:{exc.__class__.__name__}:{exc}"
            )
            # Preserve a backup or rollback tombstone on any recovery failure.
    if rollback_errors:
        raise PackBuildError(
            "official-document pack rollback was incomplete: "
            + "; ".join(rollback_errors)
        )


def _atomic_replace_packs(
    replacements: Sequence[tuple[BuildContext, dict[str, bytes]]],
) -> None:
    """Atomically swap every changed pack as one command-wide transaction."""

    states: list[_PackSwap] = []
    committed = False
    try:
        # Stage and fsync every output before any canonical pack is renamed.
        for context, outputs in replacements:
            references = context.skill_root / "references"
            references_stat = references.lstat()
            if (
                not stat.S_ISDIR(references_stat.st_mode)
                or stat.S_ISLNK(references_stat.st_mode)
            ):
                raise PackBuildError(
                    f"{context.skill_id}: references parent is not a safe real "
                    "directory"
                )
            pack_root = context.skill_root.joinpath(*PACK_RELATIVE_PATH.parts)
            stage = Path(
                tempfile.mkdtemp(
                    prefix=".source-pack-stage-",
                    dir=references,
                )
            )
            state = _PackSwap(
                context=context,
                outputs=outputs,
                references=references,
                pack_root=pack_root,
                stage=stage,
            )
            states.append(state)
            _write_staged_files(stage, outputs)

        # Retain every backup until every replacement and parent fsync passes.
        for state in states:
            if state.pack_root.exists() or state.pack_root.is_symlink():
                _pack_inventory(
                    state.pack_root,
                    label=state.context.skill_id,
                )
                state.backup = _new_empty_swap_path(
                    state.references,
                    prefix=".source-pack-backup-",
                )
                os.replace(state.pack_root, state.backup)
            os.replace(state.stage, state.pack_root)
            state.installed = True
            _fsync_directory(state.references)

        # Re-read every canonical pack after all swaps and durability barriers,
        # while every old backup is still recoverable.
        for state in states:
            observed = _pack_inventory(
                state.pack_root,
                label=f"{state.context.skill_id}:precommit-recheck",
            )
            if observed != state.outputs:
                raise PackBuildError(
                    f"{state.context.skill_id}: installed pack changed before "
                    "the command-wide commit point"
                )

        # The command-wide commit point is after all parent fsync operations.
        committed = True
    except BaseException as original:
        try:
            _rollback_pack_swaps(states)
        except BaseException as rollback:
            raise PackBuildError(
                f"pack transaction failed ({original}); rollback also failed "
                f"({rollback})"
            ) from rollback
        if isinstance(original, PackBuildError):
            raise
        raise PackBuildError(
            f"official-document pack transaction failed safely: "
            f"{original.__class__.__name__}: {original}"
        ) from None
    finally:
        for state in states:
            if state.stage.exists():
                shutil.rmtree(state.stage)
    if committed:
        cleanup_errors: list[str] = []
        for state in states:
            if state.backup is not None:
                try:
                    shutil.rmtree(state.backup)
                    state.backup = None
                    _fsync_directory(state.references)
                except BaseException as exc:
                    cleanup_errors.append(
                        f"{state.context.skill_id}:{exc.__class__.__name__}:{exc}"
                    )
        if cleanup_errors:
            raise PackBuildError(
                "packs committed but obsolete backup cleanup failed: "
                + "; ".join(cleanup_errors)
            )


def _build_selected_with_snapshot(
    root: Path,
    snapshot: RegistrySnapshot,
    skill_ids: Sequence[str],
    *,
    check: bool,
) -> BuildSummary:
    selected = tuple(sorted(set(skill_ids)))
    if not selected:
        raise PackBuildError("no seeded Skills selected")
    prepared: list[
        tuple[BuildContext, dict[str, bytes], dict[str, bytes] | None, list[str]]
    ] = []
    for skill_id in selected:
        context = load_seed(root, snapshot, skill_id)
        outputs = _build_one(context)
        _validate_output_closure(context, outputs)
        _semantic_validate_outputs(context, outputs)
        pack_root = context.skill_root.joinpath(*PACK_RELATIVE_PATH.parts)
        current = _pack_inventory(pack_root, label=skill_id)
        changes = _changed_paths(context, outputs, current)
        prepared.append((context, outputs, current, changes))
    all_changes = [
        path
        for _, _, _, changes in prepared
        for path in changes
    ]
    if check and all_changes:
        raise PackBuildError(
            "generated official-document packs are stale or have noncanonical "
            "closure: " + ", ".join(all_changes)
        )
    if not check:
        replacements = [
            (context, outputs)
            for context, outputs, _, changes in prepared
            if changes
        ]
        if replacements:
            _atomic_replace_packs(replacements)
    for context, outputs, _, _ in prepared:
        observed = _pack_inventory(
            context.skill_root.joinpath(*PACK_RELATIVE_PATH.parts),
            label=f"{context.skill_id}:final-recheck",
        )
        if observed != outputs:
            raise PackBuildError(
                f"{context.skill_id}: generated pack changed during the final "
                "transaction/check boundary"
            )
    return BuildSummary(selected, tuple(all_changes), check)


def build_selected_packs(
    root: Path,
    skill_ids: Sequence[str],
    *,
    check: bool,
) -> BuildSummary:
    """Build or byte-check selected seeded packs from one nine-registry snapshot."""

    selected_root = root.resolve()
    snapshot = load_registry_snapshot(selected_root, validate_sources=True)
    return _build_selected_with_snapshot(
        selected_root,
        snapshot,
        skill_ids,
        check=check,
    )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--all",
        action="store_true",
        help="build every Skill that has the canonical seed",
    )
    selection.add_argument(
        "--skill",
        action="append",
        default=[],
        metavar="SKILL_ID",
        help="build one Skill; repeat for more than one",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare exact bytes without writing",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        selected_root = args.root.resolve()
        snapshot = load_registry_snapshot(
            selected_root,
            validate_sources=True,
        )
        selected = (
            seeded_skill_ids(selected_root, snapshot)
            if args.all
            else tuple(args.skill)
        )
        summary = _build_selected_with_snapshot(
            selected_root,
            snapshot,
            selected,
            check=args.check,
        )
    except (PackBuildError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    verb = "checked" if summary.checked else "built"
    print(
        f"PASS: {verb} {len(summary.selected_skills)} deterministic "
        f"official-document pack(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
