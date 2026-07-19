#!/usr/bin/env python3
"""Validate one planned Skill candidate without activating it.

On supported macOS hosts, L1 copies the candidate into a temporary workspace,
probes a validator-controlled Seatbelt profile, and runs tests only when the
same profile proves workspace I/O plus host-read, host-write, child-process,
and network denial. The report describes those bounded controls; it is not a
complete sandbox or a claim of OS process isolation.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import ast
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import resource
import shutil
import signal
import subprocess
import tempfile
from typing import Any, Iterable
from urllib.parse import unquote

from jsonschema import Draft202012Validator, FormatChecker

from registry_yaml import load_yaml_strict, loads_yaml_strict
from skill_registry import source_tree_digest, source_tree_inventory_errors
import strict_json


TOOL_VERSION = "1.2.0"
SCHEMA_VERSION = "1.0"
SCRIPT_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA = SCRIPT_ROOT / "contracts" / "validation-report.schema.json"
SKILL_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_BASE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@+~-]{0,127}$")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".toml", ".txt", ".sh", ".bash"}
SSH_COMMANDS = {"ssh", "scp", "sftp"}
SSH_MODULES = {"asyncssh", "fabric", "paramiko"}
PROCESS_SIGNAL_COMMANDS = {"kill", "killall", "pkill"}
PROCESS_RESOURCE_COMMANDS = {"renice", "setsid", "taskset", "ulimit"}
SAFETY_CHECKS = (
    "CANDIDATE.SAFETY.EVAL",
    "CANDIDATE.SAFETY.EXEC",
    "CANDIDATE.SAFETY.OS_SYSTEM",
    "CANDIDATE.SAFETY.SHELL_TRUE",
    "CANDIDATE.SAFETY.SSH",
    "CANDIDATE.SAFETY.PICKLE_LOAD",
    "CANDIDATE.SAFETY.PICKLE_ARTIFACT",
    "CANDIDATE.SAFETY.PROCESS_SIGNAL",
    "CANDIDATE.SAFETY.PROCESS_SPAWN",
    "CANDIDATE.SAFETY.MULTIPROCESSING",
    "CANDIDATE.SAFETY.CTYPES",
    "CANDIDATE.SAFETY.RESOURCE_CONTROL",
)
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
SANDBOX_BACKEND_ID = "macos-seatbelt-sandbox-exec"
SANDBOX_TIMEOUT_SECONDS = 60
SANDBOX_OUTPUT_LIMIT_BYTES = 4 * 1024 * 1024
CHANGED_FILES_LIMIT_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class Check:
    check_id: str
    severity: str
    status: str
    message: str
    next_action: str | None = None
    evidence: tuple[dict[str, str | None], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "severity": self.severity,
            "status": self.status,
            "message": self.message,
            "next_action": self.next_action,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class IsolationDecision:
    check: Check
    backend_status: str
    backend_id: str | None = None
    backend_version: str | None = None
    backend_sha256: str | None = None
    profile_sha256: str | None = None
    source_tree_sha256: str | None = None
    isolated_copy_sha256: str | None = None
    enforcement_probe_status: str = "not-run"
    enforcement_probe_sha256: str | None = None
    workspace_io_enforcement: str = "not-run"
    host_read_enforcement: str = "not-run"
    host_write_enforcement: str = "not-run"
    network_enforcement: str = "not-run"
    subprocess_inheritance_enforcement: str = "not-run"
    process_resource_limits_status: str = "not-run"
    process_resource_limits_sha256: str | None = None
    process_new_session_status: str = "not-run"
    candidate_test_execution: str = "not-run"


def generated_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str | None:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError:
        return None


def candidate_tree_sha256(candidate: Path) -> str | None:
    """Hash regular candidate files and their relative names deterministically."""

    if candidate.is_symlink() or not candidate.is_dir():
        return None
    digest = hashlib.sha256()
    try:
        paths = sorted(candidate.rglob("*"), key=lambda item: item.relative_to(candidate).as_posix())
        for path in paths:
            if path.is_symlink():
                return None
            if path.is_dir():
                continue
            if not path.is_file():
                return None
            relative = path.relative_to(candidate).as_posix().encode("utf-8")
            content = path.read_bytes()
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
    except (OSError, UnicodeError, ValueError):
        return None
    return digest.hexdigest()


def safe_relative_label(path: Path, root: Path, fallback: str) -> str:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return fallback
    parts = relative.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return fallback
    return PurePosixPath(*parts).as_posix()


def file_evidence(path: Path, root: Path, fallback: str) -> dict[str, str | None]:
    return {
        "label": safe_relative_label(path, root, fallback),
        "sha256": sha256_file(path) if path.is_file() else None,
    }


def outcome_check(
    check_id: str,
    ok: bool,
    pass_message: str,
    fail_message: str,
    *,
    severity: str = "critical",
    next_action: str | None = None,
    evidence: Iterable[dict[str, str | None]] = (),
) -> Check:
    return Check(
        check_id=check_id,
        severity=severity,
        status="pass" if ok else "fail",
        message=pass_message if ok else fail_message,
        next_action=None if ok else next_action,
        evidence=tuple(evidence),
    )


def load_yaml_object(path: Path) -> dict[str, Any]:
    return load_yaml_strict(path)


def locate_repository(candidate_dir: Path) -> Path | None:
    for parent in (candidate_dir, *candidate_dir.parents):
        if (
            parent.joinpath("registry", "skill-registry.yaml").is_file()
            and parent.joinpath("registry", "software-registry.yaml").is_file()
        ):
            return parent
    return None


def candidate_codes(software: dict[str, Any], skill: str) -> set[str]:
    result: set[str] = set()
    planned = software.get("planned_software")
    if isinstance(planned, dict):
        for code, specification in planned.items():
            if (
                isinstance(code, str)
                and isinstance(specification, dict)
                and specification.get("intended_skill") == skill
            ):
                result.add(code)
    return result


def check_registries(root: Path, skill: str) -> tuple[list[Check], dict[str, Any], set[str]]:
    checks: list[Check] = []
    skill_path = root / "registry" / "skill-registry.yaml"
    software_path = root / "registry" / "software-registry.yaml"
    try:
        skill_registry = load_yaml_object(skill_path)
    except (OSError, UnicodeError, ValueError):
        skill_registry = {}
        checks.append(
            Check(
                "CANDIDATE.REGISTRY.SKILL_REGISTRY",
                "critical",
                "fail",
                "The Skill registry is unreadable or malformed.",
                "Restore a valid registry before validating a candidate.",
            )
        )
    else:
        checks.append(
            Check(
                "CANDIDATE.REGISTRY.SKILL_REGISTRY",
                "critical",
                "pass",
                "The Skill registry is readable.",
                evidence=(file_evidence(skill_path, root, "registry/skill-registry.yaml"),),
            )
        )

    try:
        software = load_yaml_object(software_path)
    except (OSError, UnicodeError, ValueError):
        software = {}
        checks.append(
            Check(
                "CANDIDATE.REGISTRY.SOFTWARE_REGISTRY",
                "critical",
                "fail",
                "The software registry is unreadable or malformed.",
                "Restore a valid registry before validating a candidate.",
            )
        )
    else:
        checks.append(
            Check(
                "CANDIDATE.REGISTRY.SOFTWARE_REGISTRY",
                "critical",
                "pass",
                "The software registry is readable.",
                evidence=(file_evidence(software_path, root, "registry/software-registry.yaml"),),
            )
        )

    skills = skill_registry.get("skills") if isinstance(skill_registry, dict) else None
    entry = skills.get(skill) if isinstance(skills, dict) else None
    checks.append(
        outcome_check(
            "CANDIDATE.REGISTRY.ENTRY",
            isinstance(entry, dict),
            "The candidate has a registered roadmap entry.",
            "The candidate has no registered roadmap entry.",
            next_action="Add a reviewed planned registry entry before candidate development.",
        )
    )
    planned = isinstance(entry, dict) and entry.get("lifecycle") == "planned"
    checks.append(
        outcome_check(
            "CANDIDATE.REGISTRY.PLANNED",
            planned,
            "The candidate remains planned.",
            "The candidate is not in the planned lifecycle.",
            next_action="Restore lifecycle=planned; candidate validation cannot activate a Skill.",
        )
    )
    null_path = isinstance(entry, dict) and entry.get("path") is None
    checks.append(
        outcome_check(
            "CANDIDATE.REGISTRY.PATH_NULL",
            null_path,
            "The planned candidate keeps a null public path.",
            "The planned candidate exposes a public path.",
            next_action="Restore path=null until an atomic promotion is reviewed.",
        )
    )
    null_source_hash = planned and isinstance(entry, dict) and entry.get("source_tree_sha256") is None
    checks.append(
        outcome_check(
            "CANDIDATE.REGISTRY.SOURCE_HASH_NULL",
            null_source_hash,
            "The planned candidate does not claim an active source-tree hash.",
            "The planned candidate claims a source-tree hash before promotion.",
            next_action="Restore source_tree_sha256=null until atomic promotion recomputes the active source hash.",
        )
    )

    active_names = {
        name
        for name, specification in (skills.items() if isinstance(skills, dict) else ())
        if isinstance(specification, dict) and specification.get("lifecycle") == "active"
    }
    checks.append(
        outcome_check(
            "CANDIDATE.ROUTING.ACTIVE",
            skill not in active_names,
            "The candidate is absent from the active Skill set.",
            "The candidate appears in the active Skill set.",
            next_action="Remove the candidate from active routing until promotion review.",
        )
    )

    installable: set[str] = set()
    active_source_hashes_valid = True
    if isinstance(skills, dict):
        for name, specification in skills.items():
            if not isinstance(name, str) or not isinstance(specification, dict):
                active_source_hashes_valid = False
                continue
            if specification.get("lifecycle") != "active":
                continue
            expected_path = f"skills/{name}"
            source = root / expected_path
            recorded_hash = specification.get("source_tree_sha256")
            if specification.get("path") != expected_path or not isinstance(recorded_hash, str):
                active_source_hashes_valid = False
                continue
            try:
                actual_hash = source_tree_digest(source).sha256
            except ValueError:
                active_source_hashes_valid = False
                continue
            if actual_hash != recorded_hash or source_tree_inventory_errors(source):
                active_source_hashes_valid = False
                continue
            installable.add(name)
    checks.append(
        outcome_check(
            "CANDIDATE.ROUTING.INSTALL",
            skill not in installable and active_source_hashes_valid,
            "The candidate is absent from the hash-verified active installer source set.",
            "The candidate is installable or an active installer source hash cannot be reproduced.",
            next_action="Keep the candidate planned and repair every active source_tree_sha256 before validation.",
        )
    )
    return checks, software, candidate_codes(software, skill)


def iter_code_enums(value: object) -> Iterable[list[object]]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "code" and isinstance(child, dict) and isinstance(child.get("enum"), list):
                yield child["enum"]
            yield from iter_code_enums(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_code_enums(child)


def check_contract_enums(root: Path, codes: set[str]) -> Check:
    offending: list[Path] = []
    malformed = False
    for path in sorted(root.joinpath("contracts").glob("*.schema.json")):
        try:
            value = strict_json.load_object(path, path.name)
        except (OSError, strict_json.StrictJSONError):
            malformed = True
            continue
        if any(codes.intersection(item for item in enum if isinstance(item, str)) for enum in iter_code_enums(value)):
            offending.append(path)
    ok = not malformed and not offending
    evidence = [file_evidence(path, root, "contracts/schema.json") for path in offending]
    return outcome_check(
        "CANDIDATE.ROUTING.CODE_ENUM",
        ok,
        "Planned software identifiers are absent from active code enums.",
        "A planned identifier is exposed by an active code enum or a contract is unreadable.",
        next_action="Remove planned identifiers from active code enums and repair malformed contracts.",
        evidence=evidence,
    )


def _contains_exact(value: object, targets: set[str]) -> bool:
    if isinstance(value, str):
        return value in targets
    if isinstance(value, dict):
        return any(str(key) in targets or _contains_exact(child, targets) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_exact(child, targets) for child in value)
    return False


def _backend_matches_code(backend_id: str, codes: set[str]) -> bool:
    return any(
        backend_id == code
        or backend_id.startswith((f"{code}.", f"{code}-", f"{code}_"))
        or backend_id.endswith((f".{code}", f"-{code}", f"_{code}"))
        for code in codes
    )


def check_observable_routes(root: Path, skill: str, codes: set[str]) -> Check:
    path = root / "skills" / "dft-postprocess" / "references" / "observable-registry.yaml"
    if not path.is_file():
        return Check(
            "CANDIDATE.ROUTING.OBSERVABLE",
            "critical",
            "pass",
            "No observable registry exposes the candidate.",
        )
    try:
        registry = load_yaml_object(path)
    except (OSError, UnicodeError, ValueError):
        return Check(
            "CANDIDATE.ROUTING.OBSERVABLE",
            "critical",
            "fail",
            "The observable registry is unreadable or malformed.",
            "Repair the observable registry before candidate validation.",
        )

    backends = registry.get("backends")
    candidate_backends = {
        backend_id
        for backend_id, specification in backends.items()
        if (
            isinstance(backend_id, str)
            and isinstance(specification, dict)
            and specification.get("implemented") is True
            and _backend_matches_code(backend_id, codes)
        )
    } if isinstance(backends, dict) else set()
    routed = _contains_exact(registry, {skill})
    observables = registry.get("observables")
    if isinstance(observables, dict):
        for observable in observables.values():
            routes = observable.get("codes") if isinstance(observable, dict) else None
            if not isinstance(routes, dict):
                continue
            for code, route in routes.items():
                # A design-only entry is an explicit non-executable reservation.
                # It may name a future code or backend without exposing the
                # planned candidate. Unknown or more mature routes fail closed.
                design_only = isinstance(route, dict) and route.get("maturity") == "design-only"
                if isinstance(code, str) and code in codes and not design_only:
                    routed = True
                backends = route.get("backends") if isinstance(route, dict) else None
                if not design_only and isinstance(backends, list) and candidate_backends.intersection(
                    item for item in backends if isinstance(item, str)
                ):
                    routed = True
    return outcome_check(
        "CANDIDATE.ROUTING.OBSERVABLE",
        not routed,
        "The candidate has no executable observable route.",
        "The candidate is exposed by an observable or backend route.",
        next_action="Keep candidate observables and backends non-routable until atomic promotion.",
        evidence=(file_evidence(path, root, "observable-registry.yaml"),),
    )


def check_operation_route(root: Path, skill: str) -> Check:
    path = root / "registry" / "operation-routes.yaml"
    if not path.is_file():
        return Check(
            "CANDIDATE.ROUTING.OPERATION",
            "critical",
            "pass",
            "No operation route exposes the candidate.",
        )
    try:
        registry = load_yaml_object(path)
    except (OSError, UnicodeError, ValueError):
        return Check(
            "CANDIDATE.ROUTING.OPERATION",
            "critical",
            "fail",
            "The operation route registry is unreadable or malformed.",
            "Repair the operation route registry before candidate validation.",
        )
    routes = registry.get("routes")
    route = routes.get(skill) if isinstance(routes, dict) else None
    safe = route is None or (
        isinstance(route, dict)
        and route.get("lifecycle") == "planned"
        and route.get("routable") is False
        and route.get("first_tool") == {}
        and route.get("tool_sequence") == {}
        and route.get("actions") == {}
    )
    return outcome_check(
        "CANDIDATE.ROUTING.OPERATION",
        safe,
        "The candidate has no executable operation route.",
        "The candidate has an active, routable, or executable operation route.",
        next_action="Restore a planned non-routable route with empty mode maps and no action templates.",
        evidence=(file_evidence(path, root, "registry/operation-routes.yaml"),),
    )


def parse_frontmatter(skill_file: Path) -> tuple[dict[str, Any] | None, str]:
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return None, text
    return loads_yaml_strict(match.group(1), "candidate-frontmatter"), text


def iter_text_files(candidate: Path) -> Iterable[Path]:
    for path in sorted(candidate.rglob("*")):
        if path.is_file() and path.suffix.casefold() in TEXT_SUFFIXES:
            yield path


def check_links(candidate: Path) -> tuple[bool, list[Path]]:
    broken: list[Path] = []
    for markdown in sorted(candidate.rglob("*.md")):
        try:
            text = markdown.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            broken.append(markdown)
            continue
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = target.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            target = unquote(target)
            path_target = Path(target)
            if path_target.is_absolute() or ".." in path_target.parts:
                broken.append(markdown)
                continue
            resolved = (markdown.parent / path_target).resolve()
            try:
                resolved.relative_to(candidate.resolve())
            except ValueError:
                broken.append(markdown)
                continue
            if not resolved.exists():
                broken.append(markdown)
    return not broken, sorted(set(broken))


def check_candidate_content(root: Path, candidate: Path, skill: str) -> list[Check]:
    checks: list[Check] = []
    expected_relative = PurePosixPath("candidates", skill).as_posix()
    actual_label = safe_relative_label(candidate, root, "candidate")
    identity_ok = candidate.is_dir() and not candidate.is_symlink() and candidate.name == skill and actual_label == expected_relative
    checks.append(
        outcome_check(
            "CANDIDATE.IDENTITY.DIRECTORY",
            identity_ok,
            "The candidate directory has the canonical Skill identity.",
            "The candidate directory is missing, aliased, or outside its canonical location.",
            next_action="Use the exact candidates/<skill-id> candidate directory without symlinks.",
        )
    )
    active_collision = root / "skills" / skill
    checks.append(
        outcome_check(
            "CANDIDATE.IDENTITY.ACTIVE_COLLISION",
            not active_collision.exists() and not active_collision.is_symlink(),
            "No same-name active Skill directory collides with the planned candidate.",
            "A same-name directory or symlink exists under the active skills/ root.",
            next_action="Remove the skills/<skill-id> collision; promotion must be an explicit atomic move.",
            evidence=(
                {"label": f"skills/{skill}", "sha256": None},
            ) if active_collision.exists() or active_collision.is_symlink() else (),
        )
    )

    skill_file = candidate / "SKILL.md"
    checks.append(
        outcome_check(
            "CANDIDATE.IDENTITY.SKILL_FILE",
            skill_file.is_file() and not skill_file.is_symlink(),
            "The candidate contains a canonical SKILL.md.",
            "The candidate lacks a canonical SKILL.md.",
            next_action="Create a regular SKILL.md file in the candidate root.",
        )
    )
    metadata: dict[str, Any] | None = None
    text = ""
    if skill_file.is_file():
        try:
            metadata, text = parse_frontmatter(skill_file)
        except (OSError, UnicodeError, ValueError):
            metadata = None
    frontmatter_ok = (
        isinstance(metadata, dict)
        and set(metadata) == {"name", "description"}
        and isinstance(metadata.get("description"), str)
        and bool(metadata["description"].strip())
    )
    checks.append(
        outcome_check(
            "CANDIDATE.IDENTITY.FRONTMATTER",
            frontmatter_ok,
            "SKILL.md has strict name and description frontmatter.",
            "SKILL.md frontmatter is missing, malformed, or contains unsupported fields.",
            next_action="Use YAML frontmatter containing only nonempty name and description fields.",
            evidence=(file_evidence(skill_file, root, expected_relative + "/SKILL.md"),) if skill_file.is_file() else (),
        )
    )
    checks.append(
        outcome_check(
            "CANDIDATE.IDENTITY.NAME",
            frontmatter_ok and metadata.get("name") == skill,
            "The frontmatter name matches the candidate identity.",
            "The frontmatter name differs from the candidate identity.",
            next_action="Set frontmatter name to the exact candidate Skill ID.",
        )
    )
    line_count = len(text.splitlines()) if text else 0
    checks.append(
        outcome_check(
            "CANDIDATE.CONTENT.LINE_LIMIT",
            bool(text) and line_count < 500,
            "SKILL.md remains below 500 lines.",
            "SKILL.md is empty or is not below 500 lines.",
            next_action="Keep the core workflow concise and move detail into one-level references.",
        )
    )

    readmes = [path for path in candidate.rglob("*") if path.is_file() and path.name.casefold() == "readme.md"] if candidate.is_dir() else []
    checks.append(
        outcome_check(
            "CANDIDATE.CONTENT.README",
            not readmes,
            "The candidate contains no Skill-internal README.",
            "The candidate contains a forbidden Skill-internal README.",
            next_action="Remove Skill-internal README files and keep usage guidance in SKILL.md or references.",
            evidence=(file_evidence(path, root, expected_relative + "/README.md") for path in readmes),
        )
    )

    todo_files: list[Path] = []
    if candidate.is_dir():
        for path in iter_text_files(candidate):
            try:
                if re.search(r"\bTODO\b", path.read_text(encoding="utf-8")):
                    todo_files.append(path)
            except (OSError, UnicodeError):
                todo_files.append(path)
    checks.append(
        outcome_check(
            "CANDIDATE.CONTENT.TODO",
            not todo_files,
            "The candidate contains no unresolved TODO marker.",
            "The candidate contains an unresolved TODO marker or unreadable text file.",
            next_action="Resolve or remove every TODO before candidate validation.",
            evidence=(file_evidence(path, root, expected_relative + "/text") for path in todo_files),
        )
    )

    references = candidate / "references"
    nested = [path for path in references.rglob("*") if path.is_dir()] if references.is_dir() else []
    checks.append(
        outcome_check(
            "CANDIDATE.CONTENT.REFERENCES_DEPTH",
            not nested,
            "Candidate references are flat and one level deep.",
            "Candidate references contain a nested directory.",
            next_action="Move referenced files directly under references/.",
            evidence=({"label": safe_relative_label(path, root, expected_relative + "/references/nested"), "sha256": None} for path in nested),
        )
    )

    links_ok, broken = check_links(candidate) if candidate.is_dir() else (False, [])
    checks.append(
        outcome_check(
            "CANDIDATE.CONTENT.LINKS",
            links_ok,
            "All local Markdown links resolve inside the candidate.",
            "A local Markdown link is broken, absolute, or escapes the candidate.",
            next_action="Repair local links and keep all targets inside the candidate directory.",
            evidence=(file_evidence(path, root, expected_relative + "/document.md") for path in broken),
        )
    )

    symlinks = [path for path in candidate.rglob("*") if path.is_symlink()] if candidate.is_dir() else []
    checks.append(
        outcome_check(
            "CANDIDATE.CONTENT.SYMLINKS",
            not symlinks,
            "The candidate contains no source symlink.",
            "The candidate contains a source symlink.",
            next_action="Replace candidate symlinks with reviewed regular source files.",
            evidence=({"label": safe_relative_label(path, root, expected_relative + "/symlink"), "sha256": None} for path in symlinks),
        )
    )
    inventory_failures: list[str] = []
    if candidate.is_dir():
        try:
            source_tree_digest(candidate)
        except ValueError:
            inventory_failures.append("source-tree-digest-invalid")
        inventory_failures.extend(source_tree_inventory_errors(candidate))
    else:
        inventory_failures.append("candidate-source-missing")
    checks.append(
        outcome_check(
            "CANDIDATE.CONTENT.SOURCE_INVENTORY",
            not inventory_failures,
            "The candidate source inventory contains only canonical regular source files.",
            "The candidate source inventory contains a cache, copy-like, linked, special, or unreadable entry.",
            next_action="Remove generated and copy-like artifacts and replace linked or special entries with reviewed regular files.",
            evidence=(
                {
                    "label": f"{expected_relative}/inventory-finding-{sha256_bytes(item.encode('utf-8'))[:16]}",
                    "sha256": None,
                }
                for item in inventory_failures
            ),
        )
    )
    return checks


def _literal_strings(value: ast.AST) -> list[str]:
    result: list[str] = []
    for child in ast.walk(value):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            result.append(child.value)
    return result


def _ssh_literal(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    first = stripped.split()[0]
    return Path(first).name.casefold() in SSH_COMMANDS


def _process_signal_literal(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    first = stripped.split()[0]
    return Path(first).name.casefold() in PROCESS_SIGNAL_COMMANDS


def python_safety_findings(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    os_aliases = {"os"}
    os_system_names: set[str] = set()
    pickle_aliases = {"pickle", "cPickle"}
    pickle_load_names: set[str] = set()
    subprocess_aliases = {"subprocess"}
    subprocess_calls: set[str] = set()
    builtin_eval_names = {"eval"}
    builtin_exec_names = {"exec"}
    signal_aliases = {"signal"}
    signal_control_names: set[str] = set()
    os_process_signal_names: set[str] = set()
    os_process_spawn_names: set[str] = set()
    os_resource_control_names: set[str] = set()
    resource_aliases = {"resource"}
    resource_control_names: set[str] = set()
    findings: set[str] = set()

    os_process_signals = {"kill", "killpg"}
    os_process_spawns = {
        "fork",
        "forkpty",
        "posix_spawn",
        "posix_spawnp",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
    }
    os_resource_controls = {
        "nice",
        "setpgid",
        "setpriority",
        "setsid",
        "sched_setaffinity",
        "sched_setparam",
        "sched_setscheduler",
        "tcsetpgrp",
    }
    signal_controls = {"pthread_kill", "raise_signal"}
    resource_controls = {"prlimit", "setrlimit"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".", 1)[0]
                local = alias.asname or root_name
                if root_name == "os":
                    os_aliases.add(local)
                if root_name in {"pickle", "cPickle"}:
                    pickle_aliases.add(local)
                if root_name == "subprocess":
                    subprocess_aliases.add(local)
                if root_name == "signal":
                    signal_aliases.add(local)
                if root_name == "resource":
                    resource_aliases.add(local)
                if root_name == "multiprocessing":
                    findings.add("CANDIDATE.SAFETY.MULTIPROCESSING")
                if root_name == "ctypes":
                    findings.add("CANDIDATE.SAFETY.CTYPES")
                if root_name == "psutil":
                    findings.add("CANDIDATE.SAFETY.RESOURCE_CONTROL")
                if root_name in SSH_MODULES:
                    findings.add("CANDIDATE.SAFETY.SSH")
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".", 1)[0]
            for alias in node.names:
                local = alias.asname or alias.name
                if alias.name == "*" and module == "os":
                    findings.update(
                        {
                            "CANDIDATE.SAFETY.OS_SYSTEM",
                            "CANDIDATE.SAFETY.PROCESS_SIGNAL",
                            "CANDIDATE.SAFETY.PROCESS_SPAWN",
                            "CANDIDATE.SAFETY.RESOURCE_CONTROL",
                        }
                    )
                if alias.name == "*" and module == "signal":
                    findings.add("CANDIDATE.SAFETY.PROCESS_SIGNAL")
                if alias.name == "*" and module == "resource":
                    findings.add("CANDIDATE.SAFETY.RESOURCE_CONTROL")
                if module == "os" and alias.name == "system":
                    os_system_names.add(local)
                if module == "os" and alias.name in os_process_signals:
                    os_process_signal_names.add(local)
                if module == "os" and alias.name in os_process_spawns:
                    os_process_spawn_names.add(local)
                if module == "os" and alias.name in os_resource_controls:
                    os_resource_control_names.add(local)
                if module in {"pickle", "cPickle"} and alias.name in {"load", "loads"}:
                    pickle_load_names.add(local)
                if module == "subprocess" and alias.name in {"call", "check_call", "check_output", "Popen", "run"}:
                    subprocess_calls.add(local)
                if module == "builtins" and alias.name == "eval":
                    builtin_eval_names.add(local)
                if module == "builtins" and alias.name == "exec":
                    builtin_exec_names.add(local)
                if module == "signal" and alias.name in signal_controls:
                    signal_control_names.add(local)
                if module == "resource" and alias.name in resource_controls:
                    resource_control_names.add(local)
                if module == "multiprocessing":
                    findings.add("CANDIDATE.SAFETY.MULTIPROCESSING")
                if module == "ctypes":
                    findings.add("CANDIDATE.SAFETY.CTYPES")
                if module == "psutil":
                    findings.add("CANDIDATE.SAFETY.RESOURCE_CONTROL")
                if module in SSH_MODULES:
                    findings.add("CANDIDATE.SAFETY.SSH")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name):
            if function.id in builtin_eval_names:
                findings.add("CANDIDATE.SAFETY.EVAL")
            if function.id in builtin_exec_names:
                findings.add("CANDIDATE.SAFETY.EXEC")
            if function.id in os_system_names:
                findings.add("CANDIDATE.SAFETY.OS_SYSTEM")
            if function.id in pickle_load_names:
                findings.add("CANDIDATE.SAFETY.PICKLE_LOAD")
            if function.id in os_process_signal_names or function.id in signal_control_names:
                findings.add("CANDIDATE.SAFETY.PROCESS_SIGNAL")
            if function.id in os_process_spawn_names:
                findings.add("CANDIDATE.SAFETY.PROCESS_SPAWN")
            if function.id in os_resource_control_names or function.id in resource_control_names:
                findings.add("CANDIDATE.SAFETY.RESOURCE_CONTROL")
            is_subprocess = function.id in subprocess_calls
        else:
            is_subprocess = False
        if isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
            owner = function.value.id
            if owner in os_aliases and function.attr == "system":
                findings.add("CANDIDATE.SAFETY.OS_SYSTEM")
            if owner in os_aliases and function.attr in os_process_signals:
                findings.add("CANDIDATE.SAFETY.PROCESS_SIGNAL")
            if owner in os_aliases and function.attr in os_process_spawns:
                findings.add("CANDIDATE.SAFETY.PROCESS_SPAWN")
            if owner in os_aliases and function.attr in os_resource_controls:
                findings.add("CANDIDATE.SAFETY.RESOURCE_CONTROL")
            if owner in pickle_aliases and function.attr in {"load", "loads"}:
                findings.add("CANDIDATE.SAFETY.PICKLE_LOAD")
            if owner in signal_aliases and function.attr in signal_controls:
                findings.add("CANDIDATE.SAFETY.PROCESS_SIGNAL")
            if owner in resource_aliases and function.attr in resource_controls:
                findings.add("CANDIDATE.SAFETY.RESOURCE_CONTROL")
            if owner in subprocess_aliases and function.attr in {"call", "check_call", "check_output", "Popen", "run"}:
                is_subprocess = True
        if any(keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True for keyword in node.keywords):
            findings.add("CANDIDATE.SAFETY.SHELL_TRUE")
        subprocess_control = False
        if is_subprocess:
            for keyword in node.keywords:
                constant = keyword.value.value if isinstance(keyword.value, ast.Constant) else object()
                if keyword.arg == "start_new_session" and constant not in (False, 0):
                    subprocess_control = True
                elif keyword.arg == "creationflags" and constant != 0:
                    subprocess_control = True
                elif keyword.arg == "preexec_fn" and constant is not None:
                    subprocess_control = True
                elif keyword.arg == "process_group" and constant not in {None, -1}:
                    subprocess_control = True
        if subprocess_control:
            findings.add("CANDIDATE.SAFETY.RESOURCE_CONTROL")
        if is_subprocess and node.args:
            if any(_ssh_literal(value) for value in _literal_strings(node.args[0])):
                findings.add("CANDIDATE.SAFETY.SSH")
            if any(_process_signal_literal(value) for value in _literal_strings(node.args[0])):
                findings.add("CANDIDATE.SAFETY.PROCESS_SIGNAL")
            if any(
                Path(value.strip().split()[0]).name.casefold() in PROCESS_RESOURCE_COMMANDS
                for value in _literal_strings(node.args[0])
                if value.strip()
            ):
                findings.add("CANDIDATE.SAFETY.RESOURCE_CONTROL")
    return findings


def shell_safety_findings(path: Path) -> set[str]:
    findings: set[str] = set()
    text = path.read_text(encoding="utf-8")
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if re.search(r"(^|[;&|]\s*)eval(?:\s|$)", line):
            findings.add("CANDIDATE.SAFETY.EVAL")
        if re.search(r"(^|[;&|]\s*)exec(?:\s|$)", line):
            findings.add("CANDIDATE.SAFETY.EXEC")
        if re.search(r"(^|[;&|]\s*)(?:command\s+)?(?:ssh|scp|sftp)(?:\s|$)", line):
            findings.add("CANDIDATE.SAFETY.SSH")
        if re.search(
            r"(^|[;&|]\s*)(?:command\s+)?(?:/(?:usr/)?bin/)?(?:kill|killall|pkill)(?:\s|$)",
            line,
        ):
            findings.add("CANDIDATE.SAFETY.PROCESS_SIGNAL")
        if re.search(
            r"(^|[;&|]\s*)(?:command\s+)?(?:/(?:usr/)?bin/)?(?:renice|setsid|taskset|ulimit)(?:\s|$)",
            line,
        ):
            findings.add("CANDIDATE.SAFETY.RESOURCE_CONTROL")
    return findings


def check_scripts_and_safety(root: Path, candidate: Path, skill: str) -> tuple[list[Check], list[Path]]:
    syntax_failures: list[Path] = []
    safety_files: dict[str, list[Path]] = {name: [] for name in SAFETY_CHECKS}
    python_files = sorted(candidate.rglob("*.py")) if candidate.is_dir() else []
    for path in python_files:
        try:
            text = path.read_text(encoding="utf-8")
            compile(text, safe_relative_label(path, candidate, "candidate.py"), "exec")
            findings = python_safety_findings(path)
        except (OSError, UnicodeError, SyntaxError, ValueError):
            syntax_failures.append(path)
            findings = set()
        for code in findings:
            safety_files[code].append(path)

    for path in sorted(candidate.rglob("*")) if candidate.is_dir() else []:
        if not path.is_file():
            continue
        if path.suffix.casefold() in {".sh", ".bash"}:
            try:
                findings = shell_safety_findings(path)
            except (OSError, UnicodeError):
                syntax_failures.append(path)
                findings = set()
            for code in findings:
                safety_files[code].append(path)
        if path.suffix.casefold() in {".pkl", ".pickle"}:
            safety_files["CANDIDATE.SAFETY.PICKLE_ARTIFACT"].append(path)

    prefix = f"candidates/{skill}"
    checks = [
        outcome_check(
            "CANDIDATE.SCRIPTS.SYNTAX",
            not syntax_failures,
            "Candidate Python sources compile without writing bytecode.",
            "A candidate source is unreadable or fails syntax compilation.",
            next_action="Repair every candidate source before running private tests.",
            evidence=(file_evidence(path, root, prefix + "/source.py") for path in syntax_failures),
        )
    ]
    messages = {
        "CANDIDATE.SAFETY.EVAL": "dynamic eval",
        "CANDIDATE.SAFETY.EXEC": "dynamic exec",
        "CANDIDATE.SAFETY.OS_SYSTEM": "os.system",
        "CANDIDATE.SAFETY.SHELL_TRUE": "shell-enabled subprocess",
        "CANDIDATE.SAFETY.SSH": "direct remote-shell operation",
        "CANDIDATE.SAFETY.PICKLE_LOAD": "unsafe pickle loading",
        "CANDIDATE.SAFETY.PICKLE_ARTIFACT": "committed pickle artifact",
        "CANDIDATE.SAFETY.PROCESS_SIGNAL": "cross-process signal control",
        "CANDIDATE.SAFETY.PROCESS_SPAWN": "unbounded low-level process spawning",
        "CANDIDATE.SAFETY.MULTIPROCESSING": "multiprocessing surface",
        "CANDIDATE.SAFETY.CTYPES": "native ctypes surface",
        "CANDIDATE.SAFETY.RESOURCE_CONTROL": "resource or process-control surface",
    }
    for code in SAFETY_CHECKS:
        paths = sorted(set(safety_files[code]))
        checks.append(
            outcome_check(
                code,
                not paths,
                f"The candidate contains no {messages[code]} surface.",
                f"The candidate contains a forbidden {messages[code]} surface.",
                next_action="Replace the unsafe surface with a deterministic, non-shell, fail-closed adapter.",
                evidence=(file_evidence(path, root, prefix + "/source") for path in paths),
            )
        )
    return checks, python_files


SEATBELT_PROBE_SOURCE = '''
from pathlib import Path
import builtins
import json
import os
import socket
import subprocess
import sys

workspace_input = Path(sys.argv[1])
workspace_output = Path(sys.argv[2])
host_read_marker = Path(sys.argv[3])
write_paths = [Path(value) for value in sys.argv[4:8]]
result = {}

def attempt(name, operation):
    try:
        operation()
    except PermissionError:
        result[name] = "denied"
    except Exception:
        result[name] = "unexpected-error"
    else:
        result[name] = "allowed"

def workspace_read():
    value = workspace_input.read_text(encoding="utf-8")
    if value != "validator-workspace-input":
        raise ValueError("unexpected workspace input")

attempt("workspace_read", workspace_read)
attempt("workspace_write", lambda: workspace_output.write_text("validator-workspace-output", encoding="utf-8"))

def builtin_read():
    with builtins.open(host_read_marker, "r", encoding="utf-8") as handle:
        handle.read()

attempt("host_read_builtins", builtin_read)

def os_read():
    descriptor = os.open(host_read_marker, os.O_RDONLY)
    try:
        os.read(descriptor, 256)
    finally:
        os.close(descriptor)

attempt("host_read_os", os_read)
attempt("host_read_pathlib", lambda: host_read_marker.read_text(encoding="utf-8"))
read_child_code = "from pathlib import Path; import sys; p=Path(sys.argv[1]);\\ntry: p.read_text(encoding='utf-8')\\nexcept PermissionError: print('denied')\\nelse: print('allowed')"
try:
    child = subprocess.run(
        [sys.executable, "-c", read_child_code, str(host_read_marker)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    result["host_read_child"] = child.stdout.strip() if child.returncode == 0 else "child-error"
except Exception:
    result["host_read_child"] = "unexpected-error"

def builtin_write():
    with builtins.open(write_paths[0], "w", encoding="utf-8"):
        pass

attempt("host_write_builtins", builtin_write)

def os_write():
    descriptor = os.open(write_paths[1], os.O_WRONLY | os.O_CREAT, 0o600)
    os.close(descriptor)

attempt("host_write_os", os_write)
attempt("host_write_pathlib", lambda: write_paths[2].write_text("outside", encoding="utf-8"))
write_child_code = "from pathlib import Path; import sys; p=Path(sys.argv[1]);\\ntry: p.write_text('child', encoding='utf-8')\\nexcept PermissionError: print('denied')\\nelse: print('allowed')"
try:
    child = subprocess.run(
        [sys.executable, "-c", write_child_code, str(write_paths[3])],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    result["host_write_child"] = child.stdout.strip() if child.returncode == 0 else "child-error"
except Exception:
    result["host_write_child"] = "unexpected-error"

def network_bind():
    sock = socket.socket()
    try:
        sock.bind(("127.0.0.1", 0))
    finally:
        sock.close()

def network_connect():
    sock = socket.socket()
    try:
        sock.connect(("127.0.0.1", 9))
    finally:
        sock.close()

attempt("network_bind", network_bind)
attempt("network_connect", network_connect)
expected = {
    "workspace_read": "allowed",
    "workspace_write": "allowed",
    "host_read_builtins": "denied",
    "host_read_os": "denied",
    "host_read_pathlib": "denied",
    "host_read_child": "denied",
    "host_write_builtins": "denied",
    "host_write_os": "denied",
    "host_write_pathlib": "denied",
    "host_write_child": "denied",
    "network_bind": "denied",
    "network_connect": "denied",
}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result == expected else 97)
'''

SEATBELT_PROBE_EXPECTED = {
    "workspace_read": "allowed",
    "workspace_write": "allowed",
    "host_read_builtins": "denied",
    "host_read_os": "denied",
    "host_read_pathlib": "denied",
    "host_read_child": "denied",
    "host_write_builtins": "denied",
    "host_write_os": "denied",
    "host_write_pathlib": "denied",
    "host_write_child": "denied",
    "network_bind": "denied",
    "network_connect": "denied",
}


def parse_seatbelt_probe(stdout: bytes) -> dict[str, str] | None:
    try:
        value = strict_json.loads_object(
            stdout,
            "seatbelt-probe.json",
            max_bytes=SANDBOX_OUTPUT_LIMIT_BYTES,
        )
    except strict_json.StrictJSONError:
        return None
    if set(value) != set(SEATBELT_PROBE_EXPECTED):
        return None
    if not all(isinstance(key, str) and isinstance(item, str) for key, item in value.items()):
        return None
    return value


def probe_control_statuses(result: dict[str, str] | None) -> dict[str, str]:
    def status(keys: tuple[str, ...]) -> str:
        if result is None:
            return "fail"
        return "pass" if all(result.get(key) == SEATBELT_PROBE_EXPECTED[key] for key in keys) else "fail"

    return {
        "workspace_io_enforcement": status(("workspace_read", "workspace_write")),
        "host_read_enforcement": status(
            ("host_read_builtins", "host_read_os", "host_read_pathlib", "host_read_child")
        ),
        "host_write_enforcement": status(
            ("host_write_builtins", "host_write_os", "host_write_pathlib", "host_write_child")
        ),
        "network_enforcement": status(("network_bind", "network_connect")),
        "subprocess_inheritance_enforcement": status(("host_read_child", "host_write_child")),
    }


def seatbelt_backend_identity() -> tuple[str, str] | None:
    if sys.platform != "darwin":
        return None
    try:
        stat = SANDBOX_EXEC.stat()
    except OSError:
        return None
    digest = sha256_file(SANDBOX_EXEC)
    version = platform.mac_ver()[0]
    if not SANDBOX_EXEC.is_file() or not os.access(SANDBOX_EXEC, os.X_OK):
        return None
    if stat.st_uid != 0 or digest is None or not version:
        return None
    return f"macos-{version}", digest


def _seatbelt_path(path: Path) -> str:
    value = str(path.resolve())
    if any(character in value for character in {'"', "\n", "\r"}):
        raise ValueError("path cannot be represented in a Seatbelt profile")
    return value


def _path_ancestors(path: Path) -> tuple[Path, ...]:
    current = path.resolve()
    result: list[Path] = []
    while current != current.parent:
        current = current.parent
        result.append(current)
    return tuple(reversed(result))


def trusted_python_runtime_roots() -> tuple[Path, ...] | None:
    """Return bounded runtime roots or fail closed for a user/project Python."""

    approved = (Path("/Library"), Path("/System"), Path("/usr"), Path("/opt"))
    roots = {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()}
    executable = Path(sys.executable).resolve()
    if not any(executable == root or root in executable.parents for root in roots):
        roots.add(executable.parent)
    for root in roots:
        if not any(root == parent or parent in root.parents for parent in approved):
            return None
    return tuple(sorted(roots, key=str))


def seatbelt_profile(workspace: Path) -> str:
    runtime_roots = trusted_python_runtime_roots()
    if runtime_roots is None:
        raise ValueError("the active Python runtime is outside trusted system roots")
    resolved_workspace = workspace.resolve()
    timezone_root = Path("/private/var/db/timezone")
    read_roots = (*runtime_roots, Path("/System"), Path("/usr/lib"), timezone_root)
    metadata_paths: set[Path] = set(_path_ancestors(resolved_workspace))
    for path in read_roots:
        metadata_paths.update(_path_ancestors(path))
    metadata_paths.add(Path("/dev"))

    lines = [
        "(version 1)",
        "(allow default)",
        "(deny network*)",
        "(deny file-read*)",
        '(allow file-read* (literal "/"))',
    ]
    for path in sorted(metadata_paths, key=lambda item: (len(item.parts), str(item))):
        if path != Path("/"):
            lines.append(f'(allow file-read-metadata (literal "{_seatbelt_path(path)}"))')
    lines.append(f'(allow file-read* (subpath "{_seatbelt_path(resolved_workspace)}"))')
    for path in read_roots:
        lines.append(f'(allow file-read* (subpath "{_seatbelt_path(path)}"))')
    lines.extend(
        [
            '(allow file-read* (literal "/dev/null"))',
            '(allow file-read* (literal "/dev/urandom"))',
            "(deny file-write*)",
            f'(allow file-write* (subpath "{_seatbelt_path(resolved_workspace)}"))',
        ]
    )
    return "\n".join(lines) + "\n"


def current_user_process_count() -> int | None:
    try:
        result = subprocess.run(
            ["/bin/ps", "-U", str(os.getuid()), "-o", "pid="],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return sum(bool(line.strip()) for line in result.stdout.splitlines())


def subprocess_resource_limits() -> tuple[tuple[int, int, str], ...]:
    process_count = current_user_process_count()
    requested = {
        "cpu-seconds": (resource.RLIMIT_CPU, 30),
        "file-size-bytes": (resource.RLIMIT_FSIZE, 16 * 1024 * 1024),
        "open-files": (resource.RLIMIT_NOFILE, 128),
        "processes": (
            resource.RLIMIT_NPROC,
            min(4096, (process_count + 64) if process_count is not None else 1024),
        ),
    }
    limits: list[tuple[int, int, str]] = []
    for label, (kind, target) in requested.items():
        soft, hard = resource.getrlimit(kind)
        effective = target
        if hard != resource.RLIM_INFINITY:
            effective = min(effective, hard)
        if soft != resource.RLIM_INFINITY:
            effective = min(effective, soft)
        if effective < 1:
            raise ValueError(f"no usable {label} resource limit")
        limits.append((kind, int(effective), label))
    return tuple(limits)


def resource_limits_sha256(limits: tuple[tuple[int, int, str], ...]) -> str:
    projection = {label: value for _kind, value, label in limits}
    return sha256_bytes(json.dumps(projection, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def apply_subprocess_resource_limits(limits: tuple[tuple[int, int, str], ...]) -> None:
    for kind, value, _label in limits:
        resource.setrlimit(kind, (value, value))


def read_bounded_stream(handle: Any) -> tuple[bytes, bool]:
    handle.flush()
    handle.seek(0, os.SEEK_END)
    overflow = handle.tell() > SANDBOX_OUTPUT_LIMIT_BYTES
    handle.seek(0)
    return handle.read(SANDBOX_OUTPUT_LIMIT_BYTES), overflow


def run_bounded_command(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    limits: tuple[tuple[int, int, str], ...],
) -> tuple[int, bytes, bytes, bool]:
    try:
        stdout_handle = tempfile.TemporaryFile(prefix=".candidate-stdout-", dir=cwd)
        stderr_handle = tempfile.TemporaryFile(prefix=".candidate-stderr-", dir=cwd)
    except OSError:
        return 1, b"", b"", False
    try:
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=environment,
                stdout=stdout_handle,
                stderr=stderr_handle,
                start_new_session=True,
                preexec_fn=lambda: apply_subprocess_resource_limits(limits),
            )
        except (OSError, subprocess.SubprocessError):
            return 1, b"", b"", False
        timed_out = False
        try:
            process.communicate(timeout=SANDBOX_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
        stdout, stdout_overflow = read_bounded_stream(stdout_handle)
        stderr, stderr_overflow = read_bounded_stream(stderr_handle)
        if timed_out:
            return 124, stdout, stderr, True
        if stdout_overflow or stderr_overflow:
            return 125, stdout, stderr, True
        return process.returncode, stdout, stderr, True
    finally:
        stdout_handle.close()
        stderr_handle.close()


def sandbox_environment(workspace: Path, candidate: Path) -> dict[str, str]:
    home = workspace / "home"
    temporary = workspace / "tmp"
    cache = workspace / "cache"
    for path in (home, temporary, cache):
        path.mkdir(exist_ok=True)
    return {
        "HOME": str(home),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": str(candidate),
        "TMPDIR": str(temporary),
        "TZ": "UTC",
        "XDG_CACHE_HOME": str(cache),
    }


def copy_candidate_tree(source: Path, destination: Path) -> Path:
    return shutil.copytree(source, destination, symlinks=True)


def no_execution_isolation(level: str, message: str, next_action: str) -> IsolationDecision:
    return IsolationDecision(
        check=Check(
            "CANDIDATE.TESTS.ISOLATION_BACKEND",
            "info" if level == "L0" else "critical",
            "not-run",
            message,
            next_action,
        ),
        backend_status="not-required" if level == "L0" else "not-run",
    )


def blocked_isolation(message: str, next_action: str) -> IsolationDecision:
    return IsolationDecision(
        check=Check(
            "CANDIDATE.TESTS.ISOLATION_BACKEND",
            "critical",
            "blocked",
            message,
            next_action,
        ),
        backend_status="unavailable",
    )


def isolated_private_test_run(
    candidate: Path,
    mode: str,
    hooks: list[Path],
) -> tuple[IsolationDecision, Check]:
    identity = seatbelt_backend_identity()
    if identity is None:
        isolation = blocked_isolation(
            "No trusted validator-controlled isolation backend is available for L1.",
            "Run L1 on a supported host with a root-owned sandbox-exec backend or add a reviewed Linux backend.",
        )
        result = Check(
            "CANDIDATE.TESTS.RESULT",
            "critical",
            "not-run",
            "Candidate-private tests were not started because isolation is unavailable.",
            "Provide a trusted validator-controlled isolation backend and rerun L1.",
        )
        return isolation, result

    backend_version, backend_digest = identity
    with tempfile.TemporaryDirectory(prefix="vibe-candidate-seatbelt-") as raw_temporary:
        base = Path(raw_temporary).resolve()
        workspace = base / "workspace"
        workspace.mkdir()
        isolated_candidate = workspace / "candidate"
        try:
            profile = seatbelt_profile(workspace)
            limits = subprocess_resource_limits()
        except (OSError, ValueError, resource.error):
            isolation = blocked_isolation(
                "A trusted Python read allowlist or bounded resource-limit profile could not be established.",
                "Use a system Python runtime under an approved root and a host with usable POSIX resource limits.",
            )
            result = Check(
                "CANDIDATE.TESTS.RESULT",
                "critical",
                "not-run",
                "Candidate-private tests were not started because the bounded runtime profile is unavailable.",
                "Provide a trusted runtime and usable resource limits, then rerun L1.",
            )
            return isolation, result

        profile_digest = sha256_bytes(profile.encode("utf-8"))
        limits_digest = resource_limits_sha256(limits)
        source_before = candidate_tree_sha256(candidate)
        setup_transcript = bytearray()
        try:
            copy_candidate_tree(candidate, isolated_candidate)
        except OSError:
            source_after = None
            copied = None
            setup_transcript.extend(b"candidate-copy-failed")
        else:
            source_after = candidate_tree_sha256(candidate)
            copied = candidate_tree_sha256(isolated_candidate)
        if source_before is None or source_before != source_after or source_before != copied:
            setup_transcript.extend(b"candidate-copy-integrity-failed")
            transcript_digest = sha256_bytes(bytes(setup_transcript))
            isolation = IsolationDecision(
                check=Check(
                    "CANDIDATE.TESTS.ISOLATION_BACKEND",
                    "critical",
                    "blocked",
                    "The isolated candidate copy could not be bound to the source tree hash.",
                    "Stabilize the candidate tree and rerun L1 without concurrent mutation.",
                    evidence=(
                        {"label": "seatbelt-profile", "sha256": profile_digest},
                        {"label": "process-resource-limits", "sha256": limits_digest},
                        {"label": "isolation-setup-transcript", "sha256": transcript_digest},
                    ),
                ),
                backend_status="setup-failed",
                backend_id=SANDBOX_BACKEND_ID,
                backend_version=backend_version,
                backend_sha256=backend_digest,
                profile_sha256=profile_digest,
                source_tree_sha256=source_before,
                isolated_copy_sha256=copied,
            )
            result = Check(
                "CANDIDATE.TESTS.RESULT",
                "critical",
                "not-run",
                "Candidate-private tests were not started because isolated copy integrity failed.",
                "Stabilize the candidate tree and rerun L1.",
            )
            return isolation, result

        environment = sandbox_environment(workspace, isolated_candidate)
        workspace_input = workspace / "probe-workspace-input"
        workspace_output = workspace / "probe-workspace-output"
        host_read_marker = base / "probe-host-read"
        workspace_input.write_text("validator-workspace-input", encoding="utf-8")
        host_read_marker.write_text("validator-host-read-marker", encoding="utf-8")
        outside_markers = [
            base / name
            for name in ("probe-write-builtin", "probe-write-os", "probe-write-pathlib", "probe-write-child")
        ]
        probe_command = [
            str(SANDBOX_EXEC),
            "-p",
            profile,
            sys.executable,
            "-c",
            SEATBELT_PROBE_SOURCE,
            str(workspace_input),
            str(workspace_output),
            str(host_read_marker),
            *(str(path) for path in outside_markers),
        ]
        probe_code, probe_stdout, probe_stderr, probe_attempted = run_bounded_command(
            probe_command,
            cwd=workspace,
            environment=environment,
            limits=limits,
        )
        probe_digest = sha256_bytes(probe_stdout + b"\0" + probe_stderr)
        probe_result = parse_seatbelt_probe(probe_stdout)
        controls = probe_control_statuses(probe_result)
        secret = b"validator-host-read-marker"
        probe_passed = (
            probe_attempted
            and probe_code == 0
            and not probe_stderr
            and probe_result == SEATBELT_PROBE_EXPECTED
            and workspace_input.read_text(encoding="utf-8") == "validator-workspace-input"
            and workspace_output.read_text(encoding="utf-8") == "validator-workspace-output"
            and host_read_marker.read_text(encoding="utf-8") == "validator-host-read-marker"
            and not any(marker.exists() for marker in outside_markers)
            and secret not in probe_stdout
            and secret not in probe_stderr
            and all(value == "pass" for value in controls.values())
        )
        isolation_evidence = (
            {"label": "sandbox-exec-binary", "sha256": backend_digest},
            {"label": "seatbelt-profile", "sha256": profile_digest},
            {"label": "process-resource-limits", "sha256": limits_digest},
            {"label": "candidate-source-tree", "sha256": source_before},
            {"label": "isolated-candidate-copy", "sha256": copied},
            {"label": "seatbelt-enforcement-probe", "sha256": probe_digest},
        )
        if not probe_passed:
            isolation = IsolationDecision(
                check=Check(
                    "CANDIDATE.TESTS.ISOLATION_BACKEND",
                    "critical",
                    "blocked",
                    "The Seatbelt probe did not prove workspace I/O, host-read, host-write, inherited-child, and network controls.",
                    "Repair or replace the isolation backend; do not execute candidate code.",
                    evidence=isolation_evidence,
                ),
                backend_status="probe-failed",
                backend_id=SANDBOX_BACKEND_ID,
                backend_version=backend_version,
                backend_sha256=backend_digest,
                profile_sha256=profile_digest,
                source_tree_sha256=source_before,
                isolated_copy_sha256=copied,
                enforcement_probe_status="fail",
                enforcement_probe_sha256=probe_digest,
                process_resource_limits_status="applied" if probe_attempted else "not-run",
                process_resource_limits_sha256=limits_digest if probe_attempted else None,
                process_new_session_status="applied" if probe_attempted else "not-run",
                **controls,
            )
            result = Check(
                "CANDIDATE.TESTS.RESULT",
                "critical",
                "not-run",
                "Candidate-private tests were not started because the enforcement probe failed.",
                "Repair or replace the isolation backend and rerun L1.",
            )
            return isolation, result

        commands: list[list[str]]
        if mode == "unittest-discover":
            commands = [[sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]]
        else:
            commands = [[sys.executable, PurePosixPath("scripts", path.name).as_posix()] for path in hooks]
        stdout_transcript = bytearray()
        stderr_transcript = bytearray()
        returncodes: list[int] = []
        passed = True
        attempted = False
        for command in commands:
            sandboxed = [str(SANDBOX_EXEC), "-p", profile, *command]
            returncode, stdout, stderr, started = run_bounded_command(
                sandboxed,
                cwd=isolated_candidate,
                environment=environment,
                limits=limits,
            )
            attempted = attempted or started
            stdout_transcript.extend(stdout)
            stderr_transcript.extend(stderr)
            returncodes.append(returncode)
            if returncode != 0:
                passed = False
                break
        isolation = IsolationDecision(
            check=Check(
                "CANDIDATE.TESTS.ISOLATION_BACKEND",
                "critical",
                "pass",
                "The validator-controlled profile passed workspace I/O, host-read, host-write, inherited-child, network, and bounded-resource probes.",
                evidence=isolation_evidence,
            ),
            backend_status="enforced",
            backend_id=SANDBOX_BACKEND_ID,
            backend_version=backend_version,
            backend_sha256=backend_digest,
            profile_sha256=profile_digest,
            source_tree_sha256=source_before,
            isolated_copy_sha256=copied,
            enforcement_probe_status="pass",
            enforcement_probe_sha256=probe_digest,
            process_resource_limits_status="applied",
            process_resource_limits_sha256=limits_digest,
            process_new_session_status="applied",
            candidate_test_execution=(
                "attempted-under-enforced-backend" if attempted else "not-run"
            ),
            **controls,
        )
        result = outcome_check(
            "CANDIDATE.TESTS.RESULT",
            passed and attempted,
            "Candidate-private tests pass in the copied workspace under the probed Seatbelt and process-limit profile.",
            "Candidate-private tests fail, time out, or cannot start under the probed Seatbelt and process-limit profile.",
            next_action="Fix the candidate-private tests without weakening the isolation or validation gates.",
            evidence=(
                {
                    "label": "candidate-private-test-stdout",
                    "sha256": sha256_bytes(bytes(stdout_transcript)),
                },
                {
                    "label": "candidate-private-test-stderr",
                    "sha256": sha256_bytes(bytes(stderr_transcript)),
                },
                {
                    "label": "candidate-private-test-return-codes:" + ",".join(str(code) for code in returncodes),
                    "sha256": None,
                },
            ),
        )
        return isolation, result


def private_test_hooks(candidate: Path) -> tuple[str | None, list[Path]]:
    tests = candidate / "tests"
    test_files = sorted(tests.glob("test_*.py")) if tests.is_dir() else []
    if test_files:
        return "unittest-discover", test_files
    scripts = candidate / "scripts"
    test_files = sorted(scripts.glob("test_*.py")) if scripts.is_dir() else []
    return ("script", test_files) if test_files else (None, [])


def check_private_tests(
    root: Path,
    candidate: Path,
    skill: str,
    level: str,
    *,
    preflight_allowed: bool,
) -> tuple[list[Check], IsolationDecision]:
    mode, hooks = private_test_hooks(candidate)
    prefix = f"candidates/{skill}"
    checks = [
        outcome_check(
            "CANDIDATE.TESTS.HOOK",
            bool(hooks),
            "The candidate provides a private deterministic test hook.",
            "The candidate provides no tests/test_*.py or scripts/test_*.py hook.",
            next_action="Add at least one offline candidate-private test hook.",
            evidence=(file_evidence(path, root, prefix + "/test.py") for path in hooks),
        )
    ]
    if level == "L0":
        isolation = no_execution_isolation(
            level,
            "L0 does not execute candidate code, so no isolation backend is started.",
            "Run L1 on a host with a trusted validator-controlled isolation backend.",
        )
        checks.append(isolation.check)
        checks.append(
            Check(
                "CANDIDATE.TESTS.RESULT",
                "info",
                "not-run",
                "L0 verifies the test hook but does not execute candidate code.",
                "Run L1 before requesting promotion review.",
            )
        )
        return checks, isolation
    if not hooks:
        isolation = no_execution_isolation(
            level,
            "The isolation backend was not started because no private test hook exists.",
            "Add an offline private test hook before requesting isolated L1 execution.",
        )
        checks.append(isolation.check)
        checks.append(
            Check(
                "CANDIDATE.TESTS.RESULT",
                "critical",
                "fail",
                "Candidate-private tests cannot run without a test hook.",
                "Add an offline test hook and rerun L1.",
            )
        )
        return checks, isolation
    if not preflight_allowed:
        isolation = no_execution_isolation(
            level,
            "The isolation backend was not started because a pre-execution gate did not pass.",
            "Resolve every failed or blocked pre-execution gate before retrying L1.",
        )
        checks.append(isolation.check)
        checks.append(
            Check(
                "CANDIDATE.TESTS.RESULT",
                "critical",
                "not-run",
                "Candidate-private tests were not started because a pre-execution gate did not pass.",
                "Resolve every failed or blocked pre-execution gate before retrying L1.",
            )
        )
        return checks, isolation

    assert mode is not None
    isolation, result = isolated_private_test_run(candidate, mode, hooks)
    checks.extend((isolation.check, result))
    return checks, isolation


def normalize_changed_file(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def load_changed_files_fixture(path: Path) -> list[str]:
    value = strict_json.load_value(
        path,
        path.name,
        max_bytes=CHANGED_FILES_LIMIT_BYTES,
    )
    if isinstance(value, dict):
        value = value.get("changed_files")
    if not isinstance(value, list):
        raise ValueError("changed file fixture must be a list")
    result: list[str] = []
    for item in value:
        normalized = normalize_changed_file(item)
        if normalized is None:
            raise ValueError("changed file fixture contains an unsafe path")
        result.append(normalized)
    return sorted(set(result))


def git_changed_files(root: Path, base_ref: str) -> tuple[list[str] | None, str | None]:
    if not SAFE_BASE_REF.fullmatch(base_ref) or base_ref.startswith("-"):
        return None, "invalid-ref"
    try:
        verify = subprocess.run(
            ["git", "rev-parse", "--verify", f"{base_ref}^{{commit}}"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if verify.returncode != 0:
            return None, "unavailable-ref"
        commands = (
            ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base_ref}...HEAD"],
            ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB"],
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
            ["git", "ls-files", "--others", "--exclude-standard"],
        )
        changed: set[str] = set()
        for command in commands:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30, check=False)
            if result.returncode != 0:
                return None, "git-query-failed"
            for line in result.stdout.splitlines():
                normalized = normalize_changed_file(line.strip())
                if normalized is None:
                    return None, "unsafe-git-path"
                changed.add(normalized)
        return sorted(changed), None
    except (OSError, subprocess.SubprocessError):
        return None, "git-unavailable"


def check_ownership(
    root: Path,
    skill: str,
    base_ref: str | None,
    changed_fixture: Path | None,
) -> tuple[Check, str]:
    if base_ref and changed_fixture:
        return (
            Check(
                "CANDIDATE.OWNERSHIP.CHANGED_FILES",
                "critical",
                "fail",
                "Two changed-file sources were supplied.",
                "Use either --base-ref or --changed-files, not both.",
            ),
            "fixture",
        )
    mode = "not-requested"
    changed: list[str] = []
    if changed_fixture is not None:
        mode = "fixture"
        try:
            changed = load_changed_files_fixture(changed_fixture)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            return (
                Check(
                    "CANDIDATE.OWNERSHIP.CHANGED_FILES",
                    "critical",
                    "fail",
                    "The explicit changed-file fixture is malformed or unsafe.",
                    "Provide a JSON list of safe repository-relative paths.",
                ),
                mode,
            )
    elif base_ref is not None:
        mode = "git"
        changed_result, error = git_changed_files(root, base_ref)
        if error == "invalid-ref":
            return (
                Check(
                    "CANDIDATE.OWNERSHIP.CHANGED_FILES",
                    "critical",
                    "fail",
                    "The base reference is syntactically unsafe.",
                    "Use a simple reviewed Git commit or branch reference.",
                ),
                mode,
            )
        if changed_result is None:
            return (
                Check(
                    "CANDIDATE.OWNERSHIP.CHANGED_FILES",
                    "critical",
                    "blocked",
                    "Git ownership evidence is unavailable.",
                    "Provide a resolvable base reference or an explicit changed-file fixture.",
                ),
                mode,
            )
        changed = changed_result
    else:
        return (
            Check(
                "CANDIDATE.OWNERSHIP.CHANGED_FILES",
                "info",
                "pass",
                "No ownership diff was requested; candidate tree checks remain in force.",
            ),
            mode,
        )

    allowed_prefix = f"candidates/{skill}/"
    unauthorized = [item for item in changed if not item.startswith(allowed_prefix)]
    evidence = tuple({"label": item, "sha256": sha256_file(root / item) if (root / item).is_file() else None} for item in unauthorized)
    return (
        outcome_check(
            "CANDIDATE.OWNERSHIP.CHANGED_FILES",
            not unauthorized,
            "All declared changes remain inside the candidate-owned directory.",
            "The candidate work package modifies a shared or foreign file.",
            next_action="Revert shared-file edits and submit them only as a promotion delta request.",
            evidence=evidence,
        ),
        mode,
    )


def git_head(root: Path | None) -> str | None:
    if root is None:
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip().casefold()
    return value if result.returncode == 0 and re.fullmatch(r"[a-f0-9]{40,64}", value) else None


def summarize(checks: list[Check]) -> dict[str, int]:
    return {
        "total": len(checks),
        "passed": sum(item.status == "pass" for item in checks),
        "failed": sum(item.status == "fail" for item in checks),
        "blocked": sum(item.status == "blocked" for item in checks),
        "not_run": sum(item.status == "not-run" for item in checks),
    }


def overall_status(checks: list[Check]) -> str:
    if any(item.status == "fail" for item in checks):
        return "fail"
    if any(item.status == "blocked" for item in checks):
        return "blocked"
    return "pass"


def build_report(
    skill: str,
    level: str,
    base_ref: str | None,
    head_commit: str | None,
    changed_mode: str,
    checks: list[Check],
    *,
    isolation: IsolationDecision | None = None,
) -> dict[str, Any]:
    boundary = isolation or IsolationDecision(
        check=Check(
            "CANDIDATE.TESTS.ISOLATION_BACKEND",
            "info",
            "not-run",
            "The isolation backend was not evaluated.",
            "Resolve repository discovery before requesting L1 execution.",
        ),
        backend_status="not-required" if level == "L0" else "not-run",
    )
    limitations = [
        "Candidate validation does not activate the Skill or authorize promotion.",
        "Candidate validation does not establish scientific validity or acceptance.",
        "The validation report is not a complete security sandbox; an L1 pass records only the observed "
        "workspace I/O, non-allowlisted host-read denial, outside-workspace write denial, network denial, "
        "child inheritance, and RLIMIT "
        "configuration under the hashed validator-controlled profiles.",
        "Seatbelt and RLIMIT probes do not establish complete VM isolation, same-UID signal isolation, "
        "complete process isolation, resource-exhaustion immunity, or scientific validity.",
    ]
    if level == "L0":
        limitations.append("L0 validates the private test hook but does not execute candidate code.")
    return {
        "contract_name": "validation-report",
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "validate_candidate", "version": TOOL_VERSION},
        "subject": {
            "kind": "candidate-skill",
            "skill_id": skill,
            "candidate_label": f"candidates/{skill}",
        },
        "source": {
            "base_ref": base_ref,
            "head_commit": head_commit,
            "changed_files_mode": changed_mode,
        },
        "requested_level": level,
        "generated_utc": generated_utc(),
        "status": overall_status(checks),
        "routing_state": "planned-not-routable",
        "promotion_authorized": False,
        "execution_boundary": {
            "report_is_complete_security_sandbox": False,
            "backend_status": boundary.backend_status,
            "backend_id": boundary.backend_id,
            "backend_version": boundary.backend_version,
            "backend_sha256": boundary.backend_sha256,
            "profile_sha256": boundary.profile_sha256,
            "source_tree_sha256": boundary.source_tree_sha256,
            "isolated_copy_sha256": boundary.isolated_copy_sha256,
            "enforcement_probe_status": boundary.enforcement_probe_status,
            "enforcement_probe_sha256": boundary.enforcement_probe_sha256,
            "workspace_io_enforcement": boundary.workspace_io_enforcement,
            "host_read_enforcement": boundary.host_read_enforcement,
            "host_write_enforcement": boundary.host_write_enforcement,
            "network_enforcement": boundary.network_enforcement,
            "subprocess_inheritance_enforcement": boundary.subprocess_inheritance_enforcement,
            "process_resource_limits_status": boundary.process_resource_limits_status,
            "process_resource_limits_sha256": boundary.process_resource_limits_sha256,
            "process_new_session_status": boundary.process_new_session_status,
            "candidate_test_execution": boundary.candidate_test_execution,
        },
        "summary": summarize(checks),
        "checks": [item.as_dict() for item in checks],
        "limitations": limitations,
    }


def validate_report(report: dict[str, Any]) -> None:
    schema = strict_json.load_object(REPORT_SCHEMA, REPORT_SCHEMA.name)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        raise ValueError("generated validation report does not match its schema")
    checks = report.get("checks")
    if not isinstance(checks, list):
        raise ValueError("generated validation report has no check list")
    check_ids: list[str] = []
    statuses: list[str] = []
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("generated validation report has a malformed check")
        check_id = check.get("check_id")
        status = check.get("status")
        next_action = check.get("next_action")
        if not isinstance(check_id, str) or not isinstance(status, str):
            raise ValueError("generated validation report has a malformed check identity")
        if status == "pass" and next_action is not None:
            raise ValueError("passing checks cannot prescribe remediation")
        if status != "pass" and (not isinstance(next_action, str) or not next_action.strip()):
            raise ValueError("non-passing checks require remediation")
        check_ids.append(check_id)
        statuses.append(status)
    if len(check_ids) != len(set(check_ids)):
        raise ValueError("generated validation report contains duplicate checks")
    expected_summary = {
        "total": len(statuses),
        "passed": statuses.count("pass"),
        "failed": statuses.count("fail"),
        "blocked": statuses.count("blocked"),
        "not_run": statuses.count("not-run"),
    }
    if report.get("summary") != expected_summary:
        raise ValueError("generated validation report summary is inconsistent")
    expected_status = "fail" if "fail" in statuses else "blocked" if "blocked" in statuses else "pass"
    if report.get("status") != expected_status:
        raise ValueError("generated validation report status is inconsistent")

    boundary = report.get("execution_boundary")
    if not isinstance(boundary, dict):
        raise ValueError("generated validation report has no execution boundary")
    backend_status = boundary.get("backend_status")
    execution_state = boundary.get("candidate_test_execution")
    backend_fields = (
        boundary.get("backend_id"),
        boundary.get("backend_version"),
        boundary.get("backend_sha256"),
        boundary.get("profile_sha256"),
    )
    tree_hashes = (
        boundary.get("source_tree_sha256"),
        boundary.get("isolated_copy_sha256"),
    )
    probe_status = boundary.get("enforcement_probe_status")
    probe_hash = boundary.get("enforcement_probe_sha256")
    control_fields = (
        boundary.get("workspace_io_enforcement"),
        boundary.get("host_read_enforcement"),
        boundary.get("host_write_enforcement"),
        boundary.get("network_enforcement"),
        boundary.get("subprocess_inheritance_enforcement"),
    )
    limits_status = boundary.get("process_resource_limits_status")
    limits_hash = boundary.get("process_resource_limits_sha256")
    session_status = boundary.get("process_new_session_status")
    if backend_status in {"enforced", "probe-failed", "setup-failed"}:
        if not all(isinstance(value, str) for value in backend_fields):
            raise ValueError("evaluated isolation backend lacks identity or profile evidence")
    elif any(value is not None for value in (*backend_fields, *tree_hashes)):
        raise ValueError("non-evaluated isolation backend cannot publish backend evidence")
    if backend_status in {"enforced", "probe-failed"}:
        if not all(isinstance(value, str) for value in tree_hashes) or tree_hashes[0] != tree_hashes[1]:
            raise ValueError("isolation backend did not bind an exact candidate copy")
        expected_probe = "pass" if backend_status == "enforced" else "fail"
        if probe_status != expected_probe or not isinstance(probe_hash, str):
            raise ValueError("isolation backend has inconsistent enforcement-probe evidence")
    elif probe_status != "not-run" or probe_hash is not None:
        raise ValueError("non-probed isolation backend cannot publish probe evidence")
    if execution_state == "attempted-under-enforced-backend" and backend_status != "enforced":
        raise ValueError("candidate execution lacks a successfully probed backend")
    if backend_status == "enforced":
        if any(value != "pass" for value in control_fields):
            raise ValueError("enforced backend lacks all required control proofs")
        if limits_status != "applied" or not isinstance(limits_hash, str) or session_status != "applied":
            raise ValueError("enforced backend lacks bounded process execution evidence")
    elif backend_status == "probe-failed":
        if any(value not in {"pass", "fail"} for value in control_fields):
            raise ValueError("failed probe must report every attempted control")
        resource_not_run = limits_status == "not-run" and limits_hash is None and session_status == "not-run"
        resource_applied = limits_status == "applied" and isinstance(limits_hash, str) and session_status == "applied"
        if not (resource_not_run or resource_applied):
            raise ValueError("failed probe has inconsistent process-limit evidence")
    else:
        if any(value != "not-run" for value in control_fields):
            raise ValueError("non-probed backend cannot claim individual enforcement")
        if limits_status != "not-run" or limits_hash is not None or session_status != "not-run":
            raise ValueError("non-probed backend cannot claim bounded process execution")
    if report.get("requested_level") == "L0" and (
        backend_status != "not-required" or execution_state != "not-run"
    ):
        raise ValueError("L0 cannot report candidate execution or backend enforcement")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".candidate-report-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def skill_argument(value: str) -> str:
    if not SKILL_ID.fullmatch(value):
        raise argparse.ArgumentTypeError("skill must be a lowercase hyphenated identifier")
    return value


def validate_candidate(
    skill: str,
    candidate_dir: Path,
    level: str,
    base_ref: str | None = None,
    changed_fixture: Path | None = None,
) -> dict[str, Any]:
    candidate = candidate_dir.expanduser().absolute()
    root = locate_repository(candidate)
    checks: list[Check] = []
    changed_mode = "fixture" if changed_fixture else "git" if base_ref else "not-requested"
    if root is None:
        checks.append(
            Check(
                "CANDIDATE.REPOSITORY.ROOT",
                "critical",
                "fail",
                "The candidate repository boundary cannot be established.",
                "Place the candidate in a repository with both canonical registries.",
            )
        )
        return build_report(skill, level, base_ref, None, changed_mode, checks)

    checks.append(
        Check(
            "CANDIDATE.REPOSITORY.ROOT",
            "critical",
            "pass",
            "The candidate repository boundary is established.",
        )
    )
    registry_checks, _software, codes = check_registries(root, skill)
    checks.extend(registry_checks)
    checks.append(check_contract_enums(root, codes))
    checks.append(check_observable_routes(root, skill, codes))
    checks.append(check_operation_route(root, skill))
    checks.extend(check_candidate_content(root, candidate, skill))
    script_checks, _python_files = check_scripts_and_safety(root, candidate, skill)
    checks.extend(script_checks)
    ownership, changed_mode = check_ownership(root, skill, base_ref, changed_fixture)
    checks.append(ownership)
    preflight_allowed = level == "L1" and all(check.status == "pass" for check in checks)
    private_checks, isolation = check_private_tests(
        root,
        candidate,
        skill,
        level,
        preflight_allowed=preflight_allowed,
    )
    checks.extend(private_checks)
    return build_report(
        skill,
        level,
        base_ref,
        git_head(root),
        changed_mode,
        checks,
        isolation=isolation,
    )


def exit_code(report: dict[str, Any]) -> int:
    return {"pass": 0, "fail": 2, "blocked": 3, "error": 4}[report["status"]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=skill_argument, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--base-ref")
    parser.add_argument(
        "--changed-files",
        type=Path,
        help="JSON changed-file fixture for deterministic ownership tests; do not combine with --base-ref",
    )
    parser.add_argument("--level", choices=("L0", "L1"), required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        report = validate_candidate(
            args.skill,
            args.candidate_dir,
            args.level,
            base_ref=args.base_ref,
            changed_fixture=args.changed_files,
        )
        validate_report(report)
        write_report(args.report.expanduser(), report)
    except Exception:
        print("ERROR: candidate validation encountered an internal failure; path details are redacted", file=sys.stderr)
        return 4

    status = report["status"].upper()
    print(f"{status}: candidate validation for {args.skill}; promotion_authorized=false")
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
