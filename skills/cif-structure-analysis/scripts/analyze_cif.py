#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from ciftool.document import inspect_cif_document
from ciftool.local_geometry import analyze_local_geometry
from ciftool.manifest import (
    element_styles,
    manifest_identity,
    provenance,
    relative_artifact_path,
    schema_errors,
    validation_from_diagnostics,
)
from ciftool.neighbors import analyze_periodic_neighbors
from ciftool.neighbors import match_neighbor_bonds as match_periodic_neighbor_bonds
from ciftool.quality import analyze_structure_quality
from ciftool.screening import analyze_property_screening, build_optimization_guidance
from ciftool.symmetry import analyze_symmetry
from ciftool.topology import analyze_connectivity

AMU_PER_ANG3_TO_G_CM3 = 1.66053906660
ROUND_DIGITS = 6
NEAREST_BOND_TOLERANCE_ANG = 0.05
DEFAULT_BOND_MATCH_TOLERANCE_ANG = 0.05
DEFAULT_TOPOLOGY_SCALE_FACTORS = [1.0, 1.15, 1.3]

def rounded(value: Any) -> Any:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    if math.isnan(number) or math.isinf(number):
        return None
    return round(number, ROUND_DIGITS)


def plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    if hasattr(value, "item"):
        return plain(value.item())
    if isinstance(value, float):
        return rounded(value)
    return value


def axis_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"min": None, "max": None, "span": None}
    low = min(values)
    high = max(values)
    return {"min": rounded(low), "max": rounded(high), "span": rounded(high - low)}


def coordinate_summary(atoms: Any) -> dict[str, Any]:
    positions = atoms.get_positions()
    scaled = atoms.get_scaled_positions(wrap=False)
    axes = ["x", "y", "z"]
    cart = {
        axis: axis_summary([float(row[idx]) for row in positions])
        for idx, axis in enumerate(axes)
    }
    frac = {
        axis: axis_summary([float(row[idx]) for row in scaled])
        for idx, axis in enumerate(axes)
    }
    sample_count = min(len(atoms), 10)
    sample = []
    symbols = atoms.get_chemical_symbols()
    for idx in range(sample_count):
        sample.append(
            {
                "index": idx,
                "symbol": symbols[idx],
                "cartesian_ang": [rounded(v) for v in positions[idx]],
                "fractional": [rounded(v) for v in scaled[idx]],
            }
        )
    return {
        "cartesian_ang": cart,
        "fractional": frac,
        "coordinate_sample": sample,
        "coordinate_sample_limit": sample_count,
    }


def site_records(atoms: Any) -> list[dict[str, Any]]:
    positions = atoms.get_positions()
    scaled = atoms.get_scaled_positions(wrap=False)
    symbols = atoms.get_chemical_symbols()
    return [
        {
            "index": index,
            "symbol": symbols[index],
            "atomic_number": int(atoms.numbers[index]),
            "cartesian_ang": [rounded(value) for value in positions[index]],
            "fractional": [rounded(value) for value in scaled[index]],
        }
        for index in range(len(atoms))
    ]


def nearest_distances(
    atoms: Any,
    short_threshold: float,
    neighbor_cutoff: float | None = None,
    maximum_neighbor_cutoff: float | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    return analyze_periodic_neighbors(
        atoms,
        short_threshold,
        requested_cutoff=neighbor_cutoff,
        maximum_cutoff=maximum_neighbor_cutoff,
        shell_tolerance=NEAREST_BOND_TOLERANCE_ANG,
    )


def parse_element_pair(value: str) -> tuple[str, str]:
    match = re.fullmatch(r"\s*([A-Z][a-z]?)\s*[-:]\s*([A-Z][a-z]?)\s*", value)
    if not match:
        raise argparse.ArgumentTypeError("element pair must use ELEMENT-ELEMENT syntax, for example Na-Cl")
    return tuple(sorted((match.group(1), match.group(2))))


def positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("value must be a finite number greater than zero")
    return number


def nonnegative_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("value must be a finite number greater than or equal to zero")
    return number


def match_neighbor_bonds(
    nearest_neighbor_pairs: list[dict[str, Any]],
    element_pair: tuple[str, str] | None,
    target_distance: float | None,
    tolerance: float,
) -> dict[str, Any]:
    return match_periodic_neighbor_bonds(
        nearest_neighbor_pairs,
        element_pair,
        target_distance,
        tolerance,
    )


def axis_gap_estimates(atoms: Any) -> list[dict[str, Any]]:
    if len(atoms) == 0:
        return []
    scaled = atoms.get_scaled_positions(wrap=True)
    cellpar = atoms.cell.cellpar()
    labels = ["a", "b", "c"]
    estimates = []
    for axis, label in enumerate(labels):
        coords = sorted(float(row[axis]) % 1.0 for row in scaled)
        gaps = []
        for idx in range(len(coords) - 1):
            gaps.append(coords[idx + 1] - coords[idx])
        gaps.append(coords[0] + 1.0 - coords[-1])
        max_gap = max(gaps)
        length = float(cellpar[axis])
        estimates.append(
            {
                "axis": label,
                "cell_length_ang": rounded(length),
                "largest_fractional_gap": rounded(max_gap),
                "largest_gap_ang": rounded(max_gap * length),
                "occupied_span_estimate_ang": rounded((1.0 - max_gap) * length),
                "note": "Largest fractional coordinate gap along this cell axis; not a physical vacuum conclusion.",
            }
        )
    return estimates


def symmetry_attempt(
    atoms: Any,
    symprec: float,
    angle_tolerance: float,
    declared: dict[str, Any] | None,
    has_partial_occupancy: bool,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    return analyze_symmetry(
        atoms,
        symprec,
        angle_tolerance,
        declared,
        has_partial_occupancy=has_partial_occupancy,
    )


def render_projection_views(atoms: Any, views_dir: Path, stem: str) -> list[dict[str, Any]]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception as exc:
        raise RuntimeError(f"failed to import matplotlib/numpy for view rendering: {exc}") from exc

    views_dir.mkdir(parents=True, exist_ok=True)
    scaled = atoms.get_scaled_positions(wrap=True)
    symbols = atoms.get_chemical_symbols()
    styles = element_styles(atoms)
    cell = np.asarray(atoms.cell.array, dtype=float)
    projections = [
        {"axis": "a", "view_index": 0, "x_index": 1, "y_index": 2, "x_label": "b", "y_label": "c"},
        {"axis": "b", "view_index": 1, "x_index": 2, "y_index": 0, "x_label": "c", "y_label": "a"},
        {"axis": "c", "view_index": 2, "x_index": 0, "y_index": 1, "x_label": "a", "y_label": "b"},
    ]
    outputs = []

    for projection in projections:
        axis = projection["axis"]
        view_index = projection["view_index"]
        x_index = projection["x_index"]
        y_index = projection["y_index"]
        x_label = projection["x_label"]
        y_label = projection["y_label"]
        view_vector = cell[view_index]
        x_vector = cell[x_index]
        y_vector = cell[y_index]

        view_norm = np.linalg.norm(view_vector)
        if view_norm == 0:
            raise RuntimeError(f"cannot render view along {axis}: zero-length cell vector")
        normal = view_vector / view_norm

        def reject_view_component(vector: Any) -> Any:
            vector = np.asarray(vector, dtype=float)
            return vector - np.dot(vector, normal) * normal

        x_projected = reject_view_component(x_vector)
        x_norm = np.linalg.norm(x_projected)
        if x_norm == 0:
            raise RuntimeError(f"cannot render view along {axis}: projected {x_label} vector has zero length")
        basis_x = x_projected / x_norm
        basis_y = np.cross(normal, basis_x)
        basis_y = basis_y / np.linalg.norm(basis_y)

        def to_2d(vector: Any) -> list[float]:
            vector = reject_view_component(vector)
            return [float(np.dot(vector, basis_x)), float(np.dot(vector, basis_y))]

        corner_vectors = [
            np.zeros(3),
            x_vector,
            x_vector + y_vector,
            y_vector,
            np.zeros(3),
        ]
        cell_polygon = [to_2d(vector) for vector in corner_vectors]
        cartesian_positions = np.matmul(np.asarray(scaled, dtype=float), cell)
        points_2d = [to_2d(position) for position in cartesian_positions]
        x_values = [point[0] for point in points_2d]
        y_values = [point[1] for point in points_2d]
        cell_x_values = [point[0] for point in cell_polygon]
        cell_y_values = [point[1] for point in cell_polygon]
        atom_x_span = max(x_values) - min(x_values) if x_values else 1.0
        atom_y_span = max(y_values) - min(y_values) if y_values else 1.0
        atom_span = max(atom_x_span, atom_y_span, 1.0)
        pad = max(0.12 * atom_span, 0.45)
        x_min = min(x_values) - pad if x_values else min(cell_x_values) - pad
        x_max = max(x_values) + pad if x_values else max(cell_x_values) + pad
        y_min = min(y_values) - pad if y_values else min(cell_y_values) - pad
        y_max = max(y_values) + pad if y_values else max(cell_y_values) + pad
        x_span = max(x_max - x_min, 1.0)
        y_span = max(y_max - y_min, 1.0)
        cell_x_span = max(cell_x_values) - min(cell_x_values) if cell_x_values else x_span
        cell_y_span = max(cell_y_values) - min(cell_y_values) if cell_y_values else y_span

        aspect = x_span / y_span if y_span else 1.0
        if aspect > 1.8:
            figure_size = (10, max(3.2, min(5.5, 10 / aspect)))
        elif aspect < 0.55:
            figure_size = (max(3.2, min(5.5, 10 * aspect)), 10)
        else:
            figure_size = (7, 7)

        fig, ax = plt.subplots(figsize=figure_size, dpi=180)
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#FFFFFF")
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect("equal", adjustable="box")
        ax.axis("off")
        ax.plot(
            [point[0] for point in cell_polygon],
            [point[1] for point in cell_polygon],
            color="#333333",
            linewidth=0.9,
            alpha=0.65,
            clip_on=True,
        )

        for symbol, x, y in zip(symbols, x_values, y_values):
            color = styles.get(symbol, {}).get("color_hex", "#D62728")
            ax.scatter(x, y, s=360, c=color, edgecolors="#111111", linewidths=0.8, alpha=0.9)

        output_path = views_dir / f"view_along_{axis}.png"
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        fig.savefig(output_path, bbox_inches="tight", pad_inches=0.02)
        plt.close(fig)
        outputs.append(
            {
                "axis": axis,
                "path": str(output_path),
                "x_axis": x_label,
                "y_axis": y_label,
                "projection": f"view along {axis}: {x_label}-{y_label} cell-vector projection, atom-extent viewport",
                "view_window_mode": "atom_extent",
                "view_window_2d": {
                    "x_min_ang": rounded(x_min),
                    "x_max_ang": rounded(x_max),
                    "x_span_ang": rounded(x_span),
                    "y_min_ang": rounded(y_min),
                    "y_max_ang": rounded(y_max),
                    "y_span_ang": rounded(y_span),
                    "cell_x_span_ang": rounded(cell_x_span),
                    "cell_y_span_ang": rounded(cell_y_span),
                    "padding_ang": rounded(pad),
                },
                "cell_polygon_2d": plain(cell_polygon),
                "atom_positions_2d": [
                    {"index": idx, "symbol": symbol, "xy_ang": plain(point)}
                    for idx, (symbol, point) in enumerate(zip(symbols, points_2d))
                ],
            }
        )

    return outputs


def build_report(input_path: Path, args: argparse.Namespace) -> dict[str, Any]:
    try:
        import ase
        from ase.io import read
    except Exception as exc:
        raise RuntimeError(f"failed to import ASE: {exc}") from exc

    document = inspect_cif_document(
        input_path,
        block_name=args.block_name,
        block_index=args.block_index,
    )
    selected_block = document["selected_block"]
    try:
        atoms = read(
            str(input_path),
            index=int(selected_block["index"]),
            store_tags=True,
            fractional_occupancies=True,
        )
    except Exception as exc:
        raise RuntimeError(
            f"failed to construct ASE structure from CIF data block "
            f"{selected_block['name']!r}: {exc}"
        ) from exc

    diagnostics: list[dict[str, str]] = list(document["diagnostics"])
    diagnostics.extend(
        [
            {
                "id": "cif-document-parse",
                "status": "pass",
                "message": (
                    f"parsed {len(document['blocks'])} CIF data block(s) with "
                    f"{document['parser']['name']} {document['parser']['version']}"
                ),
            },
            {
                "id": "structure-adapter",
                "status": "pass",
                "message": (
                    f"constructed an ASE structure from data block "
                    f"{selected_block['name']!r} at index {selected_block['index']}"
                ),
            },
        ]
    )
    limitations: list[str] = []
    symbols = atoms.get_chemical_symbols()
    counts = dict(sorted(Counter(symbols).items()))
    cellpar = atoms.cell.cellpar()
    raw_cell = document["metadata"]["cell"]
    cell_fields = ("a", "b", "c", "alpha", "beta", "gamma")
    missing_cell_fields = [
        field for field in cell_fields if raw_cell[field]["value"] is None
    ]
    cell_mismatches = []
    for index, field in enumerate(cell_fields):
        raw_value = raw_cell[field]["value"]
        if raw_value is None:
            continue
        parsed_value = float(cellpar[index])
        if not math.isclose(float(raw_value), parsed_value, rel_tol=1e-8, abs_tol=1e-6):
            cell_mismatches.append(
                f"{field}: raw={raw_value}, structure={rounded(parsed_value)}"
            )
    if cell_mismatches:
        diagnostics.append(
            {
                "id": "cell-parameter-adapter-mismatch",
                "status": "fail",
                "message": "raw CIF and ASE cell parameters disagree: " + "; ".join(cell_mismatches),
            }
        )
    elif missing_cell_fields:
        diagnostics.append(
            {
                "id": "cell-parameter-source-incomplete",
                "status": "warn",
                "message": f"raw CIF cell metadata is incomplete for fields {missing_cell_fields}",
            }
        )
    else:
        diagnostics.append(
            {
                "id": "cell-parameter-adapter-consistency",
                "status": "pass",
                "message": "raw CIF and ASE cell parameters agree within numeric tolerance",
            }
        )
    volume = float(atoms.get_volume()) if atoms.cell.rank == 3 else None
    total_mass = float(sum(atoms.get_masses())) if len(atoms) else 0.0
    density = None
    if volume and volume > 0:
        density = total_mass / volume * AMU_PER_ANG3_TO_G_CM3
    else:
        diagnostics.append(
            {
                "id": "density-unavailable",
                "status": "warn",
                "message": "density is unavailable because cell volume is zero or undefined",
            }
        )

    partial_occupancy_rows = document["metadata"].get("partial_occupancy_rows", [])
    disorder_rows = document["metadata"].get("disorder_rows", [])
    if partial_occupancy_rows:
        diagnostics.append(
            {
                "id": "density-partial-occupancy-limitation",
                "status": "warn",
                "message": (
                    "reported ASE mass density is not accepted as occupancy-weighted evidence "
                    "for a partially occupied/disordered CIF"
                ),
            }
        )
    if partial_occupancy_rows or disorder_rows:
        diagnostics.append(
            {
                "id": "representative-structure-disorder-limitation",
                "status": "warn",
                "message": (
                    "neighbor, symmetry, formula, mass, and density results use the ASE-materialized "
                    "representative structure and do not resolve correlated disorder ensembles"
                ),
            }
        )

    nearest, short_flags = nearest_distances(
        atoms,
        args.short_distance_threshold,
        neighbor_cutoff=args.neighbor_cutoff,
        maximum_neighbor_cutoff=args.maximum_neighbor_cutoff,
    )
    diagnostics.append(
        {
            "id": "periodic-neighbor-search",
            "status": "pass" if nearest["neighbor_search_complete"] else "warn",
            "message": (
                "periodic-image neighbor search found at least one neighbor for every site"
                if nearest["neighbor_search_complete"]
                else f"neighbor search has no candidate for sites {nearest['atoms_without_neighbors']} "
                f"within {nearest['neighbor_cutoff_ang']} Ang"
            ),
        }
    )
    if args.match_elements:
        try:
            from ase.data import atomic_numbers
        except Exception as exc:
            raise RuntimeError(f"failed to validate bond-match elements with ASE: {exc}") from exc
        unknown = [symbol for symbol in args.match_elements if symbol not in atomic_numbers]
        if unknown:
            raise RuntimeError(f"unknown element symbol in --match-elements: {', '.join(unknown)}")
    nearest["bond_length_match"] = match_neighbor_bonds(
        nearest["nearest_neighbor_bond_pairs"],
        args.match_elements,
        args.match_bond_length,
        args.match_bond_tolerance,
    )
    if short_flags:
        diagnostics.append(
            {
                "id": "short-distance-flags",
                "status": "warn",
                "message": (
                    f"{len(short_flags)} periodic edge(s) are shorter than "
                    f"{args.short_distance_threshold} Ang; flags require human review"
                ),
            }
        )

    symmetry, symmetry_diagnostics = symmetry_attempt(
        atoms,
        args.symprec,
        args.angle_tolerance,
        document["metadata"].get("declared_symmetry"),
        bool(partial_occupancy_rows),
    )
    diagnostics.extend(symmetry_diagnostics)
    if symmetry.get("status") == "DETECTED":
        diagnostics.append(
            {
                "id": "symmetry-dataset",
                "status": "pass",
                "message": (
                    f"spglib detected {symmetry.get('international')} "
                    f"(number {symmetry.get('number')}) at symprec={args.symprec}"
                ),
            }
        )
    quality, quality_diagnostics = analyze_structure_quality(
        atoms,
        document["metadata"],
        short_flags,
    )
    diagnostics.extend(quality_diagnostics)
    local_geometry = analyze_local_geometry(
        atoms,
        nearest["nearest_neighbor_bond_pairs"],
    )
    connectivity = analyze_connectivity(atoms, args.topology_scale_factors)
    property_screening = analyze_property_screening(
        atoms,
        symmetry,
        connectivity,
    )
    optimization_guidance = build_optimization_guidance(
        quality,
        symmetry,
        connectivity,
        short_flags,
        partial_occupancy_rows,
        disorder_rows,
    )
    views = []
    if args.views_dir:
        views = render_projection_views(atoms, Path(args.views_dir).expanduser().resolve(), input_path.stem)
        json_root = Path(args.json).expanduser().resolve().parent
        markdown_root = Path(args.markdown).expanduser().resolve().parent
        for view in views:
            absolute = Path(view["path"]).resolve()
            view["path"] = relative_artifact_path(absolute, json_root)
            view["markdown_path"] = relative_artifact_path(absolute, markdown_root)

    validation = validation_from_diagnostics(diagnostics)
    status = {"pass": "PASS", "warn": "WARN", "block": "BLOCK"}[validation["status"]]
    limitations.extend(
        item["message"]
        for item in validation["checks"]
        if item["status"] in {"warn", "fail", "not-run"}
    )
    limitations.append(
        "axis_gap_estimates are cell-axis coordinate gaps, not physical layer or vacuum thickness"
    )
    info = {
        "name": input_path.name,
        "size_bytes": input_path.stat().st_size,
        "mtime": round(input_path.stat().st_mtime, 3),
        "sha256": document["sha256"],
        "data_block": selected_block,
    }
    dependency_versions = {}
    for distribution in ("ase", "gemmi", "PyCifRW", "spglib", "matplotlib", "numpy"):
        try:
            dependency_versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            dependency_versions[distribution] = "unavailable"
    options = {
        "data_block": selected_block,
        "short_distance_threshold_ang": args.short_distance_threshold,
        "neighbor_cutoff_ang": args.neighbor_cutoff,
        "maximum_neighbor_cutoff_ang": args.maximum_neighbor_cutoff,
        "symprec": args.symprec,
        "angle_tolerance": args.angle_tolerance,
        "topology_scale_factors": args.topology_scale_factors,
        "bond_match": {
            "element_pair": list(args.match_elements) if args.match_elements else None,
            "target_distance_ang": args.match_bond_length,
            "tolerance_ang": args.match_bond_tolerance,
        },
    }
    identity = manifest_identity(document, atoms, input_path.name)
    report = plain(
        {
            **identity,
            "status": status,
            "document": {
                "blocks": document["blocks"],
                "selected_block": selected_block,
                "metadata": document["metadata"],
            },
            "validation": validation,
            "provenance": provenance(options, dependency_versions),
            "input": info,
            "execution": {
                "script": "analyze_cif.py",
                "ase_version": getattr(ase, "__version__", "unknown"),
                **options,
            },
            "structure": {
                "formula": atoms.get_chemical_formula(),
                "atom_count": len(atoms),
                "source_atom_site_count": document["metadata"].get("atom_site_count"),
                "element_counts": counts,
                "element_styles": element_styles(atoms),
                "pbc": [bool(v) for v in atoms.get_pbc()],
                "cell": {
                    "a": cellpar[0],
                    "b": cellpar[1],
                    "c": cellpar[2],
                    "alpha": cellpar[3],
                    "beta": cellpar[4],
                    "gamma": cellpar[5],
                    "rank": atoms.cell.rank,
                    "vectors_ang": atoms.cell.array,
                },
                "volume_ang3": volume,
                "total_mass_amu": total_mass,
                "density_g_cm3": density,
                "density_occupancy_weighted": False if partial_occupancy_rows else True,
                "coordinates": coordinate_summary(atoms),
                "sites": site_records(atoms),
                "nearest_distances": nearest,
                "axis_gap_estimates": axis_gap_estimates(atoms),
                "symmetry_attempt": symmetry,
                "quality_analysis": quality,
                "local_geometry": local_geometry,
                "connectivity_analysis": connectivity,
                "property_screening": property_screening,
                "optimization_guidance": optimization_guidance,
            },
            "flags": {
                "short_distances": short_flags,
                "partial_occupancy_rows": partial_occupancy_rows,
            },
            "views": views,
            "limitations": limitations,
            "not_assessed": [
                "DFT setup advice",
                "pseudopotential choice",
                "k-point or cutoff settings",
                "magnetic initialization",
                "physical credibility or stability",
                "stable atomic positions or global-minimum structure",
                "synthesis feasibility",
                "strict layer dimensionality or physical vacuum thickness",
            ],
        }
    )
    # ``plain`` intentionally rounds presentation/numerical fields to six
    # decimals.  The v1 identity preimage is a separate exact contract at ten
    # decimals and must not be silently presentation-rounded after hashing.
    report["structure_identity"] = identity["structure_identity"]
    failures = schema_errors(report, Path(__file__))
    if failures:
        raise RuntimeError("generated structure manifest is invalid: " + "; ".join(failures))
    return report


def markdown_table(rows: list[list[Any]], headers: list[str]) -> str:
    def cell(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list, tuple)):
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            rendered = str(value)
        return rendered.replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(value) for value in row) + " |")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    structure = report["structure"]
    cell = structure["cell"]
    coordinates = structure["coordinates"]
    nearest = structure["nearest_distances"]
    bond_match = nearest["bond_length_match"]
    symmetry = structure["symmetry_attempt"]
    quality = structure["quality_analysis"]
    local_geometry = structure["local_geometry"]
    connectivity = structure["connectivity_analysis"]
    property_screening = structure["property_screening"]
    optimization_guidance = structure["optimization_guidance"]
    document = report["document"]
    selected_block = document["selected_block"]

    facts = [
        ["formula", structure["formula"], "JSON: structure.formula"],
        ["atom_count", structure["atom_count"], "JSON: structure.atom_count"],
        ["element_counts", structure["element_counts"], "JSON: structure.element_counts"],
        ["cell_a_b_c_ang", f'{cell["a"]}, {cell["b"]}, {cell["c"]}', "JSON: structure.cell"],
        ["cell_angles_deg", f'{cell["alpha"]}, {cell["beta"]}, {cell["gamma"]}', "JSON: structure.cell"],
        ["volume_ang3", structure["volume_ang3"], "JSON: structure.volume_ang3"],
        ["density_g_cm3", structure["density_g_cm3"], "JSON: structure.density_g_cm3"],
        ["density_occupancy_weighted", structure["density_occupancy_weighted"], "JSON: structure.density_occupancy_weighted"],
        ["min_distance_ang", nearest["min_distance_ang"], "JSON: structure.nearest_distances.min_distance_ang"],
        ["periodic_edge_count", nearest["periodic_edge_count"], "JSON: structure.nearest_distances.periodic_edge_count"],
        ["bond_match_status", bond_match["status"], "JSON: structure.nearest_distances.bond_length_match"],
        ["symmetry_status", symmetry["status"], "JSON: structure.symmetry_attempt"],
        ["quality_status", quality["status"], "JSON: structure.quality_analysis"],
        [
            "connectivity_dimensionality_candidate",
            connectivity["dimensionality_candidate"],
            "JSON: structure.connectivity_analysis",
        ],
        [
            "optimization_ranking_status",
            optimization_guidance["ranking_status"],
            "JSON: structure.optimization_guidance",
        ],
    ]

    validation_rows = [
        [item["id"], item["status"], item["message"]]
        for item in report["validation"]["checks"]
    ]

    block_rows = [
        [item["index"], item["name"], item["tag_count"], item["pair_count"], item["loop_count"]]
        for item in document["blocks"]
    ]

    raw_cell_rows = []
    for field, record in document["metadata"]["cell"].items():
        raw_cell_rows.append(
            [field, record["tag"], record["raw"], record["value"], record["standard_uncertainty"]]
        )

    cell_rows = [
        ["a", cell["a"], "Ang"],
        ["b", cell["b"], "Ang"],
        ["c", cell["c"], "Ang"],
        ["alpha", cell["alpha"], "deg"],
        ["beta", cell["beta"], "deg"],
        ["gamma", cell["gamma"], "deg"],
        ["rank", cell["rank"], ""],
        ["volume", structure["volume_ang3"], "Ang^3"],
        ["total_mass", structure["total_mass_amu"], "amu"],
        ["density", structure["density_g_cm3"], "g/cm^3"],
    ]

    coordinate_range_rows = []
    for space, label in [("cartesian_ang", "cartesian Ang"), ("fractional", "fractional")]:
        for axis in ["x", "y", "z"]:
            values = coordinates[space][axis]
            coordinate_range_rows.append([label, axis, values["min"], values["max"], values["span"]])

    coordinate_sample_rows = []
    for item in coordinates["coordinate_sample"]:
        coordinate_sample_rows.append(
            [
                item["index"],
                item["symbol"],
                item["cartesian_ang"],
                item["fractional"],
            ]
        )

    nearest_rows = []
    for item in nearest["nearest_pairs_sample"]:
        nearest_rows.append(
            [
                f'{item["i"]}-{item["j"]}',
                "-".join(item["symbols"]),
                item["shift"],
                item["distance_ang"],
            ]
        )
    if not nearest_rows:
        nearest_rows.append(["none", "", "", ""])

    coordination_rows = [
        [
            item["index"],
            item["symbol"],
            item["nearest_distance_ang"],
            item["nearest_shell_coordination"],
        ]
        for item in nearest["coordination_by_atom"]
    ]

    match_query_rows = [
        ["status", bond_match["status"]],
        ["element_pair", bond_match["query"]["element_pair"]],
        ["target_distance_ang", bond_match["query"]["target_distance_ang"]],
        ["tolerance_ang", bond_match["query"]["tolerance_ang"]],
        ["scope", bond_match["scope"]],
        ["candidate_count", bond_match["candidate_count"]],
        ["match_count", bond_match["match_count"]],
    ]
    match_rows = []
    for item in bond_match["matches"]:
        match_rows.append(
            [
                f'{item["i"]}-{item["j"]}',
                "-".join(item["symbols"]),
                item["shift"],
                item["distance_ang"],
                item["absolute_delta_ang"],
            ]
        )
    if not match_rows:
        match_rows.append(["none", "", "", "", ""])
    closest = bond_match["closest_candidate"]
    closest_rows = []
    if closest:
        closest_rows.append(
            [
                f'{closest["i"]}-{closest["j"]}',
                "-".join(closest["symbols"]),
                closest["shift"],
                closest["distance_ang"],
                closest["absolute_delta_ang"],
            ]
        )
    else:
        closest_rows.append(["none", "", "", "", ""])

    flag_rows = []
    for flag in report["flags"]["short_distances"]:
        flag_rows.append(
            [
                f'{flag["i"]}-{flag["j"]}',
                "-".join(flag["symbols"]),
                flag["shift"],
                flag["distance_ang"],
                flag["threshold_ang"],
            ]
        )
    if not flag_rows:
        flag_rows.append(["none", "", "", "", ""])

    gap_rows = []
    for item in structure["axis_gap_estimates"]:
        gap_rows.append(
            [
                item["axis"],
                item["largest_fractional_gap"],
                item["largest_gap_ang"],
                item["occupied_span_estimate_ang"],
            ]
        )

    symmetry_rows = [
        ["status", symmetry.get("status")],
        ["available", symmetry.get("available")],
        ["international", symmetry.get("international")],
        ["number", symmetry.get("number")],
        ["hall", symmetry.get("hall")],
        ["choice", symmetry.get("choice")],
        ["pointgroup", symmetry.get("pointgroup")],
        ["operation_count", symmetry.get("operation_count")],
        ["symprec", symmetry.get("symprec")],
        ["angle_tolerance", symmetry.get("angle_tolerance")],
        ["declared_comparison", (symmetry.get("declared_comparison") or {}).get("status")],
        ["tolerance_sensitive", symmetry.get("tolerance_sensitive")],
        ["reason", symmetry.get("reason")],
    ]
    geometry_rows = [
        [
            item["index"],
            item["symbol"],
            item["coordination"],
            item["bond_distance_mean_ang"],
            item["bond_angle_count"],
            item["geometry_hint"],
        ]
        for item in local_geometry["sites"]
    ]
    topology_rows = [
        [
            item["covalent_radius_scale"],
            item["periodic_edge_count"],
            item["component_count"],
            [
                {
                    "atoms": component["atom_count"],
                    "dimensionality": component["dimensionality"],
                }
                for component in item["components"]
            ],
        ]
        for item in connectivity["scales"]
    ]
    hypothesis_rows = [
        [item["id"], item["status"], item["basis"], item["limitation"]]
        for item in property_screening["hypotheses"]
    ]
    if not hypothesis_rows:
        hypothesis_rows.append(["none", "", "", "symmetry or structure evidence unavailable"])
    starting_point_rows = [
        [
            item["candidate_id"],
            item["available"],
            item["recommended_for_screening"],
            item["role"],
            item["limitation"],
        ]
        for item in optimization_guidance["starting_points"]
    ]

    view_rows = []
    view_images = []
    for view in report.get("views", []):
        markdown_path = view.get("markdown_path", view["path"])
        view_rows.append([view["axis"], view["x_axis"], view["y_axis"], markdown_path, view["projection"]])
        view_images.extend([f'### View along {view["axis"]}', "", f'![view along {view["axis"]}]({markdown_path})', ""])
    if not view_rows:
        view_rows.append(["none", "", "", "", "run with --views-dir to export PNG views"])

    limitations = report["limitations"] or ["none"]
    not_assessed = report["not_assessed"]
    return "\n".join(
        [
            "# CIF Structure Analysis",
            "",
            "## Execution",
            f'- Status: `{report["status"]}`',
            f'- Manifest ID: `{report["manifest_id"]}`',
            f'- Schema version: `{report["schema_version"]}`',
            f'- Input CIF label: `{report["source"]["label"]}`',
            f'- Input SHA-256: `{report["source"]["sha256"]}`',
            f'- CIF syntax: `{report["source"]["format"]}`',
            f'- Parser: `{report["parser"]["name"]} {report["parser"]["version"]}` ({report["parser"]["mode"]})',
            f'- Selected data block: `{selected_block["name"]}` (index {selected_block["index"]})',
            f'- Script: `{report["execution"]["script"]}`',
            f'- ASE version: `{report["execution"]["ase_version"]}`',
            "",
            "## Validation",
            f'- Overall validation: `{report["validation"]["status"]}`',
            "",
            markdown_table(validation_rows, ["Check", "Status", "Message"]),
            "",
            "## CIF Data Blocks",
            markdown_table(block_rows, ["Index", "Name", "Tags", "Pairs", "Loops"]),
            "",
            "## Raw Cell Metadata",
            markdown_table(raw_cell_rows, ["Field", "Tag", "Raw", "Value", "Standard uncertainty"]),
            "",
            "## Computed Structure Facts",
            markdown_table(facts, ["Fact", "Value", "Artifact reference"]),
            "",
            "## Detailed Cell",
            markdown_table(cell_rows, ["Field", "Value", "Unit"]),
            "",
            "## Coordinate Ranges",
            markdown_table(coordinate_range_rows, ["Space", "Axis", "Min", "Max", "Span"]),
            "",
            "## Coordinate Sample",
            markdown_table(coordinate_sample_rows, ["Index", "Element", "Cartesian Ang", "Fractional"]),
            "",
            "## Nearest Pair Sample",
            markdown_table(nearest_rows, ["Pair", "Symbols", "Cell shift", "Distance Ang"]),
            "",
            "## Per-Site Nearest-Shell Coordination",
            markdown_table(coordination_rows, ["Index", "Element", "Nearest distance Ang", "Coordination"]),
            "",
            "## Nearest-Neighbor Bond-Length Match",
            markdown_table(match_query_rows, ["Field", "Value"]),
            "",
            markdown_table(match_rows, ["Matched pair", "Symbols", "Cell shift", "Distance Ang", "Absolute delta Ang"]),
            "",
            "### Closest Candidate",
            markdown_table(closest_rows, ["Pair", "Symbols", "Cell shift", "Distance Ang", "Absolute delta Ang"]),
            "",
            f'- Matching rule: {bond_match["matching_rule"]}',
            f'- Periodic scope: {bond_match["periodic_scope"]}',
            "",
            "## Short-Distance Flags",
            markdown_table(flag_rows, ["Pair", "Symbols", "Cell shift", "Distance ang", "Threshold ang"]),
            "",
            "## Axis Gap Estimates",
            markdown_table(gap_rows, ["Axis", "Largest fractional gap", "Largest gap ang", "Occupied span estimate ang"]),
            "",
            "## Symmetry Attempt",
            markdown_table(symmetry_rows, ["Field", "Value"]),
            "",
            "## Structure Quality Screening",
            f'- Status: `{quality["status"]}`',
            f'- Claim boundary: {quality["claim_boundary"]}',
            "",
            markdown_table(
                [
                    [item["id"], item["status"], item["message"]]
                    for item in quality["checks"]
                ],
                ["Check", "Status", "Message"],
            ),
            "",
            "## Local Geometry Hints",
            markdown_table(
                geometry_rows,
                ["Index", "Element", "Coordination", "Mean distance Ang", "Angle count", "Geometry hint"],
            ),
            "",
            f'- Claim boundary: {local_geometry["claim_boundary"]}',
            "",
            "## Multi-Scale Periodic Connectivity",
            f'- Dimensionality candidate: `{connectivity["dimensionality_candidate"]}`',
            f'- Stable across configured scales: `{connectivity["stable_across_scales"]}`',
            "",
            markdown_table(
                topology_rows,
                ["Covalent-radius scale", "Periodic edges", "Components", "Component summary"],
            ),
            "",
            f'- Claim boundary: {connectivity["claim_boundary"]}',
            "",
            "## Structure-Only Property Screening",
            markdown_table(
                hypothesis_rows,
                ["Screen", "Status", "Basis", "Limitation"],
            ),
            "",
            "## Optimization Starting-Point Guidance",
            f'- Ranking status: `{optimization_guidance["ranking_status"]}`',
            f'- Stability assessed: `{optimization_guidance["stability_assessed"]}`',
            f'- Energy model used: `{optimization_guidance["energy_model_used"]}`',
            "",
            markdown_table(
                starting_point_rows,
                ["Candidate", "Available", "Recommended for screening", "Role", "Limitation"],
            ),
            "",
            f'- Claim boundary: {optimization_guidance["claim_boundary"]}',
            "",
            "## Generated Views",
            markdown_table(view_rows, ["View axis", "Horizontal axis", "Vertical axis", "Path", "Projection"]),
            "",
            *view_images,
            "## Limitations",
            "\n".join(f"- {item}" for item in limitations),
            "",
            "## Not Assessed",
            "\n".join(f"- {item}" for item in not_assessed),
            "",
        ]
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a selected CIF data block and emit versioned JSON plus Markdown "
            "structure-analysis artifacts."
        )
    )
    parser.add_argument("--input", required=True, help="Input CIF file path.")
    parser.add_argument("--json", required=True, help="Output JSON artifact path.")
    parser.add_argument("--markdown", required=True, help="Output Markdown artifact path.")
    parser.add_argument("--views-dir", help="Optional directory for PNG views along a, b, and c.")
    block_group = parser.add_mutually_exclusive_group()
    block_group.add_argument("--block-name", help="Select a CIF data block by case-insensitive name.")
    block_group.add_argument(
        "--block-index",
        type=int,
        default=0,
        help="Select a CIF data block by zero-based index (default: 0).",
    )
    parser.add_argument(
        "--short-distance-threshold",
        type=positive_float,
        default=0.6,
        help="Flag periodic-image distances below this Angstrom threshold.",
    )
    parser.add_argument(
        "--neighbor-cutoff",
        type=positive_float,
        help="Optional fixed periodic-neighbor cutoff in Angstrom; disables adaptive expansion.",
    )
    parser.add_argument(
        "--maximum-neighbor-cutoff",
        type=positive_float,
        help="Maximum adaptive periodic-neighbor cutoff in Angstrom.",
    )
    parser.add_argument(
        "--symprec",
        type=positive_float,
        default=1e-3,
        help="spglib Cartesian symmetry precision in Angstrom (default: 1e-3).",
    )
    parser.add_argument(
        "--angle-tolerance",
        type=float,
        default=-1.0,
        help="spglib angle tolerance in degrees; -1 uses the backend default.",
    )
    parser.add_argument(
        "--topology-scale-factors",
        nargs="+",
        type=positive_float,
        default=list(DEFAULT_TOPOLOGY_SCALE_FACTORS),
        metavar="SCALE",
        help=(
            "Positive covalent-radius multipliers for periodic graph sensitivity "
            "analysis (default: 1.0 1.15 1.3)."
        ),
    )
    parser.add_argument(
        "--match-elements",
        type=parse_element_pair,
        help="Optional unordered element pair to match in the nearest-neighbor shell, for example Na-Cl.",
    )
    parser.add_argument(
        "--match-bond-length",
        type=positive_float,
        help="Optional target nearest-neighbor bond length in Angstrom.",
    )
    parser.add_argument(
        "--match-bond-tolerance",
        type=nonnegative_float,
        default=DEFAULT_BOND_MATCH_TOLERANCE_ANG,
        help="Absolute target-length tolerance in Angstrom (default: 0.05).",
    )
    args = parser.parse_args(argv)
    if args.block_index is not None and args.block_index < 0:
        parser.error("--block-index must be greater than or equal to zero")
    if not math.isfinite(args.angle_tolerance) or (
        args.angle_tolerance < 0 and args.angle_tolerance != -1.0
    ):
        parser.error("--angle-tolerance must be -1 or a finite nonnegative number")
    if (
        args.neighbor_cutoff is not None
        and args.maximum_neighbor_cutoff is not None
        and args.maximum_neighbor_cutoff < args.neighbor_cutoff
    ):
        parser.error("--maximum-neighbor-cutoff must be greater than or equal to --neighbor-cutoff")
    return args


def write_artifacts(
    report: dict[str, Any], json_path: Path, markdown_path: Path
) -> None:
    payloads = [
        (json_path, json.dumps(report, indent=2, sort_keys=True) + "\n"),
        (markdown_path, render_markdown(report)),
    ]
    staged: list[tuple[Path, Path]] = []
    try:
        for target, payload in payloads:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
                staged.append((Path(handle.name), target))
        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    input_path = Path(args.input).expanduser().resolve()
    json_path = Path(args.json).expanduser().resolve()
    markdown_path = Path(args.markdown).expanduser().resolve()

    if not input_path.exists():
        print(f"failed: input CIF does not exist: {input_path}", file=sys.stderr)
        return 2
    if not input_path.is_file():
        print(f"failed: input path is not a file: {input_path}", file=sys.stderr)
        return 2
    if json_path == markdown_path:
        print("failed: --json and --markdown must use different paths", file=sys.stderr)
        return 2
    if input_path in {json_path, markdown_path}:
        print("failed: output paths must not overwrite the input CIF", file=sys.stderr)
        return 2

    try:
        report = build_report(input_path, args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        write_artifacts(report, json_path, markdown_path)
    except Exception as exc:
        print(f"failed to write artifacts: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {json_path}")
    print(f"wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
