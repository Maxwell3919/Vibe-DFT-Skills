#!/usr/bin/env python3
"""Deterministic offline planner and static auditor for a narrow LAMMPS MD core."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import shlex
import stat
import statistics
import sys
from typing import Any


TOOL_VERSION = "0.2.0"
SCHEMA_VERSION = "1.0"
REPORT_AUTHENTICITY = "unsigned-candidate-output"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_TEXT_BYTES = 16 * 1024 * 1024
PINNED_VERSION = "4Jul2026"
PINNED_BANNER = "LAMMPS (4 Jul 2026)"
LJ_UNIT_MAP = {
    "length": "sigma",
    "time": "tau",
    "energy": "epsilon",
    "mass": "reference_mass",
    "temperature": "epsilon/k_B",
    "pressure": "epsilon/sigma^3",
    "charge": "reduced",
}
OBSERVABLE_COLUMNS = {
    "temperature": "Temp",
    "potential_energy": "PotEng",
    "kinetic_energy": "KinEng",
    "total_energy": "TotEng",
    "pressure": "Press",
}
REQUIRED_PLAN = {
    "case_id", "protocol_id", "lammps_version", "task", "objective",
    "claim_target", "artifact_class", "units_style", "unit_map", "boundary",
    "atom_style", "ensemble", "timestep", "topology", "interaction_model",
    "restart", "seeds", "equilibration", "production", "observables", "output",
    "build_requirements", "authorization",
}
BLOCKED_COMMANDS = {
    "shell", "python", "geturl", "plugin", "jump", "if", "label", "next",
    "variable", "quit", "clear",
}
ALLOWED_COMMANDS = {
    "units", "atom_style", "boundary", "read_data", "read_restart", "pair_style",
    "pair_coeff", "neighbor", "neigh_modify", "velocity", "fix", "timestep",
    "thermo", "thermo_style", "thermo_modify", "dump", "restart", "run", "include",
}
_SNAPSHOT_CACHE: dict[str, bytes] = {}
_DIRECTORY_BINDINGS: dict[str, tuple[int, int, int]] = {}
_INPUT_IDENTITIES: set[tuple[int, int]] = set()
_OPENAT_SUPPORTED = os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd
_LINKAT_SUPPORTED = all(function in os.supports_dir_fd for function in (os.open, os.stat, os.link, os.unlink))


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


def _directory_identity(value: os.stat_result) -> tuple[int, int, int]:
    return stat.S_IFMT(value.st_mode), value.st_dev, value.st_ino


def _reset_snapshot_cache() -> None:
    _SNAPSHOT_CACHE.clear()
    _INPUT_IDENTITIES.clear()
    for _device, _inode, descriptor in _DIRECTORY_BINDINGS.values():
        try:
            os.close(descriptor)
        except OSError:
            pass
    _DIRECTORY_BINDINGS.clear()


def _normalized_absolute(path: Path) -> Path:
    """Normalize only a platform root alias, then preserve every lower component lexically."""

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
                raise GuardFailure("LAMMPS.IO.UNSAFE_FILE", "A platform root alias is unstable.") from exc
            if not stat.S_ISDIR(resolved_metadata.st_mode):
                raise GuardFailure("LAMMPS.IO.UNSAFE_FILE", "A platform root alias is not a directory.")
            absolute = resolved_first.joinpath(*parts[2:])
    return absolute


def _bound_directory_descriptor(directory: Path) -> tuple[int, Path]:
    """Open every directory edge with openat/no-follow and reuse retained bindings."""

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory_flag is None or nonblock is None:
        raise GuardFailure("LAMMPS.IO.NOFOLLOW_UNAVAILABLE", "The platform lacks safe directory traversal support.", incomplete=True)
    if not _OPENAT_SUPPORTED:
        raise GuardFailure("LAMMPS.IO.NOFOLLOW_UNAVAILABLE", "The platform lacks openat/statat support.", incomplete=True)
    absolute = _normalized_absolute(directory)
    root = Path(absolute.anchor)
    flags = os.O_RDONLY | directory_flag | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)
    descriptors: list[int] = []
    edges: list[tuple[int, str, int, os.stat_result]] = []
    try:
        root_path_metadata = root.lstat()
        if stat.S_ISLNK(root_path_metadata.st_mode) or not stat.S_ISDIR(root_path_metadata.st_mode):
            raise GuardFailure("LAMMPS.IO.UNSAFE_FILE", "The filesystem root is unavailable or unsafe.")
        current_fd = os.open(root, flags)
        descriptors.append(current_fd)
        current_metadata = os.fstat(current_fd)
        if _directory_identity(current_metadata) != _directory_identity(root_path_metadata):
            raise GuardFailure("LAMMPS.IO.CHANGED_DURING_READ", "A directory identity changed during traversal.")
        root_key = os.fspath(root)
        retained_root = _DIRECTORY_BINDINGS.get(root_key)
        if retained_root is None:
            _DIRECTORY_BINDINGS[root_key] = (current_metadata.st_dev, current_metadata.st_ino, os.dup(current_fd))
        elif retained_root[:2] != (current_metadata.st_dev, current_metadata.st_ino):
            raise GuardFailure("LAMMPS.IO.CHANGED_DURING_READ", "A bound directory identity changed.")

        current_path = root
        for component in absolute.parts[1:]:
            anchored_before = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(anchored_before.st_mode) or not stat.S_ISDIR(anchored_before.st_mode):
                raise GuardFailure("LAMMPS.IO.UNSAFE_FILE", "An intermediate path component is a symlink or non-directory.")
            child_fd = os.open(component, flags, dir_fd=current_fd)
            child_metadata = os.fstat(child_fd)
            if _directory_identity(child_metadata) != _directory_identity(anchored_before):
                os.close(child_fd)
                raise GuardFailure("LAMMPS.IO.CHANGED_DURING_READ", "An intermediate directory changed during openat.")
            current_path = current_path / component
            binding_key = os.fspath(current_path)
            retained = _DIRECTORY_BINDINGS.get(binding_key)
            if retained is None:
                _DIRECTORY_BINDINGS[binding_key] = (child_metadata.st_dev, child_metadata.st_ino, os.dup(child_fd))
            else:
                if retained[:2] != (child_metadata.st_dev, child_metadata.st_ino):
                    os.close(child_fd)
                    raise GuardFailure("LAMMPS.IO.CHANGED_DURING_READ", "A request/evidence base changed identity.")
                retained_fd = os.dup(retained[2])
                retained_metadata = os.fstat(retained_fd)
                if _directory_identity(retained_metadata) != _directory_identity(child_metadata):
                    os.close(retained_fd)
                    os.close(child_fd)
                    raise GuardFailure("LAMMPS.IO.CHANGED_DURING_READ", "A retained request/evidence base is unstable.")
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
                raise GuardFailure("LAMMPS.IO.CHANGED_DURING_READ", "An intermediate directory changed during traversal.")
        lexical_final = absolute.lstat()
        if _directory_identity(lexical_final) != _directory_identity(os.fstat(current_fd)):
            raise GuardFailure("LAMMPS.IO.CHANGED_DURING_READ", "The input base changed during traversal.")
        return os.dup(current_fd), absolute
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("LAMMPS.IO.UNSAFE_FILE", "A directory path could not be traversed without aliases.") from exc
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
            raise GuardFailure("LAMMPS.IO.CHANGED_DURING_READ", "A request/evidence base changed during I/O.")
    finally:
        os.close(verification_fd)


def read_bytes(path: Path, limit: int) -> bytes:
    key = os.path.abspath(os.fspath(path))
    cached = _SNAPSHOT_CACHE.get(key)
    if cached is not None:
        if not cached or len(cached) > limit:
            raise GuardFailure("LAMMPS.IO.SIZE", "A required artifact is empty or exceeds the bounded size.")
        return cached
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        raise GuardFailure("LAMMPS.IO.NOFOLLOW_UNAVAILABLE", "The platform cannot establish a nonblocking no-follow input snapshot.", incomplete=True)
    parent_fd, _normalized_parent = _bound_directory_descriptor(path.parent)
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path.name,
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
    except OSError as exc:
        os.close(parent_fd)
        raise GuardFailure("LAMMPS.IO.UNSAFE_FILE", "A required artifact is unavailable or not a regular non-symlink file.") from exc
    try:
        assert descriptor is not None
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise GuardFailure("LAMMPS.IO.UNSAFE_FILE", "Inputs must be regular single-link non-symlink files.")
        if before.st_size <= 0 or before.st_size > limit:
            raise GuardFailure("LAMMPS.IO.SIZE", "A required artifact is empty or exceeds the bounded size.")
        blocks: list[bytes] = []
        total = 0
        while True:
            block = os.read(descriptor, min(65536, limit + 1 - total))
            if not block:
                break
            blocks.append(block)
            total += len(block)
            if total > limit:
                raise GuardFailure("LAMMPS.IO.SIZE", "A required artifact exceeds the bounded size.")
        after = os.fstat(descriptor)
        anchored_final = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        lexical_final = Path(os.path.abspath(os.fspath(path))).lstat()
        _verify_bound_directory(path.parent, parent_fd)
    except OSError as exc:
        raise GuardFailure("LAMMPS.IO.READ", "A required artifact could not be read safely.") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_fd)
    data = b"".join(blocks)
    identity = _file_identity(before)
    if identity != _file_identity(after) or identity != _file_identity(anchored_final) or identity != _file_identity(lexical_final) or not stat.S_ISREG(anchored_final.st_mode) or anchored_final.st_nlink != 1 or len(data) != before.st_size:
        raise GuardFailure("LAMMPS.IO.CHANGED_DURING_READ", "An input changed identity or content while being read.")
    _SNAPSHOT_CACHE[key] = data
    _INPUT_IDENTITIES.add((before.st_dev, before.st_ino))
    return data


def read_text(path: Path) -> str:
    data = read_bytes(path, MAX_TEXT_BYTES)
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise GuardFailure("LAMMPS.TEXT.NON_ASCII", "The conservative parser accepts ASCII only.") from exc
    if "\x00" in text:
        raise GuardFailure("LAMMPS.TEXT.NUL", "NUL bytes are not accepted.")
    return text


def parse_json_bytes(data: bytes) -> dict[str, Any]:
    if data.startswith(b"\xef\xbb\xbf"):
        raise GuardFailure("LAMMPS.JSON.INVALID", "JSON must be UTF-8 without BOM.")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=object_pairs, parse_constant=reject_constant)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise GuardFailure("LAMMPS.JSON.INVALID", "JSON is malformed or ambiguous.") from exc
    if not isinstance(value, dict):
        raise GuardFailure("LAMMPS.JSON.INVALID", "JSON root must be an object.")
    return value


def load_json(path: Path) -> dict[str, Any]:
    return parse_json_bytes(read_bytes(path, MAX_JSON_BYTES))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(read_bytes(path, MAX_TEXT_BYTES))


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(raw.encode("utf-8"))


BASE_REPORT_KEYS = {
    "schema_version", "tool", "engine", "command", "decision",
    "candidate_lifecycle", "claim_ceiling", "future_gate_ceiling",
    "promotion_ready", "promotion_authorized", "execution_authorized",
    "report_authenticity", "maturity", "findings", "evidence", "metrics",
    "limitations", "report_fingerprint",
}
COMMAND_REPORT_KEYS = {
    "plan": {"plan_request_sha256", "plan"},
    "audit-input": {"upstream", "input"},
    "audit-output": {"upstream", "output"},
    "audit-trajectory": {"upstream", "trajectory"},
}
FUTURE_CEILINGS = {
    "plan": "no_positive_claim",
    "audit-input": "input_gates_only",
    "audit-output": "technical_run_gates_only",
    "audit-trajectory": "technical_run_gates_only",
}


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[a-f0-9]{64}", value))


def _shape_failure(message: str) -> None:
    raise GuardFailure("LAMMPS.UPSTREAM.INVALID_SHAPE", message)


def _validate_upstream_shape(report: dict[str, Any], command: str) -> None:
    if command not in COMMAND_REPORT_KEYS or set(report) != BASE_REPORT_KEYS | COMMAND_REPORT_KEYS[command]:
        _shape_failure(f"Upstream {command} report does not have the complete canonical key set.")
    if report.get("schema_version") != SCHEMA_VERSION:
        _shape_failure(f"Upstream {command} schema version is not supported.")
    if report.get("tool") != {"name": "lammps_guard", "version": TOOL_VERSION}:
        _shape_failure(f"Upstream {command} tool identity is invalid.")
    if report.get("engine") != "lammps" or report.get("command") != command:
        _shape_failure(f"Upstream {command} engine or command identity is invalid.")
    if report.get("candidate_lifecycle") != "development" or report.get("claim_ceiling") != "no_positive_claim":
        _shape_failure(f"Upstream {command} candidate lifecycle or current claim ceiling is invalid.")
    if report.get("future_gate_ceiling") != FUTURE_CEILINGS[command]:
        _shape_failure(f"Upstream {command} future gate ceiling is invalid.")
    if any(report.get(key) is not False for key in ("promotion_ready", "promotion_authorized", "execution_authorized")):
        _shape_failure(f"Upstream {command} contains promotion or execution authorization.")
    if report.get("report_authenticity") != REPORT_AUTHENTICITY:
        _shape_failure(f"Upstream {command} authenticity marker is invalid.")
    if report.get("maturity") != "synthetic-validated":
        _shape_failure(f"Upstream {command} maturity is invalid.")
    findings = report.get("findings")
    if not isinstance(findings, list):
        _shape_failure(f"Upstream {command} findings are invalid.")
    for item in findings:
        if (
            not isinstance(item, dict)
            or set(item) != {"code", "gate", "severity", "kind", "message", "next_action"}
            or not all(isinstance(item[key], str) and item[key] for key in item)
            or item["severity"] != "critical"
            or item["kind"] not in {"fail", "incomplete"}
        ):
            _shape_failure(f"Upstream {command} finding shape is invalid.")
    observed_decision = report.get("decision")
    if observed_decision not in {"pass", "blocked", "incomplete"} or observed_decision != decision(findings):
        _shape_failure(f"Upstream {command} decision is inconsistent with its findings.")
    artifacts = report.get("evidence")
    if not isinstance(artifacts, list) or not artifacts:
        _shape_failure(f"Upstream {command} evidence inventory is invalid.")
    for item in artifacts:
        if (
            not isinstance(item, dict)
            or set(item) != {"role", "label", "sha256"}
            or not isinstance(item["role"], str)
            or not item["role"]
            or not isinstance(item["label"], str)
            or not item["label"]
            or Path(item["label"]).name != item["label"]
            or not _is_sha256(item["sha256"])
        ):
            _shape_failure(f"Upstream {command} evidence entry is invalid.")
    if artifacts != sorted(artifacts, key=lambda item: (item["role"], item["label"])):
        _shape_failure(f"Upstream {command} evidence inventory is not canonicalized.")
    evidence_by_role: dict[str, list[str]] = {}
    for item in artifacts:
        evidence_by_role.setdefault(item["role"], []).append(item["sha256"])
    if not isinstance(report.get("metrics"), dict):
        _shape_failure(f"Upstream {command} metrics are invalid.")
    limitations = report.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(isinstance(item, str) and item for item in limitations):
        _shape_failure(f"Upstream {command} limitations are invalid.")
    if not _is_sha256(report.get("report_fingerprint")):
        _shape_failure(f"Upstream {command} self fingerprint is invalid.")
    expected_fingerprint = canonical_hash({key: value for key, value in report.items() if key != "report_fingerprint"})
    if report["report_fingerprint"] != expected_fingerprint:
        raise GuardFailure("LAMMPS.UPSTREAM.TAMPERED", f"Upstream {command} self fingerprint is inconsistent.")
    if command == "plan":
        if (
            not isinstance(report.get("plan"), dict)
            or validate_plan(report["plan"])
            or not _is_sha256(report.get("plan_request_sha256"))
            or report["metrics"] != {"required_gate_count": 15, "supported_task_count": 1}
        ):
            _shape_failure("Upstream plan payload, source hash, or metrics are invalid.")
        if evidence_by_role.get("plan-request") != [report["plan_request_sha256"]]:
            _shape_failure("Upstream plan request evidence and source hash disagree.")
    else:
        upstream = report.get("upstream")
        required_upstream = {
            "audit-input": {"plan_report_raw_sha256"},
            "audit-output": {"plan_report_raw_sha256", "input_report_raw_sha256"},
            "audit-trajectory": {"plan_report_raw_sha256", "input_report_raw_sha256", "output_report_raw_sha256"},
        }[command]
        if not isinstance(upstream, dict) or set(upstream) != required_upstream or not all(_is_sha256(value) for value in upstream.values()):
            _shape_failure(f"Upstream {command} raw-byte lineage inventory is invalid.")
        required_roles = {
            "audit-input": {"plan-report": "plan_report_raw_sha256"},
            "audit-output": {
                "plan-report": "plan_report_raw_sha256",
                "input-audit": "input_report_raw_sha256",
            },
            "audit-trajectory": {
                "plan-report": "plan_report_raw_sha256",
                "input-audit": "input_report_raw_sha256",
                "output-audit": "output_report_raw_sha256",
            },
        }[command]
        if any(evidence_by_role.get(role) != [upstream[field]] for role, field in required_roles.items()):
            _shape_failure(f"Upstream {command} evidence and raw-byte lineage hashes disagree.")
        if command == "audit-input":
            payload = report.get("input")
            required_input = {
                "atom_count", "site_types", "bounds", "boundary", "pair_style",
                "pair_cutoff", "run_steps", "expected_thermo_steps",
                "expected_dump_steps", "build_executable_sha256", "input_closure_hashes",
            }
            if not isinstance(payload, dict) or set(payload) != required_input:
                _shape_failure("Upstream audit-input payload keys are invalid.")
            if (
                not isinstance(payload["atom_count"], int)
                or isinstance(payload["atom_count"], bool)
                or payload["atom_count"] <= 0
                or not isinstance(payload["site_types"], dict)
                or len(payload["site_types"]) != payload["atom_count"]
                or not all(isinstance(key, str) and key.isdigit() and isinstance(value, int) and not isinstance(value, bool) and value > 0 for key, value in payload["site_types"].items())
                or not isinstance(payload["bounds"], dict)
                or set(payload["bounds"]) != set("xyz")
                or not all(isinstance(value, list) and len(value) == 2 and all(isinstance(number, (int, float)) and not isinstance(number, bool) and math.isfinite(float(number)) for number in value) and value[1] > value[0] for value in payload["bounds"].values())
                or payload["boundary"] != ["p", "p", "p"]
                or payload["pair_style"] != "lj/cut"
                or not positive(payload["pair_cutoff"])
                or not isinstance(payload["run_steps"], int)
                or isinstance(payload["run_steps"], bool)
                or payload["run_steps"] <= 0
                or not all(isinstance(payload[key], list) and payload[key] and all(isinstance(step, int) and not isinstance(step, bool) and step >= 0 for step in payload[key]) for key in ("expected_thermo_steps", "expected_dump_steps"))
                or not _is_sha256(payload["build_executable_sha256"])
                or not isinstance(payload["input_closure_hashes"], dict)
                or not payload["input_closure_hashes"]
                or not all(isinstance(label, str) and Path(label).name == label and _is_sha256(value) for label, value in payload["input_closure_hashes"].items())
            ):
                _shape_failure("Upstream audit-input payload values are invalid.")
            metrics = report["metrics"]
            if (
                set(metrics) != {"commands", "include_files", "atoms", "atom_types"}
                or not all(isinstance(metrics[key], int) and not isinstance(metrics[key], bool) and metrics[key] > 0 for key in metrics)
                or metrics["atoms"] != payload["atom_count"]
                or metrics["atom_types"] != len(set(payload["site_types"].values()))
            ):
                _shape_failure("Upstream audit-input metrics are invalid.")
        elif command == "audit-output":
            payload = report.get("output")
            if (
                not isinstance(payload, dict)
                or set(payload) != {"statistics", "log_sha256"}
                or not isinstance(payload["statistics"], dict)
                or not _is_sha256(payload["log_sha256"])
            ):
                _shape_failure("Upstream audit-output payload is invalid.")
            metrics = report["metrics"]
            if (
                set(metrics) != {"version_banner_count", "loop_marker_count", "thermo_rows", "production_rows"}
                or not all(isinstance(metrics[key], int) and not isinstance(metrics[key], bool) and metrics[key] >= 0 for key in metrics)
                or metrics["version_banner_count"] != 1
                or metrics["loop_marker_count"] != 1
                or metrics["thermo_rows"] <= 0
                or metrics["production_rows"] <= 0
                or metrics["production_rows"] > metrics["thermo_rows"]
            ):
                _shape_failure("Upstream audit-output metrics are invalid.")
        else:
            payload = report.get("trajectory")
            required_trajectory = {
                "format", "source_sha256", "site_identity", "wrapped_coordinates",
                "image_flags", "orthogonal_unwrapping_reconstructable", "shared_contract_status",
            }
            if (
                not isinstance(payload, dict)
                or set(payload) != required_trajectory
                or payload["format"] != "lammps-custom-text"
                or not _is_sha256(payload["source_sha256"])
                or any(payload[key] is not True for key in ("wrapped_coordinates", "image_flags", "orthogonal_unwrapping_reconstructable"))
                or payload["site_identity"] != "atom-id"
                or payload["shared_contract_status"] != "handoff-inventory-only"
            ):
                _shape_failure("Upstream audit-trajectory payload is invalid.")
            metrics = report["metrics"]
            if (
                set(metrics) != {"frames", "atoms_per_frame", "first_step", "last_step"}
                or not all(isinstance(metrics[key], int) and not isinstance(metrics[key], bool) for key in metrics)
                or metrics["frames"] <= 0
                or metrics["atoms_per_frame"] <= 0
                or metrics["first_step"] < 0
                or metrics["last_step"] < metrics["first_step"]
            ):
                _shape_failure("Upstream audit-trajectory metrics are invalid.")


def load_verified_upstream(path: Path, command: str) -> tuple[dict[str, Any], str]:
    """Load one exact raw snapshot, validate the unsigned report, and return its raw SHA-256."""

    raw = read_bytes(path, MAX_JSON_BYTES)
    report = parse_json_bytes(raw)
    _validate_upstream_shape(report, command)
    if report["decision"] != "pass":
        raise GuardFailure("LAMMPS.UPSTREAM.NOT_PASSING", f"A passing upstream {command} report is required.")
    return report, sha256_bytes(raw)


def evidence(path: Path, role: str) -> dict[str, str]:
    return {"role": role, "label": path.name, "sha256": sha256_file(path)}


def finding(code: str, gate: str, message: str, next_action: str, *, kind: str = "fail") -> dict[str, str]:
    return {"code": code, "gate": gate, "severity": "critical", "kind": kind, "message": message, "next_action": next_action}


def decision(findings: list[dict[str, str]]) -> str:
    if any(item["kind"] == "fail" for item in findings):
        return "blocked"
    if findings:
        return "incomplete"
    return "pass"


def make_report(command: str, findings: list[dict[str, str]], artifacts: list[dict[str, str]], metrics: dict[str, Any], *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    local = decision(findings)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "lammps_guard", "version": TOOL_VERSION},
        "engine": "lammps",
        "command": command,
        "decision": local,
        "candidate_lifecycle": "development",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": FUTURE_CEILINGS[command],
        "promotion_ready": False,
        "promotion_authorized": False,
        "execution_authorized": False,
        "report_authenticity": REPORT_AUTHENTICITY,
        "maturity": "synthetic-validated",
        "findings": findings,
        "evidence": sorted(artifacts, key=lambda item: (item["role"], item["label"])),
        "metrics": metrics,
        "limitations": [
            "The tool statically parses a narrow input subset and never invokes LAMMPS.",
            "A local pass does not establish physical validity, equilibrium, or scientific acceptance.",
            "Current output validation is bounded to project-authored synthetic fixtures.",
            "The report is a handoff inventory and does not fabricate missing shared manifests.",
        ],
    }
    if extra:
        overlap = set(report) & set(extra)
        if overlap:
            raise ValueError("report extras cannot replace canonical fields: " + ", ".join(sorted(overlap)))
        report.update(extra)
    report["report_fingerprint"] = canonical_hash({key: value for key, value in report.items() if key != "report_fingerprint"})
    return report


def ensure_output_distinct(out: Path | None, inputs: list[Path]) -> None:
    if out is None:
        return
    output_resolved = out.resolve(strict=False)
    for input_path in inputs:
        if output_resolved == input_path.resolve(strict=False):
            raise GuardFailure("LAMMPS.IO.OUTPUT_ALIASES_INPUT", "The report output aliases an input artifact.")
        try:
            output_stat = out.lstat()
            input_stat = input_path.lstat()
        except OSError:
            continue
        if (output_stat.st_dev, output_stat.st_ino) == (input_stat.st_dev, input_stat.st_ino):
            raise GuardFailure("LAMMPS.IO.OUTPUT_ALIASES_INPUT", "The report output shares identity with an input artifact.")


def _metadata_at(directory_fd: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise GuardFailure("LAMMPS.IO.WRITE", "An output name could not be inspected safely.") from exc


def _same_inode_size(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        stat.S_ISREG(left.st_mode)
        and stat.S_ISREG(right.st_mode)
        and (left.st_dev, left.st_ino, left.st_size) == (right.st_dev, right.st_ino, right.st_size)
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


def _atomic_write_new(path: Path, payload: bytes) -> None:
    if not path.name or path.name in {".", ".."}:
        raise GuardFailure("LAMMPS.IO.WRITE", "The output filename is invalid.")
    if not _LINKAT_SUPPORTED:
        raise GuardFailure("LAMMPS.IO.NOFOLLOW_UNAVAILABLE", "The platform lacks safe hard-link publication support.", incomplete=True)
    directory_fd, _normalized_parent = _bound_directory_descriptor(path.parent)
    temporary_fd: int | None = None
    temporary_name: str | None = None
    link_succeeded = False
    installed = False
    try:
        if _metadata_at(directory_fd, path.name) is not None:
            raise GuardFailure("LAMMPS.IO.OVERWRITE", "The report path already exists.")
        nofollow = getattr(os, "O_NOFOLLOW", None)
        if nofollow is None:
            raise GuardFailure("LAMMPS.IO.NOFOLLOW_UNAVAILABLE", "The platform cannot create a no-follow staging file.", incomplete=True)
        for _attempt in range(32):
            candidate = f".{path.name}.candidate-{secrets.token_hex(12)}.tmp"
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
            raise GuardFailure("LAMMPS.IO.WRITE", "A private output staging file could not be created.")
        offset = 0
        while offset < len(payload):
            written = os.write(temporary_fd, payload[offset:])
            if written <= 0:
                raise OSError("short output write")
            offset += written
        os.fsync(temporary_fd)
        staged_fd_metadata = os.fstat(temporary_fd)
        staged_name_metadata = _metadata_at(directory_fd, temporary_name)
        if (
            staged_name_metadata is None
            or staged_fd_metadata.st_nlink != 1
            or not _same_inode_size(staged_fd_metadata, staged_name_metadata)
            or staged_fd_metadata.st_size != len(payload)
            or not _fd_payload_matches(temporary_fd, payload)
        ):
            raise GuardFailure("LAMMPS.IO.WRITE", "The staged report identity or payload is invalid.")
        _verify_bound_directory(path.parent, directory_fd)
        if _metadata_at(directory_fd, path.name) is not None:
            raise GuardFailure("LAMMPS.IO.OVERWRITE", "The report target appeared during staging.")
        try:
            os.link(
                temporary_name,
                path.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
            link_succeeded = True
        except FileExistsError as exc:
            raise GuardFailure("LAMMPS.IO.OVERWRITE", "The report target appeared during atomic publication.") from exc
        held_after_link = os.fstat(temporary_fd)
        published_metadata = _metadata_at(directory_fd, path.name)
        source_after_link = _metadata_at(directory_fd, temporary_name)
        if (
            published_metadata is None
            or source_after_link is None
            or held_after_link.st_nlink != 2
            or published_metadata.st_nlink != 2
            or source_after_link.st_nlink != 2
            or not _same_inode_size(published_metadata, held_after_link)
            or not _same_inode_size(source_after_link, held_after_link)
            or not _fd_payload_matches(temporary_fd, payload)
        ):
            if published_metadata is not None and source_after_link is not None and _same_inode_size(published_metadata, source_after_link):
                _unlink_if_identity(directory_fd, path.name, published_metadata)
            raise GuardFailure("LAMMPS.IO.WRITE", "The staging name was substituted during publication.")
        os.fsync(directory_fd)
        os.unlink(temporary_name, dir_fd=directory_fd)
        temporary_name = None
        final_target = _metadata_at(directory_fd, path.name)
        held_final = os.fstat(temporary_fd)
        if (
            final_target is None
            or final_target.st_nlink != 1
            or held_final.st_nlink != 1
            or not _same_inode_size(final_target, held_final)
            or not _fd_payload_matches(temporary_fd, payload)
        ):
            raise GuardFailure("LAMMPS.IO.WRITE", "The published report changed after installation.")
        _verify_bound_directory(path.parent, directory_fd)
        os.fsync(directory_fd)
        installed = True
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("LAMMPS.IO.WRITE", "The report could not be written atomically.") from exc
    finally:
        if link_succeeded and not installed and temporary_fd is not None:
            try:
                held = os.fstat(temporary_fd)
                target = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
                if _same_inode_size(target, held) and _fd_payload_matches(temporary_fd, payload):
                    _unlink_if_identity(directory_fd, path.name, target)
            except OSError:
                pass
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except OSError:
                pass
        if temporary_fd is not None:
            try:
                os.close(temporary_fd)
            except OSError:
                pass
        os.close(directory_fd)


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
        findings.append(finding("LAMMPS.PLAN.MISSING_FIELD", "claim_definition", "Required fields are missing: " + ", ".join(missing), "Supply every required field without guessing."))
        return findings
    if not safe_id(request["case_id"]) or not safe_id(request["protocol_id"]):
        findings.append(finding("LAMMPS.PLAN.INVALID_ID", "privacy", "Case and protocol IDs must be privacy-safe.", "Use anonymous identifiers."))
    if request["lammps_version"] != PINNED_VERSION:
        findings.append(finding("LAMMPS.VERSION.UNSUPPORTED", "version_build", "Only release 4Jul2026 has this candidate's documentary profile.", "Pin the exact release or add official version coverage.", kind="incomplete"))
    if request["task"] != "nve" or request["ensemble"] != "nve":
        findings.append(finding("LAMMPS.PLAN.UNSUPPORTED_TASK", "ensemble", "Only the atomic LJ NVE core is parser-supported.", "Keep other tasks design-only until separately implemented.", kind="incomplete"))
    if not isinstance(request["objective"], str) or not request["objective"].strip() or not isinstance(request["claim_target"], str) or not request["claim_target"].strip():
        findings.append(finding("LAMMPS.PLAN.CLAIM", "claim_definition", "Objective and bounded claim target must be nonempty.", "State both explicitly."))
    if request["artifact_class"] not in {"synthetic", "user-supplied"}:
        findings.append(finding("LAMMPS.PLAN.ARTIFACT_CLASS", "claim_definition", "Artifact class must be synthetic or user-supplied.", "Declare evidence class."))
    if request["units_style"] != "lj" or request["unit_map"] != LJ_UNIT_MAP:
        findings.append(finding("LAMMPS.UNITS.MISMATCH", "units", "Supported coverage requires exact reduced LJ unit semantics.", "Use units lj and the explicit reduced map."))
    if request["boundary"] != ["p", "p", "p"] or request["atom_style"] != "atomic":
        findings.append(finding("LAMMPS.BOUNDARY.UNSUPPORTED", "boundary_topology", "Supported coverage requires atomic style and fully periodic orthogonal intent.", "Keep other combinations design-only.", kind="incomplete"))
    if not positive(request["timestep"]):
        findings.append(finding("LAMMPS.PLAN.TIMESTEP", "numerical_discretization", "Time step must be finite and positive in LJ time units.", "Declare a tested value."))
    for field in ("topology", "interaction_model"):
        value = request[field]
        needed = ("identity", "source_url", "license_status")
        if not isinstance(value, dict) or not all(isinstance(value.get(key), str) and value[key].strip() for key in needed):
            findings.append(finding("LAMMPS.MODEL.PROVENANCE", "model_provenance", f"{field} provenance is incomplete.", "Provide identity, source, and license status."))
        elif value["license_status"] != "verified":
            findings.append(finding("LAMMPS.LICENSE.UNRESOLVED", "model_provenance", f"{field} license is unresolved.", "Resolve use and redistribution rights."))
    model = request["interaction_model"]
    if isinstance(model, dict) and (model.get("pair_style") != "lj/cut" or model.get("shifted") is not False or model.get("tail_correction") is not False or model.get("mixing_rule") != "not-applicable-single-type"):
        findings.append(finding("LAMMPS.MODEL.UNSUPPORTED", "model_provenance", "The supported analytic model declaration is not exact.", "Use the single-type lj/cut fixture semantics or add a profile.", kind="incomplete"))
    restart = request["restart"]
    if not isinstance(restart, dict) or restart.get("mode") not in {"new", "binary-continuation"}:
        findings.append(finding("LAMMPS.RESTART.LINEAGE", "restart_lineage", "Restart mode is missing or invalid.", "Declare new or binary-continuation."))
    elif restart["mode"] == "binary-continuation":
        valid = safe_id(restart.get("parent_run_id")) and isinstance(restart.get("restart_sha256"), str) and bool(re.fullmatch(r"[a-f0-9]{64}", restart["restart_sha256"])) and restart.get("parent_lammps_version") == request["lammps_version"] and isinstance(restart.get("parent_executable_sha256"), str) and bool(re.fullmatch(r"[a-f0-9]{64}", restart["parent_executable_sha256"])) and restart.get("exact_continuation_claim") is False
        if not valid:
            findings.append(finding("LAMMPS.RESTART.LINEAGE", "restart_lineage", "Binary continuation lacks parent, hashes, version, or honest exactness declaration.", "Bind exact parent state and set exact_continuation_claim=false."))
    seeds = request["seeds"]
    if not isinstance(seeds, list) or len(seeds) != 1 or not isinstance(seeds[0], dict) or seeds[0].get("role") != "velocity_create" or not isinstance(seeds[0].get("value"), int) or isinstance(seeds[0].get("value"), bool) or seeds[0]["value"] <= 0:
        findings.append(finding("LAMMPS.SEED.POLICY", "initial_state", "The new-run core requires one explicit velocity_create seed.", "Declare the exact positive seed."))
    if isinstance(restart, dict) and restart.get("mode") == "binary-continuation" and seeds:
        findings.append(finding("LAMMPS.SEED.POLICY", "restart_lineage", "Binary continuation must not recreate velocities.", "Use no new velocity seed for continuation."))
    total_steps = 0
    for phase_name in ("equilibration", "production"):
        phase = request[phase_name]
        if not isinstance(phase, dict) or not isinstance(phase.get("steps"), int) or isinstance(phase.get("steps"), bool) or phase["steps"] < 0 or not isinstance(phase.get("acceptance_checks"), list) or not phase["acceptance_checks"]:
            findings.append(finding("LAMMPS.PLAN.PHASE", "equilibration_production", f"{phase_name} must declare steps and acceptance checks.", "Predeclare both phases."))
        else:
            total_steps += phase["steps"]
    if total_steps <= 0:
        findings.append(finding("LAMMPS.PLAN.PHASE", "equilibration_production", "Total steps must be positive.", "Declare production steps."))
    observables = request["observables"]
    if not isinstance(observables, list) or not observables:
        findings.append(finding("LAMMPS.PLAN.OBSERVABLE", "statistics", "At least one observable is required.", "Declare estimator and uncertainty rule."))
    else:
        names: set[str] = set()
        for item in observables:
            valid = isinstance(item, dict) and item.get("name") in OBSERVABLE_COLUMNS and item.get("name") not in names and isinstance(item.get("unit"), str) and item.get("estimator") == "mean" and item.get("uncertainty_method") == "block-mean" and isinstance(item.get("minimum_effective_samples"), int) and item["minimum_effective_samples"] >= 2 and positive(item.get("max_standard_error"))
            if not valid:
                findings.append(finding("LAMMPS.PLAN.OBSERVABLE", "statistics", "Observable definition is unsupported, duplicate, or incomplete.", "Use a supported thermo column and explicit bounds."))
                break
            names.add(item["name"])
    output = request["output"]
    positive_keys = ("thermo_interval_steps", "dump_interval_steps", "restart_interval_steps", "expected_trajectory_frames")
    expected_columns = ["Step", "Temp", "PotEng", "KinEng", "TotEng", "Press"]
    if not isinstance(output, dict) or not all(isinstance(output.get(key), int) and not isinstance(output.get(key), bool) and output[key] > 0 for key in positive_keys) or output.get("thermo_columns") != expected_columns or not isinstance(output.get("trajectory_filename"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", output["trajectory_filename"]):
        findings.append(finding("LAMMPS.PLAN.OUTPUT", "output_cadence", "Output cadence, thermo schema, or filename is invalid.", "Use the deterministic custom-output profile."))
    elif total_steps > 0 and total_steps // output["dump_interval_steps"] + 1 != output["expected_trajectory_frames"]:
        findings.append(finding("LAMMPS.PLAN.OUTPUT", "output_cadence", "Expected frames do not include the initial dump plus planned cadence.", "Correct frame expectation."))
    build = request["build_requirements"]
    if not isinstance(build, dict) or build.get("pair_styles") != ["lj/cut"] or build.get("fix_styles") != ["nve"] or build.get("atom_styles") != ["atomic"] or build.get("dump_styles") != ["custom"]:
        findings.append(finding("LAMMPS.BUILD.REQUIREMENTS", "version_build", "Build style requirements are missing or ambiguous.", "Declare exact required styles."))
    auth = request["authorization"]
    if not isinstance(auth, dict) or auth.get("execute_external_software") is not False:
        findings.append(finding("LAMMPS.EXECUTION.NOT_AUTHORIZED", "execution_boundary", "This candidate accepts only explicit no-execution plans.", "Use a separately authorized execution route later."))
    return findings


def command_plan(path: Path) -> dict[str, Any]:
    request = load_json(path)
    findings = validate_plan(request)
    return make_report("plan", findings, [evidence(path, "plan-request")], {"required_gate_count": 15, "supported_task_count": 1}, extra={"plan_request_sha256": sha256_file(path), "plan": request})


def in_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def parse_script(root_input: Path) -> tuple[list[tuple[str, int, list[str]]], list[Path]]:
    root = root_input.parent.resolve()
    commands: list[tuple[str, int, list[str]]] = []
    ordered_files: list[Path] = []
    seen: set[Path] = set()

    def visit(path: Path, stack: tuple[Path, ...]) -> None:
        resolved = path.resolve()
        if not in_root(resolved, root):
            raise GuardFailure("LAMMPS.INCLUDE.ESCAPE", "An include escapes the declared input root.")
        if resolved in stack:
            raise GuardFailure("LAMMPS.INCLUDE.CYCLE", "Include cycle detected.")
        if resolved in seen:
            raise GuardFailure("LAMMPS.INCLUDE.DUPLICATE", "The same include is reached more than once, creating ambiguous execution order.")
        read_text(resolved)
        seen.add(resolved)
        ordered_files.append(resolved)
        for line_number, raw in enumerate(read_text(resolved).splitlines(), 1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.endswith("&") or "$" in stripped or "`" in stripped or ";" in stripped:
                raise GuardFailure("LAMMPS.SCRIPT.DYNAMIC", f"{resolved.name}:{line_number} uses unsupported expansion or continuation.", incomplete=True)
            try:
                tokens = shlex.split(raw, comments=True, posix=True)
            except ValueError as exc:
                raise GuardFailure("LAMMPS.SCRIPT.GRAMMAR", f"{resolved.name}:{line_number} cannot be tokenized.") from exc
            if not tokens:
                continue
            tokens[0] = tokens[0].lower()
            if tokens[0] == "include":
                if len(tokens) != 2 or not re.fullmatch(r"[A-Za-z0-9.][A-Za-z0-9._/-]{0,255}", tokens[1]):
                    raise GuardFailure("LAMMPS.INCLUDE.DYNAMIC", "Only one literal relative include path is supported.", incomplete=True)
                target = resolved.parent / tokens[1]
                visit(target, stack + (resolved,))
            else:
                commands.append((resolved.name, line_number, tokens))

    visit(root_input, ())
    return commands, ordered_files


def parse_data(text: str) -> dict[str, Any]:
    atom_count = type_count = None
    bounds: dict[str, tuple[float, float]] = {}
    lines = text.splitlines()
    for line in lines:
        if match := re.fullmatch(r"\s*(\d+)\s+atoms\s*", line):
            atom_count = int(match.group(1))
        elif match := re.fullmatch(r"\s*(\d+)\s+atom types\s*", line):
            type_count = int(match.group(1))
        elif match := re.fullmatch(r"\s*([^\s]+)\s+([^\s]+)\s+([xyz])lo\s+\3hi\s*", line):
            try:
                low, high = float(match.group(1)), float(match.group(2))
            except ValueError as exc:
                raise GuardFailure("LAMMPS.TOPOLOGY.DATA", "Box bounds are nonnumeric.") from exc
            if not math.isfinite(low) or not math.isfinite(high) or high <= low:
                raise GuardFailure("LAMMPS.TOPOLOGY.DATA", "Box bounds are invalid.")
            bounds[match.group(3)] = (low, high)
    if not isinstance(atom_count, int) or atom_count <= 0 or not isinstance(type_count, int) or type_count <= 0 or set(bounds) != {"x", "y", "z"}:
        raise GuardFailure("LAMMPS.TOPOLOGY.DATA", "Data header lacks positive counts or orthogonal bounds.")
    atoms_index = None
    for index, line in enumerate(lines):
        if re.fullmatch(r"\s*Atoms\s+#\s+atomic\s*", line):
            atoms_index = index
            break
        if re.match(r"\s*Atoms\b", line):
            raise GuardFailure("LAMMPS.TOPOLOGY.ATOM_STYLE", "Atoms section is not explicitly marked atomic.", incomplete=True)
    if atoms_index is None:
        raise GuardFailure("LAMMPS.TOPOLOGY.DATA", "Atoms # atomic section is missing.")
    rows: list[list[str]] = []
    for line in lines[atoms_index + 1:]:
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            continue
        if re.match(r"[A-Za-z]", stripped):
            break
        tokens = stripped.split()
        if len(tokens) != 5:
            raise GuardFailure("LAMMPS.TOPOLOGY.DATA", "Atomic data rows require id type x y z.")
        rows.append(tokens)
    if len(rows) != atom_count:
        raise GuardFailure("LAMMPS.TOPOLOGY.DATA", "Atoms row count differs from the header.")
    site_types: dict[int, int] = {}
    for row in rows:
        try:
            site_id, atom_type = int(row[0]), int(row[1])
            coords = [float(value) for value in row[2:]]
        except ValueError as exc:
            raise GuardFailure("LAMMPS.TOPOLOGY.DATA", "Atom row contains invalid numeric data.") from exc
        if site_id in site_types or site_id <= 0 or atom_type <= 0 or atom_type > type_count or not all(math.isfinite(value) for value in coords):
            raise GuardFailure("LAMMPS.TOPOLOGY.DATA", "Atom IDs/types/coordinates are invalid or duplicate.")
        site_types[site_id] = atom_type
    if set(site_types) != set(range(1, atom_count + 1)):
        raise GuardFailure("LAMMPS.TOPOLOGY.DATA", "This core requires contiguous atom IDs 1..N.")
    return {"atom_count": atom_count, "type_count": type_count, "bounds": bounds, "site_types": site_types}


def check_build(build: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if build.get("lammps_version") != PINNED_VERSION or build.get("release_banner") != PINNED_BANNER:
        findings.append(finding("LAMMPS.BUILD.VERSION", "version_build", "Build manifest version/banner does not match the plan.", "Capture the exact executable identity."))
    if not isinstance(build.get("executable_sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", build["executable_sha256"]):
        findings.append(finding("LAMMPS.BUILD.IDENTITY", "version_build", "Executable SHA-256 is missing.", "Record exact executable hash."))
    styles = build.get("styles")
    requirements = plan["build_requirements"]
    if not isinstance(styles, dict):
        findings.append(finding("LAMMPS.BUILD.STYLES", "version_build", "Build style inventory is missing.", "Capture configuration/style evidence."))
    else:
        mapping = {"pair_styles": "pair", "fix_styles": "fix", "atom_styles": "atom", "dump_styles": "dump"}
        for request_key, build_key in mapping.items():
            available = styles.get(build_key)
            if not isinstance(available, list) or not set(requirements[request_key]).issubset(set(available)):
                findings.append(finding("LAMMPS.BUILD.STYLES", "version_build", f"Required {build_key} style is not proven available.", "Use a build manifest from the exact executable."))
    if build.get("license_spdx") != "GPL-2.0-only" or not isinstance(build.get("source_url"), str):
        findings.append(finding("LAMMPS.LICENSE.UNRESOLVED", "license", "Build source or GPL-2.0 license declaration is unresolved.", "Resolve engine provenance."))
    return findings


def check_provenance(provenance: dict[str, Any], paths: list[Path]) -> list[dict[str, str]]:
    entries = provenance.get("artifacts")
    if not isinstance(entries, list):
        return [finding("LAMMPS.MODEL.PROVENANCE", "model_provenance", "Provenance artifact list is missing.", "Declare exact closure.")]
    by_label: dict[str, dict[str, Any]] = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("label"), str) or item["label"] in by_label:
            return [finding("LAMMPS.MODEL.PROVENANCE", "model_provenance", "Provenance entries are malformed or duplicate.", "Use one entry per basename.")]
        by_label[item["label"]] = item
    findings: list[dict[str, str]] = []
    expected_labels = {path.name for path in paths}
    for path in paths:
        item = by_label.get(path.name)
        if not item or item.get("sha256") != sha256_file(path):
            findings.append(finding("LAMMPS.MODEL.PROVENANCE", "model_provenance", f"Provenance does not hash-bind {path.name}.", "Record exact SHA-256."))
        elif not isinstance(item.get("source_url"), str) or not item["source_url"].strip() or item.get("license_status") != "verified":
            findings.append(finding("LAMMPS.LICENSE.UNRESOLVED", "model_provenance", f"Source or license unresolved for {path.name}.", "Resolve independent artifact terms."))
    if set(by_label) != expected_labels:
        findings.append(finding("LAMMPS.MODEL.PROVENANCE", "model_provenance", "Provenance labels do not exactly match the input/data/include closure.", "Remove unbound records and add missing ones."))
    return findings


def singleton(commands: list[tuple[str, int, list[str]]], name: str) -> list[str] | None:
    values = [tokens for _, _, tokens in commands if tokens[0] == name]
    if len(values) == 1:
        return values[0]
    return None


def command_audit_input(plan_path: Path, input_path: Path, data_path: Path, build_path: Path, provenance_path: Path, restart_path: Path | None) -> dict[str, Any]:
    plan_report, plan_raw_sha256 = load_verified_upstream(plan_path, "plan")
    plan = plan_report["plan"]
    commands, closure = parse_script(input_path)
    findings: list[dict[str, str]] = []
    command_names = [tokens[0] for _, _, tokens in commands]
    blocked = sorted(set(command_names) & BLOCKED_COMMANDS)
    if blocked:
        findings.append(finding("LAMMPS.SCRIPT.UNSAFE_COMMAND", "script_safety", "Executable/dynamic commands are blocked: " + ", ".join(blocked), "Remove them; this candidate never authorizes code execution."))
    unknown = sorted(set(command_names) - ALLOWED_COMMANDS - BLOCKED_COMMANDS)
    if unknown:
        findings.append(finding("LAMMPS.SCRIPT.UNSUPPORTED_COMMAND", "script_safety", "Unsupported commands: " + ", ".join(unknown), "Add official coverage and adversarial tests.", kind="incomplete"))
    for name in ("units", "atom_style", "boundary", "timestep", "thermo", "thermo_style", "thermo_modify", "pair_style", "run"):
        if singleton(commands, name) is None:
            findings.append(finding("LAMMPS.SCRIPT.SINGLETON", "input_grammar", f"Exactly one {name} command is required.", "Remove ambiguity and declare it once."))
    units = singleton(commands, "units")
    atom_style = singleton(commands, "atom_style")
    boundary = singleton(commands, "boundary")
    if units != ["units", plan["units_style"]]:
        findings.append(finding("LAMMPS.UNITS.MISMATCH", "units", "Input units do not match the plan.", "Set units before reading topology/model data."))
    if atom_style != ["atom_style", plan["atom_style"]]:
        findings.append(finding("LAMMPS.TOPOLOGY.ATOM_STYLE", "boundary_topology", "atom_style does not match the plan.", "Use the planned style before read_data."))
    if boundary != ["boundary"] + plan["boundary"]:
        findings.append(finding("LAMMPS.BOUNDARY.MISMATCH", "boundary_topology", "boundary does not match the plan.", "Declare all axes consistently."))
    positions = {name: command_names.index(name) for name in ("units", "atom_style", "boundary") if name in command_names}
    read_positions = [index for index, name in enumerate(command_names) if name in {"read_data", "read_restart"}]
    if read_positions and any(position > read_positions[0] for position in positions.values()):
        findings.append(finding("LAMMPS.SCRIPT.ORDER", "input_grammar", "units, atom_style, or boundary appears after topology read.", "Set them before read_data/read_restart."))
    topology = parse_data(read_text(data_path))
    read_data_commands = [tokens for _, _, tokens in commands if tokens[0] == "read_data"]
    read_restart_commands = [tokens for _, _, tokens in commands if tokens[0] == "read_restart"]
    if plan["restart"]["mode"] == "new":
        if len(read_data_commands) != 1 or read_data_commands[0] != ["read_data", data_path.name] or read_restart_commands:
            findings.append(finding("LAMMPS.TOPOLOGY.READ", "boundary_topology", "New-run core requires one basename-bound read_data and no read_restart.", "Bind the audited data file."))
    else:
        if len(read_restart_commands) != 1 or restart_path is None or read_restart_commands[0] != ["read_restart", restart_path.name] or sha256_file(restart_path) != plan["restart"]["restart_sha256"] or read_data_commands:
            findings.append(finding("LAMMPS.RESTART.LINEAGE", "restart_lineage", "Binary restart command/file/hash does not match the plan.", "Bind exact parent restart evidence."))
        findings.append(finding("LAMMPS.RESTART.BINARY_UNSUPPORTED", "restart_lineage", "Binary restart contents and retained state are not parsed by this offline core.", "Use a version/build-specific authorized adapter.", kind="incomplete"))
    pair_style = singleton(commands, "pair_style")
    cutoff = math.nan
    if pair_style and len(pair_style) == 3 and pair_style[1] == "lj/cut":
        try:
            cutoff = float(pair_style[2])
        except ValueError:
            cutoff = math.nan
    if not math.isfinite(cutoff) or cutoff <= 0:
        findings.append(finding("LAMMPS.MODEL.PAIR_STYLE", "model_provenance", "pair_style lj/cut needs one finite positive cutoff.", "Declare the audited cutoff."))
    pair_coeffs = [tokens for _, _, tokens in commands if tokens[0] == "pair_coeff"]
    if len(pair_coeffs) != 1 or len(pair_coeffs[0]) != 6 or pair_coeffs[0][1:3] != ["*", "*"]:
        findings.append(finding("LAMMPS.MODEL.PAIR_COEFF", "model_provenance", "Single-type core requires one explicit pair_coeff * * epsilon sigma cutoff.", "Declare all numeric coefficients."))
    else:
        try:
            coefficients = [float(value) for value in pair_coeffs[0][3:]]
        except ValueError:
            coefficients = []
        if len(coefficients) != 3 or not all(math.isfinite(value) and value > 0 for value in coefficients) or (math.isfinite(cutoff) and not math.isclose(coefficients[2], cutoff, rel_tol=0.0, abs_tol=1.0e-12)):
            findings.append(finding("LAMMPS.MODEL.PAIR_COEFF", "model_provenance", "Pair coefficients are nonpositive, nonnumeric, or cutoff-mismatched.", "Use finite explicit LJ parameters."))
    if topology["type_count"] != 1:
        findings.append(finding("LAMMPS.MODEL.TYPE_COUNT", "model_provenance", "Supported LJ core requires exactly one atom type.", "Add full coefficient/mixing coverage for multiple types.", kind="incomplete"))
    box_lengths = [topology["bounds"][axis][1] - topology["bounds"][axis][0] for axis in "xyz"]
    if math.isfinite(cutoff) and any(axis == "p" and length <= 2.0 * cutoff for axis, length in zip(plan["boundary"], box_lengths)):
        findings.append(finding("LAMMPS.MODEL.MINIMUM_IMAGE", "boundary_topology", "A periodic box length is not greater than twice the pair cutoff.", "Enlarge the box or justify a different neighbor model."))
    fixes = [tokens for _, _, tokens in commands if tokens[0] == "fix"]
    integrating = [tokens for tokens in fixes if len(tokens) >= 4 and tokens[3] in {"nve", "nvt", "npt", "nph"}]
    if len(integrating) != 1 or integrating[0][1:4] != ["integrate", "all", "nve"]:
        findings.append(finding("LAMMPS.INTEGRATOR.MULTIPLE_OR_MISSING", "ensemble", "Exactly one fix integrate all nve is required.", "Avoid missing or double integration."))
    if any(len(tokens) < 4 or tokens[3] not in {"nve"} for tokens in fixes):
        findings.append(finding("LAMMPS.INTEGRATOR.UNSUPPORTED_FIX", "ensemble", "An unsupported fix is present in the narrow NVE core.", "Add a method-specific profile before use.", kind="incomplete"))
    velocity = singleton(commands, "velocity")
    if plan["restart"]["mode"] == "new":
        valid_velocity = velocity is not None and len(velocity) >= 6 and velocity[1:3] == ["all", "create"]
        if valid_velocity:
            try:
                temperature = float(velocity[3])
                seed = int(velocity[4])
            except ValueError:
                valid_velocity = False
            else:
                valid_velocity = temperature > 0 and math.isfinite(temperature) and seed == plan["seeds"][0]["value"]
        if not valid_velocity:
            findings.append(finding("LAMMPS.SEED.POLICY", "initial_state", "velocity all create does not bind a positive temperature and planned seed.", "Use the explicit seed once."))
    elif velocity is not None:
        findings.append(finding("LAMMPS.SEED.POLICY", "restart_lineage", "Binary continuation must not recreate velocities.", "Remove velocity create."))
    timestep = singleton(commands, "timestep")
    try:
        observed_timestep = float(timestep[1]) if timestep and len(timestep) == 2 else math.nan
    except ValueError:
        observed_timestep = math.nan
    if not math.isfinite(observed_timestep) or not math.isclose(observed_timestep, float(plan["timestep"]), rel_tol=0.0, abs_tol=1.0e-12):
        findings.append(finding("LAMMPS.PLAN.TIMESTEP", "numerical_discretization", "Input timestep differs from the plan.", "Use the planned LJ-time value."))
    thermo = singleton(commands, "thermo")
    thermo_style = singleton(commands, "thermo_style")
    thermo_modify = singleton(commands, "thermo_modify")
    expected_columns_lower = ["step", "temp", "pe", "ke", "etotal", "press"]
    try:
        thermo_interval = int(thermo[1]) if thermo and len(thermo) == 2 else -1
    except ValueError:
        thermo_interval = -1
    if thermo_interval != plan["output"]["thermo_interval_steps"] or not thermo_style or thermo_style[:2] != ["thermo_style", "custom"] or thermo_style[2:] != expected_columns_lower:
        findings.append(finding("LAMMPS.OUTPUT.THERMO_CONFIG", "output_cadence", "Thermo cadence or custom schema differs from the plan.", "Use the exact planned columns."))
    if not thermo_modify or "lost" not in thermo_modify or thermo_modify[thermo_modify.index("lost") + 1:thermo_modify.index("lost") + 2] != ["error"]:
        findings.append(finding("LAMMPS.OUTPUT.LOST_POLICY", "numerical_stability", "thermo_modify lost error is required.", "Make atom loss fatal."))
    dumps = [tokens for _, _, tokens in commands if tokens[0] == "dump"]
    if len(dumps) != 1:
        findings.append(finding("LAMMPS.TRAJECTORY.CONFIG", "trajectory_integrity", "Exactly one custom dump is required.", "Use the deterministic trajectory profile."))
        dump_interval = -1
    else:
        dump = dumps[0]
        try:
            dump_interval = int(dump[4]) if len(dump) >= 7 else -1
        except ValueError:
            dump_interval = -1
        expected_prefix = ["dump", "traj", "all", "custom", str(plan["output"]["dump_interval_steps"]), plan["output"]["trajectory_filename"]]
        if dump[:6] != expected_prefix or dump[6:] != ["id", "type", "x", "y", "z", "ix", "iy", "iz"]:
            findings.append(finding("LAMMPS.TRAJECTORY.CONFIG", "trajectory_integrity", "Custom dump columns/cadence/name differ from the plan.", "Include stable IDs, wrapped positions, and image flags."))
    restart = singleton(commands, "restart")
    try:
        restart_interval = int(restart[1]) if restart and len(restart) == 3 else -1
    except ValueError:
        restart_interval = -1
    if restart_interval != plan["output"]["restart_interval_steps"] or restart is None or restart[2] != "restart.*":
        findings.append(finding("LAMMPS.RESTART.CADENCE", "restart_lineage", "Restart cadence or safe pattern differs from the plan.", "Use a deterministic in-root restart pattern."))
    run = singleton(commands, "run")
    try:
        run_steps = int(run[1]) if run and len(run) == 2 else -1
    except ValueError:
        run_steps = -1
    planned_steps = plan["equilibration"]["steps"] + plan["production"]["steps"]
    if run_steps != planned_steps:
        findings.append(finding("LAMMPS.PLAN.STEPS", "equilibration_production", "run steps differ from the plan or use dynamic syntax.", "Use one positive literal step count."))
    if run and any(token.lower() == "every" for token in run):
        findings.append(finding("LAMMPS.SCRIPT.DYNAMIC_RUN", "script_safety", "run every is executable dynamic control flow.", "Remove it from the offline supported core."))
    build = load_json(build_path)
    findings.extend(check_build(build, plan))
    provenance = load_json(provenance_path)
    provenance_paths = closure + [data_path]
    findings.extend(check_provenance(provenance, provenance_paths))
    expected_thermo_steps = list(range(0, planned_steps + 1, plan["output"]["thermo_interval_steps"]))
    if expected_thermo_steps[-1] != planned_steps:
        expected_thermo_steps.append(planned_steps)
    expected_dump_steps = list(range(0, planned_steps + 1, plan["output"]["dump_interval_steps"]))
    if expected_dump_steps[-1] != planned_steps:
        expected_dump_steps.append(planned_steps)
    if len(expected_dump_steps) != plan["output"]["expected_trajectory_frames"]:
        findings.append(finding("LAMMPS.PLAN.OUTPUT", "output_cadence", "Input-derived custom dump frame count differs from plan.", "Align run length and cadence."))
    artifact_paths = [plan_path, input_path, data_path, build_path, provenance_path] + [path for path in closure if path.resolve() != input_path.resolve()]
    if restart_path is not None:
        artifact_paths.append(restart_path)
    roles = ["plan-report", "root-input", "data-topology", "build-manifest", "provenance"] + ["literal-include"] * (len(closure) - 1) + (["binary-restart"] if restart_path is not None else [])
    return make_report(
        "audit-input", findings, [evidence(path, role) for path, role in zip(artifact_paths, roles)],
        {"commands": len(commands), "include_files": len(closure), "atoms": topology["atom_count"], "atom_types": topology["type_count"]},
        extra={
            "upstream": {"plan_report_raw_sha256": plan_raw_sha256},
            "input": {
                "atom_count": topology["atom_count"], "site_types": {str(key): value for key, value in sorted(topology["site_types"].items())},
                "bounds": {axis: list(topology["bounds"][axis]) for axis in "xyz"}, "boundary": plan["boundary"],
                "pair_style": "lj/cut", "pair_cutoff": cutoff, "run_steps": run_steps,
                "expected_thermo_steps": expected_thermo_steps, "expected_dump_steps": expected_dump_steps,
                "build_executable_sha256": build.get("executable_sha256"),
                "input_closure_hashes": {path.name: sha256_file(path) for path in closure + [data_path]},
            },
        },
    )


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
    for lag in range(1, min(count, count // 2 + 1)):
        covariance = sum(centered[index] * centered[index + lag] for index in range(count - lag)) / (count - lag)
        correlation = covariance / variance
        if correlation <= 0:
            break
        tau += 2.0 * correlation
    return max(1.0, min(float(count), count / tau))


def block_error(values: list[float]) -> tuple[float, int]:
    if len(values) < 2:
        return math.inf, 0
    size = max(1, int(math.sqrt(len(values))))
    count = len(values) // size
    if count < 2:
        return math.inf, count
    means = [statistics.fmean(values[index * size:(index + 1) * size]) for index in range(count)]
    return statistics.stdev(means) / math.sqrt(count), count


def parse_thermo(log: str, columns: list[str]) -> list[dict[str, float]]:
    lines = log.splitlines()
    header_indices = [index for index, line in enumerate(lines) if line.split() == columns]
    if len(header_indices) != 1:
        raise GuardFailure("LAMMPS.OUTPUT.THERMO_TABLE", "Expected exactly one planned thermo header.")
    rows: list[dict[str, float]] = []
    for line in lines[header_indices[0] + 1:]:
        if line.startswith("Loop time"):
            break
        tokens = line.split()
        if not tokens:
            continue
        if len(tokens) != len(columns):
            raise GuardFailure("LAMMPS.OUTPUT.THERMO_TABLE", "Thermo table contains an unexpected row.")
        try:
            values = [float(token) for token in tokens]
        except ValueError as exc:
            raise GuardFailure("LAMMPS.OUTPUT.THERMO_TABLE", "Thermo row is nonnumeric.") from exc
        if not all(math.isfinite(value) for value in values):
            raise GuardFailure("LAMMPS.OUTPUT.NONFINITE", "Thermo table contains a non-finite value.")
        rows.append(dict(zip(columns, values)))
    return rows


def command_audit_output(plan_path: Path, input_path: Path, log_path: Path) -> dict[str, Any]:
    plan_report, plan_raw_sha256 = load_verified_upstream(plan_path, "plan")
    input_report, input_raw_sha256 = load_verified_upstream(input_path, "audit-input")
    if input_report["upstream"]["plan_report_raw_sha256"] != plan_raw_sha256:
        raise GuardFailure("LAMMPS.UPSTREAM.LINEAGE_MISMATCH", "Input audit is not bound to the exact raw plan report.")
    plan = plan_report["plan"]
    log = read_text(log_path)
    findings: list[dict[str, str]] = []
    version_count = len(re.findall(r"^LAMMPS \(4 Jul 2026\)$", log, flags=re.MULTILINE))
    if version_count != 1:
        findings.append(finding("LAMMPS.OUTPUT.VERSION", "technical_completion", "Exact release banner is missing or duplicated.", "Provide one complete 4Jul2026 log segment."))
    adverse = re.findall(r"\b(?:ERROR|WARNING|nan|inf|lost atoms|segmentation fault|shell command|python command)\b", log, flags=re.IGNORECASE)
    if adverse:
        findings.append(finding("LAMMPS.OUTPUT.ADVERSE_MARKER", "numerical_stability", "Log contains an error, warning, lost-atom, non-finite, or unsafe marker.", "Diagnose and rerun without suppression."))
    pattern = re.compile(r"^Loop time of [0-9]+(?:\.[0-9]+)? on (\d+) procs for (\d+) steps with (\d+) atoms$", flags=re.MULTILINE)
    loop_matches = pattern.findall(log)
    expected_steps = input_report["input"]["run_steps"]
    expected_atoms = input_report["input"]["atom_count"]
    if len(loop_matches) != 1 or int(loop_matches[0][1]) != expected_steps or int(loop_matches[0][2]) != expected_atoms:
        findings.append(finding("LAMMPS.OUTPUT.COMPLETION", "technical_completion", "Loop-time completion marker is absent, duplicated, or count-mismatched.", "Provide the exact non-concatenated log."))
    try:
        rows = parse_thermo(log, plan["output"]["thermo_columns"])
    except GuardFailure as exc:
        findings.append(finding(exc.code, "observable_evidence", exc.message, "Provide one exact planned thermo table."))
        rows = []
    observed_steps = [int(row["Step"]) for row in rows]
    if observed_steps != input_report["input"]["expected_thermo_steps"]:
        findings.append(finding("LAMMPS.OUTPUT.STEPS", "observable_evidence", "Thermo timesteps differ from the input-derived schedule.", "Isolate the exact segment and cadence."))
    production_rows = [row for row in rows if row["Step"] > plan["equilibration"]["steps"]]
    stats: dict[str, Any] = {}
    for observable in plan["observables"]:
        name = observable["name"]
        column = OBSERVABLE_COLUMNS[name]
        values = [row[column] for row in production_rows]
        if len(values) < 2:
            findings.append(finding("LAMMPS.STATISTICS.INSUFFICIENT", "statistics", f"{name} has fewer than two production samples.", "Increase predeclared production sampling."))
            continue
        ess = autocorrelation_ess(values)
        standard_error, blocks = block_error(values)
        stats[name] = {"samples": len(values), "mean": statistics.fmean(values), "effective_samples": ess, "block_count": blocks, "block_standard_error": standard_error, "unit": observable["unit"]}
        if ess < observable["minimum_effective_samples"]:
            findings.append(finding("LAMMPS.STATISTICS.LOW_ESS", "statistics", f"{name} effective sample count is too low.", "Extend or replicate the protocol."))
        if not math.isfinite(standard_error) or standard_error > observable["max_standard_error"]:
            findings.append(finding("LAMMPS.STATISTICS.UNCERTAINTY", "statistics", f"{name} block standard error exceeds its declared bound.", "Collect sufficient independent evidence."))
    return make_report(
        "audit-output", findings, [evidence(plan_path, "plan-report"), evidence(input_path, "input-audit"), evidence(log_path, "lammps-log")],
        {"version_banner_count": version_count, "loop_marker_count": len(loop_matches), "thermo_rows": len(rows), "production_rows": len(production_rows)},
        extra={
            "upstream": {
                "plan_report_raw_sha256": plan_raw_sha256,
                "input_report_raw_sha256": input_raw_sha256,
            },
            "output": {"statistics": stats, "log_sha256": sha256_file(log_path)},
        },
    )


def parse_dump(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    frames: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        if lines[index] != "ITEM: TIMESTEP" or index + 8 >= len(lines):
            raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Custom dump frame header is invalid or truncated.")
        try:
            step = int(lines[index + 1].strip())
        except ValueError as exc:
            raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Timestep is invalid.") from exc
        if lines[index + 2] != "ITEM: NUMBER OF ATOMS":
            raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "NUMBER OF ATOMS header is missing.")
        try:
            count = int(lines[index + 3].strip())
        except ValueError as exc:
            raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Atom count is invalid.") from exc
        box_header = lines[index + 4].split()
        if box_header[:3] != ["ITEM:", "BOX", "BOUNDS"] or len(box_header) != 6:
            raise GuardFailure("LAMMPS.TRAJECTORY.UNSUPPORTED_BOX", "Only orthogonal BOX BOUNDS with three flags is supported.", incomplete=True)
        bounds: list[tuple[float, float]] = []
        for offset in range(3):
            tokens = lines[index + 5 + offset].split()
            if len(tokens) != 2:
                raise GuardFailure("LAMMPS.TRAJECTORY.UNSUPPORTED_BOX", "Triclinic/general box rows are unsupported.", incomplete=True)
            try:
                low, high = float(tokens[0]), float(tokens[1])
            except ValueError as exc:
                raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Box bound is nonnumeric.") from exc
            if not math.isfinite(low) or not math.isfinite(high) or high <= low:
                raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Box bounds are invalid.")
            bounds.append((low, high))
        atoms_header = lines[index + 8].split()
        expected_header = ["ITEM:", "ATOMS", "id", "type", "x", "y", "z", "ix", "iy", "iz"]
        if atoms_header != expected_header:
            raise GuardFailure("LAMMPS.TRAJECTORY.COLUMNS", "Custom dump columns differ from id type x y z ix iy iz.", incomplete=True)
        if count <= 0 or index + 9 + count > len(lines):
            raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Frame is truncated or atom count is invalid.")
        sites: dict[int, dict[str, Any]] = {}
        for row in lines[index + 9:index + 9 + count]:
            tokens = row.split()
            if len(tokens) != 8:
                raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Atom row width is invalid.")
            try:
                site_id, atom_type = int(tokens[0]), int(tokens[1])
                coords = [float(value) for value in tokens[2:5]]
                images = [int(value) for value in tokens[5:8]]
            except ValueError as exc:
                raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Atom row numeric type is invalid.") from exc
            if site_id in sites or not all(math.isfinite(value) for value in coords):
                raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Site IDs duplicate or coordinates are non-finite.")
            sites[site_id] = {"type": atom_type, "coords": coords, "images": images}
        frames.append({"step": step, "count": count, "flags": box_header[3:], "bounds": bounds, "sites": sites})
        index += 9 + count
    if not frames:
        raise GuardFailure("LAMMPS.TRAJECTORY.GRAMMAR", "Trajectory has no frames.")
    return frames


def command_audit_trajectory(plan_path: Path, input_path: Path, output_path: Path, trajectory_path: Path) -> dict[str, Any]:
    plan_report, plan_raw_sha256 = load_verified_upstream(plan_path, "plan")
    input_report, input_raw_sha256 = load_verified_upstream(input_path, "audit-input")
    output_report, output_raw_sha256 = load_verified_upstream(output_path, "audit-output")
    if (
        input_report["upstream"]["plan_report_raw_sha256"] != plan_raw_sha256
        or output_report["upstream"]["plan_report_raw_sha256"] != plan_raw_sha256
        or output_report["upstream"]["input_report_raw_sha256"] != input_raw_sha256
    ):
        raise GuardFailure("LAMMPS.UPSTREAM.LINEAGE_MISMATCH", "Upstream reports do not bind one exact raw-byte lineage.")
    frames = parse_dump(read_text(trajectory_path))
    findings: list[dict[str, str]] = []
    expected_steps = input_report["input"]["expected_dump_steps"]
    observed_steps = [frame["step"] for frame in frames]
    if observed_steps != expected_steps:
        findings.append(finding("LAMMPS.TRAJECTORY.CADENCE", "trajectory_integrity", "Frame timesteps differ from the planned dump schedule.", "Isolate the exact segment."))
    expected_types = {int(key): value for key, value in input_report["input"]["site_types"].items()}
    expected_bounds = [tuple(input_report["input"]["bounds"][axis]) for axis in "xyz"]
    expected_flags = [axis + axis for axis in input_report["input"]["boundary"]]
    for frame in frames:
        if frame["count"] != input_report["input"]["atom_count"] or set(frame["sites"]) != set(expected_types):
            findings.append(finding("LAMMPS.TRAJECTORY.SITE_ID", "trajectory_integrity", "Atom count or stable ID set changed.", "Reject lost/added/reidentified sites."))
            break
        if any(frame["sites"][site_id]["type"] != atom_type for site_id, atom_type in expected_types.items()):
            findings.append(finding("LAMMPS.TRAJECTORY.SITE_TYPE", "trajectory_integrity", "A stable atom ID changed type.", "Verify topology and dump lineage."))
            break
        if frame["flags"] != expected_flags:
            findings.append(finding("LAMMPS.TRAJECTORY.BOUNDARY", "trajectory_integrity", "BOX BOUNDS flags differ from planned boundary.", "Reject mixed-boundary evidence."))
            break
        if any(not math.isclose(low, expected_low, rel_tol=0.0, abs_tol=1.0e-12) or not math.isclose(high, expected_high, rel_tol=0.0, abs_tol=1.0e-12) for (low, high), (expected_low, expected_high) in zip(frame["bounds"], expected_bounds)):
            findings.append(finding("LAMMPS.TRAJECTORY.CELL", "trajectory_integrity", "Orthogonal box changed in an NVE fixed-cell plan.", "Verify the correct segment and ensemble."))
            break
        for site in frame["sites"].values():
            for coordinate, (low, high) in zip(site["coords"], frame["bounds"]):
                if coordinate < low - 1.0e-10 or coordinate >= high + 1.0e-10:
                    findings.append(finding("LAMMPS.TRAJECTORY.WRAPPED_RANGE", "trajectory_integrity", "A wrapped coordinate lies outside its orthogonal bounds.", "Verify coordinate style and box semantics."))
                    break
    return make_report(
        "audit-trajectory", findings, [evidence(plan_path, "plan-report"), evidence(input_path, "input-audit"), evidence(output_path, "output-audit"), evidence(trajectory_path, "custom-dump")],
        {"frames": len(frames), "atoms_per_frame": input_report["input"]["atom_count"], "first_step": observed_steps[0] if observed_steps else None, "last_step": observed_steps[-1] if observed_steps else None},
        extra={
            "upstream": {
                "plan_report_raw_sha256": plan_raw_sha256,
                "input_report_raw_sha256": input_raw_sha256,
                "output_report_raw_sha256": output_raw_sha256,
            },
            "trajectory": {"format": "lammps-custom-text", "source_sha256": sha256_file(trajectory_path), "site_identity": "atom-id", "wrapped_coordinates": True, "image_flags": True, "orthogonal_unwrapping_reconstructable": True, "shared_contract_status": "handoff-inventory-only"},
        },
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
    audit_input.add_argument("--data", type=Path, required=True)
    audit_input.add_argument("--build-manifest", type=Path, required=True)
    audit_input.add_argument("--provenance", type=Path, required=True)
    audit_input.add_argument("--restart-file", type=Path)
    audit_input.add_argument("--out", type=Path)
    audit_output = sub.add_parser("audit-output")
    audit_output.add_argument("--plan", type=Path, required=True)
    audit_output.add_argument("--input-audit", type=Path, required=True)
    audit_output.add_argument("--log", type=Path, required=True)
    audit_output.add_argument("--out", type=Path)
    trajectory = sub.add_parser("audit-trajectory")
    trajectory.add_argument("--plan", type=Path, required=True)
    trajectory.add_argument("--input-audit", type=Path, required=True)
    trajectory.add_argument("--output-audit", type=Path, required=True)
    trajectory.add_argument("--trajectory", type=Path, required=True)
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
            report = command_audit_input(args.plan, args.input, args.data, args.build_manifest, args.provenance, args.restart_file)
        elif args.command == "audit-output":
            report = command_audit_output(args.plan, args.input_audit, args.log)
        else:
            report = command_audit_trajectory(args.plan, args.input_audit, args.output_audit, args.trajectory)
        return emit(report, args.out)
    except GuardFailure as exc:
        report = make_report(args.command, [finding(exc.code, "deterministic_audit", exc.message, "Supply safe complete evidence and retry.", kind="incomplete" if exc.incomplete else "fail")], [], {})
        return emit(report, None if exc.code == "LAMMPS.IO.OUTPUT_ALIASES_INPUT" else getattr(args, "out", None))
    except Exception:
        report = make_report(args.command, [finding("LAMMPS.INTERNAL.ERROR", "internal", "The guard encountered an internal error.", "Report a minimal nonsensitive reproducer.")], [], {})
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if getattr(args, "out", None) is None:
            sys.stdout.write(rendered)
        else:
            sys.stderr.write(rendered)
        return 4
    finally:
        _reset_snapshot_cache()


if __name__ == "__main__":
    raise SystemExit(main())
