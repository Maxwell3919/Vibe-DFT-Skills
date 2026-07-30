from __future__ import annotations

import itertools
import math
from typing import Any


def _rounded(value: float | None) -> float | None:
    if value is None or not math.isfinite(float(value)):
        return None
    return round(float(value), 6)


def _geometry_hint(coordination: int, angles: list[float]) -> str:
    if coordination <= 1:
        return "terminal-or-isolated"
    if coordination == 2 and angles:
        return "linear-like" if abs(angles[0] - 180.0) <= 15.0 else "bent-like"
    if coordination == 3 and len(angles) == 3:
        return (
            "trigonal-planar-like"
            if max(abs(value - 120.0) for value in angles) <= 20.0
            else "three-coordinate-unclassified"
        )
    if coordination == 4 and len(angles) == 6:
        tetra_error = sum(abs(value - 109.471) for value in angles) / 6.0
        square_targets = [90.0, 90.0, 90.0, 90.0, 180.0, 180.0]
        square_error = sum(
            abs(value - target)
            for value, target in zip(sorted(angles), square_targets)
        ) / 6.0
        if tetra_error <= 18.0 and tetra_error < square_error:
            return "tetrahedral-like"
        if square_error <= 18.0:
            return "square-planar-like"
        return "four-coordinate-unclassified"
    if coordination == 6 and len(angles) == 15:
        targets = [90.0] * 12 + [180.0] * 3
        error = sum(
            abs(value - target)
            for value, target in zip(sorted(angles), targets)
        ) / 15.0
        return "octahedral-like" if error <= 18.0 else "six-coordinate-unclassified"
    return "unclassified"


def analyze_local_geometry(
    atoms: Any,
    nearest_shell_directed: list[dict[str, Any]],
) -> dict[str, Any]:
    import numpy as np

    neighbors: dict[int, list[dict[str, Any]]] = {
        index: [] for index in range(len(atoms))
    }
    for edge in nearest_shell_directed:
        i = int(edge["i"])
        j = int(edge["j"])
        vector = np.asarray(edge["vector_ang"], dtype=float)
        distance = float(edge["distance_ang"])
        shift = [int(value) for value in edge["shift"]]
        neighbors[i].append(
            {
                "index": j,
                "shift": shift,
                "distance_ang": distance,
                "vector_ang": vector,
            }
        )

    symbols = atoms.get_chemical_symbols()
    sites = []
    for index in range(len(atoms)):
        records = neighbors[index]
        distances = [float(item["distance_ang"]) for item in records]
        angles: list[float] = []
        for left, right in itertools.combinations(records, 2):
            first = np.asarray(left["vector_ang"], dtype=float)
            second = np.asarray(right["vector_ang"], dtype=float)
            denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
            if denominator <= 0:
                continue
            cosine = max(-1.0, min(1.0, float(np.dot(first, second)) / denominator))
            angles.append(math.degrees(math.acos(cosine)))
        angles.sort()
        sites.append(
            {
                "index": index,
                "symbol": symbols[index],
                "coordination": len(records),
                "bond_distance_min_ang": _rounded(min(distances)) if distances else None,
                "bond_distance_max_ang": _rounded(max(distances)) if distances else None,
                "bond_distance_mean_ang": _rounded(sum(distances) / len(distances))
                if distances
                else None,
                "bond_distance_std_ang": _rounded(float(np.std(distances)))
                if distances
                else None,
                "bond_angle_count": len(angles),
                "bond_angle_min_deg": _rounded(min(angles)) if angles else None,
                "bond_angle_max_deg": _rounded(max(angles)) if angles else None,
                "bond_angles_deg": [_rounded(value) for value in angles[:36]],
                "bond_angle_sample_limit": 36,
                "geometry_hint": _geometry_hint(len(records), angles),
            }
        )
    return {
        "method": "periodic-nearest-shell-vector-geometry",
        "method_version": "2.0-directed-center-shell",
        "site_count": len(sites),
        "sites": sites,
        "claim_boundary": (
            "Geometry hints classify the current distance-shell vectors only; "
            "they are not bond orders, oxidation states, crystal-field assignments, "
            "or energetic stability conclusions."
        ),
    }
