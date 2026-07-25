#!/usr/bin/env python3
"""Validate an immutable Vibe-DFT record/artifact bundle fail closed."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Any, Iterator
import uuid

from jsonschema import Draft202012Validator

import validate_contract
import bundle_semantics
import strict_json
from registry_yaml import RegistryYAMLError, loads_yaml_strict


MANIFEST_MAX_BYTES = 8 * 1024 * 1024
RECORD_MAX_BYTES = 64 * 1024 * 1024
JSON_OBJECT_REF_KEYS = frozenset(
    {"contract_name", "schema_version", "record_id", "sha256", "role"}
)
FILE_REF_KEYS = frozenset(
    {
        "role",
        "label",
        "media_type",
        "format",
        "format_version",
        "availability",
        "sha256",
        "bytes",
        "sensitivity",
        "redistribution",
    }
)
FORBIDDEN_PRIVATE_KEYS = frozenset(
    {
        "access_key",
        "access_token",
        "api_key",
        "authorization_token",
        "cookie",
        "email",
        "full_name",
        "host_name",
        "hostname",
        "password",
        "passwd",
        "private_key",
        "secret",
        "secret_key",
        "ssh_key",
        "token",
        "user_name",
        "username",
    }
)
ABSOLUTE_PATH = re.compile(
    r"^(?:/|~/|[A-Za-z]:[\\/]|\\\\)|"
    r"(?:^|[\s=,:;()\[\]{}\"'])(?:/Users/|/home/|/private/|/tmp/|"
    r"/Volumes/|/scratch/|/gpfs/|/lustre/|/mnt/|/work/|/project/)"
)
TRAVERSAL_PATH = re.compile(r"(?:^|[/\\])\.\.(?:[/\\]|$)")
SECRET_TEXT_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|api[_-]?key|secret)\s*[:=]\s*\S+", re.IGNORECASE),
)
RESTRICTED_DFT_NAME = re.compile(r"(?:^|/)(?:POTCAR(?:\..*)?|[^/]*\.psctr)$", re.IGNORECASE)
RESTRICTED_DFT_MARKERS = (
    b"TITEL  = PAW_",
    b"VRHFIN =",
    b"End of Dataset",
    b"PSCTR",
)
CREDENTIAL_BYTE_MARKERS = (
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
    b"password=",
    b"passwd=",
    b"api_key=",
    b"access_token=",
)
FILESYSTEM_CODES = frozenset(
    {
        "ARTIFACT_INDEX_MISMATCH",
        "BUNDLE_LABEL_COLLISION",
        "BUNDLE_PATH_COLLISION",
        "HARDLINK_ALIAS_REJECTED",
        "SPECIAL_FILE_REJECTED",
        "SYMLINK_REJECTED",
        "UNLISTED_BUNDLE_ENTRY",
        "UNSAFE_BUNDLE_PATH",
        "RECORD_TOPOLOGICAL_INDEX_MISMATCH",
    }
)
RECORD_INTEGRITY_CODES = frozenset(
    {
        "DUPLICATE_RECORD_IDENTITY",
        "RECORD_CONTRACT_UNKNOWN",
        "RECORD_ID_MISMATCH",
        "RECORD_JSON_INVALID",
        "RECORD_NOT_CONTENT_ADDRESSED",
        "RECORD_RAW_SHA256_MISMATCH",
        "RECORD_SCHEMA_INVALID",
        "RECORD_SCHEMA_VERSION_MISMATCH",
        "RECORD_UNREADABLE",
    }
)
REFERENCE_CODES = frozenset(
    {
        "RECORD_REF_CYCLE",
        "RECORD_REF_FORWARD_REFERENCE",
        "RECORD_REF_RAW_SHA256_MISMATCH",
        "RECORD_REF_SCHEMA_VERSION_MISMATCH",
        "RECORD_REF_SELF_REFERENCE",
        "RECORD_REF_TARGET_AMBIGUOUS",
        "RECORD_REF_TARGET_NOT_AUTHENTICATED",
        "RECORD_REF_TARGET_NOT_CONTENT_ADDRESSED",
        "RECORD_REF_TARGET_UNKNOWN_CONTRACT",
        "RECORD_REF_TARGET_UNRESOLVED",
    }
)
ARTIFACT_CODES = frozenset(
    {
        "ARTIFACT_BYTES_MISMATCH",
        "ARTIFACT_FILE_MISSING",
        "ARTIFACT_RAW_SHA256_MISMATCH",
        "FILE_REF_ARTIFACT_METADATA_MISMATCH",
        "FILE_REF_ARTIFACT_UNRESOLVED",
    }
)
PRIVACY_CODES = frozenset(
    {
        "ABSOLUTE_PATH_DISCLOSED",
        "CREDENTIAL_MATERIAL_DISCLOSED",
        "PRIVATE_ARTIFACT_INCLUDED",
        "PRIVATE_IDENTIFIER_FIELD_DISCLOSED",
        "RESTRICTED_ARTIFACT_INCLUDED",
        "RESTRICTED_DFT_PAYLOAD_INCLUDED",
        "TRAVERSAL_PATH_DISCLOSED",
    }
)
LEGACY_MANDATORY_OBLIGATIONS = {
    filename.removesuffix(".schema.json"): ("LEGACY_CONTRACT_CLAIM_BOUNDARY",)
    for filename in validate_contract.LEGACY_RECORD_ID_FIELDS
}


class BundleSetupError(ValueError):
    """The validator trust root or manifest cannot be established."""


@dataclass
class Finding:
    code: str
    severity: str
    location: str
    message: str
    record_index: int | None = None
    artifact_index: int | None = None

    def as_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "location": self.location,
            "message": self.message,
        }
        if self.record_index is not None:
            value["record_index"] = self.record_index
        if self.artifact_index is not None:
            value["artifact_index"] = self.artifact_index
        return value


@dataclass
class LoadedRecord:
    index: int
    entry: dict[str, Any]
    raw: bytes | None = None
    actual_sha256: str | None = None
    data: dict[str, Any] | None = None
    contract: validate_contract.ContractSchema | None = None
    lifecycle: str = "unknown"
    status: str = "pass"
    finding_codes: set[str] = field(default_factory=set)

    @property
    def identity(self) -> tuple[str, str, str]:
        return (
            self.entry["contract_name"],
            self.entry["schema_version"],
            self.entry["record_id"],
        )

    @property
    def structurally_valid(self) -> bool:
        return not self.finding_codes.intersection(RECORD_INTEGRITY_CODES)

    @property
    def integrity_verified_active(self) -> bool:
        return self.structurally_valid and self.lifecycle == "active"


@dataclass
class LoadedArtifact:
    index: int
    entry: dict[str, Any]
    status: str = "pass"
    finding_codes: set[str] = field(default_factory=set)
    actual_sha256: str | None = None
    actual_bytes: int | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_regular_file(path: Path, *, max_bytes: int | None = None) -> tuple[bytes, os.stat_result]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise BundleSetupError(f"cannot inspect required file '{path.name}': {exc}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise BundleSetupError(f"symlink is forbidden: {path.name}")
    if not stat.S_ISREG(info.st_mode):
        raise BundleSetupError(f"required path is not a regular file: {path.name}")
    if info.st_nlink != 1:
        raise BundleSetupError(f"hardlink alias is forbidden: {path.name}")
    if max_bytes is not None and info.st_size > max_bytes:
        raise BundleSetupError(
            f"file exceeds maximum size ({info.st_size} > {max_bytes} bytes): {path.name}"
        )
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BundleSetupError(f"cannot read required file '{path.name}': {exc}") from exc
    return raw, info


def _schema_error_locations(
    contract: validate_contract.ContractSchema,
    data: object,
    catalog: validate_contract.ContractCatalog,
) -> list[str]:
    validator = Draft202012Validator(
        contract.schema,
        registry=catalog.registry,
        format_checker=validate_contract.FORMAT_CHECKER,
    )
    errors = sorted(
        validator.iter_errors(data),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    result = []
    for error in errors:
        pointer = _pointer(tuple(error.absolute_path))
        result.append(f"{pointer} ({error.validator})")
    return result


def _pointer(parts: tuple[object, ...]) -> str:
    if not parts:
        return "/"
    return "/" + "/".join(
        str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


def _iter_objects(
    value: object, parts: tuple[object, ...] = ()
) -> Iterator[tuple[tuple[object, ...], dict[str, Any]]]:
    if isinstance(value, dict):
        yield parts, value
        for key, child in value.items():
            yield from _iter_objects(child, (*parts, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_objects(child, (*parts, index))


def _safe_relative_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    normalized = path.as_posix()
    if normalized != value or normalized.startswith("/"):
        return None
    return normalized


def _add_finding(
    findings: list[Finding],
    code: str,
    severity: str,
    location: str,
    message: str,
    *,
    record: LoadedRecord | None = None,
    artifact: LoadedArtifact | None = None,
) -> None:
    finding = Finding(
        code=code,
        severity=severity,
        location=location,
        message=message,
        record_index=record.index if record is not None else None,
        artifact_index=artifact.index if artifact is not None else None,
    )
    findings.append(finding)
    if record is not None:
        record.finding_codes.add(code)
        if severity == "error":
            record.status = "fail"
        elif record.status == "pass":
            record.status = "blocked"
    if artifact is not None:
        artifact.finding_codes.add(code)
        if severity == "error":
            artifact.status = "fail"
        elif artifact.status == "pass":
            artifact.status = "blocked"


def _privacy_findings(
    value: object,
    location: str,
    findings: list[Finding],
    *,
    record: LoadedRecord | None = None,
) -> None:
    def visit(node: object, parts: tuple[object, ...]) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                normalized = key.strip().lower().replace("-", "_")
                if normalized in FORBIDDEN_PRIVATE_KEYS:
                    _add_finding(
                        findings,
                        "PRIVATE_IDENTIFIER_FIELD_DISCLOSED",
                        "error",
                        f"{location}{_pointer((*parts, key))}",
                        "A credential or private-identity field name is forbidden.",
                        record=record,
                    )
                visit(child, (*parts, key))
        elif isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, (*parts, index))
        elif isinstance(node, str):
            pointer = f"{location}{_pointer(parts)}"
            if ABSOLUTE_PATH.search(node):
                _add_finding(
                    findings,
                    "ABSOLUTE_PATH_DISCLOSED",
                    "error",
                    pointer,
                    "An absolute or private filesystem path is forbidden.",
                    record=record,
                )
            if TRAVERSAL_PATH.search(node):
                _add_finding(
                    findings,
                    "TRAVERSAL_PATH_DISCLOSED",
                    "error",
                    pointer,
                    "A parent-directory traversal segment is forbidden.",
                    record=record,
                )
            if any(pattern.search(node) for pattern in SECRET_TEXT_PATTERNS):
                _add_finding(
                    findings,
                    "CREDENTIAL_MATERIAL_DISCLOSED",
                    "error",
                    pointer,
                    "Potential credential material is forbidden.",
                    record=record,
                )

    visit(value, ())


def _load_registry_context(
    path: Path, root: Path
) -> tuple[dict[str, str], dict[str, Any], dict[str, bytes]]:
    """Load one validated canonical registry snapshot plus operation routes."""

    canonical_path = root / "registry" / "interface-registry.yaml"
    if path.resolve() == canonical_path.resolve():
        try:
            import registry_snapshot

            snapshot = registry_snapshot.load_registry_snapshot(
                root, validate_sources=False
            )
        except Exception as exc:
            raise BundleSetupError(
                f"cannot load canonical registry snapshot: {exc}"
            ) from exc
        interfaces = snapshot.interfaces["interfaces"]
        lifecycle = {
            name: item["lifecycle"]
            for name, item in interfaces.items()
            if isinstance(name, str) and isinstance(item, dict)
        }
        raw_registries = {
            filename.removesuffix(".yaml"): raw
            for filename, raw in snapshot.registry_raw.items()
        }
        context = {
            "interfaces": snapshot.interfaces,
            "skills": snapshot.skills,
            "software": snapshot.software,
            "environments": snapshot.environments,
            "operation_routes": snapshot.operation_routes,
            "official_source_authorities": (
                snapshot.active_official_source_authorities()
            ),
            # Only a hosting platform may replace this empty mapping before
            # invoking a future non-CLI adapter-aware validator version.
            "external_trust_adapter_results": {},
        }
        return lifecycle, context, raw_registries

    # A noncanonical registry path is maintenance-only and never provides active
    # evidence assurance.  It is still parsed and structurally checked so tests
    # and migration tooling fail closed.
    try:
        raw, _info = _read_regular_file(path, max_bytes=8 * 1024 * 1024)
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise RegistryYAMLError(
                "YAML_ENCODING_INVALID", path.name, "expected strict UTF-8"
            ) from exc
        data = loads_yaml_strict(text, path.name)
    except (BundleSetupError, RegistryYAMLError) as exc:
        raise BundleSetupError(f"cannot load interface registry: {exc}") from exc
    try:
        import interface_registry

        failures = interface_registry.validation_errors(data, root)
    except Exception as exc:
        raise BundleSetupError(f"cannot validate interface registry: {exc}") from exc
    if failures:
        raise BundleSetupError(
            "interface registry is invalid: " + "; ".join(failures)
        )
    assert isinstance(data, dict)
    interfaces = data.get("interfaces")
    assert isinstance(interfaces, dict)
    lifecycle = {
        name: "maintenance"
        for name, item in interfaces.items()
        if isinstance(name, str) and isinstance(item, dict)
    }
    return lifecycle, {
        "interfaces": data,
        "skills": {},
        "software": {},
        "environments": {},
        "operation_routes": {},
        "official_source_authorities": {},
        "external_trust_adapter_results": {},
    }, {"interface-registry": raw}


def _catalog_trust_root(
    catalog: validate_contract.ContractCatalog, registry_raw: dict[str, bytes]
) -> dict[str, Any]:
    entries = []
    lines = []
    for contract in sorted(catalog.contracts, key=lambda item: item.schema_id):
        entries.append(
            {"schema_id": contract.schema_id, "sha256": contract.raw_sha256}
        )
        lines.append(f"{contract.schema_id} {contract.raw_sha256}\n")
    catalog_digest = _sha256("".join(lines).encode("utf-8"))
    return {
        "digest_algorithm": "sha256",
        "catalog_digest": catalog_digest,
        "catalog_entry_count": len(entries),
        "catalog_entries": entries,
        "registry_entries": [
            {"label": label, "sha256": _sha256(raw)}
            for label, raw in sorted(registry_raw.items())
        ],
    }


def _assert_registry_catalog_binding(
    registry: object,
    catalog: validate_contract.ContractCatalog,
) -> None:
    """Bind active registry interfaces to the exact schema bytes already parsed."""

    if not isinstance(registry, dict) or not isinstance(
        registry.get("interfaces"), dict
    ):
        raise BundleSetupError(
            "REGISTRY_CATALOG_SNAPSHOT_MISMATCH: interface registry shape is invalid"
        )
    mismatches: list[str] = []
    for interface_id, specification in registry["interfaces"].items():
        if not isinstance(specification, dict) or specification.get("lifecycle") != "active":
            continue
        try:
            contract = catalog.resolve(str(interface_id))
        except validate_contract.ContractSelectionError:
            mismatches.append(f"{interface_id}: absent from loaded catalog")
            continue
        expected_path = f"contracts/{contract.filename}"
        if specification.get("schema_path") != expected_path:
            mismatches.append(f"{interface_id}: schema_path differs")
        if specification.get("schema_sha256") != contract.raw_sha256:
            mismatches.append(f"{interface_id}: schema_sha256 differs")
    if mismatches:
        raise BundleSetupError(
            "REGISTRY_CATALOG_SNAPSHOT_MISMATCH: " + "; ".join(mismatches)
        )


def _validator_execution(validation_run_id: str) -> dict[str, Any]:
    """Bind the exact repository-owned validator components used by this run."""

    tool_root = Path(__file__).resolve().parent
    components = {
        "validate-bundle": tool_root / "validate_bundle.py",
        "bundle-semantics": tool_root / "bundle_semantics.py",
        "validate-contract": tool_root / "validate_contract.py",
        "strict-json": tool_root / "strict_json.py",
        "registry-yaml": tool_root / "registry_yaml.py",
    }
    for module_name in bundle_semantics.BUILTIN_DOMAIN_MODULES:
        candidate = tool_root / f"{module_name}.py"
        if candidate.is_file():
            components[module_name.replace("_", "-")] = candidate
    return {
        "execution_id": f"validator-exec-{validation_run_id.removeprefix('validation-run-')}",
        "validator_id": "vibe-dft-bundle-validator",
        "validator_version": "1.0",
        "execution_mode": "repository-controlled",
        "dynamic_module_selection": False,
        "components": [
            {"label": label, "sha256": _sha256(path.read_bytes())}
            for label, path in sorted(components.items())
        ],
    }


def _inventory_findings(
    root: Path,
    allowed_files: set[str],
    findings: list[Finding],
) -> None:
    allowed_directories: set[str] = set()
    for item in allowed_files:
        parts = PurePosixPath(item).parts[:-1]
        for length in range(1, len(parts) + 1):
            allowed_directories.add(PurePosixPath(*parts[:length]).as_posix())

    def walk(directory: Path, prefix: str = "") -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError as exc:
            _add_finding(
                findings,
                "UNLISTED_BUNDLE_ENTRY",
                "error",
                "bundle-root",
                f"Bundle inventory cannot be read: {exc.__class__.__name__}.",
            )
            return
        for entry in entries:
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                _add_finding(
                    findings,
                    "SPECIAL_FILE_REJECTED",
                    "error",
                    relative,
                    "Bundle entry cannot be inspected as a regular file or directory.",
                )
                continue
            if stat.S_ISLNK(info.st_mode):
                _add_finding(
                    findings,
                    "SYMLINK_REJECTED",
                    "error",
                    relative,
                    "Symlinks are forbidden inside a bundle.",
                )
            elif stat.S_ISDIR(info.st_mode):
                if relative not in allowed_directories:
                    _add_finding(
                        findings,
                        "UNLISTED_BUNDLE_ENTRY",
                        "error",
                        relative,
                        "Directory is not an ancestor of a listed bundle path.",
                    )
                else:
                    walk(Path(entry.path), relative)
            elif stat.S_ISREG(info.st_mode):
                if relative not in allowed_files:
                    _add_finding(
                        findings,
                        "UNLISTED_BUNDLE_ENTRY",
                        "error",
                        relative,
                        "Regular file is not listed by the manifest or explicit report output.",
                    )
                elif info.st_nlink != 1:
                    _add_finding(
                        findings,
                        "HARDLINK_ALIAS_REJECTED",
                        "error",
                        relative,
                        "Hardlink aliases are forbidden inside a bundle.",
                    )
            else:
                _add_finding(
                    findings,
                    "SPECIAL_FILE_REJECTED",
                    "error",
                    relative,
                    "Only regular files and required directories are permitted.",
                )

    walk(root)


def _stream_artifact(path: Path) -> tuple[str, int, bool, bool]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise BundleSetupError(f"artifact is missing: {path.name}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise BundleSetupError(f"artifact symlink is forbidden: {path.name}")
    if not stat.S_ISREG(info.st_mode):
        raise BundleSetupError(f"artifact is not a regular file: {path.name}")
    if info.st_nlink != 1:
        raise BundleSetupError(f"artifact hardlink alias is forbidden: {path.name}")
    digest = hashlib.sha256()
    total = 0
    restricted_marker = False
    credential_marker = False
    tail = b""
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
                total += len(block)
                sample = tail + block
                if any(marker in sample for marker in RESTRICTED_DFT_MARKERS):
                    restricted_marker = True
                lowered = sample.lower()
                if any(marker.lower() in lowered for marker in CREDENTIAL_BYTE_MARKERS):
                    credential_marker = True
                tail = sample[-64:]
    except OSError as exc:
        raise BundleSetupError(f"cannot read artifact: {path.name}") from exc
    return digest.hexdigest(), total, restricted_marker, credential_marker


def _obligation_ids(schema: dict[str, Any]) -> list[object]:
    result: list[object] = []
    for key, value in schema.items():
        if not key.startswith("x-vibe-") or "obligation" not in key:
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict) and isinstance(item.get("finding_id"), str):
                    result.append(item["finding_id"])
                else:
                    result.append(item)
        elif isinstance(value, dict):
            checks = value.get("required_checks")
            if isinstance(checks, list):
                result.extend(checks)
            else:
                result.append(checks)
        else:
            result.append(value)
    return result


def _contract_obligation_ids(
    contract: validate_contract.ContractSchema,
) -> list[object]:
    """Return advertised obligations plus mandatory legacy claim boundaries."""

    advertised = _obligation_ids(contract.schema)
    if advertised or not contract.is_legacy:
        return advertised
    return list(LEGACY_MANDATORY_OBLIGATIONS.get(contract.name, ()))


def _status_for_codes(findings: list[Finding], codes: set[str] | frozenset[str]) -> str:
    matched = [finding for finding in findings if finding.code in codes]
    if any(finding.severity == "error" for finding in matched):
        return "fail"
    if matched:
        return "blocked"
    return "pass"


def _record_reference_results(
    records: list[LoadedRecord],
    findings: list[Finding],
    catalog: validate_contract.ContractCatalog,
) -> list[dict[str, Any]]:
    identities: dict[tuple[str, str, str], list[LoadedRecord]] = {}
    for record in records:
        identities.setdefault(record.identity, []).append(record)
    for identity, matches in identities.items():
        if len(matches) > 1:
            for record in matches:
                _add_finding(
                    findings,
                    "DUPLICATE_RECORD_IDENTITY",
                    "error",
                    f"record:{record.entry['label']}",
                    "Record contract name and record ID must be globally unique.",
                    record=record,
                )

    results: list[dict[str, Any]] = []
    graph: dict[int, set[int]] = {record.index: set() for record in records}
    for source in records:
        if source.data is None:
            continue
        for parts, candidate in _iter_objects(source.data):
            if frozenset(candidate) != JSON_OBJECT_REF_KEYS:
                continue
            location = _pointer(parts)
            target_contract_name = candidate.get("contract_name")
            target_record_id = candidate.get("record_id")
            result = {
                "source_record_index": source.index,
                "location": location,
                "target_contract_name": str(target_contract_name),
                "target_record_id": str(target_record_id),
                "status": "pass",
                "finding_codes": [],
            }

            def reject(code: str, message: str, *, blocked: bool = False) -> None:
                severity = "warning" if blocked else "error"
                _add_finding(
                    findings,
                    code,
                    severity,
                    f"record:{source.entry['label']}{location}",
                    message,
                    record=source,
                )
                result["finding_codes"].append(code)
                if result["status"] != "fail":
                    result["status"] = "blocked" if blocked else "fail"

            if not isinstance(target_contract_name, str) or not isinstance(
                target_record_id, str
            ):
                reject("RECORD_REF_TARGET_UNRESOLVED", "Reference identity is malformed.")
                results.append(result)
                continue
            target_version = candidate.get("schema_version")
            candidates = identities.get(
                (target_contract_name, target_version, target_record_id), []
            )
            version_alternatives = [
                item
                for identity, values in identities.items()
                if identity[0] == target_contract_name
                and identity[2] == target_record_id
                for item in values
            ]
            target_contracts = catalog.by_name.get(target_contract_name, ())
            if not target_contracts:
                reject(
                    "RECORD_REF_TARGET_UNKNOWN_CONTRACT",
                    "Reference names no contract in the closed local catalog.",
                )
            elif not any(item.is_record_ref_target for item in target_contracts):
                reject(
                    "RECORD_REF_TARGET_NOT_CONTENT_ADDRESSED",
                    "Reference contract is a projection or definition library.",
                )
            if not candidates:
                if version_alternatives:
                    reject(
                        "RECORD_REF_SCHEMA_VERSION_MISMATCH",
                        "Reference schema version does not match the indexed target.",
                    )
                reject(
                    "RECORD_REF_TARGET_UNRESOLVED",
                    "Reference target is absent from the bundle record index.",
                )
                results.append(result)
                continue
            if len(candidates) != 1:
                reject(
                    "RECORD_REF_TARGET_AMBIGUOUS",
                    "Reference target identity is duplicated in the bundle.",
                )
                results.append(result)
                continue
            target = candidates[0]
            graph[source.index].add(target.index)
            if target.index == source.index:
                reject("RECORD_REF_SELF_REFERENCE", "Self-reference is forbidden.")
            elif target.index >= source.index:
                reject(
                    "RECORD_REF_FORWARD_REFERENCE",
                    "Reference target must precede its referrer in topological order.",
                )
            if candidate.get("schema_version") != target.entry["schema_version"]:
                reject(
                    "RECORD_REF_SCHEMA_VERSION_MISMATCH",
                    "Reference schema version does not match the indexed target.",
                )
            if candidate.get("sha256") != target.actual_sha256:
                reject(
                    "RECORD_REF_RAW_SHA256_MISMATCH",
                    "Reference digest does not match exact raw target file bytes.",
                )
            if target.contract is not None and not target.contract.is_record_ref_target:
                reject(
                    "RECORD_REF_TARGET_NOT_CONTENT_ADDRESSED",
                    "Projection and definition-library contracts cannot be reference targets.",
                )
            if not target.structurally_valid:
                reject(
                    "RECORD_REF_TARGET_NOT_AUTHENTICATED",
                    "Target failed hash, schema, or identity validation.",
                )
            elif target.lifecycle != "active":
                reject(
                    "RECORD_REF_TARGET_NOT_AUTHENTICATED",
                    "Target interface is not active; assurance is contract-only.",
                    blocked=True,
                )
            result["finding_codes"] = sorted(set(result["finding_codes"]))
            results.append(result)

    visiting: set[int] = set()
    visited: set[int] = set()
    cyclic_nodes: set[int] = set()

    def visit(node: int, trail: tuple[int, ...]) -> None:
        if node in visiting:
            cyclic_nodes.update(trail[trail.index(node) :])
            return
        if node in visited:
            return
        visiting.add(node)
        for target in graph[node]:
            visit(target, (*trail, target))
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node, (node,))
    for index in sorted(cyclic_nodes):
        record = records[index]
        _add_finding(
            findings,
            "RECORD_REF_CYCLE",
            "error",
            f"record:{record.entry['label']}",
            "Record reference graph contains a cycle.",
            record=record,
        )
    return results


def _file_reference_results(
    records: list[LoadedRecord],
    artifacts: list[LoadedArtifact],
    findings: list[Finding],
) -> list[dict[str, Any]]:
    by_label = {artifact.entry["label"]: artifact for artifact in artifacts}
    results: list[dict[str, Any]] = []
    comparable = (
        "role",
        "media_type",
        "format",
        "format_version",
        "availability",
        "sha256",
        "bytes",
        "sensitivity",
        "redistribution",
    )
    for source in records:
        if source.data is None:
            continue
        for parts, candidate in _iter_objects(source.data):
            if frozenset(candidate) != FILE_REF_KEYS:
                continue
            location = _pointer(parts)
            label = candidate.get("label")
            result = {
                "source_record_index": source.index,
                "location": location,
                "artifact_label": str(label),
                "availability": str(candidate.get("availability", "unknown")),
                "status": "pass",
                "finding_codes": [],
            }
            artifact = by_label.get(label) if isinstance(label, str) else None
            if artifact is None:
                code = "FILE_REF_ARTIFACT_UNRESOLVED"
                _add_finding(
                    findings,
                    code,
                    "error",
                    f"record:{source.entry['label']}{location}",
                    "fileRef label does not resolve to the artifact inventory.",
                    record=source,
                )
                result["status"] = "fail"
                result["finding_codes"] = [code]
            elif any(candidate.get(key) != artifact.entry.get(key) for key in comparable):
                code = "FILE_REF_ARTIFACT_METADATA_MISMATCH"
                _add_finding(
                    findings,
                    code,
                    "error",
                    f"record:{source.entry['label']}{location}",
                    "fileRef metadata differs from the indexed artifact.",
                    record=source,
                )
                result["status"] = "fail"
                result["finding_codes"] = [code]
            results.append(result)
    return results


def _source_requires_external_trust(
    record: LoadedRecord,
    authority_snapshot: dict[str, Any],
) -> bool:
    """Apply the trusted canonical-snapshot boundary to an official source."""

    if record.entry["contract_name"] != "official-source-record" or record.data is None:
        return False
    data = record.data
    content = data.get("content", {})
    license_data = data.get("license", {})
    authority = data.get("authority", {})
    if not all(
        isinstance(item, dict)
        for item in (content, license_data, authority)
    ):
        return data.get("claim_ceiling") == "documented_behavior_only"
    policy = authority_snapshot.get(authority.get("authority_registry_id"), {})
    content_status = content.get("status")
    restricted = (
        license_data.get("status") == "known-restricted"
        or license_data.get("redistribution") in {"runtime-only", "restricted"}
    )
    if content_status == "externally-resolved" or restricted:
        return True
    if data.get("claim_ceiling") != "documented_behavior_only":
        return False
    # Embedded content avoids a runtime resolver only through an exact
    # repository-verified canonical snapshot projection.  The record's own
    # trust_state is never sufficient: authority, snapshot/source IDs,
    # locator, version, raw bytes, byte count, and open redistribution must all
    # match the platform-controlled registry projection.
    pinned_ref = content.get("pinned_source_ref")
    canonical = policy.get("canonical_snapshot") if isinstance(policy, dict) else None
    sources = canonical.get("sources_by_id") if isinstance(canonical, dict) else None
    source = (
        sources.get(pinned_ref.get("source_id"))
        if isinstance(sources, dict) and isinstance(pinned_ref, dict)
        else None
    )
    pin_matches = (
        content_status == "embedded-open"
        and content.get("identity_mode") == "pinned-canonical-snapshot"
        and content.get("trust_state") == "canonical-snapshot-verified"
        and isinstance(pinned_ref, dict)
        and pinned_ref.get("authority_registry_id")
        == authority.get("authority_registry_id")
        and isinstance(canonical, dict)
        and canonical.get("integrity_verified") is True
        and pinned_ref.get("snapshot_id") == canonical.get("snapshot_id")
        and isinstance(source, dict)
        and source.get("canonical_url") == authority.get("canonical_url")
        and source.get("version_scope") == data.get("version_scope")
        and source.get("raw_integrity_verified") is True
        and source.get("raw_sha256") == content.get("raw_sha256")
        and source.get("raw_bytes") == content.get("bytes")
        and policy.get("bundle_content_policy") == "canonical-pinned-open-only"
        and policy.get("license_status") == "known-open"
        and "redistributable" in policy.get("redistribution", ())
        and license_data.get("status") == "known-open"
        and license_data.get("identifier") == policy.get("license_identifier")
        and license_data.get("terms_url") in policy.get("license_terms_urls", ())
        and license_data.get("redistribution") == "redistributable"
    )
    return not pin_matches


def _manifest_obligation_status(
    obligation_id: str, findings: list[Finding]
) -> tuple[str, str]:
    mapping: dict[str, tuple[str, set[str] | frozenset[str]]] = {
        "BUNDLE_FILESYSTEM_CONTAINMENT": ("bundle-filesystem-containment", FILESYSTEM_CODES),
        "BUNDLE_RECORD_RAW_BYTE_HASH_SCHEMA_AND_ID": (
            "bundle-record-integrity",
            RECORD_INTEGRITY_CODES,
        ),
        "BUNDLE_ARTIFACT_RAW_BYTE_HASH_AND_SIZE": (
            "bundle-artifact-integrity",
            ARTIFACT_CODES,
        ),
        "BUNDLE_RECORD_REFERENCE_DAG": ("bundle-record-reference-dag", REFERENCE_CODES),
        "BUNDLE_FILE_REFERENCE_RESOLUTION": (
            "bundle-file-reference-resolution",
            ARTIFACT_CODES,
        ),
        "BUNDLE_PRIVACY_BOUNDARY": ("bundle-privacy-boundary", PRIVACY_CODES),
        "BUNDLE_ALL_CONTRACT_OBLIGATIONS_ACCOUNTED": (
            "bundle-obligation-accounting",
            frozenset(),
        ),
    }
    handler, codes = mapping[obligation_id]
    return handler, _status_for_codes(findings, codes)


def validate_bundle(
    manifest_path: Path,
    *,
    contracts_dir: Path,
    interface_registry_path: Path,
    report_path: Path,
    maintenance_mode: bool = False,
    allow_local_validation: bool = False,
) -> tuple[dict[str, Any], int]:
    """Validate a schema-valid manifest and return its strict report and exit code."""

    catalog = validate_contract.load_catalog(contracts_dir)
    manifest_contract = catalog.resolve("bundle-manifest")
    report_contract = catalog.resolve("bundle-validation-report")
    root = manifest_path.parent.resolve()
    raw_manifest, _manifest_info = _read_regular_file(
        manifest_path, max_bytes=MANIFEST_MAX_BYTES
    )
    manifest_sha256 = _sha256(raw_manifest)
    manifest = strict_json.loads_object(raw_manifest, manifest_path.name)
    manifest_schema_errors = _schema_error_locations(manifest_contract, manifest, catalog)
    if manifest_schema_errors:
        raise BundleSetupError(
            "bundle manifest schema validation failed at: "
            + ", ".join(manifest_schema_errors)
        )
    if manifest["bundle_mode"] == "local-validation" and not allow_local_validation:
        raise BundleSetupError(
            "LOCAL_VALIDATION_AUTHORIZATION_REQUIRED: local-validation bundles "
            "require explicit --allow-local-validation"
        )

    lifecycle_by_interface, registry_snapshots, registry_raw = _load_registry_context(
        interface_registry_path, repo_root()
    )
    _assert_registry_catalog_binding(registry_snapshots.get("interfaces"), catalog)
    findings: list[Finding] = []
    core_interface_ids = (
        f"{manifest_contract.name}@{manifest_contract.version}",
        f"{report_contract.name}@{report_contract.version}",
    )
    inactive_core_interfaces = sorted(
        interface_id
        for interface_id in core_interface_ids
        if lifecycle_by_interface.get(interface_id) != "active"
    )
    for interface_id in inactive_core_interfaces:
        _add_finding(
            findings,
            "BUNDLE_CORE_INTERFACE_NOT_ACTIVE",
            "warning",
            f"validator-interface:{interface_id}",
            "The bundle core contract is not active in the selected interface trust root.",
        )

    interface_specs = registry_snapshots.get("interfaces", {}).get("interfaces", {})
    semantic_ownership_errors = bundle_semantics.builtin_ownership_errors()
    for contract in catalog.contracts:
        interface_id = f"{contract.name}@{contract.version}"
        specification = (
            interface_specs.get(interface_id, {})
            if isinstance(interface_specs, dict)
            else {}
        )
        classification = (
            specification.get("classification", {})
            if isinstance(specification, dict)
            else {}
        )
        governance_only = (
            isinstance(classification, dict)
            and classification.get("routing_scope") == "governance-only"
        )
        if (
            lifecycle_by_interface.get(interface_id) == "active"
            and contract.is_record_ref_target
            and _contract_obligation_ids(contract)
            and not governance_only
            and bundle_semantics.builtin_evaluator(contract.name) is None
        ):
            semantic_ownership_errors.append(
                f"{interface_id}: active semantic contract has no exact-one evaluator owner"
            )
    for message in sorted(set(semantic_ownership_errors)):
        _add_finding(
            findings,
            "SEMANTIC_EVALUATOR_OWNERSHIP_INVALID",
            "error",
            "validator-semantic-ownership",
            message,
        )
    if maintenance_mode:
        _add_finding(
            findings,
            "UNTRUSTED_VALIDATOR_TRUST_ROOT",
            "warning",
            "validator-trust-root",
            "Maintenance/test trust-root overrides cannot produce positive assurance.",
        )
    _privacy_findings(manifest, "manifest:", findings)

    report_relative: str | None = None
    try:
        report_relative = report_path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError:
        pass

    record_entries = manifest["records"]
    artifact_entries = manifest["artifacts"]
    all_paths: dict[str, str] = {manifest_path.name: "manifest"}
    all_labels: dict[str, str] = {}
    allowed_files = {manifest_path.name}
    if report_relative is not None:
        allowed_files.add(report_relative)

    def register_unique(value: str, owner: str, table: dict[str, str], kind: str) -> None:
        previous = table.get(value)
        if previous is not None:
            _add_finding(
                findings,
                "BUNDLE_PATH_COLLISION" if kind == "path" else "BUNDLE_LABEL_COLLISION",
                "error",
                owner,
                f"Bundle {kind} collides with another manifest entry.",
            )
        else:
            table[value] = owner

    for index, entry in enumerate(record_entries):
        owner = f"records/{index}"
        if entry["topological_index"] != index:
            _add_finding(
                findings,
                "RECORD_TOPOLOGICAL_INDEX_MISMATCH",
                "error",
                owner,
                "topological_index must equal the record's manifest array index.",
            )
        relative = _safe_relative_path(entry["path"])
        if relative is None:
            _add_finding(
                findings,
                "UNSAFE_BUNDLE_PATH",
                "error",
                owner,
                "Record path is not a normalized safe relative POSIX path.",
            )
        else:
            register_unique(relative, owner, all_paths, "path")
            allowed_files.add(relative)
        register_unique(entry["label"], owner, all_labels, "label")

    for index, entry in enumerate(artifact_entries):
        owner = f"artifacts/{index}"
        if entry["artifact_index"] != index:
            _add_finding(
                findings,
                "ARTIFACT_INDEX_MISMATCH",
                "error",
                owner,
                "artifact_index must equal the artifact's manifest array index.",
            )
        if entry["path"] is not None:
            relative = _safe_relative_path(entry["path"])
            if relative is None:
                _add_finding(
                    findings,
                    "UNSAFE_BUNDLE_PATH",
                    "error",
                    owner,
                    "Artifact path is not a normalized safe relative POSIX path.",
                )
            else:
                register_unique(relative, owner, all_paths, "path")
                allowed_files.add(relative)
        register_unique(entry["label"], owner, all_labels, "label")

    if report_relative is not None and report_relative in all_paths:
        _add_finding(
            findings,
            "BUNDLE_PATH_COLLISION",
            "error",
            "report-output",
            "Report output must not overwrite a listed record or artifact.",
        )
    _inventory_findings(root, allowed_files, findings)

    records = [LoadedRecord(index, entry) for index, entry in enumerate(record_entries)]
    for record in records:
        entry = record.entry
        location = f"record:{entry['label']}"
        relative = _safe_relative_path(entry["path"])
        if relative is None:
            _add_finding(
                findings,
                "RECORD_UNREADABLE",
                "error",
                location,
                "Record path failed containment checks.",
                record=record,
            )
            continue
        path = root / relative
        try:
            raw, _info = _read_regular_file(path, max_bytes=RECORD_MAX_BYTES)
        except BundleSetupError:
            _add_finding(
                findings,
                "RECORD_UNREADABLE",
                "error",
                location,
                "Record file is absent, unsafe, or unreadable.",
                record=record,
            )
            continue
        record.raw = raw
        record.actual_sha256 = _sha256(raw)
        if record.actual_sha256 != entry["sha256"]:
            _add_finding(
                findings,
                "RECORD_RAW_SHA256_MISMATCH",
                "error",
                location,
                "Manifest digest does not match exact raw record bytes.",
                record=record,
            )
        try:
            record.data = strict_json.loads_object(raw, entry["label"])
        except strict_json.StrictJSONError:
            _add_finding(
                findings,
                "RECORD_JSON_INVALID",
                "error",
                location,
                "Record is not strict UTF-8 object JSON.",
                record=record,
            )
            continue
        _privacy_findings(record.data, f"{location}:", findings, record=record)

        candidates = catalog.by_name.get(entry["contract_name"], ())
        matching = [item for item in candidates if item.version == entry["schema_version"]]
        if not matching:
            _add_finding(
                findings,
                "RECORD_CONTRACT_UNKNOWN",
                "error",
                location,
                "Manifest names an unknown local contract name/version.",
                record=record,
            )
            continue
        record.contract = matching[0]
        if not record.contract.is_record_ref_target:
            _add_finding(
                findings,
                "RECORD_NOT_CONTENT_ADDRESSED",
                "error",
                location,
                "Only content-addressed-record contracts may appear in records.",
                record=record,
            )
        schema_errors = _schema_error_locations(record.contract, record.data, catalog)
        if schema_errors:
            _add_finding(
                findings,
                "RECORD_SCHEMA_INVALID",
                "error",
                location,
                "Record failed schema validation at " + ", ".join(schema_errors[:8]) + ".",
                record=record,
            )
        id_field = record.contract.record_id_field
        actual_id = record.data.get(id_field) if id_field is not None else None
        if actual_id != entry["record_id"]:
            _add_finding(
                findings,
                "RECORD_ID_MISMATCH",
                "error",
                location,
                "Manifest record_id differs from the schema-declared identity field.",
                record=record,
            )
        interface_id = f"{record.contract.name}@{record.contract.version}"
        record.lifecycle = lifecycle_by_interface.get(interface_id, "unregistered")
        if record.lifecycle == "planned":
            _add_finding(
                findings,
                "INTERFACE_PLANNED_CONTRACT_ONLY",
                "warning",
                location,
                "Planned interfaces are schema-only and cannot authenticate evidence.",
                record=record,
            )
        elif record.lifecycle != "active":
            _add_finding(
                findings,
                "INTERFACE_UNREGISTERED_CONTRACT_ONLY",
                "warning",
                location,
                "Unregistered internal contracts are not routable evidence interfaces.",
                record=record,
            )

    artifacts = [
        LoadedArtifact(index, entry) for index, entry in enumerate(artifact_entries)
    ]
    for artifact in artifacts:
        entry = artifact.entry
        location = f"artifact:{entry['label']}"
        if entry["availability"] != "present":
            continue
        relative = _safe_relative_path(entry["path"])
        if relative is None:
            _add_finding(
                findings,
                "ARTIFACT_FILE_MISSING",
                "error",
                location,
                "Present artifact lacks a safe local path.",
                artifact=artifact,
            )
            continue
        try:
            (
                actual_sha,
                actual_bytes,
                restricted_marker,
                credential_marker,
            ) = _stream_artifact(root / relative)
        except BundleSetupError:
            _add_finding(
                findings,
                "ARTIFACT_FILE_MISSING",
                "error",
                location,
                "Present artifact is absent, unsafe, or unreadable.",
                artifact=artifact,
            )
            continue
        artifact.actual_sha256 = actual_sha
        artifact.actual_bytes = actual_bytes
        if actual_sha != entry["sha256"]:
            _add_finding(
                findings,
                "ARTIFACT_RAW_SHA256_MISMATCH",
                "error",
                location,
                "Artifact digest does not match exact raw file bytes.",
                artifact=artifact,
            )
        if actual_bytes != entry["bytes"]:
            _add_finding(
                findings,
                "ARTIFACT_BYTES_MISMATCH",
                "error",
                location,
                "Artifact size differs from the manifest byte count.",
                artifact=artifact,
            )
        portable_mode = manifest["bundle_mode"] == "portable-public"
        if portable_mode and entry["sensitivity"] != "public":
            _add_finding(
                findings,
                "PRIVATE_ARTIFACT_INCLUDED",
                "error",
                location,
                "Private or restricted artifact bytes cannot be included.",
                artifact=artifact,
            )
        if (
            portable_mode
            and entry["redistribution"] != "redistributable"
        ) or (
            not portable_mode
            and (
                entry["sensitivity"] == "restricted"
                or entry["redistribution"] in {"restricted", "unknown"}
            )
        ):
            _add_finding(
                findings,
                "RESTRICTED_ARTIFACT_INCLUDED",
                "error",
                location,
                "Non-redistributable artifact bytes cannot be included.",
                artifact=artifact,
            )
        if credential_marker:
            _add_finding(
                findings,
                "CREDENTIAL_MATERIAL_DISCLOSED",
                "error",
                location,
                "Potential credential bytes are forbidden in every bundle mode.",
                artifact=artifact,
            )
        if RESTRICTED_DFT_NAME.search(relative) or restricted_marker:
            _add_finding(
                findings,
                "RESTRICTED_DFT_PAYLOAD_INCLUDED",
                "error",
                location,
                "Restricted DFT data-file payload markers are forbidden.",
                artifact=artifact,
            )

    record_reference_results = _record_reference_results(records, findings, catalog)
    file_reference_results = _file_reference_results(records, artifacts, findings)

    human_decision_ids = sorted(
        record.entry["record_id"]
        for record in records
        if record.entry["contract_name"] == "decision-record"
        and record.data is not None
        and (
            record.data.get("decision_type") == "execution-authorization"
            or (
                record.data.get("decision_type") == "scientific-acceptance"
                and record.data.get("outcome") in {"accepted", "rejected"}
            )
        )
    )
    if human_decision_ids:
        for decision_id in human_decision_ids:
            _add_finding(
                findings,
                "EXTERNAL_HUMAN_TRUST_REQUIRED",
                "warning",
                f"decision:{decision_id}",
                "Human authenticity cannot be established without an external trust resolver.",
            )

    authority_snapshot = registry_snapshots["official_source_authorities"]

    external_source_ids = sorted(
        record.entry["record_id"]
        for record in records
        if _source_requires_external_trust(record, authority_snapshot)
    )
    if external_source_ids:
        for source_id in external_source_ids:
            _add_finding(
                findings,
                "EXTERNAL_SOURCE_TRUST_REQUIRED",
                "warning",
                f"official-source:{source_id}",
                "Authority, version, and content trust require a platform-injected resolver receipt.",
            )

    obligation_results: list[dict[str, Any]] = []
    manifest_obligations = _obligation_ids(manifest_contract.schema)
    for obligation_id in manifest_obligations:
        handler, status = _manifest_obligation_status(obligation_id, findings)
        obligation_results.append(
            {
                "source_contract_name": "bundle-manifest",
                "source_record_id": manifest["bundle_id"],
                "obligation_id": obligation_id,
                "handler_id": handler,
                "status": status,
                "finding_codes": [],
                "location": f"manifest-obligation:{obligation_id}",
                "message": "Evaluated by the strict bundle core.",
            }
        )
    if maintenance_mode:
        obligation_results.append(
            {
                "source_contract_name": "bundle-manifest",
                "source_record_id": manifest["bundle_id"],
                "obligation_id": "VALIDATOR_TRUST_ROOT_CANONICAL",
                "handler_id": None,
                "status": "blocked",
                "finding_codes": ["UNTRUSTED_VALIDATOR_TRUST_ROOT"],
                "location": "validator-trust-root",
                "message": "Noncanonical maintenance roots are never a positive assurance source.",
            }
        )
    for interface_id in inactive_core_interfaces:
        obligation_results.append(
            {
                "source_contract_name": "bundle-manifest",
                "source_record_id": manifest["bundle_id"],
                "obligation_id": "BUNDLE_CORE_INTERFACE_ACTIVE",
                "handler_id": None,
                "status": "blocked",
                "finding_codes": ["BUNDLE_CORE_INTERFACE_NOT_ACTIVE"],
                "location": f"validator-interface:{interface_id}",
                "message": "Bundle manifest/report assurance requires active core interfaces.",
            }
        )

    record_views: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in records:
        record_views.setdefault(
            item.identity,
            {
                "contract_name": item.entry["contract_name"],
                "schema_version": item.entry["schema_version"],
                "record_id": item.entry["record_id"],
                "index": item.index,
                "data": item.data or {},
                "raw_sha256": item.actual_sha256,
                "lifecycle": item.lifecycle,
                "integrity_verified_active": item.integrity_verified_active,
            },
        )
    artifact_views = {
        item.entry["label"]: {
            "label": item.entry["label"],
            "index": item.index,
            "metadata": {
                key: value for key, value in item.entry.items() if key != "path"
            },
            "raw_sha256": item.actual_sha256,
            "bytes": item.actual_bytes,
            "integrity_verified": (
                item.entry["availability"] == "present"
                and item.status == "pass"
                and item.actual_sha256 == item.entry["sha256"]
                and item.actual_bytes == item.entry["bytes"]
            ),
            # Reserved production seam.  Only fixed repository-owned bounded
            # parser adapters may populate this after exact raw-byte integrity
            # succeeds; bundle data and receipts cannot self-report observations.
            "parser_observations": (),
        }
        for item in artifacts
    }

    def core_check(codes: set[str] | frozenset[str]) -> dict[str, Any]:
        matched = [item for item in findings if item.code in codes]
        return {
            "status": (
                "fail"
                if any(item.severity == "error" for item in matched)
                else "blocked"
                if matched
                else "pass"
            ),
            "finding_codes": sorted({item.code for item in matched}),
        }

    core_checks = {
        "record-reference-dag": core_check(REFERENCE_CODES),
        "record-reference-integrity": core_check(REFERENCE_CODES),
        "artifact-integrity": core_check(ARTIFACT_CODES),
        "privacy-boundary": core_check(PRIVACY_CODES),
    }
    for record in records:
        if record.contract is None:
            continue
        interface_id = f"{record.contract.name}@{record.contract.version}"
        interface_specification = (
            interface_specs.get(interface_id, {})
            if isinstance(interface_specs, dict)
            else {}
        )
        classification = (
            interface_specification.get("classification", {})
            if isinstance(interface_specification, dict)
            else {}
        )
        if (
            isinstance(classification, dict)
            and classification.get("routing_scope") == "governance-only"
        ):
            for obligation_id in _contract_obligation_ids(record.contract):
                semantic = {
                    "obligation_id": str(obligation_id),
                    "handler_id": None,
                    "status": "blocked",
                    "finding_codes": ["GOVERNANCE_VALIDATOR_REQUIRED"],
                    "location": f"governance:{record.contract.name}",
                    "message": "Governance-only obligations require their repository-owned commit-aware validator and are not routed to a domain evaluator.",
                }
                if record.status == "pass":
                    record.status = "blocked"
                _add_finding(
                    findings,
                    "GOVERNANCE_VALIDATOR_REQUIRED",
                    "warning",
                    semantic["location"],
                    semantic["message"],
                )
                obligation_results.append(
                    {
                        "source_contract_name": record.entry["contract_name"],
                        "source_record_id": record.entry["record_id"],
                        **semantic,
                    }
                )
            continue
        context = {
            "current_record": record_views[record.identity],
            "current_record_index": record.index,
            "records_by_identity": record_views,
            "artifacts_by_label": artifact_views,
            "core_checks": core_checks,
            "registry_snapshots": registry_snapshots,
        }
        semantic_results = bundle_semantics.evaluate_advertised_obligations(
            _contract_obligation_ids(record.contract),
            context,
            evaluator=bundle_semantics.builtin_evaluator(record.contract.name),
        )
        for semantic in semantic_results:
            if record.lifecycle != "active":
                semantic = dict(semantic)
                semantic["status"] = "blocked"
                semantic["finding_codes"] = sorted(
                    set(semantic["finding_codes"])
                    | {"OBLIGATION_INTERFACE_NOT_ACTIVE"}
                )
                semantic["message"] = (
                    "Interface lifecycle is not active; semantic assurance is contract-only."
                )
            status = semantic["status"]
            if status == "blocked":
                if record.status == "pass":
                    record.status = "blocked"
                code = (
                    semantic["finding_codes"][0]
                    if semantic["finding_codes"]
                    else "OBLIGATION_HANDLER_UNAVAILABLE"
                )
                _add_finding(
                    findings,
                    code,
                    "warning",
                    semantic["location"],
                    semantic["message"],
                )
            elif status == "fail":
                code = (
                    semantic["finding_codes"][0]
                    if semantic["finding_codes"]
                    else "SEMANTIC_OBLIGATION_FAILED"
                )
                _add_finding(
                    findings,
                    code,
                    "error",
                    semantic["location"],
                    semantic["message"],
                    record=record,
                )
            obligation_results.append(
                {
                    "source_contract_name": record.entry["contract_name"],
                    "source_record_id": record.entry["record_id"],
                    "obligation_id": semantic["obligation_id"],
                    "handler_id": semantic["handler_id"],
                    "status": status,
                    "finding_codes": semantic["finding_codes"],
                    "location": semantic["location"],
                    "message": semantic["message"],
                }
            )

    # The accounting obligation is evaluated only after every schema obligation
    # has a corresponding report row.
    for result in obligation_results:
        if result["obligation_id"] == "BUNDLE_ALL_CONTRACT_OBLIGATIONS_ACCOUNTED":
            result["status"] = "pass"

    if human_decision_ids:
        obligation_results.append(
            {
                "source_contract_name": "bundle-manifest",
                "source_record_id": manifest["bundle_id"],
                "obligation_id": "EXTERNAL_HUMAN_TRUST_AUTHENTICITY",
                "handler_id": None,
                "status": "blocked",
                "finding_codes": ["EXTERNAL_HUMAN_TRUST_REQUIRED"],
                "location": "external-trust:human-authenticity",
                "message": "A platform trust resolver is required and was not available.",
            }
        )
    if external_source_ids:
        obligation_results.append(
            {
                "source_contract_name": "bundle-manifest",
                "source_record_id": manifest["bundle_id"],
                "obligation_id": "EXTERNAL_SOURCE_AUTHORITY_VERSION_CONTENT_TRUST",
                "handler_id": None,
                "status": "blocked",
                "finding_codes": ["EXTERNAL_SOURCE_TRUST_REQUIRED"],
                "location": "external-trust:official-source",
                "message": "A platform authority/content resolver is required and was not available.",
            }
        )

    failed_checks = (
        sum(record.status == "fail" for record in records)
        + sum(artifact.status == "fail" for artifact in artifacts)
        + sum(item["status"] == "fail" for item in record_reference_results)
        + sum(item["status"] == "fail" for item in file_reference_results)
        + sum(item["status"] == "fail" for item in obligation_results)
    )
    blocked_checks = (
        sum(item.status == "blocked" for item in records)
        + sum(item.status == "blocked" for item in artifacts)
        + sum(item["status"] == "blocked" for item in record_reference_results)
        + sum(item["status"] == "blocked" for item in file_reference_results)
        + sum(item["status"] == "blocked" for item in obligation_results)
    )
    error_count = sum(finding.severity == "error" for finding in findings)
    if failed_checks and not error_count:
        _add_finding(
            findings,
            "FAILED_CHECK_WITHOUT_ERROR_FINDING",
            "error",
            "validator-result-reduction",
            "A failed result lacked its required error finding; the reducer failed closed.",
        )
        error_count = 1
    if error_count or failed_checks:
        overall_status = "fail"
        exit_code = 2
    elif blocked_checks or human_decision_ids or external_source_ids:
        overall_status = "blocked"
        exit_code = 3
    else:
        overall_status = "pass"
        exit_code = 0

    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    validation_run_id = f"validation-run-{uuid.uuid4().hex}"
    trust_root = _catalog_trust_root(catalog, registry_raw)
    validator_execution = _validator_execution(validation_run_id)
    identity_parts = [
        manifest_sha256,
        trust_root["catalog_digest"],
        *(f"{item['label']}:{item['sha256']}" for item in trust_root["registry_entries"]),
        *(
            f"{item['label']}:{item['sha256']}"
            for item in validator_execution["components"]
        ),
        generated,
        validation_run_id,
    ]
    report_identity_digest = _sha256("\x00".join(identity_parts).encode("utf-8"))
    report = {
        "contract_name": "bundle-validation-report",
        "schema_version": "1.0",
        "report_id": f"bundle-report-{report_identity_digest}",
        "validation_run_id": validation_run_id,
        "generated_utc": generated,
        "bundle_manifest": {
            "contract_name": "bundle-manifest",
            "schema_version": manifest["schema_version"],
            "bundle_id": manifest["bundle_id"],
            "label": manifest_path.name,
            "sha256": manifest_sha256,
        },
        "bundle_mode": manifest["bundle_mode"],
        "distribution_boundary": (
            "portable-public"
            if manifest["bundle_mode"] == "portable-public"
            else "local-only-no-external-publication"
        ),
        "trust_root": trust_root,
        "validator_execution": validator_execution,
        "human_trust": {
            "status": "requires-external-trust" if human_decision_ids else "not-required",
            "human_authenticity": "not-established" if human_decision_ids else "not-applicable",
            "trust_resolver_id": None,
            "required_decision_ids": human_decision_ids,
            "limitations": [
                "P0 does not accept an agent-selected trust file or digest as proof of human identity."
            ],
        },
        "external_source_trust": {
            "status": "requires-external-trust" if external_source_ids else "not-required",
            "trust_resolver_id": None,
            "required_source_record_ids": external_source_ids,
            "resolver_receipt_labels": [],
            "limitations": [
                "P0 accepts no bundle field or CLI-selected module as an external authority resolver; only a future platform-injected adapter may supply a receipt."
            ],
        },
        "status": overall_status,
        "assurance": (
            "integrity-verified-no-positive-claim"
            if overall_status == "pass"
            else "contract-only-no-positive-claim"
            if overall_status == "blocked"
            else "invalid"
        ),
        "summary": {
            "record_count": len(records),
            "artifact_count": len(artifacts),
            "record_reference_count": len(record_reference_results),
            "file_reference_count": len(file_reference_results),
            "obligation_count": len(obligation_results),
            "failed_checks": failed_checks,
            "blocked_checks": blocked_checks,
            "error_findings": error_count,
            "warning_findings": sum(
                finding.severity == "warning" for finding in findings
            ),
            "info_findings": sum(finding.severity == "info" for finding in findings),
        },
        "record_results": [
            {
                "record_index": record.index,
                "label": record.entry["label"],
                "contract_name": record.entry["contract_name"],
                "schema_version": record.entry["schema_version"],
                "record_id": record.entry["record_id"],
                "sha256": record.entry["sha256"],
                "status": record.status,
                "finding_codes": sorted(record.finding_codes),
            }
            for record in records
        ],
        "artifact_results": [
            {
                "artifact_index": artifact.index,
                "label": artifact.entry["label"],
                "availability": artifact.entry["availability"],
                "status": artifact.status,
                "finding_codes": sorted(artifact.finding_codes),
            }
            for artifact in artifacts
        ],
        "record_reference_results": record_reference_results,
        "file_reference_results": file_reference_results,
        "obligation_results": obligation_results,
        "findings": [finding.as_dict() for finding in findings],
        "producer": {
            "skill_id": "vibe-dft-skills",
            "skill_version": "1.0",
            "tool_id": "bundle-validator",
            "tool_version": "1.0",
            "generated_utc": generated,
        },
        "limitations": [
            "Validation is bounded to the catalog and interface-registry digests in trust_root.",
            "A schema-valid report is not itself a validator trust root; consumers must compare every validator component and registry digest with a platform-controlled trusted release.",
            "Unhandled x-vibe obligations fail closed as blocked; schema validity alone is not scientific acceptance.",
        ],
    }
    report_schema_errors = _schema_error_locations(report_contract, report, catalog)
    if report_schema_errors:
        raise BundleSetupError(
            "internal bundle report failed its schema at: "
            + ", ".join(report_schema_errors)
        )
    return report, exit_code


def _write_report(path: Path, report: dict[str, Any], *, force: bool) -> None:
    if path.exists() and not force:
        raise BundleSetupError(
            f"refusing to overwrite existing report without --force: {path}"
        )
    if path.is_symlink():
        raise BundleSetupError(f"refusing symlink report output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    raw = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="strict bundle-manifest JSON file")
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=repo_root() / "contracts",
        help="maintenance/test override for the canonical JSON Schema catalog",
    )
    parser.add_argument(
        "--interface-registry",
        type=Path,
        default=repo_root() / "registry" / "interface-registry.yaml",
        help="maintenance/test override for the canonical interface lifecycle registry",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="output path (default: bundle-validation-report.json beside manifest)",
    )
    parser.add_argument("--force", action="store_true", help="replace an existing report")
    parser.add_argument(
        "--maintenance",
        action="store_true",
        help="allow noncanonical trust-root overrides; successful checks still exit 3",
    )
    parser.add_argument(
        "--allow-local-validation",
        action="store_true",
        help="explicitly authorize local-only validation of private/runtime-only artifacts",
    )
    args = parser.parse_args(argv)
    report_path = args.report or args.manifest.parent / "bundle-validation-report.json"
    if report_path.exists() and not args.force:
        print(
            f"ERROR: refusing to overwrite existing report without --force: {report_path.name}",
            file=sys.stderr,
        )
        return 2
    canonical_contracts = (repo_root() / "contracts").resolve()
    canonical_registry = (
        repo_root() / "registry" / "interface-registry.yaml"
    ).resolve()
    noncanonical_override = (
        args.contracts_dir.resolve() != canonical_contracts
        or args.interface_registry.resolve() != canonical_registry
    )
    if noncanonical_override and not args.maintenance:
        print(
            "ERROR: UNTRUSTED_VALIDATOR_TRUST_ROOT: noncanonical overrides require "
            "--maintenance and can never produce positive assurance",
            file=sys.stderr,
        )
        return 2
    try:
        report, exit_code = validate_bundle(
            args.manifest,
            contracts_dir=args.contracts_dir,
            interface_registry_path=args.interface_registry,
            report_path=report_path,
            maintenance_mode=args.maintenance,
            allow_local_validation=args.allow_local_validation,
        )
        _write_report(report_path, report, force=args.force)
    except (
        BundleSetupError,
        strict_json.StrictJSONError,
        validate_contract.CatalogError,
        validate_contract.ContractSelectionError,
        OSError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            f"ERROR: INTERNAL_VALIDATOR_ERROR: {exc.__class__.__name__}",
            file=sys.stderr,
        )
        return 2
    print(
        f"{report['status'].upper()}: {args.manifest.name} -> {report_path.name} "
        f"(assurance={report['assurance']})"
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
