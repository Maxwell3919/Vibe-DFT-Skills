#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

AMU_PER_ANG3_TO_G_CM3 = 1.66053906660
ROUND_DIGITS = 6
NEAREST_BOND_TOLERANCE_ANG = 0.05
DEFAULT_BOND_MATCH_TOLERANCE_ANG = 0.05

ELEMENT_COLORS = {
    "Br": "#8B4513",
    "Cl": "#2CA02C",
    "Hf": "#6A5ACD",
    "Na": "#1F77B4",
    "Se": "#FF7F0E",
    "Ti": "#7F7F7F",
}


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


def nearest_distances(atoms: Any, short_threshold: float) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    symbols = atoms.get_chemical_symbols()
    use_mic = bool(any(atoms.get_pbc()))
    pair_records = []
    short_flags = []
    distances = []

    for i, j in combinations(range(len(atoms)), 2):
        distance = float(atoms.get_distance(i, j, mic=use_mic))
        record = {
            "i": i,
            "j": j,
            "symbols": [symbols[i], symbols[j]],
            "distance_ang": rounded(distance),
        }
        distances.append(distance)
        pair_records.append(record)
        if distance < short_threshold:
            short_flags.append(
                {
                    "i": i,
                    "j": j,
                    "symbols": [symbols[i], symbols[j]],
                    "distance_ang": rounded(distance),
                    "threshold_ang": rounded(short_threshold),
                }
            )

    pair_records.sort(key=lambda item: item["distance_ang"])
    nearest_by_atom: dict[int, float] = {}
    for record in pair_records:
        distance = float(record["distance_ang"])
        for atom_index in (int(record["i"]), int(record["j"])):
            if atom_index not in nearest_by_atom or distance < nearest_by_atom[atom_index]:
                nearest_by_atom[atom_index] = distance
    nearest_bond_pairs = [
        record
        for record in pair_records
        if (
            float(record["distance_ang"]) <= nearest_by_atom[int(record["i"])] + NEAREST_BOND_TOLERANCE_ANG
            or float(record["distance_ang"]) <= nearest_by_atom[int(record["j"])] + NEAREST_BOND_TOLERANCE_ANG
        )
    ]
    if distances:
        summary = {
            "min_distance_ang": rounded(min(distances)),
            "max_distance_ang": rounded(max(distances)),
            "pair_count": len(distances),
            "nearest_pairs_sample": pair_records[:20],
            "nearest_neighbor_bond_pairs": nearest_bond_pairs,
            "nearest_neighbor_bond_count": len(nearest_bond_pairs),
            "nearest_neighbor_bond_tolerance_ang": rounded(NEAREST_BOND_TOLERANCE_ANG),
            "nearest_neighbor_bond_rule": "per-atom nearest-neighbor shell within tolerance",
            "uses_minimum_image": use_mic,
        }
    else:
        summary = {
            "min_distance_ang": None,
            "max_distance_ang": None,
            "pair_count": 0,
            "nearest_pairs_sample": [],
            "nearest_neighbor_bond_pairs": [],
            "nearest_neighbor_bond_count": 0,
            "nearest_neighbor_bond_tolerance_ang": rounded(NEAREST_BOND_TOLERANCE_ANG),
            "nearest_neighbor_bond_rule": "per-atom nearest-neighbor shell within tolerance",
            "uses_minimum_image": use_mic,
        }
    return summary, short_flags


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
    requested = element_pair is not None or target_distance is not None
    query = {
        "element_pair": list(element_pair) if element_pair else None,
        "target_distance_ang": rounded(target_distance),
        "tolerance_ang": rounded(tolerance),
    }
    common = {
        "query": query,
        "scope": "nearest_neighbor_bond_pairs",
        "matching_rule": (
            "unordered element-pair equality and absolute distance difference within tolerance; "
            "when target distance is omitted, match only by element pair"
        ),
        "periodic_scope": (
            "unique atom-index pairs using ASE minimum-image distances; periodic-image multiplicity "
            "and self-image neighbors are not enumerated"
        ),
    }
    if not requested:
        return {
            "status": "NOT_REQUESTED",
            **common,
            "candidate_count": 0,
            "match_count": 0,
            "matches": [],
            "closest_candidate": None,
        }

    candidates = []
    for record in nearest_neighbor_pairs:
        if element_pair and tuple(sorted(str(symbol) for symbol in record["symbols"])) != element_pair:
            continue
        distance = float(record["distance_ang"])
        delta = abs(distance - target_distance) if target_distance is not None else None
        candidates.append({**record, "absolute_delta_ang": delta})

    if target_distance is None:
        matches = list(candidates)
        closest = None
    else:
        candidates.sort(
            key=lambda item: (
                float(item["absolute_delta_ang"]),
                float(item["distance_ang"]),
                int(item["i"]),
                int(item["j"]),
            )
        )
        matches = [item for item in candidates if float(item["absolute_delta_ang"]) <= tolerance]
        closest = candidates[0] if candidates else None

    return {
        "status": "MATCHED" if matches else "NO_MATCH",
        **common,
        "candidate_count": len(candidates),
        "match_count": len(matches),
        "matches": matches,
        "closest_candidate": closest,
    }


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


def symmetry_attempt(atoms: Any, symprec: float, limitations: list[str]) -> dict[str, Any]:
    try:
        import spglib  # type: ignore
    except Exception as exc:
        limitations.append(f"optional spglib symmetry detection unavailable: {exc}")
        return {"available": False, "status": "SKIPPED", "reason": "spglib unavailable"}

    try:
        dataset = spglib.get_symmetry_dataset(
            (atoms.cell.array, atoms.get_scaled_positions(wrap=True), atoms.get_atomic_numbers()),
            symprec=symprec,
        )
    except Exception as exc:
        limitations.append(f"spglib symmetry detection failed: {exc}")
        return {"available": True, "status": "FAILED", "reason": str(exc), "symprec": symprec}

    if dataset is None:
        limitations.append("spglib returned no symmetry dataset")
        return {"available": True, "status": "FAILED", "reason": "no dataset", "symprec": symprec}

    def get_field(name: str) -> Any:
        if isinstance(dataset, dict):
            return dataset.get(name)
        return getattr(dataset, name, None)

    return {
        "available": True,
        "status": "DETECTED",
        "symprec": symprec,
        "number": plain(get_field("number")),
        "international": plain(get_field("international")),
        "hall": plain(get_field("hall")),
        "choice": plain(get_field("choice")),
    }


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
            color = ELEMENT_COLORS.get(symbol, "#D62728")
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

    try:
        atoms = read(str(input_path), index=0)
    except Exception as exc:
        raise RuntimeError(f"failed to read CIF: {exc}") from exc

    limitations: list[str] = []
    symbols = atoms.get_chemical_symbols()
    counts = dict(sorted(Counter(symbols).items()))
    cellpar = atoms.cell.cellpar()
    volume = float(atoms.get_volume()) if atoms.cell.rank == 3 else None
    total_mass = float(sum(atoms.get_masses())) if len(atoms) else 0.0
    density = None
    if volume and volume > 0:
        density = total_mass / volume * AMU_PER_ANG3_TO_G_CM3
    else:
        limitations.append("density unavailable because cell volume is zero or undefined")

    nearest, short_flags = nearest_distances(atoms, args.short_distance_threshold)
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
        limitations.append("short-distance flags require human review and are not physics conclusions")

    symmetry = symmetry_attempt(atoms, args.symprec, limitations)
    views = []
    if args.views_dir:
        views = render_projection_views(atoms, Path(args.views_dir).expanduser().resolve(), input_path.stem)

    status = "WARN" if short_flags else "PASS"
    info = {
        "path": str(input_path),
        "name": input_path.name,
        "size_bytes": input_path.stat().st_size,
        "mtime": round(input_path.stat().st_mtime, 3),
    }

    return plain(
        {
            "status": status,
            "input": info,
            "execution": {
                "script": str(Path(__file__).resolve()),
                "command": shlex.join(sys.argv),
                "ase_version": getattr(ase, "__version__", "unknown"),
                "short_distance_threshold_ang": args.short_distance_threshold,
                "symprec": args.symprec,
                "bond_match": {
                    "element_pair": list(args.match_elements) if args.match_elements else None,
                    "target_distance_ang": args.match_bond_length,
                    "tolerance_ang": args.match_bond_tolerance,
                },
            },
            "structure": {
                "formula": atoms.get_chemical_formula(),
                "atom_count": len(atoms),
                "element_counts": counts,
                "pbc": [bool(v) for v in atoms.get_pbc()],
                "cell": {
                    "a": cellpar[0],
                    "b": cellpar[1],
                    "c": cellpar[2],
                    "alpha": cellpar[3],
                    "beta": cellpar[4],
                    "gamma": cellpar[5],
                    "rank": atoms.cell.rank,
                },
                "volume_ang3": volume,
                "total_mass_amu": total_mass,
                "density_g_cm3": density,
                "coordinates": coordinate_summary(atoms),
                "nearest_distances": nearest,
                "axis_gap_estimates": axis_gap_estimates(atoms),
                "symmetry_attempt": symmetry,
            },
            "flags": {"short_distances": short_flags},
            "views": views,
            "limitations": limitations,
            "not_assessed": [
                "DFT setup advice",
                "pseudopotential choice",
                "k-point or cutoff settings",
                "magnetic initialization",
                "physics credibility",
                "stability or synthesis feasibility",
            ],
        }
    )


def markdown_table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join("" if value is None else str(value) for value in row) + " |")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    structure = report["structure"]
    cell = structure["cell"]
    coordinates = structure["coordinates"]
    nearest = structure["nearest_distances"]
    bond_match = nearest["bond_length_match"]
    symmetry = structure["symmetry_attempt"]
    facts = [
        ["formula", structure["formula"], "JSON: structure.formula"],
        ["atom_count", structure["atom_count"], "JSON: structure.atom_count"],
        ["element_counts", json.dumps(structure["element_counts"], sort_keys=True), "JSON: structure.element_counts"],
        ["cell_a_b_c_ang", f'{cell["a"]}, {cell["b"]}, {cell["c"]}', "JSON: structure.cell"],
        ["cell_angles_deg", f'{cell["alpha"]}, {cell["beta"]}, {cell["gamma"]}', "JSON: structure.cell"],
        ["volume_ang3", structure["volume_ang3"], "JSON: structure.volume_ang3"],
        ["density_g_cm3", structure["density_g_cm3"], "JSON: structure.density_g_cm3"],
        ["min_distance_ang", nearest["min_distance_ang"], "JSON: structure.nearest_distances.min_distance_ang"],
        ["bond_match_status", bond_match["status"], "JSON: structure.nearest_distances.bond_length_match"],
        ["symmetry_status", symmetry["status"], "JSON: structure.symmetry_attempt"],
    ]

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
                item["distance_ang"],
            ]
        )

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
                item["distance_ang"],
                item["absolute_delta_ang"],
            ]
        )
    if not match_rows:
        match_rows.append(["none", "", "", ""])
    closest = bond_match["closest_candidate"]
    closest_rows = []
    if closest:
        closest_rows.append(
            [
                f'{closest["i"]}-{closest["j"]}',
                "-".join(closest["symbols"]),
                closest["distance_ang"],
                closest["absolute_delta_ang"],
            ]
        )
    else:
        closest_rows.append(["none", "", "", ""])

    flag_rows = []
    for flag in report["flags"]["short_distances"]:
        flag_rows.append(
            [
                f'{flag["i"]}-{flag["j"]}',
                "-".join(flag["symbols"]),
                flag["distance_ang"],
                flag["threshold_ang"],
            ]
        )
    if not flag_rows:
        flag_rows.append(["none", "", "", ""])

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
        ["symprec", symmetry.get("symprec")],
        ["reason", symmetry.get("reason")],
    ]

    view_rows = []
    view_images = []
    for view in report.get("views", []):
        view_rows.append([view["axis"], view["x_axis"], view["y_axis"], view["path"], view["projection"]])
        view_images.extend([f'### View along {view["axis"]}', "", f'![view along {view["axis"]}]({view["path"]})', ""])
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
            f'- Input CIF: `{report["input"]["path"]}`',
            f'- Script: `{report["execution"]["script"]}`',
            f'- Command: `{report["execution"]["command"]}`',
            f'- ASE version: `{report["execution"]["ase_version"]}`',
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
            markdown_table(nearest_rows, ["Pair", "Symbols", "Distance Ang"]),
            "",
            "## Nearest-Neighbor Bond-Length Match",
            markdown_table(match_query_rows, ["Field", "Value"]),
            "",
            markdown_table(match_rows, ["Matched pair", "Symbols", "Distance Ang", "Absolute delta Ang"]),
            "",
            "### Closest Candidate",
            markdown_table(closest_rows, ["Pair", "Symbols", "Distance Ang", "Absolute delta Ang"]),
            "",
            f'- Matching rule: {bond_match["matching_rule"]}',
            f'- Periodic scope: {bond_match["periodic_scope"]}',
            "",
            "## Short-Distance Flags",
            markdown_table(flag_rows, ["Pair", "Symbols", "Distance ang", "Threshold ang"]),
            "",
            "## Axis Gap Estimates",
            markdown_table(gap_rows, ["Axis", "Largest fractional gap", "Largest gap ang", "Occupied span estimate ang"]),
            "",
            "## Symmetry Attempt",
            markdown_table(symmetry_rows, ["Field", "Value"]),
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
    parser = argparse.ArgumentParser(description="Analyze CIF structure facts with ASE.")
    parser.add_argument("--input", required=True, help="Input CIF file path.")
    parser.add_argument("--json", required=True, help="Output JSON artifact path.")
    parser.add_argument("--markdown", required=True, help="Output Markdown artifact path.")
    parser.add_argument("--views-dir", help="Optional directory for PNG views along a, b, and c.")
    parser.add_argument("--short-distance-threshold", type=float, default=0.6, help="Flag interatomic distances below this Angstrom threshold.")
    parser.add_argument("--symprec", type=float, default=1e-3, help="spglib symmetry precision when spglib is installed.")
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
    return parser.parse_args(argv)


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

    try:
        report = build_report(input_path, args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(render_markdown(report), encoding="utf-8")
    except Exception as exc:
        print(f"failed to write artifacts: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {json_path}")
    print(f"wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
