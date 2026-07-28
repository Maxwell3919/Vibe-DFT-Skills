#!/usr/bin/env python3
"""Build and independently verify a deterministic active-only source archive.

The archive is deliberately narrower than the repository.  It contains active
Skill source trees, contracts, filtered active routing metadata, a complete
offline verification-tool closure, and inert source-registry snapshots needed
to re-prove generated-pack identities.  Routable development/planned Skill
metadata and source trees, runtime records, credentials, licensed potentials,
and centrally release-blocked legacy official-document bodies are rejected or
excluded.  The unpacked verifier runs a portable, fail-closed semantic audit;
externalized legacy bodies keep its assurance ceiling at partial.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator
import yaml

from registry_yaml import load_yaml_strict
import release_content_policy
import skill_registry
import strict_json
import validate_contract
import validate_official_document_coverage


SCHEMA_VERSION = "1.0"
TOOL_VERSION = "1.2"
MANIFEST_PATH = "ACTIVE_ONLY_MANIFEST.json"
MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_BUNDLE_BYTES = 1024 * 1024
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
MAX_ARCHIVE_FILES = 100_000
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
COMMIT_RE = re.compile(r"^[a-f0-9]{40}(?:[a-f0-9]{24})?$")
SKILL_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")

VERIFICATION_TOOL_PATHS = (
    "tools/active_evidence.py",
    "tools/build_active_only_distribution.py",
    "tools/build_official_document_packs.py",
    "tools/environment_profiles.py",
    "tools/extract_official_document_pack_inputs.py",
    "tools/interface_registry.py",
    "tools/official_source_authorities.py",
    "tools/operation_routes.py",
    "tools/release_content_policy.py",
    "tools/registry_snapshot.py",
    "tools/registry_yaml.py",
    "tools/skill_registry.py",
    "tools/software_registry.py",
    "tools/strict_json.py",
    "tools/validate_contract.py",
    "tools/validate_official_document_bundles.py",
    "tools/validate_official_document_coverage.py",
    "tools/validate_official_document_storage.py",
    "tools/validate_promotion.py",
)

FILTERED_REGISTRY_PATHS = (
    "registry/active-evidence.yaml",
    "registry/skill-registry.yaml",
    "registry/software-registry.yaml",
    "registry/interface-registry.yaml",
    "registry/operation-routes.yaml",
    "registry/official-source-authorities.yaml",
    "registry/official-document-consumers.yaml",
    "registry/official-document-bundle-expectations.yaml",
    "registry/official-document-storage-discovery.yaml",
    "registry/semantic-obligations.yaml",
)

SOURCE_REGISTRY_PATHS = (
    "registry/active-evidence.yaml",
    "registry/skill-registry.yaml",
    "registry/software-registry.yaml",
    "registry/interface-registry.yaml",
    "registry/environment-profiles.yaml",
    "registry/operation-routes.yaml",
    "registry/official-source-authorities.yaml",
    "registry/official-document-consumers.yaml",
    "registry/official-document-bundle-expectations.yaml",
    "registry/official-document-storage-discovery.yaml",
    "registry/semantic-obligations.yaml",
)
SOURCE_SNAPSHOT_PREFIX = PurePosixPath("registry", "source-snapshots")
DEPENDENCY_MANIFEST_PATH = "requirements-dev.txt"
BUILD_COMMAND = (
    "python3 tools/build_active_only_distribution.py build "
    "--root . --output <artifact>"
)
RELEASE_BUILD_COMMAND = (
    f"{BUILD_COMMAND} --require-clean-commit"
)
BUILD_ENVIRONMENT_ASSUMPTIONS = (
    "Python 3.11 or newer",
    "PyYAML available for registry verification",
    "jsonschema and referencing available for offline contract verification",
    "POSIX-normalized regular-file archive members only",
    "PYTHONDONTWRITEBYTECODE=1 when executing the packaged verifier in place",
)

# These are policy/control records, not upstream documentation bytes.  Every
# other Wave-0 legacy selector match remains excluded.
LOCAL_OFFICIAL_CONTROL_PATHS = frozenset(
    {
        "skills/cp2k-rigorous-calculations/references/official-source-policy.md",
        "skills/siesta-rigorous-calculations/references/official-artifact-fixtures.json",
        "skills/siesta-rigorous-calculations/references/official-artifact-forward-tests.md",
        "skills/siesta-rigorous-calculations/references/official-sources.md",
    }
)

SENSITIVE_COMPONENTS = frozenset(
    {
        ".git",
        ".ssh",
        ".venv",
        "__pycache__",
        "private-runtime",
        "runtime",
        "runtime-data",
        "runtime-records",
    }
)
SENSITIVE_BASENAMES = frozenset(
    {
        ".env",
        ".netrc",
        "CHGCAR",
        "CONTCAR",
        "DOSCAR",
        "EIGENVAL",
        "IBZKPT",
        "LOCPOT",
        "OSZICAR",
        "OUTCAR",
        "PCDAT",
        "POTCAR",
        "PROCAR",
        "REPORT",
        "WAVECAR",
        "WAVEDER",
        "XDATCAR",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "id_rsa",
    }
)
SENSITIVE_SUFFIXES = (".pyc", ".pyo", ".swp", ".tmp")
RELEASE_CONTENT_SCOPE = "active-only-distribution"


class DistributionError(ValueError):
    """A stable fail-closed distribution construction or verification error."""


@dataclass(frozen=True)
class SourceSelection:
    active_skill_ids: tuple[str, ...]
    development_skill_ids: tuple[str, ...]
    files: dict[str, bytes]
    modes: dict[str, int]
    source_registry_digests: dict[str, str]
    excluded_legacy_artifacts: tuple[dict[str, object], ...]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_projection_sha256(value: object) -> str:
    return _sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )


def _yaml_bytes(value: object) -> bytes:
    return yaml.safe_dump(
        value,
        allow_unicode=False,
        default_flow_style=False,
        sort_keys=True,
        width=1000,
    ).encode("utf-8")


def _safe_archive_path(value: object, *, allow_manifest: bool = False) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not value.isprintable()
        or "\\" in value
        or "\x00" in value
    ):
        if isinstance(value, str):
            try:
                _reject_release_findings(
                    release_content_policy.scan_path(
                        value,
                        "opaque-binary",
                        RELEASE_CONTENT_SCOPE,
                    )
                )
            except DistributionError:
                raise
            except (TypeError, ValueError):
                pass
        raise DistributionError(
            "<unsafe-path>: release-content blocker "
            "[RCP-PATH-001/unsafe-path]"
        )
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        _reject_release_findings(
            release_content_policy.scan_path(
                value,
                "opaque-binary",
                RELEASE_CONTENT_SCOPE,
            )
        )
        raise DistributionError(
            "<unsafe-path>: release-content blocker "
            "[RCP-PATH-001/unsafe-path]"
        )
    if not allow_manifest and value == MANIFEST_PATH:
        raise DistributionError("manifest path is reserved")
    return value


def _is_sensitive_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    folded = {part.casefold() for part in parts}
    if folded & SENSITIVE_COMPONENTS:
        return True
    name = parts[-1]
    if name in SENSITIVE_BASENAMES or name.startswith("POTCAR."):
        return True
    return name.endswith(SENSITIVE_SUFFIXES)


def _is_official_source_pack(path: str) -> bool:
    return "/references/official-source-pack/" in f"/{path}"


def _is_legacy_official_artifact(path: str) -> bool:
    if path in LOCAL_OFFICIAL_CONTROL_PATHS or _is_official_source_pack(path):
        return False
    prefixes = (
        "skills/qe-rigorous-calculations/references/official-",
        "skills/vasp-rigorous-calculations/references/official-",
        "skills/cp2k-rigorous-calculations/references/official-manual/",
    )
    if path.startswith(prefixes):
        return True
    return path in {
        "skills/cp2k-rigorous-calculations/references/official-source-registry.json",
        "skills/siesta-rigorous-calculations/references/official-fdf-index.json",
        "skills/siesta-rigorous-calculations/references/official-source-registry.json",
        "skills/siesta-rigorous-calculations/references/official-source-supplements.json",
    }


def _scan_content(path: str, raw: bytes) -> None:
    if len(raw) > MAX_FILE_BYTES:
        raise DistributionError(f"{path}: file exceeds the distribution size limit")
    try:
        role = release_content_policy.classify_path(path)
        path_findings = release_content_policy.scan_path(
            path,
            role,
            RELEASE_CONTENT_SCOPE,
        )
        byte_findings = release_content_policy.scan_bytes(
            path,
            raw,
            role,
            RELEASE_CONTENT_SCOPE,
            _sha256(raw),
        )
    except (TypeError, ValueError) as exc:
        raise DistributionError(
            f"{path}: release-content classification failed"
        ) from exc
    _reject_release_findings((*path_findings, *byte_findings))


def _reject_release_findings(
    findings: Iterable[release_content_policy.Finding],
) -> None:
    canonical = {
        (
            finding.path,
            finding.rule_id,
            finding.code,
        )
        for finding in findings
    }
    if not canonical:
        return
    safe_path = sorted(item[0] for item in canonical)[0]
    stable_codes = ",".join(
        f"{rule_id}/{code}"
        for _, rule_id, code in sorted(canonical)
    )
    raise DistributionError(
        f"{safe_path}: release-content blocker [{stable_codes}]"
    )


def _scan_release_path(path: str) -> None:
    try:
        role = release_content_policy.classify_path(path)
        findings = release_content_policy.scan_path(
            path,
            role,
            RELEASE_CONTENT_SCOPE,
        )
    except (TypeError, ValueError) as exc:
        raise DistributionError(
            f"{path}: release-content classification failed"
        ) from exc
    _reject_release_findings(findings)


def _validate_release_path(path: str, active_skill_ids: frozenset[str]) -> None:
    _safe_archive_path(path)
    # The shared pure rule module is authoritative for privacy, restricted
    # payload, nested-archive, and runtime findings.  The compatibility checks
    # below remain independent active-only distribution invariants.
    _scan_release_path(path)
    if _is_sensitive_path(path):
        raise DistributionError(f"{path}: sensitive or runtime path is forbidden")
    if _is_legacy_official_artifact(path):
        raise DistributionError(f"{path}: legacy official-document artifact is forbidden")
    parts = PurePosixPath(path).parts
    if parts[0] == "skills":
        if len(parts) < 3 or parts[1] not in active_skill_ids:
            raise DistributionError(
                f"{path}: distribution may contain only an active Skill tree"
            )
    elif parts[0] not in {"contracts", "registry", "tools"} and path != (
        DEPENDENCY_MANIFEST_PATH
    ):
        raise DistributionError(f"{path}: unsupported active-only archive root")


def _canonical_file_entries(
    files: Mapping[str, bytes],
    *,
    active_skill_ids: tuple[str, ...],
    modes: Mapping[str, int] | None,
) -> tuple[list[dict[str, object]], dict[str, bytes], dict[str, int]]:
    if (
        not active_skill_ids
        or tuple(sorted(active_skill_ids)) != active_skill_ids
        or len(set(active_skill_ids)) != len(active_skill_ids)
        or not all(SKILL_ID_RE.fullmatch(item) for item in active_skill_ids)
    ):
        raise DistributionError("active_skill_ids must be a sorted unique Skill ID tuple")
    active = frozenset(active_skill_ids)
    normalized: dict[str, bytes] = {}
    normalized_modes: dict[str, int] = {}
    entries: list[dict[str, object]] = []
    for path, raw in sorted(files.items()):
        _validate_release_path(path, active)
        if not isinstance(raw, bytes):
            raise DistributionError(f"{path}: archive content must be bytes")
        _scan_content(path, raw)
        if path in normalized:
            raise DistributionError(f"{path}: duplicate archive path")
        mode = 0o644 if modes is None else modes.get(path, 0o644)
        if mode not in {0o644, 0o755}:
            raise DistributionError(f"{path}: unsupported normalized mode")
        normalized[path] = raw
        normalized_modes[path] = mode
        entries.append(
            {
                "mode": f"{mode:04o}",
                "path": path,
                "sha256": _sha256(raw),
                "size": len(raw),
            }
        )
    for skill_id in active_skill_ids:
        required = f"skills/{skill_id}/SKILL.md"
        if required not in normalized:
            raise DistributionError(f"{required}: active Skill entrypoint is missing")
    if "registry/skill-registry.yaml" not in normalized:
        raise DistributionError("registry/skill-registry.yaml is required")
    if not any(path.startswith("contracts/") for path in normalized):
        raise DistributionError("at least one contract is required")
    for tool_path in VERIFICATION_TOOL_PATHS:
        if tool_path not in normalized:
            raise DistributionError(f"{tool_path}: verification tool closure is missing")
    return entries, normalized, normalized_modes


def _manifest(
    *,
    entries: list[dict[str, object]],
    active_skill_ids: tuple[str, ...],
    source_commit: str,
    source_registry_digests: Mapping[str, str],
    excluded_legacy_artifacts: Iterable[Mapping[str, object]],
    source_state: str,
    protected_branch: str,
    build_command: str,
) -> dict[str, object]:
    if COMMIT_RE.fullmatch(source_commit) is None:
        raise DistributionError("source_commit must be an exact Git commit SHA")
    if source_state not in {"clean-commit", "candidate-worktree"}:
        raise DistributionError("unsupported source_state")
    if protected_branch not in {"user-asserted", "not-asserted"}:
        raise DistributionError("unsupported protected_branch assertion")
    if (
        build_command not in {BUILD_COMMAND, RELEASE_BUILD_COMMAND}
        or (
            build_command == RELEASE_BUILD_COMMAND
            and source_state != "clean-commit"
        )
    ):
        raise DistributionError("unsupported build command provenance")
    exclusions: list[dict[str, object]] = []
    previous_exclusion = ""
    for record in excluded_legacy_artifacts:
        if (
            not isinstance(record, Mapping)
            or set(record) != {"path", "sha256", "size"}
            or not isinstance(record.get("path"), str)
            or not isinstance(record.get("size"), int)
            or isinstance(record.get("size"), bool)
            or record["size"] < 0
            or record["size"] > MAX_FILE_BYTES
            or SHA256_RE.fullmatch(str(record.get("sha256"))) is None
        ):
            raise DistributionError(
                "excluded legacy official-document receipt is invalid"
            )
        path = _safe_archive_path(record["path"])
        if (
            not _is_legacy_official_artifact(path)
            or path <= previous_exclusion
        ):
            raise DistributionError(
                "excluded legacy official-document receipts are not canonical"
            )
        previous_exclusion = path
        exclusions.append(
            {
                "path": path,
                "sha256": record["sha256"],
                "size": record["size"],
            }
        )
    digests: dict[str, str] = {}
    for path, digest in sorted(source_registry_digests.items()):
        _safe_archive_path(path)
        if not path.startswith("registry/") or SHA256_RE.fullmatch(digest) is None:
            raise DistributionError("source registry digests must bind registry paths")
        digests[path] = digest
    contract_entries = [
        f"{entry['path']}\0{entry['sha256']}\n".encode("utf-8")
        for entry in entries
        if str(entry["path"]).startswith("contracts/")
    ]
    contract_digest = _sha256(
        b"VIBE-DFT-ACTIVE-CONTRACT-CATALOG-v1\0" + b"".join(contract_entries)
    )
    return {
        "active_skill_ids": list(active_skill_ids),
        "artifact_type": "vibe-dft-active-only-source-distribution",
        "build": {
            "command": build_command,
            "environment_assumptions": list(
                BUILD_ENVIRONMENT_ASSUMPTIONS
            ),
            "protected_branch": protected_branch,
            "python_version": platform.python_version(),
            "source_state": source_state,
            "tool_version": TOOL_VERSION,
        },
        "contract_catalog_sha256": contract_digest,
        "excluded_legacy_official_artifact_count": len(exclusions),
        "excluded_legacy_official_artifacts": exclusions,
        "files": entries,
        "schema_version": SCHEMA_VERSION,
        "source_commit": source_commit,
        "source_registry_sha256": digests,
    }


def _normalized_tar_info(path: str, size: int, mode: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(path)
    info.size = size
    info.mode = mode
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.pax_headers = {}
    return info


def _write_normalized_tar_bytes(
    output_path: Path,
    files: Mapping[str, bytes],
    modes: Mapping[str, int],
) -> None:
    with tarfile.open(
        output_path,
        mode="w",
        format=tarfile.PAX_FORMAT,
        pax_headers={},
    ) as archive:
        for path, raw in sorted(files.items()):
            archive.addfile(
                _normalized_tar_info(path, len(raw), modes[path]),
                io.BytesIO(raw),
            )


def _write_normalized_tar_tree(
    output_path: Path,
    root: Path,
    manifest_raw: bytes,
    entries: Iterable[Mapping[str, object]],
) -> None:
    entry_by_path = {str(entry["path"]): entry for entry in entries}
    paths = sorted((MANIFEST_PATH, *entry_by_path))
    with tarfile.open(
        output_path,
        mode="w",
        format=tarfile.PAX_FORMAT,
        pax_headers={},
    ) as archive:
        for path in paths:
            if path == MANIFEST_PATH:
                raw = manifest_raw
                mode = 0o644
            else:
                entry = entry_by_path[path]
                raw, mode = _read_regular_file(root / path, path)
                expected_mode = int(str(entry["mode"]), 8)
                if mode != expected_mode:
                    raise DistributionError(
                        f"{path}: unpacked mode changed during canonical replay"
                    )
            archive.addfile(
                _normalized_tar_info(path, len(raw), mode),
                io.BytesIO(raw),
            )


def _files_are_byte_identical(left: Path, right: Path) -> bool:
    try:
        if left.stat().st_size != right.stat().st_size:
            return False
        with left.open("rb") as left_handle, right.open("rb") as right_handle:
            while True:
                left_chunk = left_handle.read(1024 * 1024)
                right_chunk = right_handle.read(1024 * 1024)
                if left_chunk != right_chunk:
                    return False
                if not left_chunk:
                    return True
    except OSError as exc:
        raise DistributionError(
            f"archive canonical-byte comparison failed ({exc.__class__.__name__})"
        ) from exc


def write_distribution_archive(
    files: Mapping[str, bytes],
    *,
    active_skill_ids: tuple[str, ...],
    source_commit: str,
    source_registry_digests: Mapping[str, str],
    output_path: Path,
    modes: Mapping[str, int] | None = None,
    excluded_legacy_artifacts: Iterable[Mapping[str, object]] = (),
    source_state: str = "candidate-worktree",
    protected_branch: str = "not-asserted",
    build_command: str = BUILD_COMMAND,
    overwrite: bool = False,
) -> dict[str, object]:
    """Write a normalized tar archive from an already selected byte inventory."""

    entries, normalized, normalized_modes = _canonical_file_entries(
        files,
        active_skill_ids=active_skill_ids,
        modes=modes,
    )
    manifest = _manifest(
        entries=entries,
        active_skill_ids=active_skill_ids,
        source_commit=source_commit,
        source_registry_digests=source_registry_digests,
        excluded_legacy_artifacts=excluded_legacy_artifacts,
        source_state=source_state,
        protected_branch=protected_branch,
        build_command=build_command,
    )
    manifest_raw = _json_bytes(manifest)
    _scan_content(MANIFEST_PATH, manifest_raw)
    selected_output = Path(output_path)
    if selected_output.exists() and not overwrite:
        raise DistributionError(f"output already exists: {selected_output.name}")
    selected_output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{selected_output.name}.",
            suffix=".tmp",
            dir=selected_output.parent,
            delete=False,
        ) as temporary_handle:
            temporary = Path(temporary_handle.name)
        archive_files = {MANIFEST_PATH: manifest_raw, **normalized}
        archive_modes = {MANIFEST_PATH: 0o644, **normalized_modes}
        _write_normalized_tar_bytes(
            temporary,
            archive_files,
            archive_modes,
        )
        if selected_output.exists() and not overwrite:
            raise DistributionError(f"output appeared during build: {selected_output.name}")
        os.replace(temporary, selected_output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    archive_raw = selected_output.read_bytes()
    return {
        "active_skill_count": len(active_skill_ids),
        "archive_path": str(selected_output),
        "archive_sha256": _sha256(archive_raw),
        "archive_size": len(archive_raw),
        "excluded_legacy_official_artifact_count": len(
            manifest["excluded_legacy_official_artifacts"]
        ),
        "file_count": len(entries),
        "manifest_sha256": _sha256(manifest_raw),
    }


def _read_regular_file(path: Path, label: str) -> tuple[bytes, int]:
    try:
        before = path.lstat()
    except OSError as exc:
        raise DistributionError(f"{label}: unreadable ({exc.__class__.__name__})") from exc
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or before.st_nlink != 1
    ):
        raise DistributionError(f"{label}: expected one ordinary non-linked file")
    if before.st_size > MAX_FILE_BYTES:
        raise DistributionError(f"{label}: file exceeds the distribution size limit")
    try:
        raw = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise DistributionError(f"{label}: unreadable ({exc.__class__.__name__})") from exc
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_mode,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_mode,
    )
    if identity_before != identity_after or after.st_nlink != 1:
        raise DistributionError(f"{label}: file changed while selected")
    mode = 0o755 if before.st_mode & 0o111 else 0o644
    return raw, mode


def _canonical_registry_data(
    root: Path,
) -> tuple[dict[str, Any], dict[str, str], dict[str, bytes]]:
    loaded: dict[str, Any] = {}
    digests: dict[str, str] = {}
    snapshots: dict[str, bytes] = {}
    for relative in sorted(set((*FILTERED_REGISTRY_PATHS, *SOURCE_REGISTRY_PATHS))):
        path = root / relative
        try:
            raw, _ = _read_regular_file(path, relative)
            loaded[relative] = load_yaml_strict(path, Path(relative).name)
        except (OSError, ValueError) as exc:
            raise DistributionError(f"{relative}: invalid registry ({exc})") from exc
        if relative in SOURCE_REGISTRY_PATHS:
            snapshot_path = (
                SOURCE_SNAPSHOT_PREFIX / PurePosixPath(relative).name
            ).as_posix()
            snapshots[snapshot_path] = raw
            digests[snapshot_path] = _sha256(raw)
    return loaded, digests, snapshots


def _active_ids(skill_registry: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    skills = skill_registry.get("skills")
    if not isinstance(skills, dict) or not skills:
        raise DistributionError("skill registry must contain a nonempty skills mapping")
    active: list[str] = []
    development: list[str] = []
    for skill_id, entry in skills.items():
        if (
            not isinstance(skill_id, str)
            or SKILL_ID_RE.fullmatch(skill_id) is None
            or not isinstance(entry, dict)
        ):
            raise DistributionError("skill registry contains an invalid Skill record")
        lifecycle = entry.get("lifecycle")
        if lifecycle == "active":
            active.append(skill_id)
        elif lifecycle == "development":
            development.append(skill_id)
        elif lifecycle != "planned":
            raise DistributionError(f"{skill_id}: unsupported Skill lifecycle")
    return tuple(sorted(active)), tuple(sorted(development))


def _filter_routes(
    data: Mapping[str, Any],
    active: frozenset[str],
) -> dict[str, Any]:
    result = copy.deepcopy(dict(data))
    routes = result.get("routes")
    if not isinstance(routes, dict):
        raise DistributionError("operation-routes.yaml: routes must be a mapping")
    result["routes"] = {
        key: value
        for key, value in routes.items()
        if key in active and isinstance(value, dict) and value.get("lifecycle") == "active"
    }
    response = result.get("response_policy")
    if isinstance(response, dict):
        terminal = response.get("terminal_intent_routes")
        if isinstance(terminal, dict):
            for intent, target in tuple(terminal.items()):
                if target is not None and target not in active:
                    terminal[intent] = None
    for route in result["routes"].values():
        handoff = route.get("handoff")
        if isinstance(handoff, dict):
            consumers = handoff.get("consumers")
            if isinstance(consumers, list):
                handoff["consumers"] = [item for item in consumers if item in active]
            if "future_consumers" in handoff:
                handoff["future_consumers"] = []
    return result


def _filtered_registries(
    loaded: Mapping[str, Any],
    active_ids: tuple[str, ...],
) -> dict[str, bytes]:
    active = frozenset(active_ids)
    skill_data = copy.deepcopy(loaded["registry/skill-registry.yaml"])
    skill_data["skills"] = {
        key: value for key, value in skill_data["skills"].items() if key in active
    }

    software_data = copy.deepcopy(loaded["registry/software-registry.yaml"])
    software = software_data.get("software")
    if not isinstance(software, dict):
        raise DistributionError("software-registry.yaml: software must be a mapping")
    software_data["software"] = {
        key: value
        for key, value in software.items()
        if isinstance(value, dict)
        and value.get("lifecycle") == "active"
        and value.get("calculation_skill") in active
    }
    software_data["planned_software"] = {}

    interface_data = copy.deepcopy(loaded["registry/interface-registry.yaml"])
    interfaces = interface_data.get("interfaces")
    if not isinstance(interfaces, dict):
        raise DistributionError("interface-registry.yaml: interfaces must be a mapping")
    interface_data["interfaces"] = {
        key: value
        for key, value in interfaces.items()
        if isinstance(value, dict) and value.get("lifecycle") == "active"
    }

    authority_data = copy.deepcopy(
        loaded["registry/official-source-authorities.yaml"]
    )
    authorities = authority_data.get("authorities")
    if not isinstance(authorities, dict):
        raise DistributionError(
            "official-source-authorities.yaml: authorities must be a mapping"
        )
    consumer_data = copy.deepcopy(
        loaded["registry/official-document-consumers.yaml"]
    )
    bindings = consumer_data.get("bindings")
    if not isinstance(bindings, list):
        raise DistributionError(
            "official-document-consumers.yaml: bindings must be a list"
        )
    consumer_data["bindings"] = [
        item
        for item in bindings
        if isinstance(item, dict) and item.get("consumer_skill_id") in active
    ]
    required_authorities = {
        item.get("authority_id")
        for item in consumer_data["bindings"]
        if isinstance(item.get("authority_id"), str)
    }
    authority_data["authorities"] = {
        key: value
        for key, value in authorities.items()
        if key in required_authorities
        and isinstance(value, dict)
        and value.get("lifecycle") == "active"
    }
    if set(authority_data["authorities"]) != required_authorities:
        missing = sorted(required_authorities - set(authority_data["authorities"]))
        raise DistributionError(
            "official-source-authorities.yaml: active consumer authority closure "
            f"is unresolved: {missing}"
        )

    expectation_data = copy.deepcopy(
        loaded["registry/official-document-bundle-expectations.yaml"]
    )
    expectations = expectation_data.get("skills")
    if not isinstance(expectations, dict):
        raise DistributionError(
            "official-document-bundle-expectations.yaml: skills must be a mapping"
        )
    expectation_data["skills"] = {
        key: value for key, value in expectations.items() if key in active
    }

    filtered: dict[str, Any] = {
        "registry/active-evidence.yaml": copy.deepcopy(
            loaded["registry/active-evidence.yaml"]
        ),
        "registry/skill-registry.yaml": skill_data,
        "registry/software-registry.yaml": software_data,
        "registry/interface-registry.yaml": interface_data,
        "registry/operation-routes.yaml": _filter_routes(
            loaded["registry/operation-routes.yaml"],
            active,
        ),
        "registry/official-source-authorities.yaml": authority_data,
        "registry/official-document-consumers.yaml": consumer_data,
        "registry/official-document-bundle-expectations.yaml": expectation_data,
        "registry/official-document-storage-discovery.yaml": copy.deepcopy(
            loaded["registry/official-document-storage-discovery.yaml"]
        ),
        "registry/semantic-obligations.yaml": copy.deepcopy(
            loaded["registry/semantic-obligations.yaml"]
        ),
    }
    return {path: _yaml_bytes(value) for path, value in sorted(filtered.items())}


def _walk_source_tree(
    root: Path,
    relative_root: str,
) -> Iterable[tuple[str, bytes, int]]:
    absolute_root = root / relative_root
    try:
        root_stat = absolute_root.lstat()
    except OSError as exc:
        raise DistributionError(
            f"{relative_root}: source tree is unavailable ({exc.__class__.__name__})"
        ) from exc
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise DistributionError(f"{relative_root}: source tree is aliased or unsafe")
    for path in sorted(absolute_root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        try:
            item_stat = path.lstat()
        except OSError as exc:
            raise DistributionError(
                f"{relative}: unreadable ({exc.__class__.__name__})"
            ) from exc
        if stat.S_ISDIR(item_stat.st_mode):
            if stat.S_ISLNK(item_stat.st_mode):
                raise DistributionError(f"{relative}: symlink directory is forbidden")
            continue
        if stat.S_ISLNK(item_stat.st_mode) or not stat.S_ISREG(item_stat.st_mode):
            raise DistributionError(f"{relative}: non-regular source file is forbidden")
        if _is_sensitive_path(relative):
            if "__pycache__" in PurePosixPath(relative).parts or relative.endswith(
                (".pyc", ".pyo")
            ):
                continue
        _scan_release_path(relative)
        if _is_sensitive_path(relative):
            raise DistributionError(f"{relative}: sensitive or runtime path is forbidden")
        raw, mode = _read_regular_file(path, relative)
        yield relative, raw, mode


def collect_source_selection(root: Path) -> SourceSelection:
    try:
        selected_root = Path(root).resolve(strict=True)
    except OSError as exc:
        raise DistributionError(
            f"repository root is unavailable ({exc.__class__.__name__})"
        ) from exc
    loaded, registry_digests, registry_snapshots = _canonical_registry_data(
        selected_root
    )
    active, development = _active_ids(loaded["registry/skill-registry.yaml"])
    if not active:
        raise DistributionError("active-only distribution has no active Skills")
    skill_registry = loaded["registry/skill-registry.yaml"]["skills"]
    files = _filtered_registries(loaded, active)
    files.update(registry_snapshots)
    modes = {path: 0o644 for path in files}
    excluded_legacy: list[dict[str, object]] = []

    for skill_id in active:
        entry = skill_registry[skill_id]
        path = entry.get("path")
        expected = f"skills/{skill_id}"
        if path != expected:
            raise DistributionError(f"{skill_id}: active Skill path must be {expected}")
        for relative, raw, mode in _walk_source_tree(selected_root, expected):
            if _is_legacy_official_artifact(relative):
                excluded_legacy.append(
                    {
                        "path": relative,
                        "sha256": _sha256(raw),
                        "size": len(raw),
                    }
                )
                continue
            _validate_release_path(relative, frozenset(active))
            _scan_content(relative, raw)
            files[relative] = raw
            modes[relative] = mode

    for relative, raw, mode in _walk_source_tree(selected_root, "contracts"):
        _validate_release_path(relative, frozenset(active))
        _scan_content(relative, raw)
        files[relative] = raw
        modes[relative] = mode

    for relative in VERIFICATION_TOOL_PATHS:
        raw, mode = _read_regular_file(selected_root / relative, relative)
        _validate_release_path(relative, frozenset(active))
        _scan_content(relative, raw)
        files[relative] = raw
        modes[relative] = mode

    dependency_raw, dependency_mode = _read_regular_file(
        selected_root / DEPENDENCY_MANIFEST_PATH,
        DEPENDENCY_MANIFEST_PATH,
    )
    _validate_release_path(DEPENDENCY_MANIFEST_PATH, frozenset(active))
    _scan_content(DEPENDENCY_MANIFEST_PATH, dependency_raw)
    files[DEPENDENCY_MANIFEST_PATH] = dependency_raw
    modes[DEPENDENCY_MANIFEST_PATH] = dependency_mode

    # Re-scan the complete post-transform inventory so filtered registries and
    # source snapshots cannot bypass the same policy applied to source files.
    for relative, raw in sorted(files.items()):
        _validate_release_path(relative, frozenset(active))
        _scan_content(relative, raw)

    return SourceSelection(
        active_skill_ids=active,
        development_skill_ids=development,
        files=dict(sorted(files.items())),
        modes=dict(sorted(modes.items())),
        source_registry_digests=registry_digests,
        excluded_legacy_artifacts=tuple(
            sorted(excluded_legacy, key=lambda record: str(record["path"]))
        ),
    )


def _git_bytes(root: Path, arguments: list[str]) -> bytes:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=False,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DistributionError(f"Git identity lookup failed ({exc.__class__.__name__})") from exc
    if result.returncode != 0:
        raise DistributionError("Git identity lookup failed")
    return result.stdout


def _git(root: Path, arguments: list[str]) -> str:
    try:
        return _git_bytes(root, arguments).decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise DistributionError("Git identity output is not UTF-8") from exc


def _commit_tree(
    root: Path,
    source_commit: str,
) -> dict[str, tuple[str, str]]:
    raw = _git_bytes(
        root,
        ["ls-tree", "-r", "-z", "--full-tree", source_commit],
    )
    tree: dict[str, tuple[str, str]] = {}
    try:
        records = raw.split(b"\0")
        for record in records:
            if not record:
                continue
            metadata, path_raw = record.split(b"\t", 1)
            mode_raw, kind_raw, object_raw = metadata.split(b" ", 2)
            path = path_raw.decode("utf-8")
            mode = mode_raw.decode("ascii")
            kind = kind_raw.decode("ascii")
            object_id = object_raw.decode("ascii")
            if path in tree:
                raise ValueError
            if kind == "blob":
                tree[path] = (mode, object_id)
    except (UnicodeDecodeError, ValueError) as exc:
        raise DistributionError("Git commit tree inventory is malformed") from exc
    return tree


def _git_blob_object_id(raw: bytes, object_format: str) -> str:
    if object_format not in {"sha1", "sha256"}:
        raise DistributionError(
            f"unsupported Git object format: {object_format}"
        )
    digest = hashlib.new(object_format)
    digest.update(f"blob {len(raw)}\0".encode("ascii"))
    digest.update(raw)
    return digest.hexdigest()


def _require_selection_matches_clean_commit(
    root: Path,
    selection: SourceSelection,
    source_commit: str,
) -> None:
    status = _git(
        root,
        ["status", "--porcelain=v1", "--untracked-files=all"],
    )
    if status:
        raise DistributionError(
            "require-clean-commit rejects a dirty tracked or untracked worktree"
        )
    object_format = _git(root, ["rev-parse", "--show-object-format"])
    tree = _commit_tree(root, source_commit)
    snapshot_sources = {
        _source_snapshot_path(path): path for path in SOURCE_REGISTRY_PATHS
    }
    source_inputs: dict[str, tuple[bytes, int]] = {}

    def add_source(path: str, raw: bytes, mode: int) -> None:
        previous = source_inputs.get(path)
        value = (raw, mode)
        if previous is not None and previous != value:
            raise DistributionError(
                f"{path}: source input identity is internally inconsistent"
            )
        source_inputs[path] = value

    for archive_path, raw in selection.files.items():
        if archive_path in FILTERED_REGISTRY_PATHS:
            continue
        source_path = snapshot_sources.get(archive_path, archive_path)
        if source_path != archive_path:
            source_raw, source_mode = _read_regular_file(
                root / source_path,
                source_path,
            )
            if source_raw != raw:
                raise DistributionError(
                    f"{source_path}: source snapshot differs from selected bytes"
                )
            add_source(source_path, source_raw, source_mode)
        else:
            add_source(
                source_path,
                raw,
                selection.modes[archive_path],
            )
    for receipt in selection.excluded_legacy_artifacts:
        path = str(receipt["path"])
        raw, mode = _read_regular_file(root / path, path)
        if (
            len(raw) != receipt["size"]
            or _sha256(raw) != receipt["sha256"]
        ):
            raise DistributionError(
                f"{path}: externalization receipt changed before commit binding"
            )
        add_source(path, raw, mode)

    for path, (raw, mode) in sorted(source_inputs.items()):
        entry = tree.get(path)
        if entry is None:
            raise DistributionError(
                f"{path}: selected source input is not tracked by the "
                "declared Git commit"
            )
        git_mode, object_id = entry
        expected_mode = {"100644": 0o644, "100755": 0o755}.get(git_mode)
        if expected_mode is None or mode != expected_mode:
            raise DistributionError(
                f"{path}: selected source mode differs from the declared "
                "Git commit"
            )
        if _git_blob_object_id(raw, object_format) != object_id:
            raise DistributionError(
                f"{path}: selected source bytes differ from the declared "
                "Git commit"
            )


def build_distribution(
    root: Path,
    output_path: Path,
    *,
    overwrite: bool = False,
    protected_branch: bool = False,
    require_clean_commit: bool = False,
) -> dict[str, object]:
    selected_root = Path(root).resolve()
    source_commit = _git(selected_root, ["rev-parse", "--verify", "HEAD^{commit}"])
    selection = collect_source_selection(selected_root)
    if require_clean_commit:
        _require_selection_matches_clean_commit(
            selected_root,
            selection,
            source_commit,
        )
        source_state = "clean-commit"
    else:
        status = _git(
            selected_root,
            ["status", "--porcelain=v1", "--untracked-files=all"],
        )
        source_state = "clean-commit" if not status else "candidate-worktree"
    report = write_distribution_archive(
        selection.files,
        active_skill_ids=selection.active_skill_ids,
        source_commit=source_commit,
        source_registry_digests=selection.source_registry_digests,
        output_path=output_path,
        modes=selection.modes,
        excluded_legacy_artifacts=selection.excluded_legacy_artifacts,
        source_state=source_state,
        protected_branch="user-asserted" if protected_branch else "not-asserted",
        build_command=(
            RELEASE_BUILD_COMMAND
            if require_clean_commit
            else BUILD_COMMAND
        ),
        overwrite=overwrite,
    )
    return {
        **report,
        "active_skill_ids": list(selection.active_skill_ids),
        "development_skill_source_trees_included": 0,
        "source_commit": source_commit,
        "source_state": source_state,
    }


def _parse_manifest(raw: bytes) -> dict[str, Any]:
    _scan_content(MANIFEST_PATH, raw)
    try:
        manifest = strict_json.loads_value(
            raw,
            MANIFEST_PATH,
            max_bytes=32 * 1024 * 1024,
            max_nodes=1_000_000,
            max_depth=32,
            max_string_chars=1_000_000,
        )
    except strict_json.StrictJSONError as exc:
        raise DistributionError(f"manifest is invalid ({exc})") from exc
    expected = {
        "active_skill_ids",
        "artifact_type",
        "build",
        "contract_catalog_sha256",
        "excluded_legacy_official_artifact_count",
        "excluded_legacy_official_artifacts",
        "files",
        "schema_version",
        "source_commit",
        "source_registry_sha256",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected:
        raise DistributionError("manifest has unsupported fields")
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("artifact_type")
        != "vibe-dft-active-only-source-distribution"
    ):
        raise DistributionError("manifest identity is invalid")
    build = manifest.get("build")
    if (
        not isinstance(build, dict)
        or set(build)
        != {
            "command",
            "environment_assumptions",
            "protected_branch",
            "python_version",
            "source_state",
            "tool_version",
        }
        or build.get("command") not in {BUILD_COMMAND, RELEASE_BUILD_COMMAND}
        or build.get("environment_assumptions")
        != list(BUILD_ENVIRONMENT_ASSUMPTIONS)
        or build.get("protected_branch")
        not in {"user-asserted", "not-asserted"}
        or build.get("source_state")
        not in {"clean-commit", "candidate-worktree"}
        or (
            build.get("command") == RELEASE_BUILD_COMMAND
            and build.get("source_state") != "clean-commit"
        )
        or build.get("tool_version") != TOOL_VERSION
        or not isinstance(build.get("python_version"), str)
        or re.fullmatch(
            r"[0-9]+(?:\.[0-9]+){1,3}(?:[-+._A-Za-z0-9]*)?",
            build["python_version"],
        )
        is None
    ):
        raise DistributionError("manifest build provenance is invalid")
    active_value = manifest.get("active_skill_ids")
    if (
        not isinstance(active_value, list)
        or not all(isinstance(item, str) for item in active_value)
    ):
        raise DistributionError("manifest active_skill_ids is invalid")
    active = tuple(active_value)
    if tuple(sorted(active)) != active or len(set(active)) != len(active):
        raise DistributionError("manifest active_skill_ids is not canonical")
    if COMMIT_RE.fullmatch(str(manifest.get("source_commit"))) is None:
        raise DistributionError("manifest source_commit is invalid")
    if SHA256_RE.fullmatch(str(manifest.get("contract_catalog_sha256"))) is None:
        raise DistributionError("manifest contract catalog digest is invalid")
    exclusion_count = manifest.get("excluded_legacy_official_artifact_count")
    exclusions = manifest.get("excluded_legacy_official_artifacts")
    if (
        not isinstance(exclusion_count, int)
        or isinstance(exclusion_count, bool)
        or not isinstance(exclusions, list)
        or exclusion_count != len(exclusions)
    ):
        raise DistributionError(
            "manifest excluded legacy official-document inventory is invalid"
        )
    registry_digests = manifest.get("source_registry_sha256")
    if not isinstance(registry_digests, dict):
        raise DistributionError("manifest source registry digests are invalid")
    for path, digest in registry_digests.items():
        _safe_archive_path(path)
        if not path.startswith("registry/") or SHA256_RE.fullmatch(str(digest)) is None:
            raise DistributionError("manifest source registry digest is invalid")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise DistributionError("manifest files must be a nonempty list")
    previous = ""
    seen: set[str] = set()
    active_set = frozenset(active)
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"mode", "path", "sha256", "size"}:
            raise DistributionError("manifest file record is invalid")
        path = entry.get("path")
        if not isinstance(path, str):
            raise DistributionError("manifest file path is invalid")
        _validate_release_path(path, active_set)
        if path <= previous or path in seen:
            raise DistributionError("manifest file paths are not sorted and unique")
        previous = path
        seen.add(path)
        if entry.get("mode") not in {"0644", "0755"}:
            raise DistributionError(f"{path}: manifest mode is invalid")
        if SHA256_RE.fullmatch(str(entry.get("sha256"))) is None:
            raise DistributionError(f"{path}: manifest digest is invalid")
        size = entry.get("size")
        if (
            not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or size > MAX_FILE_BYTES
        ):
            raise DistributionError(f"{path}: manifest size is invalid")
    for skill_id in active:
        if f"skills/{skill_id}/SKILL.md" not in seen:
            raise DistributionError(f"{skill_id}: active Skill entrypoint is missing")
    previous_exclusion = ""
    for record in exclusions:
        if (
            not isinstance(record, dict)
            or set(record) != {"path", "sha256", "size"}
            or not isinstance(record.get("path"), str)
            or not isinstance(record.get("size"), int)
            or isinstance(record.get("size"), bool)
            or record["size"] < 0
            or record["size"] > MAX_FILE_BYTES
            or SHA256_RE.fullmatch(str(record.get("sha256"))) is None
        ):
            raise DistributionError(
                "manifest excluded legacy official-document receipt is invalid"
            )
        path = _safe_archive_path(record["path"])
        parts = PurePosixPath(path).parts
        if (
            not _is_legacy_official_artifact(path)
            or len(parts) < 3
            or parts[0] != "skills"
            or parts[1] not in active_set
            or path in seen
            or path <= previous_exclusion
        ):
            raise DistributionError(
                "manifest excluded legacy official-document inventory is "
                "not exact active-only metadata"
            )
        previous_exclusion = path
    return manifest


def _source_snapshot_path(registry_path: str) -> str:
    return (
        SOURCE_SNAPSHOT_PREFIX / PurePosixPath(registry_path).name
    ).as_posix()


def _validate_source_registry_snapshots(
    root: Path,
    manifest: Mapping[str, Any],
    manifest_paths: frozenset[str],
) -> dict[str, str]:
    declared = manifest.get("source_registry_sha256")
    if not isinstance(declared, dict):
        raise DistributionError("source registry snapshot digests are invalid")
    expected_paths = {
        _source_snapshot_path(path) for path in SOURCE_REGISTRY_PATHS
    }
    observed_paths = {
        path
        for path in manifest_paths
        if PurePosixPath(path).is_relative_to(SOURCE_SNAPSHOT_PREFIX)
    }
    expected_registry_inventory = {
        *FILTERED_REGISTRY_PATHS,
        *expected_paths,
    }
    observed_registry_inventory = {
        path for path in manifest_paths if path.startswith("registry/")
    }
    if set(declared) != expected_paths:
        missing = sorted(expected_paths - set(declared))
        extra = sorted(set(declared) - expected_paths)
        raise DistributionError(
            "source registry snapshot set is not exact; "
            f"missing={missing[:3]} extra={extra[:3]}"
        )
    if observed_paths != expected_paths:
        raise DistributionError(
            "source registry snapshot inventory is not exact or manifest-bound"
        )
    if observed_registry_inventory != expected_registry_inventory:
        raise DistributionError(
            "active distribution registry inventory is not exact"
        )
    verified: dict[str, str] = {}
    for path in sorted(expected_paths):
        raw, _ = _read_regular_file(root / path, path)
        digest = _sha256(raw)
        if digest != declared[path]:
            raise DistributionError(
                f"{path}: source registry snapshot digest does not match exact bytes"
            )
        try:
            load_yaml_strict(root / path, PurePosixPath(path).name)
        except (OSError, ValueError) as exc:
            raise DistributionError(
                f"{path}: source registry snapshot YAML is invalid ({exc})"
            ) from exc
        verified[path] = digest
    return verified


def _validate_filtered_registry_projection(
    root: Path,
    active_ids: tuple[str, ...],
) -> None:
    source_registries: dict[str, Any] = {}
    for registry_path in SOURCE_REGISTRY_PATHS:
        snapshot_path = _source_snapshot_path(registry_path)
        try:
            source_registries[registry_path] = load_yaml_strict(
                root / snapshot_path,
                f"source snapshot {PurePosixPath(registry_path).name}",
            )
        except (OSError, ValueError) as exc:
            raise DistributionError(
                f"{snapshot_path}: source registry projection input is invalid "
                f"({exc})"
            ) from exc
    source_active, _ = _active_ids(
        source_registries["registry/skill-registry.yaml"]
    )
    if source_active != active_ids:
        raise DistributionError(
            "manifest active Skill ids differ from the canonical source "
            "registry projection"
        )
    expected = _filtered_registries(source_registries, active_ids)
    if set(expected) != set(FILTERED_REGISTRY_PATHS):
        raise DistributionError(
            "canonical source registry projection is incomplete"
        )
    for registry_path in FILTERED_REGISTRY_PATHS:
        raw, _ = _read_regular_file(root / registry_path, registry_path)
        if raw != expected[registry_path]:
            raise DistributionError(
                f"{registry_path}: live filtered registry differs from the "
                "canonical source snapshot projection"
            )


def _verify_local_hash_ref(
    root: Path,
    reference: object,
    *,
    label: str,
    manifest_paths: frozenset[str],
) -> str:
    if (
        not isinstance(reference, dict)
        or set(reference) != {"path", "sha256"}
        or not isinstance(reference.get("path"), str)
        or SHA256_RE.fullmatch(str(reference.get("sha256"))) is None
    ):
        raise DistributionError(f"{label}: local hash reference is invalid")
    path = _safe_archive_path(reference["path"])
    if path not in manifest_paths:
        raise DistributionError(f"{label}: referenced file is absent from the archive")
    raw, _ = _read_regular_file(root / path, path)
    if _sha256(raw) != reference["sha256"]:
        raise DistributionError(f"{label}: referenced file hash does not match")
    return path


def _validate_dependency_lock_closure(
    root: Path,
    manifest_paths: frozenset[str],
) -> None:
    observed_tools = {
        path for path in manifest_paths if path.startswith("tools/")
    }
    if observed_tools != set(VERIFICATION_TOOL_PATHS):
        raise DistributionError(
            "official-document verification tool inventory is not exact"
        )
    lock_path = "contracts/official-document-pack-builder-lock.json"
    if lock_path not in manifest_paths:
        raise DistributionError("official-document builder dependency lock is missing")
    try:
        lock = strict_json.load_object(root / lock_path, lock_path)
    except (OSError, strict_json.StrictJSONError) as exc:
        raise DistributionError(
            f"official-document builder dependency lock is invalid ({exc})"
        ) from exc

    references: list[tuple[str, object]] = [
        ("dependency_manifest_ref", lock.get("dependency_manifest_ref")),
    ]
    for field in (
        "configuration_contract_refs",
        "runtime_refs",
        "output_contract_refs",
    ):
        values = lock.get(field)
        if not isinstance(values, list):
            raise DistributionError(
                f"official-document builder dependency lock {field} is invalid"
            )
        references.extend(
            (f"{field}/{index}", reference)
            for index, reference in enumerate(values)
        )
    adapters = lock.get("adapters")
    if not isinstance(adapters, dict):
        raise DistributionError(
            "official-document builder dependency lock adapters are invalid"
        )
    for adapter_id, adapter in adapters.items():
        reference = (
            adapter.get("input_contract_ref")
            if isinstance(adapter, dict)
            else None
        )
        references.append((f"adapters/{adapter_id}/input_contract_ref", reference))
        replay_paths = (
            adapter.get("replay_runtime_paths")
            if isinstance(adapter, dict)
            else None
        )
        if not isinstance(replay_paths, list):
            raise DistributionError(
                f"official-document builder dependency lock adapter {adapter_id} "
                "replay closure is invalid"
            )
        for index, path in enumerate(replay_paths):
            if not isinstance(path, str) or path not in manifest_paths:
                raise DistributionError(
                    "official-document builder replay dependency is absent from "
                    f"the archive: {adapter_id}/{index}"
                )
    for label, reference in references:
        _verify_local_hash_ref(
            root,
            reference,
            label=f"builder-lock/{label}",
            manifest_paths=manifest_paths,
        )


def _validate_consumer_processor_closure(
    root: Path,
    consumer_data: Mapping[str, Any],
    manifest_paths: frozenset[str],
) -> None:
    processors = consumer_data.get("processors")
    if not isinstance(processors, dict) or not processors:
        raise DistributionError("official-document consumer processors are missing")
    for processor_id, processor in processors.items():
        if not isinstance(processor, dict):
            raise DistributionError(
                f"official-document consumer processor {processor_id} is invalid"
            )
        for field in (
            "implementation_ref",
            "configuration_ref",
            "dependency_lock_ref",
        ):
            _verify_local_hash_ref(
                root,
                processor.get(field),
                label=f"consumer-processors/{processor_id}/{field}",
                manifest_paths=manifest_paths,
            )


def _validate_packaged_registries(
    root: Path,
    active_ids: tuple[str, ...],
    manifest_paths: frozenset[str],
) -> None:
    active = frozenset(active_ids)
    skill_path = root / "registry" / "skill-registry.yaml"
    try:
        skills_data = load_yaml_strict(skill_path, "skill-registry.yaml")
    except (OSError, ValueError) as exc:
        raise DistributionError(f"packaged skill registry is invalid ({exc})") from exc
    skills = skills_data.get("skills")
    if not isinstance(skills, dict) or set(skills) != active:
        raise DistributionError("packaged skill registry is not exact active-only metadata")
    for skill_id, entry in skills.items():
        if (
            not isinstance(entry, dict)
            or entry.get("lifecycle") != "active"
            or entry.get("path") != f"skills/{skill_id}"
        ):
            raise DistributionError(f"{skill_id}: packaged Skill metadata is not active")

    lifecycle_registries = (
        ("interface-registry.yaml", "interfaces"),
        ("operation-routes.yaml", "routes"),
    )
    for filename, field in lifecycle_registries:
        path = root / "registry" / filename
        if not path.is_file():
            continue
        try:
            data = load_yaml_strict(path, filename)
        except (OSError, ValueError) as exc:
            raise DistributionError(f"{filename}: packaged registry is invalid ({exc})") from exc
        entries = data.get(field)
        if not isinstance(entries, dict):
            raise DistributionError(f"{filename}: {field} must be a mapping")
        if any(
            not isinstance(entry, dict) or entry.get("lifecycle") != "active"
            for entry in entries.values()
        ):
            raise DistributionError(f"{filename}: non-active metadata is forbidden")
        if filename == "operation-routes.yaml":
            if set(entries) != active:
                raise DistributionError("operation routes are not exact active-only routes")
            response = data.get("response_policy")
            terminal = (
                response.get("terminal_intent_routes")
                if isinstance(response, dict)
                else None
            )
            if not isinstance(terminal, dict) or any(
                target is not None and target not in active
                for target in terminal.values()
            ):
                raise DistributionError(
                    "operation routes contain a non-active terminal target"
                )
            for skill_id, route in entries.items():
                handoff = route.get("handoff")
                if not isinstance(handoff, dict):
                    continue
                consumers = handoff.get("consumers", [])
                future = handoff.get("future_consumers", [])
                if (
                    not isinstance(consumers, list)
                    or any(item not in active for item in consumers)
                    or future not in (None, [])
                ):
                    raise DistributionError(
                        f"{skill_id}: route contains non-active consumer metadata"
                    )

    software_path = root / "registry" / "software-registry.yaml"
    if software_path.is_file():
        try:
            software_data = load_yaml_strict(software_path, "software-registry.yaml")
        except (OSError, ValueError) as exc:
            raise DistributionError(f"software registry is invalid ({exc})") from exc
        if software_data.get("planned_software") != {}:
            raise DistributionError("planned software metadata is forbidden")
        software = software_data.get("software")
        if not isinstance(software, dict) or any(
            not isinstance(item, dict)
            or item.get("lifecycle") != "active"
            or item.get("calculation_skill") not in active
            for item in software.values()
        ):
            raise DistributionError("software registry is not active-only")

    expectation_path = (
        root / "registry" / "official-document-bundle-expectations.yaml"
    )
    try:
        expectation_data = load_yaml_strict(
            expectation_path,
            "official-document-bundle-expectations.yaml",
        )
    except (OSError, ValueError) as exc:
        raise DistributionError(
            f"bundle expectation registry is invalid ({exc})"
        ) from exc
    expectations = expectation_data.get("skills")
    if not isinstance(expectations, dict) or set(expectations) != active:
        raise DistributionError("bundle expectations are not exact active-only metadata")
    for skill_id in active_ids:
        specification = expectations[skill_id]
        if not isinstance(specification, dict) or set(specification) != {
            "entrypoint",
            "expectation",
        }:
            raise DistributionError(
                f"{skill_id}: bundle expectation record is not exact"
            )
        if specification.get("expectation") != "pack-required":
            raise DistributionError(
                f"{skill_id}: active distribution bundle must be pack-required"
            )
        entrypoint = (
            f"skills/{skill_id}/references/official-source-pack/bundle.json"
        )
        if specification.get("entrypoint") != entrypoint:
            raise DistributionError(
                f"{skill_id}: active distribution bundle entrypoint is noncanonical"
            )
        if entrypoint not in manifest_paths:
            raise DistributionError(
                f"{skill_id}: active bundle.json is missing from the manifest"
            )
        _read_regular_file(root / entrypoint, entrypoint)

    consumer_path = root / "registry" / "official-document-consumers.yaml"
    if consumer_path.is_file():
        try:
            consumer_data = load_yaml_strict(
                consumer_path,
                "official-document-consumers.yaml",
            )
        except (OSError, ValueError) as exc:
            raise DistributionError(
                f"official-document consumer registry is invalid ({exc})"
            ) from exc
        bindings = consumer_data.get("bindings")
        if not isinstance(bindings, list):
            raise DistributionError("official-document consumers must be a list")
        authority_ids: set[str] = set()
        for binding in bindings:
            skill_id = (
                binding.get("consumer_skill_id")
                if isinstance(binding, dict)
                else None
            )
            if (
                skill_id not in active
                or binding.get("consumer_lifecycle") != "active"
                or binding.get("consumer_path") != f"skills/{skill_id}"
            ):
                raise DistributionError(
                    "official-document consumer metadata is not active-only"
                )
            authority_id = binding.get("authority_id")
            if not isinstance(authority_id, str):
                raise DistributionError(
                    "official-document consumer authority binding is invalid"
                )
            authority_ids.add(authority_id)
        authority_path = root / "registry" / "official-source-authorities.yaml"
        try:
            authority_data = load_yaml_strict(
                authority_path,
                "official-source-authorities.yaml",
            )
        except (OSError, ValueError) as exc:
            raise DistributionError(
                f"official-source authority registry is invalid ({exc})"
            ) from exc
        authorities = authority_data.get("authorities")
        if not isinstance(authorities, dict) or set(authorities) != authority_ids:
            raise DistributionError(
                "official-source authorities are not the exact active consumer "
                "binding closure"
            )
        if any(
            not isinstance(authority, dict)
            or authority.get("lifecycle") != "active"
            for authority in authorities.values()
        ):
            raise DistributionError(
                "official-source authority closure contains non-active metadata"
            )
        _validate_consumer_processor_closure(
            root,
            consumer_data,
            manifest_paths,
        )

    storage_path = root / "registry" / "official-document-storage-discovery.yaml"
    if storage_path.is_file():
        try:
            storage_data = load_yaml_strict(
                storage_path,
                "official-document-storage-discovery.yaml",
            )
        except (OSError, ValueError) as exc:
            raise DistributionError(
                f"official-document storage registry is invalid ({exc})"
            ) from exc
        selected_paths: list[object] = []
        artifact_sets = storage_data.get("artifact_sets")
        if isinstance(artifact_sets, dict):
            for specification in artifact_sets.values():
                selectors = (
                    specification.get("selectors")
                    if isinstance(specification, dict)
                    else None
                )
                if isinstance(selectors, list):
                    selected_paths.extend(
                        selector.get("value")
                        for selector in selectors
                        if isinstance(selector, dict)
                    )
        local_controls = storage_data.get("local_controls")
        if isinstance(local_controls, list):
            selected_paths.extend(
                control.get("path")
                for control in local_controls
                if isinstance(control, dict)
            )
        for value in selected_paths:
            if not isinstance(value, str):
                raise DistributionError("official-document storage path is invalid")
            parts = PurePosixPath(value.rstrip("/")).parts
            if len(parts) < 2 or parts[0] != "skills" or parts[1] not in active:
                raise DistributionError(
                    "official-document storage metadata names a non-active Skill"
                )


PACK_RECORD_FAMILIES = {
    "corpora": ("official-corpus-manifest@1.1", "corpus_id"),
    "slice_manifests": (
        "document-slice-manifest@1.1",
        "slice_manifest_id",
    ),
    "scope_inventory": (
        "skill-document-scope-inventory@1.0",
        "inventory_id",
    ),
    "coverage": ("skill-document-coverage@1.1", "coverage_id"),
}


def _strict_json_object(
    raw: bytes,
    label: str,
    *,
    max_bytes: int = MAX_FILE_BYTES,
) -> dict[str, Any]:
    try:
        return strict_json.loads_object(raw, label, max_bytes=max_bytes)
    except strict_json.StrictJSONError as exc:
        raise DistributionError(
            f"{label}: official-document pack JSON is invalid ({exc})"
        ) from exc


def _single_pack_filename(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not value.isprintable()
        or "\\" in value
    ):
        raise DistributionError(
            f"{label}: official-document pack record path is invalid"
        )
    path = PurePosixPath(value)
    if (
        path.as_posix() != value
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or value == "bundle.json"
    ):
        raise DistributionError(
            f"{label}: official-document pack record path is noncanonical"
        )
    return value


def _scope_enumeration_receipt_valid(
    enumeration: object,
    *,
    expected_source_tree_sha256: str,
    subjects: object,
) -> bool:
    if not isinstance(enumeration, dict):
        return False
    extractor = enumeration.get("extractor")
    method = enumeration.get("method")
    if method == "canonical-reviewed-inventory":
        return extractor is None
    if method != "deterministic-extractor" or not isinstance(extractor, dict):
        return False
    return (
        extractor.get("input_sha256") == expected_source_tree_sha256
        and extractor.get("output_sha256")
        == _canonical_projection_sha256(subjects)
    )


def _slice_source_inventory_valid(
    source_inventory: object,
    manifest_sources: object,
    *,
    status: object,
) -> bool:
    if (
        not isinstance(source_inventory, Mapping)
        or not isinstance(manifest_sources, Mapping)
        or not isinstance(status, str)
    ):
        return False
    included_ids: set[str] = set()
    included_identities: dict[str, object] = {}
    for source_id, source in source_inventory.items():
        if not isinstance(source_id, str) or not isinstance(source, dict):
            return False
        if source.get("disposition") == "included":
            included_ids.add(source_id)
            included_identities[source_id] = source.get("source_identity")
        elif source.get("disposition") != "excluded":
            return False
    if not included_ids:
        return False
    manifest_ids: set[str] = set()
    for source_id, source in manifest_sources.items():
        if (
            not isinstance(source_id, str)
            or not isinstance(source, dict)
            or source_id not in included_identities
            or source.get("source_identity") != included_identities[source_id]
        ):
            return False
        manifest_ids.add(source_id)
    if status == "complete":
        return manifest_ids == included_ids
    return manifest_ids.issubset(included_ids)


def _corpus_source_partition_valid(source_inventory: object) -> bool:
    if not isinstance(source_inventory, Mapping):
        return False
    included = 0
    excluded = 0
    for source_id, source in source_inventory.items():
        if not isinstance(source_id, str) or not isinstance(source, dict):
            return False
        disposition = source.get("disposition")
        if disposition == "included":
            included += 1
        elif disposition == "excluded":
            excluded += 1
        else:
            return False
    return included + excluded > 0 and included + excluded == len(source_inventory)


def _schema_validate_pack_record(
    catalog: Any,
    selector: str,
    value: object,
    label: str,
) -> None:
    try:
        contract = catalog.resolve(selector)
        validator = Draft202012Validator(
            contract.schema,
            registry=catalog.registry,
            format_checker=validate_contract.FORMAT_CHECKER,
        )
        errors = sorted(
            validator.iter_errors(value),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        )
    except Exception as exc:
        raise DistributionError(
            f"{label}: official-document pack schema validation failed "
            f"({exc.__class__.__name__})"
        ) from exc
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path)
        raise DistributionError(
            f"{label}: official-document pack contract violation at "
            f"{location or '<root>'}: {errors[0].message}"
        )


def _record_ref_set(
    references: object,
    *,
    id_field: str,
    records: Mapping[str, tuple[dict[str, Any], str]],
    label: str,
) -> None:
    if not isinstance(references, list):
        raise DistributionError(
            f"{label}: official-document pack reference list is invalid"
        )
    seen: set[str] = set()
    for index, reference in enumerate(references):
        if (
            not isinstance(reference, dict)
            or set(reference) != {id_field, "sha256"}
            or not isinstance(reference.get(id_field), str)
            or SHA256_RE.fullmatch(str(reference.get("sha256"))) is None
        ):
            raise DistributionError(
                f"{label}/{index}: official-document pack record reference is invalid"
            )
        record_id = reference[id_field]
        target = records.get(record_id)
        if target is None or target[1] != reference["sha256"]:
            raise DistributionError(
                f"{label}/{index}: official-document pack record hash does not resolve"
            )
        if record_id in seen:
            raise DistributionError(
                f"{label}: official-document pack record reference is duplicated"
            )
        seen.add(record_id)
    if seen != set(records):
        raise DistributionError(
            f"{label}: official-document pack record reference set is not exact"
        )


def _single_record_ref(
    reference: object,
    *,
    id_field: str,
    records: Mapping[str, tuple[dict[str, Any], str]],
    label: str,
) -> None:
    if (
        not isinstance(reference, dict)
        or set(reference) != {id_field, "sha256"}
        or not isinstance(reference.get(id_field), str)
        or SHA256_RE.fullmatch(str(reference.get("sha256"))) is None
    ):
        raise DistributionError(
            f"{label}: official-document pack record reference is invalid"
        )
    target = records.get(reference[id_field])
    if target is None or target[1] != reference["sha256"]:
        raise DistributionError(
            f"{label}: official-document pack record hash does not resolve"
        )


def _walk_mappings(value: object) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_mappings(child)


def _validate_pack_processor_refs(
    root: Path,
    records: Iterable[dict[str, Any]],
    *,
    processors: Mapping[str, Any],
    manifest_paths: frozenset[str],
) -> None:
    ref_fields = (
        "implementation_ref",
        "configuration_ref",
        "dependency_lock_ref",
    )
    observed = 0

    def _verify_file_identity(
        reference: object,
        *,
        label: str,
        require_bytes: bool,
    ) -> tuple[str, str, int | None]:
        if not isinstance(reference, Mapping):
            raise DistributionError(
                f"{label}: official-document pack processor ref is invalid"
            )
        if require_bytes:
            if set(reference) != {"path", "sha256", "bytes"}:
                raise DistributionError(
                    f"{label}: official-document pack processor ref must be a "
                    "fileIdentity with path/sha256/bytes"
                )
        elif set(reference) != {"path", "sha256"}:
            raise DistributionError(
                f"{label}: official-document pack processor ref is invalid"
            )
        path = reference.get("path")
        sha256 = reference.get("sha256")
        reference_bytes = reference.get("bytes")
        if not isinstance(path, str) or not isinstance(sha256, str):
            raise DistributionError(
                f"{label}: official-document pack processor ref is invalid"
            )
        if SHA256_RE.fullmatch(sha256) is None:
            raise DistributionError(
                f"{label}: official-document pack processor ref is invalid"
            )
        if require_bytes:
            if (
                not isinstance(reference_bytes, int)
                or isinstance(reference_bytes, bool)
                or reference_bytes < 1
            ):
                raise DistributionError(
                    f"{label}: official-document pack processor ref bytes "
                    "must be a positive integer"
                )
        elif reference_bytes is not None:
            raise DistributionError(
                f"{label}: official-document pack processor ref is invalid"
            )
        path = _safe_archive_path(path)
        payload, _ = _read_regular_file(root / path, path)
        if _sha256(payload) != sha256:
            raise DistributionError(
                f"{label}: official-document pack processor ref does not match "
                "the canonical local artifact"
            )
        if require_bytes and len(payload) != reference_bytes:
            raise DistributionError(
                f"{label}: official-document pack processor ref bytes "
                "must match local file size"
            )
        if path not in manifest_paths:
            raise DistributionError(
                f"{label}: referenced file is absent from the archive"
            )
        return (
            path,
            sha256,
            int(reference_bytes) if reference_bytes is not None else None,
        )

    def _verify_source_file_ref(
        reference: object,
        *,
        label: str,
    ) -> tuple[str, str]:
        path, digest, _ = _verify_file_identity(
            reference,
            label=label,
            require_bytes=False,
        )
        return path, digest

    def _resolve_processor_identity(
        processor: Mapping[str, Any],
        *,
        expected_kind: str,
        label: str,
        require_registry: bool,
    ) -> tuple[str, str, Mapping[str, Any] | None]:
        if expected_kind == "enumerator":
            id_field, version_field = "processor_id", "processor_version"
        elif expected_kind == "transformer":
            id_field, version_field = "processor_id", "processor_version"
        elif expected_kind == "extractor":
            id_field, version_field = "tool_id", "tool_version"
        else:
            raise DistributionError(f"{label}: unsupported processor kind")
        if id_field not in processor or version_field not in processor:
            raise DistributionError(
                f"{label}: official-document pack processor identity is missing"
            )
        processor_id = processor.get(id_field)
        version = processor.get(version_field)
        if (
            not isinstance(processor_id, str)
            or not isinstance(version, str)
            or not processor_id
            or not version
        ):
            raise DistributionError(
                f"{label}: official-document pack processor identity is invalid"
            )
        if not require_registry:
            return processor_id, version, None
        registered = processors.get(processor_id)
        if (
            not isinstance(registered, Mapping)
            or registered.get("kind") != expected_kind
            or not isinstance(registered.get("version"), str)
            or registered.get("version") != version
        ):
            raise DistributionError(
                f"official-document pack processor {processor_id} is not "
                "centrally registered"
            )
        return processor_id, version, registered

    def _iter_processors() -> Iterable[tuple[str, Mapping[str, Any], str, str | None]]:
        for record in records:
            if not isinstance(record, Mapping):
                continue
            contract_name = record.get("contract_name")
            status = (
                record.get("status")
                if isinstance(record.get("status"), str)
                else None
            )
            if contract_name == "official-corpus-manifest":
                discovery = record.get("discovery")
                if not isinstance(discovery, Mapping):
                    continue
                corpus_id = record.get("corpus_id")
                base = (
                    f"official-document-pack/corpus/{corpus_id}/discovery"
                    if isinstance(corpus_id, str)
                    else "official-document-pack/corpus/discovery"
                )
                processor = discovery.get("processor")
                if isinstance(processor, Mapping):
                    yield "enumerator", processor, f"{base}/processor", status
            elif contract_name == "document-slice-manifest":
                manifest_id = record.get("slice_manifest_id")
                base = (
                    f"official-document-pack/slice/{manifest_id}"
                    if isinstance(manifest_id, str)
                    else "official-document-pack/slice"
                )
                sources = record.get("sources")
                if isinstance(sources, Mapping):
                    for source_id, source in sources.items():
                        if (
                            not isinstance(source_id, str)
                            or not isinstance(source, Mapping)
                        ):
                            continue
                        processor = source.get("processor")
                        if isinstance(processor, Mapping):
                            yield (
                                "transformer",
                                processor,
                                f"{base}/{source_id}/processor",
                                status,
                            )
            elif contract_name == "skill-document-scope-inventory":
                inventory_id = record.get("inventory_id")
                enumeration = record.get("enumeration")
                if not isinstance(enumeration, Mapping):
                    continue
                base = (
                    f"official-document-pack/scope/{inventory_id}"
                    if isinstance(inventory_id, str)
                    else "official-document-pack/scope"
                )
                extractor = enumeration.get("extractor")
                if isinstance(extractor, Mapping):
                    yield "extractor", extractor, f"{base}/enumeration/extractor", status

    def _validate_slice_processor(
        processor: Mapping[str, Any],
        *,
        status: str | None,
        require_registry: bool,
        label: str,
    ) -> None:
        assurance = processor.get("assurance_mode")
        if assurance not in {"unverified", "pinned", "attested"}:
            raise DistributionError(
                f"{label}: processor assurance_mode is unsupported"
            )
        if status == "complete" and assurance != "attested":
            raise DistributionError(
                f"{label}: processor complete status requires attested mode"
            )
        if any(field in processor for field in ref_fields):
            raise DistributionError(
                f"{label}: slice processor cannot use direct refs"
            )
        attestations = processor.get("attestations")
        if assurance == "unverified":
            if attestations not in (None, []):
                raise DistributionError(
                    f"{label}: unverified processor cannot include attestations"
                )
            if processor.get("attestation_id") is not None:
                raise DistributionError(
                    f"{label}: unverified processor cannot expose attestation_id"
                )
            return
        if not isinstance(attestations, list) or not attestations:
            raise DistributionError(
                f"{label}: processor attestation set is required"
            )
        required_attestations = {"implementation", "configuration", "dependency-lock"}
        allowed_attestation_kinds = {
            "implementation",
            "configuration",
            "dependency-lock",
            "execution",
        }
        seen_kinds: set[str] = set()
        seen_attestation_ids: set[str] = set()
        execution_artifact: tuple[str, str, int | None] | None = None
        execution_attestation_id: str | None = None
        for index, attestation in enumerate(attestations):
            if not isinstance(attestation, Mapping):
                raise DistributionError(
                    f"{label}/attestations/{index}: processor attestation is "
                    "malformed"
                )
            attestation_kind = attestation.get("kind")
            attestation_id = attestation.get("attestation_id")
            if (
                not isinstance(attestation_kind, str)
                or not attestation_kind
                or attestation_kind not in allowed_attestation_kinds
            ):
                raise DistributionError(
                    f"{label}/attestations/{index}: processor attestation kind "
                    "is malformed"
                )
            if attestation_kind in seen_kinds:
                raise DistributionError(
                    f"{label}/attestations/{index}: processor attestation kind "
                    "must be unique"
                )
            if not isinstance(attestation_id, str) or not attestation_id:
                raise DistributionError(
                    f"{label}/attestations/{index}: processor attestation_id "
                    "must be non-empty"
                )
            if attestation_id in seen_attestation_ids:
                raise DistributionError(
                    f"{label}/attestations/{index}: processor attestation_id "
                    "must be unique"
                )
            seen_kinds.add(attestation_kind)
            seen_attestation_ids.add(attestation_id)
            artifact = attestation.get("artifact")
            path, digest, artifact_bytes = _verify_file_identity(
                artifact,
                label=f"{label}/attestations/{index}/artifact",
                require_bytes=True,
            )
            if attestation_kind in required_attestations and require_registry:
                expected_key = f"{attestation_kind.replace('-', '_')}_ref"
                expected = _resolve_processor_identity(
                    processor,
                    expected_kind="transformer",
                    label=label,
                    require_registry=True,
                )[2]
                if expected is None:
                    raise DistributionError(
                        f"{label}: processor has no central registration"
                    )
                expected_ref = expected.get(expected_key)
                if (
                    not isinstance(expected_ref, Mapping)
                    or expected_ref.get("path") != path
                    or expected_ref.get("sha256") != digest
                ):
                    raise DistributionError(
                        f"{label}/attestations/{index}/artifact: "
                        "processor attestation artifact does not match registry"
                    )
            if attestation_kind == "execution":
                execution_artifact = (path, digest, artifact_bytes)
                execution_attestation_id = attestation_id
        missing = required_attestations.difference(seen_kinds)
        if missing:
            raise DistributionError(
                f"{label}: processor attestations are incomplete"
            )
        if assurance != "attested":
            return
        if execution_artifact is None or execution_attestation_id is None:
            raise DistributionError(
                f"{label}: attested processor requires execution attestation"
            )
        if not require_registry:
            raise DistributionError(
                f"{label}: processor attested mode requires central registration"
            )
        processor_id, _, registered = _resolve_processor_identity(
            processor,
            expected_kind="transformer",
            label=label,
            require_registry=True,
        )
        attestation_runs = registered.get("attested_runs")
        if not isinstance(attestation_runs, list):
            raise DistributionError(
                f"{label}: processor attested assurance requires "
                "attested_runs in registry"
            )
        input_sha256 = processor.get("input_sha256")
        output_sha256 = processor.get("output_sha256")
        if (
            not isinstance(input_sha256, str)
            or SHA256_RE.fullmatch(input_sha256) is None
            or not isinstance(output_sha256, str)
            or SHA256_RE.fullmatch(output_sha256) is None
        ):
            raise DistributionError(
                f"{label}: processor input/output identity is malformed"
            )
        _validate_single_attested_run(
            label=label,
            attestation_runs=attestation_runs,
            attestation_id=execution_attestation_id,
            input_sha256=input_sha256,
            output_sha256=output_sha256,
            execution_artifact=execution_artifact,
        )
        return

    def _validate_single_attested_run(
        *,
        label: str,
        attestation_runs: list[object],
        attestation_id: str,
        input_sha256: str,
        output_sha256: str,
        execution_artifact: tuple[str, str, int | None] | None = None,
    ) -> None:
        expected_run_keys = {
            "attestation_id",
            "input_sha256",
            "output_sha256",
            "attestation_ref",
        }
        matches: list[tuple[str, str]] = []
        for run in attestation_runs:
            if not isinstance(run, Mapping):
                raise DistributionError(f"{label}: attested_runs must contain mappings")
            if set(run.keys()) != expected_run_keys:
                raise DistributionError(
                    f"{label}: central run must include exactly "
                    "attestation_id, input_sha256, output_sha256, attestation_ref"
                )
            if (
                run.get("attestation_id") != attestation_id
                or run.get("input_sha256") != input_sha256
                or run.get("output_sha256") != output_sha256
            ):
                continue
            match_artifact = _verify_file_identity(
                run.get("attestation_ref"),
                label=f"{label}/attestation-ref",
                require_bytes=False,
            )
            matches.append((match_artifact[0], match_artifact[1]))
            if (
                execution_artifact is not None
                and (
                    match_artifact[0] != execution_artifact[0]
                    or match_artifact[1] != execution_artifact[1]
                )
            ):
                raise DistributionError(
                    f"{label}: execution artifact must match central run "
                    "attestation_ref"
                )
        if not matches:
            raise DistributionError(
                f"{label}: attested processor has no matching central run"
            )
        if len(matches) != 1:
            raise DistributionError(
                f"{label}: attested processor has duplicate central runs"
            )
        if execution_artifact is not None and (
            matches[0][0] != execution_artifact[0]
            or matches[0][1] != execution_artifact[1]
        ):
            raise DistributionError(
                f"{label}: execution artifact must match central run attestation_ref"
            )

    def _validate_non_slice_processor(
        processor: Mapping[str, Any],
        *,
        expected_kind: str,
        status: str | None,
        label: str,
    ) -> None:
        if expected_kind == "enumerator":
            assurance_mode = processor.get("assurance_mode")
            if assurance_mode not in {"unverified", "pinned", "attested"}:
                raise DistributionError(
                    f"{label}: processor assurance_mode is unsupported"
                )
            if assurance_mode == "unverified":
                if processor.get("attestation_id") is not None:
                    raise DistributionError(
                        f"{label}: unverified processor cannot expose attestation_id"
                    )
                for field in ref_fields:
                    if processor.get(field) is not None:
                        raise DistributionError(
                            f"{label}: unverified processor cannot expose direct refs"
                        )
                if status == "complete":
                    raise DistributionError(
                        f"{label}: processor cannot claim complete under unverified mode"
                    )
                return
            _, _, registered = _resolve_processor_identity(
                processor,
                expected_kind=expected_kind,
                label=label,
                require_registry=True,
            )
            for field in ref_fields:
                path, digest, _ = _verify_file_identity(
                    processor.get(field),
                    label=f"{label}/{field}",
                    require_bytes=True,
                )
                expected = registered.get(field) if registered is not None else None
                if (
                    not isinstance(expected, Mapping)
                    or expected.get("path") != path
                    or expected.get("sha256") != digest
                ):
                    raise DistributionError(
                        f"{label}: {field} differs from the active registry"
                    )
            if assurance_mode == "pinned":
                if status == "complete":
                    raise DistributionError(
                        f"{label}: processor cannot claim complete under pinned mode"
                    )
                return
            attestation_id = processor.get("attestation_id")
            if not isinstance(attestation_id, str) or not attestation_id:
                raise DistributionError(
                    f"{label}: attested processor requires attestation_id"
                )
            attested_runs = registered.get("attested_runs")
            if not isinstance(attested_runs, list):
                raise DistributionError(
                    f"{label}: processor attested assurance requires "
                    "attested_runs in registry"
                )
            input_sha256 = processor.get("input_sha256")
            output_sha256 = processor.get("output_sha256")
            if (
                not isinstance(input_sha256, str)
                or SHA256_RE.fullmatch(input_sha256) is None
                or not isinstance(output_sha256, str)
                or SHA256_RE.fullmatch(output_sha256) is None
            ):
                raise DistributionError(
                    f"{label}: processor input/output identity is malformed"
                )
            _validate_single_attested_run(
                label=label,
                attestation_runs=attested_runs,
                attestation_id=attestation_id,
                input_sha256=input_sha256,
                output_sha256=output_sha256,
            )
            return
        trust_mode = processor.get("trust_mode")
        if trust_mode not in {"central-pinned", "platform-attested"}:
            raise DistributionError(
                f"{label}: processor trust_mode is unsupported"
            )
        _, _, registered = _resolve_processor_identity(
            processor,
            expected_kind="extractor",
            label=label,
            require_registry=True,
        )
        for field in ref_fields:
            path, digest, _ = _verify_file_identity(
                processor.get(field),
                label=f"{label}/{field}",
                require_bytes=False,
            )
            expected = registered.get(field) if registered is not None else None
            if (
                not isinstance(expected, Mapping)
                or expected.get("path") != path
                or expected.get("sha256") != digest
            ):
                raise DistributionError(
                    f"{label}: {field} differs from the active registry"
                )
        if trust_mode == "central-pinned":
            if processor.get("attestation_id") is not None:
                raise DistributionError(
                    f"{label}: central-pinned processor cannot expose attestation_id"
                )
            if status == "complete":
                raise DistributionError(
                    f"{label}: processor complete status requires platform attestation"
                )
            return
        attestation_id = processor.get("attestation_id")
        if not isinstance(attestation_id, str) or not attestation_id:
            raise DistributionError(
                f"{label}: platform-attested processor requires attestation_id"
            )
        attested_runs = registered.get("attested_runs")
        if not isinstance(attested_runs, list):
            raise DistributionError(
                f"{label}: processor platform-attested assurance requires "
                "attested_runs in registry"
            )
        input_sha256 = processor.get("input_sha256")
        output_sha256 = processor.get("output_sha256")
        if (
            not isinstance(input_sha256, str)
            or SHA256_RE.fullmatch(input_sha256) is None
            or not isinstance(output_sha256, str)
            or SHA256_RE.fullmatch(output_sha256) is None
        ):
            raise DistributionError(
                f"{label}: processor input/output identity is malformed"
            )
        _validate_single_attested_run(
            label=label,
            attestation_runs=attested_runs,
            attestation_id=attestation_id,
            input_sha256=input_sha256,
            output_sha256=output_sha256,
        )
        return

    for expected_kind, processor, label, status in _iter_processors():
        if expected_kind == "transformer":
            assurance = processor.get("assurance_mode")
            if assurance not in {"unverified", "pinned", "attested"}:
                raise DistributionError(
                    f"{label}: processor assurance_mode is unsupported"
                )
            _validate_slice_processor(
                processor,
                status=status,
                require_registry=assurance != "unverified",
                label=label,
            )
            if assurance != "unverified":
                _resolve_processor_identity(
                    processor,
                    expected_kind=expected_kind,
                    label=label,
                    require_registry=True,
                )
            observed += 1
            continue
        _validate_non_slice_processor(
            processor,
            expected_kind=expected_kind,
            status=status,
            label=label,
        )
        observed += 1

    if observed == 0:
        raise DistributionError(
            "official-document pack contains no governed processor references"
        )


def _validate_pack_registry_receipts(
    records: Iterable[dict[str, Any]],
    *,
    source_registry_digests: Mapping[str, str],
) -> None:
    source_hashes = {
        "registry/skill-registry.yaml": source_registry_digests[
            _source_snapshot_path("registry/skill-registry.yaml")
        ],
        "registry/official-document-consumers.yaml": source_registry_digests[
            _source_snapshot_path(
                "registry/official-document-consumers.yaml"
            )
        ],
    }
    for record in records:
        for mapping in _walk_mappings(record):
            registry_path = mapping.get("registry_path")
            if registry_path not in source_hashes:
                continue
            if mapping.get("registry_sha256") != source_hashes[registry_path]:
                raise DistributionError(
                    "official-document pack registry receipt does not bind the "
                    "exact source snapshot"
                )


def _verify_optional_externalized_ref(
    root: Path,
    reference: object,
    *,
    label: str,
    manifest_paths: frozenset[str],
    externalized_receipts: Mapping[str, Mapping[str, object]],
) -> bool:
    if (
        not isinstance(reference, dict)
        or not isinstance(reference.get("path"), str)
        or SHA256_RE.fullmatch(str(reference.get("sha256"))) is None
    ):
        raise DistributionError(
            f"{label}: official-document pack source reference is invalid"
        )
    path = _safe_archive_path(reference["path"])
    if path in manifest_paths:
        raw, _ = _read_regular_file(root / path, path)
        if _sha256(raw) != reference["sha256"]:
            raise DistributionError(
                f"{label}: official-document pack source hash does not match"
            )
        return False
    receipt = externalized_receipts.get(path)
    if (
        not _is_legacy_official_artifact(path)
        or not isinstance(receipt, Mapping)
        or receipt.get("sha256") != reference["sha256"]
    ):
        raise DistributionError(
            f"{label}: official-document pack source is absent without an "
            "exact externalization receipt"
        )
    return True


def _portable_official_document_pack_audit(
    root: Path,
    active_ids: tuple[str, ...],
    manifest_paths: frozenset[str],
    source_registry_digests: Mapping[str, str],
    externalized_receipts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Validate portable pack semantics with technical canonical-record closure.

    Validate against four canonical schemas (official corpus, slice manifest,
    scope inventory, and coverage record), bind all content-addressed references
    to exact canonical registry and local-byte identities, and track explicit
    externalization receipts for excluded bodies. The portable result remains
    explicitly technical and cannot exceed ``partial`` unless every required
    source record and processor binding is complete and locally replayable.
    """

    try:
        catalog = validate_contract.load_catalog(root / "contracts")
        skill_source = load_yaml_strict(
            root / _source_snapshot_path("registry/skill-registry.yaml"),
            "source snapshot skill-registry.yaml",
        )
        skill_active = load_yaml_strict(
            root / "registry" / "skill-registry.yaml",
            "skill-registry.yaml",
        )
        consumer_source = load_yaml_strict(
            root
            / _source_snapshot_path(
                "registry/official-document-consumers.yaml"
            ),
            "source snapshot official-document-consumers.yaml",
        )
        consumer_active = load_yaml_strict(
            root / "registry" / "official-document-consumers.yaml",
            "official-document-consumers.yaml",
        )
        authority_active = load_yaml_strict(
            root / "registry" / "official-source-authorities.yaml",
            "official-source-authorities.yaml",
        )
        authority_source = load_yaml_strict(
            root
            / _source_snapshot_path(
                "registry/official-source-authorities.yaml"
            ),
            "source snapshot official-source-authorities.yaml",
        )
    except (OSError, ValueError, validate_contract.CatalogError) as exc:
        raise DistributionError(
            f"official-document pack audit prerequisites are invalid ({exc})"
        ) from exc
    source_skills = skill_source.get("skills")
    active_skills = skill_active.get("skills")
    source_bindings = consumer_source.get("bindings")
    active_bindings = consumer_active.get("bindings")
    processors = consumer_active.get("processors")
    source_processors = consumer_source.get("processors")
    authorities = authority_active.get("authorities")
    source_authorities = authority_source.get("authorities")
    source_active_ids = (
        tuple(
            sorted(
                skill_id
                for skill_id, entry in source_skills.items()
                if isinstance(entry, dict)
                and entry.get("lifecycle") == "active"
            )
        )
        if isinstance(source_skills, dict)
        else ()
    )
    if (
        not isinstance(source_skills, dict)
        or tuple(active_ids) != source_active_ids
        or active_skills
        != {
            skill_id: source_skills.get(skill_id)
            for skill_id in active_ids
        }
        or not isinstance(source_bindings, list)
        or not isinstance(active_bindings, list)
        or not isinstance(processors, dict)
        or source_processors != processors
        or not isinstance(authorities, dict)
        or not isinstance(source_authorities, dict)
        or authorities
        != {
            authority_id: source_authorities.get(authority_id)
            for authority_id in authorities
        }
    ):
        raise DistributionError(
            "official-document pack audit registry prerequisites are invalid"
        )
    expected_active_bindings = [
        binding
        for binding in source_bindings
        if isinstance(binding, dict)
        and binding.get("consumer_skill_id") in active_ids
    ]
    if active_bindings != expected_active_bindings:
        raise DistributionError(
            "official-document consumer registry is not the exact active "
            "subset of its source snapshot"
        )
    source_skill_digest = source_registry_digests[
        _source_snapshot_path("registry/skill-registry.yaml")
    ]
    builder_lock_path = "contracts/official-document-pack-builder-lock.json"
    try:
        builder_lock = strict_json.load_object(
            root / builder_lock_path,
            builder_lock_path,
        )
    except (OSError, strict_json.StrictJSONError) as exc:
        raise DistributionError(
            f"official-document builder lock is invalid ({exc})"
        ) from exc
    builder_version = builder_lock.get("builder_version")
    if not isinstance(builder_version, str) or not builder_version:
        raise DistributionError(
            "official-document builder lock has no canonical builder version"
        )

    externalized_paths: set[str] = set()
    canonical_externalized_paths: set[str] = set()
    source_tree_replayed_count = 0
    source_tree_externalized_count = 0
    incomplete_record_count = 0
    pack_count = 0
    for skill_id in active_ids:
        pack_prefix = (
            f"skills/{skill_id}/references/official-source-pack/"
        )
        bundle_path = f"{pack_prefix}bundle.json"
        try:
            bundle_raw, _ = _read_regular_file(root / bundle_path, bundle_path)
        except DistributionError as exc:
            raise DistributionError(
                f"{skill_id}: official-document pack entrypoint is unavailable"
            ) from exc
        bundle = _strict_json_object(
            bundle_raw,
            bundle_path,
            max_bytes=MAX_BUNDLE_BYTES,
        )
        if set(bundle) != {
            "bundle_type",
            "schema_version",
            "skill_id",
            "records",
        } or (
            bundle.get("bundle_type") != "official-document-coverage"
            or bundle.get("schema_version") != "1.0"
            or bundle.get("skill_id") != skill_id
        ):
            raise DistributionError(
                f"{skill_id}: official-document pack entrypoint is invalid"
            )
        registrations = bundle.get("records")
        if (
            not isinstance(registrations, dict)
            or set(registrations) != set(PACK_RECORD_FAMILIES)
        ):
            raise DistributionError(
                f"{skill_id}: official-document pack record registry is invalid"
            )
        filenames: dict[str, list[str]] = {}
        for family in ("corpora", "slice_manifests"):
            values = registrations.get(family)
            if not isinstance(values, list) or not values:
                raise DistributionError(
                    f"{skill_id}: official-document pack {family} is invalid"
                )
            filenames[family] = [
                _single_pack_filename(
                    value,
                    f"{skill_id}/records/{family}/{index}",
                )
                for index, value in enumerate(values)
            ]
        for family in ("scope_inventory", "coverage"):
            filenames[family] = [
                _single_pack_filename(
                    registrations.get(family),
                    f"{skill_id}/records/{family}",
                )
            ]
        flattened = [
            filename
            for family in PACK_RECORD_FAMILIES
            for filename in filenames[family]
        ]
        if len(flattened) != len(set(flattened)):
            raise DistributionError(
                f"{skill_id}: official-document pack registers duplicate records"
            )
        expected_paths = {
            bundle_path,
            *(f"{pack_prefix}{filename}" for filename in flattened),
        }
        observed_paths = {
            path
            for path in manifest_paths
            if path.startswith(pack_prefix)
        }
        if observed_paths != expected_paths:
            raise DistributionError(
                f"{skill_id}: official-document pack inventory is not exact"
            )

        family_records: dict[
            str, dict[str, tuple[dict[str, Any], str]]
        ] = {}
        all_records: list[dict[str, Any]] = []
        canonical_producer: dict[str, Any] | None = None
        for family, (selector, id_field) in PACK_RECORD_FAMILIES.items():
            indexed: dict[str, tuple[dict[str, Any], str]] = {}
            for filename in filenames[family]:
                path = f"{pack_prefix}{filename}"
                raw, _ = _read_regular_file(root / path, path)
                value = _strict_json_object(raw, path)
                _schema_validate_pack_record(catalog, selector, value, path)
                record_id = value.get(id_field)
                if not isinstance(record_id, str) or record_id in indexed:
                    raise DistributionError(
                        f"{skill_id}: official-document pack {family} identity "
                        "is invalid or duplicated"
                    )
                producer = value.get("producer")
                if (
                    not isinstance(producer, dict)
                    or producer.get("skill_id") != skill_id
                    or producer.get("tool_id")
                    != "official-document-pack-builder"
                    or producer.get("tool_version") != builder_version
                    or (
                        canonical_producer is not None
                        and producer != canonical_producer
                    )
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document pack record producer "
                        "is not the exact canonical builder identity"
                    )
                if canonical_producer is None:
                    canonical_producer = producer
                indexed[record_id] = (value, _sha256(raw))
                all_records.append(value)
                if family == "coverage":
                    cov_status_vector = value.get("status")
                    if (
                        not isinstance(cov_status_vector, Mapping)
                        or set(cov_status_vector) != {
                            "overall",
                            "corpus",
                            "slices",
                            "scope",
                            "mappings",
                        }
                        or not all(
                            isinstance(value, str)
                            and value in {"blocked", "partial", "complete"}
                            for value in cov_status_vector.values()
                        )
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document pack coverage "
                            "status object is invalid"
                        )
                    if cov_status_vector["overall"] != "complete":
                        incomplete_record_count += 1
                elif value.get("status") != "complete":
                    incomplete_record_count += 1
            family_records[family] = indexed

        seed_path = f"skills/{skill_id}/references/source-pack-seed.json"
        seed_raw, _ = _read_regular_file(root / seed_path, seed_path)
        seed = _strict_json_object(seed_raw, seed_path)
        _schema_validate_pack_record(
            catalog,
            "official-document-pack-seed@1.0",
            seed,
            seed_path,
        )
        if seed.get("skill_id") != skill_id:
            raise DistributionError(
                f"{skill_id}: official-document pack seed identity is invalid"
            )
        scope_catalog_ref = seed.get("scope_catalog_ref")
        if _verify_optional_externalized_ref(
            root,
            scope_catalog_ref,
            label=f"{skill_id}/seed/scope_catalog_ref",
            manifest_paths=manifest_paths,
            externalized_receipts=externalized_receipts,
        ):
            raise DistributionError(
                f"{skill_id}: official-document scope catalog is not portable"
            )
        seed_catalog_refs: dict[tuple[str, str], dict[str, str]] = {}
        providers = seed.get("providers")
        if not isinstance(providers, list) or not providers:
            raise DistributionError(
                f"{skill_id}: official-document pack seed providers are invalid"
            )
        for provider_index, provider in enumerate(providers):
            if not isinstance(provider, dict):
                raise DistributionError(
                    f"{skill_id}: official-document pack seed provider is invalid"
                )
            pair = (provider.get("authority_id"), provider.get("provider_id"))
            source_ref = provider.get("source_ref")
            if (
                not all(isinstance(item, str) for item in pair)
                or not isinstance(source_ref, dict)
                or not isinstance(source_ref.get("path"), str)
                or not isinstance(source_ref.get("sha256"), str)
                or pair in seed_catalog_refs
            ):
                raise DistributionError(
                    f"{skill_id}: official-document pack seed provider "
                    f"{provider_index} is not uniquely bound"
                )
            if _verify_optional_externalized_ref(
                root,
                source_ref,
                label=f"{skill_id}/seed/providers/{provider_index}/source_ref",
                manifest_paths=manifest_paths,
                externalized_receipts=externalized_receipts,
            ):
                raise DistributionError(
                    f"{skill_id}: official-document compact provider catalog "
                    "is not portable"
                )
            seed_catalog_refs[pair] = {
                "path": source_ref["path"],
                "sha256": source_ref["sha256"],
            }
            options_ref = provider.get("options_ref")
            if options_ref is not None and _verify_optional_externalized_ref(
                root,
                options_ref,
                label=f"{skill_id}/seed/providers/{provider_index}/options_ref",
                manifest_paths=manifest_paths,
                externalized_receipts=externalized_receipts,
            ):
                externalized_paths.add(options_ref["path"])

        scope, _ = next(iter(family_records["scope_inventory"].values()))
        coverage, _ = next(iter(family_records["coverage"].values()))
        if scope.get("skill_id") != skill_id or coverage.get("skill_id") != skill_id:
            raise DistributionError(
                f"{skill_id}: official-document pack Skill identity is inconsistent"
            )
        source_skill = source_skills.get(skill_id)
        expected_skill_binding = (
            {
                "registry_path": "registry/skill-registry.yaml",
                "registry_sha256": source_skill_digest,
                "skill_path": source_skill.get("path"),
                "lifecycle": source_skill.get("lifecycle"),
                "source_tree_hash_domain": "VIBE-DFT-SKILL-SOURCE-TREE-v2",
                "source_tree_sha256": source_skill.get("source_tree_sha256"),
            }
            if isinstance(source_skill, dict)
            else None
        )
        if (
            expected_skill_binding is None
            or source_skill.get("lifecycle") != "active"
            or scope.get("skill_registry_binding") != expected_skill_binding
        ):
            raise DistributionError(
                f"{skill_id}: official-document pack source registry binding "
                "is invalid"
            )
        enumeration = scope.get("enumeration")
        if not _scope_enumeration_receipt_valid(
            enumeration,
            expected_source_tree_sha256=expected_skill_binding[
                "source_tree_sha256"
            ],
            subjects=scope.get("subjects"),
        ):
            raise DistributionError(
                f"{skill_id}: official-document scope extractor receipt "
                "does not bind its canonical input and output"
            )
        scope_subjects = scope.get("subjects")
        coverage_mappings = coverage.get("mappings")
        if (
            not isinstance(scope_subjects, list)
            or not isinstance(coverage_mappings, Mapping)
        ):
            raise DistributionError(
                f"{skill_id}: official-document subject mappings are invalid"
            )
        scope_subjects_by_id: dict[str, dict[str, Any]] = {}
        for subject_index, subject in enumerate(scope_subjects):
            if not isinstance(subject, Mapping):
                raise DistributionError(
                    f"{skill_id}: official-document subject {subject_index} "
                    "is invalid"
                )
            subject_id = subject.get("subject_id")
            if (
                not isinstance(subject_id, str)
                or subject_id in scope_subjects_by_id
            ):
                raise DistributionError(
                    f"{skill_id}: official-document subject {subject_index} "
                    "has an invalid or duplicate subject id"
                )
            scope_subjects_by_id[subject_id] = subject
        scope_subject_ids = list(scope_subjects_by_id)
        mapping_subject_ids = [
            subject_id
            for subject_id in coverage_mappings
            if isinstance(subject_id, str)
        ]
        if (
            len(scope_subject_ids) != len(scope_subjects)
            or len(mapping_subject_ids) != len(coverage_mappings)
            or len(mapping_subject_ids) != len(set(mapping_subject_ids))
            or len(scope_subject_ids) != len(set(scope_subject_ids))
            or set(scope_subject_ids) != set(mapping_subject_ids)
        ):
            raise DistributionError(
                f"{skill_id}: official-document coverage does not partition "
                "the exact declared subject set"
            )
        status_rank = {"blocked": 0, "partial": 1, "complete": 2}
        slice_subject_ids_by_ref: dict[tuple[str, str], set[str]] = {}
        for (
            manifest_id,
            (slice_manifest, _),
        ) in family_records["slice_manifests"].items():
            slice_sources = (
                slice_manifest.get("sources")
                if isinstance(slice_manifest, Mapping)
                else None
            )
            if not isinstance(slice_sources, Mapping):
                continue
            for slice_source in slice_sources.values():
                if not isinstance(slice_source, Mapping):
                    continue
                for item in slice_source.get("slices", []):
                    if not isinstance(item, Mapping):
                        continue
                    slice_id = item.get("slice_id")
                    if not isinstance(slice_id, str):
                        continue
                    subject_ids = item.get("subject_ids")
                    if isinstance(subject_ids, list):
                        slice_subject_ids_by_ref[(manifest_id, slice_id)] = {
                            subject_id
                            for subject_id in subject_ids
                            if isinstance(subject_id, str)
                        }
                    else:
                        slice_subject_ids_by_ref[(manifest_id, slice_id)] = set()
        for mapping_index, (subject_id, mapping) in enumerate(
            coverage_mappings.items()
        ):
            if not isinstance(subject_id, str):
                raise DistributionError(
                    f"{skill_id}: official-document mapping {mapping_index} "
                    "has an invalid subject id"
                )
            subject = scope_subjects_by_id.get(subject_id)
            if not isinstance(mapping, Mapping):
                raise DistributionError(
                    f"{skill_id}: official-document mapping {mapping_index} "
                    "is invalid"
                )
            if subject is None:
                raise DistributionError(
                    f"{skill_id}: official-document mapping {mapping_index} "
                    f"references unknown subject {subject_id}"
                )
            evidence_class = subject.get("evidence_class")
            mapping_status = mapping.get("mapping_status")
            disposition = mapping.get("disposition")
            slice_refs = mapping.get("slice_refs")
            rationale = mapping.get("rationale")
            limitations = mapping.get("limitations")
            if not isinstance(mapping_status, str) or mapping_status not in status_rank:
                raise DistributionError(
                    f"{skill_id}: official-document mapping {mapping_index} "
                    "has invalid mapping status"
                )
            if not isinstance(disposition, str) or not isinstance(slice_refs, list):
                raise DistributionError(
                    f"{skill_id}: official-document mapping {mapping_index} "
                    "has invalid coverage logic"
                )
            if evidence_class == "official-provider-required":
                expected_disposition = {
                    "complete": "covered",
                    "partial": "partial",
                    "blocked": "blocked",
                }.get(mapping_status)
                if disposition != expected_disposition:
                    raise DistributionError(
                        f"{skill_id}: official-document mapping {mapping_index} "
                        "has invalid coverage logic"
                    )
                if mapping_status == "complete":
                    if not slice_refs or rationale is not None:
                        raise DistributionError(
                            f"{skill_id}: official-document mapping {mapping_index} "
                            "has invalid coverage logic"
                        )
                    if not isinstance(limitations, list) or limitations:
                        raise DistributionError(
                            f"{skill_id}: official-document mapping {mapping_index} "
                            "has invalid limitations"
                        )
                elif mapping_status == "partial":
                    if not slice_refs:
                        raise DistributionError(
                            f"{skill_id}: official-document mapping {mapping_index} "
                            "has invalid coverage logic"
                        )
                    if (
                        not isinstance(rationale, str)
                        or not rationale
                        or not isinstance(limitations, list)
                        or not limitations
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document mapping {mapping_index} "
                            "has invalid coverage logic"
                        )
                else:
                    if slice_refs:
                        raise DistributionError(
                            f"{skill_id}: official-document mapping {mapping_index} "
                            "has invalid coverage logic"
                        )
                    if (
                        not isinstance(rationale, str)
                        or not rationale
                        or not isinstance(limitations, list)
                        or not limitations
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document mapping {mapping_index} "
                            "has invalid coverage logic"
                        )
            elif evidence_class is not None and evidence_class != "official-provider-required":
                if (
                    mapping_status != "complete"
                    or disposition not in {"not-applicable", "excluded"}
                    or slice_refs
                    or not isinstance(rationale, str)
                    or not rationale
                    or not isinstance(limitations, list)
                    or limitations
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document mapping {mapping_index} "
                        "has invalid coverage logic"
                    )
            else:
                raise DistributionError(
                    f"{skill_id}: official-document mapping {mapping_index} "
                    "has invalid evidence class"
                )
            for ref_index, reference in enumerate(slice_refs):
                if not isinstance(reference, Mapping):
                    raise DistributionError(
                        f"{skill_id}: official-document mapping {mapping_index}/{ref_index} "
                        "has invalid slice reference"
                    )
                slice_manifest_id = reference.get("slice_manifest_id")
                slice_id = reference.get("slice_id")
                if (
                    not isinstance(slice_manifest_id, str)
                    or not isinstance(slice_id, str)
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document mapping {mapping_index}/{ref_index} "
                        "has invalid slice reference"
                    )
                slice_subject_ids = slice_subject_ids_by_ref.get(
                    (slice_manifest_id, slice_id)
                )
                if slice_subject_ids is None:
                    raise DistributionError(
                        f"{skill_id}: official-document pack coverage slice "
                        f"reference {mapping_index}/{ref_index} does not resolve"
                    )
                if subject_id not in slice_subject_ids:
                    raise DistributionError(
                        f"{skill_id}: official-document mapping {mapping_index}/{ref_index} "
                        "references a slice missing current subject"
                    )
        status_rank = {"blocked": 0, "partial": 1, "complete": 2}
        status_dimension_vector = coverage.get("status")
        if (
            not isinstance(status_dimension_vector, Mapping)
            or set(status_dimension_vector) != {
                "overall",
                "corpus",
                "slices",
                "scope",
                "mappings",
            }
            or not isinstance(status_dimension_vector.get("overall"), str)
            or status_dimension_vector["overall"] not in status_rank
            or status_dimension_vector["corpus"] not in status_rank
            or status_dimension_vector["slices"] not in status_rank
            or status_dimension_vector["scope"] not in status_rank
            or status_dimension_vector["mappings"] not in status_rank
        ):
            raise DistributionError(
                f"{skill_id}: official-document coverage status is invalid"
            )
        corpus_statuses = [
            record.get("status")
            for record, _ in family_records["corpora"].values()
        ]
        slice_statuses = [
            record.get("status")
            for record, _ in family_records["slice_manifests"].values()
        ]
        mapping_statuses = [
            mapping.get("mapping_status")
            for mapping in coverage_mappings.values()
        ]
        scope_status = scope.get("status")
        if scope_status is None:
            raise DistributionError(
                f"{skill_id}: official-document scope status is missing"
            )
        if (
            any(status not in status_rank for status in corpus_statuses)
            or any(status not in status_rank for status in slice_statuses)
            or any(status not in status_rank for status in mapping_statuses)
            or scope_status not in status_rank
            or status_rank[status_dimension_vector["corpus"]]
            > min(status_rank[status] for status in corpus_statuses)
            or status_rank[status_dimension_vector["slices"]]
            > min(status_rank[status] for status in slice_statuses)
            or status_rank[status_dimension_vector["scope"]]
            > status_rank[scope_status]
            or status_rank[status_dimension_vector["mappings"]]
            > min(status_rank[status] for status in mapping_statuses)
            or status_rank[status_dimension_vector["overall"]]
            > min(
                status_rank[status_dimension_vector["corpus"]],
                status_rank[status_dimension_vector["slices"]],
                status_rank[status_dimension_vector["scope"]],
                status_rank[status_dimension_vector["mappings"]],
            )
        ):
            raise DistributionError(
                f"{skill_id}: official-document coverage status overclaims "
                "its component evidence"
            )

        _record_ref_set(
            coverage.get("corpus_refs"),
            id_field="corpus_id",
            records=family_records["corpora"],
            label=f"{skill_id}/coverage/corpus_refs",
        )
        _record_ref_set(
            coverage.get("slice_manifest_refs"),
            id_field="slice_manifest_id",
            records=family_records["slice_manifests"],
            label=f"{skill_id}/coverage/slice_manifest_refs",
        )
        _record_ref_set(
            [coverage.get("scope_inventory_ref")],
            id_field="inventory_id",
            records=family_records["scope_inventory"],
            label=f"{skill_id}/coverage/scope_inventory_ref",
        )
        for family in ("slice_manifests",):
            for record, _ in family_records[family].values():
                _single_record_ref(
                    record.get("corpus_ref"),
                    id_field="corpus_id",
                    records=family_records["corpora"],
                    label=f"{skill_id}/{family}/corpus_ref",
                )
        corpus_ids = set(family_records["corpora"])
        for family in ("slice_manifests",):
            referenced_corpora = [
                record["corpus_ref"]["corpus_id"]
                for record, _ in family_records[family].values()
            ]
            if (
                len(referenced_corpora) != len(set(referenced_corpora))
                or set(referenced_corpora) != corpus_ids
            ):
                raise DistributionError(
                    f"{skill_id}: official-document pack {family} does not "
                    "partition the exact corpus set"
                )
        def _source_identity_projection(
            source_identity: object,
            *,
            label: str,
        ) -> tuple[str, int]:
            projection = validate_official_document_coverage._slice_source_identity_projection(
                source_identity
            )
            if projection is None:
                raise DistributionError(
                    f"{label}: official-document source identity is invalid"
                )
            return projection

        def _loss_accounting_entries(
            accounting: object,
            *,
            label: str,
            closure_dimension: str,
        ) -> tuple[str, set[str], dict[str, dict[str, Any]]]:
            if not isinstance(accounting, Mapping):
                raise DistributionError(
                    f"{label}: official-document {closure_dimension} is "
                    "not an exact object"
                )
            closure_status = accounting.get("closure_status")
            entries = accounting.get("entries")
            if (
                closure_status not in {"blocked", "partial", "complete"}
                or not isinstance(entries, list)
            ):
                raise DistributionError(
                    f"{label}: official-document {closure_dimension} "
                    "closure_status/entries is invalid"
                )
            entry_ids: set[str] = set()
            loss_entries: dict[str, dict[str, Any]] = {}
            for entry_index, raw_entry in enumerate(entries):
                if not isinstance(raw_entry, Mapping):
                    raise DistributionError(
                        f"{label}: official-document {closure_dimension} "
                        f"entry {entry_index} is invalid"
                    )
                loss_id = raw_entry.get("loss_id")
                if not isinstance(loss_id, str) or not loss_id:
                    raise DistributionError(
                        f"{label}: official-document {closure_dimension} "
                        f"entry {entry_index} has invalid loss_id"
                    )
                if loss_id in entry_ids:
                    raise DistributionError(
                        f"{label}: official-document {closure_dimension} "
                        f"loss_id {loss_id} is duplicated"
                    )
                if closure_status == "complete":
                    disposition = raw_entry.get("disposition")
                    severity = raw_entry.get("severity")
                    if disposition == "unresolved" or severity == "blocking":
                        raise DistributionError(
                            f"{label}: official-document {closure_dimension} "
                            "contains open/blocking losses in complete mode"
                        )
                entry_ids.add(loss_id)
                loss_entries[loss_id] = dict(raw_entry)
            return closure_status, entry_ids, loss_entries

        def _subject_id_set(value: object, *, label: str) -> set[str]:
            if not isinstance(value, list):
                raise DistributionError(
                    f"{label}: official-document subject id list is invalid"
                )
            subjects: set[str] = set()
            for subject_id in value:
                if not isinstance(subject_id, str) or not subject_id:
                    raise DistributionError(
                        f"{label}: official-document subject id is invalid"
                    )
                subjects.add(subject_id)
            return subjects

        slice_subject_ids_by_ref: dict[tuple[str, str], set[str]] = {}
        slice_ids: set[tuple[str, str]] = set()
        observed_slice_ids: set[str] = set()

        for manifest_id, (manifest, _) in family_records[
            "slice_manifests"
        ].items():
            corpus_ref = manifest.get("corpus_ref")
            if not isinstance(corpus_ref, Mapping):
                raise DistributionError(
                    f"{skill_id}: official-document slice manifest does not "
                    "declare a valid corpus_ref"
                )
            _single_record_ref(
                corpus_ref,
                id_field="corpus_id",
                records=family_records["corpora"],
                label=f"{skill_id}/slice_manifests/{manifest_id}/corpus_ref",
            )
            corpus_id = corpus_ref.get("corpus_id")
            if not isinstance(corpus_id, str):
                raise DistributionError(
                    f"{skill_id}: official-document slice manifest corpus id "
                    "is invalid"
                )
            corpus = family_records["corpora"].get(corpus_id)
            if corpus is None:
                raise DistributionError(
                    f"{skill_id}: official-document slice manifest refers to an "
                    "absent corpus id"
                )
            corpus_authority_id = corpus[0].get("authority_id")
            source_authority = (
                authorities.get(corpus_authority_id)
                if isinstance(corpus_authority_id, str)
                else None
            )
            corpus_inventory = corpus[0].get("source_inventory")
            manifest_sources = manifest.get("sources")
            if (
                not isinstance(corpus_inventory, Mapping)
                or not isinstance(manifest_sources, Mapping)
            ):
                raise DistributionError(
                    f"{skill_id}: official-document slice source inventory "
                    "is invalid"
                )

            included_source_ids: set[str] = set()
            included_source_identities: dict[str, dict[str, Any]] = {}
            included_subject_ids_by_source: dict[str, set[str]] = {}
            expected_source_loss_ids_by_id: dict[str, set[str]] = {}
            for source_id, source_entry in corpus_inventory.items():
                if (
                    not isinstance(source_id, str)
                    or not isinstance(source_entry, Mapping)
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus source inventory "
                        "is malformed"
                    )
                disposition = source_entry.get("disposition")
                if disposition == "included":
                    source_identity = source_entry.get("source_identity")
                    if not isinstance(source_identity, Mapping):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus "
                            "included source entry identity is invalid"
                        )
                    included_source_ids.add(source_id)
                    included_source_identities[source_id] = source_entry[
                        "source_identity"
                    ]
                    loss_ids = source_entry.get("loss_ids")
                    if not isinstance(loss_ids, list):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            "loss_ids is invalid"
                        )
                    normalized_loss_ids: set[str] = set()
                    for loss_id in loss_ids:
                        if not isinstance(loss_id, str) or not loss_id:
                            raise DistributionError(
                                f"{skill_id}: official-document corpus source "
                                f"{source_id} loss_id is invalid"
                            )
                        if loss_id in normalized_loss_ids:
                            raise DistributionError(
                                f"{skill_id}: official-document corpus source "
                                f"{source_id} loss_ids has duplicates"
                            )
                        normalized_loss_ids.add(loss_id)
                    expected_source_loss_ids_by_id[source_id] = normalized_loss_ids
                    included_subject_ids_by_source[source_id] = _subject_id_set(
                        source_entry.get("subject_ids", []),
                        label=f"{skill_id}/corpus/{corpus_id}/sources/{source_id}/subject_ids",
                    )
                elif disposition == "excluded":
                    source_identity = source_entry.get("source_identity")
                    if not isinstance(source_identity, Mapping):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus "
                            "excluded source entry identity is invalid"
                        )
                    excluded_locator = source_identity.get("locator")
                    excluded_entry_identity = source_identity.get(
                        "inventory_entry_identity"
                    )
                    if (
                        not isinstance(excluded_locator, str)
                        or not validate_official_document_coverage._url_matches_authority(
                            excluded_locator,
                            source_authority,
                        )
                        or not isinstance(excluded_entry_identity, Mapping)
                        or set(excluded_entry_identity) != {"sha256", "bytes"}
                        or not SHA256_RE.fullmatch(
                            str(excluded_entry_identity.get("sha256"))
                        )
                        or not isinstance(excluded_entry_identity.get("bytes"), int)
                        or isinstance(excluded_entry_identity.get("bytes"), bool)
                        or excluded_entry_identity.get("bytes") <= 0
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus "
                            "excluded source identity is invalid"
                        )
                elif disposition != "excluded":
                    raise DistributionError(
                        f"{skill_id}: official-document corpus source "
                        f"{source_id} has invalid disposition"
                    )

            manifest_status = manifest.get("status")
            manifest_source_ids = set(manifest_sources)
            if not manifest_source_ids.issubset(included_source_ids):
                raise DistributionError(
                    f"{skill_id}: official-document slice manifest includes "
                    "source IDs outside the referenced corpus included set"
                )
            if manifest_status == "complete" and manifest_source_ids != included_source_ids:
                raise DistributionError(
                    f"{skill_id}: complete slice manifest must include every "
                    "included corpus source"
                )
            if manifest_status not in {"complete", "partial", "blocked"}:
                raise DistributionError(
                    f"{skill_id}: official-document slice manifest status is invalid"
                )

            for source_index, (source_id, source) in enumerate(
                manifest_sources.items()
            ):
                if not isinstance(source_id, str):
                    raise DistributionError(
                        f"{skill_id}: official-document slice source id is invalid"
                    )
                if not isinstance(source, Mapping):
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id} is not an exact object"
                    )

                source_identity = source.get("source_identity")
                if not isinstance(source_identity, Mapping):
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id}/source_identity is invalid"
                    )
                if source_identity != included_source_identities.get(source_id):
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id}/source_identity is not exactly corpus identity"
                    )
                if not isinstance(source_authority, Mapping):
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id} authority binding is invalid"
                    )
                source_projection = _source_identity_projection(
                    source_identity,
                    label=f"{skill_id}: official-document slice source {source_id}/source_identity",
                )

                raw_source_extent_bytes = source.get("raw_source_extent_bytes")
                if (
                    not isinstance(raw_source_extent_bytes, int)
                    or isinstance(raw_source_extent_bytes, bool)
                    or raw_source_extent_bytes <= 0
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id}/raw_source_extent_bytes is invalid"
                    )
                if source_projection[1] != raw_source_extent_bytes:
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id} raw extent does not match source identity bytes"
                    )

                processor = source.get("processor")
                if not isinstance(processor, Mapping):
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id}/processor is invalid"
                    )
                source_loss_accounting = source.get("source_loss_accounting")
                source_loss_closure, source_loss_ids, source_loss_entries = _loss_accounting_entries(
                    source_loss_accounting,
                    label=f"{skill_id}: official-document slice source {source_id}/source_loss_accounting",
                    closure_dimension="source_loss_accounting",
                )
                if expected_source_loss_ids_by_id.get(source_id) != source_loss_ids:
                    raise DistributionError(
                        f"{skill_id}: official-document slice source {source_id} "
                        "loss_ids must match corpus source loss_ids exactly"
                    )

                source_slices = source.get("slices")
                if not isinstance(source_slices, list):
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id}/slices is invalid"
                    )

                source_identity_mode = source_identity.get("content_mode")
                source_locator = source_identity.get("locator")
                source_receipt = source_identity.get("receipt")
                source_projection_bytes = source_projection[1]
                source_projection_sha = source_projection[0]
                source_local_raw: bytes | None = None
                if source_identity_mode == "embedded-content":
                    if not isinstance(source_locator, str):
                        raise DistributionError(
                            f"{skill_id}: official-document slice source "
                            f"{source_id} embedded source identity missing locator"
                        )
                    source_local_path = _safe_archive_path(source_locator)
                    if source_local_path not in manifest_paths:
                        raise DistributionError(
                            f"{skill_id}: official-document slice source "
                            f"{source_id} embedded source locator is missing from manifest"
                        )
                    source_local_raw, _ = _read_regular_file(
                        root / source_local_path,
                        source_local_path,
                    )
                    if len(source_local_raw) != source_projection_bytes:
                        raise DistributionError(
                            f"{skill_id}: official-document slice source "
                            f"{source_id} embedded source bytes do not match source identity"
                        )
                    if _sha256(source_local_raw) != source_projection_sha:
                        raise DistributionError(
                            f"{skill_id}: official-document slice source "
                            f"{source_id} embedded source sha256 does not match source identity"
                        )
                elif source_identity_mode == "external-content":
                    if (
                        not isinstance(source_locator, str)
                        or not isinstance(source_receipt, Mapping)
                        or not validate_official_document_coverage._url_matches_authority(
                            source_locator,
                            source_authority,
                        )
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document slice source "
                            f"{source_id} external source identity locator is invalid"
                        )
                elif source_identity_mode == "metadata-only":
                    if (
                        not isinstance(source_locator, str)
                        or not validate_official_document_coverage._url_matches_authority(
                            source_locator,
                            source_authority,
                        )
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document slice source "
                            f"{source_id} metadata-only source identity locator is invalid"
                        )
                else:
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id} has unsupported source_identity.content_mode"
                    )

                output_projection = _canonical_projection_sha256(
                    {
                        "slices": source_slices,
                        "source_loss_accounting": source_loss_accounting,
                    }
                )
                if (
                    processor.get("input_sha256") != source_projection_sha
                    or processor.get("output_sha256") != output_projection
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id}/processor does not bind exact IO"
                    )

                local_slice_subjects: set[str] = set()
                local_slice_ids: set[str] = set()
                local_selector_keys: set[str] = set()
                source_loss_union: set[str] = set()
                source_subjects = included_subject_ids_by_source.get(source_id, set())

                for slice_index, slice_record in enumerate(source_slices):
                    if not isinstance(slice_record, Mapping):
                        raise DistributionError(
                            f"{skill_id}: official-document slice source "
                            f"{source_id}/slices/{slice_index} is invalid"
                        )
                    slice_id = slice_record.get("slice_id")
                    if not isinstance(slice_id, str) or not slice_id:
                        raise DistributionError(
                            f"{skill_id}: official-document slice source "
                            f"{source_id}/slices/{slice_index}/slice_id is "
                            "invalid"
                        )
                    if slice_id in observed_slice_ids or slice_id in local_slice_ids:
                        raise DistributionError(
                            f"{skill_id}: official-document slice id is not "
                            "globally unique"
                        )
                    observed_slice_ids.add(slice_id)
                    local_slice_ids.add(slice_id)
                    selector = slice_record.get("selector")
                    if not isinstance(selector, Mapping):
                        raise DistributionError(
                            f"{skill_id}: official-document slice "
                            f"{source_id}/slices/{slice_id}/selector is invalid"
                        )
                    selector_key = json.dumps(
                        selector,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    if selector_key in local_selector_keys:
                        raise DistributionError(
                            f"{skill_id}: official-document slice source "
                            f"{source_id}/slices/{slice_id} duplicate selector"
                        )
                    local_selector_keys.add(selector_key)

                    selector_kind = selector.get("kind")
                    selector_value = selector.get("value")
                    raw_range = slice_record.get("raw_byte_range")
                    if (
                        not isinstance(raw_range, Mapping)
                        or not isinstance(raw_range.get("start_byte"), int)
                        or isinstance(raw_range.get("start_byte"), bool)
                        or not isinstance(raw_range.get("byte_count"), int)
                        or isinstance(raw_range.get("byte_count"), bool)
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document slice {source_id}/"
                            f"{slice_id}/raw_byte_range is invalid"
                        )
                    raw_start = raw_range["start_byte"]
                    raw_count = raw_range["byte_count"]
                    if raw_start < 0 or raw_count <= 0:
                        raise DistributionError(
                            f"{skill_id}: official-document slice {source_id}/"
                            f"{slice_id} raw_byte_range must be positive"
                        )
                    if raw_start + raw_count > source_projection_bytes:
                        raise DistributionError(
                            f"{skill_id}: official-document slice {source_id}/"
                            f"{slice_id} raw_byte_range exceeds source extent"
                        )
                    if selector_kind == "whole-source":
                        if raw_start != 0 or raw_count != source_projection_bytes:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} "
                                "whole-source requires full extent"
                            )
                        if selector_value != "*":
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} selector must be '*'"
                            )
                    elif selector_kind == "byte-range":
                        expected = f"{raw_start}:{raw_count}"
                        if selector_value != expected:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/selector "
                                "byte-range must be start:count"
                            )

                    content = slice_record.get("content")
                    if not isinstance(content, Mapping):
                        raise DistributionError(
                            f"{skill_id}: official-document slice "
                            f"{source_id}/slices/{slice_id}/content is invalid"
                        )
                    content_mode = content.get("content_mode")
                    if content_mode == "embedded-content":
                        if source_local_raw is None:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} embedded content "
                                "requires embedded source identity"
                            )
                        artifact = content.get("artifact")
                        if not isinstance(artifact, Mapping):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/content "
                                "embedded-content must include artifact"
                            )
                        artifact_path = artifact.get("path")
                        artifact_bytes = artifact.get("bytes")
                        artifact_sha256 = artifact.get("sha256")
                        if (
                            not isinstance(artifact_path, str)
                            or not isinstance(artifact_bytes, int)
                            or isinstance(artifact_bytes, bool)
                            or artifact_bytes <= 0
                            or SHA256_RE.fullmatch(str(artifact_sha256))
                            is None
                        ):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/content/artifact is "
                                "invalid"
                            )
                        if artifact_bytes != raw_count:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} artifact bytes "
                                "must equal selected raw_byte_range"
                            )
                        artifact_local_path = _safe_archive_path(artifact_path)
                        artifact_raw, _ = _read_regular_file(
                            root / artifact_local_path,
                            artifact_local_path,
                        )
                        if len(artifact_raw) != artifact_bytes:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} embedded artifact "
                                "bytes mismatch"
                            )
                        if _sha256(artifact_raw) != str(artifact_sha256):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} embedded artifact "
                                "sha256 mismatch"
                            )
                        if artifact_raw != source_local_raw[
                            raw_start : raw_start + raw_count
                        ]:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} "
                                "must match selected raw byte range"
                            )

                    elif content_mode == "external-content":
                        receipt = content.get("receipt")
                        locator = content.get("locator")
                        if not isinstance(locator, str):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/content/locator "
                                "is invalid"
                            )
                        if source_identity_mode != "external-content":
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} external content "
                                "requires external source identity"
                            )
                        if locator != source_locator:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/content locator "
                                "must match corpus source locator"
                            )
                        if not validate_official_document_coverage._url_matches_authority(
                            locator,
                            source_authority,
                        ):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} external locator "
                                "is outside authority scope"
                            )
                        if not isinstance(receipt, Mapping):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/content/receipt is invalid"
                            )
                        receipt_raw_sha = receipt.get("raw_sha256")
                        receipt_raw_bytes = receipt.get("raw_bytes")
                        if (
                            not SHA256_RE.fullmatch(str(receipt_raw_sha))
                            or not isinstance(receipt_raw_bytes, int)
                            or isinstance(receipt_raw_bytes, bool)
                            or receipt_raw_bytes <= 0
                        ):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/content/receipt/raw "
                                "sha256/bytes is invalid"
                            )
                        if (
                            receipt_raw_sha != source_projection_sha
                            or receipt_raw_bytes != source_projection_bytes
                        ):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} external "
                                "receipt must match source identity bytes/sha256"
                            )
                        selected = receipt.get("selected_content")
                        if not isinstance(selected, Mapping):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/content/receipt "
                                "selected_content is invalid"
                            )
                        selected_sha = selected.get("sha256")
                        selected_bytes = selected.get("bytes")
                        if (
                            not SHA256_RE.fullmatch(str(selected_sha))
                            or not isinstance(selected_bytes, int)
                            or isinstance(selected_bytes, bool)
                            or selected_bytes <= 0
                        ):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/content/receipt "
                                "selected_content is invalid"
                            )
                        if selected_bytes != raw_count:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} selected "
                                "content bytes must equal raw_byte_range byte_count"
                            )
                    elif content_mode == "metadata-only":
                        locator = content.get("locator")
                        identity = content.get("identity")
                        if source_identity_mode not in {"metadata-only", "external-content"}:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} metadata-only "
                                "requires metadata-only or external source identity"
                            )
                        if (
                            not isinstance(locator, str)
                            or locator != source_locator
                        ):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} metadata-only "
                                "content does not close to source identity"
                            )
                        if not validate_official_document_coverage._url_matches_authority(
                            locator,
                            source_authority,
                        ):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} metadata-only "
                                "locator is outside authority scope"
                            )
                        if source_identity_mode == "metadata-only" and (
                            not isinstance(identity, Mapping)
                            or identity != source_identity.get("identity")
                        ):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} metadata-only "
                                "content does not close to source identity"
                            )
                        if not isinstance(locator, str) or not isinstance(identity, Mapping):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} metadata-only "
                                "content does not close to source identity"
                            )
                        if (
                            not SHA256_RE.fullmatch(str(identity.get("sha256")))
                            or not isinstance(identity.get("bytes"), int)
                            or isinstance(identity.get("bytes"), bool)
                            or identity.get("bytes") <= 0
                        ):
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id}/content/identity "
                                "is invalid"
                            )
                    else:
                        raise DistributionError(
                            f"{skill_id}: official-document slice "
                            f"{source_id}/slices/{slice_id}/content/content_mode "
                            "is unsupported"
                        )

                    source_slice_loss = slice_record.get("loss_accounting")
                    _slice_loss_closure, source_slice_loss_ids, slice_loss_entries = (
                        _loss_accounting_entries(
                            source_slice_loss,
                            label=f"{skill_id}: official-document slice "
                            f"{source_id}/slices/{slice_id}/loss_accounting",
                            closure_dimension="loss_accounting",
                        )
                    )
                    for loss_id, slice_loss_entry in slice_loss_entries.items():
                        expected_loss = source_loss_entries.get(loss_id)
                        if expected_loss is None or slice_loss_entry != expected_loss:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} "
                                "loss entry does not match source loss entry"
                            )
                    source_loss_union.update(source_slice_loss_ids)

                    subject_ids = slice_record.get("subject_ids")
                    if not isinstance(subject_ids, list):
                        raise DistributionError(
                            f"{skill_id}: official-document slice "
                            f"{source_id}/slices/{slice_id}/subject_ids is invalid"
                        )
                    normalized_subject_ids: set[str] = set()
                    for subject_id in subject_ids:
                        if not isinstance(subject_id, str) or not subject_id:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} subject_id is "
                                "invalid"
                            )
                        if subject_id not in source_subjects:
                            raise DistributionError(
                                f"{skill_id}: official-document slice "
                                f"{source_id}/slices/{slice_id} subject_id "
                                "is not declared by corpus source"
                            )
                        normalized_subject_ids.add(subject_id)
                    local_slice_subjects.update(normalized_subject_ids)
                    slice_subject_ids_by_ref[(manifest_id, slice_id)] = normalized_subject_ids
                    slice_ids.add((manifest_id, slice_id))

                if manifest_status == "complete" and source_loss_closure == "complete":
                    source_subject_set = included_subject_ids_by_source.get(source_id, set())
                    if source_subject_set and not source_subject_set.issubset(local_slice_subjects):
                        raise DistributionError(
                            f"{skill_id}: official-document slice manifest "
                            f"{source_id} does not cover every source subject"
                        )
                if source_loss_union != source_loss_ids:
                    raise DistributionError(
                        f"{skill_id}: official-document slice source "
                        f"{source_id} loss closure is incomplete"
                    )
        for mapping_index, (subject_id, mapping) in enumerate(
            coverage_mappings.items()
        ):
            if not isinstance(mapping, dict):
                raise DistributionError(
                    f"{skill_id}: official-document mapping {mapping_index} "
                    "is invalid"
                )
            if not isinstance(subject_id, str) or not subject_id:
                raise DistributionError(
                    f"{skill_id}: official-document mapping {mapping_index} "
                    "is missing a valid subject_id"
                )
            for ref_index, reference in enumerate(mapping.get("slice_refs", [])):
                pair = (
                    reference.get("slice_manifest_id")
                    if isinstance(reference, dict)
                    else None,
                    reference.get("slice_id")
                    if isinstance(reference, dict)
                    else None,
                )
                if pair not in slice_ids:
                    raise DistributionError(
                    f"{skill_id}: official-document pack coverage slice "
                    f"reference {mapping_index}/{ref_index} does not resolve"
                )
                if subject_id not in slice_subject_ids_by_ref.get(pair, set()):
                    raise DistributionError(
                        f"{skill_id}: official-document pack coverage slice "
                        f"{mapping_index}/{ref_index} references slice without "
                        f"current subject {subject_id}"
                    )

        expected_corpus_bindings = set()
        for binding in active_bindings:
            if (
                not isinstance(binding, dict)
                or binding.get("consumer_skill_id") != skill_id
            ):
                continue
            if binding.get("consumer_lifecycle") != "active":
                raise DistributionError(
                    f"{skill_id}: official-document pack consumer binding "
                    "is inactive"
                )
            pair = (binding.get("authority_id"), binding.get("provider_id"))
            if not isinstance(pair[0], str) or not isinstance(pair[1], str):
                raise DistributionError(
                    f"{skill_id}: official-document pack consumer binding "
                    "has invalid authority/provider binding"
                )
            if pair in expected_corpus_bindings:
                raise DistributionError(
                    f"{skill_id}: official-document consumer binding list has "
                    "duplicate authority/provider pairs"
                )
            expected_corpus_bindings.add(pair)
        if (
            not expected_corpus_bindings
            or any(
                not isinstance(authority_id, str)
                or not isinstance(provider_id, str)
                for authority_id, provider_id in expected_corpus_bindings
            )
        ):
            raise DistributionError(
                f"{skill_id}: official-document pack consumer binding set is "
                "invalid"
            )

        for corpus, _ in family_records["corpora"].values():
            authority = authorities.get(corpus.get("authority_id"))
            if (
                not isinstance(authority, dict)
                or authority.get("provider_id") != corpus.get("provider_id")
            ):
                raise DistributionError(
                    f"{skill_id}: official-document pack corpus authority "
                    "does not resolve"
                )
            pair = (corpus.get("authority_id"), corpus.get("provider_id"))
            discovery = corpus.get("discovery")
            enumerator = None
            if isinstance(discovery, dict):
                enumerator = discovery.get("processor")
                if enumerator is None:
                    enumerator = discovery.get("enumerator")
            source_authority = source_authorities.get(pair[0])
            source_inventory = corpus.get("source_inventory")
            if (
                not isinstance(source_authority, dict)
                or not isinstance(source_inventory, Mapping)
                or not isinstance(discovery, dict)
            ):
                raise DistributionError(
                    f"{skill_id}: official-document corpus source universe "
                    "is invalid"
                )
            if (
                not _corpus_source_partition_valid(source_inventory)
                or not validate_official_document_coverage
                .authority_version_scope_compatible(
                    corpus.get("version_scope"),
                    source_authority.get("version_policy", {}).get(
                        "registered_scopes"
                    ),
                )
                or not validate_official_document_coverage
                ._url_matches_authority(
                    discovery.get("authority_root"),
                    source_authority,
                )
            ):
                raise DistributionError(
                    f"{skill_id}: official-document corpus source universe "
                    "or authority scope is not exact"
                )
            for source_index, (source_id, source) in enumerate(
                source_inventory.items()
            ):
                if not isinstance(source, dict):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus source "
                        f"{source_index} exceeds its authority policy"
                    )
                identity = source.get("source_identity")
                if not isinstance(identity, dict):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus source "
                        f"{source_index} exceeds its authority policy"
                    )
                content_mode = identity.get("content_mode")
                locator = identity.get("locator")
                if not isinstance(locator, str):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus source "
                        f"{source_index} has invalid locator"
                    )

                if content_mode == "embedded-content":
                    if set(identity.keys()) != {
                        "content_mode",
                        "locator",
                        "sha256",
                        "bytes",
                    }:
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} embedded-content identity keys are invalid"
                        )
                    content_sha256 = identity.get("sha256")
                    content_bytes = identity.get("bytes")
                    if (
                        SHA256_RE.fullmatch(str(content_sha256)) is None
                        or not isinstance(content_bytes, int)
                        or isinstance(content_bytes, bool)
                        or content_bytes <= 0
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} embedded-content identity is invalid"
                        )
                    safe_source_locator = _safe_archive_path(locator)
                    if safe_source_locator not in manifest_paths:
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} embedded locator is not in manifest"
                        )
                    source_local_raw, _ = _read_regular_file(
                        root / safe_source_locator,
                        safe_source_locator,
                    )
                    if len(source_local_raw) != content_bytes:
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} embedded bytes do not match identity"
                        )
                    if _sha256(source_local_raw) != content_sha256:
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} embedded hash does not match identity"
                        )
                elif content_mode == "external-content":
                    if set(identity.keys()) != {
                        "content_mode",
                        "locator",
                        "receipt",
                    }:
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} external-content identity keys are invalid"
                        )
                    if not validate_official_document_coverage._url_matches_authority(
                        locator,
                        source_authority,
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} external locator is not within authority scope"
                        )
                    receipt = identity.get("receipt")
                    if (
                        not isinstance(receipt, Mapping)
                        or set(receipt.keys())
                        != {
                            "retrieval_method",
                            "retrieved_utc",
                            "raw_sha256",
                            "raw_bytes",
                        }
                        or validate_official_document_coverage
                        ._slice_source_identity_projection(identity)
                        is None
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} external-content receipt is invalid"
                        )
                elif content_mode == "metadata-only":
                    if set(identity.keys()) != {
                        "content_mode",
                        "locator",
                        "identity",
                    }:
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} metadata-only identity keys are invalid"
                        )
                    if not validate_official_document_coverage._url_matches_authority(
                        locator,
                        source_authority,
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} metadata-only locator is not within "
                            "authority scope"
                        )
                    source_identity = identity.get("identity")
                    if (
                        not isinstance(source_identity, Mapping)
                        or set(source_identity.keys()) != {"sha256", "bytes"}
                        or SHA256_RE.fullmatch(
                            str(source_identity.get("sha256"))
                        ) is None
                        or not isinstance(source_identity.get("bytes"), int)
                        or isinstance(source_identity.get("bytes"), bool)
                        or source_identity.get("bytes") <= 0
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} metadata-only identity is invalid"
                        )
                elif content_mode == "excluded":
                    if set(identity.keys()) != {
                        "content_mode",
                        "locator",
                        "inventory_entry_identity",
                    }:
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} excluded identity keys are invalid"
                        )
                    if not validate_official_document_coverage._url_matches_authority(
                        locator,
                        source_authority,
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} excluded locator is not within "
                            "authority scope"
                        )
                    excluded_identity = identity.get("inventory_entry_identity")
                    if (
                        not isinstance(excluded_identity, Mapping)
                        or set(excluded_identity.keys()) != {"sha256", "bytes"}
                        or SHA256_RE.fullmatch(
                            str(excluded_identity.get("sha256"))
                        ) is None
                        or not isinstance(excluded_identity.get("bytes"), int)
                        or isinstance(excluded_identity.get("bytes"), bool)
                        or excluded_identity.get("bytes") <= 0
                    ):
                        raise DistributionError(
                            f"{skill_id}: official-document corpus source "
                            f"{source_index} excluded identity is invalid"
                        )
                else:
                    raise DistributionError(
                        f"{skill_id}: official-document corpus source "
                        f"{source_index} has unsupported source_identity.content_mode"
                    )
            catalog_ref = seed_catalog_refs.get(pair)
            if not isinstance(catalog_ref, dict):
                raise DistributionError(
                    f"{skill_id}: official-document seed catalog reference is "
                    "missing for corpus authority/provider closure"
                )
            discovery_inventory = discovery.get("inventory")
            if not isinstance(discovery_inventory, Mapping):
                raise DistributionError(
                    f"{skill_id}: official-document corpus inventory metadata "
                    "is invalid"
                )
            inventory_content_mode = discovery_inventory.get("content_mode")
            inventory_sha256 = None
            if inventory_content_mode == "embedded-content":
                inventory_locator = discovery_inventory.get("locator")
                inventory_bytes = discovery_inventory.get("bytes")
                inventory_sha256 = discovery_inventory.get("sha256")
                if (
                    not isinstance(inventory_locator, str)
                    or SHA256_RE.fullmatch(str(inventory_sha256)) is None
                    or not isinstance(inventory_bytes, int)
                    or isinstance(inventory_bytes, bool)
                    or inventory_bytes <= 0
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus discovery "
                        "inventory embedded content is invalid"
                    )
                inventory_local = _safe_archive_path(inventory_locator)
                inventory_raw, _ = _read_regular_file(
                    root / inventory_local,
                    inventory_local,
                )
                if len(inventory_raw) != inventory_bytes:
                    raise DistributionError(
                        f"{skill_id}: official-document corpus discovery "
                        "inventory embedded bytes mismatch"
                    )
                if _sha256(inventory_raw) != inventory_sha256:
                    raise DistributionError(
                        f"{skill_id}: official-document corpus discovery "
                        "inventory embedded hash mismatch"
                    )
            elif inventory_content_mode == "external-content":
                inventory_locator = discovery_inventory.get("locator")
                inventory_receipt = discovery_inventory.get("receipt")
                if not isinstance(inventory_locator, str) or not validate_official_document_coverage._url_matches_authority(
                    inventory_locator,
                    source_authority,
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus discovery "
                        "inventory locator is not within authority scope"
                    )
                if not isinstance(inventory_receipt, Mapping):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus discovery "
                        "inventory external receipt is invalid"
                    )
                inventory_sha256 = inventory_receipt.get("raw_sha256")
                inventory_bytes = inventory_receipt.get("raw_bytes")
                if (
                    SHA256_RE.fullmatch(str(inventory_sha256)) is None
                    or not isinstance(inventory_bytes, int)
                    or isinstance(inventory_bytes, bool)
                    or inventory_bytes <= 0
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus discovery "
                        "inventory external receipt is invalid"
                    )
            elif inventory_content_mode == "metadata-only":
                inventory_locator = discovery_inventory.get("locator")
                inventory_identity = discovery_inventory.get("identity")
                if not isinstance(inventory_locator, str) or not validate_official_document_coverage._url_matches_authority(
                    inventory_locator,
                    source_authority,
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus discovery "
                        "inventory metadata locator is not within authority scope"
                    )
                if not isinstance(inventory_identity, Mapping):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus discovery "
                        "inventory metadata identity is invalid"
                    )
                inventory_sha256 = inventory_identity.get("sha256")
                inventory_bytes = inventory_identity.get("bytes")
                if (
                    SHA256_RE.fullmatch(str(inventory_sha256)) is None
                    or not isinstance(inventory_bytes, int)
                    or isinstance(inventory_bytes, bool)
                    or inventory_bytes <= 0
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document corpus discovery "
                        "inventory metadata identity is invalid"
                    )
            else:
                raise DistributionError(
                    f"{skill_id}: official-document corpus discovery "
                    "inventory content mode is unsupported"
                )
            if (
                not isinstance(enumerator, Mapping)
                or not isinstance(inventory_sha256, str)
                or enumerator.get("input_sha256") != inventory_sha256
            ):
                raise DistributionError(
                    f"{skill_id}: official-document corpus does not bind its "
                    "exact discovery inventory"
                )
            if enumerator.get("output_sha256") != _canonical_projection_sha256(
                source_inventory
            ):
                raise DistributionError(
                    f"{skill_id}: official-document corpus enumerator receipt "
                    "does not bind its canonical output"
                )
        expected_corpus_bindings_set: set[tuple[str, str]] = set()
        for binding in active_bindings:
            if not isinstance(binding, dict) or binding.get("consumer_skill_id") != skill_id:
                continue
            pair = (binding.get("authority_id"), binding.get("provider_id"))
            if not isinstance(pair[0], str) or not isinstance(pair[1], str):
                raise DistributionError(
                    f"{skill_id}: official-document pack consumer binding set "
                    "is invalid"
                )
            if pair in expected_corpus_bindings_set:
                raise DistributionError(
                    f"{skill_id}: official-document pack consumer binding set "
                    "has duplicates"
                )
            expected_corpus_bindings_set.add(pair)

        observed_corpus_bindings_set: set[tuple[str, str]] = set()
        for corpus, _ in family_records["corpora"].values():
            pair = (corpus.get("authority_id"), corpus.get("provider_id"))
            if not isinstance(pair[0], str) or not isinstance(pair[1], str):
                raise DistributionError(
                    f"{skill_id}: official-document pack corpus set is not the "
                    "exact active consumer binding closure"
                )
            if pair in observed_corpus_bindings_set:
                raise DistributionError(
                    f"{skill_id}: official-document pack corpus set is not the "
                    "exact active consumer binding closure"
                )
            observed_corpus_bindings_set.add(pair)
        if (
            expected_corpus_bindings_set != observed_corpus_bindings_set
        ):
            raise DistributionError(
                f"{skill_id}: official-document pack corpus set is not the "
                "exact active consumer binding closure"
            )
        _validate_pack_processor_refs(
            root,
            all_records,
            processors=processors,
            manifest_paths=manifest_paths,
        )
        _validate_pack_registry_receipts(
            all_records,
            source_registry_digests=source_registry_digests,
        )
        local_skill_source_paths: set[str] = set()
        skill_externalized_source_paths: set[str] = set()
        source_ref_paths: set[str] = set()
        source_ref_hashes: dict[str, str] = {}
        for index, reference in enumerate(scope.get("skill_source_refs", [])):
            reference_path = (
                reference.get("path")
                if isinstance(reference, dict)
                else None
            )
            if (
                not isinstance(reference_path, str)
                or not reference_path.startswith(f"skills/{skill_id}/")
                or reference_path.startswith(pack_prefix)
                or reference_path in source_ref_paths
            ):
                raise DistributionError(
                    f"{skill_id}: official-document scope source inventory "
                    f"entry {index} is invalid or duplicated"
                )
            source_ref_paths.add(reference_path)
            source_ref_hashes[reference_path] = reference["sha256"]
            if _verify_optional_externalized_ref(
                root,
                reference,
                label=f"{skill_id}/scope/skill_source_refs/{index}",
                manifest_paths=manifest_paths,
                externalized_receipts=externalized_receipts,
            ):
                externalized_paths.add(reference["path"])
                skill_externalized_source_paths.add(reference["path"])
            else:
                local_skill_source_paths.add(reference_path)
        packaged_skill_source_paths = {
            path
            for path in manifest_paths
            if path.startswith(f"skills/{skill_id}/")
            and not path.startswith(pack_prefix)
        }
        if local_skill_source_paths != packaged_skill_source_paths:
            raise DistributionError(
                f"{skill_id}: official-document scope source inventory is not "
                "the exact packaged Skill source closure"
            )
        skill_receipt_paths = {
            path
            for path in externalized_receipts
            if path.startswith(f"skills/{skill_id}/")
            and not path.startswith(pack_prefix)
        }
        if skill_externalized_source_paths:
            if skill_externalized_source_paths != skill_receipt_paths:
                raise DistributionError(
                    f"{skill_id}: externalized Skill source receipts are not "
                    "the exact scope-tree dependency closure"
                )
            source_tree_externalized_count += 1
        else:
            if skill_receipt_paths:
                raise DistributionError(
                    f"{skill_id}: unconsumed externalized Skill source receipt "
                    "prevents exact source-tree replay"
                )
            try:
                digest = skill_registry.source_tree_digest(
                    root / f"skills/{skill_id}"
                )
            except ValueError as exc:
                raise DistributionError(
                    f"{skill_id}: packaged Skill source tree cannot be "
                    f"recomputed ({exc})"
                ) from exc
            recomputed_refs = {
                (f"skills/{skill_id}/{item.path}", item.sha256)
                for item in digest.files
            }
            declared_refs = {
                (path, source_ref_hashes[path])
                for path in source_ref_paths
            }
            if (
                digest.sha256
                != expected_skill_binding["source_tree_sha256"]
                or recomputed_refs != declared_refs
            ):
                raise DistributionError(
                    f"{skill_id}: packaged Skill source tree does not exactly "
                    "reproduce the registered v2 digest and scope refs"
                )
            source_tree_replayed_count += 1
        for subject_index, subject in enumerate(scope_subjects):
            origin_refs = subject.get("origin_refs")
            if not isinstance(origin_refs, list) or not origin_refs:
                raise DistributionError(
                    f"{skill_id}: official-document subject {subject_index} "
                    "has no source origin"
                )
            for origin_index, origin in enumerate(origin_refs):
                if (
                    not isinstance(origin, dict)
                    or not isinstance(origin.get("path"), str)
                    or origin.get("sha256")
                    != source_ref_hashes.get(origin.get("path"))
                ):
                    raise DistributionError(
                        f"{skill_id}: official-document subject origin "
                        f"{subject_index}/{origin_index} does not resolve"
                    )
        canonical_result = validate_official_document_coverage.validate_files(
            corpus_paths=[
                root / f"{pack_prefix}{filename}"
                for filename in filenames["corpora"]
            ],
            slice_paths=[
                root / f"{pack_prefix}{filename}"
                for filename in filenames["slice_manifests"]
            ],
            scope_inventory_path=(
                root / f"{pack_prefix}{filenames['scope_inventory'][0]}"
            ),
            coverage_path=(
                root / f"{pack_prefix}{filenames['coverage'][0]}"
            ),
            source_root=root,
            portable_context=(
                validate_official_document_coverage.PortableValidationContext(
                    repository_root=root,
                    contracts_directory=root / "contracts",
                    interface_registry_path=(
                        root
                        / _source_snapshot_path(
                            "registry/interface-registry.yaml"
                        )
                    ),
                    authority_registry_path=(
                        root
                        / _source_snapshot_path(
                            "registry/official-source-authorities.yaml"
                        )
                    ),
                    software_registry_path=(
                        root
                        / _source_snapshot_path(
                            "registry/software-registry.yaml"
                        )
                    ),
                    skill_registry_path=(
                        root
                        / _source_snapshot_path(
                            "registry/skill-registry.yaml"
                        )
                    ),
                    consumer_registry_path=(
                        root
                        / _source_snapshot_path(
                            "registry/official-document-consumers.yaml"
                        )
                    ),
                    externalized_receipts=externalized_receipts,
                )
            ),
        )
        if canonical_result.findings:
            details = ", ".join(
                sorted({finding.code for finding in canonical_result.findings})
            )
            raise DistributionError(
                f"{skill_id}: canonical official-document semantic replay "
                f"failed ({details})"
            )
        if canonical_result.assurance_status == "invalid":
            raise DistributionError(
                f"{skill_id}: canonical official-document semantic replay "
                "returned invalid assurance"
            )
        canonical_externalized_paths.update(
            canonical_result.externalized_paths
        )
        pack_count += 1

    if pack_count != len(active_ids):
        raise DistributionError(
            "official-document pack audit did not cover every active Skill"
        )
    if externalized_paths != set(externalized_receipts):
        missing = sorted(set(externalized_receipts) - externalized_paths)
        extra = sorted(externalized_paths - set(externalized_receipts))
        raise DistributionError(
            "official-document externalization receipts are not the exact "
            f"referenced closure; missing={missing[:3]} extra={extra[:3]}"
        )
    if canonical_externalized_paths != set(externalized_receipts):
        missing = sorted(
            set(externalized_receipts) - canonical_externalized_paths
        )
        extra = sorted(
            canonical_externalized_paths - set(externalized_receipts)
        )
        raise DistributionError(
            "canonical official-document replay did not consume the exact "
            f"externalization receipt closure; missing={missing[:3]} "
            f"extra={extra[:3]}"
        )
    return {
        "externalized_source_count": len(externalized_paths),
        "canonical_externalized_source_count": len(
            canonical_externalized_paths
        ),
        "source_tree_replayed_count": source_tree_replayed_count,
        "source_tree_externalized_count": source_tree_externalized_count,
        "incomplete_record_count": incomplete_record_count,
        "pack_count": pack_count,
        "state": (
            "complete"
            if not externalized_paths and incomplete_record_count == 0
            else "partial"
        ),
    }


def verify_tree(root: Path) -> dict[str, object]:
    try:
        selected_root = Path(root).resolve(strict=True)
    except OSError as exc:
        raise DistributionError(
            f"unpacked tree is unavailable ({exc.__class__.__name__})"
        ) from exc
    manifest_path = selected_root / MANIFEST_PATH
    raw, _ = _read_regular_file(manifest_path, MANIFEST_PATH)
    manifest = _parse_manifest(raw)
    entries = manifest["files"]
    assert isinstance(entries, list)
    expected = {MANIFEST_PATH, *(str(entry["path"]) for entry in entries)}
    actual: set[str] = set()
    for path in sorted(selected_root.rglob("*")):
        relative = path.relative_to(selected_root).as_posix()
        item = path.lstat()
        if stat.S_ISDIR(item.st_mode):
            if stat.S_ISLNK(item.st_mode):
                raise DistributionError(f"{relative}: unpacked symlink is forbidden")
            continue
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
            raise DistributionError(f"{relative}: unpacked non-regular file is forbidden")
        actual.add(relative)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise DistributionError(
            f"unpacked inventory mismatch; missing={missing[:3]} extra={extra[:3]}"
        )
    for entry in entries:
        path = str(entry["path"])
        payload, mode = _read_regular_file(selected_root / path, path)
        _validate_release_path(path, frozenset(manifest["active_skill_ids"]))
        _scan_content(path, payload)
        if len(payload) != entry["size"] or _sha256(payload) != entry["sha256"]:
            raise DistributionError(f"{path}: unpacked content does not match manifest")
        if f"{mode:04o}" != entry["mode"]:
            raise DistributionError(f"{path}: unpacked mode does not match manifest")
    active = tuple(manifest["active_skill_ids"])
    manifest_paths = frozenset(str(entry["path"]) for entry in entries)
    _validate_packaged_registries(selected_root, active, manifest_paths)
    source_registry_digests = _validate_source_registry_snapshots(
        selected_root,
        manifest,
        manifest_paths,
    )
    _validate_filtered_registry_projection(selected_root, active)
    externalized_receipts = {
        record["path"]: record
        for record in manifest["excluded_legacy_official_artifacts"]
    }
    pack_audit = _portable_official_document_pack_audit(
        selected_root,
        active,
        manifest_paths,
        source_registry_digests,
        externalized_receipts,
    )
    _validate_dependency_lock_closure(selected_root, manifest_paths)
    contract_entries = [
        f"{entry['path']}\0{entry['sha256']}\n".encode("utf-8")
        for entry in entries
        if str(entry["path"]).startswith("contracts/")
    ]
    digest = _sha256(
        b"VIBE-DFT-ACTIVE-CONTRACT-CATALOG-v1\0" + b"".join(contract_entries)
    )
    if digest != manifest["contract_catalog_sha256"]:
        raise DistributionError("contract catalog digest does not match manifest")
    return {
        "active_skill_ids": list(active),
        "file_count": len(entries),
        "file_paths": [str(entry["path"]) for entry in entries],
        "legacy_official_artifact_count": sum(
            _is_legacy_official_artifact(str(entry["path"])) for entry in entries
        ),
        "official_document_externalized_source_count": pack_audit[
            "externalized_source_count"
        ],
        "official_document_incomplete_record_count": pack_audit[
            "incomplete_record_count"
        ],
        "official_document_pack_audit": pack_audit["state"],
        "official_document_pack_count": pack_audit["pack_count"],
        "source_registry_snapshot_count": len(source_registry_digests),
        "source_commit": manifest["source_commit"],
        "verification": "passed",
    }


def _prepare_extraction_root(path: Path) -> Path:
    selected = Path(path)
    if selected.exists():
        if selected.is_symlink() or not selected.is_dir():
            raise DistributionError("extraction root must be a safe directory")
        try:
            if any(selected.iterdir()):
                raise DistributionError("extraction root must be empty")
        except OSError as exc:
            raise DistributionError(
                f"extraction root is unreadable ({exc.__class__.__name__})"
            ) from exc
    else:
        selected.mkdir(parents=True, mode=0o755)
    return selected.resolve(strict=True)


def _verify_archive_into(archive_path: Path, extraction_root: Path) -> dict[str, object]:
    try:
        archive_stat = archive_path.lstat()
    except OSError as exc:
        raise DistributionError(
            f"archive is unavailable ({exc.__class__.__name__})"
        ) from exc
    if (
        stat.S_ISLNK(archive_stat.st_mode)
        or not stat.S_ISREG(archive_stat.st_mode)
        or archive_stat.st_nlink != 1
        or archive_stat.st_size > MAX_ARCHIVE_BYTES
    ):
        raise DistributionError("archive must be a bounded ordinary non-linked file")
    try:
        handle = tarfile.open(archive_path, mode="r:")
    except (OSError, tarfile.TarError) as exc:
        raise DistributionError(f"archive is malformed ({exc.__class__.__name__})") from exc
    seen: set[str] = set()
    manifest_raw: bytes | None = None
    try:
        members = handle.getmembers()
        if not members or len(members) > MAX_ARCHIVE_FILES + 1:
            raise DistributionError("archive member count is invalid")
        for member in members:
            path = _safe_archive_path(
                member.name,
                allow_manifest=True,
            )
            if path in seen:
                raise DistributionError(f"{path}: duplicate archive member")
            seen.add(path)
            if not member.isfile() or member.islnk() or member.issym():
                raise DistributionError(f"{path}: archive links and special files are forbidden")
            if member.size < 0 or member.size > MAX_FILE_BYTES:
                raise DistributionError(f"{path}: archive member size is invalid")
            if member.uid != 0 or member.gid != 0 or member.mtime != 0:
                raise DistributionError(f"{path}: archive metadata is not normalized")
            if member.mode not in {0o644, 0o755}:
                raise DistributionError(f"{path}: archive mode is not normalized")
            source = handle.extractfile(member)
            if source is None:
                raise DistributionError(f"{path}: archive member is unreadable")
            raw = source.read(MAX_FILE_BYTES + 1)
            if len(raw) != member.size:
                raise DistributionError(f"{path}: archive member size changed")
            _scan_content(path, raw)
            if path == MANIFEST_PATH:
                manifest_raw = raw
            destination = extraction_root.joinpath(*PurePosixPath(path).parts)
            try:
                destination.relative_to(extraction_root)
            except ValueError as exc:
                raise DistributionError(f"{path}: extraction path escapes root") from exc
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as output:
                output.write(raw)
            os.chmod(destination, member.mode)
    finally:
        handle.close()
    if manifest_raw is None:
        raise DistributionError("archive manifest is missing")
    manifest = _parse_manifest(manifest_raw)
    expected = {MANIFEST_PATH, *(entry["path"] for entry in manifest["files"])}
    if seen != expected:
        raise DistributionError("archive inventory does not match its manifest")
    canonical_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".vibe-dft-active-canonical.",
            suffix=".tar",
            delete=False,
        ) as canonical_handle:
            canonical_path = Path(canonical_handle.name)
        _write_normalized_tar_tree(
            canonical_path,
            extraction_root,
            manifest_raw,
            manifest["files"],
        )
        if not _files_are_byte_identical(archive_path, canonical_path):
            raise DistributionError(
                "archive bytes are not the canonical normalized tar encoding; "
                "noncanonical headers, EOF padding, or trailing bytes are forbidden"
            )
    finally:
        if canonical_path is not None:
            canonical_path.unlink(missing_ok=True)
    try:
        archive_after = archive_path.lstat()
    except OSError as exc:
        raise DistributionError(
            f"archive changed during verification ({exc.__class__.__name__})"
        ) from exc
    before_identity = (
        archive_stat.st_dev,
        archive_stat.st_ino,
        archive_stat.st_size,
        archive_stat.st_mtime_ns,
        archive_stat.st_mode,
        archive_stat.st_nlink,
    )
    after_identity = (
        archive_after.st_dev,
        archive_after.st_ino,
        archive_after.st_size,
        archive_after.st_mtime_ns,
        archive_after.st_mode,
        archive_after.st_nlink,
    )
    if before_identity != after_identity:
        raise DistributionError("archive changed during verification")
    return verify_tree(extraction_root)


def verify_archive(
    archive_path: Path,
    *,
    extraction_root: Path | None = None,
) -> dict[str, object]:
    """Safely unpack and revalidate every member against the embedded manifest."""

    selected_archive = Path(archive_path).resolve(strict=False)
    if extraction_root is not None:
        root = _prepare_extraction_root(extraction_root)
        return _verify_archive_into(selected_archive, root)
    with tempfile.TemporaryDirectory(prefix="vibe-dft-active-verify-") as temporary:
        return _verify_archive_into(selected_archive, Path(temporary).resolve())


def _emit_report(report: Mapping[str, object]) -> None:
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="build a deterministic active-only tar")
    build.add_argument("--root", type=Path, default=repo_root())
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--force", action="store_true")
    build.add_argument(
        "--require-clean-commit",
        action="store_true",
        help=(
            "fail unless every selected source input is tracked with exact "
            "bytes and executable mode in the declared clean Git commit"
        ),
    )
    build.add_argument(
        "--protected-branch",
        action="store_true",
        help="record a user assertion; this tool cannot verify GitHub protection",
    )
    verify = subparsers.add_parser("verify", help="safely unpack and verify a tar")
    verify.add_argument("archive", type=Path)
    verify.add_argument("--extract-to", type=Path)
    tree = subparsers.add_parser("verify-tree", help="verify an already unpacked tree")
    tree.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            report = build_distribution(
                args.root,
                args.output,
                overwrite=args.force,
                protected_branch=args.protected_branch,
                require_clean_commit=args.require_clean_commit,
            )
        elif args.command == "verify":
            report = verify_archive(args.archive, extraction_root=args.extract_to)
        else:
            report = verify_tree(args.directory)
    except (DistributionError, OSError, ValueError) as exc:
        print(f"ERROR ACTIVE_ONLY_DISTRIBUTION {exc}", file=sys.stderr)
        return 2
    _emit_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
