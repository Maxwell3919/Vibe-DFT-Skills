#!/usr/bin/env python3
"""Deterministic candidate guard for version-bound Multiwfn evidence."""

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
from typing import Any, TextIO

SCHEMA_VERSION = "multiwfn-guard-report@1.0"
MAX_JSON_BYTES = 1_048_576
MAX_TEXT_BYTES = 2_097_152
MAX_WAVEFUNCTION_BYTES = 536_870_912
MAX_DEPTH = 24
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FORMATS = {"fch", "fchk", "wfn", "wfx", "molden", "mwfn"}
FORMAT_SUFFIXES = {
    "fch": (".fch",),
    "fchk": (".fchk",),
    "wfn": (".wfn",),
    "wfx": (".wfx",),
    "molden": (".molden", ".mol"),
    "mwfn": (".mwfn",),
}
ELEMENT = re.compile(r"^[A-Z][a-z]?$", re.ASCII)
PERIODIC_SYMBOLS = (
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf",
    "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th",
    "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs",
    "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
)
ATOMIC_NUMBERS = {symbol: index for index, symbol in enumerate(PERIODIC_SYMBOLS, start=1)}

PROFILES = {
    "multiwfn-2026.7.15-linux-nogui": {
        "version": "2026.7.15",
        "platform": "linux-x86_64",
        "distribution": "official-noGUI-binary",
        "planning_supported": True,
        "banner": "Multiwfn -- A Multifunctional Wavefunction Analyzer",
        "update": "update date: 2026-Jul-15",
    },
    "multiwfn-community-macos": {
        "version": "unverified",
        "platform": "macos",
        "distribution": "community-build",
        "planning_supported": False,
        "blocker": "Community macOS source, build, and current-version parity are unverified.",
    },
}


class GuardError(Exception):
    def __init__(self, code: str, message: str, *, blocked: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.blocked = blocked


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
    raise ValueError(f"non-finite JSON constant {value}")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _depth(value: Any, current: int = 0) -> int:
    if current > MAX_DEPTH:
        raise ValueError("JSON nesting exceeds limit")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object key is not text")
            _depth(item, current + 1)
    elif isinstance(value, list):
        for item in value:
            _depth(item, current + 1)
    return current


def read_json_object(path: Path) -> tuple[dict[str, Any], str]:
    raw = _read_bounded_file(path, MAX_JSON_BYTES, "MW_SOURCE_INVALID", "JSON")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise GuardError("MW_SOURCE_INVALID", "JSON evidence has a forbidden BOM.")
    try:
        text = raw.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)
        _depth(value)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise GuardError("MW_SOURCE_INVALID", "JSON evidence is not one strict UTF-8 object.") from exc
    if not isinstance(value, dict):
        raise GuardError("MW_SOURCE_INVALID", "JSON evidence root must be an object.")
    return value, hashlib.sha256(raw).hexdigest()


def _object(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", f"Required object is missing: {key}.")
    return value


def _text(parent: dict[str, Any], key: str, *, safe: bool = False) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", f"Required text is missing: {key}.")
    value = value.strip()
    if safe and not SAFE_ID.fullmatch(value):
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", f"Identifier is unsafe: {key}.")
    return value


def _digest(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", f"SHA-256 is invalid: {key}.")
    return value


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _projection_payload(normalized: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "multiwfn-parent-evidence-projection@1.0",
        "source_id": normalized["source_id"],
        "format": normalized["format"],
        "wavefunction": {
            "label": normalized["file_label"],
            "sha256": normalized["file_sha256"],
            "bytes": normalized["file_bytes"],
        },
        "producer": normalized["producer"],
        "structure": {
            "fingerprint": normalized["structure_fingerprint"],
            "elements": normalized["elements"],
        },
        "electronic_state": normalized["electronic_state"],
        "basis": {
            "description": normalized["basis"]["description"],
            "representation": normalized["basis"]["representation"],
            "ecp_core_electrons": normalized["basis"]["ecp_core_electrons"],
        },
        "parent_calculation": {
            "record_id": normalized["parent_calculation"]["record_id"],
            "code": normalized["parent_calculation"]["code"],
            "code_version": normalized["parent_calculation"]["code_version"],
            "record_sha256": normalized["parent_calculation"]["record_sha256"],
            "input_hash": normalized["parent_calculation"]["input_hash"],
            "output_hash": normalized["parent_calculation"]["output_hash"],
            "acceptance": normalized["parent_calculation"]["acceptance"],
        },
    }


def validate_source(source: dict[str, Any], *, verify_projection: bool = True) -> dict[str, Any]:
    if source.get("schema_version") != "electronic-wavefunction-source@0.1-candidate":
        raise GuardError("MW_SOURCE_INVALID", "Unsupported source schema_version.")
    source_id = _text(source, "source_id", safe=True)
    file_format = _text(source, "format")
    if file_format not in FORMATS:
        raise GuardError("MW_SOURCE_INVALID", "Unsupported wavefunction format.")
    file_info = _object(source, "file")
    label = _text(file_info, "label")
    if not SAFE_LABEL.fullmatch(label) or Path(label).name != label:
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Wavefunction label must be a safe basename.")
    if not label.casefold().endswith(FORMAT_SUFFIXES[file_format]):
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Wavefunction label suffix differs from the declared format.")
    file_hash = _digest(file_info, "sha256")
    byte_count = file_info.get("bytes")
    if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count <= 0:
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Wavefunction byte count must be a positive integer.")
    producer = _object(source, "producer")
    producer_name = _text(producer, "software", safe=True)
    producer_version = _text(producer, "version", safe=True)
    method = _text(producer, "method", safe=True)
    structure = _object(source, "structure")
    fingerprint = _text(structure, "fingerprint")
    if not fingerprint.startswith("sha256:") or not SHA256.fullmatch(fingerprint[7:]):
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Structure fingerprint must be sha256:<64 lowercase hex>.")
    elements = structure.get("elements")
    if not isinstance(elements, list) or not elements or len(elements) > 100_000:
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Structure elements must be a bounded nonempty list.")
    if any(not isinstance(item, str) or not ELEMENT.fullmatch(item) or item not in ATOMIC_NUMBERS for item in elements):
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Structure contains an invalid element symbol.")
    electronic = _object(source, "electronic_state")
    charge = electronic.get("charge")
    multiplicity = electronic.get("multiplicity")
    electron_count = electronic.get("electron_count")
    spin = electronic.get("spin_treatment")
    if not isinstance(charge, int) or isinstance(charge, bool):
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Charge must be an integer.")
    if not isinstance(multiplicity, int) or isinstance(multiplicity, bool) or multiplicity < 1:
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Multiplicity must be a positive integer.")
    if not isinstance(electron_count, int) or isinstance(electron_count, bool) or electron_count < 1:
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Electron count must be a positive integer.")
    if spin not in {"restricted", "unrestricted", "unknown"}:
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Spin treatment is unsupported.")
    if (electron_count - multiplicity + 1) % 2 != 0:
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Electron count and multiplicity parity are inconsistent.")
    basis = _object(source, "basis")
    basis_description = _text(basis, "description")
    representation = basis.get("representation")
    if representation not in {"cartesian", "spherical", "mixed", "unknown"}:
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "Basis representation is unsupported.")
    ecp = basis.get("ecp_core_electrons")
    if not isinstance(ecp, int) or isinstance(ecp, bool) or ecp < 0:
        raise GuardError("MW_SOURCE_PROVENANCE_INCOMPLETE", "ECP core-electron count must be a nonnegative integer.")
    nuclear_charge = sum(ATOMIC_NUMBERS[item] for item in elements)
    if ecp > nuclear_charge or nuclear_charge - charge - ecp != electron_count:
        raise GuardError(
            "MW_SOURCE_PROVENANCE_INCOMPLETE",
            "Element nuclear charges, total charge, ECP core electrons, and electron count do not close.",
        )
    parent = _object(source, "parent_calculation")
    parent_id = _text(parent, "record_id", safe=True)
    parent_code = _text(parent, "code", safe=True)
    parent_version = _text(parent, "code_version", safe=True)
    parent_record_hash = _digest(parent, "record_sha256")
    input_hash = _digest(parent, "input_hash")
    output_hash = _digest(parent, "output_hash")
    projection_hash = _digest(parent, "evidence_projection_sha256")
    acceptance_value = _object(parent, "acceptance")
    required_acceptance = {
        "input_validation": "pass",
        "output_completion": "pass",
        "electronic_convergence": "pass",
        "wavefunction_export": "pass",
    }
    if acceptance_value != required_acceptance:
        raise GuardError(
            "MW_PARENT_ACCEPTANCE_FAILED",
            "Parent input, output, electronic, and wavefunction-export acceptance gates must all explicitly pass.",
        )
    normalized = {
        "source_id": source_id,
        "format": file_format,
        "file_label": label,
        "file_sha256": file_hash,
        "file_bytes": byte_count,
        "producer": {"software": producer_name, "version": producer_version, "method": method},
        "structure_fingerprint": fingerprint,
        "elements": elements,
        "atom_count": len(elements),
        "electronic_state": {
            "charge": charge,
            "multiplicity": multiplicity,
            "spin_treatment": spin,
            "electron_count": electron_count,
        },
        "basis": {
            "description": basis_description,
            "representation": representation,
            "ecp_core_electrons": ecp,
            "electron_count_closure": "pass",
        },
        "parent_calculation": {
            "record_id": parent_id,
            "code": parent_code,
            "code_version": parent_version,
            "record_sha256": parent_record_hash,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "acceptance": required_acceptance,
            "evidence_projection_sha256": projection_hash,
        },
    }
    expected_projection = _canonical_sha256(_projection_payload(normalized))
    if verify_projection and projection_hash != expected_projection:
        raise GuardError(
            "MW_PARENT_PROJECTION_MISMATCH",
            "Parent raw record hash and semantic evidence projection are detached.",
        )
    return normalized


def compute_evidence_projection(source: dict[str, Any]) -> str:
    """Return the projection for an otherwise valid source; intended for fixture builders."""
    normalized = validate_source(source, verify_projection=False)
    return _canonical_sha256(_projection_payload(normalized))


def verify_wavefunction(path: Path, normalized: dict[str, Any]) -> dict[str, Any]:
    if path.name != normalized["file_label"]:
        raise GuardError("MW_WAVEFUNCTION_HASH_MISMATCH", "Wavefunction basename differs from the source evidence label.")
    descriptor, before = _open_read_descriptor(
        path,
        MAX_WAVEFUNCTION_BYTES,
        "MW_WAVEFUNCTION_HASH_MISMATCH",
        "wavefunction",
    )
    digest = hashlib.sha256()
    total = 0
    try:
        with os.fdopen(descriptor, "rb") as handle:
            if before.st_size <= 0 or before.st_size != normalized["file_bytes"]:
                raise GuardError(
                    "MW_WAVEFUNCTION_HASH_MISMATCH",
                    "Wavefunction is not one bounded regular file with the declared byte count.",
                )
            while True:
                chunk = handle.read(1_048_576)
                if not chunk:
                    break
                digest.update(chunk)
                total += len(chunk)
            after = os.fstat(handle.fileno())
    except OSError as exc:
        raise GuardError("MW_WAVEFUNCTION_HASH_MISMATCH", "Unable to read wavefunction evidence.") from exc
    if (
        not stat.S_ISREG(after.st_mode)
        or after.st_nlink != 1
        or _file_identity(before) != _file_identity(after)
        or total != normalized["file_bytes"]
        or digest.hexdigest() != normalized["file_sha256"]
    ):
        raise GuardError("MW_WAVEFUNCTION_HASH_MISMATCH", "Wavefunction bytes differ from the source evidence record.")
    return {"label": normalized["file_label"], "sha256": digest.hexdigest(), "bytes": total}


def _load_verified_source(source_path: Path, wavefunction_path: Path) -> tuple[dict[str, Any], str, dict[str, Any]]:
    source, record_hash = read_json_object(source_path)
    normalized = validate_source(source)
    wavefunction = verify_wavefunction(wavefunction_path, normalized)
    return normalized, record_hash, wavefunction


def _base(command: str, status: str, claim: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": "multiwfn_guard",
        "tool_version": "1.0.0",
        "command": command,
        "status": status,
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": claim,
        "promotion_authorized": False,
        "execution_authorized": False,
        "findings": [],
        "limitations": [],
    }


def audit_source(path: Path, wavefunction_path: Path) -> dict[str, Any]:
    normalized, record_hash, wavefunction = _load_verified_source(path, wavefunction_path)
    report = _base("audit-source", "pass", "technical-wavefunction-source-provenance")
    report.update({"source_record_sha256": record_hash, "verified_wavefunction": wavefunction, "source": normalized})
    report["limitations"] = [
        "The raw wavefunction bytes are identity-verified but not scientifically parsed or validated.",
        "Producer metadata is declared evidence and does not prove calculation correctness.",
    ]
    return report


def _profile(profile_id: str) -> dict[str, Any]:
    profile = PROFILES.get(profile_id)
    if profile is None:
        raise GuardError("MW_PROFILE_UNKNOWN", "Unknown exact Multiwfn profile.")
    if not profile.get("planning_supported"):
        raise GuardError("MW_PROFILE_BLOCKED", str(profile["blocker"]), blocked=True)
    return profile


def plan_menu(path: Path, wavefunction_path: Path, profile_id: str, task: str) -> dict[str, Any]:
    normalized, record_hash, wavefunction = _load_verified_source(path, wavefunction_path)
    profile = _profile(profile_id)
    if task != "wavefunction-inventory":
        raise GuardError(
            "MW_TASK_UNSUPPORTED",
            "Only wavefunction-inventory has a version-bound candidate menu plan.",
            blocked=True,
        )
    report = _base("plan-menu", "pass", "dry-run-protocol-plan-only")
    report.update(
        {
            "dry_run": True,
            "execution_performed": False,
            "profile": {
                "id": profile_id,
                "version": profile["version"],
                "platform": profile["platform"],
                "distribution": profile["distribution"],
            },
            "task": task,
            "source_id": normalized["source_id"],
            "source_record_sha256": record_hash,
            "verified_wavefunction": wavefunction,
            "executable_identity_required": ["package_sha256", "executable_sha256", "exact_banner", "accepted_terms_url"],
            "argv_template": ["<multiwfn-executable>", "<wavefunction-file>"],
            "stdin_tokens": ["q"],
            "ordered_required_sentinels": [
                profile["banner"],
                profile["update"],
                "Loaded ",
                " successfully!",
                "Main function menu",
                "exited gracefully",
            ],
            "forbidden_sentinels": ["Error:", "Fatal error", "Segmentation fault", "forrtl: severe"],
            "expected_outputs": [],
            "side_effects": ["reads-wavefunction", "writes-no-declared-artifact"],
        }
    )
    report["limitations"] = [
        "This is a non-executing plan and contains path placeholders only.",
        "The synthetic transcript regression does not establish tool-integration maturity.",
    ]
    return report


def read_text(path: Path, code: str, description: str) -> tuple[str, str, int]:
    raw = _read_bounded_file(path, MAX_TEXT_BYTES, code, description)
    if b"\x00" in raw or raw.startswith(b"\xef\xbb\xbf"):
        raise GuardError(code, f"{description.capitalize()} contains forbidden bytes.")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GuardError(code, f"{description.capitalize()} is not strict UTF-8 text.") from exc
    return text, hashlib.sha256(raw).hexdigest(), len(raw)


def audit_transcript(path: Path, profile_id: str, task: str) -> dict[str, Any]:
    profile = _profile(profile_id)
    if task != "wavefunction-inventory":
        raise GuardError("MW_TASK_UNSUPPORTED", "This transcript task is not candidate-supported.", blocked=True)
    text, transcript_hash, transcript_bytes = read_text(path, "MW_TRANSCRIPT_INVALID", "transcript")
    if text.count(profile["banner"]) != 1:
        raise GuardError("MW_VERSION_MISMATCH", "Transcript must contain exactly one expected Multiwfn banner.")
    forbidden = ["Error:", "Fatal error", "Segmentation fault", "forrtl: severe"]
    hit = next((token for token in forbidden if token.casefold() in text.casefold()), None)
    if hit is not None:
        raise GuardError("MW_FATAL_SENTINEL", "Transcript contains a forbidden fatal/error sentinel.")
    required = [
        profile["banner"],
        profile["update"],
        "Loaded ",
        " successfully!",
        "Main function menu",
        "exited gracefully",
    ]
    positions: list[int] = []
    cursor = 0
    for token in required:
        position = text.find(token, cursor)
        if position < 0:
            raise GuardError("MW_PROMPT_DRIFT", "Transcript is missing or reorders a required sentinel.")
        positions.append(position)
        cursor = position + len(token)
    if text.count(profile["update"]) != 1 or text.count("Main function menu") != 1:
        raise GuardError("MW_PROMPT_DRIFT", "Transcript contains concatenated or repeated protocol events.")
    report = _base("audit-transcript", "pass", "technical-source-load-and-menu-completion")
    report.update(
        {
            "profile": profile_id,
            "task": task,
            "transcript_sha256": transcript_hash,
            "transcript_bytes": transcript_bytes,
            "verified_events": ["exact-banner", "exact-update-date", "load-success", "main-menu", "graceful-exit"],
        }
    )
    report["limitations"] = [
        "The transcript proves only the required textual event sequence.",
        "Synthetic validation does not prove a real binary, wavefunction, or scientific analysis.",
    ]
    return report


def parse_charge_table(source_path: Path, wavefunction_path: Path, table_path: Path) -> dict[str, Any]:
    normalized, record_hash, wavefunction = _load_verified_source(source_path, wavefunction_path)
    text, table_hash, table_bytes = read_text(table_path, "MW_TABLE_INVALID", "charge table")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        raise GuardError("MW_TABLE_INVALID", "Charge table is incomplete.")
    header_re = re.compile(r"^# multiwfn_atomic_charges_v1 method=([A-Za-z0-9._+-]+) unit=(e)$")
    header = header_re.fullmatch(lines[0])
    if header is None or sum(1 for line in lines if line.startswith("# multiwfn_atomic_charges_v1")) != 1:
        raise GuardError("MW_TABLE_INVALID", "Charge table header is missing, duplicated, or unsupported.")
    total_re = re.compile(r"^# total_charge=([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)$")
    total_match = total_re.fullmatch(lines[-1])
    if total_match is None or sum(1 for line in lines if line.startswith("# total_charge=")) != 1:
        raise GuardError("MW_TABLE_INVALID", "Charge table total is missing, duplicated, or invalid.")
    rows: list[dict[str, Any]] = []
    row_re = re.compile(r"^(\d+)\s+([A-Z][a-z]?)\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)$")
    for expected, line in enumerate(lines[1:-1], start=1):
        match = row_re.fullmatch(line)
        if match is None:
            raise GuardError("MW_TABLE_INVALID", "Charge table contains an invalid row.")
        index = int(match.group(1))
        charge = float(match.group(3))
        if index != expected or not math.isfinite(charge):
            raise GuardError("MW_TABLE_INVALID", "Charge indices are not contiguous or a value is non-finite.")
        rows.append({"atom_index": index, "element": match.group(2), "charge_e": charge})
    if len(rows) != normalized["atom_count"]:
        raise GuardError("MW_ATOM_MAPPING_MISMATCH", "Charge row count differs from source atom count.")
    if [row["element"] for row in rows] != normalized["elements"]:
        raise GuardError("MW_ATOM_MAPPING_MISMATCH", "Charge-table element order differs from source atom order.")
    declared = float(total_match.group(1))
    row_sum = math.fsum(row["charge_e"] for row in rows)
    expected_total = float(normalized["electronic_state"]["charge"])
    if not math.isfinite(declared) or abs(row_sum - declared) > 1.0e-6 or abs(declared - expected_total) > 1.0e-6:
        raise GuardError("MW_CHARGE_CLOSURE_FAILED", "Charge sum, table total, and source charge do not close.")
    report = _base("parse-charge-table", "pass", "technical-table-normalization-and-charge-closure")
    report.update(
        {
            "dataset": {
                "schema_version": "multiwfn-atomic-charges@1.0",
                "observable": "atomic-charge-table",
                "maturity": "synthetic-validated",
                "method": header.group(1),
                "unit": header.group(2),
                "source_id": normalized["source_id"],
                "source_record_sha256": record_hash,
                "source_wavefunction_sha256": normalized["file_sha256"],
                "verified_wavefunction": wavefunction,
                "source_table": {"sha256": table_hash, "bytes": table_bytes},
                "structure_fingerprint": normalized["structure_fingerprint"],
                "atom_count": len(rows),
                "rows": rows,
                "charge_sum_e": row_sum,
                "declared_total_charge_e": declared,
                "validation": {"atom_mapping": "pass", "finite_values": "pass", "charge_closure": "pass"},
            }
        }
    )
    report["limitations"] = [
        "The table is an explicit interchange format, not a parser for arbitrary Multiwfn console output.",
        "Charge closure does not establish that the selected population method is physically suitable.",
    ]
    return report


def _write_payload(handle: TextIO, payload: str) -> None:
    handle.write(payload)
    handle.flush()
    os.fsync(handle.fileno())


def _entry_stat(parent_fd: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _new_staging_file(parent_fd: int) -> tuple[int, str]:
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    for _ in range(128):
        name = f".multiwfn-report-{secrets.token_hex(16)}.tmp"
        try:
            return os.open(name, flags, 0o600, dir_fd=parent_fd), name
        except FileExistsError:
            continue
    raise OSError("unable to allocate private staging name")


def _same_lexical_path(left: Path, right: Path) -> bool:
    left_name = _canonical_absolute_path(left, "MW_OUTPUT_EXISTS", "report output")
    right_name = _canonical_absolute_path(right, "MW_OUTPUT_EXISTS", "input evidence")
    return os.path.normcase(left_name) == os.path.normcase(right_name)


def write_report(
    report: dict[str, Any],
    output: Path | None,
    forbidden_inputs: tuple[Path, ...] = (),
) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if output is None:
        sys.stdout.write(payload)
        return
    if any(_same_lexical_path(output, path) for path in forbidden_inputs):
        raise GuardError("MW_OUTPUT_EXISTS", "Refusing a report path that aliases an input pathname.")
    parent_fd: int | None = None
    staging_fd: int | None = None
    staging_name: str | None = None
    try:
        parent_fd, output_name = _open_parent_dirfd(
            output,
            "MW_OUTPUT_WRITE_FAILED",
            "report output",
            create=True,
        )
        if _entry_stat(parent_fd, output_name) is not None:
            raise GuardError("MW_OUTPUT_EXISTS", "Refusing an existing or broken-symlink report target.")
        staging_fd, staging_name = _new_staging_file(parent_fd)
        before = os.fstat(staging_fd)
        with os.fdopen(staging_fd, "w", encoding="utf-8", closefd=False) as handle:
            _write_payload(handle, payload)
        staged = os.fstat(staging_fd)
        if (
            not stat.S_ISREG(staged.st_mode)
            or staged.st_nlink != 1
            or staged.st_dev != before.st_dev
            or staged.st_ino != before.st_ino
            or staged.st_size != len(payload.encode("utf-8"))
        ):
            raise GuardError("MW_OUTPUT_WRITE_FAILED", "Staging identity changed before publication.")
        try:
            os.link(
                staging_name,
                output_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise GuardError("MW_OUTPUT_EXISTS", "Refusing an existing or raced report target.") from exc
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
            raise GuardError("MW_OUTPUT_WRITE_FAILED", "Published report is detached from the verified staging inode.")
        os.unlink(staging_name, dir_fd=parent_fd)
        staging_name = None
        final = _entry_stat(parent_fd, output_name)
        if final is None or (final.st_dev, final.st_ino) != (staged.st_dev, staged.st_ino) or final.st_nlink != 1:
            raise GuardError("MW_OUTPUT_WRITE_FAILED", "Published report identity changed during finalization.")
        os.fsync(parent_fd)
    except GuardError:
        raise
    except (OSError, UnicodeError) as exc:
        raise GuardError("MW_OUTPUT_WRITE_FAILED", "Report could not be durably published.") from exc
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


def error_report(command: str, exc: GuardError) -> dict[str, Any]:
    report = _base(command, "blocked" if exc.blocked else "fail", "none")
    report["findings"] = [{"code": exc.code, "severity": "blocker" if exc.blocked else "error", "message": exc.message}]
    report["smallest_next_action"] = (
        "Supply the exact missing version/platform/fixture evidence without weakening the gate."
        if exc.blocked
        else "Correct the reported evidence defect and rerun the same command."
    )
    return report


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    source = sub.add_parser("audit-source")
    source.add_argument("--source", type=Path, required=True)
    source.add_argument("--wavefunction", type=Path, required=True)
    source.add_argument("--out", type=Path)
    plan = sub.add_parser("plan-menu")
    plan.add_argument("--source", type=Path, required=True)
    plan.add_argument("--wavefunction", type=Path, required=True)
    plan.add_argument("--profile", required=True)
    plan.add_argument("--task", required=True)
    plan.add_argument("--out", type=Path)
    transcript = sub.add_parser("audit-transcript")
    transcript.add_argument("--transcript", type=Path, required=True)
    transcript.add_argument("--profile", required=True)
    transcript.add_argument("--task", required=True)
    transcript.add_argument("--out", type=Path)
    charges = sub.add_parser("parse-charge-table")
    charges.add_argument("--source", type=Path, required=True)
    charges.add_argument("--wavefunction", type=Path, required=True)
    charges.add_argument("--table", type=Path, required=True)
    charges.add_argument("--out", type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    forbidden_inputs = tuple(
        value
        for name in ("source", "wavefunction", "transcript", "table")
        if isinstance((value := getattr(args, name, None)), Path)
    )
    try:
        if args.command == "audit-source":
            report = audit_source(args.source, args.wavefunction)
        elif args.command == "plan-menu":
            report = plan_menu(args.source, args.wavefunction, args.profile, args.task)
        elif args.command == "audit-transcript":
            report = audit_transcript(args.transcript, args.profile, args.task)
        else:
            report = parse_charge_table(args.source, args.wavefunction, args.table)
        write_report(report, args.out, forbidden_inputs)
        return 0
    except GuardError as exc:
        report = error_report(args.command, exc)
        try:
            write_report(report, args.out, forbidden_inputs)
        except GuardError:
            sys.stdout.write(json.dumps(report, sort_keys=True, allow_nan=False) + "\n")
        return 3 if exc.blocked else 2
    except Exception:
        report = _base(args.command, "fail", "none")
        report["findings"] = [{"code": "MW_INTERNAL_ERROR", "severity": "error", "message": "Unexpected internal error."}]
        sys.stdout.write(json.dumps(report, sort_keys=True, allow_nan=False) + "\n")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
