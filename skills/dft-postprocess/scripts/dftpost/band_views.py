from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from .electronic import (
    _bubble_marker_areas,
    _output_record,
    _projection_line_widths,
    _refuse_existing_outputs,
    _save_figure_atomic,
)
from .utils import sha256_file


BAND_COLOR = "#7f1d1d"
BACKGROUND_BAND_COLOR = "#aeb3b8"
PROJECTION_COLORS = (
    "#d62728",
    "#1464f4",
    "#159447",
    "#ff7f0e",
    "#9467bd",
    "#17becf",
)


def _finite(value: str, context: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context}: nonnumeric value") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{context}: non-finite value")
    return parsed


def _integer(value: str, context: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{context}: noninteger index") from exc
    if parsed < 1:
        raise ValueError(f"{context}: index must be positive")
    return parsed


def _load_bands(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"bands table is missing: {path}")
    groups: dict[tuple[str, int], list[tuple[int, float, float]]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"k_index", "k_distance", "band_index", "energy_relative_ev"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path.name}: normalized bands table is missing {sorted(required)}")
        for row_number, row in enumerate(reader, start=2):
            spin = (row.get("spin") or "none").strip() or "none"
            band_index = _integer(row["band_index"], f"{path.name}:{row_number}:band_index")
            groups.setdefault((spin, band_index), []).append(
                (
                    _integer(row["k_index"], f"{path.name}:{row_number}:k_index"),
                    _finite(row["k_distance"], f"{path.name}:{row_number}:k_distance"),
                    _finite(row["energy_relative_ev"], f"{path.name}:{row_number}:energy_relative_ev"),
                )
            )
    if not groups:
        raise ValueError(f"{path.name}: normalized bands table has no rows")

    ordered: dict[tuple[str, int], list[tuple[int, float, float]]] = {}
    reference_indices: list[int] | None = None
    reference_path: list[float] | None = None
    for key in sorted(groups):
        records = sorted(groups[key])
        indices = [item[0] for item in records]
        path_values = [item[1] for item in records]
        if len(set(indices)) != len(indices):
            raise ValueError(f"{path.name}: duplicate k index in band {key}")
        if any(right < left for left, right in zip(path_values, path_values[1:])):
            raise ValueError(f"{path.name}: k path is not monotonic in band {key}")
        if reference_indices is None:
            reference_indices = indices
            reference_path = path_values
        elif indices != reference_indices or any(
            abs(left - right) > 1.0e-8 for left, right in zip(path_values, reference_path or [])
        ):
            raise ValueError(f"{path.name}: normalized bands do not share one aligned k path")
        ordered[key] = records
    assert reference_indices is not None and reference_path is not None
    if len(reference_path) < 2 or reference_path[-1] <= reference_path[0]:
        raise ValueError(f"{path.name}: bands require a nonzero k-path interval")
    return {
        "path": path,
        "k_indices": reference_indices,
        "kpoints": reference_path,
        "groups": ordered,
        "spins": sorted({key[0] for key in ordered}),
        "band_count": len(ordered),
    }


def _load_projection(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"projection table is missing: {path}")
    records: dict[tuple[int, int], tuple[float, float, float]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "k_index",
            "k_distance",
            "band_index",
            "energy_relative_ev",
            "projection_weight",
        }
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path.name}: normalized projection table is missing {sorted(required)}")
        for row_number, row in enumerate(reader, start=2):
            k_index = _integer(row["k_index"], f"{path.name}:{row_number}:k_index")
            band_index = _integer(row["band_index"], f"{path.name}:{row_number}:band_index")
            key = (band_index, k_index)
            if key in records:
                raise ValueError(f"{path.name}: duplicate projection row {key}")
            weight = _finite(row["projection_weight"], f"{path.name}:{row_number}:projection_weight")
            if weight < 0.0:
                raise ValueError(f"{path.name}:{row_number}: projection weight must be nonnegative")
            records[key] = (
                _finite(row["k_distance"], f"{path.name}:{row_number}:k_distance"),
                _finite(row["energy_relative_ev"], f"{path.name}:{row_number}:energy_relative_ev"),
                weight,
            )
    if not records:
        raise ValueError(f"{path.name}: normalized projection table has no rows")
    return {"path": path, "records": records, "weight_max": max(item[2] for item in records.values())}


def _symmetry_points(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    path = path.resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read bands plot metadata: {path}") from exc
    points = payload.get("high_symmetry_points", [])
    if not isinstance(points, list):
        raise ValueError(f"{path.name}: high_symmetry_points must be a list")
    result = []
    for index, point in enumerate(points, start=1):
        if not isinstance(point, dict) or not str(point.get("label", "")).strip():
            raise ValueError(f"{path.name}: malformed high-symmetry point {index}")
        result.append(
            {
                "label": str(point["label"]).strip(),
                "k_distance": _finite(str(point.get("k_distance")), f"{path.name}:point-{index}"),
            }
        )
    return result


def _tick_label(label: str) -> str:
    return r"$\Gamma$" if label.strip().upper() in {"G", "GAMMA", "Γ"} else label


def _style_band_axis(
    axis: Any,
    kpoints: list[float],
    symmetry_points: list[dict[str, Any]],
    energy_window_ev: tuple[float, float] | None,
) -> None:
    axis.axhline(0.0, color="black", linestyle="--", linewidth=0.9, zorder=0)
    if symmetry_points:
        for point in symmetry_points:
            axis.axvline(point["k_distance"], color="#9c9c9c", linestyle="--", linewidth=0.5, zorder=0)
        axis.set_xticks(
            [point["k_distance"] for point in symmetry_points],
            [_tick_label(point["label"]) for point in symmetry_points],
        )
    axis.set_xlim(kpoints[0], kpoints[-1])
    axis.margins(x=0)
    if energy_window_ev is not None:
        if energy_window_ev[0] >= energy_window_ev[1]:
            raise ValueError("energy window must be increasing")
        axis.set_ylim(*energy_window_ev)
    axis.set_ylabel(r"Energy - $E_\mathrm{ref}$ (eV)")
    axis.tick_params(axis="y", direction="in", length=4, width=1.2)
    axis.tick_params(axis="x", length=0)
    for spine in axis.spines.values():
        spine.set_linewidth(1.2)


def _draw_plain(axis: Any, bands: dict[str, Any], color: str = BAND_COLOR, linewidth: float = 0.9) -> None:
    for records in bands["groups"].values():
        axis.plot(
            [item[1] for item in records],
            [item[2] for item in records],
            color=color,
            linewidth=linewidth,
            zorder=1,
        )


def _aligned_projection_weights(bands: dict[str, Any], projection: dict[str, Any]) -> dict[int, list[float]]:
    if len(bands["spins"]) != 1:
        raise ValueError("projection panels require a single-spin normalized bands table")
    aligned: dict[int, list[float]] = {}
    expected: set[tuple[int, int]] = set()
    for (_, band_index), records in bands["groups"].items():
        values = []
        for k_index, k_distance, energy in records:
            key = (band_index, k_index)
            expected.add(key)
            if key not in projection["records"]:
                raise ValueError(f"{projection['path'].name}: projection rows do not align with bands")
            projected_distance, projected_energy, weight = projection["records"][key]
            if abs(projected_distance - k_distance) > 1.0e-8 or abs(projected_energy - energy) > 1.0e-6:
                raise ValueError(f"{projection['path'].name}: projection coordinates or energies do not align with bands")
            values.append(weight)
        aligned[band_index] = values
    if set(projection["records"]) != expected:
        raise ValueError(f"{projection['path'].name}: projection contains rows outside the bands table")
    return aligned


def _draw_projection(
    axis: Any,
    bands: dict[str, Any],
    weights: dict[int, list[float]],
    color: str,
    render_mode: str,
    marker_scale: float,
) -> None:
    import numpy as np
    from matplotlib.collections import LineCollection
    from matplotlib.colors import to_rgba

    for (_, band_index), records in bands["groups"].items():
        x = np.asarray([item[1] for item in records], dtype=float)
        energy = np.asarray([item[2] for item in records], dtype=float)
        weight = np.asarray(weights[band_index], dtype=float)
        if render_mode == "bubble":
            areas = np.asarray(_bubble_marker_areas(weight.tolist(), marker_scale), dtype=float)
            mask = areas > 0.0
            axis.scatter(
                x[mask],
                energy[mask],
                s=areas[mask],
                facecolors=[to_rgba(color, 0.46)],
                edgecolors=[to_rgba(color, 0.90)],
                linewidths=0.55,
                zorder=2,
            )
        else:
            points = np.column_stack((x, energy))
            segments = np.stack((points[:-1], points[1:]), axis=1)
            segment_weights = 0.5 * (weight[:-1] + weight[1:])
            axis.add_collection(
                LineCollection(
                    segments,
                    colors=color,
                    linewidths=_projection_line_widths(
                        segment_weights.tolist(), marker_scale
                    ),
                    alpha=0.92,
                    zorder=2,
                )
            )


def plot_band_comparison(
    series: list[tuple[str, Path]],
    output: Path,
    *,
    metadata_paths: dict[str, Path] | None = None,
    layout: str = "row",
    energy_window_ev: tuple[float, float] | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    if len(series) < 2:
        raise ValueError("band comparison requires at least two labeled normalized tables")
    if layout not in {"row", "column"}:
        raise ValueError("band comparison layout must be row or column")
    labels = [label.strip() for label, _ in series]
    if any(not label for label in labels) or len(set(labels)) != len(labels):
        raise ValueError("band comparison labels must be nonempty and unique")
    output = output.resolve()
    _refuse_existing_outputs((output,), overwrite)
    loaded = [(label, _load_bands(path)) for label, path in series]
    points = {
        label: _symmetry_points((metadata_paths or {}).get(label))
        for label, _ in loaded
    }

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    nrows, ncols = ((1, len(loaded)) if layout == "row" else (len(loaded), 1))
    with plt.style.context(str(style)):
        figure, axes = plt.subplots(
            nrows,
            ncols,
            figsize=((6.1 * ncols), (5.2 * nrows)),
            squeeze=False,
            constrained_layout=True,
        )
        for axis, (label, bands) in zip(axes.flat, loaded):
            _draw_plain(axis, bands)
            _style_band_axis(axis, bands["kpoints"], points[label], energy_window_ev)
            axis.set_title(label)
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {
        "schema_version": "1.0",
        "plot_type": "bands-comparison",
        "layout": layout,
        "band_color": BAND_COLOR,
        "energy_window_ev": list(energy_window_ev) if energy_window_ev is not None else None,
        "series": [
            {
                "label": label,
                "source": {"label": bands["path"].name, "sha256": sha256_file(bands["path"])},
                "bands": bands["band_count"],
                "spin_channels": bands["spins"],
                "x_limits": [bands["kpoints"][0], bands["kpoints"][-1]],
                "high_symmetry_points": points[label],
            }
            for label, bands in loaded
        ],
        "limitations": [
            "Panels provide a visual comparison only; k-path and energy-reference comparability must be established from the source datasets.",
        ],
        "output": _output_record(output, "bands-comparison-figure", "image/png"),
    }


def plot_projection_panels(
    bands_table: Path,
    projections: list[tuple[str, Path]],
    panels_output: Path,
    *,
    overview_output: Path | None = None,
    bands_metadata_path: Path | None = None,
    energy_window_ev: tuple[float, float] | None = None,
    render_mode: str = "line-width",
    marker_scale: float = 8.0,
    bands_label: str = "Bands",
    overwrite: bool = False,
) -> dict[str, Any]:
    if not projections:
        raise ValueError("projection panels require at least one labeled projection table")
    if render_mode not in {"line-width", "bubble"}:
        raise ValueError("projection render mode must be line-width or bubble")
    if marker_scale <= 0.0:
        raise ValueError("projection marker scale must be positive")
    bands_label = bands_label.strip()
    if not bands_label:
        raise ValueError("bands label must be nonempty")
    labels = [label.strip() for label, _ in projections]
    if any(not label for label in labels) or len(set(labels)) != len(labels):
        raise ValueError("projection labels must be nonempty and unique")
    panels_output = panels_output.resolve()
    overview_output = overview_output.resolve() if overview_output is not None else None
    _refuse_existing_outputs(
        (panels_output, *(() if overview_output is None else (overview_output,))),
        overwrite,
    )
    bands = _load_bands(bands_table)
    symmetry = _symmetry_points(bands_metadata_path)
    loaded = []
    for index, (label, path) in enumerate(projections):
        projection = _load_projection(path)
        loaded.append(
            {
                "label": label,
                "projection": projection,
                "weights": _aligned_projection_weights(bands, projection),
                "color": PROJECTION_COLORS[index % len(PROJECTION_COLORS)],
            }
        )

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    with plt.style.context(str(style)):
        figure, axes = plt.subplots(
            1,
            len(loaded),
            figsize=(6.1 * len(loaded), 5.2),
            squeeze=False,
            constrained_layout=True,
        )
        for axis, item in zip(axes.flat, loaded):
            _draw_plain(axis, bands, color=BACKGROUND_BAND_COLOR, linewidth=0.65)
            _draw_projection(axis, bands, item["weights"], item["color"], render_mode, marker_scale)
            _style_band_axis(axis, bands["kpoints"], symmetry, energy_window_ev)
            axis.set_title(item["label"])
            axis.legend(
                handles=[
                    Line2D(
                        [0],
                        [0],
                        color=BACKGROUND_BAND_COLOR,
                        linewidth=1.2,
                        label=bands_label,
                    ),
                    Line2D(
                        [0],
                        [0],
                        color=item["color"],
                        marker="o" if render_mode == "bubble" else None,
                        linestyle="None" if render_mode == "bubble" else "-",
                        linewidth=2.4,
                        markersize=7,
                        label=item["label"],
                    )
                ],
                loc="upper right",
                frameon=True,
                fancybox=True,
                framealpha=0.55,
                edgecolor="#999999",
            )
        _save_figure_atomic(figure, panels_output)
        plt.close(figure)

        if overview_output is not None:
            figure, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), constrained_layout=True)
            _draw_plain(axes[0], bands)
            _style_band_axis(axes[0], bands["kpoints"], symmetry, energy_window_ev)
            axes[0].set_title("Band structure")
            _draw_plain(axes[1], bands, color=BACKGROUND_BAND_COLOR, linewidth=0.65)
            for item in loaded:
                _draw_projection(axes[1], bands, item["weights"], item["color"], render_mode, marker_scale)
            _style_band_axis(axes[1], bands["kpoints"], symmetry, energy_window_ev)
            axes[1].set_title("Projection overview")
            axes[1].legend(
                handles=[
                    Line2D(
                        [0],
                        [0],
                        color=BACKGROUND_BAND_COLOR,
                        linewidth=1.2,
                        label=bands_label,
                    ),
                    *[
                        Line2D(
                            [0],
                            [0],
                            color=item["color"],
                            marker="o" if render_mode == "bubble" else None,
                            linestyle="None" if render_mode == "bubble" else "-",
                            linewidth=2.4,
                            markersize=7,
                            label=item["label"],
                        )
                        for item in loaded
                    ],
                ],
                loc="upper right",
                frameon=True,
                fancybox=True,
                framealpha=0.55,
                edgecolor="#999999",
            )
            _save_figure_atomic(figure, overview_output)
            plt.close(figure)

    return {
        "schema_version": "1.0",
        "plot_type": "projected-bands-panels",
        "primary_representation": "separated-projection-panels",
        "overview_role": "optional-overlap-summary" if overview_output is not None else None,
        "render_mode": render_mode,
        "weight_encoding": (
            "line width on separate channel panels" if render_mode == "line-width" else "bubble area on separate channel panels"
        ),
        "background_band_color": BACKGROUND_BAND_COLOR,
        "background_label": bands_label,
        "plain_band_color": BAND_COLOR,
        "marker_scale": marker_scale,
        "legend_labels": [bands_label, *[item["label"] for item in loaded]],
        "panel_legend_labels": {
            item["label"]: [bands_label, item["label"]]
            for item in loaded
        },
        "bubble_area_mapping": (
            "marker_area_pt2 = marker_scale^2 * projection_weight"
            if render_mode == "bubble"
            else None
        ),
        "bubble_style": (
            {
                "fill_alpha": 0.46,
                "edge_alpha": 0.90,
                "edge_width_pt": 0.55,
            }
            if render_mode == "bubble"
            else None
        ),
        "line_width_mapping": (
            "line_width_pt = marker_scale * 0.45 * projection_weight"
            if render_mode == "line-width"
            else None
        ),
        "x_limits": [bands["kpoints"][0], bands["kpoints"][-1]],
        "energy_window_ev": list(energy_window_ev) if energy_window_ev is not None else None,
        "high_symmetry_points": symmetry,
        "bands_source": {"label": bands["path"].name, "sha256": sha256_file(bands["path"])},
        "projections": [
            {
                "label": item["label"],
                "color": item["color"],
                "weight_range": [0.0, item["projection"]["weight_max"]],
                "source": {
                    "label": item["projection"]["path"].name,
                    "sha256": sha256_file(item["projection"]["path"]),
                },
            }
            for item in loaded
        ],
        "limitations": [
            "Projection panels visualize caller-selected normalized weights and do not assign physical character or dominance.",
            "The optional overview can obscure overlapping channels; separated panels are the primary representation.",
        ],
        "outputs": [
            _output_record(panels_output, "separated-projection-panels", "image/png"),
            *(
                []
                if overview_output is None
                else [_output_record(overview_output, "projection-overview", "image/png")]
            ),
        ],
    }
