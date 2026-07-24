from __future__ import annotations

import csv
import math
from pathlib import Path
import re
from typing import Any

from . import __version__
from .electronic import (
    _check_maturity,
    _interpolate,
    _output_record,
    _plot_bands,
    _plot_dos,
    _plot_fatband,
    _refuse_existing_outputs,
    _sampled_band_analysis,
    _selector_projection_label,
    _source_record,
    _validated_dataset,
    _window_integral,
    _write_csv_atomic,
)
from .registry import resolve_backend_maturity
from .utils import utc_now, write_json_atomic


FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
ORBITALS_L11 = ["s", "py", "pz", "px", "dxy", "dyz", "dz2", "dxz", "dx2-y2"]


def _finite(values: list[float], context: str) -> None:
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{context}: non-finite numeric value")


def _determinant(matrix: list[list[float]]) -> float:
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def _cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def parse_poscar(path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    if len(lines) < 8:
        raise ValueError(f"{path.name}: POSCAR is incomplete")
    scale_fields = lines[1].split()
    if len(scale_fields) != 1:
        raise ValueError(f"{path.name}: only the standard scalar POSCAR scale is supported")
    try:
        scale = float(scale_fields[0])
        lattice = [[float(value) for value in lines[index].split()[:3]] for index in range(2, 5)]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{path.name}: malformed POSCAR scale or lattice") from exc
    if any(len(row) != 3 for row in lattice) or scale == 0.0:
        raise ValueError(f"{path.name}: invalid POSCAR lattice")
    determinant = abs(_determinant(lattice))
    if determinant <= 0.0:
        raise ValueError(f"{path.name}: singular POSCAR lattice")
    factor = scale if scale > 0.0 else (-scale / determinant) ** (1.0 / 3.0)
    lattice = [[factor * value for value in row] for row in lattice]

    species_fields = lines[5].split()
    if not species_fields:
        raise ValueError(f"{path.name}: missing POSCAR species/count line")
    try:
        [int(value) for value in species_fields]
        numeric_species_line = True
    except ValueError:
        numeric_species_line = False
    if numeric_species_line:
        counts = [int(value) for value in species_fields]
        species = [f"species-{index}" for index in range(1, len(counts) + 1)]
        coordinate_line = 6
    else:
        species = species_fields
        try:
            counts = [int(value) for value in lines[6].split()]
        except ValueError as exc:
            raise ValueError(f"{path.name}: malformed POSCAR atom counts") from exc
        coordinate_line = 7
    if len(species) != len(counts) or not counts or any(value <= 0 for value in counts):
        raise ValueError(f"{path.name}: inconsistent POSCAR species/count metadata")
    if lines[coordinate_line].lower().startswith("s"):
        coordinate_line += 1
    if coordinate_line >= len(lines) or not lines[coordinate_line].lower().startswith(("d", "c", "k")):
        raise ValueError(f"{path.name}: missing POSCAR coordinate mode")
    atoms = [label for label, count in zip(species, counts) for _ in range(count)]
    return {"lattice_angstrom": lattice, "species": species, "counts": counts, "atoms": atoms}


def parse_outcar_parameters(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")

    def last_integer(name: str) -> int | None:
        matches = re.findall(rf"\b{name}\s*=\s*(\d+)", text)
        return int(matches[-1]) if matches else None

    fermi_matches = re.findall(rf"E-fermi\s*:\s*({FLOAT})", text, flags=re.IGNORECASE)
    if not fermi_matches:
        raise ValueError(f"{path.name}: no E-fermi record found")
    fermi = float(fermi_matches[-1])
    _finite([fermi], path.name)
    return {
        "energy_reference_ev": fermi,
        "ispin": last_integer("ISPIN"),
        "lorbit": last_integer("LORBIT"),
        "complete": "General timing and accounting" in text,
    }


def parse_kpoints_line_mode(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 6 or not lines[2].strip().lower().startswith("line"):
        raise ValueError(f"{path.name}: expected a VASP line-mode KPOINTS file")
    try:
        points_per_segment = int(lines[1].split()[0])
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{path.name}: malformed line-mode point count") from exc
    if points_per_segment < 2:
        raise ValueError(f"{path.name}: line-mode point count must be at least two")
    coordinate_mode = lines[3].strip().lower()
    if not coordinate_mode.startswith("r"):
        raise ValueError(f"{path.name}: only reciprocal line-mode KPOINTS are supported")
    vertices = []
    for line_number, line in enumerate(lines[4:], start=5):
        stripped = line.strip()
        if not stripped:
            continue
        data, _, comment = stripped.partition("!")
        fields = data.split()
        if len(fields) < 3:
            raise ValueError(f"{path.name}:{line_number}: malformed line-mode vertex")
        try:
            coordinate = [float(value) for value in fields[:3]]
        except ValueError as exc:
            raise ValueError(f"{path.name}:{line_number}: nonnumeric line-mode vertex") from exc
        _finite(coordinate, f"{path.name}:{line_number}")
        label = comment.strip() if comment.strip() else (fields[3] if len(fields) > 3 else "")
        vertices.append({"coordinate": coordinate, "label": label})
    if len(vertices) < 2 or len(vertices) % 2:
        raise ValueError(f"{path.name}: line-mode vertices must form endpoint pairs")
    return {
        "points_per_segment": points_per_segment,
        "coordinate_mode": "reciprocal",
        "vertices": vertices,
    }


def parse_eigenval(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 8:
        raise ValueError(f"{path.name}: EIGENVAL is incomplete")
    try:
        electron_count, nkpoints, nbands = [int(value) for value in lines[5].split()[:3]]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{path.name}: malformed EIGENVAL dimensions") from exc
    if nkpoints <= 0 or nbands <= 0:
        raise ValueError(f"{path.name}: nonpositive EIGENVAL dimensions")
    cursor = 6
    kpoints: list[list[float]] = []
    weights: list[float] = []
    spin_energies: list[list[list[float]]] | None = None
    spin_occupancies: list[list[list[float]]] | None = None
    for kpoint_index in range(nkpoints):
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines):
            raise ValueError(f"{path.name}: missing k-point {kpoint_index + 1}")
        try:
            kpoint_record = [float(value) for value in lines[cursor].split()[:4]]
        except ValueError as exc:
            raise ValueError(f"{path.name}:{cursor + 1}: malformed EIGENVAL k-point") from exc
        if len(kpoint_record) != 4:
            raise ValueError(f"{path.name}:{cursor + 1}: incomplete EIGENVAL k-point")
        _finite(kpoint_record, f"{path.name}:{cursor + 1}")
        kpoints.append(kpoint_record[:3])
        weights.append(kpoint_record[3])
        cursor += 1
        for band_offset in range(nbands):
            if cursor >= len(lines):
                raise ValueError(f"{path.name}: missing band rows at k-point {kpoint_index + 1}")
            fields = lines[cursor].split()
            cursor += 1
            try:
                values = [float(value) for value in fields]
            except ValueError as exc:
                raise ValueError(f"{path.name}:{cursor}: malformed EIGENVAL band row") from exc
            if len(values) not in (3, 5):
                raise ValueError(f"{path.name}:{cursor}: unsupported EIGENVAL band-row width {len(values)}")
            spin_count = 1 if len(values) == 3 else 2
            if spin_energies is None:
                spin_energies = [[[0.0] * nkpoints for _ in range(nbands)] for _ in range(spin_count)]
                spin_occupancies = [[[0.0] * nkpoints for _ in range(nbands)] for _ in range(spin_count)]
            if len(spin_energies) != spin_count:
                raise ValueError(f"{path.name}: inconsistent EIGENVAL spin-column count")
            if int(values[0]) != band_offset + 1:
                raise ValueError(f"{path.name}:{cursor}: unexpected EIGENVAL band index")
            if spin_count == 1:
                energy_values, occupancy_values = [values[1]], [values[2]]
            else:
                energy_values, occupancy_values = values[1:3], values[3:5]
            _finite(energy_values + occupancy_values, f"{path.name}:{cursor}")
            for spin_index in range(spin_count):
                spin_energies[spin_index][band_offset][kpoint_index] = energy_values[spin_index]
                spin_occupancies[spin_index][band_offset][kpoint_index] = occupancy_values[spin_index]
    assert spin_energies is not None and spin_occupancies is not None
    return {
        "electron_count": electron_count,
        "kpoints": kpoints,
        "weights": weights,
        "energies": spin_energies,
        "occupancies": spin_occupancies,
        "nkpoints": nkpoints,
        "nbands": nbands,
        "spin_count": len(spin_energies),
    }


def _reciprocal_basis(lattice: list[list[float]]) -> list[list[float]]:
    volume = _determinant(lattice)
    if abs(volume) <= 1.0e-14:
        raise ValueError("POSCAR lattice is singular")
    factor = 2.0 * math.pi / volume
    return [[factor * value for value in _cross(lattice[1], lattice[2])],
            [factor * value for value in _cross(lattice[2], lattice[0])],
            [factor * value for value in _cross(lattice[0], lattice[1])]]


def _path_metadata(
    kpoint_coordinates: list[list[float]],
    poscar: dict[str, Any],
    kpoints: dict[str, Any],
) -> tuple[list[float], list[dict[str, Any]]]:
    segment_count = len(kpoints["vertices"]) // 2
    expected = segment_count * kpoints["points_per_segment"]
    if len(kpoint_coordinates) != expected:
        raise ValueError(
            f"EIGENVAL/KPOINTS path dimension mismatch: {len(kpoint_coordinates)} != {expected}"
        )
    reciprocal = _reciprocal_basis(poscar["lattice_angstrom"])

    def cartesian(coordinate: list[float]) -> list[float]:
        return [sum(coordinate[index] * reciprocal[index][axis] for index in range(3)) for axis in range(3)]

    distances = [0.0]
    for left, right in zip(kpoint_coordinates, kpoint_coordinates[1:]):
        left_cartesian, right_cartesian = cartesian(left), cartesian(right)
        increment = math.sqrt(sum((a - b) ** 2 for a, b in zip(left_cartesian, right_cartesian)))
        distances.append(distances[-1] + increment)
    labels: list[dict[str, Any]] = []
    count = kpoints["points_per_segment"]
    for segment_index in range(segment_count):
        for local_index, vertex_index in ((0, 2 * segment_index), (count - 1, 2 * segment_index + 1)):
            global_index = segment_index * count + local_index
            label = kpoints["vertices"][vertex_index]["label"]
            record = {"k_index": global_index + 1, "k_distance": distances[global_index], "label": label}
            if not labels or abs(labels[-1]["k_distance"] - record["k_distance"]) > 1.0e-10 or labels[-1]["label"] != label:
                labels.append(record)
    return distances, labels


def normalize_vasp_bands(
    eigenval_path: Path,
    kpoints_path: Path,
    poscar_path: Path,
    outcar_path: Path,
    output_directory: Path,
    dataset_id: str,
    *,
    figure_output: Path | None = None,
    energy_window_ev: tuple[float, float] | None = None,
    maturity: str | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    maturity = resolve_backend_maturity("bands", "vasp", "python.vasp-bands", maturity)
    _check_maturity(maturity)
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "bands.csv"
    analysis_path = output_directory / "bands.analysis.json"
    plot_metadata_path = output_directory / "bands.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "bands.png"
    dataset_path = output_directory / "bands.dataset.json"
    _refuse_existing_outputs((table_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite)

    eigenval = parse_eigenval(eigenval_path)
    poscar = parse_poscar(poscar_path)
    kpoints = parse_kpoints_line_mode(kpoints_path)
    outcar = parse_outcar_parameters(outcar_path)
    distances, labels = _path_metadata(eigenval["kpoints"], poscar, kpoints)
    reference = outcar["energy_reference_ev"]
    spin_labels = ["none"] if eigenval["spin_count"] == 1 else ["up", "down"]
    rows = (
        {
            "k_index": k_index,
            "k_distance": distance,
            "band_index": band_index,
            "spin": spin_labels[spin_index],
            "energy_raw_ev": energy,
            "energy_relative_ev": energy - reference,
            "occupancy": eigenval["occupancies"][spin_index][band_index - 1][k_index - 1],
        }
        for spin_index in range(eigenval["spin_count"])
        for band_index, band in enumerate(eigenval["energies"][spin_index], start=1)
        for k_index, (distance, energy) in enumerate(zip(distances, band), start=1)
    )
    _write_csv_atomic(
        table_path,
        ["k_index", "k_distance", "band_index", "spin", "energy_raw_ev", "energy_relative_ev", "occupancy"],
        rows,
    )
    spin_summaries = []
    for spin_label, bands in zip(spin_labels, eigenval["energies"]):
        summary = _sampled_band_analysis(bands, reference)
        summary["spin"] = spin_label
        summary["limitations"] = [
            "Band-edge and crossing values are discrete-path numerical summaries, not a global-extremum proof.",
            "The path coordinate is a reciprocal-space distance derived from the supplied POSCAR and KPOINTS.",
        ]
        spin_summaries.append(summary)
    analysis = {
        "schema_version": "1.0",
        "energy_reference_ev": reference,
        "reference_convention": "energy_relative_ev = energy_raw_ev - energy_reference_ev",
        "electron_count": eigenval["electron_count"],
        "bands": eigenval["nbands"],
        "kpoints": eigenval["nkpoints"],
        "spin_channels": eigenval["spin_count"],
        "path_coordinate_unit": "1/angstrom",
        "high_symmetry_points": labels,
        "spin_summaries": spin_summaries,
        "limitations": [
            "Band-edge and crossing values are discrete-path numerical summaries, not a global-extremum proof.",
            "Line-mode labels and reciprocal-space distances are read from the supplied KPOINTS and POSCAR evidence.",
        ],
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_bands(
        distances,
        [band for spin in eigenval["energies"] for band in spin],
        reference,
        figure_path,
        energy_window_ev,
        xlabel=r"Path distance ($\mathrm{\AA}^{-1}$)",
        symmetry_points=labels,
    )
    plot_metadata.update({"high_symmetry_points": labels, "spin_channels": spin_labels})
    write_json_atomic(plot_metadata_path, plot_metadata)
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "bands",
        "code": "vasp",
        "maturity": maturity,
        "representation": "table",
        "source_files": [
            _source_record(eigenval_path, "eigenvalues"),
            _source_record(kpoints_path, "k-path"),
            _source_record(poscar_path, "structure"),
            _source_record(outcar_path, "energy-reference"),
        ],
        "dimensions": {
            "bands": eigenval["nbands"],
            "kpoints": eigenval["nkpoints"],
            "spin_channels": eigenval["spin_count"],
            "rows": eigenval["nbands"] * eigenval["nkpoints"] * eigenval["spin_count"],
        },
        "columns": [
            {"name": "k_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "k_distance", "dtype": "float", "unit": "1/angstrom", "role": "reciprocal-path-distance"},
            {"name": "band_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "spin", "dtype": "string", "unit": None, "role": "spin-channel"},
            {"name": "energy_raw_ev", "dtype": "float", "unit": "eV", "role": "eigenvalue", "reference": "absolute-output-value"},
            {"name": "energy_relative_ev", "dtype": "float", "unit": "eV", "role": "eigenvalue", "reference": "explicit-fermi-energy"},
            {"name": "occupancy", "dtype": "float", "unit": None, "role": "band-occupancy"},
        ],
        "data_files": [
            _output_record(table_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "subtract-energy-reference",
                "parameters": {"energy_reference_ev": reference, "source_label": outcar_path.name},
                "input_columns": ["energy_raw_ev"],
                "output_columns": ["energy_relative_ev"],
            },
            {
                "operation": "reciprocal-path-distance",
                "parameters": {"coordinate_mode": "reciprocal", "unit": "1/angstrom"},
                "input_columns": ["fractional-kpoint", "POSCAR-lattice"],
                "output_columns": ["k_distance"],
            },
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "finite-values", "status": "pass", "message": "All eigenvalues, occupancies, and path distances are finite."},
                {"id": "band-kpoint-dimensions", "status": "pass", "message": "EIGENVAL dimensions and all spin/band grids are complete."},
                {"id": "energy-reference", "status": "pass", "message": "The final OUTCAR E-fermi value was parsed explicitly."},
                {"id": "path-mapping", "status": "pass", "message": "EIGENVAL count matches the line-mode KPOINTS segment definition."},
            ],
        },
        "limitations": analysis["limitations"],
        "provenance": {"producer": "dftpost.vasp-bands", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {"table": table_path, "analysis": analysis_path, "plot_metadata": plot_metadata_path, "figure": figure_path, "dataset": dataset_path}


def _orbital_family(label: str) -> str:
    if label == "s":
        return "s"
    if label.startswith("p"):
        return "p"
    if label.startswith("d") or label == "x2-y2":
        return "d"
    if label.startswith("f"):
        return "f"
    return label


def _dos_orbital_layout(value_count: int, spin_count: int) -> tuple[list[str], bool]:
    if value_count % spin_count:
        raise ValueError("DOSCAR projected column count is incompatible with ISPIN")
    orbitals_per_spin = value_count // spin_count
    layouts = {
        1: ["total"],
        3: ["s", "p", "d"],
        4: ["s", "p", "d", "f"],
        9: ORBITALS_L11,
        16: ORBITALS_L11 + [f"f{index}" for index in range(1, 8)],
    }
    if orbitals_per_spin not in layouts:
        raise ValueError(f"unsupported DOSCAR projected orbital width: {orbitals_per_spin}")
    return layouts[orbitals_per_spin], spin_count == 2


def _parse_doscar(path: Path, atoms: list[str], ispin: int) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 7:
        raise ValueError(f"{path.name}: DOSCAR is incomplete")
    try:
        ion_count = int(lines[0].split()[0])
        header = [float(value) for value in lines[5].split()[:5]]
        nedos = int(header[2])
        reference = header[3]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{path.name}: malformed DOSCAR header") from exc
    if ion_count != len(atoms) or nedos <= 1:
        raise ValueError(f"{path.name}: DOSCAR/POSCAR atom count or NEDOS is inconsistent")
    cursor = 6
    grid: list[float] = []
    total_channels: list[dict[str, Any]] = []
    total_values = [[] for _ in range(ispin)]
    for row_index in range(nedos):
        try:
            values = [float(value) for value in lines[cursor + row_index].split()]
        except (ValueError, IndexError) as exc:
            raise ValueError(f"{path.name}: malformed total-DOS row {row_index + 1}") from exc
        expected = 3 if ispin == 1 else 5
        if len(values) != expected:
            raise ValueError(f"{path.name}: total-DOS row width does not match ISPIN={ispin}")
        _finite(values, f"{path.name}: total-DOS row {row_index + 1}")
        grid.append(values[0])
        for spin_index in range(ispin):
            total_values[spin_index].append(values[1 + spin_index])
    cursor += nedos
    if any(right <= left for left, right in zip(grid, grid[1:])):
        raise ValueError(f"{path.name}: DOSCAR energy grid is not strictly increasing")
    spin_labels = [None] if ispin == 1 else ["up", "down"]
    for spin_label, values in zip(spin_labels, total_values):
        total_channels.append({
            "label": "total" if spin_label is None else f"total:{spin_label}",
            "channel_type": "total",
            "spin": spin_label,
            "values": values,
        })

    atom_blocks: list[dict[str, Any]] = []
    for atom_index, species in enumerate(atoms, start=1):
        if cursor >= len(lines):
            raise ValueError(f"{path.name}: missing projected-DOS block for atom {atom_index}")
        try:
            atom_header = [float(value) for value in lines[cursor].split()[:5]]
        except ValueError as exc:
            raise ValueError(f"{path.name}: malformed projected-DOS header for atom {atom_index}") from exc
        if len(atom_header) < 4 or int(atom_header[2]) != nedos:
            raise ValueError(f"{path.name}: projected-DOS NEDOS mismatch for atom {atom_index}")
        cursor += 1
        rows = []
        for row_index in range(nedos):
            if cursor >= len(lines):
                raise ValueError(f"{path.name}: incomplete projected-DOS block for atom {atom_index}")
            try:
                values = [float(value) for value in lines[cursor].split()]
            except ValueError as exc:
                raise ValueError(f"{path.name}:{cursor + 1}: malformed projected-DOS row") from exc
            cursor += 1
            if not values or abs(values[0] - grid[row_index]) > 5.0e-4:
                raise ValueError(f"{path.name}: projected-DOS grid mismatch for atom {atom_index}")
            _finite(values, f"{path.name}: projected-DOS row")
            rows.append(values[1:])
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise ValueError(f"{path.name}: inconsistent projected-DOS row width")
        orbital_labels, spin_paired = _dos_orbital_layout(width, ispin)
        values_by_spin_orbital: dict[tuple[str | None, str], list[float]] = {}
        if spin_paired:
            for orbital_index, orbital in enumerate(orbital_labels):
                for spin_index, spin_label in enumerate(("up", "down")):
                    values_by_spin_orbital[(spin_label, orbital)] = [
                        row[2 * orbital_index + spin_index] for row in rows
                    ]
        else:
            for orbital_index, orbital in enumerate(orbital_labels):
                values_by_spin_orbital[(None, orbital)] = [row[orbital_index] for row in rows]
        atom_blocks.append({
            "atom_index": atom_index,
            "species": species,
            "values": values_by_spin_orbital,
        })
    return {
        "grid": grid,
        "energy_reference_ev": reference,
        "total_channels": total_channels,
        "atom_blocks": atom_blocks,
        "nedos": nedos,
        "ion_count": ion_count,
    }


def _aggregate_vasp_pdos(blocks: list[dict[str, Any]], group_by: str, point_count: int) -> list[dict[str, Any]]:
    if group_by not in {"species", "orbital", "species-orbital", "atom", "atom-orbital"}:
        raise ValueError(f"unsupported projected-DOS grouping: {group_by}")
    groups: dict[tuple[str, str | None], list[float]] = {}
    order: list[tuple[str, str | None]] = []
    for block in blocks:
        for (spin, orbital), values in block["values"].items():
            family = _orbital_family(orbital)
            if group_by == "species":
                label = block["species"]
            elif group_by == "orbital":
                label = family
            elif group_by == "species-orbital":
                label = f"{block['species']}:{family}"
            elif group_by == "atom":
                label = f"atom-{block['atom_index']}({block['species']})"
            else:
                label = f"atom-{block['atom_index']}({block['species']}):{family}"
            key = (label, spin)
            if key not in groups:
                groups[key] = [0.0] * point_count
                order.append(key)
            for index, value in enumerate(values):
                groups[key][index] += value
    channels = []
    for label, spin in order:
        rendered = label if spin is None else f"{label}:{spin}"
        channels.append({"label": rendered, "channel_type": "projected", "spin": spin, "values": groups[(label, spin)]})
    return channels


def normalize_vasp_dos(
    doscar_path: Path,
    poscar_path: Path,
    outcar_path: Path,
    output_directory: Path,
    dataset_id: str,
    *,
    figure_output: Path | None = None,
    group_by: str = "species-orbital",
    integration_window_ev: tuple[float, float] | None = None,
    energy_window_ev: tuple[float, float] | None = None,
    maturity: str | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    maturity = resolve_backend_maturity("dos-pdos", "vasp", "python.vasp-dos", maturity)
    _check_maturity(maturity)
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "dos.csv"
    analysis_path = output_directory / "dos.analysis.json"
    plot_metadata_path = output_directory / "dos.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "dos.png"
    dataset_path = output_directory / "dos.dataset.json"
    _refuse_existing_outputs((table_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite)

    poscar = parse_poscar(poscar_path)
    outcar = parse_outcar_parameters(outcar_path)
    if outcar["ispin"] not in (1, 2):
        raise ValueError(f"{outcar_path.name}: missing or unsupported ISPIN")
    parsed = _parse_doscar(doscar_path, poscar["atoms"], outcar["ispin"])
    reference = parsed["energy_reference_ev"]
    relative = [value - reference for value in parsed["grid"]]
    projected = _aggregate_vasp_pdos(parsed["atom_blocks"], group_by, parsed["nedos"])
    channels = parsed["total_channels"] + projected
    rows = (
        {
            "energy_index": energy_index,
            "energy_raw_ev": raw,
            "energy_relative_ev": shifted,
            "channel_index": channel_index,
            "channel_label": channel["label"],
            "channel_type": channel["channel_type"],
            "spin": channel["spin"] or "none",
            "dos_states_per_ev": value,
        }
        for channel_index, channel in enumerate(channels, start=1)
        for energy_index, (raw, shifted, value) in enumerate(zip(parsed["grid"], relative, channel["values"]), start=1)
    )
    _write_csv_atomic(
        table_path,
        ["energy_index", "energy_raw_ev", "energy_relative_ev", "channel_index", "channel_label", "channel_type", "spin", "dos_states_per_ev"],
        rows,
    )
    channel_analysis = []
    for channel in channels:
        item = {
            "label": channel["label"],
            "channel_type": channel["channel_type"],
            "spin": channel["spin"],
            "value_at_reference": _interpolate(relative, channel["values"], 0.0),
            "window_integral": None,
            "integration_window_ev": list(integration_window_ev) if integration_window_ev else None,
        }
        if integration_window_ev is not None:
            item["window_integral"] = _window_integral(relative, channel["values"], integration_window_ev)
        channel_analysis.append(item)
    analysis = {
        "schema_version": "1.0",
        "energy_reference_ev": reference,
        "outcar_energy_reference_ev": outcar["energy_reference_ev"],
        "reference_convention": "energy_relative_ev = energy_raw_ev - DOSCAR energy reference",
        "energy_points": parsed["nedos"],
        "energy_min_relative_ev": relative[0],
        "energy_max_relative_ev": relative[-1],
        "spin_channels": outcar["ispin"],
        "lorbit": outcar["lorbit"],
        "group_by": group_by,
        "channels": channel_analysis,
        "limitations": [
            "Projected channels are sums of the explicitly present DOSCAR atom/orbital columns.",
            "No projection-completeness or material-specific physical claim is inferred.",
        ],
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_dos(relative, channels, figure_path, energy_window_ev)
    write_json_atomic(plot_metadata_path, plot_metadata)
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "dos-pdos",
        "code": "vasp",
        "maturity": maturity,
        "representation": "table",
        "source_files": [
            _source_record(doscar_path, "dos-data"),
            _source_record(poscar_path, "structure"),
            _source_record(outcar_path, "energy-reference-and-spin"),
        ],
        "dimensions": {"energy_points": parsed["nedos"], "channels": len(channels), "rows": parsed["nedos"] * len(channels)},
        "columns": [
            {"name": "energy_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "energy_raw_ev", "dtype": "float", "unit": "eV", "role": "energy", "reference": "absolute-output-value"},
            {"name": "energy_relative_ev", "dtype": "float", "unit": "eV", "role": "energy", "reference": "explicit-fermi-energy"},
            {"name": "channel_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "channel_label", "dtype": "string", "unit": None, "role": "channel-label"},
            {"name": "channel_type", "dtype": "string", "unit": None, "role": "channel-type"},
            {"name": "spin", "dtype": "string", "unit": None, "role": "spin-channel"},
            {"name": "dos_states_per_ev", "dtype": "float", "unit": "states/eV", "role": "density-of-states"},
        ],
        "data_files": [
            _output_record(table_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "subtract-energy-reference",
                "parameters": {"energy_reference_ev": reference, "source_label": doscar_path.name},
                "input_columns": ["energy_raw_ev"],
                "output_columns": ["energy_relative_ev"],
            },
            {
                "operation": "aggregate-projected-dos",
                "parameters": {"group_by": group_by, "atom_count": parsed["ion_count"]},
                "input_columns": ["DOSCAR-projected-columns"],
                "output_columns": ["dos_states_per_ev"],
            },
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "finite-values", "status": "pass", "message": "All energy and DOS values are finite."},
                {"id": "monotonic-energy-grid", "status": "pass", "message": "The DOSCAR energy grid is strictly increasing."},
                {"id": "grid-alignment", "status": "pass", "message": "Every projected atom block matches total-DOS NEDOS and grid."},
                {"id": "energy-reference", "status": "pass", "message": "The DOSCAR energy reference is explicit and the OUTCAR reference is recorded separately."},
                {"id": "channel-mapping", "status": "pass", "message": "POSCAR atom labels and DOSCAR orbital columns were mapped explicitly."},
            ],
        },
        "limitations": analysis["limitations"],
        "provenance": {"producer": "dftpost.vasp-dos", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {"table": table_path, "analysis": analysis_path, "plot_metadata": plot_metadata_path, "figure": figure_path, "dataset": dataset_path}


def _selected_orbitals(columns: list[str], selector: dict[str, str]) -> list[str]:
    if "orbital" in selector:
        requested = {value.strip() for value in selector["orbital"].split(",") if value.strip()}
        selected = [column for column in columns if column in requested or _orbital_family(column) in requested]
    elif "l" in selector:
        mapping = {"0": "s", "1": "p", "2": "d", "3": "f"}
        if selector["l"] not in mapping:
            raise ValueError("PROCAR selector l must be one of 0, 1, 2, or 3")
        family = mapping[selector["l"]]
        selected = [column for column in columns if _orbital_family(column) == family]
    else:
        selected = [column for column in columns if column != "tot"]
    if not selected:
        raise ValueError("PROCAR selector matched no orbital columns")
    return selected


def _parse_procar_selected(
    path: Path,
    atoms: list[str],
    selector: dict[str, str],
) -> tuple[int, int, int, list[list[float]], list[str]]:
    allowed = {"species", "atom", "orbital", "l", "spin_component"}
    unknown = set(selector).difference(allowed)
    if unknown:
        raise ValueError(f"unsupported PROCAR selector keys: {sorted(unknown)}")
    if not selector:
        raise ValueError("PROCAR fatband requires an explicit selector")
    text = path.read_text(encoding="utf-8", errors="replace")
    header = re.search(r"# of k-points:\s*(\d+)\s+# of bands:\s*(\d+)\s+# of ions:\s*(\d+)", text)
    if not header:
        raise ValueError(f"{path.name}: missing PROCAR dimensions")
    nkpoints, nbands, nions = (int(value) for value in header.groups())
    if nions != len(atoms):
        raise ValueError(f"{path.name}: PROCAR/POSCAR atom count mismatch")
    selected_atoms = list(range(1, nions + 1))
    if "species" in selector:
        requested_species = {value.strip() for value in selector["species"].split(",") if value.strip()}
        selected_atoms = [index for index in selected_atoms if atoms[index - 1] in requested_species]
    if "atom" in selector:
        try:
            requested_atoms = {int(value.strip()) for value in selector["atom"].split(",") if value.strip()}
        except ValueError as exc:
            raise ValueError("PROCAR atom selector must contain one-based integers") from exc
        selected_atoms = [index for index in selected_atoms if index in requested_atoms]
    if not selected_atoms:
        raise ValueError("PROCAR selector matched no atoms")
    selected_spin = int(selector.get("spin_component", "1"))
    if selected_spin <= 0:
        raise ValueError("PROCAR spin_component must be a positive integer")

    weights = [[0.0 for _ in range(nbands)] for _ in range(nkpoints)]
    lines = text.splitlines()
    current_kpoint: int | None = None
    current_band: int | None = None
    current_spin = 1
    matched_rows = 0
    selected_columns_record: list[str] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        spin_match = re.match(r"spin component\s+(\d+)", stripped, flags=re.IGNORECASE)
        if spin_match:
            current_spin = int(spin_match.group(1))
            index += 1
            continue
        kpoint_match = re.match(r"k-point\s+(\d+)\s*:", stripped, flags=re.IGNORECASE)
        if kpoint_match:
            current_kpoint = int(kpoint_match.group(1))
            index += 1
            continue
        band_match = re.match(r"band\s+(\d+)\s+#\s+energy", stripped, flags=re.IGNORECASE)
        if band_match:
            current_band = int(band_match.group(1))
            index += 1
            continue
        if stripped.lower().startswith("ion ") and current_kpoint is not None and current_band is not None:
            columns = stripped.split()[1:]
            selected_columns = _selected_orbitals(columns, selector)
            if not selected_columns_record:
                selected_columns_record = selected_columns
            elif selected_columns_record != selected_columns:
                raise ValueError(f"{path.name}: inconsistent PROCAR orbital columns")
            column_indices = [columns.index(column) for column in selected_columns]
            index += 1
            while index < len(lines):
                row = lines[index].split()
                if not row:
                    index += 1
                    continue
                if row[0].lower() == "tot":
                    index += 1
                    break
                try:
                    atom_index = int(row[0])
                    values = [float(value) for value in row[1:]]
                except ValueError as exc:
                    raise ValueError(f"{path.name}:{index + 1}: malformed PROCAR ion row") from exc
                if len(values) != len(columns):
                    raise ValueError(f"{path.name}:{index + 1}: PROCAR ion row width mismatch")
                if atom_index in selected_atoms and current_spin == selected_spin:
                    weights[current_kpoint - 1][current_band - 1] += sum(values[position] for position in column_indices)
                    matched_rows += 1
                index += 1
            continue
        index += 1
    if matched_rows == 0:
        raise ValueError("PROCAR selector matched no projection rows")
    return nkpoints, nbands, len(selected_atoms), weights, selected_columns_record


def normalize_vasp_fatband(
    eigenval_path: Path,
    kpoints_path: Path,
    poscar_path: Path,
    outcar_path: Path,
    procar_path: Path,
    output_directory: Path,
    dataset_id: str,
    selector: dict[str, str],
    *,
    figure_output: Path | None = None,
    energy_window_ev: tuple[float, float] | None = None,
    marker_scale: float = 8.0,
    render_mode: str = "line-width",
    projection_label: str | None = None,
    bands_label: str = "Bands",
    maturity: str | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    maturity = resolve_backend_maturity("bands", "vasp", "python.vasp-fatband", maturity)
    _check_maturity(maturity)
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "fatband.csv"
    analysis_path = output_directory / "fatband.analysis.json"
    plot_metadata_path = output_directory / "fatband.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "fatband.png"
    dataset_path = output_directory / "fatband.dataset.json"
    _refuse_existing_outputs((table_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite)

    eigenval = parse_eigenval(eigenval_path)
    if eigenval["spin_count"] != 1:
        raise ValueError("spin-polarized VASP fatband requires a spin-resolved EIGENVAL/PROCAR workflow")
    poscar = parse_poscar(poscar_path)
    kpoints = parse_kpoints_line_mode(kpoints_path)
    outcar = parse_outcar_parameters(outcar_path)
    distances, labels = _path_metadata(eigenval["kpoints"], poscar, kpoints)
    nkpoints, nbands, atom_count, weights, orbitals = _parse_procar_selected(procar_path, poscar["atoms"], selector)
    if nkpoints != eigenval["nkpoints"] or nbands != eigenval["nbands"]:
        raise ValueError("EIGENVAL/PROCAR dimension mismatch")
    reference = outcar["energy_reference_ev"]
    bands = eigenval["energies"][0]
    rows = (
        {
            "k_index": k_index,
            "k_distance": distance,
            "band_index": band_index,
            "energy_raw_ev": energy,
            "energy_relative_ev": energy - reference,
            "projection_weight": weights[k_index - 1][band_index - 1],
        }
        for band_index, band in enumerate(bands, start=1)
        for k_index, (distance, energy) in enumerate(zip(distances, band), start=1)
    )
    _write_csv_atomic(
        table_path,
        ["k_index", "k_distance", "band_index", "energy_raw_ev", "energy_relative_ev", "projection_weight"],
        rows,
    )
    flat_weights = [value for row in weights for value in row]
    analysis = {
        "schema_version": "1.0",
        "selector": selector,
        "selected_atom_count": atom_count,
        "selected_orbitals": orbitals,
        "weight_min": min(flat_weights),
        "weight_max": max(flat_weights),
        "weight_sum": sum(flat_weights),
        "energy_reference_ev": reference,
        "high_symmetry_points": labels,
        "limitations": [
            "Projection weights are aggregated only over the explicitly selected PROCAR atoms and orbitals.",
            "Marker area, color, and line width are visualization mappings, not separately normalized observables.",
        ],
    }
    rendered_projection_label = _selector_projection_label(selector, projection_label)
    analysis["projection_label"] = rendered_projection_label
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_fatband(
        distances,
        bands,
        reference,
        weights,
        figure_path,
        energy_window_ev,
        marker_scale,
        render_mode,
        rendered_projection_label,
        bands_label,
        xlabel=r"Path distance ($\mathrm{\AA}^{-1}$)",
        symmetry_points=labels,
    )
    plot_metadata["high_symmetry_points"] = labels
    write_json_atomic(plot_metadata_path, plot_metadata)
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "bands",
        "code": "vasp",
        "maturity": maturity,
        "representation": "table",
        "source_files": [
            _source_record(eigenval_path, "eigenvalues"),
            _source_record(kpoints_path, "k-path"),
            _source_record(poscar_path, "structure"),
            _source_record(outcar_path, "energy-reference"),
            _source_record(procar_path, "projection-weights"),
        ],
        "dimensions": {"bands": nbands, "kpoints": nkpoints, "rows": nbands * nkpoints},
        "columns": [
            {"name": "k_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "k_distance", "dtype": "float", "unit": "1/angstrom", "role": "reciprocal-path-distance"},
            {"name": "band_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "energy_raw_ev", "dtype": "float", "unit": "eV", "role": "eigenvalue", "reference": "absolute-output-value"},
            {"name": "energy_relative_ev", "dtype": "float", "unit": "eV", "role": "eigenvalue", "reference": "explicit-fermi-energy"},
            {"name": "projection_weight", "dtype": "float", "unit": None, "role": "selected-projection-weight"},
        ],
        "data_files": [
            _output_record(table_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "select-and-sum-projections",
                "parameters": {"selector": selector, "selected_atom_count": atom_count, "selected_orbitals": orbitals},
                "input_columns": ["PROCAR-ion-orbitals"],
                "output_columns": ["projection_weight"],
            },
            {
                "operation": "subtract-energy-reference",
                "parameters": {"energy_reference_ev": reference, "source_label": outcar_path.name},
                "input_columns": ["energy_raw_ev"],
                "output_columns": ["energy_relative_ev"],
            },
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "finite-values", "status": "pass", "message": "All eigenvalues and selected projection weights are finite."},
                {"id": "band-kpoint-dimensions", "status": "pass", "message": "EIGENVAL, KPOINTS, and PROCAR dimensions agree."},
                {"id": "energy-reference", "status": "pass", "message": "The final OUTCAR E-fermi value was parsed explicitly."},
                {"id": "path-mapping", "status": "pass", "message": "Line-mode path mapping is explicit and dimensionally complete."},
                {"id": "projection-sums", "status": "pass", "message": "Only explicitly selected atoms and orbital columns were summed."},
            ],
        },
        "limitations": analysis["limitations"],
        "provenance": {"producer": "dftpost.vasp-fatband", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {"table": table_path, "analysis": analysis_path, "plot_metadata": plot_metadata_path, "figure": figure_path, "dataset": dataset_path}
