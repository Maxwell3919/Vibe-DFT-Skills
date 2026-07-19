#!/usr/bin/env python3
"""Load and validate active, development, and planned Vibe-DFT Skills."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any

import yaml

from registry_yaml import load_yaml_strict


SCHEMA_VERSION = "1.0"
SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INTERFACE_ID = re.compile(r"^[a-z][a-z0-9-]*@[1-9][0-9]*\.[0-9]+$")
CATALOG_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
KINDS = {
    "orchestration",
    "structure",
    "calculation",
    "postprocess",
    "execution",
    "advisory",
    "reporting",
    "scientific-workflow",
}
LIFECYCLES = {"active", "development", "planned"}
SIDE_EFFECTS = (
    "read-only",
    "network-read",
    "local-write",
    "local-execution",
    "remote-read",
    "remote-write",
    "scheduler-submit",
    "scheduler-control",
    "external-publish",
    "destructive-delete",
)
ACTIVATION_CHECK_IDS = (
    "identity-and-routing",
    "primary-source-provenance",
    "capability-boundary",
    "deterministic-gates",
    "lineage-and-hashes",
    "scientific-gate-separation",
    "shared-interfaces",
    "side-effect-boundary",
    "idempotency-recovery-cancel",
    "validation-evidence",
    "privacy-and-license",
    "portability-and-environment",
    "maintenance-and-forward-test",
)
ACTIVATION_REQUIREMENT_FIELDS = {
    "software_profiles",
    "interface_ids",
    "activation_check_ids",
    "task_catalog_ids",
}
TREE_HASH_DOMAIN = b"VIBE-DFT-SKILL-SOURCE-TREE-v1\0"
_COPY_SUFFIX = re.compile(
    r"^.+? (?:(?:[2-9]|[1-9][0-9])|copy(?: (?:[2-9]|[1-9][0-9]))?|"
    r"副本(?: (?:[2-9]|[1-9][0-9]))?|\((?:[1-9]|[1-9][0-9])\))(?:\.[^./]+)*$",
    re.IGNORECASE,
)
_CACHE_DIRECTORIES = {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
_CACHE_FILES = {".coverage", ".DS_Store"}
_BYTECODE_SUFFIXES = {".pyc", ".pyo", ".pyd"}


@dataclass(frozen=True)
class SourceFileDigest:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class SourceTreeDigest:
    sha256: str
    files: tuple[SourceFileDigest, ...]


def _length_prefix(payload: bytes) -> bytes:
    return len(payload).to_bytes(8, byteorder="big", signed=False) + payload


def source_tree_digest(path: Path) -> SourceTreeDigest:
    """Hash every regular file using relative POSIX paths and raw bytes."""

    if path.is_symlink():
        raise ValueError("source tree root must not be a symlink")
    try:
        root_stat = path.stat()
    except OSError as exc:
        raise ValueError(f"source tree is unreadable: {exc}") from exc
    if not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError("source tree root must be a directory")

    candidates: list[Path] = []
    for directory, child_directories, filenames in os.walk(path, topdown=True, followlinks=False):
        current = Path(directory)
        retained_directories: list[str] = []
        for name in sorted(child_directories):
            child = current / name
            try:
                mode = child.lstat().st_mode
            except OSError as exc:
                raise ValueError(f"source tree entry is unreadable: {child.name}: {exc}") from exc
            if stat.S_ISLNK(mode):
                raise ValueError(f"source tree contains a symlink: {child.relative_to(path).as_posix()}")
            if not stat.S_ISDIR(mode):
                raise ValueError(f"source tree contains a special entry: {child.relative_to(path).as_posix()}")
            if name not in _CACHE_DIRECTORIES:
                retained_directories.append(name)
        child_directories[:] = retained_directories
        for name in sorted(filenames):
            candidate = current / name
            if name in _CACHE_FILES or candidate.suffix.lower() in _BYTECODE_SUFFIXES:
                continue
            candidates.append(candidate)

    tree_digest = hashlib.sha256()
    tree_digest.update(TREE_HASH_DOMAIN)
    manifest: list[SourceFileDigest] = []
    seen_inodes: set[tuple[int, int]] = set()
    for candidate in sorted(candidates, key=lambda item: item.relative_to(path).as_posix()):
        relative = candidate.relative_to(path).as_posix()
        try:
            file_stat = candidate.lstat()
        except OSError as exc:
            raise ValueError(f"source tree entry is unreadable: {relative}: {exc}") from exc
        mode = file_stat.st_mode
        if stat.S_ISLNK(mode):
            raise ValueError(f"source tree contains a symlink: {relative}")
        if not stat.S_ISREG(mode):
            raise ValueError(f"source tree contains a special entry: {relative}")
        inode = (file_stat.st_dev, file_stat.st_ino)
        if file_stat.st_nlink > 1 or inode in seen_inodes:
            raise ValueError(f"source tree contains a hard-linked file: {relative}")
        seen_inodes.add(inode)
        try:
            raw = candidate.read_bytes()
        except OSError as exc:
            raise ValueError(f"source tree file is unreadable: {relative}: {exc}") from exc
        path_bytes = relative.encode("utf-8")
        tree_digest.update(_length_prefix(path_bytes))
        tree_digest.update(_length_prefix(raw))
        manifest.append(
            SourceFileDigest(path=relative, size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        )
    if not manifest:
        raise ValueError("source tree contains no regular files")
    return SourceTreeDigest(sha256=tree_digest.hexdigest(), files=tuple(manifest))


def source_tree_inventory_errors(path: Path) -> list[str]:
    """Report copy-like candidate source paths; generated caches are not source."""

    failures: list[str] = []
    for directory, child_directories, filenames in os.walk(path, topdown=True, followlinks=False):
        current = Path(directory)
        for name in sorted(filenames):
            candidate = current / name
            relative = candidate.relative_to(path).as_posix()
            if _COPY_SUFFIX.fullmatch(name) and not (
                name in _CACHE_FILES or candidate.suffix.lower() in _BYTECODE_SUFFIXES
            ):
                failures.append(f"copy-like source path is forbidden: {relative}")
    return failures


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def registry_path() -> Path:
    return repo_root() / "registry" / "skill-registry.yaml"


def load_registry(path: Path | None = None) -> dict[str, Any]:
    selected = path or registry_path()
    return load_yaml_strict(selected, "skill-registry.yaml")


def _validate_interfaces(value: object, location: str, failures: list[str]) -> None:
    if not isinstance(value, list):
        failures.append(f"{location}: expected a list")
        return
    if len(set(item for item in value if isinstance(item, str))) != len(value):
        failures.append(f"{location}: duplicate interfaces are forbidden")
    for index, interface in enumerate(value):
        if not isinstance(interface, str) or not INTERFACE_ID.fullmatch(interface):
            failures.append(f"{location}/{index}: invalid versioned interface {interface!r}")


def _validate_string_list(
    value: object,
    location: str,
    pattern: re.Pattern[str],
    failures: list[str],
) -> list[str]:
    if not isinstance(value, list):
        failures.append(f"{location}: expected a list")
        return []
    if len(value) != len(set(item for item in value if isinstance(item, str))):
        failures.append(f"{location}: duplicate identifiers are forbidden")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not pattern.fullmatch(item):
            failures.append(f"{location}/{index}: invalid identifier {item!r}")
        else:
            result.append(item)
    return result


def _validate_software_profiles(value: object, location: str, failures: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        failures.append(f"{location}: expected a list")
        return []
    profiles: list[dict[str, Any]] = []
    software_ids: set[str] = set()
    for index, profile in enumerate(value):
        item_location = f"{location}/{index}"
        if not isinstance(profile, dict):
            failures.append(f"{item_location}: expected a mapping")
            continue
        expected = {"software_id", "selection_policy", "environment_profile_ids"}
        if set(profile) != expected:
            failures.append(
                f"{item_location}: expected fields {sorted(expected)}, found {sorted(map(str, profile))}"
            )
        software_id = profile.get("software_id")
        if not isinstance(software_id, str) or not SKILL_ID.fullmatch(software_id):
            failures.append(f"{item_location}/software_id: invalid identifier")
        elif software_id in software_ids:
            failures.append(f"{item_location}/software_id: duplicate software mapping")
        else:
            software_ids.add(software_id)
        if profile.get("selection_policy") not in {
            "all_of",
            "any_of",
            "platform_variant",
            "edition_variant",
        }:
            failures.append(f"{item_location}/selection_policy: unsupported value")
        _validate_string_list(
            profile.get("environment_profile_ids"),
            f"{item_location}/environment_profile_ids",
            SKILL_ID,
            failures,
        )
        profiles.append(profile)
    return profiles


def _expected_software_profiles(software_data: dict[str, Any], skill_id: str) -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    planned = software_data.get("planned_software")
    if not isinstance(planned, dict):
        return expected
    for software_id, specification in planned.items():
        if not isinstance(specification, dict) or specification.get("intended_skill") != skill_id:
            continue
        environment = specification.get("environment_profiles")
        if not isinstance(environment, dict):
            continue
        expected.append(
            {
                "software_id": software_id,
                "selection_policy": environment.get("selection_policy"),
                "environment_profile_ids": environment.get("profile_ids"),
            }
        )
    return expected


def validation_errors(
    data: object,
    source_root: Path | None = None,
    software_data: dict[str, Any] | None = None,
    interface_data: dict[str, Any] | None = None,
    environment_data: dict[str, Any] | None = None,
) -> list[str]:
    failures: list[str] = []
    if not isinstance(data, dict):
        return ["<root>: registry must be a mapping"]
    expected_root = {"schema_version", "skills"}
    if set(data) != expected_root:
        failures.append(f"<root>: expected fields {sorted(expected_root)}, found {sorted(map(str, data))}")
    if data.get("schema_version") != SCHEMA_VERSION:
        failures.append(f"schema_version: expected {SCHEMA_VERSION!r}")

    skills = data.get("skills")
    if not isinstance(skills, dict) or not skills:
        failures.append("skills: expected a nonempty mapping")
        return failures
    expected_fields = {
        "display_name",
        "kind",
        "lifecycle",
        "path",
        "source_tree_sha256",
        "side_effects",
        "consumes",
        "produces",
        "activation_requirements",
    }
    active_names: set[str] = set()
    development_names: set[str] = set()
    planned_names: set[str] = set()
    for name, specification in skills.items():
        location = f"skills/{name}"
        if not isinstance(name, str) or not SKILL_ID.fullmatch(name):
            failures.append(f"{location}: invalid skill identifier")
        if not isinstance(specification, dict):
            failures.append(f"{location}: expected a mapping")
            continue
        if set(specification) != expected_fields:
            failures.append(
                f"{location}: expected fields {sorted(expected_fields)}, "
                f"found {sorted(map(str, specification))}"
            )
        display_name = specification.get("display_name")
        if not isinstance(display_name, str) or not display_name.strip():
            failures.append(f"{location}/display_name: expected a nonempty string")
        if specification.get("kind") not in KINDS:
            failures.append(f"{location}/kind: unsupported kind {specification.get('kind')!r}")
        lifecycle = specification.get("lifecycle")
        if lifecycle not in LIFECYCLES:
            failures.append(f"{location}/lifecycle: unsupported lifecycle {lifecycle!r}")
        side_effects = specification.get("side_effects")
        if not isinstance(side_effects, list) or not side_effects:
            failures.append(f"{location}/side_effects: expected a nonempty list")
            side_effects = []
        elif len(side_effects) != len(set(side_effects)):
            failures.append(f"{location}/side_effects: duplicate values are forbidden")
        for index, effect in enumerate(side_effects):
            if effect not in SIDE_EFFECTS:
                failures.append(f"{location}/side_effects/{index}: unsupported value {effect!r}")
        canonical_effects = [effect for effect in SIDE_EFFECTS if effect in side_effects]
        if side_effects and side_effects != canonical_effects:
            failures.append(f"{location}/side_effects: values must use canonical order")
        _validate_interfaces(specification.get("consumes"), f"{location}/consumes", failures)
        _validate_interfaces(specification.get("produces"), f"{location}/produces", failures)

        requirements = specification.get("activation_requirements")
        if not isinstance(requirements, dict):
            failures.append(f"{location}/activation_requirements: expected a structured mapping")
            requirements = {}
        elif set(requirements) != ACTIVATION_REQUIREMENT_FIELDS:
            failures.append(
                f"{location}/activation_requirements: expected fields "
                f"{sorted(ACTIVATION_REQUIREMENT_FIELDS)}, found {sorted(map(str, requirements))}"
            )
        software_profiles = _validate_software_profiles(
            requirements.get("software_profiles"),
            f"{location}/activation_requirements/software_profiles",
            failures,
        )
        activation_interfaces = _validate_string_list(
            requirements.get("interface_ids"),
            f"{location}/activation_requirements/interface_ids",
            INTERFACE_ID,
            failures,
        )
        activation_checks = _validate_string_list(
            requirements.get("activation_check_ids"),
            f"{location}/activation_requirements/activation_check_ids",
            SKILL_ID,
            failures,
        )
        task_catalog_ids = _validate_string_list(
            requirements.get("task_catalog_ids"),
            f"{location}/activation_requirements/task_catalog_ids",
            CATALOG_ID,
            failures,
        )

        path = specification.get("path")
        source_tree_sha256 = specification.get("source_tree_sha256")
        if lifecycle == "active":
            active_names.add(name)
            expected_path = f"skills/{name}"
            if path != expected_path:
                failures.append(f"{location}/path: active skill must use {expected_path!r}")
            if not isinstance(source_tree_sha256, str) or not SHA256.fullmatch(source_tree_sha256):
                failures.append(f"{location}/source_tree_sha256: active skill requires a SHA-256")
            if any((software_profiles, activation_interfaces, activation_checks, task_catalog_ids)):
                failures.append(
                    f"{location}/activation_requirements: active skill promotion gates must be empty"
                )
            if source_root is not None:
                source_path = source_root / expected_path
                if not source_path.joinpath("SKILL.md").is_file():
                    failures.append(f"{location}: missing active SKILL.md")
                try:
                    digest = source_tree_digest(source_path)
                except ValueError as exc:
                    failures.append(f"{location}/source_tree_sha256: {exc}")
                else:
                    if source_tree_sha256 != digest.sha256:
                        failures.append(
                            f"{location}/source_tree_sha256: recorded {source_tree_sha256!r} "
                            f"!= actual {digest.sha256!r}"
                        )
                    for inventory_failure in source_tree_inventory_errors(source_path):
                        failures.append(f"{location}/source_tree_sha256: {inventory_failure}")
        elif lifecycle == "development":
            development_names.add(name)
            expected_path = f"skills/{name}"
            if path != expected_path:
                failures.append(f"{location}/path: development skill must use {expected_path!r}")
            if not isinstance(source_tree_sha256, str) or not SHA256.fullmatch(source_tree_sha256):
                failures.append(f"{location}/source_tree_sha256: development skill requires a SHA-256")
            if activation_checks != list(ACTIVATION_CHECK_IDS):
                failures.append(
                    f"{location}/activation_requirements/activation_check_ids: must equal the 13 fixed checks"
                )
            declared_interfaces = list(
                dict.fromkeys(
                    item
                    for field in ("consumes", "produces")
                    for item in specification.get(field, [])
                    if isinstance(item, str)
                )
            )
            if activation_interfaces != declared_interfaces:
                failures.append(
                    f"{location}/activation_requirements/interface_ids: must exactly cover consumes and produces"
                )
            if software_data is not None:
                expected_profiles = _expected_software_profiles(software_data, name)
                if software_profiles != expected_profiles:
                    failures.append(
                        f"{location}/activation_requirements/software_profiles: must exactly match "
                        "planned software/provider mappings"
                    )
            if source_root is not None:
                source_path = source_root / expected_path
                if not source_path.joinpath("SKILL.md").is_file():
                    failures.append(f"{location}: missing development SKILL.md")
                try:
                    digest = source_tree_digest(source_path)
                except ValueError as exc:
                    failures.append(f"{location}/source_tree_sha256: {exc}")
                else:
                    if source_tree_sha256 != digest.sha256:
                        failures.append(
                            f"{location}/source_tree_sha256: recorded {source_tree_sha256!r} "
                            f"!= actual {digest.sha256!r}"
                        )
                    for inventory_failure in source_tree_inventory_errors(source_path):
                        failures.append(f"{location}/source_tree_sha256: {inventory_failure}")
        elif lifecycle == "planned":
            planned_names.add(name)
            if path is not None:
                failures.append(f"{location}/path: planned skill must use null")
            if source_tree_sha256 is not None:
                failures.append(f"{location}/source_tree_sha256: planned skill must use null")
            if activation_checks != list(ACTIVATION_CHECK_IDS):
                failures.append(
                    f"{location}/activation_requirements/activation_check_ids: must equal the 13 fixed checks"
                )
            declared_interfaces = list(
                dict.fromkeys(
                    item
                    for field in ("consumes", "produces")
                    for item in specification.get(field, [])
                    if isinstance(item, str)
                )
            )
            if activation_interfaces != declared_interfaces:
                failures.append(
                    f"{location}/activation_requirements/interface_ids: must exactly cover consumes and produces"
                )
            if software_data is not None:
                expected_profiles = _expected_software_profiles(software_data, name)
                if software_profiles != expected_profiles:
                    failures.append(
                        f"{location}/activation_requirements/software_profiles: must exactly match "
                        "planned software/provider mappings"
                    )
            if source_root is not None and source_root.joinpath("skills", name).exists():
                failures.append(f"{location}: planned skill must not have an installable source directory")

        if interface_data is not None:
            registered_interfaces = interface_data.get("interfaces")
            if not isinstance(registered_interfaces, dict):
                failures.append("interface-registry/interfaces: expected a mapping")
                registered_interfaces = {}
            for field in ("consumes", "produces"):
                for interface_id in specification.get(field, []):
                    interface = registered_interfaces.get(interface_id)
                    if not isinstance(interface, dict):
                        failures.append(f"{location}/{field}: unknown interface {interface_id!r}")
                    elif lifecycle == "active" and interface.get("lifecycle") != "active":
                        failures.append(
                            f"{location}/{field}: active skill cannot use non-active interface {interface_id!r}"
                        )

        if environment_data is not None:
            environment_profiles = environment_data.get("profiles")
            if not isinstance(environment_profiles, dict):
                failures.append("environment-profiles/profiles: expected a mapping")
                environment_profiles = {}
            for profile in software_profiles:
                for profile_id in profile.get("environment_profile_ids", []):
                    if profile_id not in environment_profiles:
                        failures.append(
                            f"{location}/activation_requirements/software_profiles: "
                            f"unknown environment profile {profile_id!r}"
                        )

    lifecycle_sets = (active_names, development_names, planned_names)
    if any(left.intersection(right) for index, left in enumerate(lifecycle_sets) for right in lifecycle_sets[index + 1 :]):
        failures.append("skills: an identifier cannot have multiple lifecycles")

    if software_data is not None:
        active_calculation_skills = {
            entry.get("calculation_skill")
            for entry in software_data.get("software", {}).values()
            if isinstance(entry, dict)
        }
        for name in active_calculation_skills:
            entry = skills.get(name)
            if not isinstance(entry, dict):
                failures.append(
                    f"software/calculation_skill: missing active Skill mapping {name!r}"
                )
            elif entry.get("lifecycle") != "active":
                failures.append(
                    f"skills/{name}/lifecycle: registered calculation software requires active"
                )
            elif entry.get("kind") != "calculation":
                failures.append(f"skills/{name}/kind: active calculation software requires calculation")
        for code, entry in software_data.get("planned_software", {}).items():
            if not isinstance(entry, dict):
                continue
            intended_skill = entry.get("intended_skill")
            skill_entry = skills.get(intended_skill)
            if not isinstance(skill_entry, dict):
                failures.append(
                    f"planned_software/{code}/intended_skill: missing skill placeholder {intended_skill!r}"
                )
    return failures


def _validated(path: Path | None = None, source_root: Path | None = None) -> dict[str, Any]:
    data = load_registry(path)
    failures = validation_errors(data, source_root)
    if failures:
        raise ValueError("invalid skill registry: " + "; ".join(failures))
    return data


def active_skill_names(path: Path | None = None) -> tuple[str, ...]:
    data = _validated(path)
    return tuple(name for name, entry in data["skills"].items() if entry["lifecycle"] == "active")


def planned_skill_names(path: Path | None = None) -> tuple[str, ...]:
    data = _validated(path)
    return tuple(name for name, entry in data["skills"].items() if entry["lifecycle"] == "planned")


def development_skill_names(path: Path | None = None) -> tuple[str, ...]:
    data = _validated(path)
    return tuple(
        name for name, entry in data["skills"].items() if entry["lifecycle"] == "development"
    )


def source_skill_names(path: Path | None = None) -> tuple[str, ...]:
    """Return all source-backed Skills without making development Skills installable."""

    data = _validated(path)
    return tuple(
        name
        for name, entry in data["skills"].items()
        if entry["lifecycle"] in {"active", "development"}
    )


def validate_source_skills(root: Path | None = None) -> tuple[str, ...]:
    """Validate hashes and inventories for active and development source trees."""

    selected_root = root or repo_root()
    data = load_registry(selected_root / "registry" / "skill-registry.yaml")
    failures = validation_errors(data, selected_root)
    if failures:
        raise ValueError("invalid source-backed Skill trees: " + "; ".join(failures))
    return tuple(
        name
        for name, entry in data["skills"].items()
        if isinstance(entry, dict) and entry.get("lifecycle") in {"active", "development"}
    )


def validate_active_sources(root: Path | None = None) -> tuple[str, ...]:
    """Return the active set only after recomputing every source-tree hash."""

    selected_root = root or repo_root()
    data = load_registry(selected_root / "registry" / "skill-registry.yaml")
    active = tuple(
        name for name, entry in data.get("skills", {}).items()
        if isinstance(entry, dict) and entry.get("lifecycle") == "active"
    )
    return validate_selected_active_sources(active, selected_root, data=data)


def validate_selected_active_sources(
    names: tuple[str, ...] | list[str],
    root: Path | None = None,
    *,
    data: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    """Validate only the explicitly selected active source trees.

    Registry semantics are still checked globally. This lets a caller install or
    inspect one intact Skill without silently accepting damage in that Skill, while
    the all-Skill installer and repository audit continue to gate every active tree.
    """

    selected_root = root or repo_root()
    registry = data or load_registry(selected_root / "registry" / "skill-registry.yaml")
    failures = validation_errors(registry)
    skills = registry.get("skills", {})
    selected = tuple(names)
    if len(selected) != len(set(selected)):
        failures.append("selection: duplicate Skill names are forbidden")
    if isinstance(skills, dict):
        for name, entry in skills.items():
            if (
                isinstance(entry, dict)
                and entry.get("lifecycle") == "planned"
                and selected_root.joinpath("skills", name).exists()
            ):
                failures.append(f"skills/{name}: planned skill must not have an installable source directory")
    for name in selected:
        entry = skills.get(name) if isinstance(skills, dict) else None
        if not isinstance(entry, dict) or entry.get("lifecycle") != "active":
            failures.append(f"selection: {name!r} is not an active Skill")
            continue
        source_path = selected_root / f"skills/{name}"
        location = f"skills/{name}"
        if not source_path.joinpath("SKILL.md").is_file():
            failures.append(f"{location}: missing active SKILL.md")
        try:
            digest = source_tree_digest(source_path)
        except ValueError as exc:
            failures.append(f"{location}/source_tree_sha256: {exc}")
        except OSError as exc:
            failures.append(
                f"{location}/source_tree_sha256: source tree is unreadable "
                f"({exc.__class__.__name__})"
            )
        else:
            if entry.get("source_tree_sha256") != digest.sha256:
                failures.append(
                    f"{location}/source_tree_sha256: recorded "
                    f"{entry.get('source_tree_sha256')!r} != actual {digest.sha256!r}"
                )
            for inventory_failure in source_tree_inventory_errors(source_path):
                failures.append(f"{location}/source_tree_sha256: {inventory_failure}")
    if failures:
        raise ValueError("invalid active Skill sources: " + "; ".join(failures))
    return selected


def source_manifest_report(root: Path, data: dict[str, Any]) -> dict[str, Any]:
    skills: dict[str, Any] = {}
    for name, entry in data["skills"].items():
        if entry.get("lifecycle") not in {"active", "development"}:
            continue
        digest = source_tree_digest(root / entry["path"])
        skills[name] = {
            "source_tree_sha256": digest.sha256,
            "file_count": len(digest.files),
            "files": [
                {"path": item.path, "size": item.size, "sha256": item.sha256}
                for item in digest.files
            ],
        }
    return {"schema_version": "1.0", "algorithm": "length-prefixed-posix-path-and-raw-bytes", "skills": skills}


def _updated_hash_text(text: str, hashes: dict[str, str]) -> str:
    lines = text.splitlines(keepends=True)
    current_skill: str | None = None
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        skill_match = re.fullmatch(r"  ([a-z0-9]+(?:-[a-z0-9]+)*):\r?\n?", line)
        if skill_match is not None:
            current_skill = skill_match.group(1)
        if current_skill in hashes and re.match(r"^    source_tree_sha256:", line):
            newline = "\r\n" if line.endswith("\r\n") else "\n"
            line = f'    source_tree_sha256: "{hashes[current_skill]}"{newline}'
            seen.add(current_skill)
        result.append(line)
    missing = set(hashes).difference(seen)
    if missing:
        raise ValueError(f"cannot locate source_tree_sha256 fields for {sorted(missing)!r}")
    return "".join(result)


def write_source_hashes(path: Path, root: Path, data: dict[str, Any]) -> dict[str, str]:
    hashes = {
        name: source_tree_digest(root / entry["path"]).sha256
        for name, entry in data["skills"].items()
        if entry.get("lifecycle") in {"active", "development"}
    }
    original = path.read_text(encoding="utf-8")
    updated = _updated_hash_text(original, hashes)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(updated, encoding="utf-8")
    os.replace(temporary, path)
    return hashes


def _load_support_registry(root: Path, filename: str) -> dict[str, Any]:
    return load_yaml_strict(root / "registry" / filename, filename)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--check", action="store_true", help="explicit read-only validation (the default)")
    parser.add_argument("--write-hashes", action="store_true", help="explicitly update active source-tree hashes")
    parser.add_argument("--manifest-json", action="store_true", help="print the relative per-file digest report")
    args = parser.parse_args()
    selected_root = (args.root or repo_root()).resolve()
    selected_registry = args.registry or selected_root / "registry" / "skill-registry.yaml"
    try:
        data = load_registry(selected_registry)
        if args.write_hashes:
            write_source_hashes(selected_registry, selected_root, data)
            data = load_registry(selected_registry)
        software = _load_support_registry(selected_root, "software-registry.yaml")
        interfaces = _load_support_registry(selected_root, "interface-registry.yaml")
        environments = _load_support_registry(selected_root, "environment-profiles.yaml")
        failures = validation_errors(data, selected_root, software, interfaces, environments)
        report = source_manifest_report(selected_root, data) if args.manifest_json else None
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures = [f"<registry>: {exc}"]
        report = None
    if report is not None:
        print(json.dumps(report, indent=2, sort_keys=True))
    if failures:
        for item in failures:
            print(item, file=sys.stderr)
        return 2
    skills = data["skills"]
    active = sum(entry["lifecycle"] == "active" for entry in skills.values())
    development = sum(entry["lifecycle"] == "development" for entry in skills.values())
    planned = sum(entry["lifecycle"] == "planned" for entry in skills.values())
    print(
        f"PASS: registered {active} active skills, {development} development skills, "
        f"and {planned} planned skill placeholders"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
