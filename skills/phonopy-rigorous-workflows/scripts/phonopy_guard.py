#!/usr/bin/env python3
"""Deterministic candidate guard for Phonopy workflow lineage."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import secrets
import stat
import sys
from pathlib import Path
from typing import Any, TextIO

SCHEMA_VERSION = "phonopy-guard-report@1.0"
MAX_JSON_BYTES = 4_194_304
MAX_TEXT_BYTES = 4_194_304
MAX_DEPTH = 32
MAX_RECORDS = 100_000
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")


class GuardError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        blocked: bool = False,
        next_action: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.blocked = blocked
        self.next_action = next_action


def _canonical_absolute_path(path: Path, code: str, description: str) -> str:
    supplied = Path(os.fspath(path))
    if ".." in supplied.parts:
        raise GuardError(code, f"{description.capitalize()} path must not contain parent traversal.")
    absolute = os.path.abspath(os.fspath(supplied))
    # macOS exposes these root-owned aliases as symlinks.  Canonicalize only the
    # fixed system aliases; every task-controlled intermediate symlink remains
    # forbidden by the component walk below.
    if sys.platform == "darwin":
        for alias, target in (("/var", "/private/var"), ("/tmp", "/private/tmp"), ("/etc", "/private/etc")):
            if absolute != alias and not absolute.startswith(alias + os.sep):
                continue
            try:
                metadata = os.lstat(alias)
                link_target = os.readlink(alias)
            except OSError:
                break
            if stat.S_ISLNK(metadata.st_mode) and metadata.st_uid == 0 and link_target in {target, target.lstrip("/")}:
                absolute = target + absolute[len(alias) :]
            break
    return absolute


def _open_parent_dirfd(
    path: Path,
    code: str,
    description: str,
    *,
    create: bool = False,
) -> tuple[int, str]:
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise GuardError(code, "Secure component-walk I/O is unavailable on this platform.")
    absolute = _canonical_absolute_path(path, code, description)
    components = list(Path(absolute).parts[1:])
    if not components or any(item in {"", ".", ".."} for item in components):
        raise GuardError(code, f"{description.capitalize()} path is invalid.")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        current = os.open(os.sep, flags)
    except OSError as exc:
        raise GuardError(code, f"Unable to anchor {description} path.") from exc
    try:
        for component in components[:-1]:
            try:
                following = os.open(component, flags, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, mode=0o700, dir_fd=current)
                following = os.open(component, flags, dir_fd=current)
            os.close(current)
            current = following
        return current, components[-1]
    except OSError as exc:
        os.close(current)
        raise GuardError(code, f"Unable to walk {description} path without symlinks.") from exc


def _file_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _open_read_descriptor(path: Path, limit: int, code: str, description: str) -> tuple[int, os.stat_result]:
    parent_fd, name = _open_parent_dirfd(path, code, description)
    flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise GuardError(code, f"Unable to read {description} evidence.") from exc
    finally:
        os.close(parent_fd)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size < 0 or before.st_size > limit:
            raise GuardError(code, f"{description.capitalize()} evidence is not one bounded single-link regular file.")
        return descriptor, before
    except Exception:
        os.close(descriptor)
        raise


def _read_bounded_file(path: Path, limit: int, code: str, description: str) -> bytes:
    descriptor, before = _open_read_descriptor(path, limit, code, description)
    try:
        with os.fdopen(descriptor, "rb") as handle:
            raw = handle.read(limit + 1)
            after = os.fstat(handle.fileno())
    except OSError as exc:
        raise GuardError(code, f"Unable to read {description} evidence.") from exc
    if (
        len(raw) > limit
        or len(raw) != before.st_size
        or not stat.S_ISREG(after.st_mode)
        or after.st_nlink != 1
        or _file_identity(before) != _file_identity(after)
    ):
        raise GuardError(code, f"{description.capitalize()} evidence exceeds the limit or changed while reading.")
    return raw


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite constant {value}")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _check_depth(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise ValueError("JSON nesting limit exceeded")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("non-text object key")
            _check_depth(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _check_depth(item, depth + 1)


def _read_json_evidence(
    path: Path,
    code: str,
    description: str,
) -> tuple[dict[str, Any], str, int]:
    raw = _read_bounded_file(path, MAX_JSON_BYTES, code, description)
    if raw.startswith(b"\xef\xbb\xbf"):
        raise GuardError(code, f"{description.capitalize()} has a forbidden BOM.")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_reject_constant)
        _check_depth(value)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise GuardError(code, f"{description.capitalize()} must be one strict UTF-8 JSON object.") from exc
    if not isinstance(value, dict):
        raise GuardError(code, f"{description.capitalize()} root must be an object.")
    return value, hashlib.sha256(raw).hexdigest(), len(raw)


def read_json(path: Path) -> tuple[dict[str, Any], str]:
    value, digest, _ = _read_json_evidence(path, "PH_JSON_INVALID", "manifest")
    return value, digest


def _exact_keys(value: dict[str, Any], expected: set[str], code: str, description: str) -> None:
    if set(value) != expected:
        raise GuardError(code, f"{description} must contain exactly the versioned contract fields.")


def _object(parent: dict[str, Any], key: str, code: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise GuardError(code, f"Required object is missing: {key}.")
    return value


def _text(parent: dict[str, Any], key: str, code: str, *, safe: bool = False) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GuardError(code, f"Required text is missing: {key}.")
    value = value.strip()
    if safe and not SAFE_ID.fullmatch(value):
        raise GuardError(code, f"Unsafe identifier: {key}.")
    return value


def _hash(parent: dict[str, Any], key: str, code: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise GuardError(code, f"Invalid SHA-256: {key}.")
    return value


def _fingerprint(parent: dict[str, Any], key: str, code: str) -> str:
    value = _text(parent, key, code)
    if not value.startswith("sha256:") or not SHA256.fullmatch(value[7:]):
        raise GuardError(code, f"Invalid structure fingerprint: {key}.")
    return value


def _positive_int(value: Any, message: str, code: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise GuardError(code, message)
    return value


def _finite(value: Any, message: str, code: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise GuardError(code, message)
    return float(value)


def _vector(value: Any, length: int, message: str, code: str) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise GuardError(code, message)
    return [_finite(item, message, code) for item in value]


def _tensor3(value: Any, message: str, code: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 3:
        raise GuardError(code, message)
    return [_vector(row, 3, message, code) for row in value]


def _artifact(parent: dict[str, Any], code: str) -> dict[str, Any]:
    label = _text(parent, "label", code)
    if Path(label).name != label or not SAFE_LABEL.fullmatch(label):
        raise GuardError(code, "Artifact label must be a safe basename.")
    digest = _hash(parent, "sha256", code)
    byte_count = _positive_int(parent.get("bytes"), "Artifact byte count must be positive.", code)
    return {"label": label, "sha256": digest, "bytes": byte_count}


def _determinant(matrix: list[list[int]]) -> int:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def _canonical_sha(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != "phonon-workflow-manifest@0.1-candidate":
        raise GuardError("PH_JSON_INVALID", "Unsupported phonon workflow schema_version.")
    workflow_id = _text(manifest, "workflow_id", "PH_JSON_INVALID", safe=True)
    phonopy = _object(manifest, "phonopy", "PH_VERSION_UNSUPPORTED")
    version = _text(phonopy, "version", "PH_VERSION_UNSUPPORTED")
    if version != "4.3.1":
        raise GuardError("PH_VERSION_UNSUPPORTED", "Only exact Phonopy 4.3.1 candidate semantics are defined.", blocked=True)
    package_hash = _hash(phonopy, "package_sha256", "PH_VERSION_UNSUPPORTED")

    structure = _object(manifest, "structure", "PH_STRUCTURE_INVALID")
    fingerprint = _fingerprint(structure, "fingerprint", "PH_STRUCTURE_INVALID")
    unitcell_hash = _hash(structure, "unitcell_sha256", "PH_STRUCTURE_INVALID")
    atom_count = _positive_int(structure.get("atom_count"), "Unit-cell atom count must be positive.", "PH_STRUCTURE_INVALID")
    primitive_fingerprint = _fingerprint(structure, "primitive_fingerprint", "PH_STRUCTURE_INVALID")
    primitive_atom_count = _positive_int(
        structure.get("primitive_atom_count"),
        "Primitive atom count must be positive.",
        "PH_STRUCTURE_INVALID",
    )
    if primitive_atom_count > atom_count or atom_count % primitive_atom_count != 0:
        raise GuardError("PH_STRUCTURE_INVALID", "Primitive atom count must divide the unit-cell atom count.")
    primitive_matrix = _tensor3(
        structure.get("primitive_matrix"),
        "Primitive matrix must be finite 3x3.",
        "PH_STRUCTURE_INVALID",
    )
    if math.isclose(float(_determinant(primitive_matrix)), 0.0, abs_tol=1.0e-12):
        raise GuardError("PH_STRUCTURE_INVALID", "Primitive matrix must be nonsingular.")

    displacements = _object(manifest, "displacement_set", "PH_DISPLACEMENT_INVALID")
    displacement_set_id = _text(displacements, "id", "PH_DISPLACEMENT_INVALID", safe=True)
    displacement_hash = _hash(displacements, "sha256", "PH_DISPLACEMENT_INVALID")
    matrix_value = displacements.get("supercell_matrix")
    if not isinstance(matrix_value, list) or len(matrix_value) != 3:
        raise GuardError("PH_SUPERCELL_INVALID", "Supercell matrix must be 3x3 integers.")
    matrix: list[list[int]] = []
    for row in matrix_value:
        if (
            not isinstance(row, list)
            or len(row) != 3
            or any(not isinstance(item, int) or isinstance(item, bool) for item in row)
        ):
            raise GuardError("PH_SUPERCELL_INVALID", "Supercell matrix must be 3x3 integers.")
        matrix.append(list(row))
    determinant = abs(_determinant(matrix))
    if determinant == 0:
        raise GuardError("PH_SUPERCELL_INVALID", "Supercell matrix must be nonsingular.")
    supercell_atom_count = _positive_int(
        displacements.get("supercell_atom_count"),
        "Supercell atom count must be positive.",
        "PH_SUPERCELL_INVALID",
    )
    if supercell_atom_count != atom_count * determinant:
        raise GuardError("PH_SUPERCELL_INVALID", "Supercell atom count does not match unit-cell count times determinant.")
    distance = _finite(
        displacements.get("displacement_distance_angstrom"),
        "Displacement distance must be finite.",
        "PH_DISPLACEMENT_INVALID",
    )
    if distance <= 0:
        raise GuardError("PH_DISPLACEMENT_INVALID", "Displacement distance must be positive.")
    records_value = displacements.get("displacements")
    if not isinstance(records_value, list) or not records_value or len(records_value) > MAX_RECORDS:
        raise GuardError("PH_DISPLACEMENT_INVALID", "Displacements must be a bounded nonempty list.")
    displacement_records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_supercells: set[str] = set()
    for record in records_value:
        if not isinstance(record, dict):
            raise GuardError("PH_DISPLACEMENT_INVALID", "Each displacement must be an object.")
        record_id = _text(record, "id", "PH_DISPLACEMENT_INVALID", safe=True)
        if record_id in seen_ids:
            raise GuardError("PH_DISPLACEMENT_CLOSURE_FAILED", "Displacement ids must be unique.")
        seen_ids.add(record_id)
        atom_index = _positive_int(record.get("atom_index"), "Displaced atom index must be positive.", "PH_DISPLACEMENT_INVALID")
        if atom_index > supercell_atom_count:
            raise GuardError("PH_DISPLACEMENT_INVALID", "Displaced atom index exceeds the supercell atom count.")
        vector = _vector(record.get("vector_angstrom"), 3, "Displacement vector must contain three finite values.", "PH_DISPLACEMENT_INVALID")
        if not math.isclose(math.sqrt(math.fsum(component * component for component in vector)), distance, rel_tol=1e-9, abs_tol=1e-12):
            raise GuardError("PH_DISPLACEMENT_INVALID", "Displacement-vector norm differs from the declared distance.")
        supercell_hash = _hash(record, "supercell_sha256", "PH_DISPLACEMENT_INVALID")
        if supercell_hash in seen_supercells:
            raise GuardError("PH_DISPLACEMENT_CLOSURE_FAILED", "Displaced-supercell hashes must be unique.")
        seen_supercells.add(supercell_hash)
        displacement_records.append(
            {"id": record_id, "atom_index": atom_index, "vector_angstrom": vector, "supercell_sha256": supercell_hash}
        )
    canonical_displacement = {
        "structure_fingerprint": fingerprint,
        "supercell_matrix": matrix,
        "displacement_distance_angstrom": distance,
        "displacements": displacement_records,
    }
    if _canonical_sha(canonical_displacement) != displacement_hash:
        raise GuardError("PH_DISPLACEMENT_CLOSURE_FAILED", "Displacement-set canonical SHA-256 does not match its contents.")

    forces = _object(manifest, "forces", "PH_FORCE_INVALID")
    if forces.get("unit") != "eV/angstrom":
        raise GuardError("PH_FORCE_INVALID", "Force unit must be exactly eV/angstrom.")
    force_collection_hash = _hash(forces, "source_force_records_sha256", "PH_FORCE_INVALID")
    force_values = forces.get("records")
    if not isinstance(force_values, list) or len(force_values) != len(displacement_records):
        raise GuardError("PH_DISPLACEMENT_CLOSURE_FAILED", "Force-record count must equal displacement count.")
    force_records: list[dict[str, Any]] = []
    seen_force_ids: set[str] = set()
    for record in force_values:
        if not isinstance(record, dict):
            raise GuardError("PH_FORCE_INVALID", "Each force record must be an object.")
        displacement_id = _text(record, "displacement_id", "PH_FORCE_INVALID", safe=True)
        if displacement_id not in seen_ids or displacement_id in seen_force_ids:
            raise GuardError("PH_DISPLACEMENT_CLOSURE_FAILED", "Force records contain an unknown or duplicate displacement id.")
        seen_force_ids.add(displacement_id)
        artifact = _artifact(_object(record, "file", "PH_FORCE_INVALID"), "PH_FORCE_INVALID")
        if record.get("shape") != [supercell_atom_count, 3]:
            raise GuardError("PH_FORCE_INVALID", "Force array shape must be [supercell_atom_count, 3].")
        parent = _object(record, "parent_calculation", "PH_FORCE_INVALID")
        parent_id = _text(parent, "record_id", "PH_FORCE_INVALID", safe=True)
        parent_record_hash = _hash(parent, "record_sha256", "PH_FORCE_INVALID")
        parent_projection_hash = _hash(parent, "evidence_projection_sha256", "PH_FORCE_INVALID")
        code = _text(parent, "code", "PH_FORCE_INVALID", safe=True)
        if code not in {"qe", "vasp", "cp2k", "siesta"}:
            raise GuardError("PH_FORCE_INVALID", "Force parent code has no active calculation-Skill evidence route.")
        code_version = _text(parent, "code_version", "PH_FORCE_INVALID", safe=True)
        parent_fingerprint = _fingerprint(parent, "structure_fingerprint", "PH_FORCE_INVALID")
        if parent_fingerprint != fingerprint:
            raise GuardError("PH_FORCE_PARENT_MISMATCH", "Force parent has a different structure fingerprint.")
        parent_input = _hash(parent, "input_hash", "PH_FORCE_INVALID")
        parent_output = _hash(parent, "output_hash", "PH_FORCE_INVALID")
        if parent.get("completion") != "complete":
            raise GuardError("PH_FORCE_INVALID", "Every force parent calculation must be explicitly complete.")
        required_parent_gates = ("input_validation", "output_validation", "electronic_convergence", "force_acceptance")
        if any(parent.get(gate) != "pass" for gate in required_parent_gates):
            raise GuardError(
                "PH_FORCE_INVALID",
                "Every force parent must separately pass input, output, electronic-convergence, and force-acceptance gates.",
            )
        gate_projection = {gate: "pass" for gate in required_parent_gates}
        parent_projection = {
            "raw_record_sha256": parent_record_hash,
            "record_id": parent_id,
            "code": code,
            "code_version": code_version,
            "structure_fingerprint": parent_fingerprint,
            "input_hash": parent_input,
            "output_hash": parent_output,
            "completion": "complete",
            "gates": gate_projection,
        }
        if _canonical_sha(parent_projection) != parent_projection_hash:
            raise GuardError(
                "PH_FORCE_PARENT_MISMATCH",
                "Force-parent raw record hash and semantic evidence projection are detached.",
            )
        force_records.append(
            {
                "displacement_id": displacement_id,
                "force_file_sha256": artifact["sha256"],
                "parent_record_sha256": parent_record_hash,
                "parent_evidence_projection_sha256": parent_projection_hash,
                "parent_input_sha256": parent_input,
                "parent_output_sha256": parent_output,
                "record_id": parent_id,
                "code": code,
                "acceptance_gates": gate_projection,
                "artifact": artifact,
            }
        )
    if seen_force_ids != seen_ids:
        raise GuardError("PH_DISPLACEMENT_CLOSURE_FAILED", "Not every displacement has exactly one force record.")
    collection_preimage = [
        {
            "displacement_id": item["displacement_id"],
            "force_file_sha256": item["force_file_sha256"],
            "parent_record_sha256": item["parent_record_sha256"],
            "parent_evidence_projection_sha256": item["parent_evidence_projection_sha256"],
            "parent_input_sha256": item["parent_input_sha256"],
            "parent_output_sha256": item["parent_output_sha256"],
        }
        for item in sorted(force_records, key=lambda item: item["displacement_id"])
    ]
    if _canonical_sha(collection_preimage) != force_collection_hash:
        raise GuardError("PH_FORCE_COLLECTION_HASH_MISMATCH", "Force-collection canonical SHA-256 does not match its records.")

    force_constants = _object(manifest, "force_constants", "PH_FORCE_CONSTANTS_INVALID")
    fc_artifact = _artifact(_object(force_constants, "file", "PH_FORCE_CONSTANTS_INVALID"), "PH_FORCE_CONSTANTS_INVALID")
    if force_constants.get("shape") != [supercell_atom_count, supercell_atom_count, 3, 3]:
        raise GuardError("PH_FORCE_CONSTANTS_INVALID", "Full force constants must have [Ns,Ns,3,3] shape.")
    if _hash(force_constants, "source_displacement_set_sha256", "PH_FORCE_CONSTANTS_INVALID") != displacement_hash:
        raise GuardError("PH_FORCE_CONSTANTS_INVALID", "Force constants bind to a different displacement set.")
    if _hash(force_constants, "source_force_records_sha256", "PH_FORCE_CONSTANTS_INVALID") != force_collection_hash:
        raise GuardError("PH_FORCE_CONSTANTS_INVALID", "Force constants bind to a different force collection.")
    calculator = _text(force_constants, "calculator", "PH_FORCE_CONSTANTS_INVALID", safe=True)
    symmetrization = _text(force_constants, "symmetrization", "PH_FORCE_CONSTANTS_INVALID", safe=True)
    asr = _text(force_constants, "acoustic_sum_rule", "PH_FORCE_CONSTANTS_INVALID", safe=True)

    requested = manifest.get("requested_products")
    allowed_products = {"mesh", "band", "dos", "nac"}
    if not isinstance(requested, list) or not requested or any(
        not isinstance(item, str) or item not in allowed_products for item in requested
    ):
        raise GuardError("PH_PRODUCT_INVALID", "Requested products must be a unique nonempty supported list.")
    if len(requested) != len(set(requested)):
        raise GuardError("PH_PRODUCT_INVALID", "Requested products must be unique.")
    products = _object(manifest, "products", "PH_PRODUCT_INVALID")
    if set(products) != set(requested):
        raise GuardError("PH_PRODUCT_INVALID", "Product keys must exactly equal requested_products.")
    product_summary: dict[str, Any] = {}

    def check_fc_parent(product: dict[str, Any]) -> None:
        if _hash(product, "parent_force_constants_sha256", "PH_PRODUCT_INVALID") != fc_artifact["sha256"]:
            raise GuardError("PH_PRODUCT_PARENT_MISMATCH", "Product binds to a different force-constants artifact.")

    if "mesh" in products:
        product = _object(products, "mesh", "PH_PRODUCT_INVALID")
        check_fc_parent(product)
        parameters = _object(product, "parameters", "PH_PRODUCT_INVALID")
        mesh = parameters.get("mesh")
        if not isinstance(mesh, list) or len(mesh) != 3 or any(not isinstance(item, int) or isinstance(item, bool) or item <= 0 for item in mesh):
            raise GuardError("PH_PRODUCT_INVALID", "Mesh numbers must be three positive integers.")
        if not isinstance(parameters.get("gamma_centered"), bool):
            raise GuardError("PH_PRODUCT_INVALID", "Mesh gamma_centered must be explicit boolean.")
        if parameters.get("frequency_unit") not in {"THz", "cm-1", "meV"}:
            raise GuardError("PH_PRODUCT_INVALID", "Mesh frequency unit is unsupported.")
        dimensions = _object(product, "dimensions", "PH_PRODUCT_INVALID")
        qpoints = _positive_int(dimensions.get("qpoints"), "Mesh q-point count must be positive.", "PH_PRODUCT_INVALID")
        if dimensions.get("branches") != 3 * primitive_atom_count:
            raise GuardError("PH_PRODUCT_INVALID", "Mesh branch count must equal 3N for the primitive cell.")
        artifact = _artifact(_object(product, "artifact", "PH_PRODUCT_INVALID"), "PH_PRODUCT_INVALID")
        product_summary["mesh"] = {"parameters": parameters, "dimensions": {"qpoints": qpoints, "branches": 3 * primitive_atom_count}, "artifact": artifact}

    if "band" in products:
        product = _object(products, "band", "PH_PRODUCT_INVALID")
        check_fc_parent(product)
        parameters = _object(product, "parameters", "PH_PRODUCT_INVALID")
        segments = parameters.get("segments")
        if not isinstance(segments, list) or not segments:
            raise GuardError("PH_PRODUCT_INVALID", "Band segments must be a nonempty list.")
        normalized_segments: list[list[list[float]]] = []
        for segment in segments:
            if not isinstance(segment, list) or len(segment) != 2:
                raise GuardError("PH_PRODUCT_INVALID", "Each band segment must have two q points.")
            normalized_segments.append([
                _vector(segment[0], 3, "Band q point must contain three finite values.", "PH_PRODUCT_INVALID"),
                _vector(segment[1], 3, "Band q point must contain three finite values.", "PH_PRODUCT_INVALID"),
            ])
        points_per_segment = _positive_int(parameters.get("points_per_segment"), "Band points_per_segment must be positive.", "PH_PRODUCT_INVALID")
        if parameters.get("frequency_unit") not in {"THz", "cm-1", "meV"}:
            raise GuardError("PH_PRODUCT_INVALID", "Band frequency unit is unsupported.")
        dimensions = _object(product, "dimensions", "PH_PRODUCT_INVALID")
        points = _positive_int(dimensions.get("points"), "Band point count must be positive.", "PH_PRODUCT_INVALID")
        if points != len(normalized_segments) * points_per_segment:
            raise GuardError("PH_PRODUCT_INVALID", "Band point count must close against segments times points_per_segment.")
        if dimensions.get("branches") != 3 * primitive_atom_count:
            raise GuardError("PH_PRODUCT_INVALID", "Band branch count must equal 3N for the primitive cell.")
        artifact = _artifact(_object(product, "artifact", "PH_PRODUCT_INVALID"), "PH_PRODUCT_INVALID")
        product_summary["band"] = {"parameters": {"segments": normalized_segments, "points_per_segment": points_per_segment, "frequency_unit": parameters["frequency_unit"]}, "dimensions": {"points": points, "branches": 3 * primitive_atom_count}, "artifact": artifact}

    if "dos" in products:
        if "mesh" not in product_summary:
            raise GuardError("PH_PRODUCT_INVALID", "DOS requires a validated mesh product.")
        product = _object(products, "dos", "PH_PRODUCT_INVALID")
        check_fc_parent(product)
        if _hash(product, "parent_mesh_sha256", "PH_PRODUCT_INVALID") != product_summary["mesh"]["artifact"]["sha256"]:
            raise GuardError("PH_PRODUCT_PARENT_MISMATCH", "DOS binds to a different mesh artifact.")
        parameters = _object(product, "parameters", "PH_PRODUCT_INVALID")
        if parameters.get("method") not in {"tetrahedron", "gaussian"}:
            raise GuardError("PH_PRODUCT_INVALID", "DOS integration method is unsupported.")
        if parameters.get("frequency_unit") not in {"THz", "cm-1", "meV"}:
            raise GuardError("PH_PRODUCT_INVALID", "DOS frequency unit is unsupported.")
        dimensions = _object(product, "dimensions", "PH_PRODUCT_INVALID")
        bins = _positive_int(dimensions.get("bins"), "DOS bin count must be positive.", "PH_PRODUCT_INVALID")
        artifact = _artifact(_object(product, "artifact", "PH_PRODUCT_INVALID"), "PH_PRODUCT_INVALID")
        product_summary["dos"] = {"parameters": parameters, "dimensions": {"bins": bins}, "artifact": artifact}

    if "nac" in products:
        product = _object(products, "nac", "PH_NAC_INVALID")
        check_fc_parent(product)
        parameters = _object(product, "parameters", "PH_NAC_INVALID")
        born = parameters.get("born_effective_charges")
        if not isinstance(born, list) or len(born) != primitive_atom_count:
            raise GuardError("PH_NAC_INVALID", "Born charges must contain one 3x3 tensor per primitive-cell atom.")
        normalized_born = [_tensor3(tensor, "Born charge tensor must be finite 3x3.", "PH_NAC_INVALID") for tensor in born]
        dielectric = _tensor3(parameters.get("dielectric_tensor"), "Dielectric tensor must be finite 3x3.", "PH_NAC_INVALID")
        method = _text(parameters, "method", "PH_NAC_INVALID", safe=True)
        if method not in {"gonze", "wang"}:
            raise GuardError("PH_NAC_INVALID", "NAC method is unsupported.")
        factor = _finite(parameters.get("factor"), "NAC factor must be finite.", "PH_NAC_INVALID")
        if factor <= 0:
            raise GuardError("PH_NAC_INVALID", "NAC factor must be positive.")
        convention = _text(parameters, "factor_unit_convention", "PH_NAC_INVALID", safe=True)
        source = _object(product, "source", "PH_NAC_INVALID")
        source_id = _text(source, "record_id", "PH_NAC_INVALID", safe=True)
        source_hash = _hash(source, "sha256", "PH_NAC_INVALID")
        source_fingerprint = _fingerprint(source, "structure_fingerprint", "PH_NAC_INVALID")
        if source_fingerprint != fingerprint:
            raise GuardError("PH_NAC_INVALID", "NAC source has a different structure fingerprint.")
        if source.get("completion") != "complete":
            raise GuardError("PH_NAC_INVALID", "NAC source calculation must be explicitly complete.")
        source_primitive_fingerprint = _fingerprint(source, "primitive_fingerprint", "PH_NAC_INVALID")
        if source_primitive_fingerprint != primitive_fingerprint:
            raise GuardError("PH_NAC_INVALID", "NAC source has a different primitive fingerprint.")
        if source.get("response_acceptance") != "pass":
            raise GuardError("PH_NAC_INVALID", "NAC response evidence must explicitly pass acceptance.")
        source_projection_hash = _hash(source, "evidence_projection_sha256", "PH_NAC_INVALID")
        source_projection = {
            "raw_record_sha256": source_hash,
            "record_id": source_id,
            "structure_fingerprint": source_fingerprint,
            "primitive_fingerprint": source_primitive_fingerprint,
            "completion": "complete",
            "response_acceptance": "pass",
        }
        if _canonical_sha(source_projection) != source_projection_hash:
            raise GuardError("PH_NAC_INVALID", "NAC raw record hash and semantic evidence projection are detached.")
        artifact = _artifact(_object(product, "artifact", "PH_NAC_INVALID"), "PH_NAC_INVALID")
        product_summary["nac"] = {
            "parameters": {"born_effective_charges": normalized_born, "dielectric_tensor": dielectric, "method": method, "factor": factor, "factor_unit_convention": convention},
            "source": {"record_id": source_id, "sha256": source_hash, "structure_fingerprint": source_fingerprint, "primitive_fingerprint": source_primitive_fingerprint, "completion": "complete", "response_acceptance": "pass", "evidence_projection_sha256": source_projection_hash},
            "artifact": artifact,
        }

    return {
        "workflow_id": workflow_id,
        "phonopy": {"version": version, "package_sha256": package_hash},
        "structure": {"fingerprint": fingerprint, "unitcell_sha256": unitcell_hash, "atom_count": atom_count, "primitive_fingerprint": primitive_fingerprint, "primitive_atom_count": primitive_atom_count, "primitive_matrix": primitive_matrix},
        "displacement_set": {"id": displacement_set_id, "sha256": displacement_hash, "supercell_matrix": matrix, "supercell_atom_count": supercell_atom_count, "displacement_distance_angstrom": distance, "count": len(displacement_records), "records": displacement_records},
        "forces": {"unit": "eV/angstrom", "source_force_records_sha256": force_collection_hash, "count": len(force_records), "records": force_records},
        "force_constants": {"artifact": fc_artifact, "shape": [supercell_atom_count, supercell_atom_count, 3, 3], "calculator": calculator, "symmetrization": symmetrization, "acoustic_sum_rule": asr},
        "requested_products": requested,
        "products": product_summary,
    }


def _base(command: str, status: str, claim: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": "phonopy_guard",
        "tool_version": "1.0.0",
        "command": command,
        "status": status,
        "claim_ceiling": "no_positive_claim",
        "future_gate_ceiling": claim,
        "promotion_authorized": False,
        "execution_authorized": False,
        "findings": [],
        "limitations": [],
    }


def audit_lineage(path: Path) -> dict[str, Any]:
    manifest, digest = read_json(path)
    normalized = validate_manifest(manifest)
    report = _base("audit-lineage", "pass", "technical-phonon-workflow-lineage")
    report.update({"manifest_sha256": digest, "workflow": normalized})
    report["limitations"] = [
        "Synthetic validation establishes no real force-calculator or Phonopy integration maturity.",
        "Lineage closure does not establish numerical convergence or dynamical stability.",
    ]
    return report


def plan_stage(path: Path, stage: str) -> dict[str, Any]:
    manifest, digest = read_json(path)
    workflow = validate_manifest(manifest)
    stages = {"displacements", "force-collection", "force-constants", "mesh", "band", "dos", "nac"}
    if stage not in stages:
        raise GuardError("PH_VERSION_UNSUPPORTED", "Requested stage has no candidate planner.", blocked=True)
    matrix = workflow["displacement_set"]["supercell_matrix"]
    flattened = [str(item) for row in matrix for item in row]
    required_inputs: list[str]
    expected_outputs: list[str]
    if stage == "displacements":
        argv = ["phonopy-init", "-d", "--dim", *flattened, "-c", "<unitcell-file>"]
        required_inputs = ["unitcell-file"]
        expected_outputs = ["phonopy_disp.yaml", "displaced-supercells"]
    elif stage == "force-collection":
        tokens = [f"<calculator-output:{item['id']}>" for item in workflow["displacement_set"]["records"]]
        argv = ["phonopy-init", "--sp", "-f", *tokens]
        required_inputs = ["phonopy_disp.yaml", "one-calculator-output-per-displacement"]
        expected_outputs = ["phonopy_params.yaml"]
    elif stage == "force-constants":
        argv = ["phonopy", "<phonopy-params.yaml>"]
        required_inputs = ["phonopy-params.yaml", "complete-displacement-force-dataset"]
        expected_outputs = ["force-constants-in-memory-or-declared-file"]
    elif stage == "mesh":
        product = workflow["products"].get("mesh")
        if product is None:
            raise GuardError("PH_PRODUCT_INVALID", "Mesh was not requested in this workflow.", blocked=True)
        argv = ["phonopy", "--mesh", *[str(item) for item in product["parameters"]["mesh"]], "<phonopy-params.yaml>"]
        required_inputs = ["phonopy-params.yaml", "force-constants"]
        expected_outputs = [product["artifact"]["label"]]
    elif stage == "band":
        product = workflow["products"].get("band")
        if product is None:
            raise GuardError("PH_PRODUCT_INVALID", "Band was not requested in this workflow.", blocked=True)
        coordinates = ",".join(" ".join(str(value) for point in segment for value in point) for segment in product["parameters"]["segments"])
        argv = ["phonopy", "--band", coordinates, "--band-points", str(product["parameters"]["points_per_segment"]), "<phonopy-params.yaml>"]
        required_inputs = ["phonopy-params.yaml", "force-constants"]
        expected_outputs = [product["artifact"]["label"]]
    elif stage == "dos":
        product = workflow["products"].get("dos")
        mesh = workflow["products"].get("mesh")
        if product is None or mesh is None:
            raise GuardError("PH_PRODUCT_INVALID", "DOS requires requested DOS and mesh products.", blocked=True)
        argv = ["phonopy", "--mesh", *[str(item) for item in mesh["parameters"]["mesh"]], "--dos", "<phonopy-params.yaml>"]
        required_inputs = ["phonopy-params.yaml", "force-constants", "mesh-parameters"]
        expected_outputs = [product["artifact"]["label"]]
    else:
        product = workflow["products"].get("nac")
        if product is None:
            raise GuardError("PH_NAC_INVALID", "NAC was not requested in this workflow.", blocked=True)
        argv = ["phonopy", "--mesh", "<mesh-n1>", "<mesh-n2>", "<mesh-n3>", "<phonopy-params-with-nac.yaml>"]
        required_inputs = ["phonopy-params-with-nac.yaml", "force-constants", "born-and-dielectric-parameters"]
        expected_outputs = [product["artifact"]["label"]]
    report = _base("plan-stage", "pass", "dry-run-stage-plan-only")
    report.update(
        {
            "manifest_sha256": digest,
            "workflow_id": workflow["workflow_id"],
            "profile": "phonopy-4.3.1",
            "stage": stage,
            "dry_run": True,
            "execution_performed": False,
            "argv_template": argv,
            "required_inputs": required_inputs,
            "expected_outputs": expected_outputs,
            "overwrite_policy": "fresh-directory-or-refuse-existing",
        }
    )
    report["limitations"] = ["The plan contains placeholders and is never executed by this candidate.", "Parent calculator acceptance remains the responsibility of its calculation Skill."]
    return report


def _read_text(path: Path) -> tuple[str, str, int]:
    raw = _read_bounded_file(path, MAX_TEXT_BYTES, "PH_TABLE_INVALID", "frequency table")
    if raw.startswith(b"\xef\xbb\xbf") or b"\x00" in raw:
        raise GuardError("PH_TABLE_INVALID", "Frequency table is oversized or contains forbidden bytes.")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GuardError("PH_TABLE_INVALID", "Frequency table is not strict UTF-8.") from exc
    return text, hashlib.sha256(raw).hexdigest(), len(raw)


def parse_frequency_table(manifest_path: Path, table_path: Path) -> dict[str, Any]:
    manifest, manifest_hash = read_json(manifest_path)
    workflow = validate_manifest(manifest)
    text, table_hash, table_bytes = _read_text(table_path)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise GuardError("PH_TABLE_INVALID", "Frequency table is incomplete.")
    header_re = re.compile(r"^# phonopy_frequency_table_v1 kind=(band|mesh) unit=(THz|cm-1|meV) parent_force_constants_sha256=([0-9a-f]{64})$")
    header = header_re.fullmatch(lines[0])
    if header is None or sum(1 for line in lines if line.startswith("# phonopy_frequency_table_v1")) != 1:
        raise GuardError("PH_TABLE_INVALID", "Frequency-table header is missing, duplicated, or unsupported.")
    kind, unit, parent_hash = header.groups()
    if kind not in workflow["products"]:
        raise GuardError("PH_PRODUCT_INVALID", "Frequency-table kind was not requested by the workflow.")
    product = workflow["products"][kind]
    if table_hash != product["artifact"]["sha256"] or table_bytes != product["artifact"]["bytes"]:
        raise GuardError("PH_TABLE_INVALID", "Frequency-table bytes do not match the product artifact record.")
    if unit != product["parameters"]["frequency_unit"]:
        raise GuardError("PH_TABLE_INVALID", "Frequency-table unit differs from the product parameter lineage.")
    if parent_hash != workflow["force_constants"]["artifact"]["sha256"]:
        raise GuardError("PH_PRODUCT_PARENT_MISMATCH", "Frequency table binds to a different force-constants artifact.")
    branches = 3 * workflow["structure"]["primitive_atom_count"]
    rows: list[dict[str, Any]] = []
    row_re = re.compile(r"^(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$")
    current_point = 0
    current_q: list[float] | None = None
    current_weight: float | None = None
    expected_mode = 0
    for line in lines[1:]:
        match = row_re.fullmatch(line)
        if match is None:
            raise GuardError("PH_TABLE_INVALID", "Frequency table contains an invalid row.")
        point = int(match.group(1))
        mode = int(match.group(2))
        try:
            values = [float(match.group(index)) for index in range(3, 8)]
        except ValueError as exc:
            raise GuardError("PH_TABLE_INVALID", "Frequency row contains a nonnumeric value.") from exc
        if not all(math.isfinite(value) for value in values):
            raise GuardError("PH_TABLE_INVALID", "Frequency row contains a non-finite value.")
        q = values[:3]
        frequency, weight = values[3], values[4]
        if point == current_point + 1:
            if current_point and expected_mode != branches:
                raise GuardError("PH_TABLE_INVALID", "Previous point does not contain exactly 3N modes.")
            current_point = point
            expected_mode = 1
            current_q = q
            current_weight = weight
        elif point == current_point:
            expected_mode += 1
            if current_q != q or current_weight != weight:
                raise GuardError("PH_TABLE_INVALID", "Rows for one point disagree on q coordinate or weight.")
        else:
            raise GuardError("PH_TABLE_INVALID", "Point indices are not contiguous and grouped.")
        if mode != expected_mode or mode > branches or weight < 0:
            raise GuardError("PH_TABLE_INVALID", "Mode indices or point weights are invalid.")
        rows.append({"point_index": point, "mode_index": mode, "q_reduced": q, "frequency": frequency, "weight": weight})
    if current_point == 0 or expected_mode != branches:
        raise GuardError("PH_TABLE_INVALID", "Final point does not contain exactly 3N modes.")
    observed_q = [row["q_reduced"] for row in rows if row["mode_index"] == 1]
    expected_points = product["dimensions"]["points"] if kind == "band" else product["dimensions"]["qpoints"]
    if current_point != expected_points:
        raise GuardError("PH_TABLE_INVALID", "Frequency-table point count differs from the product dimensions.")
    if kind == "band":
        points_per_segment = product["parameters"]["points_per_segment"]
        expected_q: list[list[float]] = []
        for start, end in product["parameters"]["segments"]:
            for index in range(points_per_segment):
                fraction = 0.0 if points_per_segment == 1 else index / (points_per_segment - 1)
                expected_q.append([left + fraction * (right - left) for left, right in zip(start, end)])
        if len(expected_q) != len(observed_q) or any(
            any(not math.isclose(left, right, rel_tol=1.0e-10, abs_tol=1.0e-12) for left, right in zip(expected, observed))
            for expected, observed in zip(expected_q, observed_q)
        ):
            raise GuardError("PH_TABLE_INVALID", "Band-table q coordinates differ from the declared sampled path.")
    if kind == "mesh" and math.fsum(row["weight"] for row in rows if row["mode_index"] == 1) <= 0:
        raise GuardError("PH_TABLE_INVALID", "Mesh weights must have a positive sum.")
    report = _base("parse-frequency-table", "pass", "technical-frequency-table-normalization")
    report.update(
        {
            "manifest_sha256": manifest_hash,
            "dataset": {
                "schema_version": "phonopy-frequency-table@1.0",
                "maturity": "synthetic-validated",
                "kind": kind,
                "unit": unit,
                "parent_force_constants_sha256": parent_hash,
                "table_sha256": table_hash,
                "table_bytes": table_bytes,
                "structure_fingerprint": workflow["structure"]["fingerprint"],
                "points": current_point,
                "branches": branches,
                "rows": rows,
                "imaginary_frequency_count": sum(1 for row in rows if row["frequency"] < 0),
                "validation": {"finite_values": "pass", "q_mode_dimensions": "pass", "parent_lineage": "pass"},
            },
        }
    )
    report["limitations"] = ["Negative frequencies remain signed and are not an automatic instability conclusion.", "The interchange parser is not a native phonopy YAML/HDF5 parser."]
    return report


def _handoff_artifact(value: Any, code: str, description: str, *, byte_count: bool = False) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GuardError(code, f"{description} must be an object.")
    expected = {"role", "label", "sha256", "bytes"} if byte_count else {"role", "label", "sha256"}
    _exact_keys(value, expected, code, description)
    role = _text(value, "role", code, safe=True)
    label = _text(value, "label", code)
    if Path(label).name != label or not SAFE_LABEL.fullmatch(label):
        raise GuardError(code, f"{description} label must be a safe basename.")
    result: dict[str, Any] = {"role": role, "label": label, "sha256": _hash(value, "sha256", code)}
    if byte_count:
        result["bytes"] = _positive_int(value.get("bytes"), f"{description} bytes must be positive.", code)
    return result


def _validate_run_manifest_parent(manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[tuple[str, str], str]]:
    code = "PH_PARENT_RUN_MANIFEST_INVALID"
    _exact_keys(
        manifest,
        {
            "schema_version",
            "record_id",
            "code",
            "code_version",
            "task_type",
            "case_id",
            "scientific_protocol_id",
            "status",
            "scientific_acceptance",
            "configuration",
            "metrics",
            "evidence",
            "limitations",
            "provenance",
        },
        code,
        "run-manifest@1.0",
    )
    if manifest.get("schema_version") != "1.0":
        raise GuardError(code, "Parent run manifest must use schema_version 1.0.")
    record_id = _text(manifest, "record_id", code, safe=True)
    parent_code = _text(manifest, "code", code, safe=True)
    if parent_code not in {"qe", "vasp", "cp2k", "siesta"}:
        raise GuardError(code, "Parent run manifest code is outside the active contract.")
    code_version = _text(manifest, "code_version", code, safe=True)
    task_type = _text(manifest, "task_type", code, safe=True)
    case_id = _text(manifest, "case_id", code, safe=True)
    protocol_id = _text(manifest, "scientific_protocol_id", code, safe=True)
    if manifest.get("status") != "completed":
        raise GuardError("PH_PARENT_AUDIT_GATE_FAILED", "Force parent run status must be completed.")
    if manifest.get("scientific_acceptance") not in {"not_assessed", "requires_human_review"}:
        raise GuardError(code, "Parent run manifest must remain immutable pre-decision evidence.")
    configuration = manifest.get("configuration")
    if not isinstance(configuration, dict):
        raise GuardError(code, "Parent run configuration must be an object.")
    handoff = configuration.get("phonopy_force_parent")
    if not isinstance(handoff, dict):
        raise GuardError(
            "PH_PARENT_MANIFEST_FIELDS_MISSING",
            "Active run manifest lacks configuration.phonopy_force_parent structure/displacement binding.",
            blocked=True,
            next_action="Add the exact workflow, structure, displacement-set, displacement, and displaced-supercell identifiers to configuration.phonopy_force_parent before emitting the immutable run manifest.",
        )
    workflow_keys = {
        "workflow_id",
        "structure_fingerprint",
        "displacement_set_id",
        "displacement_set_sha256",
        "displacement_id",
        "displaced_supercell_sha256",
        "supercell_atom_count",
    }
    _exact_keys(handoff, workflow_keys, code, "phonopy_force_parent configuration")
    evidence_value = manifest.get("evidence")
    if not isinstance(evidence_value, list) or not evidence_value or len(evidence_value) > 1000:
        raise GuardError(code, "Parent run evidence must be a bounded nonempty list.")
    evidence: dict[tuple[str, str], str] = {}
    for item in evidence_value:
        if not isinstance(item, dict) or not set(item).issubset({"role", "label", "status", "sha256"}):
            raise GuardError(code, "Every run-manifest evidence item must follow the active contract.")
        role = _text(item, "role", code, safe=True)
        label = _text(item, "label", code)
        if Path(label).name != label or not SAFE_LABEL.fullmatch(label):
            raise GuardError(code, "Run-manifest evidence labels must be safe basenames.")
        key = (role, label)
        if key in evidence:
            raise GuardError(code, "Run-manifest evidence role/label pairs must be unique.")
        if item.get("status") == "present":
            evidence[key] = _hash(item, "sha256", code)
    return (
        {
            "record_id": record_id,
            "code": parent_code,
            "code_version": code_version,
            "task_type": task_type,
            "case_id": case_id,
            "scientific_protocol_id": protocol_id,
            "handoff": handoff,
        },
        evidence,
    )


def _require_artifact_binding(
    artifact: dict[str, Any],
    evidence: dict[tuple[str, str], str],
) -> None:
    if evidence.get((artifact["role"], artifact["label"])) != artifact["sha256"]:
        raise GuardError(
            "PH_PARENT_ARTIFACT_MISMATCH",
            "Handoff artifact role/label/hash is absent from or differs from run-manifest evidence.",
        )


def _normalized_version(value: str, code: str) -> str:
    normalized = value.strip().casefold()
    for prefix in ("vasp.", "qe-", "v.", "v"):
        if normalized.startswith(prefix) and len(normalized) > len(prefix):
            normalized = normalized[len(prefix) :]
            break
    if not normalized:
        raise GuardError(code, "Audit software version is empty.")
    return normalized


def _audit_qe_force_parent(
    audit: dict[str, Any],
    parent: dict[str, Any],
    request: dict[str, Any],
) -> tuple[str, str]:
    code = "PH_PARENT_AUDIT_INVALID"
    _exact_keys(
        audit,
        {
            "schema_version",
            "scope",
            "decision",
            "scientific_claim_decision",
            "gates",
            "summary",
            "output_summary",
            "evidence",
            "findings",
            "required_remaining_gates",
            "provenance",
        },
        code,
        "QE audit report",
    )
    provenance = _object(audit, "provenance", code)
    if audit.get("schema_version") != "1.0" or provenance.get("collector") != "qe_guard" or provenance.get("collector_version") != "1.0.0":
        raise GuardError(code, "QE audit does not identify the active qe_guard@1.0.0 producer/schema.")
    if audit.get("scope") != "pw.x input and output" or audit.get("scientific_claim_decision") != "blocked":
        raise GuardError(code, "QE audit scope or scientific-claim boundary differs from the active report contract.")
    summary = _object(audit, "summary", code)
    output_summary = _object(audit, "output_summary", code)
    if summary.get("executable") != "pw.x" or summary.get("calculation") != parent["task_type"]:
        raise GuardError("PH_PARENT_IDENTITY_MISMATCH", "QE audit calculation does not match the requested parent task.")
    if summary.get("nat") != request["workflow"]["supercell_atom_count"]:
        raise GuardError("PH_PARENT_STRUCTURE_MISMATCH", "QE audit atom count differs from the displaced supercell binding.")
    if _normalized_version(str(output_summary.get("qe_version", "")), code) != _normalized_version(parent["code_version"], code):
        raise GuardError("PH_PARENT_IDENTITY_MISMATCH", "QE output version differs from run-manifest code_version.")
    gates = _object(audit, "gates", code)
    expected_gate_names = {
        "plan",
        "input_integrity",
        "pseudopotential_provenance",
        "official_version_match",
        "parent_ancestry",
        "runtime_paths",
        "execution_completion",
        "observable_convergence",
        "physical_validity",
    }
    if set(gates) != expected_gate_names:
        raise GuardError(code, "QE audit gate set differs from the active schema; self-declared extra gates are rejected.")
    required = expected_gate_names - {"observable_convergence", "physical_validity"}
    if audit.get("decision") != "pass" or any(gates.get(name) != "pass" for name in required):
        raise GuardError("PH_PARENT_AUDIT_GATE_FAILED", "QE technical input/output/completion gates do not all pass.")
    cycles = output_summary.get("successful_scf_cycles")
    if not isinstance(cycles, int) or isinstance(cycles, bool) or cycles <= 0:
        raise GuardError("PH_PARENT_AUDIT_GATE_FAILED", "QE audit does not demonstrate a successful electronic SCF cycle.")
    evidence = _object(audit, "evidence", code)
    input_record = _object(evidence, "input", code)
    output_record = _object(evidence, "output", code)
    if input_record.get("role") != "pw_input" or output_record.get("role") != "pw_output":
        raise GuardError(code, "QE audit input/output roles differ from the active contract.")
    input_hash = _hash(input_record, "sha256", code)
    output_hash = _hash(output_record, "sha256", code)
    if input_hash != request["artifacts"]["input"]["sha256"] or output_hash != request["artifacts"]["output"]["sha256"]:
        raise GuardError("PH_PARENT_ARTIFACT_MISMATCH", "QE audit input/output hashes differ from the handoff artifacts.")
    return input_hash, output_hash


def _audit_vasp_force_parent(
    audit: dict[str, Any],
    parent: dict[str, Any],
    request: dict[str, Any],
) -> tuple[str, str]:
    code = "PH_PARENT_AUDIT_INVALID"
    _exact_keys(
        audit,
        {
            "audit_schema_version",
            "auditor",
            "mode",
            "task_type",
            "case_id",
            "files",
            "findings",
            "official_source_coverage",
            "gates",
            "verdict",
            "summary",
        },
        code,
        "VASP audit report",
    )
    if audit.get("audit_schema_version") != "2.0" or audit.get("auditor") != "audit_vasp_case.py" or audit.get("mode") != "run":
        raise GuardError(code, "VASP audit does not identify the active run-mode schema-2.0 producer.")
    if audit.get("task_type") != parent["task_type"] or audit.get("case_id") != parent["case_id"]:
        raise GuardError("PH_PARENT_IDENTITY_MISMATCH", "VASP audit task/case differs from the run manifest.")
    gates = _object(audit, "gates", code)
    expected_gate_names = {
        "input_integrity",
        "input_reproducibility",
        "execution_completion",
        "electronic_convergence",
        "ionic_convergence",
        "output_warnings",
        "version_identity",
        "local_official_source_coverage",
        "task_specific_validation",
        "numerical_convergence",
        "physical_validity",
        "scientific_claim",
    }
    if set(gates) != expected_gate_names:
        raise GuardError(code, "VASP audit gate set differs from the active schema; self-declared extra gates are rejected.")
    required = {
        "input_integrity",
        "input_reproducibility",
        "execution_completion",
        "electronic_convergence",
        "ionic_convergence",
        "output_warnings",
        "version_identity",
    }
    if audit.get("verdict") != "technical_run_gates_passed_scientific_claim_blocked" or any(
        gates.get(name) not in {"pass", "not_applicable"} for name in required
    ):
        raise GuardError("PH_PARENT_AUDIT_GATE_FAILED", "VASP technical run gates do not all pass.")
    files = _object(audit, "files", code)
    incar = _object(files, "INCAR", code)
    poscar = _object(files, "POSCAR", code)
    outcar = _object(files, "OUTCAR", code)
    if poscar.get("atom_count") != request["workflow"]["supercell_atom_count"]:
        raise GuardError("PH_PARENT_STRUCTURE_MISMATCH", "VASP audit atom count differs from the displaced supercell binding.")
    if _hash(poscar, "sha256", code) != request["artifacts"]["displaced_structure"]["sha256"]:
        raise GuardError("PH_PARENT_STRUCTURE_MISMATCH", "VASP POSCAR hash differs from the displaced-supercell artifact.")
    if _normalized_version(str(outcar.get("version", "")), code) != _normalized_version(parent["code_version"], code):
        raise GuardError("PH_PARENT_IDENTITY_MISMATCH", "VASP OUTCAR version differs from run-manifest code_version.")
    input_hash = _hash(incar, "sha256", code)
    output_hash = _hash(outcar, "sha256", code)
    if input_hash != request["artifacts"]["input"]["sha256"] or output_hash != request["artifacts"]["output"]["sha256"]:
        raise GuardError("PH_PARENT_ARTIFACT_MISMATCH", "VASP audit input/output hashes differ from the handoff artifacts.")
    return input_hash, output_hash


def audit_parent_handoff(run_manifest_path: Path, audit_report_path: Path, request_path: Path) -> dict[str, Any]:
    manifest, manifest_hash, manifest_bytes = _read_json_evidence(
        run_manifest_path,
        "PH_PARENT_RUN_MANIFEST_INVALID",
        "parent run manifest",
    )
    audit, audit_hash, audit_bytes = _read_json_evidence(
        audit_report_path,
        "PH_PARENT_AUDIT_INVALID",
        "parent audit report",
    )
    request, request_hash, request_bytes = _read_json_evidence(
        request_path,
        "PH_PARENT_HANDOFF_MISMATCH",
        "parent handoff request",
    )
    request_code = "PH_PARENT_HANDOFF_MISMATCH"
    _exact_keys(request, {"schema_version", "request_id", "workflow", "expected_parent", "artifacts"}, request_code, "Phonopy parent handoff request")
    if request.get("schema_version") != "phonopy-parent-handoff-request@1.0-candidate":
        raise GuardError(request_code, "Unsupported Phonopy parent handoff request schema.")
    request_id = _text(request, "request_id", request_code, safe=True)
    workflow = _object(request, "workflow", request_code)
    workflow_keys = {
        "workflow_id",
        "structure_fingerprint",
        "displacement_set_id",
        "displacement_set_sha256",
        "displacement_id",
        "displaced_supercell_sha256",
        "supercell_atom_count",
    }
    _exact_keys(workflow, workflow_keys, request_code, "Handoff workflow binding")
    normalized_workflow = {
        "workflow_id": _text(workflow, "workflow_id", request_code, safe=True),
        "structure_fingerprint": _fingerprint(workflow, "structure_fingerprint", request_code),
        "displacement_set_id": _text(workflow, "displacement_set_id", request_code, safe=True),
        "displacement_set_sha256": _hash(workflow, "displacement_set_sha256", request_code),
        "displacement_id": _text(workflow, "displacement_id", request_code, safe=True),
        "displaced_supercell_sha256": _hash(workflow, "displaced_supercell_sha256", request_code),
        "supercell_atom_count": _positive_int(workflow.get("supercell_atom_count"), "Supercell atom count must be positive.", request_code),
    }
    expected = _object(request, "expected_parent", request_code)
    _exact_keys(
        expected,
        {
            "record_id",
            "code",
            "code_version",
            "task_type",
            "case_id",
            "scientific_protocol_id",
            "run_manifest_sha256",
            "audit_report_sha256",
        },
        request_code,
        "Expected parent identity",
    )
    expected_parent = {
        "record_id": _text(expected, "record_id", request_code, safe=True),
        "code": _text(expected, "code", request_code, safe=True),
        "code_version": _text(expected, "code_version", request_code, safe=True),
        "task_type": _text(expected, "task_type", request_code, safe=True),
        "case_id": _text(expected, "case_id", request_code, safe=True),
        "scientific_protocol_id": _text(expected, "scientific_protocol_id", request_code, safe=True),
        "run_manifest_sha256": _hash(expected, "run_manifest_sha256", request_code),
        "audit_report_sha256": _hash(expected, "audit_report_sha256", request_code),
    }
    if expected_parent["run_manifest_sha256"] != manifest_hash or expected_parent["audit_report_sha256"] != audit_hash:
        raise GuardError("PH_PARENT_HANDOFF_HASH_MISMATCH", "Handoff request does not bind the exact raw run-manifest and audit-report bytes.")
    parent, manifest_evidence = _validate_run_manifest_parent(manifest)
    for key in ("record_id", "code", "code_version", "task_type", "case_id", "scientific_protocol_id"):
        if parent[key] != expected_parent[key]:
            raise GuardError("PH_PARENT_IDENTITY_MISMATCH", f"Parent {key} differs between run manifest and handoff request.")
    if parent["handoff"] != normalized_workflow:
        mismatch_code = (
            "PH_PARENT_DISPLACEMENT_MISMATCH"
            if any(parent["handoff"].get(name) != normalized_workflow[name] for name in ("displacement_set_id", "displacement_set_sha256", "displacement_id", "displaced_supercell_sha256"))
            else "PH_PARENT_STRUCTURE_MISMATCH"
        )
        raise GuardError(mismatch_code, "Run-manifest structure/displacement binding differs from the handoff request.")
    if parent["code"] in {"cp2k", "siesta"}:
        raise GuardError(
            "PH_PARENT_CODE_UNSUPPORTED",
            f"{parent['code']} force-parent audit projection is not implemented in this candidate.",
            blocked=True,
            next_action=f"Add a versioned {parent['code']} audit adapter that binds completion, electronic convergence, displaced structure, and force acceptance to exact raw evidence.",
        )
    allowed_tasks = {"qe": {"scf"}, "vasp": {"static"}}
    if parent["code"] not in allowed_tasks or parent["task_type"] not in allowed_tasks[parent["code"]]:
        raise GuardError("PH_PARENT_IDENTITY_MISMATCH", "Parent code/task is not a supported finite-displacement force route.")
    artifacts = _object(request, "artifacts", request_code)
    _exact_keys(artifacts, {"input", "output", "audit_report", "displaced_structure", "forces"}, request_code, "Handoff artifacts")
    normalized_artifacts = {
        name: _handoff_artifact(artifacts.get(name), request_code, f"{name} artifact")
        for name in ("input", "output", "audit_report", "displaced_structure")
    }
    force_value = artifacts.get("forces")
    if not isinstance(force_value, dict):
        raise GuardError(request_code, "forces artifact must be an object.")
    _exact_keys(force_value, {"role", "label", "sha256", "bytes", "shape", "unit", "source_output_sha256"}, request_code, "forces artifact")
    force_artifact = _handoff_artifact(
        {key: force_value[key] for key in ("role", "label", "sha256", "bytes")},
        request_code,
        "forces artifact",
        byte_count=True,
    )
    if force_value.get("unit") != "eV/angstrom" or force_value.get("shape") != [normalized_workflow["supercell_atom_count"], 3]:
        raise GuardError("PH_PARENT_ARTIFACT_MISMATCH", "Force unit/shape differs from the candidate force-record contract.")
    source_output_sha256 = _hash(force_value, "source_output_sha256", request_code)
    if source_output_sha256 != normalized_artifacts["output"]["sha256"]:
        raise GuardError("PH_PARENT_ARTIFACT_MISMATCH", "Force artifact is detached from the audited calculator output hash.")
    for artifact in (*normalized_artifacts.values(), force_artifact):
        _require_artifact_binding(artifact, manifest_evidence)
    if normalized_artifacts["audit_report"]["sha256"] != audit_hash:
        raise GuardError("PH_PARENT_HANDOFF_HASH_MISMATCH", "Audit artifact does not bind the exact raw audit-report bytes.")
    if normalized_artifacts["displaced_structure"]["sha256"] != normalized_workflow["displaced_supercell_sha256"]:
        raise GuardError("PH_PARENT_DISPLACEMENT_MISMATCH", "Displaced-structure artifact hash differs from the selected displacement.")
    request_view = {"workflow": normalized_workflow, "artifacts": {**normalized_artifacts, "forces": force_artifact}}
    if parent["code"] == "qe":
        input_hash, output_hash = _audit_qe_force_parent(audit, parent, request_view)
    else:
        input_hash, output_hash = _audit_vasp_force_parent(audit, parent, request_view)
    parent_projection = {
        "raw_record_sha256": manifest_hash,
        "record_id": parent["record_id"],
        "code": parent["code"],
        "code_version": parent["code_version"],
        "structure_fingerprint": normalized_workflow["structure_fingerprint"],
        "input_hash": input_hash,
        "output_hash": output_hash,
        "completion": "complete",
        "gates": {
            "input_validation": "pass",
            "output_validation": "pass",
            "electronic_convergence": "pass",
            "force_acceptance": "not_evaluated_by_active_audit",
        },
    }
    report = _base("audit-parent-handoff", "blocked", "technical-force-parent-projection")
    report.update(
        {
            "request_id": request_id,
            "local_consistency": "pass",
            "report_authentication": "unsigned-candidate-output",
            "upstream_authentication": "unresolved-no-trusted-producer-or-bundle",
            "raw_evidence": {
                "run_manifest": {"sha256": manifest_hash, "bytes": manifest_bytes},
                "audit_report": {"sha256": audit_hash, "bytes": audit_bytes},
                "handoff_request": {"sha256": request_hash, "bytes": request_bytes},
            },
            "workflow_binding": normalized_workflow,
            "force_artifact": {**force_artifact, "shape": force_value["shape"], "unit": force_value["unit"]},
            "parent_projection": parent_projection,
            "provisional_parent_projection_sha256": _canonical_sha(parent_projection),
            "eligible_for_workflow_manifest": False,
        }
    )
    report["findings"] = [
        {
            "code": "PH_PARENT_FORCE_GATE_MISSING",
            "severity": "blocker",
            "message": "The active QE/VASP audit schemas do not emit a force-artifact acceptance gate bound to displacement, unit, shape, and source output.",
            "minimum_next_action": "Extend the matching active calculation auditor and immutable run handoff to emit a deterministic force gate, then regenerate the audit and run manifest.",
        },
        {
            "code": "PH_PARENT_AUTHENTICATION_UNAVAILABLE",
            "severity": "blocker",
            "message": "Exact raw hashes establish integrity linkage but neither upstream record has trusted-producer or validated-bundle authentication.",
            "minimum_next_action": "Place the exact run manifest and audit in a validated bundle with a trusted-producer resolution record, then rerun this adapter against those immutable bytes.",
        },
    ]
    report["limitations"] = [
        "No external calculation software or Phonopy process was executed.",
        "The provisional projection must not be copied into a passing workflow manifest while either blocker remains.",
    ]
    return report


def _write_payload(handle: TextIO, payload: str) -> None:
    handle.write(payload)
    handle.flush()
    os.fsync(handle.fileno())


def _entry_stat(parent_fd: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _new_staging_file(parent_fd: int) -> tuple[int, str]:
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    for _ in range(128):
        name = f".phonopy-report-{secrets.token_hex(16)}.tmp"
        try:
            return os.open(name, flags, 0o600, dir_fd=parent_fd), name
        except FileExistsError:
            continue
    raise OSError("unable to allocate private staging name")


def _same_lexical_path(left: Path, right: Path) -> bool:
    left_name = _canonical_absolute_path(left, "PH_OUTPUT_EXISTS", "report output")
    right_name = _canonical_absolute_path(right, "PH_OUTPUT_EXISTS", "input evidence")
    return os.path.normcase(left_name) == os.path.normcase(right_name)


def write_report(
    report: dict[str, Any],
    output: Path | None,
    forbidden_inputs: tuple[Path, ...] = (),
) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if output is None:
        sys.stdout.write(payload)
        return
    if any(_same_lexical_path(output, path) for path in forbidden_inputs):
        raise GuardError("PH_OUTPUT_EXISTS", "Refusing a report path that aliases an input pathname.")
    parent_fd: int | None = None
    staging_fd: int | None = None
    staging_name: str | None = None
    try:
        parent_fd, output_name = _open_parent_dirfd(
            output,
            "PH_OUTPUT_WRITE_FAILED",
            "report output",
            create=True,
        )
        if _entry_stat(parent_fd, output_name) is not None:
            raise GuardError("PH_OUTPUT_EXISTS", "Refusing an existing or broken-symlink report target.")
        staging_fd, staging_name = _new_staging_file(parent_fd)
        before = os.fstat(staging_fd)
        with os.fdopen(staging_fd, "w", encoding="utf-8", closefd=False) as handle:
            _write_payload(handle, payload)
        staged = os.fstat(staging_fd)
        if (
            not stat.S_ISREG(staged.st_mode)
            or staged.st_nlink != 1
            or staged.st_dev != before.st_dev
            or staged.st_ino != before.st_ino
            or staged.st_size != len(payload.encode("utf-8"))
        ):
            raise GuardError("PH_OUTPUT_WRITE_FAILED", "Staging identity changed before publication.")
        try:
            os.link(
                staging_name,
                output_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise GuardError("PH_OUTPUT_EXISTS", "Refusing an existing or raced report target.") from exc
        published = _entry_stat(parent_fd, output_name)
        linked_stage = os.fstat(staging_fd)
        if (
            published is None
            or not stat.S_ISREG(published.st_mode)
            or (published.st_dev, published.st_ino) != (staged.st_dev, staged.st_ino)
            or (linked_stage.st_dev, linked_stage.st_ino) != (staged.st_dev, staged.st_ino)
            or published.st_nlink != 2
            or linked_stage.st_nlink != 2
        ):
            raise GuardError("PH_OUTPUT_WRITE_FAILED", "Published report is detached from the verified staging inode.")
        os.unlink(staging_name, dir_fd=parent_fd)
        staging_name = None
        final = _entry_stat(parent_fd, output_name)
        if final is None or (final.st_dev, final.st_ino) != (staged.st_dev, staged.st_ino) or final.st_nlink != 1:
            raise GuardError("PH_OUTPUT_WRITE_FAILED", "Published report identity changed during finalization.")
        os.fsync(parent_fd)
    except GuardError:
        raise
    except (OSError, UnicodeError) as exc:
        raise GuardError("PH_OUTPUT_WRITE_FAILED", "Report could not be durably published.") from exc
    finally:
        if staging_name is not None and parent_fd is not None:
            try:
                os.unlink(staging_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        if staging_fd is not None:
            os.close(staging_fd)
        if parent_fd is not None:
            os.close(parent_fd)


def error_report(command: str, exc: GuardError) -> dict[str, Any]:
    report = _base(command, "blocked" if exc.blocked else "fail", "none")
    report["findings"] = [{"code": exc.code, "severity": "blocker" if exc.blocked else "error", "message": exc.message}]
    report["smallest_next_action"] = exc.next_action or (
        "Supply the exact missing version/task/evidence without weakening the gate."
        if exc.blocked
        else "Correct the reported evidence defect and rerun."
    )
    return report


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit-lineage")
    audit.add_argument("--manifest", type=Path, required=True)
    audit.add_argument("--out", type=Path)
    plan = sub.add_parser("plan-stage")
    plan.add_argument("--manifest", type=Path, required=True)
    plan.add_argument("--stage", required=True)
    plan.add_argument("--out", type=Path)
    table = sub.add_parser("parse-frequency-table")
    table.add_argument("--manifest", type=Path, required=True)
    table.add_argument("--table", type=Path, required=True)
    table.add_argument("--out", type=Path)
    parent = sub.add_parser("audit-parent-handoff")
    parent.add_argument("--run-manifest", type=Path, required=True)
    parent.add_argument("--audit-report", type=Path, required=True)
    parent.add_argument("--handoff-request", type=Path, required=True)
    parent.add_argument("--out", type=Path)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    forbidden_inputs = tuple(
        value
        for name in ("manifest", "table", "run_manifest", "audit_report", "handoff_request")
        if isinstance((value := getattr(args, name, None)), Path)
    )
    try:
        if args.command == "audit-lineage":
            report = audit_lineage(args.manifest)
        elif args.command == "plan-stage":
            report = plan_stage(args.manifest, args.stage)
        elif args.command == "audit-parent-handoff":
            report = audit_parent_handoff(args.run_manifest, args.audit_report, args.handoff_request)
        else:
            report = parse_frequency_table(args.manifest, args.table)
        write_report(report, args.out, forbidden_inputs)
        return 3 if report.get("status") == "blocked" else 0
    except GuardError as exc:
        report = error_report(args.command, exc)
        try:
            write_report(report, args.out, forbidden_inputs)
        except GuardError:
            sys.stdout.write(json.dumps(report, sort_keys=True, allow_nan=False) + "\n")
        return 3 if exc.blocked else 2
    except Exception:
        report = _base(args.command, "fail", "none")
        report["findings"] = [{"code": "PH_INTERNAL_ERROR", "severity": "error", "message": "Unexpected internal error."}]
        sys.stdout.write(json.dumps(report, sort_keys=True, allow_nan=False) + "\n")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
