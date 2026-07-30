#!/usr/bin/env python3
"""Deterministic, fail-closed structure preparation candidate CLI."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import sys
from typing import Any


EXIT_OK = 0
EXIT_BLOCKED = 2
EXIT_UNAVAILABLE = 3
EXIT_INTERNAL = 4
MAX_JSON_BYTES = 5 * 1024 * 1024
MAX_DERIVED_SITES = 4096
MAX_PERIODIC_IMAGE_EVALUATIONS = 1_000_000
MANIFEST_PUBLIC_CARTESIAN_TOLERANCE_ANG = 1.0e-5
MIN_SURFACE_NORMAL_ALIGNMENT = 0.999999
TOOL_VERSION = "0.3.0-candidate"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
ELEMENTS = (
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn "
    "Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce "
    "Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn "
    "Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc "
    "Lv Ts Og"
).split()
ATOMIC_NUMBER = {symbol: index + 1 for index, symbol in enumerate(ELEMENTS)}
EXPECTED_DISTRIBUTIONS = {
    "ase": "3.29.0",
    "pymatgen": "2026.5.4",
    "pymatgen-core": "2026.5.18",
    "rdkit": "2026.03.4",
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
        "contract_name": "structure-preparation-error",
        "schema_version": "1.0",
        "status": status,
        "finding_id": finding_id,
        "message": message,
        **candidate_lifecycle("input_gates_only"),
        "provenance": {
            "tool": "structure_prepare.py",
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


def load_json(path_text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(path_text)
    try:
        info = path.lstat()
    except OSError as exc:
        raise GateError("INPUT_UNREADABLE", "input is not a readable regular file") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise GateError("INPUT_NOT_REGULAR", "symlinks and non-regular inputs are refused")
    if info.st_size > MAX_JSON_BYTES:
        raise GateError("INPUT_TOO_LARGE", f"JSON input exceeds {MAX_JSON_BYTES} bytes")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise GateError("INPUT_UNREADABLE", "input could not be opened safely") from exc
    try:
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode) or _stat_identity(opened) != _stat_identity(info):
                raise GateError("INPUT_CHANGED_DURING_READ", "input identity changed before read")
            raw = handle.read(MAX_JSON_BYTES + 1)
            finished = os.fstat(handle.fileno())
    except GateError:
        raise
    except OSError as exc:
        raise GateError("INPUT_UNREADABLE", "input could not be read safely") from exc
    if len(raw) > MAX_JSON_BYTES:
        raise GateError("INPUT_TOO_LARGE", f"JSON input exceeds {MAX_JSON_BYTES} bytes")
    try:
        final_path = path.lstat()
    except OSError as exc:
        raise GateError("INPUT_CHANGED_DURING_READ", "input path disappeared during read") from exc
    if (
        _stat_identity(finished) != _stat_identity(opened)
        or _stat_identity(final_path) != _stat_identity(opened)
        or len(raw) != finished.st_size
        or stat.S_ISLNK(final_path.st_mode)
    ):
        raise GateError("INPUT_CHANGED_DURING_READ", "input path or link identity changed during read")
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise GateError("JSON_INVALID", "input must be strict, duplicate-free UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise GateError("JSON_ROOT_INVALID", "JSON root must be an object")
    sha256 = hashlib.sha256(raw).hexdigest()
    return value, {
        "label": privacy_safe_label(path, sha256),
        "bytes": len(raw),
        "sha256": sha256,
    }


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


def write_json(value: dict[str, Any], path_text: str | None) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
    if path_text is None:
        sys.stdout.write(rendered)
        return
    path = Path(path_text)
    parent = path.parent
    if not path.name or path.name in {".", ".."}:
        raise GateError("OUTPUT_PATH_INVALID", "output must name a new regular file")
    if not all(function in os.supports_dir_fd for function in (os.open, os.stat, os.link, os.unlink)):
        raise GateError(
            "ATOMIC_OUTPUT_UNAVAILABLE",
            "this platform lacks the directory-descriptor operations required for safe atomic publish",
        )
    try:
        parent_info = parent.lstat()
    except OSError as exc:
        raise GateError("OUTPUT_PARENT_INVALID", "output parent must already exist") from exc
    if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
        raise GateError("OUTPUT_PARENT_INVALID", "symlinked or non-directory output parents are refused")
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
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


def _keys(value: dict[str, Any], required: set[str], context: str) -> None:
    actual = set(value)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        raise GateError(
            "SCHEMA_KEYS_INVALID",
            f"{context} keys mismatch; missing={missing}, extra={extra}",
        )


def _finite_number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GateError("NUMBER_INVALID", f"{context} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise GateError("NUMBER_INVALID", f"{context} must be finite")
    return number


def _vector3(value: Any, context: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise GateError("VECTOR_INVALID", f"{context} must contain exactly three numbers")
    return [_finite_number(item, context) for item in value]


def _matrix3(value: Any, context: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 3:
        raise GateError("MATRIX_INVALID", f"{context} must be a 3x3 matrix")
    return [_vector3(row, context) for row in value]


def determinant(matrix: list[list[float]]) -> float:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def frac_to_cart(frac: list[float], cell: list[list[float]]) -> list[float]:
    return [sum(frac[i] * cell[i][j] for i in range(3)) for j in range(3)]


def residual_norm(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((left[i] - right[i]) ** 2 for i in range(3)))


def round_float(value: float, digits: int = 12) -> float:
    rounded = round(value, digits)
    return 0.0 if rounded == 0.0 else rounded


def vector_add(left: list[float], right: list[float]) -> list[float]:
    return [left[index] + right[index] for index in range(3)]


def vector_subtract(left: list[float], right: list[float]) -> list[float]:
    return [left[index] - right[index] for index in range(3)]


def vector_scale(vector: list[float], factor: float) -> list[float]:
    return [component * factor for component in vector]


def dot(left: list[float], right: list[float]) -> float:
    return sum(left[index] * right[index] for index in range(3))


def norm(vector: list[float]) -> float:
    return math.sqrt(dot(vector, vector))


def cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def unit_vector(vector: list[float], context: str) -> list[float]:
    length = norm(vector)
    if length <= 1.0e-12:
        raise GateError("VECTOR_DEGENERATE", f"{context} has zero length")
    return vector_scale(vector, 1.0 / length)


def matrix_multiply(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [
        [sum(left[i][k] * right[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]


def row_vector_matrix(vector: list[float], matrix: list[list[float]]) -> list[float]:
    return [sum(vector[k] * matrix[k][j] for k in range(3)) for j in range(3)]


def inverse_matrix(matrix: list[list[float]]) -> list[list[float]]:
    det = determinant(matrix)
    if abs(det) <= 1.0e-12:
        raise GateError("MATRIX_SINGULAR", "matrix is singular or numerically degenerate")
    a, b, c = matrix
    cofactors = [
        [
            b[1] * c[2] - b[2] * c[1],
            -(b[0] * c[2] - b[2] * c[0]),
            b[0] * c[1] - b[1] * c[0],
        ],
        [
            -(a[1] * c[2] - a[2] * c[1]),
            a[0] * c[2] - a[2] * c[0],
            -(a[0] * c[1] - a[1] * c[0]),
        ],
        [
            a[1] * b[2] - a[2] * b[1],
            -(a[0] * b[2] - a[2] * b[0]),
            a[0] * b[1] - a[1] * b[0],
        ],
    ]
    return [[cofactors[j][i] / det for j in range(3)] for i in range(3)]


def cart_to_frac(cart: list[float], cell: list[list[float]]) -> list[float]:
    return row_vector_matrix(cart, inverse_matrix(cell))


def apply_cartesian_deformation(vector: list[float], deformation: list[list[float]]) -> list[float]:
    return [
        sum(deformation[row][column] * vector[column] for column in range(3))
        for row in range(3)
    ]


def unresolved_symmetry() -> dict[str, Any]:
    return {
        "status": "unresolved",
        "number": None,
        "symbol": None,
        "tolerance_ang": None,
        "backend": None,
        "backend_version": None,
    }


def invalidate_electronic_state(structure: dict[str, Any]) -> None:
    structure["charge_state"] = {"status": "unknown", "net_charge_e": None}
    structure["spin_state"] = {"status": "not-assessed", "multiplicity": None}


def derived_structure_id(prefix: str, structure: dict[str, Any]) -> str:
    candidate = f"{prefix}-{structure_identity(structure)['structure_sha256'][:16]}"
    if not SAFE_ID.fullmatch(candidate):
        raise GateError("DERIVED_STRUCTURE_ID_INVALID", "derived structure identifier is unsafe")
    return candidate


def validate_bounded_float(
    value: Any,
    context: str,
    *,
    minimum: float,
    maximum: float,
    include_minimum: bool = False,
) -> float:
    number = _finite_number(value, context)
    minimum_ok = number >= minimum if include_minimum else number > minimum
    if not minimum_ok or number > maximum:
        bracket = "[" if include_minimum else "("
        raise GateError(
            "PARAMETER_OUT_OF_RANGE",
            f"{context} must be in {bracket}{minimum}, {maximum}]",
        )
    return number


def periodic_basis_lower_bound(periodic_vectors: list[list[float]]) -> float:
    """Return a conservative positive lower bound for the periodic Gram spectrum."""
    dimensions = len(periodic_vectors)
    trace = sum(dot(vector, vector) for vector in periodic_vectors)
    if not math.isfinite(trace) or trace <= 0.0:
        raise GateError(
            "PERIODIC_IMAGE_SEARCH_UNSAFE",
            "a positive closest-image search bound cannot be certified for the periodic basis",
        )
    if dimensions == 1:
        raw_bound = trace
    elif dimensions == 2:
        area_vector = cross(periodic_vectors[0], periodic_vectors[1])
        raw_bound = dot(area_vector, area_vector) / trace
    elif dimensions == 3:
        volume = determinant(periodic_vectors)
        raw_bound = volume * volume / (trace * trace)
    else:
        raise GateError(
            "PERIODIC_IMAGE_SEARCH_UNSAFE",
            "periodic closest-image search requires one to three periodic axes",
        )
    if not math.isfinite(raw_bound) or raw_bound <= 0.0:
        raise GateError(
            "PERIODIC_IMAGE_SEARCH_UNSAFE",
            "a positive closest-image search bound cannot be certified for the periodic basis",
        )
    # det(G) / trace(G) ** (p - 1) is no greater than lambda_min(G).
    # Halving it keeps the integer box conservative under ordinary float roundoff.
    return raw_bound * 0.5


def continuous_periodic_shift(
    offset_cart: list[float],
    periodic_vectors: list[list[float]],
) -> list[float]:
    """Return the real-valued least-squares lattice shift for the periodic basis."""
    dimensions = len(periodic_vectors)
    projection = [dot(vector, offset_cart) for vector in periodic_vectors]
    if dimensions == 1:
        denominator = dot(periodic_vectors[0], periodic_vectors[0])
        if not math.isfinite(denominator) or denominator <= 0.0:
            raise GateError(
                "PERIODIC_IMAGE_SEARCH_UNSAFE",
                "the periodic basis is singular or numerically unsafe",
            )
        return [-projection[0] / denominator]
    if dimensions == 2:
        first, second = periodic_vectors
        first_sq = dot(first, first)
        cross_term = dot(first, second)
        second_sq = dot(second, second)
        gram_determinant = dot(cross(first, second), cross(first, second))
        if not math.isfinite(gram_determinant) or gram_determinant <= 0.0:
            raise GateError(
                "PERIODIC_IMAGE_SEARCH_UNSAFE",
                "the periodic basis is singular or numerically unsafe",
            )
        return [
            -(second_sq * projection[0] - cross_term * projection[1])
            / gram_determinant,
            -(-cross_term * projection[0] + first_sq * projection[1])
            / gram_determinant,
        ]
    if dimensions == 3:
        coefficients = cart_to_frac(offset_cart, periodic_vectors)
        return [-value for value in coefficients]
    raise GateError(
        "PERIODIC_IMAGE_SEARCH_UNSAFE",
        "periodic closest-image search requires one to three periodic axes",
    )


def bounded_periodic_distance(
    offset_cart: list[float],
    periodic_vectors: list[list[float]],
    *,
    exclude_zero_shift: bool,
    search_budget: list[int],
) -> float:
    """Solve the closest-image problem inside a proven finite integer box."""
    center = continuous_periodic_shift(offset_cart, periodic_vectors)
    if not all(math.isfinite(value) for value in center):
        raise GateError(
            "PERIODIC_IMAGE_SEARCH_UNSAFE",
            "the continuous closest-image center is not finite",
        )
    if exclude_zero_shift:
        initial_shift = min(
            (
                [1 if index == axis else 0 for index in range(len(periodic_vectors))]
                for axis in range(len(periodic_vectors))
            ),
            key=lambda shift: norm(
                vector_add(
                    offset_cart,
                    [
                        sum(
                            shift[index] * periodic_vectors[index][component]
                            for index in range(len(periodic_vectors))
                        )
                        for component in range(3)
                    ],
                )
            ),
        )
    else:
        initial_shift = [int(round(value)) for value in center]

    def shifted_cart(shift: list[int] | tuple[int, ...]) -> list[float]:
        return vector_add(
            offset_cart,
            [
                sum(
                    shift[index] * periodic_vectors[index][component]
                    for index in range(len(periodic_vectors))
                )
                for component in range(3)
            ],
        )

    initial_cart = shifted_cart(initial_shift)
    best_sq = dot(initial_cart, initial_cart)
    if not math.isfinite(best_sq):
        raise GateError(
            "PERIODIC_IMAGE_SEARCH_UNSAFE",
            "the initial closest-image distance is not finite",
        )
    center_residual = vector_add(
        offset_cart,
        [
            sum(
                center[index] * periodic_vectors[index][component]
                for index in range(len(periodic_vectors))
            )
            for component in range(3)
        ],
    )
    spectral_lower_bound = periodic_basis_lower_bound(periodic_vectors)
    radius = (
        math.sqrt(max(0.0, best_sq)) + norm(center_residual)
    ) / math.sqrt(spectral_lower_bound)
    if not math.isfinite(radius):
        raise GateError(
            "PERIODIC_IMAGE_SEARCH_UNSAFE",
            "the closest-image integer bound is not finite",
        )
    margin = 1.0e-10 * max(1.0, radius, *(abs(value) for value in center))
    integer_ranges = [
        range(
            math.ceil(value - radius - margin),
            math.floor(value + radius + margin) + 1,
        )
        for value in center
    ]
    candidate_count = math.prod(len(values) for values in integer_ranges)
    if candidate_count > search_budget[0]:
        raise GateError(
            "PERIODIC_IMAGE_SEARCH_BUDGET_EXCEEDED",
            "the mathematically bounded periodic closest-image search exceeds its evaluation budget",
        )
    search_budget[0] -= candidate_count
    for shift in itertools.product(*integer_ranges):
        if exclude_zero_shift and all(value == 0 for value in shift):
            continue
        trial = shifted_cart(shift)
        best_sq = min(best_sq, dot(trial, trial))
    return math.sqrt(max(0.0, best_sq))


def nearest_periodic_distance(
    left: dict[str, Any],
    right: dict[str, Any],
    structure: dict[str, Any],
    *,
    search_budget: list[int] | None = None,
) -> float:
    if structure["cell_ang"] is None or left["fractional"] is None or right["fractional"] is None:
        return residual_norm(left["cartesian_ang"], right["cartesian_ang"])
    delta = [
        right["fractional"][axis] - left["fractional"][axis]
        for axis in range(3)
    ]
    periodic_vectors = [
        structure["cell_ang"][axis]
        for axis, periodic in enumerate(structure["pbc"])
        if periodic
    ]
    if not periodic_vectors:
        return norm(frac_to_cart(delta, structure["cell_ang"]))
    return bounded_periodic_distance(
        frac_to_cart(delta, structure["cell_ang"]),
        periodic_vectors,
        exclude_zero_shift=False,
        search_budget=(
            [MAX_PERIODIC_IMAGE_EVALUATIONS]
            if search_budget is None
            else search_budget
        ),
    )


def nearest_periodic_self_image_distance(
    site: dict[str, Any],
    structure: dict[str, Any],
    *,
    search_budget: list[int] | None = None,
) -> float | None:
    if (
        structure["cell_ang"] is None
        or site["fractional"] is None
        or not any(structure["pbc"])
    ):
        return None
    periodic_vectors = [
        structure["cell_ang"][axis]
        for axis, periodic in enumerate(structure["pbc"])
        if periodic
    ]
    return bounded_periodic_distance(
        [0.0, 0.0, 0.0],
        periodic_vectors,
        exclude_zero_shift=True,
        search_budget=(
            [MAX_PERIODIC_IMAGE_EVALUATIONS]
            if search_budget is None
            else search_budget
        ),
    )


def minimum_distance(
    structure: dict[str, Any],
    *,
    left_ids: set[str] | None = None,
    right_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    sites = structure["sites"]
    best: dict[str, Any] | None = None
    search_budget = [MAX_PERIODIC_IMAGE_EVALUATIONS]
    if left_ids is None and right_ids is None:
        site = next(
            (
                item
                for item in sites
                if item["fractional"] is not None
            ),
            None,
        )
        if site is not None:
            distance = nearest_periodic_self_image_distance(
                site,
                structure,
                search_budget=search_budget,
            )
            if distance is not None:
                best = {
                    "site_ids": [site["site_id"], site["site_id"]],
                    "distance_ang": distance,
                    "relation": "periodic-self-image",
                }
    for left_index, left in enumerate(sites):
        for right_index in range(left_index + 1, len(sites)):
            right = sites[right_index]
            if left_ids is not None and right_ids is not None:
                cross_pair = (
                    left["site_id"] in left_ids
                    and right["site_id"] in right_ids
                ) or (
                    right["site_id"] in left_ids
                    and left["site_id"] in right_ids
                )
                if not cross_pair:
                    continue
            distance = nearest_periodic_distance(
                left,
                right,
                structure,
                search_budget=search_budget,
            )
            if best is None or distance < best["distance_ang"]:
                best = {
                    "site_ids": [left["site_id"], right["site_id"]],
                    "distance_ang": distance,
                    "relation": "distinct-sites",
                }
    return best


def enforce_minimum_distance(
    structure: dict[str, Any],
    threshold_ang: float,
    *,
    left_ids: set[str] | None = None,
    right_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    closest = minimum_distance(structure, left_ids=left_ids, right_ids=right_ids)
    if closest is not None and closest["distance_ang"] < threshold_ang:
        raise GateError(
            "MINIMUM_DISTANCE_VIOLATION",
            "derived structure contains a pair below the explicit minimum-distance gate",
        )
    return closest


def validate_cif_manifest_schema(value: dict[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise GateError(
            "MANIFEST_SCHEMA_VALIDATOR_UNAVAILABLE",
            "jsonschema is required to import a public structure-manifest",
            EXIT_UNAVAILABLE,
        ) from exc
    schema_path = Path(__file__).resolve().parents[3] / "contracts" / "structure-manifest.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(
            "MANIFEST_SCHEMA_UNAVAILABLE",
            "repository structure-manifest schema is unavailable or invalid",
            EXIT_UNAVAILABLE,
        ) from exc
    failures = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )
    if failures:
        location = "/".join(str(part) for part in failures[0].absolute_path) or "<root>"
        raise GateError(
            "MANIFEST_SCHEMA_INVALID",
            f"structure-manifest schema validation failed at {location}",
        )


def import_cif_manifest(value: dict[str, Any], tolerance_ang: float) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_cif_manifest_schema(value)
    if value["status"] == "BLOCK" or value["validation"]["status"] == "block":
        raise GateError("MANIFEST_STATUS_BLOCKED", "blocked CIF structure-manifest cannot enter mutation")
    if value["transformations"]:
        raise GateError(
            "MANIFEST_LINEAGE_UNSUPPORTED",
            "native import accepts inspection-only CIF manifests with no prior transformations",
        )
    metadata = value["document"]["metadata"]
    if metadata["partial_occupancy_rows"] or metadata["disorder_rows"]:
        raise GateError(
            "MANIFEST_OCCUPANCY_MODEL_UNRESOLVED",
            "partial occupancy or disorder cannot be losslessly adapted to the current staging contract",
        )
    identity = value["structure_identity"]
    fingerprint = identity.get("fingerprint_input")
    if identity.get("canonicalization") != "json-sort-keys-compact-utf8-v1" or not isinstance(fingerprint, dict):
        raise GateError(
            "MANIFEST_IDENTITY_PREIMAGE_MISSING",
            "CIF manifest must publish its canonical identity preimage",
        )
    if digest(fingerprint) != identity["value"]:
        raise GateError("MANIFEST_IDENTITY_HASH_MISMATCH", "CIF manifest identity preimage does not match its hash")
    structure = value["structure"]
    cell = structure["cell"]["vectors_ang"]
    pbc = structure["pbc"]
    published_sites = structure["sites"]
    if fingerprint["pbc"] != pbc or len(fingerprint["sites"]) != len(published_sites):
        raise GateError("MANIFEST_IDENTITY_PAYLOAD_MISMATCH", "CIF manifest identity and structure payload disagree")
    cell_residual = max(
        abs(fingerprint["cell_vectors_ang"][i][j] - cell[i][j])
        for i in range(3)
        for j in range(3)
    )
    if cell_residual > max(tolerance_ang, 1.0e-6):
        raise GateError("MANIFEST_IDENTITY_PAYLOAD_MISMATCH", "CIF manifest identity cell disagrees with published cell")
    normalized_sites: list[dict[str, Any]] = []
    mappings: list[dict[str, Any]] = []
    for ordinal, (site, fingerprint_site) in enumerate(zip(published_sites, fingerprint["sites"])):
        if site["index"] != ordinal:
            raise GateError("MANIFEST_SITE_ORDER_INVALID", "CIF manifest site indices must be contiguous and ordered")
        symbol = site["symbol"]
        if ATOMIC_NUMBER.get(symbol) != site["atomic_number"] or site["atomic_number"] != fingerprint_site["atomic_number"]:
            raise GateError("MANIFEST_SITE_IDENTITY_MISMATCH", "CIF manifest site symbol and atomic number disagree")
        fractional = [_finite_number(item, "manifest fractional") for item in site["fractional"]]
        fingerprint_fractional = fingerprint_site["fractional"]
        coordinate_residual = max(
            abs((fractional[axis] % 1.0) - fingerprint_fractional[axis])
            for axis in range(3)
        )
        if coordinate_residual > max(tolerance_ang, 1.0e-6):
            raise GateError(
                "MANIFEST_IDENTITY_PAYLOAD_MISMATCH",
                "CIF manifest identity coordinates disagree with published sites",
            )
        cartesian = [_finite_number(item, "manifest cartesian") for item in site["cartesian_ang"]]
        if residual_norm(cartesian, frac_to_cart(fractional, cell)) > max(
            tolerance_ang,
            MANIFEST_PUBLIC_CARTESIAN_TOLERANCE_ANG,
        ):
            raise GateError(
                "MANIFEST_COORDINATE_CELL_MISMATCH",
                "CIF manifest fractional and Cartesian site coordinates disagree",
            )
        site_id = f"{symbol}-{ordinal}"
        normalized_sites.append(
            {
                "site_id": site_id,
                "species": [{"element": symbol, "occupancy": 1.0}],
                "fractional": fractional,
                "cartesian_ang": frac_to_cart(fractional, cell),
            }
        )
        mappings.append(
            {
                "upstream_site_index": ordinal,
                "upstream_symbol": symbol,
                "child_site_id": site_id,
                "relation": "same",
            }
        )
    dimensions = sum(pbc)
    kinds = {3: "periodic-crystal", 2: "periodic-slab", 1: "periodic-wire"}
    if dimensions not in kinds:
        raise GateError("MANIFEST_PERIODICITY_UNSUPPORTED", "CIF manifest must retain at least one periodic axis")
    symmetry_attempt = structure["symmetry_attempt"]
    if symmetry_attempt["status"] == "DETECTED":
        symmetry = {
            "status": "verified",
            "number": symmetry_attempt["number"],
            "symbol": symmetry_attempt["international"],
            "tolerance_ang": symmetry_attempt["symprec"],
            "backend": symmetry_attempt["backend"],
            "backend_version": symmetry_attempt["backend_version"],
        }
    else:
        symmetry = unresolved_symmetry()
    child = {
        "contract_name": "structure-preparation-input",
        "schema_version": "1.0",
        "structure_id": value["manifest_id"],
        "structure_kind": kinds[dimensions],
        "pbc": pbc,
        "cell_ang": cell,
        "sites": normalized_sites,
        "symmetry": symmetry,
        "charge_state": {"status": "unknown", "net_charge_e": None},
        "spin_state": {"status": "not-assessed", "multiplicity": None},
    }
    return validate_structure(child, tolerance_ang), mappings


def validate_structure(value: dict[str, Any], tolerance_ang: float) -> dict[str, Any]:
    _keys(
        value,
        {
            "contract_name",
            "schema_version",
            "structure_id",
            "structure_kind",
            "pbc",
            "cell_ang",
            "sites",
            "symmetry",
            "charge_state",
            "spin_state",
        },
        "structure",
    )
    if value["contract_name"] != "structure-preparation-input" or value["schema_version"] != "1.0":
        raise GateError("SCHEMA_ID_INVALID", "structure contract_name/schema_version is unsupported")
    if not isinstance(value["structure_id"], str) or not SAFE_ID.fullmatch(value["structure_id"]):
        raise GateError("STRUCTURE_ID_INVALID", "structure_id is not a safe identifier")
    kinds = {
        "periodic-crystal": (True, True, True),
        "periodic-slab": None,
        "periodic-wire": None,
        "isolated-molecule": (False, False, False),
        "isolated-cluster": (False, False, False),
    }
    kind = value["structure_kind"]
    if kind not in kinds:
        raise GateError("STRUCTURE_KIND_INVALID", "structure_kind is unsupported")
    pbc = value["pbc"]
    if not isinstance(pbc, list) or len(pbc) != 3 or any(type(item) is not bool for item in pbc):
        raise GateError("PBC_INVALID", "pbc must contain exactly three booleans")
    dimensions = sum(pbc)
    expected_dimensions = {
        "periodic-crystal": 3,
        "periodic-slab": 2,
        "periodic-wire": 1,
        "isolated-molecule": 0,
        "isolated-cluster": 0,
    }[kind]
    if dimensions != expected_dimensions:
        raise GateError("PERIODICITY_KIND_MISMATCH", "pbc dimensionality conflicts with structure_kind")
    if dimensions:
        cell = _matrix3(value["cell_ang"], "cell_ang")
        if abs(determinant(cell)) <= 1.0e-10:
            raise GateError("CELL_SINGULAR", "periodic cell is singular or numerically degenerate")
    else:
        if value["cell_ang"] is not None:
            raise GateError("ISOLATED_CELL_PRESENT", "isolated structures must use null cell_ang")
        cell = None

    sites = value["sites"]
    if not isinstance(sites, list) or not sites:
        raise GateError("SITES_INVALID", "sites must be a non-empty array")
    seen: set[str] = set()
    normalized_sites: list[dict[str, Any]] = []
    for ordinal, site in enumerate(sites):
        if not isinstance(site, dict):
            raise GateError("SITE_INVALID", f"site {ordinal} must be an object")
        _keys(site, {"site_id", "species", "fractional", "cartesian_ang"}, f"site {ordinal}")
        site_id = site["site_id"]
        if not isinstance(site_id, str) or not SAFE_ID.fullmatch(site_id):
            raise GateError("SITE_ID_INVALID", f"site {ordinal} has an unsafe site_id")
        if site_id in seen:
            raise GateError("SITE_ID_DUPLICATE", f"site_id {site_id!r} is duplicated")
        seen.add(site_id)
        species = site["species"]
        if not isinstance(species, list) or not species:
            raise GateError("SPECIES_INVALID", f"site {site_id!r} must contain species")
        normalized_species: list[dict[str, Any]] = []
        elements_seen: set[str] = set()
        occupancy_sum = 0.0
        for entry in species:
            if not isinstance(entry, dict):
                raise GateError("SPECIES_INVALID", f"site {site_id!r} species entries must be objects")
            _keys(entry, {"element", "occupancy"}, f"site {site_id} species")
            element = entry["element"]
            if element not in ATOMIC_NUMBER or element in elements_seen:
                raise GateError("ELEMENT_INVALID", f"site {site_id!r} has unknown or duplicate element")
            elements_seen.add(element)
            occupancy = _finite_number(entry["occupancy"], f"site {site_id} occupancy")
            if occupancy <= 0.0 or occupancy > 1.0:
                raise GateError("OCCUPANCY_INVALID", f"site {site_id!r} occupancy must be in (0,1]")
            occupancy_sum += occupancy
            normalized_species.append({"element": element, "occupancy": occupancy})
        if occupancy_sum > 1.0 + 1.0e-10:
            raise GateError("OCCUPANCY_SUM_INVALID", f"site {site_id!r} occupancy sum exceeds one")
        cart = _vector3(site["cartesian_ang"], f"site {site_id} cartesian_ang")
        if dimensions:
            frac = _vector3(site["fractional"], f"site {site_id} fractional")
            expected_cart = frac_to_cart(frac, cell)
            if residual_norm(cart, expected_cart) > tolerance_ang:
                raise GateError(
                    "COORDINATE_REPRESENTATION_MISMATCH",
                    f"site {site_id!r} fractional/cartesian coordinates disagree",
                )
        else:
            if site["fractional"] is not None:
                raise GateError("ISOLATED_FRACTIONAL_PRESENT", "isolated sites must use null fractional coordinates")
            frac = None
        normalized_sites.append(
            {
                "site_id": site_id,
                "species": sorted(normalized_species, key=lambda item: item["element"]),
                "fractional": frac,
                "cartesian_ang": cart,
            }
        )

    symmetry = value["symmetry"]
    if not isinstance(symmetry, dict):
        raise GateError("SYMMETRY_INVALID", "symmetry must be an object")
    _keys(
        symmetry,
        {"status", "number", "symbol", "tolerance_ang", "backend", "backend_version"},
        "symmetry",
    )
    status = symmetry["status"]
    if status not in {"not-applicable", "unresolved", "declared", "verified"}:
        raise GateError("SYMMETRY_STATUS_INVALID", "symmetry status is unsupported")
    if dimensions == 0 and status != "not-applicable":
        raise GateError("SYMMETRY_SCOPE_INVALID", "isolated structures require not-applicable symmetry")
    if dimensions and status == "not-applicable":
        raise GateError("SYMMETRY_SCOPE_INVALID", "periodic structures cannot use not-applicable symmetry")
    if status in {"declared", "verified"}:
        number = symmetry["number"]
        if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= 230:
            raise GateError("SYMMETRY_NUMBER_INVALID", "declared symmetry requires space-group number 1..230")
        if not isinstance(symmetry["symbol"], str) or not symmetry["symbol"].strip():
            raise GateError("SYMMETRY_SYMBOL_INVALID", "declared symmetry requires a non-empty symbol")
        tolerance = _finite_number(symmetry["tolerance_ang"], "symmetry tolerance_ang")
        if tolerance <= 0.0:
            raise GateError("SYMMETRY_TOLERANCE_INVALID", "symmetry tolerance must be positive")
    else:
        if any(symmetry[key] is not None for key in ("number", "symbol", "tolerance_ang")):
            raise GateError("SYMMETRY_EVIDENCE_INVALID", "unresolved symmetry cannot carry group claims")
    if status == "verified":
        if not all(isinstance(symmetry[key], str) and symmetry[key] for key in ("backend", "backend_version")):
            raise GateError("SYMMETRY_PROVENANCE_MISSING", "verified symmetry requires backend and version")
    elif symmetry["backend"] is not None or symmetry["backend_version"] is not None:
        raise GateError("SYMMETRY_PROVENANCE_INVALID", "only verified symmetry may carry backend provenance")

    charge = value["charge_state"]
    if not isinstance(charge, dict):
        raise GateError("CHARGE_STATE_INVALID", "charge_state must be an object")
    _keys(charge, {"status", "net_charge_e"}, "charge_state")
    if charge["status"] not in {"known", "unknown"}:
        raise GateError("CHARGE_STATE_INVALID", "charge status must be known or unknown")
    if charge["status"] == "known":
        if isinstance(charge["net_charge_e"], bool) or not isinstance(charge["net_charge_e"], int):
            raise GateError("CHARGE_INVALID", "known net charge must be an integer")
    elif charge["net_charge_e"] is not None:
        raise GateError("CHARGE_INVALID", "unknown charge must use null net_charge_e")

    spin = value["spin_state"]
    if not isinstance(spin, dict):
        raise GateError("SPIN_STATE_INVALID", "spin_state must be an object")
    _keys(spin, {"status", "multiplicity"}, "spin_state")
    if spin["status"] not in {"known", "not-assessed"}:
        raise GateError("SPIN_STATE_INVALID", "spin status must be known or not-assessed")
    if spin["status"] == "known":
        multiplicity = spin["multiplicity"]
        if isinstance(multiplicity, bool) or not isinstance(multiplicity, int) or multiplicity < 1:
            raise GateError("MULTIPLICITY_INVALID", "known multiplicity must be a positive integer")
    elif spin["multiplicity"] is not None:
        raise GateError("MULTIPLICITY_INVALID", "not-assessed spin must use null multiplicity")

    normalized = dict(value)
    normalized["cell_ang"] = cell
    normalized["sites"] = normalized_sites
    if kind in {"isolated-molecule", "isolated-cluster"} and charge["status"] == "known" and spin["status"] == "known":
        nuclear_charge = sum(
            ATOMIC_NUMBER[item["element"]] * item["occupancy"]
            for site in normalized_sites
            for item in site["species"]
        )
        electrons = nuclear_charge - charge["net_charge_e"]
        if abs(electrons - round(electrons)) <= 1.0e-9:
            electron_count = int(round(electrons))
            if electron_count < 0 or spin["multiplicity"] > electron_count + 1:
                raise GateError(
                    "MULTIPLICITY_ELECTRON_COUNT_MISMATCH",
                    "isolated-system electron count is incompatible with multiplicity magnitude",
                )
            if (electron_count - (spin["multiplicity"] - 1)) % 2 != 0:
                raise GateError(
                    "CHARGE_SPIN_PARITY_MISMATCH",
                    "molecular electron count is incompatible with multiplicity parity",
                )
    return normalized


def structure_identity(structure: dict[str, Any]) -> dict[str, Any]:
    cell = structure["cell_ang"]
    labeled_sites = []
    geometry_sites = []
    composition_sites = []
    representation_sites = []
    for site in structure["sites"]:
        fractional = site["fractional"]
        canonical_fractional = (
            [
                round_float(component % 1.0 if structure["pbc"][axis] else component)
                for axis, component in enumerate(fractional)
            ]
            if fractional is not None
            else None
        )
        canonical_species = [
            {"element": item["element"], "occupancy": round_float(item["occupancy"])}
            for item in site["species"]
        ]
        canonical_position = {
            "fractional": canonical_fractional,
            "cartesian_ang": (
                None
                if canonical_fractional is not None
                else [round_float(item) for item in site["cartesian_ang"]]
            ),
        }
        labeled_sites.append(
            {
                "site_id": site["site_id"],
                "species": canonical_species,
                **canonical_position,
            }
        )
        geometry_sites.append(canonical_position)
        composition_sites.append(canonical_species)
        representation_sites.append(
            {
                "site_id": site["site_id"],
                "species": site["species"],
                "fractional": site["fractional"],
                "cartesian_ang": site["cartesian_ang"],
            }
        )
    periodicity_payload = {
        "structure_kind": structure["structure_kind"],
        "pbc": structure["pbc"],
        "cell_ang": None if cell is None else [[round_float(item) for item in row] for row in cell],
    }
    electronic_state_payload = {
        "charge_state": structure["charge_state"],
        "spin_state": structure["spin_state"],
    }
    labeled_sites = sorted(labeled_sites, key=lambda item: item["site_id"])
    geometry_sites = sorted(geometry_sites, key=canonical_bytes)
    composition_sites = sorted(composition_sites, key=canonical_bytes)
    structure_payload = {
        "periodicity": periodicity_payload,
        "labeled_sites": labeled_sites,
        "electronic_state": electronic_state_payload,
    }
    return {
        "algorithm": "sha256-canonical-json-domain-v2",
        "precision_digits": 12,
        "structure_sha256": digest(structure_payload),
        "geometry_sha256": digest(geometry_sites),
        "labeled_structure_sha256": digest(labeled_sites),
        "site_order_sha256": digest([site["site_id"] for site in structure["sites"]]),
        "periodicity_sha256": digest(periodicity_payload),
        "composition_occupancy_sha256": digest(composition_sites),
        "electronic_state_sha256": digest(electronic_state_payload),
        "symmetry_sha256": digest(structure["symmetry"]),
        "representation_sha256": digest(
            {
                "structure_kind": structure["structure_kind"],
                "pbc": structure["pbc"],
                "cell_ang": cell,
                "sites": representation_sites,
                "symmetry": structure["symmetry"],
                "charge_state": structure["charge_state"],
                "spin_state": structure["spin_state"],
            }
        ),
    }


def occupancy_findings(structure: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for site in structure["sites"]:
        occupancy_sum = sum(item["occupancy"] for item in site["species"])
        if len(site["species"]) > 1:
            findings.append(
                {
                    "finding_id": "OCCUPANCY_DISORDER_PRESENT",
                    "severity": "blocker",
                    "site_id": site["site_id"],
                    "message": "mixed occupancy requires an explicit physical disorder model",
                }
            )
        elif abs(occupancy_sum - 1.0) > 1.0e-10:
            findings.append(
                {
                    "finding_id": "PARTIAL_OCCUPANCY_PRESENT",
                    "severity": "blocker",
                    "site_id": site["site_id"],
                    "message": "vacancy occupancy requires an explicit ordered or statistical model",
                }
            )
    return findings


def audit_report(structure: dict[str, Any], source: dict[str, Any], tolerance_ang: float) -> dict[str, Any]:
    findings = occupancy_findings(structure)
    symmetry_status = structure["symmetry"]["status"]
    if symmetry_status == "verified":
        findings.append(
            {
                "finding_id": "SYMMETRY_VERIFICATION_PROVENANCE_UNRESOLVED",
                "severity": "warning",
                "message": "backend/version fields are present but their external evidence was not resolved by this audit",
            }
        )
    elif symmetry_status == "declared":
        findings.append(
            {
                "finding_id": "SYMMETRY_DECLARATION_UNVERIFIED",
                "severity": "warning",
                "message": "space-group metadata was declared but not recomputed by a pinned backend",
            }
        )
    elif symmetry_status == "unresolved":
        findings.append(
            {
                "finding_id": "SYMMETRY_UNRESOLVED",
                "severity": "warning",
                "message": "no symmetry claim is available for this periodic structure",
            }
        )
    if any(
        site["fractional"]
        and any(
            structure["pbc"][axis] and not 0.0 <= component < 1.0
            for axis, component in enumerate(site["fractional"])
        )
        for site in structure["sites"]
    ):
        findings.append(
            {
                "finding_id": "PERIODIC_IMAGE_UNWRAPPED",
                "severity": "notice",
                "message": "fractional coordinates outside [0,1) are preserved as periodic-image evidence",
            }
        )
    if structure["structure_kind"] in {"isolated-molecule", "isolated-cluster"}:
        if structure["charge_state"]["status"] != "known" or structure["spin_state"]["status"] != "known":
            findings.append(
                {
                    "finding_id": "MOLECULAR_ELECTRONIC_STATE_UNRESOLVED",
                    "severity": "blocker",
                    "message": "molecular charge and multiplicity must be explicit before calculation export",
                }
            )
    blockers = [item for item in findings if item["severity"] == "blocker"]
    warnings = [item for item in findings if item["severity"] == "warning"]
    readiness = "blocked" if blockers else ("requires-decision" if warnings else "ready")
    return {
        "contract_name": "structure-preparation-audit",
        "schema_version": "1.0",
        "status": "pass" if not blockers else "blocked",
        "source": source,
        "structure_id": structure["structure_id"],
        "identity": structure_identity(structure),
        "periodicity": {
            "dimensions": sum(structure["pbc"]),
            "pbc": structure["pbc"],
            "cell_determinant_ang3": (
                None if structure["cell_ang"] is None else round_float(determinant(structure["cell_ang"]))
            ),
            "coordinate_tolerance_ang": tolerance_ang,
        },
        "site_count": len(structure["sites"]),
        "symmetry_status": symmetry_status,
        "calculation_readiness": readiness,
        "findings": findings,
        **candidate_lifecycle("input_gates_only"),
        "limitations": [
            "No backend symmetry search was executed by the deterministic audit.",
            "A passed input gate is not scientific acceptance or DFT convergence evidence.",
        ],
        "provenance": {"tool": "structure_prepare.py", "tool_version": TOOL_VERSION},
    }


def compare_structures(parent: dict[str, Any], child: dict[str, Any], tolerance_ang: float) -> dict[str, Any]:
    parent_identity = structure_identity(parent)
    child_identity = structure_identity(child)
    if parent_identity == child_identity:
        classification = "exact"
        cell_residual = 0.0
        mappings: list[dict[str, Any]] = [
            {
                "parent_site_id": site["site_id"],
                "child_site_id": site["site_id"],
                "child_to_parent_image_shift": [0, 0, 0],
                "residual_ang": 0.0,
            }
            for site in parent["sites"]
        ]
        differences: list[str] = []
    else:
        child_by_id = {site["site_id"]: site for site in child["sites"]}
        mappings = []
        differences = []
        if set(child_by_id) != {site["site_id"] for site in parent["sites"]}:
            differences.append("site-id-set")
        if parent["pbc"] != child["pbc"] or parent["structure_kind"] != child["structure_kind"]:
            differences.append("periodicity")
        if parent["cell_ang"] is None and child["cell_ang"] is None:
            cell_residual = 0.0
        elif parent["cell_ang"] is None or child["cell_ang"] is None:
            cell_residual = math.inf
        else:
            cell_residual = max(
                abs(parent["cell_ang"][i][j] - child["cell_ang"][i][j])
                for i in range(3)
                for j in range(3)
            )
        if cell_residual > tolerance_ang:
            differences.append("cell")
        if parent["charge_state"] != child["charge_state"] or parent["spin_state"] != child["spin_state"]:
            differences.append("electronic-state")
        if parent["symmetry"] != child["symmetry"]:
            differences.append("symmetry")
        for parent_site in parent["sites"]:
            child_site = child_by_id.get(parent_site["site_id"])
            if child_site is None:
                continue
            if parent_site["species"] != child_site["species"]:
                differences.append(f"species:{parent_site['site_id']}")
                continue
            if parent_site["fractional"] is not None and child_site["fractional"] is not None:
                shift = [
                    int(round(parent_site["fractional"][i] - child_site["fractional"][i]))
                    if parent["pbc"][i] and child["pbc"][i]
                    else 0
                    for i in range(3)
                ]
                adjusted_child = [child_site["fractional"][i] + shift[i] for i in range(3)]
                residual = residual_norm(
                    parent_site["cartesian_ang"],
                    frac_to_cart(adjusted_child, parent["cell_ang"]),
                )
            else:
                shift = [0, 0, 0]
                residual = residual_norm(parent_site["cartesian_ang"], child_site["cartesian_ang"])
            mappings.append(
                {
                    "parent_site_id": parent_site["site_id"],
                    "child_site_id": child_site["site_id"],
                    "child_to_parent_image_shift": shift,
                    "residual_ang": round_float(residual),
                }
            )
            if residual > tolerance_ang:
                differences.append(f"coordinate:{parent_site['site_id']}")
        classification = "equivalent" if not differences else "lossy"
    return {
        "classification": classification,
        "tolerance_ang": tolerance_ang,
        "parent_identity": parent_identity,
        "child_identity": child_identity,
        "site_mapping": mappings,
        "site_mapping_sha256": digest(mappings),
        "cell_max_abs_residual_ang": None if math.isinf(cell_residual) else round_float(cell_residual),
        "differences": sorted(set(differences)),
    }


def validate_supercell_matrix(matrix: list[list[int]]) -> int:
    if (
        len(matrix) != 3
        or any(len(row) != 3 for row in matrix)
        or any(type(item) is not int for row in matrix for item in row)
    ):
        raise GateError("SUPERCELL_MATRIX_INVALID", "supercell matrix must contain nine integers")
    det_float = determinant(matrix)
    det_int = int(round(det_float))
    if abs(det_float - det_int) > 1.0e-9 or det_int < 1:
        raise GateError("SUPERCELL_MATRIX_INVALID", "supercell matrix must have a positive integer determinant")
    return det_int


def supercell_coset_representatives(matrix: list[list[int]], determinant_int: int) -> list[list[int]]:
    diagonal = all(matrix[i][j] == 0 for i in range(3) for j in range(3) if i != j)
    if diagonal and all(matrix[index][index] > 0 for index in range(3)):
        return [
            [i, j, k]
            for i in range(matrix[0][0])
            for j in range(matrix[1][1])
            for k in range(matrix[2][2])
        ]
    inverse = inverse_matrix(matrix)
    representatives: dict[tuple[float, float, float], list[int]] = {}
    search_limit = max(2, determinant_int)
    for radius in range(search_limit + 1):
        for translation in itertools.product(range(-radius, radius + 1), repeat=3):
            transformed = row_vector_matrix(list(translation), inverse)
            key = tuple(round_float(component % 1.0) for component in transformed)
            previous = representatives.get(key)
            candidate = list(translation)
            if previous is None or tuple(candidate) < tuple(previous):
                representatives[key] = candidate
        if len(representatives) >= determinant_int:
            break
    if len(representatives) != determinant_int:
        raise GateError(
            "SUPERCELL_COSET_ENUMERATION_FAILED",
            "could not enumerate the expected number of supercell lattice cosets",
        )
    return [representatives[key] for key in sorted(representatives)]


def replicate_by_matrix(
    parent: dict[str, Any],
    matrix: list[list[int]],
    *,
    allow_nonperiodic_unit_axes: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    determinant_int = validate_supercell_matrix(matrix)
    if parent["cell_ang"] is None:
        raise GateError("OPERATION_SCOPE_INVALID", "supercell construction requires a periodic cell")
    if allow_nonperiodic_unit_axes:
        for axis, periodic in enumerate(parent["pbc"]):
            if not periodic and (
                matrix[axis][axis] != 1
                or any(matrix[axis][other] != 0 for other in range(3) if other != axis)
                or any(matrix[other][axis] != 0 for other in range(3) if other != axis)
            ):
                raise GateError(
                    "NONPERIODIC_REPLICATION_REFUSED",
                    "a nonperiodic axis must remain an unmixed unit axis",
                )
    elif not all(parent["pbc"]):
        raise GateError("OPERATION_SCOPE_INVALID", "general supercell construction requires three-dimensional periodicity")
    derived_site_count = len(parent["sites"]) * determinant_int
    if derived_site_count > MAX_DERIVED_SITES:
        raise GateError(
            "SUPERCELL_BUDGET_EXCEEDED",
            f"derived site count {derived_site_count} exceeds candidate limit {MAX_DERIVED_SITES}",
        )
    inverse = inverse_matrix(matrix)
    representatives = supercell_coset_representatives(matrix, determinant_int)
    diagonal = all(matrix[i][j] == 0 for i in range(3) for j in range(3) if i != j)
    child = json.loads(json.dumps(parent))
    child["cell_ang"] = matrix_multiply(matrix, parent["cell_ang"])
    child["symmetry"] = unresolved_symmetry()
    child_sites: list[dict[str, Any]] = []
    mappings: list[dict[str, Any]] = []
    for parent_site in parent["sites"]:
        canonical_parent = [
            component % 1.0 if parent["pbc"][axis] else component
            for axis, component in enumerate(parent_site["fractional"])
        ]
        parent_image_shift = [
            int(round(parent_site["fractional"][axis] - canonical_parent[axis]))
            if parent["pbc"][axis]
            else 0
            for axis in range(3)
        ]
        for replica_index, translation in enumerate(representatives):
            child_site = json.loads(json.dumps(parent_site))
            replica_suffix = (
                "_".join(str(item) for item in translation)
                if diagonal
                else f"r{replica_index}"
            )
            child_site["site_id"] = f"{parent_site['site_id']}__{replica_suffix}"
            if not SAFE_ID.fullmatch(child_site["site_id"]):
                raise GateError("DERIVED_SITE_ID_INVALID", "derived supercell site_id is too long or unsafe")
            fractional = row_vector_matrix(
                [canonical_parent[axis] + translation[axis] for axis in range(3)],
                inverse,
            )
            child_site["fractional"] = [
                round_float(component % 1.0 if child["pbc"][axis] else component)
                for axis, component in enumerate(fractional)
            ]
            child_site["cartesian_ang"] = frac_to_cart(child_site["fractional"], child["cell_ang"])
            child_sites.append(child_site)
            mapping = {
                "parent_site_id": parent_site["site_id"],
                "child_site_id": child_site["site_id"],
                "relation": "replicated",
                "parent_image_shift_to_canonical": parent_image_shift,
            }
            if diagonal:
                mapping["replica_shift"] = translation
            else:
                mapping["replica_index"] = replica_index
                mapping["replica_lattice_translation"] = translation
            mappings.append(mapping)
    child["sites"] = child_sites
    return child, mappings


def parse_supercell_matrix(
    repeat: list[int] | None,
    matrix_values: list[int] | None,
) -> tuple[list[list[int]], str]:
    if repeat is not None and matrix_values is not None:
        raise GateError("PARAMETER_CONFLICT", "use either --repeat or --matrix, not both")
    if repeat is not None:
        if len(repeat) != 3 or any(type(item) is not int or item < 1 for item in repeat):
            raise GateError("SUPERCELL_PARAMETER_INVALID", "--repeat requires three positive integers")
        return [
            [repeat[0], 0, 0],
            [0, repeat[1], 0],
            [0, 0, repeat[2]],
        ], "diagonal-repeat"
    if matrix_values is not None:
        if len(matrix_values) != 9 or any(type(item) is not int for item in matrix_values):
            raise GateError("SUPERCELL_MATRIX_INVALID", "--matrix requires nine integers")
        matrix = [matrix_values[index : index + 3] for index in range(0, 9, 3)]
        validate_supercell_matrix(matrix)
        return matrix, "integer-supercell-matrix"
    raise GateError("PARAMETER_MISSING", "supercell requires --repeat or --matrix")


def transformed_structure(
    parent: dict[str, Any],
    operation: str,
    order: str | None,
    repeat: list[int] | None,
    matrix_values: list[int] | None,
    deformation_values: list[float] | None,
    max_strain: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    child = json.loads(json.dumps(parent))
    mappings: list[dict[str, Any]] = []
    parameters: list[dict[str, Any]] = []
    if operation == "wrap":
        if any(item is not None for item in (order, repeat, matrix_values, deformation_values)):
            raise GateError("PARAMETER_CONFLICT", "wrap does not accept reorder, supercell, or strain parameters")
        if not any(parent["pbc"]):
            raise GateError("OPERATION_SCOPE_INVALID", "wrap requires a periodic structure")
        for site in child["sites"]:
            original = list(site["fractional"])
            wrapped = [component % 1.0 if parent["pbc"][i] else component for i, component in enumerate(original)]
            site["fractional"] = wrapped
            site["cartesian_ang"] = frac_to_cart(wrapped, child["cell_ang"])
            mappings.append(
                {
                    "parent_site_id": site["site_id"],
                    "child_site_id": site["site_id"],
                    "relation": "same",
                    "child_to_parent_image_shift": [int(round(original[i] - wrapped[i])) for i in range(3)],
                }
            )
        parameters.append({"name": "wrap-policy", "value": "periodic-dimensions-only"})
    elif operation == "reorder":
        if any(item is not None for item in (repeat, matrix_values, deformation_values)):
            raise GateError("PARAMETER_CONFLICT", "reorder accepts only --order")
        if order is None:
            raise GateError("PARAMETER_MISSING", "reorder requires --order")
        requested = order.split(",")
        existing = [site["site_id"] for site in parent["sites"]]
        if len(requested) != len(set(requested)) or set(requested) != set(existing):
            raise GateError("SITE_ORDER_INVALID", "--order must list every site_id exactly once")
        by_id = {site["site_id"]: site for site in child["sites"]}
        child["sites"] = [by_id[site_id] for site_id in requested]
        mappings = [
            {
                "parent_site_id": site_id,
                "child_site_id": site_id,
                "relation": "same",
                "child_to_parent_image_shift": [0, 0, 0],
            }
            for site_id in existing
        ]
        parameters.append({"name": "site-order", "value": requested})
    elif operation == "supercell":
        if order is not None or deformation_values is not None:
            raise GateError("PARAMETER_CONFLICT", "supercell accepts --repeat or --matrix only")
        supercell_matrix, parameter_name = parse_supercell_matrix(repeat, matrix_values)
        child, mappings = replicate_by_matrix(parent, supercell_matrix)
        parameters.append({"name": parameter_name, "value": supercell_matrix})
    elif operation == "strain":
        if order is not None or repeat is not None or matrix_values is not None:
            raise GateError("PARAMETER_CONFLICT", "strain accepts --deformation and --max-strain only")
        if deformation_values is None or len(deformation_values) != 9:
            raise GateError("PARAMETER_MISSING", "strain requires --deformation with nine finite numbers")
        deformation = [
            [_finite_number(item, "deformation") for item in deformation_values[index : index + 3]]
            for index in range(0, 9, 3)
        ]
        if determinant(deformation) <= 1.0e-8:
            raise GateError("DEFORMATION_INVALID", "deformation must preserve handedness and remain nonsingular")
        maximum_component = max(
            abs(deformation[i][j] - (1.0 if i == j else 0.0))
            for i in range(3)
            for j in range(3)
        )
        if maximum_component > max_strain:
            raise GateError("STRAIN_BUDGET_EXCEEDED", "deformation exceeds the explicit component-wise strain budget")
        child["cell_ang"] = [
            apply_cartesian_deformation(row, deformation)
            for row in parent["cell_ang"]
        ]
        for site in child["sites"]:
            site["cartesian_ang"] = apply_cartesian_deformation(site["cartesian_ang"], deformation)
            mappings.append(
                {
                    "parent_site_id": site["site_id"],
                    "child_site_id": site["site_id"],
                    "relation": "same",
                    "child_to_parent_image_shift": [0, 0, 0],
                }
            )
        child["symmetry"] = unresolved_symmetry()
        parameters.extend(
            [
                {"name": "cartesian-deformation", "value": deformation},
                {"name": "maximum-component", "value": round_float(maximum_component)},
                {"name": "maximum-allowed-component", "value": max_strain},
            ]
        )
    else:
        raise GateError("OPERATION_UNSUPPORTED", "operation is not implemented by this candidate")
    child_identity = structure_identity(child)
    child["structure_id"] = f"{parent['structure_id']}--{operation}--{child_identity['structure_sha256'][:8]}"
    if not SAFE_ID.fullmatch(child["structure_id"]):
        child["structure_id"] = f"derived-{child_identity['structure_sha256'][:16]}"
    return child, mappings, parameters


def derived_result(
    *,
    operation: str,
    sources: list[dict[str, Any]],
    parents: list[dict[str, Any]],
    child: dict[str, Any],
    mappings: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    tolerance_ang: float,
    limitations: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    child_identity = structure_identity(child)
    audit = audit_report(
        child,
        {"label": "embedded-child", "bytes": 0, "sha256": digest(child)},
        tolerance_ang,
    )
    result = {
        "contract_name": "structure-preparation-result",
        "schema_version": "1.0",
        "status": "pass",
        "operation_status": "completed",
        "sources": sources,
        "operation": operation,
        "parameters": parameters,
        "parent_identities": [
            {
                "role": parent["role"],
                "structure_id": parent["structure"]["structure_id"],
                "identity": structure_identity(parent["structure"]),
            }
            for parent in parents
        ],
        "child_identity": child_identity,
        "mapping_status": "exact",
        "site_mapping": mappings,
        "site_mapping_sha256": digest(mappings),
        "roundtrip": {
            "classification": "not-applicable-derived-structure",
            "tolerance_ang": tolerance_ang,
            "child_identity": child_identity,
            "site_mapping_sha256": digest(mappings),
            "differences": ["derived-geometry", "derived-composition-or-cell"],
        },
        "child": child,
        "child_calculation_readiness": audit["calculation_readiness"],
        "geometry_eligibility": (
            "blocked"
            if any(item["severity"] == "blocker" for item in audit["findings"])
            else "eligible"
        ),
        "calculation_handoff": audit["calculation_readiness"],
        "scientific_stability": "not-assessed",
        "findings": audit["findings"],
        **candidate_lifecycle("input_gates_only"),
        "limitations": limitations,
        "provenance": {"tool": "structure_prepare.py", "tool_version": TOOL_VERSION},
    }
    if extra:
        result.update(extra)
    return result


def periodic_surface_frame(structure: dict[str, Any]) -> dict[str, Any]:
    if structure["structure_kind"] != "periodic-slab" or sum(structure["pbc"]) != 2:
        raise GateError("SURFACE_SCOPE_INVALID", "operation requires a two-dimensionally periodic slab")
    periodic_axes = [axis for axis, periodic in enumerate(structure["pbc"]) if periodic]
    normal_axis = next(axis for axis, periodic in enumerate(structure["pbc"]) if not periodic)
    first = structure["cell_ang"][periodic_axes[0]]
    second = structure["cell_ang"][periodic_axes[1]]
    normal = unit_vector(cross(first, second), "surface plane")
    cell_normal = unit_vector(structure["cell_ang"][normal_axis], "nonperiodic cell vector")
    alignment = dot(normal, cell_normal)
    if abs(alignment) < MIN_SURFACE_NORMAL_ALIGNMENT:
        raise GateError(
            "SURFACE_CELL_ALIGNMENT_INVALID",
            "nonperiodic cell vector must be aligned with the surface normal within the native tolerance",
        )
    if alignment < 0.0:
        normal = vector_scale(normal, -1.0)
    return {
        "periodic_axes": periodic_axes,
        "normal_axis": normal_axis,
        "normal": normal,
        "normal_alignment": round_float(abs(alignment)),
    }


def command_make_slab(args: argparse.Namespace) -> int:
    value, source = load_json(args.input)
    parent = validate_structure(value, args.tolerance_ang)
    if parent["structure_kind"] != "periodic-crystal":
        raise GateError("SLAB_PARENT_INVALID", "make-slab requires a three-dimensionally periodic crystal")
    axis = args.axis
    if axis not in {0, 1, 2}:
        raise GateError("SLAB_AXIS_INVALID", "slab axis must be 0, 1, or 2")
    if not 1 <= args.layers <= 64:
        raise GateError("SLAB_LAYER_BUDGET_INVALID", "layers must be in [1, 64]")
    vacuum_ang = validate_bounded_float(
        args.vacuum_ang,
        "vacuum_ang",
        minimum=0.0,
        maximum=200.0,
        include_minimum=True,
    )
    in_plane = [candidate for candidate in range(3) if candidate != axis]
    plane_normal = unit_vector(
        cross(parent["cell_ang"][in_plane[0]], parent["cell_ang"][in_plane[1]]),
        "slab plane",
    )
    axis_unit = unit_vector(parent["cell_ang"][axis], "slab axis")
    alignment = abs(dot(plane_normal, axis_unit))
    if alignment < MIN_SURFACE_NORMAL_ALIGNMENT:
        raise GateError(
            "SLAB_AXIS_NOT_SURFACE_NORMAL",
            "native make-slab supports only a lattice vector aligned with the plane normal",
        )
    repeat = [1, 1, 1]
    repeat[axis] = args.layers
    matrix = [[repeat[i] if i == j else 0 for j in range(3)] for i in range(3)]
    child, mappings = replicate_by_matrix(parent, matrix)
    base_length = norm(parent["cell_ang"][axis])
    scale = args.layers + vacuum_ang / base_length
    child["cell_ang"][axis] = vector_scale(parent["cell_ang"][axis], scale)
    vacuum_offset = vacuum_ang / (2.0 * base_length)
    for site in child["sites"]:
        old_fractional = site["fractional"][axis]
        site["fractional"][axis] = (old_fractional * args.layers + vacuum_offset) / scale
        site["cartesian_ang"] = frac_to_cart(site["fractional"], child["cell_ang"])
    child["pbc"][axis] = False
    child["structure_kind"] = "periodic-slab"
    child["symmetry"] = unresolved_symmetry()
    child["structure_id"] = derived_structure_id("slab", child)
    child = validate_structure(child, args.tolerance_ang)
    result = derived_result(
        operation="slab",
        sources=[{"role": "parent", **source}],
        parents=[{"role": "parent", "structure": parent}],
        child=child,
        mappings=mappings,
        parameters=[
            {"name": "lattice-axis", "value": axis},
            {"name": "layer-repeat", "value": args.layers},
            {"name": "vacuum-ang", "value": vacuum_ang},
            {"name": "axis-normal-alignment", "value": round_float(alignment)},
            {"name": "termination-policy", "value": "input-origin-preserved"},
        ],
        tolerance_ang=args.tolerance_ang,
        limitations=[
            "This native route cleaves only along an input lattice vector already aligned with the surface normal.",
            "It does not enumerate Miller indices, terminations, polarity, reconstruction, or surface stability.",
            "Vacuum and layer count are construction parameters, not convergence evidence.",
        ],
        extra={
            "operation_family": "cell-slab",
            "operation_profile_id": "native-lattice-axis-slab-v1",
            "construction_metrics": {
                "site_count": len(child["sites"]),
                "surface_axis": axis,
                "vacuum_ang": vacuum_ang,
            }
        },
    )
    write_json(result, args.out)
    return EXIT_OK


def in_plane_angle_degrees(first: list[float], second: list[float]) -> float:
    cosine = dot(first, second) / (norm(first) * norm(second))
    cosine = max(-1.0, min(1.0, cosine))
    return math.degrees(math.acos(cosine))


def interface_matches(
    substrate: dict[str, Any],
    film: dict[str, Any],
    *,
    max_repeat: int,
    max_strain: float,
    max_angle_deg: float,
    max_atoms: int,
) -> tuple[dict[str, Any], int, list[dict[str, Any]]]:
    substrate_frame = periodic_surface_frame(substrate)
    film_frame = periodic_surface_frame(film)
    if substrate["pbc"] != film["pbc"]:
        raise GateError("INTERFACE_PERIODICITY_MISMATCH", "substrate and film must use the same periodic axes")
    axes = substrate_frame["periodic_axes"]
    substrate_vectors = [substrate["cell_ang"][axis] for axis in axes]
    film_vectors = [film["cell_ang"][axis] for axis in axes]
    substrate_angle = in_plane_angle_degrees(*substrate_vectors)
    film_angle = in_plane_angle_degrees(*film_vectors)
    angle_mismatch = abs(substrate_angle - film_angle)
    accepted: list[dict[str, Any]] = []
    for substrate_repeat in itertools.product(range(1, max_repeat + 1), repeat=2):
        substrate_lengths = [
            norm(substrate_vectors[index]) * substrate_repeat[index]
            for index in range(2)
        ]
        for film_repeat in itertools.product(range(1, max_repeat + 1), repeat=2):
            film_lengths = [
                norm(film_vectors[index]) * film_repeat[index]
                for index in range(2)
            ]
            strains = [
                substrate_lengths[index] / film_lengths[index] - 1.0
                for index in range(2)
            ]
            maximum_strain = max(abs(item) for item in strains)
            atom_count = (
                len(substrate["sites"]) * substrate_repeat[0] * substrate_repeat[1]
                + len(film["sites"]) * film_repeat[0] * film_repeat[1]
            )
            if maximum_strain > max_strain or angle_mismatch > max_angle_deg or atom_count > max_atoms:
                continue
            accepted.append(
                {
                    "substrate_repeat": list(substrate_repeat),
                    "film_repeat": list(film_repeat),
                    "film_length_strain": [round_float(item) for item in strains],
                    "maximum_abs_film_length_strain": round_float(maximum_strain),
                    "in_plane_angle_mismatch_deg": round_float(angle_mismatch),
                    "derived_atom_count": atom_count,
                    "substrate_area_ang2": round_float(
                        norm(cross(substrate_vectors[0], substrate_vectors[1]))
                        * substrate_repeat[0]
                        * substrate_repeat[1]
                    ),
                }
            )
    if not accepted:
        raise GateError(
            "INTERFACE_MATCH_NOT_FOUND",
            "no coherent in-plane repeat satisfies strain, angle, and atom-count budgets",
        )
    accepted.sort(
        key=lambda item: (
            item["maximum_abs_film_length_strain"],
            item["in_plane_angle_mismatch_deg"],
            item["derived_atom_count"],
            sum(abs(value) for value in item["film_length_strain"]),
            item["substrate_repeat"],
            item["film_repeat"],
        )
    )
    return accepted[0], len(accepted), accepted[:20]


def replicate_slab_in_plane(
    slab: dict[str, Any],
    repeats: list[int],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    frame = periodic_surface_frame(slab)
    diagonal = [1, 1, 1]
    for index, axis in enumerate(frame["periodic_axes"]):
        diagonal[axis] = repeats[index]
    matrix = [[diagonal[i] if i == j else 0 for j in range(3)] for i in range(3)]
    return replicate_by_matrix(slab, matrix, allow_nonperiodic_unit_axes=True)


def command_build_interface(args: argparse.Namespace) -> int:
    substrate_value, substrate_source = load_json(args.substrate)
    film_value, film_source = load_json(args.film)
    substrate = validate_structure(substrate_value, args.tolerance_ang)
    film = validate_structure(film_value, args.tolerance_ang)
    if not 1 <= args.max_repeat <= 12:
        raise GateError("INTERFACE_REPEAT_BUDGET_INVALID", "max-repeat must be in [1, 12]")
    if not 2 <= args.max_atoms <= MAX_DERIVED_SITES:
        raise GateError("INTERFACE_ATOM_BUDGET_INVALID", f"max-atoms must be in [2, {MAX_DERIVED_SITES}]")
    max_strain = validate_bounded_float(
        args.max_strain,
        "max_strain",
        minimum=0.0,
        maximum=0.5,
        include_minimum=True,
    )
    max_angle_deg = validate_bounded_float(
        args.max_angle_deg,
        "max_angle_deg",
        minimum=0.0,
        maximum=30.0,
        include_minimum=True,
    )
    gap_ang = validate_bounded_float(args.gap_ang, "gap_ang", minimum=0.0, maximum=30.0)
    vacuum_ang = validate_bounded_float(
        args.vacuum_ang,
        "vacuum_ang",
        minimum=0.0,
        maximum=200.0,
        include_minimum=True,
    )
    minimum_distance_ang = validate_bounded_float(
        args.min_distance_ang,
        "min_distance_ang",
        minimum=0.0,
        maximum=5.0,
    )
    shift = [_finite_number(item, "registry_shift") % 1.0 for item in args.registry_shift]
    selected, accepted_count, accepted_sample = interface_matches(
        substrate,
        film,
        max_repeat=args.max_repeat,
        max_strain=max_strain,
        max_angle_deg=max_angle_deg,
        max_atoms=args.max_atoms,
    )
    substrate_supercell, substrate_mappings = replicate_slab_in_plane(
        substrate,
        selected["substrate_repeat"],
    )
    film_supercell, film_mappings = replicate_slab_in_plane(
        film,
        selected["film_repeat"],
    )
    substrate_frame = periodic_surface_frame(substrate_supercell)
    film_frame = periodic_surface_frame(film_supercell)
    axes = substrate_frame["periodic_axes"]
    normal_axis = substrate_frame["normal_axis"]
    normal = substrate_frame["normal"]
    target_vectors = [substrate_supercell["cell_ang"][axis] for axis in axes]
    substrate_projections = [dot(site["cartesian_ang"], normal) for site in substrate_supercell["sites"]]
    film_normal = film_frame["normal"]
    film_projections = [dot(site["cartesian_ang"], film_normal) for site in film_supercell["sites"]]
    substrate_min, substrate_max = min(substrate_projections), max(substrate_projections)
    film_min, film_max = min(film_projections), max(film_projections)
    substrate_thickness = substrate_max - substrate_min
    film_thickness = film_max - film_min
    total_normal_length = vacuum_ang + substrate_thickness + gap_ang + film_thickness
    if total_normal_length <= 1.0e-8:
        raise GateError("INTERFACE_CELL_DEGENERATE", "interface normal cell length is degenerate")
    child_cell = [[0.0, 0.0, 0.0] for _ in range(3)]
    child_cell[axes[0]] = target_vectors[0]
    child_cell[axes[1]] = target_vectors[1]
    child_cell[normal_axis] = vector_scale(normal, total_normal_length)
    substrate_start = vacuum_ang / 2.0
    film_start = substrate_start + substrate_thickness + gap_ang
    child_sites: list[dict[str, Any]] = []
    substrate_child_ids: set[str] = set()
    film_child_ids: set[str] = set()
    mappings: list[dict[str, Any]] = []
    substrate_mapping_by_child = {item["child_site_id"]: item for item in substrate_mappings}
    film_mapping_by_child = {item["child_site_id"]: item for item in film_mappings}
    for role, component, component_normal, minimum_projection, start, component_shift in (
        ("substrate", substrate_supercell, normal, substrate_min, substrate_start, [0.0, 0.0]),
        ("film", film_supercell, film_normal, film_min, film_start, shift),
    ):
        mapping_by_child = substrate_mapping_by_child if role == "substrate" else film_mapping_by_child
        for site in component["sites"]:
            u = (site["fractional"][axes[0]] + component_shift[0]) % 1.0
            v = (site["fractional"][axes[1]] + component_shift[1]) % 1.0
            projection = dot(site["cartesian_ang"], component_normal)
            cart = vector_add(
                vector_add(vector_scale(target_vectors[0], u), vector_scale(target_vectors[1], v)),
                vector_scale(normal, start + projection - minimum_projection),
            )
            child_id = f"{'sub' if role == 'substrate' else 'film'}-{site['site_id']}"
            if not SAFE_ID.fullmatch(child_id):
                raise GateError("DERIVED_SITE_ID_INVALID", "interface site identifier is unsafe")
            child_site = json.loads(json.dumps(site))
            child_site["site_id"] = child_id
            child_site["cartesian_ang"] = [round_float(item) for item in cart]
            child_site["fractional"] = [round_float(item) for item in cart_to_frac(cart, child_cell)]
            child_sites.append(child_site)
            (substrate_child_ids if role == "substrate" else film_child_ids).add(child_id)
            source_mapping = mapping_by_child[site["site_id"]]
            mappings.append(
                {
                    "parent_role": role,
                    "parent_site_id": source_mapping["parent_site_id"],
                    "child_site_id": child_id,
                    "relation": source_mapping["relation"],
                    "replica_shift": source_mapping.get("replica_shift", [0, 0, 0]),
                }
            )
    if substrate["charge_state"]["status"] == "known" and film["charge_state"]["status"] == "known":
        charge_state = {
            "status": "known",
            "net_charge_e": substrate["charge_state"]["net_charge_e"] + film["charge_state"]["net_charge_e"],
        }
    else:
        charge_state = {"status": "unknown", "net_charge_e": None}
    child = {
        "contract_name": "structure-preparation-input",
        "schema_version": "1.0",
        "structure_id": "interface-pending",
        "structure_kind": "periodic-slab",
        "pbc": list(substrate["pbc"]),
        "cell_ang": child_cell,
        "sites": child_sites,
        "symmetry": unresolved_symmetry(),
        "charge_state": charge_state,
        "spin_state": {"status": "not-assessed", "multiplicity": None},
    }
    child["structure_id"] = derived_structure_id("interface", child)
    child = validate_structure(child, args.tolerance_ang)
    closest_cross_interface = minimum_distance(
        child,
        left_ids=substrate_child_ids,
        right_ids=film_child_ids,
    )
    closest_full_periodic = enforce_minimum_distance(
        child,
        minimum_distance_ang,
    )
    result = derived_result(
        operation="merge",
        sources=[
            {"role": "substrate", **substrate_source},
            {"role": "film", **film_source},
        ],
        parents=[
            {"role": "substrate", "structure": substrate},
            {"role": "film", "structure": film},
        ],
        child=child,
        mappings=mappings,
        parameters=[
            {"name": "substrate-repeat", "value": selected["substrate_repeat"]},
            {"name": "film-repeat", "value": selected["film_repeat"]},
            {"name": "film-length-strain", "value": selected["film_length_strain"]},
            {"name": "registry-shift-fractional", "value": shift},
            {"name": "gap-ang", "value": gap_ang},
            {"name": "vacuum-ang", "value": vacuum_ang},
            {"name": "minimum-distance-gate-ang", "value": minimum_distance_ang},
        ],
        tolerance_ang=args.tolerance_ang,
        limitations=[
            "The native matcher compares small integer repeats of already oriented slab cells; it does not choose Miller faces or terminations.",
            "The film is coherently mapped onto the selected substrate in-plane cell, so recorded strain is a construction hypothesis.",
            "The selected candidate minimizes geometric mismatch under budgets; it is not an energetic stability result.",
            "Twist-angle and moire enumeration require a separately validated backend route.",
        ],
        extra={
            "operation_family": "interface",
            "operation_profile_id": "native-coherent-slab-interface-v1",
            "match_search": {
                "selection_policy": "minimum-strain-then-angle-then-atom-count",
                "accepted_candidate_count": accepted_count,
                "accepted_candidate_sample_limit": 20,
                "accepted_candidate_sample": accepted_sample,
                "selected": selected,
            },
            "construction_metrics": {
                "substrate_thickness_ang": round_float(substrate_thickness),
                "film_thickness_ang": round_float(film_thickness),
                "closest_cross_interface_pair": closest_cross_interface,
                "closest_full_periodic_pair": closest_full_periodic,
            },
        },
    )
    write_json(result, args.out)
    return EXIT_OK


def command_site_edit(args: argparse.Namespace) -> int:
    value, source = load_json(args.input)
    parent = validate_structure(value, args.tolerance_ang)
    child = json.loads(json.dumps(parent))
    by_id = {site["site_id"]: site for site in child["sites"]}
    mappings = [
        {
            "parent_site_id": site["site_id"],
            "child_site_id": site["site_id"],
            "relation": "same",
        }
        for site in parent["sites"]
    ]
    parameters: list[dict[str, Any]] = []
    edited_child_ids: set[str] = set()
    parent_ids = set(by_id)
    operation_class = args.operation
    if args.operation == "insert":
        if len(parent["sites"]) + 1 > MAX_DERIVED_SITES:
            raise GateError("DERIVED_SITE_BUDGET_EXCEEDED", "inserted structure exceeds the derived-site budget")
        if not any(parent["pbc"]):
            raise GateError("SITE_INSERT_SCOPE_INVALID", "native insertion requires a periodic host")
        if args.site_id in by_id or not SAFE_ID.fullmatch(args.site_id or ""):
            raise GateError("SITE_ID_INVALID", "inserted site_id must be safe and unique")
        if args.element not in ATOMIC_NUMBER:
            raise GateError("ELEMENT_INVALID", "inserted element is unknown")
        if args.fractional is None:
            raise GateError("PARAMETER_MISSING", "insert requires --fractional")
        requested_fractional = [_finite_number(item, "fractional") for item in args.fractional]
        if any(
            not 0.0 <= requested_fractional[axis] <= 1.0
            for axis, periodic in enumerate(parent["pbc"])
            if not periodic
        ):
            raise GateError(
                "INSERTION_OUTSIDE_CELL",
                "inserted site lies outside a nonperiodic cell axis",
            )
        fractional = [
            component % 1.0 if parent["pbc"][axis] else component
            for axis, component in enumerate(requested_fractional)
        ]
        site = {
            "site_id": args.site_id,
            "species": [{"element": args.element, "occupancy": 1.0}],
            "fractional": fractional,
            "cartesian_ang": frac_to_cart(fractional, child["cell_ang"]),
        }
        child["sites"].append(site)
        mappings.append(
            {
                "parent_site_id": None,
                "child_site_id": args.site_id,
                "relation": "created",
            }
        )
        edited_child_ids.add(args.site_id)
        operation_class = "interstitial"
        parameters.extend(
            [
                {"name": "created-site-id", "value": args.site_id},
                {"name": "element", "value": args.element},
                {"name": "requested-fractional-coordinate", "value": requested_fractional},
                {"name": "fractional-coordinate", "value": fractional},
            ]
        )
    elif args.operation == "remove":
        if args.element is not None or args.fractional is not None:
            raise GateError("PARAMETER_CONFLICT", "remove accepts only --site-id and distance/tolerance gates")
        if args.site_id not in by_id:
            raise GateError("SITE_ID_NOT_FOUND", "remove requires an existing --site-id")
        if len(child["sites"]) == 1:
            raise GateError("LAST_SITE_REMOVAL_REFUSED", "cannot remove the only site")
        child["sites"] = [site for site in child["sites"] if site["site_id"] != args.site_id]
        mappings = [
            (
                {
                    "parent_site_id": item["parent_site_id"],
                    "child_site_id": None,
                    "relation": "removed",
                }
                if item["parent_site_id"] == args.site_id
                else item
            )
            for item in mappings
        ]
        operation_class = "remove-sites"
        parameters.append({"name": "removed-site-id", "value": args.site_id})
    elif args.operation == "substitute":
        if args.fractional is not None:
            raise GateError("PARAMETER_CONFLICT", "substitute does not accept --fractional")
        if args.site_id not in by_id:
            raise GateError("SITE_ID_NOT_FOUND", "substitute requires an existing --site-id")
        if args.element not in ATOMIC_NUMBER:
            raise GateError("ELEMENT_INVALID", "substitution element is unknown")
        original_species = by_id[args.site_id]["species"]
        if original_species == [{"element": args.element, "occupancy": 1.0}]:
            raise GateError("NO_OP_REFUSED", "substitution would not change the site")
        by_id[args.site_id]["species"] = [{"element": args.element, "occupancy": 1.0}]
        edited_child_ids.add(args.site_id)
        operation_class = "substitution"
        parameters.extend(
            [
                {"name": "site-id", "value": args.site_id},
                {"name": "parent-species", "value": original_species},
                {"name": "child-element", "value": args.element},
            ]
        )
    else:
        raise GateError("OPERATION_UNSUPPORTED", "site-edit operation is unsupported")
    child["symmetry"] = unresolved_symmetry() if any(child["pbc"]) else child["symmetry"]
    invalidate_electronic_state(child)
    child["structure_id"] = derived_structure_id(operation_class, child)
    child = validate_structure(child, args.tolerance_ang)
    minimum_distance_ang = validate_bounded_float(
        args.min_distance_ang,
        "min_distance_ang",
        minimum=0.0,
        maximum=5.0,
    )
    closest = None
    if edited_child_ids:
        closest = enforce_minimum_distance(
            child,
            minimum_distance_ang,
            left_ids=edited_child_ids,
            right_ids=parent_ids - edited_child_ids,
        )
    result = derived_result(
        operation=operation_class,
        sources=[{"role": "parent", **source}],
        parents=[{"role": "parent", "structure": parent}],
        child=child,
        mappings=mappings,
        parameters=parameters
        + [{"name": "minimum-distance-gate-ang", "value": minimum_distance_ang}],
        tolerance_ang=args.tolerance_ang,
        limitations=[
            "Explicit site edits do not infer oxidation state, charge compensation, magnetic state, or defect formation energy.",
            "An inserted coordinate is a user-specified candidate, not a symmetry-unique or energetically preferred interstitial.",
            "Composition-changing edits invalidate electronic-state and symmetry claims until independently reassessed.",
        ],
        extra={
            "operation_family": "site-edit",
            "operation_profile_id": f"native-{operation_class}-v1",
            "construction_metrics": {"closest_edited_pair": closest},
        },
    )
    write_json(result, args.out)
    return EXIT_OK


def rotate_xyz(vector: list[float], angles_deg: list[float]) -> list[float]:
    x_angle, y_angle, z_angle = [math.radians(item) for item in angles_deg]
    x, y, z = vector
    y, z = y * math.cos(x_angle) - z * math.sin(x_angle), y * math.sin(x_angle) + z * math.cos(x_angle)
    x, z = x * math.cos(y_angle) + z * math.sin(y_angle), -x * math.sin(y_angle) + z * math.cos(y_angle)
    x, y = x * math.cos(z_angle) - y * math.sin(z_angle), x * math.sin(z_angle) + y * math.cos(z_angle)
    return [x, y, z]


def command_place_guest(args: argparse.Namespace) -> int:
    host_value, host_source = load_json(args.host)
    guest_value, guest_source = load_json(args.guest)
    host = validate_structure(host_value, args.tolerance_ang)
    guest = validate_structure(guest_value, args.tolerance_ang)
    if guest["structure_kind"] not in {"isolated-molecule", "isolated-cluster"}:
        raise GateError("GUEST_KIND_INVALID", "guest must be an isolated molecule or cluster")
    if len(host["sites"]) + len(guest["sites"]) > MAX_DERIVED_SITES:
        raise GateError("DERIVED_SITE_BUDGET_EXCEEDED", "combined structure exceeds the derived-site budget")
    guest_by_id = {site["site_id"]: site for site in guest["sites"]}
    if args.anchor_site not in guest_by_id:
        raise GateError("ANCHOR_SITE_INVALID", "anchor-site must identify one guest site")
    angles = [_finite_number(item, "rotation_deg") for item in args.rotation_deg]
    if args.mode == "adsorbate":
        frame = periodic_surface_frame(host)
        if args.target_cart is not None:
            raise GateError("PARAMETER_CONFLICT", "adsorbate mode uses --surface-frac and --height-ang")
        surface_fractional = [_finite_number(item, "surface_frac") % 1.0 for item in args.surface_frac]
        height_ang = validate_bounded_float(args.height_ang, "height_ang", minimum=0.0, maximum=30.0)
        axes = frame["periodic_axes"]
        normal = frame["normal"]
        in_plane_target = vector_add(
            vector_scale(host["cell_ang"][axes[0]], surface_fractional[0]),
            vector_scale(host["cell_ang"][axes[1]], surface_fractional[1]),
        )
        projections = [dot(site["cartesian_ang"], normal) for site in host["sites"]]
        surface_projection = max(projections) if args.side == "top" else min(projections)
        signed_height = height_ang if args.side == "top" else -height_ang
        target = vector_add(in_plane_target, vector_scale(normal, surface_projection + signed_height))
        placement_parameters = [
            {"name": "surface-fractional", "value": surface_fractional},
            {"name": "side", "value": args.side},
            {"name": "height-ang", "value": height_ang},
        ]
        operation_class = "adsorbate"
    elif args.mode == "host-guest":
        if not any(host["pbc"]):
            raise GateError("HOST_KIND_INVALID", "host-guest placement requires a periodic host")
        if args.target_cart is None:
            raise GateError("PARAMETER_MISSING", "host-guest mode requires --target-cart")
        target = [_finite_number(item, "target_cart") for item in args.target_cart]
        placement_parameters = [{"name": "target-cartesian-ang", "value": target}]
        operation_class = "merge"
    else:
        raise GateError("OPERATION_UNSUPPORTED", "guest placement mode is unsupported")
    anchor = guest_by_id[args.anchor_site]["cartesian_ang"]
    child = json.loads(json.dumps(host))
    host_child_ids = {site["site_id"] for site in child["sites"]}
    guest_child_ids: set[str] = set()
    mappings = [
        {
            "parent_role": "host",
            "parent_site_id": site["site_id"],
            "child_site_id": site["site_id"],
            "relation": "same",
        }
        for site in host["sites"]
    ]
    for guest_site in guest["sites"]:
        relative = vector_subtract(guest_site["cartesian_ang"], anchor)
        cart = vector_add(target, rotate_xyz(relative, angles))
        child_id = f"guest-{guest_site['site_id']}"
        if child_id in host_child_ids or not SAFE_ID.fullmatch(child_id):
            raise GateError("DERIVED_SITE_ID_INVALID", "guest site identifier is unsafe or collides with the host")
        child_site = json.loads(json.dumps(guest_site))
        child_site["site_id"] = child_id
        child_site["cartesian_ang"] = [round_float(item) for item in cart]
        child_site["fractional"] = [round_float(item) for item in cart_to_frac(cart, child["cell_ang"])]
        child["sites"].append(child_site)
        guest_child_ids.add(child_id)
        mappings.append(
            {
                "parent_role": "guest",
                "parent_site_id": guest_site["site_id"],
                "child_site_id": child_id,
                "relation": "same",
            }
        )
    nonperiodic_axes = [axis for axis, periodic in enumerate(host["pbc"]) if not periodic]
    if any(
        not 0.0 <= site["fractional"][axis] <= 1.0
        for site in child["sites"]
        if site["site_id"] in guest_child_ids
        for axis in nonperiodic_axes
    ):
        raise GateError(
            "GUEST_OUTSIDE_CELL",
            "guest extends outside a nonperiodic cell axis; change placement or cell size",
        )
    if host["charge_state"]["status"] == "known" and guest["charge_state"]["status"] == "known":
        child["charge_state"] = {
            "status": "known",
            "net_charge_e": host["charge_state"]["net_charge_e"] + guest["charge_state"]["net_charge_e"],
        }
    else:
        child["charge_state"] = {"status": "unknown", "net_charge_e": None}
    child["spin_state"] = {"status": "not-assessed", "multiplicity": None}
    child["symmetry"] = unresolved_symmetry()
    child["structure_id"] = derived_structure_id(operation_class, child)
    child = validate_structure(child, args.tolerance_ang)
    minimum_distance_ang = validate_bounded_float(
        args.min_distance_ang,
        "min_distance_ang",
        minimum=0.0,
        maximum=5.0,
    )
    closest = enforce_minimum_distance(
        child,
        minimum_distance_ang,
        left_ids=host_child_ids,
        right_ids=guest_child_ids,
    )
    result = derived_result(
        operation=operation_class,
        sources=[
            {"role": "host", **host_source},
            {"role": "guest", **guest_source},
        ],
        parents=[
            {"role": "host", "structure": host},
            {"role": "guest", "structure": guest},
        ],
        child=child,
        mappings=mappings,
        parameters=placement_parameters
        + [
            {"name": "anchor-site", "value": args.anchor_site},
            {"name": "rotation-deg-xyz", "value": angles},
            {"name": "minimum-distance-gate-ang", "value": minimum_distance_ang},
        ],
        tolerance_ang=args.tolerance_ang,
        limitations=[
            "Placement uses an explicit anchor, orientation, and position; it does not search adsorption or pore sites.",
            "The minimum-distance gate rejects hard overlaps but does not evaluate bonding, energy, diffusion, or stability.",
            "Coverage, charge transfer, dipole corrections, and relaxation settings remain downstream decisions.",
        ],
        extra={
            "operation_family": args.mode,
            "operation_profile_id": f"native-{args.mode}-placement-v1",
            "construction_metrics": {"closest_host_guest_pair": closest},
        },
    )
    write_json(result, args.out)
    return EXIT_OK


def command_import_cif_manifest(args: argparse.Namespace) -> int:
    value, source = load_json(args.input)
    child, mappings = import_cif_manifest(value, args.tolerance_ang)
    audit = audit_report(
        child,
        {"label": "embedded-child", "bytes": 0, "sha256": digest(child)},
        args.tolerance_ang,
    )
    report = {
        "contract_name": "structure-preparation-import",
        "schema_version": "1.0",
        "status": "pass",
        "source": source,
        "upstream_contract": "structure-manifest@1.0",
        "upstream_manifest_id": value["manifest_id"],
        "upstream_structure_identity": value["structure_identity"],
        "upstream_status": value["status"],
        "mapping_status": "exact",
        "site_mapping": mappings,
        "site_mapping_sha256": digest(mappings),
        "child": child,
        "child_identity": structure_identity(child),
        "child_calculation_readiness": audit["calculation_readiness"],
        "findings": audit["findings"],
        **candidate_lifecycle("input_gates_only"),
        "limitations": [
            "Schema and published-payload consistency do not re-parse the source CIF bytes.",
            "The staging record carries unknown charge and unassessed spin.",
            "Import preserves the representative materialized model only after refusing unresolved occupancy or disorder.",
            "A successful import does not establish structure stability or calculation readiness.",
        ],
        "provenance": {"tool": "structure_prepare.py", "tool_version": TOOL_VERSION},
    }
    write_json(report, args.out)
    return EXIT_OK


def command_audit(args: argparse.Namespace) -> int:
    value, source = load_json(args.input)
    structure = validate_structure(value, args.tolerance_ang)
    report = audit_report(structure, source, args.tolerance_ang)
    write_json(report, args.out)
    if args.require_calculation_ready and report["calculation_readiness"] != "ready":
        return EXIT_BLOCKED
    return EXIT_OK


def command_roundtrip(args: argparse.Namespace) -> int:
    parent_value, parent_source = load_json(args.parent)
    child_value, child_source = load_json(args.child)
    parent = validate_structure(parent_value, args.tolerance_ang)
    child = validate_structure(child_value, args.tolerance_ang)
    comparison = compare_structures(parent, child, args.tolerance_ang)
    report = {
        "contract_name": "structure-roundtrip-report",
        "schema_version": "1.0",
        "status": "pass" if comparison["classification"] in {"exact", "equivalent"} else "blocked",
        "parent_source": parent_source,
        "child_source": child_source,
        "roundtrip": comparison,
        "findings": (
            []
            if comparison["classification"] in {"exact", "equivalent"}
            else [
                {
                    "finding_id": "ROUNDTRIP_LOSSY",
                    "severity": "blocker",
                    "message": "one or more identity, representation, mapping, or tolerance invariants differ",
                }
            ]
        ),
        **candidate_lifecycle("input_gates_only"),
        "provenance": {"tool": "structure_prepare.py", "tool_version": TOOL_VERSION},
    }
    write_json(report, args.out)
    return EXIT_OK if report["status"] == "pass" else EXIT_BLOCKED


def command_transform(args: argparse.Namespace) -> int:
    value, source = load_json(args.input)
    parent = validate_structure(value, args.tolerance_ang)
    max_strain = validate_bounded_float(
        args.max_strain,
        "max_strain",
        minimum=0.0,
        maximum=1.0,
        include_minimum=True,
    )
    child, mappings, parameters = transformed_structure(
        parent,
        args.operation,
        args.order,
        args.repeat,
        args.matrix,
        args.deformation,
        max_strain,
    )
    child = validate_structure(child, args.tolerance_ang)
    parent_identity = structure_identity(parent)
    child_identity = structure_identity(child)
    if args.operation in {"wrap", "reorder"}:
        roundtrip = compare_structures(parent, child, args.tolerance_ang)
        if roundtrip["classification"] not in {"exact", "equivalent"}:
            raise GateError("TRANSFORM_INVARIANT_FAILED", "identity-preserving operation failed its round-trip gate")
    else:
        roundtrip = {
            "classification": "not-applicable-derived-structure",
            "tolerance_ang": args.tolerance_ang,
            "parent_identity": parent_identity,
            "child_identity": child_identity,
            "site_mapping": mappings,
            "site_mapping_sha256": digest(mappings),
            "differences": ["cell", "site-replication"],
        }
    child_audit = audit_report(child, {"label": "embedded-child", "bytes": 0, "sha256": digest(child)}, args.tolerance_ang)
    result = {
        "contract_name": "structure-preparation-result",
        "schema_version": "1.0",
        "status": "pass",
        "source": source,
        "operation": args.operation,
        "parameters": parameters,
        "parent_identity": parent_identity,
        "child_identity": child_identity,
        "mapping_status": "exact",
        "site_mapping": mappings,
        "site_mapping_sha256": digest(mappings),
        "roundtrip": roundtrip,
        "child": child,
        "child_calculation_readiness": child_audit["calculation_readiness"],
        "findings": child_audit["findings"],
        **candidate_lifecycle("input_gates_only"),
        "limitations": [
            "This candidate transform does not validate a DFT code-specific export.",
            "Symmetry is invalidated after cell-changing construction until recomputed by a pinned backend.",
            "A deterministic structure transform does not establish energetic or physical stability.",
        ],
        "provenance": {"tool": "structure_prepare.py", "tool_version": TOOL_VERSION},
    }
    write_json(result, args.out)
    return EXIT_OK


def command_plan_export(args: argparse.Namespace) -> int:
    value, source = load_json(args.input)
    structure = validate_structure(value, args.tolerance_ang)
    audit = audit_report(structure, source, args.tolerance_ang)
    handoff_roles = {
        "qe": ["structure-input-section"],
        "vasp": ["structure-input-file"],
        "cp2k": ["cell-section", "coordinate-section"],
        "siesta": ["lattice-block", "atomic-coordinate-block"],
    }
    ready = audit["calculation_readiness"] == "ready"
    report = {
        "contract_name": "structure-export-plan",
        "schema_version": "1.0",
        "status": "planned" if ready else "blocked",
        "source": source,
        "snapshot_identity": audit["identity"],
        "target_code": args.target,
        "requested_target_roles": handoff_roles[args.target],
        "generated_target_files": [],
        "target_write_performed": False,
        "target_parameter_selection_performed": False,
        "atom_order_mapping": [
            {"site_id": site["site_id"], "target_ordinal": ordinal}
            for ordinal, site in enumerate(structure["sites"])
        ],
        "source_coordinate_unit": "angstrom",
        "target_coordinate_unit": "unresolved-by-target-skill",
        "code_parameters": {
            "status": "unresolved",
            "owner": f"{args.target}-rigorous-calculations",
            "values": [],
        },
        "execution_state": "not-executed",
        "readiness_findings": [
            item for item in audit["findings"] if item["severity"] in {"blocker", "warning"}
        ],
        **candidate_lifecycle("input_gates_only"),
        "limitations": [
            "This is an export plan, not a generated or parser-round-tripped code input.",
            "Code-specific calculation parameters remain owned by the target rigorous-calculation skill.",
        ],
        "provenance": {"tool": "structure_prepare.py", "tool_version": TOOL_VERSION},
    }
    write_json(report, args.out)
    return EXIT_OK if ready else EXIT_BLOCKED


def command_probe(args: argparse.Namespace) -> int:
    distributions = []
    all_match = True
    for name, expected in EXPECTED_DISTRIBUTIONS.items():
        try:
            observed = importlib.metadata.version(name)
            state = "match" if observed == expected else "version-mismatch"
        except importlib.metadata.PackageNotFoundError:
            observed = None
            state = "not-installed"
        if state != "match":
            all_match = False
        distributions.append(
            {"distribution": name, "expected_version": expected, "observed_version": observed, "state": state}
        )
    report = {
        "contract_name": "structure-backend-probe",
        "schema_version": "1.0",
        "status": "available" if all_match else "unavailable",
        "probe_kind": "distribution-metadata-only",
        "imports_performed": False,
        "operations_executed": False,
        "distributions": distributions,
        **candidate_lifecycle("documented_behavior_only"),
        "provenance": {"tool": "structure_prepare.py", "tool_version": TOOL_VERSION},
    }
    write_json(report, args.out)
    return EXIT_OK if all_match else EXIT_UNAVAILABLE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_manifest = subparsers.add_parser(
        "import-cif-manifest",
        help="validate and adapt one active CIF structure-manifest into the candidate staging contract",
    )
    import_manifest.add_argument("input")
    import_manifest.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    import_manifest.add_argument("--out")
    import_manifest.set_defaults(handler=command_import_cif_manifest)

    audit = subparsers.add_parser("audit", help="validate identity, periodicity, occupancy, symmetry, charge, and spin gates")
    audit.add_argument("input")
    audit.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    audit.add_argument("--require-calculation-ready", action="store_true")
    audit.add_argument("--out")
    audit.set_defaults(handler=command_audit)

    transform = subparsers.add_parser("transform", help="perform a deterministic candidate-local transform")
    transform.add_argument("input")
    transform.add_argument("--operation", choices=["wrap", "reorder", "supercell", "strain"], required=True)
    transform.add_argument("--order", help="comma-separated site_id order for reorder")
    transform.add_argument("--repeat", type=int, nargs=3, metavar=("NX", "NY", "NZ"))
    transform.add_argument("--matrix", type=int, nargs=9, metavar=("M11", "M12", "M13", "M21", "M22", "M23", "M31", "M32", "M33"))
    transform.add_argument(
        "--deformation",
        type=float,
        nargs=9,
        metavar=("F11", "F12", "F13", "F21", "F22", "F23", "F31", "F32", "F33"),
    )
    transform.add_argument("--max-strain", type=float, default=0.25)
    transform.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    transform.add_argument("--out")
    transform.set_defaults(handler=command_transform)

    slab = subparsers.add_parser("make-slab", help="build a lattice-axis slab with explicit layers and vacuum")
    slab.add_argument("input")
    slab.add_argument("--axis", type=int, choices=[0, 1, 2], default=2)
    slab.add_argument("--layers", type=int, required=True)
    slab.add_argument("--vacuum-ang", type=float, required=True)
    slab.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    slab.add_argument("--out")
    slab.set_defaults(handler=command_make_slab)

    interface = subparsers.add_parser(
        "build-interface",
        help="search bounded in-plane repeats and construct one coherent slab interface candidate",
    )
    interface.add_argument("substrate")
    interface.add_argument("film")
    interface.add_argument("--max-repeat", type=int, default=6)
    interface.add_argument("--max-strain", type=float, default=0.08)
    interface.add_argument("--max-angle-deg", type=float, default=2.0)
    interface.add_argument("--max-atoms", type=int, default=512)
    interface.add_argument("--registry-shift", type=float, nargs=2, metavar=("U", "V"), default=[0.0, 0.0])
    interface.add_argument("--gap-ang", type=float, required=True)
    interface.add_argument("--vacuum-ang", type=float, required=True)
    interface.add_argument("--min-distance-ang", type=float, default=0.5)
    interface.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    interface.add_argument("--out")
    interface.set_defaults(handler=command_build_interface)

    site_edit = subparsers.add_parser(
        "site-edit",
        help="insert, remove, or substitute one explicitly identified site",
    )
    site_edit.add_argument("input")
    site_edit.add_argument("--operation", choices=["insert", "remove", "substitute"], required=True)
    site_edit.add_argument("--site-id", required=True)
    site_edit.add_argument("--element")
    site_edit.add_argument("--fractional", type=float, nargs=3, metavar=("F1", "F2", "F3"))
    site_edit.add_argument("--min-distance-ang", type=float, default=0.5)
    site_edit.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    site_edit.add_argument("--out")
    site_edit.set_defaults(handler=command_site_edit)

    guest = subparsers.add_parser(
        "place-guest",
        help="place an isolated molecule or cluster on a slab or inside a periodic host",
    )
    guest.add_argument("host")
    guest.add_argument("guest")
    guest.add_argument("--mode", choices=["adsorbate", "host-guest"], required=True)
    guest.add_argument("--anchor-site", required=True)
    guest.add_argument("--surface-frac", type=float, nargs=2, metavar=("U", "V"), default=[0.0, 0.0])
    guest.add_argument("--height-ang", type=float, default=2.0)
    guest.add_argument("--side", choices=["top", "bottom"], default="top")
    guest.add_argument("--target-cart", type=float, nargs=3, metavar=("X", "Y", "Z"))
    guest.add_argument("--rotation-deg", type=float, nargs=3, metavar=("RX", "RY", "RZ"), default=[0.0, 0.0, 0.0])
    guest.add_argument("--min-distance-ang", type=float, default=0.5)
    guest.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    guest.add_argument("--out")
    guest.set_defaults(handler=command_place_guest)

    roundtrip = subparsers.add_parser("roundtrip", help="compare exact representation and periodic structural equivalence")
    roundtrip.add_argument("parent")
    roundtrip.add_argument("child")
    roundtrip.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    roundtrip.add_argument("--out")
    roundtrip.set_defaults(handler=command_roundtrip)

    export = subparsers.add_parser("plan-export", help="create a non-executed DFT structure export plan")
    export.add_argument("input")
    export.add_argument("--target", choices=["qe", "vasp", "cp2k", "siesta"], required=True)
    export.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    export.add_argument("--out")
    export.set_defaults(handler=command_plan_export)

    probe = subparsers.add_parser("probe-backends", help="inspect pinned optional distribution metadata without importing it")
    probe.add_argument("--out")
    probe.set_defaults(handler=command_probe)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "tolerance_ang") and (
        not math.isfinite(args.tolerance_ang) or args.tolerance_ang <= 0.0 or args.tolerance_ang > 0.1
    ):
        error = GateError("TOLERANCE_INVALID", "tolerance must be finite, positive, and at most 0.1 angstrom")
        sys.stderr.write(
            json.dumps(
                error_envelope(error.finding_id, error.message),
                sort_keys=True,
            )
            + "\n"
        )
        return error.exit_code
    try:
        return int(args.handler(args))
    except GateError as exc:
        sys.stderr.write(
            json.dumps(
                error_envelope(
                    exc.finding_id,
                    exc.message,
                    status="unavailable" if exc.exit_code == EXIT_UNAVAILABLE else "blocked",
                ),
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
