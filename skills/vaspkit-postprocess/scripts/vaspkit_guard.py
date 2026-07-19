#!/usr/bin/env python3
"""Deterministic candidate guard for exact-version VASPKIT band routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import secrets
import stat
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "vaspkit-guard-report@1.1"
SOURCE_SCHEMA_VERSION = "vaspkit-band-source@0.2-candidate"
CALCULATION_PROJECTION_SCHEMA = "vasp-calculation-evidence-projection@1.0"
MAX_JSON_BYTES = 2_097_152
MAX_TRANSCRIPT_BYTES = 4_194_304
MAX_TABLE_BYTES = 16_777_216
MAX_DEPTH = 28
MAX_ROWS = 200_000
MAX_COLUMNS = 100_000
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")

TASKS = {
    "211": {
        "title": "basic-band-structure",
        "stdin_tokens": ["211", "0"],
        "required_inputs": ["INCAR", "DOSCAR", "EIGENVAL", "POSCAR", "KPOINTS"],
        "expected_outputs": ["BAND.dat", "BAND_REFORMATTED.dat", "KLINES.dat", "KLABELS", "BAND_GAP"],
        "sentinels": [
            "Reading Input Parameters From INCAR File",
            "Reading Fermi-Energy from DOSCAR File",
            "Reading Energy-Levels From EIGENVAL File",
            "Reading Structural Parameters from POSCAR File",
            "Reading K-Paths From KPOINTS File",
            "Written BAND.dat File",
            "Written KLABELS File",
            "Written BAND_GAP File",
            "If you want use the default setting",
        ],
    },
    "252": {
        "title": "hybrid-dft-band-structure",
        "stdin_tokens": ["252", "0"],
        "required_inputs": ["INCAR", "DOSCAR", "EIGENVAL", "POSCAR", "KPATH.in"],
        "expected_outputs": ["BAND.dat", "BAND_REFORMATTED.dat", "KLINES.dat", "KLABELS", "BAND_GAP"],
        "sentinels": [
            "Reading Input Parameters From INCAR File",
            "Reading Fermi-Energy from DOSCAR File",
            "Reading Energy-Levels From EIGENVAL File",
            "Reading Structural Parameters from POSCAR File",
            "Reading K-Paths From KPATH.in File",
            "Written BAND.dat File",
            "Written KLABELS File",
            "Written BAND_GAP File",
            "If you want use the default setting",
        ],
    },
}

PROFILES = {
    "vaspkit-1.5.0-macos-intel": {
        "version": "1.5.0",
        "platform": "macos-x86_64",
        "banner": "VASPKIT Standard Edition 1.5.0",
        "planning_supported": True,
        "maturity": "synthetic-validated",
    },
    "vaspkit-1.5.1-linux-x64": {
        "version": "1.5.1",
        "platform": "linux-x86_64",
        "banner": "VASPKIT Standard Edition 1.5.1",
        "planning_supported": False,
        "maturity": "design-only",
        "blocker": "Exact 1.5.1 package digests and version-specific menu transcript are absent.",
    },
}


class GuardError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        blocked: bool = False,
        next_action: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.blocked = blocked
        self.next_action = next_action


def _canonical_absolute_path(path: Path, code: str, description: str) -> str:
    supplied = Path(os.fspath(path))
    if ".." in supplied.parts:
        raise GuardError(code, f"{description.capitalize()} path must not contain parent traversal.")
    absolute = os.path.abspath(os.fspath(supplied))
    if sys.platform == "darwin":
        for alias, target in (("/var", "/private/var"), ("/tmp", "/private/tmp"), ("/etc", "/private/etc")):
            if absolute != alias and not absolute.startswith(alias + os.sep):
                continue
            try:
                metadata = os.lstat(alias)
                link_target = os.readlink(alias)
            except OSError:
                break
            if stat.S_ISLNK(metadata.st_mode) and metadata.st_uid == 0 and link_target in {target, target.lstrip("/")}:
                absolute = target + absolute[len(alias) :]
            break
    return absolute


def _open_parent_dirfd(
    path: Path,
    code: str,
    description: str,
    *,
    create: bool = False,
) -> tuple[int, str]:
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise GuardError(code, "Secure component-walk I/O is unavailable on this platform.")
    absolute = _canonical_absolute_path(path, code, description)
    components = list(Path(absolute).parts[1:])
    if not components or any(item in {"", ".", ".."} for item in components):
        raise GuardError(code, f"{description.capitalize()} path is invalid.")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        current = os.open(os.sep, flags)
    except OSError as exc:
        raise GuardError(code, f"Unable to anchor {description} path.") from exc
    try:
        for component in components[:-1]:
            try:
                following = os.open(component, flags, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, mode=0o700, dir_fd=current)
                following = os.open(component, flags, dir_fd=current)
            os.close(current)
            current = following
        return current, components[-1]
    except OSError as exc:
        os.close(current)
        raise GuardError(code, f"Unable to walk {description} path without symlinks.") from exc


def _file_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _open_read_descriptor(path: Path, limit: int, code: str, description: str) -> tuple[int, os.stat_result]:
    parent_fd, name = _open_parent_dirfd(path, code, description)
    flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise GuardError(code, f"Unable to read {description} evidence.") from exc
    finally:
        os.close(parent_fd)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size < 0 or before.st_size > limit:
            raise GuardError(code, f"{description.capitalize()} evidence is not one bounded single-link regular file.")
        return descriptor, before
    except Exception:
        os.close(descriptor)
        raise


def _read_bounded_file(path: Path, limit: int, code: str, description: str) -> bytes:
    descriptor, before = _open_read_descriptor(path, limit, code, description)
    try:
        with os.fdopen(descriptor, "rb") as handle:
            raw = handle.read(limit + 1)
            after = os.fstat(handle.fileno())
    except OSError as exc:
        raise GuardError(code, f"Unable to read {description} evidence.") from exc
    if (
        len(raw) > limit
        or len(raw) != before.st_size
        or not stat.S_ISREG(after.st_mode)
        or after.st_nlink != 1
        or _file_identity(before) != _file_identity(after)
    ):
        raise GuardError(code, f"{description.capitalize()} evidence exceeds the limit or changed while reading.")
    return raw


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite constant {value}")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _depth(value: Any, level: int = 0) -> None:
    if level > MAX_DEPTH:
        raise ValueError("nesting limit exceeded")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("non-text object key")
            _depth(item, level + 1)
    elif isinstance(value, list):
        for item in value:
            _depth(item, level + 1)


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _exact_keys(value: dict[str, Any], expected: set[str], code: str, description: str) -> None:
    if set(value) != expected:
        raise GuardError(code, f"{description} must contain exactly the versioned contract fields.")


def _read_json_evidence(
    path: Path,
    code: str,
    description: str,
) -> tuple[dict[str, Any], str, int]:
    raw = _read_bounded_file(path, MAX_JSON_BYTES, code, description)
    if raw.startswith(b"\xef\xbb\xbf"):
        raise GuardError(code, f"{description.capitalize()} has a forbidden BOM.")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_reject_constant)
        _depth(value)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise GuardError(code, f"{description.capitalize()} must be one strict UTF-8 JSON object.") from exc
    if not isinstance(value, dict):
        raise GuardError(code, f"{description.capitalize()} root must be an object.")
    return value, hashlib.sha256(raw).hexdigest(), len(raw)


def read_json(path: Path) -> tuple[dict[str, Any], str]:
    value, digest, _ = _read_json_evidence(path, "VK_JSON_INVALID", "JSON evidence")
    return value, digest


def _object(parent: dict[str, Any], key: str, code: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise GuardError(code, f"Required object is missing: {key}.")
    return value


def _text(parent: dict[str, Any], key: str, code: str, *, safe: bool = False) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GuardError(code, f"Required text is missing: {key}.")
    value = value.strip()
    if safe and not SAFE_ID.fullmatch(value):
        raise GuardError(code, f"Unsafe identifier: {key}.")
    return value


def _hash(parent: dict[str, Any], key: str, code: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise GuardError(code, f"Invalid SHA-256: {key}.")
    return value


def _fingerprint(parent: dict[str, Any], key: str, code: str) -> str:
    value = _text(parent, key, code)
    if not value.startswith("sha256:") or not SHA256.fullmatch(value[7:]):
        raise GuardError(code, f"Invalid structure fingerprint: {key}.")
    return value


def _artifact(parent: dict[str, Any], code: str, *, role_record: bool = False) -> dict[str, Any]:
    expected = {"label", "sha256", "bytes", "role"} if role_record else {"label", "sha256", "bytes"}
    _exact_keys(parent, expected, code, "Artifact record")
    label = _text(parent, "label", code)
    if Path(label).name != label or not SAFE_LABEL.fullmatch(label):
        raise GuardError(code, "Artifact label must be a safe basename.")
    digest = _hash(parent, "sha256", code)
    byte_count = parent.get("bytes")
    if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count <= 0:
        raise GuardError(code, "Artifact byte count must be a positive integer.")
    return {"label": label, "sha256": digest, "bytes": byte_count}


def calculation_evidence_projection_sha256(calculation: dict[str, Any]) -> str:
    """Return the versioned semantic projection hash for a parent calculation.

    This helper is intentionally deterministic and does not validate trust.  Callers
    must still compare its result with the independently supplied projection digest.
    """

    files_value = calculation.get("files")
    if not isinstance(files_value, list):
        raise GuardError("VK_SOURCE_INVALID", "Parent files must be a list before projection.")
    projected_files: list[dict[str, Any]] = []
    for item in files_value:
        if not isinstance(item, dict):
            raise GuardError("VK_SOURCE_INVALID", "Every projected parent file must be an object.")
        projected_files.append(
            {
                "role": item.get("role"),
                "sha256": item.get("sha256"),
                "bytes": item.get("bytes"),
                "label": item.get("label"),
            }
        )
    projected_files.sort(key=lambda item: str(item["role"]))
    projection = {
        "schema_version": CALCULATION_PROJECTION_SCHEMA,
        "raw_record_sha256": calculation.get("record_sha256"),
        "record_id": calculation.get("record_id"),
        "code": calculation.get("code"),
        "code_version": calculation.get("code_version"),
        "structure_fingerprint": calculation.get("structure_fingerprint"),
        "completion": calculation.get("completion"),
        "spin_channels": calculation.get("spin_channels"),
        "acceptance_gates": calculation.get("acceptance_gates"),
        "files": projected_files,
    }
    return _canonical_sha256(projection)


def _profile(profile_id: str, *, require_planning: bool = True) -> dict[str, Any]:
    profile = PROFILES.get(profile_id)
    if profile is None:
        raise GuardError("VK_PROFILE_UNKNOWN", "Unknown exact VASPKIT profile.")
    if require_planning and not profile["planning_supported"]:
        raise GuardError("VK_PROFILE_BLOCKED", str(profile["blocker"]), blocked=True)
    return profile


def _task(task_id: str) -> dict[str, Any]:
    task = TASKS.get(task_id)
    if task is None:
        raise GuardError("VK_TASK_UNSUPPORTED", "VASPKIT task is outside the candidate menu contract.", blocked=True)
    return task


def validate_source(source: dict[str, Any], *, require_adapter_evidence: bool = True) -> dict[str, Any]:
    allowed_source_keys = {"schema_version", "source_id", "calculation", "energy_reference", "adapter_request"}
    if "adapter_evidence" in source:
        allowed_source_keys.add("adapter_evidence")
    _exact_keys(source, allowed_source_keys, "VK_SOURCE_INVALID", "Source record")
    if source.get("schema_version") != SOURCE_SCHEMA_VERSION:
        raise GuardError("VK_SOURCE_INVALID", "Unsupported VASPKIT source schema_version.")
    source_id = _text(source, "source_id", "VK_SOURCE_INVALID", safe=True)
    calculation = _object(source, "calculation", "VK_SOURCE_INVALID")
    _exact_keys(
        calculation,
        {
            "record_id",
            "record_sha256",
            "evidence_projection_sha256",
            "code",
            "code_version",
            "structure_fingerprint",
            "completion",
            "spin_channels",
            "acceptance_gates",
            "files",
        },
        "VK_SOURCE_INVALID",
        "Parent calculation",
    )
    record_id = _text(calculation, "record_id", "VK_SOURCE_INVALID", safe=True)
    record_sha256 = _hash(calculation, "record_sha256", "VK_SOURCE_INVALID")
    projection_sha256 = _hash(calculation, "evidence_projection_sha256", "VK_SOURCE_INVALID")
    code = _text(calculation, "code", "VK_SOURCE_INVALID", safe=True)
    code_version = _text(calculation, "code_version", "VK_SOURCE_INVALID", safe=True)
    fingerprint = _fingerprint(calculation, "structure_fingerprint", "VK_SOURCE_INVALID")
    completion = _text(calculation, "completion", "VK_SOURCE_INVALID", safe=True)
    spin_channels = calculation.get("spin_channels")
    if not isinstance(spin_channels, int) or isinstance(spin_channels, bool) or spin_channels not in {1, 2}:
        raise GuardError("VK_SOURCE_INVALID", "spin_channels must be 1 or 2.")
    gates = _object(calculation, "acceptance_gates", "VK_SOURCE_INVALID")
    required_gate_names = {"input", "output", "electronic", "band_task"}
    _exact_keys(gates, required_gate_names, "VK_SOURCE_INVALID", "Parent acceptance_gates")
    for gate_name in sorted(required_gate_names):
        _text(gates, gate_name, "VK_SOURCE_INVALID", safe=True)
    files_value = calculation.get("files")
    if not isinstance(files_value, list) or not files_value or len(files_value) > 100:
        raise GuardError("VK_SOURCE_INVALID", "Parent files must be a bounded nonempty list.")
    files: dict[str, dict[str, Any]] = {}
    for item in files_value:
        if not isinstance(item, dict):
            raise GuardError("VK_SOURCE_INVALID", "Every parent file record must be an object.")
        role = _text(item, "role", "VK_SOURCE_INVALID")
        if role not in {"INCAR", "DOSCAR", "EIGENVAL", "POSCAR", "KPOINTS", "KPATH.in"} or role in files:
            raise GuardError("VK_SOURCE_INVALID", "Parent file role is unsupported or duplicated.")
        artifact = _artifact(item, "VK_SOURCE_INVALID", role_record=True)
        if artifact["label"] != role:
            raise GuardError("VK_SOURCE_INVALID", "A VASPKIT parent input label must equal its required role basename.")
        files[role] = artifact
    actual_projection_sha256 = calculation_evidence_projection_sha256(calculation)
    if actual_projection_sha256 != projection_sha256:
        raise GuardError(
            "VK_PARENT_EVIDENCE_MISMATCH",
            "Parent raw record hash and versioned semantic evidence projection are detached.",
        )
    if code != "vasp":
        raise GuardError("VK_SOURCE_INVALID", "Parent calculation code must be vasp.")
    if completion != "complete":
        raise GuardError("VK_PARENT_INCOMPLETE", "Parent VASP calculation must be explicitly complete.")
    if any(gates[name] != "pass" for name in required_gate_names):
        raise GuardError(
            "VK_PARENT_ACCEPTANCE_FAILED",
            "Parent input, output, electronic, and band-task acceptance gates must all pass.",
        )
    energy = _object(source, "energy_reference", "VK_ENERGY_REFERENCE_INVALID")
    _exact_keys(
        energy,
        {
            "input_table_reference",
            "additive_offset_ev",
            "unit",
            "sign_convention",
            "target_reference",
            "provenance",
            "source_role",
            "source_sha256",
        },
        "VK_ENERGY_REFERENCE_INVALID",
        "Energy-reference record",
    )
    input_reference = _text(energy, "input_table_reference", "VK_ENERGY_REFERENCE_INVALID", safe=True)
    target_reference = _text(energy, "target_reference", "VK_ENERGY_REFERENCE_INVALID", safe=True)
    provenance = _text(energy, "provenance", "VK_ENERGY_REFERENCE_INVALID", safe=True)
    source_role = _text(energy, "source_role", "VK_ENERGY_REFERENCE_INVALID", safe=True)
    source_sha256 = _hash(energy, "source_sha256", "VK_ENERGY_REFERENCE_INVALID")
    if energy.get("unit") != "eV" or energy.get("sign_convention") != "additive":
        raise GuardError("VK_ENERGY_REFERENCE_INVALID", "Energy unit/sign must be exactly eV/additive.")
    offset = energy.get("additive_offset_ev")
    if not isinstance(offset, (int, float)) or isinstance(offset, bool) or not math.isfinite(float(offset)):
        raise GuardError("VK_ENERGY_REFERENCE_INVALID", "Energy additive offset must be finite.")

    request = _object(source, "adapter_request", "VK_SOURCE_INVALID")
    _exact_keys(request, {"profile", "task"}, "VK_SOURCE_INVALID", "Adapter request")
    profile_id = _text(request, "profile", "VK_SOURCE_INVALID", safe=True)
    _profile(profile_id, require_planning=False)
    task_id = _text(request, "task", "VK_SOURCE_INVALID", safe=True)
    task = _task(task_id)
    missing = [role for role in task["required_inputs"] if role not in files]
    if missing:
        raise GuardError("VK_REQUIRED_INPUT_MISSING", "A task-required VASP input role is missing.")
    if source_role != "DOSCAR" or source_sha256 != files["DOSCAR"]["sha256"]:
        raise GuardError(
            "VK_ENERGY_REFERENCE_INVALID",
            "Energy reference must bind source_role DOSCAR and its exact parent artifact SHA-256.",
        )
    if task["stdin_tokens"][-1] == "0" and input_reference != "vaspkit-default-fermi-zeroed":
        raise GuardError(
            "VK_ENERGY_REFERENCE_INVALID",
            "Default stdin token 0 requires input_table_reference vaspkit-default-fermi-zeroed.",
        )
    adapter_value = source.get("adapter_evidence")
    adapter_evidence: dict[str, Any] | None
    if adapter_value is None:
        if require_adapter_evidence:
            raise GuardError("VK_SOURCE_INVALID", "Post-run adapter_evidence is required for audit or parsing.")
        adapter_evidence = None
    else:
        if not isinstance(adapter_value, dict):
            raise GuardError("VK_SOURCE_INVALID", "adapter_evidence must be an object when supplied.")
        _exact_keys(
            adapter_value,
            {"binary_sha256", "stdin_tokens", "transcript", "outputs"},
            "VK_SOURCE_INVALID",
            "Adapter evidence",
        )
        binary_hash = _hash(adapter_value, "binary_sha256", "VK_SOURCE_INVALID")
        stdin_tokens = adapter_value.get("stdin_tokens")
        if stdin_tokens != task["stdin_tokens"]:
            raise GuardError("VK_SOURCE_INVALID", "Recorded stdin tokens do not match the exact task profile.")
        transcript = _artifact(_object(adapter_value, "transcript", "VK_SOURCE_INVALID"), "VK_SOURCE_INVALID")
        outputs = _object(adapter_value, "outputs", "VK_SOURCE_INVALID")
        if set(outputs) != {"band", "klabels"}:
            raise GuardError("VK_SOURCE_INVALID", "Adapter outputs must contain exactly band and klabels.")
        band_artifact = _artifact(_object(outputs, "band", "VK_SOURCE_INVALID"), "VK_SOURCE_INVALID")
        klabels_artifact = _artifact(_object(outputs, "klabels", "VK_SOURCE_INVALID"), "VK_SOURCE_INVALID")
        adapter_evidence = {
            "binary_sha256": binary_hash,
            "stdin_tokens": stdin_tokens,
            "transcript": transcript,
            "outputs": {"band": band_artifact, "klabels": klabels_artifact},
        }
    return {
        "source_id": source_id,
        "calculation": {
            "record_id": record_id,
            "record_sha256": record_sha256,
            "evidence_projection_sha256": projection_sha256,
            "code": code,
            "code_version": code_version,
            "structure_fingerprint": fingerprint,
            "completion": completion,
            "spin_channels": spin_channels,
            "acceptance_gates": {name: gates[name] for name in sorted(required_gate_names)},
            "files": files,
        },
        "energy_reference": {
            "input_table_reference": input_reference,
            "additive_offset_ev": float(offset),
            "unit": "eV",
            "sign_convention": "additive",
            "target_reference": target_reference,
            "provenance": provenance,
            "source_role": source_role,
            "source_sha256": source_sha256,
        },
        "adapter_request": {"profile": profile_id, "task": task_id},
        "adapter_evidence": adapter_evidence,
    }


def _base(command: str, status: str, future_gate_ceiling: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": "vaspkit_guard",
        "tool_version": "1.1.0",
        "command": command,
        "status": status,
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": future_gate_ceiling,
        "promotion_authorized": False,
        "execution_authorized": False,
        "findings": [],
        "limitations": [],
    }


def audit_source(path: Path) -> dict[str, Any]:
    source, digest = read_json(path)
    normalized = validate_source(source)
    report = _base("audit-source", "pass", "technical-vasp-parent-and-adapter-provenance")
    report.update({"source_record_sha256": digest, "source": normalized})
    report["limitations"] = ["Declared file hashes are audited; raw VASP parents are not parsed by this candidate.", "Parent completion does not establish VASP numerical or scientific acceptance."]
    return report


def plan_menu(path: Path, profile_id: str, task_id: str) -> dict[str, Any]:
    source, digest = read_json(path)
    normalized = validate_source(source, require_adapter_evidence=False)
    profile = _profile(profile_id)
    task = _task(task_id)
    if normalized["adapter_request"]["profile"] != profile_id or normalized["adapter_request"]["task"] != task_id:
        raise GuardError("VK_SOURCE_INVALID", "Source adapter_request profile/task differs from the requested plan.")
    report = _base("plan-menu", "pass", "dry-run-menu-plan-only")
    report.update(
        {
            "source_record_sha256": digest,
            "source_id": normalized["source_id"],
            "profile": {"id": profile_id, "version": profile["version"], "platform": profile["platform"], "maturity": profile["maturity"]},
            "task": {"id": task_id, "title": task["title"]},
            "dry_run": True,
            "execution_performed": False,
            "argv_template": ["<vaspkit-executable>"],
            "stdin_tokens": task["stdin_tokens"],
            "required_inputs": task["required_inputs"],
            "expected_outputs": task["expected_outputs"],
            "ordered_required_sentinels": [profile["banner"], *task["sentinels"], "0) Quit"],
            "forbidden_sentinels": ["Error", "Fatal", "Segmentation fault", "forrtl: severe", "File Not Found"],
            "binary_identity_required": ["package_sha256", "binary_sha256", "exact_banner", "platform_architecture", "accepted_terms_url_and_date"],
            "overwrite_policy": "fresh-directory-or-refuse-existing",
        }
    )
    report["limitations"] = ["The plan does not execute VASPKIT or accept its usage agreement.", "Only one-channel band-table parsing is candidate-supported."]
    return report


def _read_text(path: Path, code: str) -> tuple[str, bytes]:
    raw = _read_bounded_file(path, MAX_TRANSCRIPT_BYTES, code, "transcript")
    if raw.startswith(b"\xef\xbb\xbf") or b"\x00" in raw:
        raise GuardError(code, "Text evidence is oversized or contains forbidden bytes.")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GuardError(code, "Text evidence is not strict UTF-8.") from exc
    return text, raw


def audit_transcript(path: Path, profile_id: str, task_id: str) -> dict[str, Any]:
    profile = _profile(profile_id)
    task = _task(task_id)
    text, raw = _read_text(path, "VK_TRANSCRIPT_INVALID")
    if text.count(profile["banner"]) != 1:
        raise GuardError("VK_VERSION_MISMATCH", "Transcript must contain exactly one exact VASPKIT banner.")
    forbidden = ["Error", "Fatal", "Segmentation fault", "forrtl: severe", "File Not Found"]
    if any(token.casefold() in text.casefold() for token in forbidden):
        raise GuardError("VK_FATAL_SENTINEL", "Transcript contains a forbidden failure sentinel.")
    task_lines = re.findall(rf"(?m)^\s*{re.escape(task_id)}\s*$", text)
    default_lines = re.findall(r"(?m)^\s*0\s*$", text)
    if len(task_lines) != 1 or len(default_lines) != 1:
        raise GuardError("VK_PROMPT_DRIFT", "Transcript must contain exactly one echoed task token and default token.")
    required = [profile["banner"], task_id, *task["sentinels"], "\n0\n", "0) Quit"]
    cursor = 0
    for sentinel in required:
        position = text.find(sentinel, cursor)
        if position < 0:
            raise GuardError("VK_PROMPT_DRIFT", "Transcript is missing or reorders a required versioned sentinel.")
        cursor = position + len(sentinel)
    report = _base("audit-transcript", "pass", "technical-versioned-menu-completion")
    report.update(
        {
            "profile": profile_id,
            "task": task_id,
            "transcript_sha256": hashlib.sha256(raw).hexdigest(),
            "transcript_bytes": len(raw),
            "verified_events": ["exact-banner", "task-token", "ordered-input-read-events", "ordered-output-write-events", "default-token", "main-menu-return"],
        }
    )
    report["limitations"] = ["Textual completion does not prove output correctness or scientific validity.", "Bundled transcript maturity is synthetic-validated only."]
    return report


def _verify_artifact(path: Path, expected: dict[str, Any], code: str) -> bytes:
    raw = _read_bounded_file(path, MAX_TABLE_BYTES, code, "adapter output")
    if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise GuardError("VK_ARTIFACT_HASH_MISMATCH", "Adapter output bytes do not match the source evidence record.")
    return raw


def _parse_band(raw: bytes) -> tuple[list[float], list[list[float]]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GuardError("VK_BAND_TABLE_INVALID", "Band table is not strict UTF-8.") from exc
    rows: list[list[float]] = []
    width: int | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "!")):
            continue
        try:
            row = [float(value) for value in stripped.split()]
        except ValueError as exc:
            raise GuardError("VK_BAND_TABLE_INVALID", "Band table contains a nonnumeric row.") from exc
        if len(row) < 2 or len(row) > MAX_COLUMNS or not all(math.isfinite(value) for value in row):
            raise GuardError("VK_BAND_TABLE_INVALID", "Band row width or values are invalid.")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise GuardError("VK_BAND_TABLE_INVALID", "Band table rows have inconsistent widths.")
        rows.append(row)
        if len(rows) > MAX_ROWS:
            raise GuardError("VK_BAND_TABLE_INVALID", "Band table exceeds the row limit.")
    if len(rows) < 2:
        raise GuardError("VK_BAND_TABLE_INVALID", "Band table requires at least two data rows.")
    path = [row[0] for row in rows]
    if any(right < left for left, right in zip(path, path[1:])) or path[-1] <= path[0]:
        raise GuardError("VK_BAND_TABLE_INVALID", "Band path must be nondecreasing with a nonzero interval.")
    assert width is not None
    bands = [[row[column] for row in rows] for column in range(1, width)]
    return path, bands


def _parse_klabels(raw: bytes, lower: float, upper: float) -> list[dict[str, Any]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GuardError("VK_KLABELS_INVALID", "KLABELS is not strict UTF-8.") from exc
    labels: list[dict[str, Any]] = []
    parsed_rows = 0
    tolerance = max(1.0, abs(lower), abs(upper)) * 1.0e-8
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("*", "#", "!")):
            continue
        fields = stripped.split()
        parsed_rows += 1
        if parsed_rows > MAX_ROWS:
            raise GuardError("VK_KLABELS_INVALID", "KLABELS exceeds the row limit.")
        if len(fields) < 2:
            raise GuardError("VK_KLABELS_INVALID", "KLABELS contains an incomplete data row.")
        label = fields[0]
        if not SAFE_ID.fullmatch(label):
            raise GuardError("VK_KLABELS_INVALID", "KLABELS contains an unsafe label.")
        try:
            coordinate = float(fields[1])
        except ValueError as exc:
            raise GuardError("VK_KLABELS_INVALID", "KLABELS contains a nonnumeric coordinate.") from exc
        if not math.isfinite(coordinate) or coordinate < lower - tolerance or coordinate > upper + tolerance:
            raise GuardError("VK_KLABELS_INVALID", "KLABELS coordinate is non-finite or outside the band path.")
        if labels and coordinate < labels[-1]["k_distance"] - tolerance:
            raise GuardError("VK_KLABELS_INVALID", "KLABELS coordinates are not ordered.")
        if labels and abs(coordinate - labels[-1]["k_distance"]) <= tolerance:
            if label != labels[-1]["label"]:
                labels[-1]["label"] = labels[-1]["label"] + "|" + label
        else:
            labels.append({"label": label, "k_distance": coordinate})
    if not labels:
        raise GuardError("VK_KLABELS_INVALID", "No high-symmetry labels were parsed.")
    return labels


def parse_bands(source_path: Path, transcript_path: Path, band_path: Path, klabels_path: Path) -> dict[str, Any]:
    source, source_hash = read_json(source_path)
    normalized = validate_source(source)
    evidence = normalized["adapter_evidence"]
    request = normalized["adapter_request"]
    assert evidence is not None
    if normalized["calculation"]["spin_channels"] != 1:
        raise GuardError("VK_SPIN_LAYOUT_UNSUPPORTED", "Only one explicitly declared spin channel is candidate-supported.", blocked=True)
    transcript_report = audit_transcript(transcript_path, request["profile"], request["task"])
    if transcript_report["transcript_sha256"] != evidence["transcript"]["sha256"] or transcript_report["transcript_bytes"] != evidence["transcript"]["bytes"]:
        raise GuardError("VK_ARTIFACT_HASH_MISMATCH", "Transcript bytes do not match the source evidence record.")
    band_raw = _verify_artifact(band_path, evidence["outputs"]["band"], "VK_BAND_TABLE_INVALID")
    labels_raw = _verify_artifact(klabels_path, evidence["outputs"]["klabels"], "VK_KLABELS_INVALID")
    kpoints, input_bands = _parse_band(band_raw)
    labels = _parse_klabels(labels_raw, kpoints[0], kpoints[-1])
    energy = normalized["energy_reference"]
    offset = energy["additive_offset_ev"]
    relative_bands = [[value + offset for value in band] for band in input_bands]
    flattened = [value for band in relative_bands for value in band]
    crossings = [index for index, band in enumerate(relative_bands, start=1) if min(band) <= 0.0 <= max(band)]
    rows = [
        {
            "k_index": k_index,
            "k_distance": distance,
            "band_index": band_index,
            "energy_input_ev": input_value,
            "energy_relative_ev": input_value + offset,
        }
        for band_index, band in enumerate(input_bands, start=1)
        for k_index, (distance, input_value) in enumerate(zip(kpoints, band), start=1)
    ]
    report = _base("parse-bands", "pass", "technical-band-table-and-menu-lineage")
    report.update(
        {
            "source_record_sha256": source_hash,
            "dataset": {
                "schema_version": "vaspkit-band-table@1.0",
                "observable": "bands",
                "maturity": "synthetic-validated",
                "source_id": normalized["source_id"],
                "calculation_record_id": normalized["calculation"]["record_id"],
                "calculation_record_sha256": normalized["calculation"]["record_sha256"],
                "calculation_evidence_projection_sha256": normalized["calculation"]["evidence_projection_sha256"],
                "structure_fingerprint": normalized["calculation"]["structure_fingerprint"],
                "profile": request["profile"],
                "task": request["task"],
                "binary_sha256": evidence["binary_sha256"],
                "transcript_sha256": transcript_report["transcript_sha256"],
                "source_artifacts": evidence["outputs"],
                "dimensions": {"kpoints": len(kpoints), "bands": len(input_bands), "spin_channels": 1, "rows": len(rows)},
                "energy_transform": {
                    "equation": "energy_relative_ev = energy_input_ev + additive_offset_ev",
                    "additive_offset_ev": offset,
                    "unit": energy["unit"],
                    "sign_convention": energy["sign_convention"],
                    "input_table_reference": energy["input_table_reference"],
                    "target_reference": energy["target_reference"],
                    "provenance": energy["provenance"],
                    "source_role": energy["source_role"],
                    "source_sha256": energy["source_sha256"],
                },
                "high_symmetry_points": labels,
                "rows": rows,
                "analysis": {
                    "energy_min_relative_ev": min(flattened),
                    "energy_max_relative_ev": max(flattened),
                    "reference_crossing_band_indices": crossings,
                },
                "validation": {"finite_values": "pass", "rectangular_dimensions": "pass", "path_mapping": "pass", "energy_reference": "pass", "artifact_lineage": "pass"},
            },
        }
    )
    report["limitations"] = ["The parser does not infer whether VASPKIT already shifted the input energies.", "Crossings on a sampled path do not establish a global Brillouin-zone property.", "Synthetic validation establishes no real VASPKIT tool integration."]
    return report


def _parent_artifact(value: Any, code: str, description: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GuardError(code, f"{description} must be an object.")
    _exact_keys(value, {"role", "label", "sha256", "bytes"}, code, description)
    role = _text(value, "role", code, safe=True)
    artifact = _artifact(value, code, role_record=True)
    return {"role": role, **artifact}


def _validate_vasp_run_manifest(manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[tuple[str, str], str]]:
    code = "VK_PARENT_RUN_MANIFEST_INVALID"
    _exact_keys(
        manifest,
        {
            "schema_version",
            "record_id",
            "code",
            "code_version",
            "task_type",
            "case_id",
            "scientific_protocol_id",
            "status",
            "scientific_acceptance",
            "configuration",
            "metrics",
            "evidence",
            "limitations",
            "provenance",
        },
        code,
        "run-manifest@1.0",
    )
    if manifest.get("schema_version") != "1.0":
        raise GuardError(code, "Parent run manifest must use schema_version 1.0.")
    parent_code = _text(manifest, "code", code, safe=True)
    if parent_code != "vasp":
        raise GuardError(
            "VK_PARENT_CODE_UNSUPPORTED",
            "VASPKIT parent ingestion accepts only VASP run manifests.",
            blocked=True,
            next_action="Supply the exact VASP run manifest and matching schema-2.0 VASP audit; do not translate another code's record into VASP fields.",
        )
    parent = {
        "record_id": _text(manifest, "record_id", code, safe=True),
        "code": parent_code,
        "code_version": _text(manifest, "code_version", code, safe=True),
        "task_type": _text(manifest, "task_type", code, safe=True),
        "case_id": _text(manifest, "case_id", code, safe=True),
        "scientific_protocol_id": _text(manifest, "scientific_protocol_id", code, safe=True),
    }
    if manifest.get("status") != "completed":
        raise GuardError("VK_PARENT_AUDIT_GATE_FAILED", "VASPKIT parent run status must be completed.")
    if manifest.get("scientific_acceptance") not in {"not_assessed", "requires_human_review"}:
        raise GuardError(code, "Parent run manifest must remain immutable pre-decision evidence.")
    configuration = manifest.get("configuration")
    if not isinstance(configuration, dict):
        raise GuardError(code, "Parent run configuration must be an object.")
    handoff = configuration.get("vaspkit_band_parent")
    if not isinstance(handoff, dict):
        raise GuardError(
            "VK_PARENT_MANIFEST_FIELDS_MISSING",
            "Active run manifest lacks configuration.vaspkit_band_parent structure/spin/menu binding.",
            blocked=True,
            next_action="Add the exact structure fingerprint, spin count, VASPKIT task, and path role to configuration.vaspkit_band_parent before emitting the immutable run manifest.",
        )
    _exact_keys(
        handoff,
        {"structure_fingerprint", "spin_channels", "adapter_task", "path_role"},
        code,
        "vaspkit_band_parent configuration",
    )
    parent["handoff"] = handoff
    evidence_value = manifest.get("evidence")
    if not isinstance(evidence_value, list) or not evidence_value or len(evidence_value) > 1000:
        raise GuardError(code, "Parent run evidence must be a bounded nonempty list.")
    evidence: dict[tuple[str, str], str] = {}
    for item in evidence_value:
        if not isinstance(item, dict) or not set(item).issubset({"role", "label", "status", "sha256"}):
            raise GuardError(code, "Every run-manifest evidence item must follow the active contract.")
        role = _text(item, "role", code, safe=True)
        label = _text(item, "label", code)
        if Path(label).name != label or not SAFE_LABEL.fullmatch(label):
            raise GuardError(code, "Run-manifest evidence labels must be safe basenames.")
        key = (role, label)
        if key in evidence:
            raise GuardError(code, "Run-manifest evidence role/label pairs must be unique.")
        if item.get("status") == "present":
            evidence[key] = _hash(item, "sha256", code)
    return parent, evidence


def _normalize_vasp_version(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized.startswith("vasp."):
        normalized = normalized[5:]
    if not normalized:
        raise GuardError("VK_PARENT_AUDIT_INVALID", "VASP audit version is empty.")
    return normalized


def _validate_active_vasp_band_audit(
    audit: dict[str, Any],
    parent: dict[str, Any],
    context: dict[str, Any],
    artifacts: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    code = "VK_PARENT_AUDIT_INVALID"
    _exact_keys(
        audit,
        {
            "audit_schema_version",
            "auditor",
            "mode",
            "task_type",
            "case_id",
            "files",
            "findings",
            "official_source_coverage",
            "gates",
            "verdict",
            "summary",
        },
        code,
        "VASP audit report",
    )
    if audit.get("audit_schema_version") != "2.0" or audit.get("auditor") != "audit_vasp_case.py" or audit.get("mode") != "run":
        raise GuardError(code, "VASP audit does not identify the active run-mode schema-2.0 producer.")
    if audit.get("task_type") != parent["task_type"] or audit.get("case_id") != parent["case_id"]:
        raise GuardError("VK_PARENT_IDENTITY_MISMATCH", "VASP audit task/case differs from the run manifest.")
    gates = _object(audit, "gates", code)
    expected_gate_names = {
        "input_integrity",
        "input_reproducibility",
        "execution_completion",
        "electronic_convergence",
        "ionic_convergence",
        "output_warnings",
        "version_identity",
        "local_official_source_coverage",
        "task_specific_validation",
        "numerical_convergence",
        "physical_validity",
        "scientific_claim",
    }
    if set(gates) != expected_gate_names:
        raise GuardError(code, "VASP audit gate set differs from the active schema; self-declared extra gates are rejected.")
    required = {
        "input_integrity",
        "input_reproducibility",
        "execution_completion",
        "electronic_convergence",
        "ionic_convergence",
        "output_warnings",
        "version_identity",
    }
    if audit.get("verdict") != "technical_run_gates_passed_scientific_claim_blocked" or any(
        gates.get(name) not in {"pass", "not_applicable"} for name in required
    ):
        raise GuardError("VK_PARENT_AUDIT_GATE_FAILED", "VASP technical run gates do not all pass.")
    if gates.get("task_specific_validation") != "not_evaluated":
        raise GuardError(code, "schema-2.0 active auditor cannot self-declare a passing band-task gate.")
    files = _object(audit, "files", code)
    incar = _object(files, "INCAR", code)
    poscar = _object(files, "POSCAR", code)
    outcar = _object(files, "OUTCAR", code)
    path_role = context["path_role"]
    audit_path_role = "KPOINTS" if path_role == "KPOINTS" else None
    if audit_path_role is None:
        raise GuardError(
            "VK_PARENT_BAND_GATE_MISSING",
            "Active VASP auditor has no KPATH.in artifact projection for VASPKIT task 252.",
            blocked=True,
            next_action="Extend the active VASP audit to bind KPATH.in for the bands task, then regenerate the audit and run manifest.",
        )
    kpoints = _object(files, audit_path_role, code)
    comparisons = {
        "INCAR": _hash(incar, "sha256", code),
        "POSCAR": _hash(poscar, "sha256", code),
        "OUTCAR": _hash(outcar, "sha256", code),
        path_role: _hash(kpoints, "sha256", code),
    }
    for role, digest in comparisons.items():
        if artifacts[role]["sha256"] != digest:
            raise GuardError("VK_PARENT_ARTIFACT_MISMATCH", f"VASP audit {role} hash differs from the handoff artifact.")
    if _normalize_vasp_version(str(outcar.get("version", ""))) != _normalize_vasp_version(parent["code_version"]):
        raise GuardError("VK_PARENT_IDENTITY_MISMATCH", "VASP OUTCAR version differs from run-manifest code_version.")
    return comparisons["INCAR"], comparisons["OUTCAR"]


def audit_parent_handoff(run_manifest_path: Path, audit_report_path: Path, request_path: Path) -> dict[str, Any]:
    manifest, manifest_hash, manifest_bytes = _read_json_evidence(
        run_manifest_path,
        "VK_PARENT_RUN_MANIFEST_INVALID",
        "parent run manifest",
    )
    audit, audit_hash, audit_bytes = _read_json_evidence(
        audit_report_path,
        "VK_PARENT_AUDIT_INVALID",
        "parent audit report",
    )
    request, request_hash, request_bytes = _read_json_evidence(
        request_path,
        "VK_PARENT_HANDOFF_MISMATCH",
        "parent handoff request",
    )
    request_code = "VK_PARENT_HANDOFF_MISMATCH"
    _exact_keys(request, {"schema_version", "request_id", "expected_parent", "band_context", "artifacts"}, request_code, "VASPKIT parent handoff request")
    if request.get("schema_version") != "vaspkit-parent-handoff-request@1.0-candidate":
        raise GuardError(request_code, "Unsupported VASPKIT parent handoff request schema.")
    request_id = _text(request, "request_id", request_code, safe=True)
    expected = _object(request, "expected_parent", request_code)
    _exact_keys(
        expected,
        {
            "record_id",
            "code",
            "code_version",
            "task_type",
            "case_id",
            "scientific_protocol_id",
            "run_manifest_sha256",
            "audit_report_sha256",
        },
        request_code,
        "Expected parent identity",
    )
    expected_parent = {
        "record_id": _text(expected, "record_id", request_code, safe=True),
        "code": _text(expected, "code", request_code, safe=True),
        "code_version": _text(expected, "code_version", request_code, safe=True),
        "task_type": _text(expected, "task_type", request_code, safe=True),
        "case_id": _text(expected, "case_id", request_code, safe=True),
        "scientific_protocol_id": _text(expected, "scientific_protocol_id", request_code, safe=True),
        "run_manifest_sha256": _hash(expected, "run_manifest_sha256", request_code),
        "audit_report_sha256": _hash(expected, "audit_report_sha256", request_code),
    }
    if expected_parent["run_manifest_sha256"] != manifest_hash or expected_parent["audit_report_sha256"] != audit_hash:
        raise GuardError("VK_PARENT_HANDOFF_HASH_MISMATCH", "Handoff request does not bind the exact raw run-manifest and audit-report bytes.")
    parent, manifest_evidence = _validate_vasp_run_manifest(manifest)
    if expected_parent["code"] != "vasp":
        raise GuardError(
            "VK_PARENT_CODE_UNSUPPORTED",
            "VASPKIT parent handoff request must name code=vasp.",
            blocked=True,
            next_action="Supply an actual VASP parent record; do not relabel another calculation code.",
        )
    for key in ("record_id", "code", "code_version", "task_type", "case_id", "scientific_protocol_id"):
        if parent[key] != expected_parent[key]:
            raise GuardError("VK_PARENT_IDENTITY_MISMATCH", f"Parent {key} differs between run manifest and handoff request.")
    if parent["task_type"] != "bands":
        raise GuardError("VK_PARENT_IDENTITY_MISMATCH", "VASPKIT band ingestion requires a VASP audit and run manifest with task_type=bands.")
    context = _object(request, "band_context", request_code)
    _exact_keys(context, {"structure_fingerprint", "spin_channels", "adapter_task", "path_role"}, request_code, "Band context")
    normalized_context = {
        "structure_fingerprint": _fingerprint(context, "structure_fingerprint", request_code),
        "spin_channels": context.get("spin_channels"),
        "adapter_task": _text(context, "adapter_task", request_code, safe=True),
        "path_role": _text(context, "path_role", request_code, safe=True),
    }
    if normalized_context["spin_channels"] not in {1, 2} or isinstance(normalized_context["spin_channels"], bool):
        raise GuardError(request_code, "Band spin_channels must be 1 or 2.")
    expected_path = {"211": "KPOINTS", "252": "KPATH.in"}.get(normalized_context["adapter_task"])
    if expected_path is None or normalized_context["path_role"] != expected_path:
        raise GuardError("VK_PARENT_HANDOFF_MISMATCH", "VASPKIT task and path role do not match the versioned menu contract.")
    if parent["handoff"] != normalized_context:
        raise GuardError("VK_PARENT_STRUCTURE_MISMATCH", "Run-manifest structure/spin/menu binding differs from the handoff request.")
    artifacts_value = _object(request, "artifacts", request_code)
    _exact_keys(
        artifacts_value,
        {"audit_report", "OUTCAR", "INCAR", "DOSCAR", "EIGENVAL", "POSCAR", "path"},
        request_code,
        "VASPKIT parent artifacts",
    )
    artifacts = {
        name: _parent_artifact(artifacts_value.get(name), request_code, f"{name} artifact")
        for name in ("audit_report", "OUTCAR", "INCAR", "DOSCAR", "EIGENVAL", "POSCAR", "path")
    }
    if artifacts["path"]["role"] != normalized_context["path_role"] or artifacts["path"]["label"] != normalized_context["path_role"]:
        raise GuardError("VK_PARENT_ARTIFACT_MISMATCH", "Path artifact role/label differs from the selected VASPKIT task.")
    for name in ("OUTCAR", "INCAR", "DOSCAR", "EIGENVAL", "POSCAR"):
        if artifacts[name]["role"] != name or artifacts[name]["label"] != name:
            raise GuardError("VK_PARENT_ARTIFACT_MISMATCH", f"{name} artifact must use its exact VASP basename role and label.")
    for artifact in artifacts.values():
        if manifest_evidence.get((artifact["role"], artifact["label"])) != artifact["sha256"]:
            raise GuardError("VK_PARENT_ARTIFACT_MISMATCH", "Handoff artifact role/label/hash is absent from or differs from run-manifest evidence.")
    if artifacts["audit_report"]["sha256"] != audit_hash:
        raise GuardError("VK_PARENT_HANDOFF_HASH_MISMATCH", "Audit artifact does not bind the exact raw audit-report bytes.")
    role_artifacts = {name: artifacts[name] for name in ("OUTCAR", "INCAR", "DOSCAR", "EIGENVAL", "POSCAR")}
    role_artifacts[normalized_context["path_role"]] = artifacts["path"]
    input_hash, output_hash = _validate_active_vasp_band_audit(audit, parent, normalized_context, role_artifacts)
    projected_files = [
        {key: item[key] for key in ("role", "sha256", "bytes", "label")}
        for role, item in sorted(role_artifacts.items())
        if role != "OUTCAR"
    ]
    calculation_projection = {
        "record_id": parent["record_id"],
        "record_sha256": manifest_hash,
        "code": "vasp",
        "code_version": parent["code_version"],
        "structure_fingerprint": normalized_context["structure_fingerprint"],
        "completion": "complete",
        "spin_channels": normalized_context["spin_channels"],
        "acceptance_gates": {
            "input": "pass",
            "output": "pass",
            "electronic": "pass",
            "band_task": "not_evaluated_by_active_audit",
        },
        "files": projected_files,
    }
    report = _base("audit-parent-handoff", "blocked", "technical-vasp-band-parent-projection")
    report.update(
        {
            "request_id": request_id,
            "local_consistency": "pass",
            "report_authentication": "unsigned-candidate-output",
            "upstream_authentication": "unresolved-no-trusted-producer-or-bundle",
            "raw_evidence": {
                "run_manifest": {"sha256": manifest_hash, "bytes": manifest_bytes},
                "audit_report": {"sha256": audit_hash, "bytes": audit_bytes},
                "handoff_request": {"sha256": request_hash, "bytes": request_bytes},
            },
            "band_context": normalized_context,
            "audited_input_sha256": input_hash,
            "audited_output_sha256": output_hash,
            "parent_projection": calculation_projection,
            "provisional_parent_projection_sha256": calculation_evidence_projection_sha256(calculation_projection),
            "eligible_for_source_record": False,
        }
    )
    report["findings"] = [
        {
            "code": "VK_PARENT_BAND_GATE_MISSING",
            "severity": "blocker",
            "message": "The active VASP schema-2.0 audit leaves task_specific_validation not_evaluated and does not bind DOSCAR/EIGENVAL to a passing band-task gate.",
            "minimum_next_action": "Extend the active VASP auditor and immutable run handoff with a deterministic bands-task gate covering DOSCAR, EIGENVAL, POSCAR, and the selected path artifact, then regenerate both records.",
        },
        {
            "code": "VK_PARENT_AUTHENTICATION_UNAVAILABLE",
            "severity": "blocker",
            "message": "Exact raw hashes establish integrity linkage but neither upstream record has trusted-producer or validated-bundle authentication.",
            "minimum_next_action": "Place the exact run manifest and audit in a validated bundle with a trusted-producer resolution record, then rerun this adapter against those immutable bytes.",
        },
    ]
    report["limitations"] = [
        "No VASP or VASPKIT process was executed.",
        "The provisional projection must not be copied into a passing source record while either blocker remains.",
    ]
    return report


def _same_path_identity(left: Path, right: Path) -> bool:
    left_normalized = os.path.normcase(_canonical_absolute_path(left, "VK_OUTPUT_INPUT_ALIAS", "report output"))
    right_normalized = os.path.normcase(_canonical_absolute_path(right, "VK_OUTPUT_INPUT_ALIAS", "input evidence"))
    return left_normalized == right_normalized


def _write_fully_and_sync(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("short report write")
        view = view[written:]
    os.fsync(descriptor)


def _entry_stat(parent_fd: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _new_staging_file(parent_fd: int, output_name: str) -> tuple[int, str]:
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    for _ in range(128):
        name = f".{output_name}.{secrets.token_hex(16)}.tmp"
        try:
            return os.open(name, flags, 0o600, dir_fd=parent_fd), name
        except FileExistsError:
            continue
    raise OSError("unable to allocate private staging name")


def _durable_publish_new(output: Path, payload: bytes, input_paths: tuple[Path, ...]) -> None:
    if any(_same_path_identity(output, input_path) for input_path in input_paths):
        raise GuardError("VK_OUTPUT_INPUT_ALIAS", "Report output must not identify any input evidence path.")
    parent_fd: int | None = None
    staging_fd: int | None = None
    staging_name: str | None = None
    try:
        parent_fd, output_name = _open_parent_dirfd(
            output,
            "VK_OUTPUT_WRITE_FAILED",
            "report output",
            create=True,
        )
        if _entry_stat(parent_fd, output_name) is not None:
            raise GuardError("VK_OUTPUT_EXISTS", "Refusing an existing or broken-symlink report target.")
        staging_fd, staging_name = _new_staging_file(parent_fd, output_name)
        before = os.fstat(staging_fd)
        _write_fully_and_sync(staging_fd, payload)
        staged = os.fstat(staging_fd)
        if (
            not stat.S_ISREG(staged.st_mode)
            or staged.st_nlink != 1
            or staged.st_dev != before.st_dev
            or staged.st_ino != before.st_ino
            or staged.st_size != len(payload)
        ):
            raise GuardError("VK_OUTPUT_WRITE_FAILED", "Staging identity changed before publication.")
        try:
            os.link(
                staging_name,
                output_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise GuardError("VK_OUTPUT_EXISTS", "Refusing an existing or raced report target.") from exc
        published = _entry_stat(parent_fd, output_name)
        linked_stage = os.fstat(staging_fd)
        if (
            published is None
            or not stat.S_ISREG(published.st_mode)
            or (published.st_dev, published.st_ino) != (staged.st_dev, staged.st_ino)
            or (linked_stage.st_dev, linked_stage.st_ino) != (staged.st_dev, staged.st_ino)
            or published.st_nlink != 2
            or linked_stage.st_nlink != 2
        ):
            raise GuardError("VK_OUTPUT_WRITE_FAILED", "Published report is detached from the verified staging inode.")
        os.unlink(staging_name, dir_fd=parent_fd)
        staging_name = None
        final = _entry_stat(parent_fd, output_name)
        if final is None or (final.st_dev, final.st_ino) != (staged.st_dev, staged.st_ino) or final.st_nlink != 1:
            raise GuardError("VK_OUTPUT_WRITE_FAILED", "Published report identity changed during finalization.")
        os.fsync(parent_fd)
    except GuardError:
        raise
    except OSError as exc:
        raise GuardError("VK_OUTPUT_WRITE_FAILED", "Durable report publication failed.") from exc
    finally:
        if staging_name is not None and parent_fd is not None:
            try:
                os.unlink(staging_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        if staging_fd is not None:
            os.close(staging_fd)
        if parent_fd is not None:
            os.close(parent_fd)


def write_report(
    report: dict[str, Any],
    output: Path | None,
    *,
    input_paths: tuple[Path, ...] = (),
) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if output is None:
        sys.stdout.write(payload)
        return
    _durable_publish_new(output, payload.encode("utf-8"), input_paths)


def error_report(command: str, exc: GuardError) -> dict[str, Any]:
    report = _base(command, "blocked" if exc.blocked else "fail", "none")
    report["findings"] = [{"code": exc.code, "severity": "blocker" if exc.blocked else "error", "message": exc.message}]
    report["smallest_next_action"] = exc.next_action or (
        "Supply exact version/task/platform evidence without inheriting maturity."
        if exc.blocked
        else "Correct the reported evidence defect and rerun."
    )
    return report


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit-source")
    audit.add_argument("--source", type=Path, required=True)
    audit.add_argument("--out", type=Path)
    plan = sub.add_parser("plan-menu")
    plan.add_argument("--source", type=Path, required=True)
    plan.add_argument("--profile", required=True)
    plan.add_argument("--task", required=True)
    plan.add_argument("--out", type=Path)
    transcript = sub.add_parser("audit-transcript")
    transcript.add_argument("--transcript", type=Path, required=True)
    transcript.add_argument("--profile", required=True)
    transcript.add_argument("--task", required=True)
    transcript.add_argument("--out", type=Path)
    bands = sub.add_parser("parse-bands")
    bands.add_argument("--source", type=Path, required=True)
    bands.add_argument("--transcript", type=Path, required=True)
    bands.add_argument("--band", type=Path, required=True)
    bands.add_argument("--klabels", type=Path, required=True)
    bands.add_argument("--out", type=Path)
    parent = sub.add_parser("audit-parent-handoff")
    parent.add_argument("--run-manifest", type=Path, required=True)
    parent.add_argument("--audit-report", type=Path, required=True)
    parent.add_argument("--handoff-request", type=Path, required=True)
    parent.add_argument("--out", type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    input_paths: tuple[Path, ...] = ()
    try:
        if args.command == "audit-source":
            input_paths = (args.source,)
            report = audit_source(args.source)
        elif args.command == "plan-menu":
            input_paths = (args.source,)
            report = plan_menu(args.source, args.profile, args.task)
        elif args.command == "audit-transcript":
            input_paths = (args.transcript,)
            report = audit_transcript(args.transcript, args.profile, args.task)
        elif args.command == "audit-parent-handoff":
            input_paths = (args.run_manifest, args.audit_report, args.handoff_request)
            report = audit_parent_handoff(args.run_manifest, args.audit_report, args.handoff_request)
        else:
            input_paths = (args.source, args.transcript, args.band, args.klabels)
            report = parse_bands(args.source, args.transcript, args.band, args.klabels)
        write_report(report, args.out, input_paths=input_paths)
        return 3 if report.get("status") == "blocked" else 0
    except GuardError as exc:
        report = error_report(args.command, exc)
        try:
            write_report(report, args.out, input_paths=input_paths)
        except GuardError:
            sys.stdout.write(json.dumps(report, sort_keys=True, allow_nan=False) + "\n")
        return 3 if exc.blocked else 2
    except Exception:
        report = _base(args.command, "fail", "none")
        report["findings"] = [{"code": "VK_INTERNAL_ERROR", "severity": "error", "message": "Unexpected internal error."}]
        sys.stdout.write(json.dumps(report, sort_keys=True, allow_nan=False) + "\n")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
