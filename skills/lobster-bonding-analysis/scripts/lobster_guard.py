#!/usr/bin/env python3
"""Plan and audit a fail-closed, provenance-bound LOBSTER candidate package."""

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
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_TEXT_BYTES = 8 * 1024 * 1024
LINK_HAS_DIR_FD = os.link in os.supports_dir_fd
LINK_HAS_NOFOLLOW = os.link in os.supports_follow_symlinks
SHA256 = re.compile(r"^[a-f0-9]{64}$")
FINGERPRINT = re.compile(r"^sha256:[a-f0-9]{64}$")
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
ELEMENT = re.compile(r"^[A-Z][a-z]?$")

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_BLOCKED = 3
EXIT_PARSE = 4
EXIT_FAILED = 5

SUPPORTED_VERSION = "5.1.1"
SUPPORTED_PROFILE = "lobster-5"
SUPPORTED_PARENT = "vasp"
TASK_ARTIFACTS = {
    "projection-audit": ("lobsterout",),
    "cohp-audit": ("lobsterout", "cohp"),
    "coop-audit": ("lobsterout", "coop"),
    "dos-audit": ("lobsterout", "dos"),
    "bonding-package-audit": ("lobsterout", "cohp", "coop", "dos"),
}
TASK_CLAIMS = {
    "projection-audit": {"projection-quality"},
    "cohp-audit": {"projection-quality", "cohp-curve"},
    "coop-audit": {"projection-quality", "coop-curve"},
    "dos-audit": {"projection-quality", "dos-projection-closure"},
    "bonding-package-audit": {
        "projection-quality",
        "cohp-curve",
        "coop-curve",
        "dos-projection-closure",
    },
}
ALLOWED_CLAIMS = {
    "projection-quality",
    "cohp-curve",
    "coop-curve",
    "dos-projection-closure",
}
FORBIDDEN_AUTOMATIC_CLAIMS = {
    "bond-exists",
    "bond-order",
    "bond-strength",
    "bonding-antibonding-assignment",
    "oxidation-state",
    "phase-stability",
    "structure-property-causality",
}
GATE_NAMES = (
    "provider",
    "parent",
    "execution_binding",
    "artifact",
    "completion",
    "basis",
    "projection",
    "curve",
    "consistency",
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
    """Expected, redacted validation failure."""

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
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input root identity changed during the audit.")
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
    limit: int,
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
            "LOB.INPUT.CONTRACT_INVALID",
            "Inputs must be single-link regular files, not aliases, links, or special files.",
        )
    if before.st_size > limit:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input exceeds the bounded size limit.")
    chunks: list[bytes] = []
    total = 0
    while True:
        try:
            chunk = os.read(descriptor, min(1024 * 1024, limit + 1 - total))
        except InterruptedError:
            continue
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > limit:
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input exceeds the bounded size limit.")
    after = os.fstat(descriptor)
    try:
        final = final_metadata()
        lexical_final = path.lstat()
    except OSError as exc:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input path changed while it was being read.") from exc
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
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input identity changed while it was being read.")
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
    limit: int,
    tracker: InputTracker | None = None,
    *,
    retain_parent: bool = False,
) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory_flag is None or nonblock is None:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "This host lacks required no-follow input support.")
    path = path.absolute()
    parent = path.parent
    parent_fd: int | None = None
    descriptor: int | None = None
    try:
        parent_path_metadata = parent.lstat()
        if stat.S_ISLNK(parent_path_metadata.st_mode) or not stat.S_ISDIR(parent_path_metadata.st_mode):
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input parent is unavailable or unsafe.")
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
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input parent identity is unstable.")
        descriptor = os.open(
            path.name,
            os.O_RDONLY | nofollow | nonblock | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
    except FileNotFoundError as exc:
        raise GuardError("LOB.ARTIFACT.MISSING", "A declared input is unavailable.") from exc
    except GuardError:
        raise
    except OSError as exc:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input could not be opened without following aliases.") from exc
    try:
        assert descriptor is not None and parent_fd is not None
        data = _validated_regular_read(
            descriptor,
            path,
            limit,
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
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input parent changed while it was being read.")
        return data
    except OSError as exc:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "An input could not be read safely.") from exc
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
    retain_parent: bool = False,
) -> tuple[dict[str, Any], bytes]:
    raw = read_regular_bytes(path, MAX_JSON_BYTES, tracker, retain_parent=retain_parent)
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "JSON input is malformed, duplicated, or non-finite.") from exc
    if not isinstance(value, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "JSON input must be an object.")
    return value, raw


def is_safe_relative_file(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or len(value) > 160:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def read_relative_regular_bytes(
    base: Path,
    value: Any,
    limit: int,
    tracker: InputTracker | None = None,
) -> bytes:
    """Read a relative input through one stable root and no-follow openat traversal."""
    if not is_safe_relative_file(value):
        raise GuardError("LOB.INPUT.PRIVACY_VIOLATION", "A declared file label is absolute, traversing, or unsafe.")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    nonblock = getattr(os, "O_NONBLOCK", None)
    if nofollow is None or directory_flag is None or nonblock is None:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "This host lacks required no-follow input support.")
    base = base.absolute()
    relative = PurePosixPath(value)
    path = base.joinpath(*relative.parts)
    directory_fds: list[int] = []
    directory_edges: list[tuple[int, str, int, os.stat_result]] = []
    descriptor: int | None = None
    try:
        root_path_metadata = base.lstat()
        if stat.S_ISLNK(root_path_metadata.st_mode) or not stat.S_ISDIR(root_path_metadata.st_mode):
            raise GuardError("LOB.INPUT.PRIVACY_VIOLATION", "The declared input root is an unsafe alias.")
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
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The declared input root identity is unstable.")
        if tracker is not None:
            tracker.bind_root(base, root_metadata)

        current_fd = root_fd
        for component in relative.parts[:-1]:
            component_metadata = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(component_metadata.st_mode) or not stat.S_ISDIR(component_metadata.st_mode):
                raise GuardError("LOB.INPUT.PRIVACY_VIOLATION", "A declared file parent is an unsafe alias.")
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
                raise GuardError("LOB.INPUT.CONTRACT_INVALID", "A declared file parent identity is unstable.")
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
            limit,
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
                raise GuardError("LOB.INPUT.CONTRACT_INVALID", "A declared file parent changed during the read.")
        final_root = base.lstat()
        if (
            stat.S_ISLNK(final_root.st_mode)
            or not stat.S_ISDIR(final_root.st_mode)
            or (final_root.st_dev, final_root.st_ino) != (root_metadata.st_dev, root_metadata.st_ino)
        ):
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The declared input root changed during the read.")
        return data
    except FileNotFoundError as exc:
        raise GuardError("LOB.ARTIFACT.MISSING", "A declared input is unavailable.") from exc
    except GuardError:
        raise
    except OSError as exc:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "A declared input could not be opened or read safely.") from exc
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
) -> tuple[dict[str, Any], bytes]:
    raw = read_relative_regular_bytes(base, value, MAX_JSON_BYTES, tracker)
    try:
        text = raw.decode("utf-8")
        result = json.loads(text, object_pairs_hook=_object_no_duplicates, parse_constant=_reject_constant)
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "JSON input is malformed, duplicated, or non-finite.") from exc
    if not isinstance(result, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "JSON input must be an object.")
    return result, raw


def privacy_violations(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).casefold()
            if normalized in SENSITIVE_KEYS:
                violations.append(".".join((*path, str(key))))
            violations.extend(privacy_violations(child, (*path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(privacy_violations(child, (*path, str(index))))
    elif isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("/", "~/", "ssh://", "scp://")) or WINDOWS_ABSOLUTE.match(stripped):
            violations.append(".".join(path) or "value")
        if "-----BEGIN PRIVATE KEY-----" in value:
            violations.append(".".join(path) or "value")
    return violations


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", f"{label} has missing or unknown fields.")


def require_string(value: Any, label: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", f"{label} must be a nonempty string.")
    return value


def require_sha256(value: Any, label: str) -> str:
    text = require_string(value, label)
    if not SHA256.fullmatch(text):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", f"{label} must be a lowercase SHA-256 value.")
    return text


def require_fingerprint(value: Any, label: str) -> str:
    text = require_string(value, label)
    if not FINGERPRINT.fullmatch(text):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", f"{label} must be a sha256-prefixed fingerprint.")
    return text


def require_number(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", f"{label} must be a finite number.")
    number = float(value)
    if minimum is not None and number < minimum:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", f"{label} is below its allowed minimum.")
    if maximum is not None and number > maximum:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", f"{label} exceeds its allowed maximum.")
    return number


def require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", f"{label} must be a nonempty list.")
    result = [require_string(item, label) for item in value]
    if len(result) != len(set(result)):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", f"{label} contains duplicates.")
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


def gate_projection(findings: list[dict[str, str]], evaluated: set[str]) -> dict[str, str]:
    result = {name: "not_evaluated" for name in GATE_NAMES}
    for name in evaluated:
        result[name] = "pass"
    for item in findings:
        gate = item["gate"]
        if gate not in result:
            continue
        state = "blocked" if item["severity"] == "blocker" else "fail"
        if result[gate] != "fail":
            result[gate] = state
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


def sorted_findings(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(findings, key=lambda item: (item["code"], item["gate"], item["message"]))


def invalid_report(error: GuardError, operation: str) -> dict[str, Any]:
    classification = "parse" if error.exit_code == EXIT_PARSE else "input"
    item = finding(
        error.code,
        "artifact" if classification == "parse" else "task",
        "error",
        error.message,
        "Correct the bounded declarative input and rerun without weakening a gate.",
        classification=classification,
    )
    status, _exit = determine_status([item])
    return {
        "contract_name": "lobster-candidate-validation-report",
        "schema_version": "1.0",
        "tool": {"name": "lobster_guard", "version": TOOL_VERSION},
        "operation": operation,
        "status": status,
        "maturity": "design-only",
        "maximum_claim": "no_positive_claim",
        "gates": gate_projection([item], set()),
        "findings": [item],
        "evidence": [],
        "metrics": {},
        "limitations": [
            "The Skill is in development and non-routable.",
            "No scientific interpretation or acceptance follows from this report.",
        ],
    }


def validate_thresholds(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "thresholds must be an object.")
    require_exact_keys(
        value,
        {
            "curve_integral_abs_tolerance",
            "dos_closure_relative_tolerance",
            "fermi_alignment_abs_tolerance_eV",
            "max_absolute_charge_spilling_percent",
            "max_absolute_total_spilling_percent",
            "min_projected_band_fraction",
        },
        "thresholds",
    )
    return {
        "curve_integral_abs_tolerance": require_number(
            value["curve_integral_abs_tolerance"], "curve integral tolerance", minimum=0.0
        ),
        "dos_closure_relative_tolerance": require_number(
            value["dos_closure_relative_tolerance"], "DOS closure tolerance", minimum=0.0
        ),
        "fermi_alignment_abs_tolerance_eV": require_number(
            value["fermi_alignment_abs_tolerance_eV"], "Fermi alignment tolerance", minimum=0.0
        ),
        "max_absolute_charge_spilling_percent": require_number(
            value["max_absolute_charge_spilling_percent"], "charge spilling threshold", minimum=0.0
        ),
        "max_absolute_total_spilling_percent": require_number(
            value["max_absolute_total_spilling_percent"], "total spilling threshold", minimum=0.0
        ),
        "min_projected_band_fraction": require_number(
            value["min_projected_band_fraction"], "projected band fraction", minimum=0.0, maximum=1.0
        ),
    }


def validate_task_and_claims(task_id: Any, claims_value: Any) -> tuple[str, list[str]]:
    task = require_string(task_id, "task_id")
    if task not in TASK_ARTIFACTS:
        raise GuardError("LOB.TASK.UNSUPPORTED", "The requested LOBSTER task has no candidate profile.", EXIT_BLOCKED)
    claims = require_string_list(claims_value, "requested claims")
    unknown = set(claims) - ALLOWED_CLAIMS - FORBIDDEN_AUTOMATIC_CLAIMS
    if unknown:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "A requested claim is unknown to the candidate contract.")
    incompatible = set(claims) - TASK_CLAIMS[task] - FORBIDDEN_AUTOMATIC_CLAIMS
    if incompatible:
        raise GuardError(
            "LOB.TASK.CLAIM_UNSUPPORTED",
            "A requested technical claim is outside the selected task evidence profile.",
            EXIT_BLOCKED,
        )
    return task, claims


def make_plan(request: dict[str, Any]) -> dict[str, Any]:
    violations = privacy_violations(request)
    if violations:
        raise GuardError("LOB.INPUT.PRIVACY_VIOLATION", "The plan request contains a private path or sensitive field.")
    require_exact_keys(
        request,
        {
            "contract_name",
            "evidence_class",
            "parent_dft_code",
            "provider_version",
            "requested_claims",
            "schema_version",
            "task_id",
            "thresholds",
        },
        "plan request",
    )
    if request["contract_name"] != "lobster-plan-request" or request["schema_version"] != "1.0":
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The plan contract identity is unsupported.")
    task, claims = validate_task_and_claims(request["task_id"], request["requested_claims"])
    thresholds = validate_thresholds(request["thresholds"])
    evidence_class = require_string(request["evidence_class"], "evidence_class")
    if evidence_class not in {"synthetic-fixture", "real-artifact"}:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "evidence_class is unsupported.")

    findings: list[dict[str, str]] = []
    evaluated = {"provider", "task", "claim"}
    if request["provider_version"] != SUPPORTED_VERSION:
        findings.append(
            finding(
                "LOB.PROVIDER.VERSION_UNSUPPORTED",
                "provider",
                "blocker",
                "Only the exact LOBSTER 5.1.1 provider profile is pinned.",
                "Create and validate a separate exact-version profile.",
            )
        )
    if request["parent_dft_code"] != SUPPORTED_PARENT:
        findings.append(
            finding(
                "LOB.PARENT.DFT_PROVIDER_UNSUPPORTED",
                "parent",
                "blocker",
                "Only the VASP parent route has a candidate fixture.",
                "Validate a provider-specific parent and real-artifact route before use.",
            )
        )
        evaluated.add("parent")
    forbidden = sorted(set(claims) & FORBIDDEN_AUTOMATIC_CLAIMS)
    if forbidden:
        findings.append(
            finding(
                "LOB.CLAIM.AUTOMATIC_CHEMICAL_INTERPRETATION_FORBIDDEN",
                "claim",
                "blocker",
                "The request asks automation to make a chemical interpretation.",
                "Limit automation to evidence preparation and route interpretation to expert review.",
            )
        )

    status, _exit = determine_status(findings)
    return {
        "contract_name": "lobster-candidate-plan-report",
        "schema_version": "1.0",
        "tool": {"name": "lobster_guard", "version": TOOL_VERSION},
        "operation": "plan",
        "status": status,
        "maturity": "design-only",
        "maximum_claim": "no_positive_claim",
        "task_id": task,
        "provider": {
            "environment_profile_id": SUPPORTED_PROFILE,
            "parent_dft_code": request["parent_dft_code"],
            "software": "LOBSTER",
            "version": request["provider_version"],
        },
        "required_artifacts": list(TASK_ARTIFACTS[task]),
        "required_bindings": [
            "parent_record_sha256",
            "structure_fingerprint",
            "input_wavefunction_sha256",
            "lobsterin_sha256",
            "basis_by_element",
            "artifact_sha256",
        ],
        "thresholds": thresholds,
        "requested_claims": claims,
        "gates": gate_projection(findings, evaluated),
        "findings": sorted_findings(findings),
        "steps": [
            "Establish lawful exact-version provider identity without storing licensed bytes.",
            "Validate immutable DFT parent and execution bindings.",
            "Hash and parse task-required artifacts under the exact profile.",
            "Audit basis identity and absolute spilling against declared thresholds.",
            "Audit curve units, reference, spin, sign, and numerical closure.",
            "Emit evidence for expert review without automatic chemical acceptance.",
        ],
        "limitations": [
            "A valid plan is not evidence that LOBSTER ran or that a scientific claim is true.",
            "The candidate never invokes the licensed binary.",
        ],
    }


def validate_parent_record(value: dict[str, Any]) -> None:
    require_exact_keys(
        value,
        {
            "claim_ceiling",
            "contract_name",
            "dft_code",
            "dft_inputs",
            "dft_version",
            "evidence_class",
            "gates",
            "protocol",
            "record_id",
            "schema_version",
            "structure_fingerprint",
            "task_id",
            "wavefunction",
        },
        "parent record",
    )
    if value["contract_name"] != "electronic-wavefunction-source-candidate" or value["schema_version"] != "1.0":
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The parent record contract identity is unsupported.")
    require_string(value["record_id"], "parent record_id")
    require_string(value["dft_code"], "parent dft_code")
    require_string(value["dft_version"], "parent dft_version")
    require_string(value["task_id"], "parent task_id")
    require_fingerprint(value["structure_fingerprint"], "parent structure fingerprint")
    require_string(value["claim_ceiling"], "parent claim ceiling")
    require_string(value["evidence_class"], "parent evidence class")

    protocol = value["protocol"]
    if not isinstance(protocol, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "parent protocol must be an object.")
    require_exact_keys(protocol, {"id", "sha256", "task_profile"}, "parent protocol")
    require_string(protocol["id"], "parent protocol id")
    require_sha256(protocol["sha256"], "parent protocol hash")
    require_string(protocol["task_profile"], "parent task profile")

    dft_inputs = value["dft_inputs"]
    if not isinstance(dft_inputs, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "parent dft_inputs must be an object.")
    require_exact_keys(
        dft_inputs,
        {"kpoints_sha256", "potential_metadata_sha256", "settings_sha256", "structure_sha256"},
        "parent dft_inputs",
    )
    for key, item in dft_inputs.items():
        require_sha256(item, f"parent dft_inputs.{key}")

    wavefunction = value["wavefunction"]
    if not isinstance(wavefunction, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "parent wavefunction must be an object.")
    require_exact_keys(wavefunction, {"artifact_label", "sha256"}, "parent wavefunction")
    require_string(wavefunction["artifact_label"], "wavefunction artifact label")
    require_sha256(wavefunction["sha256"], "wavefunction sha256")

    gates = value["gates"]
    if not isinstance(gates, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "parent gates must be an object.")
    require_exact_keys(
        gates,
        {"completion", "input", "numerical", "wavefunction_eligible_for_lobster"},
        "parent gates",
    )
    if any(item not in {"pass", "fail", "blocked", "not_evaluated"} for item in gates.values()):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "parent gate values are unsupported.")


def validate_parent_validation(value: dict[str, Any], parent_hash: str, parent_record: dict[str, Any]) -> None:
    require_exact_keys(
        value,
        {
            "contract_name",
            "evidence_bindings",
            "evidence_class",
            "gates",
            "schema_version",
            "subject",
            "validator",
        },
        "parent validation receipt",
    )
    if value["contract_name"] != "parent-validation-receipt-candidate" or value["schema_version"] != "1.0":
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The parent validation receipt identity is unsupported.")
    require_string(value["evidence_class"], "validation evidence class")
    subject = value["subject"]
    if not isinstance(subject, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "validation subject must be an object.")
    require_exact_keys(subject, {"record_id", "record_sha256"}, "validation subject")
    require_string(subject["record_id"], "validation subject record id")
    require_sha256(subject["record_sha256"], "validation subject record hash")
    validator = value["validator"]
    if not isinstance(validator, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "validator identity must be an object.")
    require_exact_keys(validator, {"id", "mode", "version"}, "validator identity")
    for key, item in validator.items():
        require_string(item, f"validator {key}")
    gates = value["gates"]
    bindings = value["evidence_bindings"]
    expected_gates = {"completion", "input", "numerical", "wavefunction_eligible_for_lobster"}
    if not isinstance(gates, dict) or not isinstance(bindings, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "validation gates and bindings must be objects.")
    require_exact_keys(gates, expected_gates, "validation gates")
    require_exact_keys(bindings, expected_gates, "validation evidence bindings")
    for key in expected_gates:
        if gates[key] != "pass":
            raise GuardError("LOB.PARENT.GATE_NOT_PASSED", "An independently recorded parent gate is not passed.", EXIT_FAILED)
        require_sha256(bindings[key], f"validation evidence binding {key}")
    if (
        subject["record_id"] != parent_record["record_id"]
        or subject["record_sha256"] != parent_hash
        or gates != parent_record["gates"]
        or value["evidence_class"] != parent_record["evidence_class"]
    ):
        raise GuardError(
            "LOB.PARENT.VALIDATION_DETACHED",
            "The parent validation receipt is detached from the parent bytes, gates, or evidence class.",
            EXIT_FAILED,
        )


def validate_basis(value: Any) -> tuple[str, str, dict[str, list[str]]]:
    if not isinstance(value, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "basis must be an object.")
    require_exact_keys(value, {"basis_by_element", "family", "selection_rationale", "source"}, "basis")
    family = require_string(value["family"], "basis family")
    source = require_string(value["source"], "basis source")
    require_string(value["selection_rationale"], "basis selection rationale")
    raw_map = value["basis_by_element"]
    if not isinstance(raw_map, dict) or not raw_map:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "basis_by_element must be a nonempty object.")
    result: dict[str, list[str]] = {}
    for element, orbitals in raw_map.items():
        if not isinstance(element, str) or not ELEMENT.fullmatch(element):
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "basis_by_element contains an invalid element label.")
        items = require_string_list(orbitals, f"basis orbitals for {element}")
        result[element] = sorted(items)
    return family, source, dict(sorted(result.items()))


def validate_provider(value: Any, evidence_class: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "provider must be an object.")
    require_exact_keys(
        value,
        {"environment_profile_id", "execution_identity", "license_authorization", "software", "version"},
        "provider",
    )
    if value["software"] != "LOBSTER":
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "provider software identity is invalid.")
    require_string(value["version"], "provider version")
    require_string(value["environment_profile_id"], "environment profile")
    authorization = require_string(value["license_authorization"], "license authorization")
    expected_authorization = (
        "not-applicable-synthetic" if evidence_class == "synthetic-fixture" else "attested-private-receipt"
    )
    if authorization != expected_authorization:
        raise GuardError(
            "LOB.PROVIDER.AUTHORIZATION_MISSING",
            "The evidence class lacks its required authorization state.",
            EXIT_BLOCKED,
        )
    identity = value["execution_identity"]
    if not isinstance(identity, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "execution_identity must be an object.")
    require_exact_keys(
        identity,
        {
            "execution_record_id",
            "dft_input_hashes",
            "dft_protocol_sha256",
            "input_wavefunction_sha256",
            "lobsterin_sha256",
            "parent_record_sha256",
            "parent_validation_sha256",
            "structure_fingerprint",
        },
        "execution_identity",
    )
    require_string(identity["execution_record_id"], "execution record id")
    require_sha256(identity["dft_protocol_sha256"], "execution DFT protocol hash")
    require_sha256(identity["input_wavefunction_sha256"], "execution input wavefunction hash")
    require_sha256(identity["lobsterin_sha256"], "execution lobsterin hash")
    require_sha256(identity["parent_record_sha256"], "execution parent hash")
    require_sha256(identity["parent_validation_sha256"], "execution parent validation hash")
    require_fingerprint(identity["structure_fingerprint"], "execution structure fingerprint")
    input_hashes = identity["dft_input_hashes"]
    if not isinstance(input_hashes, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "execution DFT input hashes must be an object.")
    require_exact_keys(
        input_hashes,
        {"kpoints_sha256", "potential_metadata_sha256", "settings_sha256", "structure_sha256"},
        "execution DFT input hashes",
    )
    for key, item in input_hashes.items():
        require_sha256(item, f"execution DFT input hash {key}")
    return value


def validate_parent_declaration(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "parent must be an object.")
    require_exact_keys(
        value,
        {
            "dft_code",
            "dft_input_hashes",
            "dft_protocol_id",
            "dft_protocol_sha256",
            "dft_version",
            "record_file",
            "record_id",
            "record_sha256",
            "validation_file",
            "validation_sha256",
            "structure_fingerprint",
            "task_id",
            "wavefunction_artifact_label",
            "wavefunction_sha256",
        },
        "parent declaration",
    )
    require_string(value["dft_code"], "parent dft_code")
    require_string(value["dft_protocol_id"], "parent DFT protocol id")
    require_sha256(value["dft_protocol_sha256"], "parent DFT protocol hash")
    require_string(value["dft_version"], "parent dft_version")
    require_string(value["record_id"], "parent record_id")
    if not is_safe_relative_file(value["record_file"]):
        raise GuardError("LOB.INPUT.PRIVACY_VIOLATION", "parent record_file is unsafe.")
    require_sha256(value["record_sha256"], "parent record hash")
    if not is_safe_relative_file(value["validation_file"]):
        raise GuardError("LOB.INPUT.PRIVACY_VIOLATION", "parent validation_file is unsafe.")
    require_sha256(value["validation_sha256"], "parent validation hash")
    require_fingerprint(value["structure_fingerprint"], "parent structure fingerprint")
    require_string(value["task_id"], "parent task_id")
    require_string(value["wavefunction_artifact_label"], "parent wavefunction label")
    require_sha256(value["wavefunction_sha256"], "parent wavefunction hash")
    input_hashes = value["dft_input_hashes"]
    if not isinstance(input_hashes, dict):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "parent DFT input hashes must be an object.")
    require_exact_keys(
        input_hashes,
        {"kpoints_sha256", "potential_metadata_sha256", "settings_sha256", "structure_sha256"},
        "parent DFT input hashes",
    )
    for key, item in input_hashes.items():
        require_sha256(item, f"parent DFT input hash {key}")
    return value


def validate_artifact_declarations(value: Any) -> dict[str, dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "artifacts must be a nonempty list.")
    result: dict[str, dict[str, str]] = {}
    for item in value:
        if not isinstance(item, dict):
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "artifact entries must be objects.")
        require_exact_keys(item, {"file", "role", "sha256"}, "artifact entry")
        role = require_string(item["role"], "artifact role")
        if role not in {"lobsterout", "cohp", "coop", "dos"} or role in result:
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "artifact role is unknown or duplicated.")
        if not is_safe_relative_file(item["file"]):
            raise GuardError("LOB.INPUT.PRIVACY_VIOLATION", "artifact file is unsafe.")
        result[role] = {
            "file": item["file"],
            "role": role,
            "sha256": require_sha256(item["sha256"], f"artifact {role} hash"),
        }
    return result


def parse_lobsterout(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise GuardError(
            "LOB.PARSER.LOBSTEROUT_FORMAT_UNSUPPORTED",
            "lobsterout is not bounded UTF-8 text under this candidate parser.",
            EXIT_PARSE,
        ) from exc
    if "VIBE_DFT_SYNTHETIC_LOBSTEROUT_V1" not in text:
        raise GuardError(
            "LOB.PARSER.LOBSTEROUT_FORMAT_UNSUPPORTED",
            "lobsterout does not match the synthetic candidate parser profile.",
            EXIT_PARSE,
        )
    version_match = re.search(r"^LOBSTER version\s*[:=]\s*([0-9]+\.[0-9]+\.[0-9]+)\s*$", text, re.MULTILINE)
    dft_match = re.search(r"^DFT program\s*[:=]\s*([A-Za-z0-9_-]+)\s*$", text, re.MULTILINE)
    charge_match = re.search(
        r"^absolute charge spilling percent\s*[:=]\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*$",
        text,
        re.MULTILINE,
    )
    total_match = re.search(
        r"^absolute total spilling percent\s*[:=]\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*$",
        text,
        re.MULTILINE,
    )
    band_fraction_match = re.search(
        r"^projected band fraction\s*[:=]\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*$",
        text,
        re.MULTILINE,
    )
    window_min_match = re.search(
        r"^projection window minimum eV\s*[:=]\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*$",
        text,
        re.MULTILINE,
    )
    window_max_match = re.search(
        r"^projection window maximum eV\s*[:=]\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*$",
        text,
        re.MULTILINE,
    )
    fermi_match = re.search(
        r"^fermi energy eV\s*[:=]\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*$",
        text,
        re.MULTILINE,
    )
    basis: dict[str, list[str]] = {}
    for match in re.finditer(r"^basis\s+([A-Z][a-z]?)\s*[:=]\s*([^\n]+)$", text, re.MULTILINE):
        orbitals = [item for item in re.split(r"[\s,]+", match.group(2).strip()) if item]
        basis[match.group(1)] = sorted(orbitals)
    fatal = bool(re.search(r"^(?:ERROR|FATAL)\b", text, re.MULTILINE))
    completed = bool(re.search(r"^LOBSTER run completed\s*$", text, re.MULTILINE))

    def parsed_number(match: re.Match[str] | None) -> float | None:
        if match is None:
            return None
        value = float(match.group(1))
        return value if math.isfinite(value) else None

    return {
        "basis_by_element": dict(sorted(basis.items())),
        "completed": completed,
        "dft_program": dft_match.group(1).casefold() if dft_match else None,
        "fatal_marker": fatal,
        "absolute_charge_spilling_percent": parsed_number(charge_match),
        "absolute_total_spilling_percent": parsed_number(total_match),
        "fermi_energy_eV": parsed_number(fermi_match),
        "projected_band_fraction": parsed_number(band_fraction_match),
        "projection_window_max_eV": parsed_number(window_max_match),
        "projection_window_min_eV": parsed_number(window_min_match),
        "version": version_match.group(1) if version_match else None,
    }


def parse_curve(raw: bytes, role: str) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise GuardError(
            "LOB.PARSER.CURVE_FORMAT_UNSUPPORTED",
            "A curve artifact is not bounded UTF-8 text.",
            EXIT_PARSE,
        ) from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "# VIBE_DFT_SYNTHETIC_LOBSTER_CURVE_V1":
        raise GuardError(
            "LOB.PARSER.CURVE_FORMAT_UNSUPPORTED",
            "A curve artifact does not match the synthetic candidate profile.",
            EXIT_PARSE,
        )
    metadata: dict[str, str] = {}
    rows: list[list[float]] = []
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            content = stripped[1:].strip()
            if "=" not in content:
                raise GuardError(
                    "LOB.PARSER.CURVE_FORMAT_UNSUPPORTED",
                    "A curve metadata line is malformed.",
                    EXIT_PARSE,
                )
            key, value = content.split("=", 1)
            if key.strip() in metadata:
                raise GuardError(
                    "LOB.PARSER.CURVE_FORMAT_UNSUPPORTED",
                    "A curve metadata key is duplicated.",
                    EXIT_PARSE,
                )
            metadata[key.strip()] = value.strip()
            continue
        try:
            row = [float(item) for item in stripped.split()]
        except ValueError as exc:
            raise GuardError(
                "LOB.PARSER.CURVE_FORMAT_UNSUPPORTED",
                "A curve row contains a non-numeric token.",
                EXIT_PARSE,
            ) from exc
        if not row or not all(math.isfinite(item) for item in row):
            raise GuardError(
                "LOB.PARSER.CURVE_FORMAT_UNSUPPORTED",
                "A curve row is empty or non-finite.",
                EXIT_PARSE,
            )
        rows.append(row)
    required_metadata = {
        "columns",
        "energy_reference",
        "energy_unit",
        "fermi_energy_eV",
        "kind",
        "sign_convention",
        "spin_mode",
    }
    if set(metadata) != required_metadata or not rows:
        raise GuardError(
            "LOB.CURVE.METADATA_MISSING",
            "Curve metadata or data rows are incomplete.",
            EXIT_PARSE,
        )
    expected_kind = {"cohp": "COHP", "coop": "COOP", "dos": "DOS"}[role]
    expected_columns = {
        "cohp": ["energy_eV", "value", "integrated"],
        "coop": ["energy_eV", "value", "integrated"],
        "dos": ["energy_eV", "total_dos", "projected_sum_dos"],
    }[role]
    columns = [item.strip() for item in metadata["columns"].split(",")]
    accepted_signs = {
        "cohp": {"raw_cohp", "negative_cohp"},
        "coop": {"raw_coop"},
        "dos": {"density_of_states"},
    }[role]
    if (
        metadata["kind"] != expected_kind
        or metadata["energy_unit"] != "eV"
        or metadata["energy_reference"] != "fermi"
        or metadata["spin_mode"] not in {"total", "up", "down"}
        or metadata["sign_convention"] not in accepted_signs
        or columns != expected_columns
        or any(len(row) != len(columns) for row in rows)
    ):
        raise GuardError(
            "LOB.CURVE.METADATA_MISSING",
            "Curve type, unit, reference, spin, sign, or columns do not match the selected task.",
            EXIT_PARSE,
        )
    energies = [row[0] for row in rows]
    try:
        fermi_energy = float(metadata["fermi_energy_eV"])
    except ValueError as exc:
        raise GuardError(
            "LOB.CURVE.METADATA_MISSING",
            "The curve Fermi energy is not numeric.",
            EXIT_PARSE,
        ) from exc
    if not math.isfinite(fermi_energy):
        raise GuardError("LOB.CURVE.METADATA_MISSING", "The curve Fermi energy is non-finite.", EXIT_PARSE)
    if len(energies) < 2 or any(right <= left for left, right in zip(energies, energies[1:])):
        raise GuardError(
            "LOB.CURVE.ENERGY_GRID_INVALID",
            "The curve energy grid is not strictly increasing.",
            EXIT_PARSE,
        )
    result: dict[str, Any] = {
        "energy_max_eV": energies[-1],
        "energy_min_eV": energies[0],
        "fermi_energy_eV": fermi_energy,
        "point_count": len(rows),
        "sign_convention": metadata["sign_convention"],
        "spin_mode": metadata["spin_mode"],
    }
    if role in {"cohp", "coop"}:
        cumulative = [0.0]
        for left, right in zip(rows, rows[1:]):
            cumulative.append(cumulative[-1] + 0.5 * (left[1] + right[1]) * (right[0] - left[0]))
        result["maximum_integral_abs_error"] = max(
            abs(expected - row[2]) for expected, row in zip(cumulative, rows)
        )
    else:
        relative_errors = [
            abs(row[1] - row[2]) / max(abs(row[1]), 1.0e-12)
            for row in rows
        ]
        result["maximum_projection_closure_relative_error"] = max(relative_errors)
        result["minimum_total_dos"] = min(row[1] for row in rows)
        result["minimum_projected_sum_dos"] = min(row[2] for row in rows)
    return result


def validate_audit_contract(request: dict[str, Any]) -> tuple[str, str, list[str], dict[str, float]]:
    violations = privacy_violations(request)
    if violations:
        raise GuardError("LOB.INPUT.PRIVACY_VIOLATION", "The audit request contains a private path or sensitive field.")
    require_exact_keys(
        request,
        {
            "artifacts",
            "basis",
            "contract_name",
            "evidence_class",
            "parent",
            "provider",
            "requested_claims",
            "schema_version",
            "task_id",
            "thresholds",
        },
        "audit request",
    )
    if request["contract_name"] != "lobster-audit-request" or request["schema_version"] != "1.0":
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The audit contract identity is unsupported.")
    evidence_class = require_string(request["evidence_class"], "evidence_class")
    if evidence_class not in {"synthetic-fixture", "real-artifact"}:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "evidence_class is unsupported.")
    task, claims = validate_task_and_claims(request["task_id"], request["requested_claims"])
    thresholds = validate_thresholds(request["thresholds"])
    return task, evidence_class, claims, thresholds


def audit_request(
    request: dict[str, Any],
    request_path: Path,
    tracker: InputTracker | None = None,
) -> tuple[dict[str, Any], int]:
    tracker = tracker if tracker is not None else InputTracker()
    task, evidence_class, claims, thresholds = validate_audit_contract(request)
    provider = validate_provider(request["provider"], evidence_class)
    parent_decl = validate_parent_declaration(request["parent"])
    _basis_family, _basis_source, declared_basis = validate_basis(request["basis"])
    artifacts = validate_artifact_declarations(request["artifacts"])

    findings: list[dict[str, str]] = []
    evaluated: set[str] = {"provider", "parent", "execution_binding", "artifact", "task", "claim"}
    evidence: list[dict[str, str]] = []
    metrics: dict[str, Any] = {}

    if provider["version"] != SUPPORTED_VERSION or provider["environment_profile_id"] != SUPPORTED_PROFILE:
        findings.append(
            finding(
                "LOB.PROVIDER.VERSION_UNSUPPORTED",
                "provider",
                "blocker",
                "The provider version or environment profile is not the pinned LOBSTER 5.1.1 route.",
                "Use the exact pinned provider or validate a new profile.",
            )
        )
    if parent_decl["dft_code"] != SUPPORTED_PARENT:
        findings.append(
            finding(
                "LOB.PARENT.DFT_PROVIDER_UNSUPPORTED",
                "parent",
                "blocker",
                "The declared DFT parent route has no validated candidate fixture.",
                "Validate a provider-specific parent route before auditing it.",
            )
        )

    base = request_path.parent
    parent_record, parent_raw = load_relative_json_object(base, parent_decl["record_file"], tracker)
    validate_parent_record(parent_record)
    actual_parent_hash = sha256_bytes(parent_raw)
    evidence.append({"label": parent_decl["record_file"], "role": "parent-record", "sha256": actual_parent_hash})
    if actual_parent_hash != parent_decl["record_sha256"]:
        findings.append(
            finding(
                "LOB.PARENT.HASH_MISMATCH",
                "parent",
                "error",
                "The parent record bytes do not match the declared hash.",
                "Restore the immutable parent record or update the declaration through a reviewed lineage event.",
            )
        )

    try:
        validation_record, validation_raw = load_relative_json_object(base, parent_decl["validation_file"], tracker)
        validate_parent_validation(validation_record, actual_parent_hash, parent_record)
    except GuardError as error:
        findings.append(
            finding(
                error.code,
                "parent",
                "error",
                error.message,
                "Provide an independent hash-bound validation receipt with gate evidence bindings.",
                classification="parse" if error.exit_code == EXIT_PARSE else "gate",
            )
        )
    else:
        actual_validation_hash = sha256_bytes(validation_raw)
        evidence.append(
            {
                "label": parent_decl["validation_file"],
                "role": "parent-validation",
                "sha256": actual_validation_hash,
            }
        )
        if actual_validation_hash != parent_decl["validation_sha256"]:
            findings.append(
                finding(
                    "LOB.PARENT.VALIDATION_DETACHED",
                    "parent",
                    "error",
                    "The parent validation receipt bytes do not match the declared hash.",
                    "Restore the immutable validation receipt or issue a reviewed replacement.",
                )
            )

    identity_pairs = (
        (parent_record["record_id"], parent_decl["record_id"]),
        (parent_record["dft_code"], parent_decl["dft_code"]),
        (parent_record["dft_version"], parent_decl["dft_version"]),
        (parent_record["task_id"], parent_decl["task_id"]),
        (parent_record["protocol"]["id"], parent_decl["dft_protocol_id"]),
        (parent_record["protocol"]["sha256"], parent_decl["dft_protocol_sha256"]),
        (parent_record["structure_fingerprint"], parent_decl["structure_fingerprint"]),
        (parent_record["wavefunction"]["artifact_label"], parent_decl["wavefunction_artifact_label"]),
        (parent_record["wavefunction"]["sha256"], parent_decl["wavefunction_sha256"]),
        (parent_record["evidence_class"], evidence_class),
        (parent_record["dft_inputs"], parent_decl["dft_input_hashes"]),
    )
    if any(left != right for left, right in identity_pairs):
        findings.append(
            finding(
                "LOB.PARENT.IDENTITY_MISMATCH",
                "parent",
                "error",
                "The parent declaration disagrees with the hashed parent record.",
                "Regenerate the handoff from one immutable parent record.",
            )
        )
    if any(parent_record["gates"][name] != "pass" for name in parent_record["gates"]):
        findings.append(
            finding(
                "LOB.PARENT.GATE_NOT_PASSED",
                "parent",
                "error",
                "The DFT parent has an incomplete or failed prerequisite gate.",
                "Resolve the DFT input, completion, numerical, and wavefunction-eligibility gates first.",
            )
        )

    execution = provider["execution_identity"]
    binding_pairs = (
        (execution["parent_record_sha256"], parent_decl["record_sha256"]),
        (execution["parent_validation_sha256"], parent_decl["validation_sha256"]),
        (execution["input_wavefunction_sha256"], parent_decl["wavefunction_sha256"]),
        (execution["structure_fingerprint"], parent_decl["structure_fingerprint"]),
        (execution["dft_protocol_sha256"], parent_decl["dft_protocol_sha256"]),
        (execution["dft_input_hashes"], parent_decl["dft_input_hashes"]),
    )
    if any(left != right for left, right in binding_pairs):
        findings.append(
            finding(
                "LOB.PARENT.IDENTITY_MISMATCH",
                "execution_binding",
                "error",
                "The execution identity is not bound to the declared parent evidence.",
                "Create a new execution record that binds the exact parent, structure, wavefunction, and input hashes.",
            )
        )

    expected_roles = set(TASK_ARTIFACTS[task])
    missing_roles = sorted(expected_roles - set(artifacts))
    if missing_roles:
        findings.append(
            finding(
                "LOB.TASK.EVIDENCE_MISSING",
                "task",
                "error",
                "One or more task-required artifact roles are absent.",
                "Provide every role required by the selected task profile.",
            )
        )
    unexpected_roles = sorted(set(artifacts) - expected_roles)
    if unexpected_roles:
        findings.append(
            finding(
                "LOB.TASK.EVIDENCE_UNEXPECTED",
                "task",
                "error",
                "One or more artifacts fall outside the selected task profile and would otherwise be ignored.",
                "Select the matching task profile or remove undeclared artifact roles from this request.",
            )
        )

    raw_by_role: dict[str, bytes] = {}
    for role in TASK_ARTIFACTS[task]:
        declaration = artifacts.get(role)
        if declaration is None:
            continue
        raw = read_relative_regular_bytes(base, declaration["file"], MAX_TEXT_BYTES, tracker)
        actual_hash = sha256_bytes(raw)
        evidence.append({"label": declaration["file"], "role": role, "sha256": actual_hash})
        if actual_hash != declaration["sha256"]:
            findings.append(
                finding(
                    "LOB.ARTIFACT.HASH_MISMATCH",
                    "artifact",
                    "error",
                    "A task artifact does not match its declared SHA-256.",
                    "Restore the immutable artifact or issue a reviewed replacement record.",
                )
            )
        else:
            raw_by_role[role] = raw

    lobsterout: dict[str, Any] | None = None
    if "lobsterout" in raw_by_role:
        try:
            lobsterout = parse_lobsterout(raw_by_role["lobsterout"])
        except GuardError as error:
            findings.append(
                finding(
                    error.code,
                    "completion",
                    "error",
                    error.message,
                    "Use a version-matched parser profile and a complete artifact.",
                    classification="parse",
                )
            )
        else:
            evaluated.update({"completion", "basis", "projection"})
            metrics["projection"] = {
                "absolute_charge_spilling_percent": lobsterout["absolute_charge_spilling_percent"],
                "absolute_total_spilling_percent": lobsterout["absolute_total_spilling_percent"],
                "fermi_energy_eV": lobsterout["fermi_energy_eV"],
                "projected_band_fraction": lobsterout["projected_band_fraction"],
                "projection_window_max_eV": lobsterout["projection_window_max_eV"],
                "projection_window_min_eV": lobsterout["projection_window_min_eV"],
            }
            if lobsterout["version"] != provider["version"] or lobsterout["dft_program"] != parent_decl["dft_code"]:
                findings.append(
                    finding(
                        "LOB.PROVIDER.OUTPUT_IDENTITY_MISMATCH",
                        "provider",
                        "error",
                        "lobsterout disagrees with the declared provider or DFT parent identity.",
                        "Bind the correct output to its exact execution and parent records.",
                    )
                )
            if lobsterout["fatal_marker"]:
                findings.append(
                    finding(
                        "LOB.COMPLETION.FATAL_MARKER",
                        "completion",
                        "error",
                        "lobsterout contains a fatal marker.",
                        "Diagnose the run and provide a new complete artifact without overwriting evidence.",
                    )
                )
            if not lobsterout["completed"]:
                findings.append(
                    finding(
                        "LOB.COMPLETION.MARKER_MISSING",
                        "completion",
                        "error",
                        "lobsterout lacks the selected profile's completion marker.",
                        "Provide the complete output and verify application completion separately from scheduler state.",
                    )
                )
            if lobsterout["basis_by_element"] != declared_basis:
                findings.append(
                    finding(
                        "LOB.BASIS.MISMATCH",
                        "basis",
                        "error",
                        "The parser-observed basis differs from the declared per-element basis.",
                        "Resolve basis source, element coverage, and orbital selection before interpreting projections.",
                    )
                )
            charge = lobsterout["absolute_charge_spilling_percent"]
            total = lobsterout["absolute_total_spilling_percent"]
            if charge is None or total is None or charge < 0.0 or total < 0.0:
                findings.append(
                    finding(
                        "LOB.PROJECTION.SPILLING_MISSING",
                        "projection",
                        "error",
                        "Absolute charge or total spilling is missing or invalid.",
                        "Use a complete exact-version output and retain both absolute spilling measures.",
                    )
                )
            else:
                if charge > thresholds["max_absolute_charge_spilling_percent"]:
                    findings.append(
                        finding(
                            "LOB.PROJECTION.CHARGE_SPILLING_EXCEEDED",
                            "projection",
                            "error",
                            "Absolute charge spilling exceeds the declared scientific threshold.",
                            "Reassess the basis and parent calculation; do not loosen the threshold after seeing the result.",
                        )
                    )
                if total > thresholds["max_absolute_total_spilling_percent"]:
                    findings.append(
                        finding(
                            "LOB.PROJECTION.TOTAL_SPILLING_EXCEEDED",
                            "projection",
                            "error",
                            "Absolute total spilling exceeds the declared scientific threshold.",
                            "Reassess the basis and parent calculation; preserve the failed evidence.",
                        )
                    )
            band_fraction = lobsterout["projected_band_fraction"]
            window_min = lobsterout["projection_window_min_eV"]
            window_max = lobsterout["projection_window_max_eV"]
            fermi = lobsterout["fermi_energy_eV"]
            if (
                band_fraction is None
                or window_min is None
                or window_max is None
                or fermi is None
                or band_fraction < thresholds["min_projected_band_fraction"]
                or band_fraction > 1.0
                or window_max <= window_min
            ):
                findings.append(
                    finding(
                        "LOB.PROJECTION.INCOMPLETE",
                        "projection",
                        "error",
                        "Projected-band coverage, projection window, or Fermi evidence is incomplete.",
                        "Provide the declared projection population and energy-window evidence before curve analysis.",
                    )
                )

    curve_roles = [role for role in ("cohp", "coop", "dos") if role in TASK_ARTIFACTS[task]]
    if curve_roles:
        evaluated.update({"curve", "consistency"})
    for role in curve_roles:
        raw = raw_by_role.get(role)
        if raw is None:
            continue
        try:
            curve = parse_curve(raw, role)
        except GuardError as error:
            findings.append(
                finding(
                    error.code,
                    "curve" if error.code != "LOB.CURVE.INTEGRAL_INCONSISTENT" else "consistency",
                    "error",
                    error.message,
                    "Use the exact version/task parser profile and preserve explicit curve metadata.",
                    classification="parse",
                )
            )
            continue
        metrics[role] = curve
        if lobsterout is not None:
            fermi = lobsterout["fermi_energy_eV"]
            window_min = lobsterout["projection_window_min_eV"]
            window_max = lobsterout["projection_window_max_eV"]
            if (
                fermi is None
                or abs(curve["fermi_energy_eV"] - fermi) > thresholds["fermi_alignment_abs_tolerance_eV"]
                or window_min is None
                or window_max is None
                or curve["energy_min_eV"] < window_min - thresholds["fermi_alignment_abs_tolerance_eV"]
                or curve["energy_max_eV"] > window_max + thresholds["fermi_alignment_abs_tolerance_eV"]
            ):
                findings.append(
                    finding(
                        "LOB.CURVE.FERMI_ALIGNMENT_FAILED",
                        "consistency",
                        "error",
                        "A curve Fermi reference or energy window is detached from lobsterout projection evidence.",
                        "Align curve and projection references without shifting data after inspection.",
                    )
                )
        if role in {"cohp", "coop"} and curve["maximum_integral_abs_error"] > thresholds["curve_integral_abs_tolerance"]:
            findings.append(
                finding(
                    "LOB.CURVE.INTEGRAL_INCONSISTENT",
                    "consistency",
                    "error",
                    "The supplied integrated curve is inconsistent with trapezoidal integration on its stored grid.",
                    "Verify columns, sign convention, energy grid, and integration semantics.",
                )
            )
        if role == "dos":
            closure = curve["maximum_projection_closure_relative_error"]
            if (
                curve["minimum_total_dos"] < 0.0
                or curve["minimum_projected_sum_dos"] < 0.0
                or closure > thresholds["dos_closure_relative_tolerance"]
            ):
                findings.append(
                    finding(
                        "LOB.DOS.PROJECTION_CLOSURE_FAILED",
                        "consistency",
                        "error",
                        "Projected DOS does not meet non-negativity and declared closure requirements.",
                        "Check selectors, spin channels, normalization, energy grid, and projection completeness.",
                    )
                )

    forbidden = sorted(set(claims) & FORBIDDEN_AUTOMATIC_CLAIMS)
    if forbidden:
        findings.append(
            finding(
                "LOB.CLAIM.AUTOMATIC_CHEMICAL_INTERPRETATION_FORBIDDEN",
                "claim",
                "blocker",
                "The request asks the candidate to automate a chemical conclusion.",
                "Retain technical evidence and route the interpretation to independent expert review.",
            )
        )
    if evidence_class == "real-artifact":
        findings.append(
            finding(
                "LOB.ACTIVATION.REAL_ARTIFACT_VALIDATION_MISSING",
                "claim",
                "blocker",
                "The candidate has no accepted legally reusable real-artifact forward validation.",
                "Complete licensed private integration and reviewed real-artifact tests before promotion.",
            )
        )

    status, exit_value = determine_status(findings)
    report = {
        "contract_name": "lobster-candidate-validation-report",
        "schema_version": "1.0",
        "tool": {"name": "lobster_guard", "version": TOOL_VERSION},
        "operation": "audit",
        "status": status,
        "maturity": "synthetic-validated" if evidence_class == "synthetic-fixture" else "design-only",
        "maximum_claim": "no_positive_claim",
        "task_id": task,
        "evidence_class": evidence_class,
        "provider": {
            "environment_profile_id": provider["environment_profile_id"],
            "software": provider["software"],
            "version": provider["version"],
        },
        "parent": {
            "dft_code": parent_decl["dft_code"],
            "dft_version": parent_decl["dft_version"],
            "record_id": parent_decl["record_id"],
            "structure_fingerprint": parent_decl["structure_fingerprint"],
            "task_id": parent_decl["task_id"],
        },
        "gates": gate_projection(findings, evaluated),
        "findings": sorted_findings(findings),
        "evidence": sorted(evidence, key=lambda item: (item["role"], item["label"])),
        "metrics": metrics,
        "requested_claims": claims,
        "thresholds": thresholds,
        "limitations": [
            "Synthetic parser passage does not establish licensed binary integration or real-artifact maturity.",
            "Projection quality does not itself prove a chemical bond or scientific interpretation.",
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
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output target could not be inspected safely.") from exc


def validate_output_target(
    path: Path,
    metadata: os.stat_result | None,
    tracker: InputTracker,
) -> None:
    if tracker.conflicts(path, metadata):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output aliases a request or evidence input.")
    if metadata is not None and (not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1):
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output must be a single-link regular report file.")


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
            "LOB.INPUT.CONTRACT_INVALID",
            "In-place overwrite is unsupported; publish to a new report path.",
        )
    try:
        payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(
            "utf-8"
        )
    except (TypeError, ValueError) as exc:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The report could not be serialized safely.") from exc
    if not path.name or path.name in {".", ".."}:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output filename is invalid.")
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
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "This host lacks required safe-output support.")
    try:
        parent_path_metadata = parent.lstat()
        if stat.S_ISLNK(parent_path_metadata.st_mode) or not stat.S_ISDIR(parent_path_metadata.st_mode):
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output parent directory is unavailable or unsafe.")
        directory_fd = os.open(
            parent,
            os.O_RDONLY | directory_flag | nofollow | getattr(os, "O_CLOEXEC", 0),
        )
    except GuardError:
        raise
    except OSError as exc:
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output parent directory is unavailable or unsafe.") from exc

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
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output parent identity is unstable.")
        initial = output_metadata(directory_fd, path.name)
        validate_output_target(target, initial, tracker)
        if initial is not None:
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output already exists; choose a new report path.")

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
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "A private atomic output staging file could not be created.")

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
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The staged report identity is invalid.")

        current_parent = parent.lstat()
        if (
            stat.S_ISLNK(current_parent.st_mode)
            or not stat.S_ISDIR(current_parent.st_mode)
            or (current_parent.st_dev, current_parent.st_ino)
            != (parent_fd_metadata.st_dev, parent_fd_metadata.st_ino)
        ):
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output parent changed before installation.")
        current = output_metadata(directory_fd, path.name)
        validate_output_target(target, current, tracker)
        if current is not None:
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The output target appeared during report staging.")
        staged_name_metadata = output_metadata(directory_fd, temporary_name)
        if staged_name_metadata is None or not _same_file_binding(staged_name_metadata, temporary_metadata):
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The staged report path changed before publication.")

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
                "LOB.INPUT.CONTRACT_INVALID",
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
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The published report is not the staged payload.")
        os.fsync(directory_fd)
        os.unlink(temporary_name, dir_fd=directory_fd)
        temporary_name = None
        published_snapshot = output_metadata(directory_fd, path.name)
        if (
            published_snapshot is None
            or not _same_file_binding(published_snapshot, os.fstat(temporary_fd))
            or not _fd_payload_matches(temporary_fd, payload)
        ):
            raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The final report binding is invalid.")
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
                    "LOB.INPUT.CONTRACT_INVALID",
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
                    "LOB.INPUT.CONTRACT_INVALID",
                    "Atomic report rollback failed; output state is indeterminate.",
                ) from rollback_error
        raise GuardError("LOB.INPUT.CONTRACT_INVALID", "The report could not be installed atomically.") from exc
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
    report: dict[str, Any]
    exit_value = EXIT_OK
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
    print(f"{report['status'].upper()}: LOBSTER candidate {args.command}; maximum_claim={report['maximum_claim']}")
    return exit_value


if __name__ == "__main__":
    raise SystemExit(main())
