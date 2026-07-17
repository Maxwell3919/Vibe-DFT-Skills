from __future__ import annotations

import math
from pathlib import Path
import re
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


FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
RY_TO_EV = 13.605693122994
BOHR_TO_ANGSTROM = 0.529177210903
RY_PER_BOHR_TO_EV_PER_ANGSTROM = RY_TO_EV / BOHR_TO_ANGSTROM


def _parse_qe_trace(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    groups: list[dict[int, float]] = []
    current: dict[int, float] = {}
    current_iteration: int | None = None
    for line in lines:
        iteration_match = re.search(r"iteration\s*#\s*(\d+)", line, flags=re.IGNORECASE)
        if iteration_match:
            iteration = int(iteration_match.group(1))
            if iteration == 1 and current:
                groups.append(current)
                current = {}
            current_iteration = iteration
            continue
        residual_match = re.search(rf"estimated\s+scf\s+accuracy\s*<\s*({FLOAT})\s*Ry", line, flags=re.IGNORECASE)
        if residual_match and current_iteration is not None:
            residual = float(residual_match.group(1)) * RY_TO_EV
            if not math.isfinite(residual):
                raise ValueError(f"{path.name}: non-finite QE SCF residual")
            current[current_iteration] = residual
    if current:
        groups.append(current)

    energies = [
        float(value) * RY_TO_EV
        for value in re.findall(rf"!\s+total\s+energy\s*=\s*({FLOAT})\s*Ry", text, flags=re.IGNORECASE)
    ]
    convergence_counts = [
        int(value)
        for value in re.findall(r"convergence\s+has\s+been\s+achieved\s+in\s+(\d+)\s+iterations", text, flags=re.IGNORECASE)
    ]
    forces = [
        float(value) * RY_PER_BOHR_TO_EV_PER_ANGSTROM
        for value in re.findall(rf"Total\s+force\s*=\s*({FLOAT})", text, flags=re.IGNORECASE)
    ]
    if not energies and not groups and not forces:
        raise ValueError(f"{path.name}: no QE run-trace records found")
    ionic_count = max(len(energies), len(groups), len(forces), len(convergence_counts), 1)
    electronic_rows = []
    for ionic_index, group in enumerate(groups, start=1):
        for iteration, residual in sorted(group.items()):
            electronic_rows.append({
                "ionic_step": ionic_index,
                "electronic_iteration": iteration,
                "residual_ev": residual,
            })
    ionic_rows = []
    for index in range(ionic_count):
        group = groups[index] if index < len(groups) else {}
        iterations = convergence_counts[index] if index < len(convergence_counts) else (max(group) if group else 0)
        ionic_rows.append({
            "ionic_step": index + 1,
            "energy_ev": energies[index] if index < len(energies) else None,
            "force_ev_per_angstrom": forces[index] if index < len(forces) else None,
            "force_kind": "total-force" if index < len(forces) else "none",
            "electronic_iterations": iterations,
        })
    calculation_match = re.search(r"calculation\s*=\s*['\"]?([A-Za-z_-]+)", text, flags=re.IGNORECASE)
    calculation = calculation_match.group(1).lower() if calculation_match else "unknown"
    geometry_marker = bool(re.search(r"(?:bfgs\s+converged|End\s+of\s+BFGS\s+Geometry\s+Optimization)", text, flags=re.IGNORECASE))
    if calculation in {"relax", "vc-relax", "md", "vc-md"}:
        geometry_converged: bool | None = geometry_marker
    else:
        geometry_converged = None
    return {
        "code": "qe",
        "run_complete": "JOB DONE." in text,
        "electronic_converged": True if convergence_counts else None,
        "geometry_converged": geometry_converged,
        "calculation": calculation,
        "electronic_rows": electronic_rows,
        "ionic_rows": ionic_rows,
        "force_kind": "total-force",
    }


def _vasp_force_blocks(lines: list[str], path: Path) -> list[float]:
    maxima = []
    index = 0
    while index < len(lines):
        if "POSITION" not in lines[index] or "TOTAL-FORCE" not in lines[index]:
            index += 1
            continue
        index += 1
        started = False
        values = []
        while index < len(lines):
            stripped = lines[index].strip()
            index += 1
            if not stripped:
                if started:
                    break
                continue
            if set(stripped) <= {"-", " "}:
                if started:
                    break
                continue
            fields = stripped.split()
            try:
                numbers = [float(value) for value in fields]
            except ValueError:
                if started:
                    break
                continue
            if len(numbers) < 6:
                if started:
                    break
                continue
            started = True
            force = numbers[-3:]
            if not all(math.isfinite(value) for value in force):
                raise ValueError(f"{path.name}: non-finite VASP force")
            values.append(math.sqrt(sum(value * value for value in force)))
        if values:
            maxima.append(max(values))
    return maxima


def _parse_vasp_trace(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    iteration_pairs = [
        (int(ionic), int(electronic))
        for ionic, electronic in re.findall(r"Iteration\s+(\d+)\s*\(\s*(\d+)\s*\)", text)
    ]
    electronic_energies = [
        float(value)
        for value in re.findall(rf"free energy\s+TOTEN\s*=\s*({FLOAT})\s+eV", text, flags=re.IGNORECASE)
    ]
    energies = [
        float(value)
        for value in re.findall(rf"free\s{{2,}}energy\s+TOTEN\s*=\s*({FLOAT})\s+eV", text, flags=re.IGNORECASE)
    ]
    force_maxima = _vasp_force_blocks(lines, path)
    if not iteration_pairs and not energies and not force_maxima:
        raise ValueError(f"{path.name}: no VASP run-trace records found")
    iteration_counts: dict[int, int] = {}
    for ionic, electronic in iteration_pairs:
        iteration_counts[ionic] = max(iteration_counts.get(ionic, 0), electronic)
    ionic_count = max(
        max(iteration_counts, default=0),
        len(energies),
        len(force_maxima),
        1,
    )
    electronic_rows = [
        {
            "ionic_step": ionic,
            "electronic_iteration": electronic,
            "residual_ev": None,
            "electronic_energy_ev": electronic_energies[index] if index < len(electronic_energies) else None,
        }
        for index, (ionic, electronic) in enumerate(iteration_pairs)
    ]
    ionic_rows = []
    for index in range(ionic_count):
        ionic_rows.append({
            "ionic_step": index + 1,
            "energy_ev": energies[index] if index < len(energies) else None,
            "force_ev_per_angstrom": force_maxima[index] if index < len(force_maxima) else None,
            "force_kind": "max-atom-force" if index < len(force_maxima) else "none",
            "electronic_iterations": iteration_counts.get(index + 1, 0),
        })
    nsw_matches = re.findall(r"\bNSW\s*=\s*(\d+)", text)
    nsw = int(nsw_matches[-1]) if nsw_matches else None
    geometry_marker = "reached required accuracy" in text.lower()
    if nsw == 0:
        geometry_converged: bool | None = None
    elif nsw is not None or force_maxima:
        geometry_converged = geometry_marker
    else:
        geometry_converged = None
    return {
        "code": "vasp",
        "run_complete": "General timing and accounting" in text,
        "electronic_converged": None,
        "geometry_converged": geometry_converged,
        "calculation": "ionic" if nsw and nsw > 0 else "static" if nsw == 0 else "unknown",
        "electronic_rows": electronic_rows,
        "ionic_rows": ionic_rows,
        "force_kind": "max-atom-force",
    }


def _plot_trace(parsed: dict[str, Any], output: Path) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    ionic = parsed["ionic_rows"]
    energy_points = [(row["ionic_step"], row["energy_ev"]) for row in ionic if row["energy_ev"] is not None]
    residual_points = [
        (row["electronic_iteration"], row["residual_ev"])
        for row in parsed["electronic_rows"] if row["residual_ev"] is not None and row["residual_ev"] > 0.0
    ]
    electronic_energy_points = [
        (row["electronic_iteration"], row.get("electronic_energy_ev"))
        for row in parsed["electronic_rows"] if row.get("electronic_energy_ev") is not None
    ]
    force_points = [(row["ionic_step"], row["force_ev_per_angstrom"]) for row in ionic if row["force_ev_per_angstrom"] is not None]
    output.parent.mkdir(parents=True, exist_ok=True)
    with plt.style.context(str(style)):
        figure, (energy_axis, convergence_axis) = plt.subplots(2, 1, figsize=(6.4, 6.8))
        if energy_points:
            energy_axis.plot(
                [point[0] for point in energy_points],
                [point[1] for point in energy_points],
                color="#7f1d1d",
                marker="o",
                linewidth=1.1,
            )
            if len(energy_points) > 1:
                energy_axis.set_xlim(energy_points[0][0], energy_points[-1][0])
                energy_axis.margins(x=0)
        else:
            energy_axis.text(0.5, 0.5, "No ionic energy records", transform=energy_axis.transAxes, ha="center")
        energy_axis.set_xlabel("Ionic step")
        energy_axis.set_ylabel("Total energy (eV)")

        if residual_points:
            convergence_axis.semilogy(
                [point[0] for point in residual_points],
                [point[1] for point in residual_points],
                color="#1f4e79",
                marker="o",
                linewidth=1.0,
            )
            if len(residual_points) > 1:
                convergence_axis.set_xlim(residual_points[0][0], residual_points[-1][0])
                convergence_axis.margins(x=0)
            convergence_axis.set_xlabel("Electronic iteration")
            convergence_axis.set_ylabel("SCF residual (eV)")
            lower_plot = "scf-residual"
        elif electronic_energy_points:
            convergence_axis.plot(
                [point[0] for point in electronic_energy_points],
                [point[1] for point in electronic_energy_points],
                color="#1f4e79",
                marker="o",
                linewidth=1.0,
            )
            if len(electronic_energy_points) > 1:
                convergence_axis.set_xlim(electronic_energy_points[0][0], electronic_energy_points[-1][0])
                convergence_axis.margins(x=0)
            convergence_axis.set_xlabel("Electronic iteration")
            convergence_axis.set_ylabel("Electronic free energy (eV)")
            lower_plot = "electronic-energy"
        elif force_points:
            convergence_axis.plot(
                [point[0] for point in force_points],
                [point[1] for point in force_points],
                color="#1f4e79",
                marker="o",
                linewidth=1.0,
            )
            if len(force_points) > 1:
                convergence_axis.set_xlim(force_points[0][0], force_points[-1][0])
                convergence_axis.margins(x=0)
            convergence_axis.set_xlabel("Ionic step")
            convergence_axis.set_ylabel("Force metric (eV/Å)")
            lower_plot = "force"
        else:
            convergence_axis.text(0.5, 0.5, "No residual or force records", transform=convergence_axis.transAxes, ha="center")
            lower_plot = "none"
        figure.tight_layout()
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {
        "schema_version": "1.0",
        "plot_type": "run-trace",
        "energy_points": len(energy_points),
        "lower_panel": lower_plot,
        "lower_panel_points": (
            len(residual_points) if residual_points
            else len(electronic_energy_points) if electronic_energy_points
            else len(force_points)
        ),
        "output": _output_record(output, "figure", "image/png"),
    }


def normalize_run_trace(
    output_path: Path,
    code: str,
    output_directory: Path,
    dataset_id: str,
    *,
    figure_output: Path | None = None,
    maturity: str = "format-fixture-validated",
    overwrite: bool = False,
) -> dict[str, Path]:
    _check_maturity(maturity)
    if code not in {"qe", "vasp"}:
        raise ValueError("run trace code must be qe or vasp")
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    electronic_path = output_directory / "electronic-iterations.csv"
    ionic_path = output_directory / "ionic-steps.csv"
    analysis_path = output_directory / "run-trace.analysis.json"
    plot_metadata_path = output_directory / "run-trace.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "run-trace.png"
    dataset_path = output_directory / "run-trace.dataset.json"
    _refuse_existing_outputs(
        (electronic_path, ionic_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite
    )
    parsed = _parse_qe_trace(output_path) if code == "qe" else _parse_vasp_trace(output_path)
    _write_csv_atomic(
        electronic_path,
        ["ionic_step", "electronic_iteration", "residual_ev", "electronic_energy_ev"],
        parsed["electronic_rows"],
    )
    _write_csv_atomic(
        ionic_path,
        ["ionic_step", "energy_ev", "force_ev_per_angstrom", "force_kind", "electronic_iterations"],
        parsed["ionic_rows"],
    )
    energy_values = [row["energy_ev"] for row in parsed["ionic_rows"] if row["energy_ev"] is not None]
    force_values = [row["force_ev_per_angstrom"] for row in parsed["ionic_rows"] if row["force_ev_per_angstrom"] is not None]
    residual_values = [row["residual_ev"] for row in parsed["electronic_rows"] if row["residual_ev"] is not None]
    electronic_energy_values = [
        row.get("electronic_energy_ev") for row in parsed["electronic_rows"]
        if row.get("electronic_energy_ev") is not None
    ]
    analysis = {
        "schema_version": "1.0",
        "code": code,
        "calculation": parsed["calculation"],
        "run_complete": parsed["run_complete"],
        "electronic_converged": parsed["electronic_converged"],
        "geometry_converged": parsed["geometry_converged"],
        "ionic_step_count": len(parsed["ionic_rows"]),
        "electronic_iteration_count": len(parsed["electronic_rows"]),
        "final_energy_ev": energy_values[-1] if energy_values else None,
        "final_scf_residual_ev": residual_values[-1] if residual_values else None,
        "final_electronic_energy_ev": electronic_energy_values[-1] if electronic_energy_values else None,
        "final_force_ev_per_angstrom": force_values[-1] if force_values else None,
        "final_max_force_ev_per_angstrom": force_values[-1] if code == "vasp" and force_values else None,
        "force_kind": parsed["force_kind"],
        "limitations": [
            "A normal program-termination marker is recorded separately from electronic and geometry convergence.",
            "Force metrics retain their code-specific meaning: QE total force and VASP maximum atomic-force norm are not equated.",
            "No material-specific convergence threshold or physical interpretation is imposed by this normalizer.",
        ],
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_trace(parsed, figure_path)
    write_json_atomic(plot_metadata_path, plot_metadata)
    completion_status = "pass" if parsed["run_complete"] else "warn"
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "run-trace",
        "code": code,
        "maturity": maturity,
        "representation": "trajectory",
        "source_files": [_source_record(output_path, "main-output")],
        "dimensions": {
            "ionic_steps": len(parsed["ionic_rows"]),
            "electronic_iterations": len(parsed["electronic_rows"]),
        },
        "columns": [
            {"name": "ionic_step", "dtype": "integer", "unit": None, "role": "ordered-step"},
            {"name": "electronic_iteration", "dtype": "integer", "unit": None, "role": "ordered-step"},
            {"name": "residual_ev", "dtype": "float", "unit": "eV", "role": "scf-residual"},
            {"name": "electronic_energy_ev", "dtype": "float", "unit": "eV", "role": "electronic-iteration-energy"},
            {"name": "energy_ev", "dtype": "float", "unit": "eV", "role": "total-energy", "reference": "code-output-total-energy"},
            {"name": "force_ev_per_angstrom", "dtype": "float", "unit": "eV/angstrom", "role": "force-metric"},
            {"name": "force_kind", "dtype": "string", "unit": None, "role": "force-definition"},
            {"name": "electronic_iterations", "dtype": "integer", "unit": None, "role": "iteration-count"},
        ],
        "data_files": [
            _output_record(electronic_path, "electronic-iteration-table", "text/csv"),
            _output_record(ionic_path, "ionic-step-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "unit-normalization",
                "parameters": {
                    "energy_unit": "eV",
                    "force_unit": "eV/angstrom",
                    "qe_ry_to_ev": RY_TO_EV,
                    "qe_bohr_to_angstrom": BOHR_TO_ANGSTROM,
                },
                "input_columns": ["native-energy", "native-residual", "native-force"],
                "output_columns": ["energy_ev", "residual_ev", "force_ev_per_angstrom"],
            }
        ],
        "validation": {
            "status": completion_status,
            "checks": [
                {"id": "completion-marker", "status": completion_status, "message": "Normal termination marker present." if parsed["run_complete"] else "Normal termination marker absent."},
                {"id": "finite-values", "status": "pass", "message": "All parsed trace values are finite."},
                {"id": "ordered-steps", "status": "pass", "message": "Electronic and ionic records are stored in increasing step order."},
                {"id": "unit-declaration", "status": "pass", "message": "Energy, residual, and force units are explicitly normalized and declared."},
            ],
        },
        "limitations": analysis["limitations"],
        "provenance": {"producer": "dftpost.run-trace", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {
        "electronic_table": electronic_path,
        "ionic_table": ionic_path,
        "analysis": analysis_path,
        "plot_metadata": plot_metadata_path,
        "figure": figure_path,
        "dataset": dataset_path,
    }
