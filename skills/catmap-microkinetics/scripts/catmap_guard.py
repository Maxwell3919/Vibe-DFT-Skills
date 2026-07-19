#!/usr/bin/env python3
"""Plan and audit a safe declarative CatMAP microkinetic evidence package."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import sys
from typing import Any, Callable


TOOL_VERSION = "1.2.0"
MAX_JSON_BYTES = 4 * 1024 * 1024
LINK_HAS_DIR_FD = os.link in os.supports_dir_fd
LINK_HAS_NOFOLLOW = os.link in os.supports_follow_symlinks
SHA256 = re.compile(r"^[a-f0-9]{64}$")
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:+*-]{0,95}$")
ELEMENT = re.compile(r"^[A-Z][a-z]?$|^X$")

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_BLOCKED = 3
EXIT_PARSE = 4
EXIT_FAILED = 5

SUPPORTED_VERSION = "0.4.1"
SUPPORTED_PROFILE = "catmap-v041"
NATIVE_FORBIDDEN_SUFFIXES = {".log", ".mkm", ".pickle", ".pkl", ".py"}
TASK_ARTIFACTS = {
    "network-audit": ("network",),
    "thermochemistry-audit": ("network", "thermochemistry"),
    "steady-state-audit": ("network", "thermochemistry", "result"),
    "sensitivity-audit": ("network", "thermochemistry", "result"),
    "uncertainty-audit": ("network", "thermochemistry", "result"),
    "microkinetic-package-audit": ("network", "thermochemistry", "result"),
}
TASK_BLOCKS = {
    "network-audit": (),
    "thermochemistry-audit": (),
    "steady-state-audit": ("steady_state", "data_partition", "rate_normalization"),
    "sensitivity-audit": ("steady_state", "data_partition", "rate_normalization", "sensitivity"),
    "uncertainty-audit": ("steady_state", "data_partition", "rate_normalization", "uncertainty"),
    "microkinetic-package-audit": (
        "steady_state",
        "data_partition",
        "rate_normalization",
        "sensitivity",
        "uncertainty",
    ),
}
ALLOWED_CLAIMS = {
    "coverage",
    "elementary-rates",
    "network-balance",
    "sensitivity-coefficients",
    "steady-state-solution",
    "thermochemistry-consistency",
    "uncertainty-intervals",
}
FORBIDDEN_CLAIMS = {
    "causal-descriptor",
    "experiment-agreement",
    "mechanism-identification",
    "predictive-catalyst-ranking",
    "rate-determining-step",
    "true-mechanism",
    "unique-steady-state",
}
TASK_CLAIMS = {
    "network-audit": {"network-balance"},
    "thermochemistry-audit": {"network-balance", "thermochemistry-consistency"},
    "steady-state-audit": {
        "network-balance",
        "thermochemistry-consistency",
        "steady-state-solution",
        "coverage",
        "elementary-rates",
    },
    "sensitivity-audit": {
        "network-balance",
        "thermochemistry-consistency",
        "steady-state-solution",
        "coverage",
        "elementary-rates",
        "sensitivity-coefficients",
    },
    "uncertainty-audit": {
        "network-balance",
        "thermochemistry-consistency",
        "steady-state-solution",
        "coverage",
        "elementary-rates",
        "uncertainty-intervals",
    },
    "microkinetic-package-audit": set(ALLOWED_CLAIMS),
}
GATE_NAMES = (
    "provider",
    "safety",
    "lineage",
    "network",
    "units",
    "thermochemistry",
    "solver",
    "coverage",
    "rate",
    "sensitivity",
    "uncertainty",
    "data_partition",
    "task",
    "claim",
)
SENSITIVE_KEYS = {
    "account",
    "api_key",
    "credential",
    "hostname",
    "password",
    "private_key",
    "remote_path",
    "scheduler_job_id",
    "secret",
    "token",
    "username",
}


class GuardError(Exception):
    """Expected validation failure with stable code and redacted message."""

    def __init__(self, code: str, message: str, exit_code: int = EXIT_INPUT):
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")


def _object_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        value.st_nlink,
    )


class InputTracker:
    """Process-local input identities used only to prevent output aliasing."""

    def __init__(self) -> None:
        self._entries: list[tuple[Path, Path, int, int]] = []
        self._roots: dict[Path, tuple[int, int, int | None]] = {}

    def bind_root(self, path: Path, metadata: os.stat_result, descriptor: int | None = None) -> None:
        lexical = path.absolute()
        identity = (metadata.st_dev, metadata.st_ino)
        previous = self._roots.get(lexical)
        if previous is not None and previous[:2] != identity:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input root identity changed during the audit.")
        retained = previous[2] if previous is not None else None
        if retained is None and descriptor is not None:
            retained = os.dup(descriptor)
        self._roots[lexical] = (*identity, retained)

    def acquire_root(self, path: Path) -> int | None:
        entry = self._roots.get(path.absolute())
        return os.dup(entry[2]) if entry is not None and entry[2] is not None else None

    def close(self) -> None:
        for _device, _inode, descriptor in self._roots.values():
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        self._roots.clear()

    def record(
        self,
        path: Path,
        metadata: os.stat_result,
        *,
        root_path: Path | None = None,
        root_metadata: os.stat_result | None = None,
        root_descriptor: int | None = None,
    ) -> None:
        if root_path is not None and root_metadata is not None:
            self.bind_root(root_path, root_metadata, root_descriptor)
        lexical = path.absolute()
        try:
            resolved = path.resolve(strict=True)
        except OSError:
            resolved = lexical
        entry = (lexical, resolved, metadata.st_dev, metadata.st_ino)
        if entry not in self._entries:
            self._entries.append(entry)

    def conflicts(self, path: Path, metadata: os.stat_result | None = None) -> bool:
        lexical = path.absolute()
        try:
            resolved = path.resolve(strict=False)
        except OSError:
            resolved = lexical
        for input_lexical, input_resolved, device, inode in self._entries:
            if {lexical, resolved} & {input_lexical, input_resolved}:
                return True
            if metadata is not None and (metadata.st_dev, metadata.st_ino) == (device, inode):
                return True
        return False


def _validated_regular_read(
    descriptor: int,
    path: Path,
    final_metadata: Callable[[], os.stat_result],
    tracker: InputTracker | None,
    *,
    root_path: Path,
    root_metadata: os.stat_result,
    root_descriptor: int | None = None,
) -> bytes:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise GuardError(
            "CAT.INPUT.CONTRACT_INVALID",
            "Inputs must be single-link regular files, not aliases, links, or special files.",
        )
    if before.st_size > MAX_JSON_BYTES:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input exceeds the bounded size limit.")
    chunks: list[bytes] = []
    total = 0
    while True:
        try:
            chunk = os.read(descriptor, min(1024 * 1024, MAX_JSON_BYTES + 1 - total))
        except InterruptedError:
            continue
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > MAX_JSON_BYTES:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input exceeds the bounded size limit.")
    after = os.fstat(descriptor)
    try:
        final = final_metadata()
        lexical_final = path.lstat()
    except OSError as exc:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input path changed while it was being read.") from exc
    if (
        not stat.S_ISREG(after.st_mode)
        or not stat.S_ISREG(final.st_mode)
        or not stat.S_ISREG(lexical_final.st_mode)
        or after.st_nlink != 1
        or final.st_nlink != 1
        or lexical_final.st_nlink != 1
        or stat_identity(before) != stat_identity(after)
        or stat_identity(after) != stat_identity(final)
        or stat_identity(final) != stat_identity(lexical_final)
        or total != before.st_size
    ):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input identity changed while it was being read.")
    if tracker is not None:
        tracker.record(
            path,
            after,
            root_path=root_path,
            root_metadata=root_metadata,
            root_descriptor=root_descriptor,
        )
    return b"".join(chunks)


def read_regular_bytes(
    path: Path,
    tracker: InputTracker | None = None,
    *,
    retain_parent: bool = False,
) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory_flag is None or nonblock is None:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "This host lacks required no-follow input support.")
    path = path.absolute()
    parent = path.parent
    parent_fd: int | None = None
    descriptor: int | None = None
    try:
        parent_path_metadata = parent.lstat()
        if stat.S_ISLNK(parent_path_metadata.st_mode) or not stat.S_ISDIR(parent_path_metadata.st_mode):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input parent is unavailable or unsafe.")
        parent_fd = os.open(
            parent,
            os.O_RDONLY | directory_flag | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
        )
        parent_metadata = os.fstat(parent_fd)
        if (
            not stat.S_ISDIR(parent_metadata.st_mode)
            or (parent_metadata.st_dev, parent_metadata.st_ino)
            != (parent_path_metadata.st_dev, parent_path_metadata.st_ino)
        ):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input parent identity is unstable.")
        descriptor = os.open(
            path.name,
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
    except FileNotFoundError as exc:
        raise GuardError("CAT.TASK.EVIDENCE_MISSING", "A declared input is unavailable.", EXIT_FAILED) from exc
    except GuardError:
        raise
    except OSError as exc:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input could not be opened without following aliases.") from exc
    try:
        assert descriptor is not None and parent_fd is not None
        data = _validated_regular_read(
            descriptor,
            path,
            lambda: os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False),
            tracker,
            root_path=parent,
            root_metadata=parent_metadata,
            root_descriptor=parent_fd if retain_parent else None,
        )
        final_parent = parent.lstat()
        if (
            stat.S_ISLNK(final_parent.st_mode)
            or not stat.S_ISDIR(final_parent.st_mode)
            or (final_parent.st_dev, final_parent.st_ino) != (parent_metadata.st_dev, parent_metadata.st_ino)
        ):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input parent changed while it was being read.")
        return data
    except OSError as exc:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An input could not be read safely.") from exc
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if parent_fd is not None:
            try:
                os.close(parent_fd)
            except OSError:
                pass


def load_json_object(
    path: Path,
    tracker: InputTracker | None = None,
    *,
    artifact: bool = False,
    retain_parent: bool = False,
) -> tuple[dict[str, Any], bytes]:
    if path.suffix.casefold() in NATIVE_FORBIDDEN_SUFFIXES:
        raise GuardError("CAT.INPUT.NATIVE_FORMAT_FORBIDDEN", "Native executable or pickle-oriented input is forbidden.")
    raw = read_regular_bytes(path, tracker, retain_parent=retain_parent)
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise GuardError(
            "CAT.PARSER.ARTIFACT_UNSUPPORTED" if artifact else "CAT.INPUT.CONTRACT_INVALID",
            "JSON input is malformed, duplicated, non-finite, or not UTF-8.",
            EXIT_PARSE if artifact else EXIT_INPUT,
        ) from exc
    if not isinstance(value, dict):
        raise GuardError(
            "CAT.PARSER.ARTIFACT_UNSUPPORTED" if artifact else "CAT.INPUT.CONTRACT_INVALID",
            "JSON input must be an object.",
            EXIT_PARSE if artifact else EXIT_INPUT,
        )
    return value, raw


def is_safe_relative_json(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or len(value) > 160:
        return False
    path = PurePosixPath(value)
    return (
        path.suffix.casefold() == ".json"
        and not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def read_relative_regular_bytes(
    base: Path,
    value: Any,
    tracker: InputTracker | None = None,
) -> bytes:
    """Read declarative JSON through a stable root and no-follow openat traversal."""
    if not is_safe_relative_json(value):
        suffix = PurePosixPath(value).suffix.casefold() if isinstance(value, str) else ""
        if suffix in NATIVE_FORBIDDEN_SUFFIXES:
            raise GuardError("CAT.INPUT.NATIVE_FORMAT_FORBIDDEN", "Native CatMAP or Python-oriented input is forbidden.")
        raise GuardError("CAT.INPUT.PRIVACY_VIOLATION", "A declared artifact label is unsafe or not JSON.")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory_flag is None or nonblock is None:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "This host lacks required no-follow input support.")
    base = base.absolute()
    relative = PurePosixPath(value)
    path = base.joinpath(*relative.parts)
    directory_fds: list[int] = []
    directory_edges: list[tuple[int, str, int, os.stat_result]] = []
    descriptor: int | None = None
    try:
        root_path_metadata = base.lstat()
        if stat.S_ISLNK(root_path_metadata.st_mode) or not stat.S_ISDIR(root_path_metadata.st_mode):
            raise GuardError("CAT.INPUT.PRIVACY_VIOLATION", "The declared input root is an unsafe alias.")
        root_fd = tracker.acquire_root(base) if tracker is not None else None
        if root_fd is None:
            root_fd = os.open(
                base,
                os.O_RDONLY | directory_flag | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
            )
        directory_fds.append(root_fd)
        root_metadata = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(root_metadata.st_mode)
            or (root_metadata.st_dev, root_metadata.st_ino)
            != (root_path_metadata.st_dev, root_path_metadata.st_ino)
        ):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The declared input root identity is unstable.")
        if tracker is not None:
            tracker.bind_root(base, root_metadata)

        current_fd = root_fd
        for component in relative.parts[:-1]:
            component_metadata = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(component_metadata.st_mode) or not stat.S_ISDIR(component_metadata.st_mode):
                raise GuardError("CAT.INPUT.PRIVACY_VIOLATION", "A declared artifact parent is an unsafe alias.")
            child_fd = os.open(
                component,
                os.O_RDONLY | directory_flag | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
                dir_fd=current_fd,
            )
            child_metadata = os.fstat(child_fd)
            if (
                not stat.S_ISDIR(child_metadata.st_mode)
                or (child_metadata.st_dev, child_metadata.st_ino)
                != (component_metadata.st_dev, component_metadata.st_ino)
            ):
                os.close(child_fd)
                raise GuardError("CAT.INPUT.CONTRACT_INVALID", "A declared artifact parent identity is unstable.")
            directory_edges.append((current_fd, component, child_fd, child_metadata))
            directory_fds.append(child_fd)
            current_fd = child_fd

        descriptor = os.open(
            relative.parts[-1],
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
            dir_fd=current_fd,
        )
        data = _validated_regular_read(
            descriptor,
            path,
            lambda: os.stat(relative.parts[-1], dir_fd=current_fd, follow_symlinks=False),
            tracker,
            root_path=base,
            root_metadata=root_metadata,
        )
        for parent_fd, component, child_fd, child_metadata in directory_edges:
            anchored = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            open_metadata = os.fstat(child_fd)
            if (
                not stat.S_ISDIR(anchored.st_mode)
                or not stat.S_ISDIR(open_metadata.st_mode)
                or (anchored.st_dev, anchored.st_ino) != (child_metadata.st_dev, child_metadata.st_ino)
                or (open_metadata.st_dev, open_metadata.st_ino)
                != (child_metadata.st_dev, child_metadata.st_ino)
            ):
                raise GuardError("CAT.INPUT.CONTRACT_INVALID", "A declared artifact parent changed during the read.")
        final_root = base.lstat()
        if (
            stat.S_ISLNK(final_root.st_mode)
            or not stat.S_ISDIR(final_root.st_mode)
            or (final_root.st_dev, final_root.st_ino) != (root_metadata.st_dev, root_metadata.st_ino)
        ):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The declared input root changed during the read.")
        return data
    except FileNotFoundError as exc:
        raise GuardError("CAT.TASK.EVIDENCE_MISSING", "A declared input is unavailable.", EXIT_FAILED) from exc
    except GuardError:
        raise
    except OSError as exc:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "A declared input could not be opened or read safely.") from exc
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        for directory_fd in reversed(directory_fds):
            try:
                os.close(directory_fd)
            except OSError:
                pass


def load_relative_json_object(
    base: Path,
    value: Any,
    tracker: InputTracker | None = None,
    *,
    artifact: bool = False,
) -> tuple[dict[str, Any], bytes]:
    raw = read_relative_regular_bytes(base, value, tracker)
    try:
        result = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise GuardError(
            "CAT.PARSER.ARTIFACT_UNSUPPORTED" if artifact else "CAT.INPUT.CONTRACT_INVALID",
            "JSON input is malformed, duplicated, non-finite, or not UTF-8.",
            EXIT_PARSE if artifact else EXIT_INPUT,
        ) from exc
    if not isinstance(result, dict):
        raise GuardError(
            "CAT.PARSER.ARTIFACT_UNSUPPORTED" if artifact else "CAT.INPUT.CONTRACT_INVALID",
            "JSON input must be an object.",
            EXIT_PARSE if artifact else EXIT_INPUT,
        )
    return result, raw


def privacy_violations(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in SENSITIVE_KEYS:
                result.append(".".join((*path, str(key))))
            result.extend(privacy_violations(child, (*path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(privacy_violations(child, (*path, str(index))))
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("/", "~/", "ssh://", "scp://")) or WINDOWS_ABSOLUTE.match(stripped):
            result.append(".".join(path) or "value")
        if "-----BEGIN PRIVATE KEY-----" in value:
            result.append(".".join(path) or "value")
    return result


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} has missing or unknown fields.")


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} must be a nonempty string.")
    return value


def require_identifier(value: Any, label: str) -> str:
    text = require_string(value, label)
    if not IDENTIFIER.fullmatch(text):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} has an unsafe identifier.")
    return text


def require_sha256(value: Any, label: str) -> str:
    text = require_string(value, label)
    if not SHA256.fullmatch(text):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} must be a lowercase SHA-256 value.")
    return text


def require_number(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} must be a finite number.")
    number = float(value)
    if minimum is not None and number < minimum:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} is below its allowed minimum.")
    if maximum is not None and number > maximum:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} exceeds its allowed maximum.")
    return number


def require_positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} must be a positive integer.")
    return value


def require_nonnegative_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} must be a nonnegative integer.")
    return value


def require_string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} must be a list with the required cardinality.")
    result = [require_identifier(item, label) for item in value]
    if len(result) != len(set(result)):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", f"{label} contains duplicates.")
    return result


def finding(
    code: str,
    gate: str,
    severity: str,
    message: str,
    next_action: str,
    *,
    classification: str = "gate",
) -> dict[str, str]:
    return {
        "classification": classification,
        "code": code,
        "gate": gate,
        "message": message,
        "next_action": next_action,
        "severity": severity,
    }


def sorted_findings(value: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(value, key=lambda item: (item["code"], item["gate"], item["message"]))


def gate_projection(findings: list[dict[str, str]], evaluated: set[str]) -> dict[str, str]:
    result = {name: "not_evaluated" for name in GATE_NAMES}
    for name in evaluated:
        result[name] = "pass"
    for item in findings:
        if item["gate"] not in result:
            continue
        state = "blocked" if item["severity"] == "blocker" else "fail"
        if result[item["gate"]] != "fail":
            result[item["gate"]] = state
    return result


def determine_status(findings: list[dict[str, str]]) -> tuple[str, int]:
    if any(item["classification"] == "input" for item in findings):
        return "invalid_input", EXIT_INPUT
    if any(item["classification"] == "parse" for item in findings):
        return "parse_failed", EXIT_PARSE
    if any(item["severity"] == "error" for item in findings):
        return "failed", EXIT_FAILED
    if any(item["severity"] == "blocker" for item in findings):
        return "blocked_external_evidence", EXIT_BLOCKED
    return "passed", EXIT_OK


def invalid_report(error: GuardError, operation: str) -> dict[str, Any]:
    classification = "parse" if error.exit_code == EXIT_PARSE else "input"
    item = finding(
        error.code,
        "safety",
        "error",
        error.message,
        "Provide bounded declarative JSON and rerun without weakening a gate.",
        classification=classification,
    )
    status, _exit = determine_status([item])
    return {
        "contract_name": "catmap-candidate-validation-report",
        "schema_version": "1.0",
        "tool": {"name": "catmap_guard", "version": TOOL_VERSION},
        "operation": operation,
        "status": status,
        "maturity": "design-only",
        "maximum_claim": "no_positive_claim",
        "gates": gate_projection([item], {"safety"}),
        "findings": [item],
        "evidence": [],
        "metrics": {},
        "limitations": [
            "The Skill is in development and non-routable.",
            "No native CatMAP or Python-oriented artifact was executed.",
        ],
    }


def validate_thresholds(value: Any) -> dict[str, float | int]:
    if not isinstance(value, dict):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "thresholds must be an object.")
    expected = {
        "barrier_cycle_abs_tolerance_eV",
        "coverage_abs_tolerance",
        "energy_component_abs_tolerance_eV",
        "max_multistart_coverage_spread",
        "min_sensitivity_converged_fraction",
        "min_sensitivity_perturbation_count",
        "min_solver_initializations",
        "min_uncertainty_converged_fraction",
        "min_uncertainty_samples",
        "solver_residual_tolerance",
        "species_rate_residual_tolerance",
    }
    require_exact_keys(value, expected, "thresholds")
    return {
        "barrier_cycle_abs_tolerance_eV": require_number(
            value["barrier_cycle_abs_tolerance_eV"], "barrier tolerance", minimum=0.0
        ),
        "coverage_abs_tolerance": require_number(
            value["coverage_abs_tolerance"], "coverage tolerance", minimum=0.0
        ),
        "energy_component_abs_tolerance_eV": require_number(
            value["energy_component_abs_tolerance_eV"], "energy component tolerance", minimum=0.0
        ),
        "max_multistart_coverage_spread": require_number(
            value["max_multistart_coverage_spread"], "multi-start coverage spread", minimum=0.0
        ),
        "min_sensitivity_converged_fraction": require_number(
            value["min_sensitivity_converged_fraction"],
            "sensitivity convergence fraction",
            minimum=0.0,
            maximum=1.0,
        ),
        "min_sensitivity_perturbation_count": require_positive_integer(
            value["min_sensitivity_perturbation_count"], "minimum sensitivity perturbation count"
        ),
        "min_solver_initializations": require_positive_integer(
            value["min_solver_initializations"], "minimum solver initialization count"
        ),
        "min_uncertainty_converged_fraction": require_number(
            value["min_uncertainty_converged_fraction"],
            "uncertainty convergence fraction",
            minimum=0.0,
            maximum=1.0,
        ),
        "min_uncertainty_samples": require_positive_integer(
            value["min_uncertainty_samples"], "minimum uncertainty samples"
        ),
        "solver_residual_tolerance": require_number(
            value["solver_residual_tolerance"], "solver residual tolerance", minimum=0.0
        ),
        "species_rate_residual_tolerance": require_number(
            value["species_rate_residual_tolerance"], "species rate residual tolerance", minimum=0.0
        ),
    }


def validate_task_claims(task_value: Any, claims_value: Any) -> tuple[str, list[str]]:
    task = require_identifier(task_value, "task_id")
    if task not in TASK_ARTIFACTS:
        raise GuardError("CAT.TASK.UNSUPPORTED", "The requested CatMAP task has no candidate profile.", EXIT_BLOCKED)
    claims = require_string_list(claims_value, "requested claims")
    if set(claims) - ALLOWED_CLAIMS - FORBIDDEN_CLAIMS:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "A requested claim is unknown to the candidate contract.")
    incompatible = set(claims) - TASK_CLAIMS[task] - FORBIDDEN_CLAIMS
    if incompatible:
        raise GuardError(
            "CAT.TASK.CLAIM_UNSUPPORTED",
            "A requested technical claim is outside the selected task evidence profile.",
            EXIT_BLOCKED,
        )
    return task, claims


def make_plan(request: dict[str, Any]) -> dict[str, Any]:
    if privacy_violations(request):
        raise GuardError("CAT.INPUT.PRIVACY_VIOLATION", "The plan request contains a private path or sensitive field.")
    require_exact_keys(
        request,
        {
            "contract_name",
            "evidence_class",
            "provider_version",
            "requested_claims",
            "schema_version",
            "task_id",
            "thresholds",
        },
        "plan request",
    )
    if request["contract_name"] != "catmap-plan-request" or request["schema_version"] != "1.0":
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The plan contract identity is unsupported.")
    task, claims = validate_task_claims(request["task_id"], request["requested_claims"])
    thresholds = validate_thresholds(request["thresholds"])
    evidence_class = require_identifier(request["evidence_class"], "evidence_class")
    if evidence_class not in {"synthetic-fixture", "real-artifact"}:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "evidence_class is unsupported.")
    findings: list[dict[str, str]] = []
    evaluated = {"provider", "safety", "task", "claim"}
    if request["provider_version"] != SUPPORTED_VERSION:
        findings.append(
            finding(
                "CAT.PROVIDER.VERSION_UNSUPPORTED",
                "provider",
                "blocker",
                "Only the exact CatMAP v0.4.1 provider is pinned.",
                "Create a separate version and solver-default profile with forward evidence.",
            )
        )
    if set(claims) & FORBIDDEN_CLAIMS:
        findings.append(
            finding(
                "CAT.CLAIM.MECHANISM_AUTOMATION_FORBIDDEN",
                "claim",
                "blocker",
                "The plan asks automation to assert a mechanism, causal ranking, or experiment agreement.",
                "Restrict the plan to technical evidence and require independent scientific review.",
            )
        )
    status, _exit = determine_status(findings)
    return {
        "contract_name": "catmap-candidate-plan-report",
        "schema_version": "1.0",
        "tool": {"name": "catmap_guard", "version": TOOL_VERSION},
        "operation": "plan",
        "status": status,
        "maturity": "design-only",
        "maximum_claim": "no_positive_claim",
        "task_id": task,
        "provider": {
            "environment_profile_id": SUPPORTED_PROFILE,
            "software": "CatMAP",
            "version": request["provider_version"],
        },
        "required_artifacts": list(TASK_ARTIFACTS[task]),
        "required_blocks": list(TASK_BLOCKS[task]),
        "thresholds": thresholds,
        "requested_claims": claims,
        "gates": gate_projection(findings, evaluated),
        "findings": sorted_findings(findings),
        "steps": [
            "Establish exact v0.4.1 source, Python, dependency, and license evidence.",
            "Export trusted inputs to strict declarative JSON without loading untrusted native artifacts.",
            "Bind network, thermochemistry, and result bytes by SHA-256.",
            "Audit elemental/site balance, units, references, corrections, and barriers.",
            "Audit solver residual, coverages, site closure, and surface-species production residuals.",
            "Audit sensitivity and uncertainty evidence separately when selected.",
            "Prepare bounded evidence for expert review without automatic mechanism acceptance.",
        ],
        "limitations": [
            "A valid plan is not evidence of a CatMAP run or a true kinetic mechanism.",
            "The candidate has no external executor or native-file loader.",
        ],
    }


def validate_units(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "units must be an object.")
    require_exact_keys(value, {"coverage", "energy", "pressure", "rate", "temperature"}, "units")
    expected = {
        "coverage": "fraction_of_site",
        "energy": "eV",
        "pressure": "bar",
        "rate": "site^-1 s^-1",
        "temperature": "K",
    }
    for key, expected_value in expected.items():
        require_string(value[key], f"unit {key}")
        if value[key] != expected_value:
            raise GuardError("CAT.UNITS.UNSUPPORTED", "A unit or rate basis is unsupported.", EXIT_FAILED)
    return value


def validate_network(value: dict[str, Any]) -> dict[str, Any]:
    require_exact_keys(
        value,
        {
            "contract_name",
            "elements",
            "evidence_class",
            "network_id",
            "reactions",
            "schema_version",
            "sites",
            "species",
        },
        "network",
    )
    if value["contract_name"] != "reaction-network-candidate" or value["schema_version"] != "1.0":
        raise GuardError("CAT.PARSER.ARTIFACT_UNSUPPORTED", "The network contract identity is unsupported.", EXIT_PARSE)
    require_identifier(value["network_id"], "network_id")
    require_identifier(value["evidence_class"], "network evidence class")
    elements = require_string_list(value["elements"], "elements")
    if any(not ELEMENT.fullmatch(item) for item in elements):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "An element label is invalid.")

    sites_raw = value["sites"]
    if not isinstance(sites_raw, list) or not sites_raw:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "sites must be a nonempty list.")
    sites: dict[str, dict[str, Any]] = {}
    for item in sites_raw:
        if not isinstance(item, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "site entries must be objects.")
        require_exact_keys(item, {"capacity", "empty_species", "id"}, "site entry")
        site_id = require_identifier(item["id"], "site id")
        if site_id in sites:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "site identifiers are duplicated.")
        sites[site_id] = {
            "capacity": require_number(item["capacity"], "site capacity", minimum=0.0),
            "empty_species": require_identifier(item["empty_species"], "empty-site species"),
        }

    species_raw = value["species"]
    if not isinstance(species_raw, list) or not species_raw:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "species must be a nonempty list.")
    species: dict[str, dict[str, Any]] = {}
    for item in species_raw:
        if not isinstance(item, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "species entries must be objects.")
        require_exact_keys(item, {"composition", "id", "phase", "site_occupancy"}, "species entry")
        species_id = require_identifier(item["id"], "species id")
        if species_id in species:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "species identifiers are duplicated.")
        phase = require_identifier(item["phase"], "species phase")
        if phase not in {"adsorbate", "gas", "site"}:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "species phase is unsupported.")
        composition_raw = item["composition"]
        occupancy_raw = item["site_occupancy"]
        if not isinstance(composition_raw, dict) or not isinstance(occupancy_raw, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "species composition and occupancy must be objects.")
        composition: dict[str, int] = {}
        for element, count in composition_raw.items():
            if element not in elements or isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise GuardError("CAT.INPUT.CONTRACT_INVALID", "species composition is invalid.")
            if count:
                composition[element] = count
        occupancy: dict[str, float] = {}
        for site_id, count in occupancy_raw.items():
            if site_id not in sites:
                raise GuardError("CAT.INPUT.CONTRACT_INVALID", "species references an unknown site.")
            number = require_number(count, "site occupancy", minimum=0.0)
            if number:
                occupancy[site_id] = number
        if phase == "gas" and occupancy:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "gas species cannot occupy a surface site.")
        if phase in {"adsorbate", "site"} and not occupancy:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "surface species must declare site occupancy.")
        species[species_id] = {"composition": composition, "phase": phase, "site_occupancy": occupancy}
    for site_id, definition in sites.items():
        empty = definition["empty_species"]
        if empty not in species or species[empty]["phase"] != "site" or site_id not in species[empty]["site_occupancy"]:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "a site lacks a valid empty-site species.")

    reactions_raw = value["reactions"]
    if not isinstance(reactions_raw, list) or not reactions_raw:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "reactions must be a nonempty list.")
    reactions: dict[str, dict[str, Any]] = {}
    for item in reactions_raw:
        if not isinstance(item, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "reaction entries must be objects.")
        require_exact_keys(item, {"id", "reversible", "stoichiometry"}, "reaction entry")
        reaction_id = require_identifier(item["id"], "reaction id")
        if reaction_id in reactions or not isinstance(item["reversible"], bool):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "reaction identity or reversibility is invalid.")
        stoich_raw = item["stoichiometry"]
        if not isinstance(stoich_raw, dict) or len(stoich_raw) < 2:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "reaction stoichiometry is incomplete.")
        stoich: dict[str, int] = {}
        for species_id, coefficient in stoich_raw.items():
            if species_id not in species:
                raise GuardError("CAT.NETWORK.SPECIES_UNDEFINED", "A reaction references an undefined species.", EXIT_FAILED)
            if isinstance(coefficient, bool) or not isinstance(coefficient, int) or coefficient == 0:
                raise GuardError("CAT.INPUT.CONTRACT_INVALID", "Stoichiometric coefficients must be nonzero integers.")
            stoich[species_id] = coefficient
        if not any(value < 0 for value in stoich.values()) or not any(value > 0 for value in stoich.values()):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "A reaction must contain reactants and products.")
        reactions[reaction_id] = {"reversible": item["reversible"], "stoichiometry": stoich}

    return {
        "elements": elements,
        "evidence_class": value["evidence_class"],
        "network_id": value["network_id"],
        "reactions": reactions,
        "sites": sites,
        "species": species,
    }


def network_balance_findings(network: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    findings: list[dict[str, str]] = []
    metrics: dict[str, Any] = {"reaction_count": len(network["reactions"]), "species_count": len(network["species"])}
    maximum_element = 0.0
    maximum_site = 0.0
    for reaction in network["reactions"].values():
        stoich = reaction["stoichiometry"]
        for element in network["elements"]:
            balance = sum(
                coefficient * network["species"][species_id]["composition"].get(element, 0)
                for species_id, coefficient in stoich.items()
            )
            maximum_element = max(maximum_element, abs(float(balance)))
            if balance != 0:
                findings.append(
                    finding(
                        "CAT.NETWORK.ELEMENT_IMBALANCE",
                        "network",
                        "error",
                        "An elementary reaction violates elemental balance.",
                        "Correct the declarative reaction network before adding kinetics.",
                    )
                )
        for site_id in network["sites"]:
            balance = sum(
                coefficient * network["species"][species_id]["site_occupancy"].get(site_id, 0.0)
                for species_id, coefficient in stoich.items()
            )
            maximum_site = max(maximum_site, abs(balance))
            if abs(balance) > 1.0e-12:
                findings.append(
                    finding(
                        "CAT.NETWORK.SITE_IMBALANCE",
                        "network",
                        "error",
                        "An elementary reaction violates site balance.",
                        "Correct site occupancy and empty-site stoichiometry before solving.",
                    )
                )
    metrics["maximum_element_balance_error"] = maximum_element
    metrics["maximum_site_balance_error"] = maximum_site
    return findings, metrics


def validate_thermochemistry(value: dict[str, Any], network: dict[str, Any]) -> dict[str, Any]:
    require_exact_keys(
        value,
        {
            "barriers",
            "conditions",
            "contract_name",
            "corrections",
            "evidence_class",
            "network_sha256",
            "reference_state",
            "schema_version",
            "species_free_energies_eV",
            "thermochemistry_id",
            "units",
        },
        "thermochemistry",
    )
    if value["contract_name"] != "thermochemistry-dataset-candidate" or value["schema_version"] != "1.0":
        raise GuardError("CAT.PARSER.ARTIFACT_UNSUPPORTED", "The thermochemistry contract is unsupported.", EXIT_PARSE)
    require_identifier(value["thermochemistry_id"], "thermochemistry id")
    require_identifier(value["evidence_class"], "thermochemistry evidence class")
    require_sha256(value["network_sha256"], "thermochemistry network hash")
    validate_units(value["units"])

    reference = value["reference_state"]
    if not isinstance(reference, dict):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "reference_state must be an object.")
    require_exact_keys(reference, {"description", "energy_zero", "pressure_standard_bar"}, "reference_state")
    require_string(reference["description"], "reference description")
    require_string(reference["energy_zero"], "energy zero")
    require_number(reference["pressure_standard_bar"], "standard pressure", minimum=0.0)

    conditions = value["conditions"]
    if not isinstance(conditions, dict):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "conditions must be an object.")
    require_exact_keys(conditions, {"gas_pressures_bar", "temperature_K"}, "conditions")
    require_number(conditions["temperature_K"], "temperature", minimum=0.0)
    pressures = conditions["gas_pressures_bar"]
    gas_species = {key for key, item in network["species"].items() if item["phase"] == "gas"}
    if not isinstance(pressures, dict) or set(pressures) != gas_species:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "gas pressures must cover every gas species exactly.")
    for gas, pressure in pressures.items():
        require_number(pressure, f"pressure for {gas}", minimum=0.0)

    energies_raw = value["species_free_energies_eV"]
    if not isinstance(energies_raw, dict) or set(energies_raw) != set(network["species"]):
        raise GuardError("CAT.THERMO.ENERGY_MISSING", "Free energies do not cover every network species.", EXIT_FAILED)
    energies = {key: require_number(item, f"free energy for {key}") for key, item in energies_raw.items()}

    corrections_raw = value["corrections"]
    if not isinstance(corrections_raw, list) or len(corrections_raw) != len(network["species"]):
        raise GuardError("CAT.THERMO.PROVENANCE_MISSING", "Correction records must cover every species.", EXIT_FAILED)
    corrections: dict[str, dict[str, Any]] = {}
    for item in corrections_raw:
        if not isinstance(item, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "correction entries must be objects.")
        require_exact_keys(item, {"components_eV", "free_energy_eV", "provenance_id", "species_id"}, "correction")
        species_id = require_identifier(item["species_id"], "correction species")
        if species_id not in network["species"] or species_id in corrections:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "correction species is unknown or duplicated.")
        components = item["components_eV"]
        if not isinstance(components, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "correction components must be an object.")
        require_exact_keys(components, {"electronic", "enthalpy", "minus_t_s", "zero_point"}, "correction components")
        parsed_components = {key: require_number(component, f"correction component {key}") for key, component in components.items()}
        corrections[species_id] = {
            "components_eV": parsed_components,
            "free_energy_eV": require_number(item["free_energy_eV"], "correction free energy"),
            "provenance_id": require_identifier(item["provenance_id"], "correction provenance"),
        }
    if set(corrections) != set(network["species"]):
        raise GuardError("CAT.THERMO.PROVENANCE_MISSING", "Correction provenance does not cover the network.", EXIT_FAILED)

    barriers_raw = value["barriers"]
    if not isinstance(barriers_raw, list) or len(barriers_raw) != len(network["reactions"]):
        raise GuardError("CAT.THERMO.ENERGY_MISSING", "Barrier records must cover every reaction.", EXIT_FAILED)
    barriers: dict[str, dict[str, Any]] = {}
    for item in barriers_raw:
        if not isinstance(item, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "barrier entries must be objects.")
        require_exact_keys(
            item,
            {"forward_barrier_eV", "provenance_id", "reaction_id", "reverse_barrier_eV"},
            "barrier",
        )
        reaction_id = require_identifier(item["reaction_id"], "barrier reaction")
        if reaction_id not in network["reactions"] or reaction_id in barriers:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "barrier reaction is unknown or duplicated.")
        barriers[reaction_id] = {
            "forward_barrier_eV": require_number(item["forward_barrier_eV"], "forward barrier", minimum=0.0),
            "reverse_barrier_eV": require_number(item["reverse_barrier_eV"], "reverse barrier", minimum=0.0),
            "provenance_id": require_identifier(item["provenance_id"], "barrier provenance"),
        }
    return {
        "barriers": barriers,
        "corrections": corrections,
        "evidence_class": value["evidence_class"],
        "network_sha256": value["network_sha256"],
        "species_free_energies_eV": energies,
        "thermochemistry_id": value["thermochemistry_id"],
        "units": value["units"],
    }


def thermochemistry_findings(
    thermo: dict[str, Any],
    network: dict[str, Any],
    thresholds: dict[str, float | int],
) -> tuple[list[dict[str, str]], dict[str, float]]:
    findings: list[dict[str, str]] = []
    maximum_component_error = 0.0
    for species_id, correction in thermo["corrections"].items():
        calculated = sum(correction["components_eV"].values())
        error = max(
            abs(calculated - correction["free_energy_eV"]),
            abs(correction["free_energy_eV"] - thermo["species_free_energies_eV"][species_id]),
        )
        maximum_component_error = max(maximum_component_error, error)
        if error > float(thresholds["energy_component_abs_tolerance_eV"]):
            findings.append(
                finding(
                    "CAT.THERMO.ENERGY_MISSING",
                    "thermochemistry",
                    "error",
                    "A species free energy is inconsistent with its declared components.",
                    "Correct energy components and provenance before solving the network.",
                )
            )
    maximum_barrier_error = 0.0
    for reaction_id, reaction in network["reactions"].items():
        delta_g = sum(
            coefficient * thermo["species_free_energies_eV"][species_id]
            for species_id, coefficient in reaction["stoichiometry"].items()
        )
        barrier = thermo["barriers"][reaction_id]
        error = abs((barrier["forward_barrier_eV"] - barrier["reverse_barrier_eV"]) - delta_g)
        maximum_barrier_error = max(maximum_barrier_error, error)
        if error > float(thresholds["barrier_cycle_abs_tolerance_eV"]):
            findings.append(
                finding(
                    "CAT.THERMO.BARRIER_INCONSISTENT",
                    "thermochemistry",
                    "error",
                    "Forward/reverse barriers are inconsistent with the reaction free energy.",
                    "Resolve energy reference, stoichiometry, and barrier provenance before solving.",
                )
            )
    return findings, {
        "maximum_barrier_cycle_error_eV": maximum_barrier_error,
        "maximum_energy_component_error_eV": maximum_component_error,
    }


def validate_data_partition(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "data_partition must be an object.")
    require_exact_keys(
        value,
        {
            "calibration_data_ids",
            "declared_overlap_count",
            "evaluation_data_ids",
            "partition_sha256",
            "purpose",
        },
        "data partition",
    )
    calibration = require_string_list(value["calibration_data_ids"], "calibration data ids")
    evaluation = require_string_list(value["evaluation_data_ids"], "evaluation data ids")
    overlap_count = require_nonnegative_integer(value["declared_overlap_count"], "declared overlap count")
    purpose = require_identifier(value["purpose"], "data partition purpose")
    declared_hash = require_sha256(value["partition_sha256"], "data partition hash")
    canonical = json.dumps(
        {
            "calibration_data_ids": sorted(calibration),
            "evaluation_data_ids": sorted(evaluation),
            "purpose": purpose,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "calibration_data_ids": calibration,
        "computed_partition_sha256": sha256_bytes(canonical),
        "declared_overlap_count": overlap_count,
        "evaluation_data_ids": evaluation,
        "observed_overlap_count": len(set(calibration) & set(evaluation)),
        "partition_sha256": declared_hash,
        "purpose": purpose,
    }


def validate_rate_normalization(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "rate_normalization must be an object.")
    require_exact_keys(value, {"area_normalization", "basis", "site_id"}, "rate normalization")
    return {
        "area_normalization": require_identifier(value["area_normalization"], "area normalization"),
        "basis": require_identifier(value["basis"], "rate normalization basis"),
        "site_id": require_identifier(value["site_id"], "rate normalization site id"),
    }


def validate_result(value: dict[str, Any]) -> dict[str, Any]:
    require_exact_keys(
        value,
        {
            "contract_name",
            "data_partition",
            "evidence_class",
            "model_binding",
            "points",
            "provider",
            "rate_normalization",
            "result_id",
            "schema_version",
            "sensitivity",
            "solver",
            "uncertainty",
            "units",
        },
        "result",
    )
    if value["contract_name"] != "catmap-result-candidate" or value["schema_version"] != "1.0":
        raise GuardError("CAT.PARSER.ARTIFACT_UNSUPPORTED", "The result contract is unsupported.", EXIT_PARSE)
    require_identifier(value["result_id"], "result id")
    require_identifier(value["evidence_class"], "result evidence class")
    validate_units(value["units"])

    binding = value["model_binding"]
    if not isinstance(binding, dict):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "model_binding must be an object.")
    require_exact_keys(binding, {"network_sha256", "thermochemistry_sha256"}, "model_binding")
    require_sha256(binding["network_sha256"], "result network hash")
    require_sha256(binding["thermochemistry_sha256"], "result thermochemistry hash")

    provider = value["provider"]
    if not isinstance(provider, dict):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "result provider must be an object.")
    require_exact_keys(
        provider,
        {
            "dependency_lock_sha256",
            "environment_profile_id",
            "python_version",
            "software",
            "source_revision",
            "version",
        },
        "result provider",
    )
    require_sha256(provider["dependency_lock_sha256"], "dependency lock hash")
    for key in ("environment_profile_id", "python_version", "software", "source_revision", "version"):
        require_string(provider[key], f"provider {key}")

    solver = value["solver"]
    if not isinstance(solver, dict):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "solver must be an object.")
    require_exact_keys(
        solver,
        {
            "branch_identity",
            "converged",
            "initialization_trials",
            "iterations",
            "name",
            "residual_norm",
            "residual_tolerance",
            "settings_sha256",
        },
        "solver",
    )
    if not isinstance(solver["converged"], bool):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "solver converged must be boolean.")
    trials_raw = solver["initialization_trials"]
    if not isinstance(trials_raw, list) or not trials_raw:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "solver initialization trials must be nonempty.")
    trials: list[dict[str, Any]] = []
    initial_ids: set[str] = set()
    for trial in trials_raw:
        if not isinstance(trial, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "solver initialization trials must be objects.")
        require_exact_keys(
            trial,
            {
                "converged",
                "final_coverages",
                "initial_state_id",
                "point_id",
                "residual_norm",
                "solution_fingerprint",
            },
            "solver initialization trial",
        )
        initial_id = require_identifier(trial["initial_state_id"], "initial state id")
        if initial_id in initial_ids or not isinstance(trial["converged"], bool):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "initialization identity or convergence state is invalid.")
        initial_ids.add(initial_id)
        final_coverages = trial["final_coverages"]
        if not isinstance(final_coverages, dict) or not final_coverages:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "trial final coverages must be a nonempty object.")
        parsed_coverages = {
            require_identifier(key, "trial coverage species"): require_number(item, "trial coverage")
            for key, item in final_coverages.items()
        }
        trials.append(
            {
                "converged": trial["converged"],
                "final_coverages": parsed_coverages,
                "initial_state_id": initial_id,
                "point_id": require_identifier(trial["point_id"], "trial point id"),
                "residual_norm": require_number(trial["residual_norm"], "trial residual", minimum=0.0),
                "solution_fingerprint": require_sha256(
                    trial["solution_fingerprint"], "trial solution fingerprint"
                ),
            }
        )
    parsed_solver = {
        "branch_identity": require_identifier(solver["branch_identity"], "solver branch identity"),
        "converged": solver["converged"],
        "initialization_trials": trials,
        "iterations": require_positive_integer(solver["iterations"], "solver iterations"),
        "name": require_identifier(solver["name"], "solver name"),
        "residual_norm": require_number(solver["residual_norm"], "solver residual", minimum=0.0),
        "residual_tolerance": require_number(solver["residual_tolerance"], "solver tolerance", minimum=0.0),
        "settings_sha256": require_sha256(solver["settings_sha256"], "solver settings hash"),
    }
    if not isinstance(value["points"], list) or not value["points"]:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "result points must be a nonempty list.")
    return {
        "data_partition": validate_data_partition(value["data_partition"]),
        "evidence_class": value["evidence_class"],
        "model_binding": binding,
        "points": value["points"],
        "provider": provider,
        "rate_normalization": validate_rate_normalization(value["rate_normalization"]),
        "result_id": value["result_id"],
        "sensitivity": value["sensitivity"],
        "solver": parsed_solver,
        "uncertainty": value["uncertainty"],
        "units": value["units"],
    }


def audit_points(
    result: dict[str, Any],
    network: dict[str, Any],
    thresholds: dict[str, float | int],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    findings: list[dict[str, str]] = []
    maximum_site_error = 0.0
    maximum_species_residual = 0.0
    surface_species = {
        species_id for species_id, definition in network["species"].items() if definition["phase"] in {"adsorbate", "site"}
    }
    point_ids: set[str] = set()
    for point in result["points"]:
        if not isinstance(point, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "point entries must be objects.")
        require_exact_keys(
            point,
            {"coverages", "elementary_rates", "point_id", "surface_species_residuals"},
            "result point",
        )
        point_id = require_identifier(point["point_id"], "point id")
        if point_id in point_ids:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "point identifiers are duplicated.")
        point_ids.add(point_id)
        coverages = point["coverages"]
        rates = point["elementary_rates"]
        residuals = point["surface_species_residuals"]
        if not isinstance(coverages, dict) or set(coverages) != surface_species:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "coverages must cover every surface species exactly.")
        if not isinstance(rates, dict) or set(rates) != set(network["reactions"]):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "elementary rates must cover every reaction exactly.")
        if not isinstance(residuals, dict) or set(residuals) != surface_species:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "surface residuals must cover every surface species exactly.")
        parsed_coverages = {key: require_number(item, f"coverage {key}") for key, item in coverages.items()}
        parsed_rates = {key: require_number(item, f"rate {key}") for key, item in rates.items()}
        parsed_residuals = {key: require_number(item, f"surface residual {key}") for key, item in residuals.items()}
        tolerance = float(thresholds["coverage_abs_tolerance"])
        if any(item < -tolerance or item > 1.0 + tolerance for item in parsed_coverages.values()):
            findings.append(
                finding(
                    "CAT.COVERAGE.BOUNDS_FAILED",
                    "coverage",
                    "error",
                    "A surface coverage is outside its allowed fractional bounds.",
                    "Resolve solver branch, site model, and normalization before interpretation.",
                )
            )
        for site_id, site in network["sites"].items():
            total = sum(
                parsed_coverages[species_id] * network["species"][species_id]["site_occupancy"].get(site_id, 0.0)
                for species_id in surface_species
            )
            error = abs(total - site["capacity"])
            maximum_site_error = max(maximum_site_error, error)
            if error > tolerance:
                findings.append(
                    finding(
                        "CAT.COVERAGE.SITE_CLOSURE_FAILED",
                        "coverage",
                        "error",
                        "Surface coverages do not close to the declared site capacity.",
                        "Check empty-site coverage, multi-dentate occupancy, and site normalization.",
                    )
                )
        for species_id in surface_species:
            derived = sum(
                network["reactions"][reaction_id]["stoichiometry"].get(species_id, 0) * rate
                for reaction_id, rate in parsed_rates.items()
            )
            error = max(abs(derived), abs(derived - parsed_residuals[species_id]), abs(parsed_residuals[species_id]))
            maximum_species_residual = max(maximum_species_residual, error)
            if error > float(thresholds["species_rate_residual_tolerance"]):
                findings.append(
                    finding(
                        "CAT.RATE.SPECIES_RESIDUAL_FAILED",
                        "rate",
                        "error",
                        "A surface-species production residual exceeds the declared tolerance.",
                        "Resolve stoichiometry, rate mapping, and steady-state convergence.",
                    )
                )
    return findings, {
        "maximum_site_closure_error": maximum_site_error,
        "maximum_surface_species_rate_residual": maximum_species_residual,
        "point_count": len(result["points"]),
    }


def coverage_fingerprint(coverages: dict[str, float]) -> str:
    canonical = json.dumps(
        dict(sorted(coverages.items())),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256_bytes(canonical)


def audit_solver_initializations(
    result: dict[str, Any],
    network: dict[str, Any],
    thresholds: dict[str, float | int],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    surface_species = {
        species_id
        for species_id, definition in network["species"].items()
        if definition["phase"] in {"adsorbate", "site"}
    }
    points = {item["point_id"]: item["coverages"] for item in result["points"]}
    trials = result["solver"]["initialization_trials"]
    valid = True
    maximum_spread = 0.0
    maximum_point_difference = 0.0
    maximum_trial_residual = 0.0
    trials_by_point: dict[str, list[dict[str, Any]]] = {point_id: [] for point_id in points}
    for trial in trials:
        point_id = trial["point_id"]
        if point_id not in trials_by_point:
            valid = False
            continue
        trials_by_point[point_id].append(trial)
        coverages = trial["final_coverages"]
        maximum_trial_residual = max(maximum_trial_residual, trial["residual_norm"])
        if (
            set(coverages) != surface_species
            or not trial["converged"]
            or trial["residual_norm"] > float(thresholds["solver_residual_tolerance"])
            or trial["solution_fingerprint"] != coverage_fingerprint(coverages)
        ):
            valid = False
            continue
        if any(item < 0.0 or item > 1.0 for item in coverages.values()):
            valid = False
        for species_id in surface_species:
            maximum_point_difference = max(
                maximum_point_difference,
                abs(coverages[species_id] - points[point_id][species_id]),
            )

    minimum_trials = int(thresholds["min_solver_initializations"])
    spread_limit = float(thresholds["max_multistart_coverage_spread"])
    for point_trials in trials_by_point.values():
        if len(point_trials) < minimum_trials:
            valid = False
            continue
        for species_id in surface_species:
            values = [trial["final_coverages"].get(species_id) for trial in point_trials]
            if any(item is None for item in values):
                valid = False
                continue
            spread = max(values) - min(values)
            maximum_spread = max(maximum_spread, spread)
    if maximum_spread > spread_limit or maximum_point_difference > spread_limit:
        valid = False

    findings = [] if valid else [
        finding(
            "CAT.SOLVER.MULTISTART_INCONSISTENT",
            "solver",
            "error",
            "Independent initial-state trials are missing, unconverged, detached, or converge to inconsistent stored coverages.",
            "Run the predeclared initial-state set, retain each residual/final state, and preserve competing branches.",
        )
    ]
    return findings, {
        "initialization_trial_count": len(trials),
        "maximum_multistart_coverage_spread": maximum_spread,
        "maximum_multistart_point_difference": maximum_point_difference,
        "maximum_trial_residual": maximum_trial_residual,
        "point_count_with_trials": sum(bool(items) for items in trials_by_point.values()),
    }


def audit_data_partition(value: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    valid = (
        value["purpose"] == "calibration-evaluation-separation"
        and value["declared_overlap_count"] == 0
        and value["observed_overlap_count"] == 0
        and value["partition_sha256"] == value["computed_partition_sha256"]
    )
    findings = [] if valid else [
        finding(
            "CAT.DATA.PARTITION_LEAKAGE",
            "data_partition",
            "error",
            "Calibration/evaluation identities overlap, disagree with accounting, or are detached from their partition hash.",
            "Create disjoint immutable calibration and evaluation manifests before model assessment.",
        )
    ]
    return findings, {
        "calibration_count": len(value["calibration_data_ids"]),
        "evaluation_count": len(value["evaluation_data_ids"]),
        "observed_overlap_count": value["observed_overlap_count"],
        "partition_sha256": value["partition_sha256"],
    }


def audit_rate_normalization(
    value: dict[str, str], network: dict[str, Any]
) -> tuple[list[dict[str, str]], dict[str, str]]:
    valid = (
        value["basis"] == "per_declared_active_site"
        and value["area_normalization"] == "not-applied"
        and value["site_id"] in network["sites"]
    )
    findings = [] if valid else [
        finding(
            "CAT.RATE.NORMALIZATION_INVALID",
            "rate",
            "error",
            "The rate unit is detached from a supported declared active-site normalization.",
            "Bind every rate to one declared site population and state any area normalization explicitly.",
        )
    ]
    return findings, value


def audit_sensitivity(
    value: Any,
    thresholds: dict[str, float | int],
    expected_branch: str,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if not isinstance(value, dict):
        return [
            finding(
                "CAT.SENSITIVITY.EVIDENCE_INCOMPLETE",
                "sensitivity",
                "error",
                "Sensitivity evidence is absent.",
                "Provide the complete declared perturbation and convergence block.",
            )
        ], {}
    require_exact_keys(
        value,
        {
            "branch_identity",
            "coefficient_units",
            "coefficients",
            "converged_fraction",
            "method",
            "output_ids",
            "parameter_ids",
            "perturbations_eV",
        },
        "sensitivity",
    )
    method = require_identifier(value["method"], "sensitivity method")
    branch = require_identifier(value["branch_identity"], "sensitivity branch")
    units = require_identifier(value["coefficient_units"], "sensitivity coefficient units")
    parameters = require_string_list(value["parameter_ids"], "sensitivity parameters")
    outputs = require_string_list(value["output_ids"], "sensitivity outputs")
    perturbations_raw = value["perturbations_eV"]
    if not isinstance(perturbations_raw, list):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "sensitivity perturbations must be a list.")
    perturbations = [require_number(item, "sensitivity perturbation", minimum=0.0) for item in perturbations_raw]
    convergence = require_number(value["converged_fraction"], "sensitivity convergence", minimum=0.0, maximum=1.0)
    coefficients = value["coefficients"]
    valid_coefficients = isinstance(coefficients, dict) and set(coefficients) == set(parameters)
    if valid_coefficients:
        for parameter in parameters:
            row = coefficients[parameter]
            if not isinstance(row, dict) or set(row) != set(outputs):
                valid_coefficients = False
                break
            for coefficient in row.values():
                require_number(coefficient, "sensitivity coefficient")
    complete = (
        method == "central-finite-difference"
        and units == "dimensionless-log-derivative"
        and branch == expected_branch
        and len(perturbations) >= int(thresholds["min_sensitivity_perturbation_count"])
        and len(perturbations) == len(set(perturbations))
        and all(item > 0.0 for item in perturbations)
        and convergence >= float(thresholds["min_sensitivity_converged_fraction"])
        and valid_coefficients
    )
    findings = [] if complete else [
        finding(
            "CAT.SENSITIVITY.EVIDENCE_INCOMPLETE",
            "sensitivity",
            "error",
            "Sensitivity method, perturbations, convergence, selectors, or coefficients are incomplete.",
            "Provide at least two converged perturbation scales on one identified solver branch.",
        )
    ]
    return findings, {
        "converged_fraction": convergence,
        "output_count": len(outputs),
        "parameter_count": len(parameters),
        "perturbation_count": len(perturbations),
    }


def audit_uncertainty(
    value: Any,
    thresholds: dict[str, float | int],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if not isinstance(value, dict):
        return [
            finding(
                "CAT.UNCERTAINTY.EVIDENCE_INCOMPLETE",
                "uncertainty",
                "error",
                "Uncertainty evidence is absent.",
                "Provide distributions, sampling identity, sample accounting, and intervals.",
            )
        ], {}
    require_exact_keys(
        value,
        {
            "converged_samples",
            "correlation_model",
            "distribution_provenance_id",
            "method",
            "output_intervals",
            "parameter_ids",
            "requested_samples",
            "sampling_identity_sha256",
        },
        "uncertainty",
    )
    method = require_identifier(value["method"], "uncertainty method")
    correlation = require_identifier(value["correlation_model"], "uncertainty correlation model")
    provenance = require_identifier(value["distribution_provenance_id"], "distribution provenance")
    parameters = require_string_list(value["parameter_ids"], "uncertainty parameters")
    requested = require_positive_integer(value["requested_samples"], "requested uncertainty samples")
    converged = require_positive_integer(value["converged_samples"], "converged uncertainty samples")
    require_sha256(value["sampling_identity_sha256"], "uncertainty sampling identity")
    intervals = value["output_intervals"]
    intervals_valid = isinstance(intervals, dict) and bool(intervals)
    if intervals_valid:
        for output_id, interval in intervals.items():
            require_identifier(output_id, "uncertainty output id")
            if not isinstance(interval, dict):
                intervals_valid = False
                break
            require_exact_keys(interval, {"q05", "q50", "q95", "unit"}, "uncertainty interval")
            q05 = require_number(interval["q05"], "uncertainty q05")
            q50 = require_number(interval["q50"], "uncertainty q50")
            q95 = require_number(interval["q95"], "uncertainty q95")
            if interval["unit"] != "site^-1 s^-1" or not q05 <= q50 <= q95:
                intervals_valid = False
    fraction = converged / requested if converged <= requested else 0.0
    complete = (
        method in {"deterministic-grid", "seeded-ensemble"}
        and bool(correlation)
        and bool(provenance)
        and bool(parameters)
        and requested >= int(thresholds["min_uncertainty_samples"])
        and converged <= requested
        and fraction >= float(thresholds["min_uncertainty_converged_fraction"])
        and intervals_valid
    )
    findings = [] if complete else [
        finding(
            "CAT.UNCERTAINTY.EVIDENCE_INCOMPLETE",
            "uncertainty",
            "error",
            "Uncertainty distributions, sample accounting, convergence, or intervals are incomplete.",
            "Record parameter provenance/correlation and enough converged samples with ordered intervals.",
        )
    ]
    return findings, {
        "converged_fraction": fraction,
        "output_count": len(intervals) if isinstance(intervals, dict) else 0,
        "parameter_count": len(parameters),
        "requested_samples": requested,
    }


def validate_audit_request(request: dict[str, Any]) -> tuple[str, str, list[str], dict[str, float | int]]:
    if privacy_violations(request):
        raise GuardError("CAT.INPUT.PRIVACY_VIOLATION", "The audit request contains a private path or sensitive field.")
    require_exact_keys(
        request,
        {
            "artifacts",
            "contract_name",
            "evidence_class",
            "provider_version",
            "requested_claims",
            "schema_version",
            "task_id",
            "thresholds",
        },
        "audit request",
    )
    if request["contract_name"] != "catmap-audit-request" or request["schema_version"] != "1.0":
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The audit contract identity is unsupported.")
    task, claims = validate_task_claims(request["task_id"], request["requested_claims"])
    evidence_class = require_identifier(request["evidence_class"], "evidence_class")
    if evidence_class not in {"synthetic-fixture", "real-artifact"}:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "evidence_class is unsupported.")
    provider_version = require_string(request["provider_version"], "provider version")
    thresholds = validate_thresholds(request["thresholds"])
    return task, evidence_class, claims, thresholds


def validate_artifact_declarations(value: Any) -> dict[str, dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "artifacts must be a nonempty list.")
    result: dict[str, dict[str, str]] = {}
    for item in value:
        if not isinstance(item, dict):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "artifact entries must be objects.")
        require_exact_keys(item, {"file", "role", "sha256"}, "artifact entry")
        role = require_identifier(item["role"], "artifact role")
        if role not in {"network", "result", "thermochemistry"} or role in result:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "artifact role is unknown or duplicated.")
        if not is_safe_relative_json(item["file"]):
            suffix = PurePosixPath(item["file"]).suffix.casefold() if isinstance(item["file"], str) else ""
            if suffix in NATIVE_FORBIDDEN_SUFFIXES:
                raise GuardError("CAT.INPUT.NATIVE_FORMAT_FORBIDDEN", "Native CatMAP or Python-oriented input is forbidden.")
            raise GuardError("CAT.INPUT.PRIVACY_VIOLATION", "artifact file must be a safe relative JSON label.")
        result[role] = {"file": item["file"], "sha256": require_sha256(item["sha256"], "artifact hash")}
    return result


def audit_request(
    request: dict[str, Any],
    request_path: Path,
    tracker: InputTracker | None = None,
) -> tuple[dict[str, Any], int]:
    tracker = tracker if tracker is not None else InputTracker()
    task, evidence_class, claims, thresholds = validate_audit_request(request)
    artifacts = validate_artifact_declarations(request["artifacts"])
    findings: list[dict[str, str]] = []
    evaluated: set[str] = {"provider", "safety", "lineage", "task", "claim"}
    evidence: list[dict[str, str]] = []
    metrics: dict[str, Any] = {}
    if request["provider_version"] != SUPPORTED_VERSION:
        findings.append(
            finding(
                "CAT.PROVIDER.VERSION_UNSUPPORTED",
                "provider",
                "blocker",
                "The request is not pinned to CatMAP v0.4.1.",
                "Use the pinned provider or validate a separate exact-version profile.",
            )
        )
    expected_roles = set(TASK_ARTIFACTS[task])
    missing_roles = sorted(expected_roles - set(artifacts))
    if missing_roles:
        findings.append(
            finding(
                "CAT.TASK.EVIDENCE_MISSING",
                "task",
                "error",
                "One or more task-required declarative artifacts are absent.",
                "Provide every artifact required by the selected task profile.",
            )
        )
    unexpected_roles = sorted(set(artifacts) - expected_roles)
    if unexpected_roles:
        findings.append(
            finding(
                "CAT.TASK.EVIDENCE_UNEXPECTED",
                "task",
                "error",
                "One or more artifacts fall outside the selected task profile and would otherwise be ignored.",
                "Select the matching task or remove artifact roles outside its evidence profile.",
            )
        )

    base = request_path.parent
    loaded: dict[str, tuple[dict[str, Any], bytes]] = {}
    for role in TASK_ARTIFACTS[task]:
        declaration = artifacts.get(role)
        if declaration is None:
            continue
        try:
            value, raw = load_relative_json_object(base, declaration["file"], tracker, artifact=True)
        except GuardError as error:
            findings.append(
                finding(
                    error.code,
                    "safety",
                    "error",
                    error.message,
                    "Export the trusted source to bounded declarative JSON under the selected contract.",
                    classification="parse" if error.exit_code == EXIT_PARSE else "input",
                )
            )
            continue
        actual_hash = sha256_bytes(raw)
        evidence.append({"label": declaration["file"], "role": role, "sha256": actual_hash})
        if actual_hash != declaration["sha256"]:
            findings.append(
                finding(
                    "CAT.LINEAGE.HASH_MISMATCH",
                    "lineage",
                    "error",
                    "A declarative artifact does not match its requested SHA-256.",
                    "Restore immutable evidence or create a reviewed replacement record.",
                )
            )
        else:
            loaded[role] = (value, raw)

    network: dict[str, Any] | None = None
    network_hash: str | None = None
    if "network" in loaded:
        try:
            network = validate_network(loaded["network"][0])
        except GuardError as error:
            findings.append(
                finding(
                    error.code,
                    "network" if error.exit_code != EXIT_PARSE else "safety",
                    "error" if error.exit_code != EXIT_BLOCKED else "blocker",
                    error.message,
                    "Correct the declarative network without executing a native file.",
                    classification="parse" if error.exit_code == EXIT_PARSE else "gate",
                )
            )
        else:
            evaluated.add("network")
            network_hash = sha256_bytes(loaded["network"][1])
            network_findings, network_metrics = network_balance_findings(network)
            findings.extend(network_findings)
            metrics["network"] = network_metrics
            if network["evidence_class"] != evidence_class:
                findings.append(
                    finding(
                        "CAT.LINEAGE.HASH_MISMATCH",
                        "lineage",
                        "error",
                        "Network evidence class disagrees with the request.",
                        "Rebuild the package from one evidence class and immutable lineage.",
                    )
                )

    thermo: dict[str, Any] | None = None
    thermo_hash: str | None = None
    if "thermochemistry" in loaded and network is not None:
        try:
            thermo = validate_thermochemistry(loaded["thermochemistry"][0], network)
        except GuardError as error:
            findings.append(
                finding(
                    error.code,
                    "thermochemistry" if error.code != "CAT.UNITS.UNSUPPORTED" else "units",
                    "error",
                    error.message,
                    "Correct units, references, energies, corrections, and barriers before solving.",
                    classification="parse" if error.exit_code == EXIT_PARSE else "gate",
                )
            )
        else:
            evaluated.update({"units", "thermochemistry"})
            thermo_hash = sha256_bytes(loaded["thermochemistry"][1])
            if thermo["network_sha256"] != network_hash or thermo["evidence_class"] != evidence_class:
                findings.append(
                    finding(
                        "CAT.LINEAGE.HASH_MISMATCH",
                        "lineage",
                        "error",
                        "Thermochemistry is detached from the network or evidence class.",
                        "Export thermochemistry against the exact hashed network.",
                    )
                )
            thermo_findings, thermo_metrics = thermochemistry_findings(thermo, network, thresholds)
            findings.extend(thermo_findings)
            metrics["thermochemistry"] = thermo_metrics

    result: dict[str, Any] | None = None
    if "result" in loaded and network is not None and thermo is not None:
        try:
            result = validate_result(loaded["result"][0])
        except GuardError as error:
            findings.append(
                finding(
                    error.code,
                    "units" if error.code == "CAT.UNITS.UNSUPPORTED" else "solver",
                    "error",
                    error.message,
                    "Correct the declarative result export under the exact provider/task contract.",
                    classification="parse" if error.exit_code == EXIT_PARSE else "gate",
                )
            )
        else:
            evaluated.update({"solver", "coverage", "rate", "data_partition"})
            provider = result["provider"]
            expected_python = "not-applicable-synthetic" if evidence_class == "synthetic-fixture" else None
            provider_ok = (
                provider["software"] == "CatMAP"
                and provider["version"] == SUPPORTED_VERSION
                and provider["environment_profile_id"] == SUPPORTED_PROFILE
                and provider["source_revision"] == "v0.4.1"
                and (provider["python_version"] == expected_python if expected_python else re.fullmatch(r"3\.(10|11)(?:\.[0-9]+)?", provider["python_version"]) is not None)
            )
            if not provider_ok:
                findings.append(
                    finding(
                        "CAT.PROVIDER.ENVIRONMENT_UNVALIDATED",
                        "provider",
                        "blocker",
                        "Result provider, source revision, environment profile, or Python identity is unvalidated.",
                        "Use the exact pinned source and reviewed Python/dependency environment.",
                    )
                )
            if (
                result["model_binding"]["network_sha256"] != network_hash
                or result["model_binding"]["thermochemistry_sha256"] != thermo_hash
                or result["evidence_class"] != evidence_class
            ):
                findings.append(
                    finding(
                        "CAT.LINEAGE.HASH_MISMATCH",
                        "lineage",
                        "error",
                        "Result model bindings disagree with network, thermochemistry, or evidence class.",
                        "Re-export the result from the exact hashed model inputs.",
                    )
                )
            solver = result["solver"]
            metrics["solver"] = {
                "branch_identity": solver["branch_identity"],
                "initialization_trial_count": len(solver["initialization_trials"]),
                "iterations": solver["iterations"],
                "residual_norm": solver["residual_norm"],
                "residual_tolerance": solver["residual_tolerance"],
            }
            if not solver["converged"]:
                findings.append(
                    finding(
                        "CAT.SOLVER.NOT_CONVERGED",
                        "solver",
                        "error",
                        "The solver did not declare convergence.",
                        "Preserve the failed branch and revise the numerical plan before rerunning.",
                    )
                )
            if (
                solver["residual_tolerance"] != float(thresholds["solver_residual_tolerance"])
                or solver["residual_norm"] > float(thresholds["solver_residual_tolerance"])
            ):
                findings.append(
                    finding(
                        "CAT.SOLVER.RESIDUAL_EXCEEDED",
                        "solver",
                        "error",
                        "Solver residual or stored tolerance does not meet the predeclared threshold.",
                        "Use the predeclared tolerance and resolve numerical convergence without post-hoc relaxation.",
                    )
                )
            point_findings, point_metrics = audit_points(result, network, thresholds)
            findings.extend(point_findings)
            metrics["steady_state"] = point_metrics
            multistart_findings, multistart_metrics = audit_solver_initializations(
                result, network, thresholds
            )
            findings.extend(multistart_findings)
            metrics["solver"].update(multistart_metrics)

            rate_findings, rate_metrics = audit_rate_normalization(
                result["rate_normalization"], network
            )
            findings.extend(rate_findings)
            metrics["rate_normalization"] = rate_metrics

            partition_findings, partition_metrics = audit_data_partition(result["data_partition"])
            findings.extend(partition_findings)
            metrics["data_partition"] = partition_metrics

            if "sensitivity" in TASK_BLOCKS[task]:
                evaluated.add("sensitivity")
                sensitivity_findings, sensitivity_metrics = audit_sensitivity(
                    result["sensitivity"], thresholds, solver["branch_identity"]
                )
                findings.extend(sensitivity_findings)
                metrics["sensitivity"] = sensitivity_metrics
            if "uncertainty" in TASK_BLOCKS[task]:
                evaluated.add("uncertainty")
                uncertainty_findings, uncertainty_metrics = audit_uncertainty(result["uncertainty"], thresholds)
                findings.extend(uncertainty_findings)
                metrics["uncertainty"] = uncertainty_metrics

    if set(claims) & FORBIDDEN_CLAIMS:
        findings.append(
            finding(
                "CAT.CLAIM.MECHANISM_AUTOMATION_FORBIDDEN",
                "claim",
                "blocker",
                "The request asks automation to assert a mechanism, causal ranking, or experiment agreement.",
                "Keep the technical result and route the scientific interpretation to independent expert review.",
            )
        )
    if evidence_class == "real-artifact":
        findings.append(
            finding(
                "CAT.ACTIVATION.REAL_ARTIFACT_VALIDATION_MISSING",
                "claim",
                "blocker",
                "No accepted v0.4.1 real-artifact and trusted-exporter forward validation exists.",
                "Complete isolated provider integration and real tutorial regression before promotion.",
            )
        )

    status, exit_value = determine_status(findings)
    report = {
        "contract_name": "catmap-candidate-validation-report",
        "schema_version": "1.0",
        "tool": {"name": "catmap_guard", "version": TOOL_VERSION},
        "operation": "audit",
        "status": status,
        "maturity": "synthetic-validated" if evidence_class == "synthetic-fixture" else "design-only",
        "maximum_claim": "no_positive_claim",
        "task_id": task,
        "evidence_class": evidence_class,
        "provider": {"environment_profile_id": SUPPORTED_PROFILE, "software": "CatMAP", "version": request["provider_version"]},
        "gates": gate_projection(findings, evaluated),
        "findings": sorted_findings(findings),
        "evidence": sorted(evidence, key=lambda item: (item["role"], item["label"])),
        "metrics": metrics,
        "requested_claims": claims,
        "thresholds": thresholds,
        "limitations": [
            "Synthetic declarative validation does not establish CatMAP tool integration or real-artifact maturity.",
            "Network balance and solver convergence do not establish a true or unique catalytic mechanism.",
            "Sensitivity and uncertainty are conditional on the declared model, branch, perturbations, and distributions.",
            "Scientific acceptance requires an independent human decision record.",
        ],
    }
    return report, exit_value


def output_metadata(directory_fd: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output target could not be inspected safely.") from exc


def validate_output_target(
    path: Path,
    metadata: os.stat_result | None,
    tracker: InputTracker,
) -> None:
    if tracker.conflicts(path, metadata):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output aliases a request or evidence input.")
    if metadata is not None and (not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output must be a single-link regular report file.")


def _same_file_binding(left: os.stat_result, right: os.stat_result, expected_links: int = 1) -> bool:
    return (
        stat.S_ISREG(left.st_mode)
        and stat.S_ISREG(right.st_mode)
        and left.st_nlink == expected_links
        and right.st_nlink == expected_links
        and (left.st_dev, left.st_ino, left.st_size) == (right.st_dev, right.st_ino, right.st_size)
    )


def _fd_payload_matches(descriptor: int, payload: bytes, expected_links: int = 1) -> bool:
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != expected_links
        or metadata.st_size != len(payload)
    ):
        return False
    digest = hashlib.sha256()
    offset = 0
    while offset < len(payload):
        chunk = os.pread(descriptor, min(1024 * 1024, len(payload) - offset), offset)
        if not chunk:
            return False
        digest.update(chunk)
        offset += len(chunk)
    return offset == len(payload) and digest.digest() == hashlib.sha256(payload).digest()


def write_json_report(
    path: Path,
    value: dict[str, Any],
    overwrite: bool,
    tracker: InputTracker | None = None,
) -> None:
    tracker = tracker if tracker is not None else InputTracker()
    if overwrite:
        raise GuardError(
            "CAT.INPUT.CONTRACT_INVALID",
            "In-place overwrite is unsupported; publish to a new report path.",
        )
    try:
        payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(
            "utf-8"
        )
    except (TypeError, ValueError) as exc:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The report could not be serialized safely.") from exc
    if not path.name or path.name in {".", ".."}:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output filename is invalid.")
    parent = path.parent.absolute()
    target = parent / path.name
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if (
        nofollow is None
        or directory_flag is None
        or not hasattr(os, "pread")
        or not LINK_HAS_DIR_FD
        or not LINK_HAS_NOFOLLOW
    ):
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "This host lacks required safe-output support.")
    try:
        parent_path_metadata = parent.lstat()
        if stat.S_ISLNK(parent_path_metadata.st_mode) or not stat.S_ISDIR(parent_path_metadata.st_mode):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output parent directory is unavailable or unsafe.")
        directory_fd = os.open(
            parent,
            os.O_RDONLY | directory_flag | nofollow | getattr(os, "O_CLOEXEC", 0),
        )
    except GuardError:
        raise
    except OSError as exc:
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output parent directory is unavailable or unsafe.") from exc

    temporary_fd: int | None = None
    temporary_name: str | None = None
    installed = False
    published_new = False
    published_snapshot: os.stat_result | None = None
    try:
        parent_fd_metadata = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(parent_fd_metadata.st_mode)
            or (parent_fd_metadata.st_dev, parent_fd_metadata.st_ino)
            != (parent_path_metadata.st_dev, parent_path_metadata.st_ino)
        ):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output parent identity is unstable.")
        initial = output_metadata(directory_fd, path.name)
        validate_output_target(target, initial, tracker)
        if initial is not None:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output already exists; choose a new report path.")

        for _attempt in range(32):
            candidate = f".vibe-dft-report-{secrets.token_hex(12)}.tmp"
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
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "A private atomic output staging file could not be created.")

        offset = 0
        while offset < len(payload):
            try:
                written = os.write(temporary_fd, payload[offset:])
            except InterruptedError:
                continue
            if written <= 0:
                raise OSError("short atomic report write")
            offset += written
        os.fsync(temporary_fd)
        temporary_metadata = os.fstat(temporary_fd)
        if (
            not stat.S_ISREG(temporary_metadata.st_mode)
            or temporary_metadata.st_nlink != 1
            or temporary_metadata.st_size != len(payload)
            or not _fd_payload_matches(temporary_fd, payload)
        ):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The staged report identity is invalid.")

        current_parent = parent.lstat()
        if (
            stat.S_ISLNK(current_parent.st_mode)
            or not stat.S_ISDIR(current_parent.st_mode)
            or (current_parent.st_dev, current_parent.st_ino)
            != (parent_fd_metadata.st_dev, parent_fd_metadata.st_ino)
        ):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output parent changed before installation.")
        current = output_metadata(directory_fd, path.name)
        validate_output_target(target, current, tracker)
        if current is not None:
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The output target appeared during report staging.")
        staged_name_metadata = output_metadata(directory_fd, temporary_name)
        if staged_name_metadata is None or not _same_file_binding(staged_name_metadata, temporary_metadata):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The staged report path changed before publication.")

        try:
            os.link(
                temporary_name,
                path.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise GuardError(
                "CAT.INPUT.CONTRACT_INVALID",
                "The output target appeared during atomic publication.",
            ) from exc
        published_new = True
        published_snapshot = output_metadata(directory_fd, path.name)
        linked_source = output_metadata(directory_fd, temporary_name)
        linked_descriptor = os.fstat(temporary_fd)
        if (
            published_snapshot is None
            or linked_source is None
            or not _same_file_binding(published_snapshot, linked_descriptor, 2)
            or not _same_file_binding(linked_source, linked_descriptor, 2)
            or not _fd_payload_matches(temporary_fd, payload, 2)
        ):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The published report is not the staged payload.")
        os.fsync(directory_fd)
        os.unlink(temporary_name, dir_fd=directory_fd)
        temporary_name = None
        published_snapshot = output_metadata(directory_fd, path.name)
        if (
            published_snapshot is None
            or not _same_file_binding(published_snapshot, os.fstat(temporary_fd))
            or not _fd_payload_matches(temporary_fd, payload)
        ):
            raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The final report binding is invalid.")
        os.fsync(directory_fd)
        installed = True
        published_new = False
    except GuardError:
        if published_new:
            try:
                current_published = output_metadata(directory_fd, path.name)
                if (
                    current_published is None
                    or published_snapshot is None
                    or stat_identity(current_published) != stat_identity(published_snapshot)
                ):
                    raise OSError("published target identity changed before rollback")
                os.unlink(path.name, dir_fd=directory_fd)
                os.fsync(directory_fd)
                published_new = False
            except OSError as rollback_error:
                raise GuardError(
                    "CAT.INPUT.CONTRACT_INVALID",
                    "Atomic report rollback failed; output state is indeterminate.",
                ) from rollback_error
        raise
    except OSError as exc:
        if published_new:
            try:
                current_published = output_metadata(directory_fd, path.name)
                if (
                    current_published is None
                    or published_snapshot is None
                    or stat_identity(current_published) != stat_identity(published_snapshot)
                ):
                    raise OSError("published target identity changed before rollback")
                os.unlink(path.name, dir_fd=directory_fd)
                os.fsync(directory_fd)
                published_new = False
            except OSError as rollback_error:
                raise GuardError(
                    "CAT.INPUT.CONTRACT_INVALID",
                    "Atomic report rollback failed; output state is indeterminate.",
                ) from rollback_error
        raise GuardError("CAT.INPUT.CONTRACT_INVALID", "The report could not be installed atomically.") from exc
    finally:
        if temporary_fd is not None:
            try:
                os.close(temporary_fd)
            except OSError:
                pass
        if temporary_name is not None and not installed:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        try:
            os.close(directory_fd)
        except OSError:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("plan", "audit"):
        child = subparsers.add_parser(command)
        child.add_argument("--request", type=Path, required=True)
        child.add_argument("--output", type=Path, required=True)
        child.add_argument("--overwrite", action="store_true", help="unsupported compatibility flag; always rejected")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tracker = InputTracker()
    try:
        request, _raw = load_json_object(args.request, tracker, retain_parent=True)
        if args.command == "plan":
            report = make_plan(request)
            _status, exit_value = determine_status(report["findings"])
        else:
            report, exit_value = audit_request(request, args.request.absolute(), tracker)
    except GuardError as error:
        report = invalid_report(error, args.command)
        exit_value = error.exit_code
    try:
        write_json_report(args.output, report, args.overwrite, tracker)
    except GuardError:
        tracker.close()
        print("ERROR: report output is unavailable; path details are redacted", file=sys.stderr)
        return EXIT_INPUT
    tracker.close()
    print(f"{report['status'].upper()}: CatMAP candidate {args.command}; maximum_claim={report['maximum_claim']}")
    return exit_value


if __name__ == "__main__":
    raise SystemExit(main())
