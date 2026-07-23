from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from . import __version__
from .utils import find_repo_root, relative_file, sha256_file, utc_now


REPO_ROOT = find_repo_root(Path(__file__))
TOOLS_ROOT = str(REPO_ROOT / "tools")
if TOOLS_ROOT not in sys.path:
    sys.path.insert(0, TOOLS_ROOT)

from validate_contract import validate_file as catalog_validate_file  # noqa: E402
from validate_contract import validation_errors as catalog_validation_errors  # noqa: E402


SCHEMAS = {
    "run": "run-manifest.schema.json",
    "artifact": "artifact-manifest.schema.json",
    "campaign": "campaign-record.schema.json",
    "recommendation": "recommendation-record.schema.json",
    "dataset": "normalized-dataset.schema.json",
    "plan": "postprocess-plan.schema.json",
    "execution": "tool-execution.schema.json",
    "structure": "structure-manifest.schema.json",
}


def schema_path(kind: str) -> Path:
    return REPO_ROOT / "contracts" / SCHEMAS[kind]


def validation_errors(kind: str, data: object) -> list[str]:
    return catalog_validation_errors(kind, data, REPO_ROOT / "contracts")


def validate_manifest(kind: str, path: Path) -> list[str]:
    return catalog_validate_file(kind, path, REPO_ROOT / "contracts")


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
