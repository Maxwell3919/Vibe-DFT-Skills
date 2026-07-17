#!/usr/bin/env python3
"""Analyze a one-dimensional convergence series without claiming physical validity."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path


def finite_float(value: str, name: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} is not numeric: {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} is not finite: {value!r}")
    return result


def load_series(path: Path, x_name: str, y_name: str) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or x_name not in reader.fieldnames or y_name not in reader.fieldnames:
            raise ValueError(f"CSV must contain columns {x_name!r} and {y_name!r}")
        rows = [
            {"x": finite_float(row[x_name], x_name), "y": finite_float(row[y_name], y_name)}
            for row in reader
        ]
    if len(rows) < 2:
        raise ValueError("At least two data rows are required")
    rows.sort(key=lambda row: row["x"])
    if len({row["x"] for row in rows}) != len(rows):
        raise ValueError("The control variable contains duplicate values")
    return rows


def analyze(
    rows: list[dict[str, float]], abs_tol: float, rel_tol: float, min_tail: int
) -> dict[str, object]:
    if abs_tol < 0 or rel_tol < 0:
        raise ValueError("Tolerances must be non-negative")
    if min_tail < 2:
        raise ValueError("--min-tail must be at least 2")
    reference = rows[-1]["y"]
    allowed = abs_tol + rel_tol * abs(reference)
    enriched: list[dict[str, float | None]] = []
    for index, row in enumerate(rows):
        previous = rows[index - 1]["y"] if index else None
        enriched.append(
            {
                "x": row["x"],
                "y": row["y"],
                "delta_previous": None if previous is None else row["y"] - previous,
                "delta_reference": row["y"] - reference,
            }
        )

    candidate = None
    for start in range(0, len(rows) - min_tail + 1):
        tail = rows[start:]
        if len(tail) >= min_tail and all(abs(row["y"] - reference) <= allowed for row in tail):
            candidate = rows[start]["x"]
            break

    adjacent = [abs(enriched[i]["delta_previous"]) for i in range(1, len(enriched))]
    direction_changes = 0
    signed = [enriched[i]["delta_previous"] for i in range(1, len(enriched))]
    nonzero = [value for value in signed if value not in (None, 0.0)]
    for first, second in zip(nonzero, nonzero[1:]):
        if first * second < 0:
            direction_changes += 1

    return {
        "status": "candidate_found" if candidate is not None else "no_stable_tail",
        "candidate_x": candidate,
        "reference": {"x": rows[-1]["x"], "y": reference},
        "criterion": {
            "absolute_tolerance": abs_tol,
            "relative_tolerance": rel_tol,
            "combined_tolerance_at_reference": allowed,
            "minimum_tail_points": min_tail,
            "rule": "all values from candidate through final reference lie within tolerance of final value",
        },
        "diagnostics": {
            "points": len(rows),
            "maximum_adjacent_change": max(adjacent),
            "direction_changes": direction_changes,
            "nonmonotonic": direction_changes > 0,
        },
        "series": enriched,
        "limitation": (
            "This numerical screen uses the final sampled value as a reference. It does not prove the "
            "reference is converged, exclude hidden state changes, or establish physical validity."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--x", required=True, help="Control-variable column")
    parser.add_argument("--y", required=True, help="Observable column")
    parser.add_argument("--abs-tol", type=float, required=True)
    parser.add_argument("--rel-tol", type=float, default=0.0)
    parser.add_argument("--min-tail", type=int, default=3)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = analyze(load_series(args.csv_path, args.x, args.y), args.abs_tol, args.rel_tol, args.min_tail)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["status"] == "candidate_found" else 1


if __name__ == "__main__":
    raise SystemExit(main())
