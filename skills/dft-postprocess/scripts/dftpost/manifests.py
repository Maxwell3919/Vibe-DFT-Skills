from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from . import __version__
from .utils import find_repo_root, relative_file, sha256_file, utc_now


SCHEMAS = {
    "run": "run-manifest.schema.json",
    "artifact": "artifact-manifest.schema.json",
    "campaign": "campaign-record.schema.json",
    "recommendation": "recommendation-record.schema.json",
}


def schema_path(kind: str) -> Path:
    root = find_repo_root(Path(__file__))
    return root / "contracts" / SCHEMAS[kind]


def validation_errors(kind: str, data: object) -> list[str]:
    schema = json.loads(schema_path(kind).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        failures.append(f"{location}: {error.message}")
    return failures


def validate_manifest(kind: str, path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"<file>: {exc}"]
    return validation_errors(kind, data)


def _file_record(root: Path, specification: str) -> dict[str, Any]:
    if "=" not in specification:
        raise ValueError("file specifications must use role=relative/path")
    role, value = specification.split("=", 1)
    if not role or not value:
        raise ValueError("file specifications require nonempty role and path")
    path, relative = relative_file(root, Path(value))
    return {"role": role, "path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def build_artifact_manifest(
    artifact_id: str,
    source_run_ids: list[str],
    code: str,
    artifact_type: str,
    status: str,
    root: Path,
    data_specs: list[str],
    figure_specs: list[str],
    validation_status: str,
    checks: list[str],
    claim_boundary: list[str],
    command: list[str],
) -> dict[str, Any]:
    manifest = {
        "schema_version": "1.0",
        "artifact_id": artifact_id,
        "source_run_ids": source_run_ids,
        "code": code,
        "artifact_type": artifact_type,
        "status": status,
        "data_files": [_file_record(root, item) for item in data_specs],
        "figure_files": [_file_record(root, item) for item in figure_specs],
        "validation": {"status": validation_status, "checks": checks},
        "claim_boundary": claim_boundary,
        "provenance": {"tool": "dftpost", "tool_version": __version__, "generated_utc": utc_now(), "command": command},
    }
    errors = validation_errors("artifact", manifest)
    if errors:
        raise ValueError("artifact manifest is invalid: " + "; ".join(errors))
    return manifest
