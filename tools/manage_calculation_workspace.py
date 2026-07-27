#!/usr/bin/env python3
"""Create and verify orderly calculation workspaces and revisioned taskbooks."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any


TOOL_VERSION = "1.1.0"
LAYOUT_VERSION = "1.1"
TASKBOOK_VERSION = "1.1"
INPUT_SET_VERSION = "1.0"
ATTEMPT_VERSION = "1.0"
DIRECTORIES = (
    "00-governance/plans",
    "00-governance/taskbook-revisions",
    "01-structures",
    "02-inputs",
    "03-runs",
    "04-derived",
    "05-figures",
    "06-reports",
    "90-archive",
)
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{1,127}$")
ARTIFACT_SPEC = re.compile(r"^(?P<kind>[a-z][a-z0-9-]{1,63})=(?P<label>.+)$")
REVIEW_MODES = ("off", "silent-update", "milestone-review")
INITIAL_REVIEW_STATES = (
    "not-required",
    "awaiting-request",
    "pending-review",
    "approved",
    "changes-requested",
)
MILESTONE_KINDS = (
    "planning",
    "structure",
    "input",
    "execution",
    "data",
    "figure",
    "report",
)
MILESTONE_ARTIFACT_KINDS = {
    "planning": "workflow-plan",
    "structure": "structure",
    "input": "input-set",
    "execution": "run-record",
    "data": "dataset",
    "figure": "figure",
    "report": "report",
}
ARTIFACT_ROOTS = {
    "workflow-plan": Path("00-governance/plans"),
    "structure": Path("01-structures"),
    "input-set": Path("02-inputs"),
    "run-record": Path("03-runs"),
    "dataset": Path("04-derived"),
    "figure": Path("05-figures"),
    "report": Path("06-reports"),
}
STAGE_STATUSES = (
    "planned",
    "running",
    "pending-review",
    "completed",
    "blocked",
    "failed",
    "abandoned",
)
REVIEW_STATES = ("not-required", "pending-review", "approved", "changes-requested")
ATTEMPT_STATES = (
    "prepared",
    "active",
    "completed",
    "failed",
    "stopped",
    "abandoned",
)
TERMINAL_ATTEMPT_STATES = frozenset(
    {"completed", "failed", "stopped", "abandoned"}
)
ATTEMPT_TRANSITIONS = {
    "prepared": frozenset({"active", "failed", "stopped", "abandoned"}),
    "active": TERMINAL_ATTEMPT_STATES,
}
STAGE_TRANSITIONS = {
    "planned": frozenset(
        {"planned", "running", "pending-review", "blocked", "failed", "abandoned"}
    ),
    "running": frozenset(
        {"running", "pending-review", "completed", "blocked", "failed", "abandoned"}
    ),
    "pending-review": frozenset(
        {"pending-review", "planned", "completed", "blocked", "abandoned"}
    ),
    "blocked": frozenset({"blocked", "planned", "running", "abandoned"}),
    "failed": frozenset({"failed", "planned", "abandoned"}),
    "completed": frozenset({"completed"}),
    "abandoned": frozenset({"abandoned"}),
}


class WorkspaceError(ValueError):
    """A workspace or taskbook invariant was violated."""


def _parse_utc(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WorkspaceError(f"{label}: expected RFC 3339 date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise WorkspaceError(f"{label}: timezone offset is required")
    return parsed


def _safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value):
        raise WorkspaceError(f"{label}: expected a privacy-safe identifier")
    return value


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise WorkspaceError(f"{label}: cannot read {path}: {exc}") from exc
    try:
        text = raw.decode("utf-8", errors="strict")
        data = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, WorkspaceError) as exc:
        raise WorkspaceError(f"{label}: invalid strict UTF-8 JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise WorkspaceError(f"{label}: expected a JSON object")
    return data


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WorkspaceError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _atomic_write(path: Path, raw: bytes, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and path.exists():
        raise WorkspaceError(f"refusing to overwrite immutable file: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        if exclusive and path.exists():
            raise WorkspaceError(f"refusing to overwrite immutable file: {path}")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@contextmanager
def _workspace_lock(root: Path):
    lock_path = root / "00-governance" / ".workspace.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise WorkspaceError(
                "another workspace mutation is in progress; retry after it finishes"
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _paths(root: Path) -> tuple[Path, Path, Path]:
    governance = root / "00-governance"
    return (
        governance / "workspace-manifest.json",
        governance / "taskbook-current.json",
        governance / "taskbook-revisions",
    )


def _validate_workspace_root(root: Path) -> Path:
    resolved = root.resolve()
    if resolved == Path(resolved.anchor):
        raise WorkspaceError("workspace root cannot be a filesystem root")
    return resolved


def _contained_relative(root: Path, label: str, purpose: str) -> tuple[Path, Path]:
    relative = Path(label)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise WorkspaceError(f"{purpose} must be a contained relative path")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise WorkspaceError(f"{purpose} resolves outside the workspace") from exc
    return relative, candidate


def _artifact(root: Path, specification: str) -> dict[str, Any]:
    match = ARTIFACT_SPEC.fullmatch(specification)
    if match is None:
        raise WorkspaceError("--artifact must be KIND=RELATIVE_PATH")
    relative, candidate = _contained_relative(
        root, match.group("label"), "artifact path"
    )
    if not candidate.is_file() or candidate.is_symlink():
        raise WorkspaceError(f"artifact is not a regular non-symlink file: {relative}")
    raw = candidate.read_bytes()
    return {
        "kind": match.group("kind"),
        "label": relative.as_posix(),
        "bytes": len(raw),
        "sha256": _sha256(raw),
    }


def _require_artifact_root(artifact: dict[str, Any]) -> None:
    expected_root = ARTIFACT_ROOTS.get(str(artifact["kind"]))
    if expected_root is None:
        return
    label = Path(str(artifact["label"]))
    try:
        label.relative_to(expected_root)
    except ValueError as exc:
        raise WorkspaceError(
            f"{artifact['kind']} artifact must be under {expected_root.as_posix()}/"
        ) from exc


def _validate_recorded_artifact(
    root: Path,
    artifact: Any,
    label: str,
    *,
    verify_bytes: bool,
) -> dict[str, Any]:
    if not isinstance(artifact, dict):
        raise WorkspaceError(f"{label}: artifact must be an object")
    expected = {"kind", "label", "bytes", "sha256"}
    if set(artifact) != expected:
        raise WorkspaceError(f"{label}: artifact fields differ from the format")
    kind = artifact.get("kind")
    if not isinstance(kind, str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}", kind):
        raise WorkspaceError(f"{label}: invalid artifact kind")
    relative, candidate = _contained_relative(
        root, str(artifact.get("label")), f"{label} artifact label"
    )
    if (
        not isinstance(artifact.get("bytes"), int)
        or isinstance(artifact.get("bytes"), bool)
        or artifact["bytes"] < 0
    ):
        raise WorkspaceError(f"{label}: invalid artifact byte count")
    if not isinstance(artifact.get("sha256"), str) or not re.fullmatch(
        r"[0-9a-f]{64}", artifact["sha256"]
    ):
        raise WorkspaceError(f"{label}: invalid artifact sha256")
    _require_artifact_root(artifact)
    if verify_bytes:
        if not candidate.is_file() or candidate.is_symlink():
            raise WorkspaceError(
                f"{label}: recorded artifact is unavailable: {relative.as_posix()}"
            )
        raw = candidate.read_bytes()
        if len(raw) != artifact["bytes"]:
            raise WorkspaceError(f"{label}: artifact byte count drift")
        if _sha256(raw) != artifact["sha256"]:
            raise WorkspaceError(f"{label}: artifact hash drift")
    return artifact


def _append_taskbook_revision(
    root: Path,
    latest: dict[str, Any],
    latest_raw: bytes,
    *,
    at_utc: str,
    update_kind: str,
    stage_id: str | None,
    summary: str,
    changes: dict[str, Any],
) -> tuple[int, bytes]:
    revision = int(latest["revision"]) + 1
    updated = dict(latest)
    updated.update(
        {
            "revision": revision,
            "previous_revision": {
                "revision": revision - 1,
                "sha256": _sha256(latest_raw),
                "label": f"revision-{revision - 1:06d}.json",
            },
            "updated_utc": at_utc,
            "update": {
                "kind": update_kind,
                "stage_id": stage_id,
                "summary": summary,
            },
            **changes,
        }
    )
    raw = _json_bytes(updated)
    _, current_path, revisions = _paths(root)
    revision_path = revisions / f"revision-{revision:06d}.json"
    _atomic_write(revision_path, raw, exclusive=True)
    _atomic_write(current_path, raw)
    return revision, raw


def _base_taskbook(
    *,
    case_id: str,
    protocol_id: str,
    objective: str,
    review_mode: str,
    selected_utc: str,
) -> dict[str, Any]:
    return {
        "format_name": "calculation-taskbook",
        "format_version": TASKBOOK_VERSION,
        "taskbook_id": f"taskbook-{case_id}-{protocol_id}",
        "case_id": case_id,
        "scientific_protocol_id": protocol_id,
        "objective": objective,
        "revision": 1,
        "previous_revision": None,
        "review_policy": {
            "mode": review_mode,
            "selected_by": "user",
            "selected_utc": selected_utc,
            "scope": "taskbook-pauses-only",
        },
        "initial_execution_review": {
            "state": (
                "awaiting-request"
                if review_mode == "milestone-review"
                else "not-required"
            ),
            "requested_utc": None,
            "decided_utc": None,
            "review_note": None,
            "frozen_artifacts": [],
            "approval_basis": None,
        },
        "updated_utc": selected_utc,
        "update": {
            "kind": "initialized",
            "stage_id": None,
            "summary": "Taskbook initialized from the user-selected review mode.",
        },
        "stages": [],
        "limitations": [
            "The taskbook does not grant execution authorization or scientific acceptance.",
            "The tool records an operator assertion of user review; it does not authenticate a human.",
            "Initial review readiness is separate from scheduler authority and site policy.",
        ],
        "producer": {
            "tool_id": "manage-calculation-workspace",
            "tool_version": TOOL_VERSION,
        },
    }


def init_workspace(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    if root.exists() and any(root.iterdir()):
        raise WorkspaceError("init requires a missing or empty workspace root")
    case_id = _safe_id(args.case_id, "case id")
    protocol_id = _safe_id(args.protocol_id, "protocol id")
    _parse_utc(args.selected_utc, "selected utc")
    if not args.objective.strip():
        raise WorkspaceError("objective cannot be empty")
    root.mkdir(parents=True, exist_ok=True)
    for directory in DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)
    with _workspace_lock(root):
        manifest_path, current_path, revisions = _paths(root)
        manifest = {
            "format_name": "calculation-workspace-manifest",
            "format_version": LAYOUT_VERSION,
            "case_id": case_id,
            "scientific_protocol_id": protocol_id,
            "review_mode": args.review_mode,
            "review_mode_selected_utc": args.selected_utc,
            "directories": list(DIRECTORIES),
            "taskbook_enabled": args.review_mode != "off",
            "taskbook_current": (
                "00-governance/taskbook-current.json"
                if args.review_mode != "off"
                else None
            ),
            "initial_review_required": args.review_mode == "milestone-review",
            "producer": {
                "tool_id": "manage-calculation-workspace",
                "tool_version": TOOL_VERSION,
            },
        }
        _atomic_write(manifest_path, _json_bytes(manifest), exclusive=True)
        taskbook_sha = None
        if args.review_mode != "off":
            taskbook = _base_taskbook(
                case_id=case_id,
                protocol_id=protocol_id,
                objective=args.objective.strip(),
                review_mode=args.review_mode,
                selected_utc=args.selected_utc,
            )
            raw = _json_bytes(taskbook)
            revision_path = revisions / "revision-000001.json"
            _atomic_write(revision_path, raw, exclusive=True)
            _atomic_write(current_path, raw)
            taskbook_sha = _sha256(raw)
    return {
        "status": "initialized",
        "workspace": str(root),
        "review_mode": args.review_mode,
        "taskbook_sha256": taskbook_sha,
        "initial_review_state": (
            "awaiting-request"
            if args.review_mode == "milestone-review"
            else "not-required"
        ),
    }


def _validate_manifest(root: Path) -> dict[str, Any]:
    manifest_path, _, _ = _paths(root)
    manifest = _load_object(manifest_path, "workspace manifest")
    expected = {
        "format_name",
        "format_version",
        "case_id",
        "scientific_protocol_id",
        "review_mode",
        "review_mode_selected_utc",
        "directories",
        "taskbook_enabled",
        "taskbook_current",
        "initial_review_required",
        "producer",
    }
    if set(manifest) != expected:
        raise WorkspaceError(
            f"workspace manifest fields differ from format {LAYOUT_VERSION}"
        )
    if manifest["format_name"] != "calculation-workspace-manifest":
        raise WorkspaceError("workspace manifest format_name mismatch")
    if manifest["format_version"] != LAYOUT_VERSION:
        raise WorkspaceError("workspace manifest version mismatch")
    _safe_id(manifest["case_id"], "manifest case id")
    _safe_id(manifest["scientific_protocol_id"], "manifest protocol id")
    if manifest["review_mode"] not in REVIEW_MODES:
        raise WorkspaceError("workspace manifest review mode is invalid")
    _parse_utc(manifest["review_mode_selected_utc"], "review mode selected utc")
    if manifest["directories"] != list(DIRECTORIES):
        raise WorkspaceError("workspace directory inventory mismatch")
    for directory in DIRECTORIES:
        candidate = root / directory
        if not candidate.is_dir() or candidate.is_symlink():
            raise WorkspaceError(f"required workspace directory is missing: {directory}")
    enabled = manifest["review_mode"] != "off"
    if manifest["taskbook_enabled"] is not enabled:
        raise WorkspaceError("taskbook_enabled contradicts review mode")
    expected_current = "00-governance/taskbook-current.json" if enabled else None
    if manifest["taskbook_current"] != expected_current:
        raise WorkspaceError("taskbook_current contradicts review mode")
    if manifest["initial_review_required"] is not (
        manifest["review_mode"] == "milestone-review"
    ):
        raise WorkspaceError("initial_review_required contradicts review mode")
    return manifest


def _revision_files(revisions: Path) -> list[Path]:
    paths = sorted(revisions.glob("revision-*.json"))
    expected = [
        revisions / f"revision-{index:06d}.json"
        for index in range(1, len(paths) + 1)
    ]
    if paths != expected:
        raise WorkspaceError("taskbook revision filenames are not contiguous")
    return paths


def _validate_taskbook_chain(
    root: Path, manifest: dict[str, Any], *, verify_artifacts: bool
) -> tuple[dict[str, Any], bytes]:
    _, current_path, revisions = _paths(root)
    paths = _revision_files(revisions)
    if not paths:
        raise WorkspaceError("taskbook has no immutable revisions")
    previous_raw: bytes | None = None
    previous_updated: datetime | None = None
    previous_data: dict[str, Any] | None = None
    latest: dict[str, Any] | None = None
    latest_raw = b""
    for index, path in enumerate(paths, 1):
        raw = path.read_bytes()
        data = _load_object(path, path.name)
        expected_fields = {
            "format_name",
            "format_version",
            "taskbook_id",
            "case_id",
            "scientific_protocol_id",
            "objective",
            "revision",
            "previous_revision",
            "review_policy",
            "initial_execution_review",
            "updated_utc",
            "update",
            "stages",
            "limitations",
            "producer",
        }
        if set(data) != expected_fields:
            raise WorkspaceError(f"{path.name}: taskbook fields differ from format")
        if data.get("format_name") != "calculation-taskbook":
            raise WorkspaceError(f"{path.name}: format_name mismatch")
        if data.get("format_version") != TASKBOOK_VERSION:
            raise WorkspaceError(f"{path.name}: format version mismatch")
        if data.get("revision") != index:
            raise WorkspaceError(f"{path.name}: revision number mismatch")
        if data.get("case_id") != manifest["case_id"]:
            raise WorkspaceError(f"{path.name}: case id mismatch")
        if data.get("scientific_protocol_id") != manifest["scientific_protocol_id"]:
            raise WorkspaceError(f"{path.name}: protocol id mismatch")
        policy = data.get("review_policy")
        if (
            not isinstance(policy, dict)
            or set(policy) != {"mode", "selected_by", "selected_utc", "scope"}
            or policy.get("mode") != manifest["review_mode"]
            or policy.get("selected_by") != "user"
            or policy.get("selected_utc") != manifest["review_mode_selected_utc"]
            or policy.get("scope") != "taskbook-pauses-only"
        ):
            raise WorkspaceError(f"{path.name}: review policy mismatch")
        _parse_utc(str(policy["selected_utc"]), f"{path.name} selected utc")
        review = data.get("initial_execution_review")
        if not isinstance(review, dict) or set(review) != {
            "state",
            "requested_utc",
            "decided_utc",
            "review_note",
            "frozen_artifacts",
            "approval_basis",
        }:
            raise WorkspaceError(f"{path.name}: invalid initial execution review")
        if review.get("state") not in INITIAL_REVIEW_STATES:
            raise WorkspaceError(f"{path.name}: invalid initial review state")
        requested_utc: datetime | None = None
        if manifest["review_mode"] != "milestone-review":
            if review != {
                "state": "not-required",
                "requested_utc": None,
                "decided_utc": None,
                "review_note": None,
                "frozen_artifacts": [],
                "approval_basis": None,
            }:
                raise WorkspaceError(
                    f"{path.name}: non-review mode cannot claim initial review"
                )
        else:
            if review["state"] == "not-required":
                raise WorkspaceError(
                    f"{path.name}: milestone review cannot bypass initial review"
                )
            frozen = review.get("frozen_artifacts")
            if not isinstance(frozen, list):
                raise WorkspaceError(f"{path.name}: frozen_artifacts must be an array")
            frozen_kinds: set[str] = set()
            frozen_labels: set[str] = set()
            for artifact in frozen:
                checked = _validate_recorded_artifact(
                    root,
                    artifact,
                    f"{path.name} initial review",
                    verify_bytes=verify_artifacts,
                )
                frozen_kinds.add(checked["kind"])
                if checked["label"] in frozen_labels:
                    raise WorkspaceError(
                        f"{path.name}: duplicate initial-review artifact label"
                    )
                frozen_labels.add(checked["label"])
            if review["state"] in {
                "pending-review",
                "approved",
                "changes-requested",
            }:
                if frozen_kinds != {"workflow-plan", "input-set"}:
                    raise WorkspaceError(
                        f"{path.name}: initial review requires one workflow-plan "
                        "and one input-set"
                    )
                requested_utc = _parse_utc(
                    str(review.get("requested_utc")),
                    f"{path.name} initial review requested utc",
                )
            else:
                requested_utc = None
            if review["state"] == "awaiting-request" and any(
                review.get(field) is not None
                for field in ("requested_utc", "decided_utc", "review_note")
            ):
                raise WorkspaceError(
                    f"{path.name}: awaiting review request carries decision data"
                )
            basis = review.get("approval_basis")
            if review["state"] == "approved":
                if (
                    not isinstance(review.get("review_note"), str)
                    or not review["review_note"].strip()
                ):
                    raise WorkspaceError(
                        f"{path.name}: approved initial review lacks review note"
                    )
                decided_utc = _parse_utc(
                    str(review.get("decided_utc")),
                    f"{path.name} initial review decided utc",
                )
                if requested_utc is None or decided_utc < requested_utc:
                    raise WorkspaceError(
                        f"{path.name}: initial decision precedes its request"
                    )
                if (
                    not isinstance(basis, dict)
                    or set(basis) != {"revision", "sha256", "label"}
                    or not isinstance(basis.get("revision"), int)
                    or basis["revision"] >= index
                    or not re.fullmatch(r"[0-9a-f]{64}", str(basis.get("sha256")))
                    or basis.get("label")
                    != f"revision-{basis.get('revision', 0):06d}.json"
                ):
                    raise WorkspaceError(
                        f"{path.name}: invalid initial review approval basis"
                    )
                basis_path = revisions / basis["label"]
                if not basis_path.is_file():
                    raise WorkspaceError(
                        f"{path.name}: initial review basis revision is missing"
                    )
                if _sha256(basis_path.read_bytes()) != basis["sha256"]:
                    raise WorkspaceError(
                        f"{path.name}: initial review basis hash mismatch"
                    )
                basis_data = _load_object(
                    basis_path, f"{path.name} initial review basis"
                )
                basis_review = basis_data.get("initial_execution_review")
                if (
                    basis_data.get("revision") != basis["revision"]
                    or not isinstance(basis_review, dict)
                    or basis_review.get("state") != "pending-review"
                    or basis_review.get("frozen_artifacts")
                    != review["frozen_artifacts"]
                ):
                    raise WorkspaceError(
                        f"{path.name}: approval basis is not the matching "
                        "pending-review revision"
                    )
            elif basis is not None:
                raise WorkspaceError(
                    f"{path.name}: non-approved initial review carries approval basis"
                )
            if review["state"] == "changes-requested":
                if (
                    not isinstance(review.get("review_note"), str)
                    or not review["review_note"].strip()
                ):
                    raise WorkspaceError(
                        f"{path.name}: requested changes lack a review note"
                    )
                decided_utc = _parse_utc(
                    str(review.get("decided_utc")),
                    f"{path.name} initial review decided utc",
                )
                if requested_utc is None or decided_utc < requested_utc:
                    raise WorkspaceError(
                        f"{path.name}: requested-changes decision precedes request"
                    )
        if previous_data is not None:
            previous_review = previous_data.get("initial_execution_review")
            previous_state = (
                previous_review.get("state")
                if isinstance(previous_review, dict)
                else None
            )
            allowed_review_transitions = {
                "not-required": {"not-required"},
                "awaiting-request": {"awaiting-request", "pending-review"},
                "pending-review": {
                    "pending-review",
                    "approved",
                    "changes-requested",
                },
                "approved": {"approved", "pending-review"},
                "changes-requested": {"changes-requested", "pending-review"},
            }
            if review["state"] not in allowed_review_transitions.get(
                str(previous_state), set()
            ):
                raise WorkspaceError(
                    f"{path.name}: invalid initial review state transition"
                )
        updated = _parse_utc(str(data.get("updated_utc")), f"{path.name} updated utc")
        if requested_utc is not None and requested_utc > updated:
            raise WorkspaceError(
                f"{path.name}: initial review request exceeds revision update time"
            )
        if review.get("decided_utc") is not None:
            if _parse_utc(
                str(review["decided_utc"]),
                f"{path.name} initial review decided utc",
            ) > updated:
                raise WorkspaceError(
                    f"{path.name}: initial review decision exceeds update time"
                )
        if previous_updated is not None and updated < previous_updated:
            raise WorkspaceError(f"{path.name}: update time moved backward")
        expected_previous = (
            None
            if previous_raw is None
            else {
                "revision": index - 1,
                "sha256": _sha256(previous_raw),
                "label": f"revision-{index - 1:06d}.json",
            }
        )
        if data.get("previous_revision") != expected_previous:
            raise WorkspaceError(f"{path.name}: previous revision reference mismatch")
        stages = data.get("stages")
        if not isinstance(stages, list):
            raise WorkspaceError(f"{path.name}: stages must be an array")
        seen: set[str] = set()
        previous_stages = (
            {
                stage["stage_id"]: stage
                for stage in previous_data.get("stages", [])
                if isinstance(stage, dict) and "stage_id" in stage
            }
            if previous_data is not None
            else {}
        )
        for stage in stages:
            if not isinstance(stage, dict):
                raise WorkspaceError(f"{path.name}: stage must be an object")
            if set(stage) != {
                "stage_id",
                "title",
                "milestone_kind",
                "status",
                "review_state",
                "updated_utc",
                "summary",
                "next_action",
                "review_note",
                "artifacts",
            }:
                raise WorkspaceError(f"{path.name}: stage fields differ from format")
            stage_id = _safe_id(str(stage.get("stage_id")), "stage id")
            if stage_id in seen:
                raise WorkspaceError(f"{path.name}: duplicate stage id {stage_id}")
            seen.add(stage_id)
            if stage.get("status") not in STAGE_STATUSES:
                raise WorkspaceError(f"{path.name}: invalid stage status")
            if stage.get("milestone_kind") not in MILESTONE_KINDS:
                raise WorkspaceError(f"{path.name}: invalid milestone kind")
            if stage.get("review_state") not in REVIEW_STATES:
                raise WorkspaceError(f"{path.name}: invalid review state")
            if not isinstance(stage.get("title"), str) or not stage["title"].strip():
                raise WorkspaceError(f"{path.name}: stage title cannot be empty")
            if not isinstance(stage.get("summary"), str) or not stage["summary"].strip():
                raise WorkspaceError(f"{path.name}: stage summary cannot be empty")
            if (
                not isinstance(stage.get("next_action"), str)
                or not stage["next_action"].strip()
            ):
                raise WorkspaceError(f"{path.name}: stage next_action cannot be empty")
            stage_updated = _parse_utc(
                str(stage.get("updated_utc")), f"{path.name} stage updated utc"
            )
            if stage_updated > updated:
                raise WorkspaceError(
                    f"{path.name}: stage update time exceeds revision update time"
                )
            previous_stage = previous_stages.get(stage_id)
            if previous_stage is not None:
                if stage["title"] != previous_stage.get("title"):
                    raise WorkspaceError(f"{path.name}: stage title is immutable")
                if stage["milestone_kind"] != previous_stage.get("milestone_kind"):
                    raise WorkspaceError(
                        f"{path.name}: stage milestone kind is immutable"
                    )
                if stage["status"] not in STAGE_TRANSITIONS[
                    str(previous_stage.get("status"))
                ]:
                    raise WorkspaceError(f"{path.name}: invalid stage state transition")
            if manifest["review_mode"] == "silent-update" and stage.get(
                "review_state"
            ) != "not-required":
                raise WorkspaceError(f"{path.name}: silent mode cannot claim review")
            if (
                manifest["review_mode"] == "milestone-review"
                and stage.get("status") == "completed"
                and stage.get("review_state") != "approved"
            ):
                raise WorkspaceError(
                    f"{path.name}: completed reviewed milestone lacks approval"
                )
            if (
                manifest["review_mode"] == "milestone-review"
                and stage.get("status") == "pending-review"
                and stage.get("review_state") != "pending-review"
            ):
                raise WorkspaceError(
                    f"{path.name}: pending milestone lacks pending review state"
                )
            if (
                manifest["review_mode"] == "milestone-review"
                and stage.get("review_state") == "approved"
                and stage.get("status") != "completed"
            ):
                raise WorkspaceError(
                    f"{path.name}: approved milestone is not completed"
                )
            artifacts = stage.get("artifacts")
            if not isinstance(artifacts, list):
                raise WorkspaceError(f"{path.name}: stage artifacts must be an array")
            artifact_kinds: set[str] = set()
            artifact_labels: set[str] = set()
            for artifact in artifacts:
                checked = _validate_recorded_artifact(
                    root,
                    artifact,
                    f"{path.name} stage {stage_id}",
                    verify_bytes=verify_artifacts,
                )
                artifact_kinds.add(checked["kind"])
                if checked["label"] in artifact_labels:
                    raise WorkspaceError(
                        f"{path.name}: duplicate stage artifact label"
                    )
                artifact_labels.add(checked["label"])
            if stage["status"] in {"pending-review", "completed"}:
                required_kind = MILESTONE_ARTIFACT_KINDS[stage["milestone_kind"]]
                if required_kind not in artifact_kinds:
                    raise WorkspaceError(
                        f"{path.name}: {stage['milestone_kind']} milestone requires "
                        f"a {required_kind} artifact"
                    )
        previous_raw = raw
        previous_updated = updated
        previous_data = data
        latest = data
        latest_raw = raw
    if current_path.read_bytes() != latest_raw:
        raise WorkspaceError("taskbook-current.json is not the exact latest revision")
    assert latest is not None
    return latest, latest_raw


def update_taskbook(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    with _workspace_lock(root):
        manifest = _validate_manifest(root)
        if manifest["review_mode"] == "off":
            raise WorkspaceError("taskbook updates are disabled for review mode off")
        latest, latest_raw = _validate_taskbook_chain(
            root, manifest, verify_artifacts=True
        )
        if (
            latest["initial_execution_review"]["state"] == "pending-review"
        ):
            raise WorkspaceError(
                "initial review is already pending; record a decision first"
            )
        _safe_id(args.stage_id, "stage id")
        at_utc = _parse_utc(args.at_utc, "update utc")
        if at_utc < _parse_utc(latest["updated_utc"], "latest updated utc"):
            raise WorkspaceError("update time cannot precede the latest revision")
        if (
            not args.stage_title.strip()
            or not args.summary.strip()
            or not args.next_action.strip()
        ):
            raise WorkspaceError(
                "stage title, summary, and next action cannot be empty"
            )
        mode = manifest["review_mode"]
        if mode == "silent-update" and args.review_state != "not-required":
            raise WorkspaceError("silent-update requires review-state not-required")
        if mode == "milestone-review":
            if args.stage_status == "completed" and args.review_state != "approved":
                raise WorkspaceError("completed reviewed milestone requires approved")
            if (
                args.stage_status == "pending-review"
                and args.review_state != "pending-review"
            ):
                raise WorkspaceError(
                    "pending reviewed milestone requires pending-review"
                )
            if (
                args.review_state == "approved"
                and args.stage_status != "completed"
            ):
                raise WorkspaceError(
                    "approved reviewed milestone must be completed"
                )
            if args.review_state == "approved" and not args.review_note:
                raise WorkspaceError("approved review requires --review-note")
            if (
                args.milestone_kind in {"execution", "data", "figure", "report"}
                and args.stage_status in {"running", "completed"}
                and latest["initial_execution_review"]["state"] != "approved"
            ):
                raise WorkspaceError(
                    "initial execution review is not approved for this milestone"
                )
        artifacts = [_artifact(root, value) for value in args.artifact]
        for artifact in artifacts:
            _require_artifact_root(artifact)
        stages = [dict(stage) for stage in latest["stages"]]
        recorded_by_label = {
            item["label"]: item
            for recorded_stage in stages
            for item in recorded_stage.get("artifacts", [])
        }
        for item in artifacts:
            previous = recorded_by_label.get(item["label"])
            if previous is not None and previous != item:
                raise WorkspaceError(
                    "recorded artifact labels are immutable; write changed bytes "
                    "or a changed artifact kind under a new relative label"
                )
        stage = next(
            (
                candidate
                for candidate in stages
                if candidate["stage_id"] == args.stage_id
            ),
            None,
        )
        if stage is None:
            if mode == "milestone-review" and args.review_state == "approved":
                raise WorkspaceError(
                    "a reviewed milestone must first be recorded pending-review"
                )
            stage = {
                "stage_id": args.stage_id,
                "title": args.stage_title.strip(),
                "milestone_kind": args.milestone_kind,
                "status": args.stage_status,
                "review_state": args.review_state,
                "updated_utc": args.at_utc,
                "summary": args.summary.strip(),
                "next_action": args.next_action.strip(),
                "review_note": args.review_note,
                "artifacts": artifacts,
            }
            stages.append(stage)
        else:
            if stage["title"] != args.stage_title.strip():
                raise WorkspaceError("stage title is immutable")
            if stage["milestone_kind"] != args.milestone_kind:
                raise WorkspaceError("stage milestone kind is immutable")
            if args.stage_status not in STAGE_TRANSITIONS[stage["status"]]:
                raise WorkspaceError(
                    f"invalid stage transition: {stage['status']} -> "
                    f"{args.stage_status}"
                )
            if stage["review_state"] == "approved" and args.review_state != "approved":
                raise WorkspaceError("approved stage review cannot be downgraded")
            if (
                mode == "milestone-review"
                and args.review_state == "approved"
                and stage["review_state"] != "pending-review"
            ):
                raise WorkspaceError(
                    "milestone approval requires an earlier pending-review revision"
                )
            combined = {item["label"]: item for item in stage.get("artifacts", [])}
            for item in artifacts:
                combined[item["label"]] = item
            stage.update(
                {
                    "status": args.stage_status,
                    "review_state": args.review_state,
                    "updated_utc": args.at_utc,
                    "summary": args.summary.strip(),
                    "next_action": args.next_action.strip(),
                    "review_note": args.review_note,
                    "artifacts": sorted(
                        combined.values(),
                        key=lambda item: (item["kind"], item["label"]),
                    ),
                }
            )
        required_kind = MILESTONE_ARTIFACT_KINDS[args.milestone_kind]
        if args.stage_status in {"pending-review", "completed"} and not any(
            item["kind"] == required_kind for item in stage["artifacts"]
        ):
            raise WorkspaceError(
                f"{args.milestone_kind} milestone requires a "
                f"{required_kind} artifact"
            )
        revision, raw = _append_taskbook_revision(
            root,
            latest,
            latest_raw,
            at_utc=args.at_utc,
            update_kind="stage-update",
            stage_id=args.stage_id,
            summary=args.summary.strip(),
            changes={
                "stages": sorted(stages, key=lambda item: item["stage_id"])
            },
        )
    return {
        "status": "updated",
        "workspace": str(root),
        "revision": revision,
        "taskbook_sha256": _sha256(raw),
        "review_state": args.review_state,
        "pause_required": (
            mode == "milestone-review" and args.review_state == "pending-review"
        ),
    }


def request_initial_review(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    with _workspace_lock(root):
        manifest = _validate_manifest(root)
        if manifest["review_mode"] != "milestone-review":
            raise WorkspaceError(
                "initial review requests require milestone-review mode"
            )
        latest, latest_raw = _validate_taskbook_chain(
            root, manifest, verify_artifacts=True
        )
        if latest["initial_execution_review"]["state"] == "pending-review":
            raise WorkspaceError(
                "initial review is already pending; record a decision first"
            )
        at_utc = _parse_utc(args.at_utc, "initial review request utc")
        if at_utc < _parse_utc(latest["updated_utc"], "latest updated utc"):
            raise WorkspaceError("request time cannot precede the latest revision")
        if not args.summary.strip():
            raise WorkspaceError("initial review summary cannot be empty")
        workflow_plan = _artifact(
            root, f"workflow-plan={args.workflow_plan}"
        )
        input_set, _ = _load_input_set(root, Path(args.input_set))
        input_set_artifact = _artifact(root, f"input-set={args.input_set}")
        for artifact in (workflow_plan, input_set_artifact):
            _require_artifact_root(artifact)
        review = {
            "state": "pending-review",
            "requested_utc": args.at_utc,
            "decided_utc": None,
            "review_note": None,
            "frozen_artifacts": sorted(
                [workflow_plan, input_set_artifact],
                key=lambda item: (item["kind"], item["label"]),
            ),
            "approval_basis": None,
        }
        revision, raw = _append_taskbook_revision(
            root,
            latest,
            latest_raw,
            at_utc=args.at_utc,
            update_kind="initial-review-request",
            stage_id=None,
            summary=args.summary.strip(),
            changes={"initial_execution_review": review},
        )
    return {
        "status": "pending-review",
        "workspace": str(root),
        "revision": revision,
        "taskbook_sha256": _sha256(raw),
        "input_set_id": input_set["input_set_id"],
        "pause_required": True,
        "execution_review_ready": False,
    }


def decide_initial_review(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    with _workspace_lock(root):
        manifest = _validate_manifest(root)
        if manifest["review_mode"] != "milestone-review":
            raise WorkspaceError(
                "initial review decisions require milestone-review mode"
            )
        latest, latest_raw = _validate_taskbook_chain(
            root, manifest, verify_artifacts=True
        )
        latest_sha = _sha256(latest_raw)
        if args.expected_taskbook_sha256 != latest_sha:
            raise WorkspaceError(
                "stale initial review decision: expected taskbook hash differs "
                "from the current immutable revision"
            )
        review = latest["initial_execution_review"]
        if review["state"] != "pending-review":
            raise WorkspaceError("initial review is not pending")
        at_utc = _parse_utc(args.at_utc, "initial review decision utc")
        if at_utc < _parse_utc(latest["updated_utc"], "latest updated utc"):
            raise WorkspaceError("decision time cannot precede the latest revision")
        if not args.review_note.strip():
            raise WorkspaceError("initial review decision requires a review note")
        decided = dict(review)
        decided.update(
            {
                "state": args.decision,
                "decided_utc": args.at_utc,
                "review_note": args.review_note.strip(),
                "approval_basis": (
                    {
                        "revision": latest["revision"],
                        "sha256": latest_sha,
                        "label": f"revision-{latest['revision']:06d}.json",
                    }
                    if args.decision == "approved"
                    else None
                ),
            }
        )
        summary = (
            "Initial execution review approved for the frozen plan and input set."
            if args.decision == "approved"
            else "Initial execution review returned for changes."
        )
        revision, raw = _append_taskbook_revision(
            root,
            latest,
            latest_raw,
            at_utc=args.at_utc,
            update_kind="initial-review-decision",
            stage_id=None,
            summary=summary,
            changes={"initial_execution_review": decided},
        )
    return {
        "status": args.decision,
        "workspace": str(root),
        "revision": revision,
        "taskbook_sha256": _sha256(raw),
        "pause_required": args.decision != "approved",
        "execution_review_ready": args.decision == "approved",
    }


def _input_set_path(root: Path, stage_id: str, input_set_id: str) -> Path:
    return root / "02-inputs" / stage_id / input_set_id / "input-set.json"


def _load_input_set(
    root: Path, relative_path: Path
) -> tuple[dict[str, Any], bytes]:
    relative, path = _contained_relative(
        root, relative_path.as_posix(), "input-set path"
    )
    if len(relative.parts) != 4 or relative.parts[0] != "02-inputs":
        raise WorkspaceError(
            "input-set path must be 02-inputs/<stage-id>/<input-set-id>/input-set.json"
        )
    if relative.name != "input-set.json":
        raise WorkspaceError("input-set path must end with input-set.json")
    data = _load_object(path, "input set")
    expected = {
        "format_name",
        "format_version",
        "case_id",
        "scientific_protocol_id",
        "stage_id",
        "input_set_id",
        "engine_id",
        "created_utc",
        "files",
        "producer",
    }
    if set(data) != expected:
        raise WorkspaceError("input-set fields differ from format 1.0")
    if (
        data["format_name"] != "calculation-input-set"
        or data["format_version"] != INPUT_SET_VERSION
    ):
        raise WorkspaceError("input-set format mismatch")
    workspace_manifest = _validate_manifest(root)
    if (
        data["case_id"] != workspace_manifest["case_id"]
        or data["scientific_protocol_id"]
        != workspace_manifest["scientific_protocol_id"]
    ):
        raise WorkspaceError("input-set case or protocol identity mismatch")
    stage_id = _safe_id(str(data["stage_id"]), "input-set stage id")
    input_set_id = _safe_id(str(data["input_set_id"]), "input-set id")
    _safe_id(str(data["engine_id"]), "input-set engine id")
    if relative.parts[1:3] != (stage_id, input_set_id):
        raise WorkspaceError("input-set path does not match its identities")
    _parse_utc(str(data["created_utc"]), "input-set created utc")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise WorkspaceError("input-set must contain at least one input file")
    labels: set[str] = set()
    input_root = relative.parent
    for item in files:
        checked = _validate_recorded_artifact(
            root, item, "input set", verify_bytes=True
        )
        file_label = Path(checked["label"])
        try:
            tail = file_label.relative_to(input_root)
        except ValueError as exc:
            raise WorkspaceError(
                "input-set files must be stored beside their input-set manifest"
            ) from exc
        if not tail.parts or tail.parts[0] == "00-attempt":
            raise WorkspaceError("input-set file uses a reserved relative path")
        if checked["label"] in labels:
            raise WorkspaceError("input-set contains a duplicate file label")
        labels.add(checked["label"])
    return data, path.read_bytes()


def create_input_set(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    with _workspace_lock(root):
        manifest = _validate_manifest(root)
        stage_id = _safe_id(args.stage_id, "stage id")
        input_set_id = _safe_id(args.input_set_id, "input-set id")
        engine_id = _safe_id(args.engine_id, "engine id")
        _parse_utc(args.at_utc, "input-set created utc")
        target = _input_set_path(root, stage_id, input_set_id)
        input_root = target.parent.relative_to(root)
        files = [_artifact(root, value) for value in args.input]
        if not files:
            raise WorkspaceError("input-set requires at least one --input")
        labels: set[str] = set()
        for item in files:
            label = Path(item["label"])
            try:
                tail = label.relative_to(input_root)
            except ValueError as exc:
                raise WorkspaceError(
                    f"input file must be under {input_root.as_posix()}/"
                ) from exc
            if not tail.parts or tail.parts[0] == "00-attempt":
                raise WorkspaceError("input file uses a reserved relative path")
            if item["label"] in labels:
                raise WorkspaceError("duplicate input file label")
            labels.add(item["label"])
        value = {
            "format_name": "calculation-input-set",
            "format_version": INPUT_SET_VERSION,
            "case_id": manifest["case_id"],
            "scientific_protocol_id": manifest["scientific_protocol_id"],
            "stage_id": stage_id,
            "input_set_id": input_set_id,
            "engine_id": engine_id,
            "created_utc": args.at_utc,
            "files": sorted(files, key=lambda item: (item["kind"], item["label"])),
            "producer": {
                "tool_id": "manage-calculation-workspace",
                "tool_version": TOOL_VERSION,
            },
        }
        raw = _json_bytes(value)
        _atomic_write(target, raw, exclusive=True)
    return {
        "status": "created",
        "workspace": str(root),
        "input_set": target.relative_to(root).as_posix(),
        "input_set_sha256": _sha256(raw),
        "file_count": len(files),
    }


def _attempt_root(root: Path, stage_id: str, attempt_id: str) -> Path:
    return root / "03-runs" / stage_id / attempt_id


def _initial_review_basis(
    root: Path,
    manifest: dict[str, Any],
    input_set_artifact: dict[str, Any],
) -> dict[str, Any]:
    if manifest["review_mode"] in {"off", "silent-update"}:
        return {
            "mode": manifest["review_mode"],
            "state": "not-required",
            "taskbook_revision": None,
            "taskbook_sha256": None,
            "taskbook_label": None,
        }
    latest, raw = _validate_taskbook_chain(root, manifest, verify_artifacts=True)
    review = latest["initial_execution_review"]
    if review["state"] != "approved":
        raise WorkspaceError(
            "cannot prepare an executable attempt before initial review approval"
        )
    approved_input = next(
        (
            artifact
            for artifact in review["frozen_artifacts"]
            if artifact["kind"] == "input-set"
        ),
        None,
    )
    if approved_input != input_set_artifact:
        raise WorkspaceError(
            "attempt input-set bytes differ from the approved initial review"
        )
    return {
        "mode": "milestone-review",
        "state": "approved",
        "taskbook_revision": latest["revision"],
        "taskbook_sha256": _sha256(raw),
        "taskbook_label": f"00-governance/taskbook-revisions/"
        f"revision-{latest['revision']:06d}.json",
    }


def init_attempt(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    with _workspace_lock(root):
        manifest = _validate_manifest(root)
        stage_id = _safe_id(args.stage_id, "stage id")
        attempt_id = _safe_id(args.attempt_id, "attempt id")
        engine_id = _safe_id(args.engine_id, "engine id")
        _parse_utc(args.at_utc, "attempt created utc")
        input_set, _ = _load_input_set(root, Path(args.input_set))
        if input_set["stage_id"] != stage_id:
            raise WorkspaceError("attempt stage does not match input-set stage")
        if input_set["engine_id"] != engine_id:
            raise WorkspaceError("attempt engine does not match input-set engine")
        input_set_artifact = _artifact(root, f"input-set={args.input_set}")
        review_basis = _initial_review_basis(
            root, manifest, input_set_artifact
        )
        attempt_root = _attempt_root(root, stage_id, attempt_id)
        if attempt_root.exists():
            raise WorkspaceError("attempt directory already exists")
        attempt_root.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{attempt_id}.", dir=attempt_root.parent)
        )
        try:
            materialized: list[dict[str, Any]] = []
            input_root = _input_set_path(
                root, stage_id, input_set["input_set_id"]
            ).parent.relative_to(root)
            for item in input_set["files"]:
                tail = Path(item["label"]).relative_to(input_root)
                destination = temporary / tail
                source = root / item["label"]
                raw = source.read_bytes()
                if len(raw) != item["bytes"] or _sha256(raw) != item["sha256"]:
                    raise WorkspaceError(
                        f"input changed while materializing: {item['label']}"
                    )
                _atomic_write(destination, raw, exclusive=True)
                materialized.append(
                    {
                        "kind": item["kind"],
                        "source_label": item["label"],
                        "materialized_label": tail.as_posix(),
                        "bytes": item["bytes"],
                        "sha256": item["sha256"],
                    }
                )
            attempt_manifest = {
                "format_name": "calculation-attempt",
                "format_version": ATTEMPT_VERSION,
                "case_id": manifest["case_id"],
                "scientific_protocol_id": manifest["scientific_protocol_id"],
                "stage_id": stage_id,
                "attempt_id": attempt_id,
                "engine_id": engine_id,
                "created_utc": args.at_utc,
                "input_set": input_set_artifact,
                "materialized_inputs": sorted(
                    materialized, key=lambda item: item["materialized_label"]
                ),
                "initial_review_basis": review_basis,
                "limitations": [
                    "Review readiness does not grant scheduler or execution authority.",
                    "Attempt state does not establish numerical or scientific validity.",
                ],
                "producer": {
                    "tool_id": "manage-calculation-workspace",
                    "tool_version": TOOL_VERSION,
                },
            }
            governance = temporary / "00-attempt"
            manifest_raw = _json_bytes(attempt_manifest)
            _atomic_write(
                governance / "attempt-manifest.json",
                manifest_raw,
                exclusive=True,
            )
            event = {
                "format_name": "calculation-attempt-event",
                "format_version": ATTEMPT_VERSION,
                "attempt_id": attempt_id,
                "attempt_manifest_sha256": _sha256(manifest_raw),
                "sequence": 1,
                "previous_event": None,
                "state": "prepared",
                "at_utc": args.at_utc,
                "summary": args.summary.strip(),
                "artifacts": [],
                "producer": {
                    "tool_id": "manage-calculation-workspace",
                    "tool_version": TOOL_VERSION,
                },
            }
            if not event["summary"]:
                raise WorkspaceError("attempt summary cannot be empty")
            _atomic_write(
                governance / "events" / "event-000001.json",
                _json_bytes(event),
                exclusive=True,
            )
            os.replace(temporary, attempt_root)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    return {
        "status": "prepared",
        "workspace": str(root),
        "attempt": attempt_root.relative_to(root).as_posix(),
        "input_set_sha256": input_set_artifact["sha256"],
        "materialized_file_count": len(input_set["files"]),
        "initial_review_state": review_basis["state"],
    }


def _event_paths(attempt_root: Path) -> list[Path]:
    events = attempt_root / "00-attempt" / "events"
    paths = sorted(events.glob("event-*.json"))
    expected = [
        events / f"event-{index:06d}.json"
        for index in range(1, len(paths) + 1)
    ]
    if paths != expected:
        raise WorkspaceError("attempt event filenames are not contiguous")
    return paths


def _validate_attempt(
    root: Path, attempt_root: Path, *, verify_artifacts: bool
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    manifest_path = attempt_root / "00-attempt" / "attempt-manifest.json"
    attempt = _load_object(manifest_path, "attempt manifest")
    attempt_raw = manifest_path.read_bytes()
    expected = {
        "format_name",
        "format_version",
        "case_id",
        "scientific_protocol_id",
        "stage_id",
        "attempt_id",
        "engine_id",
        "created_utc",
        "input_set",
        "materialized_inputs",
        "initial_review_basis",
        "limitations",
        "producer",
    }
    if set(attempt) != expected:
        raise WorkspaceError("attempt manifest fields differ from format 1.0")
    if (
        attempt["format_name"] != "calculation-attempt"
        or attempt["format_version"] != ATTEMPT_VERSION
    ):
        raise WorkspaceError("attempt manifest format mismatch")
    workspace_manifest = _validate_manifest(root)
    if (
        attempt["case_id"] != workspace_manifest["case_id"]
        or attempt["scientific_protocol_id"]
        != workspace_manifest["scientific_protocol_id"]
    ):
        raise WorkspaceError("attempt case or protocol identity mismatch")
    stage_id = _safe_id(str(attempt["stage_id"]), "attempt stage id")
    attempt_id = _safe_id(str(attempt["attempt_id"]), "attempt id")
    _safe_id(str(attempt["engine_id"]), "attempt engine id")
    if attempt_root.parts[-2:] != (stage_id, attempt_id):
        raise WorkspaceError("attempt path does not match attempt identities")
    _parse_utc(str(attempt["created_utc"]), "attempt created utc")
    input_set_artifact = _validate_recorded_artifact(
        root, attempt["input_set"], "attempt input set", verify_bytes=True
    )
    input_set, _ = _load_input_set(root, Path(input_set_artifact["label"]))
    if (
        input_set["stage_id"] != stage_id
        or input_set["engine_id"] != attempt["engine_id"]
    ):
        raise WorkspaceError("attempt identity differs from its input set")
    materialized = attempt.get("materialized_inputs")
    if not isinstance(materialized, list) or not materialized:
        raise WorkspaceError("attempt has no materialized inputs")
    labels: set[str] = set()
    source_records = {
        item["label"]: item
        for item in input_set["files"]
    }
    for item in materialized:
        if not isinstance(item, dict) or set(item) != {
            "kind",
            "source_label",
            "materialized_label",
            "bytes",
            "sha256",
        }:
            raise WorkspaceError("invalid materialized input record")
        relative, candidate = _contained_relative(
            attempt_root,
            str(item["materialized_label"]),
            "materialized input label",
        )
        if relative.parts[0] == "00-attempt":
            raise WorkspaceError("materialized input uses reserved directory")
        if relative.as_posix() in labels:
            raise WorkspaceError("duplicate materialized input label")
        labels.add(relative.as_posix())
        source = source_records.get(item["source_label"])
        if source is None or {
            "kind": item["kind"],
            "label": item["source_label"],
            "bytes": item["bytes"],
            "sha256": item["sha256"],
        } != source:
            raise WorkspaceError(
                "materialized input record differs from the input set"
            )
        if not candidate.is_file() or candidate.is_symlink():
            raise WorkspaceError("materialized input is unavailable")
        raw = candidate.read_bytes()
        if len(raw) != item.get("bytes") or _sha256(raw) != item.get("sha256"):
            raise WorkspaceError("materialized input bytes drifted")
    if {item["source_label"] for item in materialized} != set(source_records):
        raise WorkspaceError("materialized inputs do not cover the exact input set")
    review_basis = attempt.get("initial_review_basis")
    if not isinstance(review_basis, dict) or set(review_basis) != {
        "mode",
        "state",
        "taskbook_revision",
        "taskbook_sha256",
        "taskbook_label",
    }:
        raise WorkspaceError("invalid attempt initial review basis")
    if review_basis["mode"] != workspace_manifest["review_mode"]:
        raise WorkspaceError("attempt review mode differs from workspace")
    if workspace_manifest["review_mode"] == "milestone-review":
        if review_basis["state"] != "approved":
            raise WorkspaceError("reviewed attempt lacks initial approval")
        revision = review_basis.get("taskbook_revision")
        label = review_basis.get("taskbook_label")
        if (
            not isinstance(revision, int)
            or label
            != f"00-governance/taskbook-revisions/revision-{revision:06d}.json"
            or not isinstance(review_basis.get("taskbook_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", review_basis["taskbook_sha256"])
        ):
            raise WorkspaceError("invalid reviewed attempt taskbook basis")
        basis_path = root / label
        if (
            not basis_path.is_file()
            or _sha256(basis_path.read_bytes()) != review_basis["taskbook_sha256"]
        ):
            raise WorkspaceError("reviewed attempt taskbook basis is unavailable")
        basis_taskbook = _load_object(basis_path, "attempt review basis")
        basis_review = basis_taskbook.get("initial_execution_review")
        if (
            not isinstance(basis_review, dict)
            or basis_review.get("state") != "approved"
            or input_set_artifact not in basis_review.get("frozen_artifacts", [])
        ):
            raise WorkspaceError(
                "attempt input set is absent from its approved review basis"
            )
    elif review_basis != {
        "mode": workspace_manifest["review_mode"],
        "state": "not-required",
        "taskbook_revision": None,
        "taskbook_sha256": None,
        "taskbook_label": None,
    }:
        raise WorkspaceError("non-review attempt carries a review approval claim")
    paths = _event_paths(attempt_root)
    if not paths:
        raise WorkspaceError("attempt has no immutable events")
    previous_raw: bytes | None = None
    previous_state: str | None = None
    previous_time: datetime | None = None
    latest: dict[str, Any] | None = None
    latest_raw = b""
    for sequence, path in enumerate(paths, 1):
        raw = path.read_bytes()
        event = _load_object(path, path.name)
        if set(event) != {
            "format_name",
            "format_version",
            "attempt_id",
            "attempt_manifest_sha256",
            "sequence",
            "previous_event",
            "state",
            "at_utc",
            "summary",
            "artifacts",
            "producer",
        }:
            raise WorkspaceError(f"{path.name}: event fields differ from format")
        if (
            event["format_name"] != "calculation-attempt-event"
            or event["format_version"] != ATTEMPT_VERSION
            or event["attempt_id"] != attempt_id
            or event["attempt_manifest_sha256"] != _sha256(attempt_raw)
            or event["sequence"] != sequence
        ):
            raise WorkspaceError(f"{path.name}: event identity mismatch")
        expected_previous = (
            None
            if previous_raw is None
            else {
                "sequence": sequence - 1,
                "sha256": _sha256(previous_raw),
                "label": f"event-{sequence - 1:06d}.json",
            }
        )
        if event["previous_event"] != expected_previous:
            raise WorkspaceError(f"{path.name}: previous event mismatch")
        state = event.get("state")
        if state not in ATTEMPT_STATES:
            raise WorkspaceError(f"{path.name}: invalid attempt state")
        if sequence == 1 and state != "prepared":
            raise WorkspaceError("first attempt event must be prepared")
        if previous_state is not None and state not in ATTEMPT_TRANSITIONS.get(
            previous_state, frozenset()
        ):
            raise WorkspaceError(
                f"{path.name}: invalid attempt transition "
                f"{previous_state} -> {state}"
            )
        at_utc = _parse_utc(str(event["at_utc"]), f"{path.name} at utc")
        if previous_time is not None and at_utc < previous_time:
            raise WorkspaceError(f"{path.name}: event time moved backward")
        if not isinstance(event.get("summary"), str) or not event["summary"].strip():
            raise WorkspaceError(f"{path.name}: event summary cannot be empty")
        artifacts = event.get("artifacts")
        if not isinstance(artifacts, list):
            raise WorkspaceError(f"{path.name}: artifacts must be an array")
        kinds: set[str] = set()
        event_labels: set[str] = set()
        for artifact in artifacts:
            checked = _validate_recorded_artifact(
                root,
                artifact,
                f"{path.name} attempt event",
                verify_bytes=verify_artifacts,
            )
            artifact_path = root / checked["label"]
            try:
                artifact_path.resolve().relative_to(attempt_root)
            except ValueError as exc:
                raise WorkspaceError(
                    f"{path.name}: attempt artifact is outside its attempt"
                ) from exc
            if checked["label"] in event_labels:
                raise WorkspaceError(
                    f"{path.name}: duplicate attempt artifact label"
                )
            event_labels.add(checked["label"])
            kinds.add(checked["kind"])
        if state not in TERMINAL_ATTEMPT_STATES and artifacts:
            raise WorkspaceError(
                f"{path.name}: changing attempt cannot record stable artifacts"
            )
        if state == "completed" and "run-record" not in kinds:
            raise WorkspaceError(
                f"{path.name}: completed attempt requires a run-record artifact"
            )
        previous_raw = raw
        previous_state = state
        previous_time = at_utc
        latest = event
        latest_raw = raw
    assert latest is not None
    return attempt, latest, latest_raw


def append_attempt_event(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    with _workspace_lock(root):
        _validate_manifest(root)
        stage_id = _safe_id(args.stage_id, "stage id")
        attempt_id = _safe_id(args.attempt_id, "attempt id")
        attempt_root = _attempt_root(root, stage_id, attempt_id)
        _, latest, latest_raw = _validate_attempt(
            root, attempt_root, verify_artifacts=True
        )
        if args.state not in ATTEMPT_TRANSITIONS.get(
            latest["state"], frozenset()
        ):
            raise WorkspaceError(
                f"invalid attempt transition: {latest['state']} -> {args.state}"
            )
        at_utc = _parse_utc(args.at_utc, "attempt event utc")
        if at_utc < _parse_utc(latest["at_utc"], "latest attempt event utc"):
            raise WorkspaceError("attempt event time cannot move backward")
        if not args.summary.strip():
            raise WorkspaceError("attempt event summary cannot be empty")
        artifacts = [_artifact(root, value) for value in args.artifact]
        for artifact in artifacts:
            artifact_path = root / artifact["label"]
            try:
                artifact_path.resolve().relative_to(attempt_root)
            except ValueError as exc:
                raise WorkspaceError(
                    "attempt event artifacts must be inside the attempt directory"
                ) from exc
        if args.state not in TERMINAL_ATTEMPT_STATES and artifacts:
            raise WorkspaceError(
                "changing attempts cannot record stable output artifacts"
            )
        if args.state == "completed" and not any(
            item["kind"] == "run-record" for item in artifacts
        ):
            raise WorkspaceError(
                "completed attempt requires a run-record artifact"
            )
        sequence = latest["sequence"] + 1
        event = {
            "format_name": "calculation-attempt-event",
            "format_version": ATTEMPT_VERSION,
            "attempt_id": attempt_id,
            "attempt_manifest_sha256": latest["attempt_manifest_sha256"],
            "sequence": sequence,
            "previous_event": {
                "sequence": sequence - 1,
                "sha256": _sha256(latest_raw),
                "label": f"event-{sequence - 1:06d}.json",
            },
            "state": args.state,
            "at_utc": args.at_utc,
            "summary": args.summary.strip(),
            "artifacts": sorted(
                artifacts, key=lambda item: (item["kind"], item["label"])
            ),
            "producer": {
                "tool_id": "manage-calculation-workspace",
                "tool_version": TOOL_VERSION,
            },
        }
        event_path = (
            attempt_root
            / "00-attempt"
            / "events"
            / f"event-{sequence:06d}.json"
        )
        raw = _json_bytes(event)
        _atomic_write(event_path, raw, exclusive=True)
        active_attempts = [
            f"{item['stage_id']}/{item['attempt_id']}"
            for item in _validate_attempt_inventory(
                root, verify_artifacts=True
            )
            if item["state"] == "active"
        ]
    return {
        "status": args.state,
        "workspace": str(root),
        "attempt": attempt_root.relative_to(root).as_posix(),
        "event_sequence": sequence,
        "event_sha256": _sha256(raw),
        "active_attempts": active_attempts,
        "workspace_reorganization_allowed": not active_attempts,
    }


def _validate_input_inventory(root: Path) -> int:
    inputs = root / "02-inputs"
    count = 0
    for stage_entry in sorted(inputs.iterdir()):
        if (
            stage_entry.is_symlink()
            or not stage_entry.is_dir()
        ):
            raise WorkspaceError(
                f"unmanaged entry under 02-inputs: "
                f"{stage_entry.relative_to(root).as_posix()}"
            )
        _safe_id(stage_entry.name, "input stage directory")
        for input_set_entry in sorted(stage_entry.iterdir()):
            if (
                input_set_entry.is_symlink()
                or not input_set_entry.is_dir()
            ):
                raise WorkspaceError(
                    f"unmanaged entry under input stage: "
                    f"{input_set_entry.relative_to(root).as_posix()}"
                )
            _safe_id(input_set_entry.name, "input-set directory")
            manifest_path = input_set_entry / "input-set.json"
            if not manifest_path.is_file() or manifest_path.is_symlink():
                raise WorkspaceError(
                    f"unmanaged input-set directory: "
                    f"{input_set_entry.relative_to(root).as_posix()}"
                )
            _load_input_set(root, manifest_path.relative_to(root))
            count += 1
    return count


def _validate_attempt_inventory(
    root: Path, *, verify_artifacts: bool
) -> list[dict[str, Any]]:
    runs = root / "03-runs"
    inventory: list[dict[str, Any]] = []
    for stage_dir in sorted(runs.iterdir()):
        if stage_dir.is_symlink() or not stage_dir.is_dir():
            raise WorkspaceError(
                f"unmanaged entry under 03-runs: "
                f"{stage_dir.relative_to(root).as_posix()}"
            )
        _safe_id(stage_dir.name, "run stage directory")
        for attempt_dir in sorted(stage_dir.iterdir()):
            if attempt_dir.is_symlink() or not attempt_dir.is_dir():
                raise WorkspaceError(
                    f"unmanaged entry under run stage: "
                    f"{attempt_dir.relative_to(root).as_posix()}"
                )
            _safe_id(attempt_dir.name, "run attempt directory")
            if not (
                attempt_dir / "00-attempt" / "attempt-manifest.json"
            ).is_file():
                raise WorkspaceError(
                    f"unmanaged attempt directory: "
                    f"{attempt_dir.relative_to(root).as_posix()}"
                )
            attempt, event, _ = _validate_attempt(
                root, attempt_dir, verify_artifacts=verify_artifacts
            )
            inventory.append(
                {
                    "stage_id": attempt["stage_id"],
                    "attempt_id": attempt["attempt_id"],
                    "state": event["state"],
                }
            )
    return inventory


def check_workspace(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    with _workspace_lock(root):
        manifest = _validate_manifest(root)
        input_set_count = _validate_input_inventory(root)
        attempts = _validate_attempt_inventory(root, verify_artifacts=True)
        active = [
            f"{item['stage_id']}/{item['attempt_id']}"
            for item in attempts
            if item["state"] == "active"
        ]
        if args.require_quiescent and active:
            raise WorkspaceError(
                "workspace is not quiescent; active attempts: " + ", ".join(active)
            )
        result = {
            "status": "ok",
            "workspace": str(root),
            "review_mode": manifest["review_mode"],
            "taskbook_enabled": manifest["taskbook_enabled"],
            "input_set_count": input_set_count,
            "attempt_count": len(attempts),
            "active_attempts": active,
            "workspace_reorganization_allowed": not active,
        }
        if manifest["taskbook_enabled"]:
            latest, raw = _validate_taskbook_chain(
                root, manifest, verify_artifacts=True
            )
            initial_state = latest["initial_execution_review"]["state"]
            result.update(
                {
                    "revision": latest["revision"],
                    "updated_utc": latest["updated_utc"],
                    "taskbook_sha256": _sha256(raw),
                    "initial_review_state": initial_state,
                    "execution_review_ready": initial_state
                    in {"not-required", "approved"},
                }
            )
        else:
            result.update(
                {
                    "initial_review_state": "not-required",
                    "execution_review_ready": True,
                }
            )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    initialize = subparsers.add_parser("init")
    initialize.add_argument("root", type=Path)
    initialize.add_argument("--case-id", required=True)
    initialize.add_argument("--protocol-id", required=True)
    initialize.add_argument("--objective", required=True)
    initialize.add_argument("--review-mode", choices=REVIEW_MODES, required=True)
    initialize.add_argument("--selected-utc", required=True)
    initialize.set_defaults(handler=init_workspace)
    update = subparsers.add_parser("update")
    update.add_argument("root", type=Path)
    update.add_argument("--stage-id", required=True)
    update.add_argument("--stage-title", required=True)
    update.add_argument("--milestone-kind", choices=MILESTONE_KINDS, required=True)
    update.add_argument("--stage-status", choices=STAGE_STATUSES, required=True)
    update.add_argument("--review-state", choices=REVIEW_STATES, required=True)
    update.add_argument("--summary", required=True)
    update.add_argument("--next-action", required=True)
    update.add_argument("--review-note")
    update.add_argument("--artifact", action="append", default=[])
    update.add_argument("--at-utc", required=True)
    update.set_defaults(handler=update_taskbook)
    request_review = subparsers.add_parser("request-initial-review")
    request_review.add_argument("root", type=Path)
    request_review.add_argument("--workflow-plan", required=True)
    request_review.add_argument("--input-set", required=True)
    request_review.add_argument("--summary", required=True)
    request_review.add_argument("--at-utc", required=True)
    request_review.set_defaults(handler=request_initial_review)
    decide_review = subparsers.add_parser("decide-initial-review")
    decide_review.add_argument("root", type=Path)
    decide_review.add_argument(
        "--decision", choices=("approved", "changes-requested"), required=True
    )
    decide_review.add_argument("--expected-taskbook-sha256", required=True)
    decide_review.add_argument("--review-note", required=True)
    decide_review.add_argument("--at-utc", required=True)
    decide_review.set_defaults(handler=decide_initial_review)
    input_set = subparsers.add_parser("create-input-set")
    input_set.add_argument("root", type=Path)
    input_set.add_argument("--stage-id", required=True)
    input_set.add_argument("--input-set-id", required=True)
    input_set.add_argument("--engine-id", required=True)
    input_set.add_argument("--input", action="append", default=[])
    input_set.add_argument("--at-utc", required=True)
    input_set.set_defaults(handler=create_input_set)
    attempt = subparsers.add_parser("init-attempt")
    attempt.add_argument("root", type=Path)
    attempt.add_argument("--stage-id", required=True)
    attempt.add_argument("--attempt-id", required=True)
    attempt.add_argument("--engine-id", required=True)
    attempt.add_argument("--input-set", required=True)
    attempt.add_argument("--summary", required=True)
    attempt.add_argument("--at-utc", required=True)
    attempt.set_defaults(handler=init_attempt)
    attempt_event = subparsers.add_parser("append-attempt-event")
    attempt_event.add_argument("root", type=Path)
    attempt_event.add_argument("--stage-id", required=True)
    attempt_event.add_argument("--attempt-id", required=True)
    attempt_event.add_argument(
        "--state",
        choices=tuple(state for state in ATTEMPT_STATES if state != "prepared"),
        required=True,
    )
    attempt_event.add_argument("--summary", required=True)
    attempt_event.add_argument("--artifact", action="append", default=[])
    attempt_event.add_argument("--at-utc", required=True)
    attempt_event.set_defaults(handler=append_attempt_event)
    check = subparsers.add_parser("check")
    check.add_argument("root", type=Path)
    check.add_argument("--require-quiescent", action="store_true")
    check.set_defaults(handler=check_workspace)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.handler(args)
    except (OSError, WorkspaceError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
