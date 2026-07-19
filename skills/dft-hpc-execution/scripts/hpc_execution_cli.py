#!/usr/bin/env python3
"""Offline validation, dry-run rendering, and layered status classification."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import sys
from typing import Any


TOOL_VERSION = "0.1.0-candidate"
MAX_INPUT_BYTES = 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_JSON_NODES = 100_000
MAX_JSON_STRING_CHARS = 262_144
MAX_JSON_NUMBER_CHARS = 128
MAX_PATH_COMPONENTS = 256
SAFE_ID = re.compile(r"^[a-z0-9]+(?:[a-z0-9._-]*[a-z0-9])?$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
EXECUTABLE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
SAFE_LABEL = re.compile(r"^(?![/\\])(?![A-Za-z]:[/\\])(?!.*(?:^|[/\\])\.\.(?:[/\\]|$))[^\x00\r\n]+$")
MEDIA_TYPE = re.compile(r"^[a-z0-9.+-]+/[a-z0-9.+-]+$")
SECRET = re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]")
PRIVATE_PATH = re.compile(r"(?:^|[\s=,:;()\[\]{}\"'])[/\\](?:Users|home|private|tmp|var|Volumes|scratch|gpfs|lustre|mnt|work|project)(?:[/\\]|$)")
SHELLS = {
    "sh", "ash", "bash", "csh", "dash", "fish", "ksh", "tcsh", "zsh",
    "cmd", "cmd.exe", "powershell", "powershell.exe",
}
REQUEST_KEYS = {
    "schema_version", "contract_name", "request_id", "created_utc", "requested_by",
    "workflow_plan_ref", "workflow_step_id", "operation_id", "execution_mode",
    "command_kind", "shell", "argv", "working_directory_label", "environment_profile_id",
    "resources", "inputs", "expected_outputs", "parent_records", "timeout_s",
    "retry_policy", "authorization_requirement", "state", "blocker_codes", "gates", "producer",
}
DECISION_KEYS = {
    "schema_version", "contract_name", "decision_id", "decision_type", "subject_ref",
    "outcome", "scientific_acceptance", "decided_by", "decided_utc", "evidence_ids",
    "evidence_refs", "rationale", "scope_labels", "valid_until_utc", "claim_ceiling",
    "limitations", "producer",
}
LEASE_KEYS = {
    "schema_version", "contract_name", "lease_id", "request_ref",
    "authorization_decision_ref", "issued_by", "issued_utc", "expires_utc",
    "lease_duration_s", "status", "single_use", "grant", "constraints", "producer",
}
FILE_REF_KEYS = {
    "role", "label", "media_type", "format", "format_version", "availability",
    "sha256", "bytes", "sensitivity", "redistribution",
}
RESOURCE_KEYS = {
    "scheduler_profile_id", "nodes", "mpi_ranks", "threads_per_rank", "gpus",
    "memory_mb", "walltime_s",
}
LEASE_RESOURCE_KEYS = {"nodes", "mpi_ranks", "threads_per_rank", "gpus", "memory_mb", "walltime_s"}
GATE_KEYS = {"status", "maximum_action", "claim_ceiling", "checks"}
SIDE_EFFECTS = {
    "read-only", "network-read", "local-write", "local-execution", "remote-read",
    "remote-write", "scheduler-submit", "scheduler-control", "external-publish", "destructive-delete",
}
CLAIMS = {
    "no_positive_claim", "documented_behavior_only", "input_gates_only",
    "technical_run_gates_only", "numerical_candidate_only", "eligible_for_expert_review",
}
EXECUTION_DECISION_CLAIMS = {
    "no_positive_claim", "documented_behavior_only", "input_gates_only",
}
SYNTHETIC_ENVIRONMENT_PROFILES = {"synthetic-qe-env-001"}
SYNTHETIC_SCHEDULER_PROFILES = {
    "local": "synthetic-local-001",
    "slurm": "synthetic-slurm-001",
    "openpbs": "synthetic-pbs-001",
}


class InputFailure(ValueError):
    """A bounded, user-correctable input failure."""


def _duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputFailure("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise InputFailure("non-finite JSON number")


def _parse_integer(token: str) -> int:
    if len(token) > MAX_JSON_NUMBER_CHARS:
        raise InputFailure("JSON number exceeds the bounded token length")
    return int(token)


def _parse_float(token: str) -> float:
    if len(token) > MAX_JSON_NUMBER_CHARS:
        raise InputFailure("JSON number exceeds the bounded token length")
    value = float(token)
    if not math.isfinite(value):
        raise InputFailure("non-finite JSON number")
    return value


def _preflight_json(text: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    string_chars = 0
    for character in text:
        if in_string:
            if escaped:
                escaped = False
                string_chars += 1
            elif character == "\\":
                escaped = True
                string_chars += 1
            elif character == '"':
                in_string = False
            else:
                string_chars += 1
            if string_chars > MAX_JSON_STRING_CHARS:
                raise InputFailure("JSON string exceeds the bounded length")
            continue
        if character == '"':
            in_string = True
            string_chars = 0
        elif character in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise InputFailure("JSON nesting exceeds the bounded depth")
        elif character in "]}":
            depth -= 1


def _validate_json_tree(value: Any) -> None:
    pending: list[tuple[Any, int]] = [(value, 0)]
    nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise InputFailure("JSON structure exceeds the bounded node or depth limit")
        if isinstance(item, dict):
            for key, child in item.items():
                nodes += 1
                if nodes > MAX_JSON_NODES:
                    raise InputFailure("JSON structure exceeds the bounded node limit")
                if len(key) > MAX_JSON_STRING_CHARS or any(0xD800 <= ord(char) <= 0xDFFF for char in key):
                    raise InputFailure("JSON contains an invalid Unicode string")
                pending.append((child, depth + 1))
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
        elif isinstance(item, str) and (
            len(item) > MAX_JSON_STRING_CHARS
            or any(0xD800 <= ord(char) <= 0xDFFF for char in item)
        ):
            raise InputFailure("JSON contains an invalid Unicode string")


def _file_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        stat.S_IFMT(value.st_mode),
        value.st_dev,
        value.st_ino,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _directory_identity(value: os.stat_result) -> tuple[int, int, int]:
    return (stat.S_IFMT(value.st_mode), value.st_dev, value.st_ino)


def _close_descriptor(descriptor: int) -> None:
    try:
        os.close(descriptor)
    except OSError:
        pass


def _canonical_absolute_path(path: Path) -> Path:
    absolute = os.fspath(path)
    if sys.platform == "darwin":
        for alias, target in (("/var", "/private/var"), ("/tmp", "/private/tmp"), ("/etc", "/private/etc")):
            if absolute != alias and not absolute.startswith(alias + os.sep):
                continue
            try:
                metadata = os.lstat(alias)
                link_target = os.readlink(alias)
            except OSError:
                break
            if (
                stat.S_ISLNK(metadata.st_mode)
                and metadata.st_uid == 0
                and link_target in {target, target.lstrip("/")}
            ):
                absolute = target + absolute[len(alias):]
            break
    return Path(absolute)


def _path_anchor_and_components(path: Path) -> tuple[str, list[str]]:
    supplied = Path(os.fspath(path))
    if supplied.is_absolute():
        normalized = _canonical_absolute_path(supplied)
        anchor = normalized.anchor
        components = list(normalized.parts[1:])
    else:
        anchor = "."
        components = list(supplied.parts)
    if (
        not anchor
        or not components
        or len(components) > MAX_PATH_COMPONENTS
        or any(not component or component == "." or "\x00" in component for component in components)
        or components[-1] == ".."
    ):
        raise InputFailure("input path is invalid or exceeds the component limit")
    return anchor, components


def _open_directory_chain(
    path: Path,
) -> tuple[str, list[int], list[tuple[int, str, int, tuple[int, ...]]], str, tuple[int, ...]]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory is None or nonblock is None:
        raise InputFailure("platform cannot establish a stable no-follow directory walk")
    anchor, components = _path_anchor_and_components(path)
    flags = os.O_RDONLY | directory | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)
    descriptors: list[int] = []
    edges: list[tuple[int, str, int, tuple[int, ...]]] = []
    try:
        anchor_before = os.stat(anchor, follow_symlinks=False)
        anchor_fd = os.open(anchor, flags)
        descriptors.append(anchor_fd)
        anchor_opened = os.fstat(anchor_fd)
        anchor_identity = _directory_identity(anchor_opened)
        if not stat.S_ISDIR(anchor_before.st_mode) or _directory_identity(anchor_before) != anchor_identity:
            raise InputFailure("input path anchor changed during traversal")
        current = anchor_fd
        for component in components[:-1]:
            before = os.stat(component, dir_fd=current, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode):
                raise InputFailure("input path contains a non-directory or symlink component")
            child = os.open(component, flags, dir_fd=current)
            descriptors.append(child)
            opened = os.fstat(child)
            opened_identity = _directory_identity(opened)
            if not stat.S_ISDIR(opened.st_mode) or _directory_identity(before) != opened_identity:
                raise InputFailure("input directory component changed during traversal")
            edges.append((current, component, child, opened_identity))
            current = child
        return anchor, descriptors, edges, components[-1], anchor_identity
    except InputFailure:
        for descriptor in reversed(descriptors):
            _close_descriptor(descriptor)
        raise
    except (OSError, ValueError, TypeError) as exc:
        for descriptor in reversed(descriptors):
            _close_descriptor(descriptor)
        raise InputFailure("input path cannot be walked without following symlinks") from exc


def _revalidate_directory_chain(
    anchor: str,
    descriptors: list[int],
    edges: list[tuple[int, str, int, tuple[int, ...]]],
    anchor_identity: tuple[int, ...],
) -> None:
    try:
        anchor_by_name = os.stat(anchor, follow_symlinks=False)
        anchor_by_fd = os.fstat(descriptors[0])
        if (
            not stat.S_ISDIR(anchor_by_name.st_mode)
            or _directory_identity(anchor_by_name) != anchor_identity
            or _directory_identity(anchor_by_fd) != anchor_identity
        ):
            raise InputFailure("input path anchor changed while reading")
        for parent_fd, component, child_fd, opened_identity in edges:
            by_name = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            by_fd = os.fstat(child_fd)
            if (
                not stat.S_ISDIR(by_name.st_mode)
                or not stat.S_ISDIR(by_fd.st_mode)
                or _directory_identity(by_name) != opened_identity
                or _directory_identity(by_fd) != opened_identity
            ):
                raise InputFailure("input directory component changed while reading")
    except InputFailure:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise InputFailure("input directory chain cannot be revalidated") from exc


def _read_stable_bytes(path: Path) -> bytes:
    anchor, descriptors, edges, final_name, anchor_identity = _open_directory_chain(path)
    descriptor: int | None = None
    try:
        parent_fd = descriptors[-1]
        before = os.stat(final_name, dir_fd=parent_fd, follow_symlinks=False)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size < 2
            or before.st_size > MAX_INPUT_BYTES
        ):
            raise InputFailure("input must be one bounded single-link regular file")
        flags = (
            os.O_RDONLY
            | getattr(os, "O_NONBLOCK")
            | getattr(os, "O_NOFOLLOW")
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(final_name, flags, dir_fd=parent_fd)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or opened.st_size < 2
            or opened.st_size > MAX_INPUT_BYTES
            or _file_identity(before) != _file_identity(opened)
        ):
            raise InputFailure("input changed before it could be opened safely")
        blocks: list[bytes] = []
        total = 0
        while True:
            block = os.read(descriptor, min(65536, MAX_INPUT_BYTES + 1 - total))
            if not block:
                break
            blocks.append(block)
            total += len(block)
            if total > MAX_INPUT_BYTES:
                raise InputFailure("input size is outside the 2-byte to 1-MiB limit")
        after_fd = os.fstat(descriptor)
        final_path = os.stat(final_name, dir_fd=parent_fd, follow_symlinks=False)
        _revalidate_directory_chain(anchor, descriptors, edges, anchor_identity)
        raw = b"".join(blocks)
        identity = _file_identity(opened)
        if (
            identity != _file_identity(after_fd)
            or identity != _file_identity(final_path)
            or not stat.S_ISREG(final_path.st_mode)
            or final_path.st_nlink != 1
            or len(raw) != opened.st_size
        ):
            raise InputFailure("input changed while being read")
        return raw
    except InputFailure:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise InputFailure("input could not be read as one stable regular file") from exc
    finally:
        if descriptor is not None:
            _close_descriptor(descriptor)
        for directory_fd in reversed(descriptors):
            _close_descriptor(directory_fd)


def strict_load(path: Path) -> tuple[dict[str, Any], str]:
    """Load one bounded regular-file snapshot and hash the exact verified bytes."""

    raw = _read_stable_bytes(path)
    if raw.startswith(b"\xef\xbb\xbf"):
        raise InputFailure("UTF-8 BOM is forbidden")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputFailure("input is not UTF-8") from exc
    try:
        _preflight_json(text)
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_pairs,
            parse_constant=_reject_constant,
            parse_int=_parse_integer,
            parse_float=_parse_float,
        )
        _validate_json_tree(value)
    except (json.JSONDecodeError, InputFailure, RecursionError, ValueError) as exc:
        raise InputFailure("input is not one strict JSON object") from exc
    if not isinstance(value, dict):
        raise InputFailure("top-level JSON value must be an object")
    return value, hashlib.sha256(raw).hexdigest()


def _safe_id(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 128 and SAFE_ID.fullmatch(value) is not None


def _bounded_integer(value: Any, minimum: int, maximum: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= maximum
    )


def _safe_label(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= 255
        and SAFE_LABEL.fullmatch(value) is not None
        and not any(ord(character) < 32 or ord(character) == 127 for character in value)
        and not SECRET.search(value)
        and not PRIVATE_PATH.search(value)
    )


def _contains_sensitive_text(value: Any) -> bool:
    if isinstance(value, str):
        return SECRET.search(value) is not None or PRIVATE_PATH.search(value) is not None
    if isinstance(value, list):
        return any(_contains_sensitive_text(item) for item in value)
    if isinstance(value, dict):
        return any(
            _contains_sensitive_text(key) or _contains_sensitive_text(item)
            for key, item in value.items()
        )
    return False


def _valid_ref(value: Any) -> bool:
    keys = {"contract_name", "schema_version", "record_id", "sha256", "role"}
    return (
        isinstance(value, dict)
        and set(value) == keys
        and _safe_id(value.get("contract_name"))
        and value.get("schema_version") == "1.0"
        and _safe_id(value.get("record_id"))
        and isinstance(value.get("sha256"), str)
        and SHA256.fullmatch(value["sha256"]) is not None
        and _safe_id(value.get("role"))
    )


def _valid_actor(value: Any, *, actor_type: str | None = None, role: str | None = None) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"actor_type", "actor_id", "role"}
        and value.get("actor_type") in {"deterministic-tool", "agent", "human"}
        and (actor_type is None or value.get("actor_type") == actor_type)
        and _safe_id(value.get("actor_id"))
        and _safe_id(value.get("role"))
        and (role is None or value.get("role") == role)
    )


def _valid_producer(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"skill_id", "skill_version", "tool_id", "tool_version", "generated_utc"}
        and _safe_id(value.get("skill_id"))
        and _safe_id(value.get("tool_id"))
        and isinstance(value.get("skill_version"), str)
        and bool(value["skill_version"].strip())
        and isinstance(value.get("tool_version"), str)
        and bool(value["tool_version"].strip())
        and _parse_utc(value.get("generated_utc")) is not None
    )


def _valid_ref_list(value: Any) -> bool:
    if not isinstance(value, list) or not all(_valid_ref(item) for item in value):
        return False
    identities = [
        (item["contract_name"], item["schema_version"], item["record_id"], item["sha256"], item["role"])
        for item in value
    ]
    return len(identities) == len(set(identities))


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result if result.tzinfo is not None else None


def canonical_argv_sha256(argv: list[str]) -> str:
    raw = json.dumps(argv, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def finding(code: str, message: str, *, severity: str = "critical") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _exact_keys(value: Any, expected: set[str], label: str, findings: list[dict[str, str]], code: str) -> bool:
    if not isinstance(value, dict):
        findings.append(finding(code, f"{label} must be an object"))
        return False
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        findings.append(finding(code, f"{label} is missing field {missing[0]}"))
    if unknown:
        findings.append(finding(code, f"{label} contains an unsupported field"))
    return not missing and not unknown


def _gate_summary(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != GATE_KEYS:
        return False
    if (
        value.get("status") not in {"pass", "blocked"}
        or value.get("maximum_action") not in {
            "inspect-only", "plan-only", "stage-local-files", "request-execution-authorization",
            "execute-approved-request", "postprocess-only", "eligible-for-expert-review",
        }
        or value.get("claim_ceiling") not in CLAIMS
        or not isinstance(value.get("checks"), list)
        or not value["checks"]
    ):
        return False
    check_keys = {
        "check_id", "status", "decisive", "finding_codes", "evidence_refs",
        "validated_by", "validated_utc", "limitations",
    }
    for item in value["checks"]:
        if not isinstance(item, dict) or set(item) != check_keys:
            return False
        if (
            not _safe_id(item.get("check_id"))
            or item.get("status") not in {"pass", "warn", "fail", "blocked", "not-assessed", "not-applicable"}
            or not isinstance(item.get("decisive"), bool)
            or not isinstance(item.get("finding_codes"), list)
            or not all(_safe_id(code) for code in item["finding_codes"])
            or len(item["finding_codes"]) != len(set(item["finding_codes"]))
            or not _valid_ref_list(item.get("evidence_refs"))
            or not _valid_actor(item.get("validated_by"))
            or _parse_utc(item.get("validated_utc")) is None
            or not isinstance(item.get("limitations"), list)
            or not all(isinstance(text, str) and text.strip() for text in item["limitations"])
        ):
            return False
        if (
            item["status"] in {"pass", "not-applicable"}
            and item["finding_codes"]
        ) or (
            item["decisive"]
            and item["status"] in {"fail", "blocked", "not-assessed"}
            and not item["finding_codes"]
        ):
            return False
    if value["status"] == "pass" and any(
        not isinstance(item, dict) or item.get("status") not in {"pass", "not-applicable"}
        for item in value["checks"]
    ):
        return False
    if value["status"] == "blocked" and not any(
        item["decisive"] and item["status"] not in {"pass", "not-applicable"}
        for item in value["checks"]
    ):
        return False
    return True


def _file_ref(value: Any, expected_availability: str) -> bool:
    if not isinstance(value, dict) or set(value) != FILE_REF_KEYS:
        return False
    if (
        not _safe_id(value.get("role"))
        or not isinstance(value.get("label"), str)
        or not isinstance(value.get("media_type"), str)
        or MEDIA_TYPE.fullmatch(value["media_type"]) is None
        or not _safe_id(value.get("format"))
        or not (value.get("format_version") is None or isinstance(value.get("format_version"), str) and bool(value["format_version"].strip()))
        or value.get("sensitivity") not in {"public", "private", "restricted"}
        or value.get("redistribution") not in {"redistributable", "runtime-only", "restricted", "unknown"}
    ):
        return False
    if "/" in value["label"] or "\\" in value["label"] or not _safe_label(value["label"]):
        return False
    if value.get("availability") != expected_availability:
        return False
    if expected_availability == "present":
        return (
            isinstance(value.get("sha256"), str)
            and SHA256.fullmatch(value["sha256"]) is not None
            and _bounded_integer(value.get("bytes"), 0, MAX_INPUT_BYTES * 1024 * 1024)
        )
    return value.get("sha256") is None and value.get("bytes") is None


def validate_request(request: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    invalid: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    if not _exact_keys(request, REQUEST_KEYS, "execution request", invalid, "HPC.REQUEST.INVALID"):
        return invalid, blocked
    if _contains_sensitive_text(request):
        invalid.append(finding("HPC.COMMAND.UNSAFE", "request contains a secret-like value or private absolute path"))
    if request.get("schema_version") != "1.0" or request.get("contract_name") != "execution-request":
        invalid.append(finding("HPC.REQUEST.INVALID", "expected execution-request@1.0"))
    if not all(_safe_id(request.get(name)) for name in ("request_id", "workflow_step_id", "operation_id", "environment_profile_id")):
        invalid.append(finding("HPC.REQUEST.INVALID", "request contains an invalid identity"))
    if _parse_utc(request.get("created_utc")) is None or not _valid_actor(request.get("requested_by")):
        invalid.append(finding("HPC.REQUEST.INVALID", "request creation time or requester identity is invalid"))
    plan_ref = request.get("workflow_plan_ref")
    if (
        not _valid_ref(plan_ref)
        or plan_ref.get("contract_name") != "workflow-plan"
        or plan_ref.get("role") != "workflow-plan"
    ):
        invalid.append(finding("HPC.REQUEST.INVALID", "workflow plan reference is invalid"))
    argv = request.get("argv")
    command_safe = (
        request.get("command_kind") == "argv"
        and request.get("shell") is False
        and isinstance(argv, list)
        and 0 < len(argv) <= 1024
        and all(
            isinstance(item, str)
            and 0 < len(item) <= 4096
            and not any(ord(character) < 32 or ord(character) == 127 for character in item)
            and not SECRET.search(item)
            for item in argv
        )
        and EXECUTABLE.fullmatch(argv[0]) is not None
        and argv[0].casefold() not in SHELLS
        and not (
            argv[0].casefold().startswith(("python", "pypy"))
            and any(item in {"-c", "-e", "--eval"} for item in argv[1:])
        )
    )
    if not command_safe:
        invalid.append(finding("HPC.COMMAND.UNSAFE", "request must use a direct bounded secret-free argv with shell=false"))
    if not _safe_label(request.get("working_directory_label")):
        invalid.append(finding("HPC.REQUEST.INVALID", "working directory must be a privacy-safe logical label"))
    resources = request.get("resources")
    if not isinstance(resources, dict) or set(resources) != RESOURCE_KEYS:
        invalid.append(finding("HPC.REQUEST.INVALID", "resource object has invalid fields"))
    else:
        for key, minimum, maximum in (
            ("nodes", 1, 100_000),
            ("mpi_ranks", 1, 10_000_000),
            ("threads_per_rank", 1, 4096),
            ("gpus", 0, 1_000_000),
            ("memory_mb", 1, 1_000_000_000),
            ("walltime_s", 1, 604800),
        ):
            if not _bounded_integer(resources.get(key), minimum, maximum):
                invalid.append(finding("HPC.REQUEST.INVALID", f"resource {key} is invalid"))
                break
        profile = resources.get("scheduler_profile_id")
        if profile is not None and not _safe_id(profile):
            invalid.append(finding("HPC.PROFILE.UNRESOLVED", "scheduler profile ID is invalid"))
    inputs = request.get("inputs")
    outputs = request.get("expected_outputs")
    if not isinstance(inputs, list) or not inputs or not all(_file_ref(item, "present") for item in inputs):
        invalid.append(finding("HPC.ARTIFACT.INVALID", "every declared input must be present and hash-bound"))
    if not isinstance(outputs, list) or not outputs or not all(_file_ref(item, "missing") for item in outputs):
        invalid.append(finding("HPC.ARTIFACT.INVALID", "expected outputs must begin as named missing artifacts"))
    if isinstance(inputs, list) and len({item.get("sha256") for item in inputs if isinstance(item, dict)}) != len(inputs):
        invalid.append(finding("HPC.ARTIFACT.INVALID", "input hashes must be unique"))
    if isinstance(outputs, list) and len({item.get("label") for item in outputs if isinstance(item, dict)}) != len(outputs):
        invalid.append(finding("HPC.ARTIFACT.INVALID", "output labels must be unique"))
    if not _valid_ref_list(request.get("parent_records")):
        invalid.append(finding("HPC.REQUEST.INVALID", "parent record references are invalid"))
    retry = request.get("retry_policy")
    if (
        not isinstance(retry, dict)
        or set(retry) != {"maximum_attempts", "automatic_retry", "retryable_finding_codes"}
        or not _bounded_integer(retry.get("maximum_attempts"), 1, 20)
        or retry.get("automatic_retry") is not False
        or not isinstance(retry.get("retryable_finding_codes"), list)
        or not all(_safe_id(item) for item in retry.get("retryable_finding_codes", []))
        or len(retry.get("retryable_finding_codes", [])) != len(set(retry.get("retryable_finding_codes", [])))
    ):
        invalid.append(finding("HPC.REQUEST.INVALID", "retry policy must be bounded with automatic_retry=false"))
    auth = request.get("authorization_requirement")
    if not isinstance(auth, dict) or set(auth) != {"required", "side_effects", "scope_labels", "reason"}:
        invalid.append(finding("HPC.REQUEST.INVALID", "authorization requirement has invalid fields"))
    else:
        effects = auth.get("side_effects")
        scopes = auth.get("scope_labels")
        if (
            auth.get("required") is not True
            or not isinstance(effects, list)
            or not effects
            or not all(isinstance(item, str) and item in SIDE_EFFECTS for item in effects)
            or len(effects) != len(set(effects))
            or not isinstance(scopes, list)
            or not scopes
            or not all(_safe_label(item) for item in scopes)
            or len(scopes) != len(set(scopes))
            or not isinstance(auth.get("reason"), str)
            or not auth["reason"].strip()
        ):
            blocked.append(finding("HPC.AUTH.NOT_GRANTED", "request lacks a bounded side-effect authorization requirement", severity="blocking"))
    if request.get("execution_mode") not in {"dry-run", "execute"}:
        invalid.append(finding("HPC.REQUEST.INVALID", "execution mode is invalid"))
    if request.get("state") != "prepared" or request.get("blocker_codes") != []:
        blocked.append(finding("HPC.REQUEST.INVALID", "request is not prepared and blocker-free", severity="blocking"))
    if not _bounded_integer(request.get("timeout_s"), 1, 604800):
        invalid.append(finding("HPC.REQUEST.INVALID", "timeout is invalid"))
    if not _gate_summary(request.get("gates")):
        invalid.append(finding("HPC.REQUEST.INVALID", "request gate summary is invalid"))
    elif request["gates"]["status"] != "pass":
        blocked.append(finding("HPC.REQUEST.INVALID", "request gates are blocked", severity="blocking"))
    if not _valid_producer(request.get("producer")):
        invalid.append(finding("HPC.REQUEST.INVALID", "request producer provenance is invalid"))
    environment_profile = request.get("environment_profile_id")
    scheduler_profile = resources.get("scheduler_profile_id") if isinstance(resources, dict) else None
    if (
        environment_profile not in SYNTHETIC_ENVIRONMENT_PROFILES
        or scheduler_profile not in set(SYNTHETIC_SCHEDULER_PROFILES.values())
    ):
        blocked.append(finding("HPC.PROFILE.UNRESOLVED", "candidate can resolve only explicit synthetic fixture profiles", severity="blocking"))
    return invalid, blocked


def validate_decision(
    decision: dict[str, Any],
    request: dict[str, Any],
    request_sha256: str,
    at_utc: datetime,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    invalid: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    if not _exact_keys(decision, DECISION_KEYS, "decision record", invalid, "HPC.AUTH.NOT_GRANTED"):
        return invalid, blocked
    if _contains_sensitive_text(decision):
        invalid.append(finding("HPC.AUTH.NOT_GRANTED", "decision contains a secret-like value or private absolute path"))
    if decision.get("schema_version") != "1.0" or decision.get("contract_name") != "decision-record":
        invalid.append(finding("HPC.AUTH.NOT_GRANTED", "expected decision-record@1.0"))
    if not _safe_id(decision.get("decision_id")):
        invalid.append(finding("HPC.AUTH.NOT_GRANTED", "decision identity is invalid"))
    subject = decision.get("subject_ref")
    if not _valid_ref(subject):
        invalid.append(finding("HPC.AUTH.NOT_GRANTED", "authorization subject ref is invalid"))
    elif subject.get("contract_name") != "execution-request" or subject.get("role") != "execution-subject":
        invalid.append(finding("HPC.AUTH.NOT_GRANTED", "authorization subject contract or role is invalid"))
    elif subject.get("record_id") != request.get("request_id") or subject.get("sha256") != request_sha256:
        blocked.append(finding("HPC.AUTH.HASH_MISMATCH", "authorization does not bind exact request bytes", severity="blocking"))
    actor = decision.get("decided_by")
    if not _valid_actor(actor, actor_type="human"):
        blocked.append(finding("HPC.AUTH.NOT_GRANTED", "execution authorization must be decided by a human", severity="blocking"))
    if decision.get("decision_type") != "execution-authorization" or decision.get("outcome") != "approved":
        blocked.append(finding("HPC.AUTH.NOT_GRANTED", "decision is not an approved execution authorization", severity="blocking"))
    if decision.get("scientific_acceptance") != "not_assessed":
        invalid.append(finding("HPC.AUTH.NOT_GRANTED", "execution decision must not grant scientific acceptance"))
    decided = _parse_utc(decision.get("decided_utc"))
    expires = _parse_utc(decision.get("valid_until_utc"))
    request_created = _parse_utc(request.get("created_utc"))
    if (
        decided is None
        or expires is None
        or request_created is None
        or decided < request_created
        or decided >= expires
        or decided > at_utc
        or expires <= at_utc
    ):
        blocked.append(finding("HPC.AUTH.NOT_GRANTED", "authorization time chain is invalid or expired", severity="blocking"))
    required_scopes = request.get("authorization_requirement", {}).get("scope_labels", [])
    decision_scopes = decision.get("scope_labels")
    if (
        not isinstance(decision_scopes, list)
        or not all(_safe_label(item) for item in decision_scopes)
        or len(decision_scopes) != len(set(decision_scopes))
        or set(decision_scopes) != set(required_scopes)
    ):
        blocked.append(finding("HPC.AUTH.NOT_GRANTED", "authorization scope does not exactly match request scope", severity="blocking"))
    evidence = decision.get("evidence_refs")
    if not isinstance(evidence, list) or not any(
        _valid_ref(item)
        and item.get("contract_name") == "execution-request"
        and item.get("record_id") == request.get("request_id")
        and item.get("sha256") == request_sha256
        for item in evidence
    ):
        blocked.append(finding("HPC.AUTH.NOT_GRANTED", "authorization lacks exact request evidence", severity="blocking"))
    if (
        not isinstance(decision.get("evidence_ids"), list)
        or not decision["evidence_ids"]
        or not all(_safe_id(item) for item in decision["evidence_ids"])
        or len(decision["evidence_ids"]) != len(set(decision["evidence_ids"]))
        or not set(decision["evidence_ids"]).issubset(
            {item.get("record_id") for item in evidence if isinstance(item, dict)}
        )
        or not _valid_ref_list(evidence)
        or not isinstance(decision.get("rationale"), str)
        or not decision["rationale"].strip()
        or decision.get("claim_ceiling") not in EXECUTION_DECISION_CLAIMS
        or not isinstance(decision.get("limitations"), list)
        or not all(isinstance(item, str) and item.strip() for item in decision["limitations"])
        or not _valid_producer(decision.get("producer"))
    ):
        invalid.append(finding("HPC.AUTH.NOT_GRANTED", "decision evidence or provenance fields are invalid"))
    return invalid, blocked


def validate_lease(
    lease: dict[str, Any],
    lease_sha256: str,
    request: dict[str, Any],
    request_sha256: str,
    decision: dict[str, Any],
    decision_sha256: str,
    at_utc: datetime,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    del lease_sha256
    invalid: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    if not _exact_keys(lease, LEASE_KEYS, "execution lease", invalid, "HPC.LEASE.INVALID"):
        return invalid, blocked
    if _contains_sensitive_text(lease):
        invalid.append(finding("HPC.LEASE.INVALID", "lease contains a secret-like value or private absolute path"))
    if lease.get("schema_version") != "1.0" or lease.get("contract_name") != "execution-lease":
        invalid.append(finding("HPC.LEASE.INVALID", "expected execution-lease@1.0"))
    request_ref = lease.get("request_ref")
    decision_ref = lease.get("authorization_decision_ref")
    if not _valid_ref(request_ref) or request_ref.get("contract_name") != "execution-request" or request_ref.get("role") != "execution-request":
        invalid.append(finding("HPC.LEASE.INVALID", "lease request reference contract or role is invalid"))
    elif request_ref.get("record_id") != request.get("request_id") or request_ref.get("sha256") != request_sha256:
        blocked.append(finding("HPC.LEASE.INVALID", "lease does not bind exact request bytes", severity="blocking"))
    if not _valid_ref(decision_ref) or decision_ref.get("contract_name") != "decision-record" or decision_ref.get("role") != "execution-authorization":
        invalid.append(finding("HPC.LEASE.INVALID", "lease authorization reference contract or role is invalid"))
    elif decision_ref.get("record_id") != decision.get("decision_id") or decision_ref.get("sha256") != decision_sha256:
        blocked.append(finding("HPC.LEASE.INVALID", "lease does not bind exact decision bytes", severity="blocking"))
    issuer = lease.get("issued_by")
    if not _valid_actor(issuer, actor_type="deterministic-tool", role="lease-issuer"):
        invalid.append(finding("HPC.LEASE.INVALID", "lease issuer identity is invalid"))
    if not _safe_id(lease.get("lease_id")):
        invalid.append(finding("HPC.LEASE.INVALID", "lease identity is invalid"))
    issued = _parse_utc(lease.get("issued_utc"))
    expires = _parse_utc(lease.get("expires_utc"))
    decision_time = _parse_utc(decision.get("decided_utc"))
    decision_expiry = _parse_utc(decision.get("valid_until_utc"))
    duration = lease.get("lease_duration_s")
    if not _bounded_integer(duration, 1, 604800):
        invalid.append(finding("HPC.LEASE.INVALID", "lease duration is invalid"))
    if (
        issued is None
        or expires is None
        or not _bounded_integer(duration, 1, 604800)
        or int((expires - issued).total_seconds()) != duration
        or issued > at_utc
        or expires <= at_utc
        or decision_time is None
        or decision_expiry is None
        or issued < decision_time
        or issued >= decision_expiry
        or expires > decision_expiry
    ):
        blocked.append(finding("HPC.LEASE.INVALID", "lease time chain is invalid or expired", severity="blocking"))
    if lease.get("status") != "active" or lease.get("single_use") is not True:
        blocked.append(finding("HPC.IDEMPOTENCY.BLOCKED", "lease is not active and unused", severity="blocking"))
    grant = lease.get("grant")
    grant_keys = {
        "side_effects", "environment_profile_ids", "scheduler_profile_ids", "argv_sha256",
        "input_sha256", "output_labels", "resource_ceiling", "maximum_executions",
    }
    if not isinstance(grant, dict) or set(grant) != grant_keys:
        invalid.append(finding("HPC.LEASE.INVALID", "lease grant has invalid fields"))
        return invalid, blocked
    auth = request.get("authorization_requirement", {})
    resources = request.get("resources", {})
    if not _bounded_integer(grant.get("maximum_executions"), 1, 1):
        blocked.append(finding("HPC.IDEMPOTENCY.BLOCKED", "lease must authorize exactly one execution", severity="blocking"))
    if grant.get("side_effects") != auth.get("side_effects"):
        blocked.append(finding("HPC.LEASE.INVALID", "lease side effects differ from request authorization", severity="blocking"))
    if grant.get("environment_profile_ids") != [request.get("environment_profile_id")]:
        blocked.append(finding("HPC.LEASE.INVALID", "lease environment profile broadens or differs from request", severity="blocking"))
    scheduler_ids = [] if resources.get("scheduler_profile_id") is None else [resources.get("scheduler_profile_id")]
    if grant.get("scheduler_profile_ids") != scheduler_ids:
        blocked.append(finding("HPC.LEASE.INVALID", "lease scheduler profile broadens or differs from request", severity="blocking"))
    if grant.get("argv_sha256") != canonical_argv_sha256(request.get("argv", [])):
        blocked.append(finding("HPC.LEASE.INVALID", "lease argv hash does not match request argv", severity="blocking"))
    expected_inputs = sorted(item["sha256"] for item in request.get("inputs", []) if isinstance(item, dict))
    expected_outputs = sorted(item["label"] for item in request.get("expected_outputs", []) if isinstance(item, dict))
    if not isinstance(grant.get("input_sha256"), list) or sorted(grant["input_sha256"]) != expected_inputs:
        blocked.append(finding("HPC.LEASE.INVALID", "lease input hashes differ from request", severity="blocking"))
    if not isinstance(grant.get("output_labels"), list) or sorted(grant["output_labels"]) != expected_outputs:
        blocked.append(finding("HPC.LEASE.INVALID", "lease output labels differ from request", severity="blocking"))
    ceiling = grant.get("resource_ceiling")
    expected_ceiling = {key: resources.get(key) for key in LEASE_RESOURCE_KEYS}
    if not isinstance(ceiling, dict) or set(ceiling) != LEASE_RESOURCE_KEYS or ceiling != expected_ceiling:
        blocked.append(finding("HPC.LEASE.INVALID", "lease resource ceiling differs from exact request resources", severity="blocking"))
    if (
        not isinstance(grant.get("side_effects"), list)
        or not all(isinstance(item, str) and item in SIDE_EFFECTS for item in grant["side_effects"])
        or len(grant["side_effects"]) != len(set(grant["side_effects"]))
        or not isinstance(grant.get("environment_profile_ids"), list)
        or not all(_safe_id(item) for item in grant["environment_profile_ids"])
        or len(grant["environment_profile_ids"]) != len(set(grant["environment_profile_ids"]))
        or not isinstance(grant.get("scheduler_profile_ids"), list)
        or not all(_safe_id(item) for item in grant["scheduler_profile_ids"])
        or len(grant["scheduler_profile_ids"]) != len(set(grant["scheduler_profile_ids"]))
        or not isinstance(grant.get("argv_sha256"), str)
        or SHA256.fullmatch(grant["argv_sha256"]) is None
        or not isinstance(grant.get("input_sha256"), list)
        or not all(isinstance(item, str) and SHA256.fullmatch(item) for item in grant["input_sha256"])
        or len(grant["input_sha256"]) != len(set(grant["input_sha256"]))
        or not isinstance(grant.get("output_labels"), list)
        or not all(_safe_label(item) for item in grant["output_labels"])
        or len(grant["output_labels"]) != len(set(grant["output_labels"]))
        or not _bounded_integer(grant.get("maximum_executions"), 1, 1)
    ):
        invalid.append(finding("HPC.LEASE.INVALID", "lease grant contains invalid identifiers or digests"))
    if (
        not isinstance(lease.get("constraints"), list)
        or not all(isinstance(item, str) and item.strip() for item in lease["constraints"])
        or len(lease["constraints"]) != len(set(lease["constraints"]))
        or not _valid_producer(lease.get("producer"))
    ):
        invalid.append(finding("HPC.LEASE.INVALID", "lease constraints or producer provenance is invalid"))
    return invalid, blocked


def _walltime(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def render_script(request: dict[str, Any], scheduler: str) -> tuple[str, list[str]]:
    resources = request["resources"]
    command = "exec " + shlex.join(request["argv"])
    common = ["#!/bin/sh", "set -eu", "# argv is immutable; no launcher, module, path, or site policy is inferred"]
    if scheduler == "local":
        lines = common + [command]
        submit = ["local-dry-run-only", "synthetic-job.sh"]
    elif scheduler == "slurm":
        directives = [
            f"#SBATCH --nodes={resources['nodes']}",
            f"#SBATCH --ntasks={resources['mpi_ranks']}",
            f"#SBATCH --cpus-per-task={resources['threads_per_rank']}",
            f"#SBATCH --mem={resources['memory_mb']}M",
            f"#SBATCH --time={_walltime(resources['walltime_s'])}",
        ]
        if resources["gpus"]:
            directives.append(f"#SBATCH --gpus={resources['gpus']}")
        lines = [common[0], *directives, *common[1:], command]
        submit = ["sbatch", "synthetic-job.sh"]
    else:
        if resources["mpi_ranks"] % resources["nodes"] != 0:
            raise InputFailure("OpenPBS bounded template requires mpi_ranks divisible by nodes")
        ranks_per_node = resources["mpi_ranks"] // resources["nodes"]
        ncpus = ranks_per_node * resources["threads_per_rank"]
        select = f"select={resources['nodes']}:ncpus={ncpus}:mpiprocs={ranks_per_node}:ompthreads={resources['threads_per_rank']}"
        if resources["gpus"]:
            if resources["gpus"] % resources["nodes"] != 0:
                raise InputFailure("OpenPBS bounded template requires gpus divisible by nodes")
            select += f":ngpus={resources['gpus'] // resources['nodes']}"
        directives = [
            f"#PBS -l {select}",
            f"#PBS -l mem={resources['memory_mb']}mb",
            f"#PBS -l walltime={_walltime(resources['walltime_s'])}",
        ]
        lines = [common[0], *directives, *common[1:], command]
        submit = ["qsub", "synthetic-job.sh"]
    script = "\n".join(lines) + "\n"
    return script, submit


OBSERVATION_KEYS = {
    "schema_version", "contract_name", "scheduler_family", "native_scheduler_status",
    "scheduler_status", "native_process_status", "process_status",
    "native_application_status", "application_status", "return_code", "evidence_labels",
}
SCHEDULER_STATES = {"not-submitted", "submitted", "queued", "running", "succeeded", "failed", "cancelled", "unknown", "not-applicable"}
PROCESS_STATES = {"not-started", "running", "exited-zero", "exited-nonzero", "signalled", "timed-out", "unknown", "not-applicable"}
APPLICATION_STATES = {"not-started", "running", "completed", "incomplete", "failed", "unknown", "not-applicable"}
SLURM_NATIVE_STATUS = {
    "PENDING": "queued", "CONFIGURING": "queued", "REQUEUED": "queued",
    "REQUEUE_FED": "queued", "RESIZING": "queued", "RUNNING": "running",
    "COMPLETING": "running", "SUSPENDED": "running", "SIGNALING": "running",
    "STAGE_OUT": "running", "COMPLETED": "succeeded", "BOOT_FAIL": "failed",
    "DEADLINE": "failed", "FAILED": "failed", "NODE_FAIL": "failed",
    "OUT_OF_MEMORY": "failed", "PREEMPTED": "failed", "REVOKED": "failed",
    "SPECIAL_EXIT": "failed", "CANCELLED": "cancelled",
}
OPENPBS_NATIVE_STATUS = {
    "Q": "queued", "H": "queued", "W": "queued", "T": "queued",
    "R": "running", "E": "running", "B": "running", "S": "running",
    "F": "unknown", "X": "unknown",
}


def _expected_scheduler_status(family: Any, native: Any) -> str | None:
    if family == "slurm":
        return SLURM_NATIVE_STATUS.get(native) if isinstance(native, str) else None
    if family == "openpbs":
        return OPENPBS_NATIVE_STATUS.get(native) if isinstance(native, str) else None
    if family == "local" and native in {None, "NOT_APPLICABLE"}:
        return "not-applicable"
    return None


def classify_status(observation: dict[str, Any]) -> tuple[list[dict[str, str]], str]:
    invalid: list[dict[str, str]] = []
    if not _exact_keys(observation, OBSERVATION_KEYS, "status observation", invalid, "HPC.STATUS.UNKNOWN"):
        return invalid, "blocked"
    scheduler = observation.get("scheduler_status")
    process = observation.get("process_status")
    application = observation.get("application_status")
    if observation.get("schema_version") != "1.0" or observation.get("contract_name") != "status-observation":
        invalid.append(finding("HPC.STATUS.UNKNOWN", "expected status-observation@1.0"))
    if _contains_sensitive_text(observation):
        invalid.append(finding("HPC.STATUS.UNKNOWN", "status observation contains private or secret-like text"))
    family = observation.get("scheduler_family")
    native_scheduler = observation.get("native_scheduler_status")
    if family not in {"slurm", "openpbs", "local"} or scheduler not in SCHEDULER_STATES:
        invalid.append(finding("HPC.STATUS.UNKNOWN", "scheduler family or status is invalid"))
    else:
        expected_scheduler = _expected_scheduler_status(family, native_scheduler)
        if expected_scheduler is None and scheduler != "unknown":
            invalid.append(finding("HPC.STATUS.UNKNOWN", "native scheduler state cannot support the declared normalized state"))
        elif expected_scheduler is not None and scheduler != expected_scheduler:
            invalid.append(finding("HPC.STATUS.UNKNOWN", "native scheduler state is unknown or conflicts with normalized state"))
    if process not in PROCESS_STATES:
        invalid.append(finding("HPC.PROCESS.UNKNOWN", "process status is invalid"))
    if application not in APPLICATION_STATES:
        invalid.append(finding("HPC.APPLICATION.UNKNOWN", "application status is invalid"))
    return_code = observation.get("return_code")
    if (
        return_code is not None
        and (not isinstance(return_code, int) or isinstance(return_code, bool))
        or process == "exited-zero" and return_code != 0
        or process == "exited-nonzero"
        and (
            not isinstance(return_code, int)
            or isinstance(return_code, bool)
            or return_code == 0
        )
        or process in {"not-started", "running"} and return_code is not None
    ):
        invalid.append(finding("HPC.PROCESS.UNKNOWN", "process status conflicts with return code"))
    if not isinstance(observation.get("evidence_labels"), list) or not observation["evidence_labels"] or not all(_safe_label(item) for item in observation["evidence_labels"]):
        invalid.append(finding("HPC.STATUS.UNKNOWN", "status observation lacks privacy-safe evidence labels"))
    if invalid:
        return invalid, "blocked"
    if scheduler == "cancelled":
        return [], "cancelled"
    if process == "timed-out":
        return [], "timed-out"
    if scheduler == "failed" or process in {"exited-nonzero", "signalled"} or application in {"incomplete", "failed"}:
        return [
            finding(
                "HPC.RUNTIME.FAILED",
                "authoritative scheduler, process, or application evidence records a terminal failure",
                severity="blocking",
            )
        ], "failed"
    if scheduler in {"succeeded", "not-applicable"} and process == "exited-zero" and application == "completed":
        return [], "succeeded"
    if scheduler == "running" or process == "running" or application == "running":
        return [], "running"
    if scheduler in {"submitted", "queued"} and process == "not-started" and application == "not-started":
        return [], "queued"
    findings = []
    if scheduler == "unknown":
        findings.append(finding("HPC.STATUS.UNKNOWN", "scheduler state is unknown", severity="blocking"))
    if process in {"unknown", "not-started"}:
        findings.append(finding("HPC.PROCESS.UNKNOWN", "terminal process evidence is absent", severity="blocking"))
    if application in {"unknown", "not-started", "not-applicable"}:
        findings.append(finding("HPC.APPLICATION.UNKNOWN", "application completion evidence is absent", severity="blocking"))
    return findings or [finding("HPC.STATUS.UNKNOWN", "state layers are not jointly classifiable", severity="blocking")], "blocked"


def _reported_state(value: Any, allowed: set[str], fallback: str = "unknown") -> str:
    return value if isinstance(value, str) and value in allowed else fallback


def make_report(
    command: str,
    status: str,
    findings: list[dict[str, str]],
    evidence: list[dict[str, str]],
    next_action: str,
    states: dict[str, Any],
    *,
    script: str | None = None,
    submission_argv: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "contract_name": "candidate-hpc-report",
        "tool": {"name": "hpc-execution-cli", "version": TOOL_VERSION},
        "command": command,
        "status": status,
        "dry_run": True,
        "side_effect_performed": False,
        "external_execution_performed": False,
        "execute": False,
        "lease_consumed": False,
        "workflow_event_emitted": False,
        "scheduler_job_id": None,
        "promotion_authorized": False,
        "execution_authorized": False,
        "report_authenticity": "unsigned-candidate-output",
        "downstream_binding_required": "sha256-of-exact-report-bytes-in-external-manifest",
        "scientific_acceptance": "not_assessed",
        "claim_ceiling": "no_positive_claim",
        "states": states,
        "decisive_evidence": evidence,
        "findings": findings,
        "minimum_next_action": next_action,
        "rendered_script": script,
        "rendered_script_sha256": hashlib.sha256(script.encode("utf-8")).hexdigest() if script is not None else None,
        "proposed_submission_argv": submission_argv,
        "limitations": [
            "No process, scheduler, network, remote host, or filesystem side effect was invoked.",
            "Rendered text and proposed argv are intent, not proof of submission or execution.",
            "Scheduler, process, application, numerical, and human scientific states remain independent.",
            "This unsigned report can be altered after emission and must be exact-byte bound by a trusted external manifest before evidentiary use.",
        ],
    }


def _print(value: dict[str, Any]) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    commands = value.add_subparsers(dest="command", required=True)
    request = commands.add_parser("validate-request")
    request.add_argument("--request", required=True, type=Path)
    render = commands.add_parser("render-dry-run")
    render.add_argument("--request", required=True, type=Path)
    render.add_argument("--decision", required=True, type=Path)
    render.add_argument("--lease", required=True, type=Path)
    render.add_argument("--scheduler", required=True, choices=("local", "slurm", "openpbs"))
    render.add_argument("--at-utc", required=True)
    status = commands.add_parser("classify-status")
    status.add_argument("--observation", required=True, type=Path)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "validate-request":
            request, request_sha = strict_load(args.request)
            invalid, blocked = validate_request(request)
            findings = invalid + blocked
            status = "fail" if invalid else "blocked" if blocked else "pass"
            _print(make_report(
                args.command,
                status,
                findings,
                [{"contract_name": "execution-request", "sha256": request_sha, "role": "audited-request"}],
                "regenerate-immutable-request" if invalid else "resolve-first-request-blocker" if blocked else "obtain-exact-request-human-authorization",
                {"scheduler": "not-submitted", "process": "not-started", "application": "not-started", "normalized_execution": "dry-run", "scientific": "not_assessed"},
            ))
            return 2 if invalid else 3 if blocked else 0

        if args.command == "classify-status":
            observation, observation_sha = strict_load(args.observation)
            findings, normalized = classify_status(observation)
            invalid = any(item["severity"] == "critical" for item in findings)
            blocked = normalized == "blocked"
            status = "fail" if invalid else "blocked" if blocked else "pass"
            _print(make_report(
                args.command,
                status,
                findings,
                [{"contract_name": "status-observation", "sha256": observation_sha, "role": "status-evidence"}],
                "repair-status-observation" if invalid else "collect-missing-independent-status-evidence" if blocked else "handoff-to-engine-specific-output-gates",
                {
                    "scheduler": _reported_state(observation.get("scheduler_status"), SCHEDULER_STATES),
                    "process": _reported_state(observation.get("process_status"), PROCESS_STATES),
                    "application": _reported_state(observation.get("application_status"), APPLICATION_STATES),
                    "normalized_execution": normalized,
                    "scientific": "not_assessed",
                },
            ))
            return 2 if invalid else 3 if blocked else 0

        at_utc = _parse_utc(args.at_utc)
        if at_utc is None:
            raise InputFailure("evaluation time must be timezone-aware ISO 8601")
        at_utc = at_utc.astimezone(timezone.utc)
        request, request_sha = strict_load(args.request)
        decision, decision_sha = strict_load(args.decision)
        lease, lease_sha = strict_load(args.lease)
        request_invalid, request_blocked = validate_request(request)
        invalid = list(request_invalid)
        blocked = list(request_blocked)
        if not request_invalid:
            decision_invalid, decision_blocked = validate_decision(
                decision, request, request_sha, at_utc
            )
            invalid.extend(decision_invalid)
            blocked.extend(decision_blocked)
            if not decision_invalid:
                lease_invalid, lease_blocked = validate_lease(
                    lease, lease_sha, request, request_sha, decision, decision_sha, at_utc
                )
                invalid.extend(lease_invalid)
                blocked.extend(lease_blocked)
        resources = request.get("resources")
        profile = resources.get("scheduler_profile_id") if isinstance(resources, dict) else None
        if profile != SYNTHETIC_SCHEDULER_PROFILES[args.scheduler]:
            blocked.append(finding("HPC.SCHEDULER.UNSUPPORTED", "selected scheduler family does not match the request profile", severity="blocking"))
        authorization = request.get("authorization_requirement")
        side_effects = authorization.get("side_effects") if isinstance(authorization, dict) else None
        if side_effects != ["scheduler-submit"]:
            blocked.append(finding("HPC.AUTH.NOT_GRANTED", "submission rendering requires an exact scheduler-submit authorization scope", severity="blocking"))
        script: str | None = None
        submit: list[str] | None = None
        if not invalid and not blocked:
            try:
                script, submit = render_script(request, args.scheduler)
            except InputFailure as exc:
                blocked.append(finding("HPC.SCHEDULER.UNSUPPORTED", str(exc), severity="blocking"))
        findings = invalid + blocked
        status = "fail" if invalid else "blocked" if blocked else "pass"
        _print(make_report(
            args.command,
            status,
            findings,
            [
                {"contract_name": "execution-request", "sha256": request_sha, "role": "render-subject"},
                {"contract_name": "decision-record", "sha256": decision_sha, "role": "authorization"},
                {"contract_name": "execution-lease", "sha256": lease_sha, "role": "single-use-lease"},
            ],
            "regenerate-invalid-record" if invalid else "resolve-first-authorization-or-lease-blocker" if blocked else "review-rendered-plan-without-submitting",
            {"scheduler": "not-submitted", "process": "not-started", "application": "not-started", "normalized_execution": "dry-run", "scientific": "not_assessed"},
            script=script,
            submission_argv=submit,
        ))
        return 2 if invalid else 3 if blocked else 0
    except InputFailure as exc:
        _print(make_report(
            args.command,
            "fail",
            [finding("HPC.JSON.INVALID", str(exc))],
            [],
            "replace-first-malformed-input",
            {"scheduler": "unknown", "process": "unknown", "application": "unknown", "normalized_execution": "blocked", "scientific": "not_assessed"},
        ))
        return 2
    except (OSError, ValueError, TypeError, KeyError):
        _print(make_report(
            args.command,
            "fail",
            [finding("HPC.REQUEST.INVALID", "bounded deterministic audit failed")],
            [],
            "inspect-input-and-rerun",
            {"scheduler": "unknown", "process": "unknown", "application": "unknown", "normalized_execution": "blocked", "scientific": "not_assessed"},
        ))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
