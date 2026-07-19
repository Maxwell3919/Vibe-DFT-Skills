#!/usr/bin/env python3
"""Offline fail-closed audits for non-active DFT orchestration records."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
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
CLAIMS = {
    "no_positive_claim", "documented_behavior_only", "input_gates_only",
    "technical_run_gates_only", "numerical_candidate_only", "eligible_for_expert_review",
}
EXECUTION_DECISION_CLAIMS = {
    "no_positive_claim", "documented_behavior_only", "input_gates_only",
}
GATE_ACTIONS = {
    "inspect-only", "plan-only", "stage-local-files",
    "request-execution-authorization", "execute-approved-request",
    "postprocess-only", "eligible-for-expert-review",
}
SIDE_EFFECTING = {"authorized-local", "authorized-remote", "scheduler"}
DOMAINS = {
    "structure", "periodic-dft", "quantum-chemistry", "molecular-dynamics",
    "machine-learned-potential", "postprocessing", "campaign-efficiency", "reporting",
}
SIDE_EFFECTS = {
    "read-only", "network-read", "local-write", "local-execution", "remote-read",
    "remote-write", "scheduler-submit", "scheduler-control", "external-publish", "destructive-delete",
}
FILE_REF_KEYS = {
    "role", "label", "media_type", "format", "format_version", "availability",
    "sha256", "bytes", "sensitivity", "redistribution",
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


def finding(code: str, message: str, *, severity: str = "critical") -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _exact_keys(
    value: Any,
    required: set[str],
    label: str,
    findings: list[dict[str, str]],
    *,
    code: str = "ORCH.CONTRACT.INVALID",
) -> bool:
    if not isinstance(value, dict):
        findings.append(finding(code, f"{label} must be an object"))
        return False
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        findings.append(finding(code, f"{label} is missing field {missing[0]}"))
    if unknown:
        findings.append(finding(code, f"{label} contains an unsupported field"))
    return not missing and not unknown


def _safe_id(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 128 and SAFE_ID.fullmatch(value) is not None


def _bounded_integer(value: Any, minimum: int, maximum: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= maximum
    )


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


def _list_of_refs(value: Any) -> bool:
    if not isinstance(value, list) or not all(_valid_ref(item) for item in value):
        return False
    identities = [
        (item["contract_name"], item["schema_version"], item["record_id"], item["sha256"], item["role"])
        for item in value
    ]
    return len(identities) == len(set(identities))


def _valid_actor(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"actor_type", "actor_id", "role"}
        and value.get("actor_type") in {"deterministic-tool", "agent", "human"}
        and _safe_id(value.get("actor_id"))
        and _safe_id(value.get("role"))
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


def _valid_file_ref(value: Any, availability: str) -> bool:
    if (
        not isinstance(value, dict)
        or set(value) != FILE_REF_KEYS
        or not _safe_id(value.get("role"))
        or not isinstance(value.get("label"), str)
        or "/" in value["label"]
        or "\\" in value["label"]
        or not _safe_label(value["label"])
        or not isinstance(value.get("media_type"), str)
        or MEDIA_TYPE.fullmatch(value["media_type"]) is None
        or not _safe_id(value.get("format"))
        or not (value.get("format_version") is None or isinstance(value.get("format_version"), str) and bool(value["format_version"].strip()))
        or value.get("sensitivity") not in {"public", "private", "restricted"}
        or value.get("redistribution") not in {"redistributable", "runtime-only", "restricted", "unknown"}
        or value.get("availability") != availability
    ):
        return False
    if availability == "present":
        return (
            isinstance(value.get("sha256"), str)
            and SHA256.fullmatch(value["sha256"]) is not None
            and _bounded_integer(value.get("bytes"), 0, MAX_INPUT_BYTES * 1024 * 1024)
        )
    return value.get("sha256") is None and value.get("bytes") is None


def _gate_summary(value: Any, label: str, findings: list[dict[str, str]]) -> bool:
    keys = {"status", "maximum_action", "claim_ceiling", "checks"}
    if not isinstance(value, dict) or set(value) != keys:
        findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate summary has invalid fields"))
        return False
    if value.get("status") not in {"pass", "blocked"}:
        findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate status is invalid"))
        return False
    if value.get("maximum_action") not in GATE_ACTIONS:
        findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate maximum action is invalid"))
        return False
    if value.get("claim_ceiling") not in CLAIMS:
        findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate claim ceiling is invalid"))
        return False
    checks = value.get("checks")
    if not isinstance(checks, list) or not checks:
        findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} has no gate checks"))
        return False
    allowed_status = {"pass", "warn", "fail", "blocked", "not-assessed", "not-applicable"}
    required = {
        "check_id", "status", "decisive", "finding_codes", "evidence_refs",
        "validated_by", "validated_utc", "limitations",
    }
    for index, check in enumerate(checks):
        if not isinstance(check, dict) or set(check) != required:
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate check {index} has invalid fields"))
            return False
        if not _safe_id(check.get("check_id")) or check.get("status") not in allowed_status:
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate check {index} has invalid identity or status"))
            return False
        if not isinstance(check.get("decisive"), bool):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate check {index} has invalid decisive flag"))
            return False
        if not isinstance(check.get("finding_codes"), list) or not all(_safe_id(item) for item in check["finding_codes"]):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate check {index} has invalid finding codes"))
            return False
        if (
            check["status"] in {"pass", "not-applicable"}
            and check["finding_codes"]
        ) or (
            check["decisive"]
            and check["status"] in {"fail", "blocked", "not-assessed"}
            and not check["finding_codes"]
        ):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate check {index} has inconsistent findings"))
            return False
        if not _list_of_refs(check.get("evidence_refs")):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate check {index} has invalid evidence refs"))
            return False
        if (
            not _valid_actor(check.get("validated_by"))
            or _parse_utc(check.get("validated_utc")) is None
            or not isinstance(check.get("limitations"), list)
            or not all(isinstance(item, str) and item.strip() for item in check["limitations"])
        ):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} gate check {index} has invalid provenance"))
            return False
        if value["status"] == "pass" and check["status"] not in {"pass", "not-applicable"}:
            findings.append(finding("ORCH.STEP.NOT_READY", f"{label} claims pass while gate {check['check_id']} is {check['status']}", severity="blocking"))
            return False
    if value["status"] == "blocked" and not any(
        check["decisive"] and check["status"] not in {"pass", "not-applicable"}
        for check in checks
    ):
        findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} blocked gate has no decisive blocker"))
        return False
    return True


def _cycle(step_ids: list[str], dependencies: dict[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {step_id: 0 for step_id in step_ids}
    for root in step_ids:
        if state[root] != 0:
            continue
        state[root] = 1
        path = [root]
        positions = {root: 0}
        iterators = [iter(dependencies.get(root, []))]
        while path:
            current = path[-1]
            try:
                dependency = next(iterators[-1])
            except StopIteration:
                state[current] = 2
                positions.pop(current)
                path.pop()
                iterators.pop()
                continue
            if dependency not in state:
                continue
            if state[dependency] == 1:
                return path[positions[dependency]:] + [dependency]
            if state[dependency] == 0:
                state[dependency] = 1
                positions[dependency] = len(path)
                path.append(dependency)
                iterators.append(iter(dependencies.get(dependency, [])))
    return None


PLAN_KEYS = {
    "schema_version", "contract_name", "plan_id", "title", "objective", "case_id",
    "scientific_protocol_id", "status", "domains", "source_records", "steps",
    "authorization_policy", "required_decisions", "scientific_acceptance",
    "scientific_decision_ref", "claim_ceiling", "gates", "blocker_codes",
    "limitations", "producer",
}
STEP_KEYS = {
    "step_id", "skill_id", "operation_id", "route_lifecycle", "state",
    "execution_class", "dependencies", "input_records", "output_contracts",
    "calculation_envelope_ref", "execution_request_ref", "maturity", "gates",
    "blocker_codes",
}


def audit_plan(plan: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not _exact_keys(plan, PLAN_KEYS, "workflow plan", findings):
        return findings
    if _contains_sensitive_text(plan):
        findings.append(finding("ORCH.CONTRACT.INVALID", "workflow plan contains a secret-like value or private absolute path"))
    if plan.get("schema_version") != "1.0" or plan.get("contract_name") != "workflow-plan":
        findings.append(finding("ORCH.CONTRACT.INVALID", "expected workflow-plan@1.0"))
    for name in ("plan_id", "case_id", "scientific_protocol_id"):
        if not _safe_id(plan.get(name)):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{name} is not a safe ID"))
    if not isinstance(plan.get("title"), str) or not plan["title"].strip():
        findings.append(finding("ORCH.CONTRACT.INVALID", "title is empty"))
    if not isinstance(plan.get("objective"), str) or not plan["objective"].strip():
        findings.append(finding("ORCH.CONTRACT.INVALID", "objective is empty"))
    if plan.get("status") not in {"draft", "ready", "blocked", "executing", "completed", "abandoned"}:
        findings.append(finding("ORCH.CONTRACT.INVALID", "workflow status is invalid"))
    if plan.get("scientific_acceptance") != "not_assessed" or plan.get("scientific_decision_ref") is not None:
        findings.append(finding("ORCH.STATE.CONFLATED", "a workflow plan cannot grant scientific acceptance"))
    if plan.get("claim_ceiling") not in CLAIMS:
        findings.append(finding("ORCH.CONTRACT.INVALID", "plan claim ceiling is invalid"))
    domains = plan.get("domains")
    if (
        not isinstance(domains, list)
        or not domains
        or not all(isinstance(item, str) and item in DOMAINS for item in domains)
        or len(domains) != len(set(domains))
    ):
        findings.append(finding("ORCH.CONTRACT.INVALID", "plan domains are invalid"))
    if not _list_of_refs(plan.get("source_records")) or not _list_of_refs(plan.get("required_decisions")):
        findings.append(finding("ORCH.CONTRACT.INVALID", "plan record references are invalid"))
    if not isinstance(plan.get("blocker_codes"), list) or not all(_safe_id(item) for item in plan["blocker_codes"]):
        findings.append(finding("ORCH.CONTRACT.INVALID", "plan blocker codes are invalid"))
    elif len(plan["blocker_codes"]) != len(set(plan["blocker_codes"])):
        findings.append(finding("ORCH.CONTRACT.INVALID", "plan blocker codes are duplicated"))
    if (
        not isinstance(plan.get("limitations"), list)
        or not all(isinstance(item, str) and item.strip() for item in plan["limitations"])
        or len(plan["limitations"]) != len(set(plan["limitations"]))
        or not _valid_producer(plan.get("producer"))
    ):
        findings.append(finding("ORCH.CONTRACT.INVALID", "plan limitations or producer provenance are invalid"))
    plan_gates_valid = _gate_summary(plan.get("gates"), "plan", findings)

    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        findings.append(finding("ORCH.CONTRACT.INVALID", "plan requires at least one step"))
        return findings
    step_ids: list[str] = []
    dependencies: dict[str, list[str]] = {}
    states: dict[str, str] = {}
    side_effecting = False
    for index, step in enumerate(steps):
        label = f"step {index}"
        if not _exact_keys(step, STEP_KEYS, label, findings):
            continue
        step_id = step.get("step_id")
        if not _safe_id(step_id) or not _safe_id(step.get("skill_id")) or not _safe_id(step.get("operation_id")):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{label} has an invalid ID"))
            continue
        if step_id in step_ids:
            findings.append(finding("ORCH.DAG.DUPLICATE_STEP", f"duplicate step ID {step_id}"))
        step_ids.append(step_id)
        states[step_id] = step.get("state")
        deps = step.get("dependencies")
        if not isinstance(deps, list) or not all(_safe_id(item) for item in deps) or len(deps) != len(set(deps)):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{step_id} dependencies are invalid"))
            deps = []
        dependencies[step_id] = deps
        if step.get("route_lifecycle") not in {"active", "development", "planned", "unsupported"}:
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{step_id} route lifecycle is invalid"))
        elif step["route_lifecycle"] != "active":
            findings.append(finding("ORCH.ROUTE.NOT_ACTIVE", f"{step_id} route is {step['route_lifecycle']}", severity="blocking"))
        if step.get("state") not in {"planned", "ready", "blocked", "running", "completed", "failed", "skipped"}:
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{step_id} state is invalid"))
        execution_class = step.get("execution_class")
        if execution_class not in {"inspect-only", "local-deterministic", *SIDE_EFFECTING}:
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{step_id} execution class is invalid"))
        side_effecting = side_effecting or execution_class in SIDE_EFFECTING
        blockers = step.get("blocker_codes")
        if not isinstance(blockers, list) or not all(_safe_id(item) for item in blockers):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{step_id} blocker codes are invalid"))
            blockers = []
        gate_valid = _gate_summary(step.get("gates"), step_id, findings)
        if step.get("execution_request_ref") is not None:
            findings.append(finding("ORCH.IDENTITY.MISMATCH", f"{step_id} reverse execution-request ref must remain null"))
        if not _list_of_refs(step.get("input_records")):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{step_id} input records are invalid"))
        outputs = step.get("output_contracts")
        output_keys = {"contract_name", "schema_version", "role", "required"}
        if (
            not isinstance(outputs, list)
            or not outputs
            or not all(
                isinstance(output, dict)
                and set(output) == output_keys
                and _safe_id(output.get("contract_name"))
                and output.get("schema_version") == "1.0"
                and _safe_id(output.get("role"))
                and isinstance(output.get("required"), bool)
                for output in outputs
            )
        ):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{step_id} declares no output contract"))
        calculation_ref = step.get("calculation_envelope_ref")
        if calculation_ref is not None and (
            not _valid_ref(calculation_ref)
            or calculation_ref.get("contract_name") != "calculation-record-envelope"
        ):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{step_id} calculation envelope ref is invalid"))
        maturity = step.get("maturity")
        if (
            not isinstance(maturity, dict)
            or set(maturity) != {"implementation", "validation", "claim_ceiling"}
            or maturity.get("implementation") not in {"unsupported", "contract-only", "implemented"}
            or maturity.get("validation") not in {
                "design-only", "synthetic-validated", "format-fixture-validated",
                "real-artifact-validated", "tool-integration-validated",
            }
            or maturity.get("claim_ceiling") not in CLAIMS
        ):
            findings.append(finding("ORCH.CONTRACT.INVALID", f"{step_id} maturity is invalid"))
        if step.get("state") == "ready" and (blockers or not gate_valid or step.get("gates", {}).get("status") != "pass"):
            findings.append(finding("ORCH.STEP.NOT_READY", f"{step_id} is ready but has a blocker or nonpassing gate", severity="blocking"))

    id_set = set(step_ids)
    for index, step_id in enumerate(step_ids):
        for dependency in dependencies.get(step_id, []):
            if dependency not in id_set:
                findings.append(finding("ORCH.DAG.UNKNOWN_DEPENDENCY", f"{step_id} depends on unknown {dependency}"))
            elif dependency == step_id:
                findings.append(finding("ORCH.DAG.CYCLE", f"{step_id} depends on itself"))
            elif step_ids.index(dependency) >= index:
                findings.append(finding("ORCH.STEP.NOT_READY", f"{step_id} is not dependency ordered after {dependency}", severity="blocking"))
            elif (
                states.get(dependency) != "completed"
                and states.get(step_id) in {"ready", "running", "completed"}
            ):
                findings.append(finding("ORCH.STEP.NOT_READY", f"{step_id} advanced before dependency {dependency} completed", severity="blocking"))
    cycle = _cycle(step_ids, dependencies)
    if cycle:
        findings.append(finding("ORCH.DAG.CYCLE", "dependency cycle: " + " -> ".join(cycle)))

    policy = plan.get("authorization_policy")
    policy_keys = {"human_decision_required", "lease_required", "side_effects", "scope_labels"}
    if not isinstance(policy, dict) or set(policy) != policy_keys:
        findings.append(finding("ORCH.CONTRACT.INVALID", "authorization policy has invalid fields"))
    else:
        effects = policy.get("side_effects")
        scopes = policy.get("scope_labels")
        invalid_policy_shape = (
            not isinstance(policy.get("human_decision_required"), bool)
            or not isinstance(policy.get("lease_required"), bool)
            or not isinstance(effects, list)
            or not all(isinstance(item, str) and item in SIDE_EFFECTS for item in effects)
            or len(effects) != len(set(effects))
            or not isinstance(scopes, list)
            or not all(_safe_label(item) for item in scopes)
            or len(scopes) != len(set(scopes))
        )
        if invalid_policy_shape:
            findings.append(finding("ORCH.CONTRACT.INVALID", "authorization policy values are invalid"))
        elif side_effecting and (
            policy.get("human_decision_required") is not True
            or policy.get("lease_required") is not True
            or not effects
            or not scopes
        ):
            findings.append(finding("ORCH.AUTH.POLICY_MISSING", "side-effecting workflow lacks bounded human-decision and lease policy", severity="blocking"))
        elif not side_effecting and (
            policy.get("human_decision_required") is not False
            or policy.get("lease_required") is not False
            or effects
            or scopes
        ):
            findings.append(finding("ORCH.CONTRACT.INVALID", "non-side-effecting workflow has an inconsistent authorization policy"))

    if plan.get("status") == "ready":
        if plan.get("blocker_codes") or not plan_gates_valid or plan.get("gates", {}).get("status") != "pass":
            findings.append(finding("ORCH.STEP.NOT_READY", "ready plan has blockers or a nonpassing gate", severity="blocking"))
        for step in steps:
            if isinstance(step, dict) and step.get("state") not in {"ready", "completed"}:
                findings.append(finding("ORCH.STEP.NOT_READY", f"ready plan contains step state {step.get('state')}", severity="blocking"))
                break
    if plan.get("status") == "blocked" and not plan.get("blocker_codes"):
        findings.append(finding("ORCH.CONTRACT.INVALID", "blocked plan requires a blocker code"))
    if (
        plan.get("status") == "blocked"
        and isinstance(plan.get("gates"), dict)
        and plan["gates"].get("status") != "blocked"
    ):
        findings.append(finding("ORCH.CONTRACT.INVALID", "blocked plan requires a blocked plan gate"))
    if plan.get("status") == "completed" and any(
        isinstance(step, dict) and step.get("state") not in {"completed", "skipped"}
        for step in steps
    ):
        findings.append(finding("ORCH.STATE.CONFLATED", "completed workflow contains a nonterminal step state"))
    return findings


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


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def audit_authorization(
    request: dict[str, Any],
    request_sha256: str,
    decision: dict[str, Any],
    at_utc: datetime,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    invalid: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    if not _exact_keys(request, REQUEST_KEYS, "execution request", invalid, code="ORCH.REQUEST.INVALID"):
        return invalid, blocked
    if _contains_sensitive_text(request):
        invalid.append(finding("ORCH.REQUEST.INVALID", "execution request contains a secret-like value or private absolute path"))
    if request.get("schema_version") != "1.0" or request.get("contract_name") != "execution-request":
        invalid.append(finding("ORCH.REQUEST.INVALID", "expected execution-request@1.0"))
    if not _safe_id(request.get("request_id")) or not _safe_id(request.get("workflow_step_id")):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request identity is invalid"))
    if (
        _parse_utc(request.get("created_utc")) is None
        or not _valid_actor(request.get("requested_by"))
        or not _safe_id(request.get("operation_id"))
        or not _safe_id(request.get("environment_profile_id"))
    ):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request provenance or routing identity is invalid"))
    if (
        not _valid_ref(request.get("workflow_plan_ref"))
        or request["workflow_plan_ref"].get("contract_name") != "workflow-plan"
        or request["workflow_plan_ref"].get("role") != "workflow-plan"
    ):
        invalid.append(finding("ORCH.REQUEST.INVALID", "workflow plan reference is invalid"))
    argv = request.get("argv")
    if (
        request.get("command_kind") != "argv"
        or request.get("shell") is not False
        or not isinstance(argv, list)
        or not argv
        or not all(
            isinstance(item, str)
            and 0 < len(item) <= 4096
            and not any(ord(character) < 32 or ord(character) == 127 for character in item)
            for item in argv
        )
        or not EXECUTABLE.fullmatch(argv[0])
        or argv[0].casefold() in SHELLS
        or any(SECRET.search(item) for item in argv)
    ):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request must contain a bounded secret-free argv and shell=false"))
    if request.get("execution_mode") not in {"dry-run", "execute"} or not _safe_label(request.get("working_directory_label")):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request mode or working-directory label is invalid"))
    retry = request.get("retry_policy")
    if (
        not isinstance(retry, dict)
        or set(retry) != {"maximum_attempts", "automatic_retry", "retryable_finding_codes"}
        or retry.get("automatic_retry") is not False
        or not _bounded_integer(retry.get("maximum_attempts"), 1, 20)
        or not isinstance(retry.get("retryable_finding_codes"), list)
        or not all(_safe_id(item) for item in retry.get("retryable_finding_codes", []))
        or len(retry.get("retryable_finding_codes", [])) != len(set(retry.get("retryable_finding_codes", [])))
    ):
        invalid.append(finding("ORCH.REQUEST.INVALID", "automatic retry must be false and attempts bounded"))
    resources = request.get("resources")
    resource_keys = {"scheduler_profile_id", "nodes", "mpi_ranks", "threads_per_rank", "gpus", "memory_mb", "walltime_s"}
    if not isinstance(resources, dict) or set(resources) != resource_keys or any(
        not _bounded_integer(resources.get(key), minimum, maximum)
        for key, minimum, maximum in (
            ("nodes", 1, 100_000),
            ("mpi_ranks", 1, 10_000_000),
            ("threads_per_rank", 1, 4096),
            ("gpus", 0, 1_000_000),
            ("memory_mb", 1, 1_000_000_000),
            ("walltime_s", 1, 604800),
        )
    ):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request resources are invalid"))
    elif resources.get("scheduler_profile_id") is not None and not _safe_id(resources.get("scheduler_profile_id")):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request scheduler profile is invalid"))
    inputs = request.get("inputs")
    outputs = request.get("expected_outputs")
    if not isinstance(inputs, list) or not inputs or not all(_valid_file_ref(item, "present") for item in inputs):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request inputs are not present and hash-bound"))
    if not isinstance(outputs, list) or not outputs or not all(_valid_file_ref(item, "missing") for item in outputs):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request expected outputs are invalid"))
    if not _list_of_refs(request.get("parent_records")):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request parent record refs are invalid"))
    auth = request.get("authorization_requirement")
    if not isinstance(auth, dict) or set(auth) != {"required", "side_effects", "scope_labels", "reason"}:
        invalid.append(finding("ORCH.REQUEST.INVALID", "authorization requirement is invalid"))
        auth = {}
    elif (
        auth.get("required") is not True
        or not isinstance(auth.get("side_effects"), list)
        or not auth["side_effects"]
        or not all(isinstance(item, str) and item in SIDE_EFFECTS for item in auth["side_effects"])
        or len(auth["side_effects"]) != len(set(auth["side_effects"]))
        or not isinstance(auth.get("scope_labels"), list)
        or not auth["scope_labels"]
        or not all(_safe_label(item) for item in auth["scope_labels"])
        or len(auth["scope_labels"]) != len(set(auth["scope_labels"]))
        or not isinstance(auth.get("reason"), str)
        or not auth["reason"].strip()
    ):
        blocked.append(finding("ORCH.AUTH.NOT_GRANTED", "request does not require bounded side-effect authorization", severity="blocking"))
    if request.get("state") != "prepared" or request.get("blocker_codes") != []:
        blocked.append(finding("ORCH.AUTH.NOT_GRANTED", "request is not prepared and blocker-free", severity="blocking"))
    _gate_summary(request.get("gates"), "execution request", invalid)
    if isinstance(request.get("gates"), dict) and request["gates"].get("status") != "pass":
        blocked.append(finding("ORCH.AUTH.NOT_GRANTED", "request gates do not pass", severity="blocking"))
    if not _bounded_integer(request.get("timeout_s"), 1, 604800):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request timeout is invalid"))
    if not _valid_producer(request.get("producer")):
        invalid.append(finding("ORCH.REQUEST.INVALID", "request producer provenance is invalid"))

    if not _exact_keys(decision, DECISION_KEYS, "decision record", invalid):
        return invalid, blocked
    if _contains_sensitive_text(decision):
        invalid.append(finding("ORCH.CONTRACT.INVALID", "decision contains a secret-like value or private absolute path"))
    if decision.get("schema_version") != "1.0" or decision.get("contract_name") != "decision-record":
        invalid.append(finding("ORCH.CONTRACT.INVALID", "expected decision-record@1.0"))
    if not _safe_id(decision.get("decision_id")):
        invalid.append(finding("ORCH.CONTRACT.INVALID", "decision identity is invalid"))
    if decision.get("decision_type") != "execution-authorization":
        blocked.append(finding("ORCH.AUTH.NOT_GRANTED", "decision type is not execution-authorization", severity="blocking"))
    subject = decision.get("subject_ref")
    if not _valid_ref(subject):
        invalid.append(finding("ORCH.CONTRACT.INVALID", "decision subject ref is invalid"))
    elif subject.get("contract_name") != "execution-request" or subject.get("role") != "execution-subject":
        invalid.append(finding("ORCH.CONTRACT.INVALID", "decision subject contract or role is invalid"))
    elif subject.get("record_id") != request.get("request_id") or subject.get("sha256") != request_sha256:
        blocked.append(finding("ORCH.AUTH.SUBJECT_MISMATCH", "decision subject does not resolve to exact request bytes", severity="blocking"))
    actor = decision.get("decided_by")
    if not _valid_actor(actor) or actor.get("actor_type") != "human":
        blocked.append(finding("ORCH.AUTH.NOT_GRANTED", "execution authorization must be a human decision", severity="blocking"))
    if decision.get("outcome") != "approved" or decision.get("scientific_acceptance") != "not_assessed":
        blocked.append(finding("ORCH.AUTH.NOT_GRANTED", "decision is not a non-scientific approval", severity="blocking"))
    decided = _parse_utc(decision.get("decided_utc"))
    valid_until = _parse_utc(decision.get("valid_until_utc"))
    request_created = _parse_utc(request.get("created_utc"))
    if (
        decided is None
        or request_created is None
        or decided < request_created
        or decided > at_utc
        or valid_until is None
        or valid_until <= at_utc
        or decided >= valid_until
    ):
        blocked.append(finding("ORCH.AUTH.NOT_GRANTED", "decision time chain is invalid or expired", severity="blocking"))
    requested_scope_values = auth.get("scope_labels", []) if isinstance(auth, dict) else []
    required_scopes = (
        set(requested_scope_values)
        if isinstance(requested_scope_values, list)
        and all(_safe_label(item) for item in requested_scope_values)
        else set()
    )
    decision_scopes = decision.get("scope_labels")
    if (
        not isinstance(decision_scopes, list)
        or not all(_safe_label(item) for item in decision_scopes)
        or len(decision_scopes) != len(set(decision_scopes))
        or set(decision_scopes) != required_scopes
    ):
        blocked.append(finding("ORCH.AUTH.NOT_GRANTED", "decision scopes do not exactly match request scopes", severity="blocking"))
    evidence_refs = decision.get("evidence_refs")
    exact_evidence = isinstance(evidence_refs, list) and any(
        _valid_ref(item)
        and item.get("contract_name") == "execution-request"
        and item.get("record_id") == request.get("request_id")
        and item.get("sha256") == request_sha256
        for item in evidence_refs
    )
    if not exact_evidence:
        blocked.append(finding("ORCH.AUTH.NOT_GRANTED", "decision lacks exact request evidence", severity="blocking"))
    if (
        not _list_of_refs(evidence_refs)
        or not isinstance(decision.get("evidence_ids"), list)
        or not decision["evidence_ids"]
        or not all(_safe_id(item) for item in decision["evidence_ids"])
        or len(decision["evidence_ids"]) != len(set(decision["evidence_ids"]))
        or not set(decision["evidence_ids"]).issubset(
            {item.get("record_id") for item in evidence_refs if isinstance(item, dict)}
        )
        or not isinstance(decision.get("rationale"), str)
        or not decision["rationale"].strip()
        or decision.get("claim_ceiling") not in EXECUTION_DECISION_CLAIMS
        or not isinstance(decision.get("limitations"), list)
        or not all(isinstance(item, str) and item.strip() for item in decision["limitations"])
        or not _valid_producer(decision.get("producer"))
    ):
        invalid.append(finding("ORCH.CONTRACT.INVALID", "decision evidence or producer provenance is invalid"))
    return invalid, blocked


def minimum_next_action(plan: dict[str, Any], findings: list[dict[str, str]]) -> str:
    if findings:
        mapping = {
            "ORCH.JSON.INVALID": "replace-input-with-one-strict-json-object",
            "ORCH.CONTRACT.INVALID": "repair-first-invalid-contract-field",
            "ORCH.DAG.DUPLICATE_STEP": "assign-unique-step-ids",
            "ORCH.DAG.UNKNOWN_DEPENDENCY": "resolve-first-unknown-dependency",
            "ORCH.DAG.CYCLE": "break-first-dependency-cycle",
            "ORCH.ROUTE.NOT_ACTIVE": "promote-or-replace-first-nonactive-route",
            "ORCH.STEP.NOT_READY": "resolve-first-step-readiness-blocker",
            "ORCH.AUTH.POLICY_MISSING": "add-bounded-human-authorization-policy",
            "ORCH.IDENTITY.MISMATCH": "repair-first-exact-byte-reference",
            "ORCH.STATE.CONFLATED": "separate-state-layers",
        }
        return mapping.get(findings[0]["code"], "resolve-first-decisive-finding")
    for step in plan.get("steps", []):
        if step.get("state") == "ready":
            if step.get("execution_class") in SIDE_EFFECTING:
                return f"prepare-immutable-execution-request-for-{step['step_id']}"
            return f"invoke-active-skill-for-{step['step_id']}"
    if all(step.get("state") in {"completed", "skipped"} for step in plan.get("steps", [])):
        return "prepare-claim-evidence-map-for-human-review"
    return "reconcile-persisted-workflow-events"


def report(
    command: str,
    status: str,
    findings: list[dict[str, str]],
    evidence: list[dict[str, str]],
    next_action: str,
    states: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "contract_name": "candidate-orchestrator-report",
        "tool": {"name": "orchestrator-cli", "version": TOOL_VERSION},
        "command": command,
        "status": status,
        "dry_run": True,
        "side_effect_performed": False,
        "execute": False,
        "lease_issued": False,
        "workflow_event_emitted": False,
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
        "limitations": [
            "This development Skill performs offline bounded checks only.",
            "A valid plan or authorization record does not issue a lease or execute a job.",
            "Scheduler, process, application, numerical, and human scientific states remain independent.",
            "This unsigned report can be altered after emission and must be exact-byte bound by a trusted external manifest before evidentiary use.",
        ],
    }


def _plan_state_projection(plan: dict[str, Any]) -> tuple[str, dict[str, str]]:
    workflow_states = {"draft", "ready", "blocked", "executing", "completed", "abandoned"}
    step_states = {"planned", "ready", "blocked", "running", "completed", "failed", "skipped"}
    workflow = plan.get("status")
    projected_steps: dict[str, str] = {}
    steps = plan.get("steps")
    if isinstance(steps, list):
        for index, item in enumerate(steps):
            if not isinstance(item, dict):
                continue
            step_id = item.get("step_id")
            label = step_id if _safe_id(step_id) else f"invalid-{index}"
            state = item.get("state")
            projected_steps[label] = state if state in step_states else "not_observed"
    return (
        workflow if workflow in workflow_states else "not_observed",
        projected_steps,
    )


def _print(value: dict[str, Any]) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("audit-plan", "next-action"):
        command = sub.add_parser(name)
        command.add_argument("--plan", required=True, type=Path)
    command = sub.add_parser("authorize-check")
    command.add_argument("--request", required=True, type=Path)
    command.add_argument("--decision", required=True, type=Path)
    command.add_argument("--at-utc", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command in {"audit-plan", "next-action"}:
            plan, digest = strict_load(args.plan)
            findings = audit_plan(plan)
            has_invalid = any(item["severity"] == "critical" for item in findings)
            status = "fail" if has_invalid else "blocked" if findings else "pass"
            next_action = minimum_next_action(plan, findings)
            workflow_state, step_states = _plan_state_projection(plan)
            _print(report(
                args.command,
                status,
                findings,
                [{"contract_name": "workflow-plan", "sha256": digest, "role": "audited-plan"}],
                next_action,
                {
                    "workflow": workflow_state,
                    "steps": step_states,
                    "scheduler": "not_observed",
                    "process": "not_observed",
                    "application": "not_observed",
                    "scientific": "not_assessed",
                },
            ))
            return 2 if status == "fail" else 3 if status == "blocked" else 0

        at_utc = _parse_utc(args.at_utc)
        if at_utc is None:
            raise InputFailure("evaluation time must be a timezone-aware ISO 8601 value")
        request, request_digest = strict_load(args.request)
        decision, decision_digest = strict_load(args.decision)
        invalid, blocked = audit_authorization(request, request_digest, decision, at_utc.astimezone(timezone.utc))
        findings = invalid + blocked
        status = "fail" if invalid else "blocked" if blocked else "pass"
        _print(report(
            args.command,
            status,
            findings,
            [
                {"contract_name": "execution-request", "sha256": request_digest, "role": "authorization-subject"},
                {"contract_name": "decision-record", "sha256": decision_digest, "role": "authorization-decision"},
            ],
            "repair-first-invalid-contract-field" if invalid else "obtain-valid-bounded-human-authorization" if blocked else "request-bounded-single-use-lease",
            {
                "workflow": "not_observed", "steps": {}, "scheduler": "not_submitted",
                "process": "not_started", "application": "not_started", "scientific": "not_assessed",
            },
        ))
        return 2 if invalid else 3 if blocked else 0
    except InputFailure as exc:
        _print(report(
            args.command,
            "fail",
            [finding("ORCH.JSON.INVALID", str(exc))],
            [],
            "replace-input-with-one-strict-json-object",
            {
                "workflow": "not_observed", "steps": {}, "scheduler": "not_observed",
                "process": "not_observed", "application": "not_observed", "scientific": "not_assessed",
            },
        ))
        return 2
    except (OSError, ValueError, TypeError, KeyError):
        _print(report(
            args.command,
            "fail",
            [finding("ORCH.CONTRACT.INVALID", "bounded deterministic audit failed")],
            [],
            "inspect-input-and-rerun",
            {
                "workflow": "not_observed", "steps": {}, "scheduler": "not_observed",
                "process": "not_observed", "application": "not_observed", "scientific": "not_assessed",
            },
        ))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
