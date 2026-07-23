from __future__ import annotations

import csv
import math
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable

from . import __version__
from .manifests import validation_errors
from .utils import sha256_file, utc_now, write_json_atomic
from strict_json import StrictJSONError, load_object


FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
MATURITY_LEVELS = {
    "design-only",
    "synthetic-validated",
    "format-fixture-validated",
    "real-artifact-validated",
    "tool-integration-validated",
}
PDOS_NAME = re.compile(
    r"pdos_atm#(?P<atom>\d+)\((?P<species>[^)]+)\)_wfc#(?P<wfc>\d+)\((?P<orbital>[^)]+)\)$"
)


def _check_maturity(value: str) -> None:
    if value not in MATURITY_LEVELS:
        raise ValueError(f"unknown maturity: {value}")


def _source_record(path: Path, role: str) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"source file is missing: {path}")
    if path.name == "POTCAR":
        raise ValueError("POTCAR contents must not be used as postprocessing evidence")
    return {
        "role": role,
        "label": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "hash_status": "present",
    }


def _output_record(path: Path, role: str, format_name: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": path.name,
        "format": format_name,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def _write_csv_atomic(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", newline="", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
    temporary.replace(path)


def _save_figure_atomic(figure: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb",
        dir=path.parent,
        prefix=f".{path.stem}.",
        suffix=path.suffix,
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
    try:
        figure.savefig(temporary)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError(f"figure renderer produced an empty file: {path}")
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _refuse_existing_outputs(paths: Iterable[Path], overwrite: bool) -> None:
    if overwrite:
        return
    for path in paths:
        if path.exists():
            raise ValueError(f"refusing to overwrite output: {path}")


def _validated_dataset(dataset: dict[str, Any], output: Path) -> None:
    errors = validation_errors("dataset", dataset)
    if errors:
        raise ValueError("normalized dataset is invalid: " + "; ".join(errors))
    write_json_atomic(output, dataset)


def parse_qe_fermi_energy(path: Path) -> float:
    text = path.read_text(encoding="utf-8", errors="replace")
    patterns = (
        rf"the\s+Fermi\s+energy\s+is\s+({FLOAT})\s*eV",
        rf"EFermi\s*=\s*({FLOAT})\s*eV",
    )
    values: list[float] = []
    for pattern in patterns:
        values.extend(float(value) for value in re.findall(pattern, text, re.IGNORECASE))
    if not values:
        raise ValueError(f"could not parse an explicit Fermi energy in {path.name}")
    if not math.isfinite(values[-1]):
        raise ValueError(f"non-finite Fermi energy in {path.name}")
    return values[-1]


def parse_qe_bands_gnu(path: Path) -> tuple[list[float], list[list[float]]]:
    blocks: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append(current)
                current = []
            continue
        fields = stripped.split()
        if len(fields) != 2:
            raise ValueError(f"{path.name}:{line_number}: expected two numeric columns")
        try:
            point = (float(fields[0]), float(fields[1]))
        except ValueError as exc:
            raise ValueError(f"{path.name}:{line_number}: non-numeric bands data") from exc
        if not all(math.isfinite(value) for value in point):
            raise ValueError(f"{path.name}:{line_number}: non-finite bands data")
        current.append(point)
    if current:
        blocks.append(current)
    if not blocks:
        raise ValueError(f"{path.name}: no band blocks found")
    kpoints = [item[0] for item in blocks[0]]
    if len(kpoints) < 2:
        raise ValueError(f"{path.name}: at least two k-points are required")
    tolerance = max(1.0, max(abs(value) for value in kpoints)) * 1.0e-8
    for band_index, block in enumerate(blocks, start=1):
        if len(block) != len(kpoints):
            raise ValueError(f"{path.name}: band {band_index} has an inconsistent k-point count")
        if any(abs(item[0] - expected) > tolerance for item, expected in zip(block, kpoints)):
            raise ValueError(f"{path.name}: band {band_index} has an inconsistent k-path")
    if any(right < left - tolerance for left, right in zip(kpoints, kpoints[1:])):
        raise ValueError(f"{path.name}: k-path coordinate is not monotonic")
    return kpoints, [[item[1] for item in block] for block in blocks]


def _validated_symmetry_points(
    symmetry_points: list[dict[str, Any]] | None,
    sampled_kpoints: list[float],
) -> list[dict[str, Any]]:
    if symmetry_points is None:
        return []
    if not isinstance(symmetry_points, list):
        raise ValueError("high-symmetry points must be a list")
    if not sampled_kpoints:
        raise ValueError("cannot validate high-symmetry points without sampled k-points")
    tolerance = max(1.0, max(abs(value) for value in sampled_kpoints)) * 1.0e-8
    lower = min(sampled_kpoints)
    upper = max(sampled_kpoints)
    normalized: list[dict[str, Any]] = []
    previous_distance: float | None = None
    for index, point in enumerate(symmetry_points, start=1):
        if not isinstance(point, dict) or set(point) != {"label", "k_distance"}:
            raise ValueError(
                f"high-symmetry point {index} must contain exactly label and k_distance"
            )
        label = point["label"]
        if not isinstance(label, str) or not label.strip() or any(
            character in label for character in "\r\n\t"
        ):
            raise ValueError(f"high-symmetry point {index} has an invalid label")
        try:
            distance = float(point["k_distance"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"high-symmetry point {index} has a non-numeric k_distance"
            ) from exc
        if not math.isfinite(distance):
            raise ValueError(f"high-symmetry point {index} has a non-finite k_distance")
        if distance < lower - tolerance or distance > upper + tolerance:
            raise ValueError(
                f"high-symmetry point {label.strip()!r} is outside the band path range"
            )
        closest = min(sampled_kpoints, key=lambda value: abs(value - distance))
        if abs(closest - distance) > tolerance:
            raise ValueError(
                f"high-symmetry point {label.strip()!r} does not match a sampled k-point"
            )
        if previous_distance is not None and closest <= previous_distance + tolerance:
            raise ValueError("high-symmetry point distances must be strictly increasing")
        normalized.append({"label": label.strip(), "k_distance": closest})
        previous_distance = closest
    return normalized


def _symmetry_points_from_plot_metadata(
    metadata_path: Path,
    sampled_kpoints: list[float],
) -> list[dict[str, Any]]:
    try:
        payload = load_object(
            metadata_path,
            metadata_path.name,
            max_bytes=4 * 1024 * 1024,
            max_nodes=100_000,
            max_depth=64,
        )
    except StrictJSONError as exc:
        raise ValueError(f"could not read bands plot metadata: {metadata_path.name}") from exc
    points = payload.get("high_symmetry_points")
    if points is None:
        raise ValueError(
            f"{metadata_path.name}: bands plot metadata has no high_symmetry_points"
        )
    return _validated_symmetry_points(points, sampled_kpoints)


def _sampled_band_analysis(bands: list[list[float]], reference: float) -> dict[str, Any]:
    relative = [[energy - reference for energy in band] for band in bands]
    occupied = [energy for band in relative for energy in band if energy <= 0.0]
    unoccupied = [energy for band in relative for energy in band if energy > 0.0]
    crossings = [
        index
        for index, band in enumerate(relative, start=1)
        if min(band) <= 0.0 <= max(band)
    ]
    vbm = max(occupied) if occupied else None
    cbm = min(unoccupied) if unoccupied else None
    sampled_gap = None
    if crossings:
        sampled_gap = 0.0
    elif vbm is not None and cbm is not None:
        sampled_gap = cbm - vbm
    return {
        "energy_reference_ev": reference,
        "reference_convention": "energy_relative_ev = energy_raw_ev - energy_reference_ev",
        "sampled_vbm_ev": vbm,
        "sampled_cbm_ev": cbm,
        "sampled_reference_gap_ev": sampled_gap,
        "fermi_crossing_band_indices": crossings,
        "energy_min_relative_ev": min(energy for band in relative for energy in band),
        "energy_max_relative_ev": max(energy for band in relative for energy in band),
        "limitations": [
            "Band-edge and crossing values are discrete-path numerical summaries, not a proof of a global Brillouin-zone extremum.",
            "The native QE path coordinate is retained without assigning a physical distance unit.",
        ],
    }


def _plot_bands(
    kpoints: list[float],
    bands: list[list[float]],
    reference: float,
    output: Path,
    energy_window_ev: tuple[float, float] | None,
    xlabel: str = "Path coordinate (native QE units)",
    symmetry_points: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    output.parent.mkdir(parents=True, exist_ok=True)
    with plt.style.context(str(style)):
        figure, axis = plt.subplots()
        for band in bands:
            axis.plot(kpoints, [value - reference for value in band], color="#7f1d1d", linewidth=0.9)
        axis.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
        axis.set_xlabel(xlabel)
        axis.set_ylabel(r"Energy - $E_\mathrm{ref}$ (eV)")
        if symmetry_points:
            for point in symmetry_points:
                axis.axvline(point["k_distance"], color="#b8b8b8", linewidth=0.55, zorder=0)
            axis.set_xticks(
                [point["k_distance"] for point in symmetry_points],
                [point["label"] for point in symmetry_points],
            )
        axis.set_xlim(kpoints[0], kpoints[-1])
        axis.margins(x=0)
        if energy_window_ev is not None:
            if energy_window_ev[0] >= energy_window_ev[1]:
                raise ValueError("energy window must be increasing")
            axis.set_ylim(*energy_window_ev)
        _save_figure_atomic(figure, output)
        plt.close(figure)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"band plot was not created: {output}")
    return {
        "schema_version": "1.0",
        "plot_type": "bands",
        "band_color": "#7f1d1d",
        "x_limits": [kpoints[0], kpoints[-1]],
        "energy_window_ev": list(energy_window_ev) if energy_window_ev is not None else None,
        "high_symmetry_points": symmetry_points or [],
        "output": _output_record(output, "figure", "image/png"),
    }


def normalize_qe_bands(
    bands_path: Path,
    energy_reference_path: Path,
    output_directory: Path,
    dataset_id: str,
    *,
    figure_output: Path | None = None,
    energy_window_ev: tuple[float, float] | None = None,
    symmetry_points: list[dict[str, Any]] | None = None,
    maturity: str = "format-fixture-validated",
    overwrite: bool = False,
) -> dict[str, Path]:
    _check_maturity(maturity)
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "bands.csv"
    analysis_path = output_directory / "bands.analysis.json"
    plot_metadata_path = output_directory / "bands.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "bands.png"
    dataset_path = output_directory / "bands.dataset.json"
    _refuse_existing_outputs(
        (table_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite
    )

    kpoints, bands = parse_qe_bands_gnu(bands_path)
    validated_symmetry_points = _validated_symmetry_points(symmetry_points, kpoints)
    reference = parse_qe_fermi_energy(energy_reference_path)
    rows = (
        {
            "k_index": k_index,
            "k_distance": kpoint,
            "band_index": band_index,
            "energy_raw_ev": energy,
            "energy_relative_ev": energy - reference,
        }
        for band_index, band in enumerate(bands, start=1)
        for k_index, (kpoint, energy) in enumerate(zip(kpoints, band), start=1)
    )
    _write_csv_atomic(
        table_path,
        ["k_index", "k_distance", "band_index", "energy_raw_ev", "energy_relative_ev"],
        rows,
    )
    analysis = _sampled_band_analysis(bands, reference)
    analysis.update({
        "schema_version": "1.0",
        "bands": len(bands),
        "kpoints": len(kpoints),
        "high_symmetry_points": validated_symmetry_points,
        "path_label_source": "caller-supplied" if validated_symmetry_points else "not-supplied",
    })
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_bands(
        kpoints,
        bands,
        reference,
        figure_path,
        energy_window_ev,
        symmetry_points=validated_symmetry_points,
    )
    write_json_atomic(plot_metadata_path, plot_metadata)

    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "bands",
        "code": "qe",
        "maturity": maturity,
        "representation": "table",
        "source_files": [
            _source_record(bands_path, "eigenvalues"),
            _source_record(energy_reference_path, "energy-reference"),
        ],
        "dimensions": {"bands": len(bands), "kpoints": len(kpoints), "rows": len(bands) * len(kpoints)},
        "columns": [
            {"name": "k_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "k_distance", "dtype": "float", "unit": None, "role": "native-path-coordinate"},
            {"name": "band_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "energy_raw_ev", "dtype": "float", "unit": "eV", "role": "eigenvalue", "reference": "absolute-output-value"},
            {"name": "energy_relative_ev", "dtype": "float", "unit": "eV", "role": "eigenvalue", "reference": "explicit-fermi-energy"},
        ],
        "data_files": [
            _output_record(table_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "subtract-energy-reference",
                "parameters": {"energy_reference_ev": reference, "source_label": energy_reference_path.name},
                "input_columns": ["energy_raw_ev"],
                "output_columns": ["energy_relative_ev"],
            },
            *([{
                "operation": "annotate-high-symmetry-points",
                "parameters": {
                    "source": "caller-supplied",
                    "high_symmetry_points": validated_symmetry_points,
                },
                "input_columns": ["k_distance"],
                "output_columns": ["k_distance"],
            }] if validated_symmetry_points else []),
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "finite-values", "status": "pass", "message": "All path and energy values are finite."},
                {"id": "band-kpoint-dimensions", "status": "pass", "message": "Every band uses the same k-point grid."},
                {"id": "energy-reference", "status": "pass", "message": "An explicit Fermi energy was parsed from a separate evidence file."},
                {"id": "path-mapping", "status": "pass", "message": "The native path coordinate is monotonic and preserved."},
            ],
        },
        "limitations": analysis["limitations"],
        "provenance": {
            "producer": "dftpost.qe-bands",
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


def _read_numeric_table(path: Path) -> tuple[list[str], list[list[float]]]:
    comments: list[str] = []
    rows: list[list[float]] = []
    width: int | None = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            comments.append(stripped)
            continue
        try:
            row = [float(value) for value in stripped.split()]
        except ValueError as exc:
            raise ValueError(f"{path.name}:{line_number}: non-numeric table row") from exc
        if not row or not all(math.isfinite(value) for value in row):
            raise ValueError(f"{path.name}:{line_number}: empty or non-finite table row")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError(f"{path.name}:{line_number}: inconsistent column count")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path.name}: no numeric rows found")
    return comments, rows


def _strict_energy_grid(rows: list[list[float]], label: str) -> list[float]:
    grid = [row[0] for row in rows]
    if len(grid) < 2:
        raise ValueError(f"{label}: at least two energy points are required")
    if any(right <= left for left, right in zip(grid, grid[1:])):
        raise ValueError(f"{label}: energy grid must be strictly increasing")
    return grid


def _interpolate(x: list[float], y: list[float], point: float) -> float | None:
    if point < x[0] or point > x[-1]:
        return None
    for index, value in enumerate(x):
        if value == point:
            return y[index]
        if value > point:
            left = index - 1
            fraction = (point - x[left]) / (value - x[left])
            return y[left] + fraction * (y[index] - y[left])
    return y[-1]


def _window_integral(x: list[float], y: list[float], window: tuple[float, float]) -> float:
    lower, upper = window
    if lower >= upper:
        raise ValueError("integration window must be increasing")
    if lower < x[0] or upper > x[-1]:
        raise ValueError("integration window lies outside the energy grid")
    points = [lower, *[value for value in x if lower < value < upper], upper]
    values = [_interpolate(x, y, value) for value in points]
    if any(value is None for value in values):
        raise AssertionError("window interpolation unexpectedly failed")
    return sum(
        (right_x - left_x) * (float(left_y) + float(right_y)) * 0.5
        for left_x, right_x, left_y, right_y in zip(points, points[1:], values, values[1:])
    )


def _pdos_metadata(path: Path) -> dict[str, Any]:
    match = PDOS_NAME.search(path.name)
    if not match:
        raise ValueError(f"projected DOS filename does not follow the standard QE pattern: {path.name}")
    return {
        "atom_index": int(match.group("atom")),
        "species": match.group("species"),
        "wfc_index": int(match.group("wfc")),
        "orbital": match.group("orbital"),
    }


def _pdos_group(metadata: dict[str, Any], group_by: str) -> str:
    mappings = {
        "species": str(metadata["species"]),
        "orbital": str(metadata["orbital"]),
        "species-orbital": f"{metadata['species']}:{metadata['orbital']}",
        "atom": f"atom-{metadata['atom_index']}:{metadata['species']}",
        "atom-orbital": f"atom-{metadata['atom_index']}:{metadata['species']}:{metadata['orbital']}",
    }
    try:
        return mappings[group_by]
    except KeyError as exc:
        raise ValueError(f"unsupported projected-DOS grouping: {group_by}") from exc


def _parse_total_dos(
    path: Path, energy_reference_path: Path | None
) -> tuple[list[float], list[dict[str, Any]], float]:
    comments, rows = _read_numeric_table(path)
    grid = _strict_energy_grid(rows, path.name)
    reference = parse_qe_fermi_energy(energy_reference_path or path)
    width = len(rows[0])
    header = " ".join(comments).lower()
    if width == 3:
        channels = [{"label": "total", "channel_type": "total", "spin": None, "values": [row[1] for row in rows]}]
        if "pdos" in header and "int dos" not in header:
            channels.append(
                {
                    "label": "projected-total",
                    "channel_type": "projected-total",
                    "spin": None,
                    "values": [row[2] for row in rows],
                }
            )
    elif width == 4:
        channels = [
            {"label": "total-up", "channel_type": "total", "spin": "up", "values": [row[1] for row in rows]},
            {"label": "total-down", "channel_type": "total", "spin": "down", "values": [row[2] for row in rows]},
        ]
    else:
        raise ValueError(f"{path.name}: expected a 3-column non-spin or 4-column spin DOS table")
    if "dos" not in header:
        raise ValueError(f"{path.name}: DOS header was not recognized")
    return grid, channels, reference


def _aggregate_projected_dos(paths: list[Path], grid: list[float], group_by: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str | None], list[float]] = {}
    tolerance = max(1.0, max(abs(value) for value in grid)) * 1.0e-8
    for path in paths:
        metadata = _pdos_metadata(path)
        comments, rows = _read_numeric_table(path)
        candidate = _strict_energy_grid(rows, path.name)
        if len(candidate) != len(grid) or any(abs(left - right) > tolerance for left, right in zip(candidate, grid)):
            raise ValueError(
                f"{path.name}: projected DOS grid is not aligned with the total DOS grid; "
                "for QE projwfc outputs, use the matching prefix.pdos_tot as --total and keep a differently sampled dos.x table separate"
            )
        header = " ".join(comments).lower()
        width = len(rows[0])
        label = _pdos_group(metadata, group_by)
        if "ldos" not in header:
            raise ValueError(f"{path.name}: ldos columns were not recognized")
        if "up" in header and "down" in header:
            if width < 3:
                raise ValueError(f"{path.name}: spin-resolved ldos requires at least three columns")
            candidates = (("up", [row[1] for row in rows]), ("down", [row[2] for row in rows]))
        else:
            if width < 2:
                raise ValueError(f"{path.name}: ldos requires at least two columns")
            candidates = ((None, [row[1] for row in rows]),)
        for spin, values in candidates:
            key = (label, spin)
            accumulated = groups.setdefault(key, [0.0] * len(grid))
            for index, value in enumerate(values):
                accumulated[index] += value
    return [
        {"label": label, "channel_type": "projected", "spin": spin, "values": values}
        for (label, spin), values in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1] or ""))
    ]


def _plot_dos(
    grid_relative: list[float],
    channels: list[dict[str, Any]],
    output: Path,
    energy_window_ev: tuple[float, float] | None = None,
) -> dict[str, Any]:
    if energy_window_ev is not None and energy_window_ev[0] >= energy_window_ev[1]:
        raise ValueError("energy window must be increasing")
    x_limits = list(energy_window_ev) if energy_window_ev is not None else [grid_relative[0], grid_relative[-1]]
    visible_indices = [
        index for index, energy in enumerate(grid_relative)
        if x_limits[0] <= energy <= x_limits[1]
    ]
    if not visible_indices:
        raise ValueError("DOS energy window contains no data points")
    visible_values = [channel["values"][index] for channel in channels for index in visible_indices]
    visible_min, visible_max = min(visible_values), max(visible_values)
    if visible_min == visible_max:
        raise ValueError("DOS energy window has a zero-width value range")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    output.parent.mkdir(parents=True, exist_ok=True)
    with plt.style.context(str(style)):
        figure, axis = plt.subplots()
        for channel in channels:
            linewidth = 1.4 if channel["channel_type"] == "total" else 0.9
            axis.plot(grid_relative, channel["values"], label=channel["label"], linewidth=linewidth)
        axis.axvline(0.0, color="black", linewidth=0.8, linestyle="--")
        axis.set_xlabel(r"Energy - $E_\mathrm{ref}$ (eV)")
        axis.set_ylabel("Density of states (states/eV)")
        axis.set_xlim(*x_limits)
        axis.margins(x=0)
        if visible_min >= 0.0:
            axis.set_ylim(0.0, visible_max * 1.05)
        else:
            padding = 0.05 * (visible_max - visible_min)
            axis.set_ylim(visible_min - padding, visible_max + padding)
        axis.legend(fontsize="small", ncols=2 if len(channels) > 6 else 1)
        _save_figure_atomic(figure, output)
        plt.close(figure)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"DOS plot was not created: {output}")
    return {
        "schema_version": "1.0",
        "plot_type": "dos-pdos",
        "x_limits": x_limits,
        "visible_value_range": [visible_min, visible_max],
        "channel_labels": [channel["label"] for channel in channels],
        "output": _output_record(output, "figure", "image/png"),
    }


def normalize_qe_dos(
    total_dos_path: Path,
    projected_dos_paths: list[Path],
    output_directory: Path,
    dataset_id: str,
    *,
    energy_reference_path: Path | None = None,
    figure_output: Path | None = None,
    group_by: str = "species-orbital",
    integration_window_ev: tuple[float, float] | None = None,
    energy_window_ev: tuple[float, float] | None = None,
    maturity: str = "format-fixture-validated",
    overwrite: bool = False,
) -> dict[str, Path]:
    _check_maturity(maturity)
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "dos.csv"
    analysis_path = output_directory / "dos.analysis.json"
    plot_metadata_path = output_directory / "dos.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "dos.png"
    dataset_path = output_directory / "dos.dataset.json"
    _refuse_existing_outputs(
        (table_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite
    )

    grid, total_channels, reference = _parse_total_dos(total_dos_path, energy_reference_path)
    projected_channels = _aggregate_projected_dos(projected_dos_paths, grid, group_by)
    channels = total_channels + projected_channels
    relative = [value - reference for value in grid]
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
        for energy_index, (raw, shifted, value) in enumerate(zip(grid, relative, channel["values"]), start=1)
    )
    _write_csv_atomic(
        table_path,
        [
            "energy_index", "energy_raw_ev", "energy_relative_ev", "channel_index",
            "channel_label", "channel_type", "spin", "dos_states_per_ev",
        ],
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
        "reference_convention": "energy_relative_ev = energy_raw_ev - energy_reference_ev",
        "energy_points": len(grid),
        "energy_min_relative_ev": relative[0],
        "energy_max_relative_ev": relative[-1],
        "group_by": group_by,
        "channels": channel_analysis,
        "limitations": [
            "Projected channels are sums of the ldos column from explicitly supplied standard QE projwfc files.",
            "No physical interpretation or completeness claim is inferred from a selected set of projection files.",
        ],
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_dos(relative, channels, figure_path, energy_window_ev)
    write_json_atomic(plot_metadata_path, plot_metadata)
    source_files = [_source_record(total_dos_path, "dos-table")]
    if energy_reference_path is not None and energy_reference_path.resolve() != total_dos_path.resolve():
        source_files.append(_source_record(energy_reference_path, "energy-reference"))
    source_files.extend(_source_record(path, "projected-dos") for path in projected_dos_paths)
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "dos-pdos",
        "code": "qe",
        "maturity": maturity,
        "representation": "table",
        "source_files": source_files,
        "dimensions": {"energy_points": len(grid), "channels": len(channels), "rows": len(grid) * len(channels)},
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
                "parameters": {
                    "energy_reference_ev": reference,
                    "source_label": (energy_reference_path or total_dos_path).name,
                },
                "input_columns": ["energy_raw_ev"],
                "output_columns": ["energy_relative_ev"],
            },
            {
                "operation": "aggregate-projected-ldos",
                "parameters": {"group_by": group_by, "source_file_count": len(projected_dos_paths)},
                "input_columns": ["ldos"],
                "output_columns": ["dos_states_per_ev"],
            },
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "finite-values", "status": "pass", "message": "All energy and DOS values are finite."},
                {"id": "monotonic-energy-grid", "status": "pass", "message": "The energy grid is strictly increasing."},
                {"id": "grid-alignment", "status": "pass", "message": "All supplied projected files use the total-DOS energy grid."},
                {"id": "energy-reference", "status": "pass", "message": "An explicit Fermi energy was parsed from the DOS header or a supplied evidence file."},
                {"id": "channel-mapping", "status": "pass", "message": "Projection metadata was parsed from standard QE filenames."},
            ],
        },
        "limitations": analysis["limitations"],
        "provenance": {
            "producer": "dftpost.qe-dos",
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


def plot_bands_dos(
    bands_table_path: Path,
    dos_table_path: Path,
    output_path: Path,
    *,
    energy_window_ev: tuple[float, float] | None = None,
    pdos_channel_labels: list[str] | None = None,
    bands_metadata_path: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    _refuse_existing_outputs((output_path,), overwrite)
    band_series: dict[int, list[tuple[float, float]]] = {}
    with bands_table_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"k_distance", "band_index", "energy_relative_ev"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"bands table is missing columns: {sorted(missing)}")
        for row_number, row in enumerate(reader, start=2):
            try:
                band_index = int(row["band_index"])
                point = (float(row["k_distance"]), float(row["energy_relative_ev"]))
            except ValueError as exc:
                raise ValueError(f"bands table row {row_number} is malformed") from exc
            if not all(math.isfinite(value) for value in point):
                raise ValueError(f"bands table row {row_number} contains non-finite values")
            band_series.setdefault(band_index, []).append(point)
    if not band_series:
        raise ValueError("bands table contains no data rows")

    dos_series: dict[str, list[tuple[float, float]]] = {}
    dos_channel_types: dict[str, str] = {}
    with dos_table_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"energy_relative_ev", "channel_label", "channel_type", "dos_states_per_ev"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"DOS table is missing columns: {sorted(missing)}")
        for row_number, row in enumerate(reader, start=2):
            label = row["channel_label"]
            channel_type = row["channel_type"]
            if not label or not channel_type:
                raise ValueError(f"DOS table row {row_number} has an empty channel label or type")
            previous_type = dos_channel_types.setdefault(label, channel_type)
            if previous_type != channel_type:
                raise ValueError(f"DOS channel {label!r} has inconsistent channel types")
            try:
                point = (float(row["dos_states_per_ev"]), float(row["energy_relative_ev"]))
            except ValueError as exc:
                raise ValueError(f"DOS table row {row_number} is malformed") from exc
            if not all(math.isfinite(value) for value in point):
                raise ValueError(f"DOS table row {row_number} contains non-finite values")
            dos_series.setdefault(label, []).append(point)
    if not dos_series:
        raise ValueError("DOS table contains no data rows")

    tdos_labels = [label for label in dos_series if dos_channel_types[label] == "total"]
    available_pdos_labels = [
        label for label in dos_series if dos_channel_types[label].startswith("projected")
    ]
    unsupported_types = sorted(
        {channel_type for channel_type in dos_channel_types.values()}
        .difference({"total", "projected", "projected-total"})
    )
    if unsupported_types:
        raise ValueError(f"DOS table contains unsupported channel types: {unsupported_types}")
    if not tdos_labels:
        raise ValueError("TDOS + PDOS plot requires at least one channel_type=total channel")

    if pdos_channel_labels is None:
        selected_pdos_labels = available_pdos_labels
    else:
        if len(set(pdos_channel_labels)) != len(pdos_channel_labels):
            raise ValueError("PDOS channel selection contains duplicate labels")
        missing_channels = [label for label in pdos_channel_labels if label not in dos_series]
        if missing_channels:
            raise ValueError(f"requested PDOS channels are missing: {missing_channels}")
        non_projected = [
            label for label in pdos_channel_labels
            if not dos_channel_types[label].startswith("projected")
        ]
        if non_projected:
            raise ValueError(f"requested PDOS channels are not projected channels: {non_projected}")
        selected_pdos_labels = list(pdos_channel_labels)
    if not selected_pdos_labels:
        raise ValueError("TDOS + PDOS plot requires at least one projected DOS channel")

    selected_labels = [*tdos_labels, *selected_pdos_labels]
    selected_dos_series = {label: dos_series[label] for label in selected_labels}

    all_band_x = [point[0] for points in band_series.values() for point in points]
    visible_dos_points = [
        point for points in selected_dos_series.values() for point in points
        if energy_window_ev is None or energy_window_ev[0] <= point[1] <= energy_window_ev[1]
    ]
    if not visible_dos_points:
        raise ValueError("DOS energy window contains no data points")
    all_dos_x = [point[0] for point in visible_dos_points]
    band_limits = [min(all_band_x), max(all_band_x)]
    dos_limits = [min(0.0, min(all_dos_x)), max(all_dos_x)]
    if band_limits[0] == band_limits[1]:
        raise ValueError("bands table has a zero-width path coordinate range")
    if dos_limits[0] == dos_limits[1]:
        raise ValueError("DOS channels have a zero-width value range")
    if energy_window_ev is not None and energy_window_ev[0] >= energy_window_ev[1]:
        raise ValueError("energy window must be increasing")
    sampled_kpoints = sorted(set(all_band_x))
    symmetry_points = (
        _symmetry_points_from_plot_metadata(bands_metadata_path, sampled_kpoints)
        if bands_metadata_path is not None
        else []
    )

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    tdos_colors = ["#111827", "#4b5563"]
    pdos_colors = [
        "#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9",
        "#D55E00", "#6F4E7C", "#8C564B", "#17BECF", "#7F7F7F",
    ]
    line_styles = ["-", "--", ":", "-."]
    channel_styles: list[dict[str, Any]] = []
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with plt.style.context(str(style)):
        figure, (band_axis, dos_axis) = plt.subplots(
            1,
            2,
            sharey=True,
            gridspec_kw={"width_ratios": [3.2, 1.0], "wspace": 0.04},
        )
        for points in band_series.values():
            band_axis.plot(
                [point[0] for point in points],
                [point[1] for point in points],
                color="#7f1d1d",
                linewidth=0.9,
            )
        band_axis.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
        band_axis.set_xlabel("Wave vector" if symmetry_points else "Path coordinate")
        band_axis.set_ylabel(r"Energy - $E_\mathrm{ref}$ (eV)")
        if symmetry_points:
            for point in symmetry_points:
                band_axis.axvline(
                    point["k_distance"], color="#b8b8b8", linewidth=0.55, zorder=0
                )
            band_axis.set_xticks(
                [point["k_distance"] for point in symmetry_points],
                [point["label"] for point in symmetry_points],
            )
        band_axis.set_xlim(*band_limits)
        band_axis.margins(x=0)

        for index, label in enumerate(tdos_labels):
            points = selected_dos_series[label]
            color = tdos_colors[index % len(tdos_colors)]
            linestyle = line_styles[index // len(tdos_colors) % len(line_styles)]
            dos_axis.plot(
                [point[0] for point in points],
                [point[1] for point in points],
                label=label,
                color=color,
                linewidth=1.7,
                linestyle=linestyle,
                zorder=3,
            )
            channel_styles.append({
                "label": label,
                "role": "tdos",
                "color": color,
                "linewidth": 1.7,
                "linestyle": linestyle,
            })
        for index, label in enumerate(selected_pdos_labels):
            points = selected_dos_series[label]
            color = pdos_colors[index % len(pdos_colors)]
            linestyle = line_styles[index // len(pdos_colors) % len(line_styles)]
            dos_axis.plot(
                [point[0] for point in points],
                [point[1] for point in points],
                label=label,
                color=color,
                linewidth=1.0,
                linestyle=linestyle,
                zorder=2,
            )
            channel_styles.append({
                "label": label,
                "role": "pdos",
                "color": color,
                "linewidth": 1.0,
                "linestyle": linestyle,
            })
        dos_axis.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
        dos_axis.set_xlabel("DOS (states/eV)")
        dos_axis.set_xlim(*dos_limits)
        dos_axis.margins(x=0)
        dos_axis.legend(
            fontsize="x-small",
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            borderaxespad=0.0,
        )
        if energy_window_ev is not None:
            band_axis.set_ylim(*energy_window_ev)
        _save_figure_atomic(figure, output_path)
        plt.close(figure)
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"combined bands-DOS plot was not created: {output_path}")
    return {
        "schema_version": "1.0",
        "plot_type": "bands-dos",
        "band_color": "#7f1d1d",
        "band_x_limits": band_limits,
        "dos_x_limits": dos_limits,
        "energy_window_ev": list(energy_window_ev) if energy_window_ev is not None else None,
        "high_symmetry_points": symmetry_points,
        "dos_content": "tdos+pdos",
        "tdos_channel_labels": tdos_labels,
        "pdos_channel_labels": selected_pdos_labels,
        "dos_channel_labels": selected_labels,
        "excluded_pdos_channel_labels": [
            label for label in available_pdos_labels if label not in selected_pdos_labels
        ],
        "dos_channel_styles": channel_styles,
        "inputs": [
            {"role": "bands-table", "label": bands_table_path.name, "sha256": sha256_file(bands_table_path)},
            {"role": "dos-table", "label": dos_table_path.name, "sha256": sha256_file(dos_table_path)},
            *([{
                "role": "bands-plot-metadata",
                "label": bands_metadata_path.name,
                "sha256": sha256_file(bands_metadata_path),
            }] if bands_metadata_path is not None else []),
        ],
        "output": _output_record(output_path, "figure", "image/png"),
    }


def _filproj_metadata_line(lines: list[str], path: Path) -> tuple[int, int, int, int]:
    for index, line in enumerate(lines):
        match = re.fullmatch(r"\s*(\d+)\s+(\d+)\s+(\d+)\s*", line)
        if not match:
            continue
        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1
        if next_index < len(lines) and re.fullmatch(r"\s*[TF]\s+[TF]\s*", lines[next_index], re.IGNORECASE):
            return int(match.group(1)), int(match.group(2)), int(match.group(3)), next_index + 1
    raise ValueError(f"{path.name}: filproj dimension header was not found")


def _parse_filproj_selected(
    path: Path, selector: dict[str, str]
) -> tuple[int, int, list[dict[str, Any]], list[list[float]]]:
    if not selector:
        raise ValueError("a nonempty filproj selector is required")
    allowed = {"state_index", "atom_index", "species", "orbital", "wfc_index", "l", "m"}
    unknown = set(selector).difference(allowed)
    if unknown:
        raise ValueError(f"unknown filproj selector keys: {sorted(unknown)}")
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    _nat, nkpoints, nbands, index = _filproj_metadata_line(lines, path)
    weights = [[0.0] * nbands for _ in range(nkpoints)]
    selected_states: list[dict[str, Any]] = []
    state_header = re.compile(
        r"\s*(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s*"
    )
    observed_states = 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        match = state_header.fullmatch(lines[index])
        if not match:
            raise ValueError(f"{path.name}:{index + 1}: expected a filproj state header")
        state = {
            "state_index": int(match.group(1)),
            "atom_index": int(match.group(2)),
            "species": match.group(3),
            "orbital": match.group(4),
            "wfc_index": int(match.group(5)),
            "l": int(match.group(6)),
            "m": int(match.group(7)),
        }
        observed_states += 1
        index += 1
        selected = all(str(state[key]) == str(value) for key, value in selector.items())
        if selected:
            selected_states.append(state)
        expected_rows = nkpoints * nbands
        for _ in range(expected_rows):
            if index >= len(lines):
                raise ValueError(f"{path.name}: truncated filproj weight block")
            fields = lines[index].split()
            if len(fields) != 3:
                raise ValueError(f"{path.name}:{index + 1}: expected k-index, band-index, weight")
            try:
                kpoint, band, weight = int(fields[0]), int(fields[1]), float(fields[2])
            except ValueError as exc:
                raise ValueError(f"{path.name}:{index + 1}: malformed filproj weight") from exc
            if not (1 <= kpoint <= nkpoints and 1 <= band <= nbands):
                raise ValueError(f"{path.name}:{index + 1}: filproj index is out of bounds")
            if not math.isfinite(weight) or weight < 0.0:
                raise ValueError(f"{path.name}:{index + 1}: filproj weight must be finite and nonnegative")
            if selected:
                weights[kpoint - 1][band - 1] += weight
            index += 1
    if observed_states == 0:
        raise ValueError(f"{path.name}: no filproj states found")
    if not selected_states:
        raise ValueError(f"{path.name}: selector matched no projection states")
    return nkpoints, nbands, selected_states, weights


def _plot_fatband(
    kpoints: list[float],
    bands: list[list[float]],
    reference: float,
    weights: list[list[float]],
    output: Path,
    energy_window_ev: tuple[float, float] | None,
    marker_scale: float,
    render_mode: str,
    projection_label: str,
    bands_label: str,
    xlabel: str = "Path coordinate (native QE units)",
    symmetry_points: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if marker_scale <= 0.0:
        raise ValueError("fatband marker scale must be positive")
    if render_mode not in {"line-width", "bubble"}:
        raise ValueError(f"unsupported fatband render mode: {render_mode}")
    bands_label = bands_label.strip()
    if not bands_label:
        raise ValueError("bands label must be nonempty")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.colors import Normalize
    from matplotlib.lines import Line2D
    import numpy as np

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    output.parent.mkdir(parents=True, exist_ok=True)
    maximum_weight = max(weight for row in weights for weight in row)
    with plt.style.context(str(style)):
        figure, axis = plt.subplots()
        for band_index, band in enumerate(bands):
            shifted = [value - reference for value in band]
            axis.plot(kpoints, shifted, color="#aeb3b8", linewidth=0.65, zorder=1)
            band_weights = [weights[kpoint_index][band_index] for kpoint_index in range(len(kpoints))]
            if render_mode == "bubble":
                sizes = np.asarray(_bubble_marker_areas(band_weights, marker_scale), dtype=float)
                mask = sizes > 0.0
                axis.scatter(
                    np.asarray(kpoints, dtype=float)[mask],
                    np.asarray(shifted, dtype=float)[mask],
                    s=sizes[mask],
                    facecolors=[(0.561, 0.114, 0.114, 0.46)],
                    edgecolors=[(0.424, 0.082, 0.082, 0.90)],
                    linewidths=0.55,
                    zorder=2,
                )
            else:
                points = np.column_stack((kpoints, shifted))
                segments = np.stack((points[:-1], points[1:]), axis=1)
                segment_weights = np.asarray(
                    [(left + right) * 0.5 for left, right in zip(band_weights, band_weights[1:])]
                )
                denominator = maximum_weight if maximum_weight > 0.0 else 1.0
                widths = np.asarray(
                    _projection_line_widths(segment_weights.tolist(), marker_scale),
                    dtype=float,
                )
                collection = LineCollection(
                    segments,
                    cmap="Reds",
                    norm=Normalize(vmin=0.0, vmax=denominator),
                    linewidths=widths,
                    alpha=0.95,
                    zorder=2,
                )
                collection.set_array(segment_weights)
                axis.add_collection(collection)
        axis.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
        axis.set_xlabel(xlabel)
        axis.set_ylabel(r"Energy - $E_\mathrm{ref}$ (eV)")
        if symmetry_points:
            for point in symmetry_points:
                axis.axvline(point["k_distance"], color="#b8b8b8", linewidth=0.55, zorder=0)
            axis.set_xticks(
                [point["k_distance"] for point in symmetry_points],
                [point["label"] for point in symmetry_points],
            )
        axis.set_xlim(kpoints[0], kpoints[-1])
        axis.margins(x=0)
        if energy_window_ev is not None:
            if energy_window_ev[0] >= energy_window_ev[1]:
                raise ValueError("energy window must be increasing")
            axis.set_ylim(*energy_window_ev)
        background_handle = Line2D(
            [0],
            [0],
            color="#aeb3b8",
            linewidth=1.2,
            label=bands_label,
        )
        if render_mode == "line-width":
            scalar = plt.cm.ScalarMappable(norm=Normalize(vmin=0.0, vmax=maximum_weight or 1.0), cmap="Reds")
            scalar.set_array([])
            colorbar = figure.colorbar(scalar, ax=axis, pad=0.02)
            colorbar.set_label("Selected projection weight")
            legend_handle = Line2D([0], [0], color="#8f1d1d", linewidth=2.4, label=projection_label)
        else:
            legend_handle = Line2D(
                [0],
                [0],
                color="#8f1d1d",
                marker="o",
                linestyle="None",
                markersize=7,
                label=projection_label,
            )
        axis.legend(
            handles=[background_handle, legend_handle],
            loc="upper right",
            frameon=True,
            fancybox=True,
            framealpha=0.55,
            edgecolor="#999999",
        )
        _save_figure_atomic(figure, output)
        plt.close(figure)
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"fatband plot was not created: {output}")
    return {
        "schema_version": "1.0",
        "plot_type": "fatband",
        "render_mode": render_mode,
        "background_label": bands_label,
        "projection_label": projection_label,
        "legend_labels": [bands_label, projection_label],
        "weight_encoding": (
            "continuous Reds color and line width" if render_mode == "line-width" else "bubble area"
        ),
        "weight_range": [0.0, maximum_weight],
        "marker_scale": marker_scale,
        "bubble_area_mapping": (
            "marker_area_pt2 = marker_scale^2 * projection_weight"
            if render_mode == "bubble"
            else None
        ),
        "line_width_mapping": (
            "line_width_pt = marker_scale * 0.45 * projection_weight"
            if render_mode == "line-width"
            else None
        ),
        "bubble_style": (
            {
                "fill_color": "#8f1d1d",
                "fill_alpha": 0.46,
                "edge_color": "#6c1515",
                "edge_alpha": 0.90,
                "edge_width_pt": 0.55,
            }
            if render_mode == "bubble"
            else None
        ),
        "x_limits": [kpoints[0], kpoints[-1]],
        "energy_window_ev": list(energy_window_ev) if energy_window_ev is not None else None,
        "output": _output_record(output, "figure", "image/png"),
    }


def _bubble_marker_areas(weights: list[float], marker_scale: float) -> list[float]:
    if not math.isfinite(marker_scale) or marker_scale <= 0.0:
        raise ValueError("fatband marker scale must be finite and positive")
    areas = []
    for weight in weights:
        if not math.isfinite(weight) or weight < 0.0:
            raise ValueError("fatband projection weights must be finite and nonnegative")
        areas.append(marker_scale**2 * weight)
    return areas


def _projection_line_widths(weights: list[float], marker_scale: float) -> list[float]:
    if not math.isfinite(marker_scale) or marker_scale <= 0.0:
        raise ValueError("fatband marker scale must be finite and positive")
    widths = []
    for weight in weights:
        if not math.isfinite(weight) or weight < 0.0:
            raise ValueError("fatband projection weights must be finite and nonnegative")
        widths.append(marker_scale * 0.45 * weight)
    return widths


def _selector_projection_label(selector: dict[str, str], explicit: str | None = None) -> str:
    if explicit is not None:
        label = explicit.strip()
        if not label:
            raise ValueError("projection label must be nonempty")
        return label
    prefix = selector.get("species") or (
        f"atom-{selector['atom_index']}" if "atom_index" in selector else "projection"
    )
    orbital = selector.get("orbital")
    if not orbital and "l" in selector:
        orbital = {"0": "s", "1": "p", "2": "d", "3": "f"}.get(
            str(selector["l"]), f"l={selector['l']}"
        )
    if orbital:
        return f"{prefix}-{orbital}"
    return ", ".join(f"{key}={value}" for key, value in sorted(selector.items()))


def normalize_qe_fatband(
    bands_path: Path,
    filproj_path: Path,
    energy_reference_path: Path,
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
    maturity: str = "format-fixture-validated",
    overwrite: bool = False,
) -> dict[str, Path]:
    _check_maturity(maturity)
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "fatband.csv"
    analysis_path = output_directory / "fatband.analysis.json"
    plot_metadata_path = output_directory / "fatband.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "fatband.png"
    dataset_path = output_directory / "fatband.dataset.json"
    _refuse_existing_outputs(
        (table_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite
    )

    kpoints, bands = parse_qe_bands_gnu(bands_path)
    reference = parse_qe_fermi_energy(energy_reference_path)
    nkpoints, nbands, states, weights = _parse_filproj_selected(filproj_path, selector)
    if nkpoints != len(kpoints) or nbands != len(bands):
        raise ValueError(
            f"bands/filproj dimension mismatch: bands={len(kpoints)}x{len(bands)}, filproj={nkpoints}x{nbands}"
        )
    rows = (
        {
            "k_index": kpoint_index,
            "k_distance": kpoint,
            "band_index": band_index,
            "energy_raw_ev": energy,
            "energy_relative_ev": energy - reference,
            "projection_weight": weights[kpoint_index - 1][band_index - 1],
        }
        for band_index, band in enumerate(bands, start=1)
        for kpoint_index, (kpoint, energy) in enumerate(zip(kpoints, band), start=1)
    )
    _write_csv_atomic(
        table_path,
        ["k_index", "k_distance", "band_index", "energy_raw_ev", "energy_relative_ev", "projection_weight"],
        rows,
    )
    flat_weights = [weight for kpoint in weights for weight in kpoint]
    analysis = {
        "schema_version": "1.0",
        "selector": selector,
        "selected_state_count": len(states),
        "selected_states": states,
        "weight_min": min(flat_weights),
        "weight_max": max(flat_weights),
        "weight_sum": sum(flat_weights),
        "energy_reference_ev": reference,
        "limitations": [
            "Projection weights are aggregated only over the explicitly selected filproj states.",
            "Marker area or line width is a visualization mapping and must not be interpreted as a separately normalized observable.",
        ],
    }
    rendered_projection_label = _selector_projection_label(selector, projection_label)
    analysis["projection_label"] = rendered_projection_label
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_fatband(
        kpoints,
        bands,
        reference,
        weights,
        figure_path,
        energy_window_ev,
        marker_scale,
        render_mode,
        rendered_projection_label,
        bands_label,
    )
    write_json_atomic(plot_metadata_path, plot_metadata)
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "bands",
        "code": "qe",
        "maturity": maturity,
        "representation": "table",
        "source_files": [
            _source_record(bands_path, "eigenvalues"),
            _source_record(filproj_path, "projection-weights"),
            _source_record(energy_reference_path, "energy-reference"),
        ],
        "dimensions": {"bands": len(bands), "kpoints": len(kpoints), "rows": len(bands) * len(kpoints), "selected_states": len(states)},
        "columns": [
            {"name": "k_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "k_distance", "dtype": "float", "unit": None, "role": "native-path-coordinate"},
            {"name": "band_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "energy_raw_ev", "dtype": "float", "unit": "eV", "role": "eigenvalue", "reference": "absolute-output-value"},
            {"name": "energy_relative_ev", "dtype": "float", "unit": "eV", "role": "eigenvalue", "reference": "explicit-fermi-energy"},
            {"name": "projection_weight", "dtype": "float", "unit": None, "role": "selected-projection-weight", "channel": "selector-defined"},
        ],
        "data_files": [
            _output_record(table_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "select-and-sum-projection-states",
                "parameters": {"selector": selector, "selected_state_count": len(states)},
                "input_columns": ["state_weight"],
                "output_columns": ["projection_weight"],
            },
            {
                "operation": "subtract-energy-reference",
                "parameters": {"energy_reference_ev": reference, "source_label": energy_reference_path.name},
                "input_columns": ["energy_raw_ev"],
                "output_columns": ["energy_relative_ev"],
            },
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "finite-values", "status": "pass", "message": "All energies and selected projection weights are finite."},
                {"id": "band-kpoint-dimensions", "status": "pass", "message": "Bands and filproj dimensions agree."},
                {"id": "energy-reference", "status": "pass", "message": "An explicit Fermi energy was parsed."},
                {"id": "projection-sums", "status": "pass", "message": "Only explicitly selected state weights were aggregated."},
            ],
        },
        "limitations": analysis["limitations"],
        "provenance": {
            "producer": "dftpost.qe-fatband",
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
