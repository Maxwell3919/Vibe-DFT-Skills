#!/usr/bin/env python3
"""Deterministic documentary inventory for LASP artifacts; no LASP syntax or execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import sys
from typing import Any


TOOL_VERSION = "0.3.0"
SCHEMA_VERSION = "1.0"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_TEXT_BYTES = 16 * 1024 * 1024
OPERATING_VERSION = "3.7.3"
TASKS = {"nve", "nvt", "npt", "global-structure-search", "reaction-search"}
REQUIRED_PLAN = {
    "case_id", "protocol_id", "lasp_version", "task", "objective", "claim_target",
    "artifact_class", "units", "boundary", "ensemble", "timestep", "model",
    "restart", "seed", "equilibration", "production", "observables", "documents",
    "authorization",
}
_SNAPSHOT_CACHE: dict[str, bytes] = {}
_DIRECTORY_ANCHORS: dict[str, tuple[int, os.stat_result]] = {}
REPORT_BASE_KEYS = {
    "schema_version", "tool", "engine", "command", "decision",
    "candidate_lifecycle", "claim_ceiling", "future_gate_ceiling",
    "promotion_ready", "promotion_authorized", "execution_authorized",
    "report_authenticity", "maturity", "findings", "evidence", "metrics",
    "limitations", "report_fingerprint",
}
REPORT_COMMAND_KEYS = {
    "plan": {"plan_request_sha256", "plan"},
    "audit-input": {"upstream", "input_inventory"},
    "audit-output": {"upstream", "output_inventory"},
    "audit-trajectory": {"upstream", "trajectory_inventory"},
}


class GuardFailure(Exception):
    def __init__(self, code: str, message: str, *, incomplete: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.incomplete = incomplete


def reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value!r}")


def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _file_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        stat.S_IFMT(value.st_mode), value.st_dev, value.st_ino, value.st_nlink,
        value.st_size, value.st_mtime_ns, value.st_ctime_ns,
    )


def _directory_identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _reset_snapshot_cache() -> None:
    _SNAPSHOT_CACHE.clear()
    for descriptor, _metadata in _DIRECTORY_ANCHORS.values():
        try:
            os.close(descriptor)
        except OSError:
            pass
    _DIRECTORY_ANCHORS.clear()


def _stable_directory(path: Path) -> tuple[int, list[tuple[int, str, int, os.stat_result, Path]], Path]:
    """Open every directory component without following links and retain the anchors."""

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory_flag is None or nonblock is None:
        raise GuardFailure("LASP.IO.NOFOLLOW_UNAVAILABLE", "The host lacks no-follow, directory, or nonblocking path support.", incomplete=True)
    absolute = Path(os.path.abspath(os.fspath(path)))
    root = Path(absolute.anchor)
    flags = os.O_RDONLY | directory_flag | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)
    try:
        root_path_metadata = root.lstat()
        if stat.S_ISLNK(root_path_metadata.st_mode) or not stat.S_ISDIR(root_path_metadata.st_mode):
            raise GuardFailure("LASP.IO.UNSAFE_FILE", "A path root is not a real directory.")
        root_key = os.fspath(root)
        cached_root = _DIRECTORY_ANCHORS.get(root_key)
        if cached_root is None:
            root_fd = os.open(root, flags)
            root_metadata = os.fstat(root_fd)
            _DIRECTORY_ANCHORS[root_key] = (root_fd, root_metadata)
        else:
            root_fd, root_metadata = cached_root
        if (
            not stat.S_ISDIR(root_metadata.st_mode)
            or not stat.S_ISDIR(os.fstat(root_fd).st_mode)
            or _directory_identity(root_path_metadata) != _directory_identity(root_metadata)
            or _directory_identity(os.fstat(root_fd)) != _directory_identity(root_metadata)
        ):
            raise GuardFailure("LASP.IO.CHANGED_DURING_READ", "A path root changed identity.")
        current_fd = root_fd
        current_path = root
        edges: list[tuple[int, str, int, os.stat_result, Path]] = []
        for component in absolute.parts[1:]:
            anchored = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(anchored.st_mode) or not stat.S_ISDIR(anchored.st_mode):
                raise GuardFailure("LASP.IO.UNSAFE_FILE", "An intermediate path component is not a real directory.")
            current_path = current_path / component
            key = os.fspath(current_path)
            cached = _DIRECTORY_ANCHORS.get(key)
            if cached is None:
                child_fd = os.open(component, flags, dir_fd=current_fd)
                child_metadata = os.fstat(child_fd)
                _DIRECTORY_ANCHORS[key] = (child_fd, child_metadata)
            else:
                child_fd, child_metadata = cached
            opened = os.fstat(child_fd)
            if (
                not stat.S_ISDIR(child_metadata.st_mode)
                or not stat.S_ISDIR(opened.st_mode)
                or _directory_identity(anchored) != _directory_identity(child_metadata)
                or _directory_identity(opened) != _directory_identity(child_metadata)
            ):
                raise GuardFailure("LASP.IO.CHANGED_DURING_READ", "An intermediate directory changed identity.")
            edges.append((current_fd, component, child_fd, child_metadata, current_path))
            current_fd = child_fd
        return current_fd, edges, absolute
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("LASP.IO.UNSAFE_FILE", "A directory path could not be opened safely.") from exc


def _verify_directory_edges(directory: Path, edges: list[tuple[int, str, int, os.stat_result, Path]]) -> None:
    root = Path(directory.anchor)
    try:
        root_fd, root_metadata = _DIRECTORY_ANCHORS[os.fspath(root)]
        lexical_root = root.lstat()
        if (
            not stat.S_ISDIR(lexical_root.st_mode)
            or _directory_identity(lexical_root) != _directory_identity(root_metadata)
            or _directory_identity(os.fstat(root_fd)) != _directory_identity(root_metadata)
        ):
            raise GuardFailure("LASP.IO.CHANGED_DURING_READ", "A path root changed identity.")
        for parent_fd, component, child_fd, child_metadata, lexical_path in edges:
            anchored = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            opened = os.fstat(child_fd)
            lexical = lexical_path.lstat()
            if (
                not stat.S_ISDIR(anchored.st_mode)
                or not stat.S_ISDIR(opened.st_mode)
                or not stat.S_ISDIR(lexical.st_mode)
                or _directory_identity(anchored) != _directory_identity(child_metadata)
                or _directory_identity(opened) != _directory_identity(child_metadata)
                or _directory_identity(lexical) != _directory_identity(child_metadata)
            ):
                raise GuardFailure("LASP.IO.CHANGED_DURING_READ", "An intermediate directory changed during access.")
    except GuardFailure:
        raise
    except (KeyError, OSError) as exc:
        raise GuardFailure("LASP.IO.CHANGED_DURING_READ", "A directory anchor changed during access.") from exc


def read_bytes(path: Path, limit: int) -> bytes:
    key = os.path.abspath(os.fspath(path))
    cached = _SNAPSHOT_CACHE.get(key)
    if cached is not None:
        if not cached or len(cached) > limit:
            raise GuardFailure("LASP.IO.SIZE", "A required artifact is empty or exceeds the bounded size.")
        return cached
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        raise GuardFailure("LASP.IO.NOFOLLOW_UNAVAILABLE", "The platform cannot establish a no-follow nonblocking input snapshot.", incomplete=True)
    absolute = Path(key)
    if not absolute.name or absolute.name in {".", ".."}:
        raise GuardFailure("LASP.IO.UNSAFE_FILE", "An input must name a regular file.")
    parent_fd, edges, _parent = _stable_directory(absolute.parent)
    try:
        anchored_before = os.stat(absolute.name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(anchored_before.st_mode) or anchored_before.st_nlink != 1:
            raise GuardFailure("LASP.IO.UNSAFE_FILE", "Inputs must be regular single-link non-symlink files.")
        descriptor = os.open(
            absolute.name,
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("LASP.IO.UNSAFE_FILE", "A required artifact is unavailable or not a regular non-symlink file.") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or _file_identity(before) != _file_identity(anchored_before):
            raise GuardFailure("LASP.IO.UNSAFE_FILE", "Inputs must be regular single-link non-symlink files.")
        if before.st_size <= 0 or before.st_size > limit:
            raise GuardFailure("LASP.IO.SIZE", "A required artifact is empty or exceeds the bounded size.")
        blocks: list[bytes] = []
        total = 0
        while True:
            block = os.read(descriptor, min(65536, limit + 1 - total))
            if not block:
                break
            blocks.append(block)
            total += len(block)
            if total > limit:
                raise GuardFailure("LASP.IO.SIZE", "A required artifact exceeds the bounded size.")
        after = os.fstat(descriptor)
        anchored_after = os.stat(absolute.name, dir_fd=parent_fd, follow_symlinks=False)
        lexical_after = absolute.lstat()
        _verify_directory_edges(absolute.parent, edges)
    except OSError as exc:
        raise GuardFailure("LASP.IO.READ", "A required artifact could not be read safely.") from exc
    finally:
        os.close(descriptor)
    data = b"".join(blocks)
    identity = _file_identity(before)
    if (
        identity != _file_identity(after)
        or identity != _file_identity(anchored_after)
        or identity != _file_identity(lexical_after)
        or not stat.S_ISREG(anchored_after.st_mode)
        or not stat.S_ISREG(lexical_after.st_mode)
        or anchored_after.st_nlink != 1
        or lexical_after.st_nlink != 1
        or len(data) != before.st_size
    ):
        raise GuardFailure("LASP.IO.CHANGED_DURING_READ", "An input changed identity or content while being read.")
    _SNAPSHOT_CACHE[key] = data
    return data


def read_text(path: Path) -> str:
    data = read_bytes(path, MAX_TEXT_BYTES)
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise GuardFailure("LASP.TEXT.NON_ASCII", "The documentary inventory accepts ASCII text only.") from exc
    if "\x00" in text:
        raise GuardFailure("LASP.TEXT.NUL", "NUL bytes are not accepted.")
    return text


def decode_json_object(data: bytes) -> dict[str, Any]:
    if data.startswith(b"\xef\xbb\xbf"):
        raise GuardFailure("LASP.JSON.INVALID", "JSON must be UTF-8 without BOM.")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=object_pairs, parse_constant=reject_constant)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise GuardFailure("LASP.JSON.INVALID", "JSON is malformed or ambiguous.") from exc
    if not isinstance(value, dict):
        raise GuardFailure("LASP.JSON.INVALID", "JSON root must be an object.")
    return value


def load_json(path: Path) -> dict[str, Any]:
    return decode_json_object(read_bytes(path, MAX_JSON_BYTES))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(read_bytes(path, MAX_TEXT_BYTES))


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(raw.encode("utf-8"))


def evidence(path: Path, role: str) -> dict[str, Any]:
    return {"role": role, "label": path.name, "sha256": sha256_file(path), "bytes": len(read_bytes(path, MAX_TEXT_BYTES))}


def finding(code: str, gate: str, message: str, next_action: str, *, kind: str = "fail") -> dict[str, str]:
    return {"code": code, "gate": gate, "severity": "critical", "kind": kind, "message": message, "next_action": next_action}


def decision(findings: list[dict[str, str]]) -> str:
    if any(item["kind"] == "fail" for item in findings):
        return "blocked"
    if findings:
        return "incomplete"
    return "pass"


def make_report(command: str, findings: list[dict[str, str]], artifacts: list[dict[str, Any]], metrics: dict[str, Any], *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    local = decision(findings)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "lasp_evidence_guard", "version": TOOL_VERSION},
        "engine": "lasp",
        "command": command,
        "decision": local,
        "candidate_lifecycle": "development",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": "no_positive_claim",
        "promotion_ready": False,
        "promotion_authorized": False,
        "execution_authorized": False,
        "report_authenticity": "unsigned-candidate-output",
        "maturity": "documentary-inventory-only",
        "findings": findings,
        "evidence": sorted(artifacts, key=lambda item: (item["role"], item["label"])),
        "metrics": metrics,
        "limitations": [
            "No version-matched authoritative LASP input/output/restart manual is implemented.",
            "The tool inventories bounded artifacts and never invokes LASP.",
            "Generic extxyz integrity is independent of LASP provenance or completion.",
            "No positive technical or scientific LASP claim can be automated at this maturity.",
            "This unsigned candidate report needs an external trusted manifest or signature before it can serve as authenticated evidence.",
        ],
    }
    if extra:
        report.update(extra)
    report["report_fingerprint"] = canonical_hash({key: value for key, value in report.items() if key != "report_fingerprint"})
    return report


def ensure_output_distinct(out: Path | None, inputs: list[Path]) -> None:
    if out is None:
        return
    output_resolved = out.resolve(strict=False)
    for input_path in inputs:
        if output_resolved == input_path.resolve(strict=False):
            raise GuardFailure("LASP.IO.OUTPUT_ALIASES_INPUT", "The report output aliases an input artifact.")
        try:
            output_stat = out.lstat()
            input_stat = input_path.lstat()
        except OSError:
            continue
        if (output_stat.st_dev, output_stat.st_ino) == (input_stat.st_dev, input_stat.st_ino):
            raise GuardFailure("LASP.IO.OUTPUT_ALIASES_INPUT", "The report output shares identity with an input artifact.")


def _binding_identity(value: os.stat_result) -> tuple[int, int, int, int]:
    return stat.S_IFMT(value.st_mode), value.st_dev, value.st_ino, value.st_size


def _fd_payload_matches(descriptor: int, payload: bytes) -> bool:
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != len(payload):
        return False
    digest = hashlib.sha256()
    offset = 0
    while offset < len(payload):
        block = os.pread(descriptor, min(65536, len(payload) - offset), offset)
        if not block:
            return False
        digest.update(block)
        offset += len(block)
    return offset == len(payload) and digest.digest() == hashlib.sha256(payload).digest()


def _staging_matches(directory_fd: int, name: str, descriptor: int, payload: bytes, expected_links: int) -> bool:
    try:
        by_name = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        by_fd = os.fstat(descriptor)
    except OSError:
        return False
    return (
        stat.S_ISREG(by_name.st_mode)
        and stat.S_ISREG(by_fd.st_mode)
        and by_name.st_nlink == expected_links
        and by_fd.st_nlink == expected_links
        and _binding_identity(by_name) == _binding_identity(by_fd)
        and _fd_payload_matches(descriptor, payload)
    )


def _publish_hard_link(directory_fd: int, staging_name: str, target_name: str, staging_fd: int, payload: bytes) -> os.stat_result:
    """Atomically create target if absent after revalidating the still-open staging file."""

    if not _staging_matches(directory_fd, staging_name, staging_fd, payload, 1):
        raise GuardFailure("LASP.IO.WRITE", "The staged report path changed before publication.")
    published = False
    published_snapshot: os.stat_result | None = None
    try:
        try:
            os.link(
                staging_name,
                target_name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise GuardFailure("LASP.IO.OVERWRITE", "The report target appeared during atomic publication.") from exc
        published = True
        published_snapshot = os.stat(target_name, dir_fd=directory_fd, follow_symlinks=False)
        staged = os.stat(staging_name, dir_fd=directory_fd, follow_symlinks=False)
        opened = os.fstat(staging_fd)
        if (
            not _staging_matches(directory_fd, staging_name, staging_fd, payload, 2)
            or published_snapshot.st_nlink != 2
            or _binding_identity(published_snapshot) != _binding_identity(staged)
            or _binding_identity(published_snapshot) != _binding_identity(opened)
        ):
            raise GuardFailure("LASP.IO.WRITE", "Atomic publication did not bind the retained staging descriptor.")
        return published_snapshot
    except (GuardFailure, OSError) as exc:
        if published:
            try:
                current = os.stat(target_name, dir_fd=directory_fd, follow_symlinks=False)
                opened = os.fstat(staging_fd)
                if (
                    (published_snapshot is not None and _file_identity(current) != _file_identity(published_snapshot))
                    or _binding_identity(current) != _binding_identity(opened)
                    or not _fd_payload_matches(staging_fd, payload)
                ):
                    raise OSError("published target identity changed before rollback")
                os.unlink(target_name, dir_fd=directory_fd)
                os.fsync(directory_fd)
            except OSError as rollback_error:
                raise GuardFailure("LASP.IO.WRITE", "Atomic publication rollback failed; output state is indeterminate.") from rollback_error
        if isinstance(exc, GuardFailure):
            raise
        raise GuardFailure("LASP.IO.WRITE", "Atomic publication could not be verified.") from exc


def _atomic_write_new(path: Path, payload: bytes) -> None:
    absolute = Path(os.path.abspath(os.fspath(path)))
    if not absolute.name or absolute.name in {".", ".."}:
        raise GuardFailure("LASP.IO.WRITE", "The output must name a new regular file.")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None or not all(function in os.supports_dir_fd for function in (os.open, os.stat, os.link, os.unlink)):
        raise GuardFailure("LASP.IO.NOFOLLOW_UNAVAILABLE", "The host lacks descriptor-relative atomic publish support.", incomplete=True)
    directory_fd, edges, _parent = _stable_directory(absolute.parent)
    temporary_fd = -1
    temporary_name: str | None = None
    linked_target: os.stat_result | None = None
    installed = False
    try:
        try:
            os.stat(absolute.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise GuardFailure("LASP.IO.OVERWRITE", "The report path already exists.")
        for _attempt in range(32):
            candidate = f".{absolute.name}.candidate-{secrets.token_hex(12)}.tmp"
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
        if temporary_fd < 0 or temporary_name is None:
            raise GuardFailure("LASP.IO.WRITE", "A private staging file could not be created.")
        offset = 0
        while offset < len(payload):
            written = os.write(temporary_fd, payload[offset:])
            if written <= 0:
                raise OSError("short report write")
            offset += written
        os.fsync(temporary_fd)
        if not _staging_matches(directory_fd, temporary_name, temporary_fd, payload, 1):
            raise GuardFailure("LASP.IO.WRITE", "The staged report identity or content is invalid.")
        _verify_directory_edges(absolute.parent, edges)
        try:
            os.stat(absolute.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise GuardFailure("LASP.IO.OVERWRITE", "The report target appeared during staging.")
        linked_target = _publish_hard_link(directory_fd, temporary_name, absolute.name, temporary_fd, payload)
        os.unlink(temporary_name, dir_fd=directory_fd)
        temporary_name = None
        final = os.stat(absolute.name, dir_fd=directory_fd, follow_symlinks=False)
        linked_target = final
        opened = os.fstat(temporary_fd)
        if (
            final.st_nlink != 1
            or opened.st_nlink != 1
            or _binding_identity(final) != _binding_identity(opened)
            or not _fd_payload_matches(temporary_fd, payload)
        ):
            raise GuardFailure("LASP.IO.WRITE", "The published report changed after staging cleanup.")
        _verify_directory_edges(absolute.parent, edges)
        os.fsync(directory_fd)
        installed = True
        linked_target = None
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("LASP.IO.WRITE", "The report could not be published atomically without overwrite.") from exc
    finally:
        if linked_target is not None and not installed and temporary_fd >= 0:
            try:
                current = os.stat(absolute.name, dir_fd=directory_fd, follow_symlinks=False)
                opened = os.fstat(temporary_fd)
                if _binding_identity(current) == _binding_identity(opened) and _fd_payload_matches(temporary_fd, payload):
                    os.unlink(absolute.name, dir_fd=directory_fd)
                    os.fsync(directory_fd)
            except OSError:
                pass
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except OSError:
                pass
        if temporary_fd >= 0:
            try:
                os.close(temporary_fd)
            except OSError:
                pass


def emit(report: dict[str, Any], out: Path | None) -> int:
    rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if out is None:
        sys.stdout.write(rendered)
    else:
        try:
            _atomic_write_new(out, rendered.encode("utf-8"))
        except GuardFailure as exc:
            blocked = make_report(report["command"], [finding(exc.code, "side_effect_boundary", exc.message, "Choose a distinct new report path.", kind="incomplete" if exc.incomplete else "fail")], [], {})
            sys.stdout.write(json.dumps(blocked, indent=2, sort_keys=True) + "\n")
            return 3 if exc.incomplete else 2
    return {"pass": 0, "blocked": 2, "incomplete": 3}[report["decision"]]


def safe_id(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value))


def positive(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) > 0


def validate_plan(request: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    missing = sorted(REQUIRED_PLAN - set(request))
    if missing:
        findings.append(finding("LASP.PLAN.MISSING_FIELD", "claim_definition", "Required fields are missing: " + ", ".join(missing), "Supply every field without inventing LASP defaults."))
        return findings
    if not safe_id(request["case_id"]) or not safe_id(request["protocol_id"]):
        findings.append(finding("LASP.PLAN.INVALID_ID", "privacy", "Case and protocol IDs must be anonymous safe identifiers.", "Use alphanumeric IDs."))
    if request["lasp_version"] != OPERATING_VERSION:
        findings.append(finding("LASP.PLAN.VERSION_CONTEXT", "documentation", "Only LASP 3.7.3 has the reviewed public distribution context.", "Obtain version-specific primary documentation.", kind="incomplete"))
    if request["task"] not in TASKS:
        findings.append(finding("LASP.PLAN.TASK", "claim_definition", "Task is outside the literature-context vocabulary.", "Keep it out of scope until primary evidence exists.", kind="incomplete"))
    if not isinstance(request["objective"], str) or not request["objective"].strip() or not isinstance(request["claim_target"], str) or not request["claim_target"].strip():
        findings.append(finding("LASP.PLAN.CLAIM", "claim_definition", "Objective and bounded claim target must be nonempty.", "State them explicitly."))
    if request["artifact_class"] not in {"synthetic", "user-supplied"}:
        findings.append(finding("LASP.PLAN.ARTIFACT_CLASS", "claim_definition", "Artifact class must be synthetic or user-supplied.", "Declare evidence origin."))
    units = request["units"]
    if not isinstance(units, dict) or units.get("declared_by_project") is not True or not isinstance(units.get("map"), dict) or not units["map"] or not all(isinstance(key, str) and key and isinstance(value, str) and value for key, value in units["map"].items()):
        findings.append(finding("LASP.UNITS.PROJECT_DECLARATION", "units", "Intended units must be explicit project declarations.", "Do not attribute them to LASP until mapped to a manual."))
    if not isinstance(request["boundary"], list) or len(request["boundary"]) != 3 or not all(isinstance(value, bool) for value in request["boundary"]):
        findings.append(finding("LASP.BOUNDARY.PROJECT_DECLARATION", "boundary", "Boundary intent must contain three booleans.", "Declare all axes."))
    if not isinstance(request["ensemble"], str) or not request["ensemble"]:
        findings.append(finding("LASP.ENSEMBLE.PROJECT_DECLARATION", "ensemble", "Ensemble intent is missing.", "Declare intended ensemble without claiming keyword mapping."))
    timestep = request["timestep"]
    if not isinstance(timestep, dict) or not positive(timestep.get("value")) or not isinstance(timestep.get("unit"), str) or not timestep["unit"] or timestep.get("declared_by_project") is not True:
        findings.append(finding("LASP.PLAN.TIMESTEP", "numerical_discretization", "Time step must be a positive project-declared value and unit.", "Declare intent without asserting LASP syntax."))
    model = request["model"]
    if not isinstance(model, dict) or not all(isinstance(model.get(key), str) and model[key].strip() for key in ("identity", "source_url", "license_status")):
        findings.append(finding("LASP.MODEL.PROVENANCE", "model_provenance", "Model identity/source/license status is incomplete.", "Provide independent provenance."))
    elif model["license_status"] != "verified":
        findings.append(finding("LASP.LICENSE.MODEL_UNRESOLVED", "model_provenance", "Model license is unresolved.", "Resolve model rights before use."))
    restart = request["restart"]
    if not isinstance(restart, dict) or restart.get("mode") not in {"new", "opaque-state-continuation"}:
        findings.append(finding("LASP.RESTART.LINEAGE", "restart_lineage", "Restart mode is missing or invalid.", "Declare new or opaque-state-continuation."))
    elif restart["mode"] == "opaque-state-continuation":
        if not safe_id(restart.get("parent_run_id")) or not isinstance(restart.get("state_sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", restart["state_sha256"]) or restart.get("exact_continuation_claim") is not False:
            findings.append(finding("LASP.RESTART.LINEAGE", "restart_lineage", "Opaque continuation lacks parent/hash or honest exactness limit.", "Bind state and set exact_continuation_claim=false."))
    seed = request["seed"]
    if not isinstance(seed, dict) or seed.get("mode") not in {"explicit-project-intent", "opaque-state"}:
        findings.append(finding("LASP.SEED.PROJECT_DECLARATION", "initial_state", "Seed intent is missing or invalid.", "Record explicit intent or opaque state."))
    elif seed["mode"] == "explicit-project-intent" and (not isinstance(seed.get("value"), int) or isinstance(seed.get("value"), bool) or seed["value"] <= 0):
        findings.append(finding("LASP.SEED.PROJECT_DECLARATION", "initial_state", "Explicit seed intent must be a positive integer.", "Record the intended value."))
    for phase_name in ("equilibration", "production"):
        phase = request[phase_name]
        if not isinstance(phase, dict) or not isinstance(phase.get("steps"), int) or isinstance(phase.get("steps"), bool) or phase["steps"] < 0 or not isinstance(phase.get("acceptance_checks"), list) or not phase["acceptance_checks"]:
            findings.append(finding("LASP.PLAN.PHASE", "equilibration_production", f"{phase_name} must declare intended steps and checks.", "Predeclare phase intent."))
    observables = request["observables"]
    if not isinstance(observables, list) or not observables:
        findings.append(finding("LASP.PLAN.OBSERVABLE", "statistics", "At least one intended observable is required.", "Declare estimator and uncertainty policy."))
    else:
        names: set[str] = set()
        for item in observables:
            valid = isinstance(item, dict) and safe_id(item.get("name")) and item["name"] not in names and isinstance(item.get("unit"), str) and item["unit"] and item.get("estimator") == "mean" and item.get("uncertainty_method") == "block-mean" and isinstance(item.get("minimum_effective_samples"), int) and item["minimum_effective_samples"] >= 2 and positive(item.get("max_standard_error"))
            if not valid:
                findings.append(finding("LASP.PLAN.OBSERVABLE", "statistics", "Observable intent is duplicate or incomplete.", "Use unique explicit estimator/uncertainty definitions."))
                break
            names.add(item["name"])
    documents = request["documents"]
    unavailable_flags = ("version_matched_manual_available", "input_reference_available", "output_reference_available", "restart_reference_available", "license_terms_available")
    public_flags = ("manual_advertised_by_official_page", "public_environment_baseline_available", "public_executable_entry_available")
    if (
        not isinstance(documents, dict)
        or not all(documents.get(flag) is False for flag in unavailable_flags)
        or not all(documents.get(flag) is True for flag in public_flags)
        or documents.get("discovery_url") != "http://www.lasphub.com/#/lasp/download"
    ):
        findings.append(finding("LASP.DOCS.UNREVIEWED_CLAIM", "documentation", "Document availability claims exceed this candidate's reviewed evidence.", "Review and implement authorized primary documents first.", kind="incomplete"))
    auth = request["authorization"]
    if not isinstance(auth, dict) or auth.get("execute_external_software") is not False:
        findings.append(finding("LASP.EXECUTION.NOT_AUTHORIZED", "execution_boundary", "This candidate accepts only explicit no-execution plans.", "Do not run or probe LASP."))
    return findings


def command_plan(path: Path) -> dict[str, Any]:
    request = load_json(path)
    findings = validate_plan(request)
    return make_report("plan", findings, [evidence(path, "plan-request")], {"documented_operational_interfaces": 1, "known_evidence_gaps": 9}, extra={"plan_request_sha256": sha256_file(path), "plan": request})


def load_upstream_report(
    path: Path, command: str, allowed_decisions: set[str]
) -> tuple[dict[str, Any], str]:
    """Load one verified byte snapshot; candidate fingerprints are not trust roots."""

    raw = read_bytes(path, MAX_JSON_BYTES)
    report = decode_json_object(raw)
    if command not in REPORT_COMMAND_KEYS or set(report) != REPORT_BASE_KEYS | REPORT_COMMAND_KEYS[command]:
        raise GuardFailure("LASP.UPSTREAM.SHAPE", f"The upstream {command} report does not have the complete canonical shape.")
    invariant = (
        report.get("schema_version") == SCHEMA_VERSION
        and report.get("tool") == {"name": "lasp_evidence_guard", "version": TOOL_VERSION}
        and report.get("engine") == "lasp"
        and report.get("command") == command
        and report.get("decision") in allowed_decisions
        and report.get("candidate_lifecycle") == "development"
        and report.get("claim_ceiling") == "no_positive_claim"
        and report.get("future_gate_ceiling") == "no_positive_claim"
        and report.get("promotion_ready") is False
        and report.get("promotion_authorized") is False
        and report.get("execution_authorized") is False
        and report.get("report_authenticity") == "unsigned-candidate-output"
        and report.get("maturity") == "documentary-inventory-only"
        and isinstance(report.get("findings"), list)
        and isinstance(report.get("evidence"), list)
        and isinstance(report.get("metrics"), dict)
        and isinstance(report.get("limitations"), list)
        and report["limitations"]
        and all(isinstance(item, str) and item for item in report["limitations"])
    )
    if not invariant:
        raise GuardFailure("LASP.UPSTREAM.INVARIANT", f"The upstream {command} report violates development unsigned candidate invariants.")
    finding_keys = {"code", "gate", "severity", "kind", "message", "next_action"}
    if any(
        not isinstance(item, dict)
        or set(item) != finding_keys
        or item.get("kind") not in {"fail", "incomplete"}
        or not all(isinstance(item.get(key), str) and item[key] for key in finding_keys)
        for item in report["findings"]
    ) or decision(report["findings"]) != report["decision"]:
        raise GuardFailure("LASP.UPSTREAM.SHAPE", f"The upstream {command} findings are not canonical.")
    evidence_keys = {"role", "label", "sha256", "bytes"}
    if any(
        not isinstance(item, dict)
        or set(item) != evidence_keys
        or not isinstance(item.get("role"), str)
        or not item["role"]
        or not isinstance(item.get("label"), str)
        or not item["label"]
        or not isinstance(item.get("sha256"), str)
        or re.fullmatch(r"[a-f0-9]{64}", item["sha256"]) is None
        or not isinstance(item.get("bytes"), int)
        or isinstance(item.get("bytes"), bool)
        or item["bytes"] <= 0
        for item in report["evidence"]
    ) or report["evidence"] != sorted(report["evidence"], key=lambda item: (item["role"], item["label"])):
        raise GuardFailure("LASP.UPSTREAM.SHAPE", f"The upstream {command} evidence inventory is not canonical.")
    fingerprint = report.get("report_fingerprint")
    expected_fingerprint = canonical_hash({key: value for key, value in report.items() if key != "report_fingerprint"})
    if not isinstance(fingerprint, str) or re.fullmatch(r"[a-f0-9]{64}", fingerprint) is None or fingerprint != expected_fingerprint:
        raise GuardFailure("LASP.UPSTREAM.TAMPERED", f"The upstream {command} self-fingerprint is invalid.")
    if command == "plan":
        if not isinstance(report.get("plan"), dict) or re.fullmatch(r"[a-f0-9]{64}", report.get("plan_request_sha256", "")) is None:
            raise GuardFailure("LASP.UPSTREAM.SHAPE", "The upstream plan payload is incomplete.")
    else:
        payload_key = {"audit-input": "input_inventory", "audit-output": "output_inventory", "audit-trajectory": "trajectory_inventory"}[command]
        upstream_keys = {
            "audit-input": {"plan_raw_sha256", "plan_fingerprint"},
            "audit-output": {"plan_raw_sha256", "input_raw_sha256", "plan_fingerprint", "input_fingerprint"},
            "audit-trajectory": {
                "plan_raw_sha256", "input_raw_sha256", "output_raw_sha256",
                "plan_fingerprint", "input_fingerprint", "output_fingerprint",
            },
        }[command]
        upstream = report.get("upstream")
        if (
            not isinstance(report.get(payload_key), dict)
            or not isinstance(upstream, dict)
            or set(upstream) != upstream_keys
            or any(not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None for value in upstream.values())
        ):
            raise GuardFailure("LASP.UPSTREAM.SHAPE", f"The upstream {command} lineage payload is incomplete.")
    return report, sha256_bytes(raw)


def privacy_findings(text: str, role: str) -> list[dict[str, str]]:
    patterns = [r"/Users/", r"/home/", r"(?i)password\s*=", r"(?i)api[_-]?key\s*=", r"(?i)token\s*="]
    if any(re.search(pattern, text) for pattern in patterns):
        return [finding("LASP.PRIVACY.SENSITIVE_MARKER", "privacy", f"{role} contains a private-path or credential-like marker.", "Remove sensitive content; retain only safe hashes and labels.")]
    return []


def check_provenance(provenance: dict[str, Any], paths: list[Path]) -> list[dict[str, str]]:
    entries = provenance.get("artifacts")
    if not isinstance(entries, list):
        return [finding("LASP.MODEL.PROVENANCE", "model_provenance", "Provenance artifacts are missing.", "Declare exact opaque closure.")]
    by_label: dict[str, dict[str, Any]] = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("label"), str) or item["label"] in by_label:
            return [finding("LASP.MODEL.PROVENANCE", "model_provenance", "Provenance entries are malformed or duplicate.", "Use one record per basename.")]
        by_label[item["label"]] = item
    findings: list[dict[str, str]] = []
    for path in paths:
        item = by_label.get(path.name)
        if not item or item.get("sha256") != sha256_file(path):
            findings.append(finding("LASP.MODEL.PROVENANCE", "model_provenance", f"Provenance does not hash-bind {path.name}.", "Record exact SHA-256."))
        elif not isinstance(item.get("source_url"), str) or not item["source_url"].strip() or item.get("license_status") != "verified":
            findings.append(finding("LASP.LICENSE.ARTIFACT_UNRESOLVED", "license", f"Source/license is unresolved for {path.name}.", "Resolve independent artifact rights."))
    if set(by_label) != {path.name for path in paths}:
        findings.append(finding("LASP.MODEL.PROVENANCE", "model_provenance", "Provenance labels differ from the exact opaque input/model set.", "Use the exact closure."))
    return findings


def command_audit_input(plan_path: Path, input_path: Path, model_path: Path, provenance_path: Path, documentation_path: Path) -> dict[str, Any]:
    plan_report, plan_raw_sha256 = load_upstream_report(plan_path, "plan", {"pass"})
    input_text = read_text(input_path)
    model_text = read_text(model_path)
    findings = privacy_findings(input_text, "opaque input") + privacy_findings(model_text, "opaque model")
    provenance = load_json(provenance_path)
    findings.extend(check_provenance(provenance, [input_path, model_path]))
    documentation = load_json(documentation_path)
    required_false = ("manual_available", "input_syntax_verified", "output_markers_verified", "restart_semantics_verified")
    required_true = ("manual_advertised", "official_download_page_reviewed", "public_environment_baseline_verified", "public_executable_entry_verified")
    if documentation.get("engine_version") != OPERATING_VERSION:
        findings.append(finding("LASP.DOCS.VERSION_MISMATCH", "documentation", "Documentation attestation version differs from the plan.", "Use a consistent evidence-gap attestation."))
    if (
        not all(documentation.get(key) is False for key in required_false)
        or not all(documentation.get(key) is True for key in required_true)
        or documentation.get("license_status") != "restricted-unverified-terms"
        or documentation.get("discovery_url") != "http://www.lasphub.com/#/lasp/download"
    ):
        findings.append(finding("LASP.DOCS.UNREVIEWED_ATTESTATION", "documentation", "Attestation claims operational evidence not reviewed by this candidate.", "Review primary documents and redesign the parser.", kind="incomplete"))
    findings.extend([
        finding("LASP.DOCS.VERSION_MATCHED_MANUAL_MISSING", "documentation", "No version-matched operational manual is implemented.", "Obtain authorized complete primary documentation.", kind="incomplete"),
        finding("LASP.INPUT.SYNTAX_UNVERIFIED", "input_semantics", "Opaque input syntax, units, defaults, ensemble, timestep, seed and boundary mapping are not verified.", "Implement only from reviewed version-matched documentation.", kind="incomplete"),
        finding("LASP.RESTART.SEMANTICS_UNVERIFIED", "restart_lineage", "State retention and continuation semantics are unknown.", "Obtain authoritative restart specification.", kind="incomplete"),
        finding("LASP.ENVIRONMENT.EXACT_BUILD_UNVERIFIED", "environment", "The public Linux/Intel baseline is known, but exact architecture, compiler/MPI ABI, libraries and package compatibility are unverified.", "Obtain and bind the authorized distribution requirements.", kind="incomplete"),
        finding("LASP.LICENSE.ENGINE_TERMS_UNRESOLVED", "license", "LASP software terms are not retained or verified.", "Resolve exact authorized terms before use.", kind="incomplete"),
    ])
    return make_report(
        "audit-input", findings,
        [evidence(plan_path, "plan-report"), evidence(input_path, "opaque-input"), evidence(model_path, "opaque-model"), evidence(provenance_path, "provenance"), evidence(documentation_path, "documentation-attestation")],
        {"opaque_input_lines": len(input_text.splitlines()), "opaque_model_lines": len(model_text.splitlines()), "semantic_fields_verified": 0},
        extra={"upstream": {"plan_raw_sha256": plan_raw_sha256, "plan_fingerprint": plan_report["report_fingerprint"]}, "input_inventory": {"input_sha256": sha256_file(input_path), "model_sha256": sha256_file(model_path), "syntax_interpretation": "none", "operational_readiness": False}},
    )


def command_audit_output(plan_path: Path, input_path: Path, output_path: Path, attestation_path: Path) -> dict[str, Any]:
    plan_report, plan_raw_sha256 = load_upstream_report(plan_path, "plan", {"pass"})
    input_report, input_raw_sha256 = load_upstream_report(input_path, "audit-input", {"incomplete"})
    if input_report["upstream"]["plan_raw_sha256"] != plan_raw_sha256:
        raise GuardFailure("LASP.UPSTREAM.MISMATCH", "Input inventory is not bound to this plan.")
    output_text = read_text(output_path)
    findings = privacy_findings(output_text, "opaque output")
    if re.search(r"\b(?:error|fatal|nan|inf|segmentation fault)\b", output_text, flags=re.IGNORECASE):
        findings.append(finding("LASP.OUTPUT.ADVERSE_MARKER", "technical_integrity", "Opaque output contains an adverse or non-finite marker.", "Reject it and diagnose through an authorized documented workflow."))
    attestation = load_json(attestation_path)
    valid_attestation = attestation.get("artifact_class") == "project-authored-synthetic" and attestation.get("software_generated") is False and attestation.get("completion_marker_authority") is False and attestation.get("license_status") == "verified"
    if not valid_attestation:
        findings.append(finding("LASP.OUTPUT.ATTESTATION", "artifact_origin", "Output origin/completion/license attestation is contradictory or incomplete.", "Declare exact lawful origin without claiming LASP completion."))
    findings.extend([
        finding("LASP.DOCS.OUTPUT_GRAMMAR_MISSING", "output_semantics", "No version-matched LASP output grammar is implemented.", "Obtain and test authoritative output documentation.", kind="incomplete"),
        finding("LASP.OUTPUT.COMPLETION_UNVERIFIED", "technical_completion", "No phrase can be treated as a LASP completion marker at current maturity.", "Implement version-matched completion and error rules.", kind="incomplete"),
        finding("LASP.OUTPUT.OBSERVABLES_UNVERIFIED", "observable_evidence", "No LASP observable extraction or units mapping is supported.", "Implement deterministic extractors with legal fixtures.", kind="incomplete"),
    ])
    return make_report(
        "audit-output", findings,
        [evidence(plan_path, "plan-report"), evidence(input_path, "input-inventory"), evidence(output_path, "opaque-output"), evidence(attestation_path, "origin-attestation")],
        {"output_lines": len(output_text.splitlines()), "output_bytes": len(output_text.encode("ascii")), "completion_markers_verified": 0, "observables_extracted": 0},
        extra={"upstream": {"plan_raw_sha256": plan_raw_sha256, "input_raw_sha256": input_raw_sha256, "plan_fingerprint": plan_report["report_fingerprint"], "input_fingerprint": input_report["report_fingerprint"]}, "output_inventory": {"source_sha256": sha256_file(output_path), "syntax_interpretation": "none", "technical_completion": "unverified"}},
    )


def parse_extxyz(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    frames: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        try:
            count = int(lines[index].strip())
        except ValueError as exc:
            raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Generic extxyz atom count is invalid.") from exc
        if count <= 0 or index + count + 1 >= len(lines):
            raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Generic extxyz frame is invalid or truncated.")
        metadata_line = lines[index + 1]
        metadata: dict[str, str] = {}
        covered = [False] * len(metadata_line)
        for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)=(\"[^\"]*\"|[^\s]+)", metadata_line):
            key = match.group(1).lower()
            if key in metadata:
                raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Duplicate extxyz metadata key.")
            raw = match.group(2)
            metadata[key] = raw[1:-1] if raw.startswith('"') else raw
            for position in range(match.start(), match.end()):
                covered[position] = True
        if any(not covered[position] and not char.isspace() for position, char in enumerate(metadata_line)):
            raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Unparsed extxyz metadata text.")
        if not all(key in metadata for key in ("pbc", "lattice", "properties")):
            raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "pbc, Lattice, and Properties are required.")
        pbc = metadata["pbc"].upper().split()
        if len(pbc) != 3 or any(item not in {"T", "F"} for item in pbc):
            raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "pbc metadata is invalid.")
        try:
            lattice = [float(value) for value in metadata["lattice"].split()]
        except ValueError as exc:
            raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Lattice is nonnumeric.") from exc
        if len(lattice) != 9 or not all(math.isfinite(value) for value in lattice):
            raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Lattice needs nine finite values.")
        determinant = lattice[0] * (lattice[4] * lattice[8] - lattice[5] * lattice[7]) - lattice[1] * (lattice[3] * lattice[8] - lattice[5] * lattice[6]) + lattice[2] * (lattice[3] * lattice[7] - lattice[4] * lattice[6])
        if abs(determinant) <= 1.0e-12:
            raise GuardFailure("LASP.TRAJECTORY.CELL", "Generic extxyz cell is singular.")
        parts = metadata["properties"].split(":")
        if len(parts) % 3:
            raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Properties metadata is malformed.")
        properties: list[tuple[str, str, int]] = []
        width = 0
        for offset in range(0, len(parts), 3):
            name, kind, width_text = parts[offset:offset + 3]
            try:
                columns = int(width_text)
            except ValueError as exc:
                raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Property width is invalid.") from exc
            if kind not in {"S", "R", "I"} or columns <= 0:
                raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Property type/width is unsupported.")
            properties.append((name, kind, columns))
            width += columns
        if properties[:2] != [("species", "S", 1), ("pos", "R", 3)]:
            raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Properties must begin species:S:1:pos:R:3.")
        species: list[str] = []
        for row in lines[index + 2:index + 2 + count]:
            tokens = row.split()
            if len(tokens) != width or not re.fullmatch(r"[A-Z][a-z]?", tokens[0]):
                raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Atom row width/species is invalid.")
            cursor = 0
            for _, kind, columns in properties:
                values = tokens[cursor:cursor + columns]
                if kind == "R":
                    try:
                        numbers = [float(value) for value in values]
                    except ValueError as exc:
                        raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Real property is nonnumeric.") from exc
                    if not all(math.isfinite(value) for value in numbers):
                        raise GuardFailure("LASP.TRAJECTORY.NONFINITE", "Trajectory contains a non-finite value.")
                elif kind == "I":
                    try:
                        [int(value) for value in values]
                    except ValueError as exc:
                        raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "Integer property is invalid.") from exc
                cursor += columns
            species.append(tokens[0])
        frames.append({"count": count, "species": species, "pbc": [value == "T" for value in pbc], "lattice": lattice, "metadata": metadata})
        index += count + 2
    if not frames:
        raise GuardFailure("LASP.TRAJECTORY.GRAMMAR", "No generic extxyz frame was found.")
    return frames


def command_audit_trajectory(plan_path: Path, input_path: Path, output_path: Path, trajectory_path: Path, frame_index_path: Path) -> dict[str, Any]:
    plan_report, plan_raw_sha256 = load_upstream_report(plan_path, "plan", {"pass"})
    input_report, input_raw_sha256 = load_upstream_report(input_path, "audit-input", {"incomplete"})
    output_report, output_raw_sha256 = load_upstream_report(output_path, "audit-output", {"incomplete"})
    if (
        input_report["upstream"]["plan_raw_sha256"] != plan_raw_sha256
        or output_report["upstream"]["plan_raw_sha256"] != plan_raw_sha256
        or output_report["upstream"]["input_raw_sha256"] != input_raw_sha256
    ):
        raise GuardFailure("LASP.UPSTREAM.MISMATCH", "Inventory reports do not form one raw-byte-bound lineage.")
    frames = parse_extxyz(read_text(trajectory_path))
    frame_index = load_json(frame_index_path)
    findings: list[dict[str, str]] = []
    if frame_index.get("format") != "project-authored-extxyz" or frame_index.get("engine_provenance") != "unverified" or frame_index.get("trajectory_sha256") != sha256_file(trajectory_path) or not isinstance(frame_index.get("frames"), list):
        findings.append(finding("LASP.TRAJECTORY.FRAME_INDEX", "trajectory_integrity", "Frame index does not hash-bind this project-authored trajectory and unverified provenance.", "Regenerate the deterministic sidecar."))
        indexed = []
    else:
        indexed = frame_index["frames"]
    if len(indexed) != len(frames):
        findings.append(finding("LASP.TRAJECTORY.FRAME_COUNT", "trajectory_integrity", "Frame-index and extxyz counts differ.", "Use one exact artifact pair."))
    expected_count = frames[0]["count"]
    expected_species = frames[0]["species"]
    expected_pbc = plan_report["plan"]["boundary"]
    for frame in frames:
        if frame["count"] != expected_count or frame["species"] != expected_species:
            findings.append(finding("LASP.TRAJECTORY.SITE_ORDER", "trajectory_integrity", "Atom count or species order changes across frames.", "Preserve a stable project-defined site order."))
            break
        if frame["pbc"] != expected_pbc:
            findings.append(finding("LASP.TRAJECTORY.BOUNDARY", "trajectory_integrity", "Generic extxyz PBC differs from project plan intent.", "Align the generic artifact and plan."))
            break
    steps: list[int] = []
    times: list[float] = []
    if len(indexed) == len(frames):
        for position, item in enumerate(indexed):
            if not isinstance(item, dict) or item.get("frame") != position or not isinstance(item.get("step"), int) or item["step"] < 0 or not isinstance(item.get("time"), (int, float)) or isinstance(item.get("time"), bool) or not math.isfinite(float(item["time"])) or not isinstance(item.get("time_unit"), str) or not item["time_unit"]:
                findings.append(finding("LASP.TRAJECTORY.FRAME_INDEX", "trajectory_integrity", "Frame index entry is malformed.", "Use ordered finite step/time entries."))
                break
            steps.append(item["step"])
            times.append(float(item["time"]))
        if any(right <= left for left, right in zip(steps, steps[1:])) or any(right <= left for left, right in zip(times, times[1:])):
            findings.append(finding("LASP.TRAJECTORY.CADENCE", "trajectory_integrity", "Frame steps/times are not strictly increasing.", "Correct the generic frame index."))
    findings.append(finding("LASP.TRAJECTORY.ENGINE_PROVENANCE_UNVERIFIED", "engine_provenance", "Generic extxyz integrity cannot establish that LASP generated or completed the trajectory.", "Obtain version-matched output provenance and completion semantics.", kind="incomplete"))
    return make_report(
        "audit-trajectory", findings,
        [evidence(plan_path, "plan-report"), evidence(input_path, "input-inventory"), evidence(output_path, "output-inventory"), evidence(trajectory_path, "generic-extxyz"), evidence(frame_index_path, "frame-index")],
        {"frames": len(frames), "atoms_per_frame": expected_count, "generic_format_integrity": not any(item["kind"] == "fail" for item in findings), "engine_provenance_verified": False},
        extra={"upstream": {"plan_raw_sha256": plan_raw_sha256, "input_raw_sha256": input_raw_sha256, "output_raw_sha256": output_raw_sha256, "plan_fingerprint": plan_report["report_fingerprint"], "input_fingerprint": input_report["report_fingerprint"], "output_fingerprint": output_report["report_fingerprint"]}, "trajectory_inventory": {"source_sha256": sha256_file(trajectory_path), "format": "project-authored-extxyz", "site_identity_limit": "species-order-only", "shared_contract_status": "not-ready"}},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--request", type=Path, required=True)
    plan.add_argument("--out", type=Path)
    audit_input = sub.add_parser("audit-input")
    audit_input.add_argument("--plan", type=Path, required=True)
    audit_input.add_argument("--input", type=Path, required=True)
    audit_input.add_argument("--model", type=Path, required=True)
    audit_input.add_argument("--provenance", type=Path, required=True)
    audit_input.add_argument("--documentation-attestation", type=Path, required=True)
    audit_input.add_argument("--out", type=Path)
    audit_output = sub.add_parser("audit-output")
    audit_output.add_argument("--plan", type=Path, required=True)
    audit_output.add_argument("--input-audit", type=Path, required=True)
    audit_output.add_argument("--output", type=Path, required=True)
    audit_output.add_argument("--attestation", type=Path, required=True)
    audit_output.add_argument("--out", type=Path)
    trajectory = sub.add_parser("audit-trajectory")
    trajectory.add_argument("--plan", type=Path, required=True)
    trajectory.add_argument("--input-audit", type=Path, required=True)
    trajectory.add_argument("--output-audit", type=Path, required=True)
    trajectory.add_argument("--trajectory", type=Path, required=True)
    trajectory.add_argument("--frame-index", type=Path, required=True)
    trajectory.add_argument("--out", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _reset_snapshot_cache()
    try:
        input_paths = [value for key, value in vars(args).items() if key != "out" and isinstance(value, Path)]
        ensure_output_distinct(args.out, input_paths)
        if args.command == "plan":
            report = command_plan(args.request)
        elif args.command == "audit-input":
            report = command_audit_input(args.plan, args.input, args.model, args.provenance, args.documentation_attestation)
        elif args.command == "audit-output":
            report = command_audit_output(args.plan, args.input_audit, args.output, args.attestation)
        else:
            report = command_audit_trajectory(args.plan, args.input_audit, args.output_audit, args.trajectory, args.frame_index)
        return emit(report, args.out)
    except GuardFailure as exc:
        report = make_report(args.command, [finding(exc.code, "deterministic_inventory", exc.message, "Supply safe complete evidence and retry.", kind="incomplete" if exc.incomplete else "fail")], [], {})
        return emit(report, None if exc.code == "LASP.IO.OUTPUT_ALIASES_INPUT" else getattr(args, "out", None))
    except Exception:
        report = make_report(args.command, [finding("LASP.INTERNAL.ERROR", "internal", "The guard encountered an internal error.", "Report a minimal nonsensitive reproducer.")], [], {})
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if getattr(args, "out", None) is None:
            sys.stdout.write(rendered)
        else:
            sys.stderr.write(rendered)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
