#!/usr/bin/env python3
"""Deterministic, non-executing planner and auditor for a conservative GPUMD v5.3 MD slice."""

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
import statistics
import sys
from typing import Any


TOOL_VERSION = "0.2.0"
SCHEMA_VERSION = "1.0"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_TEXT_BYTES = 16 * 1024 * 1024
PINNED_VERSION = "5.3"
PINNED_COMMIT = "f2b46c5d528e985a5bf68becd442b18c0e04396c"
EXPECTED_UNITS = {
    "mass": "amu",
    "charge": "e",
    "length": "angstrom",
    "time": "fs",
    "energy": "eV",
    "pressure": "GPa",
    "temperature": "K",
    "velocity": "angstrom/fs",
}
THERMO_COLUMNS = {
    "temperature": 0,
    "kinetic_energy": 1,
    "potential_energy": 2,
    "pressure_xx": 3,
    "pressure_yy": 4,
    "pressure_zz": 5,
    "pressure_yz": 6,
    "pressure_xz": 7,
    "pressure_xy": 8,
    "cell_ax": 9,
    "cell_ay": 10,
    "cell_az": 11,
    "cell_bx": 12,
    "cell_by": 13,
    "cell_bz": 14,
    "cell_cx": 15,
    "cell_cy": 16,
    "cell_cz": 17,
}
REQUIRED_PLAN = {
    "case_id", "protocol_id", "gpumd_version", "gpumd_commit", "task",
    "objective", "claim_target", "artifact_class", "units", "boundary",
    "ensemble", "timestep_fs", "potential", "restart", "seed",
    "equilibration", "production", "observables", "output", "authorization",
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
    "audit-input": {"upstream", "input"},
    "audit-output": {"upstream", "output"},
    "audit-trajectory": {"upstream", "trajectory"},
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
        raise GuardFailure("GPUMD.IO.NOFOLLOW_UNAVAILABLE", "The host lacks no-follow, directory, or nonblocking path support.", incomplete=True)
    absolute = Path(os.path.abspath(os.fspath(path)))
    root = Path(absolute.anchor)
    flags = os.O_RDONLY | directory_flag | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)
    try:
        root_path_metadata = root.lstat()
        if stat.S_ISLNK(root_path_metadata.st_mode) or not stat.S_ISDIR(root_path_metadata.st_mode):
            raise GuardFailure("GPUMD.IO.UNSAFE_FILE", "A path root is not a real directory.")
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
            raise GuardFailure("GPUMD.IO.CHANGED_DURING_READ", "A path root changed identity.")
        current_fd = root_fd
        current_path = root
        edges: list[tuple[int, str, int, os.stat_result, Path]] = []
        for component in absolute.parts[1:]:
            anchored = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(anchored.st_mode) or not stat.S_ISDIR(anchored.st_mode):
                raise GuardFailure("GPUMD.IO.UNSAFE_FILE", "An intermediate path component is not a real directory.")
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
                raise GuardFailure("GPUMD.IO.CHANGED_DURING_READ", "An intermediate directory changed identity.")
            edges.append((current_fd, component, child_fd, child_metadata, current_path))
            current_fd = child_fd
        return current_fd, edges, absolute
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("GPUMD.IO.UNSAFE_FILE", "A directory path could not be opened safely.") from exc


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
            raise GuardFailure("GPUMD.IO.CHANGED_DURING_READ", "A path root changed identity.")
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
                raise GuardFailure("GPUMD.IO.CHANGED_DURING_READ", "An intermediate directory changed during access.")
    except GuardFailure:
        raise
    except (KeyError, OSError) as exc:
        raise GuardFailure("GPUMD.IO.CHANGED_DURING_READ", "A directory anchor changed during access.") from exc


def read_bytes(path: Path, limit: int) -> bytes:
    key = os.path.abspath(os.fspath(path))
    cached = _SNAPSHOT_CACHE.get(key)
    if cached is not None:
        if not cached or len(cached) > limit:
            raise GuardFailure("GPUMD.IO.SIZE", "A required artifact is empty or exceeds the bounded size.")
        return cached
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        raise GuardFailure("GPUMD.IO.NOFOLLOW_UNAVAILABLE", "The platform cannot establish a no-follow nonblocking input snapshot.", incomplete=True)
    absolute = Path(key)
    if not absolute.name or absolute.name in {".", ".."}:
        raise GuardFailure("GPUMD.IO.UNSAFE_FILE", "An input must name a regular file.")
    parent_fd, edges, _parent = _stable_directory(absolute.parent)
    try:
        anchored_before = os.stat(absolute.name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(anchored_before.st_mode) or anchored_before.st_nlink != 1:
            raise GuardFailure("GPUMD.IO.UNSAFE_FILE", "Inputs must be regular single-link non-symlink files.")
        descriptor = os.open(
            absolute.name,
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("GPUMD.IO.UNSAFE_FILE", "A required artifact is unavailable or not a regular non-symlink file.") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or _file_identity(before) != _file_identity(anchored_before):
            raise GuardFailure("GPUMD.IO.UNSAFE_FILE", "Inputs must be regular single-link non-symlink files.")
        if before.st_size <= 0 or before.st_size > limit:
            raise GuardFailure("GPUMD.IO.SIZE", "A required artifact is empty or exceeds the bounded size.")
        blocks: list[bytes] = []
        total = 0
        while True:
            block = os.read(descriptor, min(65536, limit + 1 - total))
            if not block:
                break
            blocks.append(block)
            total += len(block)
            if total > limit:
                raise GuardFailure("GPUMD.IO.SIZE", "A required artifact exceeds the bounded size.")
        after = os.fstat(descriptor)
        anchored_after = os.stat(absolute.name, dir_fd=parent_fd, follow_symlinks=False)
        lexical_after = absolute.lstat()
        _verify_directory_edges(absolute.parent, edges)
    except OSError as exc:
        raise GuardFailure("GPUMD.IO.READ", "A required artifact could not be read safely.") from exc
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
        raise GuardFailure("GPUMD.IO.CHANGED_DURING_READ", "An input changed identity or content while being read.")
    _SNAPSHOT_CACHE[key] = data
    return data


def read_text(path: Path) -> str:
    data = read_bytes(path, MAX_TEXT_BYTES)
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise GuardFailure("GPUMD.TEXT.NON_ASCII", "The conservative parser accepts ASCII text only.") from exc
    if "\x00" in text:
        raise GuardFailure("GPUMD.TEXT.NUL", "NUL bytes are not accepted.")
    return text


def decode_json_object(data: bytes) -> dict[str, Any]:
    if data.startswith(b"\xef\xbb\xbf"):
        raise GuardFailure("GPUMD.JSON.INVALID", "JSON must be UTF-8 without a BOM.")
    try:
        value = json.loads(
            data.decode("utf-8"), object_pairs_hook=object_pairs, parse_constant=reject_constant
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise GuardFailure("GPUMD.JSON.INVALID", "JSON is malformed or ambiguous.") from exc
    if not isinstance(value, dict):
        raise GuardFailure("GPUMD.JSON.INVALID", "JSON root must be an object.")
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


def artifact(path: Path, role: str) -> dict[str, str]:
    return {"role": role, "label": path.name, "sha256": sha256_file(path)}


def finding(
    code: str,
    gate: str,
    message: str,
    next_action: str,
    *,
    kind: str = "fail",
) -> dict[str, str]:
    return {
        "code": code,
        "gate": gate,
        "severity": "critical",
        "kind": kind,
        "message": message,
        "next_action": next_action,
    }


def local_decision(findings: list[dict[str, str]]) -> str:
    if any(item["kind"] == "fail" for item in findings):
        return "blocked"
    if findings:
        return "incomplete"
    return "pass"


def make_report(
    command: str,
    findings: list[dict[str, str]],
    evidence: list[dict[str, str]],
    metrics: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision = local_decision(findings)
    ceilings = {
        "plan": "no_positive_claim",
        "audit-input": "input_gates_only",
        "audit-output": "technical_run_gates_only",
        "audit-trajectory": "technical_run_gates_only",
    }
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "gpumd_guard", "version": TOOL_VERSION},
        "engine": "gpumd",
        "command": command,
        "decision": decision,
        "candidate_lifecycle": "development",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": ceilings[command],
        "promotion_ready": False,
        "promotion_authorized": False,
        "execution_authorized": False,
        "report_authenticity": "unsigned-candidate-output",
        "maturity": "synthetic-validated",
        "findings": findings,
        "evidence": sorted(evidence, key=lambda item: (item["role"], item["label"])),
        "metrics": metrics,
        "limitations": [
            "This tool performs bounded offline parsing and never invokes GPUMD.",
            "A local pass does not establish model validity, equilibrium, ergodicity, or scientific acceptance.",
            "Current validation uses project-authored synthetic and format fixtures.",
            "No missing shared run, structure, topology, segment, or trajectory record is fabricated.",
            "This unsigned candidate report needs an external trusted manifest or signature before it can serve as authenticated evidence.",
        ],
    }
    if extra:
        report.update(extra)
    report["report_fingerprint"] = canonical_hash(
        {key: value for key, value in report.items() if key != "report_fingerprint"}
    )
    return report


def ensure_output_distinct(out: Path | None, inputs: list[Path]) -> None:
    if out is None:
        return
    output_resolved = out.resolve(strict=False)
    for input_path in inputs:
        if output_resolved == input_path.resolve(strict=False):
            raise GuardFailure("GPUMD.IO.OUTPUT_ALIASES_INPUT", "The report output aliases an input artifact.")
        try:
            output_stat = out.lstat()
            input_stat = input_path.lstat()
        except OSError:
            continue
        if (output_stat.st_dev, output_stat.st_ino) == (input_stat.st_dev, input_stat.st_ino):
            raise GuardFailure("GPUMD.IO.OUTPUT_ALIASES_INPUT", "The report output shares identity with an input artifact.")


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
        raise GuardFailure("GPUMD.IO.WRITE", "The staged report path changed before publication.")
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
            raise GuardFailure("GPUMD.IO.OVERWRITE", "The report target appeared during atomic publication.") from exc
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
            raise GuardFailure("GPUMD.IO.WRITE", "Atomic publication did not bind the retained staging descriptor.")
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
                raise GuardFailure("GPUMD.IO.WRITE", "Atomic publication rollback failed; output state is indeterminate.") from rollback_error
        if isinstance(exc, GuardFailure):
            raise
        raise GuardFailure("GPUMD.IO.WRITE", "Atomic publication could not be verified.") from exc


def _atomic_write_new(path: Path, payload: bytes) -> None:
    absolute = Path(os.path.abspath(os.fspath(path)))
    if not absolute.name or absolute.name in {".", ".."}:
        raise GuardFailure("GPUMD.IO.WRITE", "The output must name a new regular file.")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None or not all(function in os.supports_dir_fd for function in (os.open, os.stat, os.link, os.unlink)):
        raise GuardFailure("GPUMD.IO.NOFOLLOW_UNAVAILABLE", "The host lacks descriptor-relative atomic publish support.", incomplete=True)
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
            raise GuardFailure("GPUMD.IO.OVERWRITE", "The report path already exists.")
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
            raise GuardFailure("GPUMD.IO.WRITE", "A private staging file could not be created.")
        offset = 0
        while offset < len(payload):
            written = os.write(temporary_fd, payload[offset:])
            if written <= 0:
                raise OSError("short report write")
            offset += written
        os.fsync(temporary_fd)
        if not _staging_matches(directory_fd, temporary_name, temporary_fd, payload, 1):
            raise GuardFailure("GPUMD.IO.WRITE", "The staged report identity or content is invalid.")
        _verify_directory_edges(absolute.parent, edges)
        try:
            os.stat(absolute.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise GuardFailure("GPUMD.IO.OVERWRITE", "The report target appeared during staging.")
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
            raise GuardFailure("GPUMD.IO.WRITE", "The published report changed after staging cleanup.")
        _verify_directory_edges(absolute.parent, edges)
        os.fsync(directory_fd)
        installed = True
        linked_target = None
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("GPUMD.IO.WRITE", "The report could not be published atomically without overwrite.") from exc
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


def is_safe_id(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value))


def finite_positive(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0
    )


def validate_plan_request(request: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    missing = sorted(REQUIRED_PLAN - set(request))
    if missing:
        findings.append(finding("GPUMD.PLAN.MISSING_FIELD", "claim_definition", "Required fields are missing: " + ", ".join(missing), "Supply every required field without guessing."))
        return findings
    if not is_safe_id(request["case_id"]) or not is_safe_id(request["protocol_id"]):
        findings.append(finding("GPUMD.PLAN.INVALID_ID", "privacy", "Case and protocol IDs must be privacy-safe.", "Use anonymous alphanumeric identifiers."))
    if request["gpumd_version"] != PINNED_VERSION or request["gpumd_commit"] != PINNED_COMMIT:
        findings.append(finding("GPUMD.VERSION.UNSUPPORTED", "official_version_match", "Only exact GPUMD v5.3 at the pinned commit has documentary coverage.", "Pin v5.3 and its exact commit or extend official evidence.", kind="incomplete"))
    if request["task"] != "nve" or request["ensemble"] != "nve":
        findings.append(finding("GPUMD.PLAN.UNSUPPORTED_TASK", "ensemble", "The parser-supported core is standard NVE only.", "Keep other ensembles design-only until separately implemented.", kind="incomplete"))
    if not isinstance(request["objective"], str) or not request["objective"].strip() or not isinstance(request["claim_target"], str) or not request["claim_target"].strip():
        findings.append(finding("GPUMD.PLAN.CLAIM", "claim_definition", "Objective and bounded claim target must be nonempty.", "State both explicitly."))
    if request["artifact_class"] not in {"synthetic", "user-supplied"}:
        findings.append(finding("GPUMD.PLAN.ARTIFACT_CLASS", "claim_definition", "Artifact class must be synthetic or user-supplied.", "Declare the evidence class."))
    if request["units"] != EXPECTED_UNITS:
        findings.append(finding("GPUMD.UNITS.MISMATCH", "units", "The plan does not use GPUMD's fixed MD unit map.", "Use the exact documented unit map."))
    if not isinstance(request["boundary"], list) or len(request["boundary"]) != 3 or not all(isinstance(item, bool) for item in request["boundary"]):
        findings.append(finding("GPUMD.BOUNDARY.INVALID", "boundary", "Boundary must contain three booleans.", "Declare all three axes."))
    if not finite_positive(request["timestep_fs"]):
        findings.append(finding("GPUMD.PLAN.TIMESTEP", "numerical_discretization", "Time step must be finite and positive in fs.", "Declare an explicitly tested time step."))
    potential = request["potential"]
    if not isinstance(potential, dict) or potential.get("family") != "lj" or not all(isinstance(potential.get(key), str) and potential[key].strip() for key in ("identity", "source_url", "license_status")):
        findings.append(finding("GPUMD.POTENTIAL.PROVENANCE", "potential_provenance", "A complete analytic LJ potential declaration is required.", "Provide family, identity, source, and license status."))
    elif potential["license_status"] != "verified":
        findings.append(finding("GPUMD.LICENSE.UNRESOLVED", "potential_provenance", "Potential license status is unresolved.", "Resolve use and redistribution terms."))
    restart = request["restart"]
    if not isinstance(restart, dict) or restart.get("mode") not in {"new", "state-file-continuation"}:
        findings.append(finding("GPUMD.RESTART.LINEAGE", "restart_lineage", "Restart mode is missing or invalid.", "Declare new or state-file-continuation."))
    elif restart["mode"] == "state-file-continuation":
        valid = (
            is_safe_id(restart.get("parent_run_id"))
            and isinstance(restart.get("state_sha256"), str)
            and bool(re.fullmatch(r"[a-f0-9]{64}", restart["state_sha256"]))
            and isinstance(restart.get("parent_final_step"), int)
            and restart["parent_final_step"] >= 0
            and finite_positive(restart.get("segment_start_time_fs"))
        )
        if not valid:
            findings.append(finding("GPUMD.RESTART.LINEAGE", "restart_lineage", "Continuation lacks parent ID, state hash, final step, or segment time.", "Bind the exact parent state and segment boundary."))
    seed = request["seed"]
    if not isinstance(seed, dict) or seed.get("mode") not in {"explicit", "state-velocities"}:
        findings.append(finding("GPUMD.SEED.POLICY", "initial_state", "Seed policy is missing or invalid.", "Declare explicit or state-velocities."))
    elif seed["mode"] == "explicit" and (not isinstance(seed.get("value"), int) or isinstance(seed.get("value"), bool) or seed["value"] <= 0):
        findings.append(finding("GPUMD.SEED.POLICY", "initial_state", "Explicit seed must be a positive integer.", "Record the exact seed."))
    if isinstance(restart, dict) and isinstance(seed, dict):
        if restart.get("mode") == "new" and seed.get("mode") != "explicit":
            findings.append(finding("GPUMD.SEED.POLICY", "initial_state", "A new run requires an explicit seed.", "Use explicit seed mode."))
        if restart.get("mode") == "state-file-continuation" and seed.get("mode") != "state-velocities":
            findings.append(finding("GPUMD.SEED.POLICY", "initial_state", "Continuation must preserve state velocities.", "Use state-velocities mode."))
    total_steps = 0
    for phase_name in ("equilibration", "production"):
        phase = request[phase_name]
        if not isinstance(phase, dict) or not isinstance(phase.get("steps"), int) or isinstance(phase.get("steps"), bool) or phase["steps"] < 0 or not isinstance(phase.get("acceptance_checks"), list) or not phase["acceptance_checks"]:
            findings.append(finding("GPUMD.PLAN.PHASE", "equilibration_production", f"{phase_name} must declare steps and acceptance checks.", "Predeclare both phases."))
        else:
            total_steps += phase["steps"]
    if total_steps <= 0:
        findings.append(finding("GPUMD.PLAN.PHASE", "equilibration_production", "Total planned steps must be positive.", "Declare a nonzero production."))
    observables = request["observables"]
    if not isinstance(observables, list) or not observables:
        findings.append(finding("GPUMD.PLAN.OBSERVABLE", "statistics", "At least one observable is required.", "Declare observable and uncertainty policy."))
    else:
        names: set[str] = set()
        for item in observables:
            valid = (
                isinstance(item, dict)
                and item.get("name") in THERMO_COLUMNS
                and item.get("name") not in names
                and isinstance(item.get("unit"), str)
                and item.get("estimator") == "mean"
                and item.get("uncertainty_method") == "block-mean"
                and isinstance(item.get("minimum_effective_samples"), int)
                and item["minimum_effective_samples"] >= 2
                and finite_positive(item.get("max_standard_error"))
            )
            if not valid:
                findings.append(finding("GPUMD.PLAN.OBSERVABLE", "statistics", "Observable definition is duplicate, unsupported, or incomplete.", "Use a documented thermo column and explicit ESS/error bounds."))
                break
            names.add(item["name"])
    output = request["output"]
    output_keys = ("thermo_interval_steps", "trajectory_interval_steps", "restart_interval_steps", "expected_trajectory_frames")
    if not isinstance(output, dict) or not all(isinstance(output.get(key), int) and not isinstance(output.get(key), bool) and output[key] > 0 for key in output_keys) or not isinstance(output.get("trajectory_filename"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", output["trajectory_filename"]):
        findings.append(finding("GPUMD.PLAN.OUTPUT", "output_cadence", "Output cadence, frame expectation, or safe trajectory filename is invalid.", "Declare deterministic positive intervals and a basename."))
    elif total_steps > 0 and total_steps // output["trajectory_interval_steps"] != output["expected_trajectory_frames"]:
        findings.append(finding("GPUMD.PLAN.OUTPUT", "output_cadence", "Expected trajectory frames do not match total steps and cadence.", "Correct the predeclared frame count."))
    auth = request["authorization"]
    if not isinstance(auth, dict) or auth.get("execute_external_software") is not False:
        findings.append(finding("GPUMD.EXECUTION.NOT_AUTHORIZED", "execution_boundary", "This candidate accepts only explicit no-execution plans.", "Route future execution through a separately authorized Skill."))
    return findings


def command_plan(request_path: Path) -> dict[str, Any]:
    request = load_json(request_path)
    findings = validate_plan_request(request)
    return make_report(
        "plan",
        findings,
        [artifact(request_path, "plan-request")],
        {"required_gate_count": 14, "supported_task_count": 1},
        extra={"plan_request_sha256": sha256_file(request_path), "plan": request},
    )


def load_upstream_report(
    path: Path, command: str, allowed_decisions: set[str]
) -> tuple[dict[str, Any], str]:
    """Load one verified byte snapshot; candidate fingerprints are not trust roots."""

    raw = read_bytes(path, MAX_JSON_BYTES)
    report = decode_json_object(raw)
    if command not in REPORT_COMMAND_KEYS or set(report) != REPORT_BASE_KEYS | REPORT_COMMAND_KEYS[command]:
        raise GuardFailure("GPUMD.UPSTREAM.SHAPE", f"The upstream {command} report does not have the complete canonical shape.")
    invariant = (
        report.get("schema_version") == SCHEMA_VERSION
        and report.get("tool") == {"name": "gpumd_guard", "version": TOOL_VERSION}
        and report.get("engine") == "gpumd"
        and report.get("command") == command
        and report.get("decision") in allowed_decisions
        and report.get("candidate_lifecycle") == "development"
        and report.get("claim_ceiling") == "no_positive_claim"
        and report.get("promotion_ready") is False
        and report.get("promotion_authorized") is False
        and report.get("execution_authorized") is False
        and report.get("report_authenticity") == "unsigned-candidate-output"
        and report.get("maturity") == "synthetic-validated"
        and isinstance(report.get("future_gate_ceiling"), str)
        and isinstance(report.get("findings"), list)
        and isinstance(report.get("evidence"), list)
        and isinstance(report.get("metrics"), dict)
        and isinstance(report.get("limitations"), list)
        and report["limitations"]
        and all(isinstance(item, str) and item for item in report["limitations"])
    )
    if not invariant:
        raise GuardFailure("GPUMD.UPSTREAM.INVARIANT", f"The upstream {command} report violates development unsigned candidate invariants.")
    finding_keys = {"code", "gate", "severity", "kind", "message", "next_action"}
    if any(
        not isinstance(item, dict)
        or set(item) != finding_keys
        or item.get("kind") not in {"fail", "incomplete"}
        or not all(isinstance(item.get(key), str) and item[key] for key in finding_keys)
        for item in report["findings"]
    ) or local_decision(report["findings"]) != report["decision"]:
        raise GuardFailure("GPUMD.UPSTREAM.SHAPE", f"The upstream {command} findings are not canonical.")
    evidence_keys = {"role", "label", "sha256"}
    if any(
        not isinstance(item, dict)
        or set(item) != evidence_keys
        or not isinstance(item.get("role"), str)
        or not item["role"]
        or not isinstance(item.get("label"), str)
        or not item["label"]
        or not isinstance(item.get("sha256"), str)
        or re.fullmatch(r"[a-f0-9]{64}", item["sha256"]) is None
        for item in report["evidence"]
    ) or report["evidence"] != sorted(report["evidence"], key=lambda item: (item["role"], item["label"])):
        raise GuardFailure("GPUMD.UPSTREAM.SHAPE", f"The upstream {command} evidence inventory is not canonical.")
    fingerprint = report.get("report_fingerprint")
    expected_fingerprint = canonical_hash({key: value for key, value in report.items() if key != "report_fingerprint"})
    if not isinstance(fingerprint, str) or re.fullmatch(r"[a-f0-9]{64}", fingerprint) is None or fingerprint != expected_fingerprint:
        raise GuardFailure("GPUMD.UPSTREAM.TAMPERED", f"The upstream {command} self-fingerprint is invalid.")
    if command == "plan":
        if not isinstance(report.get("plan"), dict) or re.fullmatch(r"[a-f0-9]{64}", report.get("plan_request_sha256", "")) is None:
            raise GuardFailure("GPUMD.UPSTREAM.SHAPE", "The upstream plan payload is incomplete.")
    else:
        payload_key = {"audit-input": "input", "audit-output": "output", "audit-trajectory": "trajectory"}[command]
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
            raise GuardFailure("GPUMD.UPSTREAM.SHAPE", f"The upstream {command} lineage payload is incomplete.")
    return report, sha256_bytes(raw)


def parse_run_in(text: str) -> list[tuple[int, list[str]]]:
    parsed: list[tuple[int, list[str]]] = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if any(char in line for char in ("$", "`", ";", "\\")):
            raise GuardFailure("GPUMD.INPUT.AMBIGUOUS", f"run.in line {number} contains unsupported expansion or control characters.", incomplete=True)
        tokens = line.split()
        if not all(re.fullmatch(r"[^\s\x00]+", token) for token in tokens):
            raise GuardFailure("GPUMD.INPUT.AMBIGUOUS", f"run.in line {number} cannot be tokenized conservatively.", incomplete=True)
        parsed.append((number, tokens))
    if not parsed:
        raise GuardFailure("GPUMD.INPUT.EMPTY", "run.in has no commands.")
    return parsed


def parse_extxyz(text: str, *, role: str) -> list[dict[str, Any]]:
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
            raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} frame atom count is invalid.") from exc
        if count <= 0 or index + count + 1 >= len(lines):
            raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} frame is truncated or has invalid atom count.")
        metadata_line = lines[index + 1].strip()
        metadata: dict[str, str] = {}
        covered = [False] * len(metadata_line)
        for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)=(\"[^\"]*\"|[^\s]+)", metadata_line):
            key = match.group(1).lower()
            if key in metadata:
                raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} metadata has a duplicate key.")
            value = match.group(2)
            metadata[key] = value[1:-1] if value.startswith('"') else value
            for pos in range(match.start(), match.end()):
                covered[pos] = True
        if any(not covered[pos] and not char.isspace() for pos, char in enumerate(metadata_line)):
            raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} metadata contains unparsed text.")
        for required in ("pbc", "lattice", "properties"):
            if required not in metadata:
                raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} metadata lacks {required}.")
        pbc_tokens = metadata["pbc"].upper().split()
        if len(pbc_tokens) != 3 or any(token not in {"T", "F"} for token in pbc_tokens):
            raise GuardFailure("GPUMD.BOUNDARY.INVALID", f"{role} pbc is invalid.")
        try:
            lattice = [float(value) for value in metadata["lattice"].split()]
        except ValueError as exc:
            raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} lattice is invalid.") from exc
        if len(lattice) != 9 or not all(math.isfinite(value) for value in lattice):
            raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} lattice must contain nine finite values.")
        property_tokens = metadata["properties"].split(":")
        if len(property_tokens) % 3:
            raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} Properties is malformed.")
        properties: list[tuple[str, str, int]] = []
        width = 0
        for offset in range(0, len(property_tokens), 3):
            name, kind, columns_text = property_tokens[offset:offset + 3]
            try:
                columns = int(columns_text)
            except ValueError as exc:
                raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} property width is invalid.") from exc
            if kind not in {"S", "R", "I"} or columns <= 0 or any(existing[0] == name for existing in properties):
                raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} Properties is unsupported or duplicate.")
            properties.append((name, kind, columns))
            width += columns
        if properties[:2] != [("species", "S", 1), ("pos", "R", 3)]:
            raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} must begin with species:S:1:pos:R:3.")
        rows: list[list[str]] = []
        for row_number in range(count):
            row = lines[index + 2 + row_number].split()
            if len(row) != width or not re.fullmatch(r"[A-Z][a-z]?", row[0]):
                raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} atom row width or species is invalid.")
            cursor = 0
            for _, kind, columns in properties:
                values = row[cursor:cursor + columns]
                if kind == "R":
                    try:
                        numbers = [float(value) for value in values]
                    except ValueError as exc:
                        raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} has nonnumeric real data.") from exc
                    if not all(math.isfinite(value) for value in numbers):
                        raise GuardFailure("GPUMD.MODEL.NONFINITE", f"{role} contains non-finite values.")
                elif kind == "I":
                    try:
                        [int(value) for value in values]
                    except ValueError as exc:
                        raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} has noninteger data.") from exc
                cursor += columns
            rows.append(row)
        frames.append({
            "count": count,
            "metadata": metadata,
            "pbc": [token == "T" for token in pbc_tokens],
            "lattice": lattice,
            "properties": properties,
            "rows": rows,
            "species": [row[0] for row in rows],
        })
        index += count + 2
    if not frames:
        raise GuardFailure("GPUMD.MODEL.GRAMMAR", f"{role} has no frames.")
    return frames


def determinant(cell: list[float]) -> float:
    ax, ay, az, bx, by, bz, cx, cy, cz = cell
    return ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)


def cross_norm(left: list[float], right: list[float]) -> float:
    cross = [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]
    return math.sqrt(sum(value * value for value in cross))


def cell_thicknesses(cell: list[float]) -> list[float]:
    a, b, c = cell[0:3], cell[3:6], cell[6:9]
    volume = abs(determinant(cell))
    areas = [cross_norm(b, c), cross_norm(c, a), cross_norm(a, b)]
    if volume <= 1.0e-12 or any(area <= 1.0e-12 for area in areas):
        raise GuardFailure("GPUMD.MODEL.CELL", "Cell is singular.")
    return [volume / area for area in areas]


def parse_lj(text: str) -> dict[str, Any]:
    lines = [line.split("#", 1)[0].strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        raise GuardFailure("GPUMD.POTENTIAL.GRAMMAR", "Potential file is empty.")
    header = lines[0].split()
    if len(header) < 3 or header[0].lower() != "lj":
        raise GuardFailure("GPUMD.POTENTIAL.UNSUPPORTED", "Only the v5.3 LJ potential format is supported.", incomplete=True)
    try:
        count = int(header[1])
    except ValueError as exc:
        raise GuardFailure("GPUMD.POTENTIAL.GRAMMAR", "LJ type count is invalid.") from exc
    elements = header[2:]
    if count <= 0 or count > 10 or len(elements) != count or len(set(elements)) != count or any(not re.fullmatch(r"[A-Z][a-z]?", item) for item in elements):
        raise GuardFailure("GPUMD.POTENTIAL.GRAMMAR", "LJ element declaration is invalid.")
    if len(lines) != 1 + count * count:
        raise GuardFailure("GPUMD.POTENTIAL.GRAMMAR", "LJ pair table is incomplete or has extra rows.")
    triples: list[list[float]] = []
    for line in lines[1:]:
        tokens = line.split()
        if len(tokens) != 3:
            raise GuardFailure("GPUMD.POTENTIAL.GRAMMAR", "Each LJ pair row needs epsilon, sigma, and cutoff.")
        try:
            values = [float(token) for token in tokens]
        except ValueError as exc:
            raise GuardFailure("GPUMD.POTENTIAL.GRAMMAR", "LJ pair parameters must be numeric.") from exc
        if not all(math.isfinite(value) and value > 0 for value in values):
            raise GuardFailure("GPUMD.POTENTIAL.GRAMMAR", "LJ parameters must be finite and positive.")
        triples.append(values)
    return {"family": "lj", "elements": elements, "max_cutoff_angstrom": max(row[2] for row in triples)}


def check_provenance(provenance: dict[str, Any], files: list[Path]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    entries = provenance.get("artifacts")
    if not isinstance(entries, list):
        return [finding("GPUMD.POTENTIAL.PROVENANCE", "potential_provenance", "Provenance artifacts are missing.", "Declare each input artifact.")]
    by_label: dict[str, dict[str, Any]] = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("label"), str) or item["label"] in by_label:
            findings.append(finding("GPUMD.POTENTIAL.PROVENANCE", "potential_provenance", "Provenance entries are malformed or duplicate.", "Use one complete record per basename."))
            return findings
        by_label[item["label"]] = item
    for path in files:
        item = by_label.get(path.name)
        if not item or item.get("sha256") != sha256_file(path):
            findings.append(finding("GPUMD.POTENTIAL.PROVENANCE", "potential_provenance", f"Provenance hash does not bind {path.name}.", "Record the exact SHA-256."))
        elif not isinstance(item.get("source_url"), str) or not item["source_url"].strip() or item.get("license_status") != "verified":
            findings.append(finding("GPUMD.LICENSE.UNRESOLVED", "potential_provenance", f"Source or license status is unresolved for {path.name}.", "Resolve authority and legal status."))
    if set(by_label) != {path.name for path in files}:
        findings.append(finding("GPUMD.POTENTIAL.PROVENANCE", "potential_provenance", "Provenance contains missing or unbound artifact labels.", "Use the exact audited artifact set."))
    return findings


def command_audit_input(plan_path: Path, run_path: Path, model_path: Path, potential_path: Path, provenance_path: Path) -> dict[str, Any]:
    plan_report, plan_raw_sha256 = load_upstream_report(plan_path, "plan", {"pass"})
    plan = plan_report["plan"]
    findings: list[dict[str, str]] = []
    commands = parse_run_in(read_text(run_path))
    allowed = {"potential", "velocity", "time_step", "ensemble", "dump_thermo", "dump_restart", "dump_xyz", "run"}
    unknown = sorted({tokens[0] for _, tokens in commands if tokens[0] not in allowed})
    if unknown:
        findings.append(finding("GPUMD.INPUT.UNSUPPORTED_COMMAND", "input_grammar", "Unsupported commands: " + ", ".join(unknown), "Add a version-matched profile and tests before use.", kind="incomplete"))
    potential_commands = [tokens for _, tokens in commands if tokens[0] == "potential"]
    if len(potential_commands) != 1 or len(potential_commands[0]) != 2 or potential_commands[0][1] != potential_path.name or "/" in potential_commands[0][1] or "\\" in potential_commands[0][1]:
        findings.append(finding("GPUMD.INPUT.POTENTIAL", "potential_provenance", "Exactly one basename-only potential command must bind the audited file.", "Use the audited potential basename."))
    timestep_commands = [tokens for _, tokens in commands if tokens[0] == "time_step"]
    if len(timestep_commands) != 1 or len(timestep_commands[0]) not in {2, 3}:
        findings.append(finding("GPUMD.INPUT.TIMESTEP", "numerical_discretization", "Exactly one supported time_step command is required.", "Declare time_step before run."))
    else:
        try:
            observed_dt = float(timestep_commands[0][1])
        except ValueError:
            observed_dt = math.nan
        if not math.isfinite(observed_dt) or not math.isclose(observed_dt, float(plan["timestep_fs"]), rel_tol=0.0, abs_tol=1.0e-12):
            findings.append(finding("GPUMD.INPUT.TIMESTEP", "numerical_discretization", "run.in time_step does not match the plan.", "Use the planned fs value."))
    frames = parse_extxyz(read_text(model_path), role="model.xyz")
    if len(frames) != 1:
        findings.append(finding("GPUMD.MODEL.GRAMMAR", "initial_state", "model.xyz must contain exactly one structure.", "Provide one initial state."))
    model = frames[0]
    if model["pbc"] != plan["boundary"]:
        findings.append(finding("GPUMD.BOUNDARY.MISMATCH", "boundary", "model.xyz pbc differs from the plan.", "Align all three axes."))
    property_names = [item[0] for item in model["properties"]]
    velocities_present = "vel" in property_names
    velocity_commands = [tokens for _, tokens in commands if tokens[0] == "velocity"]
    if plan["restart"]["mode"] == "new":
        valid_velocity = len(velocity_commands) == 1 and len(velocity_commands[0]) == 4 and velocity_commands[0][2] == "seed"
        if valid_velocity:
            try:
                seed = int(velocity_commands[0][3])
                temperature = float(velocity_commands[0][1])
            except ValueError:
                valid_velocity = False
            else:
                valid_velocity = seed == plan["seed"]["value"] and math.isfinite(temperature) and temperature > 0
        if not valid_velocity or velocities_present:
            findings.append(finding("GPUMD.SEED.POLICY", "initial_state", "New-run velocity generation is ambiguous or does not match the explicit seed.", "Remove model velocities and use velocity <K> seed <integer>."))
    else:
        if velocity_commands or not velocities_present or sha256_file(model_path) != plan["restart"]["state_sha256"]:
            findings.append(finding("GPUMD.RESTART.LINEAGE", "restart_lineage", "Continuation must use the hash-bound model velocities without a velocity command.", "Bind and preserve the exact state file."))
    lj = parse_lj(read_text(potential_path))
    if sorted(set(model["species"])) != sorted(lj["elements"]):
        findings.append(finding("GPUMD.POTENTIAL.ELEMENTS", "potential_provenance", "Model species and LJ elements differ.", "Use a complete matching potential."))
    try:
        thicknesses = cell_thicknesses(model["lattice"])
    except GuardFailure as exc:
        findings.append(finding(exc.code, "boundary", exc.message, "Provide a nonsingular cell."))
        thicknesses = []
    if thicknesses and any(periodic and thickness <= 2.0 * lj["max_cutoff_angstrom"] for periodic, thickness in zip(model["pbc"], thicknesses)):
        findings.append(finding("GPUMD.POTENTIAL.MINIMUM_IMAGE", "boundary", "A periodic cell thickness is not greater than twice the LJ cutoff.", "Enlarge the cell or use a justified compatible model."))
    total_steps = 0
    expected_thermo_rows = 0
    expected_frames = 0
    segment: dict[str, list[str]] = {}
    segment_count = 0
    for line_number, tokens in commands:
        command = tokens[0]
        if command in {"ensemble", "dump_thermo", "dump_restart", "dump_xyz"}:
            if command in segment and command != "dump_xyz":
                findings.append(finding("GPUMD.RUN_BLOCK.DUPLICATE", "run_block", f"Duplicate {command} before run at line {line_number}.", "Use one unambiguous control per block."))
            segment[command] = tokens
        if command != "run":
            continue
        segment_count += 1
        try:
            steps = int(tokens[1]) if len(tokens) == 2 else -1
        except ValueError:
            steps = -1
        if steps <= 0:
            findings.append(finding("GPUMD.RUN_BLOCK.STEPS", "run_block", "run requires one positive integer step count.", "Declare deterministic steps."))
            steps = 0
        required_controls = {"ensemble", "dump_thermo", "dump_restart", "dump_xyz"}
        missing = sorted(required_controls - set(segment))
        if missing:
            findings.append(finding("GPUMD.RUN_BLOCK.NONPROPAGATING", "run_block", "Run block lacks non-propagating controls: " + ", ".join(missing), "Repeat every required control before each run."))
        else:
            ensemble = segment["ensemble"]
            if ensemble != ["ensemble", "nve"] or plan["ensemble"] != "nve":
                findings.append(finding("GPUMD.RUN_BLOCK.ENSEMBLE", "ensemble", "The run block is not the planned NVE ensemble.", "Use ensemble nve for this profile."))
            try:
                thermo_interval = int(segment["dump_thermo"][1]) if len(segment["dump_thermo"]) == 2 else -1
                restart_interval = int(segment["dump_restart"][1]) if len(segment["dump_restart"]) == 2 else -1
                xyz = segment["dump_xyz"]
                xyz_interval = int(xyz[3]) if len(xyz) >= 5 else -1
            except ValueError:
                thermo_interval = restart_interval = xyz_interval = -1
            if thermo_interval != plan["output"]["thermo_interval_steps"] or restart_interval != plan["output"]["restart_interval_steps"]:
                findings.append(finding("GPUMD.RUN_BLOCK.CADENCE", "output_cadence", "Thermo or restart cadence differs from the plan.", "Use planned intervals in every block."))
            if len(xyz) < 5 or xyz[1] != "-1" or xyz_interval != plan["output"]["trajectory_interval_steps"] or xyz[4] != plan["output"]["trajectory_filename"]:
                findings.append(finding("GPUMD.RUN_BLOCK.CADENCE", "trajectory_integrity", "dump_xyz does not cover the whole system at the planned cadence/name.", "Use the planned dump_xyz form."))
            elif "unwrapped_position" not in xyz[5:]:
                findings.append(finding("GPUMD.TRAJECTORY.PROPERTY", "trajectory_integrity", "dump_xyz does not request unwrapped_position.", "Request it when diffusion or crossing claims may be made.", kind="incomplete"))
            if thermo_interval > 0:
                expected_thermo_rows += steps // thermo_interval
            if xyz_interval > 0:
                expected_frames += steps // xyz_interval
        total_steps += steps
        segment = {}
    if segment_count == 0:
        findings.append(finding("GPUMD.RUN_BLOCK.MISSING", "run_block", "No run command was found.", "Add an explicit run block."))
    if segment:
        findings.append(finding("GPUMD.RUN_BLOCK.TRAILING", "run_block", "Non-propagating controls remain after the final run.", "Remove unused trailing controls."))
    planned_steps = plan["equilibration"]["steps"] + plan["production"]["steps"]
    if total_steps != planned_steps:
        findings.append(finding("GPUMD.RUN_BLOCK.STEPS", "equilibration_production", "Total run steps differ from the plan.", "Align input and plan."))
    if expected_frames != plan["output"]["expected_trajectory_frames"]:
        findings.append(finding("GPUMD.RUN_BLOCK.CADENCE", "trajectory_integrity", "Derived frame count differs from the plan.", "Correct segment cadence or expected count."))
    provenance = load_json(provenance_path)
    findings.extend(check_provenance(provenance, [run_path, model_path, potential_path]))
    evidence = [
        artifact(plan_path, "plan-report"), artifact(run_path, "run-input"),
        artifact(model_path, "initial-state"), artifact(potential_path, "potential"),
        artifact(provenance_path, "provenance"),
    ]
    extra = {
        "upstream": {
            "plan_raw_sha256": plan_raw_sha256,
            "plan_fingerprint": plan_report["report_fingerprint"],
        },
        "input": {
            "atom_count": model["count"], "species_order": model["species"],
            "boundary": model["pbc"], "lattice": model["lattice"],
            "properties": property_names, "potential_family": lj["family"],
            "max_cutoff_angstrom": lj["max_cutoff_angstrom"],
            "cell_thickness_angstrom": thicknesses, "total_steps": total_steps,
            "run_blocks": segment_count, "expected_thermo_rows": expected_thermo_rows,
            "expected_trajectory_frames": expected_frames,
            "artifact_hashes": {path.name: sha256_file(path) for path in (run_path, model_path, potential_path)},
        },
    }
    return make_report("audit-input", findings, evidence, {"commands": len(commands), "run_blocks": segment_count, "atoms": model["count"]}, extra=extra)


def autocorrelation_ess(values: list[float]) -> float:
    count = len(values)
    if count < 2:
        return float(count)
    mean = statistics.fmean(values)
    centered = [value - mean for value in values]
    variance = sum(value * value for value in centered) / count
    if variance <= 1.0e-30:
        return float(count)
    tau = 1.0
    for lag in range(1, min(count, max(2, count // 2 + 1))):
        covariance = sum(centered[index] * centered[index + lag] for index in range(count - lag)) / (count - lag)
        correlation = covariance / variance
        if correlation <= 0:
            break
        tau += 2.0 * correlation
    return max(1.0, min(float(count), count / tau))


def block_standard_error(values: list[float]) -> tuple[float, int]:
    count = len(values)
    if count < 2:
        return math.inf, 0
    block_size = max(1, int(math.sqrt(count)))
    block_count = count // block_size
    if block_count < 2:
        return math.inf, block_count
    means = [statistics.fmean(values[index * block_size:(index + 1) * block_size]) for index in range(block_count)]
    return statistics.stdev(means) / math.sqrt(block_count), block_count


def command_audit_output(plan_path: Path, input_path: Path, stdout_path: Path, thermo_path: Path) -> dict[str, Any]:
    plan_report, plan_raw_sha256 = load_upstream_report(plan_path, "plan", {"pass"})
    input_report, input_raw_sha256 = load_upstream_report(input_path, "audit-input", {"pass"})
    if input_report["upstream"]["plan_raw_sha256"] != plan_raw_sha256:
        raise GuardFailure("GPUMD.UPSTREAM.MISMATCH", "Input audit is not bound to this plan.")
    plan = plan_report["plan"]
    findings: list[dict[str, str]] = []
    stdout = read_text(stdout_path)
    markers = {
        "version": len(re.findall(r"^\*\s+version 5\.3\s+\*$", stdout, flags=re.MULTILINE)),
        "start": stdout.count("Started running GPUMD."),
        "commands_complete": stdout.count("Finished executing the commands in run.in."),
        "timing": len(re.findall(r"^Time used = [0-9]+(?:\.[0-9]+)? s\.$", stdout, flags=re.MULTILINE)),
        "finish": stdout.count("Finished running GPUMD."),
    }
    if any(value != 1 for value in markers.values()):
        findings.append(finding("GPUMD.OUTPUT.COMPLETION", "technical_completion", "Required v5.3 start/completion markers are missing, duplicated, or concatenated.", "Provide one complete captured stdout stream."))
    if re.search(r"\b(?:error|nan|inf|segmentation fault|cuda failure)\b", stdout, flags=re.IGNORECASE):
        findings.append(finding("GPUMD.OUTPUT.ERROR", "technical_completion", "Stdout contains an error or non-finite marker.", "Diagnose the run; do not accept completion."))
    thermo_lines = [line.strip() for line in read_text(thermo_path).splitlines() if line.strip() and not line.lstrip().startswith("#")]
    rows: list[list[float]] = []
    for line in thermo_lines:
        tokens = line.split()
        if len(tokens) != 18:
            findings.append(finding("GPUMD.OUTPUT.THERMO_GRAMMAR", "observable_evidence", "Every thermo.out row must contain exactly 18 columns.", "Use an unmodified v5.3 thermo.out segment."))
            break
        try:
            values = [float(token) for token in tokens]
        except ValueError:
            findings.append(finding("GPUMD.OUTPUT.THERMO_GRAMMAR", "observable_evidence", "thermo.out contains nonnumeric data.", "Provide the exact numeric file."))
            break
        if not all(math.isfinite(value) for value in values):
            findings.append(finding("GPUMD.OUTPUT.NONFINITE", "numerical_stability", "thermo.out contains non-finite values.", "Reject and diagnose the run."))
            break
        rows.append(values)
    expected_rows = input_report["input"]["expected_thermo_rows"]
    if len(rows) != expected_rows:
        findings.append(finding("GPUMD.OUTPUT.THERMO_COUNT", "observable_evidence", "Thermo row count differs from the input-derived expectation.", "Isolate the exact output segment and cadence."))
    thermo_interval = plan["output"]["thermo_interval_steps"]
    equil_steps = plan["equilibration"]["steps"]
    production_indices = [index for index in range(len(rows)) if (index + 1) * thermo_interval > equil_steps]
    stats: dict[str, Any] = {}
    for observable in plan["observables"]:
        name = observable["name"]
        values = [rows[index][THERMO_COLUMNS[name]] for index in production_indices] if rows else []
        if len(values) < 2:
            findings.append(finding("GPUMD.STATISTICS.INSUFFICIENT", "statistics", f"{name} has fewer than two production samples.", "Increase predeclared production sampling."))
            continue
        ess = autocorrelation_ess(values)
        standard_error, blocks = block_standard_error(values)
        stats[name] = {
            "samples": len(values), "mean": statistics.fmean(values),
            "effective_samples": ess, "block_count": blocks,
            "block_standard_error": standard_error, "unit": observable["unit"],
        }
        if ess < observable["minimum_effective_samples"]:
            findings.append(finding("GPUMD.STATISTICS.LOW_ESS", "statistics", f"{name} effective sample count is below the declared minimum.", "Extend or replicate the predeclared protocol."))
        if not math.isfinite(standard_error) or standard_error > observable["max_standard_error"]:
            findings.append(finding("GPUMD.STATISTICS.UNCERTAINTY", "statistics", f"{name} block standard error exceeds the declared bound.", "Collect sufficient independent evidence."))
    return make_report(
        "audit-output", findings,
        [artifact(plan_path, "plan-report"), artifact(input_path, "input-audit"), artifact(stdout_path, "stdout"), artifact(thermo_path, "thermo-series")],
        {"thermo_rows": len(rows), "production_rows": len(production_indices), "completion_markers": markers},
        extra={
            "upstream": {
                "plan_raw_sha256": plan_raw_sha256,
                "input_raw_sha256": input_raw_sha256,
                "plan_fingerprint": plan_report["report_fingerprint"],
                "input_fingerprint": input_report["report_fingerprint"],
            },
            "output": {"statistics": stats, "stdout_sha256": sha256_file(stdout_path), "thermo_sha256": sha256_file(thermo_path)},
        },
    )


def command_audit_trajectory(plan_path: Path, input_path: Path, output_path: Path, trajectory_path: Path) -> dict[str, Any]:
    plan_report, plan_raw_sha256 = load_upstream_report(plan_path, "plan", {"pass"})
    input_report, input_raw_sha256 = load_upstream_report(input_path, "audit-input", {"pass"})
    output_report, output_raw_sha256 = load_upstream_report(output_path, "audit-output", {"pass"})
    if (
        input_report["upstream"]["plan_raw_sha256"] != plan_raw_sha256
        or output_report["upstream"]["plan_raw_sha256"] != plan_raw_sha256
        or output_report["upstream"]["input_raw_sha256"] != input_raw_sha256
    ):
        raise GuardFailure("GPUMD.UPSTREAM.MISMATCH", "Trajectory audit upstream reports do not form one lineage.")
    plan = plan_report["plan"]
    frames = parse_extxyz(read_text(trajectory_path), role="trajectory")
    findings: list[dict[str, str]] = []
    expected_count = input_report["input"]["expected_trajectory_frames"]
    if len(frames) != expected_count:
        findings.append(finding("GPUMD.TRAJECTORY.FRAME_COUNT", "trajectory_integrity", "Trajectory frame count differs from the plan.", "Isolate the exact trajectory segment."))
    expected_atoms = input_report["input"]["atom_count"]
    expected_species = input_report["input"]["species_order"]
    expected_boundary = input_report["input"]["boundary"]
    times: list[float] = []
    for frame in frames:
        if frame["count"] != expected_atoms or frame["species"] != expected_species:
            findings.append(finding("GPUMD.TRAJECTORY.SITE_ORDER", "trajectory_integrity", "Atom count or species/site order changed.", "Preserve the complete-system stable ordering."))
            break
        if frame["pbc"] != expected_boundary:
            findings.append(finding("GPUMD.TRAJECTORY.PBC", "trajectory_integrity", "Frame PBC differs from the plan.", "Reject mixed-boundary segments."))
            break
        try:
            cell_thicknesses(frame["lattice"])
        except GuardFailure:
            findings.append(finding("GPUMD.TRAJECTORY.CELL", "trajectory_integrity", "A frame cell is singular.", "Reject the trajectory."))
            break
        names = [item[0] for item in frame["properties"]]
        if "unwrapped_position" not in names:
            findings.append(finding("GPUMD.TRAJECTORY.PROPERTY", "trajectory_integrity", "unwrapped_position is absent.", "Do not make displacement-across-boundary claims.", kind="incomplete"))
            break
        try:
            time_value = float(frame["metadata"]["time"])
        except (KeyError, ValueError):
            findings.append(finding("GPUMD.TRAJECTORY.TIME", "trajectory_integrity", "Frame Time metadata is missing or invalid.", "Preserve GPUMD v5.3 Time metadata."))
            break
        if not math.isfinite(time_value):
            findings.append(finding("GPUMD.TRAJECTORY.TIME", "trajectory_integrity", "Frame Time is non-finite.", "Reject the trajectory."))
            break
        times.append(time_value)
    interval_time = plan["output"]["trajectory_interval_steps"] * plan["timestep_fs"]
    segment_start = plan["restart"].get("segment_start_time_fs", 0.0)
    expected_times = [segment_start + interval_time * (index + 1) for index in range(len(frames))]
    if len(times) == len(frames):
        if any(not math.isclose(value, expected, rel_tol=0.0, abs_tol=1.0e-6) for value, expected in zip(times, expected_times)):
            findings.append(finding("GPUMD.TRAJECTORY.CADENCE", "trajectory_integrity", "Frame Time values do not match planned cadence and lineage.", "Correct the segment boundary or isolate the exact file."))
        if any(right <= left for left, right in zip(times, times[1:])):
            findings.append(finding("GPUMD.TRAJECTORY.TIME", "trajectory_integrity", "Frame Time is not strictly increasing.", "Reject concatenated or reordered frames."))
    return make_report(
        "audit-trajectory", findings,
        [artifact(plan_path, "plan-report"), artifact(input_path, "input-audit"), artifact(output_path, "output-audit"), artifact(trajectory_path, "trajectory")],
        {"frames": len(frames), "atoms_per_frame": expected_atoms, "time_start_fs": times[0] if times else None, "time_end_fs": times[-1] if times else None},
        extra={
            "upstream": {
                "plan_raw_sha256": plan_raw_sha256,
                "input_raw_sha256": input_raw_sha256,
                "output_raw_sha256": output_raw_sha256,
                "plan_fingerprint": plan_report["report_fingerprint"],
                "input_fingerprint": input_report["report_fingerprint"],
                "output_fingerprint": output_report["report_fingerprint"],
            },
            "trajectory": {"format": "extxyz", "source_sha256": sha256_file(trajectory_path), "coordinate_semantics": ["wrapped", "unwrapped"], "site_identity_limit": "species-order-only-without-explicit-site-id", "shared_contract_status": "handoff-inventory-only"},
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="validate a no-execution GPUMD plan")
    plan.add_argument("--request", type=Path, required=True)
    plan.add_argument("--out", type=Path)
    audit_input = sub.add_parser("audit-input", help="audit v5.3 core input files")
    audit_input.add_argument("--plan", type=Path, required=True)
    audit_input.add_argument("--run-in", type=Path, required=True)
    audit_input.add_argument("--model", type=Path, required=True)
    audit_input.add_argument("--potential", type=Path, required=True)
    audit_input.add_argument("--provenance", type=Path, required=True)
    audit_input.add_argument("--out", type=Path)
    audit_output = sub.add_parser("audit-output", help="audit stdout, thermo and sampling")
    audit_output.add_argument("--plan", type=Path, required=True)
    audit_output.add_argument("--input-audit", type=Path, required=True)
    audit_output.add_argument("--stdout", type=Path, required=True)
    audit_output.add_argument("--thermo", type=Path, required=True)
    audit_output.add_argument("--out", type=Path)
    trajectory = sub.add_parser("audit-trajectory", help="audit GPUMD extxyz trajectory")
    trajectory.add_argument("--plan", type=Path, required=True)
    trajectory.add_argument("--input-audit", type=Path, required=True)
    trajectory.add_argument("--output-audit", type=Path, required=True)
    trajectory.add_argument("--trajectory", type=Path, required=True)
    trajectory.add_argument("--out", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _reset_snapshot_cache()
    try:
        input_paths = [value for key, value in vars(args).items() if key != "out" and isinstance(value, Path)]
        ensure_output_distinct(args.out, input_paths)
        if args.command == "plan":
            report = command_plan(args.request)
        elif args.command == "audit-input":
            report = command_audit_input(args.plan, args.run_in, args.model, args.potential, args.provenance)
        elif args.command == "audit-output":
            report = command_audit_output(args.plan, args.input_audit, args.stdout, args.thermo)
        else:
            report = command_audit_trajectory(args.plan, args.input_audit, args.output_audit, args.trajectory)
        return emit(report, args.out)
    except GuardFailure as exc:
        report = make_report(
            args.command,
            [finding(exc.code, "deterministic_audit", exc.message, "Supply safe complete evidence and retry.", kind="incomplete" if exc.incomplete else "fail")],
            [],
            {},
        )
        return emit(report, None if exc.code == "GPUMD.IO.OUTPUT_ALIASES_INPUT" else getattr(args, "out", None))
    except Exception:
        report = make_report(
            args.command,
            [finding("GPUMD.INTERNAL.ERROR", "internal", "The guard encountered an internal error.", "Report the reproducible fixture without sensitive data.")],
            [],
            {},
        )
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if getattr(args, "out", None) is None:
            sys.stdout.write(rendered)
        else:
            sys.stderr.write(rendered)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
