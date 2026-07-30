from __future__ import annotations

from collections import defaultdict
import math
from typing import Any


ROUND_DIGITS = 6


def _rounded(value: float | None) -> float | None:
    if value is None or not math.isfinite(float(value)):
        return None
    return round(float(value), ROUND_DIGITS)


def _default_cutoffs(atoms: Any, short_threshold: float) -> tuple[float, float]:
    from ase.neighborlist import natural_cutoffs

    radii = natural_cutoffs(atoms, mult=1.25) if len(atoms) else []
    initial = max(3.5, short_threshold + 0.1, 2.0 * max(radii, default=0.0))
    lengths = [
        float(length)
        for length, periodic in zip(atoms.cell.lengths(), atoms.get_pbc())
        if periodic and float(length) > 0
    ]
    positions = atoms.get_positions()
    diameter = 0.0
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            diameter = max(diameter, float(((positions[j] - positions[i]) ** 2).sum() ** 0.5))
    maximum = max(12.0, max(lengths, default=0.0) + 0.1, diameter + 0.1, initial)
    return initial, maximum


def _canonical_record(record: dict[str, Any]) -> tuple[tuple[int, ...], dict[str, Any]]:
    i = int(record["i"])
    j = int(record["j"])
    shift = tuple(int(value) for value in record["shift"])
    forward = (i, j, *shift)
    reverse_shift = tuple(-value for value in shift)
    reverse = (j, i, *reverse_shift)
    if forward <= reverse:
        return forward, record
    reversed_record = {
        **record,
        "i": j,
        "j": i,
        "symbols": [record["symbols"][1], record["symbols"][0]],
        "shift": list(reverse_shift),
        "vector_ang": [-float(value) for value in record["vector_ang"]],
    }
    return reverse, reversed_record


def _enumerate(atoms: Any, cutoff: float) -> list[dict[str, Any]]:
    from ase.neighborlist import neighbor_list

    if len(atoms) == 0:
        return []
    i_values, j_values, distances, vectors, shifts = neighbor_list(
        "ijdDS",
        atoms,
        cutoff,
        self_interaction=False,
    )
    symbols = atoms.get_chemical_symbols()
    records = []
    for i, j, distance, vector, shift in zip(
        i_values, j_values, distances, vectors, shifts
    ):
        records.append(
            {
                "i": int(i),
                "j": int(j),
                "symbols": [symbols[int(i)], symbols[int(j)]],
                "shift": [int(value) for value in shift],
                # Preserve exact backend floats for all decisions.  The
                # presentation layer rounds only after shell, threshold, and
                # bond-match comparisons are complete.
                "vector_ang": [float(value) for value in vector],
                "distance_ang": float(distance),
            }
        )
    return sorted(
        records,
        key=lambda item: (
            float(item["distance_ang"]),
            int(item["i"]),
            int(item["j"]),
            tuple(item["shift"]),
        ),
    )


def analyze_periodic_neighbors(
    atoms: Any,
    short_threshold: float,
    requested_cutoff: float | None = None,
    maximum_cutoff: float | None = None,
    shell_tolerance: float = 0.05,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    default_initial, default_maximum = _default_cutoffs(atoms, short_threshold)
    cutoff = float(requested_cutoff) if requested_cutoff is not None else default_initial
    limit = float(maximum_cutoff) if maximum_cutoff is not None else default_maximum
    if limit < cutoff:
        raise ValueError("maximum neighbor cutoff must be greater than or equal to the initial cutoff")

    directed: list[dict[str, Any]] = []
    atoms_without_neighbors = list(range(len(atoms)))
    while True:
        directed = _enumerate(atoms, cutoff)
        centers = {int(record["i"]) for record in directed}
        atoms_without_neighbors = [index for index in range(len(atoms)) if index not in centers]
        if not atoms_without_neighbors or requested_cutoff is not None or cutoff >= limit:
            break
        cutoff = min(limit, max(cutoff * 2.0, cutoff + 1.0))

    grouped: dict[tuple[int, ...], list[dict[str, Any]]] = defaultdict(list)
    canonical: dict[tuple[int, ...], dict[str, Any]] = {}
    for record in directed:
        key, normalized = _canonical_record(record)
        grouped[key].append(record)
        canonical.setdefault(key, normalized)

    unique_records = []
    for key, record in canonical.items():
        unique_records.append(
            {
                **record,
                "directed_multiplicity": len(grouped[key]),
                "periodic_edge_key": [int(value) for value in key],
            }
        )
    unique_records.sort(
        key=lambda item: (
            float(item["distance_ang"]),
            int(item["i"]),
            int(item["j"]),
            tuple(item["shift"]),
        )
    )

    nearest_by_atom: dict[int, float] = {}
    for record in directed:
        index = int(record["i"])
        distance = float(record["distance_ang"])
        nearest_by_atom[index] = min(distance, nearest_by_atom.get(index, distance))

    nearest_directed = [
        record
        for record in directed
        if float(record["distance_ang"])
        <= nearest_by_atom[int(record["i"])] + shell_tolerance
    ]
    nearest_keys = {_canonical_record(record)[0] for record in nearest_directed}
    nearest_pairs = [
        record for record in unique_records if tuple(record["periodic_edge_key"]) in nearest_keys
    ]

    coordination_counts = {index: 0 for index in range(len(atoms))}
    for record in nearest_directed:
        coordination_counts[int(record["i"])] += 1
    symbols = atoms.get_chemical_symbols()
    coordination = [
        {
            "index": index,
            "symbol": symbols[index],
            "nearest_distance_ang": _rounded(nearest_by_atom.get(index)),
            "nearest_shell_coordination": coordination_counts[index],
        }
        for index in range(len(atoms))
    ]

    short_flags = [
        {
            "i": record["i"],
            "j": record["j"],
            "symbols": record["symbols"],
            "shift": record["shift"],
            "distance_ang": record["distance_ang"],
            "threshold_ang": _rounded(short_threshold),
        }
        for record in unique_records
        if float(record["distance_ang"]) < short_threshold
    ]
    distances = [float(record["distance_ang"]) for record in unique_records]
    complete = not atoms_without_neighbors or (len(atoms) <= 1 and not any(atoms.get_pbc()))
    summary = {
        "method": "ase.neighborlist.neighbor_list",
        "method_version": "periodic-images-v2-full-precision-decisions",
        "neighbor_cutoff_ang": _rounded(cutoff),
        "maximum_neighbor_cutoff_ang": _rounded(limit),
        "cutoff_was_user_supplied": requested_cutoff is not None,
        "neighbor_search_complete": complete,
        "atoms_without_neighbors": atoms_without_neighbors,
        "min_distance_ang": _rounded(min(distances)) if distances else None,
        "max_distance_within_cutoff_ang": _rounded(max(distances)) if distances else None,
        "pair_count": len(unique_records),
        "directed_neighbor_count": len(directed),
        "periodic_edge_count": len(unique_records),
        "nearest_pairs_sample": unique_records[:50],
        "nearest_pairs_sample_limit": 50,
        "nearest_neighbor_bond_pairs": nearest_pairs,
        "nearest_neighbor_bond_count": len(nearest_pairs),
        "nearest_neighbor_bond_tolerance_ang": _rounded(shell_tolerance),
        "nearest_neighbor_bond_rule": "per-center nearest periodic-image shell within tolerance",
        "coordination_by_atom": coordination,
        "uses_minimum_image": False,
        "periodic_images_enumerated": True,
        "self_image_neighbors_enumerated": True,
        "canonicalization": "undirected edge (i,j,S) is equivalent to (j,i,-S)",
    }
    return summary, short_flags, nearest_directed


def match_neighbor_bonds(
    nearest_neighbor_pairs: list[dict[str, Any]],
    element_pair: tuple[str, str] | None,
    target_distance: float | None,
    tolerance: float,
) -> dict[str, Any]:
    requested = element_pair is not None or target_distance is not None
    query = {
        "element_pair": list(element_pair) if element_pair else None,
        "target_distance_ang": _rounded(target_distance),
        "tolerance_ang": _rounded(tolerance),
    }
    common = {
        "query": query,
        "scope": "periodic_nearest_neighbor_bond_pairs",
        "matching_rule": (
            "unordered element-pair equality and absolute distance difference within tolerance; "
            "when target distance is omitted, match only by element pair"
        ),
        "periodic_scope": (
            "unique undirected periodic edges carrying cell shift S; (i,j,S) and (j,i,-S) "
            "are one edge, while distinct periodic images remain distinct candidates"
        ),
    }
    if not requested:
        return {
            "status": "NOT_REQUESTED",
            **common,
            "candidate_count": 0,
            "match_count": 0,
            "matches": [],
            "closest_candidate": None,
        }

    candidates = []
    for record in nearest_neighbor_pairs:
        if element_pair and tuple(sorted(str(symbol) for symbol in record["symbols"])) != element_pair:
            continue
        distance = float(record["distance_ang"])
        delta = abs(distance - target_distance) if target_distance is not None else None
        candidates.append({**record, "absolute_delta_ang": delta})

    candidates.sort(
        key=lambda item: (
            float(item["absolute_delta_ang"]) if item["absolute_delta_ang"] is not None else 0.0,
            float(item["distance_ang"]),
            int(item["i"]),
            int(item["j"]),
            tuple(item.get("shift", [0, 0, 0])),
        )
    )
    if target_distance is None:
        matches = list(candidates)
        closest = None
    else:
        matches = [
            item for item in candidates if float(item["absolute_delta_ang"]) <= tolerance
        ]
        closest = candidates[0] if candidates else None

    return {
        "status": "MATCHED" if matches else "NO_MATCH",
        **common,
        "candidate_count": len(candidates),
        "match_count": len(matches),
        "matches": matches,
        "closest_candidate": closest,
    }
