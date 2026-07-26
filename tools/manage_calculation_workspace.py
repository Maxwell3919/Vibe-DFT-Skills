#!/usr/bin/env python3
"""Create and verify orderly calculation workspaces and revisioned taskbooks."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


TOOL_VERSION = "1.0.0"
LAYOUT_VERSION = "1.0"
TASKBOOK_VERSION = "1.0"
DIRECTORIES = (
    "00-governance/taskbook-revisions",
    "01-structures",
    "02-inputs",
    "03-runs",
    "04-derived",
    "05-figures",
    "06-reports",
    "90-archive",
)
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")
ARTIFACT_SPEC = re.compile(r"^(?P<kind>[a-z][a-z0-9-]{1,63})=(?P<label>.+)$")
REVIEW_MODES = ("off", "silent-update", "milestone-review")
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


def _artifact(root: Path, specification: str) -> dict[str, Any]:
    match = ARTIFACT_SPEC.fullmatch(specification)
    if match is None:
        raise WorkspaceError("--artifact must be KIND=RELATIVE_PATH")
    relative = Path(match.group("label"))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise WorkspaceError("artifact path must be a contained relative path")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise WorkspaceError("artifact resolves outside the workspace") from exc
    if not candidate.is_file() or candidate.is_symlink():
        raise WorkspaceError(f"artifact is not a regular non-symlink file: {relative}")
    raw = candidate.read_bytes()
    return {
        "kind": match.group("kind"),
        "label": relative.as_posix(),
        "bytes": len(raw),
        "sha256": _sha256(raw),
    }


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
        "producer",
    }
    if set(manifest) != expected:
        raise WorkspaceError("workspace manifest fields differ from format 1.0")
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
        if not (root / directory).is_dir():
            raise WorkspaceError(f"required workspace directory is missing: {directory}")
    enabled = manifest["review_mode"] != "off"
    if manifest["taskbook_enabled"] is not enabled:
        raise WorkspaceError("taskbook_enabled contradicts review mode")
    expected_current = "00-governance/taskbook-current.json" if enabled else None
    if manifest["taskbook_current"] != expected_current:
        raise WorkspaceError("taskbook_current contradicts review mode")
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
    latest: dict[str, Any] | None = None
    latest_raw = b""
    for index, path in enumerate(paths, 1):
        raw = path.read_bytes()
        data = _load_object(path, path.name)
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
        if not isinstance(policy, dict) or policy.get("mode") != manifest["review_mode"]:
            raise WorkspaceError(f"{path.name}: review policy mismatch")
        updated = _parse_utc(str(data.get("updated_utc")), f"{path.name} updated utc")
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
        for stage in stages:
            if not isinstance(stage, dict):
                raise WorkspaceError(f"{path.name}: stage must be an object")
            stage_id = _safe_id(str(stage.get("stage_id")), "stage id")
            if stage_id in seen:
                raise WorkspaceError(f"{path.name}: duplicate stage id {stage_id}")
            seen.add(stage_id)
            if stage.get("status") not in STAGE_STATUSES:
                raise WorkspaceError(f"{path.name}: invalid stage status")
            if stage.get("review_state") not in REVIEW_STATES:
                raise WorkspaceError(f"{path.name}: invalid review state")
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
            for artifact in stage.get("artifacts", []):
                if not isinstance(artifact, dict):
                    raise WorkspaceError(f"{path.name}: artifact must be an object")
                label = artifact.get("label")
                relative = Path(str(label))
                if relative.is_absolute() or ".." in relative.parts:
                    raise WorkspaceError(f"{path.name}: unsafe artifact label")
                if verify_artifacts:
                    candidate = (root / relative).resolve()
                    try:
                        candidate.relative_to(root)
                    except ValueError as exc:
                        raise WorkspaceError(
                            f"{path.name}: artifact escapes workspace"
                        ) from exc
                    if not candidate.is_file() or candidate.is_symlink():
                        raise WorkspaceError(
                            f"{path.name}: recorded artifact is unavailable: {label}"
                        )
                    artifact_raw = candidate.read_bytes()
                    if len(artifact_raw) != artifact.get("bytes"):
                        raise WorkspaceError(f"{path.name}: artifact byte count drift")
                    if _sha256(artifact_raw) != artifact.get("sha256"):
                        raise WorkspaceError(f"{path.name}: artifact hash drift")
        previous_raw = raw
        previous_updated = updated
        latest = data
        latest_raw = raw
    if current_path.read_bytes() != latest_raw:
        raise WorkspaceError("taskbook-current.json is not the exact latest revision")
    assert latest is not None
    return latest, latest_raw


def update_taskbook(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    manifest = _validate_manifest(root)
    if manifest["review_mode"] == "off":
        raise WorkspaceError("taskbook updates are disabled for review mode off")
    latest, latest_raw = _validate_taskbook_chain(
        root, manifest, verify_artifacts=True
    )
    _safe_id(args.stage_id, "stage id")
    at_utc = _parse_utc(args.at_utc, "update utc")
    if at_utc < _parse_utc(latest["updated_utc"], "latest updated utc"):
        raise WorkspaceError("update time cannot precede the latest revision")
    if not args.stage_title.strip() or not args.summary.strip():
        raise WorkspaceError("stage title and summary cannot be empty")
    mode = manifest["review_mode"]
    if mode == "silent-update" and args.review_state != "not-required":
        raise WorkspaceError("silent-update requires review-state not-required")
    if mode == "milestone-review":
        if args.stage_status == "completed" and args.review_state != "approved":
            raise WorkspaceError("completed reviewed milestone requires approved")
        if args.review_state == "approved" and not args.review_note:
            raise WorkspaceError("approved review requires --review-note")
    artifacts = [_artifact(root, value) for value in args.artifact]
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
        (candidate for candidate in stages if candidate["stage_id"] == args.stage_id),
        None,
    )
    if stage is None:
        stage = {
            "stage_id": args.stage_id,
            "title": args.stage_title.strip(),
            "status": args.stage_status,
            "review_state": args.review_state,
            "updated_utc": args.at_utc,
            "summary": args.summary.strip(),
            "review_note": args.review_note,
            "artifacts": artifacts,
        }
        stages.append(stage)
    else:
        combined = {item["label"]: item for item in stage.get("artifacts", [])}
        for item in artifacts:
            combined[item["label"]] = item
        stage.update(
            {
                "title": args.stage_title.strip(),
                "status": args.stage_status,
                "review_state": args.review_state,
                "updated_utc": args.at_utc,
                "summary": args.summary.strip(),
                "review_note": args.review_note,
                "artifacts": sorted(
                    combined.values(), key=lambda item: (item["kind"], item["label"])
                ),
            }
        )
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
            "updated_utc": args.at_utc,
            "update": {
                "kind": "stage-update",
                "stage_id": args.stage_id,
                "summary": args.summary.strip(),
            },
            "stages": sorted(stages, key=lambda item: item["stage_id"]),
        }
    )
    raw = _json_bytes(updated)
    _, current_path, revisions = _paths(root)
    revision_path = revisions / f"revision-{revision:06d}.json"
    _atomic_write(revision_path, raw, exclusive=True)
    _atomic_write(current_path, raw)
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


def check_workspace(args: argparse.Namespace) -> dict[str, Any]:
    root = _validate_workspace_root(args.root)
    manifest = _validate_manifest(root)
    result = {
        "status": "ok",
        "workspace": str(root),
        "review_mode": manifest["review_mode"],
        "taskbook_enabled": manifest["taskbook_enabled"],
    }
    if manifest["taskbook_enabled"]:
        latest, raw = _validate_taskbook_chain(
            root, manifest, verify_artifacts=True
        )
        result.update(
            {
                "revision": latest["revision"],
                "updated_utc": latest["updated_utc"],
                "taskbook_sha256": _sha256(raw),
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
    update.add_argument("--stage-status", choices=STAGE_STATUSES, required=True)
    update.add_argument("--review-state", choices=REVIEW_STATES, required=True)
    update.add_argument("--summary", required=True)
    update.add_argument("--review-note")
    update.add_argument("--artifact", action="append", default=[])
    update.add_argument("--at-utc", required=True)
    update.set_defaults(handler=update_taskbook)
    check = subparsers.add_parser("check")
    check.add_argument("root", type=Path)
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
