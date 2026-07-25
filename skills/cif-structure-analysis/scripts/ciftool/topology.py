from __future__ import annotations

from collections import defaultdict, deque
import math
from typing import Any


def _canonical_edge(
    i: int, j: int, shift: tuple[int, int, int]
) -> tuple[int, int, int, int, int]:
    forward = (i, j, *shift)
    reverse = (j, i, *(-value for value in shift))
    return min(forward, reverse)


def _periodic_edges(atoms: Any, scale: float) -> list[tuple[int, int, tuple[int, int, int]]]:
    from ase.neighborlist import natural_cutoffs, neighbor_list

    if not len(atoms):
        return []
    cutoffs = natural_cutoffs(atoms, mult=scale)
    i_values, j_values, shifts = neighbor_list(
        "ijS", atoms, cutoffs, self_interaction=False
    )
    edges: dict[
        tuple[int, int, int, int, int],
        tuple[int, int, tuple[int, int, int]],
    ] = {}
    for i, j, shift in zip(i_values, j_values, shifts):
        integer_shift = tuple(int(value) for value in shift)
        key = _canonical_edge(int(i), int(j), integer_shift)
        if key[:2] == (int(i), int(j)):
            record = (int(i), int(j), integer_shift)
        else:
            record = (int(j), int(i), tuple(-value for value in integer_shift))
        edges.setdefault(key, record)
    return [edges[key] for key in sorted(edges)]


def _components(
    atoms: Any,
    edges: list[tuple[int, int, tuple[int, int, int]]],
) -> list[dict[str, Any]]:
    import numpy as np

    adjacency: dict[int, list[tuple[int, tuple[int, int, int]]]] = defaultdict(list)
    for i, j, shift in edges:
        adjacency[i].append((j, shift))
        adjacency[j].append((i, tuple(-value for value in shift)))

    symbols = atoms.get_chemical_symbols()
    unseen = set(range(len(atoms)))
    results: list[dict[str, Any]] = []
    while unseen:
        root = min(unseen)
        offsets: dict[int, tuple[int, int, int]] = {root: (0, 0, 0)}
        queue: deque[int] = deque([root])
        component: set[int] = set()
        cycles: set[tuple[int, int, int]] = set()
        while queue:
            current = queue.popleft()
            if current in component:
                continue
            component.add(current)
            unseen.discard(current)
            current_offset = offsets[current]
            for neighbor, shift in adjacency.get(current, []):
                proposed = tuple(
                    current_offset[index] + shift[index] for index in range(3)
                )
                if neighbor not in offsets:
                    offsets[neighbor] = proposed
                    queue.append(neighbor)
                else:
                    cycle = tuple(
                        proposed[index] - offsets[neighbor][index]
                        for index in range(3)
                    )
                    if any(cycle):
                        canonical = min(cycle, tuple(-value for value in cycle))
                        cycles.add(canonical)
        rank = (
            int(np.linalg.matrix_rank(np.asarray(sorted(cycles), dtype=float), tol=1e-8))
            if cycles
            else 0
        )
        results.append(
            {
                "component_index": len(results),
                "atom_indices": sorted(component),
                "atom_count": len(component),
                "elements": sorted({symbols[index] for index in component}),
                "translation_rank": rank,
                "dimensionality": f"{rank}D",
                "independent_translation_candidates": [
                    list(vector) for vector in sorted(cycles)
                ][:12],
                "translation_candidate_limit": 12,
            }
        )
    return results


def analyze_connectivity(
    atoms: Any,
    scale_factors: list[float],
) -> dict[str, Any]:
    if not scale_factors or any(
        not math.isfinite(float(value)) or float(value) <= 0
        for value in scale_factors
    ):
        raise ValueError("topology scale factors must be positive finite values")
    scales = []
    signatures = []
    for scale in sorted(set(float(value) for value in scale_factors)):
        edges = _periodic_edges(atoms, scale)
        components = _components(atoms, edges)
        signature = tuple(
            sorted((item["translation_rank"], item["atom_count"]) for item in components)
        )
        signatures.append(signature)
        scales.append(
            {
                "covalent_radius_scale": round(scale, 6),
                "periodic_edge_count": len(edges),
                "component_count": len(components),
                "components": components,
            }
        )
    stable = len(set(signatures)) == 1
    ranks = sorted(
        {
            item["translation_rank"]
            for scale in scales
            for item in scale["components"]
        }
    )
    if not stable:
        candidate = "SENSITIVE"
    elif len(ranks) == 1:
        candidate = f"{ranks[0]}D"
    else:
        candidate = "MIXED"
    return {
        "method": "ase-natural-covalent-radii-periodic-graph",
        "method_version": "translation-rank-v1",
        "scale_factors": [round(float(value), 6) for value in sorted(set(scale_factors))],
        "stable_across_scales": stable,
        "dimensionality_candidate": candidate,
        "scales": scales,
        "claim_boundary": (
            "Dimensionality is a covalent-radius graph candidate. Sensitivity to scale, "
            "ionic, metallic, molecular, or weak interlayer bonding can change the graph; "
            "the result is not a bonding-energy or exfoliation claim."
        ),
    }
