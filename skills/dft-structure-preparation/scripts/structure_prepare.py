#!/usr/bin/env python3
"""Deterministic, fail-closed structure preparation candidate CLI."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
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
TOOL_VERSION = "0.1.0-candidate"
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


def transformed_structure(
    parent: dict[str, Any], operation: str, order: str | None, repeat: list[int] | None
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    child = json.loads(json.dumps(parent))
    mappings: list[dict[str, Any]] = []
    parameters: list[dict[str, Any]] = []
    if operation == "wrap":
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
        if repeat is None or len(repeat) != 3 or any(type(item) is not int or item < 1 for item in repeat):
            raise GateError("SUPERCELL_PARAMETER_INVALID", "--repeat requires three positive integers")
        if not all(parent["pbc"]):
            raise GateError("OPERATION_SCOPE_INVALID", "candidate supercell requires three-dimensional periodicity")
        nx, ny, nz = repeat
        derived_site_count = len(parent["sites"]) * nx * ny * nz
        if derived_site_count > MAX_DERIVED_SITES:
            raise GateError(
                "SUPERCELL_BUDGET_EXCEEDED",
                f"derived site count {derived_site_count} exceeds candidate limit {MAX_DERIVED_SITES}",
            )
        child["cell_ang"] = [[item * repeat[i] for item in row] for i, row in enumerate(parent["cell_ang"])]
        sites: list[dict[str, Any]] = []
        for parent_site in parent["sites"]:
            canonical_parent = [component % 1.0 for component in parent_site["fractional"]]
            parent_image_shift = [
                int(round(parent_site["fractional"][axis] - canonical_parent[axis])) for axis in range(3)
            ]
            for i in range(nx):
                for j in range(ny):
                    for k in range(nz):
                        child_site = json.loads(json.dumps(parent_site))
                        child_site["site_id"] = f"{parent_site['site_id']}__{i}_{j}_{k}"
                        if not SAFE_ID.fullmatch(child_site["site_id"]):
                            raise GateError("DERIVED_SITE_ID_INVALID", "derived supercell site_id is too long or unsafe")
                        child_site["fractional"] = [
                            (canonical_parent[0] + i) / nx,
                            (canonical_parent[1] + j) / ny,
                            (canonical_parent[2] + k) / nz,
                        ]
                        child_site["cartesian_ang"] = frac_to_cart(child_site["fractional"], child["cell_ang"])
                        sites.append(child_site)
                        mappings.append(
                            {
                                "parent_site_id": parent_site["site_id"],
                                "child_site_id": child_site["site_id"],
                                "relation": "replicated",
                                "parent_image_shift_to_canonical": parent_image_shift,
                                "replica_shift": [i, j, k],
                            }
                        )
        child["sites"] = sites
        child["symmetry"] = {
            "status": "unresolved",
            "number": None,
            "symbol": None,
            "tolerance_ang": None,
            "backend": None,
            "backend_version": None,
        }
        parameters.append({"name": "diagonal-repeat", "value": repeat})
    else:
        raise GateError("OPERATION_UNSUPPORTED", "operation is not implemented by this candidate")
    child_identity = structure_identity(child)
    child["structure_id"] = f"{parent['structure_id']}--{operation}--{child_identity['structure_sha256'][:8]}"
    if not SAFE_ID.fullmatch(child["structure_id"]):
        child["structure_id"] = f"derived-{child_identity['structure_sha256'][:16]}"
    return child, mappings, parameters


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
    child, mappings, parameters = transformed_structure(parent, args.operation, args.order, args.repeat)
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
            "Symmetry is invalidated after supercell construction until recomputed by a pinned backend.",
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

    audit = subparsers.add_parser("audit", help="validate identity, periodicity, occupancy, symmetry, charge, and spin gates")
    audit.add_argument("input")
    audit.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    audit.add_argument("--require-calculation-ready", action="store_true")
    audit.add_argument("--out")
    audit.set_defaults(handler=command_audit)

    transform = subparsers.add_parser("transform", help="perform a deterministic candidate-local transform")
    transform.add_argument("input")
    transform.add_argument("--operation", choices=["wrap", "reorder", "supercell"], required=True)
    transform.add_argument("--order", help="comma-separated site_id order for reorder")
    transform.add_argument("--repeat", type=int, nargs=3, metavar=("NX", "NY", "NZ"))
    transform.add_argument("--tolerance-ang", type=float, default=1.0e-8)
    transform.add_argument("--out")
    transform.set_defaults(handler=command_transform)

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
