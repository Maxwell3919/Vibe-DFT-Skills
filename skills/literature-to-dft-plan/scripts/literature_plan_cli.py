#!/usr/bin/env python3
"""Offline fail-closed literature evidence, inference, and DFT plan tooling."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
from typing import Any


sys.dont_write_bytecode = True

TOOL_VERSION = "0.1.0-candidate"
MAX_INPUT_BYTES = 4 * 1024 * 1024
SAFE_ID = re.compile(r"^[a-z0-9]+(?:[a-z0-9._-]*[a-z0-9])?$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
PRIVATE_PATH = re.compile(r"(?i)(?:/Users/|/home/|/scratch/|/private/|/tmp/|/Volumes/|[A-Za-z]:[\\/]|\\\\)")
SECRET = re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|password|secret|bearer)\s*[:=]")
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")

REQUEST_KEYS = {
    "schema_version", "contract_name", "request_id", "plan_id", "generated_utc",
    "objective", "target_observables", "sources", "facts", "inferences",
    "assumptions", "new_claims", "calculation_steps", "limitations",
}
SOURCE_KEYS = {
    "source_id", "source_kind", "citation_label", "identifier", "version",
    "retrieval_status", "content_sha256", "source_record_ref", "license_status",
    "redistribution", "limitations",
}
FACT_KEYS = {
    "fact_id", "classification", "statement", "text_mode", "quantity",
    "source_id", "locator", "evidence_status", "limitations",
}
QUANTITY_KEYS = {"value", "unit", "reported_precision"}
INFERENCE_KEYS = {"inference_id", "classification", "statement", "premise_fact_ids", "uncertainty", "validation_action", "status"}
ASSUMPTION_KEYS = {
    "assumption_id", "classification", "statement", "owner", "status", "validation_evidence_ids",
    "impact", "failure_consequence",
}
NEW_CLAIM_KEYS = {
    "new_claim_id", "classification", "question", "premise_inference_ids",
    "validation_step_ids", "status", "claim_ceiling",
}
STEP_KEYS = {
    "step_id", "engine_skill", "route_lifecycle", "task_type", "observable_ids",
    "tests_inference_ids", "tests_new_claim_ids", "assumption_ids", "required_evidence",
    "authorization_required", "status",
}
PLAN_KEYS = {
    "schema_version", "contract_name", "plan_id", "request_id", "generated_utc",
    "objective", "target_observables", "request_sha256", "retrieval_evidence",
    "source_assertions", "quoted_numerical_facts", "proposed_inferences",
    "project_choices", "new_claim_proposals", "calculation_steps", "status",
    "claim_ceiling", "gates", "findings",
    "minimum_next_action", "network_access_performed", "calculation_authorized",
    "execution_started", "external_message_sent", "limitations", "producer",
}

_DIRECTORY_BINDINGS: dict[str, tuple[int, int, int]] = {}
_OPENAT_SUPPORTED = os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd
_LINKAT_SUPPORTED = all(
    function in os.supports_dir_fd for function in (os.open, os.stat, os.link, os.unlink)
)


class InputFailure(ValueError):
    """A bounded user-correctable input error."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputFailure("duplicate JSON key")
        result[key] = value
    return result


def _constant(_value: str) -> None:
    raise InputFailure("non-finite JSON number")


def _file_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        stat.S_IFMT(value.st_mode), value.st_dev, value.st_ino, value.st_nlink,
        value.st_size, value.st_mtime_ns, value.st_ctime_ns,
    )


def _directory_identity(value: os.stat_result) -> tuple[int, int, int]:
    return stat.S_IFMT(value.st_mode), value.st_dev, value.st_ino


def _reset_io_bindings() -> None:
    for _device, _inode, descriptor in _DIRECTORY_BINDINGS.values():
        try:
            os.close(descriptor)
        except OSError:
            pass
    _DIRECTORY_BINDINGS.clear()


def _normalized_absolute(path: Path) -> Path:
    """Resolve only a platform root alias; preserve lower components lexically."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    parts = absolute.parts
    if len(parts) > 1:
        first = Path(parts[0]) / parts[1]
        try:
            first_metadata = first.lstat()
        except OSError:
            return absolute
        if stat.S_ISLNK(first_metadata.st_mode):
            try:
                resolved_first = first.resolve(strict=True)
                resolved_metadata = resolved_first.lstat()
            except OSError as exc:
                raise InputFailure("platform root alias is unstable") from exc
            if not stat.S_ISDIR(resolved_metadata.st_mode):
                raise InputFailure("platform root alias is not a directory")
            absolute = resolved_first.joinpath(*parts[2:])
    return absolute


def _bound_directory_descriptor(directory: Path) -> tuple[int, Path]:
    """Traverse each component with openat/no-follow and retain lexical bindings."""

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory_flag is None or nonblock is None or not _OPENAT_SUPPORTED:
        raise InputFailure("platform lacks stable dirfd no-follow traversal")
    absolute = _normalized_absolute(directory)
    root = Path(absolute.anchor)
    flags = os.O_RDONLY | directory_flag | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)
    descriptors: list[int] = []
    edges: list[tuple[int, str, int, os.stat_result]] = []
    try:
        root_path_metadata = root.lstat()
        if stat.S_ISLNK(root_path_metadata.st_mode) or not stat.S_ISDIR(root_path_metadata.st_mode):
            raise InputFailure("filesystem root is unavailable or unsafe")
        current_fd = os.open(root, flags)
        descriptors.append(current_fd)
        current_metadata = os.fstat(current_fd)
        if _directory_identity(current_metadata) != _directory_identity(root_path_metadata):
            raise InputFailure("directory identity changed during traversal")
        root_key = os.fspath(root)
        retained_root = _DIRECTORY_BINDINGS.get(root_key)
        if retained_root is None:
            _DIRECTORY_BINDINGS[root_key] = (
                current_metadata.st_dev, current_metadata.st_ino, os.dup(current_fd),
            )
        elif retained_root[:2] != (current_metadata.st_dev, current_metadata.st_ino):
            raise InputFailure("bound filesystem root changed identity")

        current_path = root
        for component in absolute.parts[1:]:
            anchored_before = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(anchored_before.st_mode) or not stat.S_ISDIR(anchored_before.st_mode):
                raise InputFailure("intermediate path component is a symlink or non-directory")
            child_fd = os.open(component, flags, dir_fd=current_fd)
            child_metadata = os.fstat(child_fd)
            if _directory_identity(child_metadata) != _directory_identity(anchored_before):
                os.close(child_fd)
                raise InputFailure("intermediate directory changed during openat")
            current_path = current_path / component
            binding_key = os.fspath(current_path)
            retained = _DIRECTORY_BINDINGS.get(binding_key)
            if retained is None:
                _DIRECTORY_BINDINGS[binding_key] = (
                    child_metadata.st_dev, child_metadata.st_ino, os.dup(child_fd),
                )
            else:
                if retained[:2] != (child_metadata.st_dev, child_metadata.st_ino):
                    os.close(child_fd)
                    raise InputFailure("request or evidence base changed identity")
                retained_fd = os.dup(retained[2])
                retained_metadata = os.fstat(retained_fd)
                if _directory_identity(retained_metadata) != _directory_identity(child_metadata):
                    os.close(retained_fd)
                    os.close(child_fd)
                    raise InputFailure("retained request or evidence base is unstable")
                os.close(child_fd)
                child_fd = retained_fd
                child_metadata = retained_metadata
            edges.append((current_fd, component, child_fd, child_metadata))
            descriptors.append(child_fd)
            current_fd = child_fd

        for parent_fd, component, child_fd, child_metadata in edges:
            anchored_after = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            opened_after = os.fstat(child_fd)
            if (
                not stat.S_ISDIR(anchored_after.st_mode)
                or _directory_identity(anchored_after) != _directory_identity(child_metadata)
                or _directory_identity(opened_after) != _directory_identity(child_metadata)
            ):
                raise InputFailure("intermediate directory changed during traversal")
        lexical_final = absolute.lstat()
        if _directory_identity(lexical_final) != _directory_identity(os.fstat(current_fd)):
            raise InputFailure("request or evidence base changed during traversal")
        return os.dup(current_fd), absolute
    except InputFailure:
        raise
    except OSError as exc:
        raise InputFailure("directory path cannot be traversed without aliases") from exc
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _verify_bound_directory(directory: Path, descriptor: int) -> None:
    verification_fd, _normalized = _bound_directory_descriptor(directory)
    try:
        if _directory_identity(os.fstat(verification_fd)) != _directory_identity(os.fstat(descriptor)):
            raise InputFailure("request or evidence base changed during I/O")
    finally:
        os.close(verification_fd)


def strict_load(path: Path) -> tuple[dict[str, Any], str]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        raise InputFailure("platform lacks nonblocking no-follow input support")
    absolute = _normalized_absolute(path)
    if absolute.name in {"", ".", ".."}:
        raise InputFailure("input filename is invalid")
    parent_fd, _normalized_parent = _bound_directory_descriptor(absolute.parent)
    descriptor: int | None = None
    try:
        descriptor = os.open(
            absolute.name,
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise InputFailure("input must be a regular, non-symlink, single-link file")
        if before.st_size < 2 or before.st_size > MAX_INPUT_BYTES:
            raise InputFailure("input size is outside the allowed range")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65536, MAX_INPUT_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_INPUT_BYTES:
                raise InputFailure("input size is outside the allowed range")
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        anchored_final = os.stat(absolute.name, dir_fd=parent_fd, follow_symlinks=False)
        lexical_final = absolute.lstat()
        _verify_bound_directory(absolute.parent, parent_fd)
    except InputFailure:
        raise
    except OSError as exc:
        raise InputFailure("input is unavailable or cannot be read safely") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_fd)
    identity = _file_identity(before)
    if (
        identity != _file_identity(after)
        or identity != _file_identity(anchored_final)
        or identity != _file_identity(lexical_final)
        or not stat.S_ISREG(anchored_final.st_mode)
        or anchored_final.st_nlink != 1
        or len(raw) != before.st_size
    ):
        raise InputFailure("input changed while being read")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise InputFailure("UTF-8 BOM is forbidden")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, InputFailure) as exc:
        raise InputFailure("input is not one strict UTF-8 JSON object") from exc
    if not isinstance(value, dict):
        raise InputFailure("top-level JSON value must be an object")
    return value, hashlib.sha256(raw).hexdigest()


def guard_output(output: Path, inputs: list[Path]) -> None:
    absolute = _normalized_absolute(output)
    if absolute.name in {"", ".", ".."}:
        raise InputFailure("output filename is invalid")
    output_name = os.path.normcase(os.fspath(absolute))
    for source in inputs:
        if output_name == os.path.normcase(os.fspath(_normalized_absolute(source))):
            raise InputFailure("output aliases an input; overwrite is forbidden")
    parent_fd, _normalized_parent = _bound_directory_descriptor(absolute.parent)
    try:
        if _metadata_at(parent_fd, absolute.name) is not None:
            raise InputFailure("output exists; overwrite is forbidden")
        _verify_bound_directory(absolute.parent, parent_fd)
    finally:
        os.close(parent_fd)


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _metadata_at(directory_fd: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise InputFailure("output name cannot be inspected safely") from exc


def _same_inode_size(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        stat.S_ISREG(left.st_mode)
        and stat.S_ISREG(right.st_mode)
        and (left.st_dev, left.st_ino, left.st_size)
        == (right.st_dev, right.st_ino, right.st_size)
    )


def _fd_payload_matches(descriptor: int, payload: bytes) -> bool:
    if not hasattr(os, "pread"):
        return False
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != len(payload):
        return False
    digest = hashlib.sha256()
    offset = 0
    while offset < len(payload):
        block = os.pread(descriptor, min(1024 * 1024, len(payload) - offset), offset)
        if not block:
            return False
        digest.update(block)
        offset += len(block)
    return offset == len(payload) and digest.digest() == hashlib.sha256(payload).digest()


def _unlink_if_identity(directory_fd: int, name: str, expected: os.stat_result) -> bool:
    try:
        current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (expected.st_dev, expected.st_ino):
            return False
        os.unlink(name, dir_fd=directory_fd)
        return True
    except OSError:
        return False


def write_new(path: Path, value: dict[str, Any]) -> str:
    raw = canonical_bytes(value)
    digest = hashlib.sha256(raw).hexdigest()
    absolute = _normalized_absolute(path)
    if absolute.name in {"", ".", ".."}:
        raise InputFailure("output filename is invalid")
    if not _LINKAT_SUPPORTED:
        raise InputFailure("platform lacks safe hard-link publication support")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise InputFailure("platform lacks no-follow staging support")
    directory_fd, _normalized_parent = _bound_directory_descriptor(absolute.parent)
    temporary_fd: int | None = None
    temporary_name: str | None = None
    linked_target: os.stat_result | None = None
    installed = False
    try:
        if _metadata_at(directory_fd, absolute.name) is not None:
            raise InputFailure("output exists; overwrite is forbidden")
        for _attempt in range(32):
            candidate = f".{absolute.name}.literature-plan-{secrets.token_hex(12)}.tmp"
            try:
                temporary_fd = os.open(
                    candidate,
                    os.O_RDWR | os.O_CREAT | os.O_EXCL | nofollow | getattr(os, "O_CLOEXEC", 0),
                    0o600,
                    dir_fd=directory_fd,
                )
            except FileExistsError:
                continue
            temporary_name = candidate
            break
        if temporary_fd is None or temporary_name is None:
            raise InputFailure("private output staging file cannot be created")
        offset = 0
        while offset < len(raw):
            written = os.write(temporary_fd, raw[offset:])
            if written <= 0:
                raise OSError("short output write")
            offset += written
        os.fsync(temporary_fd)
        staged_fd = os.fstat(temporary_fd)
        staged_name = _metadata_at(directory_fd, temporary_name)
        if (
            staged_name is None
            or staged_fd.st_nlink != 1
            or not _same_inode_size(staged_fd, staged_name)
            or staged_fd.st_size != len(raw)
            or not _fd_payload_matches(temporary_fd, raw)
        ):
            raise InputFailure("staged output identity or payload is invalid")
        _verify_bound_directory(absolute.parent, directory_fd)
        if _metadata_at(directory_fd, absolute.name) is not None:
            raise InputFailure("output appeared during staging; overwrite is forbidden")
        try:
            os.link(
                temporary_name,
                absolute.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise InputFailure("output appeared concurrently; overwrite is forbidden") from exc
        linked_target = staged_fd
        held_after_link = os.fstat(temporary_fd)
        published = _metadata_at(directory_fd, absolute.name)
        source_after_link = _metadata_at(directory_fd, temporary_name)
        if (
            published is None
            or source_after_link is None
            or held_after_link.st_nlink != 2
            or published.st_nlink != 2
            or source_after_link.st_nlink != 2
            or not _same_inode_size(published, held_after_link)
            or not _same_inode_size(source_after_link, held_after_link)
            or not _fd_payload_matches(temporary_fd, raw)
        ):
            if (
                published is not None
                and source_after_link is not None
                and _same_inode_size(published, source_after_link)
            ):
                _unlink_if_identity(directory_fd, absolute.name, published)
            raise InputFailure("staging name was substituted during publication")
        linked_target = published
        os.fsync(directory_fd)
        os.unlink(temporary_name, dir_fd=directory_fd)
        temporary_name = None
        final_target = _metadata_at(directory_fd, absolute.name)
        held_final = os.fstat(temporary_fd)
        if (
            final_target is None
            or final_target.st_nlink != 1
            or held_final.st_nlink != 1
            or not _same_inode_size(final_target, held_final)
            or not _fd_payload_matches(temporary_fd, raw)
        ):
            raise InputFailure("published output changed after installation")
        _verify_bound_directory(absolute.parent, directory_fd)
        os.fsync(directory_fd)
        installed = True
        linked_target = None
    except InputFailure:
        raise
    except OSError as exc:
        raise InputFailure("output cannot be written and published safely") from exc
    finally:
        if linked_target is not None and not installed:
            removed = _unlink_if_identity(directory_fd, absolute.name, linked_target)
            if removed:
                try:
                    os.fsync(directory_fd)
                except OSError:
                    pass
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
                os.fsync(directory_fd)
            except OSError:
                pass
        if temporary_fd is not None:
            try:
                os.close(temporary_fd)
            except OSError:
                pass
        os.close(directory_fd)
    return digest


def finding(code: str, location: str, message: str, next_action: str, severity: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message, "next_action": next_action, "severity": severity}


def _safe_id(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 128 and SAFE_ID.fullmatch(value) is not None


def _ref(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"contract_name", "schema_version", "record_id", "sha256", "role"}
        and _safe_id(value.get("contract_name"))
        and value.get("schema_version") == "1.0"
        and _safe_id(value.get("record_id"))
        and isinstance(value.get("sha256"), str)
        and SHA256.fullmatch(value["sha256"]) is not None
        and _safe_id(value.get("role"))
    )


def _privacy(value: Any, location: str = "$") -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            result.extend(_privacy(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(_privacy(child, f"{location}[{index}]"))
    elif isinstance(value, str) and (PRIVATE_PATH.search(value) or SECRET.search(value) or EMAIL.search(value)):
        result.append(finding("LIT.PRIVACY.UNSAFE_TEXT", location, "privacy-sensitive text is forbidden", "replace it with an anonymized label", "critical"))
    return result


def _status(findings: list[dict[str, str]]) -> str:
    if any(item["severity"] == "critical" for item in findings):
        return "fail"
    return "blocked" if findings else "pass"


def _exit(status: str) -> int:
    return {"pass": 0, "fail": 2, "blocked": 3}[status]


def _unique(items: Any, field: str) -> bool:
    if not isinstance(items, list):
        return False
    values = [item.get(field) for item in items if isinstance(item, dict)]
    return len(values) == len(items) and all(_safe_id(item) for item in values) and len(values) == len(set(values))


def validate_request(value: dict[str, Any]) -> list[dict[str, str]]:
    findings = _privacy(value)
    if set(value) != REQUEST_KEYS or value.get("schema_version") != "1.0" or value.get("contract_name") != "literature-dft-request":
        findings.append(finding("LIT.CONTRACT.INVALID", "$", "request fields or identity are invalid", "repair the exact candidate request fields", "critical"))
        return findings
    if not all(_safe_id(value.get(name)) for name in ("request_id", "plan_id")):
        findings.append(finding("LIT.IDENTITY.INVALID", "$.request_id", "request or plan ID is invalid", "use unique safe IDs", "critical"))
    if not isinstance(value.get("objective"), str) or not value["objective"].strip():
        findings.append(finding("LIT.OBJECTIVE.MISSING", "$.objective", "objective is missing", "state the bounded scientific objective", "blocking"))
    if not isinstance(value.get("generated_utc"), str) or UTC.fullmatch(value["generated_utc"]) is None:
        findings.append(finding("LIT.CONTRACT.INVALID", "$.generated_utc", "generated_utc is invalid", "repair the exact candidate request fields", "critical"))
    observables = value.get("target_observables")
    if not isinstance(observables, list) or not observables or not all(_safe_id(item) for item in observables) or len(observables) != len(set(observables)):
        findings.append(finding("LIT.OBJECTIVE.OBSERVABLE_INVALID", "$.target_observables", "target observables are empty, invalid, or duplicated", "name bounded observable IDs", "critical"))
    for field, id_field in (("sources", "source_id"), ("facts", "fact_id"), ("inferences", "inference_id"), ("assumptions", "assumption_id"), ("new_claims", "new_claim_id"), ("calculation_steps", "step_id")):
        if not _unique(value.get(field), id_field):
            findings.append(finding("LIT.IDENTITY.DUPLICATE", f"$.{field}", f"{field} identities are invalid or duplicated", "use unique safe IDs", "critical"))
    return findings


def build_plan(request: dict[str, Any], request_sha: str) -> dict[str, Any]:
    findings = validate_request(request)
    sources = request.get("sources") if isinstance(request.get("sources"), list) else []
    facts = request.get("facts") if isinstance(request.get("facts"), list) else []
    inferences = request.get("inferences") if isinstance(request.get("inferences"), list) else []
    assumptions = request.get("assumptions") if isinstance(request.get("assumptions"), list) else []
    new_claims = request.get("new_claims") if isinstance(request.get("new_claims"), list) else []
    steps = request.get("calculation_steps") if isinstance(request.get("calculation_steps"), list) else []
    source_by_id = {item.get("source_id"): item for item in sources if isinstance(item, dict)}
    fact_by_id = {item.get("fact_id"): item for item in facts if isinstance(item, dict)}
    inference_by_id = {item.get("inference_id"): item for item in inferences if isinstance(item, dict)}
    assumption_by_id = {item.get("assumption_id"): item for item in assumptions if isinstance(item, dict)}
    new_claim_by_id = {item.get("new_claim_id"): item for item in new_claims if isinstance(item, dict)}
    step_by_id = {item.get("step_id"): item for item in steps if isinstance(item, dict)}
    namespaces = [set(source_by_id), set(fact_by_id), set(inference_by_id), set(assumption_by_id), set(new_claim_by_id), set(step_by_id)]
    for index, left in enumerate(namespaces):
        for right in namespaces[index + 1:]:
            if left.intersection(right):
                findings.append(finding("LIT.CLASSIFICATION.ID_COLLISION", "$", "all source, fact, inference, choice, claim, and step IDs must be disjoint", "rename the colliding IDs", "critical"))
    for index, source in enumerate(sources):
        if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
            findings.append(finding("LIT.SOURCE.INVALID", f"$.sources[{index}]", "source fields are invalid", "repair the exact source metadata record", "critical"))
            continue
        if not _safe_id(source.get("source_id")) or not all(isinstance(source.get(field), str) and source[field].strip() for field in ("citation_label", "identifier")) or not isinstance(source.get("limitations"), list) or not all(isinstance(item, str) and item for item in source["limitations"]):
            findings.append(finding("LIT.SOURCE.INVALID", f"$.sources[{index}]", "source identity, citation, identifier, or limitations are invalid", "repair the exact source metadata record", "critical"))
        if source.get("source_kind") not in {"official-manual", "peer-reviewed-article", "review", "dataset", "synthetic-fixture"}:
            findings.append(finding("LIT.SOURCE.INVALID", f"$.sources[{index}].source_kind", "source kind is unsupported", "repair the exact source metadata record", "critical"))
        status = source.get("retrieval_status")
        digest = source.get("content_sha256")
        reference = source.get("source_record_ref")
        if status in {"retrieved", "externally-resolved"}:
            if not isinstance(digest, str) or SHA256.fullmatch(digest) is None or not _ref(reference):
                findings.append(finding("LIT.SOURCE.RETRIEVAL_EVIDENCE_MISSING", f"$.sources[{index}]", "resolved source lacks content hash or record ref", "provide exact retrieval evidence", "blocking"))
            elif source.get("source_kind") != "synthetic-fixture" and reference.get("contract_name") != "official-source-record":
                findings.append(finding("LIT.SOURCE.AUTHORITY_REF_INVALID", f"$.sources[{index}].source_record_ref", "real source does not use an official-source record", "supply an externally resolvable official-source ref", "blocking"))
        elif status in {"metadata-only", "missing"}:
            if digest is not None or reference is not None:
                findings.append(finding("LIT.SOURCE.STATUS_CONFLICT", f"$.sources[{index}]", "unresolved source claims resolved hash or ref", "remove unsupported retrieval claims", "critical"))
        else:
            findings.append(finding("LIT.SOURCE.INVALID", f"$.sources[{index}].retrieval_status", "retrieval status is invalid", "repair the exact source metadata record", "critical"))
        if source.get("source_kind") == "official-manual" and not isinstance(source.get("version"), str):
            findings.append(finding("LIT.SOURCE.VERSION_MISSING", f"$.sources[{index}].version", "official behavior source lacks a version", "supply a matching manual/software version", "blocking"))
        if source.get("version") is not None and (not isinstance(source.get("version"), str) or not source["version"].strip()):
            findings.append(finding("LIT.SOURCE.VERSION_INVALID", f"$.sources[{index}].version", "source version is empty or malformed", "supply a bounded version or null", "critical"))
        if source.get("license_status") not in {"known-open", "known-restricted", "unknown", "synthetic"} or source.get("redistribution") not in {"metadata-only", "redistributable", "restricted", "unknown"}:
            findings.append(finding("LIT.SOURCE.LICENSE_INVALID", f"$.sources[{index}]", "license or redistribution state is invalid", "record the bounded source license state", "critical"))
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict) or set(fact) != FACT_KEYS:
            findings.append(finding("LIT.FACT.INVALID", f"$.facts[{index}]", "fact fields are invalid", "repair the exact fact record", "critical"))
            continue
        if not _safe_id(fact.get("fact_id")) or not isinstance(fact.get("statement"), str) or not fact["statement"].strip() or not isinstance(fact.get("limitations"), list) or not all(isinstance(item, str) and item for item in fact["limitations"]):
            findings.append(finding("LIT.FACT.INVALID", f"$.facts[{index}]", "fact identity, statement, or limitations are invalid", "repair the exact fact record", "critical"))
        classification = fact.get("classification")
        if classification == "source-assertion":
            if fact.get("text_mode") != "paraphrase" or fact.get("quantity") is not None:
                findings.append(finding("LIT.FACT.CLASSIFICATION_INVALID", f"$.facts[{index}]", "source assertion must be a paraphrase without a numerical quantity", "repair the explicit fact classification", "critical"))
        elif classification == "quoted-numerical-fact":
            quantity = fact.get("quantity")
            if (
                fact.get("text_mode") != "structured-numerical"
                or not isinstance(quantity, dict)
                or set(quantity) != QUANTITY_KEYS
                or isinstance(quantity.get("value"), bool)
                or not isinstance(quantity.get("value"), (int, float))
                or not isinstance(quantity.get("unit"), str)
                or not quantity["unit"].strip()
                or not isinstance(quantity.get("reported_precision"), str)
                or not quantity["reported_precision"].strip()
            ):
                findings.append(finding("LIT.FACT.NUMERICAL_INVALID", f"$.facts[{index}]", "quoted numerical fact needs structured value, unit, and reported precision", "encode a structured value, unit, and reported precision without source prose", "critical"))
        else:
            findings.append(finding("LIT.FACT.CLASSIFICATION_INVALID", f"$.facts[{index}].classification", "fact classification is invalid", "repair the explicit fact classification", "critical"))
        source = source_by_id.get(fact.get("source_id"))
        if not isinstance(source, dict):
            findings.append(finding("LIT.FACT.SOURCE_UNKNOWN", f"$.facts[{index}].source_id", "fact source does not resolve", "bind an existing source ID", "critical"))
            continue
        if fact.get("evidence_status") != "extracted" or source.get("retrieval_status") not in {"retrieved", "externally-resolved"}:
            findings.append(finding("LIT.FACT.NOT_EXTRACTABLE", f"$.facts[{index}]", "metadata-only, missing, or conflicting evidence cannot support a fact", "retrieve and hash the exact source before extraction", "blocking"))
        if not isinstance(fact.get("locator"), str) or not fact["locator"].strip():
            findings.append(finding("LIT.FACT.LOCATOR_MISSING", f"$.facts[{index}].locator", "fact has no bounded source locator", "add a page, section, table, figure, or equation locator", "blocking"))
    for index, inference in enumerate(inferences):
        if not isinstance(inference, dict) or set(inference) != INFERENCE_KEYS:
            findings.append(finding("LIT.INFERENCE.INVALID", f"$.inferences[{index}]", "inference fields are invalid", "repair the exact inference record", "critical"))
            continue
        if not _safe_id(inference.get("inference_id")) or not all(isinstance(inference.get(field), str) and inference[field].strip() for field in ("statement", "uncertainty")):
            findings.append(finding("LIT.INFERENCE.INVALID", f"$.inferences[{index}]", "inference identity, statement, or uncertainty is invalid", "repair the exact inference record", "critical"))
        if inference.get("classification") != "inference":
            findings.append(finding("LIT.INFERENCE.CLASSIFICATION_INVALID", f"$.inferences[{index}].classification", "inference is not explicitly classified", "set classification to inference", "critical"))
        premises = inference.get("premise_fact_ids")
        if not isinstance(premises, list) or not premises or len(premises) != len(set(premises)) or any(item not in fact_by_id for item in premises):
            findings.append(finding("LIT.INFERENCE.PREMISE_INVALID", f"$.inferences[{index}].premise_fact_ids", "inference lacks resolved fact premises", "bind one or more extracted fact IDs", "critical"))
        if inference.get("status") != "proposed" or not isinstance(inference.get("validation_action"), str) or not inference["validation_action"].strip():
            findings.append(finding("LIT.INFERENCE.OVERCLAIM", f"$.inferences[{index}]", "inference is asserted or lacks a validation action", "keep it proposed and state how to test it", "critical"))
    for index, assumption in enumerate(assumptions):
        if not isinstance(assumption, dict) or set(assumption) != ASSUMPTION_KEYS:
            findings.append(finding("LIT.ASSUMPTION.INVALID", f"$.assumptions[{index}]", "assumption fields are invalid", "repair the exact project-choice record", "critical"))
            continue
        if not _safe_id(assumption.get("assumption_id")) or not all(isinstance(assumption.get(field), str) and assumption[field].strip() for field in ("statement", "impact", "failure_consequence")):
            findings.append(finding("LIT.ASSUMPTION.INVALID", f"$.assumptions[{index}]", "assumption identity, statement, impact, or failure consequence is invalid", "repair the exact project-choice record", "critical"))
        if assumption.get("classification") != "project-choice":
            findings.append(finding("LIT.ASSUMPTION.CLASSIFICATION_INVALID", f"$.assumptions[{index}].classification", "calculation assumption is not explicitly a project choice", "set classification to project-choice", "critical"))
        if assumption.get("owner") not in {"user", "planner"} or assumption.get("status") not in {"unverified", "user-confirmed", "evidence-validated"}:
            findings.append(finding("LIT.ASSUMPTION.INVALID", f"$.assumptions[{index}]", "assumption owner or status is invalid", "repair the exact project-choice record", "critical"))
        evidence_ids = assumption.get("validation_evidence_ids")
        if not isinstance(evidence_ids, list) or len(evidence_ids) != len(set(evidence_ids)) or not all(_safe_id(item) for item in evidence_ids):
            findings.append(finding("LIT.ASSUMPTION.INVALID", f"$.assumptions[{index}].validation_evidence_ids", "assumption evidence IDs are invalid or duplicated", "repair the exact project-choice record", "critical"))
        elif assumption.get("status") == "evidence-validated":
            findings.append(finding("LIT.ASSUMPTION.EXTERNAL_EVIDENCE_REQUIRED", f"$.assumptions[{index}]", "candidate cannot authenticate assumption validation from unresolvable IDs", "supply content-addressed evidence through a production bundle or mark it unverified", "blocking"))
        elif evidence_ids:
            findings.append(finding("LIT.ASSUMPTION.STATUS_CONFLICT", f"$.assumptions[{index}]", "unverified or user-confirmed assumption claims validation evidence", "remove the evidence IDs or use an externally verified workflow", "critical"))
    for index, new_claim in enumerate(new_claims):
        if not isinstance(new_claim, dict) or set(new_claim) != NEW_CLAIM_KEYS:
            findings.append(finding("LIT.NEW_CLAIM.INVALID", f"$.new_claims[{index}]", "new claim fields are invalid", "use the exact hypothesis-to-test shape", "critical"))
            continue
        if (
            not _safe_id(new_claim.get("new_claim_id"))
            or new_claim.get("classification") != "new-claim-proposal"
            or not isinstance(new_claim.get("question"), str)
            or not new_claim["question"].strip()
            or new_claim.get("status") != "proposed"
            or new_claim.get("claim_ceiling") != "no_positive_claim"
        ):
            findings.append(finding("LIT.NEW_CLAIM.OVERCLAIM", f"$.new_claims[{index}]", "new claim must remain a no-positive hypothesis-to-test", "restore a proposed question with no_positive_claim authority", "critical"))
        premise_ids = new_claim.get("premise_inference_ids")
        validation_ids = new_claim.get("validation_step_ids")
        if not isinstance(premise_ids, list) or not premise_ids or len(premise_ids) != len(set(premise_ids)) or any(item not in inference_by_id for item in premise_ids):
            findings.append(finding("LIT.NEW_CLAIM.PREMISE_INVALID", f"$.new_claims[{index}].premise_inference_ids", "new claim lacks resolved inference premises", "bind one or more proposed inference IDs", "critical"))
        if not isinstance(validation_ids, list) or not validation_ids or len(validation_ids) != len(set(validation_ids)) or any(item not in step_by_id for item in validation_ids):
            findings.append(finding("LIT.NEW_CLAIM.VALIDATION_INVALID", f"$.new_claims[{index}].validation_step_ids", "new claim lacks resolved validation steps", "bind one or more proposed step IDs", "critical"))
        else:
            for step_id in validation_ids:
                if new_claim.get("new_claim_id") not in step_by_id[step_id].get("tests_new_claim_ids", []):
                    findings.append(finding("LIT.STEP.NEW_CLAIM_LINEAGE_INVALID", f"$.new_claims[{index}]", "new-claim and validation-step links are not reciprocal", "link the same step and proposal in both records", "critical"))
    observables = set(request.get("target_observables", []))
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or set(step) != STEP_KEYS:
            findings.append(finding("LIT.STEP.INVALID", f"$.calculation_steps[{index}]", "calculation step fields are invalid", "repair the exact proposal-only step", "critical"))
            continue
        if step.get("route_lifecycle") != "active":
            findings.append(finding("LIT.STEP.ROUTE_NOT_ACTIVE", f"$.calculation_steps[{index}].route_lifecycle", "step uses a non-active or unsupported route", "activate the route through governance or replace the step", "blocking"))
        if step.get("status") != "proposed" or step.get("authorization_required") is not True:
            findings.append(finding("LIT.STEP.AUTHORITY_INVALID", f"$.calculation_steps[{index}]", "step claims progress or omits execution authorization", "keep it proposed and require separate authorization", "critical"))
        if not _safe_id(step.get("engine_skill")) or not _safe_id(step.get("task_type")):
            findings.append(finding("LIT.STEP.INVALID", f"$.calculation_steps[{index}]", "step Skill or task identity is invalid", "repair the exact proposal-only step", "critical"))
        if not isinstance(step.get("observable_ids"), list) or not step["observable_ids"] or len(step["observable_ids"]) != len(set(step["observable_ids"])) or any(item not in observables for item in step["observable_ids"]):
            findings.append(finding("LIT.STEP.OBSERVABLE_INVALID", f"$.calculation_steps[{index}].observable_ids", "step observables do not resolve", "bind target observables", "critical"))
        if not isinstance(step.get("tests_inference_ids"), list) or not step["tests_inference_ids"] or len(step["tests_inference_ids"]) != len(set(step["tests_inference_ids"])) or any(item not in inference_by_id for item in step["tests_inference_ids"]):
            findings.append(finding("LIT.STEP.INFERENCE_INVALID", f"$.calculation_steps[{index}].tests_inference_ids", "step does not test a known inference", "bind at least one proposed inference", "critical"))
        if not isinstance(step.get("tests_new_claim_ids"), list) or not step["tests_new_claim_ids"] or len(step["tests_new_claim_ids"]) != len(set(step["tests_new_claim_ids"])) or any(item not in new_claim_by_id for item in step["tests_new_claim_ids"]):
            findings.append(finding("LIT.STEP.NEW_CLAIM_INVALID", f"$.calculation_steps[{index}].tests_new_claim_ids", "step does not test a known new-claim proposal", "bind at least one proposed new-claim ID", "critical"))
        for new_claim_id in step.get("tests_new_claim_ids", []) if isinstance(step.get("tests_new_claim_ids"), list) else []:
            proposal = new_claim_by_id.get(new_claim_id)
            if isinstance(proposal, dict) and step.get("step_id") not in proposal.get("validation_step_ids", []):
                findings.append(finding("LIT.STEP.NEW_CLAIM_LINEAGE_INVALID", f"$.calculation_steps[{index}]", "step and new-claim validation links are not reciprocal", "link the same step and proposal in both records", "critical"))
        if not isinstance(step.get("assumption_ids"), list) or not step["assumption_ids"] or len(step["assumption_ids"]) != len(set(step["assumption_ids"])) or any(item not in assumption_by_id for item in step["assumption_ids"]):
            findings.append(finding("LIT.STEP.ASSUMPTION_INVALID", f"$.calculation_steps[{index}].assumption_ids", "step assumptions do not resolve", "bind explicit calculation assumptions", "critical"))
        if not isinstance(step.get("required_evidence"), list) or not step["required_evidence"] or len(step["required_evidence"]) != len(set(step["required_evidence"])) or not all(isinstance(item, str) and item for item in step["required_evidence"]):
            findings.append(finding("LIT.STEP.EVIDENCE_PROFILE_MISSING", f"$.calculation_steps[{index}].required_evidence", "step lacks future evidence requirements", "name completion, convergence, and validity evidence", "blocking"))
    status = _status(findings)
    return {
        "schema_version": "1.0",
        "contract_name": "literature-evidence-plan-candidate",
        "plan_id": request.get("plan_id", "invalid-plan"),
        "request_id": request.get("request_id"),
        "generated_utc": request.get("generated_utc"),
        "objective": request.get("objective"),
        "target_observables": request.get("target_observables", []),
        "request_sha256": request_sha,
        "retrieval_evidence": sources,
        "source_assertions": [item for item in facts if isinstance(item, dict) and item.get("classification") == "source-assertion"],
        "quoted_numerical_facts": [item for item in facts if isinstance(item, dict) and item.get("classification") == "quoted-numerical-fact"],
        "proposed_inferences": inferences,
        "project_choices": assumptions,
        "new_claim_proposals": new_claims,
        "calculation_steps": steps,
        "status": status,
        "claim_ceiling": "no_positive_claim",
        "gates": [
            {"gate_id": "retrieval-evidence", "status": "pass" if not any(item["code"].startswith("LIT.SOURCE") for item in findings) else "blocked"},
            {"gate_id": "five-way-classification", "status": "pass" if not any(item["code"].startswith(("LIT.FACT", "LIT.INFERENCE", "LIT.ASSUMPTION", "LIT.NEW_CLAIM", "LIT.CLASSIFICATION")) for item in findings) else "blocked"},
            {"gate_id": "calculation-plan", "status": "pass" if not any(item["code"].startswith("LIT.STEP") for item in findings) else "blocked"},
            {"gate_id": "external-source-authority", "status": "requires-external-verification"},
        ],
        "findings": findings,
        "minimum_next_action": "audit-unchanged-literature-plan" if status == "pass" else findings[0]["next_action"],
        "network_access_performed": False,
        "calculation_authorized": False,
        "execution_started": False,
        "external_message_sent": False,
        "limitations": list(request.get("limitations", [])) + [
            "Source authority and extracted content require production bundle resolution.",
            "Source assertions, quoted numerical facts, inferences, project choices, and new-claim proposals remain mechanically distinct; this plan accepts none scientifically.",
        ],
        "producer": {
            "skill_id": "literature-to-dft-plan", "skill_version": TOOL_VERSION,
            "tool_id": "literature-plan-cli-plan", "tool_version": TOOL_VERSION,
            "generated_utc": request.get("generated_utc"),
        },
    }


def audit_plan(plan: dict[str, Any], plan_sha: str) -> dict[str, Any]:
    findings = _privacy(plan)
    if set(plan) != PLAN_KEYS or plan.get("contract_name") != "literature-evidence-plan-candidate" or plan.get("schema_version") != "1.0":
        findings.append(finding("LIT.AUDIT.PLAN_INVALID", "$", "plan fields or identity are invalid", "regenerate the plan", "critical"))
    for key in ("network_access_performed", "calculation_authorized", "execution_started", "external_message_sent"):
        if plan.get(key) is not False:
            findings.append(finding("LIT.AUTHORITY.OVERCLAIM", f"$.{key}", "candidate asserts an external action", "restore no-positive and no-external-action authority flags", "critical"))
    if plan.get("claim_ceiling") != "no_positive_claim":
        findings.append(finding("LIT.AUTHORITY.OVERCLAIM", "$.claim_ceiling", "candidate claim ceiling was raised", "restore no-positive and no-external-action authority flags", "critical"))
    if plan.get("status") != "pass" or plan.get("findings"):
        findings.append(finding("LIT.AUDIT.SOURCE_BLOCKED", "$.status", "source plan is not a clean pass", "resolve the plan findings", "blocking"))
    retrieval = plan.get("retrieval_evidence")
    assertions = plan.get("source_assertions")
    numerical = plan.get("quoted_numerical_facts")
    inferences = plan.get("proposed_inferences")
    choices = plan.get("project_choices")
    proposals = plan.get("new_claim_proposals")
    steps = plan.get("calculation_steps")
    if not isinstance(retrieval, list) or any(not isinstance(item, dict) or set(item) != SOURCE_KEYS for item in retrieval):
        findings.append(finding("LIT.SOURCE.INVALID", "$.retrieval_evidence", "plan source metadata shape is invalid or contains source body fields", "repair the exact source metadata record", "critical"))
    if not isinstance(assertions, list) or any(not isinstance(item, dict) or set(item) != FACT_KEYS or item.get("classification") != "source-assertion" or item.get("text_mode") != "paraphrase" or item.get("quantity") is not None for item in assertions):
        findings.append(finding("LIT.FACT.CLASSIFICATION_INVALID", "$.source_assertions", "source assertion classification is invalid", "repair the explicit fact classification", "critical"))
    if not isinstance(numerical, list) or any(
        not isinstance(item, dict)
        or set(item) != FACT_KEYS
        or item.get("classification") != "quoted-numerical-fact"
        or item.get("text_mode") != "structured-numerical"
        or not isinstance(item.get("quantity"), dict)
        or set(item["quantity"]) != QUANTITY_KEYS
        for item in numerical
    ):
        findings.append(finding("LIT.FACT.NUMERICAL_INVALID", "$.quoted_numerical_facts", "structured numerical fact shape is invalid", "encode a structured value, unit, and reported precision without source prose", "critical"))
    if not isinstance(inferences, list) or any(not isinstance(item, dict) or set(item) != INFERENCE_KEYS or item.get("classification") != "inference" or item.get("status") != "proposed" for item in inferences):
        findings.append(finding("LIT.INFERENCE.INVALID", "$.proposed_inferences", "proposed inference shape is invalid", "repair the exact inference record", "critical"))
    if not isinstance(choices, list) or any(not isinstance(item, dict) or set(item) != ASSUMPTION_KEYS or item.get("classification") != "project-choice" for item in choices):
        findings.append(finding("LIT.ASSUMPTION.INVALID", "$.project_choices", "project-choice shape is invalid", "repair the exact project-choice record", "critical"))
    if not isinstance(proposals, list) or any(not isinstance(item, dict) or set(item) != NEW_CLAIM_KEYS or item.get("classification") != "new-claim-proposal" or item.get("status") != "proposed" or item.get("claim_ceiling") != "no_positive_claim" for item in proposals):
        findings.append(finding("LIT.NEW_CLAIM.OVERCLAIM", "$.new_claim_proposals", "new-claim proposal shape or authority is invalid", "restore a proposed question with no_positive_claim authority", "critical"))
    if not isinstance(steps, list) or any(not isinstance(item, dict) or set(item) != STEP_KEYS or item.get("status") != "proposed" or item.get("authorization_required") is not True for item in steps):
        findings.append(finding("LIT.STEP.INVALID", "$.calculation_steps", "calculation-step shape or authority is invalid", "repair the exact proposal-only step", "critical"))
    source_ids = {item.get("source_id") for item in plan.get("retrieval_evidence", []) if isinstance(item, dict)}
    source_by_id = {item.get("source_id"): item for item in plan.get("retrieval_evidence", []) if isinstance(item, dict)}
    facts = list(plan.get("source_assertions", [])) + list(plan.get("quoted_numerical_facts", [])) if isinstance(plan.get("source_assertions"), list) and isinstance(plan.get("quoted_numerical_facts"), list) else []
    fact_ids = {item.get("fact_id") for item in facts if isinstance(item, dict)}
    inference_ids = {item.get("inference_id") for item in plan.get("proposed_inferences", []) if isinstance(item, dict)}
    assumption_ids = {item.get("assumption_id") for item in plan.get("project_choices", []) if isinstance(item, dict)}
    new_claim_ids = {item.get("new_claim_id") for item in plan.get("new_claim_proposals", []) if isinstance(item, dict)}
    step_by_id = {item.get("step_id"): item for item in plan.get("calculation_steps", []) if isinstance(item, dict)}
    for source in source_by_id.values():
        retrieval_status = source.get("retrieval_status")
        if retrieval_status in {"retrieved", "externally-resolved"} and (not isinstance(source.get("content_sha256"), str) or SHA256.fullmatch(source["content_sha256"]) is None or not _ref(source.get("source_record_ref"))):
            findings.append(finding("LIT.SOURCE.RETRIEVAL_EVIDENCE_MISSING", "$.retrieval_evidence", "resolved source lacks exact retrieval evidence", "provide exact retrieval evidence", "blocking"))
        if source.get("source_kind") == "official-manual" and not isinstance(source.get("version"), str):
            findings.append(finding("LIT.SOURCE.VERSION_MISSING", "$.retrieval_evidence", "version-sensitive source lacks version", "supply a matching manual/software version", "blocking"))
    if any(item.get("source_id") not in source_ids for item in facts if isinstance(item, dict)):
        findings.append(finding("LIT.FACT.SOURCE_UNKNOWN", "$.source_assertions", "fact source does not resolve", "bind an existing source ID", "critical"))
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        source = source_by_id.get(fact.get("source_id"))
        if not isinstance(source, dict) or source.get("retrieval_status") not in {"retrieved", "externally-resolved"}:
            findings.append(finding("LIT.FACT.NOT_EXTRACTABLE", "$.source_assertions", "metadata-only source cannot support a plan fact", "retrieve and hash the exact source before extraction", "blocking"))
        if not isinstance(fact.get("locator"), str) or not fact["locator"].strip():
            findings.append(finding("LIT.FACT.LOCATOR_MISSING", "$.source_assertions", "plan fact lacks bounded locator", "add a page, section, table, figure, or equation locator", "blocking"))
    if any(any(premise not in fact_ids for premise in item.get("premise_fact_ids", [])) for item in plan.get("proposed_inferences", []) if isinstance(item, dict)):
        findings.append(finding("LIT.INFERENCE.PREMISE_INVALID", "$.proposed_inferences", "inference premise does not resolve", "bind one or more extracted fact IDs", "critical"))
    if any(item.get("status") == "evidence-validated" for item in plan.get("project_choices", []) if isinstance(item, dict)):
        findings.append(finding("LIT.ASSUMPTION.EXTERNAL_EVIDENCE_REQUIRED", "$.project_choices", "candidate cannot authenticate a self-validated project choice", "supply content-addressed evidence through a production bundle or mark it unverified", "blocking"))
    for step in plan.get("calculation_steps", []) if isinstance(plan.get("calculation_steps"), list) else []:
        if not isinstance(step, dict) or any(item not in inference_ids for item in step.get("tests_inference_ids", [])) or any(item not in new_claim_ids for item in step.get("tests_new_claim_ids", [])) or any(item not in assumption_ids for item in step.get("assumption_ids", [])):
            findings.append(finding("LIT.STEP.LINEAGE_INVALID", "$.calculation_steps", "step lineage does not resolve", "regenerate the plan", "critical"))
        elif step.get("route_lifecycle") != "active":
            findings.append(finding("LIT.STEP.ROUTE_NOT_ACTIVE", "$.calculation_steps", "plan step route is not active", "activate the route through governance or replace the step", "blocking"))
        if not isinstance(step, dict) or not isinstance(step.get("required_evidence"), list) or not step.get("required_evidence"):
            findings.append(finding("LIT.STEP.EVIDENCE_PROFILE_MISSING", "$.calculation_steps", "plan step lacks future evidence requirements", "name completion, convergence, and validity evidence", "blocking"))
    for proposal in plan.get("new_claim_proposals", []) if isinstance(plan.get("new_claim_proposals"), list) else []:
        if not isinstance(proposal, dict):
            continue
        for step_id in proposal.get("validation_step_ids", []):
            if step_id not in step_by_id or proposal.get("new_claim_id") not in step_by_id[step_id].get("tests_new_claim_ids", []):
                findings.append(finding("LIT.STEP.NEW_CLAIM_LINEAGE_INVALID", "$.new_claim_proposals", "new-claim and step links are not reciprocal", "link the same step and proposal in both records", "critical"))
    status = _status(findings)
    plan_id = plan.get("plan_id") if _safe_id(plan.get("plan_id")) else "invalid-plan"
    return {
        "schema_version": "1.0",
        "contract_name": "literature-plan-candidate-audit",
        "audit_id": f"{plan_id}-audit",
        "subject_ref": {"contract_name": "literature-evidence-plan-candidate", "schema_version": "1.0", "record_id": plan_id, "sha256": plan_sha, "role": "literature-plan"},
        "subject_semantic_sha256": hashlib.sha256(canonical_bytes(plan)).hexdigest(),
        "status": status,
        "render_allowed": status == "pass",
        "claim_ceiling": "no_positive_claim",
        "findings": findings,
        "minimum_next_action": "render-local-literature-package" if status == "pass" else findings[0]["next_action"],
        "network_access_performed": False,
        "calculation_authorized": False,
        "execution_started": False,
        "external_message_sent": False,
        "limitations": ["Audit checks candidate-local classification and lineage only; source authority and scientific adequacy remain external."],
        "producer": {
            "skill_id": "literature-to-dft-plan", "skill_version": TOOL_VERSION,
            "tool_id": "literature-plan-cli-audit", "tool_version": TOOL_VERSION,
            "generated_utc": plan.get("generated_utc"),
        },
    }


def render_package(plan: dict[str, Any], plan_sha: str, audit: dict[str, Any], audit_sha: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    findings = _privacy(plan) + _privacy(audit, "$.audit")
    subject = audit.get("subject_ref")
    expected_audit = audit_plan(plan, plan_sha)
    valid_subject = (
        _ref(subject)
        and subject.get("contract_name") == "literature-evidence-plan-candidate"
        and subject.get("role") == "literature-plan"
        and subject.get("record_id") == plan.get("plan_id")
        and subject.get("sha256") == plan_sha
    )
    if audit.get("contract_name") != "literature-plan-candidate-audit" or audit.get("status") != "pass" or audit.get("render_allowed") is not True or not valid_subject or audit != expected_audit:
        findings.append(finding("LIT.RENDER.AUDIT_MISMATCH", "$.audit", "audit does not bind these exact passing plan bytes", "reaudit the unchanged plan", "blocking"))
    if plan.get("status") != "pass" or any(plan.get(key) is not False for key in ("network_access_performed", "calculation_authorized", "execution_started", "external_message_sent")):
        findings.append(finding("LIT.RENDER.PLAN_BLOCKED", "$.plan", "plan is blocked or exceeds candidate authority", "resolve and reaudit the plan", "blocking"))
    package = {
        "schema_version": "1.0",
        "contract_name": "literature-dft-candidate-package",
        "package_id": f"{plan.get('plan_id', 'invalid-plan')}-package",
        "generated_utc": plan.get("generated_utc"),
        "objective": plan.get("objective"),
        "target_observables": plan.get("target_observables", []),
        "source_refs": [
            {"contract_name": "literature-evidence-plan-candidate", "schema_version": "1.0", "record_id": plan.get("plan_id"), "sha256": plan_sha, "role": "literature-plan"},
            {"contract_name": "literature-plan-candidate-audit", "schema_version": "1.0", "record_id": audit.get("audit_id"), "sha256": audit_sha, "role": "literature-audit"},
        ],
        "retrieval_evidence": plan.get("retrieval_evidence", []),
        "source_assertions": plan.get("source_assertions", []),
        "quoted_numerical_facts": plan.get("quoted_numerical_facts", []),
        "proposed_inferences": plan.get("proposed_inferences", []),
        "project_choices": plan.get("project_choices", []),
        "new_claim_proposals": plan.get("new_claim_proposals", []),
        "calculation_steps": plan.get("calculation_steps", []),
        "claim_ceiling": "no_positive_claim",
        "draft_only": True,
        "network_access_performed": False,
        "calculation_authorized": False,
        "execution_started": False,
        "external_message_sent": False,
        "required_next_stages": [
            "resolve real source records and licenses through production bundle semantics",
            "review facts, inferences, assumptions, observables, tolerances, and routes with domain experts",
            "create a separate calculation plan and obtain execution authorization before any run",
        ],
        "limitations": plan.get("limitations", []),
        "producer": {
            "skill_id": "literature-to-dft-plan", "skill_version": TOOL_VERSION,
            "tool_id": "literature-plan-cli-render-package", "tool_version": TOOL_VERSION,
            "generated_utc": plan.get("generated_utc"),
        },
    }
    return package, findings


def summary(command: str, status: str, output: Path | None, digest: str | None, findings: list[dict[str, str]]) -> dict[str, Any]:
    success_actions = {
        "plan": "audit-unchanged-literature-plan",
        "audit": "render-local-literature-package",
        "render-package": "request-source-resolution-and-human-scientific-review",
    }
    return {
        "command": command, "status": status,
        "output_label": output.name if output is not None else None,
        "output_sha256": digest,
        "finding_codes": sorted({item["code"] for item in findings}),
        "first_decisive_finding": findings[0]["code"] if findings else None,
        "minimum_next_action": findings[0]["next_action"] if findings else success_actions[command],
        "maximum_claim": "no_positive_claim",
        "maximum_action": {"plan": "local-draft-plan", "audit": "local-audit", "render-package": "local-json-draft"}[command],
        "tool_invocation_mode": "execute-local-candidate-write" if output is not None and digest is not None else "execute-local-validation-only",
        "local_write_performed": output is not None and digest is not None,
        "external_execution_performed": False,
        "positive_claim_made": False,
        "send": False, "execute": False, "publish": False,
        "promotion_authorized": False, "network_access_performed": False,
        "calculation_authorized": False, "execution_started": False,
        "external_message_sent": False,
    }


def _print(value: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan_parser = commands.add_parser("plan")
    plan_parser.add_argument("--request", type=Path, required=True)
    plan_parser.add_argument("--out", type=Path, required=True)
    audit_parser = commands.add_parser("audit")
    audit_parser.add_argument("--plan", type=Path, required=True)
    audit_parser.add_argument("--out", type=Path, required=True)
    render_parser = commands.add_parser("render-package")
    render_parser.add_argument("--plan", type=Path, required=True)
    render_parser.add_argument("--audit", type=Path, required=True)
    render_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            guard_output(args.out, [args.request])
            request, request_sha = strict_load(args.request)
            artifact = build_plan(request, request_sha)
            findings = artifact["findings"]
        elif args.command == "audit":
            guard_output(args.out, [args.plan])
            plan, plan_sha = strict_load(args.plan)
            artifact = audit_plan(plan, plan_sha)
            findings = artifact["findings"]
        else:
            guard_output(args.out, [args.plan, args.audit])
            plan, plan_sha = strict_load(args.plan)
            audit, audit_sha = strict_load(args.audit)
            artifact, findings = render_package(plan, plan_sha, audit, audit_sha)
            if findings:
                status = _status(findings)
                _print(summary(args.command, status, None, None, findings))
                return _exit(status)
        status = artifact.get("status", "pass")
        if status == "fail":
            _print(summary(args.command, status, None, None, findings))
            return 2
        digest = write_new(args.out, artifact)
        _print(summary(args.command, status, args.out, digest, findings))
        return _exit(status)
    except InputFailure as exc:
        findings = [finding("LIT.JSON.INVALID", "$", str(exc), "repair the first bounded input or output error", "critical")]
        _print(summary(args.command, "fail", None, None, findings))
        return 2
    except (OSError, ValueError, TypeError, KeyError):
        findings = [finding("LIT.INTERNAL.ERROR", "$", "bounded deterministic operation failed", "inspect inputs and rerun", "critical")]
        _print(summary(args.command, "fail", None, None, findings))
        return 4


def main(argv: list[str] | None = None) -> int:
    _reset_io_bindings()
    try:
        return _main(argv)
    finally:
        _reset_io_bindings()


if __name__ == "__main__":
    raise SystemExit(main())
