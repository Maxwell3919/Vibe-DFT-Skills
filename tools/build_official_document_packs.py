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
    "contracts", "official-document-source-catalog.schema.json"
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
    inventory_format: str
    inventory_locator: str
    inventory_sha256: str
    upstream_universe_complete: bool
    included_sources: tuple[dict[str, Any], ...]
    reviewed_exclusions: tuple[dict[str, Any], ...]
    source_slices: tuple[dict[str, Any], ...]
    subject_slice_ids: dict[str, tuple[str, ...]]
    license: dict[str, Any]
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
        "contracts/official-corpus-manifest.schema.json",
        "contracts/document-slice-manifest.schema.json",
        "contracts/official-source-license-review.schema.json",
        "contracts/skill-document-scope-inventory.schema.json",
        "contracts/skill-document-coverage.schema.json",
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
    if "content_ref" in source:
        raw = _validate_content_ref(
            context,
            source["content_ref"],
            label=f"{context.skill_id}:{provider['input_id']}:{source['source_id']}",
        )
        digest = sha256_bytes(raw)
        return {
            "kind": "sha256",
            "value": digest,
            "raw_sha256": digest,
            "raw_bytes": len(raw),
            "resolver_receipt": None,
        }
    external = source["external_identity"]
    receipt_id = _safe_id(
        context.skill_id,
        provider["input_id"],
        source["source_id"],
        "source-receipt",
    )
    evidence_sha256 = external.get(
        "evidence_sha256", provider["source_ref"]["sha256"]
    )
    receipt = _receipt(
        context,
        receipt_id=receipt_id,
        canonical_url=source["locator"],
        retrieved_utc=external["retrieved_utc"],
        raw_sha256=external["raw_sha256"],
        raw_bytes=external["raw_bytes"],
        selected_sha256=external["raw_sha256"],
        selected_bytes=external["raw_bytes"],
        evidence_sha256=evidence_sha256,
    )
    return {
        "kind": external["kind"],
        "value": receipt_id if external["kind"] == "external-receipt" else external["value"],
        "raw_sha256": external["raw_sha256"],
        "raw_bytes": external["raw_bytes"],
        "resolver_receipt": receipt,
    }


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
        "category": "other",
        "severity": severity,
        "disposition": disposition,
        "description": loss["description"],
        "affected_slice_ids": slice_ids,
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
    item: dict[str, Any],
) -> dict[str, Any]:
    selector = copy.deepcopy(item["selector"])
    byte_range = None
    if selector["kind"] == "byte-range":
        start, end = (int(value) for value in selector["value"].split(":", 1))
        byte_range = {
            "start_byte": start,
            "end_byte_exclusive": end,
        }
    if "content_ref" in item:
        raw = _validate_content_ref(
            context,
            item["content_ref"],
            label=(
                f"{context.skill_id}:{provider['input_id']}:"
                f"{source['source_id']}:{item['slice_id']}"
            ),
        )
        storage_mode = "embedded-open"
        content_locator = item["content_ref"]["path"]
        hash_basis = "artifact-and-payload-exact-bytes"
        artifact_sha256: str | None = sha256_bytes(raw)
        content_sha256 = artifact_sha256
        receipt = None
    else:
        external = item["external_receipt"]
        storage_mode = "metadata-only"
        content_locator = source["locator"]
        hash_basis = "external-receipt-content-bytes"
        artifact_sha256 = None
        content_sha256 = external["selected_sha256"]
        receipt = _receipt(
            context,
            receipt_id=(
                f"{context.skill_id}-{provider['input_id']}-"
                f"{source['source_id']}-{item['slice_id']}"
            ),
            canonical_url=source["locator"],
            retrieved_utc=external["retrieved_utc"],
            raw_sha256=external["raw_sha256"],
            raw_bytes=external["raw_bytes"],
            selected_sha256=external["selected_sha256"],
            selected_bytes=external["selected_bytes"],
            evidence_sha256=(
                source.get("metadata_evidence_ref", {}).get(
                    "sha256",
                    provider["source_ref"]["sha256"],
                )
            ),
        )
    return {
        "slice_id": item["slice_id"],
        "ordinal": item["order"],
        "selector": selector,
        "byte_range": byte_range,
        "artifact_kind": "metadata",
        "source_material_class": "documentation-text",
        "storage_mode": storage_mode,
        "content_locator": content_locator,
        "hash_basis": hash_basis,
        "artifact_sha256": artifact_sha256,
        "content_sha256": content_sha256,
        "content_receipt": receipt,
        "loss_ids": list(item.get("loss_ids", [])),
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
    embedded_refs = [
        source["source_id"]
        for source in catalog["sources"]
        if "content_ref" in source
        or any("content_ref" in item for item in source["slices"])
    ]
    if embedded_refs:
        bundle_policy = authority_entry["redistribution_policy"][
            "bundle_content"
        ]
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: declarative content_ref "
            "would place provider bytes in the ordinary Skill/distribution tree; "
            f"central bundle_content={bundle_policy!r}, so only external identity "
            "and metadata receipts are accepted"
        )
    for source in catalog["sources"]:
        evidence_ref = source.get("metadata_evidence_ref")
        if evidence_ref is None:
            continue
        evidence_raw = _validate_content_ref(
            context,
            evidence_ref,
            label=(
                f"{context.skill_id}:{provider['input_id']}:"
                f"{source['source_id']}:metadata_evidence_ref"
            ),
        )
        external_identity = source.get("external_identity")
        if (
            not isinstance(external_identity, dict)
            or external_identity.get("evidence_sha256")
            != evidence_ref["sha256"]
            or sha256_bytes(evidence_raw) != evidence_ref["sha256"]
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:"
                f"{source['source_id']}: metadata sidecar must exactly bind "
                "the external identity evidence hash; it cannot substitute for "
                "the independent upstream raw identity"
            )
        for item in source["slices"]:
            receipt = item.get("external_receipt")
            if (
                not isinstance(receipt, dict)
                or item["selector"] != {
                    "layer": "raw-source",
                    "kind": "whole-source",
                    "value": "*",
                }
                or receipt["raw_sha256"]
                != external_identity["raw_sha256"]
                or receipt["raw_bytes"] != external_identity["raw_bytes"]
                or receipt["selected_sha256"]
                != external_identity["raw_sha256"]
                or receipt["selected_bytes"]
                != external_identity["raw_bytes"]
            ):
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:"
                    f"{source['source_id']}: metadata sidecar slices require "
                    "one exact external whole-source receipt independent from "
                    "the local sidecar bytes"
                )
    included_ids: set[str] = set()
    excluded_ids: set[str] = set()
    source_records: list[dict[str, Any]] = []
    source_slices: list[dict[str, Any]] = []
    subject_slices: dict[str, list[str]] = {}
    declared_source_ids = [item["source_id"] for item in catalog["sources"]]
    if len(declared_source_ids) != len(set(declared_source_ids)):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: duplicate included "
            "source_id"
        )
    declared_source_set = set(declared_source_ids)
    declared_exclusion_ids = [
        item["source_id"] for item in catalog["reviewed_exclusions"]
    ]
    if (
        len(declared_exclusion_ids) != len(set(declared_exclusion_ids))
        or declared_source_set.intersection(declared_exclusion_ids)
    ):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: included/excluded "
            "source IDs are not a disjoint unique partition"
        )
    source_id_map = _output_id_map(
        [*declared_source_ids, *declared_exclusion_ids],
        label=f"{context.skill_id}:{provider['input_id']}:source IDs",
    )
    declared_slice_ids = [
        item["slice_id"]
        for source in catalog["sources"]
        for item in source["slices"]
    ]
    slice_id_map = _output_id_map(
        declared_slice_ids,
        label=f"{context.skill_id}:{provider['input_id']}:slice IDs",
    )
    loss_id_map = _output_id_map(
        [item["loss_id"] for item in catalog["losses"]],
        label=f"{context.skill_id}:{provider['input_id']}:loss IDs",
    )
    loss_by_id: dict[str, dict[str, Any]] = {}
    for loss in catalog["losses"]:
        loss_id = loss["loss_id"]
        if loss_id in loss_by_id:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: duplicate loss_id "
                f"{loss_id!r}"
            )
        if not set(loss["affected_source_ids"]).issubset(
            declared_source_set
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{loss_id}: "
                "affected_source_ids contain a non-included source"
            )
        loss_by_id[loss_id] = loss
    global_slice_ids: set[str] = set()
    declared_catalog_subject_ids = [
        item["subject_id"] for item in catalog["subjects"]
    ]
    declared_catalog_subjects = set(declared_catalog_subject_ids)
    if len(declared_catalog_subject_ids) != len(declared_catalog_subjects):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: duplicate catalog "
            "subject_id"
        )
    expected_provider_subjects = {
        item["subject_id"]: item
        for item in _scope_catalog(context)["subjects"]
        if item["evidence_class"] == "official-provider-required"
        and provider["input_id"] in item["provider_input_ids"]
    }
    if declared_catalog_subjects != set(expected_provider_subjects):
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: declarative catalog "
            "subject IDs do not exactly equal the canonical provider scope"
        )
    source_identity_by_id = {
        source["source_id"]: _source_identity_from_catalog(
            context,
            provider,
            source,
        )
        for source in catalog["sources"]
    }
    rolling_snapshot_sha256 = None
    if catalog["version_scope"]["kind"] == "latest-at-retrieval":
        rolling_snapshot_sha256 = _source_identity_aggregate_sha256(
            authority_id=provider["authority_id"],
            provider_id=provider["provider_id"],
            retrieved_utc=_utc(
                catalog["version_scope"]["retrieved_utc"]
            ),
            included_sources=[
                {
                    "source_id": source_id_map[source["source_id"]],
                    "locator": source["locator"],
                    "identity": source_identity_by_id[source["source_id"]],
                }
                for source in catalog["sources"]
            ],
            reviewed_exclusions=[
                {
                    "source_id": source_id_map[item["source_id"]],
                    "reason_code": item["reason_code"],
                }
                for item in catalog["reviewed_exclusions"]
            ],
        )
    output_version_scope = _output_version_scope(
        catalog["version_scope"],
        rolling_snapshot_sha256=rolling_snapshot_sha256,
    )
    (
        inventory_format,
        inventory_locator,
        inventory_sha256,
        upstream_universe_complete,
    ) = _declarative_inventory_projection(
        context,
        provider,
        authority_entry=authority_entry,
        authority_projection=authority_projection,
        mapped_discovered_ids=set(source_id_map.values()),
        upstream_universe_complete=catalog[
            "upstream_universe_complete"
        ],
    )
    for source in catalog["sources"]:
        source_id = source["source_id"]
        if source_id in included_ids:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: duplicate source_id "
                f"{source_id!r}"
            )
        included_ids.add(source_id)
        identity = source_identity_by_id[source_id]
        output_slices: list[dict[str, Any]] = []
        seen_ordinals: set[int] = set()
        slice_ids_by_loss: dict[str, list[str]] = {}
        for item in sorted(source["slices"], key=lambda value: value["order"]):
            if item["order"] in seen_ordinals:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    "duplicate slice order"
                )
            seen_ordinals.add(item["order"])
            if item["slice_id"] in global_slice_ids:
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}: duplicate "
                    f"slice_id {item['slice_id']!r}"
                )
            global_slice_ids.add(item["slice_id"])
            if not set(item["subject_ids"]).issubset(
                declared_catalog_subjects
            ):
                raise PackBuildError(
                    f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                    "slice subject_ids do not resolve to official scope subjects"
                )
            for loss_id in item.get("loss_ids", []):
                loss = loss_by_id.get(loss_id)
                if loss is None or source_id not in loss["affected_source_ids"]:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                        f"slice references dangling or cross-source loss {loss_id!r}"
                    )
                slice_ids_by_loss.setdefault(loss_id, []).append(
                    slice_id_map[item["slice_id"]]
                )
            output = _slice_from_catalog(
                context, provider, source, identity, item
            )
            output["slice_id"] = slice_id_map[item["slice_id"]]
            output["loss_ids"] = [
                loss_id_map[loss_id]
                for loss_id in item.get("loss_ids", [])
            ]
            output_slices.append(output)
            for subject_id in item["subject_ids"]:
                subject_slices.setdefault(subject_id, []).append(
                    output["slice_id"]
                )
        if [item["ordinal"] for item in output_slices] != list(
            range(len(output_slices))
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "slice orders must be contiguous from zero"
            )
        relevant_losses = [
            loss
            for loss in catalog["losses"]
            if source_id in loss["affected_source_ids"]
        ]
        missing_loss_links = sorted(
            loss["loss_id"]
            for loss in relevant_losses
            if not slice_ids_by_loss.get(loss["loss_id"])
        )
        if missing_loss_links:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}:{source_id}: "
                "loss ledger entries are not linked from exact slices: "
                + ", ".join(missing_loss_links)
            )
        loss_ledger = [
            _output_loss(
                {
                    **loss,
                    "loss_id": loss_id_map[loss["loss_id"]],
                },
                sorted(slice_ids_by_loss[loss["loss_id"]]),
            )
            for loss in relevant_losses
        ]
        projection = {
            "slices": output_slices,
            "reviewed_overlaps": [],
            "preserved_ranges": [],
            "reviewed_orphans": [],
            "loss_ledger": loss_ledger,
        }
        source_slices.append(
            {
                "source_id": source_id_map[source_id],
                "source_identity": identity,
                "raw_source_extent_bytes": identity["raw_bytes"],
                "transformer": _processor(
                    context,
                    kind="transformer",
                    input_sha256=identity["raw_sha256"],
                    output_sha256=canonical_projection_sha256(projection),
                ),
                **projection,
            }
        )
        source_records.append(
            {
                "source_id": source_id_map[source_id],
                "source_kind": source["source_kind"],
                "locator": source["locator"],
                "version_scope": _source_version_scope(
                    output_version_scope,
                    raw_sha256=identity["raw_sha256"],
                ),
                "identity": identity,
            }
        )
    exclusions: list[dict[str, Any]] = []
    for item in catalog["reviewed_exclusions"]:
        source_id = item["source_id"]
        if source_id in included_ids or source_id in excluded_ids:
            raise PackBuildError(
                f"{context.skill_id}:{provider['input_id']}: source universe is "
                "not a disjoint ID partition"
            )
        excluded_ids.add(source_id)
        exclusions.append(
            {
                "source_id": source_id_map[source_id],
                "reason_code": item["reason_code"],
                "rationale": item["rationale"],
                "reviewed_by": "official-document-pack-builder",
                "reviewed_utc": _utc(item["reviewed_utc"]),
            }
        )
    missing_required_slices = sorted(
        subject_id
        for subject_id, subject in expected_provider_subjects.items()
        if subject["expected_disposition"] != "blocked"
        and not subject_slices.get(subject_id)
    )
    if missing_required_slices:
        raise PackBuildError(
            f"{context.skill_id}:{provider['input_id']}: slice mappings do not "
            "cover non-blocked canonical provider scope subjects: "
            + ", ".join(missing_required_slices)
        )
    for subject_id in expected_provider_subjects:
        subject_slices.setdefault(subject_id, [])
    projection = authority_projection
    version = catalog["version_scope"]
    retrieved_values = [
        item["external_identity"]["retrieved_utc"]
        for item in catalog["sources"]
        if "external_identity" in item
    ]
    retrieved = max((_utc(item) for item in retrieved_values), default=DEFAULT_GENERATED_UTC)
    revision = (
        version["value"]
        if version["value"] is not None
        else (
            output_version_scope["snapshot_identity"]["value"]
            if output_version_scope["snapshot_identity"] is not None
            else f"catalog-{provider['source_ref']['sha256']}"
        )
    )
    return ProviderBuild(
        input_id=provider["input_id"],
        authority_id=provider["authority_id"],
        provider_id=provider["provider_id"],
        version_scope=copy.deepcopy(output_version_scope),
        retrieved_utc=retrieved,
        authority_root=projection["canonical_urls"][0],
        authority_revision=str(revision),
        inventory_format=inventory_format,
        inventory_locator=inventory_locator,
        inventory_sha256=inventory_sha256,
        upstream_universe_complete=upstream_universe_complete,
        included_sources=tuple(source_records),
        reviewed_exclusions=tuple(exclusions),
        source_slices=tuple(source_slices),
        subject_slice_ids={
            subject_id: tuple(sorted(subject_slices[subject_id]))
            for subject_id in sorted(expected_provider_subjects)
        },
        license=copy.deepcopy(catalog["license"]),
        limitations=tuple(catalog["limitations"]),
        blockers=tuple(
            [
                *copy.deepcopy(catalog["blockers"]),
                *_blocking_loss_blockers(catalog["losses"]),
            ]
        ),
    )


def _qe_adapter(
    context: BuildContext,
    provider: dict[str, Any],
) -> ProviderBuild:
    _authority(context, provider)
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
        or not isinstance(manifest["manuals"], list)
    ):
        raise PackBuildError(
            "QE compact catalog root does not match the exact v1 adapter"
        )
    included: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    source_slices: list[dict[str, Any]] = []
    subject_slices: dict[str, list[str]] = {}
    seen_names: set[str] = set()
    total_sections = 0
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
        if not isinstance(manual, dict) or set(manual) != expected_manual:
            raise PackBuildError("QE input manual does not match the exact adapter")
        name = manual["name"]
        if name in seen_names:
            raise PackBuildError(f"QE manifest has duplicate input manual {name!r}")
        seen_names.add(name)
        source_id = _safe_id("qe-input", name)
        if manual["version"] != "7.5":
            if name != "INPUT_LD1" or manual["version"] != "7.4":
                raise PackBuildError(
                    f"QE manifest has unexpected non-7.5 manual {name!r} "
                    f"at version {manual['version']!r}"
                )
            exclusions.append(
                {
                    "source_id": source_id,
                    "reason_code": "obsolete",
                    "rationale": (
                        "INPUT_LD1 is explicitly version 7.4 and is excluded "
                        "from the exact QE 7.5 corpus."
                    ),
                    "reviewed_by": "official-document-pack-builder",
                    "reviewed_utc": _utc(manual["retrieved_utc"]),
                }
            )
            continue
        identity = {
            "kind": "sha256",
            "value": manual["raw_sha256"],
            "raw_sha256": manual["raw_sha256"],
            "raw_bytes": manual["raw_bytes"],
            "resolver_receipt": None,
        }
        version_scope = {
            "kind": "exact",
            "value": "7.5",
            "retrieved_utc": None,
            "snapshot_identity": None,
        }
        included.append(
            {
                "source_id": source_id,
                "source_kind": "reference-page",
                "locator": manual["url"],
                "version_scope": version_scope,
                "identity": identity,
            }
        )
        output_slices: list[dict[str, Any]] = []
        section_ids: set[str] = set()
        for ordinal, section in enumerate(manual["sections"]):
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
                or section["order"] != ordinal
                or section["section_id"] in section_ids
            ):
                raise PackBuildError(
                    f"QE {name}: section structure/order is not exact"
                )
            section_ids.add(section["section_id"])
            if section["payload_hash_basis"] != (
                "utf-8 bytes of the fenced text payload after removing "
                "the single wrapper separator newline"
            ):
                raise PackBuildError(
                    f"QE {name} section {section['section_id']}: "
                    "unsupported payload hash basis"
                )
            slice_id = _safe_id("qe", name, section["section_id"])
            output_slices.append(
                {
                    "slice_id": slice_id,
                    "ordinal": ordinal,
                    "selector": {
                        "layer": "derived-artifact",
                        "kind": "source-symbol",
                        "value": section["section_id"],
                    },
                    "byte_range": None,
                    "artifact_kind": "metadata",
                    "source_material_class": "documentation-text",
                    "storage_mode": "metadata-only",
                    "content_locator": manual["url"],
                    "hash_basis": "external-receipt-content-bytes",
                    "artifact_sha256": None,
                    "content_sha256": section["selected_sha256"],
                    "content_receipt": _receipt(
                        context,
                        receipt_id=f"{slice_id}-receipt",
                        canonical_url=manual["url"],
                        retrieved_utc=manual["retrieved_utc"],
                        raw_sha256=manual["raw_sha256"],
                        raw_bytes=manual["raw_bytes"],
                        selected_sha256=section["selected_sha256"],
                        selected_bytes=section["selected_bytes"],
            evidence_sha256=provider["source_ref"]["sha256"],
                    ),
                    "loss_ids": [
                        _safe_id(source_id, "portal-pdf-asset-closure")
                    ],
                }
            )
            total_sections += 1
        loss = {
            "loss_id": _safe_id(source_id, "portal-pdf-asset-closure"),
            "category": "asset",
            "severity": "material",
            "disposition": "external-only",
            "description": (
                "Portal navigation, PDF parity, linked pages, images, and "
                "non-text assets remain external and are not byte-closed by "
                "the input-manual section mirror."
            ),
            "affected_slice_ids": [
                item["slice_id"] for item in output_slices
            ],
        }
        projection = {
            "slices": output_slices,
            "reviewed_overlaps": [],
            "preserved_ranges": [],
            "reviewed_orphans": [],
            "loss_ledger": [loss],
        }
        source_slices.append(
            {
                "source_id": source_id,
                "source_identity": identity,
                "raw_source_extent_bytes": manual["raw_bytes"],
                "transformer": _processor(
                    context,
                    kind="transformer",
                    input_sha256=manual["raw_sha256"],
                    output_sha256=canonical_projection_sha256(projection),
                ),
                **projection,
            }
        )
        ids = [item["slice_id"] for item in output_slices]
        subject_slices.setdefault("qe-input-manuals", []).extend(ids)
    if len(included) != 35 or total_sections != 1159:
        raise PackBuildError(
            "QE adapter requires exactly 35 QE 7.5 manuals and 1159 sections "
            f"(found {len(included)} and {total_sections})"
        )
    return ProviderBuild(
        input_id=provider["input_id"],
        authority_id=provider["authority_id"],
        provider_id=provider["provider_id"],
        version_scope={
            "kind": "exact",
            "value": "7.5",
            "retrieved_utc": None,
            "snapshot_identity": None,
        },
        retrieved_utc=_utc(manifest["retrieved_utc"]),
        authority_root=manifest["source_root"],
        authority_revision="7.5",
        inventory_format="qe-official-manifest-v1",
        inventory_locator=provider["source_ref"]["path"],
        inventory_sha256=provider["source_ref"]["sha256"],
        upstream_universe_complete=False,
        included_sources=tuple(included),
        reviewed_exclusions=tuple(exclusions),
        source_slices=tuple(source_slices),
        subject_slice_ids={
            key: tuple(value) for key, value in subject_slices.items()
        },
        license={},
        limitations=(
            "Coverage is a bounded exact QE 7.5 input-manual subset, not the complete Doc portal.",
            "INPUT_LD1 is explicitly excluded because the official mirror labels it as QE 7.4.",
            "PDF manuals, user-guide pages, release notes, links, images, and assets remain external.",
        ),
        blockers=(),
    )


def _vasp_adapter(
    context: BuildContext,
    provider: dict[str, Any],
) -> ProviderBuild:
    _authority(context, provider)
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
    included: list[dict[str, Any]] = []
    source_slices: list[dict[str, Any]] = []
    subject_slices: dict[str, list[str]] = {}
    expected_provider_subjects = {
        item["subject_id"]
        for item in _scope_catalog(context)["subjects"]
        if item["evidence_class"] == "official-provider-required"
        and provider["input_id"] in item["provider_input_ids"]
    }
    pageids: set[int] = set()
    revision_pairs: set[tuple[int, int]] = set()
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
        if pageid in pageids or (pageid, revid) in revision_pairs:
            raise PackBuildError("VASP manifest has duplicate page/revision identity")
        pageids.add(pageid)
        revision_pairs.add((pageid, revid))
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
            identity = {
                "kind": "sha256",
                "value": digest,
                "raw_sha256": digest,
                "raw_bytes": extent,
                "resolver_receipt": None,
            }
            source_scope = {
                "kind": "latest-at-retrieval",
                "value": None,
                "retrieved_utc": retrieved,
                "snapshot_identity": {
                    "kind": "revision",
                    "value": str(revid),
                    "content_sha256": digest,
                },
            }
            included.append(
                {
                    "source_id": source_id,
                    "source_kind": (
                        "api-record"
                        if representation == "api-json"
                        else "reference-page"
                    ),
                    "locator": (
                        page["api_request_url"]
                        if representation == "api-json"
                        else page["url"]
                    ),
                    "version_scope": source_scope,
                    "identity": identity,
                }
            )
            slice_id = _safe_id(source_id, "whole")
            item = {
                "slice_id": slice_id,
                "ordinal": 0,
                "selector": {
                    "layer": "raw-source",
                    "kind": "whole-source",
                    "value": "*",
                },
                "byte_range": None,
                "artifact_kind": "metadata",
                "source_material_class": "documentation-text",
                "storage_mode": "metadata-only",
                "content_locator": page["api_request_url"],
                "hash_basis": "external-receipt-content-bytes",
                "artifact_sha256": None,
                "content_sha256": digest,
                "content_receipt": _receipt(
                    context,
                    receipt_id=f"{slice_id}-receipt",
                    canonical_url=page["api_request_url"],
                    retrieved_utc=retrieved,
                    raw_sha256=digest,
                    raw_bytes=extent,
                    selected_sha256=digest,
                    selected_bytes=extent,
                    evidence_sha256=provider["source_ref"]["sha256"],
                ),
                "loss_ids": [
                    _safe_id(source_id, "page-link-asset-closure")
                ],
            }
            loss = {
                "loss_id": _safe_id(
                    source_id, "page-link-asset-closure"
                ),
                "category": "link",
                "severity": "material",
                "disposition": "external-only",
                "description": (
                    "Linked Wiki pages, Portal content, rendered media, and "
                    "third-party assets are outside this exact page identity."
                ),
                "affected_slice_ids": [slice_id],
            }
            projection = {
                "slices": [item],
                "reviewed_overlaps": [],
                "preserved_ranges": [],
                "reviewed_orphans": [],
                "loss_ledger": [loss],
            }
            source_slices.append(
                {
                    "source_id": source_id,
                    "source_identity": identity,
                    "raw_source_extent_bytes": extent,
                    "transformer": _processor(
                        context,
                        kind="transformer",
                        input_sha256=digest,
                        output_sha256=canonical_projection_sha256(projection),
                    ),
                    **projection,
                }
            )
            if representation == "wikitext":
                tag_subject = _safe_id("vasp-safe-tag", page["title"])
                if tag_subject in expected_provider_subjects:
                    subject_slices.setdefault(tag_subject, []).append(slice_id)
    if len(included) != 162 or len(source_slices) != 162:
        raise PackBuildError("VASP adapter must emit 81 API + 81 wikitext identities")
    if (
        set(subject_slices) != expected_provider_subjects
        or any(not values for values in subject_slices.values())
    ):
        raise PackBuildError(
            "VASP adapter safe-tag mappings do not exactly equal canonical "
            "provider scope subjects"
        )
    manifest_digest = provider["source_ref"]["sha256"]
    return ProviderBuild(
        input_id=provider["input_id"],
        authority_id=provider["authority_id"],
        provider_id=provider["provider_id"],
        version_scope={
            "kind": "latest-at-retrieval",
            "value": None,
            "retrieved_utc": retrieved,
            "snapshot_identity": {
                "kind": "sha256",
                "value": manifest_digest,
                "content_sha256": manifest_digest,
            },
        },
        retrieved_utc=retrieved,
        authority_root=manifest["official_root"],
        authority_revision=f"81-pages-at-{retrieved}",
        inventory_format="vasp-wiki-manifest-v1",
        inventory_locator=provider["source_ref"]["path"],
        inventory_sha256=manifest_digest,
        upstream_universe_complete=False,
        included_sources=tuple(included),
        reviewed_exclusions=(),
        source_slices=tuple(source_slices),
        subject_slice_ids={
            key: tuple(value) for key, value in subject_slices.items()
        },
        license={},
        limitations=(
            "The 81-page curated Wiki set is a bounded subset, not full site closure.",
            "API JSON and extracted wikitext are separate exact identities; rendered Markdown is not substituted for either.",
            "Portal downloads, link closure, images, templates, and third-party assets remain external.",
        ),
        blockers=(),
    )


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
    """Reject dangling identities, slices, and losses from every adapter."""

    included_by_id = {
        item["source_id"]: item for item in provider.included_sources
    }
    if len(included_by_id) != len(provider.included_sources):
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: duplicate included source ID"
        )
    excluded_ids = [item["source_id"] for item in provider.reviewed_exclusions]
    if (
        len(excluded_ids) != len(set(excluded_ids))
        or set(excluded_ids).intersection(included_by_id)
    ):
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: included/excluded source "
            "IDs are not disjoint and unique"
        )
    sliced_by_id = {item["source_id"]: item for item in provider.source_slices}
    if (
        len(sliced_by_id) != len(provider.source_slices)
        or set(sliced_by_id) != set(included_by_id)
    ):
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: source-slice records do "
            "not exactly equal included source IDs"
        )
    all_slice_ids: set[str] = set()
    for source_id, source in sliced_by_id.items():
        if source["source_identity"] != included_by_id[source_id]["identity"]:
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: corpus "
                "and slice source identities differ"
            )
        slice_ids = [item["slice_id"] for item in source["slices"]]
        if (
            len(slice_ids) != len(set(slice_ids))
            or all_slice_ids.intersection(slice_ids)
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: slice IDs are not "
                "globally unique"
            )
        all_slice_ids.update(slice_ids)
        losses = {
            item["loss_id"]: item for item in source["loss_ledger"]
        }
        if len(losses) != len(source["loss_ledger"]):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: duplicate "
                "loss ledger ID"
            )
        linked: dict[str, set[str]] = {}
        for item in source["slices"]:
            if len(item["loss_ids"]) != len(set(item["loss_ids"])):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: "
                    "duplicate loss reference on a slice"
                )
            for loss_id in item["loss_ids"]:
                if loss_id not in losses:
                    raise PackBuildError(
                        f"{context.skill_id}:{provider.input_id}:{source_id}: "
                        f"dangling slice loss ID {loss_id!r}"
                    )
                linked.setdefault(loss_id, set()).add(item["slice_id"])
        if set(linked) != set(losses):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{source_id}: loss "
                "ledger and slice references do not have exact closure"
            )
        for loss_id, loss in losses.items():
            affected = loss["affected_slice_ids"]
            if (
                not affected
                or len(affected) != len(set(affected))
                or set(affected) != linked[loss_id]
            ):
                raise PackBuildError(
                    f"{context.skill_id}:{provider.input_id}:{source_id}: loss "
                    f"{loss_id!r} does not exactly bind its affected slices"
                )
    for subject_id, slice_ids in provider.subject_slice_ids.items():
        if (
            len(slice_ids) != len(set(slice_ids))
            or not set(slice_ids).issubset(all_slice_ids)
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}:{subject_id}: subject "
                "mapping contains duplicate or dangling slices"
            )


def _license_projection(
    context: BuildContext,
    provider: ProviderBuild,
) -> dict[str, Any]:
    """Compute the conservative central-policy ∩ catalog license projection."""

    authority = context.snapshot.official_source_authorities["authorities"][
        provider.authority_id
    ]
    central = authority["license_policy"]
    redistribution = authority["redistribution_policy"]
    central_modes = {"metadata-only", "excluded"}
    if redistribution["external_runtime_content"] != "unavailable":
        central_modes.add("external-runtime-only")

    if provider.license:
        supplied = provider.license
        supplied_identity = supplied["identity"]
        requested_modes = set(supplied["allowed_storage_modes"])
        supplied_assessment = supplied["assessment"]
        evidence_locator = supplied["official_terms_locator"]
        license_limitations = list(supplied["limitations"])
    else:
        supplied_identity = {
            "identifier": central["identifier"],
            "terms_urls": list(central["terms_urls"]),
            "verification": (
                "verified"
                if central["verification_status"] == "verified"
                else "unknown"
            ),
        }
        requested_modes = set(central_modes)
        supplied_assessment = (
            "allowed"
            if central["status"] == "known-open"
            else (
                "conditional"
                if central["status"] == "known-restricted"
                else "unresolved"
            )
        )
        evidence_locator = (
            central["terms_urls"][0]
            if central["terms_urls"]
            else authority["provenance"]["official_fact_urls"][0]
        )
        license_limitations = []

    central_verified = (
        central["verification_status"] == "verified"
        and central["status"] in {"known-open", "known-restricted"}
    )
    supplied_verified = supplied_identity["verification"] == "verified"
    if central_verified and supplied_verified:
        if (
            supplied_identity["identifier"] != central["identifier"]
            or supplied_identity["terms_urls"] != central["terms_urls"]
            or evidence_locator not in central["terms_urls"]
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: verified catalog "
                "license identity conflicts with the central authority policy"
            )
        identity = {
            "identifier": central["identifier"],
            "terms_urls": list(central["terms_urls"]),
            "verification": "verified",
        }
    elif supplied_verified:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: catalog cannot upgrade an "
            "unresolved central license identity to verified"
        )
    else:
        if supplied_identity["identifier"] is not None or supplied_identity[
            "terms_urls"
        ]:
            license_limitations.append(
                "Unverified catalog license identifier and terms URL claims "
                "were conservatively downgraded to null/empty; the separately "
                "declared official_terms_locator remains evidence only."
            )
        identity = {
            "identifier": None,
            "terms_urls": [],
            "verification": "unknown",
        }

    central_assessment = (
        "allowed"
        if central["status"] == "known-open"
        else (
            "conditional"
            if central["status"] == "known-restricted"
            else "unresolved"
        )
    )
    restrictiveness = {
        "allowed": 0,
        "conditional": 1,
        "unresolved": 2,
        "forbidden": 3,
    }
    assessment = max(
        (central_assessment, supplied_assessment),
        key=restrictiveness.__getitem__,
    )
    allowed_modes = sorted(requested_modes.intersection(central_modes))
    if assessment == "forbidden":
        allowed_modes = [
            item for item in allowed_modes if item == "excluded"
        ]
    if "metadata-only" not in allowed_modes:
        raise PackBuildError(
            f"{context.skill_id}:{provider.input_id}: central/catalog license "
            "intersection does not permit the pack's metadata-only slices"
        )
    return {
        "identity": identity,
        "assessment": assessment,
        "allowed_storage_modes": allowed_modes,
        "evidence_locator": evidence_locator,
        "limitations": sorted(
            set(
                [
                    *license_limitations,
                    "The generated review is the conservative intersection of "
                    "the central authority policy and the hashed provider catalog.",
                ]
            )
        ),
    }


def _build_one(context: BuildContext) -> dict[str, bytes]:
    """Return one complete byte-stable pack without mutating the repository."""

    _validate_dependency_lock(context)
    scope_catalog = _scope_catalog(context)
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
        if set(built.subject_slice_ids) != expected_subjects:
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
    corpus_records: list[tuple[ProviderBuild, dict[str, Any], str, str]] = []
    slice_records: list[tuple[ProviderBuild, dict[str, Any], str, str]] = []
    license_records: list[tuple[ProviderBuild, dict[str, Any], str, str]] = []
    bindings_by_id: dict[str, dict[str, Any]] = {}

    for provider_input, provider in providers:
        binding = _central_binding(context, provider_input)
        bindings_by_id[binding["binding_id"]] = binding
        corpus_blockers = _output_blockers(
            provider.blockers,
            label=f"{context.skill_id}:{provider.input_id}:corpus",
            dimension="corpus",
        )
        slice_blockers = _output_blockers(
            provider.blockers,
            label=f"{context.skill_id}:{provider.input_id}:slices",
            dimension="slices",
        )
        corpus_status = "blocked" if corpus_blockers else "partial"
        slice_status = "blocked" if slice_blockers else "partial"
        limitations = sorted(
            set(
                [
                    *context.seed["limitations"],
                    *provider.limitations,
                    (
                        "Central processor hashes are pinned, but this exact "
                        "input/output run has no platform attestation."
                    ),
                ]
            )
        )
        included_ids = [
            item["source_id"] for item in provider.included_sources
        ]
        excluded_ids = [
            item["source_id"] for item in provider.reviewed_exclusions
        ]
        discovered_ids = sorted([*included_ids, *excluded_ids])
        if (
            len(discovered_ids) != len(set(discovered_ids))
            or not included_ids
        ):
            raise PackBuildError(
                f"{context.skill_id}:{provider.input_id}: invalid source universe"
            )
        corpus_id = _safe_id(
            context.skill_id, provider.input_id, "official-corpus"
        )
        enumerator_output = canonical_projection_sha256(
            {"discovered_source_ids": discovered_ids}
        )
        corpus = {
            "schema_version": "1.0",
            "contract_name": "official-corpus-manifest",
            "corpus_id": corpus_id,
            "authority_id": provider.authority_id,
            "provider_id": provider.provider_id,
            "version_scope": copy.deepcopy(provider.version_scope),
            "status": corpus_status,
            "discovery": {
                "method": (
                    "official-api"
                    if provider.inventory_format == "vasp-wiki-manifest-v1"
                    else (
                        "official-index"
                        if provider.inventory_format
                        == "qe-official-manifest-v1"
                        else "manual-inventory"
                    )
                ),
                "upstream_universe_complete": (
                    provider.upstream_universe_complete
                ),
                "inventory_scope": (
                    "upstream-universe"
                    if provider.upstream_universe_complete
                    else "bounded-authority-subset"
                ),
                "authority_root": provider.authority_root,
                "authority_revision": provider.authority_revision,
                "inventory_format": provider.inventory_format,
                "inventory_storage_mode": "embedded-open",
                "inventory_locator": provider.inventory_locator,
                "inventory_sha256": provider.inventory_sha256,
                "inventory_receipt": None,
                "enumerator": _processor(
                    context,
                    kind="enumerator",
                    input_sha256=provider.inventory_sha256,
                    output_sha256=enumerator_output,
                ),
                "discovered_source_ids": discovered_ids,
            },
            "included_sources": list(provider.included_sources),
            "reviewed_exclusions": list(provider.reviewed_exclusions),
            "blockers": corpus_blockers,
            "limitations": limitations,
            "producer": producer,
        }
        corpus_name = f"corpus-{provider.input_id}.json"
        corpus_raw = canonical_json_bytes(corpus)
        corpus_sha = sha256_bytes(corpus_raw)
        records[corpus_name] = corpus_raw
        corpus_records.append((provider, corpus, corpus_name, corpus_sha))

        slice_id = _safe_id(
            context.skill_id, provider.input_id, "official-slices"
        )
        slices = {
            "schema_version": "1.0",
            "contract_name": "document-slice-manifest",
            "slice_manifest_id": slice_id,
            "corpus_ref": {
                "corpus_id": corpus_id,
                "sha256": corpus_sha,
            },
            "status": slice_status,
            "sources": list(provider.source_slices),
            "blockers": slice_blockers,
            "limitations": limitations,
            "producer": producer,
        }
        slice_name = f"slices-{provider.input_id}.json"
        slice_raw = canonical_json_bytes(slices)
        slice_sha = sha256_bytes(slice_raw)
        records[slice_name] = slice_raw
        slice_records.append((provider, slices, slice_name, slice_sha))

        authority_entry = context.snapshot.official_source_authorities[
            "authorities"
        ][provider.authority_id]
        license_projection = _license_projection(context, provider)
        license_identity = license_projection["identity"]
        allowed_modes = license_projection["allowed_storage_modes"]
        evidence_locator = license_projection["evidence_locator"]
        evidence_id = _safe_id(provider.input_id, "license-evidence")
        license_review_id = _safe_id(
            context.skill_id, provider.input_id, "license-review"
        )
        license_status = "partial"
        license_limitations = sorted(
            set(
                [
                    *license_projection["limitations"],
                    "The exact official-terms bytes and retrieval revision are "
                    "not locally bound or platform attested.",
                    "License trust remains unverified in the central consumer "
                    "registry.",
                ]
            )
        )
        license_review = {
            "schema_version": "1.0",
            "contract_name": "official-source-license-review",
            "license_review_id": license_review_id,
            "corpus_ref": {
                "corpus_id": corpus_id,
                "sha256": corpus_sha,
            },
            "authority_id": provider.authority_id,
            "status": license_status,
            "trust_attestation": {
                "trust_mode": "unverified",
                "registry_path": "registry/official-document-consumers.yaml",
                "registry_sha256": context.snapshot.registry_sha256[
                    CONSUMER_REGISTRY_NAME
                ],
                "trust_id": None,
                "attestation_ref": None,
            },
            "license_identity": license_identity,
            "storage_rules": [
                {
                    "artifact_kind": "metadata",
                    "source_material_class": "documentation-text",
                    "assessment": license_projection["assessment"],
                    "allowed_storage_modes": allowed_modes,
                    "conditions": [
                        "Keep official body content external; retain only exact identities, selectors, and receipts in this pack."
                    ],
                    "limitations": sorted(
                        set(
                            [
                                *license_projection["limitations"],
                                "The exact official-terms bytes, retrieval "
                                "revision, reviewer, and obligation analysis "
                                "are not platform attested.",
                            ]
                        )
                    ),
                    "license_evidence_refs": [evidence_id],
                    "rights_holder": (
                        "Official provider; exact rights-holder scope remains "
                        "subject to the cited official terms."
                    ),
                    "attribution_required": "unknown",
                    "notice_required": "unknown",
                    "modified_content_marking_required": "unknown",
                    "share_alike_required": "unknown",
                    "source_offer_required": "unknown",
                }
            ],
            "evidence": [
                {
                    "evidence_id": evidence_id,
                    "locator": evidence_locator,
                    "revision": None,
                    "sha256": None,
                    "hash_basis": "unattested-external-locator",
                    "terms_content_ref": None,
                }
            ],
            "review_expires_utc": None,
            "supersedes_review_ids": [],
            "blockers": [],
            "limitations": license_limitations,
            "reviewer": {
                "reviewer_id": "official-document-pack-builder",
                "role": "license-reviewer",
                "reviewed_utc": generated_utc,
            },
            "producer": producer,
        }
        license_name = f"license-review-{provider.input_id}.json"
        license_raw = canonical_json_bytes(license_review)
        license_sha = sha256_bytes(license_raw)
        records[license_name] = license_raw
        license_records.append(
            (provider, license_review, license_name, license_sha)
        )

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
    scope_subject_id_map = _output_id_map(
        [item["subject_id"] for item in scope_catalog["subjects"]],
        label=f"{context.skill_id}:scope subjects",
    )
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
        subject = {
            "subject_id": scope_subject_id_map[item["subject_id"]],
            "subject_kind": item["subject_kind"],
            "evidence_class": item["evidence_class"],
            "origin_refs": origins,
            "statement": item["statement"],
        }
        scope_subjects.append(subject)
        scope_meta[subject["subject_id"]] = item
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

    provider_by_input = {
        provider.input_id: provider for _, provider in providers
    }
    slice_manifest_ids = {
        provider.input_id: record["slice_manifest_id"]
        for provider, record, _, _ in slice_records
    }
    mappings: list[dict[str, Any]] = []
    official_mapping_blocked = False
    for subject in scope_subjects:
        meta = scope_meta[subject["subject_id"]]
        if subject["evidence_class"] == "official-provider-required":
            refs: list[dict[str, str]] = []
            for input_id in meta["provider_input_ids"]:
                provider = provider_by_input[input_id]
                for slice_id in provider.subject_slice_ids.get(
                    meta["subject_id"], ()
                ):
                    refs.append(
                        {
                            "slice_manifest_id": slice_manifest_ids[input_id],
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
            if not refs and meta["expected_disposition"] != "blocked":
                raise PackBuildError(
                    f"{context.skill_id}: official scope subject "
                    f"{subject['subject_id']!r} has no exact provider slice"
                )
            if meta["expected_disposition"] == "blocked":
                mapping_status = "blocked"
                official_mapping_blocked = True
            else:
                mapping_status = "partial"
            mappings.append(
                {
                    "subject_id": subject["subject_id"],
                    "coverage_status": mapping_status,
                    "official_disposition": mapping_status,
                    "slice_refs": refs,
                    "local_evidence_refs": [],
                    "rationale": (
                        "The canonical Skill scope marks this provider subject "
                        "blocked; no unrelated public or literature slice is "
                        "substituted for unavailable official evidence."
                        if mapping_status == "blocked"
                        else None
                    ),
                    "limitations": (
                        [
                            "Official evidence is unavailable, restricted, or "
                            "otherwise unresolved for this blocked subject."
                        ]
                        if mapping_status == "blocked"
                        else [
                            "Official source and slice identities are exact "
                            "metadata, but resolver, processor, and license "
                            "trust remain below complete."
                        ]
                    ),
                }
            )
        else:
            local_refs = sorted(
                {
                    (origin["path"], origin["sha256"])
                    for origin in subject["origin_refs"]
                }
            )
            mappings.append(
                {
                    "subject_id": subject["subject_id"],
                    "coverage_status": "complete",
                    "official_disposition": meta["expected_disposition"],
                    "slice_refs": [],
                    "local_evidence_refs": [
                        {"path": path, "sha256": digest}
                        for path, digest in local_refs
                    ],
                    "rationale": (
                        "This subject is established by exact local Skill "
                        "source and is outside provider-document coverage."
                    ),
                    "limitations": [],
                }
            )
    coverage_blockers = list(scope_blockers)
    if official_mapping_blocked and not coverage_blockers:
        coverage_blockers.append(
            {
                "code": "official-subject-blocked",
                "description": (
                    "At least one canonical scope subject is explicitly blocked."
                ),
            }
        )
    if any(
        record["status"] == "blocked"
        for _, record, _, _ in [
            *corpus_records,
            *slice_records,
            *license_records,
        ]
    ) and not coverage_blockers:
        coverage_blockers.append(
            {
                "code": "provider-record-blocked",
                "description": (
                    "At least one exact provider record is blocked."
                ),
            }
        )
    coverage_status = "blocked" if coverage_blockers else "partial"
    coverage = {
        "schema_version": "1.0",
        "contract_name": "skill-document-coverage",
        "coverage_id": _safe_id(
            context.skill_id, "official-document-coverage"
        ),
        "skill_id": context.skill_id,
        "consumer_binding_refs": [
            {
                "registry_path": "registry/official-document-consumers.yaml",
                "registry_sha256": context.snapshot.registry_sha256[
                    CONSUMER_REGISTRY_NAME
                ],
                "binding_id": binding_id,
            }
            for binding_id in sorted(bindings_by_id)
        ],
        "status": coverage_status,
        "corpus_refs": [
            {
                "corpus_id": record["corpus_id"],
                "sha256": digest,
            }
            for _, record, _, digest in corpus_records
        ],
        "slice_manifest_refs": [
            {
                "slice_manifest_id": record["slice_manifest_id"],
                "sha256": digest,
            }
            for _, record, _, digest in slice_records
        ],
        "license_review_refs": [
            {
                "license_review_id": record["license_review_id"],
                "sha256": digest,
            }
            for _, record, _, digest in license_records
        ],
        "scope_inventory_ref": {
            "inventory_id": scope_id,
            "sha256": scope_sha,
        },
        "declared_scope": scope_subjects,
        "mappings": sorted(
            mappings, key=lambda item: item["subject_id"]
        ),
        "blockers": coverage_blockers,
        "limitations": sorted(
            set(
                [
                    *context.seed["limitations"],
                    "Complete official-document coverage is not claimed by this metadata-only pack.",
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
            "corpora": sorted(
                name for _, _, name, _ in corpus_records
            ),
            "slice_manifests": sorted(
                name for _, _, name, _ in slice_records
            ),
            "license_reviews": sorted(
                name for _, _, name, _ in license_records
            ),
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
                f"license-review-{input_id}.json",
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
    for name, raw in outputs.items():
        if (
            PurePosixPath(name).name != name
            or not re.fullmatch(
                r"(?:bundle|scope-inventory|coverage|"
                r"(?:corpus|slices|license-review)-"
                r"[a-z0-9]+(?:-[a-z0-9]+)*)\.json",
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
            license_review_paths=[
                stage / f"license-review-{input_id}.json"
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
