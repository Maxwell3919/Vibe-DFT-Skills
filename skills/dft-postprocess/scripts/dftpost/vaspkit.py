from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from . import __version__
from .electronic import (
    _check_maturity,
    _output_record,
    _plot_bands,
    _refuse_existing_outputs,
    _source_record,
    _validated_dataset,
    _write_csv_atomic,
)
from .registry import resolve_backend_maturity
from .utils import utc_now, write_json_atomic


def parse_vaspkit_band_data(path: Path) -> tuple[list[float], list[list[float]]]:
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"VASPKIT band table is missing: {path}")
    rows: list[list[float]] = []
    width: int | None = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "!")):
            continue
        try:
            row = [float(value) for value in stripped.split()]
        except ValueError as exc:
            raise ValueError(f"{path.name}:{line_number}: nonnumeric VASPKIT band row") from exc
        if len(row) < 2 or not all(math.isfinite(value) for value in row):
            raise ValueError(f"{path.name}:{line_number}: invalid VASPKIT band row")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError(f"{path.name}:{line_number}: inconsistent VASPKIT band column count")
        rows.append(row)
    if len(rows) < 2:
        raise ValueError(f"{path.name}: at least two VASPKIT k-path rows are required")
    kpoints = [row[0] for row in rows]
    if any(right < left for left, right in zip(kpoints, kpoints[1:])) or kpoints[-1] <= kpoints[0]:
        raise ValueError(f"{path.name}: VASPKIT path coordinate must be nondecreasing with a nonzero interval")
    assert width is not None
    bands = [[row[column] for row in rows] for column in range(1, width)]
    return kpoints, bands


def parse_vaspkit_klabels(path: Path, lower: float, upper: float) -> list[dict[str, Any]]:
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"VASPKIT KLABELS file is missing: {path}")
    points: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("*", "#", "!")):
            continue
        fields = stripped.split()
        if len(fields) < 2:
            continue
        try:
            coordinate = float(fields[1])
        except ValueError:
            continue
        if not math.isfinite(coordinate):
            raise ValueError(f"{path.name}:{line_number}: non-finite KLABELS coordinate")
        label = fields[0].strip()
        if not label:
            raise ValueError(f"{path.name}:{line_number}: empty KLABELS label")
        tolerance = max(1.0, abs(lower), abs(upper)) * 1.0e-8
        if coordinate < lower - tolerance or coordinate > upper + tolerance:
            raise ValueError(f"{path.name}:{line_number}: KLABELS coordinate lies outside the band path")
        if points and coordinate < points[-1]["k_distance"] - tolerance:
            raise ValueError(f"{path.name}: KLABELS coordinates are not ordered")
        if points and abs(coordinate - points[-1]["k_distance"]) <= tolerance:
            if label != points[-1]["label"]:
                points[-1]["label"] = f"{points[-1]['label']}|{label}"
            continue
        points.append({"label": label, "k_distance": coordinate})
    if not points:
        raise ValueError(f"{path.name}: no VASPKIT high-symmetry labels were parsed")
    return points


def normalize_vaspkit_bands(
    band_data_path: Path,
    klabels_path: Path,
    output_directory: Path,
    dataset_id: str,
    *,
    energy_offset_ev: float,
    energy_reference_description: str,
    figure_output: Path | None = None,
    energy_window_ev: tuple[float, float] | None = None,
    maturity: str | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    maturity = resolve_backend_maturity(
        "bands", "vasp", "python.vaspkit-table", maturity
    )
    _check_maturity(maturity)
    if not math.isfinite(energy_offset_ev):
        raise ValueError("VASPKIT energy offset must be finite")
    description = energy_reference_description.strip()
    if not description:
        raise ValueError("VASPKIT energy-reference description must be explicit")

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "bands.csv"
    analysis_path = output_directory / "bands.analysis.json"
    plot_metadata_path = output_directory / "bands.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "bands.png"
    dataset_path = output_directory / "bands.dataset.json"
    _refuse_existing_outputs(
        (table_path, analysis_path, plot_metadata_path, figure_path, dataset_path),
        overwrite,
    )

    kpoints, input_bands = parse_vaspkit_band_data(band_data_path)
    symmetry_points = parse_vaspkit_klabels(klabels_path, kpoints[0], kpoints[-1])
    relative_bands = [[energy + energy_offset_ev for energy in band] for band in input_bands]
    _write_csv_atomic(
        table_path,
        ["k_index", "k_distance", "band_index", "energy_input_ev", "energy_relative_ev"],
        (
            {
                "k_index": k_index,
                "k_distance": k_distance,
                "band_index": band_index,
                "energy_input_ev": energy,
                "energy_relative_ev": energy + energy_offset_ev,
            }
            for band_index, band in enumerate(input_bands, start=1)
            for k_index, (k_distance, energy) in enumerate(zip(kpoints, band), start=1)
        ),
    )
    flattened = [value for band in relative_bands for value in band]
    crossings = [
        index
        for index, band in enumerate(relative_bands, start=1)
        if min(band) <= 0.0 <= max(band)
    ]
    analysis = {
        "schema_version": "1.0",
        "bands": len(input_bands),
        "kpoints": len(kpoints),
        "energy_offset_ev": energy_offset_ev,
        "energy_reference_description": description,
        "energy_transform": "energy_relative_ev = energy_input_ev + energy_offset_ev",
        "energy_min_relative_ev": min(flattened),
        "energy_max_relative_ev": max(flattened),
        "reference_crossing_band_indices": crossings,
        "high_symmetry_points": symmetry_points,
        "limitations": [
            "The adapter does not infer whether VASPKIT input energies are absolute or already shifted.",
            "The caller-supplied energy offset and reference description define the full energy transformation.",
            "Discrete path crossings do not prove a global Brillouin-zone property.",
        ],
    }
    write_json_atomic(analysis_path, analysis)
    # _plot_bands subtracts its reference argument; using -offset applies the declared additive transform.
    plot_metadata = _plot_bands(
        kpoints,
        input_bands,
        -energy_offset_ev,
        figure_path,
        energy_window_ev,
        xlabel="Path coordinate (VASPKIT line-mode)",
        symmetry_points=symmetry_points,
    )
    plot_metadata.update(
        {
            "plot_type": "vaspkit-bands",
            "energy_offset_ev": energy_offset_ev,
            "energy_reference_description": description,
            "high_symmetry_points": symmetry_points,
        }
    )
    write_json_atomic(plot_metadata_path, plot_metadata)

    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "bands",
        "code": "vasp",
        "maturity": maturity,
        "representation": "table",
        "source_files": [
            _source_record(band_data_path, "vaspkit-band-table"),
            _source_record(klabels_path, "vaspkit-klabels"),
        ],
        "dimensions": {
            "bands": len(input_bands),
            "kpoints": len(kpoints),
            "rows": len(input_bands) * len(kpoints),
        },
        "columns": [
            {"name": "k_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "k_distance", "dtype": "float", "unit": None, "role": "vaspkit-path-coordinate"},
            {"name": "band_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "energy_input_ev", "dtype": "float", "unit": "eV", "role": "input-energy", "reference": "caller-described"},
            {"name": "energy_relative_ev", "dtype": "float", "unit": "eV", "role": "eigenvalue", "reference": "caller-declared-offset"},
        ],
        "data_files": [
            _output_record(table_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "add-explicit-energy-offset",
                "parameters": {
                    "energy_offset_ev": energy_offset_ev,
                    "energy_reference_description": description,
                },
                "input_columns": ["energy_input_ev"],
                "output_columns": ["energy_relative_ev"],
            }
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "finite-values", "status": "pass", "message": "All VASPKIT path and energy values are finite."},
                {"id": "band-dimensions", "status": "pass", "message": "Every VASPKIT row has the same band count."},
                {"id": "energy-transform", "status": "pass", "message": "The caller supplied a finite energy offset and reference description."},
                {"id": "path-labels", "status": "pass", "message": "KLABELS points are ordered and lie inside the path interval."},
            ],
        },
        "limitations": analysis["limitations"],
        "provenance": {
            "producer": "dftpost.vaspkit-bands",
            "producer_version": __version__,
            "generated_utc": utc_now(),
            "tool_execution_ids": [],
        },
    }
    _validated_dataset(dataset, dataset_path)
    return {
        "table": table_path,
        "analysis": analysis_path,
        "plot_metadata": plot_metadata_path,
        "figure": figure_path,
        "dataset": dataset_path,
    }
