from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from .utils import sha256_file, utc_now


def _load_rows(path: Path, x_column: str, y_column: str, group_column: str | None) -> dict[str, list[tuple[float, float]]]:
    groups: dict[str, list[tuple[float, float]]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {x_column, y_column}.union({group_column} if group_column else set())
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing CSV columns: {sorted(missing)}")
        for row_number, row in enumerate(reader, start=2):
            try:
                x = float(row[x_column])
                y = float(row[y_column])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"row {row_number} contains non-numeric x/y data") from exc
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError(f"row {row_number} contains non-finite x/y data")
            group = row[group_column] if group_column else "series"
            groups.setdefault(group, []).append((x, y))
    if not groups:
        raise ValueError("CSV contains no data rows")
    return groups


def plot_table(
    input_path: Path,
    output_path: Path,
    x_column: str,
    y_column: str,
    group_column: str | None,
    xlabel: str,
    ylabel: str,
    title: str | None,
    style_path: Path,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    groups = _load_rows(input_path, x_column, y_column, group_column)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with plt.style.context(str(style_path)):
        figure, axis = plt.subplots()
        for label, points in sorted(groups.items()):
            axis.plot([item[0] for item in points], [item[1] for item in points], label=label)
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)
        if title:
            axis.set_title(title)
        all_x = [point[0] for points in groups.values() for point in points]
        if min(all_x) < max(all_x):
            axis.set_xlim(min(all_x), max(all_x))
        axis.margins(x=0)
        if group_column or len(groups) > 1:
            axis.legend()
        figure.savefig(output_path)
        plt.close(figure)
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"plot was not created: {output_path}")
    return {
        "schema_version": "1.0",
        "generated_utc": utc_now(),
        "input": {"path": input_path.name, "sha256": sha256_file(input_path), "bytes": input_path.stat().st_size},
        "columns": {"x": x_column, "y": y_column, "group": group_column},
        "labels": {"x": xlabel, "y": ylabel, "title": title},
        "groups": {label: len(points) for label, points in sorted(groups.items())},
        "output": {"path": output_path.name, "sha256": sha256_file(output_path), "bytes": output_path.stat().st_size},
        "style": style_path.name,
    }
