#!/usr/bin/env python3
"""Fail-closed OVITO candidate: parse, plan, probe, or explicitly execute."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import secrets
import shlex
import stat
import sys
import tempfile
from typing import Any


EXIT_OK = 0
EXIT_BLOCKED = 2
EXIT_UNAVAILABLE = 3
EXIT_INTERNAL = 4
MAX_TRAJECTORY_BYTES = 50 * 1024 * 1024
MAX_JSON_BYTES = 5 * 1024 * 1024
TOOL_VERSION = "0.1.0-candidate"
EXPECTED_OVITO_VERSION = "3.15.5"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
ELEMENT = re.compile(r"^[A-Z][a-z]?$|^X$")
PROPERTY_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
OPERATION_CATALOG = {
    "compute-frame-metadata": {
        "minimum_profile": "ovito-basic",
        "candidate_execution": "implemented",
        "evidence_role": "technical-metadata",
        "allowed_parameters": set(),
        "required_parameters": set(),
        "output_kinds": {"json-data"},
    },
    "coordination-analysis": {
        "minimum_profile": "ovito-basic",
        "candidate_execution": "plan-only",
        "evidence_role": "numerical-analysis",
        "allowed_parameters": {"cutoff_source_units", "number_of_bins"},
        "required_parameters": {"cutoff_source_units"},
        "output_kinds": {"json-data", "data-table"},
    },
    "common-neighbor-analysis": {
        "minimum_profile": "ovito-basic",
        "candidate_execution": "plan-only",
        "evidence_role": "numerical-analysis",
        "allowed_parameters": {"mode"},
        "required_parameters": {"mode"},
        "output_kinds": {"json-data", "data-table"},
    },
    "atomic-strain": {
        "minimum_profile": "ovito-pro",
        "candidate_execution": "plan-only",
        "evidence_role": "numerical-analysis",
        "allowed_parameters": {"cutoff_source_units", "reference_frame"},
        "required_parameters": {"cutoff_source_units", "reference_frame"},
        "output_kinds": {"json-data", "data-table"},
    },
    "dislocation-analysis": {
        "minimum_profile": "ovito-pro",
        "candidate_execution": "plan-only",
        "evidence_role": "numerical-analysis",
        "allowed_parameters": {"crystal_structure"},
        "required_parameters": {"crystal_structure"},
        "output_kinds": {"json-data", "data-table"},
    },
    "render-image": {
        "minimum_profile": "ovito-pro",
        "candidate_execution": "plan-only",
        "evidence_role": "visual-only",
        "allowed_parameters": {"width_px", "height_px", "background", "camera"},
        "required_parameters": {"width_px", "height_px", "background", "camera"},
        "output_kinds": {"image"},
    },
    "export-table": {
        "minimum_profile": "ovito-basic",
        "candidate_execution": "plan-only",
        "evidence_role": "technical-export",
        "allowed_parameters": {"columns", "format"},
        "required_parameters": {"columns", "format"},
        "output_kinds": {"data-table"},
    },
}


class GateError(Exception):
    def __init__(self, finding_id: str, message: str, exit_code: int = EXIT_BLOCKED):
        super().__init__(message)
        self.finding_id = finding_id
        self.message = message
        self.exit_code = exit_code


def candidate_lifecycle(future_gate_ceiling: str) -> dict[str, Any]:
    return {
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": future_gate_ceiling,
        "promotion_authorized": False,
        "execution_authorized": False,
    }


def error_envelope(
    finding_id: str,
    message: str,
    *,
    status: str = "blocked",
) -> dict[str, Any]:
    """Return one schema-shaped, lifecycle-capped candidate error record."""

    return {
        "contract_name": "ovito-candidate-error",
        "schema_version": "0.1",
        "status": status,
        "finding_id": finding_id,
        "message": message,
        **candidate_lifecycle("input_gates_only"),
        "provenance": {
            "tool": "ovito_analysis.py",
            "tool_version": TOOL_VERSION,
        },
    }


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value!r}")


def _object_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def inventory_evidence_payload(value: dict[str, Any]) -> dict[str, Any]:
    """Return parser-derived inventory evidence without the path-label presentation field."""

    payload = dict(value)
    source = dict(payload["source"])
    source.pop("label", None)
    payload["source"] = source
    return payload


def privacy_safe_label(path: Path, sha256: str) -> str:
    suffix = path.suffix.lower()
    if not re.fullmatch(r"\.[a-z0-9]{1,10}", suffix):
        suffix = ""
    return f"source-{sha256[:12]}{suffix}"


def _stat_identity(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        stat.S_IFMT(info.st_mode),
        info.st_size,
        info.st_mtime_ns,
        info.st_nlink,
    )


def _directory_identity(info: os.stat_result) -> tuple[int, int, int]:
    return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))


def _regular_bytes(path_text: str, maximum: int, kind: str) -> tuple[bytes, dict[str, Any]]:
    path = Path(path_text)
    try:
        info = path.lstat()
    except OSError as exc:
        raise GateError(f"{kind}_UNREADABLE", f"{kind.lower()} is not readable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise GateError(f"{kind}_NOT_REGULAR", "symlinks and non-regular inputs are refused")
    if info.st_size > maximum:
        raise GateError(f"{kind}_TOO_LARGE", f"{kind.lower()} exceeds {maximum} bytes")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise GateError(f"{kind}_UNREADABLE", f"{kind.lower()} could not be opened safely") from exc
    try:
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode) or _stat_identity(opened) != _stat_identity(info):
                raise GateError(f"{kind}_CHANGED_DURING_READ", f"{kind.lower()} identity changed before read")
            if opened.st_size > maximum:
                raise GateError(f"{kind}_TOO_LARGE", f"{kind.lower()} exceeds {maximum} bytes")
            raw = handle.read(maximum + 1)
            finished = os.fstat(handle.fileno())
    except GateError:
        raise
    except OSError as exc:
        raise GateError(f"{kind}_UNREADABLE", f"{kind.lower()} could not be read safely") from exc
    if len(raw) > maximum:
        raise GateError(f"{kind}_TOO_LARGE", f"{kind.lower()} exceeds {maximum} bytes")
    try:
        final_path = path.lstat()
    except OSError as exc:
        raise GateError(f"{kind}_CHANGED_DURING_READ", f"{kind.lower()} path disappeared during read") from exc
    if (
        _stat_identity(finished) != _stat_identity(opened)
        or _stat_identity(final_path) != _stat_identity(opened)
        or len(raw) != finished.st_size
        or stat.S_ISLNK(final_path.st_mode)
    ):
        raise GateError(f"{kind}_CHANGED_DURING_READ", f"{kind.lower()} path or link identity changed during read")
    sha256 = hashlib.sha256(raw).hexdigest()
    return raw, {"label": privacy_safe_label(path, sha256), "bytes": len(raw), "sha256": sha256}


def load_json(path_text: str, expected_kind: str) -> tuple[dict[str, Any], dict[str, Any]]:
    raw, source = _regular_bytes(path_text, MAX_JSON_BYTES, expected_kind)
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise GateError("JSON_INVALID", "input must be strict, duplicate-free UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise GateError("JSON_ROOT_INVALID", "JSON root must be an object")
    return value, source


def write_json(value: dict[str, Any], path_text: str | None) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
    if path_text is None:
        sys.stdout.write(rendered)
        return
    preflight_output(path_text)
    path = Path(path_text)
    parent = path.parent
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        parent_info = parent.lstat()
        parent_descriptor = os.open(parent, flags)
    except OSError as exc:
        raise GateError("OUTPUT_PARENT_INVALID", "output parent could not be opened safely") from exc
    temporary_name = f".{path.name}.candidate-{secrets.token_hex(8)}.tmp"
    temporary_created = False
    try:
        opened_parent = os.fstat(parent_descriptor)
        if not stat.S_ISDIR(opened_parent.st_mode) or _directory_identity(opened_parent) != _directory_identity(parent_info):
            raise GateError("OUTPUT_PARENT_CHANGED", "output parent identity changed")
        try:
            os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise GateError("OUTPUT_EXISTS", "output already exists or aliases evidence; overwrite is refused")
        create_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            create_flags |= os.O_NOFOLLOW
        temporary_descriptor = os.open(
            temporary_name,
            create_flags,
            0o600,
            dir_fd=parent_descriptor,
        )
        temporary_created = True
        with os.fdopen(temporary_descriptor, "w", encoding="utf-8", newline="\n", closefd=True) as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(
                temporary_name,
                path.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise GateError("OUTPUT_EXISTS", "output appeared concurrently; overwrite is refused") from exc
        os.unlink(temporary_name, dir_fd=parent_descriptor)
        temporary_created = False
        os.fsync(parent_descriptor)
        final_parent = parent.lstat()
        if _directory_identity(final_parent) != _directory_identity(opened_parent):
            raise GateError("OUTPUT_PARENT_CHANGED", "output parent identity changed during publish")
    except GateError:
        raise
    except OSError as exc:
        raise GateError("OUTPUT_WRITE_FAILED", "output could not be published atomically") from exc
    finally:
        if temporary_created:
            try:
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            except OSError:
                pass
        os.close(parent_descriptor)


def preflight_output(path_text: str) -> None:
    path = Path(path_text)
    if not path.name or path.name in {".", ".."}:
        raise GateError("OUTPUT_PATH_INVALID", "output must name a new regular file")
    if not all(function in os.supports_dir_fd for function in (os.open, os.stat, os.link, os.unlink)):
        raise GateError(
            "ATOMIC_OUTPUT_UNAVAILABLE",
            "this platform lacks the directory-descriptor operations required for safe atomic publish",
        )
    if path.exists() or path.is_symlink():
        raise GateError("OUTPUT_EXISTS", "output already exists; overwrite is refused")
    try:
        parent_info = path.parent.lstat()
    except OSError as exc:
        raise GateError("OUTPUT_PARENT_INVALID", "output parent must already exist") from exc
    if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
        raise GateError("OUTPUT_PARENT_INVALID", "symlinked or non-directory output parents are refused")


def _keys(value: dict[str, Any], required: set[str], context: str) -> None:
    actual = set(value)
    if actual != required:
        raise GateError(
            "SCHEMA_KEYS_INVALID",
            f"{context} keys mismatch; missing={sorted(required - actual)}, extra={sorted(actual - required)}",
        )


def _finite(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GateError("NUMBER_INVALID", f"{context} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise GateError("NUMBER_INVALID", f"{context} must be finite")
    return result


def _int(value: str, finding_id: str, message: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise GateError(finding_id, message) from exc
    return result


def determinant(matrix: list[list[float]]) -> float:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def parse_comment(comment: str) -> dict[str, Any]:
    attributes: dict[str, str] = {}
    try:
        tokens = shlex.split(comment, posix=True)
    except ValueError as exc:
        raise GateError("EXTXYZ_COMMENT_INVALID", "extended XYZ comment has invalid quoting") from exc
    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            if key in attributes:
                raise GateError("EXTXYZ_ATTRIBUTE_DUPLICATE", f"duplicate extended XYZ attribute {key!r}")
            attributes[key] = value

    cell = None
    if "Lattice" in attributes:
        fields = attributes["Lattice"].split()
        if len(fields) != 9:
            raise GateError("EXTXYZ_LATTICE_INVALID", "Lattice must contain nine finite numbers")
        try:
            values = [float(item) for item in fields]
        except ValueError as exc:
            raise GateError("EXTXYZ_LATTICE_INVALID", "Lattice must contain nine finite numbers") from exc
        if any(not math.isfinite(item) for item in values):
            raise GateError("EXTXYZ_LATTICE_INVALID", "Lattice values must be finite")
        cell = [values[0:3], values[3:6], values[6:9]]
        if abs(determinant(cell)) <= 1.0e-10:
            raise GateError("EXTXYZ_LATTICE_SINGULAR", "Lattice is singular or numerically degenerate")

    pbc = None
    if "pbc" in attributes:
        fields = attributes["pbc"].split()
        if len(fields) != 3:
            raise GateError("EXTXYZ_PBC_INVALID", "pbc must contain three booleans")
        parsed = []
        for item in fields:
            lowered = item.lower()
            if lowered in {"t", "true", "1"}:
                parsed.append(True)
            elif lowered in {"f", "false", "0"}:
                parsed.append(False)
            else:
                raise GateError("EXTXYZ_PBC_INVALID", "pbc values must be true or false")
        pbc = parsed
        if any(pbc) and cell is None:
            raise GateError("PBC_CELL_MISMATCH", "periodic extended XYZ frame requires Lattice")

    descriptors = None
    if "Properties" in attributes:
        parts = attributes["Properties"].split(":")
        if len(parts) % 3 != 0 or not parts:
            raise GateError("EXTXYZ_PROPERTIES_INVALID", "Properties must use name:type:count triplets")
        descriptors = []
        offset = 0
        property_names: set[str] = set()
        for index in range(0, len(parts), 3):
            name, value_type, count_text = parts[index : index + 3]
            count = _int(count_text, "EXTXYZ_PROPERTIES_INVALID", "property count must be an integer")
            if not PROPERTY_NAME.fullmatch(name) or value_type not in {"R", "I", "S", "L"} or not 1 <= count <= 64:
                raise GateError("EXTXYZ_PROPERTIES_INVALID", "property descriptor is invalid")
            if name in property_names:
                raise GateError("EXTXYZ_PROPERTY_DUPLICATE", f"property {name!r} is declared more than once")
            property_names.add(name)
            descriptors.append({"name": name, "type": value_type, "count": count, "offset": offset})
            offset += count
            if offset > 256:
                raise GateError("EXTXYZ_PROPERTIES_INVALID", "total declared property width exceeds 256 columns")
        species_fields = [item for item in descriptors if item["name"] in {"species", "element"}]
        position_fields = [item for item in descriptors if item["name"] in {"pos", "position"}]
        if len(species_fields) != 1 or species_fields[0]["count"] != 1:
            raise GateError("EXTXYZ_SPECIES_PROPERTY_MISSING", "Properties needs one scalar species field")
        if species_fields[0]["type"] != "S":
            raise GateError("EXTXYZ_SPECIES_PROPERTY_MISSING", "species property must have type S")
        if len(position_fields) != 1 or position_fields[0]["count"] != 3:
            raise GateError("EXTXYZ_POSITION_PROPERTY_MISSING", "Properties needs one three-component position field")
        if position_fields[0]["type"] != "R":
            raise GateError("EXTXYZ_POSITION_PROPERTY_MISSING", "position property must have type R")
    return {
        "attributes": sorted(attributes),
        "is_extxyz": any(key in attributes for key in ("Lattice", "Properties", "pbc")),
        "cell_vectors": cell,
        "pbc": pbc,
        "property_descriptors": descriptors,
    }


def parse_atom_line(line: str, descriptor_info: list[dict[str, Any]] | None, frame: int, atom: int) -> dict[str, Any]:
    fields = line.split()
    if descriptor_info is None:
        if len(fields) != 4:
            raise GateError(
                "XYZ_ATOM_LINE_INVALID",
                f"frame {frame} atom {atom} must contain exactly symbol and three coordinates; use extxyz Properties for extra columns",
            )
        symbol = fields[0]
        coordinate_fields = fields[1:4]
        properties = ["species", "pos"]
        property_schema = [
            {"name": "species", "type": "S", "count": 1},
            {"name": "pos", "type": "R", "count": 3},
        ]
        canonical_values: dict[str, list[Any]] = {
            "species": [symbol],
            "pos": [],
        }
    else:
        total = sum(item["count"] for item in descriptor_info)
        if len(fields) != total:
            raise GateError("EXTXYZ_COLUMN_COUNT_MISMATCH", f"frame {frame} atom {atom} column count mismatches Properties")
        species = next(item for item in descriptor_info if item["name"] in {"species", "element"})
        position = next(item for item in descriptor_info if item["name"] in {"pos", "position"})
        symbol = fields[species["offset"]]
        coordinate_fields = fields[position["offset"] : position["offset"] + 3]
        properties = [item["name"] for item in descriptor_info]
        property_schema = [
            {"name": item["name"], "type": item["type"], "count": item["count"]}
            for item in descriptor_info
        ]
        canonical_values = {}
        for descriptor in descriptor_info:
            values = fields[descriptor["offset"] : descriptor["offset"] + descriptor["count"]]
            try:
                if descriptor["type"] == "R":
                    parsed_values: list[Any] = [float(item) for item in values]
                    if any(not math.isfinite(item) for item in parsed_values):
                        raise ValueError("non-finite real")
                elif descriptor["type"] == "I":
                    parsed_values = [int(item) for item in values]
                elif descriptor["type"] == "L":
                    parsed_values = []
                    for item in values:
                        lowered = item.lower()
                        if lowered in {"t", "true", "1"}:
                            parsed_values.append(True)
                        elif lowered in {"f", "false", "0"}:
                            parsed_values.append(False)
                        else:
                            raise ValueError("invalid logical")
                else:
                    parsed_values = values
            except ValueError as exc:
                raise GateError(
                    "EXTXYZ_PROPERTY_VALUE_INVALID",
                    f"frame {frame} atom {atom} property {descriptor['name']!r} violates its declared type",
                ) from exc
            canonical_values[descriptor["name"]] = parsed_values
    if not ELEMENT.fullmatch(symbol):
        raise GateError("XYZ_SPECIES_INVALID", f"frame {frame} atom {atom} has unsupported species label")
    try:
        coordinates = [float(item) for item in coordinate_fields]
    except ValueError as exc:
        raise GateError("XYZ_COORDINATE_INVALID", f"frame {frame} atom {atom} coordinates must be numeric") from exc
    if any(not math.isfinite(item) for item in coordinates):
        raise GateError("XYZ_COORDINATE_INVALID", f"frame {frame} atom {atom} coordinates must be finite")
    canonical_values["pos"] = coordinates
    return {
        "species": symbol,
        "position_values": coordinates,
        "properties": properties,
        "property_schema": property_schema,
        "canonical_values": canonical_values,
    }


def inventory_xyz(path_text: str) -> dict[str, Any]:
    raw, source = _regular_bytes(path_text, MAX_TRAJECTORY_BYTES, "TRAJECTORY")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise GateError("TRAJECTORY_NOT_UTF8", "candidate XYZ parser requires UTF-8 text") from exc
    lines = text.splitlines()
    cursor = 0
    frames: list[dict[str, Any]] = []
    all_properties: set[str] = set()
    while cursor < len(lines):
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines):
            break
        count = _int(lines[cursor].strip(), "XYZ_ATOM_COUNT_INVALID", "frame atom count must be an integer")
        if count < 1:
            raise GateError("XYZ_ATOM_COUNT_INVALID", "frame atom count must be positive")
        cursor += 1
        if cursor >= len(lines):
            raise GateError("XYZ_FRAME_TRUNCATED", "frame is missing its comment line")
        comment = lines[cursor]
        cursor += 1
        comment_info = parse_comment(comment)
        atoms = []
        for atom_index in range(count):
            if cursor >= len(lines):
                raise GateError("XYZ_FRAME_TRUNCATED", "frame ends before its declared atom count")
            atom = parse_atom_line(lines[cursor], comment_info["property_descriptors"], len(frames), atom_index)
            atoms.append(atom)
            all_properties.update(atom["properties"])
            cursor += 1
        frame_payload = {
            "species_order": [atom["species"] for atom in atoms],
            "position_values": [atom["position_values"] for atom in atoms],
            "cell_vectors": comment_info["cell_vectors"],
            "pbc": comment_info["pbc"],
            "property_schema": atoms[0]["property_schema"],
            "property_values": [atom["canonical_values"] for atom in atoms],
        }
        particle_identifiers = None
        if all("id" in atom["canonical_values"] for atom in atoms):
            raw_identifiers = [atom["canonical_values"]["id"] for atom in atoms]
            if any(len(item) != 1 or isinstance(item[0], bool) or not isinstance(item[0], int) for item in raw_identifiers):
                raise GateError(
                    "EXTXYZ_PARTICLE_IDENTIFIER_INVALID",
                    "id must be a scalar integer property when used as a particle identifier",
                )
            particle_identifiers = [item[0] for item in raw_identifiers]
            if len(set(particle_identifiers)) != len(particle_identifiers):
                raise GateError(
                    "EXTXYZ_PARTICLE_IDENTIFIER_INVALID",
                    "particle identifiers must be unique within every frame",
                )
        frames.append(
            {
                "frame_index": len(frames),
                "atom_count": count,
                "species_order": frame_payload["species_order"],
                "particle_identifiers": particle_identifiers,
                "cell_present": comment_info["cell_vectors"] is not None,
                "cell_vectors": comment_info["cell_vectors"],
                "cell_sha256": None if comment_info["cell_vectors"] is None else digest(comment_info["cell_vectors"]),
                "cell_determinant_source_units3": (
                    None if comment_info["cell_vectors"] is None else determinant(comment_info["cell_vectors"])
                ),
                "pbc": comment_info["pbc"],
                "comment_attributes": comment_info["attributes"],
                "extended_xyz": comment_info["is_extxyz"],
                "properties": sorted(set(atom_property for atom in atoms for atom_property in atom["properties"])),
                "property_schema": atoms[0]["property_schema"],
                "frame_sha256": digest(frame_payload),
            }
        )
    if not frames:
        raise GateError("XYZ_NO_FRAMES", "trajectory contains no XYZ frames")
    atom_counts = [frame["atom_count"] for frame in frames]
    species_orders = [frame["species_order"] for frame in frames]
    identifier_orders = [frame["particle_identifiers"] for frame in frames]
    pbc_values = [frame["pbc"] for frame in frames]
    cell_values = [frame["cell_present"] for frame in frames]
    cell_hashes = [frame["cell_sha256"] for frame in frames]
    property_schemas = [frame["property_schema"] for frame in frames]
    findings: list[dict[str, str]] = []
    atom_count_constant = len(set(atom_counts)) == 1
    species_order_constant = all(item == species_orders[0] for item in species_orders)
    identifiers_present_all = all(item is not None for item in identifier_orders)
    identifiers_absent_all = all(item is None for item in identifier_orders)
    identifier_sets_constant = identifiers_present_all and all(
        set(item) == set(identifier_orders[0]) for item in identifier_orders
    )
    stable_particle_identifiers = identifiers_present_all and identifier_sets_constant
    property_schema_constant = all(item == property_schemas[0] for item in property_schemas)
    if not atom_count_constant:
        findings.append(
            {
                "finding_id": "TRAJECTORY_ATOM_COUNT_CHANGED",
                "severity": "blocker",
                "message": "frame atom counts differ; topology mapping is unresolved",
            }
        )
    if not species_order_constant and not stable_particle_identifiers:
        findings.append(
            {
                "finding_id": "TRAJECTORY_SPECIES_ORDER_CHANGED",
                "severity": "blocker",
                "message": "species order differs between frames; ordinal atom mapping is unsafe",
            }
        )
    if stable_particle_identifiers:
        baseline_species_by_id = dict(zip(identifier_orders[0], species_orders[0], strict=True))
        if any(
            dict(zip(identifier_order, species_order, strict=True)) != baseline_species_by_id
            for identifier_order, species_order in zip(identifier_orders[1:], species_orders[1:], strict=True)
        ):
            findings.append(
                {
                    "finding_id": "TRAJECTORY_IDENTIFIER_SPECIES_CHANGED",
                    "severity": "blocker",
                    "message": "a stable particle identifier is associated with different species across frames",
                }
            )
        elif any(identifier_order != identifier_orders[0] for identifier_order in identifier_orders[1:]):
            findings.append(
                {
                    "finding_id": "TRAJECTORY_STORAGE_ORDER_CHANGED_WITH_IDS",
                    "severity": "notice",
                    "message": "storage order changes but stable unique particle identifiers preserve mapping",
                }
            )
    if not identifiers_present_all and not identifiers_absent_all:
        findings.append(
            {
                "finding_id": "TRAJECTORY_PARTICLE_IDENTIFIERS_CHANGED",
                "severity": "blocker",
                "message": "particle identifiers are present in only part of the trajectory",
            }
        )
    elif identifiers_present_all and not identifier_sets_constant:
        findings.append(
            {
                "finding_id": "TRAJECTORY_PARTICLE_IDENTIFIERS_CHANGED",
                "severity": "blocker",
                "message": "particle identifier sets differ across frames",
            }
        )
    if not property_schema_constant:
        findings.append(
            {
                "finding_id": "TRAJECTORY_PROPERTY_SCHEMA_CHANGED",
                "severity": "blocker",
                "message": "extended XYZ property declarations differ between frames",
            }
        )
    if any(item is None for item in pbc_values):
        findings.append(
            {
                "finding_id": "TRAJECTORY_PBC_UNDECLARED",
                "severity": "warning",
                "message": "one or more frames omit explicit PBC metadata",
            }
        )
    if len(set(json.dumps(item, sort_keys=True) for item in pbc_values)) > 1:
        findings.append(
            {
                "finding_id": "TRAJECTORY_PBC_CHANGED",
                "severity": "blocker",
                "message": "PBC declarations differ between frames",
            }
        )
    if len(set(cell_values)) > 1:
        findings.append(
            {
                "finding_id": "TRAJECTORY_CELL_PRESENCE_CHANGED",
                "severity": "blocker",
                "message": "cell presence differs between frames",
            }
        )
        cell_mode = "mixed"
    elif not any(cell_values):
        cell_mode = "absent"
    elif len(set(cell_hashes)) == 1:
        cell_mode = "fixed"
    else:
        cell_mode = "variable"
        findings.append(
            {
                "finding_id": "TRAJECTORY_CELL_CHANGED",
                "severity": "warning",
                "message": "cell vectors vary between frames and require a variable-cell analysis policy",
            }
        )
    blockers = [item for item in findings if item["severity"] == "blocker"]
    warnings = [item for item in findings if item["severity"] == "warning"]
    is_extxyz = any(frame["extended_xyz"] for frame in frames)
    return {
        "contract_name": "ovito-trajectory-inventory-candidate",
        "schema_version": "0.1",
        "status": "pass" if not blockers else "blocked",
        "source": source,
        "format": "extxyz" if is_extxyz else "xyz",
        "frame_count": len(frames),
        "atom_count": atom_counts[0] if atom_count_constant else None,
        "atom_count_constant": atom_count_constant,
        "species_order_constant": species_order_constant,
        "particle_identifier_status": (
            "present-stable" if stable_particle_identifiers else ("absent-all" if identifiers_absent_all else "mixed-or-changing")
        ),
        "property_schema_constant": property_schema_constant,
        "site_order_status": (
            "stable-site-ids" if stable_particle_identifiers else ("ordinal-only" if species_order_constant else "unresolved")
        ),
        "pbc_status": "explicit" if all(item is not None for item in pbc_values) else "partly-undeclared",
        "cell_status": "present-all" if all(cell_values) else ("absent-all" if not any(cell_values) else "mixed"),
        "cell_mode": cell_mode,
        "length_unit": "undeclared-source-native",
        "available_properties": sorted(all_properties),
        "frames": frames,
        "analysis_readiness": "blocked" if blockers else ("requires-decision" if warnings else "ready"),
        "findings": findings,
        "parser_state": "parser-only",
        "ovito_executed": False,
        **candidate_lifecycle("input_gates_only"),
        "limitations": [
            "XYZ continuity is ordinal-only unless stable unique id:I:1 values or an external mapping record are supplied.",
            "XYZ/extxyz coordinates remain in source-native units; the format does not establish an angstrom conversion.",
            "The standard-library parser does not establish OVITO import compatibility.",
        ],
        "provenance": {"tool": "ovito_analysis.py", "tool_version": TOOL_VERSION},
    }


def validate_inventory(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "contract_name", "schema_version", "status", "source", "format", "frame_count", "atom_count",
        "atom_count_constant", "species_order_constant", "particle_identifier_status",
        "property_schema_constant", "site_order_status", "pbc_status", "cell_status", "cell_mode",
        "length_unit", "available_properties", "frames", "analysis_readiness",
        "findings", "parser_state", "ovito_executed", "claim_ceiling", "future_gate_ceiling",
        "promotion_authorized", "execution_authorized", "limitations", "provenance",
    }
    _keys(value, required, "inventory")
    if value["contract_name"] != "ovito-trajectory-inventory-candidate" or value["schema_version"] != "0.1":
        raise GateError("INVENTORY_SCHEMA_INVALID", "inventory contract identity is unsupported")
    if value["parser_state"] != "parser-only" or value["ovito_executed"] is not False:
        raise GateError("INVENTORY_EXECUTION_CLAIM_INVALID", "inventory must remain parser-only and non-executed")
    if (
        value["claim_ceiling"] != "no_positive_claim"
        or value["future_gate_ceiling"] != "input_gates_only"
        or value["promotion_authorized"] is not False
        or value["execution_authorized"] is not False
    ):
        raise GateError("INVENTORY_CLAIM_INVALID", "candidate lifecycle fields cannot assert a current positive claim")
    if value["format"] not in {"xyz", "extxyz"}:
        raise GateError("INVENTORY_FORMAT_INVALID", "inventory format is unsupported")
    source = value["source"]
    if not isinstance(source, dict):
        raise GateError("INVENTORY_SOURCE_INVALID", "inventory source must be an object")
    _keys(source, {"label", "bytes", "sha256"}, "inventory source")
    if (
        isinstance(source["bytes"], bool)
        or not isinstance(source["bytes"], int)
        or source["bytes"] < 1
        or not isinstance(source["sha256"], str)
        or not re.fullmatch(r"[a-f0-9]{64}", source["sha256"])
        or not isinstance(source["label"], str)
        or not re.fullmatch(
            rf"source-{source['sha256'][:12]}(?:\.[a-z0-9]{{1,10}})?",
            source["label"],
        )
    ):
        raise GateError("INVENTORY_SOURCE_INVALID", "inventory source hash is invalid")
    if isinstance(value["frame_count"], bool) or not isinstance(value["frame_count"], int) or value["frame_count"] < 1:
        raise GateError("INVENTORY_FRAME_COUNT_INVALID", "inventory frame_count must be positive")
    if not isinstance(value["frames"], list) or len(value["frames"]) != value["frame_count"]:
        raise GateError("INVENTORY_FRAME_COUNT_INVALID", "inventory frame list does not match frame_count")
    frame_keys = {
        "frame_index", "atom_count", "species_order", "particle_identifiers", "cell_present",
        "cell_vectors", "cell_sha256", "cell_determinant_source_units3", "pbc",
        "comment_attributes", "extended_xyz", "properties", "property_schema", "frame_sha256",
    }
    for expected_index, frame in enumerate(value["frames"]):
        if not isinstance(frame, dict):
            raise GateError("INVENTORY_FRAME_INVALID", "every inventory frame must be an object")
        _keys(frame, frame_keys, f"inventory frame {expected_index}")
        if frame["frame_index"] != expected_index:
            raise GateError("INVENTORY_FRAME_INDEX_INVALID", "inventory frame indices must be contiguous from zero")
        if isinstance(frame["atom_count"], bool) or not isinstance(frame["atom_count"], int) or frame["atom_count"] < 1:
            raise GateError("INVENTORY_ATOM_COUNT_INVALID", "frame atom_count must be positive")
        species_order = frame["species_order"]
        if (
            not isinstance(species_order, list)
            or len(species_order) != frame["atom_count"]
            or any(not isinstance(item, str) or not ELEMENT.fullmatch(item) for item in species_order)
        ):
            raise GateError("INVENTORY_SPECIES_ORDER_INVALID", "frame species order does not match atom_count")
        particle_identifiers = frame["particle_identifiers"]
        if particle_identifiers is not None and (
            not isinstance(particle_identifiers, list)
            or len(particle_identifiers) != frame["atom_count"]
            or any(isinstance(item, bool) or not isinstance(item, int) for item in particle_identifiers)
            or len(set(particle_identifiers)) != len(particle_identifiers)
        ):
            raise GateError(
                "INVENTORY_PARTICLE_IDENTIFIERS_INVALID",
                "frame particle identifiers must be null or unique integers matching atom_count",
            )
        if type(frame["cell_present"]) is not bool or type(frame["extended_xyz"]) is not bool:
            raise GateError("INVENTORY_FRAME_INVALID", "frame boolean states are invalid")
        if frame["cell_present"]:
            if (
                not isinstance(frame["cell_vectors"], list)
                or len(frame["cell_vectors"]) != 3
                or any(not isinstance(vector, list) or len(vector) != 3 for vector in frame["cell_vectors"])
                or not isinstance(frame["cell_sha256"], str)
                or not re.fullmatch(r"[a-f0-9]{64}", frame["cell_sha256"])
                or _finite(frame["cell_determinant_source_units3"], "cell determinant") == 0.0
            ):
                raise GateError("INVENTORY_CELL_INVALID", "present frame cell evidence is invalid")
            for row in frame["cell_vectors"]:
                for component in row:
                    _finite(component, "cell vector component")
            if digest(frame["cell_vectors"]) != frame["cell_sha256"]:
                raise GateError("INVENTORY_CELL_INVALID", "cell hash does not match cell vectors")
        elif (
            frame["cell_vectors"] is not None
            or frame["cell_sha256"] is not None
            or frame["cell_determinant_source_units3"] is not None
        ):
            raise GateError("INVENTORY_CELL_INVALID", "absent frame cell must not carry cell evidence")
        pbc = frame["pbc"]
        if pbc is not None and (
            not isinstance(pbc, list) or len(pbc) != 3 or any(type(item) is not bool for item in pbc)
        ):
            raise GateError("INVENTORY_PBC_INVALID", "frame PBC must be null or three booleans")
        if pbc is not None and any(pbc) and not frame["cell_present"]:
            raise GateError("INVENTORY_PBC_INVALID", "periodic frame must carry cell evidence")
        attributes = frame["comment_attributes"]
        if (
            not isinstance(attributes, list)
            or len(attributes) != len(set(attributes))
            or any(not isinstance(item, str) or not PROPERTY_NAME.fullmatch(item) for item in attributes)
        ):
            raise GateError("INVENTORY_ATTRIBUTES_INVALID", "frame comment attribute names are invalid")
        properties = frame["properties"]
        schema = frame["property_schema"]
        if not isinstance(properties, list) or properties != sorted(set(properties)) or not isinstance(schema, list):
            raise GateError("INVENTORY_PROPERTY_SCHEMA_INVALID", "frame properties or schema are invalid")
        schema_names: list[str] = []
        for descriptor in schema:
            if not isinstance(descriptor, dict):
                raise GateError("INVENTORY_PROPERTY_SCHEMA_INVALID", "property descriptor must be an object")
            _keys(descriptor, {"name", "type", "count"}, "inventory property descriptor")
            if (
                not isinstance(descriptor["name"], str)
                or not PROPERTY_NAME.fullmatch(descriptor["name"])
                or descriptor["type"] not in {"R", "I", "S", "L"}
                or isinstance(descriptor["count"], bool)
                or not isinstance(descriptor["count"], int)
                or not 1 <= descriptor["count"] <= 64
            ):
                raise GateError("INVENTORY_PROPERTY_SCHEMA_INVALID", "property descriptor value is invalid")
            schema_names.append(descriptor["name"])
        if len(schema_names) != len(set(schema_names)) or properties != sorted(schema_names):
            raise GateError("INVENTORY_PROPERTY_SCHEMA_INVALID", "property names disagree with schema")
        if not isinstance(frame["frame_sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", frame["frame_sha256"]):
            raise GateError("INVENTORY_FRAME_HASH_INVALID", "frame hash is invalid")

    frames = value["frames"]
    atom_counts = [frame["atom_count"] for frame in frames]
    species_orders = [frame["species_order"] for frame in frames]
    identifier_orders = [frame["particle_identifiers"] for frame in frames]
    schemas = [frame["property_schema"] for frame in frames]
    pbc_values = [frame["pbc"] for frame in frames]
    cell_presence = [frame["cell_present"] for frame in frames]
    cell_hashes = [frame["cell_sha256"] for frame in frames]
    atom_count_constant = len(set(atom_counts)) == 1
    species_order_constant = all(item == species_orders[0] for item in species_orders)
    identifiers_present_all = all(item is not None for item in identifier_orders)
    identifiers_absent_all = all(item is None for item in identifier_orders)
    identifier_sets_constant = identifiers_present_all and all(
        set(item) == set(identifier_orders[0]) for item in identifier_orders
    )
    stable_particle_identifiers = identifiers_present_all and identifier_sets_constant
    property_schema_constant = all(item == schemas[0] for item in schemas)
    if value["atom_count_constant"] is not atom_count_constant:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "atom_count_constant does not match frames")
    if value["species_order_constant"] is not species_order_constant:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "species_order_constant does not match frames")
    if value["property_schema_constant"] is not property_schema_constant:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "property_schema_constant does not match frames")
    expected_atom_count = atom_counts[0] if atom_count_constant else None
    if value["atom_count"] != expected_atom_count:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "atom_count does not match frame reduction")
    expected_identifier_status = (
        "present-stable"
        if stable_particle_identifiers
        else ("absent-all" if identifiers_absent_all else "mixed-or-changing")
    )
    if value["particle_identifier_status"] != expected_identifier_status:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "particle_identifier_status does not match frames")
    expected_site_order = (
        "stable-site-ids"
        if stable_particle_identifiers
        else ("ordinal-only" if species_order_constant else "unresolved")
    )
    if value["site_order_status"] != expected_site_order:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "site_order_status does not match frames")
    expected_pbc_status = "explicit" if all(item is not None for item in pbc_values) else "partly-undeclared"
    if value["pbc_status"] != expected_pbc_status:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "pbc_status does not match frames")
    expected_cell_status = "present-all" if all(cell_presence) else ("absent-all" if not any(cell_presence) else "mixed")
    if value["cell_status"] != expected_cell_status:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "cell_status does not match frames")
    if expected_cell_status == "mixed":
        expected_cell_mode = "mixed"
    elif expected_cell_status == "absent-all":
        expected_cell_mode = "absent"
    elif len(set(cell_hashes)) == 1:
        expected_cell_mode = "fixed"
    else:
        expected_cell_mode = "variable"
    if value["cell_mode"] != expected_cell_mode:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "cell_mode does not match frames")
    if value["length_unit"] != "undeclared-source-native":
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "XYZ inventory cannot infer a physical length unit")
    expected_format = "extxyz" if any(frame["extended_xyz"] for frame in frames) else "xyz"
    if value["format"] != expected_format:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "format does not match frame evidence")
    expected_properties = sorted({item for frame in frames for item in frame["properties"]})
    if value["available_properties"] != expected_properties:
        raise GateError("INVENTORY_REDUCTION_MISMATCH", "available_properties do not match frames")

    expected_findings: dict[str, str] = {}
    if not atom_count_constant:
        expected_findings["TRAJECTORY_ATOM_COUNT_CHANGED"] = "blocker"
    if not species_order_constant and not stable_particle_identifiers:
        expected_findings["TRAJECTORY_SPECIES_ORDER_CHANGED"] = "blocker"
    if stable_particle_identifiers:
        baseline_species_by_id = dict(zip(identifier_orders[0], species_orders[0], strict=True))
        if any(
            dict(zip(identifier_order, species_order, strict=True)) != baseline_species_by_id
            for identifier_order, species_order in zip(identifier_orders[1:], species_orders[1:], strict=True)
        ):
            expected_findings["TRAJECTORY_IDENTIFIER_SPECIES_CHANGED"] = "blocker"
        elif any(identifier_order != identifier_orders[0] for identifier_order in identifier_orders[1:]):
            expected_findings["TRAJECTORY_STORAGE_ORDER_CHANGED_WITH_IDS"] = "notice"
    if not identifiers_present_all and not identifiers_absent_all:
        expected_findings["TRAJECTORY_PARTICLE_IDENTIFIERS_CHANGED"] = "blocker"
    elif identifiers_present_all and not identifier_sets_constant:
        expected_findings["TRAJECTORY_PARTICLE_IDENTIFIERS_CHANGED"] = "blocker"
    if not property_schema_constant:
        expected_findings["TRAJECTORY_PROPERTY_SCHEMA_CHANGED"] = "blocker"
    if any(item is None for item in pbc_values):
        expected_findings["TRAJECTORY_PBC_UNDECLARED"] = "warning"
    if len({json.dumps(item, sort_keys=True) for item in pbc_values}) > 1:
        expected_findings["TRAJECTORY_PBC_CHANGED"] = "blocker"
    if expected_cell_mode == "mixed":
        expected_findings["TRAJECTORY_CELL_PRESENCE_CHANGED"] = "blocker"
    elif expected_cell_mode == "variable":
        expected_findings["TRAJECTORY_CELL_CHANGED"] = "warning"
    findings = value["findings"]
    if not isinstance(findings, list):
        raise GateError("INVENTORY_FINDINGS_INVALID", "inventory findings must be an array")
    observed_findings: dict[str, str] = {}
    for finding in findings:
        if not isinstance(finding, dict):
            raise GateError("INVENTORY_FINDINGS_INVALID", "inventory finding must be an object")
        _keys(finding, {"finding_id", "severity", "message"}, "inventory finding")
        if (
            finding["finding_id"] in observed_findings
            or finding["severity"] not in {"blocker", "warning", "notice"}
            or not isinstance(finding["message"], str)
            or not finding["message"]
        ):
            raise GateError("INVENTORY_FINDINGS_INVALID", "inventory finding is invalid")
        observed_findings[finding["finding_id"]] = finding["severity"]
    if observed_findings != expected_findings:
        raise GateError("INVENTORY_FINDINGS_MISMATCH", "inventory findings do not match frame reductions")
    blockers = any(severity == "blocker" for severity in expected_findings.values())
    warnings = any(severity == "warning" for severity in expected_findings.values())
    expected_status = "blocked" if blockers else "pass"
    expected_readiness = "blocked" if blockers else ("requires-decision" if warnings else "ready")
    if value["status"] != expected_status or value["analysis_readiness"] != expected_readiness:
        raise GateError("INVENTORY_READINESS_MISMATCH", "inventory status/readiness do not match findings")
    if (
        not isinstance(value["limitations"], list)
        or any(not isinstance(item, str) or not item for item in value["limitations"])
        or value["provenance"] != {"tool": "ovito_analysis.py", "tool_version": TOOL_VERSION}
    ):
        raise GateError("INVENTORY_PROVENANCE_INVALID", "inventory limitations or provenance are invalid")
    return value


def validate_pipeline(value: dict[str, Any], inventory: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[int]]:
    _keys(
        value,
        {
            "contract_name", "schema_version", "pipeline_id", "provider", "source", "frame_selection",
            "operations", "outputs", "periodic_policy", "mapping_policy", "source_length_unit",
            "claim_boundary",
        },
        "pipeline",
    )
    if value["contract_name"] != "ovito-pipeline-spec-candidate" or value["schema_version"] != "0.1":
        raise GateError("PIPELINE_SCHEMA_INVALID", "pipeline contract identity is unsupported")
    if not isinstance(value["pipeline_id"], str) or not SAFE_ID.fullmatch(value["pipeline_id"]):
        raise GateError("PIPELINE_ID_INVALID", "pipeline_id is unsafe")
    provider = value["provider"]
    if not isinstance(provider, dict):
        raise GateError("PROVIDER_INVALID", "provider must be an object")
    _keys(provider, {"profile", "version"}, "provider")
    if provider["profile"] not in {"ovito-basic", "ovito-pro"}:
        raise GateError("PROVIDER_PROFILE_INVALID", "provider profile must be ovito-basic or ovito-pro")
    if provider["version"] != EXPECTED_OVITO_VERSION:
        raise GateError("PROVIDER_VERSION_MISMATCH", f"provider version must be {EXPECTED_OVITO_VERSION}")
    source = value["source"]
    if not isinstance(source, dict):
        raise GateError("PIPELINE_SOURCE_INVALID", "pipeline source must be an object")
    _keys(source, {"sha256", "format"}, "pipeline source")
    if source["sha256"] != inventory["source"]["sha256"] or source["format"] != inventory["format"]:
        raise GateError("PIPELINE_SOURCE_MISMATCH", "pipeline source identity does not match inventory")

    selection = value["frame_selection"]
    if not isinstance(selection, dict) or "mode" not in selection:
        raise GateError("FRAME_SELECTION_INVALID", "frame_selection is invalid")
    if selection["mode"] == "indices":
        _keys(selection, {"mode", "indices"}, "frame_selection")
        indices = selection["indices"]
        if (
            not isinstance(indices, list)
            or not indices
            or any(isinstance(item, bool) or not isinstance(item, int) for item in indices)
            or len(indices) != len(set(indices))
        ):
            raise GateError("FRAME_SELECTION_INVALID", "indices must be a non-empty unique integer list")
    elif selection["mode"] == "range":
        _keys(selection, {"mode", "start", "stop", "step"}, "frame_selection")
        start, stop, step = selection["start"], selection["stop"], selection["step"]
        if any(isinstance(item, bool) or not isinstance(item, int) for item in (start, stop, step)):
            raise GateError("FRAME_SELECTION_INVALID", "range bounds must be integers")
        if start < 0 or stop <= start or step < 1:
            raise GateError("FRAME_SELECTION_INVALID", "range must satisfy 0 <= start < stop and step >= 1")
        indices = list(range(start, stop, step))
    else:
        raise GateError("FRAME_SELECTION_INVALID", "selection mode must be indices or range")
    if any(item < 0 or item >= inventory["frame_count"] for item in indices):
        raise GateError("FRAME_SELECTION_OUT_OF_RANGE", "selected frame is outside the inventory")

    if value["periodic_policy"] not in {"preserve-source", "require-cell"}:
        raise GateError("PERIODIC_POLICY_INVALID", "periodic_policy is unsupported")
    if value["periodic_policy"] == "require-cell" and inventory["cell_status"] != "present-all":
        raise GateError("PERIODIC_CELL_REQUIRED", "pipeline requires a cell in every selected source frame")
    if value["mapping_policy"] not in {"ordinal-only-for-metadata", "require-stable-site-ids"}:
        raise GateError("MAPPING_POLICY_INVALID", "mapping_policy is unsupported")
    if value["mapping_policy"] == "require-stable-site-ids" and inventory["site_order_status"] != "stable-site-ids":
        raise GateError("STABLE_SITE_MAPPING_REQUIRED", "inventory lacks stable site IDs")
    if value["source_length_unit"] not in {"undeclared", "angstrom", "nanometer", "bohr"}:
        raise GateError("LENGTH_UNIT_INVALID", "source_length_unit is unsupported")
    if value["claim_boundary"] != "technical-only":
        raise GateError("CLAIM_BOUNDARY_INVALID", "candidate pipeline claim_boundary must be technical-only")

    operations = value["operations"]
    if not isinstance(operations, list) or not operations:
        raise GateError("OPERATIONS_INVALID", "operations must be a non-empty array")
    operation_ids: set[str] = set()
    findings: list[dict[str, str]] = []
    for operation in operations:
        if not isinstance(operation, dict):
            raise GateError("OPERATION_INVALID", "each operation must be an object")
        _keys(operation, {"operation_id", "kind", "parameters", "evidence_role"}, "operation")
        operation_id = operation["operation_id"]
        if not isinstance(operation_id, str) or not SAFE_ID.fullmatch(operation_id) or operation_id in operation_ids:
            raise GateError("OPERATION_ID_INVALID", "operation_id must be unique and safe")
        operation_ids.add(operation_id)
        kind = operation["kind"]
        if kind not in OPERATION_CATALOG:
            raise GateError("OPERATION_UNSUPPORTED", f"operation kind {kind!r} is not cataloged")
        catalog = OPERATION_CATALOG[kind]
        parameters = operation["parameters"]
        if (
            not isinstance(parameters, dict)
            or set(parameters) - catalog["allowed_parameters"]
            or not catalog["required_parameters"].issubset(parameters)
        ):
            raise GateError("OPERATION_PARAMETERS_INVALID", f"operation {operation_id!r} has unsupported parameters")
        for parameter_name, parameter_value in parameters.items():
            if parameter_name == "cutoff_source_units":
                if _finite(parameter_value, parameter_name) <= 0.0:
                    raise GateError("OPERATION_PARAMETERS_INVALID", f"{parameter_name} must be positive")
                if value["source_length_unit"] == "undeclared":
                    raise GateError(
                        "LENGTH_UNIT_UNRESOLVED",
                        "a numerical cutoff requires an explicit source_length_unit",
                    )
            elif parameter_name == "reference_frame":
                if isinstance(parameter_value, bool) or not isinstance(parameter_value, int) or parameter_value < 0:
                    raise GateError("OPERATION_PARAMETERS_INVALID", "reference_frame must be a non-negative integer")
            elif parameter_name in {"number_of_bins", "width_px", "height_px"}:
                if isinstance(parameter_value, bool) or not isinstance(parameter_value, int) or parameter_value < 1:
                    raise GateError("OPERATION_PARAMETERS_INVALID", f"{parameter_name} must be a positive integer")
            elif parameter_name == "mode" and parameter_value not in {"fixed-cutoff", "adaptive"}:
                raise GateError("OPERATION_PARAMETERS_INVALID", "mode must be fixed-cutoff or adaptive")
            elif parameter_name == "camera" and parameter_value not in {"orthographic", "perspective"}:
                raise GateError("OPERATION_PARAMETERS_INVALID", "camera must be orthographic or perspective")
            elif parameter_name == "crystal_structure" and parameter_value not in {
                "fcc", "bcc", "hcp", "cubic-diamond", "hexagonal-diamond"
            }:
                raise GateError("OPERATION_PARAMETERS_INVALID", "crystal_structure is unsupported")
            elif parameter_name == "format" and parameter_value not in {"csv", "txt"}:
                raise GateError("OPERATION_PARAMETERS_INVALID", "export format must be csv or txt")
            elif parameter_name == "columns":
                if not isinstance(parameter_value, list) or not parameter_value or any(
                    not isinstance(item, str) or not item or len(item) > 128 for item in parameter_value
                ):
                    raise GateError("OPERATION_PARAMETERS_INVALID", "columns must be a non-empty string list")
            elif parameter_name == "background":
                if not isinstance(parameter_value, str) or not parameter_value or len(parameter_value) > 64:
                    raise GateError("OPERATION_PARAMETERS_INVALID", "background must be a bounded string")
        if operation["evidence_role"] != catalog["evidence_role"]:
            raise GateError("EVIDENCE_ROLE_MISMATCH", f"operation {operation_id!r} evidence_role is incorrect")
        if catalog["minimum_profile"] == "ovito-pro" and provider["profile"] != "ovito-pro":
            raise GateError("PRO_OPERATION_ON_BASIC", f"operation {operation_id!r} requires ovito-pro")
        if catalog["candidate_execution"] != "implemented":
            findings.append(
                {
                    "finding_id": "OPERATION_PLAN_ONLY",
                    "severity": "blocker",
                    "message": f"operation {operation_id!r} is cataloged but not executable by this candidate",
                }
            )
    outputs = value["outputs"]
    if not isinstance(outputs, list) or not outputs:
        raise GateError("OUTPUTS_INVALID", "outputs must be a non-empty array")
    output_ids: set[str] = set()
    requested_output_kinds: set[str] = set()
    for output in outputs:
        if not isinstance(output, dict):
            raise GateError("OUTPUT_SPEC_INVALID", "each output must be an object")
        _keys(output, {"output_id", "kind", "label"}, "output")
        output_id = output["output_id"]
        if not isinstance(output_id, str) or not SAFE_ID.fullmatch(output_id) or output_id in output_ids:
            raise GateError("OUTPUT_ID_INVALID", "output_id must be unique and safe")
        output_ids.add(output_id)
        if output["kind"] not in {"json-data", "data-table", "image", "animation"}:
            raise GateError("OUTPUT_KIND_INVALID", "output kind is unsupported")
        requested_output_kinds.add(output["kind"])
        label = output["label"]
        if not isinstance(label, str) or not label or "/" in label or "\\" in label or label in {".", ".."}:
            raise GateError("OUTPUT_LABEL_INVALID", "output label must be a basename, not a path")
    for operation in operations:
        allowed_output_kinds = OPERATION_CATALOG[operation["kind"]]["output_kinds"]
        if not requested_output_kinds.intersection(allowed_output_kinds):
            raise GateError(
                "OUTPUT_OPERATION_MISMATCH",
                f"operation {operation['operation_id']!r} has no compatible requested output",
            )
    allowed_union = set().union(*(OPERATION_CATALOG[operation["kind"]]["output_kinds"] for operation in operations))
    if requested_output_kinds - allowed_union:
        raise GateError("OUTPUT_OPERATION_MISMATCH", "requested output kind has no producing operation")
    return value, findings, indices


def make_plan(
    inventory: dict[str, Any],
    inventory_record_source: dict[str, Any],
    spec: dict[str, Any],
    spec_source: dict[str, Any],
) -> dict[str, Any]:
    spec, findings, indices = validate_pipeline(spec, inventory)
    if spec["provider"]["profile"] == "ovito-pro":
        findings.append(
            {
                "finding_id": "PRO_ENTITLEMENT_NOT_VERIFIED",
                "severity": "blocker",
                "message": "candidate cannot verify OVITO Pro entitlement or activation material",
            }
        )
    if inventory["analysis_readiness"] != "ready":
        findings.append(
            {
                "finding_id": "INVENTORY_ANALYSIS_NOT_READY",
                "severity": "blocker",
                "message": "trajectory inventory contains unresolved periodicity, cell, topology, or mapping evidence",
            }
        )
    execution_ready = not findings and inventory["status"] == "pass" and inventory["analysis_readiness"] == "ready"
    authorization_scope = {
        "action": "ovito-basic-frame-metadata-execution",
        "pipeline_id": spec["pipeline_id"],
        "source_sha256": inventory["source"]["sha256"],
        "inventory_record_sha256": inventory_record_source["sha256"],
        "pipeline_spec_sha256": spec_source["sha256"],
        "provider": spec["provider"],
        "source_length_unit": spec["source_length_unit"],
        "selected_frames": indices,
        "operations": [
            {"operation_id": operation["operation_id"], "kind": operation["kind"]}
            for operation in spec["operations"]
        ],
    }
    return {
        "contract_name": "ovito-pipeline-plan-candidate",
        "schema_version": "0.1",
        "status": "planned",
        "pipeline_id": spec["pipeline_id"],
        "inventory_source_sha256": inventory["source"]["sha256"],
        "inventory_record_source": inventory_record_source,
        "spec_source": spec_source,
        "provider": spec["provider"],
        "source_length_unit": spec["source_length_unit"],
        "selected_frames": indices,
        "operations": [
            {
                "operation_id": operation["operation_id"],
                "kind": operation["kind"],
                "candidate_execution": OPERATION_CATALOG[operation["kind"]]["candidate_execution"],
                "minimum_profile": OPERATION_CATALOG[operation["kind"]]["minimum_profile"],
                "evidence_role": operation["evidence_role"],
            }
            for operation in spec["operations"]
        ],
        "outputs": spec["outputs"],
        "authorization_scope": authorization_scope,
        "authorization_scope_sha256": digest(authorization_scope),
        "execution_readiness": "ready" if execution_ready else "blocked",
        "execution_state": "planned-not-executed",
        "ovito_executed": False,
        "findings": findings,
        **candidate_lifecycle("input_gates_only"),
        "limitations": [
            "A planned pipeline contains no numerical analysis or rendered artifact.",
            "Execution readiness is not scientific acceptance and does not verify a software license.",
        ],
        "provenance": {"tool": "ovito_analysis.py", "tool_version": TOOL_VERSION},
    }


def command_inventory(args: argparse.Namespace) -> int:
    report = inventory_xyz(args.source)
    write_json(report, args.out)
    if args.require_analysis_ready and report["analysis_readiness"] != "ready":
        return EXIT_BLOCKED
    return EXIT_OK


def command_plan(args: argparse.Namespace) -> int:
    inventory_value, inventory_record_source = load_json(args.inventory, "INVENTORY")
    spec, spec_source = load_json(args.pipeline, "PIPELINE")
    inventory = validate_inventory(inventory_value)
    report = make_plan(inventory, inventory_record_source, spec, spec_source)
    write_json(report, args.out)
    if args.require_execution_ready and report["execution_readiness"] != "ready":
        return EXIT_BLOCKED
    return EXIT_OK


def command_probe(args: argparse.Namespace) -> int:
    try:
        observed = importlib.metadata.version("ovito")
        state = "match" if observed == EXPECTED_OVITO_VERSION else "version-mismatch"
    except importlib.metadata.PackageNotFoundError:
        observed = None
        state = "not-installed"
    report = {
        "contract_name": "ovito-provider-probe-candidate",
        "schema_version": "0.1",
        "status": "available" if state == "match" else "unavailable",
        "provider_profile": "ovito-basic",
        "distribution": "ovito",
        "expected_version": EXPECTED_OVITO_VERSION,
        "observed_version": observed,
        "state": state,
        "probe_kind": "distribution-metadata-only",
        "module_imported": False,
        "pipeline_executed": False,
        "license_entitlement_verified": False,
        **candidate_lifecycle("documented_behavior_only"),
        "provenance": {"tool": "ovito_analysis.py", "tool_version": TOOL_VERSION},
    }
    write_json(report, args.out)
    return EXIT_OK if state == "match" else EXIT_UNAVAILABLE


def command_execute(args: argparse.Namespace) -> int:
    if not args.authorize_execution:
        raise GateError("EXECUTION_NOT_AUTHORIZED", "actual OVITO execution requires --authorize-execution")
    inventory_value, inventory_record_source = load_json(args.inventory, "INVENTORY")
    spec, spec_source = load_json(args.pipeline, "PIPELINE")
    inventory = validate_inventory(inventory_value)
    report = make_plan(inventory, inventory_record_source, spec, spec_source)
    if args.authorization_scope is None:
        raise GateError("AUTHORIZATION_SCOPE_MISSING", "execution requires the exact scope hash emitted by plan")
    if args.authorization_scope != report["authorization_scope_sha256"]:
        raise GateError("AUTHORIZATION_SCOPE_MISMATCH", "execution authorization scope does not match this plan")
    if args.out is None:
        raise GateError("EXECUTION_OUTPUT_REQUIRED", "actual execution requires a new durable JSON output path")
    if report["execution_readiness"] != "ready":
        raise GateError("PIPELINE_NOT_EXECUTION_READY", "pipeline plan is blocked and was not executed")
    if report["provider"]["profile"] != "ovito-basic":
        raise GateError("PRO_EXECUTION_REFUSED", "candidate does not execute OVITO Pro profiles")
    preflight_output(args.out)
    raw, source = _regular_bytes(args.source, MAX_TRAJECTORY_BYTES, "TRAJECTORY")
    if source["sha256"] != inventory["source"]["sha256"]:
        raise GateError("EXECUTION_SOURCE_MISMATCH", "execution source hash differs from inventoried source")
    if source["bytes"] != inventory["source"]["bytes"]:
        raise GateError("OVITO_INVENTORY_MISMATCH", "inventory source size differs from verified source bytes")
    suffix = Path(args.source).suffix.lower()
    if not re.fullmatch(r"\.[a-z0-9]{1,10}", suffix):
        suffix = ".data"
    with tempfile.TemporaryDirectory(prefix="ovito-candidate-") as temporary_directory:
        snapshot_path = Path(temporary_directory) / f"verified-source{suffix}"
        try:
            with snapshot_path.open("xb") as snapshot_handle:
                snapshot_handle.write(raw)
        except OSError as exc:
            raise GateError("SNAPSHOT_WRITE_FAILED", "verified private source snapshot could not be created") from exc
        reparsed_inventory = inventory_xyz(str(snapshot_path))
        if digest(inventory_evidence_payload(reparsed_inventory)) != digest(inventory_evidence_payload(inventory)):
            raise GateError(
                "OVITO_INVENTORY_MISMATCH",
                "inventory record does not match a deterministic reparse of the verified source snapshot",
            )
        try:
            distribution_version = importlib.metadata.version("ovito")
        except importlib.metadata.PackageNotFoundError as exc:
            raise GateError(
                "OVITO_DISTRIBUTION_MISMATCH",
                "OVITO distribution metadata is absent",
                EXIT_UNAVAILABLE,
            ) from exc
        if distribution_version != EXPECTED_OVITO_VERSION:
            raise GateError(
                "OVITO_DISTRIBUTION_MISMATCH",
                f"OVITO distribution version must be {EXPECTED_OVITO_VERSION}",
                EXIT_UNAVAILABLE,
            )
        try:
            ovito_module = importlib.import_module("ovito")
            observed_version = getattr(ovito_module, "version_string", None)
            if observed_version != EXPECTED_OVITO_VERSION:
                raise GateError(
                    "OVITO_VERSION_MISMATCH",
                    f"imported OVITO version must be {EXPECTED_OVITO_VERSION}",
                    EXIT_UNAVAILABLE,
                )
            io_module = importlib.import_module("ovito.io")
            import_file = getattr(io_module, "import_file")
        except GateError:
            raise
        except (ImportError, AttributeError) as exc:
            raise GateError("OVITO_UNAVAILABLE", "pinned OVITO Python API is unavailable", EXIT_UNAVAILABLE) from exc
        try:
            pipeline = import_file(str(snapshot_path), sort_particles=False)
            frame_results = []
            for frame_index in report["selected_frames"]:
                data = pipeline.compute(frame_index)
                particles = getattr(data, "particles", None)
                if particles is None:
                    raise GateError("OVITO_PARTICLES_MISSING", "computed frame contains no particle collection")
                count_value = getattr(particles, "count", None)
                if count_value is None:
                    count_value = len(particles)
                property_values = particles.values()
                property_names = sorted(str(getattr(item, "name", "")) for item in property_values)
                cell = getattr(data, "cell", None)
                pbc = None if cell is None else [bool(item) for item in getattr(cell, "pbc", (False, False, False))]
                expected_frame = inventory["frames"][frame_index]
                cell_vectors = None
                if cell is not None:
                    try:
                        cell_vectors = [
                            [float(cell[row, column]) for row in range(3)]
                            for column in range(3)
                        ]
                    except (IndexError, KeyError, TypeError, ValueError) as exc:
                        raise GateError(
                            "OVITO_CELL_INVALID",
                            "OVITO did not expose the expected 3x4 SimulationCell matrix",
                        ) from exc
                expected_identifiers = expected_frame["particle_identifiers"]
                particle_identifiers = None
                if expected_identifiers is not None:
                    try:
                        particle_identifiers = [int(item) for item in particles["Particle Identifier"]]
                    except (IndexError, KeyError, TypeError, ValueError) as exc:
                        raise GateError(
                            "OVITO_PARTICLE_IDENTIFIERS_MISSING",
                            "OVITO did not preserve the inventoried Particle Identifier property",
                        ) from exc
                cell_mismatch = False
                if expected_frame["cell_vectors"] is not None and cell_vectors is not None:
                    cell_mismatch = any(
                        abs(expected_frame["cell_vectors"][i][j] - cell_vectors[i][j]) > 1.0e-10
                        for i in range(3)
                        for j in range(3)
                    )
                if (
                    isinstance(count_value, bool)
                    or not isinstance(count_value, int)
                    or count_value != expected_frame["atom_count"]
                    or (cell is not None) is not expected_frame["cell_present"]
                    or (pbc is not None and len(pbc) != 3)
                    or (expected_frame["pbc"] is not None and pbc != expected_frame["pbc"])
                    or cell_mismatch
                    or particle_identifiers != expected_identifiers
                ):
                    raise GateError(
                        "OVITO_INVENTORY_MISMATCH",
                        "computed particle count, cell, PBC, or particle identifiers differ from inventory evidence",
                    )
                frame_results.append(
                    {
                        "frame_index": frame_index,
                        "particle_count": int(count_value),
                        "particle_properties": property_names,
                        "cell_present": cell is not None,
                        "cell_vectors": cell_vectors,
                        "pbc": pbc,
                        "particle_identifiers": particle_identifiers,
                        "particle_order_policy": "source-storage-order-sort_particles-false",
                    }
                )
        except GateError:
            raise
        except Exception as exc:
            raise GateError("OVITO_EXECUTION_FAILED", "OVITO import or compute failed; no result was certified") from exc
    result = {
        "contract_name": "ovito-execution-result-candidate",
        "schema_version": "0.1",
        "status": "complete",
        "pipeline_id": report["pipeline_id"],
        "source": source,
        "provider": {"profile": "ovito-basic", "version": observed_version},
        "distribution_version": distribution_version,
        "source_length_unit": report["source_length_unit"],
        "import_source": "verified-private-snapshot",
        "authorization": {
            "mode": "explicit-cli-confirmation",
            "scope_sha256": report["authorization_scope_sha256"],
        },
        "executed_operations": [item["kind"] for item in report["operations"]],
        "frames": frame_results,
        "execution_state": "actual-external-execution",
        "ovito_executed": True,
        "license_entitlement_verified": False,
        **candidate_lifecycle("technical_run_gates_only"),
        "limitations": [
            "The candidate executed frame metadata only; it produced no scientific analysis or rendering.",
            "Package execution does not establish license entitlement, scientific validity, or activation readiness.",
        ],
        "provenance": {"tool": "ovito_analysis.py", "tool_version": TOOL_VERSION},
    }
    write_json(result, args.out)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory", help="parse XYZ/extxyz without importing OVITO")
    inventory.add_argument("source")
    inventory.add_argument("--require-analysis-ready", action="store_true")
    inventory.add_argument("--out")
    inventory.set_defaults(handler=command_inventory)

    plan = subparsers.add_parser("plan", help="validate a candidate pipeline without importing OVITO")
    plan.add_argument("--inventory", required=True)
    plan.add_argument("--pipeline", required=True)
    plan.add_argument("--require-execution-ready", action="store_true")
    plan.add_argument("--out")
    plan.set_defaults(handler=command_plan)

    probe = subparsers.add_parser("probe", help="inspect OVITO distribution metadata without importing it")
    probe.add_argument("--out")
    probe.set_defaults(handler=command_probe)

    execute = subparsers.add_parser("execute", help="execute only the implemented metadata operation with pinned OVITO")
    execute.add_argument("--source", required=True)
    execute.add_argument("--inventory", required=True)
    execute.add_argument("--pipeline", required=True)
    execute.add_argument("--authorize-execution", action="store_true")
    execute.add_argument("--authorization-scope")
    execute.add_argument("--out")
    execute.set_defaults(handler=command_execute)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except GateError as exc:
        sys.stderr.write(
            json.dumps(
                error_envelope(exc.finding_id, exc.message),
                sort_keys=True,
            )
            + "\n"
        )
        return exc.exit_code
    except Exception:
        sys.stderr.write(
            json.dumps(
                error_envelope(
                    "UNEXPECTED_INTERNAL_ERROR",
                    "unexpected internal failure; no result was certified",
                    status="internal-error",
                ),
                sort_keys=True,
            )
            + "\n"
        )
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
