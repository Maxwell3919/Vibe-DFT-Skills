#!/usr/bin/env python3
"""Offline fail-closed metadata gates for the development generic MLP workflow."""

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
from typing import Any, Callable, Iterable


sys.dont_write_bytecode = True

SCHEMA_VERSION = "candidate-1.0"
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_FRAMES = 200000
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
ELEMENT = re.compile(r"^[A-Z][a-z]?$|^D$|^T$")
SPLITS = ("train", "validation", "test", "ood")
EXACT_UNITS = {
    "energy": "eV",
    "forces": "eV/angstrom",
    "stress": "eV/angstrom^3",
}
PROVIDERS: dict[str, dict[str, object]] = {
    "mace-python": {"version": "0.3.16", "modes": {"train_from_scratch", "fine_tune", "evaluate_pretrained"}},
    "nequip-python": {"version": "0.19.0", "modes": {"train_from_scratch", "fine_tune", "evaluate_pretrained"}},
    "fairchem-v1-gemnet-oc": {"version": "1.10.0", "modes": {"evaluate_pretrained"}},
    "fairchem-v1-equiformer-v2": {"version": "1.10.0", "modes": {"evaluate_pretrained"}},
    "fairchem-v2-uma": {"version": "2.21.0", "modes": {"evaluate_pretrained"}},
}
BASE_METRICS = {
    "energy_mae_ev_per_atom",
    "energy_rmse_ev_per_atom",
    "energy_p95_abs_ev_per_atom",
    "force_mae_ev_per_angstrom",
    "force_rmse_ev_per_angstrom",
    "force_p95_abs_ev_per_angstrom",
}
STRESS_METRICS = {
    "stress_mae_ev_per_angstrom3",
    "stress_rmse_ev_per_angstrom3",
    "stress_p95_abs_ev_per_angstrom3",
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
    "audit-dataset": (
        "local_gate_passed_limited",
        "input_gates_only",
        ("identity", "protocol-and-units", "species-and-labels", "split-independence", "source-and-license"),
    ),
    "plan-training": (
        "needs_authorization",
        "input_gates_only",
        ("dataset-audit-binding", "provider-version-mode", "seeds-loss-stopping", "thresholds-and-slices", "environment-and-lineage"),
    ),
    "audit-model": (
        "needs_authorization",
        "technical_run_gates_only",
        ("artifact-identity", "dataset-plan-origin-lineage", "units-precision-convention", "license-separation"),
    ),
    "audit-evaluation": (
        "local_gate_passed_limited",
        "numerical_candidate_only",
        ("upstream-lineage", "independent-test", "frozen-metrics", "slice-and-ood"),
    ),
    "audit-deployment": (
        "needs_authorization",
        "eligible_for_expert_review",
        ("model-evaluation-lineage", "adapter-species-units", "domain-and-pilot", "monitor-and-rollback", "external-authorization"),
    ),
}


class BoundaryError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def sha256(raw: bytes) -> str:
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


def read_regular(path: Path, kind: str) -> bytes:
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
        if before.st_size > MAX_JSON_BYTES:
            raise BoundaryError(f"{kind}_TOO_LARGE", f"{kind} evidence exceeds the size limit.")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW") | getattr(os, "O_NONBLOCK") | getattr(os, "O_CLOEXEC", 0)
        file_fd = os.open(name, flags, dir_fd=parent_fd)
        opened = os.fstat(file_fd)
        if _stable_identity(before) != _stable_identity(opened):
            raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} evidence changed before reading.")
        chunks: list[bytes] = []
        total = 0
        while total <= MAX_JSON_BYTES:
            chunk = os.read(file_fd, min(65536, MAX_JSON_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        after = os.fstat(file_fd)
        final = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        _revalidate_directories(absolute, descriptors, edges, kind)
        raw = b"".join(chunks)
        if len(raw) > MAX_JSON_BYTES:
            raise BoundaryError(f"{kind}_TOO_LARGE", f"{kind} evidence exceeds the size limit.")
        if (
            _stable_identity(opened) != _stable_identity(after)
            or _stable_identity(after) != _stable_identity(final)
            or not stat.S_ISREG(after.st_mode)
            or after.st_nlink != 1
            or len(raw) != opened.st_size
        ):
            raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} evidence changed while reading.")
        return raw
    except BoundaryError:
        raise
    except OSError as exc:
        raise BoundaryError(f"{kind}_UNREADABLE", f"{kind} evidence is unreadable.") from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def load_json(path: Path, kind: str) -> tuple[dict[str, Any], bytes]:
    raw = read_regular(path, kind)
    if raw.startswith(b"\xef\xbb\xbf"):
        raise BoundaryError(f"{kind}_BOM", f"{kind} JSON must not contain a BOM.")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique_pairs,
            parse_constant=reject_constant,
        )
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
    digest = hashlib.sha256()
    offset = 0
    while offset < len(payload):
        chunk = os.pread(descriptor, min(65536, len(payload) - offset), offset)
        if not chunk:
            return False
        digest.update(chunk)
        offset += len(chunk)
    return offset == len(payload) and digest.digest() == hashlib.sha256(payload).digest()


def _inode_matches(left: os.stat_result, right: os.stat_result, *, links: int) -> bool:
    return (
        stat.S_ISREG(left.st_mode)
        and stat.S_ISREG(right.st_mode)
        and left.st_nlink == links
        and right.st_nlink == links
        and (left.st_dev, left.st_ino, left.st_size) == (right.st_dev, right.st_ino, right.st_size)
    )


def write_report(path: Path, report: dict[str, Any]) -> None:
    try:
        payload = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
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
            candidate = f".mlp-guard-{secrets.token_hex(12)}.tmp"
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


def exact_fields(value: object, fields: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == fields


def finding(code: str, message: str, next_action: str) -> dict[str, str]:
    return {"code": code, "message": message, "next_action": next_action}


def gate(identifier: str, passed: bool, codes: Iterable[str] = ()) -> dict[str, Any]:
    return {"id": identifier, "status": "pass" if passed else "blocked", "finding_codes": list(codes)}


def report(
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
        "contract_name": "mlp-candidate-audit",
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
    return report(
        command,
        [item],
        [],
        [],
        None,
        item["next_action"],
        "no_positive_claim",
        ["No provider execution, model loading, or positive scientific conclusion occurred."],
    )


def audit_dataset(manifest: dict[str, Any], raw: bytes) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    root_fields = {
        "schema_version",
        "dataset_id",
        "dataset_version",
        "purpose",
        "reference_protocol_sha256",
        "species_order",
        "units",
        "stress_policy",
        "test_use_policy",
        "licenses",
        "frames",
    }
    if not exact_fields(manifest, root_fields):
        findings.append(finding("DATASET_FIELDS_INVALID", "Dataset manifest fields are missing or unsupported.", "Use the exact candidate dataset fields."))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        findings.append(finding("DATASET_SCHEMA_VERSION_INVALID", "Dataset schema version is unsupported.", f"Use {SCHEMA_VERSION}."))
    if not is_id(manifest.get("dataset_id")) or not is_id(manifest.get("dataset_version")):
        findings.append(finding("DATASET_IDENTITY_INVALID", "Dataset ID or version is unsafe.", "Provide stable safe dataset identity fields."))
    if manifest.get("purpose") != "deployment_candidate":
        findings.append(finding("DATASET_PURPOSE_UNSUPPORTED", "Dataset purpose is outside the deployment-oriented profile.", "Use deployment_candidate or add a narrower reviewed profile."))
    if not is_sha(manifest.get("reference_protocol_sha256")):
        findings.append(finding("DATASET_PROTOCOL_HASH_INVALID", "Reference DFT protocol hash is missing.", "Bind one exact reference protocol with SHA-256."))
    species = manifest.get("species_order")
    species_ok = (
        isinstance(species, list)
        and bool(species)
        and len(species) == len(set(item for item in species if isinstance(item, str)))
        and all(isinstance(item, str) and ELEMENT.fullmatch(item) for item in species)
    )
    if not species_ok:
        findings.append(finding("DATASET_SPECIES_INVALID", "Species order is missing, duplicated, or invalid.", "Provide one explicit unique ordered element list."))
        species = []
    units = manifest.get("units")
    if not exact_fields(units, {"energy", "forces", "stress"}) or any(units.get(key) != expected for key, expected in EXACT_UNITS.items()):
        findings.append(finding("DATASET_UNITS_INVALID", "Dataset units differ from the exact candidate convention.", "Normalize energy, force, and stress units before manifest creation."))
    stress_policy = manifest.get("stress_policy")
    if stress_policy not in {"all_frames", "absent"}:
        findings.append(finding("DATASET_STRESS_POLICY_INVALID", "Stress coverage policy is invalid.", "Choose all_frames or absent."))
    if manifest.get("test_use_policy") != "held_out_once_after_freeze":
        findings.append(finding("DATASET_TEST_POLICY_INVALID", "Test-use policy is not independent.", "Reserve the test split until model and thresholds are frozen."))
    licenses = manifest.get("licenses")
    if not exact_fields(licenses, {"dataset", "reference_data", "redistribution"}) or not all(
        isinstance(licenses.get(key), str) and 0 < len(licenses[key]) <= 128
        for key in ("dataset", "reference_data")
    ) or licenses.get("redistribution") not in {"allowed", "restricted", "prohibited", "unknown"}:
        findings.append(finding("DATASET_LICENSE_INVENTORY_INVALID", "Dataset/reference license inventory is incomplete.", "Record separate data and reference-data license IDs and redistribution status."))
    frames = manifest.get("frames")
    if not isinstance(frames, list) or not 4 <= len(frames) <= MAX_FRAMES:
        findings.append(finding("DATASET_FRAME_COUNT_INVALID", "Frame inventory is missing or outside the bounded range.", "Provide a bounded metadata inventory with all required splits."))
    if not isinstance(frames, list) or len(frames) > MAX_FRAMES:
        frames = []
    frame_fields = {
        "frame_id",
        "group_id",
        "split",
        "structure_sha256",
        "labels_sha256",
        "source_run_sha256",
        "source_acceptance_sha256",
        "atom_count",
        "elements",
        "has_energy",
        "has_forces",
        "has_stress",
    }
    ids: set[str] = set()
    structures: set[str] = set()
    labels: set[str] = set()
    group_splits: dict[str, set[str]] = {}
    source_run_splits: dict[str, set[str]] = {}
    split_counts = {name: 0 for name in SPLITS}
    total_atoms = 0
    for item in frames:
        if not exact_fields(item, frame_fields):
            findings.append(finding("DATASET_FRAME_FIELDS_INVALID", "A frame metadata item is malformed.", "Regenerate every frame item with exact fields."))
            continue
        frame_id = item.get("frame_id")
        group_id = item.get("group_id")
        split = item.get("split")
        if not is_id(frame_id) or frame_id in ids:
            findings.append(finding("DATASET_FRAME_ID_DUPLICATE", "Frame ID is unsafe or duplicated.", "Assign a unique safe frame ID."))
        else:
            ids.add(frame_id)
        if not is_id(group_id) or split not in SPLITS:
            findings.append(finding("DATASET_GROUP_OR_SPLIT_INVALID", "Correlation group or split is invalid.", "Assign a safe group and one exact split."))
        else:
            group_splits.setdefault(group_id, set()).add(split)
            split_counts[split] += 1
        structure_hash = item.get("structure_sha256")
        label_hash = item.get("labels_sha256")
        if not is_sha(structure_hash) or structure_hash in structures:
            findings.append(finding("DATASET_STRUCTURE_DUPLICATE", "Structure hash is invalid or duplicated.", "Remove exact structure duplication and rebuild the split."))
        else:
            structures.add(structure_hash)
        if not is_sha(label_hash) or label_hash in labels:
            findings.append(finding("DATASET_LABEL_DUPLICATE", "Label hash is invalid or duplicated.", "Bind each frame to one unique exact label record."))
        else:
            labels.add(label_hash)
        source_run = item.get("source_run_sha256")
        if not is_sha(source_run) or not is_sha(item.get("source_acceptance_sha256")):
            findings.append(finding("DATASET_SOURCE_LINEAGE_MISSING", "Reference run or scientific-acceptance hash is missing.", "Bind every frame to exact reference-run and external acceptance records."))
        elif split in SPLITS:
            source_run_splits.setdefault(source_run, set()).add(split)
            role_hashes = {
                structure_hash,
                label_hash,
                source_run,
                item.get("source_acceptance_sha256"),
            }
            if len(role_hashes) != 4:
                findings.append(finding("DATASET_SOURCE_ROLE_COLLISION", "One hash is reused for structurally different evidence roles.", "Bind distinct structure, label, run, and external acceptance artifacts."))
        atom_count = item.get("atom_count")
        if not is_int(atom_count, 1, 1000000):
            findings.append(finding("DATASET_ATOM_COUNT_INVALID", "Frame atom count is invalid.", "Provide a bounded positive atom count."))
        else:
            total_atoms += atom_count
        elements = item.get("elements")
        expected_elements = [element for element in species if isinstance(elements, list) and element in elements]
        if not isinstance(elements, list) or not elements or elements != expected_elements or len(elements) != len(set(elements)):
            findings.append(finding("DATASET_FRAME_SPECIES_INVALID", "Frame elements are not a unique subset in dataset order.", "Normalize every frame element inventory to species_order."))
        if item.get("has_energy") is not True or item.get("has_forces") is not True:
            findings.append(finding("DATASET_REQUIRED_LABEL_MISSING", "Every frame must contain energy and force labels.", "Regenerate or remove frames without both required labels."))
        expected_stress = stress_policy == "all_frames"
        if item.get("has_stress") is not expected_stress:
            findings.append(finding("DATASET_STRESS_COVERAGE_MISMATCH", "Frame stress coverage differs from the dataset policy.", "Use uniform stress coverage or a separately reviewed missing-label profile."))
    leaking = sorted(group for group, splits in group_splits.items() if len(splits) > 1)
    if leaking:
        findings.append(finding("DATASET_GROUP_LEAKAGE", "A correlation group spans multiple splits.", "Move every correlated group wholly into one split and regenerate the manifest."))
    if any(len(splits) > 1 for splits in source_run_splits.values()):
        findings.append(finding("DATASET_SOURCE_RUN_LEAKAGE", "Frames from one reference run span multiple splits.", "Keep every frame from one trajectory or relaxation run in one split and rebuild groups."))
    missing_splits = [name for name, count in split_counts.items() if count == 0]
    if missing_splits:
        findings.append(finding("DATASET_SPLIT_MISSING", "One or more required train/validation/test/OOD splits are empty.", "Provide nonempty disjoint metadata groups for all four splits."))
    checks = {
        "identity": not any(item["code"].startswith("DATASET_IDENTITY") or item["code"].startswith("DATASET_SCHEMA") or item["code"].startswith("DATASET_FIELDS") for item in findings),
        "protocol-and-units": not any(item["code"] in {"DATASET_PROTOCOL_HASH_INVALID", "DATASET_UNITS_INVALID"} for item in findings),
        "species-and-labels": not any(item["code"] in {"DATASET_SPECIES_INVALID", "DATASET_FRAME_SPECIES_INVALID", "DATASET_REQUIRED_LABEL_MISSING", "DATASET_STRESS_COVERAGE_MISMATCH"} for item in findings),
        "split-independence": not any(item["code"] in {"DATASET_GROUP_LEAKAGE", "DATASET_SOURCE_RUN_LEAKAGE", "DATASET_SPLIT_MISSING", "DATASET_TEST_POLICY_INVALID", "DATASET_STRUCTURE_DUPLICATE", "DATASET_LABEL_DUPLICATE"} for item in findings),
        "source-and-license": not any(item["code"] in {"DATASET_SOURCE_LINEAGE_MISSING", "DATASET_SOURCE_ROLE_COLLISION", "DATASET_LICENSE_INVENTORY_INVALID"} for item in findings),
    }
    return report(
        "audit-dataset",
        findings,
        [gate(name, passed, [] if passed else [item["code"] for item in findings]) for name, passed in checks.items()],
        [{"role": "ml-dataset-manifest", "source_label": "dataset.json", "sha256": sha256(raw), "bytes": len(raw)}],
        {
            "dataset_id": manifest.get("dataset_id") if is_id(manifest.get("dataset_id")) else None,
            "dataset_version": manifest.get("dataset_version") if is_id(manifest.get("dataset_version")) else None,
            "species_order": species,
            "stress_policy": stress_policy if stress_policy in {"all_frames", "absent"} else None,
            "frame_count": len(frames),
            "total_atoms": total_atoms,
            "split_counts": split_counts,
            "group_count": len(group_splits),
            "reference_protocol_sha256": manifest.get("reference_protocol_sha256") if is_sha(manifest.get("reference_protocol_sha256")) else None,
            "redistribution": licenses.get("redistribution") if isinstance(licenses, dict) else None,
        },
        "Freeze a provider-bound workflow plan using the exact dataset-audit report hash.",
        "input_gates_only",
        [
            "This audit checks manifest metadata only; referenced structures, labels, runs, decisions, and licenses are not resolved or authenticated.",
            "Exact hashes do not detect structural near-duplicates; correctness depends on conservative correlation groups.",
        ],
    )


def require_pass_report(value: dict[str, Any], command: str) -> list[dict[str, str]]:
    profile = REPORT_PROFILES.get(command)
    if profile is None:
        return [finding("UPSTREAM_REPORT_PROFILE_UNKNOWN", "Required upstream report profile is unknown.", "Use a reviewed upstream command profile.")]
    expected_action, expected_ceiling, expected_gates = profile
    if set(value) != REPORT_FIELDS or (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("contract_name") != "mlp-candidate-audit"
        or value.get("command") != command
        or value.get("candidate_lifecycle") != "development"
        or value.get("status") != "pass"
        or value.get("action_state") != expected_action
        or value.get("claim_ceiling") != "no_positive_claim"
        or value.get("future_gate_ceiling") != expected_ceiling
        or value.get("findings") != []
    ):
        return [finding("UPSTREAM_REPORT_INVALID", "Required upstream report is not a canonical pass record.", "Regenerate the upstream report and resolve all findings.")]
    if value.get("gates") != [gate(identifier, True) for identifier in expected_gates]:
        return [finding("UPSTREAM_REPORT_GATES_INVALID", "Upstream pass gates are missing, reordered, or noncanonical.", "Regenerate the upstream report with the deterministic guard.")]
    evidence = value.get("evidence")
    if (
        not isinstance(evidence, list)
        or not evidence
        or any(
            not exact_fields(item, {"role", "source_label", "sha256", "bytes"})
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


def required_metric_names(stress_policy: object) -> set[str]:
    return BASE_METRICS | (STRESS_METRICS if stress_policy == "all_frames" else set())


def plan_training(request: dict[str, Any], raw: bytes, dataset: dict[str, Any], dataset_raw: bytes) -> dict[str, Any]:
    findings = require_pass_report(dataset, "audit-dataset")
    fields = {
        "schema_version",
        "workflow_id",
        "provider_profile",
        "provider_version",
        "mode",
        "dataset_audit_sha256",
        "species_order",
        "seeds",
        "precision",
        "cutoff_angstrom",
        "loss_weights",
        "stopping",
        "thresholds",
        "required_slices",
        "required_slice_ids",
        "environment_sha256",
        "provider_config_sha256",
        "parent_model_sha256",
        "parent_model_record_sha256",
    }
    if not exact_fields(request, fields):
        findings.append(finding("PLAN_FIELDS_INVALID", "Workflow plan fields are missing or unsupported.", "Use the exact provider-bound plan fields."))
    if request.get("schema_version") != SCHEMA_VERSION or not is_id(request.get("workflow_id")):
        findings.append(finding("PLAN_IDENTITY_INVALID", "Workflow schema or ID is invalid.", "Use the candidate schema and a safe workflow ID."))
    provider = PROVIDERS.get(request.get("provider_profile")) if isinstance(request.get("provider_profile"), str) else None
    if not isinstance(provider, dict) or request.get("provider_version") != provider.get("version") or request.get("mode") not in provider.get("modes", set()):
        findings.append(finding("PLAN_PROVIDER_MODE_INVALID", "Provider, version, or mode is not an exact registered combination.", "Select one exact provider/version/mode from the provider matrix."))
    dataset_hash = sha256(dataset_raw)
    if request.get("dataset_audit_sha256") != dataset_hash:
        findings.append(finding("PLAN_DATASET_BINDING_MISMATCH", "Plan does not bind the exact dataset-audit bytes.", "Set dataset_audit_sha256 to the exact upstream report hash."))
    observations = dataset.get("observations") if isinstance(dataset.get("observations"), dict) else {}
    species = request.get("species_order")
    if species != observations.get("species_order"):
        findings.append(finding("PLAN_SPECIES_MISMATCH", "Plan species order differs from the dataset audit.", "Use the exact audited species order."))
    seeds = request.get("seeds")
    if not exact_fields(seeds, {"split", "initialization", "training"}) or not all(is_int(seeds.get(key), 0, 2**32 - 1) for key in ("split", "initialization", "training")):
        findings.append(finding("PLAN_SEEDS_INVALID", "All deterministic seed roles must be explicit bounded integers.", "Provide split, initialization, and training seeds."))
    if request.get("precision") not in {"float32", "float64"}:
        findings.append(finding("PLAN_PRECISION_INVALID", "Numeric precision is unsupported or missing.", "Choose float32 or float64 explicitly."))
    if not is_number(request.get("cutoff_angstrom"), positive=True) or request["cutoff_angstrom"] > 20:
        findings.append(finding("PLAN_CUTOFF_INVALID", "Cutoff is missing or outside the bounded range.", "Provide an explicit positive cutoff no greater than 20 angstrom."))
    loss = request.get("loss_weights")
    if not exact_fields(loss, {"energy", "forces", "stress"}) or not all(is_number(loss.get(key)) for key in ("energy", "forces", "stress")) or loss.get("energy", 0) + loss.get("forces", 0) <= 0:
        findings.append(finding("PLAN_LOSS_INVALID", "Loss weights are incomplete, non-finite, or omit energy/forces.", "Provide explicit nonnegative loss weights with energy or force supervision."))
    elif observations.get("stress_policy") == "absent" and loss.get("stress") != 0:
        findings.append(finding("PLAN_STRESS_LOSS_WITHOUT_LABELS", "Stress loss is nonzero for a dataset without stress labels.", "Set stress weight to zero or use an all-stress dataset."))
    expected_metrics = required_metric_names(observations.get("stress_policy"))
    stopping = request.get("stopping")
    if not exact_fields(stopping, {"max_epochs", "patience", "selection_metric", "checkpoint_interval"}) or not is_int(stopping.get("max_epochs"), 1, 10000000) or not is_int(stopping.get("patience"), 1, 10000000) or not is_int(stopping.get("checkpoint_interval"), 1, 10000000) or stopping["patience"] > stopping["max_epochs"] or stopping["checkpoint_interval"] > stopping["max_epochs"] or stopping.get("selection_metric") not in expected_metrics:
        findings.append(finding("PLAN_STOPPING_INVALID", "Stopping and checkpoint policy is incomplete.", "Provide bounded epochs, patience, selection metric, and checkpoint interval."))
    thresholds = request.get("thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != expected_metrics or not all(is_number(value, positive=True) for value in thresholds.values()):
        findings.append(finding("PLAN_THRESHOLDS_INVALID", "Predeclared evaluation thresholds are incomplete or invalid.", "Provide one positive threshold for every required metric."))
    slices = request.get("required_slices")
    if slices != ["per_species", "configuration_class", "ood"]:
        findings.append(finding("PLAN_SLICES_INVALID", "Required evaluation slices are missing or noncanonical.", "Use per_species, configuration_class, and ood in canonical order."))
    slice_ids = request.get("required_slice_ids")
    slice_ids_ok = exact_fields(slice_ids, {"per_species", "configuration_class", "ood"})
    if slice_ids_ok:
        for category in ("per_species", "configuration_class", "ood"):
            identifiers = slice_ids.get(category)
            if not isinstance(identifiers, list) or not 1 <= len(identifiers) <= 1000 or identifiers != sorted(set(identifiers)) or not all(is_id(item) for item in identifiers):
                slice_ids_ok = False
                break
    expected_species_slices = [str(item).casefold() for item in observations.get("species_order", [])]
    if slice_ids_ok and slice_ids.get("per_species") != sorted(expected_species_slices):
        slice_ids_ok = False
    if not slice_ids_ok:
        findings.append(finding("PLAN_SLICE_IDS_INVALID", "Predeclared slice IDs are missing, unsafe, duplicated, unsorted, or omit a species.", "Predeclare sorted per-species, configuration-class, and OOD slice IDs before evaluation."))
    for key in ("environment_sha256", "provider_config_sha256"):
        if not is_sha(request.get(key)):
            findings.append(finding("PLAN_PROVENANCE_HASH_INVALID", "Environment or provider-config hash is missing.", "Bind exact environment and provider configuration bytes."))
            break
    if is_sha(request.get("environment_sha256")) and request.get("environment_sha256") == request.get("provider_config_sha256"):
        findings.append(finding("PLAN_PROVENANCE_ROLE_COLLISION", "Environment and provider-config records reuse one hash.", "Bind distinct exact environment and provider-config evidence."))
    mode = request.get("mode")
    parent = request.get("parent_model_sha256")
    parent_record = request.get("parent_model_record_sha256")
    if (mode in {"fine_tune", "evaluate_pretrained"} and (not is_sha(parent) or not is_sha(parent_record) or parent == parent_record)) or (mode == "train_from_scratch" and (parent is not None or parent_record is not None)):
        findings.append(finding("PLAN_PARENT_MODEL_INVALID", "Parent model artifact/record lineage conflicts with the workflow mode.", "Bind distinct parent artifact and model-record hashes for fine-tune/pretrained mode and omit both for from-scratch mode."))
    canonical_request = json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    observations_out = {
        "workflow_id": request.get("workflow_id") if is_id(request.get("workflow_id")) else None,
        "provider_profile": request.get("provider_profile") if request.get("provider_profile") in PROVIDERS else None,
        "provider_version": request.get("provider_version") if isinstance(request.get("provider_version"), str) else None,
        "mode": mode if isinstance(mode, str) else None,
        "dataset_audit_sha256": dataset_hash,
        "species_order": species if isinstance(species, list) else [],
        "stress_policy": observations.get("stress_policy"),
        "precision": request.get("precision") if request.get("precision") in {"float32", "float64"} else None,
        "cutoff_angstrom": request.get("cutoff_angstrom") if is_number(request.get("cutoff_angstrom"), positive=True) else None,
        "thresholds": thresholds if isinstance(thresholds, dict) else {},
        "thresholds_sha256": sha256(
            json.dumps(thresholds, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ) if isinstance(thresholds, dict) else None,
        "required_slices": slices if isinstance(slices, list) else [],
        "required_slice_ids": slice_ids if slice_ids_ok else {},
        "plan_content_sha256": sha256(canonical_request),
        "parent_model_sha256": parent if is_sha(parent) else None,
        "parent_model_record_sha256": parent_record if is_sha(parent_record) else None,
    }
    return report(
        "plan-training",
        findings,
        [
            gate("dataset-audit-binding", not any(item["code"].startswith("UPSTREAM") or "DATASET" in item["code"] for item in findings)),
            gate("provider-version-mode", not any(item["code"] == "PLAN_PROVIDER_MODE_INVALID" for item in findings)),
            gate("seeds-loss-stopping", not any(item["code"] in {"PLAN_SEEDS_INVALID", "PLAN_LOSS_INVALID", "PLAN_STRESS_LOSS_WITHOUT_LABELS", "PLAN_STOPPING_INVALID"} for item in findings)),
            gate("thresholds-and-slices", not any(item["code"] in {"PLAN_THRESHOLDS_INVALID", "PLAN_SLICES_INVALID", "PLAN_SLICE_IDS_INVALID"} for item in findings)),
            gate("environment-and-lineage", not any(item["code"] in {"PLAN_PROVENANCE_HASH_INVALID", "PLAN_PROVENANCE_ROLE_COLLISION", "PLAN_PARENT_MODEL_INVALID"} for item in findings)),
        ],
        [
            {"role": "workflow-request", "source_label": "training-request.json", "sha256": sha256(raw), "bytes": len(raw)},
            {"role": "dataset-audit", "source_label": "dataset-audit.json", "sha256": dataset_hash, "bytes": len(dataset_raw)},
        ],
        observations_out,
        "Obtain external authorization and a provider-specific validated adapter; this candidate cannot train or evaluate.",
        "input_gates_only",
        [
            "The plan does not validate provider config syntax or dependency compatibility.",
            "No framework import, training, model loading, or scientific acceptance occurred.",
        ],
        action_on_pass="needs_authorization",
    )


def audit_model(manifest: dict[str, Any], raw: bytes, plan: dict[str, Any], plan_raw: bytes) -> dict[str, Any]:
    findings = require_pass_report(plan, "plan-training")
    fields = {
        "schema_version",
        "model_id",
        "provider_profile",
        "provider_version",
        "mode",
        "artifact_sha256",
        "artifact_bytes",
        "dataset_audit_sha256",
        "training_plan_sha256",
        "training_run_sha256",
        "official_model_record_sha256",
        "parent_model_sha256",
        "parent_model_record_sha256",
        "species_order",
        "units",
        "cutoff_angstrom",
        "precision",
        "energy_reference_convention",
        "licenses",
        "status",
    }
    if not exact_fields(manifest, fields):
        findings.append(finding("MODEL_FIELDS_INVALID", "Model manifest fields are missing or unsupported.", "Use the exact candidate model fields."))
    plan_obs = plan.get("observations") if isinstance(plan.get("observations"), dict) else {}
    if manifest.get("schema_version") != SCHEMA_VERSION or not is_id(manifest.get("model_id")):
        findings.append(finding("MODEL_IDENTITY_INVALID", "Model schema or ID is invalid.", "Provide safe exact model identity."))
    if any(manifest.get(key) != plan_obs.get(key) for key in ("provider_profile", "provider_version", "mode", "species_order")):
        findings.append(finding("MODEL_PLAN_MISMATCH", "Model provider, version, mode, or species differs from the plan.", "Regenerate the manifest from the exact frozen plan."))
    if not is_sha(manifest.get("artifact_sha256")) or not is_int(manifest.get("artifact_bytes"), 1, 2**63 - 1):
        findings.append(finding("MODEL_ARTIFACT_IDENTITY_INVALID", "Model artifact hash or byte count is invalid.", "Record exact artifact bytes and SHA-256 without loading it."))
    if manifest.get("dataset_audit_sha256") != plan_obs.get("dataset_audit_sha256") or manifest.get("training_plan_sha256") != sha256(plan_raw):
        findings.append(finding("MODEL_LINEAGE_MISMATCH", "Model dataset or training-plan reference is detached.", "Bind exact upstream report hashes."))
    mode = plan_obs.get("mode")
    if manifest.get("parent_model_sha256") != plan_obs.get("parent_model_sha256") or manifest.get("parent_model_record_sha256") != plan_obs.get("parent_model_record_sha256"):
        findings.append(finding("MODEL_PARENT_LINEAGE_MISMATCH", "Model parent artifact or record differs from the plan.", "Bind the exact frozen parent-model artifact and record hashes."))
    if mode in {"train_from_scratch", "fine_tune"}:
        run_ok = is_sha(manifest.get("training_run_sha256")) and manifest.get("official_model_record_sha256") is None and manifest.get("status") == "training_completed"
    else:
        run_ok = manifest.get("training_run_sha256") is None and manifest.get("official_model_record_sha256") == plan_obs.get("parent_model_record_sha256") and manifest.get("artifact_sha256") == plan_obs.get("parent_model_sha256") and manifest.get("status") == "pretrained_unloaded"
    if not run_ok:
        findings.append(finding("MODEL_ORIGIN_INVALID", "Training-run or official pretrained-model lineage conflicts with mode.", "Provide the exact mode-specific origin record and status."))
    units = manifest.get("units")
    if units != EXACT_UNITS or manifest.get("cutoff_angstrom") != plan_obs.get("cutoff_angstrom"):
        findings.append(finding("MODEL_UNITS_OR_CUTOFF_INVALID", "Model units or cutoff are invalid.", "Bind exact units and planned cutoff."))
    if manifest.get("precision") != plan_obs.get("precision") or not isinstance(manifest.get("energy_reference_convention"), str) or not 1 <= len(manifest["energy_reference_convention"]) <= 128:
        findings.append(finding("MODEL_NUMERIC_CONVENTION_INVALID", "Model precision or energy reference convention is missing.", "Record exact precision and bounded energy convention ID."))
    licenses = manifest.get("licenses")
    if not exact_fields(licenses, {"framework", "model", "dataset"}) or not all(isinstance(licenses.get(key), str) and 0 < len(licenses[key]) <= 128 for key in ("framework", "model", "dataset")):
        findings.append(finding("MODEL_LICENSE_INVENTORY_INVALID", "Framework, model, and dataset licenses are not separated.", "Record all three license identities independently."))
    return report(
        "audit-model",
        findings,
        [
            gate("artifact-identity", not any(item["code"] == "MODEL_ARTIFACT_IDENTITY_INVALID" for item in findings)),
            gate("dataset-plan-origin-lineage", not any(item["code"] in {"MODEL_LINEAGE_MISMATCH", "MODEL_PARENT_LINEAGE_MISMATCH", "MODEL_ORIGIN_INVALID", "MODEL_PLAN_MISMATCH"} for item in findings)),
            gate("units-precision-convention", not any(item["code"] in {"MODEL_UNITS_OR_CUTOFF_INVALID", "MODEL_NUMERIC_CONVENTION_INVALID"} for item in findings)),
            gate("license-separation", not any(item["code"] == "MODEL_LICENSE_INVENTORY_INVALID" for item in findings)),
        ],
        [
            {"role": "model-manifest", "source_label": "model.json", "sha256": sha256(raw), "bytes": len(raw)},
            {"role": "training-plan", "source_label": "training-plan.json", "sha256": sha256(plan_raw), "bytes": len(plan_raw)},
        ],
        {
            "model_id": manifest.get("model_id") if is_id(manifest.get("model_id")) else None,
            "provider_profile": manifest.get("provider_profile") if manifest.get("provider_profile") in PROVIDERS else None,
            "provider_version": manifest.get("provider_version") if isinstance(manifest.get("provider_version"), str) else None,
            "mode": manifest.get("mode") if isinstance(manifest.get("mode"), str) else None,
            "artifact_sha256": manifest.get("artifact_sha256") if is_sha(manifest.get("artifact_sha256")) else None,
            "artifact_bytes": manifest.get("artifact_bytes") if is_int(manifest.get("artifact_bytes"), 1) else None,
            "dataset_audit_sha256": manifest.get("dataset_audit_sha256") if is_sha(manifest.get("dataset_audit_sha256")) else None,
            "species_order": manifest.get("species_order") if isinstance(manifest.get("species_order"), list) else [],
            "units": units if isinstance(units, dict) else None,
            "cutoff_angstrom": manifest.get("cutoff_angstrom") if is_number(manifest.get("cutoff_angstrom"), positive=True) else None,
            "precision": manifest.get("precision") if manifest.get("precision") in {"float32", "float64"} else None,
            "stress_policy": plan_obs.get("stress_policy") if plan_obs.get("stress_policy") in {"all_frames", "absent"} else None,
        },
        "Evaluate the exact artifact through a separately authorized, provider-specific safe adapter on the frozen test and OOD sets.",
        "technical_run_gates_only",
        [
            "The model artifact was identified but never opened, deserialized, imported, or executed.",
            "Manifest consistency does not establish model correctness, safety, domain coverage, or license authenticity.",
        ],
        action_on_pass="needs_authorization",
    )


def audit_evaluation(
    evaluation: dict[str, Any],
    raw: bytes,
    model: dict[str, Any],
    model_raw: bytes,
    dataset: dict[str, Any],
    dataset_raw: bytes,
    plan: dict[str, Any],
    plan_raw: bytes,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    findings.extend(require_pass_report(model, "audit-model"))
    findings.extend(require_pass_report(dataset, "audit-dataset"))
    findings.extend(require_pass_report(plan, "plan-training"))
    fields = {
        "schema_version",
        "evaluation_id",
        "model_audit_sha256",
        "dataset_audit_sha256",
        "training_plan_sha256",
        "evaluator_sha256",
        "test_policy",
        "test_influenced_selection",
        "metrics",
        "slice_coverage",
        "slice_metrics",
        "slice_metrics_sha256",
        "thresholds_frozen_sha256",
    }
    if not exact_fields(evaluation, fields):
        findings.append(finding("EVALUATION_FIELDS_INVALID", "Evaluation fields are missing or unsupported.", "Use the exact frozen evaluation record fields."))
    if evaluation.get("schema_version") != SCHEMA_VERSION or not is_id(evaluation.get("evaluation_id")):
        findings.append(finding("EVALUATION_IDENTITY_INVALID", "Evaluation schema or ID is invalid.", "Provide safe exact evaluation identity."))
    expected_refs = {
        "model_audit_sha256": sha256(model_raw),
        "dataset_audit_sha256": sha256(dataset_raw),
        "training_plan_sha256": sha256(plan_raw),
    }
    if any(evaluation.get(key) != value for key, value in expected_refs.items()):
        findings.append(finding("EVALUATION_LINEAGE_MISMATCH", "Evaluation does not bind exact model, dataset, and plan reports.", "Set all upstream report hashes from exact bytes."))
    if not is_sha(evaluation.get("evaluator_sha256")) or not is_sha(evaluation.get("slice_metrics_sha256")) or not is_sha(evaluation.get("thresholds_frozen_sha256")):
        findings.append(finding("EVALUATION_EVIDENCE_HASH_INVALID", "Evaluator, slice, or frozen-threshold hash is missing.", "Bind exact evaluator, slice metrics, and pre-test threshold records."))
    evaluation_role_hashes = list(expected_refs.values()) + [
        evaluation.get("evaluator_sha256"),
        evaluation.get("slice_metrics_sha256"),
        evaluation.get("thresholds_frozen_sha256"),
    ]
    valid_evaluation_role_hashes = [item for item in evaluation_role_hashes if is_sha(item)]
    if len(valid_evaluation_role_hashes) != len(set(valid_evaluation_role_hashes)):
        findings.append(finding("EVALUATION_EVIDENCE_ROLE_COLLISION", "One hash is reused for distinct evaluation-evidence roles.", "Bind distinct model, dataset, plan, evaluator, slice-metric, and frozen-threshold artifacts."))
    if evaluation.get("test_policy") != "held_out_once_after_freeze" or evaluation.get("test_influenced_selection") is not False:
        findings.append(finding("EVALUATION_TEST_LEAKAGE", "Test data was not held out independently.", "Freeze model and thresholds before one test evaluation."))
    plan_obs = plan.get("observations") if isinstance(plan.get("observations"), dict) else {}
    thresholds = plan_obs.get("thresholds") if isinstance(plan_obs.get("thresholds"), dict) else {}
    if evaluation.get("thresholds_frozen_sha256") != plan_obs.get("thresholds_sha256"):
        findings.append(finding("EVALUATION_THRESHOLDS_HASH_MISMATCH", "Evaluation does not bind the exact predeclared thresholds.", "Use the canonical threshold hash from the frozen training plan."))
    metrics = evaluation.get("metrics")
    if not isinstance(metrics, dict) or set(metrics) != set(thresholds) or not all(is_number(value) for value in metrics.values()):
        findings.append(finding("EVALUATION_METRICS_INVALID", "Metric set differs from frozen thresholds or contains invalid values.", "Report every and only predeclared metric in matching units."))
        metrics = {}
    failed_metrics = sorted(name for name, threshold in thresholds.items() if name in metrics and metrics[name] > threshold)
    if failed_metrics:
        findings.append(finding("EVALUATION_THRESHOLD_FAILED", "One or more frozen metric thresholds failed.", "Do not deploy; improve data/model under a new plan and preserve this failed record."))
    slices = evaluation.get("slice_coverage")
    if slices != ["per_species", "configuration_class", "ood"]:
        findings.append(finding("EVALUATION_SLICE_COVERAGE_MISSING", "Required per-species, configuration, or OOD slice is missing.", "Produce all frozen slice results without folding them into headline means."))
    slice_metrics = evaluation.get("slice_metrics")
    slice_metric_failures = 0
    slice_shape_ok = isinstance(slice_metrics, dict) and set(slice_metrics) == {
        "per_species",
        "configuration_class",
        "ood",
    }
    if slice_shape_ok:
        total_slices = 0
        required_slice_ids = plan_obs.get("required_slice_ids") if isinstance(plan_obs.get("required_slice_ids"), dict) else {}
        for category in ("per_species", "configuration_class", "ood"):
            items = slice_metrics.get(category)
            if not isinstance(items, list) or not 1 <= len(items) <= 1000:
                slice_shape_ok = False
                continue
            total_slices += len(items)
            seen_ids: set[str] = set()
            for item in items:
                if not exact_fields(item, {"slice_id", "metrics"}) or not is_id(item.get("slice_id")) or item.get("slice_id") in seen_ids:
                    slice_shape_ok = False
                    continue
                seen_ids.add(item["slice_id"])
                item_metrics = item.get("metrics")
                if not isinstance(item_metrics, dict) or set(item_metrics) != set(thresholds) or not all(is_number(value) for value in item_metrics.values()):
                    slice_shape_ok = False
                    continue
                slice_metric_failures += sum(
                    1 for name, threshold in thresholds.items() if item_metrics[name] > threshold
                )
            if seen_ids != set(required_slice_ids.get(category, [])):
                slice_shape_ok = False
    else:
        total_slices = 0
    if not slice_shape_ok:
        findings.append(finding("EVALUATION_SLICE_METRICS_INVALID", "Slice metrics are missing, duplicated, malformed, or incomplete.", "Provide bounded per-species, configuration-class, and OOD metrics for every frozen target."))
    else:
        canonical_slices = json.dumps(slice_metrics, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if evaluation.get("slice_metrics_sha256") != sha256(canonical_slices):
            findings.append(finding("EVALUATION_SLICE_HASH_MISMATCH", "Slice metrics hash does not bind the inline slice values.", "Recompute the SHA-256 over canonical inline slice metrics."))
        if slice_metric_failures:
            findings.append(finding("EVALUATION_SLICE_THRESHOLD_FAILED", "One or more required slice metrics exceed frozen thresholds.", "Do not deploy; preserve the failed slice record and revise data/model under a new plan."))
    return report(
        "audit-evaluation",
        findings,
        [
            gate("upstream-lineage", not any(item["code"] in {"UPSTREAM_REPORT_INVALID", "EVALUATION_LINEAGE_MISMATCH"} for item in findings)),
            gate("independent-test", not any(item["code"] == "EVALUATION_TEST_LEAKAGE" for item in findings)),
            gate("frozen-metrics", not any(item["code"] in {"EVALUATION_METRICS_INVALID", "EVALUATION_THRESHOLD_FAILED", "EVALUATION_THRESHOLDS_HASH_MISMATCH"} for item in findings)),
            gate("slice-and-ood", not any(item["code"] in {"EVALUATION_SLICE_COVERAGE_MISSING", "EVALUATION_SLICE_METRICS_INVALID", "EVALUATION_SLICE_HASH_MISMATCH", "EVALUATION_SLICE_THRESHOLD_FAILED"} for item in findings)),
        ],
        [
            {"role": "evaluation-record", "source_label": "evaluation.json", "sha256": sha256(raw), "bytes": len(raw)},
            {"role": "model-audit", "source_label": "model-audit.json", "sha256": sha256(model_raw), "bytes": len(model_raw)},
            {"role": "dataset-audit", "source_label": "dataset-audit.json", "sha256": sha256(dataset_raw), "bytes": len(dataset_raw)},
            {"role": "training-plan", "source_label": "training-plan.json", "sha256": sha256(plan_raw), "bytes": len(plan_raw)},
        ],
        {
            "evaluation_id": evaluation.get("evaluation_id") if is_id(evaluation.get("evaluation_id")) else None,
            "metric_count": len(metrics),
            "threshold_failure_count": len(failed_metrics),
            "failed_metrics": failed_metrics,
            "slice_coverage": slices if isinstance(slices, list) else [],
            "slice_count": total_slices,
            "slice_threshold_failure_count": slice_metric_failures,
        },
        "Define a bounded deployment envelope tied to this exact evaluation; independent expert review remains required.",
        "numerical_candidate_only",
        [
            "Passing declared aggregate thresholds does not establish MD stability, conservation, transferability, or scientific acceptance.",
            "Slice metrics are hash-bound but not resolved or recomputed by this metadata candidate.",
        ],
    )


def audit_deployment(
    deployment: dict[str, Any],
    raw: bytes,
    evaluation: dict[str, Any],
    evaluation_raw: bytes,
    model: dict[str, Any],
    model_raw: bytes,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    findings.extend(require_pass_report(evaluation, "audit-evaluation"))
    findings.extend(require_pass_report(model, "audit-model"))
    fields = {
        "schema_version",
        "deployment_id",
        "model_audit_sha256",
        "evaluation_audit_sha256",
        "target_engine",
        "target_version",
        "adapter_sha256",
        "species_order",
        "units",
        "observables",
        "domain",
        "max_timestep_fs",
        "ensembles",
        "monitor",
        "rollback_model_sha256",
        "pilot",
        "authorization_decision_sha256",
        "licenses_cleared",
    }
    if not exact_fields(deployment, fields):
        findings.append(finding("DEPLOYMENT_FIELDS_INVALID", "Deployment fields are missing or unsupported.", "Use the exact bounded deployment fields."))
    if deployment.get("schema_version") != SCHEMA_VERSION or not is_id(deployment.get("deployment_id")):
        findings.append(finding("DEPLOYMENT_IDENTITY_INVALID", "Deployment schema or ID is invalid.", "Provide safe exact deployment identity."))
    if deployment.get("model_audit_sha256") != sha256(model_raw) or deployment.get("evaluation_audit_sha256") != sha256(evaluation_raw):
        findings.append(finding("DEPLOYMENT_LINEAGE_MISMATCH", "Deployment does not bind exact model and evaluation reports.", "Use exact upstream report hashes."))
    model_obs = model.get("observations") if isinstance(model.get("observations"), dict) else {}
    if deployment.get("species_order") != model_obs.get("species_order") or deployment.get("units") != model_obs.get("units"):
        findings.append(finding("DEPLOYMENT_SPECIES_OR_UNITS_MISMATCH", "Deployment species order or units differ from the model.", "Use the exact audited model species order and units."))
    if not is_id(deployment.get("target_engine")) or not isinstance(deployment.get("target_version"), str) or not deployment["target_version"] or not is_sha(deployment.get("adapter_sha256")):
        findings.append(finding("DEPLOYMENT_ADAPTER_INVALID", "Target engine/version or adapter identity is missing.", "Bind an exact tested engine adapter and version."))
    observables = deployment.get("observables")
    if observables not in (["energy", "forces"], ["energy", "forces", "stress"]):
        findings.append(finding("DEPLOYMENT_OBSERVABLES_INVALID", "Deployment observables are incomplete or noncanonical.", "Request energy/forces and stress only when validated."))
    elif "stress" in observables and model_obs.get("stress_policy") != "all_frames":
        findings.append(finding("DEPLOYMENT_STRESS_UNVALIDATED", "Stress deployment was requested for a model without all-frame stress evidence.", "Remove stress or rebuild and independently evaluate a model with all-frame stress labels."))
    domain = deployment.get("domain")
    if not exact_fields(domain, {"composition_id", "structure_classes", "temperature_k", "pressure_gpa"}) or not is_id(domain.get("composition_id")) or not isinstance(domain.get("structure_classes"), list) or not domain["structure_classes"] or not all(is_id(item) for item in domain["structure_classes"]):
        findings.append(finding("DEPLOYMENT_DOMAIN_INVALID", "Composition or structural domain is incomplete.", "Provide a bounded composition and nonempty safe structure classes."))
    else:
        for field in ("temperature_k", "pressure_gpa"):
            bounds = domain.get(field)
            if not isinstance(bounds, list) or len(bounds) != 2 or not all(is_number(value) for value in bounds) or bounds[0] > bounds[1]:
                findings.append(finding("DEPLOYMENT_DOMAIN_BOUNDS_INVALID", "Temperature or pressure bounds are invalid.", "Provide finite nonnegative [minimum, maximum] bounds."))
                break
    if not is_number(deployment.get("max_timestep_fs"), positive=True) or deployment["max_timestep_fs"] > 10:
        findings.append(finding("DEPLOYMENT_TIMESTEP_INVALID", "Maximum timestep is missing or outside the bounded pilot range.", "Provide a positive timestep no greater than 10 fs."))
    ensembles = deployment.get("ensembles")
    if not isinstance(ensembles, list) or not ensembles or len(ensembles) != len(set(ensembles)) or not all(item in {"nve", "nvt", "npt"} for item in ensembles):
        findings.append(finding("DEPLOYMENT_ENSEMBLES_INVALID", "Ensemble set is empty, duplicated, or unsupported.", "Choose a unique subset of nve, nvt, and npt."))
    elif "npt" in ensembles and (not isinstance(observables, list) or "stress" not in observables):
        findings.append(finding("DEPLOYMENT_NPT_REQUIRES_STRESS", "NPT deployment lacks independently evaluated stress output.", "Add all-frame stress labels, frozen stress metrics, and stress output before requesting NPT."))
    monitor = deployment.get("monitor")
    if not exact_fields(monitor, {"kind", "threshold", "unit", "fail_action"}) or not is_id(monitor.get("kind")) or not is_number(monitor.get("threshold"), positive=True) or not isinstance(monitor.get("unit"), str) or not monitor["unit"] or monitor.get("fail_action") != "stop_and_record":
        findings.append(finding("DEPLOYMENT_MONITOR_INVALID", "Extrapolation monitor or fail action is incomplete.", "Define a numeric monitor and stop_and_record fail action."))
    if not is_sha(deployment.get("rollback_model_sha256")) or deployment.get("rollback_model_sha256") == model_obs.get("artifact_sha256"):
        findings.append(finding("DEPLOYMENT_ROLLBACK_INVALID", "Rollback model identity is missing or identical to the candidate model.", "Bind a distinct validated rollback model hash."))
    pilot = deployment.get("pilot")
    if not exact_fields(pilot, {"max_steps", "max_atoms"}) or not is_int(pilot.get("max_steps"), 1, 1000000) or not is_int(pilot.get("max_atoms"), 1, 1000000):
        findings.append(finding("DEPLOYMENT_PILOT_INVALID", "Pilot budget is missing or unbounded.", "Set bounded positive maximum steps and atoms."))
    if not is_sha(deployment.get("authorization_decision_sha256")) or deployment.get("licenses_cleared") is not True:
        findings.append(finding("DEPLOYMENT_AUTHORIZATION_OR_LICENSE_MISSING", "Execution authorization or license clearance is missing.", "Obtain external hash-bound authorization and independent license clearance."))
    deployment_role_hashes = [
        sha256(model_raw),
        sha256(evaluation_raw),
        deployment.get("adapter_sha256"),
        deployment.get("rollback_model_sha256"),
        deployment.get("authorization_decision_sha256"),
    ]
    valid_deployment_role_hashes = [item for item in deployment_role_hashes if is_sha(item)]
    if len(valid_deployment_role_hashes) != len(set(valid_deployment_role_hashes)):
        findings.append(finding("DEPLOYMENT_EVIDENCE_ROLE_COLLISION", "One hash is reused for distinct deployment-evidence roles.", "Bind distinct model, evaluation, adapter, rollback, and authorization artifacts."))
    return report(
        "audit-deployment",
        findings,
        [
            gate("model-evaluation-lineage", not any(item["code"] in {"UPSTREAM_REPORT_INVALID", "DEPLOYMENT_LINEAGE_MISMATCH"} for item in findings)),
            gate("adapter-species-units", not any(item["code"] in {"DEPLOYMENT_ADAPTER_INVALID", "DEPLOYMENT_SPECIES_OR_UNITS_MISMATCH", "DEPLOYMENT_OBSERVABLES_INVALID", "DEPLOYMENT_STRESS_UNVALIDATED", "DEPLOYMENT_NPT_REQUIRES_STRESS"} for item in findings)),
            gate("domain-and-pilot", not any(item["code"] in {"DEPLOYMENT_DOMAIN_INVALID", "DEPLOYMENT_DOMAIN_BOUNDS_INVALID", "DEPLOYMENT_TIMESTEP_INVALID", "DEPLOYMENT_ENSEMBLES_INVALID", "DEPLOYMENT_PILOT_INVALID"} for item in findings)),
            gate("monitor-and-rollback", not any(item["code"] in {"DEPLOYMENT_MONITOR_INVALID", "DEPLOYMENT_ROLLBACK_INVALID", "DEPLOYMENT_EVIDENCE_ROLE_COLLISION"} for item in findings)),
            gate("external-authorization", not any(item["code"] in {"DEPLOYMENT_AUTHORIZATION_OR_LICENSE_MISSING", "DEPLOYMENT_EVIDENCE_ROLE_COLLISION"} for item in findings)),
        ],
        [
            {"role": "deployment-record", "source_label": "deployment.json", "sha256": sha256(raw), "bytes": len(raw)},
            {"role": "evaluation-audit", "source_label": "evaluation-audit.json", "sha256": sha256(evaluation_raw), "bytes": len(evaluation_raw)},
            {"role": "model-audit", "source_label": "model-audit.json", "sha256": sha256(model_raw), "bytes": len(model_raw)},
        ],
        {
            "deployment_id": deployment.get("deployment_id") if is_id(deployment.get("deployment_id")) else None,
            "target_engine": deployment.get("target_engine") if is_id(deployment.get("target_engine")) else None,
            "target_version": deployment.get("target_version") if isinstance(deployment.get("target_version"), str) else None,
            "max_timestep_fs": deployment.get("max_timestep_fs") if is_number(deployment.get("max_timestep_fs"), positive=True) else None,
            "ensembles": ensembles if isinstance(ensembles, list) else [],
            "pilot": pilot if isinstance(pilot, dict) else None,
        },
        "Have a trusted platform resolve authorization and execute only the bounded pilot; this candidate cannot deploy it.",
        "eligible_for_expert_review",
        [
            "A syntactically complete authorization hash is not authenticated by this offline candidate.",
            "No model, adapter, engine, inference, MD trajectory, stability, or scientific result was executed or validated.",
        ],
        action_on_pass="needs_authorization",
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    dataset = commands.add_parser("audit-dataset")
    dataset.add_argument("--manifest", type=Path, required=True)
    dataset.add_argument("--out", type=Path, required=True)
    plan = commands.add_parser("plan-training")
    plan.add_argument("--request", type=Path, required=True)
    plan.add_argument("--dataset-audit", type=Path, required=True)
    plan.add_argument("--out", type=Path, required=True)
    model = commands.add_parser("audit-model")
    model.add_argument("--manifest", type=Path, required=True)
    model.add_argument("--training-plan", type=Path, required=True)
    model.add_argument("--out", type=Path, required=True)
    evaluation = commands.add_parser("audit-evaluation")
    evaluation.add_argument("--evaluation", type=Path, required=True)
    evaluation.add_argument("--model-audit", type=Path, required=True)
    evaluation.add_argument("--dataset-audit", type=Path, required=True)
    evaluation.add_argument("--training-plan", type=Path, required=True)
    evaluation.add_argument("--out", type=Path, required=True)
    deployment = commands.add_parser("audit-deployment")
    deployment.add_argument("--deployment", type=Path, required=True)
    deployment.add_argument("--evaluation-audit", type=Path, required=True)
    deployment.add_argument("--model-audit", type=Path, required=True)
    deployment.add_argument("--out", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    evidence_paths = {
        "audit-dataset": [args.manifest] if args.command == "audit-dataset" else [],
        "plan-training": [args.request, args.dataset_audit] if args.command == "plan-training" else [],
        "audit-model": [args.manifest, args.training_plan] if args.command == "audit-model" else [],
        "audit-evaluation": [args.evaluation, args.model_audit, args.dataset_audit, args.training_plan] if args.command == "audit-evaluation" else [],
        "audit-deployment": [args.deployment, args.evaluation_audit, args.model_audit] if args.command == "audit-deployment" else [],
    }[args.command]
    try:
        ensure_output_is_distinct(args.out, evidence_paths)
    except BoundaryError as exc:
        sys.stderr.write(json.dumps({"status": "blocked", "finding_code": exc.code}, sort_keys=True) + "\n")
        return 2
    try:
        if args.command == "audit-dataset":
            value, raw = load_json(args.manifest, "DATASET")
            result = audit_dataset(value, raw)
        elif args.command == "plan-training":
            value, raw = load_json(args.request, "REQUEST")
            dataset, dataset_raw = load_json(args.dataset_audit, "DATASET_AUDIT")
            result = plan_training(value, raw, dataset, dataset_raw)
        elif args.command == "audit-model":
            value, raw = load_json(args.manifest, "MODEL")
            plan, plan_raw = load_json(args.training_plan, "TRAINING_PLAN")
            result = audit_model(value, raw, plan, plan_raw)
        elif args.command == "audit-evaluation":
            value, raw = load_json(args.evaluation, "EVALUATION")
            model, model_raw = load_json(args.model_audit, "MODEL_AUDIT")
            dataset, dataset_raw = load_json(args.dataset_audit, "DATASET_AUDIT")
            plan, plan_raw = load_json(args.training_plan, "TRAINING_PLAN")
            result = audit_evaluation(value, raw, model, model_raw, dataset, dataset_raw, plan, plan_raw)
        else:
            value, raw = load_json(args.deployment, "DEPLOYMENT")
            evaluation, evaluation_raw = load_json(args.evaluation_audit, "EVALUATION_AUDIT")
            model, model_raw = load_json(args.model_audit, "MODEL_AUDIT")
            result = audit_deployment(value, raw, evaluation, evaluation_raw, model, model_raw)
    except BoundaryError as exc:
        result = boundary_report(args.command, exc)
    try:
        write_report(args.out, result)
    except BoundaryError as exc:
        sys.stderr.write(json.dumps({"status": "blocked", "finding_code": exc.code}, sort_keys=True) + "\n")
        return 2
    sys.stdout.write(json.dumps({"status": result["status"], "report": args.out.name}, sort_keys=True) + "\n")
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
