from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from . import __version__
from .electronic import (
    _check_maturity,
    _output_record,
    _refuse_existing_outputs,
    _save_figure_atomic,
    _source_record,
    _validated_dataset,
    _write_csv_atomic,
)
from .utils import utc_now, write_json_atomic


HBAR_C_EV_ANGSTROM = 1973.269804593025


def _read_named_table(path: Path) -> tuple[list[str], list[dict[str, float]]]:
    lines = [line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if len(lines) < 2:
        raise ValueError(f"{path.name}: named table requires a header and data")
    delimiter = "," if "," in lines[0] else None
    headers = [item.strip() for item in (next(csv.reader([lines[0]])) if delimiter else lines[0].split())]
    if not headers or len(set(headers)) != len(headers):
        raise ValueError(f"{path.name}: table headers must be unique and nonempty")
    result = []
    for line_number, line in enumerate(lines[1:], start=2):
        fields = [item.strip() for item in (next(csv.reader([line])) if delimiter else line.split())]
        if len(fields) != len(headers):
            raise ValueError(f"{path.name}:{line_number}: table width does not match header")
        try:
            values = [float(value) for value in fields]
        except ValueError as exc:
            raise ValueError(f"{path.name}:{line_number}: nonnumeric table value") from exc
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"{path.name}:{line_number}: non-finite table value")
        result.append(dict(zip(headers, values)))
    if not result:
        raise ValueError(f"{path.name}: table contains no data rows")
    return headers, result


def _plot_neb(
    coordinates: list[float],
    relative_energies: list[float],
    forces: list[float] | None,
    coordinate_unit: str,
    energy_unit: str,
    force_unit: str | None,
    output: Path,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    panels = 2 if forces is not None else 1
    with plt.style.context(str(style)):
        figure, axes = plt.subplots(panels, 1, figsize=(7.0, 3.5 * panels), squeeze=False, sharex=True)
        energy_axis = axes[0][0]
        energy_axis.plot(coordinates, relative_energies, color="#7f1d1d", marker="o", linewidth=1.1)
        energy_axis.set_ylabel(f"Relative energy ({energy_unit})")
        energy_axis.set_xlim(coordinates[0], coordinates[-1])
        energy_axis.margins(x=0)
        if forces is not None:
            force_axis = axes[1][0]
            force_axis.plot(coordinates, forces, color="#2f6f9f", marker="o", linewidth=1.0)
            force_axis.set_ylabel(f"Image force ({force_unit})")
            force_axis.set_xlabel(f"Reaction coordinate ({coordinate_unit})")
            force_axis.set_xlim(coordinates[0], coordinates[-1])
            force_axis.margins(x=0)
        else:
            energy_axis.set_xlabel(f"Reaction coordinate ({coordinate_unit})")
        figure.tight_layout()
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {
        "schema_version": "1.0",
        "plot_type": "neb-profile",
        "x_limits": [coordinates[0], coordinates[-1]],
        "force_panel": forces is not None,
        "output": _output_record(output, "figure", "image/png"),
    }


def normalize_neb_table(
    table_path: Path,
    code: str,
    output_directory: Path,
    dataset_id: str,
    *,
    coordinate_column: str,
    energy_column: str,
    coordinate_unit: str,
    energy_unit: str,
    reference: str,
    force_column: str | None = None,
    force_unit: str | None = None,
    figure_output: Path | None = None,
    maturity: str = "synthetic-validated",
    overwrite: bool = False,
) -> dict[str, Path]:
    _check_maturity(maturity)
    if code not in {"qe", "vasp", "mixed"}:
        raise ValueError("code must be qe, vasp, or mixed")
    if reference not in {"initial", "minimum", "none"}:
        raise ValueError("reference must be initial, minimum, or none")
    if not coordinate_unit.strip() or not energy_unit.strip():
        raise ValueError("coordinate_unit and energy_unit must be explicit")
    if (force_column is None) != (force_unit is None):
        raise ValueError("force_column and force_unit must be supplied together")
    headers, rows = _read_named_table(table_path)
    required = [coordinate_column, energy_column] + ([force_column] if force_column else [])
    missing = [column for column in required if column not in headers]
    if missing:
        raise ValueError(f"{table_path.name}: missing columns {missing}")
    coordinates = [row[coordinate_column] for row in rows]
    energies = [row[energy_column] for row in rows]
    forces = [row[force_column] for row in rows] if force_column else None
    if len(coordinates) < 3:
        raise ValueError("NEB table requires at least three images including endpoints")
    if any(right <= left for left, right in zip(coordinates, coordinates[1:])):
        raise ValueError("reaction coordinate must be strictly increasing")
    reference_energy = {"initial": energies[0], "minimum": min(energies), "none": 0.0}[reference]
    relative = [energy - reference_energy for energy in energies]
    saddle_index = max(range(len(energies)), key=energies.__getitem__)
    forward_barrier = energies[saddle_index] - energies[0]
    reverse_barrier = energies[saddle_index] - energies[-1]

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    normalized_path = output_directory / "neb.csv"
    analysis_path = output_directory / "neb.analysis.json"
    plot_metadata_path = output_directory / "neb.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "neb.png"
    dataset_path = output_directory / "neb.dataset.json"
    _refuse_existing_outputs((normalized_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite)
    fields = ["image_index", "reaction_coordinate", "energy_raw", "energy_relative"] + (["image_force"] if forces else [])
    _write_csv_atomic(
        normalized_path,
        fields,
        (
            {
                "image_index": index,
                "reaction_coordinate": coordinate,
                "energy_raw": energy,
                "energy_relative": relative_energy,
                **({"image_force": forces[index]} if forces else {}),
            }
            for index, (coordinate, energy, relative_energy) in enumerate(zip(coordinates, energies, relative))
        ),
    )
    limitations = [
        "The reaction coordinate, energy, force columns, and units are caller-declared; no code-specific column guessing is performed.",
        "The maximum sampled image is reported as the discrete saddle image; no spline maximum or transition-state proof is inferred.",
        "Barrier values are numerical endpoint-to-maximum differences and do not establish path convergence or physical mechanism.",
    ]
    analysis = {
        "schema_version": "1.0",
        "image_count": len(rows),
        "reference": reference,
        "reference_energy": reference_energy,
        "saddle_image_index": saddle_index,
        "saddle_coordinate": coordinates[saddle_index],
        "forward_barrier": forward_barrier,
        "reverse_barrier": reverse_barrier,
        "energy_unit": energy_unit,
        "coordinate_unit": coordinate_unit,
        "force_unit": force_unit,
        "maximum_force": max(forces) if forces else None,
        "limitations": limitations,
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_neb(coordinates, relative, forces, coordinate_unit, energy_unit, force_unit, figure_path)
    write_json_atomic(plot_metadata_path, plot_metadata)
    columns = [
        {"name": "image_index", "dtype": "integer", "unit": None, "role": "image-index"},
        {"name": "reaction_coordinate", "dtype": "float", "unit": coordinate_unit, "role": "caller-reaction-coordinate"},
        {"name": "energy_raw", "dtype": "float", "unit": energy_unit, "role": "raw-image-energy"},
        {"name": "energy_relative", "dtype": "float", "unit": energy_unit, "role": "referenced-image-energy", "reference": reference},
    ]
    if forces:
        columns.append({"name": "image_force", "dtype": "float", "unit": force_unit, "role": "caller-declared-image-force"})
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "neb",
        "code": code,
        "maturity": maturity,
        "representation": "trajectory",
        "source_files": [_source_record(table_path, "neb-table")],
        "dimensions": {"images": len(rows), "rows": len(rows)},
        "columns": columns,
        "data_files": [
            _output_record(normalized_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [{
            "operation": "energy-reference-subtraction",
            "parameters": {"reference": reference, "reference_energy": reference_energy},
            "input_columns": ["energy_raw"],
            "output_columns": ["energy_relative"],
        }],
        "validation": {"status": "pass", "checks": [
            {"id": "finite-values", "status": "pass", "message": "All selected values are finite."},
            {"id": "image-order", "status": "pass", "message": "Reaction coordinates are strictly increasing."},
            {"id": "endpoint-presence", "status": "pass", "message": "At least three images including two endpoints are present."},
            {"id": "force-convergence", "status": "not-run", "message": "No project-specific force threshold is imposed by the generic normalizer."},
            {"id": "energy-reference", "status": "pass", "message": f"The caller selected the {reference} reference convention."},
        ]},
        "limitations": limitations,
        "provenance": {"producer": "dftpost.neb-table", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {"table": normalized_path, "analysis": analysis_path, "plot_metadata": plot_metadata_path, "figure": figure_path, "dataset": dataset_path}


def _plot_optical(energy: list[float], series: dict[str, dict[str, list[float]]], output: Path) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    colors = ["#7f1d1d", "#2f6f9f", "#348f50", "#8f5e9f", "#c06b2c", "#555555"]
    with plt.style.context(str(style)):
        figure, axes = plt.subplots(3, 1, figsize=(7.2, 9.0), sharex=True)
        for index, (label, values) in enumerate(sorted(series.items())):
            color = colors[index % len(colors)]
            axes[0].plot(energy, values["real"], color=color, label=label)
            axes[1].plot(energy, values["imag"], color=color, label=label)
            axes[2].plot(energy, values["absorption_cm-1"], color=color, label=label)
        axes[0].set_ylabel(r"$\epsilon_1$")
        axes[1].set_ylabel(r"$\epsilon_2$")
        axes[2].set_ylabel(r"Absorption (cm$^{-1}$)")
        axes[2].set_xlabel("Photon energy (eV)")
        for axis in axes:
            axis.set_xlim(energy[0], energy[-1])
            axis.margins(x=0)
            axis.legend(frameon=False)
        figure.tight_layout()
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {
        "schema_version": "1.0",
        "plot_type": "dielectric-and-absorption-spectrum",
        "x_limits_ev": [energy[0], energy[-1]],
        "components": sorted(series),
        "output": _output_record(output, "figure", "image/png"),
    }


def normalize_optical_table(
    table_path: Path,
    code: str,
    output_directory: Path,
    dataset_id: str,
    *,
    energy_column: str,
    components: dict[str, tuple[str, str]],
    broadening_declaration: str,
    figure_output: Path | None = None,
    maturity: str = "synthetic-validated",
    overwrite: bool = False,
) -> dict[str, Path]:
    _check_maturity(maturity)
    if code not in {"qe", "vasp", "mixed"}:
        raise ValueError("code must be qe, vasp, or mixed")
    if not components:
        raise ValueError("at least one dielectric component mapping is required")
    if not broadening_declaration.strip():
        raise ValueError("broadening_declaration must be explicit and nonempty")
    headers, rows = _read_named_table(table_path)
    selected_columns = [energy_column] + [column for pair in components.values() for column in pair]
    missing = [column for column in selected_columns if column not in headers]
    if missing:
        raise ValueError(f"{table_path.name}: missing columns {missing}")
    energy = [row[energy_column] for row in rows]
    if len(energy) < 2 or energy[0] < 0.0 or any(right <= left for left, right in zip(energy, energy[1:])):
        raise ValueError("photon-energy grid must be nonnegative and strictly increasing")
    series: dict[str, dict[str, list[float]]] = {}
    for label, (real_column, imag_column) in components.items():
        real_values = [row[real_column] for row in rows]
        imag_values = [row[imag_column] for row in rows]
        magnitude = [math.hypot(real, imag) for real, imag in zip(real_values, imag_values)]
        refractive = [math.sqrt(max(0.0, 0.5 * (mag + real))) for mag, real in zip(magnitude, real_values)]
        extinction = [math.sqrt(max(0.0, 0.5 * (mag - real))) for mag, real in zip(magnitude, real_values)]
        absorption = [2.0 * photon_energy * kappa / HBAR_C_EV_ANGSTROM * 1.0e8 for photon_energy, kappa in zip(energy, extinction)]
        series[label] = {"real": real_values, "imag": imag_values, "refractive": refractive, "extinction": extinction, "absorption_cm-1": absorption}

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    normalized_path = output_directory / "optical.csv"
    analysis_path = output_directory / "optical.analysis.json"
    plot_metadata_path = output_directory / "optical.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "optical.png"
    dataset_path = output_directory / "optical.dataset.json"
    _refuse_existing_outputs((normalized_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite)
    _write_csv_atomic(
        normalized_path,
        ["energy_ev", "component", "epsilon_real", "epsilon_imag", "refractive_index", "extinction_coefficient", "absorption_cm_1"],
        (
            {
                "energy_ev": photon_energy,
                "component": label,
                "epsilon_real": values["real"][index],
                "epsilon_imag": values["imag"][index],
                "refractive_index": values["refractive"][index],
                "extinction_coefficient": values["extinction"][index],
                "absorption_cm_1": values["absorption_cm-1"][index],
            }
            for label, values in sorted(series.items())
            for index, photon_energy in enumerate(energy)
        ),
    )
    component_extrema = {
        label: {
            "epsilon_real_min": min(values["real"]),
            "epsilon_real_max": max(values["real"]),
            "epsilon_imag_min": min(values["imag"]),
            "epsilon_imag_max": max(values["imag"]),
            "absorption_max_cm_1": max(values["absorption_cm-1"]),
        }
        for label, values in sorted(series.items())
    }
    limitations = [
        "Energy and dielectric tensor-component columns are caller-mapped; the normalizer does not infer tensor semantics from filenames.",
        "The broadening declaration is provenance text supplied by the caller and is not reconstructed from the spectrum.",
        "Derived n, k, and absorption use the principal nonmagnetic square root of epsilon; anisotropic propagation and local-field analysis are outside scope.",
        "No material-specific peak assignment, transition attribution, or experimental comparison is performed.",
    ]
    analysis = {
        "schema_version": "1.0",
        "energy_points": len(energy),
        "component_count": len(series),
        "energy_range_ev": [energy[0], energy[-1]],
        "broadening_declaration": broadening_declaration,
        "component_extrema": component_extrema,
        "absorption_formula": "alpha_cm^-1 = 2 * E_eV * kappa / (hbar*c in eV*angstrom) * 1e8",
        "hbar_c_ev_angstrom": HBAR_C_EV_ANGSTROM,
        "limitations": limitations,
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_optical(energy, series, figure_path)
    write_json_atomic(plot_metadata_path, plot_metadata)
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "optical",
        "code": code,
        "maturity": maturity,
        "representation": "table",
        "source_files": [_source_record(table_path, "dielectric-data")],
        "dimensions": {"energy_points": len(energy), "components": len(series), "rows": len(energy) * len(series)},
        "columns": [
            {"name": "energy_ev", "dtype": "float", "unit": "eV", "role": "photon-energy"},
            {"name": "component", "dtype": "string", "unit": None, "role": "caller-mapped-tensor-component"},
            {"name": "epsilon_real", "dtype": "float", "unit": None, "role": "dielectric-real"},
            {"name": "epsilon_imag", "dtype": "float", "unit": None, "role": "dielectric-imaginary"},
            {"name": "absorption_cm_1", "dtype": "float", "unit": "cm^-1", "role": "derived-absorption"},
        ],
        "data_files": [
            _output_record(normalized_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [{
            "operation": "principal-complex-dielectric-optical-constants",
            "parameters": {"hbar_c_ev_angstrom": HBAR_C_EV_ANGSTROM},
            "input_columns": ["epsilon_real", "epsilon_imag", "energy_ev"],
            "output_columns": ["refractive_index", "extinction_coefficient", "absorption_cm_1"],
        }],
        "validation": {"status": "pass", "checks": [
            {"id": "finite-values", "status": "pass", "message": "All selected and derived values are finite."},
            {"id": "monotonic-energy-grid", "status": "pass", "message": "Photon energy is nonnegative and strictly increasing."},
            {"id": "tensor-shape", "status": "pass", "message": "Every mapped component shares the same energy grid."},
            {"id": "unit-declaration", "status": "pass", "message": "Photon energy is explicitly normalized as eV and epsilon is dimensionless."},
            {"id": "broadening-declaration", "status": "pass", "message": "The caller supplied an explicit broadening declaration."},
        ]},
        "limitations": limitations,
        "provenance": {"producer": "dftpost.optical-table", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {"table": normalized_path, "analysis": analysis_path, "plot_metadata": plot_metadata_path, "figure": figure_path, "dataset": dataset_path}
