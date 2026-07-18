from __future__ import annotations

import importlib.metadata
import math
from typing import Any


def _plain(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if hasattr(value, "tolist"):
        return _plain(value.tolist())
    if hasattr(value, "item"):
        return _plain(value.item())
    if isinstance(value, float):
        return round(value, 10) if math.isfinite(value) else None
    return value


def _field(dataset: Any, name: str) -> Any:
    if isinstance(dataset, dict):
        return dataset.get(name)
    return getattr(dataset, name, None)


def _cell_tuple(atoms: Any) -> tuple[Any, Any, Any]:
    return (
        atoms.cell.array,
        atoms.get_scaled_positions(wrap=True),
        atoms.get_atomic_numbers(),
    )


def _standardized_summary(spglib: Any, cell: tuple[Any, Any, Any], to_primitive: bool, symprec: float, angle_tolerance: float) -> dict[str, Any]:
    import numpy as np

    standardized = spglib.standardize_cell(
        cell,
        to_primitive=to_primitive,
        no_idealize=False,
        symprec=symprec,
        angle_tolerance=angle_tolerance,
    )
    if standardized is None:
        return {"status": "FAILED", "reason": "spglib returned no standardized cell"}
    lattice, positions, numbers = standardized
    return {
        "status": "GENERATED",
        "atom_count": len(numbers),
        "volume_ang3": round(abs(float(np.linalg.det(lattice))), 10),
        "lattice_vectors_ang": _plain(lattice),
        "fractional_positions": _plain(positions),
        "atomic_numbers": _plain(numbers),
    }


def _declared_comparison(dataset: Any, declared: dict[str, Any] | None) -> dict[str, Any]:
    declared = declared or {}
    declared_number = (declared.get("international_tables_number") or {}).get("value")
    declared_hm = (declared.get("hermann_mauguin") or {}).get("value")
    detected_number = _field(dataset, "number")
    detected_hm = _field(dataset, "international")
    number_match = None
    if declared_number is not None and detected_number is not None:
        number_match = int(round(float(declared_number))) == int(detected_number)
    symbol_match = None
    if declared_hm and detected_hm:
        normalize = lambda value: (
            "".join(str(value).split()).replace("_", "").replace("−", "-").casefold()
        )
        symbol_match = normalize(declared_hm) == normalize(detected_hm)
    checks = [item for item in (number_match, symbol_match) if item is not None]
    if not checks:
        status = "NOT_COMPARABLE"
    elif all(checks):
        status = "MATCH"
    else:
        status = "MISMATCH"
    return {
        "status": status,
        "declared_number": int(round(float(declared_number))) if declared_number is not None else None,
        "detected_number": int(detected_number) if detected_number is not None else None,
        "number_match": number_match,
        "declared_hermann_mauguin": declared_hm,
        "detected_hermann_mauguin": detected_hm,
        "symbol_match": symbol_match,
    }


def analyze_symmetry(
    atoms: Any,
    symprec: float,
    angle_tolerance: float,
    declared: dict[str, Any] | None,
    has_partial_occupancy: bool = False,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    diagnostics: list[dict[str, str]] = []
    try:
        import spglib
    except Exception as exc:
        diagnostics.append(
            {
                "id": "symmetry-backend-unavailable",
                "status": "warn",
                "message": f"spglib symmetry analysis is unavailable: {exc}",
            }
        )
        return (
            {
                "available": False,
                "status": "SKIPPED",
                "reason": "spglib unavailable",
                "symprec": symprec,
                "angle_tolerance": angle_tolerance,
            },
            diagnostics,
        )

    cell = _cell_tuple(atoms)
    try:
        dataset = spglib.get_symmetry_dataset(
            cell,
            symprec=symprec,
            angle_tolerance=angle_tolerance,
        )
    except Exception as exc:
        diagnostics.append(
            {
                "id": "symmetry-detection-failed",
                "status": "warn",
                "message": f"spglib symmetry detection failed: {exc}",
            }
        )
        return (
            {
                "available": True,
                "status": "FAILED",
                "reason": str(exc),
                "symprec": symprec,
                "angle_tolerance": angle_tolerance,
            },
            diagnostics,
        )
    if dataset is None:
        diagnostics.append(
            {
                "id": "symmetry-no-dataset",
                "status": "warn",
                "message": "spglib returned no symmetry dataset",
            }
        )
        return (
            {
                "available": True,
                "status": "FAILED",
                "reason": "no dataset",
                "symprec": symprec,
                "angle_tolerance": angle_tolerance,
            },
            diagnostics,
        )

    comparison = _declared_comparison(dataset, declared)
    if comparison["status"] == "MISMATCH":
        diagnostics.append(
            {
                "id": "declared-detected-symmetry-mismatch",
                "status": "warn",
                "message": (
                    "CIF-declared symmetry does not match the symmetry detected from the selected "
                    "structure at the requested tolerance"
                ),
            }
        )
    if has_partial_occupancy:
        diagnostics.append(
            {
                "id": "symmetry-partial-occupancy-limitation",
                "status": "warn",
                "message": "spglib species labels do not represent mixed/partial site occupancy",
            }
        )

    sweep = []
    tolerances = sorted({max(symprec / 10.0, 1e-8), symprec, symprec * 10.0})
    for tolerance in tolerances:
        try:
            trial = spglib.get_symmetry_dataset(
                cell,
                symprec=tolerance,
                angle_tolerance=angle_tolerance,
            )
        except Exception as exc:
            trial = None
            diagnostics.append(
                {
                    "id": "symmetry-tolerance-sweep-failed",
                    "status": "warn",
                    "message": f"spglib tolerance sweep failed at symprec={tolerance}: {exc}",
                }
            )
        sweep.append(
            {
                "symprec": tolerance,
                "status": "DETECTED" if trial is not None else "FAILED",
                "number": _plain(_field(trial, "number")) if trial is not None else None,
                "international": _plain(_field(trial, "international")) if trial is not None else None,
            }
        )
    detected_signatures = {
        (item["number"], item["international"])
        for item in sweep
        if item["status"] == "DETECTED"
    }
    if len(detected_signatures) > 1:
        diagnostics.append(
            {
                "id": "symmetry-tolerance-sensitive",
                "status": "warn",
                "message": "detected space group changes across the recorded symprec sweep",
            }
        )

    try:
        primitive = _standardized_summary(
            spglib, cell, True, symprec, angle_tolerance
        )
        conventional = _standardized_summary(
            spglib, cell, False, symprec, angle_tolerance
        )
    except Exception as exc:
        primitive = conventional = {"status": "FAILED", "reason": str(exc)}
        diagnostics.append(
            {
                "id": "symmetry-standardization-failed",
                "status": "warn",
                "message": f"spglib cell standardization failed: {exc}",
            }
        )

    rotations = _field(dataset, "rotations")
    backend_version = getattr(spglib, "__version__", None)
    if not backend_version:
        try:
            backend_version = importlib.metadata.version("spglib")
        except importlib.metadata.PackageNotFoundError:
            backend_version = "unknown"
    result = {
        "available": True,
        "backend": "spglib",
        "backend_version": str(backend_version),
        "status": "DETECTED",
        "symprec": symprec,
        "angle_tolerance": angle_tolerance,
        "number": _plain(_field(dataset, "number")),
        "international": _plain(_field(dataset, "international")),
        "hall": _plain(_field(dataset, "hall")),
        "choice": _plain(_field(dataset, "choice")),
        "pointgroup": _plain(_field(dataset, "pointgroup")),
        "wyckoffs": _plain(_field(dataset, "wyckoffs")),
        "site_symmetry_symbols": _plain(_field(dataset, "site_symmetry_symbols")),
        "equivalent_atoms": _plain(_field(dataset, "equivalent_atoms")),
        "mapping_to_primitive": _plain(_field(dataset, "mapping_to_primitive")),
        "transformation_matrix": _plain(_field(dataset, "transformation_matrix")),
        "origin_shift": _plain(_field(dataset, "origin_shift")),
        "operation_count": len(rotations) if rotations is not None else 0,
        "declared_comparison": comparison,
        "tolerance_sweep": sweep,
        "tolerance_sensitive": len(detected_signatures) > 1,
        "standardized_cells": {
            "primitive": primitive,
            "conventional": conventional,
        },
        "partial_occupancy_supported": not has_partial_occupancy,
    }
    return result, diagnostics
