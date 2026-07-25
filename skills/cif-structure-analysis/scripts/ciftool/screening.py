from __future__ import annotations

from typing import Any


CENTROSYMMETRIC_POINT_GROUPS = {
    "-1",
    "2/m",
    "mmm",
    "4/m",
    "4/mmm",
    "-3",
    "-3m",
    "6/m",
    "6/mmm",
    "m-3",
    "m-3m",
}
POLAR_POINT_GROUPS = {"1", "2", "m", "mm2", "4", "4mm", "3", "3m", "6", "6mm"}
D_OR_F_BLOCK_RANGES = ((21, 30), (39, 48), (57, 80), (89, 112))


def _normalized_point_group(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.replace(" ", "").replace("−", "-")
    return {
        "-4m2": "-42m",
        "-62m": "-6m2",
    }.get(normalized, normalized)


def analyze_property_screening(
    atoms: Any,
    symmetry: dict[str, Any],
    connectivity: dict[str, Any],
) -> dict[str, Any]:
    point_group = _normalized_point_group(symmetry.get("pointgroup"))
    symmetry_available = symmetry.get("status") == "DETECTED" and point_group is not None
    centrosymmetric = (
        point_group in CENTROSYMMETRIC_POINT_GROUPS if symmetry_available else None
    )
    piezoelectric_allowed = (
        (not centrosymmetric and point_group != "432")
        if centrosymmetric is not None
        else None
    )
    polar = point_group in POLAR_POINT_GROUPS if symmetry_available else None
    electric_dipole_shg_allowed = (
        not centrosymmetric if centrosymmetric is not None else None
    )

    lengths = [float(value) for value in atoms.cell.lengths() if float(value) > 0]
    metric_ratio = max(lengths) / min(lengths) if lengths else None
    symbols = atoms.get_chemical_symbols()
    numbers = atoms.get_atomic_numbers()
    d_or_f_elements = sorted(
        {
            symbol
            for symbol, number in zip(symbols, numbers)
            if any(low <= int(number) <= high for low, high in D_OR_F_BLOCK_RANGES)
        }
    )

    hypotheses = []
    if piezoelectric_allowed is not None:
        hypotheses.append(
            {
                "id": "piezoelectric-symmetry-screen",
                "status": "ALLOWED" if piezoelectric_allowed else "FORBIDDEN",
                "basis": f"detected crystallographic point group {point_group}",
                "limitation": (
                    "Symmetry determines whether the ordinary bulk tensor is allowed; "
                    "it does not establish a nonzero coefficient or ferroelectric switching."
                ),
            }
        )
    if polar is not None:
        hypotheses.append(
            {
                "id": "polar-point-group-screen",
                "status": "CANDIDATE" if polar else "NOT_POLAR_BY_POINT_GROUP",
                "basis": f"detected crystallographic point group {point_group}",
                "limitation": (
                    "A polar point group permits a spontaneous polar direction but does "
                    "not establish switchability, polarization magnitude, or phase stability."
                ),
            }
        )
    if electric_dipole_shg_allowed is not None:
        hypotheses.append(
            {
                "id": "bulk-electric-dipole-shg-screen",
                "status": "ALLOWED" if electric_dipole_shg_allowed else "FORBIDDEN",
                "basis": f"detected crystallographic point group {point_group}",
                "limitation": (
                    "This is an inversion-symmetry screen for the bulk electric-dipole "
                    "contribution, not an optical response calculation."
                ),
            }
        )
    if connectivity.get("dimensionality_candidate") in {"0D", "1D", "2D", "3D"}:
        hypotheses.append(
            {
                "id": "connectivity-dimensionality-screen",
                "status": connectivity["dimensionality_candidate"],
                "basis": "multi-scale covalent-radius periodic graph",
                "limitation": (
                    "Graph dimensionality does not establish bonding energy, mechanical "
                    "anisotropy, exfoliation energy, porosity, or transport."
                ),
            }
        )
    if d_or_f_elements:
        hypotheses.append(
            {
                "id": "d-or-f-block-presence",
                "status": "CANDIDATE",
                "basis": f"d/f-block elements present: {', '.join(d_or_f_elements)}",
                "limitation": (
                    "Element presence alone does not establish oxidation state, local moment, "
                    "spin state, exchange coupling, or magnetic order."
                ),
            }
        )
    return {
        "method_version": "cif-structure-only-screening-v1",
        "evidence_level": "structure-only-candidate",
        "symmetry": {
            "point_group": point_group,
            "centrosymmetric": centrosymmetric,
            "piezoelectric_symmetry_allowed": piezoelectric_allowed,
            "polar_point_group": polar,
            "bulk_electric_dipole_shg_symmetry_allowed": electric_dipole_shg_allowed,
        },
        "metric_anisotropy": {
            "cell_length_ratio_max_over_min": round(metric_ratio, 6)
            if metric_ratio is not None
            else None,
            "large_metric_ratio_candidate": metric_ratio >= 1.5
            if metric_ratio is not None
            else None,
            "threshold": 1.5,
        },
        "connectivity_dimensionality_candidate": connectivity.get(
            "dimensionality_candidate"
        ),
        "d_or_f_block_elements": d_or_f_elements,
        "hypotheses": hypotheses,
        "not_assessed": [
            "formation energy or convex-hull stability",
            "band gap or metallicity",
            "magnetic ground state",
            "elastic, dielectric, piezoelectric, or optical coefficient magnitude",
            "phonon or finite-temperature stability",
            "diffusion barrier, conductivity, adsorption, or exfoliation energy",
        ],
    }


def build_optimization_guidance(
    quality: dict[str, Any],
    symmetry: dict[str, Any],
    connectivity: dict[str, Any],
    short_flags: list[dict[str, Any]],
    partial_occupancy_rows: list[int],
    disorder_rows: list[int],
) -> dict[str, Any]:
    tolerance_sensitive = bool(symmetry.get("tolerance_sensitive"))
    representative_limited = bool(partial_occupancy_rows or disorder_rows)
    standardized = symmetry.get("standardized_cells", {})
    primitive_available = (
        isinstance(standardized.get("primitive"), dict)
        and standardized["primitive"].get("status") == "GENERATED"
    )
    conventional_available = (
        isinstance(standardized.get("conventional"), dict)
        and standardized["conventional"].get("status") == "GENERATED"
    )
    idealized_recommended = (
        quality.get("status") != "FAIL"
        and not tolerance_sensitive
        and not representative_limited
    )
    starting_points = [
        {
            "candidate_id": "source-as-read",
            "available": True,
            "recommended_for_screening": True,
            "coordinates_ref": "structure.sites",
            "role": "unmodified provenance anchor and unconstrained baseline",
            "limitation": "The source geometry is not an energy-ranked structure.",
        },
        {
            "candidate_id": "symmetry-idealized-primitive",
            "available": primitive_available,
            "recommended_for_screening": primitive_available and idealized_recommended,
            "coordinates_ref": "structure.symmetry_attempt.standardized_cells.primitive",
            "role": "reduced symmetry-idealized optimization starting-point candidate",
            "limitation": (
                "Idealization can hide a real symmetry-breaking distortion and is not a "
                "stable-position or minimum-energy claim."
            ),
        },
        {
            "candidate_id": "symmetry-idealized-conventional",
            "available": conventional_available,
            "recommended_for_screening": conventional_available and idealized_recommended,
            "coordinates_ref": "structure.symmetry_attempt.standardized_cells.conventional",
            "role": "conventional symmetry-idealized comparison candidate",
            "limitation": (
                "The conventional cell can contain more atoms and is not automatically the "
                "lowest-cost or lowest-energy representation."
            ),
        },
    ]
    controls = [
        {
            "id": "retain-source-baseline",
            "reason": "Never overwrite the source CIF or replace its provenance anchor.",
        },
        {
            "id": "symmetry-breaking-control",
            "reason": (
                "Compare any symmetry-preserving relaxation with a small, explicitly "
                "generated lower-symmetry perturbation under the same energy model."
            ),
        },
    ]
    blockers = []
    if representative_limited:
        controls.append(
            {
                "id": "enumerate-ordered-occupancy-candidates",
                "reason": (
                    "Partial occupancy or disorder requires bounded, composition-preserving "
                    "ordered configurations before energy ranking."
                ),
            }
        )
        blockers.append("partial occupancy or disorder is unresolved")
    if short_flags:
        controls.append(
            {
                "id": "resolve-short-contact-candidates",
                "reason": "Review or repair short contacts before expensive relaxation.",
            }
        )
        blockers.append("configured short-distance flags are present")
    if tolerance_sensitive:
        blockers.append("detected symmetry changes across the tolerance sweep")
    if connectivity.get("dimensionality_candidate") == "2D":
        controls.append(
            {
                "id": "enumerate-layer-registry-candidates",
                "reason": (
                    "A robust 2D graph is a cue to compare bounded stacking translations and "
                    "interlayer separations with an appropriate energy model."
                ),
            }
        )
    if connectivity.get("dimensionality_candidate") == "SENSITIVE":
        blockers.append("connectivity dimensionality is radius-scale sensitive")
    return {
        "method_version": "optimization-starting-point-guidance-v1",
        "stability_assessed": False,
        "energy_model_used": False,
        "ranking_status": "NOT_RANKED",
        "starting_points": starting_points,
        "recommended_controls": controls,
        "blockers": blockers,
        "claim_boundary": (
            "Starting points and controls reduce avoidable search space. Only a specified "
            "energy/force method plus convergence and stability evidence can rank positions "
            "or support a stable-structure claim."
        ),
    }
