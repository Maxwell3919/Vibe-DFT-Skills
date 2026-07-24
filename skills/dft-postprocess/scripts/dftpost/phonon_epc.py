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
from .registry import resolve_backend_maturity
from .utils import utc_now, write_json_atomic


FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"


def _numeric_rows(path: Path) -> list[list[float]]:
    rows = []
    width = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            row = [float(value) for value in stripped.split()]
        except ValueError as exc:
            raise ValueError(f"{path.name}:{line_number}: nonnumeric table row") from exc
        if not row or not all(math.isfinite(value) for value in row):
            raise ValueError(f"{path.name}:{line_number}: empty or non-finite table row")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError(f"{path.name}:{line_number}: inconsistent table width")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path.name}: no numeric table rows")
    return rows


def _plot_phonon(
    path_coordinates: list[float],
    modes: list[list[float]],
    unit: str,
    output: Path,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    with plt.style.context(str(style)):
        figure, axis = plt.subplots()
        for mode in modes:
            axis.plot(path_coordinates, mode, color="#7f1d1d", linewidth=0.9)
        axis.axhline(0.0, color="black", linestyle="--", linewidth=0.8)
        axis.set_xlabel("Path coordinate")
        axis.set_ylabel(f"Frequency ({unit})")
        axis.set_xlim(path_coordinates[0], path_coordinates[-1])
        axis.margins(x=0)
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {
        "schema_version": "1.0",
        "plot_type": "phonon-dispersion",
        "x_limits": [path_coordinates[0], path_coordinates[-1]],
        "frequency_unit": unit,
        "imaginary_frequencies_shown_as_negative": True,
        "output": _output_record(output, "figure", "image/png"),
    }


def normalize_qe_phonon(
    frequencies_path: Path,
    output_directory: Path,
    dataset_id: str,
    *,
    frequency_unit: str,
    imaginary_threshold: float = 0.0,
    figure_output: Path | None = None,
    maturity: str | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    maturity = resolve_backend_maturity("phonon", "qe", "python.qe-phonon", maturity)
    _check_maturity(maturity)
    if not frequency_unit.strip():
        raise ValueError("frequency_unit must be explicit and nonempty")
    if imaginary_threshold < 0.0:
        raise ValueError("imaginary_threshold must be nonnegative")
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "phonon.csv"
    analysis_path = output_directory / "phonon.analysis.json"
    plot_metadata_path = output_directory / "phonon.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "phonon.png"
    dataset_path = output_directory / "phonon.dataset.json"
    _refuse_existing_outputs((table_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite)

    rows = _numeric_rows(frequencies_path)
    if len(rows[0]) < 2:
        raise ValueError(f"{frequencies_path.name}: phonon table requires path plus at least one mode")
    coordinates = [row[0] for row in rows]
    if any(right < left for left, right in zip(coordinates, coordinates[1:])) or coordinates[0] == coordinates[-1]:
        raise ValueError(f"{frequencies_path.name}: path coordinate must be nondecreasing with nonzero extent")
    mode_count = len(rows[0]) - 1
    modes = [[row[mode + 1] for row in rows] for mode in range(mode_count)]
    flat = [value for mode in modes for value in mode]
    imaginary = [value for value in flat if value < -imaginary_threshold]
    _write_csv_atomic(
        table_path,
        ["q_index", "q_distance", "mode_index", "frequency"],
        (
            {"q_index": q_index, "q_distance": distance, "mode_index": mode_index, "frequency": value}
            for mode_index, mode in enumerate(modes, start=1)
            for q_index, (distance, value) in enumerate(zip(coordinates, mode), start=1)
        ),
    )
    analysis = {
        "schema_version": "1.0",
        "frequency_unit": frequency_unit,
        "qpoints": len(coordinates),
        "modes": mode_count,
        "frequency_min": min(flat),
        "frequency_max": max(flat),
        "imaginary_threshold": imaginary_threshold,
        "imaginary_frequency_count": len(imaginary),
        "imaginary_qpoint_count": len({q_index for q_index, row in enumerate(rows, start=1) if any(value < -imaginary_threshold for value in row[1:])}),
        "limitations": [
            "Negative values remain signed and visible; no automatic absolute-value or clipping transformation is applied.",
            "The path coordinate and frequency unit are caller-declared evidence and are not inferred from a material name.",
            "No dynamical-stability conclusion is made by this numerical normalizer.",
        ],
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_phonon(coordinates, modes, frequency_unit, figure_path)
    write_json_atomic(plot_metadata_path, plot_metadata)
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "phonon",
        "code": "qe",
        "maturity": maturity,
        "representation": "table",
        "source_files": [_source_record(frequencies_path, "phonon-frequencies")],
        "dimensions": {"qpoints": len(coordinates), "modes": mode_count, "rows": len(coordinates) * mode_count},
        "columns": [
            {"name": "q_index", "dtype": "integer", "unit": None, "role": "index"},
            {"name": "q_distance", "dtype": "float", "unit": None, "role": "native-path-coordinate"},
            {"name": "mode_index", "dtype": "integer", "unit": None, "role": "mode-index"},
            {"name": "frequency", "dtype": "float", "unit": frequency_unit, "role": "signed-frequency"},
        ],
        "data_files": [
            _output_record(table_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "finite-values", "status": "pass", "message": "All path and frequency values are finite."},
                {"id": "q-mode-dimensions", "status": "pass", "message": "Every q point has the same mode count."},
                {"id": "frequency-unit", "status": "pass", "message": "The caller supplied an explicit frequency unit."},
                {"id": "path-mapping", "status": "pass", "message": "The native path coordinate is ordered and retained."},
                {"id": "imaginary-mode-visibility", "status": "pass", "message": "Negative signed frequencies are preserved in table and plot."},
            ],
        },
        "limitations": analysis["limitations"],
        "provenance": {"producer": "dftpost.qe-phonon", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {"table": table_path, "analysis": analysis_path, "plot_metadata": plot_metadata_path, "figure": figure_path, "dataset": dataset_path}


def _parse_alpha2f(path: Path) -> tuple[list[float], list[float], list[list[float]]]:
    lines = [line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    if not lines or not lines[0].lstrip().startswith("#"):
        raise ValueError(f"{path.name}: alpha2F table requires a header")
    header = [float(value) for value in re.findall(FLOAT, lines[0].split("THz", 1)[-1])]
    if not header:
        raise ValueError(f"{path.name}: alpha2F header contains no smearing values")
    cursor = 1
    first_values = [float(value) for value in lines[cursor].split()]
    if len(first_values) == len(header):
        header.extend(first_values)
        cursor += 1
    channel_count = len(header)
    frequencies: list[float] = []
    channel_values = [[] for _ in range(channel_count)]
    while cursor < len(lines):
        try:
            primary = [float(value) for value in lines[cursor].split()]
        except ValueError as exc:
            raise ValueError(f"{path.name}:{cursor + 1}: malformed alpha2F row") from exc
        cursor += 1
        if len(primary) < 2:
            raise ValueError(f"{path.name}:{cursor}: alpha2F primary row requires frequency and values")
        frequency, values = primary[0], primary[1:]
        while len(values) < channel_count and cursor < len(lines):
            continuation = [float(value) for value in lines[cursor].split()]
            cursor += 1
            values.extend(continuation)
        if len(values) != channel_count:
            raise ValueError(f"{path.name}: alpha2F row/channel count mismatch")
        if not all(math.isfinite(value) for value in [frequency, *values]):
            raise ValueError(f"{path.name}: non-finite alpha2F value")
        frequencies.append(frequency)
        for index, value in enumerate(values):
            channel_values[index].append(value)
    if len(frequencies) < 2 or any(right <= left for left, right in zip(frequencies, frequencies[1:])):
        raise ValueError(f"{path.name}: alpha2F frequency grid must be strictly increasing")
    return header, frequencies, channel_values


def _parse_lambda_table(path: Path) -> list[dict[str, float]]:
    result = []
    for row in _numeric_rows(path):
        if len(row) < 5:
            raise ValueError(f"{path.name}: lambda table requires five columns")
        result.append({"smearing_ry": row[0], "lambda": row[1], "integrated_alpha2f": row[2], "omega_log": row[3], "nef": row[4]})
    return result


def _cumulative_lambda(frequencies: list[float], values: list[float]) -> list[float]:
    integrand = [0.0 if frequency <= 0.0 else 2.0 * value / frequency for frequency, value in zip(frequencies, values)]
    cumulative = [0.0]
    for index in range(1, len(frequencies)):
        width = frequencies[index] - frequencies[index - 1]
        cumulative.append(cumulative[-1] + 0.5 * width * (integrand[index - 1] + integrand[index]))
    return cumulative


def _parse_elph_qmode(path: Path, smearing_index: int) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines:
        raise ValueError(f"{path.name}: empty elph input")
    fields = lines[0].split()
    if len(fields) < 5:
        raise ValueError(f"{path.name}: malformed elph q-point header")
    try:
        q = [float(value) for value in fields[:3]]
        nsigma, nmodes = int(fields[3]), int(fields[4])
    except ValueError as exc:
        raise ValueError(f"{path.name}: malformed elph q-point metadata") from exc
    if smearing_index < 1 or smearing_index > nsigma:
        raise ValueError(f"{path.name}: qmode smearing index is outside 1..{nsigma}")
    gaussian_indices = [index for index, line in enumerate(lines) if "Gaussian Broadening" in line]
    if len(gaussian_indices) != nsigma:
        raise ValueError(f"{path.name}: elph smearing block count mismatch")
    frequency_tokens = []
    for line in lines[1:gaussian_indices[0]]:
        frequency_tokens.extend(float(value) for value in line.split())
    if len(frequency_tokens) != nmodes:
        raise ValueError(f"{path.name}: elph mode-frequency count mismatch")
    start = gaussian_indices[smearing_index - 1]
    end = gaussian_indices[smearing_index] if smearing_index < nsigma else len(lines)
    records = []
    pattern = re.compile(rf"lambda\(\s*(\d+)\s*\)\s*=\s*({FLOAT})\s+gamma\s*=\s*({FLOAT})\s+GHz", re.IGNORECASE)
    for line in lines[start:end]:
        match = pattern.search(line)
        if not match:
            continue
        mode = int(match.group(1))
        records.append({
            "qx": q[0], "qy": q[1], "qz": q[2], "mode_index": mode,
            "frequency_thz": frequency_tokens[mode - 1],
            "lambda_q_mode": float(match.group(2)), "gamma_ghz": float(match.group(3)),
        })
    if len(records) != nmodes:
        raise ValueError(f"{path.name}: selected elph block does not contain all modes")
    return records


def _plot_epc(
    smearing_values: list[float],
    frequencies: list[float],
    alpha_channels: list[list[float]],
    cumulative_channels: list[list[float]],
    lambda_rows: list[dict[str, float]],
    selected: list[int],
    output: Path,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    with plt.style.context(str(style)):
        figure, axes = plt.subplots(3, 1, figsize=(7.0, 9.0))
        for index in selected:
            label = f"#{index} ({smearing_values[index - 1]:.6g} Ry)"
            axes[0].plot(frequencies, alpha_channels[index - 1], label=label, linewidth=1.0)
            axes[1].plot(frequencies, cumulative_channels[index - 1], label=label, linewidth=1.0)
        axes[0].set_ylabel(r"$\alpha^2F(\omega)$")
        axes[1].set_ylabel(r"Cumulative $\lambda$")
        for axis in axes[:2]:
            axis.set_xlim(frequencies[0], frequencies[-1])
            axis.margins(x=0)
            axis.legend(fontsize="small")
        axes[1].set_xlabel("Frequency (THz)")
        channel_indices = list(range(1, len(lambda_rows) + 1))
        axes[2].plot(channel_indices, [row["lambda"] for row in lambda_rows], color="#7f1d1d", marker="o", linewidth=1.0)
        if len(channel_indices) > 1:
            axes[2].set_xlim(channel_indices[0], channel_indices[-1])
            axes[2].margins(x=0)
        axes[2].set_xlabel("Smearing channel index")
        axes[2].set_ylabel(r"Reported $\lambda$")
        figure.tight_layout()
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {
        "schema_version": "1.0", "plot_type": "epc-spectra-and-smearing",
        "frequency_x_limits": [frequencies[0], frequencies[-1]], "selected_smearing_indices": selected,
        "output": _output_record(output, "figure", "image/png"),
    }


def _plot_qmode(rows: list[dict[str, Any]], output: Path) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    q_indices = sorted({row["q_index"] for row in rows})
    mode_indices = sorted({row["mode_index"] for row in rows})
    matrix = np.zeros((len(mode_indices), len(q_indices)))
    for row in rows:
        matrix[mode_indices.index(row["mode_index"]), q_indices.index(row["q_index"])] = row["lambda_q_mode"]
    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    with plt.style.context(str(style)):
        figure, axis = plt.subplots()
        image = axis.imshow(matrix, origin="lower", aspect="auto", cmap="Reds")
        axis.set_xlabel("q-point index")
        axis.set_ylabel("Mode index")
        axis.set_xticks(range(len(q_indices)), q_indices)
        axis.set_yticks(range(len(mode_indices)), mode_indices)
        colorbar = figure.colorbar(image, ax=axis)
        colorbar.set_label(r"Raw $\lambda_{q\nu}$")
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {"schema_version": "1.0", "plot_type": "q-mode-lambda", "qpoints": len(q_indices), "modes": len(mode_indices), "output": _output_record(output, "figure", "image/png")}


def normalize_qe_epc(
    alpha2f_path: Path,
    lambda_table_path: Path,
    elph_paths: list[Path],
    output_directory: Path,
    dataset_id: str,
    *,
    selected_smearing_indices: list[int] | None = None,
    qmode_smearing_index: int = 1,
    figure_output: Path | None = None,
    qmode_figure_output: Path | None = None,
    maturity: str | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    maturity = resolve_backend_maturity("epc", "qe", "python.qe-epc", maturity)
    _check_maturity(maturity)
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    spectrum_path = output_directory / "alpha2f.csv"
    smearing_path = output_directory / "smearing-series.csv"
    qmode_path = output_directory / "q-mode.csv"
    analysis_path = output_directory / "epc.analysis.json"
    plot_metadata_path = output_directory / "epc.plot.json"
    qmode_plot_metadata_path = output_directory / "q-mode.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "epc.png"
    qmode_figure_path = qmode_figure_output.resolve() if qmode_figure_output is not None else output_directory / "q-mode.png"
    dataset_path = output_directory / "epc.dataset.json"
    targets = [spectrum_path, smearing_path, analysis_path, plot_metadata_path, figure_path, dataset_path]
    if elph_paths:
        targets.extend([qmode_path, qmode_plot_metadata_path, qmode_figure_path])
    _refuse_existing_outputs(targets, overwrite)

    smearing_values, frequencies, alpha_channels = _parse_alpha2f(alpha2f_path)
    lambda_rows = _parse_lambda_table(lambda_table_path)
    if len(lambda_rows) != len(smearing_values):
        raise ValueError("alpha2F/lambda smearing channel count mismatch")
    cumulative_channels = [_cumulative_lambda(frequencies, values) for values in alpha_channels]
    selected = selected_smearing_indices or sorted({1, (len(smearing_values) + 1) // 2, len(smearing_values)})
    if not selected or any(index < 1 or index > len(smearing_values) for index in selected):
        raise ValueError("selected smearing indices are outside the available range")
    _write_csv_atomic(
        spectrum_path,
        ["frequency_index", "frequency_thz", "smearing_index", "smearing_ry", "alpha2f", "cumulative_lambda"],
        (
            {"frequency_index": frequency_index, "frequency_thz": frequency, "smearing_index": channel_index,
             "smearing_ry": smearing_values[channel_index - 1], "alpha2f": alpha_channels[channel_index - 1][frequency_index - 1],
             "cumulative_lambda": cumulative_channels[channel_index - 1][frequency_index - 1]}
            for channel_index in range(1, len(smearing_values) + 1)
            for frequency_index, frequency in enumerate(frequencies, start=1)
        ),
    )
    _write_csv_atomic(
        smearing_path,
        ["smearing_index", "smearing_ry", "lambda", "integrated_alpha2f", "omega_log", "nef", "computed_cumulative_lambda"],
        (
            {"smearing_index": index, **row, "computed_cumulative_lambda": cumulative_channels[index - 1][-1]}
            for index, row in enumerate(lambda_rows, start=1)
        ),
    )
    qmode_rows = []
    for q_index, path in enumerate(elph_paths, start=1):
        for record in _parse_elph_qmode(path, qmode_smearing_index):
            qmode_rows.append({"q_index": q_index, **record})
    if qmode_rows:
        _write_csv_atomic(
            qmode_path,
            ["q_index", "qx", "qy", "qz", "mode_index", "frequency_thz", "lambda_q_mode", "gamma_ghz"],
            qmode_rows,
        )
    analysis = {
        "schema_version": "1.0", "frequency_unit": "THz", "frequency_points": len(frequencies),
        "smearing_channels": len(smearing_values), "selected_smearing_indices": selected,
        "qmode_smearing_index": qmode_smearing_index if qmode_rows else None,
        "qpoints": len(elph_paths), "modes_per_qpoint": len(qmode_rows) // len(elph_paths) if elph_paths else 0,
        "q_weight_closure_status": "not-run" if qmode_rows else "not-applicable",
        "channels": [
            {"smearing_index": index, "smearing_ry": smearing_values[index - 1], "reported_lambda": lambda_rows[index - 1]["lambda"],
             "computed_cumulative_lambda": cumulative_channels[index - 1][-1]}
            for index in range(1, len(smearing_values) + 1)
        ],
        "limitations": [
            "Cumulative lambda is a direct trapezoidal integration of the supplied alpha2F table; the separately reported lambda table is preserved for comparison.",
            "Raw q/mode lambda and gamma values are not q-weighted when no q-weight evidence is supplied; total-lambda closure is therefore not claimed.",
            "No material-specific superconducting or mode-character interpretation is produced.",
        ],
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_epc(smearing_values, frequencies, alpha_channels, cumulative_channels, lambda_rows, selected, figure_path)
    write_json_atomic(plot_metadata_path, plot_metadata)
    if qmode_rows:
        qmode_metadata = _plot_qmode(qmode_rows, qmode_figure_path)
        write_json_atomic(qmode_plot_metadata_path, qmode_metadata)
    source_files = [_source_record(alpha2f_path, "epc-table"), _source_record(lambda_table_path, "smearing-definition")]
    source_files.extend(_source_record(path, "q-mode-epc") for path in elph_paths)
    data_files = [
        _output_record(spectrum_path, "alpha2f-table", "text/csv"), _output_record(smearing_path, "smearing-series", "text/csv"),
        _output_record(analysis_path, "numerical-analysis", "application/json"), _output_record(plot_metadata_path, "plot-metadata", "application/json"),
    ]
    if qmode_rows:
        data_files.extend([_output_record(qmode_path, "q-mode-table", "text/csv"), _output_record(qmode_plot_metadata_path, "q-mode-plot-metadata", "application/json")])
    dataset = {
        "schema_version": "1.0", "dataset_id": dataset_id, "observable": "epc", "code": "qe", "maturity": maturity,
        "representation": "collection", "source_files": source_files,
        "dimensions": {"frequency_points": len(frequencies), "smearing_channels": len(smearing_values), "spectrum_rows": len(frequencies) * len(smearing_values), "q_mode_rows": len(qmode_rows)},
        "columns": [
            {"name": "frequency_thz", "dtype": "float", "unit": "THz", "role": "frequency"},
            {"name": "smearing_index", "dtype": "integer", "unit": None, "role": "smearing-index"},
            {"name": "smearing_ry", "dtype": "float", "unit": "Ry", "role": "smearing"},
            {"name": "alpha2f", "dtype": "float", "unit": None, "role": "eliashberg-spectral-function"},
            {"name": "cumulative_lambda", "dtype": "float", "unit": None, "role": "integrated-coupling"},
            {"name": "lambda_q_mode", "dtype": "float", "unit": None, "role": "raw-q-mode-coupling"},
            {"name": "gamma_ghz", "dtype": "float", "unit": "GHz", "role": "linewidth"},
        ],
        "data_files": data_files,
        "transformations": [{"operation": "trapezoidal-cumulative-lambda", "parameters": {"formula": "2*integral(alpha2F/frequency)"}, "input_columns": ["frequency_thz", "alpha2f"], "output_columns": ["cumulative_lambda"]}],
        "validation": {"status": "warn" if qmode_rows else "pass", "checks": [
            {"id": "finite-values", "status": "pass", "message": "All EPC tables contain finite values."},
            {"id": "smearing-grid", "status": "pass", "message": "alpha2F and lambda tables have the same channel count."},
            {"id": "frequency-alignment", "status": "pass", "message": "Every alpha2F channel uses the same increasing frequency grid."},
            {"id": "q-weight-closure", "status": "not-run" if qmode_rows else "pass", "message": "No q weights were supplied; raw q/mode values are not promoted to a weighted total." if qmode_rows else "No q/mode closure was requested."},
            {"id": "mode-closure", "status": "not-run" if qmode_rows else "pass", "message": "Mode totals remain unweighted without q-weight evidence." if qmode_rows else "No q/mode closure was requested."},
        ]},
        "limitations": analysis["limitations"], "provenance": {"producer": "dftpost.qe-epc", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    result = {"spectrum_table": spectrum_path, "smearing_table": smearing_path, "analysis": analysis_path, "plot_metadata": plot_metadata_path, "figure": figure_path, "dataset": dataset_path}
    if qmode_rows:
        result.update({"qmode_table": qmode_path, "qmode_plot_metadata": qmode_plot_metadata_path, "qmode_figure": qmode_figure_path})
    return result
