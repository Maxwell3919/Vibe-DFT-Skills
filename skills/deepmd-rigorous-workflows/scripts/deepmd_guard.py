#!/usr/bin/env python3
"""Offline provider-specific gates for the development DeePMD-kit workflow."""

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
from typing import Any, Iterable


sys.dont_write_bytecode = True

SCHEMA_VERSION = "candidate-1.0"
DEEPMD_VERSION = "3.1.3"
BACKENDS = {"pytorch", "tensorflow", "jax", "paddle"}
TRAINING_BACKENDS = {"pytorch", "tensorflow", "paddle"}
SPLITS = ("train", "validation", "test", "ood")
MAX_BYTES = 16 * 1024 * 1024
MAX_SYSTEMS = 100000
MAX_ARRAY_BYTES = 2**63 - 1
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ELEMENT = re.compile(r"^[A-Z][a-z]?$|^D$|^T$")
UNITS = {"energy": "eV", "forces": "eV/angstrom", "virial": "eV"}
METRIC_NAMES = {
    "energy_rmse_ev_per_atom",
    "force_rmse_ev_per_angstrom",
}
REPORT_FIELDS = {
    "schema_version",
    "contract_name",
    "command",
    "candidate_lifecycle",
    "status",
    "action_state",
    "claim_ceiling",
    "future_gate_ceiling",
    "gates",
    "findings",
    "smallest_next_action",
    "evidence",
    "observations",
    "limitations",
}
REPORT_PROFILES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "audit-layout": (
        "local_gate_passed_limited",
        "input_gates_only",
        ("version-backend-type-map", "array-identity-shape-dtype", "group-disjoint-splits", "protocol-units-licenses"),
    ),
    "audit-config": (
        "needs_authorization",
        "input_gates_only",
        ("layout-version-backend-type-map", "descriptor-fitting", "learning-loss-training", "schema-environment-restart-thresholds"),
    ),
    "audit-run": (
        "local_gate_passed_limited",
        "technical_run_gates_only",
        ("upstream-version-backend-environment", "authorization-completion", "artifacts-restart", "finite-training-validation-metrics"),
    ),
    "audit-model": (
        "needs_authorization",
        "technical_run_gates_only",
        ("run-config-lineage", "artifact-identity", "units-provider-config-schema", "license-separation"),
    ),
}


class BoundaryError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reject_constant(_: str) -> None:
    raise BoundaryError("JSON_NONFINITE", "JSON contains a non-finite number.")


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BoundaryError("JSON_DUPLICATE_KEY", "JSON contains a duplicate object key.")
        result[key] = value
    return result


def _stable_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        stat.S_IFMT(value.st_mode),
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _directory_identity(value: os.stat_result) -> tuple[int, int, int]:
    return (value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode))


def _directory_chain(path: Path, kind: str) -> tuple[Path, list[int], list[tuple[int, str, int, os.stat_result]]]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory is None or nonblock is None:
        raise BoundaryError(f"{kind}_UNSAFE_HOST", "This host lacks required no-follow directory support.")
    absolute = path.absolute()
    if not absolute.anchor:
        raise BoundaryError(f"{kind}_UNREADABLE", f"{kind} path is not absolute.")
    flags = os.O_RDONLY | directory | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0)
    descriptors: list[int] = []
    edges: list[tuple[int, str, int, os.stat_result]] = []
    try:
        root = Path(absolute.anchor)
        root_before = root.lstat()
        root_fd = os.open(root, flags)
        descriptors.append(root_fd)
        root_open = os.fstat(root_fd)
        if not stat.S_ISDIR(root_before.st_mode) or _directory_identity(root_before) != _directory_identity(root_open):
            raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} root identity is unstable.")
        current = root_fd
        for component in absolute.parts[1:]:
            before = os.stat(component, dir_fd=current, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise BoundaryError(f"{kind}_NOT_REGULAR", f"{kind} parent must be a real directory.")
            child = os.open(component, flags, dir_fd=current)
            opened = os.fstat(child)
            if _directory_identity(before) != _directory_identity(opened):
                os.close(child)
                raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} parent identity is unstable.")
            descriptors.append(child)
            edges.append((current, component, child, opened))
            current = child
        return absolute, descriptors, edges
    except BoundaryError:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise
    except OSError as exc:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise BoundaryError(f"{kind}_UNREADABLE", f"{kind} path could not be traversed safely.") from exc


def _revalidate_directories(
    absolute: Path,
    descriptors: list[int],
    edges: list[tuple[int, str, int, os.stat_result]],
    kind: str,
) -> None:
    root_now = Path(absolute.anchor).lstat()
    if _directory_identity(root_now) != _directory_identity(os.fstat(descriptors[0])):
        raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} root changed during access.")
    for parent_fd, component, child_fd, opened in edges:
        anchored = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
        current = os.fstat(child_fd)
        if not stat.S_ISDIR(anchored.st_mode) or (
            _directory_identity(anchored) != _directory_identity(opened)
            or _directory_identity(current) != _directory_identity(opened)
        ):
            raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} parent changed during access.")


def read_json(path: Path, kind: str) -> tuple[dict[str, Any], bytes]:
    absolute, descriptors, edges = _directory_chain(path.absolute().parent, kind)
    file_fd: int | None = None
    try:
        parent_fd = descriptors[-1]
        name = path.absolute().name
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise BoundaryError(f"{kind}_NOT_REGULAR", f"{kind} evidence must be a regular file.")
        if before.st_nlink != 1:
            raise BoundaryError(f"{kind}_LINKED", f"{kind} evidence must not be hard-linked.")
        if before.st_size > MAX_BYTES:
            raise BoundaryError(f"{kind}_TOO_LARGE", f"{kind} evidence exceeds the size limit.")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW") | getattr(os, "O_NONBLOCK") | getattr(os, "O_CLOEXEC", 0)
        file_fd = os.open(name, flags, dir_fd=parent_fd)
        opened = os.fstat(file_fd)
        if _stable_identity(before) != _stable_identity(opened):
            raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} evidence changed before reading.")
        chunks: list[bytes] = []
        total = 0
        while total <= MAX_BYTES:
            chunk = os.read(file_fd, min(65536, MAX_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        after = os.fstat(file_fd)
        final = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        _revalidate_directories(absolute, descriptors, edges, kind)
        raw = b"".join(chunks)
        if len(raw) > MAX_BYTES:
            raise BoundaryError(f"{kind}_TOO_LARGE", f"{kind} evidence exceeds the size limit.")
        if (
            _stable_identity(opened) != _stable_identity(after)
            or _stable_identity(after) != _stable_identity(final)
            or not stat.S_ISREG(after.st_mode)
            or after.st_nlink != 1
            or len(raw) != opened.st_size
        ):
            raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} evidence changed while reading.")
    except BoundaryError:
        raise
    except OSError as exc:
        raise BoundaryError(f"{kind}_UNREADABLE", f"{kind} evidence is unreadable.") from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    if raw.startswith(b"\xef\xbb\xbf"):
        raise BoundaryError(f"{kind}_BOM", f"{kind} JSON must not contain a BOM.")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    except BoundaryError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BoundaryError(f"{kind}_INVALID_JSON", f"{kind} JSON is invalid.") from exc
    if not isinstance(value, dict):
        raise BoundaryError(f"{kind}_NOT_OBJECT", f"{kind} JSON root must be an object.")
    return value, raw


def _fd_matches_payload(descriptor: int, payload: bytes, expected_links: int) -> bool:
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != expected_links or metadata.st_size != len(payload):
        return False
    hasher = hashlib.sha256()
    offset = 0
    while offset < len(payload):
        chunk = os.pread(descriptor, min(65536, len(payload) - offset), offset)
        if not chunk:
            return False
        hasher.update(chunk)
        offset += len(chunk)
    return offset == len(payload) and hasher.digest() == hashlib.sha256(payload).digest()


def _inode_matches(left: os.stat_result, right: os.stat_result, *, links: int) -> bool:
    return (
        stat.S_ISREG(left.st_mode)
        and stat.S_ISREG(right.st_mode)
        and left.st_nlink == links
        and right.st_nlink == links
        and (left.st_dev, left.st_ino, left.st_size) == (right.st_dev, right.st_ino, right.st_size)
    )


def write_json(path: Path, value: dict[str, Any]) -> None:
    try:
        payload = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BoundaryError("OUTPUT_WRITE_FAILED", "Output report could not be serialized safely.") from exc
    target = path.absolute()
    if not target.name or target.name in {".", ".."}:
        raise BoundaryError("OUTPUT_TARGET_INVALID", "Output filename is invalid.")
    absolute, descriptors, edges = _directory_chain(target.parent, "OUTPUT_PARENT")
    parent_fd = descriptors[-1]
    stage_fd: int | None = None
    stage_name: str | None = None
    published_identity: tuple[int, int] | None = None
    try:
        try:
            os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise BoundaryError("OUTPUT_EXISTS", "Output report already exists; overwrite is refused.")
        for _ in range(32):
            candidate = f".deepmd-guard-{secrets.token_hex(12)}.tmp"
            try:
                stage_fd = os.open(
                    candidate,
                    os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW") | getattr(os, "O_CLOEXEC", 0),
                    0o600,
                    dir_fd=parent_fd,
                )
            except FileExistsError:
                continue
            stage_name = candidate
            break
        if stage_fd is None or stage_name is None:
            raise BoundaryError("OUTPUT_WRITE_FAILED", "A private output staging file could not be created.")
        offset = 0
        while offset < len(payload):
            written = os.write(stage_fd, payload[offset:])
            if written <= 0:
                raise OSError("short report write")
            offset += written
        os.fsync(stage_fd)
        staged = os.fstat(stage_fd)
        if not _fd_matches_payload(stage_fd, payload, 1):
            raise BoundaryError("OUTPUT_WRITE_FAILED", "Staged report identity or payload is invalid.")
        _revalidate_directories(absolute, descriptors, edges, "OUTPUT_PARENT")
        try:
            os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise BoundaryError("OUTPUT_EXISTS", "Output report appeared during staging; overwrite is refused.")
        stage_path = os.stat(stage_name, dir_fd=parent_fd, follow_symlinks=False)
        if not _inode_matches(stage_path, staged, links=1):
            raise BoundaryError("OUTPUT_WRITE_FAILED", "Staging filename changed before publication.")
        try:
            os.link(stage_name, target.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd, follow_symlinks=False)
        except FileExistsError as exc:
            raise BoundaryError("OUTPUT_EXISTS", "Output report appeared during publication; overwrite is refused.") from exc
        published = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        published_identity = (published.st_dev, published.st_ino)
        named_stage = os.stat(stage_name, dir_fd=parent_fd, follow_symlinks=False)
        current_fd = os.fstat(stage_fd)
        if (
            not _inode_matches(published, current_fd, links=2)
            or not _inode_matches(named_stage, current_fd, links=2)
            or not _fd_matches_payload(stage_fd, payload, 2)
        ):
            raise BoundaryError("OUTPUT_WRITE_FAILED", "Published report is not the staged payload.")
        os.unlink(stage_name, dir_fd=parent_fd)
        stage_name = None
        final = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        if not _inode_matches(final, os.fstat(stage_fd), links=1) or not _fd_matches_payload(stage_fd, payload, 1):
            raise BoundaryError("OUTPUT_WRITE_FAILED", "Published report identity changed after installation.")
        _revalidate_directories(absolute, descriptors, edges, "OUTPUT_PARENT")
        os.fsync(parent_fd)
        published_identity = None
    except BoundaryError:
        if published_identity is not None:
            try:
                current = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
                if (current.st_dev, current.st_ino) == published_identity:
                    os.unlink(target.name, dir_fd=parent_fd)
            except OSError:
                pass
        raise
    except OSError as exc:
        if published_identity is not None:
            try:
                current = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
                if (current.st_dev, current.st_ino) == published_identity:
                    os.unlink(target.name, dir_fd=parent_fd)
            except OSError:
                pass
        raise BoundaryError("OUTPUT_WRITE_FAILED", "Output report could not be written safely.") from exc
    finally:
        if stage_name is not None:
            try:
                current = os.stat(stage_name, dir_fd=parent_fd, follow_symlinks=False)
                allowed = published_identity == (current.st_dev, current.st_ino)
                if stage_fd is not None:
                    opened = os.fstat(stage_fd)
                    allowed = allowed or (current.st_dev, current.st_ino) == (opened.st_dev, opened.st_ino)
                if allowed:
                    os.unlink(stage_name, dir_fd=parent_fd)
            except OSError:
                pass
        if stage_fd is not None:
            os.close(stage_fd)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def ensure_output_is_distinct(path: Path, evidence_paths: Iterable[Path]) -> None:
    """Refuse to replace an evidence file after it has been read."""

    output_identity = path.absolute()
    for evidence_path in evidence_paths:
        if output_identity == evidence_path.absolute():
            raise BoundaryError("OUTPUT_ALIASES_EVIDENCE", "Output report must not replace an evidence file.")


def is_id(value: object) -> bool:
    return isinstance(value, str) and SAFE_ID.fullmatch(value) is not None


def is_sha(value: object) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def is_int(value: object, minimum: int = 0, maximum: int = 2**63 - 1) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum


def is_number(value: object, *, positive: bool = False) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        return False
    return value > 0 if positive else value >= 0


def exact(value: object, fields: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == fields


def finding(code: str, message: str, next_action: str) -> dict[str, str]:
    return {"code": code, "message": message, "next_action": next_action}


def gate(identifier: str, passed: bool, codes: Iterable[str] = ()) -> dict[str, Any]:
    return {"id": identifier, "status": "pass" if passed else "blocked", "finding_codes": list(codes)}


def make_report(
    command: str,
    findings: list[dict[str, str]],
    gates: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    observations: dict[str, Any] | None,
    next_action: str,
    future_ceiling: str,
    limitations: list[str],
    *,
    action_on_pass: str = "local_gate_passed_limited",
) -> dict[str, Any]:
    passed = not findings
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_name": "deepmd-candidate-audit",
        "command": command,
        "candidate_lifecycle": "development",
        "status": "pass" if passed else "blocked",
        "action_state": action_on_pass if passed else "local_gate_blocked",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": future_ceiling if passed else "no_positive_claim",
        "gates": gates,
        "findings": findings,
        "smallest_next_action": findings[0]["next_action"] if findings else next_action,
        "evidence": evidence,
        "observations": observations,
        "limitations": limitations,
    }


def boundary_report(command: str, error: BoundaryError) -> dict[str, Any]:
    item = finding(error.code, error.message, "Provide a regular bounded strict-JSON evidence file and rerun the same command.")
    return make_report(
        command,
        [item],
        [],
        [],
        None,
        item["next_action"],
        "no_positive_claim",
        ["No array/model payload, provider process, training, inference, or scientific conclusion was accessed."],
    )


def require_pass(value: dict[str, Any], command: str) -> list[dict[str, str]]:
    profile = REPORT_PROFILES.get(command)
    if profile is None:
        return [finding("UPSTREAM_REPORT_PROFILE_UNKNOWN", "Required upstream report profile is unknown.", "Use a reviewed upstream command profile.")]
    expected_action, expected_ceiling, expected_gates = profile
    if set(value) != REPORT_FIELDS or (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("contract_name") != "deepmd-candidate-audit"
        or value.get("command") != command
        or value.get("candidate_lifecycle") != "development"
        or value.get("status") != "pass"
        or value.get("action_state") != expected_action
        or value.get("claim_ceiling") != "no_positive_claim"
        or value.get("future_gate_ceiling") != expected_ceiling
        or value.get("findings") != []
    ):
        return [finding("UPSTREAM_REPORT_INVALID", "Required upstream report is not a canonical pass record.", "Regenerate and resolve the upstream report before continuing.")]
    if value.get("gates") != [gate(identifier, True) for identifier in expected_gates]:
        return [finding("UPSTREAM_REPORT_GATES_INVALID", "Upstream pass gates are missing, reordered, or noncanonical.", "Regenerate the upstream report with the deterministic guard.")]
    evidence = value.get("evidence")
    if (
        not isinstance(evidence, list)
        or not evidence
        or any(
            not exact(item, {"role", "source_label", "sha256", "bytes"})
            or not is_id(item.get("role"))
            or not is_id(item.get("source_label"))
            or not is_sha(item.get("sha256"))
            or not is_int(item.get("bytes"), 1)
            for item in evidence
        )
        or not isinstance(value.get("observations"), dict)
        or not isinstance(value.get("smallest_next_action"), str)
        or not value["smallest_next_action"].strip()
        or not isinstance(value.get("limitations"), list)
        or not value["limitations"]
        or not all(isinstance(item, str) and item.strip() for item in value["limitations"])
    ):
        return [finding("UPSTREAM_REPORT_SHAPE_INVALID", "Upstream evidence, observations, action, or limitations are noncanonical.", "Regenerate the upstream report with the deterministic guard.")]
    return []


def expected_arrays(nframes: int, natoms: int, periodic: bool, virial: bool) -> dict[str, list[int]]:
    # DeePMD's version-matched raw_to_set.sh writes the canonical NPY payloads
    # with one row per frame. Atomic/cartesian and box tensors are flattened on
    # disk; the provider loader restores their logical tensor dimensions.
    result = {
        "coord.npy": [nframes, natoms * 3],
        "energy.npy": [nframes],
        "force.npy": [nframes, natoms * 3],
    }
    if periodic:
        result["box.npy"] = [nframes, 9]
    if virial:
        result["virial.npy"] = [nframes, 9]
    return result


def audit_layout(value: dict[str, Any], raw: bytes) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    fields = {
        "schema_version",
        "deepmd_version",
        "backend",
        "dataset_id",
        "type_map",
        "type_map_sha256",
        "units",
        "reference_protocol_sha256",
        "source_dataset_audit_sha256",
        "virial_policy",
        "licenses",
        "systems",
    }
    if not exact(value, fields):
        findings.append(finding("LAYOUT_FIELDS_INVALID", "Layout fields are missing or unsupported.", "Use the exact portable layout fields."))
    if value.get("schema_version") != SCHEMA_VERSION or not is_id(value.get("dataset_id")):
        findings.append(finding("LAYOUT_IDENTITY_INVALID", "Layout schema or dataset ID is invalid.", "Use the candidate schema and a safe dataset ID."))
    if value.get("deepmd_version") != DEEPMD_VERSION or value.get("backend") not in BACKENDS:
        findings.append(finding("LAYOUT_VERSION_BACKEND_INVALID", "DeePMD version or backend is unsupported.", "Use exact DeePMD 3.1.3 and one explicit registered backend."))
    type_map = value.get("type_map")
    type_map_ok = (
        isinstance(type_map, list)
        and bool(type_map)
        and len(type_map) == len(set(item for item in type_map if isinstance(item, str)))
        and all(isinstance(item, str) and ELEMENT.fullmatch(item) for item in type_map)
        and is_sha(value.get("type_map_sha256"))
    )
    if not type_map_ok:
        findings.append(finding("LAYOUT_TYPE_MAP_INVALID", "Ordered type map or its hash is invalid.", "Provide a unique ordered element map and exact type_map.raw hash."))
        type_map = []
    if value.get("units") != UNITS:
        findings.append(finding("LAYOUT_UNITS_INVALID", "Layout units differ from the exact candidate convention.", "Normalize to eV, eV/angstrom, and eV before layout creation."))
    if not is_sha(value.get("reference_protocol_sha256")):
        findings.append(finding("LAYOUT_REFERENCE_PROTOCOL_INVALID", "Reference protocol hash is missing.", "Bind the exact accepted DFT reference protocol."))
    if not is_sha(value.get("source_dataset_audit_sha256")):
        findings.append(finding("LAYOUT_SOURCE_DATASET_AUDIT_INVALID", "Generic source-dataset audit hash is missing.", "Bind the exact accepted generic MLP dataset-audit report."))
    virial_policy = value.get("virial_policy")
    if virial_policy not in {"all_systems", "absent"}:
        findings.append(finding("LAYOUT_VIRIAL_POLICY_INVALID", "Virial policy is unsupported.", "Choose all_systems or absent."))
    licenses = value.get("licenses")
    if not exact(licenses, {"framework", "backend", "dataset", "reference_data"}) or not all(
        isinstance(licenses.get(key), str) and 0 < len(licenses[key]) <= 128
        for key in ("framework", "backend", "dataset", "reference_data")
    ):
        findings.append(finding("LAYOUT_LICENSES_INVALID", "Framework/backend/dataset/reference licenses are incomplete.", "Record all four license identities independently."))
    systems = value.get("systems")
    if not isinstance(systems, list) or not 4 <= len(systems) <= MAX_SYSTEMS:
        findings.append(finding("LAYOUT_SYSTEM_COUNT_INVALID", "System inventory is missing or outside the bounded range.", "Provide bounded nonempty systems for all four splits."))
    if not isinstance(systems, list) or len(systems) > MAX_SYSTEMS:
        systems = []
    system_fields = {
        "system_id",
        "group_id",
        "split",
        "periodic",
        "nframes",
        "natoms",
        "type_raw_sha256",
        "type_map_raw_sha256",
        "source_frame_index_sha256",
        "arrays",
    }
    system_ids: set[str] = set()
    group_splits: dict[str, set[str]] = {}
    split_system_ids = {name: [] for name in SPLITS}
    array_hashes: set[str] = set()
    source_index_hashes: set[str] = set()
    frame_count = 0
    for system in systems:
        if not exact(system, system_fields):
            findings.append(finding("LAYOUT_SYSTEM_FIELDS_INVALID", "A system metadata item is malformed.", "Regenerate every system item with exact fields."))
            continue
        system_id = system.get("system_id")
        group_id = system.get("group_id")
        split = system.get("split")
        if not is_id(system_id) or system_id in system_ids:
            findings.append(finding("LAYOUT_SYSTEM_ID_DUPLICATE", "System ID is unsafe or duplicated.", "Assign one unique safe system ID."))
        else:
            system_ids.add(system_id)
        if not is_id(group_id) or split not in SPLITS:
            findings.append(finding("LAYOUT_GROUP_OR_SPLIT_INVALID", "Group or split is invalid.", "Assign one safe group and exact split."))
        else:
            group_splits.setdefault(group_id, set()).add(split)
            if is_id(system_id):
                split_system_ids[split].append(system_id)
        periodic = system.get("periodic")
        nframes = system.get("nframes")
        natoms = system.get("natoms")
        if not isinstance(periodic, bool) or not is_int(nframes, 1, 1000000000) or not is_int(natoms, 1, 1000000):
            findings.append(finding("LAYOUT_SYSTEM_SHAPE_INVALID", "System periodicity, frame count, or atom count is invalid.", "Provide explicit bounded system dimensions."))
            continue
        frame_count += nframes
        if not is_sha(system.get("type_raw_sha256")) or system.get("type_map_raw_sha256") != value.get("type_map_sha256"):
            findings.append(finding("LAYOUT_TYPE_FILE_IDENTITY_INVALID", "type.raw or type_map.raw identity is missing or mismatched.", "Bind exact type bytes and the dataset-level ordered type map."))
        source_index_hash = system.get("source_frame_index_sha256")
        if not is_sha(source_index_hash) or source_index_hash in source_index_hashes:
            findings.append(finding("LAYOUT_SOURCE_FRAME_INDEX_INVALID", "Ordered source-frame mapping identity is missing or duplicated.", "Bind each array row to the accepted source frame/label/run records with one exact ordered index hash."))
        else:
            source_index_hashes.add(source_index_hash)
        arrays = system.get("arrays")
        expected = expected_arrays(nframes, natoms, periodic, virial_policy == "all_systems")
        if not isinstance(arrays, list) or len(arrays) != len(expected):
            findings.append(finding("LAYOUT_ARRAY_SET_INVALID", "System array set differs from required arrays.", "Provide every and only required array metadata item."))
            continue
        observed_names: set[str] = set()
        for array in arrays:
            if not exact(array, {"name", "sha256", "bytes", "dtype", "shape"}):
                findings.append(finding("LAYOUT_ARRAY_FIELDS_INVALID", "An array metadata item is malformed.", "Provide exact array name/hash/bytes/dtype/shape fields."))
                continue
            name = array.get("name")
            if name not in expected or name in observed_names:
                findings.append(finding("LAYOUT_ARRAY_NAME_INVALID", "Array name is unexpected or duplicated.", "Use every required array name once."))
                continue
            observed_names.add(name)
            array_hash = array.get("sha256")
            if not is_sha(array_hash) or array_hash in array_hashes or not is_int(array.get("bytes"), 1, MAX_ARRAY_BYTES):
                findings.append(finding("LAYOUT_ARRAY_IDENTITY_INVALID", "Array hash/bytes is invalid or duplicated.", "Bind each exact array payload uniquely."))
            else:
                array_hashes.add(array_hash)
            if array.get("dtype") not in {"float32", "float64"} or array.get("shape") != expected[name]:
                findings.append(finding("LAYOUT_ARRAY_SHAPE_OR_DTYPE_MISMATCH", "Array dtype or shape differs from system dimensions.", "Regenerate array metadata from a trusted header parser."))
            else:
                itemsize = 4 if array["dtype"] == "float32" else 8
                payload_bytes = itemsize * math.prod(expected[name])
                if not is_int(array.get("bytes"), payload_bytes, MAX_ARRAY_BYTES):
                    findings.append(finding("LAYOUT_ARRAY_BYTE_COUNT_IMPOSSIBLE", "Array byte count is smaller than the declared dense payload.", "Regenerate byte count, dtype, and shape metadata from the exact array header."))
        if observed_names != set(expected):
            findings.append(finding("LAYOUT_ARRAY_SET_INVALID", "Required array names are incomplete.", "Provide every required array exactly once."))
    if any(len(splits) > 1 for splits in group_splits.values()):
        findings.append(finding("LAYOUT_GROUP_LEAKAGE", "A correlated system group spans multiple splits.", "Keep each trajectory/relaxation/query group wholly in one split."))
    if any(not split_system_ids[name] for name in SPLITS):
        findings.append(finding("LAYOUT_SPLIT_MISSING", "Train, validation, test, or OOD system inventory is empty.", "Provide nonempty group-disjoint systems for all four roles."))
    return make_report(
        "audit-layout",
        findings,
        [
            gate("version-backend-type-map", not any(item["code"] in {"LAYOUT_VERSION_BACKEND_INVALID", "LAYOUT_TYPE_MAP_INVALID", "LAYOUT_TYPE_FILE_IDENTITY_INVALID"} for item in findings)),
            gate("array-identity-shape-dtype", not any(item["code"].startswith("LAYOUT_ARRAY") or item["code"] == "LAYOUT_SYSTEM_SHAPE_INVALID" for item in findings)),
            gate("group-disjoint-splits", not any(item["code"] in {"LAYOUT_GROUP_LEAKAGE", "LAYOUT_SPLIT_MISSING"} for item in findings)),
            gate("protocol-units-licenses", not any(item["code"] in {"LAYOUT_REFERENCE_PROTOCOL_INVALID", "LAYOUT_SOURCE_DATASET_AUDIT_INVALID", "LAYOUT_SOURCE_FRAME_INDEX_INVALID", "LAYOUT_UNITS_INVALID", "LAYOUT_LICENSES_INVALID"} for item in findings)),
        ],
        [{"role": "deepmd-layout-manifest", "source_label": "layout.json", "sha256": digest(raw), "bytes": len(raw)}],
        {
            "dataset_id": value.get("dataset_id") if is_id(value.get("dataset_id")) else None,
            "deepmd_version": value.get("deepmd_version") if isinstance(value.get("deepmd_version"), str) else None,
            "backend": value.get("backend") if value.get("backend") in BACKENDS else None,
            "type_map": type_map,
            "type_map_sha256": value.get("type_map_sha256") if is_sha(value.get("type_map_sha256")) else None,
            "source_dataset_audit_sha256": value.get("source_dataset_audit_sha256") if is_sha(value.get("source_dataset_audit_sha256")) else None,
            "virial_policy": virial_policy if virial_policy in {"all_systems", "absent"} else None,
            "system_count": len(systems),
            "frame_count": frame_count,
            "split_system_ids": {name: sorted(ids) for name, ids in split_system_ids.items()},
        },
        "Freeze a portable training projection bound to this exact layout-audit report.",
        "input_gates_only",
        [
            "Array, type, structure, label, protocol and license bytes are hash inventories only and were not resolved.",
            "No NumPy header or value, near-duplicate structure, type index, or scientific acceptance was validated.",
        ],
    )


def _positive_int_list(value: object, *, maximum: int = 1000000) -> bool:
    return isinstance(value, list) and bool(value) and len(value) <= 32 and all(is_int(item, 1, maximum) for item in value)


def audit_config(value: dict[str, Any], raw: bytes, layout: dict[str, Any], layout_raw: bytes) -> dict[str, Any]:
    findings = require_pass(layout, "audit-layout")
    fields = {
        "schema_version",
        "deepmd_version",
        "backend",
        "workflow_id",
        "mode",
        "layout_audit_sha256",
        "environment_sha256",
        "provider_schema_sha256",
        "type_map",
        "training_systems",
        "validation_systems",
        "descriptor",
        "fitting_net",
        "learning_rate",
        "loss",
        "training",
        "restart_parent_checkpoint_sha256",
        "restart_parent_run_audit_sha256",
        "evaluation_thresholds",
    }
    if not exact(value, fields):
        findings.append(finding("CONFIG_FIELDS_INVALID", "Training projection fields are missing or unsupported.", "Use the exact portable projection fields."))
    if value.get("schema_version") != SCHEMA_VERSION or not is_id(value.get("workflow_id")):
        findings.append(finding("CONFIG_IDENTITY_INVALID", "Projection schema or workflow ID is invalid.", "Use the candidate schema and safe workflow ID."))
    layout_obs = layout.get("observations") if isinstance(layout.get("observations"), dict) else {}
    if value.get("deepmd_version") != layout_obs.get("deepmd_version") or value.get("backend") != layout_obs.get("backend") or value.get("type_map") != layout_obs.get("type_map"):
        findings.append(finding("CONFIG_LAYOUT_IDENTITY_MISMATCH", "Version, backend, or type map differs from layout.", "Use exact audited layout identity."))
    if value.get("backend") not in TRAINING_BACKENDS:
        findings.append(finding("CONFIG_BACKEND_TRAINING_UNSUPPORTED", "The selected backend is not registered for training in this projection.", "Use the exact PyTorch, TensorFlow, or Paddle training backend, or add a version-matched capability profile before planning."))
    if value.get("layout_audit_sha256") != digest(layout_raw):
        findings.append(finding("CONFIG_LAYOUT_HASH_MISMATCH", "Projection does not bind exact layout-audit bytes.", "Use the exact upstream report SHA-256."))
    if not is_sha(value.get("environment_sha256")) or not is_sha(value.get("provider_schema_sha256")):
        findings.append(finding("CONFIG_ENV_OR_SCHEMA_HASH_INVALID", "Environment or provider-schema hash is missing.", "Bind exact environment and version-generated provider schema evidence."))
    split_ids = layout_obs.get("split_system_ids") if isinstance(layout_obs.get("split_system_ids"), dict) else {}
    train_ids = value.get("training_systems")
    val_ids = value.get("validation_systems")
    if train_ids != split_ids.get("train") or val_ids != split_ids.get("validation") or not isinstance(train_ids, list) or not isinstance(val_ids, list):
        findings.append(finding("CONFIG_SYSTEM_SPLIT_MISMATCH", "Training/validation systems differ from audited split roles.", "Use every and only audited train/validation system ID."))
    descriptor = value.get("descriptor")
    descriptor_ok = exact(descriptor, {"type", "rcut", "rcut_smth", "sel", "neurons", "axis_neuron", "seed"})
    if descriptor_ok:
        descriptor_ok = (
            descriptor.get("type") == "se_e2_a"
            and is_number(descriptor.get("rcut"), positive=True)
            and is_number(descriptor.get("rcut_smth"), positive=True)
            and descriptor["rcut_smth"] < descriptor["rcut"] <= 20
            and _positive_int_list(descriptor.get("sel"))
            and len(descriptor["sel"]) == len(layout_obs.get("type_map", []))
            and _positive_int_list(descriptor.get("neurons"))
            and is_int(descriptor.get("axis_neuron"), 1, 1000000)
            and is_int(descriptor.get("seed"), 0, 2**32 - 1)
        )
    if not descriptor_ok:
        findings.append(finding("CONFIG_DESCRIPTOR_INVALID", "Descriptor projection is incomplete or outside the se_e2_a profile.", "Provide explicit cutoff, smoothing, per-type selection, network and seed."))
    fitting = value.get("fitting_net")
    fitting_ok = exact(fitting, {"type", "neurons", "resnet_dt", "seed"}) and fitting.get("type") == "ener" and _positive_int_list(fitting.get("neurons")) and isinstance(fitting.get("resnet_dt"), bool) and is_int(fitting.get("seed"), 0, 2**32 - 1)
    if not fitting_ok:
        findings.append(finding("CONFIG_FITTING_INVALID", "Energy fitting projection is incomplete.", "Provide explicit network, residual toggle and seed."))
    learning = value.get("learning_rate")
    learning_ok = exact(learning, {"type", "start", "stop", "decay_steps"}) and learning.get("type") == "exp" and is_number(learning.get("start"), positive=True) and is_number(learning.get("stop"), positive=True) and learning["start"] > learning["stop"] and is_int(learning.get("decay_steps"), 1, 1000000000)
    if not learning_ok:
        findings.append(finding("CONFIG_LEARNING_RATE_INVALID", "Learning-rate schedule is incomplete or invalid.", "Provide explicit decreasing exponential schedule."))
    loss = value.get("loss")
    loss_keys = {"start_energy", "limit_energy", "start_force", "limit_force", "start_virial", "limit_virial"}
    loss_ok = exact(loss, loss_keys) and all(is_number(loss.get(key)) for key in loss_keys) and (loss.get("start_energy", 0) + loss.get("start_force", 0) > 0) and (loss.get("limit_energy", 0) + loss.get("limit_force", 0) > 0)
    if loss_ok and layout_obs.get("virial_policy") == "absent" and (loss.get("start_virial") != 0 or loss.get("limit_virial") != 0):
        loss_ok = False
    if not loss_ok:
        findings.append(finding("CONFIG_LOSS_INVALID", "Loss schedule is incomplete or conflicts with label coverage.", "Provide all explicit energy/force/virial weights and zero virial weights when absent."))
    training = value.get("training")
    training_ok = exact(training, {"seed", "numb_steps", "disp_freq", "save_freq", "training_batch_size", "validation_batch_size"}) and is_int(training.get("seed"), 0, 2**32 - 1) and is_int(training.get("numb_steps"), 1, 10**12) and is_int(training.get("disp_freq"), 1, 10**12) and is_int(training.get("save_freq"), 1, 10**12) and training["disp_freq"] <= training["numb_steps"] and training["save_freq"] <= training["numb_steps"] and is_int(training.get("training_batch_size"), 1, 1000000) and is_int(training.get("validation_batch_size"), 1, 1000000)
    if not training_ok:
        findings.append(finding("CONFIG_TRAINING_INVALID", "Training seed, steps, cadence or batches are incomplete.", "Provide all bounded training controls explicitly."))
    mode = value.get("mode")
    parent = value.get("restart_parent_checkpoint_sha256")
    parent_run = value.get("restart_parent_run_audit_sha256")
    if mode not in {"from_scratch", "restart"} or (mode == "from_scratch" and (parent is not None or parent_run is not None)) or (mode == "restart" and (not is_sha(parent) or not is_sha(parent_run) or parent == parent_run)):
        findings.append(finding("CONFIG_RESTART_LINEAGE_INVALID", "Restart mode, parent checkpoint, or parent run-audit identity conflict.", "Omit both parents for from-scratch or bind distinct exact checkpoint and parent run-audit SHA-256 values for restart."))
    thresholds = value.get("evaluation_thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != METRIC_NAMES or not all(is_number(item, positive=True) for item in thresholds.values()):
        findings.append(finding("CONFIG_THRESHOLDS_INVALID", "Evaluation thresholds are incomplete or invalid.", "Predeclare positive energy and force RMSE thresholds."))
        thresholds = {}
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return make_report(
        "audit-config",
        findings,
        [
            gate("layout-version-backend-type-map", not any(item["code"] in {"UPSTREAM_REPORT_INVALID", "CONFIG_LAYOUT_IDENTITY_MISMATCH", "CONFIG_BACKEND_TRAINING_UNSUPPORTED", "CONFIG_LAYOUT_HASH_MISMATCH", "CONFIG_SYSTEM_SPLIT_MISMATCH"} for item in findings)),
            gate("descriptor-fitting", not any(item["code"] in {"CONFIG_DESCRIPTOR_INVALID", "CONFIG_FITTING_INVALID"} for item in findings)),
            gate("learning-loss-training", not any(item["code"] in {"CONFIG_LEARNING_RATE_INVALID", "CONFIG_LOSS_INVALID", "CONFIG_TRAINING_INVALID"} for item in findings)),
            gate("schema-environment-restart-thresholds", not any(item["code"] in {"CONFIG_ENV_OR_SCHEMA_HASH_INVALID", "CONFIG_RESTART_LINEAGE_INVALID", "CONFIG_THRESHOLDS_INVALID"} for item in findings)),
        ],
        [
            {"role": "training-projection", "source_label": "projection.json", "sha256": digest(raw), "bytes": len(raw)},
            {"role": "layout-audit", "source_label": "layout-audit.json", "sha256": digest(layout_raw), "bytes": len(layout_raw)},
        ],
        {
            "workflow_id": value.get("workflow_id") if is_id(value.get("workflow_id")) else None,
            "deepmd_version": value.get("deepmd_version") if isinstance(value.get("deepmd_version"), str) else None,
            "backend": value.get("backend") if value.get("backend") in BACKENDS else None,
            "mode": mode if mode in {"from_scratch", "restart"} else None,
            "layout_audit_sha256": digest(layout_raw),
            "source_dataset_audit_sha256": layout_obs.get("source_dataset_audit_sha256") if is_sha(layout_obs.get("source_dataset_audit_sha256")) else None,
            "environment_sha256": value.get("environment_sha256") if is_sha(value.get("environment_sha256")) else None,
            "provider_schema_sha256": value.get("provider_schema_sha256") if is_sha(value.get("provider_schema_sha256")) else None,
            "projection_content_sha256": digest(canonical),
            "type_map": value.get("type_map") if isinstance(value.get("type_map"), list) else [],
            "rcut": descriptor.get("rcut") if isinstance(descriptor, dict) and is_number(descriptor.get("rcut"), positive=True) else None,
            "numb_steps": training.get("numb_steps") if isinstance(training, dict) and is_int(training.get("numb_steps"), 1) else None,
            "restart_parent_checkpoint_sha256": parent if is_sha(parent) else None,
            "restart_parent_run_audit_sha256": parent_run if is_sha(parent_run) else None,
            "evaluation_thresholds": thresholds,
        },
        "Have a trusted version-bound adapter render, schema-validate and execute the private config under external authorization.",
        "input_gates_only",
        [
            "This is a portable projection, not an executable DeePMD input file.",
            "No provider schema, environment, rendered config, dataset payload, training or scientific result was authenticated.",
        ],
        action_on_pass="needs_authorization",
    )


def audit_run(value: dict[str, Any], raw: bytes, config: dict[str, Any], config_raw: bytes, layout: dict[str, Any], layout_raw: bytes) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    findings.extend(require_pass(config, "audit-config"))
    findings.extend(require_pass(layout, "audit-layout"))
    fields = {
        "schema_version",
        "run_id",
        "deepmd_version",
        "backend",
        "layout_audit_sha256",
        "config_audit_sha256",
        "source_dataset_audit_sha256",
        "environment_sha256",
        "authorization_decision_sha256",
        "execution_record_sha256",
        "output_log_sha256",
        "rendered_config_sha256",
        "status",
        "exit_code",
        "final_step",
        "checkpoint_sha256",
        "learning_curve_sha256",
        "nonfinite_detected",
        "restart_parent_checkpoint_sha256",
        "restart_parent_run_audit_sha256",
        "metrics",
    }
    if not exact(value, fields):
        findings.append(finding("RUN_FIELDS_INVALID", "Training-run fields are missing or unsupported.", "Use the exact technical run fields."))
    if value.get("schema_version") != SCHEMA_VERSION or not is_id(value.get("run_id")):
        findings.append(finding("RUN_IDENTITY_INVALID", "Run schema or ID is invalid.", "Provide safe exact run identity."))
    config_obs = config.get("observations") if isinstance(config.get("observations"), dict) else {}
    if value.get("deepmd_version") != config_obs.get("deepmd_version") or value.get("backend") != config_obs.get("backend"):
        findings.append(finding("RUN_VERSION_BACKEND_MISMATCH", "Run version/backend differs from config.", "Bind the exact configured provider identity."))
    if value.get("layout_audit_sha256") != digest(layout_raw) or value.get("config_audit_sha256") != digest(config_raw) or value.get("source_dataset_audit_sha256") != config_obs.get("source_dataset_audit_sha256") or value.get("environment_sha256") != config_obs.get("environment_sha256"):
        findings.append(finding("RUN_UPSTREAM_HASH_MISMATCH", "Run layout/config/environment lineage is detached.", "Bind exact upstream report and environment hashes."))
    if not is_sha(value.get("authorization_decision_sha256")) or not is_sha(value.get("execution_record_sha256")):
        findings.append(finding("RUN_AUTHORIZATION_OR_EXECUTION_RECORD_MISSING", "External execution authorization or execution-record hash is missing.", "Obtain external records bound to the exact rendered action and outcome."))
    completion_ok = value.get("status") == "completed" and is_int(value.get("exit_code"), 0, 0) and value.get("final_step") == config_obs.get("numb_steps") and value.get("nonfinite_detected") is False
    if not completion_ok:
        findings.append(finding("RUN_COMPLETION_INVALID", "Run status, exit, final step, or non-finite sentinel failed.", "Preserve the failed run and diagnose before any retry."))
    if not is_sha(value.get("checkpoint_sha256")) or not is_sha(value.get("learning_curve_sha256")) or not is_sha(value.get("output_log_sha256")) or not is_sha(value.get("rendered_config_sha256")):
        findings.append(finding("RUN_ARTIFACT_IDENTITY_INVALID", "Rendered config, output log, checkpoint, or learning-curve hash is missing.", "Bind every exact technical artifact without loading it in this candidate."))
    run_role_hashes = [
        value.get("authorization_decision_sha256"),
        value.get("execution_record_sha256"),
        value.get("output_log_sha256"),
        value.get("rendered_config_sha256"),
        value.get("checkpoint_sha256"),
        value.get("learning_curve_sha256"),
        value.get("restart_parent_checkpoint_sha256"),
        value.get("restart_parent_run_audit_sha256"),
    ]
    valid_run_role_hashes = [item for item in run_role_hashes if is_sha(item)]
    if len(valid_run_role_hashes) != len(set(valid_run_role_hashes)):
        findings.append(finding("RUN_EVIDENCE_ROLE_COLLISION", "One hash is reused for distinct run-evidence roles.", "Bind distinct authorization, execution record, log, config, checkpoint, and curve artifacts."))
    expected_parent = config_obs.get("restart_parent_checkpoint_sha256")
    expected_parent_run = config_obs.get("restart_parent_run_audit_sha256")
    if value.get("restart_parent_checkpoint_sha256") != expected_parent or value.get("restart_parent_run_audit_sha256") != expected_parent_run:
        findings.append(finding("RUN_RESTART_LINEAGE_MISMATCH", "Run restart parent checkpoint or parent run audit differs from the config projection.", "Use the exact planned parent checkpoint and run audit or start a new workflow."))
    metrics = value.get("metrics")
    metric_keys = {f"training_{name}" for name in METRIC_NAMES} | {f"validation_{name}" for name in METRIC_NAMES}
    if not isinstance(metrics, dict) or set(metrics) != metric_keys or not all(is_number(item) for item in metrics.values()):
        findings.append(finding("RUN_METRICS_INVALID", "Training/validation metric set is incomplete or non-finite.", "Provide all finite technical energy/force RMSE values."))
        metrics = {}
    return make_report(
        "audit-run",
        findings,
        [
            gate("upstream-version-backend-environment", not any(item["code"] in {"UPSTREAM_REPORT_INVALID", "RUN_VERSION_BACKEND_MISMATCH", "RUN_UPSTREAM_HASH_MISMATCH"} for item in findings)),
            gate("authorization-completion", not any(item["code"] in {"RUN_AUTHORIZATION_OR_EXECUTION_RECORD_MISSING", "RUN_EVIDENCE_ROLE_COLLISION", "RUN_COMPLETION_INVALID"} for item in findings)),
            gate("artifacts-restart", not any(item["code"] in {"RUN_ARTIFACT_IDENTITY_INVALID", "RUN_RESTART_LINEAGE_MISMATCH"} for item in findings)),
            gate("finite-training-validation-metrics", not any(item["code"] == "RUN_METRICS_INVALID" for item in findings)),
        ],
        [
            {"role": "training-run-record", "source_label": "training-run.json", "sha256": digest(raw), "bytes": len(raw)},
            {"role": "config-audit", "source_label": "config-audit.json", "sha256": digest(config_raw), "bytes": len(config_raw)},
            {"role": "layout-audit", "source_label": "layout-audit.json", "sha256": digest(layout_raw), "bytes": len(layout_raw)},
        ],
        {
            "run_id": value.get("run_id") if is_id(value.get("run_id")) else None,
            "deepmd_version": value.get("deepmd_version") if isinstance(value.get("deepmd_version"), str) else None,
            "backend": value.get("backend") if value.get("backend") in BACKENDS else None,
            "final_step": value.get("final_step") if is_int(value.get("final_step"), 0) else None,
            "checkpoint_sha256": value.get("checkpoint_sha256") if is_sha(value.get("checkpoint_sha256")) else None,
            "rendered_config_sha256": value.get("rendered_config_sha256") if is_sha(value.get("rendered_config_sha256")) else None,
            "config_audit_sha256": digest(config_raw),
            "layout_audit_sha256": digest(layout_raw),
            "source_dataset_audit_sha256": value.get("source_dataset_audit_sha256") if is_sha(value.get("source_dataset_audit_sha256")) else None,
            "metrics": metrics,
        },
        "Freeze the exact checkpoint/model with provider-specific evidence; do not infer test accuracy from training metrics.",
        "technical_run_gates_only",
        [
            "The record is unsigned metadata until a trusted bundle resolves the execution decision and exact artifacts.",
            "Training/validation curves do not establish independent test, OOD, stability, deployment, or scientific acceptance.",
        ],
    )


def audit_model(value: dict[str, Any], raw: bytes, run: dict[str, Any], run_raw: bytes, config: dict[str, Any], config_raw: bytes) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    findings.extend(require_pass(run, "audit-run"))
    findings.extend(require_pass(config, "audit-config"))
    fields = {
        "schema_version",
        "model_id",
        "deepmd_version",
        "backend",
        "artifact_sha256",
        "artifact_bytes",
        "source_checkpoint_sha256",
        "run_audit_sha256",
        "config_audit_sha256",
        "source_dataset_audit_sha256",
        "type_map",
        "rcut",
        "units",
        "energy_reference_convention",
        "rendered_config_sha256",
        "provider_schema_sha256",
        "licenses",
        "status",
    }
    if not exact(value, fields):
        findings.append(finding("MODEL_FIELDS_INVALID", "Frozen-model fields are missing or unsupported.", "Use the exact provider-specific model fields."))
    if value.get("schema_version") != SCHEMA_VERSION or not is_id(value.get("model_id")):
        findings.append(finding("MODEL_IDENTITY_INVALID", "Model schema or ID is invalid.", "Provide safe exact model identity."))
    config_obs = config.get("observations") if isinstance(config.get("observations"), dict) else {}
    if value.get("deepmd_version") != config_obs.get("deepmd_version") or value.get("backend") != config_obs.get("backend") or value.get("type_map") != config_obs.get("type_map") or value.get("rcut") != config_obs.get("rcut"):
        findings.append(finding("MODEL_CONFIG_IDENTITY_MISMATCH", "Model version/backend/type-map/cutoff differs from config.", "Use the exact audited config identity."))
    if value.get("run_audit_sha256") != digest(run_raw) or value.get("config_audit_sha256") != digest(config_raw):
        findings.append(finding("MODEL_LINEAGE_MISMATCH", "Model does not bind exact run and config reports.", "Use exact upstream report hashes."))
    if value.get("source_dataset_audit_sha256") != config_obs.get("source_dataset_audit_sha256"):
        findings.append(finding("MODEL_DATASET_LINEAGE_MISMATCH", "Model does not bind the generic source-dataset audit.", "Use the exact generic dataset-audit hash inherited through the layout and config."))
    run_obs = run.get("observations") if isinstance(run.get("observations"), dict) else {}
    if value.get("source_checkpoint_sha256") != run_obs.get("checkpoint_sha256"):
        findings.append(finding("MODEL_CHECKPOINT_LINEAGE_MISMATCH", "Frozen model does not bind the exact training checkpoint.", "Bind source_checkpoint_sha256 to the audited run checkpoint."))
    if not is_sha(value.get("artifact_sha256")) or not is_int(value.get("artifact_bytes"), 1, MAX_ARRAY_BYTES) or value.get("status") != "frozen_unloaded":
        findings.append(finding("MODEL_ARTIFACT_IDENTITY_INVALID", "Frozen model hash/bytes/status is invalid.", "Record exact frozen artifact identity without loading it."))
    if value.get("units") != UNITS or not isinstance(value.get("energy_reference_convention"), str) or not 1 <= len(value["energy_reference_convention"]) <= 128:
        findings.append(finding("MODEL_UNITS_OR_ENERGY_CONVENTION_INVALID", "Model units or energy convention is incomplete.", "Record exact units and a bounded energy-reference ID."))
    if value.get("rendered_config_sha256") != run_obs.get("rendered_config_sha256") or value.get("provider_schema_sha256") != config_obs.get("provider_schema_sha256"):
        findings.append(finding("MODEL_PROVIDER_CONFIG_OR_SCHEMA_INVALID", "Rendered config or provider-schema identity is missing/mismatched.", "Bind exact rendered config and the planned provider schema."))
    model_role_hashes = [
        value.get("artifact_sha256"),
        value.get("source_checkpoint_sha256"),
        value.get("run_audit_sha256"),
        value.get("config_audit_sha256"),
        value.get("source_dataset_audit_sha256"),
        value.get("rendered_config_sha256"),
        value.get("provider_schema_sha256"),
    ]
    valid_model_role_hashes = [item for item in model_role_hashes if is_sha(item)]
    if len(valid_model_role_hashes) != len(set(valid_model_role_hashes)):
        findings.append(finding("MODEL_EVIDENCE_ROLE_COLLISION", "One hash is reused for distinct model-evidence roles.", "Bind distinct model, checkpoint, report, dataset, config, and schema artifacts."))
    licenses = value.get("licenses")
    if not exact(licenses, {"framework", "backend", "model", "dataset"}) or not all(isinstance(licenses.get(key), str) and 0 < len(licenses[key]) <= 128 for key in ("framework", "backend", "model", "dataset")):
        findings.append(finding("MODEL_LICENSES_INVALID", "Framework/backend/model/dataset license identities are incomplete.", "Record all license roles independently."))
    return make_report(
        "audit-model",
        findings,
        [
            gate("run-config-lineage", not any(item["code"] in {"UPSTREAM_REPORT_INVALID", "MODEL_LINEAGE_MISMATCH", "MODEL_DATASET_LINEAGE_MISMATCH", "MODEL_CHECKPOINT_LINEAGE_MISMATCH", "MODEL_CONFIG_IDENTITY_MISMATCH", "MODEL_EVIDENCE_ROLE_COLLISION"} for item in findings)),
            gate("artifact-identity", not any(item["code"] == "MODEL_ARTIFACT_IDENTITY_INVALID" for item in findings)),
            gate("units-provider-config-schema", not any(item["code"] in {"MODEL_UNITS_OR_ENERGY_CONVENTION_INVALID", "MODEL_PROVIDER_CONFIG_OR_SCHEMA_INVALID"} for item in findings)),
            gate("license-separation", not any(item["code"] == "MODEL_LICENSES_INVALID" for item in findings)),
        ],
        [
            {"role": "deepmd-model-manifest", "source_label": "model.json", "sha256": digest(raw), "bytes": len(raw)},
            {"role": "run-audit", "source_label": "run-audit.json", "sha256": digest(run_raw), "bytes": len(run_raw)},
            {"role": "config-audit", "source_label": "config-audit.json", "sha256": digest(config_raw), "bytes": len(config_raw)},
        ],
        {
            "model_id": value.get("model_id") if is_id(value.get("model_id")) else None,
            "deepmd_version": value.get("deepmd_version") if isinstance(value.get("deepmd_version"), str) else None,
            "backend": value.get("backend") if value.get("backend") in BACKENDS else None,
            "artifact_sha256": value.get("artifact_sha256") if is_sha(value.get("artifact_sha256")) else None,
            "artifact_bytes": value.get("artifact_bytes") if is_int(value.get("artifact_bytes"), 1) else None,
            "type_map": value.get("type_map") if isinstance(value.get("type_map"), list) else [],
            "rcut": value.get("rcut") if is_number(value.get("rcut"), positive=True) else None,
            "units": value.get("units") if isinstance(value.get("units"), dict) else None,
            "run_audit_sha256": digest(run_raw),
            "config_audit_sha256": digest(config_raw),
            "source_dataset_audit_sha256": value.get("source_dataset_audit_sha256") if is_sha(value.get("source_dataset_audit_sha256")) else None,
        },
        "Hand the exact unloaded model identity to independent generic test/OOD evaluation; do not deploy from training evidence.",
        "technical_run_gates_only",
        [
            "The model artifact was never opened, deserialized, imported, inferred, or compared with the training checkpoint.",
            "No independent test/OOD accuracy, MD stability, consumer compatibility, deployment, or scientific acceptance is established.",
        ],
        action_on_pass="needs_authorization",
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    layout = commands.add_parser("audit-layout")
    layout.add_argument("--manifest", type=Path, required=True)
    layout.add_argument("--out", type=Path, required=True)
    config = commands.add_parser("audit-config")
    config.add_argument("--projection", type=Path, required=True)
    config.add_argument("--layout-audit", type=Path, required=True)
    config.add_argument("--out", type=Path, required=True)
    run = commands.add_parser("audit-run")
    run.add_argument("--record", type=Path, required=True)
    run.add_argument("--config-audit", type=Path, required=True)
    run.add_argument("--layout-audit", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    model = commands.add_parser("audit-model")
    model.add_argument("--manifest", type=Path, required=True)
    model.add_argument("--run-audit", type=Path, required=True)
    model.add_argument("--config-audit", type=Path, required=True)
    model.add_argument("--out", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    evidence_paths = {
        "audit-layout": [args.manifest] if args.command == "audit-layout" else [],
        "audit-config": [args.projection, args.layout_audit] if args.command == "audit-config" else [],
        "audit-run": [args.record, args.config_audit, args.layout_audit] if args.command == "audit-run" else [],
        "audit-model": [args.manifest, args.run_audit, args.config_audit] if args.command == "audit-model" else [],
    }[args.command]
    try:
        ensure_output_is_distinct(args.out, evidence_paths)
    except BoundaryError as exc:
        sys.stderr.write(json.dumps({"status": "blocked", "finding_code": exc.code}, sort_keys=True) + "\n")
        return 2
    try:
        if args.command == "audit-layout":
            value, raw = read_json(args.manifest, "LAYOUT")
            result = audit_layout(value, raw)
        elif args.command == "audit-config":
            value, raw = read_json(args.projection, "CONFIG")
            layout, layout_raw = read_json(args.layout_audit, "LAYOUT_AUDIT")
            result = audit_config(value, raw, layout, layout_raw)
        elif args.command == "audit-run":
            value, raw = read_json(args.record, "RUN")
            config, config_raw = read_json(args.config_audit, "CONFIG_AUDIT")
            layout, layout_raw = read_json(args.layout_audit, "LAYOUT_AUDIT")
            result = audit_run(value, raw, config, config_raw, layout, layout_raw)
        else:
            value, raw = read_json(args.manifest, "MODEL")
            run, run_raw = read_json(args.run_audit, "RUN_AUDIT")
            config, config_raw = read_json(args.config_audit, "CONFIG_AUDIT")
            result = audit_model(value, raw, run, run_raw, config, config_raw)
    except BoundaryError as exc:
        result = boundary_report(args.command, exc)
    try:
        write_json(args.out, result)
    except BoundaryError as exc:
        sys.stderr.write(json.dumps({"status": "blocked", "finding_code": exc.code}, sort_keys=True) + "\n")
        return 2
    sys.stdout.write(json.dumps({"status": result["status"], "report": args.out.name}, sort_keys=True) + "\n")
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
