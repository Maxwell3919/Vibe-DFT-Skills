#!/usr/bin/env python3
"""Deterministic offline planner and auditor for a conservative GROMACS MD core."""

from __future__ import annotations

import argparse
import csv
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
REPORT_AUTHENTICITY = "unsigned-candidate-output"
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_TEXT_BYTES = 16 * 1024 * 1024
EXPECTED_UNITS = {
    "length": "nm",
    "time": "ps",
    "energy": "kJ/mol",
    "pressure": "bar",
    "temperature": "K",
}
ALLOWED_MDP = {
    "integrator", "dt", "nsteps", "continuation", "gen-vel", "gen-seed",
    "gen-temp", "pbc", "tcoupl", "tc-grps", "tau-t", "ref-t", "pcoupl",
    "pcoupltype", "tau-p", "ref-p", "compressibility", "constraints",
    "constraint-algorithm", "cutoff-scheme", "coulombtype", "rcoulomb",
    "vdwtype", "rvdw", "dispcorr", "nstlog", "nstenergy", "nstxout",
    "nstxout-compressed", "comm-mode", "comm-grps", "nstcomm",
}
REQUIRED_PLAN = {
    "case_id", "protocol_id", "gromacs_version", "task", "objective",
    "claim_target", "artifact_class", "units", "pbc", "integrator", "ensemble",
    "timestep_ps", "topology", "force_field", "restart", "seed",
    "equilibration", "production", "observables", "output", "authorization",
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


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value!r}")


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
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
                raise GuardFailure("GROMACS.IO.UNSAFE_FILE", "A platform root alias is unstable.") from exc
            if not stat.S_ISDIR(resolved_metadata.st_mode):
                raise GuardFailure("GROMACS.IO.UNSAFE_FILE", "A platform root alias is not a directory.")
            absolute = resolved_first.joinpath(*parts[2:])
    return absolute


def _bound_directory_descriptor(directory: Path) -> tuple[int, Path]:
    """Open every directory edge with openat/no-follow and reuse retained bindings."""

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory_flag is None or nonblock is None:
        raise GuardFailure("GROMACS.IO.NOFOLLOW_UNAVAILABLE", "The platform lacks safe directory traversal support.", incomplete=True)
    if not _OPENAT_SUPPORTED:
        raise GuardFailure("GROMACS.IO.NOFOLLOW_UNAVAILABLE", "The platform lacks openat/statat support.", incomplete=True)
    absolute = _normalized_absolute(directory)
    root = Path(absolute.anchor)
    flags = os.O_RDONLY | directory_flag | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)
    descriptors: list[int] = []
    edges: list[tuple[int, str, int, os.stat_result]] = []
    try:
        root_path_metadata = root.lstat()
        if stat.S_ISLNK(root_path_metadata.st_mode) or not stat.S_ISDIR(root_path_metadata.st_mode):
            raise GuardFailure("GROMACS.IO.UNSAFE_FILE", "The filesystem root is unavailable or unsafe.")
        current_fd = os.open(root, flags)
        descriptors.append(current_fd)
        current_metadata = os.fstat(current_fd)
        if _directory_identity(current_metadata) != _directory_identity(root_path_metadata):
            raise GuardFailure("GROMACS.IO.CHANGED_DURING_READ", "A directory identity changed during traversal.")
        root_key = os.fspath(root)
        retained_root = _DIRECTORY_BINDINGS.get(root_key)
        if retained_root is None:
            _DIRECTORY_BINDINGS[root_key] = (current_metadata.st_dev, current_metadata.st_ino, os.dup(current_fd))
        elif retained_root[:2] != (current_metadata.st_dev, current_metadata.st_ino):
            raise GuardFailure("GROMACS.IO.CHANGED_DURING_READ", "A bound directory identity changed.")

        current_path = root
        for component in absolute.parts[1:]:
            anchored_before = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(anchored_before.st_mode) or not stat.S_ISDIR(anchored_before.st_mode):
                raise GuardFailure("GROMACS.IO.UNSAFE_FILE", "An intermediate path component is a symlink or non-directory.")
            child_fd = os.open(component, flags, dir_fd=current_fd)
            child_metadata = os.fstat(child_fd)
            if _directory_identity(child_metadata) != _directory_identity(anchored_before):
                os.close(child_fd)
                raise GuardFailure("GROMACS.IO.CHANGED_DURING_READ", "An intermediate directory changed during openat.")
            current_path = current_path / component
            binding_key = os.fspath(current_path)
            retained = _DIRECTORY_BINDINGS.get(binding_key)
            if retained is None:
                _DIRECTORY_BINDINGS[binding_key] = (child_metadata.st_dev, child_metadata.st_ino, os.dup(child_fd))
            else:
                if retained[:2] != (child_metadata.st_dev, child_metadata.st_ino):
                    os.close(child_fd)
                    raise GuardFailure("GROMACS.IO.CHANGED_DURING_READ", "A request/evidence base changed identity.")
                retained_fd = os.dup(retained[2])
                retained_metadata = os.fstat(retained_fd)
                if _directory_identity(retained_metadata) != _directory_identity(child_metadata):
                    os.close(retained_fd)
                    os.close(child_fd)
                    raise GuardFailure("GROMACS.IO.CHANGED_DURING_READ", "A retained request/evidence base is unstable.")
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
                raise GuardFailure("GROMACS.IO.CHANGED_DURING_READ", "An intermediate directory changed during traversal.")
        lexical_final = absolute.lstat()
        if _directory_identity(lexical_final) != _directory_identity(os.fstat(current_fd)):
            raise GuardFailure("GROMACS.IO.CHANGED_DURING_READ", "The input base changed during traversal.")
        return os.dup(current_fd), absolute
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("GROMACS.IO.UNSAFE_FILE", "A directory path could not be traversed without aliases.") from exc
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
            raise GuardFailure("GROMACS.IO.CHANGED_DURING_READ", "A request/evidence base changed during I/O.")
    finally:
        os.close(verification_fd)


def read_bytes(path: Path, limit: int) -> bytes:
    """Read one bounded no-follow snapshot and verify fd/path identity did not drift."""

    key = os.path.abspath(os.fspath(path))
    cached = _SNAPSHOT_CACHE.get(key)
    if cached is not None:
        if not cached or len(cached) > limit:
            raise GuardFailure("GROMACS.IO.SIZE", "A required artifact is empty or exceeds the bounded size.")
        return cached
    nofollow = getattr(os, "O_NOFOLLOW", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or nonblock is None:
        raise GuardFailure("GROMACS.IO.NOFOLLOW_UNAVAILABLE", "The platform cannot establish a nonblocking no-follow input snapshot.", incomplete=True)
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
        raise GuardFailure("GROMACS.IO.UNSAFE_FILE", "A required artifact is unavailable or not a regular non-symlink file.") from exc
    try:
        assert descriptor is not None
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise GuardFailure("GROMACS.IO.UNSAFE_FILE", "Inputs must be regular single-link non-symlink files.")
        if before.st_size <= 0 or before.st_size > limit:
            raise GuardFailure("GROMACS.IO.SIZE", "A required artifact is empty or exceeds the bounded size.")
        blocks: list[bytes] = []
        total = 0
        while True:
            block = os.read(descriptor, min(65536, limit + 1 - total))
            if not block:
                break
            blocks.append(block)
            total += len(block)
            if total > limit:
                raise GuardFailure("GROMACS.IO.SIZE", "A required artifact exceeds the bounded size.")
        after = os.fstat(descriptor)
        anchored_final = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        lexical_final = Path(os.path.abspath(os.fspath(path))).lstat()
        _verify_bound_directory(path.parent, parent_fd)
    except OSError as exc:
        raise GuardFailure("GROMACS.IO.READ", "A required artifact could not be read safely.") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_fd)
    data = b"".join(blocks)
    identity = _file_identity(before)
    if (
        identity != _file_identity(after)
        or identity != _file_identity(anchored_final)
        or identity != _file_identity(lexical_final)
        or not stat.S_ISREG(anchored_final.st_mode)
        or anchored_final.st_nlink != 1
        or len(data) != before.st_size
    ):
        raise GuardFailure("GROMACS.IO.CHANGED_DURING_READ", "An input changed identity or content while being read.")
    _SNAPSHOT_CACHE[key] = data
    _INPUT_IDENTITIES.add((before.st_dev, before.st_ino))
    return data


def parse_json_bytes(data: bytes) -> dict[str, Any]:
    if data.startswith(b"\xef\xbb\xbf"):
        raise GuardFailure("GROMACS.JSON.INVALID", "JSON must be UTF-8 without a BOM.")
    try:
        value = json.loads(
            data.decode("utf-8"), object_pairs_hook=_object_pairs, parse_constant=_reject_constant
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise GuardFailure("GROMACS.JSON.INVALID", "JSON is malformed or ambiguous.") from exc
    if not isinstance(value, dict):
        raise GuardFailure("GROMACS.JSON.INVALID", "JSON root must be an object.")
    return value


def load_json(path: Path) -> dict[str, Any]:
    return parse_json_bytes(read_bytes(path, MAX_JSON_BYTES))


def read_text(path: Path) -> str:
    data = read_bytes(path, MAX_TEXT_BYTES)
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise GuardFailure("GROMACS.TEXT.NON_ASCII", "The conservative text parser requires ASCII.") from exc
    if "\x00" in text:
        raise GuardFailure("GROMACS.TEXT.NUL", "NUL bytes are not accepted in text artifacts.")
    return text


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(read_bytes(path, MAX_TEXT_BYTES))


def evidence(path: Path, role: str) -> dict[str, str]:
    return {"role": role, "label": path.name, "sha256": sha256_file(path)}


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
    "plan": {"plan_id", "plan"},
    "audit-input": {"plan_id", "inventory", "upstream"},
    "audit-output": {"plan_id", "upstream"},
    "audit-trajectory": {"plan_id", "upstream"},
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
    raise GuardFailure("GROMACS.UPSTREAM.INVALID_SHAPE", message)


def _validate_upstream_shape(report: dict[str, Any], command: str) -> None:
    if command not in COMMAND_REPORT_KEYS or set(report) != BASE_REPORT_KEYS | COMMAND_REPORT_KEYS[command]:
        _shape_failure(f"Upstream {command} report does not have the complete canonical key set.")
    if report.get("schema_version") != SCHEMA_VERSION:
        _shape_failure(f"Upstream {command} schema version is not supported.")
    if report.get("tool") != {"name": "gromacs_guard", "version": TOOL_VERSION}:
        _shape_failure(f"Upstream {command} tool identity is invalid.")
    if report.get("engine") != "gromacs" or report.get("command") != command:
        _shape_failure(f"Upstream {command} engine or command identity is invalid.")
    if report.get("candidate_lifecycle") != "development" or report.get("claim_ceiling") != "no_positive_claim":
        _shape_failure(f"Upstream {command} candidate lifecycle or current claim ceiling is invalid.")
    if report.get("future_gate_ceiling") != FUTURE_CEILINGS[command]:
        _shape_failure(f"Upstream {command} future gate ceiling is invalid.")
    if any(report.get(key) is not False for key in ("promotion_ready", "promotion_authorized", "execution_authorized")):
        _shape_failure(f"Upstream {command} contains promotion or execution authorization.")
    if report.get("report_authenticity") != REPORT_AUTHENTICITY:
        _shape_failure(f"Upstream {command} authenticity marker is invalid.")
    expected_maturity = {
        "plan": "synthetic-validated",
        "audit-input": "synthetic-validated",
        "audit-output": "synthetic-validated",
        "audit-trajectory": "format-fixture-validated",
    }[command]
    if report.get("maturity") != expected_maturity:
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
        raise GuardFailure("GROMACS.UPSTREAM.TAMPERED", f"Upstream {command} self fingerprint is inconsistent.")
    if command == "plan":
        plan = report.get("plan")
        if (
            not isinstance(plan, dict)
            or validate_plan_request(plan)
            or not _is_sha256(report.get("plan_id"))
            or report["plan_id"] != canonical_hash(plan)
            or report["metrics"] != {"plan_id": report["plan_id"]}
        ):
            _shape_failure("Upstream plan payload, ID, or metrics are invalid.")
        if len(evidence_by_role.get("plan-request", [])) != 1:
            _shape_failure("Upstream plan does not identify exactly one plan request.")
    else:
        if not _is_sha256(report.get("plan_id")):
            _shape_failure(f"Upstream {command} plan ID is invalid.")
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
            inventory = report.get("inventory")
            if (
                not isinstance(inventory, dict)
                or report["metrics"] != inventory
                or inventory.get("plan_id") != report["plan_id"]
                or not isinstance(inventory.get("atom_count"), int)
                or isinstance(inventory.get("atom_count"), bool)
                or inventory["atom_count"] <= 0
                or not isinstance(inventory.get("site_order"), list)
                or not all(isinstance(item, str) for item in inventory["site_order"])
                or len(inventory["site_order"]) != inventory["atom_count"]
                or not isinstance(inventory.get("topology_file_count"), int)
                or inventory["topology_file_count"] <= 0
                or not isinstance(inventory.get("topology_atom_count"), int)
                or inventory["topology_atom_count"] != inventory["atom_count"]
                or not isinstance(inventory.get("expected_final_step"), int)
                or inventory["expected_final_step"] < 0
                or not isinstance(inventory.get("mdp"), dict)
                or not all(isinstance(key, str) and isinstance(value, str) for key, value in inventory["mdp"].items())
            ):
                _shape_failure("Upstream audit-input inventory is invalid.")
        elif command == "audit-output":
            metrics = report["metrics"]
            if (
                set(metrics) != {"version_banners", "terminal_marker_count", "last_step", "expected_final_step", "sampling"}
                or not isinstance(metrics["version_banners"], list)
                or len(metrics["version_banners"]) != 1
                or not all(isinstance(item, str) and item for item in metrics["version_banners"])
                or not isinstance(metrics["terminal_marker_count"], int)
                or isinstance(metrics["terminal_marker_count"], bool)
                or metrics["terminal_marker_count"] != 1
                or not isinstance(metrics["last_step"], int)
                or isinstance(metrics["last_step"], bool)
                or not isinstance(metrics["expected_final_step"], int)
                or isinstance(metrics["expected_final_step"], bool)
                or metrics["last_step"] != metrics["expected_final_step"]
                or not isinstance(metrics["sampling"], dict)
            ):
                _shape_failure("Upstream audit-output metrics are invalid.")
        else:
            metrics = report["metrics"]
            required_metrics = {
                "format", "frame_count", "atom_count", "site_order_sha256", "time_unit",
                "first_time", "last_time", "cell_mode", "pbc", "wrapped_coordinates",
                "unwrapped_coordinates", "velocities_all_frames", "handoff_contract",
                "handoff_ready", "handoff_blocker",
            }
            if (
                set(metrics) != required_metrics
                or metrics["format"] != "gro"
                or not isinstance(metrics["frame_count"], int)
                or isinstance(metrics["frame_count"], bool)
                or metrics["frame_count"] <= 0
                or not isinstance(metrics["atom_count"], int)
                or isinstance(metrics["atom_count"], bool)
                or metrics["atom_count"] <= 0
                or not _is_sha256(metrics["site_order_sha256"])
                or metrics["time_unit"] != "ps"
                or not all(isinstance(metrics[key], (int, float)) and not isinstance(metrics[key], bool) and math.isfinite(float(metrics[key])) for key in ("first_time", "last_time"))
                or metrics["cell_mode"] not in {"fixed", "variable"}
                or not isinstance(metrics["pbc"], list)
                or len(metrics["pbc"]) != 3
                or not all(isinstance(value, bool) for value in metrics["pbc"])
                or metrics["wrapped_coordinates"] is not True
                or metrics["unwrapped_coordinates"] is not False
                or not isinstance(metrics["velocities_all_frames"], bool)
                or metrics["handoff_contract"] != "atomistic-trajectory-manifest@1.0"
                or metrics["handoff_ready"] is not False
                or not isinstance(metrics["handoff_blocker"], str)
                or not metrics["handoff_blocker"]
            ):
                _shape_failure("Upstream audit-trajectory metrics are invalid.")


def load_verified_upstream(path: Path, command: str) -> tuple[dict[str, Any], str]:
    """Load one exact raw snapshot, validate the unsigned report, and return its raw SHA-256."""

    raw = read_bytes(path, MAX_JSON_BYTES)
    report = parse_json_bytes(raw)
    _validate_upstream_shape(report, command)
    if report["decision"] != "pass":
        raise GuardFailure("GROMACS.UPSTREAM.NOT_PASSING", f"A passing upstream {command} report is required.")
    return report, sha256_bytes(raw)


def finding(code: str, gate: str, message: str, next_action: str, *, kind: str = "fail") -> dict[str, str]:
    return {
        "code": code,
        "gate": gate,
        "severity": "critical",
        "kind": kind,
        "message": message,
        "next_action": next_action,
    }


def decision(findings: list[dict[str, str]]) -> str:
    if any(item["kind"] == "fail" for item in findings):
        return "blocked"
    if findings:
        return "incomplete"
    return "pass"


def make_report(
    command: str,
    findings: list[dict[str, str]],
    evidence_items: list[dict[str, str]],
    metrics: dict[str, Any],
    *,
    maturity: str = "synthetic-validated",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    local = decision(findings)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "gromacs_guard", "version": TOOL_VERSION},
        "engine": "gromacs",
        "command": command,
        "decision": local,
        "candidate_lifecycle": "development",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": FUTURE_CEILINGS[command],
        "promotion_ready": False,
        "promotion_authorized": False,
        "execution_authorized": False,
        "report_authenticity": REPORT_AUTHENTICITY,
        "maturity": maturity,
        "findings": findings,
        "evidence": sorted(evidence_items, key=lambda item: (item["role"], item["label"])),
        "metrics": metrics,
        "limitations": [
            "The tool performs offline parsing only and never invokes GROMACS.",
            "A local pass does not establish physical validity or scientific acceptance.",
            "Current parser maturity is bounded by project-authored synthetic or format fixtures.",
            "Reports do not instantiate missing shared run or trajectory records.",
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
            raise GuardFailure("GROMACS.IO.OUTPUT_ALIASES_INPUT", "The report output aliases an input artifact.")
        try:
            output_stat = out.lstat()
            input_stat = input_path.lstat()
        except OSError:
            continue
        if (output_stat.st_dev, output_stat.st_ino) == (input_stat.st_dev, input_stat.st_ino):
            raise GuardFailure("GROMACS.IO.OUTPUT_ALIASES_INPUT", "The report output shares identity with an input artifact.")


def _metadata_at(directory_fd: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise GuardFailure("GROMACS.IO.WRITE", "An output name could not be inspected safely.") from exc


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
        raise GuardFailure("GROMACS.IO.WRITE", "The output filename is invalid.")
    if not _LINKAT_SUPPORTED:
        raise GuardFailure("GROMACS.IO.NOFOLLOW_UNAVAILABLE", "The platform lacks safe hard-link publication support.", incomplete=True)
    directory_fd, _normalized_parent = _bound_directory_descriptor(path.parent)
    temporary_fd: int | None = None
    temporary_name: str | None = None
    link_succeeded = False
    installed = False
    try:
        if _metadata_at(directory_fd, path.name) is not None:
            raise GuardFailure("GROMACS.IO.OVERWRITE", "The report path already exists.")
        nofollow = getattr(os, "O_NOFOLLOW", None)
        if nofollow is None:
            raise GuardFailure("GROMACS.IO.NOFOLLOW_UNAVAILABLE", "The platform cannot create a no-follow staging file.", incomplete=True)
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
            raise GuardFailure("GROMACS.IO.WRITE", "A private output staging file could not be created.")
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
            raise GuardFailure("GROMACS.IO.WRITE", "The staged report identity or payload is invalid.")
        _verify_bound_directory(path.parent, directory_fd)
        if _metadata_at(directory_fd, path.name) is not None:
            raise GuardFailure("GROMACS.IO.OVERWRITE", "The report target appeared during staging.")
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
            raise GuardFailure("GROMACS.IO.OVERWRITE", "The report target appeared during atomic publication.") from exc
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
            raise GuardFailure("GROMACS.IO.WRITE", "The staging name was substituted during publication.")
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
            raise GuardFailure("GROMACS.IO.WRITE", "The published report changed after installation.")
        _verify_bound_directory(path.parent, directory_fd)
        os.fsync(directory_fd)
        installed = True
    except GuardFailure:
        raise
    except OSError as exc:
        raise GuardFailure("GROMACS.IO.WRITE", "The report could not be written atomically.") from exc
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
            blocked = make_report(
                report["command"],
                [finding(exc.code, "side_effect_boundary", exc.message, "Choose a distinct new report path.", kind="incomplete" if exc.incomplete else "fail")],
                [],
                {},
            )
            sys.stdout.write(json.dumps(blocked, indent=2, sort_keys=True) + "\n")
            return 3 if exc.incomplete else 2
    return {"pass": 0, "blocked": 2, "incomplete": 3}[report["decision"]]


def validate_safe_id(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value))


def validate_plan_request(request: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    missing = sorted(REQUIRED_PLAN - set(request))
    if missing:
        findings.append(finding("GROMACS.PLAN.MISSING_FIELD", "claim_definition", "Required plan fields are missing: " + ", ".join(missing), "Supply every required field without inventing values."))
        return findings
    if not validate_safe_id(request["case_id"]) or not validate_safe_id(request["protocol_id"]):
        findings.append(finding("GROMACS.PLAN.INVALID_ID", "claim_definition", "Case and protocol IDs must be privacy-safe identifiers.", "Use anonymous alphanumeric IDs."))
    if request["gromacs_version"] != "2026.3":
        findings.append(finding("GROMACS.VERSION.UNSUPPORTED", "official_version_match", "This candidate has documentary coverage only for GROMACS 2026.3.", "Provide exact version-matched official sources and extend tests.", kind="incomplete"))
    if request["task"] not in {"nve", "nvt", "npt", "energy-minimization"}:
        findings.append(finding("GROMACS.PLAN.UNSUPPORTED_TASK", "claim_definition", "The requested task is outside the conservative core.", "Keep the task design-only or add a tested task profile.", kind="incomplete"))
    if not isinstance(request["objective"], str) or not request["objective"].strip() or not isinstance(request["claim_target"], str) or not request["claim_target"].strip():
        findings.append(finding("GROMACS.PLAN.MISSING_FIELD", "claim_definition", "Objective and bounded claim target must be nonempty.", "State both explicitly."))
    if request["artifact_class"] not in {"synthetic", "user-supplied"}:
        findings.append(finding("GROMACS.PLAN.ARTIFACT_CLASS", "claim_definition", "Artifact class must be synthetic or user-supplied.", "Declare the evidence class."))
    if request["units"] != EXPECTED_UNITS:
        findings.append(finding("GROMACS.UNITS.MISMATCH", "units_boundary_and_pbc", "Plan units do not match GROMACS MD units.", "Use the exact GROMACS unit map."))
    if not isinstance(request["pbc"], list) or len(request["pbc"]) != 3 or not all(isinstance(value, bool) for value in request["pbc"]):
        findings.append(finding("GROMACS.PLAN.PBC", "units_boundary_and_pbc", "PBC must contain three booleans.", "Declare all three periodic axes."))
    if not isinstance(request["timestep_ps"], (int, float)) or isinstance(request["timestep_ps"], bool) or not math.isfinite(request["timestep_ps"]) or request["timestep_ps"] <= 0:
        findings.append(finding("GROMACS.PLAN.TIMESTEP", "numerical_discretization", "Time step must be a finite positive number in ps.", "Declare a tested time step."))
    for name in ("topology", "force_field"):
        value = request[name]
        if not isinstance(value, dict) or not all(isinstance(value.get(key), str) and value[key].strip() for key in ("identity", "source_url", "license_status")):
            findings.append(finding("GROMACS.PLAN.MODEL_PROVENANCE", "model_forcefield_provenance", f"{name} identity, source URL, and license status are required.", "Provide independent provenance declarations."))
        elif value["license_status"] != "verified":
            findings.append(finding("GROMACS.PROVENANCE.LICENSE_UNRESOLVED", "model_forcefield_provenance", f"{name} license is not verified.", "Resolve legal terms before a positive model gate."))
    restart = request["restart"]
    if not isinstance(restart, dict) or restart.get("mode") not in {"new", "checkpoint-continuation"}:
        findings.append(finding("GROMACS.RESTART.LINEAGE_MISSING", "restart_lineage", "Restart mode is invalid or missing.", "Declare new or checkpoint-continuation."))
    elif restart["mode"] == "checkpoint-continuation":
        if not validate_safe_id(restart.get("parent_run_id")) or not isinstance(restart.get("checkpoint_sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", restart["checkpoint_sha256"]):
            findings.append(finding("GROMACS.RESTART.LINEAGE_MISSING", "restart_lineage", "Checkpoint continuation lacks parent ID or checkpoint hash.", "Bind exact parent and checkpoint evidence."))
    seed = request["seed"]
    if not isinstance(seed, dict) or seed.get("mode") not in {"explicit", "checkpoint-state"}:
        findings.append(finding("GROMACS.INPUT.SEED_POLICY", "initial_state_and_seed", "Seed policy is missing or invalid.", "Declare explicit or checkpoint-state seed policy."))
    elif seed["mode"] == "explicit" and (not isinstance(seed.get("value"), int) or isinstance(seed.get("value"), bool) or seed["value"] < 0):
        findings.append(finding("GROMACS.INPUT.SEED_POLICY", "initial_state_and_seed", "Explicit seed must be a nonnegative integer.", "Provide the exact seed."))
    for phase in ("equilibration", "production"):
        value = request[phase]
        if not isinstance(value, dict) or not isinstance(value.get("steps"), int) or isinstance(value.get("steps"), bool) or value["steps"] < 0 or not isinstance(value.get("acceptance_checks"), list) or not value["acceptance_checks"]:
            findings.append(finding("GROMACS.PLAN.PHASE", "equilibration_assessment", f"{phase} must declare steps and acceptance checks.", "Define the phase before execution."))
    observables = request["observables"]
    if not isinstance(observables, list) or not observables:
        findings.append(finding("GROMACS.PLAN.OBSERVABLE", "statistical_convergence", "At least one observable is required.", "Name the observable, unit, estimator and uncertainty policy."))
    else:
        names: set[str] = set()
        for item in observables:
            valid = isinstance(item, dict) and all(key in item for key in ("name", "unit", "estimator", "uncertainty_method", "minimum_effective_samples", "max_standard_error"))
            if not valid or not isinstance(item.get("name"), str) or item["name"] in names or item.get("estimator") != "mean" or item.get("uncertainty_method") != "block-mean" or not isinstance(item.get("minimum_effective_samples"), int) or item["minimum_effective_samples"] < 2 or not isinstance(item.get("max_standard_error"), (int, float)) or item["max_standard_error"] <= 0:
                findings.append(finding("GROMACS.PLAN.OBSERVABLE", "statistical_convergence", "Observable definitions are incomplete, duplicate, or unsupported.", "Use unique mean/block-mean definitions with explicit ESS and uncertainty bounds."))
                break
            names.add(item["name"])
    output = request["output"]
    if not isinstance(output, dict) or not all(isinstance(output.get(key), int) and not isinstance(output.get(key), bool) and output[key] > 0 for key in ("log_interval_steps", "energy_interval_steps", "trajectory_interval_steps", "expected_trajectory_frames")):
        findings.append(finding("GROMACS.PLAN.OUTPUT", "trajectory_integrity", "Output cadence and expected frame count must be positive integers.", "Declare deterministic output expectations."))
    authorization = request["authorization"]
    if not isinstance(authorization, dict) or authorization.get("execute_external_software") is not False:
        findings.append(finding("GROMACS.EXECUTION.NOT_AUTHORIZED", "input_execution_safety", "This candidate accepts only explicit no-execution plans.", "Route later execution through an authorized execution Skill."))
    return findings


def command_plan(args: argparse.Namespace) -> dict[str, Any]:
    request = load_json(args.request)
    findings = validate_plan_request(request)
    plan_id = canonical_hash(request)
    return make_report("plan", findings, [evidence(args.request, "plan-request")], {"plan_id": plan_id}, extra={"plan_id": plan_id, "plan": request})


def load_passing_plan(path: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    report, raw_sha256 = load_verified_upstream(path, "plan")
    return report, report["plan"], raw_sha256


def parse_mdp(path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    values: dict[str, str] = {}
    findings: list[dict[str, str]] = []
    for number, raw in enumerate(read_text(path).splitlines(), 1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if "=" not in line:
            findings.append(finding("GROMACS.INPUT.MDP_GRAMMAR", "input_integrity", f"MDP line {number} has no assignment.", "Use literal key=value syntax."))
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        normalized = re.sub(r"[-_]", "-", key.casefold())
        if normalized in values:
            findings.append(finding("GROMACS.INPUT.DUPLICATE_MDP_KEY", "input_integrity", f"Duplicate normalized MDP key: {normalized}.", "Remove the ambiguous assignment."))
        if normalized not in ALLOWED_MDP:
            findings.append(finding("GROMACS.INPUT.UNSUPPORTED_MDP_KEY", "input_integrity", f"Unsupported MDP key: {normalized}.", "Extend the version-matched allowlist with tests or retain incomplete status.", kind="incomplete"))
        values[normalized] = value.strip()
    return values, findings


def parse_gro(path: Path) -> list[dict[str, Any]]:
    lines = read_text(path).splitlines()
    frames: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        title = lines[index].strip()
        index += 1
        if not title:
            raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO frame has an empty title.")
        if index >= len(lines):
            raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO frame is truncated before atom count.")
        try:
            count = int(lines[index].strip())
        except ValueError as exc:
            raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO atom count is invalid.") from exc
        index += 1
        if count <= 0 or index + count >= len(lines):
            raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO frame is empty or truncated.")
        sites: list[str] = []
        coordinates: list[list[float]] = []
        velocities_present = True
        for _ in range(count):
            line = lines[index]
            index += 1
            if len(line) < 20:
                raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO atom record is too short.")
            site = ":".join((line[:5].strip(), line[5:10].strip(), line[10:15].strip(), line[15:20].strip()))
            fields = line[20:].split()
            if len(fields) not in {3, 6}:
                raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO atom record has unsupported coordinate columns.")
            try:
                numeric = [float(value) for value in fields]
            except ValueError as exc:
                raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO atom record has nonnumeric coordinates.") from exc
            if not all(math.isfinite(value) for value in numeric):
                raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO atom record contains non-finite values.")
            sites.append(site)
            coordinates.append(numeric[:3])
            velocities_present = velocities_present and len(numeric) == 6
        try:
            box = [float(value) for value in lines[index].split()]
        except ValueError as exc:
            raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO box line is nonnumeric.") from exc
        index += 1
        if len(box) not in {3, 9} or not all(math.isfinite(value) for value in box) or any(value <= 0 for value in box[:3]):
            raise GuardFailure("GROMACS.TRAJECTORY.FRAME_INVALID", "A GRO box is invalid or singular in its leading vectors.")
        match = re.search(r"(?:^|\s)t\s*=\s*([-+0-9.eE]+)", title)
        time = float(match.group(1)) if match else None
        frames.append({"title": title, "atom_count": count, "sites": sites, "coordinates": coordinates, "velocities": velocities_present, "box": box, "time_ps": time})
    return frames


def topology_closure(root_topology: Path) -> tuple[list[Path], int | None, list[dict[str, str]]]:
    root = root_topology.parent.resolve()
    ordered: list[Path] = []
    active: set[Path] = set()
    findings: list[dict[str, str]] = []
    flattened: list[str] = []

    def visit(path: Path) -> None:
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            findings.append(finding("GROMACS.TOPOLOGY.INCLUDE_ESCAPE", "system_topology_integrity", "A topology include escapes the declared topology root.", "Move and review the include closure under one root."))
            return
        if resolved in active:
            findings.append(finding("GROMACS.TOPOLOGY.INCLUDE_CYCLE", "system_topology_integrity", "The topology include graph contains a cycle.", "Remove the include cycle."))
            return
        if resolved in ordered:
            return
        if not resolved.is_file() or resolved.is_symlink():
            findings.append(finding("GROMACS.TOPOLOGY.INCLUDE_UNRESOLVED", "system_topology_integrity", "A quoted topology include is missing or unsafe.", "Provide the literal include under the topology root."))
            return
        active.add(resolved)
        ordered.append(resolved)
        for raw in read_text(resolved).splitlines():
            stripped = raw.strip()
            angle = re.match(r'^\s*#\s*include\s*<([^>]+)>', raw)
            quoted = re.match(r'^\s*#\s*include\s*"([^"]+)"', raw)
            if angle:
                findings.append(finding("GROMACS.TOPOLOGY.INCLUDE_UNRESOLVED", "system_topology_integrity", "Angle-bracket include depends on an unbound search path.", "Provide a processed literal closure or a future grompp adapter.", kind="incomplete"))
            elif quoted:
                visit(resolved.parent / quoted.group(1))
            elif stripped.startswith(("#if", "#else", "#endif", "#undef")):
                findings.append(finding("GROMACS.TOPOLOGY.PREPROCESSOR_UNSUPPORTED", "system_topology_integrity", "Conditional topology preprocessing is unsupported offline.", "Use a hash-bound processed topology from an authorized grompp adapter.", kind="incomplete"))
            elif not stripped.startswith("#"):
                flattened.append(raw)
        active.remove(resolved)

    visit(root_topology)
    section = ""
    current_molecule: str | None = None
    expect_molecule_name = False
    atoms_per_molecule: dict[str, int] = {}
    molecule_counts: dict[str, int] = {}
    for raw in flattened:
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r"\[\s*([^]]+)\s*\]", line)
        if match:
            section = match.group(1).strip().casefold()
            expect_molecule_name = section == "moleculetype"
            continue
        if expect_molecule_name:
            current_molecule = line.split()[0]
            atoms_per_molecule.setdefault(current_molecule, 0)
            expect_molecule_name = False
        elif section == "atoms" and current_molecule:
            atoms_per_molecule[current_molecule] += 1
        elif section == "molecules":
            fields = line.split()
            if len(fields) >= 2:
                try:
                    molecule_counts[fields[0]] = molecule_counts.get(fields[0], 0) + int(fields[1])
                except ValueError:
                    findings.append(finding("GROMACS.TOPOLOGY.MOLECULE_COUNT", "system_topology_integrity", "A molecules count is invalid.", "Use an integer molecule count."))
    total = None
    if molecule_counts and all(name in atoms_per_molecule for name in molecule_counts):
        total = sum(atoms_per_molecule[name] * count for name, count in molecule_counts.items())
    else:
        findings.append(finding("GROMACS.TOPOLOGY.ATOM_COUNT_UNRESOLVED", "system_topology_integrity", "The conservative parser cannot resolve total topology atoms.", "Provide literal moleculetype, atoms, and molecules sections.", kind="incomplete"))
    return ordered, total, findings


def provenance_gate(manifest_path: Path, files: list[Path], plan: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    manifest = load_json(manifest_path)
    findings: list[dict[str, str]] = []
    evidence_items = [evidence(manifest_path, "provenance-manifest")]
    entries = manifest.get("files")
    if manifest.get("schema_version") != "1.0" or manifest.get("engine") != "gromacs" or not isinstance(entries, list):
        return [finding("GROMACS.PROVENANCE.INVALID", "model_forcefield_provenance", "The provenance manifest is malformed.", "Use the documented manifest structure.")], evidence_items
    by_name: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("filename"), str) or entry["filename"] in by_name:
            findings.append(finding("GROMACS.PROVENANCE.INVALID", "model_forcefield_provenance", "Provenance filenames are missing or duplicate.", "List each artifact once."))
            continue
        by_name[entry["filename"]] = entry
    expected = {path.name for path in files}
    if set(by_name) != expected:
        findings.append(finding("GROMACS.PROVENANCE.COVERAGE", "model_forcefield_provenance", "The provenance manifest does not exactly cover audited artifacts.", "Add missing entries and remove unrelated ones."))
    for path in files:
        entry = by_name.get(path.name, {})
        observed = sha256_file(path)
        if entry.get("sha256") != observed:
            findings.append(finding("GROMACS.PROVENANCE.HASH_MISMATCH", "model_forcefield_provenance", f"Hash mismatch for {path.name}.", "Restore the declared content or update provenance before audit."))
        if entry.get("license_status") != "verified" or not isinstance(entry.get("license"), str) or not isinstance(entry.get("source_url"), str):
            findings.append(finding("GROMACS.PROVENANCE.LICENSE_UNRESOLVED", "model_forcefield_provenance", f"License/source is unresolved for {path.name}.", "Verify independent legal and source metadata."))
        evidence_items.append({"role": str(entry.get("role", "artifact")), "label": path.name, "sha256": observed})
    model = manifest.get("force_field")
    if not isinstance(model, dict) or model.get("identity") != plan["force_field"]["identity"] or model.get("source_url") != plan["force_field"]["source_url"] or model.get("license_status") != "verified":
        findings.append(finding("GROMACS.PROVENANCE.MODEL_MISMATCH", "model_forcefield_provenance", "Force-field declaration does not match the plan.", "Bind the exact planned model identity, source, and terms."))
    return findings, evidence_items


def expected_pbc_token(pbc: list[bool]) -> str | None:
    mapping = {(True, True, True): "xyz", (True, True, False): "xy", (False, False, False): "no"}
    return mapping.get(tuple(pbc))


def command_audit_input(args: argparse.Namespace) -> dict[str, Any]:
    plan_report, plan, plan_raw_sha256 = load_passing_plan(args.plan)
    mdp, findings = parse_mdp(args.mdp)
    frames = parse_gro(args.coordinates)
    if len(frames) != 1:
        findings.append(finding("GROMACS.INPUT.COORDINATE_FRAMES", "system_topology_integrity", "The input coordinate file must contain exactly one GRO frame.", "Provide one starting state."))
    closure, topology_atoms, topology_findings = topology_closure(args.topology)
    findings.extend(topology_findings)
    all_files = [args.mdp, args.coordinates, *closure]
    provenance_findings, evidence_items = provenance_gate(args.provenance, all_files, plan)
    findings.extend(provenance_findings)
    required_mdp = {"integrator", "dt", "nsteps", "continuation", "gen-vel", "pbc", "tcoupl", "pcoupl", "nstlog", "nstenergy", "nstxout-compressed"}
    absent = sorted(required_mdp - set(mdp))
    if absent:
        findings.append(finding("GROMACS.INPUT.MISSING_MDP_KEY", "input_integrity", "Required explicit MDP keys are missing: " + ", ".join(absent), "Make defaults explicit for audit."))
    try:
        dt = float(mdp.get("dt", "nan"))
        nsteps = int(mdp.get("nsteps", "-1"))
    except ValueError:
        dt, nsteps = math.nan, -1
    if not math.isfinite(dt) or not math.isclose(dt, float(plan["timestep_ps"]), rel_tol=0.0, abs_tol=1e-12):
        findings.append(finding("GROMACS.INPUT.TIMESTEP_MISMATCH", "numerical_discretization", "MDP dt does not match the plan.", "Use the planned explicit time step."))
    expected_steps = plan["equilibration"]["steps"] + plan["production"]["steps"]
    if nsteps != expected_steps:
        findings.append(finding("GROMACS.INPUT.NSTEPS_MISMATCH", "integrator_and_coupling_definition", "MDP nsteps does not equal planned equilibration plus production steps.", "Align the phase length."))
    if mdp.get("integrator", "").casefold() != str(plan["integrator"]).casefold():
        findings.append(finding("GROMACS.INPUT.INTEGRATOR_MISMATCH", "integrator_and_coupling_definition", "MDP integrator does not match the plan.", "Use the planned integrator."))
    pbc_token = expected_pbc_token(plan["pbc"])
    if pbc_token is None:
        findings.append(finding("GROMACS.INPUT.PBC_UNSUPPORTED", "units_boundary_and_pbc", "This PBC combination is outside the offline core.", "Retain incomplete status or extend exact-version coverage.", kind="incomplete"))
    elif mdp.get("pbc", "").casefold() != pbc_token:
        findings.append(finding("GROMACS.INPUT.PBC_MISMATCH", "units_boundary_and_pbc", "MDP PBC does not match the plan.", "Use the planned boundary condition."))
    tcoupl = mdp.get("tcoupl", "").casefold()
    pcoupl = mdp.get("pcoupl", "").casefold()
    ensemble = plan["ensemble"].casefold()
    mismatch = (ensemble == "nve" and (tcoupl != "no" or pcoupl != "no")) or (ensemble == "nvt" and (tcoupl == "no" or pcoupl != "no")) or (ensemble == "npt" and (tcoupl == "no" or pcoupl == "no"))
    if mismatch:
        findings.append(finding("GROMACS.INPUT.ENSEMBLE_MISMATCH", "integrator_and_coupling_definition", "Thermostat/barostat settings do not implement the planned ensemble.", "Correct coupling fields."))
    if ensemble == "npt" and pcoupl == "berendsen":
        findings.append(finding("GROMACS.INPUT.BERENDSEN_PRODUCTION", "integrator_and_coupling_definition", "Berendsen pressure coupling cannot support a production NPT ensemble claim.", "Choose and justify a production-capable barostat."))
    restart_mode = plan["restart"]["mode"]
    gen_vel = mdp.get("gen-vel", "").casefold()
    continuation = mdp.get("continuation", "").casefold()
    if restart_mode == "new":
        seed = mdp.get("gen-seed")
        if continuation not in {"no", "false"} or gen_vel not in {"yes", "true"} or seed is None:
            findings.append(finding("GROMACS.INPUT.SEED_POLICY", "initial_state_and_seed", "A new run must explicitly generate velocities with a seed and no continuation.", "Set continuation=no, gen-vel=yes, and gen-seed."))
        else:
            try:
                if int(seed) != plan["seed"]["value"] or int(seed) < 0:
                    raise ValueError
            except ValueError:
                findings.append(finding("GROMACS.INPUT.SEED_POLICY", "initial_state_and_seed", "MDP gen-seed does not match the planned nonnegative seed.", "Use the exact planned seed."))
    else:
        if continuation not in {"yes", "true"} or gen_vel not in {"no", "false"} or "gen-seed" in mdp:
            findings.append(finding("GROMACS.RESTART.LINEAGE_MISSING", "restart_lineage", "Checkpoint continuation must preserve state and not regenerate velocities.", "Use continuation=yes, gen-vel=no, and remove gen-seed."))
    for key, planned_key in (("nstlog", "log_interval_steps"), ("nstenergy", "energy_interval_steps"), ("nstxout-compressed", "trajectory_interval_steps")):
        try:
            if int(mdp.get(key, "-1")) != plan["output"][planned_key]:
                raise ValueError
        except ValueError:
            findings.append(finding("GROMACS.INPUT.OUTPUT_CADENCE", "trajectory_integrity", f"{key} does not match the plan.", "Use the predeclared output cadence."))
    coordinate_atoms = frames[0]["atom_count"] if frames else None
    if topology_atoms is None or coordinate_atoms != topology_atoms:
        findings.append(finding("GROMACS.INPUT.ATOM_COUNT_MISMATCH", "system_topology_integrity", "Coordinate and topology atom counts do not agree.", "Repair system/topology identity."))
    evidence_items.extend([evidence(args.plan, "plan-report"), evidence(args.mdp, "mdp"), evidence(args.coordinates, "coordinates")])
    inventory = {
        "plan_id": plan_report["plan_id"],
        "atom_count": coordinate_atoms,
        "site_order": frames[0]["sites"] if frames else [],
        "topology_file_count": len(closure),
        "topology_atom_count": topology_atoms,
        "expected_final_step": expected_steps,
        "mdp": mdp,
    }
    return make_report(
        "audit-input",
        findings,
        evidence_items,
        inventory,
        extra={
            "plan_id": plan_report["plan_id"],
            "inventory": inventory,
            "upstream": {"plan_report_raw_sha256": plan_raw_sha256},
        },
    )


def load_passing_audit(path: Path, command: str, plan_id: str) -> tuple[dict[str, Any], str]:
    report, raw_sha256 = load_verified_upstream(path, command)
    if report.get("plan_id") != plan_id:
        raise GuardFailure("GROMACS.EVIDENCE.NOT_PASSING", f"A passing {command} report bound to this plan is required.")
    return report, raw_sha256


def autocorrelation_stats(values: list[float]) -> dict[str, float | int]:
    count = len(values)
    mean = statistics.fmean(values)
    if count < 2:
        return {"count": count, "mean": mean, "standard_deviation": 0.0, "tau_int": float(count), "effective_sample_size": 1.0, "block_size": 1, "block_count": 1, "standard_error": float("inf")}
    variance = sum((value - mean) ** 2 for value in values) / count
    rho_sum = 0.0
    if variance > 0:
        for lag in range(1, min(count // 2, 1000) + 1):
            covariance = sum((values[i] - mean) * (values[i + lag] - mean) for i in range(count - lag)) / (count - lag)
            rho = covariance / variance
            if not math.isfinite(rho) or rho <= 0:
                break
            rho_sum += rho
    tau = max(1.0, 1.0 + 2.0 * rho_sum)
    ess = max(1.0, count / tau)
    block_size = max(1, math.ceil(tau))
    blocks = [statistics.fmean(values[index:index + block_size]) for index in range(0, count, block_size) if len(values[index:index + block_size]) == block_size]
    if len(blocks) >= 2:
        standard_error = statistics.stdev(blocks) / math.sqrt(len(blocks))
    else:
        standard_error = float("inf")
    return {
        "count": count,
        "mean": mean,
        "standard_deviation": statistics.stdev(values),
        "tau_int": tau,
        "effective_sample_size": ess,
        "block_size": block_size,
        "block_count": len(blocks),
        "standard_error": standard_error,
    }


def parse_series(path: Path, plan: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    text = read_text(path)
    reader = csv.DictReader(text.splitlines())
    findings: list[dict[str, str]] = []
    expected_columns = {"step", *(item["name"] for item in plan["observables"])}
    if reader.fieldnames is None or set(reader.fieldnames) != expected_columns:
        return {}, [finding("GROMACS.SAMPLING.COLUMNS", "sampling_sufficiency", "Series columns do not exactly match step plus planned observables.", "Provide a content-bound normalized series.")]
    rows: list[dict[str, float]] = []
    last_step = -1
    try:
        for raw in reader:
            step = int(raw["step"])
            if step <= last_step:
                raise ValueError
            converted = {"step": float(step)}
            for observable in plan["observables"]:
                value = float(raw[observable["name"]])
                if not math.isfinite(value):
                    raise ValueError
                converted[observable["name"]] = value
            rows.append(converted)
            last_step = step
    except (TypeError, ValueError, KeyError):
        return {}, [finding("GROMACS.SAMPLING.INVALID_SERIES", "sampling_sufficiency", "Series rows are non-finite, malformed, or nonmonotonic.", "Regenerate the normalized series from bound output.")]
    cutoff = plan["equilibration"]["steps"]
    production = [row for row in rows if row["step"] > cutoff]
    if not production:
        return {}, [finding("GROMACS.SAMPLING.NO_PRODUCTION", "sampling_sufficiency", "No samples remain after the predeclared equilibration cutoff.", "Produce the planned production samples.")]
    metrics: dict[str, Any] = {"equilibration_cutoff_step": cutoff, "raw_sample_count": len(rows), "production_sample_count": len(production), "observables": {}}
    for observable in plan["observables"]:
        stats = autocorrelation_stats([row[observable["name"]] for row in production])
        metrics["observables"][observable["name"]] = {"unit": observable["unit"], **stats}
        if stats["effective_sample_size"] < observable["minimum_effective_samples"]:
            findings.append(finding("GROMACS.SAMPLING.INSUFFICIENT_ESS", "sampling_sufficiency", f"Effective sample size is too small for {observable['name']}.", "Extend production or add independent replicas under the fixed protocol."))
        if not math.isfinite(float(stats["standard_error"])) or stats["standard_error"] > observable["max_standard_error"]:
            findings.append(finding("GROMACS.SAMPLING.UNCERTAINTY_EXCEEDED", "statistical_convergence", f"Block-mean uncertainty exceeds the plan for {observable['name']}.", "Increase independent sampling or revise the accepted plan before execution."))
    return metrics, findings


def command_audit_output(args: argparse.Namespace) -> dict[str, Any]:
    plan_report, plan, plan_raw_sha256 = load_passing_plan(args.plan)
    input_audit, input_raw_sha256 = load_passing_audit(args.input_audit, "audit-input", plan_report["plan_id"])
    if input_audit["upstream"]["plan_report_raw_sha256"] != plan_raw_sha256:
        raise GuardFailure("GROMACS.UPSTREAM.LINEAGE_MISMATCH", "Input audit is not bound to the exact raw plan report.")
    log = read_text(args.log)
    findings: list[dict[str, str]] = []
    versions = re.findall(r"GROMACS:\s+gmx\s+mdrun,\s+version\s+([^\s]+)", log, re.IGNORECASE)
    terminals = len(re.findall(r"Finished\s+mdrun", log, re.IGNORECASE))
    if len(versions) != 1 or terminals != 1:
        findings.append(finding("GROMACS.OUTPUT.TRUNCATED_OR_CONCATENATED", "execution_completion", "The log does not contain exactly one version banner and terminal marker.", "Provide one complete unconcatenated log."))
    elif versions[0] != plan["gromacs_version"]:
        findings.append(finding("GROMACS.OUTPUT.VERSION_MISMATCH", "execution_completion", "The mdrun version does not match the plan.", "Use a matching plan/manual/build."))
    adverse = re.findall(r"Fatal error|LINCS WARNING|SETTLE.*warning|constraint.*warning|segmentation|terminated|\bnan\b|\binf\b", log, re.IGNORECASE)
    if adverse:
        findings.append(finding("GROMACS.OUTPUT.ADVERSE_MARKER", "output_warnings", "The log contains a fatal, constraint, non-finite, or termination marker.", "Diagnose the first adverse event; do not suppress it."))
    steps = [int(value) for value in re.findall(r"(?im)^\s*Step\s*[=: ]\s*(\d+)\s*$", log)]
    expected_step = input_audit["inventory"]["expected_final_step"]
    if not steps or steps[-1] != expected_step:
        findings.append(finding("GROMACS.OUTPUT.STEP_MISMATCH", "execution_completion", "The last explicit log step does not match the plan.", "Provide a log reaching the planned terminal step."))
    sampling, sampling_findings = parse_series(args.series, plan)
    findings.extend(sampling_findings)
    evidence_items = [evidence(args.plan, "plan-report"), evidence(args.input_audit, "input-audit"), evidence(args.log, "mdrun-log"), evidence(args.series, "normalized-series")]
    metrics = {"version_banners": versions, "terminal_marker_count": terminals, "last_step": steps[-1] if steps else None, "expected_final_step": expected_step, "sampling": sampling}
    return make_report(
        "audit-output",
        findings,
        evidence_items,
        metrics,
        extra={
            "plan_id": plan_report["plan_id"],
            "upstream": {
                "plan_report_raw_sha256": plan_raw_sha256,
                "input_report_raw_sha256": input_raw_sha256,
            },
        },
    )


def command_audit_trajectory(args: argparse.Namespace) -> dict[str, Any]:
    plan_report, plan, plan_raw_sha256 = load_passing_plan(args.plan)
    input_audit, input_raw_sha256 = load_passing_audit(args.input_audit, "audit-input", plan_report["plan_id"])
    output_audit, output_raw_sha256 = load_passing_audit(args.output_audit, "audit-output", plan_report["plan_id"])
    if (
        input_audit["upstream"]["plan_report_raw_sha256"] != plan_raw_sha256
        or output_audit["upstream"]["plan_report_raw_sha256"] != plan_raw_sha256
        or output_audit["upstream"]["input_report_raw_sha256"] != input_raw_sha256
    ):
        raise GuardFailure("GROMACS.UPSTREAM.LINEAGE_MISMATCH", "Upstream reports do not bind one exact raw-byte lineage.")
    lineage = {
        "plan_report_raw_sha256": plan_raw_sha256,
        "input_report_raw_sha256": input_raw_sha256,
        "output_report_raw_sha256": output_raw_sha256,
    }
    if args.trajectory.suffix.casefold() != ".gro":
        findings = [finding("GROMACS.TRAJECTORY.UNSUPPORTED_FORMAT", "trajectory_integrity", "Only text GRO frame sequences are supported offline.", "Use a future version-pinned official adapter for binary trajectories.", kind="incomplete")]
        evidence_items = [
            evidence(args.plan, "plan-report"),
            evidence(args.input_audit, "input-audit"),
            evidence(args.output_audit, "output-audit"),
            evidence(args.trajectory, "trajectory"),
        ]
        return make_report("audit-trajectory", findings, evidence_items, {}, maturity="unsupported", extra={"plan_id": plan_report["plan_id"], "upstream": lineage})
    frames = parse_gro(args.trajectory)
    findings: list[dict[str, str]] = []
    expected_sites = input_audit["inventory"]["site_order"]
    expected_atoms = input_audit["inventory"]["atom_count"]
    for frame in frames:
        if frame["atom_count"] != expected_atoms or frame["sites"] != expected_sites:
            findings.append(finding("GROMACS.TRAJECTORY.SITE_ORDER_MISMATCH", "trajectory_integrity", "Trajectory atom count or site order differs from the audited system.", "Restore exact topology/site mapping."))
            break
    times = [frame["time_ps"] for frame in frames]
    if any(value is None or not math.isfinite(value) for value in times):
        findings.append(finding("GROMACS.TRAJECTORY.TIME_NONMONOTONIC", "trajectory_integrity", "Every GRO frame title must contain a finite t= value.", "Create a hash-bound frame index with explicit time."))
    else:
        numeric_times = [float(value) for value in times]
        expected_dt = plan["output"]["trajectory_interval_steps"] * plan["timestep_ps"]
        if any(numeric_times[index] <= numeric_times[index - 1] or not math.isclose(numeric_times[index] - numeric_times[index - 1], expected_dt, rel_tol=1e-8, abs_tol=1e-10) for index in range(1, len(numeric_times))):
            findings.append(finding("GROMACS.TRAJECTORY.TIME_NONMONOTONIC", "trajectory_integrity", "Trajectory times are nonmonotonic or violate the planned cadence.", "Audit segment gaps/overlaps and output cadence."))
    if len(frames) != plan["output"]["expected_trajectory_frames"]:
        findings.append(finding("GROMACS.TRAJECTORY.FRAME_INVALID", "trajectory_integrity", "Trajectory frame count does not match the plan.", "Provide the complete frame sequence or record a segment gap."))
    cell_mode = "variable" if any(frame["box"] != frames[0]["box"] for frame in frames[1:]) else "fixed"
    evidence_items = [evidence(args.plan, "plan-report"), evidence(args.input_audit, "input-audit"), evidence(args.output_audit, "output-audit"), evidence(args.trajectory, "trajectory")]
    metrics = {
        "format": "gro",
        "frame_count": len(frames),
        "atom_count": expected_atoms,
        "site_order_sha256": canonical_hash(expected_sites),
        "time_unit": "ps",
        "first_time": times[0] if times else None,
        "last_time": times[-1] if times else None,
        "cell_mode": cell_mode,
        "pbc": plan["pbc"],
        "wrapped_coordinates": True,
        "unwrapped_coordinates": False,
        "velocities_all_frames": all(frame["velocities"] for frame in frames),
        "handoff_contract": "atomistic-trajectory-manifest@1.0",
        "handoff_ready": False,
        "handoff_blocker": "Required upstream structure/topology/run/frame-index record references are not created by this candidate.",
    }
    return make_report("audit-trajectory", findings, evidence_items, metrics, maturity="format-fixture-validated", extra={"plan_id": plan_report["plan_id"], "upstream": lineage})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan", help="validate and freeze an offline simulation plan")
    plan.add_argument("--request", type=Path, required=True)
    plan.add_argument("--out", type=Path)
    audit_input = subparsers.add_parser("audit-input", help="audit a conservative GROMACS text-input core")
    audit_input.add_argument("--plan", type=Path, required=True)
    audit_input.add_argument("--mdp", type=Path, required=True)
    audit_input.add_argument("--coordinates", type=Path, required=True)
    audit_input.add_argument("--topology", type=Path, required=True)
    audit_input.add_argument("--provenance", type=Path, required=True)
    audit_input.add_argument("--out", type=Path)
    audit_output = subparsers.add_parser("audit-output", help="audit log completion and normalized sampling series")
    audit_output.add_argument("--plan", type=Path, required=True)
    audit_output.add_argument("--input-audit", type=Path, required=True)
    audit_output.add_argument("--log", type=Path, required=True)
    audit_output.add_argument("--series", type=Path, required=True)
    audit_output.add_argument("--out", type=Path)
    trajectory = subparsers.add_parser("audit-trajectory", help="audit a text GRO frame sequence")
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
            report = command_plan(args)
        elif args.command == "audit-input":
            report = command_audit_input(args)
        elif args.command == "audit-output":
            report = command_audit_output(args)
        else:
            report = command_audit_trajectory(args)
        return emit(report, args.out)
    except GuardFailure as exc:
        report = make_report(
            args.command,
            [finding(exc.code, "deterministic_preflight", exc.message, "Correct the evidence and rerun.", kind="incomplete" if exc.incomplete else "fail")],
            [],
            {},
        )
        return emit(report, None)
    except Exception:
        print("ERROR: gromacs_guard internal failure; path details are redacted", file=sys.stderr)
        return 4
    finally:
        _reset_snapshot_cache()


if __name__ == "__main__":
    raise SystemExit(main())
