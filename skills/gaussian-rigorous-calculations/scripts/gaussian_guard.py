#!/usr/bin/env python3
"""Deterministic offline planner and sentinel auditor for the Gaussian candidate.

This module never launches Gaussian.  Reports deliberately remain at
``no_positive_claim`` while the Skill lifecycle is development.
"""

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
MAX_JSON_BYTES = 1 * 1024 * 1024
MAX_TEXT_BYTES = 16 * 1024 * 1024
SUPPORTED_REVISION = "G16 C.02"
SUPPORTED_TASKS = {
    "single_point",
    "optimization",
    "frequency",
    "optimization_frequency",
}
SUPPORTED_MODEL_CHEMISTRIES = {("B3LYP", "6-31G(d)")}
STATIONARY_POINTS = {"minimum", "transition_state", "not_applicable", "not_assessed"}
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SAFE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+*().,_-]{0,95}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CHECKPOINT_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.chk$", re.IGNORECASE)
ELEMENT_SYMBOLS = tuple(
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr "
    "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu "
    "Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh "
    "Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split()
)
ATOMIC_NUMBERS = {symbol: index for index, symbol in enumerate(ELEMENT_SYMBOLS, start=1)}
FLOAT = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[DEde][+-]?\d+)?")
SCF_ENERGY = re.compile(
    r"SCF\s+Done\s*:\s*E\([^)]*\)\s*=\s*"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[DEde][+-]?\d+)?)",
    re.IGNORECASE,
)
VERSION_PATTERNS = (
    re.compile(r"Gaussian\s+16\s*,\s*Revision\s+([A-Z]\.\d{2})", re.IGNORECASE),
    re.compile(r"Gaussian\s+16[^\n]*?G16Rev([A-Z]\.\d{2})", re.IGNORECASE),
)
UNPROFILED_ROUTE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ONIOM", re.compile(r"\boniom\b", re.IGNORECASE)),
    ("EXTERNAL", re.compile(r"\bexternal\b", re.IGNORECASE)),
    ("COUNTERPOISE", re.compile(r"\bcounterpoise\b", re.IGNORECASE)),
    ("GEN_BASIS", re.compile(r"(?:/|^|\s)(?:gen|genecp)(?:\s|$)", re.IGNORECASE)),
    ("PSEUDO_READ", re.compile(r"\bpseudo\s*=\s*read\b", re.IGNORECASE)),
    ("IRC", re.compile(r"\birc\b", re.IGNORECASE)),
    ("SCAN", re.compile(r"\bscan\b", re.IGNORECASE)),
    ("NMR", re.compile(r"\bnmr\b", re.IGNORECASE)),
    ("EXCITED_STATE", re.compile(r"(?:^|\s)(?:td|cis)(?:\s|=|\()", re.IGNORECASE)),
    ("SOLVENT", re.compile(r"\bscrf\b", re.IGNORECASE)),
    ("STABILITY", re.compile(r"\bstable\b", re.IGNORECASE)),
    ("FORCE", re.compile(r"(?:^|\s)force(?:\s|$)", re.IGNORECASE)),
    ("MODREDUNDANT", re.compile(r"\bmodredundant\b", re.IGNORECASE)),
    ("CONNECTIVITY", re.compile(r"\bconnectivity\b", re.IGNORECASE)),
)


class BoundaryError(Exception):
    """A stable, non-path-bearing input boundary failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BoundaryError("JSON_DUPLICATE_KEY", "JSON contains a duplicate object key.")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise BoundaryError("JSON_NONFINITE", "JSON contains a non-finite number.")


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
    """Open an absolute directory path component-by-component without following links."""

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


def _read_regular(path: Path, *, limit: int, kind: str) -> bytes:
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
        if before.st_size > limit:
            raise BoundaryError(f"{kind}_TOO_LARGE", f"{kind} evidence exceeds the bounded size limit.")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW") | getattr(os, "O_NONBLOCK") | getattr(os, "O_CLOEXEC", 0)
        file_fd = os.open(name, flags, dir_fd=parent_fd)
        opened = os.fstat(file_fd)
        if _stable_identity(before) != _stable_identity(opened):
            raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} evidence changed before reading.")
        chunks: list[bytes] = []
        total = 0
        while total <= limit:
            chunk = os.read(file_fd, min(65536, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        after = os.fstat(file_fd)
        final = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        _revalidate_directories(absolute, descriptors, edges, kind)
        raw = b"".join(chunks)
        if len(raw) > limit:
            raise BoundaryError(f"{kind}_TOO_LARGE", f"{kind} evidence exceeds the bounded size limit.")
        if (
            _stable_identity(opened) != _stable_identity(after)
            or _stable_identity(after) != _stable_identity(final)
            or not stat.S_ISREG(after.st_mode)
            or after.st_nlink != 1
            or len(raw) != opened.st_size
        ):
            raise BoundaryError(f"{kind}_CHANGED_DURING_READ", f"{kind} evidence changed during reading.")
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
    raw = _read_regular(path, limit=MAX_JSON_BYTES, kind=kind)
    if raw.startswith(b"\xef\xbb\xbf"):
        raise BoundaryError(f"{kind}_BOM", f"{kind} JSON must not contain a BOM.")
    try:
        text = raw.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_json_pairs, parse_constant=_reject_constant)
    except BoundaryError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise BoundaryError(f"{kind}_INVALID_JSON", f"{kind} JSON is invalid.") from exc
    if not isinstance(value, dict):
        raise BoundaryError(f"{kind}_NOT_OBJECT", f"{kind} JSON root must be an object.")
    return value, raw


def load_text(path: Path, kind: str) -> tuple[str, bytes]:
    raw = _read_regular(path, limit=MAX_TEXT_BYTES, kind=kind)
    if b"\x00" in raw:
        raise BoundaryError(f"{kind}_NUL", f"{kind} text contains a NUL byte.")
    try:
        return raw.decode("utf-8"), raw
    except UnicodeError as exc:
        raise BoundaryError(f"{kind}_INVALID_UTF8", f"{kind} text is not valid UTF-8.") from exc


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


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
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
            candidate = f".gaussian-guard-{secrets.token_hex(12)}.tmp"
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
            os.link(
                stage_name,
                target.name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
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


def _safe_label(value: object, *, checkpoint: bool = False) -> bool:
    if not isinstance(value, str) or Path(value).name != value or value in {".", ".."}:
        return False
    return bool((CHECKPOINT_LABEL if checkpoint else SAFE_ID).fullmatch(value))


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _finite_positive(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def finding(code: str, message: str, next_action: str) -> dict[str, str]:
    return {"code": code, "message": message, "next_action": next_action}


def gate(identifier: str, passed: bool, codes: Iterable[str] = ()) -> dict[str, Any]:
    return {
        "id": identifier,
        "status": "pass" if passed else "blocked",
        "finding_codes": list(codes),
    }


def _blocked_report(command: str, code: str, message: str) -> dict[str, Any]:
    item = finding(code, message, "Provide a regular, bounded, schema-valid evidence file and rerun the same command.")
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_name": "gaussian-candidate-audit",
        "command": command,
        "candidate_lifecycle": "development",
        "status": "blocked",
        "action_state": "local_gate_blocked",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": "no_positive_claim",
        "gates": [],
        "findings": [item],
        "smallest_next_action": item["next_action"],
        "evidence": [],
        "limitations": ["No Gaussian execution or scientific conclusion is established."],
    }


def validate_request(value: dict[str, Any]) -> list[dict[str, str]]:
    required = {
        "schema_version",
        "case_id",
        "gaussian_revision",
        "task",
        "model_chemistry",
        "charge",
        "multiplicity",
        "atom_count",
        "structure_manifest_sha256",
        "target",
        "stationary_point",
        "expected_checkpoint",
        "parent_checkpoint_ref",
    }
    findings: list[dict[str, str]] = []
    if set(value) != required:
        findings.append(finding("PLAN_FIELDS_INVALID", "Plan request fields are missing or unsupported.", "Use the exact documented request fields."))
        return findings
    if value.get("schema_version") != SCHEMA_VERSION:
        findings.append(finding("PLAN_SCHEMA_VERSION_INVALID", "Plan schema version is unsupported.", f"Set schema_version to {SCHEMA_VERSION}."))
    if not _safe_label(value.get("case_id")):
        findings.append(finding("PLAN_CASE_ID_INVALID", "Case ID is unsafe or missing.", "Use a short lowercase safe case ID."))
    if value.get("gaussian_revision") != SUPPORTED_REVISION:
        findings.append(finding("PLAN_REVISION_UNSUPPORTED", "Gaussian revision is not the registered candidate revision.", f"Use {SUPPORTED_REVISION} or add a separately reviewed version profile."))
    task = value.get("task")
    if task not in SUPPORTED_TASKS:
        findings.append(finding("PLAN_TASK_UNSUPPORTED", "Task is outside the candidate task set.", "Choose one exact supported task or add a reviewed task profile."))
    model = value.get("model_chemistry")
    if not isinstance(model, dict) or set(model) != {"method", "basis"}:
        findings.append(finding("PLAN_MODEL_CHEMISTRY_INVALID", "Method and basis must be explicit.", "Provide exact method and basis tokens."))
    else:
        if not isinstance(model.get("method"), str) or not SAFE_TOKEN.fullmatch(model["method"]):
            findings.append(finding("PLAN_METHOD_INVALID", "Method token is missing or unsafe.", "Provide an explicit safe method token."))
        if not isinstance(model.get("basis"), str) or not SAFE_TOKEN.fullmatch(model["basis"]):
            findings.append(finding("PLAN_BASIS_INVALID", "Basis token is missing or unsafe.", "Provide an explicit safe basis token."))
        if (model.get("method"), model.get("basis")) not in SUPPORTED_MODEL_CHEMISTRIES:
            findings.append(finding("PLAN_MODEL_CHEMISTRY_UNSUPPORTED", "Model chemistry is outside the only registered parser profile.", "Use exact B3LYP/6-31G(d) for this synthetic candidate profile or add separately reviewed public-source and licensed real-fixture evidence."))
    if not _integer(value.get("charge")) or not -20 <= value["charge"] <= 20:
        findings.append(finding("PLAN_CHARGE_INVALID", "Charge is missing or outside the bounded range.", "Provide an integer charge between -20 and 20."))
    if not _integer(value.get("multiplicity")) or not 1 <= value["multiplicity"] <= 20:
        findings.append(finding("PLAN_MULTIPLICITY_INVALID", "Multiplicity is missing or outside the bounded range.", "Provide an integer multiplicity between 1 and 20."))
    if not _integer(value.get("atom_count")) or not 1 <= value["atom_count"] <= 100000:
        findings.append(finding("PLAN_ATOM_COUNT_INVALID", "Atom count is missing or outside the bounded range.", "Provide an explicit positive atom count."))
    if not isinstance(value.get("structure_manifest_sha256"), str) or SHA256.fullmatch(value["structure_manifest_sha256"]) is None:
        findings.append(finding("PLAN_STRUCTURE_LINEAGE_INVALID", "Molecular structure-manifest hash is missing.", "Bind the exact accepted molecular structure manifest with SHA-256."))
    target = value.get("target")
    if not isinstance(target, dict) or set(target) != {"observable", "unit", "absolute_tolerance"}:
        findings.append(finding("PLAN_TARGET_INVALID", "Target observable, unit, and tolerance must be explicit.", "Provide the exact target object."))
    else:
        if not _safe_label(target.get("observable")):
            findings.append(finding("PLAN_OBSERVABLE_INVALID", "Observable is missing or unsafe.", "Provide a safe observable ID."))
        if not isinstance(target.get("unit"), str) or not target["unit"].strip() or len(target["unit"]) > 32:
            findings.append(finding("PLAN_UNIT_INVALID", "Observable unit is missing or unsafe.", "Provide an explicit bounded unit string."))
        if not _finite_positive(target.get("absolute_tolerance")):
            findings.append(finding("PLAN_TOLERANCE_INVALID", "Absolute tolerance must be finite and positive.", "Provide a positive finite tolerance."))
    stationary = value.get("stationary_point")
    if stationary not in STATIONARY_POINTS:
        findings.append(finding("PLAN_STATIONARY_POINT_INVALID", "Stationary-point intent is unsupported.", "Choose minimum, transition_state, not_applicable, or not_assessed."))
    if task in {"frequency", "optimization_frequency"} and stationary not in {"minimum", "transition_state"}:
        findings.append(finding("PLAN_STATIONARY_POINT_REQUIRED", "Frequency tasks require a planned stationary-point type.", "Choose minimum or transition_state."))
    if task == "single_point" and stationary != "not_applicable":
        findings.append(finding("PLAN_STATIONARY_POINT_CONFLICT", "Single-point task must use not_applicable.", "Set stationary_point to not_applicable."))
    if task == "optimization" and stationary != "not_assessed":
        findings.append(finding("PLAN_STATIONARY_POINT_CONFLICT", "Optimization without frequency analysis cannot predeclare a stationary-point type in this profile.", "Set stationary_point to not_assessed."))
    if task == "optimization_frequency" and stationary != "minimum":
        findings.append(finding("PLAN_STATIONARY_POINT_CONFLICT", "The plain Opt+Freq profile supports a minimum candidate only; transition-state optimization keywords are not implemented.", "Use minimum or add a separately reviewed transition-state optimization profile."))
    expected_checkpoint = value.get("expected_checkpoint")
    if expected_checkpoint is not None and not _safe_label(expected_checkpoint, checkpoint=True):
        findings.append(finding("PLAN_CHECKPOINT_LABEL_INVALID", "Checkpoint label is unsafe.", "Use a portable .chk basename without directories."))
    parent = value.get("parent_checkpoint_ref")
    if parent is not None:
        if not isinstance(parent, dict) or set(parent) != {"source_label", "sha256"}:
            findings.append(finding("PLAN_PARENT_REF_INVALID", "Parent checkpoint reference is malformed.", "Provide source_label and exact SHA-256 only."))
        elif not _safe_label(parent.get("source_label"), checkpoint=True) or not isinstance(parent.get("sha256"), str) or not SHA256.fullmatch(parent["sha256"]):
            findings.append(finding("PLAN_PARENT_REF_INVALID", "Parent checkpoint reference is unsafe or unhashed.", "Provide a portable .chk label and lowercase SHA-256."))
    return findings


def make_plan(request: dict[str, Any], raw: bytes) -> dict[str, Any]:
    findings = validate_request(request)
    passed = not findings
    canonical_request = json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_name": "gaussian-candidate-plan",
        "command": "plan",
        "candidate_lifecycle": "development",
        "status": "pass" if passed else "blocked",
        "action_state": "local_gate_passed_limited" if passed else "local_gate_blocked",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": "no_positive_claim",
        "plan_id": f"gaussian-plan-{_sha256(canonical_request)[:24]}",
        "request_sha256": _sha256(raw),
        "plan": request if passed else None,
        "gates": [gate("plan-integrity", passed, [item["code"] for item in findings])],
        "findings": findings,
        "smallest_next_action": (
            findings[0]["next_action"] if findings else "Audit the exact Gaussian input bytes against this plan."
        ),
        "evidence": [{"role": "plan-request", "source_label": "request.json", "sha256": _sha256(raw), "bytes": len(raw)}],
        "limitations": [
            "The Skill remains in development and non-routable.",
            "The plan does not authenticate a license, execute Gaussian, or establish scientific validity.",
        ],
    }
    return report


def validate_plan_record(value: dict[str, Any]) -> list[dict[str, str]]:
    required = {
        "schema_version",
        "contract_name",
        "command",
        "candidate_lifecycle",
        "status",
        "action_state",
        "claim_ceiling",
        "future_gate_ceiling",
        "plan_id",
        "request_sha256",
        "plan",
        "gates",
        "findings",
        "smallest_next_action",
        "evidence",
        "limitations",
    }
    if set(value) != required:
        return [finding("PLAN_RECORD_FIELDS_INVALID", "Plan record fields are missing or unsupported.", "Regenerate the plan with this candidate version.")]
    if (
        value.get("contract_name") != "gaussian-candidate-plan"
        or value.get("schema_version") != SCHEMA_VERSION
        or value.get("command") != "plan"
        or value.get("candidate_lifecycle") != "development"
    ):
        return [finding("PLAN_RECORD_INVALID", "Plan record identity is invalid.", "Regenerate the plan with this candidate version.")]
    if (
        value.get("status") != "pass"
        or value.get("action_state") != "local_gate_passed_limited"
        or value.get("claim_ceiling") != "no_positive_claim"
        or value.get("future_gate_ceiling") != "no_positive_claim"
        or value.get("findings") != []
        or not isinstance(value.get("plan"), dict)
    ):
        return [finding("PLAN_RECORD_BLOCKED", "Plan record did not pass.", "Resolve the plan findings and regenerate it.")]
    request_findings = validate_request(value["plan"])
    if request_findings:
        return request_findings
    canonical = json.dumps(value["plan"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    expected_plan_id = f"gaussian-plan-{_sha256(canonical)[:24]}"
    request_sha = value.get("request_sha256")
    evidence = value.get("evidence")
    gates = value.get("gates")
    if value.get("plan_id") != expected_plan_id:
        return [finding("PLAN_RECORD_ID_MISMATCH", "Plan ID does not bind the plan content.", "Regenerate the plan after any request change.")]
    if not isinstance(request_sha, str) or SHA256.fullmatch(request_sha) is None:
        return [finding("PLAN_RECORD_REQUEST_HASH_INVALID", "Plan request hash is invalid.", "Regenerate the plan from exact request bytes.")]
    if not isinstance(gates, list) or len(gates) != 1 or gates[0] != gate("plan-integrity", True):
        return [finding("PLAN_RECORD_GATE_INVALID", "Plan-integrity gate is not canonical.", "Regenerate the plan with the deterministic planner.")]
    if not isinstance(evidence, list) or len(evidence) != 1 or evidence[0] != {
        "role": "plan-request",
        "source_label": "request.json",
        "sha256": request_sha,
        "bytes": evidence[0].get("bytes") if isinstance(evidence[0], dict) else None,
    }:
        return [finding("PLAN_RECORD_EVIDENCE_INVALID", "Plan evidence reference is not canonical.", "Regenerate the plan from exact request bytes.")]
    if not isinstance(evidence[0].get("bytes"), int) or isinstance(evidence[0].get("bytes"), bool) or evidence[0]["bytes"] <= 0:
        return [finding("PLAN_RECORD_EVIDENCE_INVALID", "Plan evidence byte count is invalid.", "Regenerate the plan from exact request bytes.")]
    return []


def _parse_input(text: str) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    if re.search(r"^\s*--Link1--\s*$", text, re.MULTILINE | re.IGNORECASE):
        findings.append(finding("INPUT_LINK1_UNSUPPORTED", "Multi-link input is outside the parser profile.", "Split and validate one hash-bound job or add a reviewed Link1 profile."))
        return None, findings
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    index = 0
    link0: dict[str, str] = {}
    while index < len(lines) and (not lines[index].strip() or lines[index].lstrip().startswith("%")):
        stripped = lines[index].strip()
        if stripped.startswith("%"):
            if "=" in stripped:
                key, value = stripped[1:].split("=", 1)
                lowered = key.strip().lower()
                if lowered in link0:
                    findings.append(finding("INPUT_LINK0_DUPLICATE", "A Link 0 key is duplicated.", "Keep one unambiguous value for each Link 0 key."))
                link0[lowered] = value.strip()
            else:
                link0[stripped[1:].strip().lower()] = ""
        index += 1
    unsupported_link0 = sorted(set(link0).difference({"chk", "oldchk", "mem", "nprocshared"}))
    if unsupported_link0:
        findings.append(finding("INPUT_LINK0_UNSUPPORTED", "Input contains an unprofiled Link 0 directive.", "Remove it or add a reviewed directive-specific profile."))
    if "mem" in link0 and re.fullmatch(r"[1-9]\d*(?:KB|MB|GB|TB|MW|GW)?", link0["mem"], re.IGNORECASE) is None:
        findings.append(finding("INPUT_MEMORY_INVALID", "Memory directive is outside the supported numeric form.", "Use a positive integer with an optional documented size suffix."))
    if "nprocshared" in link0:
        try:
            nproc = int(link0["nprocshared"])
        except ValueError:
            nproc = 0
        if not 1 <= nproc <= 1048576:
            findings.append(finding("INPUT_NPROCSHARED_INVALID", "Shared-process count is outside the bounded positive range.", "Use a positive bounded integer process count."))
    if index >= len(lines) or not lines[index].lstrip().startswith("#"):
        findings.append(finding("INPUT_ROUTE_MISSING", "A single route section was not found.", "Provide one supported route section beginning with #."))
        return None, findings
    route_lines: list[str] = []
    while index < len(lines) and lines[index].strip():
        if index != 0 and lines[index].lstrip().startswith("#") and route_lines:
            findings.append(finding("INPUT_ROUTE_AMBIGUOUS", "More than one route start was found.", "Provide one unambiguous route section."))
        route_lines.append(lines[index].strip())
        index += 1
    route = " ".join(route_lines)
    index += 1
    title_count = 0
    while index < len(lines) and lines[index].strip():
        title_count += 1
        index += 1
    if title_count == 0:
        findings.append(finding("INPUT_TITLE_MISSING", "The supported input subset requires a nonempty title section.", "Provide a nonempty title without relying on a filename."))
    index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        findings.append(finding("INPUT_CHARGE_MULTIPLICITY_MISSING", "Charge and multiplicity were not found.", "Provide explicit integer charge and multiplicity."))
        return None, findings
    charge_match = re.fullmatch(r"\s*([+-]?\d+)\s+(\d+)\s*", lines[index])
    if charge_match is None:
        findings.append(finding("INPUT_CHARGE_MULTIPLICITY_INVALID", "Charge/multiplicity line is malformed.", "Provide two explicit integers after the title section."))
        return None, findings
    charge = int(charge_match.group(1))
    multiplicity = int(charge_match.group(2))
    index += 1
    atom_count = 0
    atomic_numbers: list[int] = []
    while index < len(lines) and lines[index].strip():
        parts = lines[index].split()
        if len(parts) != 4:
            findings.append(finding("INPUT_COORDINATE_INVALID", "A Cartesian coordinate line is outside the supported subset.", "Use element/atomic-number plus three finite Cartesian coordinates."))
            index += 1
            continue
        atom_token = parts[0]
        if atom_token.isdigit():
            atomic_number = int(atom_token)
            element_ok = 1 <= atomic_number <= len(ELEMENT_SYMBOLS)
        else:
            atomic_number = ATOMIC_NUMBERS.get(atom_token, 0)
            element_ok = atomic_number > 0
        if not element_ok:
            findings.append(finding("INPUT_ELEMENT_UNSUPPORTED", "Cartesian atom label is not a canonical element or atomic number 1-118.", "Use a canonical element symbol or add a reviewed atom-label profile."))
            index += 1
            continue
        try:
            coordinates = [float(value.replace("D", "E").replace("d", "e")) for value in parts[1:4]]
        except ValueError:
            findings.append(finding("INPUT_COORDINATE_INVALID", "A Cartesian coordinate is not numeric.", "Use three finite Cartesian coordinates per atom."))
        else:
            if not all(math.isfinite(value) for value in coordinates):
                findings.append(finding("INPUT_COORDINATE_INVALID", "A Cartesian coordinate is non-finite.", "Use finite Cartesian coordinates."))
            else:
                atom_count += 1
                atomic_numbers.append(atomic_number)
        index += 1
    if any(line.strip() for line in lines[index + 1 :]):
        findings.append(finding("INPUT_TRAILING_SECTION_UNSUPPORTED", "Input contains an unparsed trailing section.", "Remove it or add a reviewed parser profile for that section."))
    parsed = {
        "link0": link0,
        "route": route,
        "charge": charge,
        "multiplicity": multiplicity,
        "atom_count": atom_count,
        "atomic_numbers": atomic_numbers,
    }
    return parsed, findings


def _route_has(route: str, token: str) -> bool:
    return re.search(rf"(?:^|\s){re.escape(token)}(?:\s|=|\(|$)", route, re.IGNORECASE) is not None


def _route_model_tokens(route: str) -> list[str]:
    body = route.strip()
    if body.startswith("#"):
        body = body[1:].strip()
    tokens = body.split()
    if tokens and tokens[0].casefold() in {"p", "n", "t"}:
        tokens = tokens[1:]
    return [token.casefold() for token in tokens if "/" in token]


def _unsupported_route_tokens(route: str, model_token: str) -> list[str]:
    body = route.strip()
    if body.startswith("#"):
        body = body[1:].strip()
    tokens = body.split()
    if tokens and tokens[0].casefold() in {"p", "n", "t"}:
        tokens = tokens[1:]
    allowed = {model_token, "opt", "freq", "guess=read", "chkbasis", "readfc"}
    return [token for token in tokens if token.casefold() not in allowed]


def audit_input_data(text: str, raw: bytes, plan_record: dict[str, Any], plan_raw: bytes) -> dict[str, Any]:
    plan_findings = validate_plan_record(plan_record)
    findings = list(plan_findings)
    parsed: dict[str, Any] | None = None
    if not findings:
        parsed, parsing_findings = _parse_input(text)
        findings.extend(parsing_findings)
    plan = plan_record.get("plan") if isinstance(plan_record.get("plan"), dict) else {}
    gates: list[dict[str, Any]] = [gate("plan-integrity", not plan_findings, [item["code"] for item in plan_findings])]
    structure_lineage_ok = not plan_findings and isinstance(plan.get("structure_manifest_sha256"), str) and SHA256.fullmatch(plan["structure_manifest_sha256"]) is not None
    gates.append(gate("structure-lineage", structure_lineage_ok, [] if structure_lineage_ok else ["PLAN_STRUCTURE_LINEAGE_INVALID"]))
    gates.append(gate("input-identity", True))
    if parsed is not None:
        route = str(parsed["route"])
        for label, pattern in UNPROFILED_ROUTE_PATTERNS:
            if pattern.search(route):
                findings.append(finding(f"INPUT_FEATURE_{label}_UNSUPPORTED", "The route contains an unprofiled feature.", "Remove the feature or add a versioned task profile with real licensed validation."))
        model = plan.get("model_chemistry") if isinstance(plan.get("model_chemistry"), dict) else {}
        model_token = f"{model.get('method', '')}/{model.get('basis', '')}".casefold()
        observed_model_tokens = _route_model_tokens(route)
        model_ok = observed_model_tokens == [model_token]
        if not model_ok:
            findings.append(finding("INPUT_MODEL_CHEMISTRY_MISMATCH", "Route method/basis does not match the plan.", "Use the exact planned method/basis or regenerate the plan."))
        gates.append(gate("route-model-chemistry", model_ok, [] if model_ok else ["INPUT_MODEL_CHEMISTRY_MISMATCH"]))
        unsupported_tokens = _unsupported_route_tokens(route, model_token)
        if unsupported_tokens:
            findings.append(finding("INPUT_ROUTE_TOKEN_UNSUPPORTED", "Route contains a token outside the narrow allowlist.", "Remove the token or add a versioned, real-fixture parser profile."))
        task = plan.get("task")
        has_opt = _route_has(route, "opt")
        has_freq = _route_has(route, "freq")
        task_ok = {
            "single_point": not has_opt and not has_freq,
            "optimization": has_opt and not has_freq,
            "frequency": has_freq and not has_opt,
            "optimization_frequency": has_opt and has_freq,
        }.get(task, False)
        if not task_ok:
            findings.append(finding("INPUT_TASK_MISMATCH", "Route task keywords do not match the plan.", "Use exactly the planned supported task keywords."))
        gates.append(gate("task-keyword", task_ok, [] if task_ok else ["INPUT_TASK_MISMATCH"]))
        charge_ok = parsed["charge"] == plan.get("charge") and parsed["multiplicity"] == plan.get("multiplicity")
        electron_count = sum(parsed["atomic_numbers"]) - parsed["charge"]
        electron_spin_ok = electron_count > 0 and parsed["multiplicity"] <= electron_count + 1 and (electron_count + parsed["multiplicity"]) % 2 == 1
        if not electron_spin_ok:
            charge_ok = False
            findings.append(finding("INPUT_ELECTRON_MULTIPLICITY_INVALID", "Charge and multiplicity conflict with the explicit nuclear charges.", "Correct charge, multiplicity, or element identity before execution."))
        if not charge_ok:
            findings.append(finding("INPUT_CHARGE_MULTIPLICITY_MISMATCH", "Charge or multiplicity differs from the plan.", "Resolve the plan/input identity before execution."))
        gates.append(gate("charge-multiplicity", charge_ok, [] if charge_ok else ["INPUT_CHARGE_MULTIPLICITY_MISMATCH"]))
        atom_ok = parsed["atom_count"] == plan.get("atom_count")
        if not atom_ok:
            findings.append(finding("INPUT_ATOM_COUNT_MISMATCH", "Parsed Cartesian atom count differs from the plan.", "Provide the planned Cartesian structure or a separately profiled geometry source."))
        gates.append(gate("atom-count", atom_ok, [] if atom_ok else ["INPUT_ATOM_COUNT_MISMATCH"]))
        link0 = parsed["link0"]
        expected = plan.get("expected_checkpoint")
        observed_chk = link0.get("chk")
        checkpoint_ok = observed_chk == expected and (observed_chk is None or _safe_label(observed_chk, checkpoint=True))
        if not checkpoint_ok:
            findings.append(finding("INPUT_CHECKPOINT_MISMATCH", "Checkpoint label is unsafe or differs from the plan.", "Use the exact planned portable checkpoint basename."))
        gates.append(gate("checkpoint-output", checkpoint_ok, [] if checkpoint_ok else ["INPUT_CHECKPOINT_MISMATCH"]))
        oldchk = link0.get("oldchk")
        route_lower = route.lower()
        parent_required = oldchk is not None or any(
            marker in route_lower.replace(" ", "")
            for marker in ("geom=check", "guess=read", "chkbasis", "readfc")
        )
        parent = plan.get("parent_checkpoint_ref")
        checkpoint_read_label = oldchk if oldchk is not None else observed_chk
        parent_ok = not parent_required or (
            isinstance(parent, dict)
            and _safe_label(parent.get("source_label"), checkpoint=True)
            and isinstance(parent.get("sha256"), str)
            and SHA256.fullmatch(parent["sha256"]) is not None
            and checkpoint_read_label == parent.get("source_label")
        )
        if parent_required and not parent_ok:
            findings.append(finding("INPUT_PARENT_LINEAGE_MISSING", "Checkpoint-reading input lacks a matching hash-bound parent.", "Provide the exact parent checkpoint safe label and SHA-256 in the plan."))
        if not parent_required and parent is not None:
            parent_ok = False
            findings.append(finding("INPUT_PARENT_LINEAGE_UNEXPECTED", "Plan supplies a parent checkpoint that the input does not read.", "Remove the stale parent reference or bind an explicit checkpoint-reading route."))
        gates.append(gate("parent-lineage", parent_ok, [] if parent_ok else [item["code"] for item in findings if item["code"].startswith("INPUT_PARENT_LINEAGE_")]))
    else:
        gates.extend(
            gate(identifier, False, ["INPUT_PARSE_BLOCKED"])
            for identifier in ("route-model-chemistry", "task-keyword", "charge-multiplicity", "atom-count", "checkpoint-output", "parent-lineage")
        )
    passed = not findings
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_name": "gaussian-candidate-audit",
        "command": "audit-input",
        "candidate_lifecycle": "development",
        "status": "pass" if passed else "blocked",
        "action_state": "local_gate_passed_limited" if passed else "local_gate_blocked",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": "input_gates_only" if passed else "no_positive_claim",
        "gates": gates,
        "findings": findings,
        "smallest_next_action": findings[0]["next_action"] if findings else "Obtain external licensed execution authorization for the exact audited input; this candidate cannot execute it.",
        "evidence": [
            {"role": "gaussian-input", "source_label": "input.gjf", "sha256": _sha256(raw), "bytes": len(raw)},
            {"role": "gaussian-plan", "source_label": "plan.json", "sha256": _sha256(plan_raw), "bytes": len(plan_raw)},
        ],
        "observations": None if parsed is None else {
            "atom_count": parsed["atom_count"],
            "charge": parsed["charge"],
            "multiplicity": parsed["multiplicity"],
            "has_checkpoint_output": "chk" in parsed["link0"],
            "has_checkpoint_parent": "oldchk" in parsed["link0"],
        },
        "limitations": [
            "The parser covers only the documented conservative subset.",
            "The structure-manifest hash is not resolved or semantically compared with the Cartesian input by this development Skill.",
            "No licensed execution, checkpoint content, numerical convergence, method adequacy, or scientific acceptance is established.",
        ],
    }


def _output_revisions(text: str) -> list[str]:
    result: list[str] = []
    for pattern in VERSION_PATTERNS:
        result.extend(f"G16 {match.group(1).upper()}" for match in pattern.finditer(text))
    return result


def _frequencies(text: str) -> list[float]:
    values: list[float] = []
    for line in text.splitlines():
        if "Frequencies --" not in line:
            continue
        tail = line.split("Frequencies --", 1)[1]
        for token in FLOAT.findall(tail):
            try:
                value = float(token.replace("D", "E").replace("d", "e"))
            except ValueError:
                continue
            if math.isfinite(value):
                values.append(value)
    return values


def validate_execution_record(
    value: dict[str, Any] | None,
    input_raw: bytes,
    output_raw: bytes,
    plan: dict[str, Any],
    plan_raw: bytes,
) -> list[dict[str, str]]:
    """Validate a narrow external record shape without authenticating its issuer."""

    if value is None:
        return [finding(
            "EXECUTION_RECORD_MISSING",
            "No external execution record binds the input and output bytes.",
            "Provide a trusted execution record for the exact input, output, environment, authorization, and checkpoint identity.",
        )]
    required = {
        "schema_version",
        "record_type",
        "issuer",
        "gaussian_revision",
        "environment_attestation_sha256",
        "authorization_decision_sha256",
        "plan_sha256",
        "input_sha256",
        "output_sha256",
        "exit_code",
        "status",
        "checkpoint_output",
    }
    findings: list[dict[str, str]] = []
    if set(value) != required:
        findings.append(finding("EXECUTION_RECORD_FIELDS_INVALID", "Execution-record fields are missing or unsupported.", "Regenerate the record with the exact documented fields."))
        return findings
    if value.get("schema_version") != SCHEMA_VERSION or value.get("record_type") != "gaussian-execution-record":
        findings.append(finding("EXECUTION_RECORD_IDENTITY_INVALID", "Execution-record schema or type is invalid.", "Use the candidate schema and gaussian-execution-record type."))
    if not _safe_label(value.get("issuer")):
        findings.append(finding("EXECUTION_RECORD_ISSUER_INVALID", "Execution-record issuer is missing or unsafe.", "Use a safe external issuer identifier."))
    if value.get("gaussian_revision") != plan.get("gaussian_revision"):
        findings.append(finding("EXECUTION_RECORD_REVISION_MISMATCH", "Execution-record revision differs from the plan.", "Bind the record to the exact planned Gaussian revision."))
    if value.get("plan_sha256") != _sha256(plan_raw):
        findings.append(finding("EXECUTION_RECORD_PLAN_BINDING_MISMATCH", "Execution record does not bind the exact plan-report bytes.", "Regenerate the execution record against the exact immutable plan report."))
    if not isinstance(value.get("environment_attestation_sha256"), str) or SHA256.fullmatch(value["environment_attestation_sha256"]) is None or not isinstance(value.get("authorization_decision_sha256"), str) or SHA256.fullmatch(value["authorization_decision_sha256"]) is None:
        findings.append(finding("EXECUTION_RECORD_TRUST_REFS_INVALID", "Environment or authorization evidence hash is missing.", "Bind exact external environment and authorization records."))
    if value.get("input_sha256") != _sha256(input_raw) or value.get("output_sha256") != _sha256(output_raw):
        findings.append(finding("EXECUTION_RECORD_BYTE_BINDING_MISMATCH", "Execution record does not bind the exact input and output bytes.", "Regenerate the record from the exact executed input and captured output bytes."))
    if not _integer(value.get("exit_code")) or value.get("exit_code") != 0 or value.get("status") != "completed":
        findings.append(finding("EXECUTION_RECORD_COMPLETION_INVALID", "Execution record does not declare a zero-exit completed action.", "Preserve and diagnose the failed external action before any retry."))
    expected_checkpoint = plan.get("expected_checkpoint")
    checkpoint = value.get("checkpoint_output")
    if expected_checkpoint is None:
        checkpoint_ok = checkpoint is None
    else:
        checkpoint_ok = (
            isinstance(checkpoint, dict)
            and set(checkpoint) == {"source_label", "sha256", "bytes"}
            and checkpoint.get("source_label") == expected_checkpoint
            and isinstance(checkpoint.get("sha256"), str)
            and SHA256.fullmatch(checkpoint["sha256"]) is not None
            and _integer(checkpoint.get("bytes"))
            and checkpoint["bytes"] > 0
        )
    if not checkpoint_ok:
        findings.append(finding("EXECUTION_RECORD_CHECKPOINT_MISMATCH", "Execution record does not bind the planned checkpoint output.", "Bind the planned checkpoint safe label, exact SHA-256, and positive byte count."))
    role_hashes = [
        value.get("environment_attestation_sha256"),
        value.get("authorization_decision_sha256"),
        value.get("plan_sha256"),
        value.get("input_sha256"),
        value.get("output_sha256"),
    ]
    if isinstance(checkpoint, dict):
        role_hashes.append(checkpoint.get("sha256"))
    valid_role_hashes = [item for item in role_hashes if isinstance(item, str) and SHA256.fullmatch(item)]
    if len(valid_role_hashes) != len(set(valid_role_hashes)):
        findings.append(finding("EXECUTION_RECORD_ROLE_HASH_COLLISION", "One hash is reused for distinct execution-evidence roles.", "Bind distinct environment, authorization, plan, input, output, and checkpoint artifacts."))
    return findings


def audit_run_data(
    input_text: str,
    input_raw: bytes,
    output_text: str,
    output_raw: bytes,
    plan_record: dict[str, Any],
    plan_raw: bytes,
    execution_record: dict[str, Any] | None = None,
    execution_raw: bytes | None = None,
) -> dict[str, Any]:
    input_report = audit_input_data(input_text, input_raw, plan_record, plan_raw)
    findings = list(input_report["findings"])
    gates = list(input_report["gates"])
    plan = plan_record.get("plan") if isinstance(plan_record.get("plan"), dict) else {}
    gates.append(gate("output-identity", True))
    execution_findings = validate_execution_record(execution_record, input_raw, output_raw, plan, plan_raw)
    findings.extend(execution_findings)
    gates.append(gate("execution-record-binding", not execution_findings, [item["code"] for item in execution_findings]))
    revisions = _output_revisions(output_text)
    revision = revisions[0] if len(revisions) == 1 else None
    revision_ok = revisions == [plan.get("gaussian_revision")]
    if not revision_ok:
        findings.append(finding("OUTPUT_REVISION_MISMATCH", "Output revision is missing or differs from the plan.", "Use a hash-bound output from the exact planned registered revision."))
    gates.append(gate("revision-match", revision_ok, [] if revision_ok else ["OUTPUT_REVISION_MISMATCH"]))
    error_count = len(re.findall(r"Error\s+termination", output_text, re.IGNORECASE))
    normal_count = len(re.findall(r"Normal\s+termination\s+of\s+Gaussian\s+16", output_text, re.IGNORECASE))
    last_nonempty = next((line.strip() for line in reversed(output_text.splitlines()) if line.strip()), "")
    termination_is_last = re.fullmatch(r"Normal\s+termination\s+of\s+Gaussian\s+16", last_nonempty, re.IGNORECASE) is not None
    completion_ok = error_count == 0 and normal_count == 1 and termination_is_last
    if not completion_ok:
        findings.append(finding("OUTPUT_TERMINATION_INVALID", "Output has an error, missing, or ambiguous termination sentinel.", "Provide one complete single-job output with exactly one normal and no error termination."))
    gates.append(gate("normal-termination", completion_ok, [] if completion_ok else ["OUTPUT_TERMINATION_INVALID"]))
    energies: list[float] = []
    for match in SCF_ENERGY.finditer(output_text):
        try:
            value = float(match.group(1).replace("D", "E").replace("d", "e"))
        except ValueError:
            continue
        if math.isfinite(value):
            energies.append(value)
    energy_ok = bool(energies)
    if not energy_ok:
        findings.append(finding("OUTPUT_SCF_ENERGY_MISSING", "No supported final SCF-energy sentinel was parsed.", "Provide a complete supported output or add a reviewed method-specific energy parser."))
    gates.append(gate("scf-energy-present", energy_ok, [] if energy_ok else ["OUTPUT_SCF_ENERGY_MISSING"]))
    scf_failure_count = len(re.findall(
        r"(?:Convergence\s+failure|SCF\s+(?:has\s+)?(?:not\s+converged|failed\s+to\s+converge)|No\s+convergence)",
        output_text,
        re.IGNORECASE,
    ))
    scf_convergence_ok = scf_failure_count == 0
    if not scf_convergence_ok:
        findings.append(finding("OUTPUT_SCF_CONVERGENCE_FAILURE", "Output contains a supported SCF non-convergence sentinel.", "Preserve the failed output and diagnose SCF stability/convergence under a new authorized action."))
    gates.append(gate("scf-no-known-failure", scf_convergence_ok, [] if scf_convergence_ok else ["OUTPUT_SCF_CONVERGENCE_FAILURE"]))
    task = plan.get("task")
    optimization_required = task in {"optimization", "optimization_frequency"}
    optimization_completed = re.search(r"Optimization\s+completed\s*\.", output_text, re.IGNORECASE) is not None
    optimization_ok = not optimization_required or optimization_completed
    if not optimization_ok:
        findings.append(finding("OUTPUT_OPTIMIZATION_INCOMPLETE", "Requested optimization completion sentinel is missing.", "Continue or repair the optimization under the same bound plan before frequency or structural claims."))
    gates.append(gate("optimization-completed", optimization_ok, [] if optimization_ok else ["OUTPUT_OPTIMIZATION_INCOMPLETE"]))
    frequencies = _frequencies(output_text)
    frequency_required = task in {"frequency", "optimization_frequency"}
    frequencies_ok = not frequency_required or bool(frequencies)
    if not frequencies_ok:
        findings.append(finding("OUTPUT_FREQUENCIES_MISSING", "Requested frequency values were not parsed.", "Provide the complete bound frequency output or add a reviewed parser profile."))
    gates.append(gate("frequencies-present", frequencies_ok, [] if frequencies_ok else ["OUTPUT_FREQUENCIES_MISSING"]))
    imaginary_count = sum(1 for value in frequencies if value < 0.0)
    stationary = plan.get("stationary_point")
    stationary_ok = True
    if frequency_required and frequencies:
        expected_count = 0 if stationary == "minimum" else 1 if stationary == "transition_state" else None
        stationary_ok = expected_count is not None and imaginary_count == expected_count
        if not stationary_ok:
            findings.append(finding("OUTPUT_STATIONARY_POINT_MISMATCH", "Negative-frequency count differs from the planned stationary-point type.", "Re-examine the structure, mode, and task before making a stationary-point claim."))
    elif frequency_required:
        stationary_ok = False
    gates.append(gate("stationary-point-count", stationary_ok, [] if stationary_ok else ["OUTPUT_STATIONARY_POINT_MISMATCH"]))
    passed = not findings
    future_ceiling = "no_positive_claim"
    if passed:
        future_ceiling = "numerical_candidate_only" if frequency_required else "technical_run_gates_only"
    near_zero_count = sum(1 for value in frequencies if abs(value) < 20.0)
    limitations = [
        "The Skill remains in development, so the public claim ceiling is no_positive_claim.",
        "The external execution record is strict hash-bound metadata but its issuer, authorization, environment, and checkpoint bytes are not authenticated by this offline candidate.",
        "Normal termination and sentinels do not prove method adequacy, convergence, conformer identity, thermochemistry, or scientific acceptance.",
    ]
    if near_zero_count:
        limitations.append("One or more parsed frequencies have absolute magnitude below 20 cm^-1 and require expert interpretation.")
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_name": "gaussian-candidate-audit",
        "command": "audit-run",
        "candidate_lifecycle": "development",
        "status": "pass" if passed else "blocked",
        "action_state": "local_gate_passed_limited" if passed else "local_gate_blocked",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": future_ceiling,
        "gates": gates,
        "findings": findings,
        "smallest_next_action": findings[0]["next_action"] if findings else "Package the exact evidence for independent expert review; do not self-accept the calculation.",
        "evidence": [
            {"role": "gaussian-input", "source_label": "input.gjf", "sha256": _sha256(input_raw), "bytes": len(input_raw)},
            {"role": "gaussian-output", "source_label": "output.log", "sha256": _sha256(output_raw), "bytes": len(output_raw)},
            {"role": "gaussian-plan", "source_label": "plan.json", "sha256": _sha256(plan_raw), "bytes": len(plan_raw)},
        ] + ([{"role": "execution-record", "source_label": "execution-record.json", "sha256": _sha256(execution_raw), "bytes": len(execution_raw)}] if execution_raw is not None else []),
        "observations": {
            "revision": revision,
            "revision_sentinel_count": len(revisions),
            "normal_termination_count": normal_count,
            "error_termination_count": error_count,
            "scf_energy_count": len(energies),
            "scf_failure_sentinel_count": scf_failure_count,
            "final_scf_energy_hartree": energies[-1] if energies else None,
            "optimization_completed": optimization_completed,
            "frequency_count": len(frequencies),
            "negative_frequency_count": imaginary_count,
            "near_zero_frequency_count": near_zero_count,
        },
        "limitations": limitations,
    }


def probe_environment(attestation: dict[str, Any], raw: bytes) -> dict[str, Any]:
    required = {
        "schema_version",
        "provider_id",
        "expected_identity",
        "platform",
        "architecture",
        "license_authorized",
        "supported_host",
        "issuer",
        "evidence_sha256",
    }
    findings: list[dict[str, str]] = []
    if set(attestation) != required:
        findings.append(finding("ENV_ATTESTATION_FIELDS_INVALID", "Environment attestation fields are missing or unsupported.", "Use the exact documented attestation fields."))
    else:
        if attestation.get("schema_version") != SCHEMA_VERSION:
            findings.append(finding("ENV_ATTESTATION_VERSION_INVALID", "Attestation version is unsupported.", f"Use {SCHEMA_VERSION}."))
        if attestation.get("provider_id") != "gaussian-g16-c02" or attestation.get("expected_identity") != "Gaussian 16 Rev C.02 Apple M-Series":
            findings.append(finding("ENV_PROVIDER_IDENTITY_MISMATCH", "Provider identity differs from the registered profile.", "Obtain a trusted attestation for the exact registered provider."))
        if attestation.get("platform") != "macos" or attestation.get("architecture") != "arm64":
            findings.append(finding("ENV_PLATFORM_UNSUPPORTED", "Platform or architecture differs from the candidate profile.", "Add a separately reviewed provider profile or use the registered target."))
        if attestation.get("license_authorized") is not True:
            findings.append(finding("ENV_LICENSE_AUTHORIZATION_MISSING", "License authorization is not attested.", "Obtain external license authorization; do not self-attest it in model prose."))
        if attestation.get("supported_host") is not True:
            findings.append(finding("ENV_HOST_SUPPORT_MISSING", "Host support is not attested.", "Obtain version-matched supported-host evidence."))
        if not _safe_label(attestation.get("issuer")):
            findings.append(finding("ENV_ISSUER_INVALID", "Attestation issuer is missing or unsafe.", "Provide a safe external issuer ID."))
        if not isinstance(attestation.get("evidence_sha256"), str) or not SHA256.fullmatch(attestation["evidence_sha256"]):
            findings.append(finding("ENV_EVIDENCE_HASH_INVALID", "Attestation evidence hash is missing or invalid.", "Bind the external evidence with lowercase SHA-256."))
    passed = not findings
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_name": "gaussian-candidate-environment-probe",
        "command": "probe-environment",
        "candidate_lifecycle": "development",
        "status": "pass" if passed else "blocked",
        "action_state": "needs_authorization" if passed else "local_gate_blocked",
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": "documented_behavior_only" if passed else "no_positive_claim",
        "gates": [gate("environment-attestation-shape", passed, [item["code"] for item in findings])],
        "findings": findings,
        "smallest_next_action": findings[0]["next_action"] if findings else "Have the trusted platform authenticate this attestation and issue a separately scoped execution authorization.",
        "evidence": [{"role": "environment-attestation", "source_label": "attestation.json", "sha256": _sha256(raw), "bytes": len(raw)}],
        "limitations": [
            "This command validates document shape only; it cannot authenticate a license, issuer, binary, host, or authorization.",
            "It never searches for or executes Gaussian.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="Validate and freeze an explicit candidate plan.")
    plan.add_argument("--request", type=Path, required=True)
    plan.add_argument("--out", type=Path, required=True)
    audit_input = commands.add_parser("audit-input", help="Audit one Gaussian input against a plan.")
    audit_input.add_argument("--input", type=Path, required=True)
    audit_input.add_argument("--plan", type=Path, required=True)
    audit_input.add_argument("--out", type=Path, required=True)
    audit_run = commands.add_parser("audit-run", help="Audit one Gaussian input/output pair against a plan.")
    audit_run.add_argument("--input", type=Path, required=True)
    audit_run.add_argument("--output", type=Path, required=True)
    audit_run.add_argument("--plan", type=Path, required=True)
    audit_run.add_argument("--execution-record", type=Path, required=True)
    audit_run.add_argument("--out", type=Path, required=True)
    probe = commands.add_parser("probe-environment", help="Validate an external environment-attestation shape.")
    probe.add_argument("--attestation", type=Path, required=True)
    probe.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report: dict[str, Any]
    evidence_paths = {
        "plan": [args.request] if args.command == "plan" else [],
        "audit-input": [args.input, args.plan] if args.command == "audit-input" else [],
        "audit-run": [args.input, args.output, args.plan, args.execution_record] if args.command == "audit-run" else [],
        "probe-environment": [args.attestation] if args.command == "probe-environment" else [],
    }[args.command]
    try:
        ensure_output_is_distinct(args.out, evidence_paths)
    except BoundaryError as exc:
        sys.stderr.write(json.dumps({"status": "blocked", "finding_code": exc.code}, sort_keys=True) + "\n")
        return 2
    try:
        if args.command == "plan":
            request, raw = load_json(args.request, "REQUEST")
            report = make_plan(request, raw)
        elif args.command == "audit-input":
            plan_record, plan_raw = load_json(args.plan, "PLAN")
            input_text, input_raw = load_text(args.input, "INPUT")
            report = audit_input_data(input_text, input_raw, plan_record, plan_raw)
        elif args.command == "audit-run":
            plan_record, plan_raw = load_json(args.plan, "PLAN")
            execution_record, execution_raw = load_json(args.execution_record, "EXECUTION_RECORD")
            input_text, input_raw = load_text(args.input, "INPUT")
            output_text, output_raw = load_text(args.output, "OUTPUT")
            report = audit_run_data(input_text, input_raw, output_text, output_raw, plan_record, plan_raw, execution_record, execution_raw)
        else:
            attestation, raw = load_json(args.attestation, "ATTESTATION")
            report = probe_environment(attestation, raw)
    except BoundaryError as exc:
        report = _blocked_report(args.command, exc.code, exc.message)
    try:
        atomic_write_json(args.out, report)
    except BoundaryError as exc:
        sys.stderr.write(json.dumps({"status": "blocked", "finding_code": exc.code}, sort_keys=True) + "\n")
        return 2
    sys.stdout.write(json.dumps({"status": report["status"], "report": args.out.name}, sort_keys=True) + "\n")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
