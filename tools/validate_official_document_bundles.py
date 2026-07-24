#!/usr/bin/env python3
"""Discover and validate per-Skill official-document coverage bundles.

Every source-backed Skill has one canonical discovery location:

``skills/<skill-id>/references/official-source-pack/bundle.json``.

The entrypoint is a small repository-local registration record.  It identifies
every contract record passed to ``validate_official_document_coverage.py``;
no unregistered or path-only supporting files are permitted in the pack.  This
module treats that semantic validator as a black-box CLI rather than
reimplementing the four official-document technical contracts. Discovery
additionally checks the scope/coverage ``skill_id`` binding to prevent cross-
Skill replay.
It is not the portable immutable ``bundle-manifest@1.0`` format.

Normal audit mode reports missing or semantically partial bundles without
preventing development validation.  Invalid packs always fail.
``--strict-release`` additionally blocks every missing or partial bundle.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from typing import Iterable

from registry_yaml import (
    RegistryYAMLError,
    load_yaml_strict,
    loads_yaml_bytes_strict,
)
import strict_json


BUNDLE_DIRECTORY = PurePosixPath("references", "official-source-pack")
BUNDLE_ENTRYPOINT = "bundle.json"
BUNDLE_TYPE = "official-document-coverage"
SCHEMA_VERSION = "1.0"
MAX_INDEX_BYTES = 1024 * 1024
VALIDATOR_TIMEOUT_SECONDS = 120
MAX_RECORD_BYTES = 64 * 1024 * 1024
SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_LIFECYCLES = frozenset({"active", "development"})
LIFECYCLES = frozenset({*SOURCE_LIFECYCLES, "planned"})
RECORD_FIELDS = frozenset(
    {
        "corpora",
        "slice_manifests",
        "scope_inventory",
        "coverage",
    }
)
INDEX_FIELDS = frozenset(
    {
        "bundle_type",
        "schema_version",
        "skill_id",
        "records",
    }
)
STATE_ORDER = ("complete", "partial", "missing", "invalid")
EXPECTATIONS = frozenset({"legacy-missing", "pack-required"})
MIGRATION_POLICY = {
    "temporary": True,
    "removal_condition": "replace-with-pack-required-when-first-pack-is-added",
    "downgrade_policy": "forbidden",
}


class BundleAuditError(ValueError):
    """One stable discovery or registration failure."""


@dataclass(frozen=True)
class SourceSkill:
    skill_id: str
    relative_path: PurePosixPath
    absolute_path: Path


@dataclass(frozen=True)
class BundleRegistration:
    skill_id: str
    pack_path: Path
    corpora: tuple[Path, ...]
    slice_manifests: tuple[Path, ...]
    scope_inventory: Path
    coverage: Path


@dataclass(frozen=True)
class BundleResult:
    skill_id: str
    state: str
    entrypoint: str
    message: str


@dataclass(frozen=True)
class AuditReport:
    results: tuple[BundleResult, ...]

    @property
    def counts(self) -> dict[str, int]:
        return {
            state: sum(result.state == state for result in self.results)
            for state in STATE_ORDER
        }


@dataclass(frozen=True)
class MigrationSnapshot:
    source_skill_ids: frozenset[str]
    expectations: dict[str, str] | None
    pack_skill_ids: frozenset[str]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _safe_relative_path(value: object, location: str) -> PurePosixPath:
    if (
        not isinstance(value, str)
        or not value
        or not value.isprintable()
        or "\\" in value
    ):
        raise BundleAuditError(f"{location}: expected a canonical relative POSIX path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise BundleAuditError(f"{location}: expected a canonical relative POSIX path")
    if path == PurePosixPath(BUNDLE_ENTRYPOINT):
        raise BundleAuditError(f"{location}: bundle.json cannot register itself")
    return path


def _require_safe_directory_chain(root: Path, path: Path, label: str) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise BundleAuditError(f"{label} escapes the repository root") from exc
    current = root
    try:
        root_stat = current.lstat()
    except OSError as exc:
        raise BundleAuditError(
            f"{label} root is unreadable ({exc.__class__.__name__})"
        ) from exc
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise BundleAuditError(f"{label} root is aliased or unsafe")
    for part in relative.parts:
        current = current / part
        try:
            current_stat = current.lstat()
        except OSError as exc:
            raise BundleAuditError(
                f"{label} is missing or unreadable ({exc.__class__.__name__})"
            ) from exc
        if stat.S_ISLNK(current_stat.st_mode) or not stat.S_ISDIR(current_stat.st_mode):
            raise BundleAuditError(f"{label} is aliased or unsafe")


def _load_source_skills(root: Path) -> tuple[SourceSkill, ...]:
    registry_path = root / "registry" / "skill-registry.yaml"
    try:
        data = load_yaml_strict(registry_path, "skill-registry.yaml")
    except (OSError, RegistryYAMLError) as exc:
        raise BundleAuditError(f"Skill registry is unreadable or invalid ({exc})") from exc
    if data.get("schema_version") != "1.0":
        raise BundleAuditError("Skill registry schema_version must be '1.0'")
    skills = data.get("skills")
    if not isinstance(skills, dict) or not skills:
        raise BundleAuditError("Skill registry must contain a nonempty skills mapping")
    if any(not isinstance(skill_id, str) for skill_id in skills):
        raise BundleAuditError("Skill registry contains an invalid Skill identifier")

    source_skills: list[SourceSkill] = []
    resolved_paths: set[Path] = set()
    for skill_id in sorted(skills):
        specification = skills[skill_id]
        if not isinstance(skill_id, str) or not SKILL_ID.fullmatch(skill_id):
            raise BundleAuditError("Skill registry contains an invalid Skill identifier")
        if not isinstance(specification, dict):
            raise BundleAuditError(f"{skill_id}: Skill registry entry must be a mapping")
        lifecycle = specification.get("lifecycle")
        path_value = specification.get("path")
        if not isinstance(lifecycle, str) or lifecycle not in LIFECYCLES:
            raise BundleAuditError(
                f"{skill_id}: Skill registry lifecycle is unsupported"
            )
        if lifecycle not in SOURCE_LIFECYCLES:
            if path_value is not None:
                raise BundleAuditError(
                    f"{skill_id}: non-source-backed lifecycle must use path: null"
                )
            continue
        expected = PurePosixPath("skills", skill_id)
        if path_value != expected.as_posix():
            raise BundleAuditError(
                f"{skill_id}: source-backed Skill path must be {expected.as_posix()}"
            )
        absolute = root.joinpath(*expected.parts)
        _require_safe_directory_chain(root, absolute, f"{skill_id}: registered Skill source")
        resolved = absolute.resolve()
        if resolved in resolved_paths:
            raise BundleAuditError("multiple Skill records resolve to one source directory")
        resolved_paths.add(resolved)
        source_skills.append(
            SourceSkill(
                skill_id=skill_id,
                relative_path=expected,
                absolute_path=absolute,
            )
        )
    if not source_skills:
        raise BundleAuditError("Skill registry contains no source-backed Skills")
    return tuple(source_skills)


def _load_expectations(
    root: Path,
    source_skills: tuple[SourceSkill, ...],
) -> dict[str, str]:
    path = root / "registry" / "official-document-bundle-expectations.yaml"
    try:
        data = load_yaml_strict(
            path,
            "official-document-bundle-expectations.yaml",
        )
    except (OSError, RegistryYAMLError) as exc:
        raise BundleAuditError(
            f"bundle expectation registry is unreadable or invalid ({exc})"
        ) from exc
    expected_fields = {"schema_version", "migration_policy", "skills"}
    if set(data) != expected_fields or data.get("schema_version") != "1.0":
        raise BundleAuditError(
            "bundle expectation registry has unsupported top-level fields"
        )
    if data.get("migration_policy") != MIGRATION_POLICY:
        raise BundleAuditError(
            "bundle expectation registry migration policy is unsupported"
        )
    specifications = data.get("skills")
    if not isinstance(specifications, dict):
        raise BundleAuditError(
            "bundle expectation registry must contain a skills mapping"
        )
    expected_ids = {skill.skill_id for skill in source_skills}
    if set(specifications) != expected_ids:
        raise BundleAuditError(
            "bundle expectation Skill IDs must exactly match source-backed Skills"
        )
    expectations: dict[str, str] = {}
    for skill in source_skills:
        specification = specifications[skill.skill_id]
        if not isinstance(specification, dict) or set(specification) != {
            "expectation",
            "entrypoint",
        }:
            raise BundleAuditError(
                f"{skill.skill_id}: bundle expectation entry is malformed"
            )
        expectation = specification.get("expectation")
        if not isinstance(expectation, str) or expectation not in EXPECTATIONS:
            raise BundleAuditError(
                f"{skill.skill_id}: bundle expectation is unsupported"
            )
        expected_entrypoint = (
            skill.relative_path
            / BUNDLE_DIRECTORY
            / BUNDLE_ENTRYPOINT
        ).as_posix()
        if specification.get("entrypoint") != expected_entrypoint:
            raise BundleAuditError(
                f"{skill.skill_id}: bundle expectation entrypoint is noncanonical"
            )
        expectations[skill.skill_id] = expectation
    return expectations


def _source_skill_paths_from_data(data: object) -> dict[str, PurePosixPath]:
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        raise BundleAuditError("baseline Skill registry schema is invalid")
    skills = data.get("skills")
    if not isinstance(skills, dict) or not skills:
        raise BundleAuditError("baseline Skill registry has no skills mapping")
    if any(not isinstance(skill_id, str) for skill_id in skills):
        raise BundleAuditError("baseline Skill registry has an invalid Skill identifier")
    result: dict[str, PurePosixPath] = {}
    for skill_id in sorted(skills):
        specification = skills[skill_id]
        if not SKILL_ID.fullmatch(skill_id) or not isinstance(specification, dict):
            raise BundleAuditError("baseline Skill registry entry is malformed")
        lifecycle = specification.get("lifecycle")
        path_value = specification.get("path")
        if not isinstance(lifecycle, str) or lifecycle not in LIFECYCLES:
            raise BundleAuditError(
                f"{skill_id}: baseline Skill lifecycle is unsupported"
            )
        if lifecycle not in SOURCE_LIFECYCLES:
            if path_value is not None:
                raise BundleAuditError(
                    f"{skill_id}: baseline planned Skill must use path: null"
                )
            continue
        expected = PurePosixPath("skills", skill_id)
        if path_value != expected.as_posix():
            raise BundleAuditError(
                f"{skill_id}: baseline source path is noncanonical"
            )
        result[skill_id] = expected
    if not result:
        raise BundleAuditError("baseline has no source-backed Skills")
    return result


def _expectations_from_data(
    data: object,
    source_paths: dict[str, PurePosixPath],
) -> dict[str, str]:
    if not isinstance(data, dict):
        raise BundleAuditError("baseline expectation registry is malformed")
    if set(data) != {"schema_version", "migration_policy", "skills"}:
        raise BundleAuditError(
            "baseline expectation registry has unsupported top-level fields"
        )
    if data.get("schema_version") != "1.0" or data.get("migration_policy") != MIGRATION_POLICY:
        raise BundleAuditError("baseline expectation registry policy is invalid")
    specifications = data.get("skills")
    if not isinstance(specifications, dict) or set(specifications) != set(source_paths):
        raise BundleAuditError(
            "baseline expectation IDs do not match source-backed Skills"
        )
    result: dict[str, str] = {}
    for skill_id, relative_path in source_paths.items():
        specification = specifications[skill_id]
        if not isinstance(specification, dict) or set(specification) != {
            "expectation",
            "entrypoint",
        }:
            raise BundleAuditError(
                f"{skill_id}: baseline expectation entry is malformed"
            )
        expectation = specification.get("expectation")
        if not isinstance(expectation, str) or expectation not in EXPECTATIONS:
            raise BundleAuditError(
                f"{skill_id}: baseline expectation is unsupported"
            )
        expected_entrypoint = (
            relative_path / BUNDLE_DIRECTORY / BUNDLE_ENTRYPOINT
        ).as_posix()
        if specification.get("entrypoint") != expected_entrypoint:
            raise BundleAuditError(
                f"{skill_id}: baseline expectation entrypoint is noncanonical"
            )
        result[skill_id] = expectation
    return result


def expectation_registry_validation_errors(
    expectation_data: object,
    skill_data: object,
) -> list[str]:
    """Validate expectation data against the canonical source-backed Skill set."""

    try:
        source_paths = _source_skill_paths_from_data(skill_data)
        _expectations_from_data(expectation_data, source_paths)
    except BundleAuditError as exc:
        return [str(exc)]
    return []


def _registered_path_list(value: object, location: str) -> tuple[PurePosixPath, ...]:
    if not isinstance(value, list) or not value:
        raise BundleAuditError(f"{location}: expected a nonempty list")
    paths = tuple(
        _safe_relative_path(item, f"{location}/{index}")
        for index, item in enumerate(value)
    )
    if len(paths) != len(set(paths)):
        raise BundleAuditError(f"{location}: duplicate registered paths are forbidden")
    return paths


def _single_registered_path(value: object, location: str) -> PurePosixPath:
    return _safe_relative_path(value, location)


def _pack_inventory(pack: Path) -> frozenset[PurePosixPath]:
    inventory: set[PurePosixPath] = set()
    seen_inodes: set[tuple[int, int]] = set()
    def fail_walk(error: OSError) -> None:
        raise BundleAuditError(
            f"pack directory is unreadable ({error.__class__.__name__})"
        ) from error

    for directory, directory_names, filenames in os.walk(
        pack,
        topdown=True,
        onerror=fail_walk,
        followlinks=False,
    ):
        current = Path(directory)
        retained: list[str] = []
        for name in sorted(directory_names):
            child = current / name
            try:
                child_stat = child.lstat()
            except OSError as exc:
                raise BundleAuditError(f"pack entry is unreadable: {name} ({exc.__class__.__name__})") from exc
            relative = child.relative_to(pack).as_posix()
            if stat.S_ISLNK(child_stat.st_mode) or not stat.S_ISDIR(child_stat.st_mode):
                raise BundleAuditError(f"pack directory is aliased or unsafe: {relative}")
            retained.append(name)
        directory_names[:] = retained
        for name in sorted(filenames):
            child = current / name
            try:
                child_stat = child.lstat()
            except OSError as exc:
                raise BundleAuditError(f"pack file is unreadable: {name} ({exc.__class__.__name__})") from exc
            relative = child.relative_to(pack)
            if stat.S_ISLNK(child_stat.st_mode) or not stat.S_ISREG(child_stat.st_mode):
                raise BundleAuditError(f"pack file is aliased or unsafe: {relative.as_posix()}")
            inode = (child_stat.st_dev, child_stat.st_ino)
            if child_stat.st_nlink > 1 or inode in seen_inodes:
                raise BundleAuditError(f"pack file is hard-linked: {relative.as_posix()}")
            seen_inodes.add(inode)
            inventory.add(PurePosixPath(relative.as_posix()))
    return frozenset(inventory)


def _load_registration(skill: SourceSkill, pack: Path) -> BundleRegistration:
    entrypoint = pack / BUNDLE_ENTRYPOINT
    inventory = _pack_inventory(pack)
    try:
        index = strict_json.load_object(
            entrypoint,
            f"{skill.skill_id}/{BUNDLE_ENTRYPOINT}",
            max_bytes=MAX_INDEX_BYTES,
        )
    except (OSError, strict_json.StrictJSONError) as exc:
        raise BundleAuditError(f"bundle registration is malformed or unsafe ({exc})") from exc
    if _pack_inventory(pack) != inventory:
        raise BundleAuditError("pack inventory changed while registration was read")
    if set(index) != INDEX_FIELDS:
        raise BundleAuditError(
            "bundle registration must contain exactly "
            f"{sorted(INDEX_FIELDS)}"
        )
    if index.get("bundle_type") != BUNDLE_TYPE:
        raise BundleAuditError(f"bundle_type must be {BUNDLE_TYPE!r}")
    if index.get("schema_version") != SCHEMA_VERSION:
        raise BundleAuditError(f"schema_version must be {SCHEMA_VERSION!r}")
    if index.get("skill_id") != skill.skill_id:
        raise BundleAuditError("bundle skill_id does not match the registered Skill")
    records = index.get("records")
    if not isinstance(records, dict) or set(records) != RECORD_FIELDS:
        raise BundleAuditError(
            f"records must contain exactly {sorted(RECORD_FIELDS)}"
        )

    corpora = _registered_path_list(records["corpora"], "records/corpora")
    slices = _registered_path_list(
        records["slice_manifests"],
        "records/slice_manifests",
    )
    scope = _single_registered_path(
        records["scope_inventory"],
        "records/scope_inventory",
    )
    coverage = _single_registered_path(records["coverage"], "records/coverage")
    registered = (*corpora, *slices, scope, coverage)
    if len(registered) != len(set(registered)):
        raise BundleAuditError("one pack path is registered more than once")

    expected_inventory = frozenset({PurePosixPath(BUNDLE_ENTRYPOINT), *registered})
    missing = sorted(expected_inventory - inventory, key=PurePosixPath.as_posix)
    if missing:
        raise BundleAuditError(
            "registered file is missing: "
            + ", ".join(path.as_posix() for path in missing)
        )
    unregistered = sorted(inventory - expected_inventory, key=PurePosixPath.as_posix)
    if unregistered:
        raise BundleAuditError(
            "pack contains unregistered file: "
            + ", ".join(path.as_posix() for path in unregistered)
        )

    def absolute(path: PurePosixPath) -> Path:
        return pack.joinpath(*path.parts)

    registration = BundleRegistration(
        skill_id=skill.skill_id,
        pack_path=pack,
        corpora=tuple(absolute(path) for path in corpora),
        slice_manifests=tuple(absolute(path) for path in slices),
        scope_inventory=absolute(scope),
        coverage=absolute(coverage),
    )
    _validate_record_skill_identity(registration)
    return registration


def _validate_record_skill_identity(registration: BundleRegistration) -> None:
    for label, path in (
        ("scope inventory", registration.scope_inventory),
        ("coverage", registration.coverage),
    ):
        try:
            before = path.lstat()
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
            ):
                raise BundleAuditError(f"{label} record is aliased or unsafe")
            record = strict_json.load_object(path, f"{registration.skill_id}/{label}")
            after = path.lstat()
        except (OSError, strict_json.StrictJSONError) as exc:
            raise BundleAuditError(
                f"{label} record is malformed or unsafe ({exc})"
            ) from exc
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
        ) or after.st_nlink != 1:
            raise BundleAuditError(f"{label} record changed while it was read")
        if record.get("skill_id") != registration.skill_id:
            raise BundleAuditError(
                f"{label} skill_id does not match the registered Skill"
            )


def _relative_display(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _argument_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _command_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _validator_command(
    registration: BundleRegistration,
    *,
    root: Path,
    validator_path: Path,
    python_executable: str,
) -> tuple[str, ...]:
    command: list[str] = [
        python_executable,
        _command_path(validator_path, root),
    ]
    for path in registration.corpora:
        command.extend(("--corpus", _argument_path(path, root)))
    for path in registration.slice_manifests:
        command.extend(("--slices", _argument_path(path, root)))
    command.extend(
        (
            "--scope-inventory",
            _argument_path(registration.scope_inventory, root),
            "--coverage",
            _argument_path(registration.coverage, root),
            "--source-root",
            ".",
            "--enforce-canonical-pack-closure",
        )
    )
    return tuple(command)


def _read_stable_record(path: Path, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        before_path = path.lstat()
        descriptor = os.open(path, flags)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or (before.st_dev, before.st_ino)
            != (before_path.st_dev, before_path.st_ino)
            or before.st_size > MAX_RECORD_BYTES
        ):
            raise BundleAuditError(f"{label} record is aliased, unsafe, or oversized")
        chunks: list[bytes] = []
        remaining = MAX_RECORD_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        after_path = path.lstat()
    except OSError as exc:
        raise BundleAuditError(
            f"{label} record is unavailable or unsafe ({exc.__class__.__name__})"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(raw) > MAX_RECORD_BYTES:
        raise BundleAuditError(f"{label} record is oversized")
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
        or len(raw) != before.st_size
    ):
        raise BundleAuditError(f"{label} record changed while it was read")
    return raw


def _record_paths(
    registration: BundleRegistration,
) -> tuple[tuple[str, Path], ...]:
    return (
        *tuple(
            (f"corpus/{index}", path)
            for index, path in enumerate(registration.corpora)
        ),
        *tuple(
            (f"slice/{index}", path)
            for index, path in enumerate(registration.slice_manifests)
        ),
        ("scope", registration.scope_inventory),
        ("coverage", registration.coverage),
    )


@contextmanager
def _immutable_record_snapshot(
    registration: BundleRegistration,
) -> Iterable[tuple[BundleRegistration, dict[Path, str]]]:
    originals = _record_paths(registration)
    raw_records = [
        (label, path, _read_stable_record(path, label))
        for label, path in originals
    ]
    expected_hashes = {
        path: hashlib.sha256(raw).hexdigest()
        for _, path, raw in raw_records
    }
    with tempfile.TemporaryDirectory(prefix="official-doc-bundle-") as directory:
        snapshot_root = Path(directory)
        snapshot_paths: dict[str, list[Path]] = {
            "corpus": [],
            "slice": [],
        }
        singles: dict[str, Path] = {}
        for label, _, raw in raw_records:
            family, _, raw_index = label.partition("/")
            suffix = f"-{int(raw_index):04d}" if raw_index else ""
            snapshot_path = snapshot_root / f"{family}{suffix}.json"
            try:
                descriptor = os.open(
                    snapshot_path,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                )
                try:
                    view = memoryview(raw)
                    while view:
                        written = os.write(descriptor, view)
                        if written <= 0:
                            raise OSError("short snapshot write")
                        view = view[written:]
                finally:
                    os.close(descriptor)
            except OSError as exc:
                raise BundleAuditError(
                    f"immutable validator snapshot failed ({exc.__class__.__name__})"
                ) from exc
            if family in snapshot_paths:
                snapshot_paths[family].append(snapshot_path)
            else:
                singles[family] = snapshot_path
        yield (
            BundleRegistration(
                skill_id=registration.skill_id,
                pack_path=snapshot_root,
                corpora=tuple(snapshot_paths["corpus"]),
                slice_manifests=tuple(snapshot_paths["slice"]),
                scope_inventory=singles["scope"],
                coverage=singles["coverage"],
            ),
            expected_hashes,
        )


def _records_match_snapshot(expected_hashes: dict[Path, str]) -> None:
    for path, expected in expected_hashes.items():
        actual = hashlib.sha256(
            _read_stable_record(path, _relative_display(path, path.parent))
        ).hexdigest()
        if actual != expected:
            raise BundleAuditError("pack record changed during semantic validation")


def _diagnostic_excerpt(stderr: str, stdout: str, *, root: Path) -> str:
    """Return bounded validator findings without echoing arbitrary process output."""

    candidates: list[str] = []
    root_spellings = {str(root), str(root.resolve())}
    for raw_line in (*stderr.splitlines(), *stdout.splitlines()):
        line = raw_line.strip()
        if not line.startswith(("ERROR ", "BLOCKED:")):
            continue
        for spelling in root_spellings:
            if spelling:
                line = line.replace(spelling, ".")
        line = "".join(character if character.isprintable() else "?" for character in line)
        candidates.append(line[:400])
        if len(candidates) == 3:
            break
    if not candidates:
        return ""
    return "; validator: " + " | ".join(candidates)


def _run_validator(
    registration: BundleRegistration,
    *,
    root: Path,
    validator_path: Path,
    python_executable: str,
) -> tuple[str, str]:
    if validator_path.is_symlink() or not validator_path.is_file():
        return "invalid", "official-document semantic validator is missing or unsafe"
    try:
        inventory = _pack_inventory(registration.pack_path)
    except BundleAuditError as exc:
        return "invalid", str(exc)
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        with _immutable_record_snapshot(registration) as (
            snapshot,
            expected_hashes,
        ):
            command = _validator_command(
                snapshot,
                root=root,
                validator_path=validator_path,
                python_executable=python_executable,
            )
            completed = subprocess.run(
                command,
                cwd=root,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                check=False,
                timeout=VALIDATOR_TIMEOUT_SECONDS,
            )
            _records_match_snapshot(expected_hashes)
        if _pack_inventory(registration.pack_path) != inventory:
            raise BundleAuditError("pack inventory changed during semantic validation")
    except BundleAuditError as exc:
        return "invalid", str(exc)
    except (OSError, subprocess.SubprocessError) as exc:
        return "invalid", f"semantic validator could not run ({exc.__class__.__name__})"
    try:
        _validate_record_skill_identity(registration)
    except BundleAuditError as exc:
        return "invalid", str(exc)
    if completed.returncode == 0:
        return "complete", "black-box semantic validator accepted complete coverage"
    diagnostic = _diagnostic_excerpt(
        completed.stderr,
        completed.stdout,
        root=root,
    )
    if completed.returncode == 3:
        return (
            "partial",
            "bundle is semantically valid but incomplete; strict release blocker"
            + diagnostic,
        )
    return (
        "invalid",
        f"black-box semantic validator rejected the bundle (exit {completed.returncode})"
        + diagnostic,
    )


def _orphan_pack_results(
    root: Path,
    source_skills: Iterable[SourceSkill],
) -> list[BundleResult]:
    registered = {skill.skill_id for skill in source_skills}
    skills_root = root / "skills"
    if skills_root.is_symlink() or not skills_root.is_dir():
        return []
    results: list[BundleResult] = []
    for candidate in sorted(skills_root.iterdir(), key=lambda path: path.name):
        pack = candidate.joinpath(*BUNDLE_DIRECTORY.parts)
        if candidate.name in registered or not (pack.exists() or pack.is_symlink()):
            continue
        results.append(
            BundleResult(
                skill_id=candidate.name,
                state="invalid",
                entrypoint=_relative_display(pack / BUNDLE_ENTRYPOINT, root),
                message="official-source pack has no source-backed Skill registry record",
            )
        )
    return results


def migration_delta_findings(
    baseline: MigrationSnapshot,
    current: MigrationSnapshot,
) -> tuple[str, ...]:
    findings: list[str] = []
    removed = sorted(baseline.source_skill_ids - current.source_skill_ids)
    if removed:
        findings.append(
            "source-backed Skills cannot disappear during bundle migration: "
            + ", ".join(removed)
        )
    added = sorted(current.source_skill_ids - baseline.source_skill_ids)
    if baseline.expectations is None and added:
        findings.append(
            "the expectation-ledger bootstrap cannot add source-backed Skills: "
            + ", ".join(added)
        )
    current_expectations = current.expectations or {}
    for skill_id in added:
        if (
            current_expectations.get(skill_id) != "pack-required"
            or skill_id not in current.pack_skill_ids
        ):
            findings.append(
                f"{skill_id}: a new source-backed Skill requires pack-required "
                "and a tracked pack entrypoint"
            )

    if baseline.expectations is None:
        for skill_id in sorted(
            baseline.source_skill_ids & current.source_skill_ids
        ):
            if (
                skill_id in baseline.pack_skill_ids
                and (
                    current_expectations.get(skill_id) != "pack-required"
                    or skill_id not in current.pack_skill_ids
                )
            ):
                findings.append(
                    f"{skill_id}: a pre-ledger pack cannot disappear or become optional"
                )
        return tuple(findings)

    for skill_id in sorted(baseline.source_skill_ids & current.source_skill_ids):
        before = baseline.expectations[skill_id]
        after = current_expectations.get(skill_id)
        if before == "pack-required" and after != "pack-required":
            findings.append(
                f"{skill_id}: pack-required cannot downgrade to legacy-missing"
            )
        elif before == "legacy-missing" and after not in {
            "legacy-missing",
            "pack-required",
        }:
            findings.append(
                f"{skill_id}: unsupported migration transition {before!r} -> {after!r}"
            )
        if skill_id in baseline.pack_skill_ids and skill_id not in current.pack_skill_ids:
            findings.append(f"{skill_id}: a baseline pack entrypoint was deleted")
        if after == "pack-required" and skill_id not in current.pack_skill_ids:
            findings.append(f"{skill_id}: pack-required has no current pack entrypoint")
    return tuple(findings)


def _git_run(
    root: Path,
    arguments: tuple[str, ...],
    *,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ("git", "-C", str(root), *arguments),
            input=input_bytes,
            stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BundleAuditError(
            f"Git baseline query failed ({exc.__class__.__name__})"
        ) from exc


def _resolve_baseline_commit(root: Path, baseline_ref: str) -> str:
    if (
        not isinstance(baseline_ref, str)
        or not baseline_ref
        or not baseline_ref.isprintable()
        or baseline_ref.startswith("-")
    ):
        raise BundleAuditError("baseline ref is empty or unsafe")
    completed = _git_run(
        root,
        ("rev-parse", "--verify", f"{baseline_ref}^{{commit}}"),
    )
    if completed.returncode != 0:
        raise BundleAuditError("baseline ref does not resolve to a commit")
    try:
        commit = completed.stdout.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise BundleAuditError("baseline commit identity is invalid") from exc
    if re.fullmatch(r"[a-f0-9]{40,64}", commit) is None:
        raise BundleAuditError("baseline commit identity is invalid")
    return commit


def _git_blob(root: Path, commit: str, path: str, *, required: bool) -> bytes | None:
    object_name = f"{commit}:{path}"
    exists = _git_run(root, ("cat-file", "-e", object_name))
    if exists.returncode != 0:
        if required:
            raise BundleAuditError(f"baseline is missing required {path}")
        return None
    completed = _git_run(root, ("cat-file", "blob", object_name))
    if completed.returncode != 0:
        raise BundleAuditError(f"baseline {path} cannot be read")
    return completed.stdout


def _baseline_snapshot(root: Path, baseline_ref: str) -> MigrationSnapshot:
    commit = _resolve_baseline_commit(root, baseline_ref)
    skill_raw = _git_blob(
        root,
        commit,
        "registry/skill-registry.yaml",
        required=True,
    )
    assert skill_raw is not None
    try:
        skill_data = loads_yaml_bytes_strict(skill_raw, "baseline skill-registry.yaml")
    except RegistryYAMLError as exc:
        raise BundleAuditError(f"baseline Skill registry is invalid ({exc})") from exc
    source_paths = _source_skill_paths_from_data(skill_data)
    expectation_raw = _git_blob(
        root,
        commit,
        "registry/official-document-bundle-expectations.yaml",
        required=False,
    )
    expectations: dict[str, str] | None = None
    if expectation_raw is not None:
        try:
            expectation_data = loads_yaml_bytes_strict(
                expectation_raw,
                "baseline bundle expectations",
            )
        except RegistryYAMLError as exc:
            raise BundleAuditError(
                f"baseline expectation registry is invalid ({exc})"
            ) from exc
        expectations = _expectations_from_data(expectation_data, source_paths)
    packs = {
        skill_id
        for skill_id, source_path in source_paths.items()
        if _git_blob(
            root,
            commit,
            (source_path / BUNDLE_DIRECTORY / BUNDLE_ENTRYPOINT).as_posix(),
            required=False,
        )
        is not None
    }
    if expectations is not None:
        for skill_id, expectation in expectations.items():
            if expectation == "pack-required" and skill_id not in packs:
                raise BundleAuditError(
                    f"baseline {skill_id} is pack-required without a pack"
                )
            if expectation == "legacy-missing" and skill_id in packs:
                raise BundleAuditError(
                    f"baseline {skill_id} has a pack hidden by legacy-missing"
                )
    return MigrationSnapshot(
        source_skill_ids=frozenset(source_paths),
        expectations=expectations,
        pack_skill_ids=frozenset(packs),
    )


def _current_snapshot(root: Path) -> MigrationSnapshot:
    source_skills = _load_source_skills(root)
    expectations = _load_expectations(root, source_skills)
    packs = {
        skill.skill_id
        for skill in source_skills
        if (
            skill.absolute_path
            / BUNDLE_DIRECTORY
            / BUNDLE_ENTRYPOINT
        ).is_file()
    }
    return MigrationSnapshot(
        source_skill_ids=frozenset(skill.skill_id for skill in source_skills),
        expectations=expectations,
        pack_skill_ids=frozenset(packs),
    )


def validate_migration_delta(root: Path, baseline_ref: str) -> tuple[str, ...]:
    try:
        baseline = _baseline_snapshot(root, baseline_ref)
        current = _current_snapshot(root)
    except BundleAuditError as exc:
        return (str(exc),)
    return migration_delta_findings(baseline, current)


def audit_repository(
    root: Path,
    *,
    validator_path: Path | None = None,
    python_executable: str = sys.executable,
) -> AuditReport:
    """Discover all source-backed Skills and audit their fixed bundle entrypoints."""

    try:
        selected_root = Path(root).resolve(strict=True)
    except OSError as exc:
        return AuditReport(
            results=(
                BundleResult(
                    skill_id="<registry>",
                    state="invalid",
                    entrypoint="registry/skill-registry.yaml",
                    message=f"repository root is unavailable ({exc.__class__.__name__})",
                ),
            )
        )
    try:
        source_skills = _load_source_skills(selected_root)
        expectations = _load_expectations(selected_root, source_skills)
    except BundleAuditError as exc:
        return AuditReport(
            results=(
                BundleResult(
                    skill_id="<registry>",
                    state="invalid",
                    entrypoint="registry/skill-registry.yaml",
                    message=str(exc),
                ),
            )
        )
    selected_validator = validator_path or (
        selected_root / "tools" / "validate_official_document_coverage.py"
    )
    results: list[BundleResult] = _orphan_pack_results(selected_root, source_skills)
    for skill in source_skills:
        expectation = expectations[skill.skill_id]
        references = skill.absolute_path / "references"
        pack = skill.absolute_path.joinpath(*BUNDLE_DIRECTORY.parts)
        entrypoint = pack / BUNDLE_ENTRYPOINT
        display = _relative_display(entrypoint, selected_root)
        if references.exists() or references.is_symlink():
            try:
                _require_safe_directory_chain(
                    selected_root,
                    references,
                    f"{skill.skill_id}: references directory",
                )
            except BundleAuditError as exc:
                results.append(
                    BundleResult(
                        skill_id=skill.skill_id,
                        state="invalid",
                        entrypoint=display,
                        message=str(exc),
                    )
                )
                continue
        if not (pack.exists() or pack.is_symlink()):
            state = "invalid" if expectation == "pack-required" else "missing"
            message = (
                f"required pack is missing at {display}"
                if expectation == "pack-required"
                else (
                    f"source-backed Skill has no {display}; "
                    "strict release blocker"
                )
            )
            results.append(
                BundleResult(
                    skill_id=skill.skill_id,
                    state=state,
                    entrypoint=display,
                    message=message,
                )
            )
            continue
        if expectation != "pack-required":
            results.append(
                BundleResult(
                    skill_id=skill.skill_id,
                    state="invalid",
                    entrypoint=display,
                    message=(
                        "pack exists but migration expectation must be changed "
                        "to pack-required in the same change"
                    ),
                )
            )
            continue
        try:
            _require_safe_directory_chain(
                selected_root,
                pack,
                f"{skill.skill_id}: official-source pack directory",
            )
        except BundleAuditError as exc:
            results.append(
                BundleResult(
                    skill_id=skill.skill_id,
                    state="invalid",
                    entrypoint=display,
                    message=str(exc),
                )
            )
            continue
        if not (entrypoint.exists() or entrypoint.is_symlink()):
            results.append(
                BundleResult(
                    skill_id=skill.skill_id,
                    state="invalid",
                    entrypoint=display,
                    message="official-source pack exists without its bundle registration entry",
                )
            )
            continue
        try:
            registration = _load_registration(skill, pack)
        except BundleAuditError as exc:
            results.append(
                BundleResult(
                    skill_id=skill.skill_id,
                    state="invalid",
                    entrypoint=display,
                    message=str(exc),
                )
            )
            continue
        state, message = _run_validator(
            registration,
            root=selected_root,
            validator_path=selected_validator,
            python_executable=python_executable,
        )
        results.append(
            BundleResult(
                skill_id=skill.skill_id,
                state=state,
                entrypoint=display,
                message=message,
            )
        )
    return AuditReport(results=tuple(sorted(results, key=lambda result: result.skill_id)))


def exit_code(report: AuditReport, *, strict_release: bool) -> int:
    counts = report.counts
    if counts["invalid"]:
        return 2
    if strict_release and (counts["missing"] or counts["partial"]):
        return 3
    return 0


def _safe_log_text(value: str) -> str:
    return "".join(character if character.isprintable() else "?" for character in value)


def emit_report(report: AuditReport, *, stream: object = sys.stdout) -> None:
    for result in report.results:
        print(
            f"OFFICIAL_DOC_BUNDLE {_safe_log_text(result.state).upper()} "
            f"{_safe_log_text(result.skill_id)}: {_safe_log_text(result.message)}",
            file=stream,
        )
    counts = report.counts
    print(
        "OFFICIAL_DOC_BUNDLE SUMMARY "
        + " ".join(f"{state}={counts[state]}" for state in STATE_ORDER),
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
                print(
                    "ERROR OFFICIAL_DOC_MIGRATION_NON_MONOTONIC "
                    + _safe_log_text(finding),
                    file=sys.stderr,
                )
            return 2
        print("OFFICIAL_DOC_MIGRATION PASS: baseline transition is monotonic")
    return exit_code(report, strict_release=strict_release)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=repo_root(),
        help="repository root (default: root containing this tool)",
    )
    parser.add_argument(
        "--strict-release",
        action="store_true",
        help="fail with exit 3 when any source-backed Skill is missing or partial",
    )
    parser.add_argument(
        "--baseline-ref",
        help=(
            "Git commit/ref used to enforce one-way expectation and pack "
            "migration"
        ),
    )
    args = parser.parse_args(argv)
    return run_audit(
        args.root,
        strict_release=args.strict_release,
        baseline_ref=args.baseline_ref,
    )


if __name__ == "__main__":
    raise SystemExit(main())
