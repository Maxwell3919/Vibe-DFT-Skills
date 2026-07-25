#!/usr/bin/env python3
"""Audit tracked official-document storage topology and exact identities.

The Git index supplies the tracked path set, while ordinary local audit hashes
the corresponding regular worktree bytes and scans for untracked namespace
paths. Repository-local configuration classifies every path in the four
legacy official-document namespaces as either an artifact set or an exact
local control. Artifact sets retain every applicable registered authority ID;
one authority cannot overwrite another authority from the same provider.

Invalid configuration, authority projection, unsafe worktree state,
classification, or exact candidate baseline identity always exits 2.
``--strict-release`` additionally blocks worktree drift and legacy namespace
artifacts that have not migrated into the canonical v1.1 pack domain.
Git-baseline comparison is delete-only after a bounded first-registry
bootstrap. There is no waiver or grandfather lane.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from typing import Iterable

import official_source_authorities
from registry_yaml import (
    RegistryYAMLError,
    load_yaml_strict,
    loads_yaml_bytes_strict,
)
import validate_official_document_bundles as official_document_bundles


SCHEMA_VERSION = "1.0"
CONFIGURATION_PATH = PurePosixPath(
    "registry", "official-document-storage-discovery.yaml"
)
MIGRATION_POLICY = {
    "authority_evaluation": "all-of",
    "waiver_policy": "forbidden",
    "unclassified_namespace_path": "invalid",
    "baseline_policy": "exact-git-index",
}
TOP_LEVEL_FIELDS = {
    "schema_version",
    "authority_registry",
    "migration_policy",
    "namespaces",
    "artifact_sets",
    "local_controls",
}
NAMESPACE_FIELDS = {"provider_id", "path_prefix"}
ARTIFACT_SET_FIELDS = {
    "provider_id",
    "authority_ids",
    "selectors",
    "baseline",
}
SELECTOR_FIELDS = {"kind", "value"}
BASELINE_FIELDS = {"path_count", "byte_count", "digest_sha256"}
LOCAL_CONTROL_FIELDS = {"provider_id", "path", "baseline"}
CONTROL_BASELINE_FIELDS = {"mode", "byte_count", "blob_oid"}
IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OBJECT_ID = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
REGULAR_INDEX_MODES = frozenset({"100644", "100755"})
DIGEST_DOMAIN = b"VIBE-OFFICIAL-DOCUMENT-STORAGE-SET-v1\0"
CONTROL_DIGEST_DOMAIN = b"VIBE-OFFICIAL-DOCUMENT-LOCAL-CONTROLS-v1\0"
CANONICAL_AUTHORITY_REGISTRY = "registry/official-source-authorities.yaml"
MAX_WORKTREE_ARTIFACT_BYTES = 256 * 1024 * 1024
REQUIRED_NAMESPACES = {
    "qe": (
        "qe",
        "skills/qe-rigorous-calculations/references/official-",
    ),
    "vasp": (
        "vasp",
        "skills/vasp-rigorous-calculations/references/official-",
    ),
    "cp2k": (
        "cp2k",
        "skills/cp2k-rigorous-calculations/references/official-",
    ),
    "siesta": (
        "siesta",
        "skills/siesta-rigorous-calculations/references/official-",
    ),
}
REQUIRED_ARTIFACT_AUTHORITIES = {
    "qe-legacy": ("qe-official-docs", "qe-release-source-docs"),
    "vasp-wiki": ("vasp-official-wiki",),
    "cp2k-manual": ("cp2k-official-manual",),
    "cp2k-source-registry": (
        "cp2k-official-manual",
        "cp2k-release-source-docs",
    ),
    "siesta-portal-registry": ("siesta-official-docs",),
    "siesta-release-derived": ("siesta-release-source-docs",),
}


class StorageAuditError(ValueError):
    """One fail-closed storage-audit input error."""


@dataclass(frozen=True)
class TrackedBlob:
    path: str
    mode: str
    oid: str
    size: int


@dataclass(frozen=True)
class Selector:
    kind: str
    value: str

    def matches(self, path: str) -> bool:
        if self.kind == "exact":
            return path == self.value
        return path.startswith(self.value)


@dataclass(frozen=True)
class Namespace:
    namespace_id: str
    provider_id: str
    path_prefix: str


@dataclass(frozen=True)
class Baseline:
    path_count: int
    byte_count: int
    digest_sha256: str


@dataclass(frozen=True)
class ArtifactRule:
    set_id: str
    provider_id: str
    authority_ids: tuple[str, ...]
    selectors: tuple[Selector, ...]
    baseline: Baseline


@dataclass(frozen=True)
class LocalControl:
    provider_id: str
    path: str
    mode: str
    byte_count: int
    blob_oid: str


@dataclass(frozen=True)
class StorageConfiguration:
    authority_registry: str
    namespaces: tuple[Namespace, ...]
    artifact_sets: tuple[ArtifactRule, ...]
    local_controls: tuple[LocalControl, ...]


@dataclass(frozen=True)
class ArtifactSetResult:
    set_id: str
    provider_id: str
    authority_ids: tuple[str, ...]
    state: str
    path_count: int
    byte_count: int
    digest_sha256: str
    forbidden_path_count: int


@dataclass(frozen=True)
class StorageReport:
    invalid_findings: tuple[str, ...]
    namespace_path_count: int
    artifact_path_count: int
    local_control_count: int
    local_control_bytes: int
    local_control_digest_sha256: str
    artifact_bytes: int
    forbidden_path_count: int
    release_blocking_path_count: int
    artifact_sets: tuple[ArtifactSetResult, ...]
    worktree_drift_findings: tuple[str, ...]


@dataclass(frozen=True)
class WorktreeView:
    blobs: tuple[TrackedBlob, ...]
    invalid_findings: tuple[str, ...]
    drift_findings: tuple[str, ...]


@dataclass(frozen=True)
class StorageMigrationEntry:
    path: str
    classification: str
    owner_id: str
    mode: str
    oid: str
    size: int


@dataclass(frozen=True)
class StorageMigrationSnapshot:
    entries: tuple[StorageMigrationEntry, ...]

    @property
    def artifact_path_count(self) -> int:
        return sum(entry.classification == "artifact" for entry in self.entries)

    @property
    def release_blocking_path_count(self) -> int:
        # Every entry is a legacy namespace artifact outside the canonical
        # v1.1 pack domain and therefore still requires technical migration.
        return self.artifact_path_count


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _safe_repo_path(value: object, location: str, *, prefix: bool) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not value.isprintable()
        or "\\" in value
        or value.startswith("/")
    ):
        raise StorageAuditError(f"{location}: expected a canonical repository path")
    path = PurePosixPath(value)
    canonical_value = value[:-1] if prefix and value.endswith("/") else value
    if (
        path.as_posix() != canonical_value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise StorageAuditError(f"{location}: expected a canonical repository path")
    if prefix and not value.endswith(("/", "-")):
        raise StorageAuditError(
            f"{location}: path prefix must end in '/' or '-'"
        )
    return value


def _identifier(value: object, location: str) -> str:
    if not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None:
        raise StorageAuditError(f"{location}: invalid identifier")
    return value


def _exact_fields(value: object, fields: set[str], location: str) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise StorageAuditError(f"{location}: expected exact fields {sorted(fields)}")
    return value


def _parse_selector(value: object, location: str) -> Selector:
    data = _exact_fields(value, SELECTOR_FIELDS, location)
    kind = data.get("kind")
    if kind not in {"exact", "prefix"}:
        raise StorageAuditError(f"{location}/kind: expected exact or prefix")
    return Selector(
        kind=kind,
        value=_safe_repo_path(
            data.get("value"),
            f"{location}/value",
            prefix=kind == "prefix",
        ),
    )


def _parse_baseline(value: object, location: str) -> Baseline:
    data = _exact_fields(value, BASELINE_FIELDS, location)
    path_count = data.get("path_count")
    byte_count = data.get("byte_count")
    digest = data.get("digest_sha256")
    if not isinstance(path_count, int) or isinstance(path_count, bool) or path_count < 0:
        raise StorageAuditError(
            f"{location}/path_count: expected a nonnegative integer"
        )
    if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
        raise StorageAuditError(f"{location}/byte_count: expected a nonnegative integer")
    if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
        raise StorageAuditError(f"{location}/digest_sha256: expected lowercase SHA-256")
    return Baseline(path_count, byte_count, digest)


def _inside_namespace(
    value: str,
    provider_id: str,
    namespaces: tuple[Namespace, ...],
) -> bool:
    return any(
        namespace.provider_id == provider_id
        and value.startswith(namespace.path_prefix)
        for namespace in namespaces
    )


def _parse_configuration(data: object) -> StorageConfiguration:
    root = _exact_fields(data, TOP_LEVEL_FIELDS, "<root>")
    if root.get("schema_version") != SCHEMA_VERSION:
        raise StorageAuditError(f"schema_version: expected {SCHEMA_VERSION!r}")
    authority_registry = _safe_repo_path(
        root.get("authority_registry"),
        "authority_registry",
        prefix=False,
    )
    if authority_registry != CANONICAL_AUTHORITY_REGISTRY:
        raise StorageAuditError(
            "authority_registry: expected the canonical "
            f"{CANONICAL_AUTHORITY_REGISTRY}"
        )
    if root.get("migration_policy") != MIGRATION_POLICY:
        raise StorageAuditError("migration_policy: unsupported policy")

    namespace_data = root.get("namespaces")
    if not isinstance(namespace_data, dict) or not namespace_data:
        raise StorageAuditError("namespaces: expected a nonempty mapping")
    namespaces: list[Namespace] = []
    for namespace_id, raw in sorted(namespace_data.items()):
        namespace_id = _identifier(namespace_id, "namespaces/<id>")
        item = _exact_fields(raw, NAMESPACE_FIELDS, f"namespaces/{namespace_id}")
        namespaces.append(
            Namespace(
                namespace_id=namespace_id,
                provider_id=_identifier(
                    item.get("provider_id"),
                    f"namespaces/{namespace_id}/provider_id",
                ),
                path_prefix=_safe_repo_path(
                    item.get("path_prefix"),
                    f"namespaces/{namespace_id}/path_prefix",
                    prefix=True,
                ),
            )
        )
    namespace_tuple = tuple(namespaces)
    actual_namespaces = {
        item.namespace_id: (item.provider_id, item.path_prefix)
        for item in namespace_tuple
    }
    if actual_namespaces != REQUIRED_NAMESPACES:
        raise StorageAuditError(
            "namespaces: expected the exact Wave-0 tracked-storage discovery roots"
        )
    if len({item.path_prefix for item in namespace_tuple}) != len(namespace_tuple):
        raise StorageAuditError("namespaces: duplicate path prefixes are forbidden")
    for index, left in enumerate(namespace_tuple):
        for right in namespace_tuple[index + 1 :]:
            if (
                left.path_prefix.startswith(right.path_prefix)
                or right.path_prefix.startswith(left.path_prefix)
            ):
                raise StorageAuditError("namespaces: overlapping prefixes are forbidden")

    artifact_data = root.get("artifact_sets")
    if not isinstance(artifact_data, dict) or not artifact_data:
        raise StorageAuditError("artifact_sets: expected a nonempty mapping")
    artifact_sets: list[ArtifactRule] = []
    for set_id, raw in sorted(artifact_data.items()):
        set_id = _identifier(set_id, "artifact_sets/<id>")
        item = _exact_fields(raw, ARTIFACT_SET_FIELDS, f"artifact_sets/{set_id}")
        provider_id = _identifier(
            item.get("provider_id"),
            f"artifact_sets/{set_id}/provider_id",
        )
        raw_authorities = item.get("authority_ids")
        if (
            not isinstance(raw_authorities, list)
            or not raw_authorities
            or any(
                not isinstance(authority, str)
                or IDENTIFIER.fullmatch(authority) is None
                for authority in raw_authorities
            )
            or len(raw_authorities) != len(set(raw_authorities))
        ):
            raise StorageAuditError(
                f"artifact_sets/{set_id}/authority_ids: expected unique identifiers"
            )
        raw_selectors = item.get("selectors")
        if not isinstance(raw_selectors, list) or not raw_selectors:
            raise StorageAuditError(
                f"artifact_sets/{set_id}/selectors: expected a nonempty list"
            )
        selectors = tuple(
            _parse_selector(
                selector,
                f"artifact_sets/{set_id}/selectors/{index}",
            )
            for index, selector in enumerate(raw_selectors)
        )
        for selector in selectors:
            if not _inside_namespace(selector.value, provider_id, namespace_tuple):
                raise StorageAuditError(
                    f"artifact_sets/{set_id}: selector escapes provider namespace"
                )
        artifact_sets.append(
            ArtifactRule(
                set_id=set_id,
                provider_id=provider_id,
                authority_ids=tuple(raw_authorities),
                selectors=selectors,
                baseline=_parse_baseline(
                    item.get("baseline"),
                    f"artifact_sets/{set_id}/baseline",
                ),
            )
        )
    actual_authorities = {
        rule.set_id: rule.authority_ids for rule in artifact_sets
    }
    if actual_authorities != REQUIRED_ARTIFACT_AUTHORITIES:
        raise StorageAuditError(
            "artifact_sets: expected exact Wave-0 set IDs and authority assignments"
        )

    raw_controls = root.get("local_controls")
    if not isinstance(raw_controls, list):
        raise StorageAuditError("local_controls: expected a list")
    local_controls: list[LocalControl] = []
    for index, raw in enumerate(raw_controls):
        item = _exact_fields(raw, LOCAL_CONTROL_FIELDS, f"local_controls/{index}")
        provider_id = _identifier(
            item.get("provider_id"),
            f"local_controls/{index}/provider_id",
        )
        path = _safe_repo_path(
            item.get("path"),
            f"local_controls/{index}/path",
            prefix=False,
        )
        if not _inside_namespace(path, provider_id, namespace_tuple):
            raise StorageAuditError(
                f"local_controls/{index}: path escapes provider namespace"
            )
        baseline = _exact_fields(
            item.get("baseline"),
            CONTROL_BASELINE_FIELDS,
            f"local_controls/{index}/baseline",
        )
        mode = baseline.get("mode")
        byte_count = baseline.get("byte_count")
        blob_oid = baseline.get("blob_oid")
        if mode not in REGULAR_INDEX_MODES:
            raise StorageAuditError(
                f"local_controls/{index}/baseline/mode: expected a regular mode"
            )
        if (
            not isinstance(byte_count, int)
            or isinstance(byte_count, bool)
            or byte_count < 0
        ):
            raise StorageAuditError(
                f"local_controls/{index}/baseline/byte_count: "
                "expected a nonnegative integer"
            )
        if not isinstance(blob_oid, str) or OBJECT_ID.fullmatch(blob_oid) is None:
            raise StorageAuditError(
                f"local_controls/{index}/baseline/blob_oid: invalid Git object ID"
            )
        local_controls.append(
            LocalControl(provider_id, path, mode, byte_count, blob_oid)
        )
    if len({item.path for item in local_controls}) != len(local_controls):
        raise StorageAuditError("local_controls: duplicate paths are forbidden")

    configuration = StorageConfiguration(
        authority_registry=authority_registry,
        namespaces=namespace_tuple,
        artifact_sets=tuple(artifact_sets),
        local_controls=tuple(local_controls),
    )
    # A configuration collision is invalid even if no current blob exercises it.
    all_selectors = [
        (rule.set_id, selector)
        for rule in configuration.artifact_sets
        for selector in rule.selectors
    ]
    for control in configuration.local_controls:
        matches = [
            set_id for set_id, selector in all_selectors if selector.matches(control.path)
        ]
        if matches:
            raise StorageAuditError(
                f"local control {control.path}: also selected by artifact set(s) "
                + ", ".join(sorted(matches))
            )
    for index, (left_id, left) in enumerate(all_selectors):
        for right_id, right in all_selectors[index + 1 :]:
            if left_id == right_id:
                continue
            if left.kind == right.kind == "exact":
                overlap = left.value == right.value
            elif left.kind == right.kind == "prefix":
                overlap = (
                    left.value.startswith(right.value)
                    or right.value.startswith(left.value)
                )
            elif left.kind == "prefix":
                overlap = right.value.startswith(left.value)
            else:
                overlap = left.value.startswith(right.value)
            if overlap:
                raise StorageAuditError(
                    f"artifact selectors for {left_id} and {right_id} overlap"
                )
    return configuration


def load_configuration(root: Path) -> StorageConfiguration:
    path = root / CONFIGURATION_PATH
    try:
        data = load_yaml_strict(path, CONFIGURATION_PATH.name)
    except (OSError, RegistryYAMLError, ValueError) as exc:
        raise StorageAuditError(
            f"storage discovery configuration is unreadable or invalid ({exc})"
        ) from exc
    return _parse_configuration(data)


def configuration_validation_errors(data: object) -> list[str]:
    """Validate the canonical storage-discovery registry without I/O."""

    try:
        _parse_configuration(data)
    except StorageAuditError as exc:
        return [str(exc)]
    return []


def load_authority_projection(
    root: Path,
    configuration: StorageConfiguration | None = None,
) -> dict[str, dict]:
    selected = configuration or load_configuration(root)
    registry_path = root.joinpath(*PurePosixPath(selected.authority_registry).parts)
    try:
        authority_data = load_yaml_strict(
            registry_path,
            "official-source-authorities.yaml",
        )
        software_data = load_yaml_strict(
            root / "registry" / "software-registry.yaml",
            "software-registry.yaml",
        )
        return official_source_authorities.active_authority_technical_snapshot(
            authority_data,
            software_data=software_data,
            source_root=root,
        )
    except (OSError, RegistryYAMLError, ValueError) as exc:
        raise StorageAuditError(
            f"official-source authority projection is invalid ({exc})"
        ) from exc


def _git(root: Path, arguments: list[str], *, stdin: bytes | None = None) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise StorageAuditError(
            f"Git index inspection failed ({exc.__class__.__name__})"
        ) from exc
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise StorageAuditError(
            f"Git index inspection failed ({message or 'nonzero exit'})"
        )
    return completed.stdout


def load_git_index(root: Path) -> tuple[TrackedBlob, ...]:
    raw = _git(root, ["ls-files", "--stage", "-z"])
    records: list[tuple[str, str, str]] = []
    for index, record in enumerate(raw.split(b"\0")):
        if not record:
            continue
        try:
            header, raw_path = record.split(b"\t", 1)
            mode_bytes, oid_bytes, stage_bytes = header.split(b" ", 2)
            mode = mode_bytes.decode("ascii")
            oid = oid_bytes.decode("ascii")
            stage = stage_bytes.decode("ascii")
            path = raw_path.decode("utf-8", errors="strict")
        except (ValueError, UnicodeError) as exc:
            raise StorageAuditError(
                f"Git index record {index}: malformed or non-UTF-8"
            ) from exc
        if stage != "0":
            raise StorageAuditError(f"Git index path {path}: unmerged stage {stage}")
        if (
            not path
            or not path.isprintable()
            or PurePosixPath(path).as_posix() != path
            or path.startswith("/")
            or any(part in {"", ".", ".."} for part in PurePosixPath(path).parts)
        ):
            raise StorageAuditError(f"Git index record {index}: unsafe path")
        if OBJECT_ID.fullmatch(oid) is None:
            raise StorageAuditError(f"Git index path {path}: invalid object ID")
        records.append((path, mode, oid))
    if not records:
        raise StorageAuditError("Git index is empty")

    unique_oids = sorted({oid for _, _, oid in records})
    query = b"".join(oid.encode("ascii") + b"\n" for oid in unique_oids)
    raw_objects = _git(
        root,
        ["cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        stdin=query,
    )
    sizes: dict[str, int] = {}
    lines = raw_objects.splitlines()
    if len(lines) != len(unique_oids):
        raise StorageAuditError("Git object inspection returned an incomplete response")
    for line in lines:
        try:
            oid_bytes, kind_bytes, size_bytes = line.split(b" ", 2)
            oid = oid_bytes.decode("ascii")
            kind = kind_bytes.decode("ascii")
            size = int(size_bytes.decode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise StorageAuditError("Git object inspection returned malformed data") from exc
        if oid not in unique_oids or kind != "blob" or size < 0:
            raise StorageAuditError("Git index references a non-blob or invalid object")
        sizes[oid] = size
    if set(sizes) != set(unique_oids):
        raise StorageAuditError("Git object inspection did not resolve every object")
    return tuple(
        TrackedBlob(path=path, mode=mode, oid=oid, size=sizes[oid])
        for path, mode, oid in records
    )


def _digest(
    blobs: Iterable[TrackedBlob],
    *,
    domain: bytes = DIGEST_DOMAIN,
) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    for blob in sorted(blobs, key=lambda item: item.path):
        for value in (
            blob.path.encode("utf-8"),
            blob.mode.encode("ascii"),
            blob.oid.encode("ascii"),
        ):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
        digest.update(blob.size.to_bytes(8, "big"))
    return digest.hexdigest()


def _is_canonical_pack_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    bundle_parts = official_document_bundles.BUNDLE_DIRECTORY.parts
    return (
        len(parts) > 2 + len(bundle_parts)
        and parts[0] == "skills"
        and IDENTIFIER.fullmatch(parts[1]) is not None
        and parts[2 : 2 + len(bundle_parts)] == bundle_parts
    )


def _worktree_blob(
    root: Path,
    relative: str,
    *,
    object_format: str,
) -> TrackedBlob:
    path = root.joinpath(*PurePosixPath(relative).parts)
    current = root
    try:
        for part in PurePosixPath(relative).parts[:-1]:
            current = current / part
            parent_stat = current.lstat()
            if stat.S_ISLNK(parent_stat.st_mode) or not stat.S_ISDIR(
                parent_stat.st_mode
            ):
                raise StorageAuditError(
                    f"{relative}: worktree ancestor is aliased or unsafe"
                )
        before_path = path.lstat()
        if (
            not stat.S_ISREG(before_path.st_mode)
            or before_path.st_nlink != 1
            or before_path.st_size > MAX_WORKTREE_ARTIFACT_BYTES
        ):
            raise StorageAuditError(
                f"{relative}: worktree path is aliased, unsafe, or oversized"
            )
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
    except FileNotFoundError as exc:
        raise StorageAuditError(f"{relative}: tracked worktree path was deleted") from exc
    except OSError as exc:
        raise StorageAuditError(
            f"{relative}: worktree path is unavailable or unsafe "
            f"({exc.__class__.__name__})"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or (before.st_dev, before.st_ino)
            != (before_path.st_dev, before_path.st_ino)
        ):
            raise StorageAuditError(
                f"{relative}: worktree path is aliased or unsafe"
            )
        try:
            digest = hashlib.new(object_format)
        except ValueError as exc:
            raise StorageAuditError(
                f"unsupported Git object format {object_format!r}"
            ) from exc
        digest.update(f"blob {before.st_size}\0".encode("ascii"))
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after_path = path.lstat()
    except OSError as exc:
        raise StorageAuditError(
            f"{relative}: worktree path changed while it was read"
        ) from exc
    identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    if (
        identity
        != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        or identity
        != (
            after_path.st_dev,
            after_path.st_ino,
            after_path.st_size,
            after_path.st_mtime_ns,
        )
        or after.st_nlink != 1
        or after_path.st_nlink != 1
        or total != before.st_size
    ):
        raise StorageAuditError(
            f"{relative}: worktree path changed while it was read"
        )
    mode = "100755" if before.st_mode & 0o111 else "100644"
    return TrackedBlob(
        path=relative,
        mode=mode,
        oid=digest.hexdigest(),
        size=total,
    )


def _worktree_namespace_candidates(
    root: Path,
    configuration: StorageConfiguration,
) -> tuple[set[str], list[str]]:
    candidates: set[str] = set()
    findings: list[str] = []

    def walk_error(error: OSError) -> None:
        findings.append(
            "worktree namespace is unreadable "
            f"({error.__class__.__name__})"
        )

    roots = {
        namespace.path_prefix.rsplit("/", 1)[0]
        for namespace in configuration.namespaces
    }
    for relative_root in sorted(roots):
        absolute_root = root.joinpath(*PurePosixPath(relative_root).parts)
        try:
            root_stat = absolute_root.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            findings.append(
                f"{relative_root}: worktree namespace is unreadable "
                f"({exc.__class__.__name__})"
            )
            continue
        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
            findings.append(f"{relative_root}: worktree namespace root is unsafe")
            continue
        for directory, directory_names, filenames in os.walk(
            absolute_root,
            topdown=True,
            followlinks=False,
            onerror=walk_error,
        ):
            current = Path(directory)
            retained: list[str] = []
            for name in sorted(directory_names):
                child = current / name
                relative = child.relative_to(root).as_posix()
                if _is_canonical_pack_path(relative + "/record"):
                    continue
                try:
                    child_stat = child.lstat()
                except OSError as exc:
                    findings.append(
                        f"{relative}: worktree path is unreadable "
                        f"({exc.__class__.__name__})"
                    )
                    continue
                if stat.S_ISLNK(child_stat.st_mode):
                    if any(
                        relative.startswith(namespace.path_prefix)
                        for namespace in configuration.namespaces
                    ):
                        candidates.add(relative)
                    continue
                retained.append(name)
            directory_names[:] = retained
            for name in sorted(filenames):
                child = current / name
                relative = child.relative_to(root).as_posix()
                if _is_canonical_pack_path(relative):
                    continue
                if any(
                    relative.startswith(namespace.path_prefix)
                    for namespace in configuration.namespaces
                ):
                    candidates.add(relative)
    return candidates, findings


def load_worktree_view(
    root: Path,
    index_blobs: tuple[TrackedBlob, ...],
    configuration: StorageConfiguration,
) -> WorktreeView:
    index_by_path = {
        blob.path: blob
        for blob in index_blobs
        if not _is_canonical_pack_path(blob.path)
        and any(
            blob.path.startswith(namespace.path_prefix)
            for namespace in configuration.namespaces
        )
    }
    object_lengths = {len(blob.oid) for blob in index_by_path.values()}
    if object_lengths - {40, 64} or len(object_lengths) > 1:
        return WorktreeView(
            blobs=(),
            invalid_findings=("Git index uses an unsupported mixed object format",),
            drift_findings=(),
        )
    object_format = "sha256" if object_lengths == {64} else "sha1"
    discovered, findings = _worktree_namespace_candidates(root, configuration)
    all_paths = set(index_by_path) | discovered
    worktree_blobs: list[TrackedBlob] = []
    drift: list[str] = []
    for relative in sorted(all_paths):
        tracked = index_by_path.get(relative)
        if tracked is None:
            findings.append(
                f"{relative}: untracked official-document namespace path"
            )
        try:
            current = _worktree_blob(
                root,
                relative,
                object_format=object_format,
            )
        except StorageAuditError as exc:
            if tracked is not None and "was deleted" in str(exc):
                drift.append(
                    f"{relative}: tracked path was deleted from the worktree"
                )
            else:
                findings.append(str(exc))
            continue
        worktree_blobs.append(current)
        if tracked is not None and (
            current.mode,
            current.oid,
            current.size,
        ) != (
            tracked.mode,
            tracked.oid,
            tracked.size,
        ):
            drift.append(
                f"{relative}: worktree identity differs from the Git index"
            )
    return WorktreeView(
        blobs=tuple(worktree_blobs),
        invalid_findings=tuple(sorted(set(findings))),
        drift_findings=tuple(sorted(set(drift))),
    )


def _resolve_commit(root: Path, baseline_ref: str) -> str:
    if (
        not isinstance(baseline_ref, str)
        or not baseline_ref
        or not baseline_ref.isprintable()
        or baseline_ref.startswith("-")
    ):
        raise StorageAuditError("baseline ref is empty or unsafe")
    raw = _git(root, ["rev-parse", "--verify", f"{baseline_ref}^{{commit}}"])
    try:
        commit = raw.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise StorageAuditError("baseline commit identity is invalid") from exc
    if re.fullmatch(r"[a-f0-9]{40}(?:[a-f0-9]{24})?", commit) is None:
        raise StorageAuditError("baseline commit identity is invalid")
    return commit


def _tree_blobs(root: Path, commit: str) -> tuple[TrackedBlob, ...]:
    raw = _git(root, ["ls-tree", "-r", "-z", "--full-tree", commit])
    records: list[tuple[str, str, str]] = []
    for index, record in enumerate(raw.split(b"\0")):
        if not record:
            continue
        try:
            header, raw_path = record.split(b"\t", 1)
            mode_bytes, kind_bytes, oid_bytes = header.split(b" ", 2)
            mode = mode_bytes.decode("ascii")
            kind = kind_bytes.decode("ascii")
            oid = oid_bytes.decode("ascii")
            path = raw_path.decode("utf-8", errors="strict")
        except (ValueError, UnicodeError) as exc:
            raise StorageAuditError(
                f"baseline tree record {index}: malformed or non-UTF-8"
            ) from exc
        if kind != "blob":
            continue
        if (
            not path
            or not path.isprintable()
            or PurePosixPath(path).as_posix() != path
            or path.startswith("/")
            or any(part in {"", ".", ".."} for part in PurePosixPath(path).parts)
            or OBJECT_ID.fullmatch(oid) is None
        ):
            raise StorageAuditError(f"baseline tree record {index}: unsafe identity")
        records.append((path, mode, oid))
    unique_oids = sorted({oid for _, _, oid in records})
    query = b"".join(oid.encode("ascii") + b"\n" for oid in unique_oids)
    raw_objects = _git(
        root,
        ["cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        stdin=query,
    )
    sizes: dict[str, int] = {}
    for line in raw_objects.splitlines():
        try:
            oid_bytes, kind_bytes, size_bytes = line.split(b" ", 2)
            oid = oid_bytes.decode("ascii")
            kind = kind_bytes.decode("ascii")
            size = int(size_bytes.decode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise StorageAuditError(
                "baseline object inspection returned malformed data"
            ) from exc
        if oid not in unique_oids or kind != "blob" or size < 0:
            raise StorageAuditError(
                "baseline tree references a non-blob or invalid object"
            )
        sizes[oid] = size
    if set(sizes) != set(unique_oids):
        raise StorageAuditError(
            "baseline object inspection did not resolve every object"
        )
    return tuple(
        TrackedBlob(path=path, mode=mode, oid=oid, size=sizes[oid])
        for path, mode, oid in records
    )


def _baseline_configuration(
    root: Path,
    tree_blobs: tuple[TrackedBlob, ...],
    current: StorageConfiguration,
) -> tuple[StorageConfiguration, bool]:
    relative = CONFIGURATION_PATH.as_posix()
    configuration_blob = next(
        (blob for blob in tree_blobs if blob.path == relative),
        None,
    )
    if configuration_blob is None:
        # Bootstrap for the first reviewed commit that introduces this registry.
        # Classification roots and authority assignments are still exact,
        # hard-coded Wave-0 invariants in _parse_configuration.
        return current, True
    raw = _git(root, ["cat-file", "blob", configuration_blob.oid])
    try:
        data = loads_yaml_bytes_strict(
            raw,
            "baseline official-document-storage-discovery.yaml",
        )
    except RegistryYAMLError as exc:
        raise StorageAuditError(
            f"baseline storage configuration is invalid ({exc})"
        ) from exc
    return _parse_configuration(data), False


def _migration_snapshot(
    blobs: tuple[TrackedBlob, ...],
    configuration: StorageConfiguration,
) -> StorageMigrationSnapshot:
    controls = {control.path: control for control in configuration.local_controls}
    entries: list[StorageMigrationEntry] = []
    failures: list[str] = []
    for blob in sorted(blobs, key=lambda item: item.path):
        if _is_canonical_pack_path(blob.path):
            continue
        namespaces = [
            namespace
            for namespace in configuration.namespaces
            if blob.path.startswith(namespace.path_prefix)
        ]
        if not namespaces:
            continue
        if len(namespaces) != 1:
            failures.append(f"{blob.path}: ambiguous storage namespace")
            continue
        rules = [
            rule
            for rule in configuration.artifact_sets
            if any(selector.matches(blob.path) for selector in rule.selectors)
        ]
        control = controls.get(blob.path)
        if len(rules) + int(control is not None) != 1:
            failures.append(
                f"{blob.path}: storage migration path is unclassified or ambiguous"
            )
            continue
        if control is not None:
            classification = "control"
            owner_id = control.provider_id
        else:
            classification = "artifact"
            owner_id = rules[0].set_id
        entries.append(
            StorageMigrationEntry(
                path=blob.path,
                classification=classification,
                owner_id=owner_id,
                mode=blob.mode,
                oid=blob.oid,
                size=blob.size,
            )
        )
    if failures:
        raise StorageAuditError("; ".join(sorted(set(failures))))
    return StorageMigrationSnapshot(entries=tuple(entries))


def migration_snapshots(
    root: Path,
    baseline_ref: str,
) -> tuple[StorageMigrationSnapshot, StorageMigrationSnapshot]:
    selected_root = Path(root).resolve()
    current_configuration = load_configuration(selected_root)
    commit = _resolve_commit(selected_root, baseline_ref)
    baseline_blobs = _tree_blobs(selected_root, commit)
    baseline_configuration, bootstrap = _baseline_configuration(
        selected_root,
        baseline_blobs,
        current_configuration,
    )
    index_blobs = load_git_index(selected_root)
    worktree = load_worktree_view(
        selected_root,
        index_blobs,
        current_configuration,
    )
    if worktree.invalid_findings:
        raise StorageAuditError("; ".join(worktree.invalid_findings))
    current_snapshot = _migration_snapshot(
        worktree.blobs,
        current_configuration,
    )
    if bootstrap:
        # The first reviewed registry commit establishes the exact candidate
        # inventory.  There is no prior storage policy registry to compare;
        # current exact-state validation remains mandatory.  Every later
        # commit has a real baseline and is delete-only.
        return current_snapshot, current_snapshot
    return (
        _migration_snapshot(baseline_blobs, baseline_configuration),
        current_snapshot,
    )


def validate_migration_delta(root: Path, baseline_ref: str) -> tuple[str, ...]:
    try:
        baseline, current = migration_snapshots(root, baseline_ref)
    except StorageAuditError as exc:
        return (str(exc),)
    before = {entry.path: entry for entry in baseline.entries}
    after = {entry.path: entry for entry in current.entries}
    findings: list[str] = []

    baseline_artifacts = {
        path: entry
        for path, entry in before.items()
        if entry.classification == "artifact"
    }
    current_artifacts = {
        path: entry
        for path, entry in after.items()
        if entry.classification == "artifact"
    }
    for path in sorted(set(current_artifacts) - set(baseline_artifacts)):
        findings.append(
            f"{path}: legacy official-document artifact addition or restoration "
            "is forbidden"
        )
    for path in sorted(set(current_artifacts) & set(baseline_artifacts)):
        old = baseline_artifacts[path]
        new = current_artifacts[path]
        if (
            old.mode,
            old.oid,
            old.size,
        ) != (
            new.mode,
            new.oid,
            new.size,
        ):
            findings.append(
                f"{path}: legacy artifact content or mode rewrite is forbidden"
            )
        if old.owner_id != new.owner_id:
            findings.append(
                f"{path}: legacy artifact-set reclassification is forbidden"
            )

    baseline_controls = {
        path: entry
        for path, entry in before.items()
        if entry.classification == "control"
    }
    current_controls = {
        path: entry
        for path, entry in after.items()
        if entry.classification == "control"
    }
    for path in sorted(set(baseline_controls) | set(current_controls)):
        old = baseline_controls.get(path)
        new = current_controls.get(path)
        if old is None or new is None:
            findings.append(
                f"{path}: local-control addition, deletion, or reclassification "
                "is forbidden"
            )
            continue
        if (
            old.mode,
            old.oid,
            old.size,
            old.owner_id,
        ) != (
            new.mode,
            new.oid,
            new.size,
            new.owner_id,
        ):
            findings.append(
                f"{path}: local-control identity or classification rewrite "
                "is forbidden"
            )

    # A baseline path cannot move across the artifact/control boundary while
    # masquerading as an allowed artifact deletion.
    for path in sorted(set(before) & set(after)):
        if before[path].classification != after[path].classification:
            findings.append(
                f"{path}: artifact/control reclassification is forbidden"
            )
    return tuple(sorted(set(findings)))


def evaluate_storage(
    blobs: tuple[TrackedBlob, ...],
    configuration: StorageConfiguration,
    authorities: dict[str, dict],
    *,
    enforce_baseline: bool,
) -> StorageReport:
    findings: list[str] = []
    path_occurrences: dict[str, int] = {}
    for blob in blobs:
        path_occurrences[blob.path] = path_occurrences.get(blob.path, 0) + 1
    for path, count in sorted(path_occurrences.items()):
        if count != 1:
            findings.append(f"{path}: duplicate tracked-blob records are forbidden")
    namespace_paths: dict[str, Namespace] = {}
    for blob in blobs:
        if _is_canonical_pack_path(blob.path):
            continue
        matches = [
            namespace
            for namespace in configuration.namespaces
            if blob.path.startswith(namespace.path_prefix)
        ]
        if len(matches) > 1:
            findings.append(f"{blob.path}: matches multiple storage namespaces")
        elif matches:
            namespace_paths[blob.path] = matches[0]
            if blob.mode not in REGULAR_INDEX_MODES:
                findings.append(
                    f"{blob.path}: namespace entries must be regular Git blobs"
                )
            if not isinstance(blob.size, int) or isinstance(blob.size, bool) or blob.size < 0:
                findings.append(f"{blob.path}: invalid blob size")
            if OBJECT_ID.fullmatch(blob.oid) is None:
                findings.append(f"{blob.path}: invalid object ID")

    controls = {control.path: control for control in configuration.local_controls}
    blobs_by_path = {blob.path: blob for blob in blobs}
    assignments: dict[str, list[ArtifactRule]] = {}
    control_paths: set[str] = set()
    for path, namespace in sorted(namespace_paths.items()):
        matched_sets = [
            rule
            for rule in configuration.artifact_sets
            if any(selector.matches(path) for selector in rule.selectors)
        ]
        is_control = path in controls
        if is_control and controls[path].provider_id != namespace.provider_id:
            findings.append(f"{path}: local-control provider does not match namespace")
        if len(matched_sets) + int(is_control) != 1:
            if not matched_sets and not is_control:
                findings.append(f"{path}: unclassified official-document namespace path")
            else:
                findings.append(f"{path}: classified more than once")
            continue
        if is_control:
            control_paths.add(path)
        else:
            assignments[path] = matched_sets

    if enforce_baseline:
        missing_controls = sorted(set(controls) - control_paths)
        findings.extend(
            f"{path}: registered local control is missing from the Git index"
            for path in missing_controls
        )
        for path in sorted(control_paths):
            control = controls[path]
            blob = blobs_by_path[path]
            if (
                blob.mode,
                blob.size,
                blob.oid,
            ) != (
                control.mode,
                control.byte_count,
                control.blob_oid,
            ):
                findings.append(
                    f"{path}: local control identity does not match "
                    "its exact baseline"
                )

    results: list[ArtifactSetResult] = []
    all_artifact_paths: set[str] = set()
    legacy_migration_paths: set[str] = set()
    for rule in configuration.artifact_sets:
        selected_paths = sorted(
            path
            for path, matches in assignments.items()
            if rule in matches
        )
        selected = tuple(
            blob
            for blob in blobs
            if blob.path in selected_paths
        )
        all_artifact_paths.update(selected_paths)
        legacy_migration_paths.update(selected_paths)
        for authority_id in rule.authority_ids:
            authority = authorities.get(authority_id)
            if not isinstance(authority, dict):
                findings.append(
                    f"artifact set {rule.set_id}: unknown active authority {authority_id}"
                )
                continue
            if authority.get("provider_id") != rule.provider_id:
                findings.append(
                    f"artifact set {rule.set_id}: authority {authority_id} provider "
                    "does not match artifact provider"
                )
        state = "legacy-technical-migration-required"

        byte_count = sum(blob.size for blob in selected)
        digest = _digest(selected)
        if enforce_baseline:
            actual = (len(selected), byte_count, digest)
            expected = (
                rule.baseline.path_count,
                rule.baseline.byte_count,
                rule.baseline.digest_sha256,
            )
            if actual != expected:
                findings.append(
                    f"artifact set {rule.set_id}: exact configured baseline mismatch "
                    f"(paths={actual[0]}, bytes={actual[1]}, digest={actual[2]})"
                )
        results.append(
            ArtifactSetResult(
                set_id=rule.set_id,
                provider_id=rule.provider_id,
                authority_ids=rule.authority_ids,
                state=state,
                path_count=len(selected),
                byte_count=byte_count,
                digest_sha256=digest,
                forbidden_path_count=len(selected),
            )
        )

    # Preserve deterministic diagnostics without repeating the same malformed
    # path for every downstream count.
    findings = sorted(set(findings))
    control_blobs = tuple(
        blob for blob in blobs if blob.path in control_paths
    )
    return StorageReport(
        invalid_findings=tuple(findings),
        namespace_path_count=len(namespace_paths),
        artifact_path_count=len(all_artifact_paths),
        local_control_count=len(control_paths),
        local_control_bytes=sum(blob.size for blob in control_blobs),
        local_control_digest_sha256=_digest(
            control_blobs,
            domain=CONTROL_DIGEST_DOMAIN,
        ),
        artifact_bytes=sum(
            blob.size for blob in blobs if blob.path in all_artifact_paths
        ),
        forbidden_path_count=len(legacy_migration_paths),
        release_blocking_path_count=len(legacy_migration_paths),
        artifact_sets=tuple(results),
        worktree_drift_findings=(),
    )


def exit_code(report: StorageReport, *, strict_release: bool) -> int:
    if report.invalid_findings:
        return 2
    if strict_release and report.worktree_drift_findings:
        return 3
    if strict_release and report.release_blocking_path_count:
        return 3
    return 0


def _invalid_report(message: str) -> StorageReport:
    return StorageReport(
        invalid_findings=(message,),
        namespace_path_count=0,
        artifact_path_count=0,
        local_control_count=0,
        local_control_bytes=0,
        local_control_digest_sha256=_digest(
            (),
            domain=CONTROL_DIGEST_DOMAIN,
        ),
        artifact_bytes=0,
        forbidden_path_count=0,
        release_blocking_path_count=0,
        artifact_sets=(),
        worktree_drift_findings=(),
    )


def audit_git_index(root: Path) -> StorageReport:
    try:
        configuration = load_configuration(root)
        authorities = load_authority_projection(root, configuration)
        blobs = load_git_index(root)
        return evaluate_storage(
            blobs,
            configuration,
            authorities,
            enforce_baseline=True,
        )
    except StorageAuditError as exc:
        return _invalid_report(str(exc))


def audit_repository(root: Path) -> StorageReport:
    try:
        configuration = load_configuration(root)
        authorities = load_authority_projection(root, configuration)
        index_blobs = load_git_index(root)
        worktree = load_worktree_view(root, index_blobs, configuration)
        report = evaluate_storage(
            worktree.blobs,
            configuration,
            authorities,
            enforce_baseline=True,
        )
        return replace(
            report,
            invalid_findings=tuple(
                sorted(
                    set(report.invalid_findings)
                    | set(worktree.invalid_findings)
                )
            ),
            worktree_drift_findings=worktree.drift_findings,
        )
    except StorageAuditError as exc:
        return _invalid_report(str(exc))


def emit_report(report: StorageReport, *, stream=sys.stdout) -> None:
    for result in report.artifact_sets:
        authorities = ",".join(result.authority_ids)
        print(
            "OFFICIAL_DOCUMENT_STORAGE "
            f"set={result.set_id} provider={result.provider_id} "
            f"state={result.state} authorities={authorities} "
            f"paths={result.path_count} bytes={result.byte_count} "
            f"digest={result.digest_sha256}",
            file=stream,
        )
    for finding in report.invalid_findings:
        safe = "".join(
            character if character.isprintable() else "?"
            for character in finding
        )
        print(f"OFFICIAL_DOCUMENT_STORAGE_INVALID {safe}", file=stream)
    for finding in report.worktree_drift_findings:
        safe = "".join(
            character if character.isprintable() else "?"
            for character in finding
        )
        print(f"OFFICIAL_DOCUMENT_STORAGE_WORKTREE_DRIFT {safe}", file=stream)
    print(
        "OFFICIAL_DOCUMENT_STORAGE_SUMMARY "
        f"namespace_paths={report.namespace_path_count} "
        f"artifact_paths={report.artifact_path_count} "
        f"local_controls={report.local_control_count} "
        f"local_control_bytes={report.local_control_bytes} "
        f"local_control_digest={report.local_control_digest_sha256} "
        f"artifact_bytes={report.artifact_bytes} "
        f"forbidden_paths={report.forbidden_path_count} "
        f"release_blocking_paths={report.release_blocking_path_count} "
        f"invalid={len(report.invalid_findings)} "
        f"worktree_drift={len(report.worktree_drift_findings)}",
        file=stream,
    )


def run_audit(
    root: Path,
    *,
    strict_release: bool,
    baseline_ref: str | None = None,
) -> int:
    report = audit_repository(root)
    emit_report(report)
    if baseline_ref is not None:
        findings = validate_migration_delta(Path(root).resolve(), baseline_ref)
        if findings:
            for finding in findings:
                safe = "".join(
                    character if character.isprintable() else "?"
                    for character in finding
                )
                print(
                    "ERROR OFFICIAL_DOCUMENT_STORAGE_MIGRATION_NON_MONOTONIC "
                    + safe,
                    file=sys.stderr,
                )
            return 2
        print(
            "OFFICIAL_DOCUMENT_STORAGE_MIGRATION PASS: "
            "legacy tracked storage changed monotonically"
        )
    return exit_code(report, strict_release=strict_release)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument("--strict-release", action="store_true")
    parser.add_argument(
        "--baseline-ref",
        help=(
            "Git commit/ref used to enforce delete-only legacy artifact "
            "migration and immutable local controls"
        ),
    )
    args = parser.parse_args(argv)
    return run_audit(
        args.root.resolve(),
        strict_release=args.strict_release,
        baseline_ref=args.baseline_ref,
    )


if __name__ == "__main__":
    raise SystemExit(main())
