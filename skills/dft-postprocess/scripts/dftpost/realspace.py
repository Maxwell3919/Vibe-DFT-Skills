from __future__ import annotations

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
    parse_qe_fermi_energy,
)
from .utils import utc_now, write_json_atomic


BOHR_TO_ANGSTROM = 0.529177210903
FIELD_KINDS = {
    "charge-density",
    "electron-localization",
    "electrostatic-potential",
    "other",
}


def _finite_array(values: Any, label: str) -> Any:
    import numpy as np

    array = np.asarray(values, dtype=float)
    if array.ndim != 3 or min(array.shape) < 1:
        raise ValueError(f"{label}: expected a nonempty three-dimensional grid")
    if not np.isfinite(array).all():
        raise ValueError(f"{label}: grid contains non-finite values")
    return array


def _read_cube(path: Path) -> tuple[Any, list[list[float]], dict[str, Any]]:
    import numpy as np

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        comments = [handle.readline().rstrip("\n"), handle.readline().rstrip("\n")]
        atom_line = handle.readline().split()
        if len(atom_line) < 4:
            raise ValueError(f"{path.name}: malformed cube atom/origin row")
        atom_count_raw = int(atom_line[0])
        atom_count = abs(atom_count_raw)
        origin = [float(value) for value in atom_line[1:4]]
        dimensions: list[int] = []
        vectors: list[list[float]] = []
        axis_units: list[str] = []
        for _ in range(3):
            fields = handle.readline().split()
            if len(fields) < 4:
                raise ValueError(f"{path.name}: malformed cube axis row")
            signed_count = int(fields[0])
            if signed_count == 0:
                raise ValueError(f"{path.name}: cube axis count cannot be zero")
            dimensions.append(abs(signed_count))
            vectors.append([float(value) for value in fields[1:4]])
            axis_units.append("angstrom" if signed_count < 0 else "bohr")
        if len(set(axis_units)) != 1:
            raise ValueError(f"{path.name}: mixed cube coordinate-unit signs are unsupported")
        atoms = []
        for atom_index in range(atom_count):
            fields = handle.readline().split()
            if len(fields) < 5:
                raise ValueError(f"{path.name}: malformed cube atom row {atom_index + 1}")
            atoms.append(
                {
                    "atomic_number": int(float(fields[0])),
                    "nuclear_charge": float(fields[1]),
                    "position": [float(value) for value in fields[2:5]],
                }
            )
        if atom_count_raw < 0:
            orbital_fields = handle.readline().split()
            if not orbital_fields:
                raise ValueError(f"{path.name}: missing cube orbital-id row")
        tokens = [token for line in handle for token in line.split()]
    expected = math.prod(dimensions)
    if len(tokens) != expected:
        raise ValueError(f"{path.name}: expected {expected} grid values, found {len(tokens)}")
    try:
        values = np.asarray([float(token) for token in tokens], dtype=float).reshape(dimensions)
    except ValueError as exc:
        raise ValueError(f"{path.name}: nonnumeric cube grid value") from exc
    if not np.isfinite(values).all():
        raise ValueError(f"{path.name}: cube grid contains non-finite values")
    coordinate_unit = axis_units[0]
    factor = BOHR_TO_ANGSTROM if coordinate_unit == "bohr" else 1.0
    step_vectors_angstrom = [[component * factor for component in vector] for vector in vectors]
    metadata = {
        "format": "gaussian-cube",
        "comments": comments,
        "atom_count": atom_count,
        "atoms": atoms,
        "origin_native": origin,
        "coordinate_unit_native": coordinate_unit,
        "step_vectors_angstrom": step_vectors_angstrom,
    }
    return values, step_vectors_angstrom, metadata


def _read_vasp_grid(path: Path) -> tuple[Any, list[list[float]], dict[str, Any]]:
    try:
        from pymatgen.io.vasp.outputs import Chgcar, Elfcar, Locpot
    except ImportError as exc:
        raise RuntimeError("pymatgen is required to parse VASP volumetric grids") from exc

    upper = path.name.upper()
    if upper.startswith("ELFCAR"):
        parsed = Elfcar.from_file(path)
        parser_name = "pymatgen.Elfcar"
    elif upper.startswith("LOCPOT"):
        parsed = Locpot.from_file(path)
        parser_name = "pymatgen.Locpot"
    elif upper.startswith("CHGCAR"):
        parsed = Chgcar.from_file(path)
        parser_name = "pymatgen.Chgcar"
    else:
        raise ValueError("VASP grid filename must begin with CHGCAR, ELFCAR, or LOCPOT")
    values = _finite_array(parsed.data["total"], path.name)
    lattice = parsed.structure.lattice.matrix.tolist()
    step_vectors = [
        [float(component) / int(values.shape[axis]) for component in lattice[axis]]
        for axis in range(3)
    ]
    metadata = {
        "format": "vasp-volumetric-grid",
        "parser": parser_name,
        "atom_count": len(parsed.structure),
        "lattice_vectors_angstrom": lattice,
        "coordinate_unit_native": "angstrom",
        "step_vectors_angstrom": step_vectors,
        "available_channels": sorted(parsed.data),
        "selected_channel": "total",
    }
    return values, step_vectors, metadata


def _axis_positions(shape: tuple[int, int, int], step_vectors: list[list[float]], axis: int) -> list[float]:
    step_length = math.sqrt(sum(component * component for component in step_vectors[axis]))
    if step_length <= 0.0 or not math.isfinite(step_length):
        raise ValueError("grid axis has a nonpositive or non-finite spacing")
    return [index * step_length for index in range(shape[axis])]


def _plot_grid_field(
    positions: list[float],
    profile: list[float],
    plane: Any,
    plane_axes: tuple[int, int],
    plane_lengths: tuple[float, float],
    field_unit: str,
    axis: int,
    slice_index: int,
    output: Path,
    work_function: dict[str, Any] | None = None,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    with plt.style.context(str(style)):
        figure, (profile_axis, slice_axis) = plt.subplots(1, 2, figsize=(10.0, 4.0))
        profile_axis.plot(positions, profile, color="#7f1d1d", linewidth=1.1)
        profile_axis.set_xlabel(f"Axis {axis} position (angstrom)")
        profile_axis.set_ylabel(f"Planar average ({field_unit})")
        profile_axis.set_xlim(positions[0], positions[-1])
        profile_axis.margins(x=0)
        if work_function is not None:
            window = work_function["vacuum_window_angstrom"]
            profile_axis.axvspan(window[0], window[1], color="#d9b44a", alpha=0.22, linewidth=0)
            vacuum_native = work_function["vacuum_mean_ev"] / work_function["potential_to_ev"]
            profile_axis.axhline(vacuum_native, color="#d9b44a", linestyle="--", linewidth=0.9)
            profile_axis.text(
                0.02,
                0.04,
                f"selected window; Phi = {work_function['work_function_ev']:.6f} eV",
                transform=profile_axis.transAxes,
                fontsize="small",
            )
        image = slice_axis.imshow(
            plane.T,
            origin="lower",
            aspect="auto",
            extent=(0.0, plane_lengths[0], 0.0, plane_lengths[1]),
            cmap="viridis",
        )
        slice_axis.set_xlabel(f"Axis {plane_axes[0]} position (angstrom)")
        slice_axis.set_ylabel(f"Axis {plane_axes[1]} position (angstrom)")
        slice_axis.set_title(f"Slice index {slice_index}")
        figure.colorbar(image, ax=slice_axis, label=field_unit)
        figure.tight_layout()
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {
        "schema_version": "1.0",
        "plot_type": "real-space-planar-and-slice",
        "axis": axis,
        "slice_index": slice_index,
        "x_limits": [positions[0], positions[-1]],
        "field_unit": field_unit,
        "work_function_window_shown": work_function is not None,
        "output": _output_record(output, "figure", "image/png"),
    }


def normalize_grid_field(
    grid_path: Path,
    code: str,
    output_directory: Path,
    dataset_id: str,
    *,
    field_kind: str,
    field_unit: str,
    axis: int = 2,
    slice_index: int | None = None,
    potential_to_ev: float | None = None,
    fermi_energy_ev: float | None = None,
    fermi_energy_path: Path | None = None,
    vacuum_window_angstrom: tuple[float, float] | None = None,
    figure_output: Path | None = None,
    maturity: str = "format-fixture-validated",
    overwrite: bool = False,
) -> dict[str, Path]:
    import numpy as np

    _check_maturity(maturity)
    if code not in {"qe", "vasp", "mixed"}:
        raise ValueError("code must be qe, vasp, or mixed")
    if field_kind not in FIELD_KINDS:
        raise ValueError(f"unknown field_kind: {field_kind}")
    if not field_unit.strip():
        raise ValueError("field_unit must be explicit and nonempty")
    if axis not in {0, 1, 2}:
        raise ValueError("axis must be 0, 1, or 2")
    if fermi_energy_ev is not None and fermi_energy_path is not None:
        raise ValueError("supply only one of fermi_energy_ev and fermi_energy_path")
    if fermi_energy_path is not None:
        if code == "qe":
            fermi_energy_ev = parse_qe_fermi_energy(fermi_energy_path)
        elif code == "vasp":
            import re

            matches = re.findall(
                r"E-fermi\s*:\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)",
                fermi_energy_path.read_text(encoding="utf-8", errors="replace"),
                re.IGNORECASE,
            )
            if not matches:
                raise ValueError(f"could not parse an explicit VASP Fermi energy in {fermi_energy_path.name}")
            fermi_energy_ev = float(matches[-1])
        else:
            raise ValueError("fermi_energy_path parsing requires code=qe or code=vasp")
    work_function_arguments = (potential_to_ev, fermi_energy_ev, vacuum_window_angstrom)
    if any(value is not None for value in work_function_arguments) and not all(value is not None for value in work_function_arguments):
        raise ValueError("work-function evaluation requires potential_to_ev, a Fermi-energy value/file, and vacuum_window_angstrom together")
    if all(value is not None for value in work_function_arguments):
        if field_kind != "electrostatic-potential":
            raise ValueError("work-function evaluation requires field_kind=electrostatic-potential")
        if not math.isfinite(float(potential_to_ev)) or float(potential_to_ev) == 0.0:
            raise ValueError("potential_to_ev must be finite and nonzero")
        if not math.isfinite(float(fermi_energy_ev)):
            raise ValueError("fermi_energy_ev must be finite")
        if vacuum_window_angstrom[0] >= vacuum_window_angstrom[1]:
            raise ValueError("vacuum_window_angstrom must be increasing")

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    profile_path = output_directory / "planar-average.csv"
    slice_path = output_directory / "slice.csv"
    analysis_path = output_directory / "real-space.analysis.json"
    plot_metadata_path = output_directory / "real-space.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "real-space.png"
    dataset_path = output_directory / "real-space.dataset.json"
    _refuse_existing_outputs((profile_path, slice_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite)

    if grid_path.suffix.lower() == ".cube":
        values, step_vectors, source_metadata = _read_cube(grid_path)
    elif code == "vasp":
        values, step_vectors, source_metadata = _read_vasp_grid(grid_path)
    else:
        raise ValueError("QE grid input currently requires a .cube file; VASP input requires CHGCAR/ELFCAR/LOCPOT naming")
    values = _finite_array(values, grid_path.name)
    positions = _axis_positions(values.shape, step_vectors, axis)
    other_axes = tuple(index for index in range(3) if index != axis)
    profile = np.mean(values, axis=other_axes).tolist()
    selected_slice = values.shape[axis] // 2 if slice_index is None else slice_index
    if selected_slice < 0 or selected_slice >= values.shape[axis]:
        raise ValueError(f"slice_index must be within 0..{values.shape[axis] - 1}")
    plane = np.take(values, selected_slice, axis=axis)
    plane_axes = tuple(index for index in range(3) if index != axis)
    plane_lengths = tuple(
        math.sqrt(sum(component * component for component in step_vectors[item])) * values.shape[item]
        for item in plane_axes
    )

    _write_csv_atomic(
        profile_path,
        ["grid_index", "position_angstrom", "planar_average"],
        (
            {"grid_index": index, "position_angstrom": position, "planar_average": value}
            for index, (position, value) in enumerate(zip(positions, profile))
        ),
    )
    _write_csv_atomic(
        slice_path,
        ["index_a", "index_b", "position_a_angstrom", "position_b_angstrom", "field_value"],
        (
            {
                "index_a": index_a,
                "index_b": index_b,
                "position_a_angstrom": index_a * plane_lengths[0] / plane.shape[0],
                "position_b_angstrom": index_b * plane_lengths[1] / plane.shape[1],
                "field_value": float(plane[index_a, index_b]),
            }
            for index_a in range(plane.shape[0])
            for index_b in range(plane.shape[1])
        ),
    )

    work_function = None
    checks = [
        {"id": "finite-grid", "status": "pass", "message": "All selected grid-channel values are finite."},
        {"id": "grid-shape", "status": "pass", "message": "A nonempty three-dimensional grid was parsed."},
        {"id": "coordinate-scale", "status": "pass", "message": "Axis positions were derived from explicit grid vectors."},
    ]
    if all(value is not None for value in work_function_arguments):
        selected = [
            value for position, value in zip(positions, profile)
            if vacuum_window_angstrom[0] <= position <= vacuum_window_angstrom[1]
        ]
        if len(selected) < 2:
            raise ValueError("vacuum window selects fewer than two grid planes")
        selected_ev = [value * float(potential_to_ev) for value in selected]
        vacuum_mean_ev = float(np.mean(selected_ev))
        vacuum_std_ev = float(np.std(selected_ev))
        work_function = {
            "potential_to_ev": float(potential_to_ev),
            "fermi_energy_ev": float(fermi_energy_ev),
            "vacuum_window_angstrom": list(vacuum_window_angstrom),
            "selected_plane_count": len(selected),
            "vacuum_mean_ev": vacuum_mean_ev,
            "vacuum_std_ev": vacuum_std_ev,
            "work_function_ev": vacuum_mean_ev - float(fermi_energy_ev),
            "definition": "work_function_ev = mean(planar potential in caller-selected vacuum window, converted to eV) - fermi_energy_ev",
        }
        checks.append({"id": "work-function-inputs", "status": "pass", "message": "Potential conversion, Fermi energy, and vacuum window were supplied explicitly."})
    else:
        checks.append({"id": "work-function-inputs", "status": "not-run", "message": "No work function was computed because the complete explicit input triple was not supplied."})

    limitations = [
        "The selected field kind and field unit are caller-declared and are not inferred from a material or value range.",
        "The planar average is an arithmetic mean over grid planes; no macroscopic smoothing is applied.",
        "The displayed two-dimensional slice is a visualization of one caller-selected grid plane, not an isosurface analysis.",
        "Work-function evaluation never detects a vacuum plateau automatically; it requires an explicit unit conversion, Fermi energy, and vacuum window.",
    ]
    analysis = {
        "schema_version": "1.0",
        "field_kind": field_kind,
        "field_unit": field_unit,
        "grid_shape": list(values.shape),
        "axis": axis,
        "axis_length_sampled_angstrom": positions[-1] if positions else 0.0,
        "slice_index": selected_slice,
        "field_min": float(np.min(values)),
        "field_max": float(np.max(values)),
        "field_mean": float(np.mean(values)),
        "source_metadata": source_metadata,
        "work_function": work_function,
        "limitations": limitations,
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_grid_field(
        positions,
        profile,
        plane,
        plane_axes,
        plane_lengths,
        field_unit,
        axis,
        selected_slice,
        figure_path,
        work_function,
    )
    write_json_atomic(plot_metadata_path, plot_metadata)
    source_role = {
        "charge-density": "charge-density-grid",
        "electron-localization": "electron-localization-grid",
        "electrostatic-potential": "potential-grid",
        "other": "real-space-grid",
    }[field_kind]
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "real-space",
        "code": code,
        "maturity": maturity,
        "representation": "grid",
        "source_files": [_source_record(grid_path, source_role)] + (
            [_source_record(fermi_energy_path, "energy-reference")] if fermi_energy_path is not None else []
        ),
        "dimensions": {
            "grid_x": int(values.shape[0]),
            "grid_y": int(values.shape[1]),
            "grid_z": int(values.shape[2]),
            "profile_points": len(profile),
            "slice_points": int(plane.size),
        },
        "columns": [
            {"name": "position_angstrom", "dtype": "float", "unit": "angstrom", "role": "axis-position"},
            {"name": "planar_average", "dtype": "float", "unit": field_unit, "role": "plane-mean-field"},
            {"name": "field_value", "dtype": "float", "unit": field_unit, "role": "slice-field"},
        ],
        "data_files": [
            _output_record(profile_path, "planar-average-table", "text/csv"),
            _output_record(slice_path, "slice-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "planar-arithmetic-mean",
                "parameters": {"axis": axis},
                "input_columns": ["field_value"],
                "output_columns": ["planar_average"],
            },
            {
                "operation": "grid-plane-slice",
                "parameters": {"axis": axis, "slice_index": selected_slice},
                "input_columns": ["field_value"],
                "output_columns": ["field_value"],
            },
        ],
        "validation": {"status": "pass", "checks": checks},
        "limitations": limitations,
        "provenance": {"producer": "dftpost.grid-field", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {
        "profile": profile_path,
        "slice": slice_path,
        "analysis": analysis_path,
        "plot_metadata": plot_metadata_path,
        "figure": figure_path,
        "dataset": dataset_path,
    }


def _parse_bader_acf(path: Path) -> tuple[list[dict[str, float | int]], dict[str, float]]:
    records: list[dict[str, float | int]] = []
    footer: dict[str, float] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or set(stripped) == {"-"}:
            continue
        fields = stripped.split()
        if fields[0].isdigit() and len(fields) >= 7:
            try:
                values = [float(value) for value in fields[1:7]]
            except ValueError as exc:
                raise ValueError(f"{path.name}:{line_number}: malformed Bader atom row") from exc
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"{path.name}:{line_number}: non-finite Bader atom row")
            records.append(
                {
                    "atom_index": int(fields[0]),
                    "x_angstrom": values[0],
                    "y_angstrom": values[1],
                    "z_angstrom": values[2],
                    "basin_electrons": values[3],
                    "min_distance_angstrom": values[4],
                    "atomic_volume_angstrom3": values[5],
                }
            )
        elif ":" in stripped:
            label, value = stripped.split(":", 1)
            try:
                footer[label.strip().lower().replace(" ", "_")] = float(value.split()[0])
            except (ValueError, IndexError):
                continue
    if not records:
        raise ValueError(f"{path.name}: no Bader atom rows found")
    if [record["atom_index"] for record in records] != list(range(1, len(records) + 1)):
        raise ValueError(f"{path.name}: Bader atom indices must be consecutive from 1")
    return records, footer


def _plot_bader(records: list[dict[str, Any]], has_reference: bool, output: Path) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    panel_count = 2 if has_reference else 1
    with plt.style.context(str(style)):
        figure, axes = plt.subplots(panel_count, 1, figsize=(7.0, 3.4 * panel_count), squeeze=False)
        axis = axes[0][0]
        indices = [record["atom_index"] for record in records]
        axis.bar(indices, [record["basin_electrons"] for record in records], color="#7f1d1d")
        axis.set_ylabel("Basin electrons (e)")
        axis.set_xlim(0.5, len(records) + 0.5)
        if has_reference:
            delta_axis = axes[1][0]
            delta_axis.bar(indices, [record["reference_minus_basin_electrons"] for record in records], color="#2f6f9f")
            delta_axis.axhline(0.0, color="black", linestyle="--", linewidth=0.8)
            delta_axis.set_ylabel("Reference - basin (e)")
            delta_axis.set_xlim(0.5, len(records) + 0.5)
            delta_axis.set_xlabel("Atom index")
        else:
            axis.set_xlabel("Atom index")
        figure.tight_layout()
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {
        "schema_version": "1.0",
        "plot_type": "bader-basin-electrons",
        "reference_difference_shown": has_reference,
        "x_limits": [0.5, len(records) + 0.5],
        "output": _output_record(output, "figure", "image/png"),
    }


def normalize_bader_acf(
    acf_path: Path,
    code: str,
    output_directory: Path,
    dataset_id: str,
    *,
    reference_electrons: list[float] | None = None,
    electron_closure_tolerance: float = 1.0e-3,
    figure_output: Path | None = None,
    maturity: str = "format-fixture-validated",
    overwrite: bool = False,
) -> dict[str, Path]:
    _check_maturity(maturity)
    if code not in {"qe", "vasp", "mixed"}:
        raise ValueError("code must be qe, vasp, or mixed")
    if electron_closure_tolerance < 0.0:
        raise ValueError("electron_closure_tolerance must be nonnegative")
    records, footer = _parse_bader_acf(acf_path)
    if reference_electrons is not None:
        if len(reference_electrons) != len(records):
            raise ValueError("reference_electrons count must match Bader atom count")
        if not all(math.isfinite(value) for value in reference_electrons):
            raise ValueError("reference_electrons contains non-finite values")
        for record, reference in zip(records, reference_electrons):
            record["reference_electrons"] = reference
            record["reference_minus_basin_electrons"] = reference - float(record["basin_electrons"])

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "bader.csv"
    analysis_path = output_directory / "bader.analysis.json"
    plot_metadata_path = output_directory / "bader.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "bader.png"
    dataset_path = output_directory / "bader.dataset.json"
    _refuse_existing_outputs((table_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite)
    fields = [
        "atom_index", "x_angstrom", "y_angstrom", "z_angstrom", "basin_electrons",
        "min_distance_angstrom", "atomic_volume_angstrom3",
    ]
    if reference_electrons is not None:
        fields.extend(["reference_electrons", "reference_minus_basin_electrons"])
    _write_csv_atomic(table_path, fields, records)

    basin_sum = sum(float(record["basin_electrons"]) for record in records)
    reported_total = footer.get("number_of_electrons")
    closure_difference = None if reported_total is None else basin_sum + footer.get("vacuum_charge", 0.0) - reported_total
    closure_status = "not-run" if closure_difference is None else ("pass" if abs(closure_difference) <= electron_closure_tolerance else "warn")
    limitations = [
        "ACF.dat CHARGE is reported as basin electron population; it is not relabeled as an oxidation state or ionic charge.",
        "Reference-minus-basin values are emitted only when the caller supplies one explicit reference-electron value per atom.",
        "No chemical grouping, oxidation-state assignment, or material-specific interpretation is performed.",
    ]
    analysis = {
        "schema_version": "1.0",
        "atom_count": len(records),
        "basin_electron_sum": basin_sum,
        "footer": footer,
        "electron_closure_tolerance": electron_closure_tolerance,
        "electron_closure_difference": closure_difference,
        "electron_closure_status": closure_status,
        "reference_electrons_supplied": reference_electrons is not None,
        "reference_minus_basin_sum": None if reference_electrons is None else sum(float(record["reference_minus_basin_electrons"]) for record in records),
        "limitations": limitations,
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_bader(records, reference_electrons is not None, figure_path)
    write_json_atomic(plot_metadata_path, plot_metadata)
    checks = [
        {"id": "atom-index", "status": "pass", "message": "Atom indices are consecutive from one."},
        {"id": "finite-table", "status": "pass", "message": "All parsed atom-table values are finite."},
        {
            "id": "electron-closure",
            "status": closure_status,
            "message": "Footer electron closure was not available." if closure_difference is None else f"Basin plus vacuum minus reported electrons = {closure_difference:.8g} e.",
        },
    ]
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "real-space",
        "code": code,
        "maturity": maturity,
        "representation": "table",
        "source_files": [_source_record(acf_path, "bader-acf")],
        "dimensions": {"atoms": len(records), "rows": len(records)},
        "columns": [
            {"name": "atom_index", "dtype": "integer", "unit": None, "role": "atom-index"},
            {"name": "basin_electrons", "dtype": "float", "unit": "electron", "role": "bader-basin-population"},
            {"name": "reference_minus_basin_electrons", "dtype": "float", "unit": "electron", "role": "caller-reference-minus-basin"},
        ] if reference_electrons is not None else [
            {"name": "atom_index", "dtype": "integer", "unit": None, "role": "atom-index"},
            {"name": "basin_electrons", "dtype": "float", "unit": "electron", "role": "bader-basin-population"},
        ],
        "data_files": [
            _output_record(table_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [] if reference_electrons is None else [
            {
                "operation": "caller-reference-minus-basin",
                "parameters": {"reference_source": "explicit-cli-values"},
                "input_columns": ["reference_electrons", "basin_electrons"],
                "output_columns": ["reference_minus_basin_electrons"],
            }
        ],
        "validation": {"status": "warn" if closure_status == "warn" else "pass", "checks": checks},
        "limitations": limitations,
        "provenance": {"producer": "dftpost.bader-acf", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {"table": table_path, "analysis": analysis_path, "plot_metadata": plot_metadata_path, "figure": figure_path, "dataset": dataset_path}
