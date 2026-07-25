from __future__ import annotations

from collections import Counter
import math
import re
from typing import Any


def _declared_formula_counts(raw: object) -> tuple[dict[str, float] | None, str | None]:
    if not isinstance(raw, str) or raw.strip() in {"", ".", "?"}:
        return None, "declared formula is unavailable"
    try:
        from ase.formula import Formula

        compact = re.sub(r"\s+", "", raw)
        counts = {
            str(symbol): float(value)
            for symbol, value in Formula(compact).count().items()
        }
    except Exception as exc:
        return None, f"declared formula could not be parsed: {exc}"
    if not counts or any(not math.isfinite(value) or value <= 0 for value in counts.values()):
        return None, "declared formula did not produce positive finite element counts"
    return dict(sorted(counts.items())), None


def _normalized_counts(counts: dict[str, float]) -> dict[str, float]:
    total = sum(float(value) for value in counts.values())
    return {
        symbol: float(value) / total
        for symbol, value in sorted(counts.items())
    }


def _counts_match(
    left: dict[str, float], right: dict[str, float], tolerance: float = 1e-6
) -> bool:
    if set(left) != set(right):
        return False
    return all(
        math.isclose(float(left[symbol]), float(right[symbol]), rel_tol=tolerance, abs_tol=tolerance)
        for symbol in left
    )


def analyze_structure_quality(
    atoms: Any,
    metadata: dict[str, Any],
    short_flags: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    import numpy as np

    checks: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    materialized_counts = {
        str(symbol): float(count)
        for symbol, count in sorted(Counter(atoms.get_chemical_symbols()).items())
    }
    declared_formula = (
        metadata.get("declared_formula", {}).get("sum", {}).get("value")
    )
    declared_counts, formula_error = _declared_formula_counts(declared_formula)
    z_value = (
        metadata.get("declared_formula", {})
        .get("formula_units_z", {})
        .get("value")
    )
    partial_rows = list(metadata.get("partial_occupancy_rows", []))
    disorder_rows = list(metadata.get("disorder_rows", []))

    formula_status = "NOT_COMPARABLE"
    formula_mode = "none"
    expected_cell_counts: dict[str, float] | None = None
    formula_message = formula_error or "formula comparison was not attempted"
    if partial_rows or disorder_rows:
        formula_message = (
            "formula comparison is not accepted for the representative materialized "
            "model because partial occupancy or disorder metadata is present"
        )
    elif declared_counts is not None:
        normalized_declared = _normalized_counts(declared_counts)
        normalized_materialized = _normalized_counts(materialized_counts)
        formula_mode = "reduced-ratio"
        formula_status = (
            "MATCH"
            if _counts_match(normalized_declared, normalized_materialized)
            else "MISMATCH"
        )
        formula_message = (
            "declared and materialized element ratios match"
            if formula_status == "MATCH"
            else "declared and materialized element ratios differ"
        )
        if z_value is not None and math.isfinite(float(z_value)) and float(z_value) > 0:
            expected_cell_counts = {
                symbol: float(value) * float(z_value)
                for symbol, value in declared_counts.items()
            }
            formula_mode = "formula-times-z"
            formula_status = (
                "MATCH"
                if _counts_match(expected_cell_counts, materialized_counts)
                else "MISMATCH"
            )
            formula_message = (
                "declared formula multiplied by Z matches the materialized cell"
                if formula_status == "MATCH"
                else "declared formula multiplied by Z differs from the materialized cell"
            )
    checks.append(
        {
            "id": "formula-materialization-consistency",
            "status": formula_status,
            "message": formula_message,
        }
    )
    if formula_status == "MISMATCH":
        diagnostics.append(
            {
                "id": "declared-materialized-formula-mismatch",
                "status": "warn",
                "message": formula_message,
            }
        )

    lattice = np.asarray(atoms.cell.array, dtype=float)
    determinant = float(np.linalg.det(lattice)) if lattice.shape == (3, 3) else 0.0
    condition_number = (
        float(np.linalg.cond(lattice))
        if atoms.cell.rank == 3 and abs(determinant) > 1e-12
        else None
    )
    cell_status = "PASS"
    cell_message = "cell is full-rank with finite determinant and condition number"
    if (
        atoms.cell.rank != 3
        or not math.isfinite(determinant)
        or abs(determinant) <= 1e-10
        or condition_number is None
        or not math.isfinite(condition_number)
    ):
        cell_status = "FAIL"
        cell_message = "cell is singular, non-finite, or not three-dimensional"
    elif condition_number > 1e6:
        cell_status = "WARN"
        cell_message = "cell is numerically ill-conditioned"
    checks.append(
        {
            "id": "cell-numerical-quality",
            "status": cell_status,
            "message": cell_message,
        }
    )
    if cell_status != "PASS":
        diagnostics.append(
            {
                "id": "cell-numerical-quality",
                "status": "fail" if cell_status == "FAIL" else "warn",
                "message": cell_message,
            }
        )

    contact_status = "PASS" if not short_flags else "WARN"
    contact_message = (
        "no periodic edge is below the configured short-distance threshold"
        if not short_flags
        else f"{len(short_flags)} periodic edge(s) are below the configured short-distance threshold"
    )
    checks.append(
        {
            "id": "configured-short-contact-screen",
            "status": contact_status,
            "message": contact_message,
        }
    )

    overall = "PASS"
    if any(item["status"] == "FAIL" for item in checks):
        overall = "FAIL"
    elif any(item["status"] in {"WARN", "MISMATCH", "NOT_COMPARABLE"} for item in checks):
        overall = "WARN"
    return (
        {
            "method_version": "cif-structure-quality-v1",
            "status": overall,
            "formula_consistency": {
                "status": formula_status,
                "comparison_mode": formula_mode,
                "declared_formula": declared_formula,
                "declared_counts": declared_counts,
                "formula_units_z": z_value,
                "expected_cell_counts": expected_cell_counts,
                "materialized_counts": materialized_counts,
                "representative_model_limited": bool(partial_rows or disorder_rows),
            },
            "cell_numerics": {
                "rank": int(atoms.cell.rank),
                "determinant_ang3": determinant,
                "absolute_determinant_ang3": abs(determinant),
                "condition_number": condition_number,
            },
            "short_contact_count": len(short_flags),
            "partial_occupancy_present": bool(partial_rows),
            "disorder_metadata_present": bool(disorder_rows),
            "checks": checks,
            "claim_boundary": (
                "Quality findings identify input consistency and review needs; "
                "they do not establish energetic, dynamic, or thermodynamic stability."
            ),
        },
        diagnostics,
    )
