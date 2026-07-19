#!/usr/bin/env python3
"""Offline fail-closed planner, auditor, and JSON package renderer for DFT reports."""

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
PRIVATE_PATH = re.compile(
    r"(?i)(?:/Users/|/home/|/scratch/|/private/|/tmp/|/Volumes/|[A-Za-z]:[\\/]|\\\\)"
)
SECRET = re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|password|secret|bearer)\s*[:=]")
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
CLAIM_ORDER = {
    "no_positive_claim": 0,
    "documented_behavior_only": 1,
    "input_gates_only": 2,
    "technical_run_gates_only": 3,
    "numerical_candidate_only": 4,
    "eligible_for_expert_review": 5,
}

REQUEST_KEYS = {
    "schema_version", "contract_name", "request_id", "report_id", "title",
    "language", "generated_utc", "claim_map_ref", "selected_claim_ids",
    "sections", "citation_locators", "artifact_refs", "campaign_refs", "limitations",
}
PLAN_KEYS = {
    "schema_version", "contract_name", "plan_id", "request_id", "generated_utc",
    "title", "language", "source_bindings", "sections", "claims", "evidence",
    "citations", "artifact_refs", "campaign_refs", "scientific_acceptance",
    "decision_lineage", "status", "claim_ceiling", "tool_claim_ceiling", "gates",
    "findings", "minimum_next_action", "source_claim_ceiling", "publication_ready",
    "external_message_sent", "limitations", "producer",
}
CLAIM_MAP_KEYS = {
    "schema_version", "contract_name", "map_id", "subject_records", "status",
    "claim_ceiling", "scientific_acceptance", "scientific_decision_ref", "evidence",
    "gates", "claims", "limitations", "producer",
}
EVIDENCE_KEYS = {"evidence_id", "kind", "record_ref", "file_ref", "status", "limitations"}
CLAIM_KEYS = {"claim_id", "statement", "claim_level", "status", "evidence_ids", "gate_ids", "blocker_codes"}
GATE_KEYS = {
    "check_id", "status", "decisive", "finding_codes", "evidence_refs",
    "validated_by", "validated_utc", "limitations",
}
FILE_REF_KEYS = {
    "role", "label", "media_type", "format", "format_version", "availability",
    "sha256", "bytes", "sensitivity", "redistribution",
}
PLAN_CLAIM_KEYS = {
    "claim_id", "statement", "source_statement_sha256", "claim_level",
    "status", "evidence_ids", "gate_ids",
}
PLAN_CITATION_KEYS = {
    "evidence_id", "source_ref", "source_label", "locator",
    "authority_authentication",
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
            candidate = f".{absolute.name}.reporting-{secrets.token_hex(12)}.tmp"
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
    return {
        "code": code,
        "location": location,
        "message": message,
        "next_action": next_action,
        "severity": severity,
    }


def _safe_id(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 128 and SAFE_ID.fullmatch(value) is not None


def _ref(value: Any, *, contract: str | None = None, role: str | None = None) -> bool:
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
        and (contract is None or value.get("contract_name") == contract)
        and (role is None or value.get("role") == role)
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
        result.append(finding(
            "REPORT.PRIVACY.UNSAFE_TEXT", location, "privacy-sensitive text is forbidden",
            "replace the value with an anonymized label", "critical",
        ))
    return result


def _status(findings: list[dict[str, str]]) -> str:
    if any(item["severity"] == "critical" for item in findings):
        return "fail"
    return "blocked" if findings else "pass"


def _exit(status: str) -> int:
    return {"pass": 0, "fail": 2, "blocked": 3}[status]


def _unique_ids(items: Any, field: str) -> bool:
    if not isinstance(items, list):
        return False
    values = [item.get(field) for item in items if isinstance(item, dict)]
    return len(values) == len(items) and all(_safe_id(item) for item in values) and len(values) == len(set(values))


def _present_evidence(item: dict[str, Any]) -> bool:
    if set(item) != EVIDENCE_KEYS or item.get("status") != "present":
        return False
    if not _safe_id(item.get("evidence_id")) or not isinstance(item.get("limitations"), list):
        return False
    if item.get("kind") == "record":
        return _ref(item.get("record_ref")) and item.get("file_ref") is None
    file_ref = item.get("file_ref")
    return (
        item.get("kind") == "file"
        and item.get("record_ref") is None
        and isinstance(file_ref, dict)
        and set(file_ref) == FILE_REF_KEYS
        and file_ref.get("availability") == "present"
        and isinstance(file_ref.get("sha256"), str)
        and SHA256.fullmatch(file_ref["sha256"]) is not None
        and isinstance(file_ref.get("bytes"), int)
        and file_ref["bytes"] >= 0
    )


def _valid_gate(item: Any) -> bool:
    actor = item.get("validated_by") if isinstance(item, dict) else None
    return (
        isinstance(item, dict)
        and set(item) == GATE_KEYS
        and _safe_id(item.get("check_id"))
        and item.get("status") in {"pass", "warn", "fail", "blocked", "not-assessed", "not-applicable"}
        and isinstance(item.get("decisive"), bool)
        and isinstance(item.get("finding_codes"), list)
        and all(_safe_id(value) for value in item["finding_codes"])
        and len(item["finding_codes"]) == len(set(item["finding_codes"]))
        and isinstance(item.get("evidence_refs"), list)
        and all(_ref(value) for value in item["evidence_refs"])
        and isinstance(actor, dict)
        and set(actor) == {"actor_type", "actor_id", "role"}
        and actor.get("actor_type") in {"deterministic-tool", "agent", "human"}
        and _safe_id(actor.get("actor_id"))
        and _safe_id(actor.get("role"))
        and isinstance(item.get("validated_utc"), str)
        and UTC.fullmatch(item["validated_utc"]) is not None
        and isinstance(item.get("limitations"), list)
        and all(isinstance(value, str) and value for value in item["limitations"])
    )


def _valid_claim(item: Any) -> bool:
    if not isinstance(item, dict) or set(item) != CLAIM_KEYS:
        return False
    lists = (item.get("evidence_ids"), item.get("gate_ids"), item.get("blocker_codes"))
    return (
        _safe_id(item.get("claim_id"))
        and isinstance(item.get("statement"), str)
        and bool(item["statement"].strip())
        and item.get("claim_level") in CLAIM_ORDER
        and item.get("status") in {"supported", "blocked", "not-assessed", "rejected"}
        and all(isinstance(values, list) and all(_safe_id(value) for value in values) and len(values) == len(set(values)) for values in lists)
    )


def validate_request(value: dict[str, Any], claim_map: dict[str, Any], map_sha: str) -> list[dict[str, str]]:
    findings = _privacy(value) + _privacy(claim_map, "$.claim_map")
    if set(value) != REQUEST_KEYS or value.get("schema_version") != "1.0" or value.get("contract_name") != "dft-report-request":
        findings.append(finding(
            "REPORT.CONTRACT.INVALID", "$", "report request fields or identity are invalid",
            "repair the exact candidate request fields", "critical",
        ))
        return findings
    if not all(_safe_id(value.get(name)) for name in ("request_id", "report_id")):
        findings.append(finding("REPORT.IDENTITY.INVALID", "$.request_id", "request or report ID is invalid", "bind stable IDs and exact referenced identities", "critical"))
    if not isinstance(value.get("title"), str) or not value["title"].strip() or value.get("language") not in {"en", "zh", "bilingual"}:
        findings.append(finding("REPORT.CONTRACT.INVALID", "$.title", "title or language is invalid", "repair the exact candidate request fields", "critical"))
    elif value.get("language") == "bilingual":
        findings.append(finding("REPORT.BILINGUAL.NOT_VALIDATED", "$.language", "bilingual claim-preserving rendering is not validated in this candidate", "use one source language or wait for a reviewed bilingual adapter", "blocking"))
    if not isinstance(value.get("generated_utc"), str) or UTC.fullmatch(value["generated_utc"]) is None:
        findings.append(finding("REPORT.CONTRACT.INVALID", "$.generated_utc", "generated_utc is invalid", "repair the exact candidate request fields", "critical"))
    expected_ref = value.get("claim_map_ref")
    if not _ref(expected_ref, contract="claim-evidence-map", role="claim-map"):
        findings.append(finding("REPORT.IDENTITY.INVALID", "$.claim_map_ref", "claim-map reference is invalid", "bind stable IDs and exact referenced identities", "critical"))
    elif expected_ref["sha256"] != map_sha:
        findings.append(finding("REPORT.HASH.MISMATCH", "$.claim_map_ref.sha256", "claim-map raw-byte hash does not match", "recompute the ref without reserializing the source", "critical"))
    if set(claim_map) != CLAIM_MAP_KEYS or claim_map.get("contract_name") != "claim-evidence-map" or claim_map.get("schema_version") != "1.0":
        findings.append(finding("REPORT.CLAIM_MAP.INVALID", "$.claim_map", "source is not claim-evidence-map@1.0", "repair the canonical claim map", "critical"))
        return findings
    if isinstance(expected_ref, dict) and claim_map.get("map_id") != expected_ref.get("record_id"):
        findings.append(finding("REPORT.IDENTITY.INVALID", "$.claim_map.map_id", "claim-map ID differs from its ref", "bind stable IDs and exact referenced identities", "critical"))
    if claim_map.get("status") != "complete":
        findings.append(finding("REPORT.CLAIM_MAP.NOT_COMPLETE", "$.claim_map.status", "source claim map is partial or blocked", "complete the claim map before reporting", "blocking"))
    if claim_map.get("claim_ceiling") not in CLAIM_ORDER or claim_map.get("scientific_acceptance") not in {"not_assessed", "requires_human_review", "accepted", "rejected"}:
        findings.append(finding("REPORT.CLAIM_MAP.INVALID", "$.claim_map", "claim ceiling or scientific acceptance is invalid", "repair the canonical claim map", "critical"))
    selected = value.get("selected_claim_ids")
    if not isinstance(selected, list) or not selected or not all(_safe_id(item) for item in selected) or len(selected) != len(set(selected)):
        findings.append(finding("REPORT.CLAIM.SELECTION_INVALID", "$.selected_claim_ids", "selected claim IDs are empty, invalid, or duplicated", "select unique claim IDs", "critical"))
    for name, contract, role in (
        ("artifact_refs", "artifact-manifest", "artifact"),
        ("campaign_refs", "campaign-record", "campaign"),
    ):
        refs = value.get(name)
        if not isinstance(refs, list) or not all(_ref(item, contract=contract, role=role) for item in refs):
            findings.append(finding("REPORT.REFERENCE.INVALID", f"$.{name}", f"{name} contains an invalid ref", "supply exact content-addressed refs", "critical"))
    if not _unique_ids(value.get("sections"), "section_id"):
        findings.append(finding("REPORT.SECTION.INVALID", "$.sections", "sections need unique safe IDs", "repair the exact section records", "critical"))
    if not _unique_ids(value.get("citation_locators"), "evidence_id"):
        findings.append(finding("REPORT.CITATION.INVALID", "$.citation_locators", "citation locators need unique evidence IDs", "repair the exact citation records", "critical"))
    if not isinstance(value.get("limitations"), list) or not all(isinstance(item, str) and item for item in value["limitations"]):
        findings.append(finding("REPORT.CONTRACT.INVALID", "$.limitations", "limitations are invalid", "repair the exact candidate request fields", "critical"))
    return findings


def build_plan(request: dict[str, Any], request_sha: str, claim_map: dict[str, Any], map_sha: str) -> dict[str, Any]:
    findings = validate_request(request, claim_map, map_sha)
    evidence_items = claim_map.get("evidence") if isinstance(claim_map.get("evidence"), list) else []
    gates = claim_map.get("gates") if isinstance(claim_map.get("gates"), list) else []
    claims = claim_map.get("claims") if isinstance(claim_map.get("claims"), list) else []
    if not isinstance(claim_map.get("evidence"), list):
        findings.append(finding("REPORT.EVIDENCE.SHAPE_INVALID", "$.claim_map.evidence", "claim-map evidence is not a list", "repair evidence using the exact canonical shape", "critical"))
    if not isinstance(claim_map.get("gates"), list):
        findings.append(finding("REPORT.GATE.SHAPE_INVALID", "$.claim_map.gates", "claim-map gates are not a list", "repair the canonical gate record", "critical"))
    if not isinstance(claim_map.get("claims"), list):
        findings.append(finding("REPORT.CLAIM.SHAPE_INVALID", "$.claim_map.claims", "claim-map claims are not a list", "repair the canonical claim record", "critical"))
    evidence_by_id = {item.get("evidence_id"): item for item in evidence_items if isinstance(item, dict) and _safe_id(item.get("evidence_id"))}
    gate_by_id = {item.get("check_id"): item for item in gates if isinstance(item, dict) and _safe_id(item.get("check_id"))}
    claim_by_id = {item.get("claim_id"): item for item in claims if isinstance(item, dict) and _safe_id(item.get("claim_id"))}
    if len(evidence_by_id) != len(evidence_items):
        findings.append(finding("REPORT.EVIDENCE.IDENTITY_INVALID", "$.claim_map.evidence", "evidence IDs are invalid or duplicated", "repair the source claim map", "critical"))
    if any(not _present_evidence(item) and isinstance(item, dict) and item.get("status") == "present" for item in evidence_items):
        findings.append(finding("REPORT.EVIDENCE.SHAPE_INVALID", "$.claim_map.evidence", "present evidence has an invalid or incomplete shape", "repair evidence using the exact canonical shape", "critical"))
    if len(gate_by_id) != len(gates):
        findings.append(finding("REPORT.GATE.IDENTITY_INVALID", "$.claim_map.gates", "gate IDs are invalid or duplicated", "repair the source claim map", "critical"))
    if any(not _valid_gate(item) for item in gates):
        findings.append(finding("REPORT.GATE.SHAPE_INVALID", "$.claim_map.gates", "gate record is incomplete or malformed", "repair the canonical gate record", "critical"))
    if len(claim_by_id) != len(claims):
        findings.append(finding("REPORT.CLAIM.IDENTITY_INVALID", "$.claim_map.claims", "claim IDs are invalid or duplicated", "repair the source claim map", "critical"))
    if any(not _valid_claim(item) for item in claims):
        findings.append(finding("REPORT.CLAIM.SHAPE_INVALID", "$.claim_map.claims", "claim record is incomplete or malformed", "repair the canonical claim record", "critical"))
    selected: list[dict[str, Any]] = []
    used_evidence: set[str] = set()
    locator_items = request.get("citation_locators") if isinstance(request.get("citation_locators"), list) else []
    locators = {item.get("evidence_id"): item for item in locator_items if isinstance(item, dict)}
    for claim_id in request.get("selected_claim_ids", []) if isinstance(request.get("selected_claim_ids"), list) else []:
        claim = claim_by_id.get(claim_id)
        if not isinstance(claim, dict):
            findings.append(finding("REPORT.CLAIM.UNKNOWN", f"$.selected_claim_ids.{claim_id}", "selected claim does not resolve", "select an existing claim", "blocking"))
            continue
        evidence_ids = claim.get("evidence_ids")
        gate_ids = claim.get("gate_ids")
        if claim.get("status") != "supported" or not isinstance(evidence_ids, list) or not evidence_ids or not isinstance(gate_ids, list) or not gate_ids:
            findings.append(finding("REPORT.CLAIM.UNSUPPORTED", f"$.claims.{claim_id}", "claim is not evidence-supported", "resolve the claim-map blocker before reporting", "blocking"))
        for evidence_id in evidence_ids if isinstance(evidence_ids, list) else []:
            evidence = evidence_by_id.get(evidence_id)
            if not isinstance(evidence, dict) or not _present_evidence(evidence):
                findings.append(finding("REPORT.EVIDENCE.NOT_PRESENT", f"$.claims.{claim_id}.evidence_ids", "claim evidence is absent or unhashed", "provide present content-addressed evidence", "blocking"))
                continue
            used_evidence.add(evidence_id)
            record_ref = evidence.get("record_ref")
            if isinstance(record_ref, dict) and record_ref.get("contract_name") == "official-source-record":
                locator = locators.get(evidence_id)
                if not isinstance(locator, dict) or set(locator) != {"evidence_id", "source_label", "locator"} or not all(isinstance(locator.get(key), str) and locator[key] for key in ("source_label", "locator")):
                    findings.append(finding("REPORT.CITATION.LOCATOR_MISSING", f"$.claims.{claim_id}", "official source evidence lacks a bounded locator", "supply a source label and page, section, table, or figure locator", "blocking"))
        for gate_id in gate_ids if isinstance(gate_ids, list) else []:
            gate = gate_by_id.get(gate_id)
            if not isinstance(gate, dict) or gate.get("status") not in {"pass", "not-applicable"}:
                findings.append(finding("REPORT.GATE.NOT_PASSING", f"$.claims.{claim_id}.gate_ids", "claim gate is missing or non-passing", "resolve the decisive gate", "blocking"))
        level = claim.get("claim_level")
        if level not in CLAIM_ORDER or CLAIM_ORDER[level] > CLAIM_ORDER.get(claim_map.get("claim_ceiling"), -1):
            findings.append(finding("REPORT.CLAIM.CEILING_EXCEEDED", f"$.claims.{claim_id}.claim_level", "claim exceeds the source map ceiling", "lower or revalidate the claim", "critical"))
        elif level != "no_positive_claim":
            findings.append(finding("REPORT.EXTERNAL_BUNDLE.REQUIRED", f"$.claims.{claim_id}", "positive claim cannot be rendered from a self-declared upstream map", "validate the positive claim through production bundle semantics before rendering", "blocking"))
        statement = claim.get("statement") if level == "no_positive_claim" else None
        statement_hash = hashlib.sha256(str(claim.get("statement", "")).encode("utf-8")).hexdigest()
        selected.append({
            "claim_id": claim_id,
            "statement": statement,
            "source_statement_sha256": statement_hash,
            "claim_level": level,
            "status": claim.get("status"),
            "evidence_ids": evidence_ids if isinstance(evidence_ids, list) else [],
            "gate_ids": gate_ids if isinstance(gate_ids, list) else [],
        })
    sections = request.get("sections") if isinstance(request.get("sections"), list) else []
    covered: set[str] = set()
    valid_selected = {item["claim_id"] for item in selected}
    artifact_ids = {item.get("record_id") for item in request.get("artifact_refs", []) if isinstance(item, dict)}
    for index, section in enumerate(sections):
        if not isinstance(section, dict) or set(section) != {"section_id", "title", "claim_ids", "artifact_record_ids"}:
            findings.append(finding("REPORT.SECTION.INVALID", f"$.sections[{index}]", "section fields are invalid", "repair the exact section records", "critical"))
            continue
        claim_ids = section.get("claim_ids")
        referenced_artifacts = section.get("artifact_record_ids")
        if not isinstance(claim_ids, list) or any(item not in valid_selected for item in claim_ids):
            findings.append(finding("REPORT.SECTION.UNKNOWN_CLAIM", f"$.sections[{index}].claim_ids", "section refers to an unselected claim", "select or remove the claim", "critical"))
        else:
            covered.update(claim_ids)
        if not isinstance(referenced_artifacts, list) or any(item not in artifact_ids for item in referenced_artifacts):
            findings.append(finding("REPORT.SECTION.UNKNOWN_ARTIFACT", f"$.sections[{index}].artifact_record_ids", "section refers to an unknown artifact", "bind the artifact ref or remove it", "critical"))
    for claim_id in sorted(valid_selected - covered):
        findings.append(finding("REPORT.SECTION.CLAIM_UNMAPPED", f"$.claims.{claim_id}", "selected claim is not mapped to a section", "map the claim to a report section", "blocking"))
    acceptance = claim_map.get("scientific_acceptance")
    decision_ref = claim_map.get("scientific_decision_ref")
    if acceptance in {"accepted", "rejected"} and not _ref(decision_ref, contract="decision-record", role="scientific-acceptance"):
        findings.append(finding("REPORT.DECISION.LINEAGE_MISSING", "$.claim_map.scientific_decision_ref", "acceptance lacks a decision ref", "supply the post-decision claim map", "critical"))
    status = _status(findings)
    source_ceiling = claim_map.get("claim_ceiling") if claim_map.get("claim_ceiling") in CLAIM_ORDER else "no_positive_claim"
    citations = [
        {
            "evidence_id": evidence_id,
            "source_ref": evidence_by_id[evidence_id]["record_ref"],
            "source_label": locators[evidence_id]["source_label"],
            "locator": locators[evidence_id]["locator"],
            "authority_authentication": "requires-external-bundle-verification",
        }
        for evidence_id in sorted(used_evidence)
        if isinstance(evidence_by_id[evidence_id].get("record_ref"), dict)
        and evidence_by_id[evidence_id]["record_ref"].get("contract_name") == "official-source-record"
        and evidence_id in locators
    ]
    return {
        "schema_version": "1.0",
        "contract_name": "scientific-report-candidate-plan",
        "plan_id": f"{request.get('report_id', 'invalid-report')}-plan",
        "request_id": request.get("request_id"),
        "generated_utc": request.get("generated_utc"),
        "title": request.get("title"),
        "language": request.get("language"),
        "source_bindings": {
            "request_sha256": request_sha,
            "claim_map_ref": request.get("claim_map_ref"),
            "claim_map_sha256": map_sha,
        },
        "sections": sections,
        "claims": selected,
        "evidence": [evidence_by_id[item] for item in sorted(used_evidence) if item in evidence_by_id],
        "citations": citations,
        "artifact_refs": request.get("artifact_refs", []),
        "campaign_refs": request.get("campaign_refs", []),
        "scientific_acceptance": acceptance if acceptance in {"not_assessed", "requires_human_review", "accepted", "rejected"} else "not_assessed",
        "decision_lineage": {
            "scientific_decision_ref": decision_ref if isinstance(decision_ref, dict) else None,
            "authentication": "requires-external-bundle-verification",
        },
        "status": status,
        "claim_ceiling": "no_positive_claim",
        "tool_claim_ceiling": "no_positive_claim",
        "gates": [
            {"gate_id": "claim-support", "status": "pass" if not any(item["code"].startswith(("REPORT.CLAIM", "REPORT.EVIDENCE", "REPORT.GATE")) for item in findings) else "blocked"},
            {"gate_id": "citation-lineage", "status": "pass" if not any(item["code"].startswith("REPORT.CITATION") for item in findings) else "blocked"},
            {"gate_id": "section-coverage", "status": "pass" if not any(item["code"].startswith("REPORT.SECTION") for item in findings) else "blocked"},
            {"gate_id": "external-trust", "status": "requires-external-verification"},
        ],
        "findings": findings,
        "minimum_next_action": "audit-unchanged-report-plan" if status == "pass" else findings[0]["next_action"],
        "source_claim_ceiling": source_ceiling,
        "publication_ready": False,
        "external_message_sent": False,
        "limitations": list(request.get("limitations", [])) + [
            "Candidate checks do not authenticate source authority or a human decision.",
            "The package is a local draft and requires production bundle validation and human release.",
        ],
        "producer": {
            "skill_id": "dft-reporting",
            "skill_version": TOOL_VERSION,
            "tool_id": "reporting-cli-plan",
            "tool_version": TOOL_VERSION,
            "generated_utc": request.get("generated_utc"),
        },
    }


def audit_plan(plan: dict[str, Any], plan_sha: str) -> dict[str, Any]:
    findings = _privacy(plan)
    if set(plan) != PLAN_KEYS or plan.get("contract_name") != "scientific-report-candidate-plan" or plan.get("schema_version") != "1.0":
        findings.append(finding("REPORT.AUDIT.PLAN_INVALID", "$", "plan fields or identity are invalid", "regenerate the plan", "critical"))
    if plan.get("publication_ready") is not False or plan.get("external_message_sent") is not False or plan.get("tool_claim_ceiling") != "no_positive_claim":
        findings.append(finding("REPORT.AUTHORITY.OVERCLAIM", "$", "plan exceeds candidate authority", "restore draft-only authority flags", "critical"))
    if plan.get("source_claim_ceiling") not in CLAIM_ORDER:
        findings.append(finding("REPORT.CLAIM.CEILING_EXCEEDED", "$.source_claim_ceiling", "source claim ceiling is invalid", "lower or revalidate the claim", "critical"))
    if plan.get("claim_ceiling") != "no_positive_claim" or any(item.get("claim_level") != "no_positive_claim" for item in plan.get("claims", []) if isinstance(item, dict)):
        findings.append(finding("REPORT.EXTERNAL_BUNDLE.REQUIRED", "$.claims", "positive claim remains in a candidate-local render plan", "validate the positive claim through production bundle semantics before rendering", "blocking"))
    if plan.get("status") != "pass" or plan.get("findings"):
        findings.append(finding("REPORT.AUDIT.SOURCE_BLOCKED", "$.status", "source plan is not a clean pass", "resolve plan findings before rendering", "blocking"))
    claims = plan.get("claims") if isinstance(plan.get("claims"), list) else []
    claim_ids = [item.get("claim_id") for item in claims if isinstance(item, dict)]
    if not claims or len(claim_ids) != len(set(claim_ids)):
        findings.append(finding("REPORT.AUDIT.CLAIMS_INVALID", "$.claims", "claims are empty or duplicated", "regenerate from a valid claim map", "critical"))
    for index, claim in enumerate(claims):
        if (
            not isinstance(claim, dict)
            or set(claim) != PLAN_CLAIM_KEYS
            or claim.get("status") != "supported"
            or claim.get("claim_level") != "no_positive_claim"
            or not isinstance(claim.get("statement"), str)
            or not claim["statement"].strip()
            or not isinstance(claim.get("source_statement_sha256"), str)
            or SHA256.fullmatch(claim["source_statement_sha256"]) is None
            or not claim.get("evidence_ids")
            or not claim.get("gate_ids")
        ):
            findings.append(finding("REPORT.CLAIM.UNSUPPORTED", f"$.claims[{index}]", "render candidate is unsupported", "resolve the claim-map blocker before reporting", "blocking"))
    plan_evidence = plan.get("evidence")
    if not isinstance(plan_evidence, list) or any(not isinstance(item, dict) or set(item) != EVIDENCE_KEYS or not _present_evidence(item) for item in plan_evidence):
        findings.append(finding("REPORT.EVIDENCE.SHAPE_INVALID", "$.evidence", "plan evidence shape is invalid", "repair evidence using the exact canonical shape", "critical"))
    plan_citations = plan.get("citations")
    if not isinstance(plan_citations, list) or any(not isinstance(item, dict) or set(item) != PLAN_CITATION_KEYS for item in plan_citations):
        findings.append(finding("REPORT.CITATION.INVALID", "$.citations", "plan citation shape is invalid", "repair the exact citation records", "critical"))
    covered = {
        claim_id
        for section in plan.get("sections", []) if isinstance(section, dict)
        for claim_id in section.get("claim_ids", []) if isinstance(claim_id, str)
    }
    if set(claim_ids) - covered:
        findings.append(finding("REPORT.SECTION.CLAIM_UNMAPPED", "$.sections", "not all claims are section-bound", "map the claim to a report section", "blocking"))
    status = _status(findings)
    plan_id = plan.get("plan_id") if _safe_id(plan.get("plan_id")) else "invalid-plan"
    return {
        "schema_version": "1.0",
        "contract_name": "dft-report-candidate-audit",
        "audit_id": f"{plan_id}-audit",
        "subject_ref": {
            "contract_name": "scientific-report-candidate-plan",
            "schema_version": "1.0",
            "record_id": plan_id,
            "sha256": plan_sha,
            "role": "report-plan",
        },
        "subject_semantic_sha256": hashlib.sha256(canonical_bytes(plan)).hexdigest(),
        "status": status,
        "render_allowed": status == "pass",
        "claim_ceiling": "no_positive_claim",
        "findings": findings,
        "minimum_next_action": "render-local-draft-package" if status == "pass" else findings[0]["next_action"],
        "publication_ready": False,
        "external_message_sent": False,
        "limitations": [
            "Audit proves only candidate-local internal consistency.",
            "External bundle semantics, source authority, human decision authenticity, and release remain unresolved.",
        ],
        "producer": {
            "skill_id": "dft-reporting",
            "skill_version": TOOL_VERSION,
            "tool_id": "reporting-cli-audit",
            "tool_version": TOOL_VERSION,
            "generated_utc": plan.get("generated_utc"),
        },
    }


def render_package(plan: dict[str, Any], plan_sha: str, audit: dict[str, Any], audit_sha: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    findings = _privacy(plan) + _privacy(audit, "$.audit")
    subject = audit.get("subject_ref")
    expected_audit = audit_plan(plan, plan_sha)
    if (
        audit.get("contract_name") != "dft-report-candidate-audit"
        or audit.get("status") != "pass"
        or audit.get("render_allowed") is not True
        or not _ref(subject, contract="scientific-report-candidate-plan", role="report-plan")
        or subject.get("record_id") != plan.get("plan_id")
        or subject.get("sha256") != plan_sha
        or audit != expected_audit
    ):
        findings.append(finding("REPORT.RENDER.AUDIT_MISMATCH", "$.audit", "audit does not authorize rendering of these exact plan bytes", "rerun audit for the unchanged plan", "blocking"))
    if plan.get("status") != "pass" or plan.get("publication_ready") is not False:
        findings.append(finding("REPORT.RENDER.PLAN_BLOCKED", "$.plan", "plan is blocked or overclaims publication state", "resolve and reaudit the plan", "blocking"))
    claims = {item.get("claim_id"): item for item in plan.get("claims", []) if isinstance(item, dict)}
    citations = {item.get("evidence_id"): item for item in plan.get("citations", []) if isinstance(item, dict)}
    sections: list[dict[str, Any]] = []
    for section in plan.get("sections", []) if isinstance(plan.get("sections"), list) else []:
        if not isinstance(section, dict):
            continue
        entries = []
        for claim_id in section.get("claim_ids", []):
            claim = claims.get(claim_id)
            if not isinstance(claim, dict):
                continue
            entries.append({
                "claim_id": claim_id,
                "draft_statement": claim.get("statement"),
                "claim_level": claim.get("claim_level"),
                "evidence_ids": claim.get("evidence_ids", []),
                "gate_ids": claim.get("gate_ids", []),
                "citations": [citations[item] for item in claim.get("evidence_ids", []) if item in citations],
            })
        sections.append({
            "section_id": section.get("section_id"),
            "title": section.get("title"),
            "entries": entries,
            "artifact_record_ids": section.get("artifact_record_ids", []),
        })
    package = {
        "schema_version": "1.0",
        "contract_name": "scientific-report-candidate-package",
        "package_id": f"{plan.get('plan_id', 'invalid-plan')}-package",
        "generated_utc": plan.get("generated_utc"),
        "title": plan.get("title"),
        "language": plan.get("language"),
        "source_refs": [
            {"contract_name": "scientific-report-candidate-plan", "schema_version": "1.0", "record_id": plan.get("plan_id"), "sha256": plan_sha, "role": "report-plan"},
            {"contract_name": "dft-report-candidate-audit", "schema_version": "1.0", "record_id": audit.get("audit_id"), "sha256": audit_sha, "role": "report-audit"},
        ],
        "sections": sections,
        "artifact_refs": plan.get("artifact_refs", []),
        "campaign_refs": plan.get("campaign_refs", []),
        "scientific_acceptance": plan.get("scientific_acceptance"),
        "acceptance_authentication": "requires-external-bundle-verification",
        "claim_ceiling": plan.get("claim_ceiling"),
        "tool_claim_ceiling": "no_positive_claim",
        "draft_only": True,
        "publication_ready": False,
        "external_message_sent": False,
        "required_release_steps": [
            "run production contract and bundle semantic validation",
            "authenticate any human scientific decision through an external trust resolver",
            "complete human editorial, privacy, license, and release review",
        ],
        "limitations": plan.get("limitations", []),
        "producer": {
            "skill_id": "dft-reporting",
            "skill_version": TOOL_VERSION,
            "tool_id": "reporting-cli-render-package",
            "tool_version": TOOL_VERSION,
            "generated_utc": plan.get("generated_utc"),
        },
    }
    return package, findings


def summary(command: str, status: str, output: Path | None, sha256: str | None, findings: list[dict[str, str]]) -> dict[str, Any]:
    success_actions = {
        "plan": "audit-unchanged-report-plan",
        "audit": "render-local-draft-package",
        "render-package": "request-production-bundle-validation-and-human-release",
    }
    return {
        "command": command,
        "status": status,
        "output_label": output.name if output is not None else None,
        "output_sha256": sha256,
        "finding_codes": sorted({item["code"] for item in findings}),
        "first_decisive_finding": findings[0]["code"] if findings else None,
        "minimum_next_action": findings[0]["next_action"] if findings else success_actions[command],
        "maximum_claim": "no_positive_claim",
        "maximum_action": {"plan": "local-draft-plan", "audit": "local-audit", "render-package": "local-json-draft"}[command],
        "tool_invocation_mode": "execute-local-candidate-write" if output is not None and sha256 is not None else "execute-local-validation-only",
        "local_write_performed": output is not None and sha256 is not None,
        "external_execution_performed": False,
        "positive_claim_made": False,
        "send": False,
        "execute": False,
        "publish": False,
        "execution_started": False,
        "promotion_authorized": False,
        "publication_ready": False,
        "external_message_sent": False,
    }


def _print(value: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan_parser = commands.add_parser("plan")
    plan_parser.add_argument("--request", type=Path, required=True)
    plan_parser.add_argument("--claim-map", type=Path, required=True)
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
            guard_output(args.out, [args.request, args.claim_map])
            request, request_sha = strict_load(args.request)
            claim_map, map_sha = strict_load(args.claim_map)
            artifact = build_plan(request, request_sha, claim_map, map_sha)
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
                _print(summary(args.command, _status(findings), None, None, findings))
                return _exit(_status(findings))
        status = artifact.get("status", "pass")
        if status == "fail":
            _print(summary(args.command, status, None, None, findings))
            return 2
        output_sha = write_new(args.out, artifact)
        _print(summary(args.command, status, args.out, output_sha, findings))
        return _exit(status)
    except InputFailure as exc:
        findings = [finding("REPORT.JSON.INVALID", "$", str(exc), "repair the first bounded input or output error", "critical")]
        _print(summary(args.command, "fail", None, None, findings))
        return 2
    except (OSError, ValueError, TypeError, KeyError):
        findings = [finding("REPORT.INTERNAL.ERROR", "$", "bounded deterministic operation failed", "inspect inputs and rerun", "critical")]
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
