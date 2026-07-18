from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable

from .electronic import _output_record, _refuse_existing_outputs, _save_figure_atomic
from .utils import sha256_file, write_json_atomic


BOUNDARY_TOLERANCE = 1.0e-6
CELL_COLOR = "#666666"
BOND_OUTLINE_COLOR = "#707070"
DISPLAY_RADIUS_SCALE = 0.55


def _normalized(vector: Any, context: str) -> Any:
    import numpy as np

    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 1.0e-12:
        raise ValueError(f"cannot construct {context} projection basis")
    return np.asarray(vector, dtype=float) / norm


def _view_basis(cell: Any, view: str) -> tuple[Any, Any, Any]:
    import numpy as np

    first = np.asarray(cell[0], dtype=float)
    second = np.asarray(cell[1] if view == "top" else cell[2], dtype=float)
    screen_x = _normalized(first, f"{view} x")
    screen_y = _normalized(second - np.dot(second, screen_x) * screen_x, f"{view} y")
    depth = _normalized(np.cross(screen_x, screen_y), f"{view} depth")
    return screen_x, screen_y, depth


def _project(position: Any, basis: tuple[Any, Any, Any]) -> Any:
    import numpy as np

    return np.asarray([float(np.dot(position, axis)) for axis in basis], dtype=float)


def _boundary_sites(atoms: Any) -> list[dict[str, Any]]:
    import numpy as np

    scaled = atoms.get_scaled_positions(wrap=True)
    scaled[np.isclose(scaled, 1.0, atol=BOUNDARY_TOLERANCE)] = 0.0
    scaled[np.isclose(scaled, 0.0, atol=BOUNDARY_TOLERANCE)] = 0.0
    sites = []
    seen: set[tuple[Any, ...]] = set()
    for atom_index, (symbol, fractional) in enumerate(zip(atoms.get_chemical_symbols(), scaled)):
        choices = [(0.0, 1.0) if value == 0.0 else (float(value),) for value in fractional]
        for x in choices[0]:
            for y in choices[1]:
                for z in choices[2]:
                    image = np.asarray([x, y, z], dtype=float)
                    key = (atom_index, *np.round(image, 9))
                    if key in seen:
                        continue
                    seen.add(key)
                    sites.append(
                        {
                            "atom_index": atom_index,
                            "symbol": symbol,
                            "fractional": image,
                            "cartesian": image @ atoms.cell.array,
                        }
                    )
    return sites


def _pair_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _normalize_explicit_limits(
    limits: dict[Iterable[str], float] | None,
) -> dict[tuple[str, str], float]:
    result: dict[tuple[str, str], float] = {}
    for raw_key, raw_value in (limits or {}).items():
        symbols = sorted(str(value).strip() for value in raw_key if str(value).strip())
        if len(symbols) == 1:
            symbols = [symbols[0], symbols[0]]
        if len(symbols) != 2:
            raise ValueError("explicit graphical-connection keys must name one or two elements")
        value = float(raw_value)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError("explicit graphical-connection limits must be finite and positive")
        key = _pair_key(*symbols)
        if key in result:
            raise ValueError(f"duplicate explicit graphical-connection limit: {key}")
        result[key] = value
    return result


def _display_parameters(
    symbols: list[str],
    color_overrides: dict[str, str] | None,
    radius_overrides: dict[str, float] | None,
) -> tuple[dict[str, str], dict[str, float], dict[str, float]]:
    from ase.data import atomic_numbers, covalent_radii
    from ase.data.colors import jmol_colors
    from matplotlib.colors import to_hex, to_rgb

    colors: dict[str, str] = {}
    radii: dict[str, float] = {}
    covalent: dict[str, float] = {}
    for symbol in symbols:
        if symbol not in atomic_numbers:
            raise ValueError(f"unknown element symbol in structure: {symbol}")
        number = atomic_numbers[symbol]
        colors[symbol] = to_hex(jmol_colors[number], keep_alpha=False)
        covalent[symbol] = float(covalent_radii[number])
        radii[symbol] = max(0.22, DISPLAY_RADIUS_SCALE * covalent[symbol])
    for symbol, color in (color_overrides or {}).items():
        if symbol not in colors:
            raise ValueError(f"element color override does not occur in the structures: {symbol}")
        to_rgb(color)
        colors[symbol] = color
    for symbol, radius in (radius_overrides or {}).items():
        if symbol not in radii:
            raise ValueError(f"element radius override does not occur in the structures: {symbol}")
        value = float(radius)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"element radius must be finite and positive: {symbol}")
        radii[symbol] = value
    return colors, radii, covalent


def _graphical_connections(
    sites: list[dict[str, Any]],
    *,
    bond_mode: str,
    bond_scale: float,
    covalent_radii: dict[str, float],
    explicit_limits: dict[tuple[str, str], float],
) -> list[tuple[int, int]]:
    import numpy as np

    connections = []
    for left_index, left in enumerate(sites):
        for right_index in range(left_index + 1, len(sites)):
            right = sites[right_index]
            if left["atom_index"] == right["atom_index"]:
                continue
            distance = float(np.linalg.norm(left["cartesian"] - right["cartesian"]))
            if distance <= 1.0e-8:
                continue
            if bond_mode == "covalent":
                limit = bond_scale * (
                    covalent_radii[left["symbol"]] + covalent_radii[right["symbol"]]
                )
            else:
                limit = explicit_limits.get(_pair_key(left["symbol"], right["symbol"]))
            if limit is not None and distance <= limit:
                connections.append((left_index, right_index))
    return connections


def _cell_edges(cell: Any, basis: tuple[Any, Any, Any]) -> list[tuple[Any, Any]]:
    import numpy as np

    fractional = np.asarray(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 1],
            [1, 1, 1],
        ],
        dtype=float,
    )
    corners = fractional @ cell
    projected = [_project(position, basis) for position in corners]
    edges = []
    for left in range(len(corners)):
        for right in range(left + 1, len(corners)):
            if np.count_nonzero(np.abs(fractional[left] - fractional[right]) > 1.0e-8) == 1:
                edges.append((projected[left], projected[right]))
    return edges


def _lighten(color: str, amount: float) -> tuple[float, float, float]:
    import numpy as np
    from matplotlib.colors import to_rgb

    rgb = np.asarray(to_rgb(color), dtype=float)
    return tuple(rgb + (1.0 - rgb) * amount)


def _draw_connection(
    axis: Any,
    left: Any,
    right: Any,
    left_symbol: str,
    right_symbol: str,
    colors: dict[str, str],
    radii: dict[str, float],
) -> None:
    import numpy as np

    vector = right - left
    projected_length = float(np.linalg.norm(vector[:2]))
    if projected_length <= radii[left_symbol] + radii[right_symbol]:
        return
    start = radii[left_symbol] / projected_length
    stop = 1.0 - radii[right_symbol] / projected_length
    if stop <= start:
        return
    fractions = np.linspace(start, stop, 25)
    for first, second in zip(fractions[:-1], fractions[1:]):
        a = left + vector * first
        b = left + vector * second
        midpoint = 0.5 * (first + second)
        color = colors[left_symbol] if midpoint < 0.5 else colors[right_symbol]
        zorder = 10.0 + 0.1 * float(0.5 * (a[2] + b[2]))
        axis.plot(
            [a[0], b[0]],
            [a[1], b[1]],
            color=BOND_OUTLINE_COLOR,
            linewidth=3.8,
            solid_capstyle="butt",
            zorder=zorder,
        )
        axis.plot(
            [a[0], b[0]],
            [a[1], b[1]],
            color=color,
            linewidth=2.4,
            solid_capstyle="butt",
            zorder=zorder + 0.01,
        )


def _draw_view(
    axis: Any,
    atoms: Any,
    sites: list[dict[str, Any]],
    connections: list[tuple[int, int]],
    colors: dict[str, str],
    radii: dict[str, float],
    view: str,
) -> None:
    import numpy as np
    from matplotlib.patches import Circle

    basis = _view_basis(atoms.cell.array, view)
    projected = np.asarray([_project(site["cartesian"], basis) for site in sites])
    for left, right in _cell_edges(atoms.cell.array, basis):
        axis.plot(
            [left[0], right[0]],
            [left[1], right[1]],
            color=CELL_COLOR,
            linewidth=1.0,
            alpha=0.85,
            zorder=1,
        )
    for left_index, right_index in connections:
        _draw_connection(
            axis,
            projected[left_index],
            projected[right_index],
            sites[left_index]["symbol"],
            sites[right_index]["symbol"],
            colors,
            radii,
        )
    for index in np.argsort(projected[:, 2]):
        symbol = sites[index]["symbol"]
        x, y, depth = projected[index]
        radius = radii[symbol]
        zorder = 10.0 + 0.1 * float(depth)
        axis.add_patch(
            Circle(
                (x, y),
                radius,
                facecolor=colors[symbol],
                edgecolor="#303030",
                linewidth=0.8,
                zorder=zorder,
            )
        )
        axis.add_patch(
            Circle(
                (x - 0.28 * radius, y + 0.28 * radius),
                0.23 * radius,
                facecolor=_lighten(colors[symbol], 0.82),
                edgecolor="none",
                alpha=0.88,
                zorder=zorder + 0.01,
            )
        )
    edge_points = [point for edge in _cell_edges(atoms.cell.array, basis) for point in edge]
    visible = np.vstack((projected, edge_points))
    extent = max(float(np.ptp(visible[:, 0])), float(np.ptp(visible[:, 1])))
    pad = max(0.8, 0.05 * extent)
    axis.set_xlim(float(visible[:, 0].min()) - pad, float(visible[:, 0].max()) + pad)
    axis.set_ylim(float(visible[:, 1].min()) - pad, float(visible[:, 1].max()) + pad)
    axis.set_aspect("equal")
    axis.axis("off")
    axis.set_title("Top view [001]" if view == "top" else "Side view [010]", fontsize=14)


def render_structure_views(
    structure_paths: list[Path],
    output_directory: Path,
    *,
    bond_mode: str = "covalent",
    bond_scale: float = 1.15,
    explicit_bond_limits: dict[Iterable[str], float] | None = None,
    element_colors: dict[str, str] | None = None,
    element_radii_angstrom: dict[str, float] | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    if not structure_paths:
        raise ValueError("structure views require at least one structure file")
    if bond_mode not in {"none", "covalent", "explicit"}:
        raise ValueError("bond mode must be none, covalent, or explicit")
    if not math.isfinite(bond_scale) or bond_scale <= 0.0:
        raise ValueError("covalent graphical-connection scale must be finite and positive")
    explicit_limits = _normalize_explicit_limits(explicit_bond_limits)
    if bond_mode == "explicit" and not explicit_limits:
        raise ValueError("explicit bond mode requires at least one graphical-connection limit")

    try:
        import importlib.metadata
        from ase.io import read
    except ImportError as exc:
        raise RuntimeError("structure views require the optional ASE package") from exc
    ase_version = importlib.metadata.version("ase")

    resolved = [path.resolve() for path in structure_paths]
    if any(not path.is_file() for path in resolved):
        missing = [str(path) for path in resolved if not path.is_file()]
        raise ValueError(f"structure source is missing: {missing}")
    stems = [path.stem for path in resolved]
    if len(set(stems)) != len(stems):
        raise ValueError("structure source basenames must be unique within one overview")
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    figure_paths = [output_directory / f"{stem}-top-side.png" for stem in stems]
    overview_path = output_directory / "all-structures-overview.png"
    metadata_path = output_directory / "structure-views.plot.json"
    _refuse_existing_outputs((*figure_paths, overview_path, metadata_path), overwrite)

    loaded = []
    all_symbols: set[str] = set()
    for path in resolved:
        try:
            atoms = read(path)
        except Exception as exc:
            raise ValueError(f"ASE could not read structure: {path}") from exc
        if len(atoms) == 0 or abs(float(atoms.get_volume())) <= 1.0e-12:
            raise ValueError(f"{path.name}: structure must contain atoms and a nonzero cell")
        atoms.wrap()
        sites = _boundary_sites(atoms)
        all_symbols.update(atoms.get_chemical_symbols())
        loaded.append({"path": path, "atoms": atoms, "sites": sites})
    colors, radii, covalent = _display_parameters(
        sorted(all_symbols), element_colors, element_radii_angstrom
    )
    for item in loaded:
        item["connections"] = (
            []
            if bond_mode == "none"
            else _graphical_connections(
                item["sites"],
                bond_mode=bond_mode,
                bond_scale=bond_scale,
                covalent_radii=covalent,
                explicit_limits=explicit_limits,
            )
        )

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    with plt.style.context(str(style)):
        for item, output in zip(loaded, figure_paths):
            figure, axes = plt.subplots(1, 2, figsize=(13.0, 7.0), facecolor="white")
            for axis, view in zip(axes, ("top", "side")):
                _draw_view(
                    axis,
                    item["atoms"],
                    item["sites"],
                    item["connections"],
                    colors,
                    radii,
                    view,
                )
            figure.suptitle(item["path"].stem, fontsize=17, fontweight="bold")
            figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
            _save_figure_atomic(figure, output)
            plt.close(figure)

        figure, axes = plt.subplots(len(figure_paths), 1, figsize=(14.0, 7.0 * len(figure_paths)), squeeze=False)
        for axis, image_path in zip(axes.flat, figure_paths):
            axis.imshow(plt.imread(image_path))
            axis.axis("off")
        figure.tight_layout(pad=0.6)
        _save_figure_atomic(figure, overview_path)
        plt.close(figure)

    metadata = {
        "schema_version": "1.0",
        "plot_type": "structure-top-side-views",
        "reader": {"package": "ase", "version": ase_version},
        "views": ["top-[001]", "side-[010]"],
        "boundary_image_policy": "duplicate crystallographically equivalent atoms on 0/1 cell boundaries",
        "bond_mode": bond_mode,
        "graphical_connectivity_notice": "Rendered connections are visualization rules, not a bond-order or physical bonding analysis.",
        "bond_scale": bond_scale if bond_mode == "covalent" else None,
        "explicit_bond_limits_angstrom": [
            {"elements": list(key), "maximum_distance": value}
            for key, value in sorted(explicit_limits.items())
        ],
        "element_colors": colors,
        "element_radii_angstrom": radii,
        "display_radius_source": f"{DISPLAY_RADIUS_SCALE:.2f} * ASE covalent radius",
        "structures": [
            {
                "source": {
                    "label": item["path"].name,
                    "sha256": sha256_file(item["path"]),
                    "bytes": item["path"].stat().st_size,
                },
                "source_atom_count": len(item["atoms"]),
                "displayed_site_count": len(item["sites"]),
                "graphical_connection_count": len(item["connections"]),
                "elements": sorted(set(item["atoms"].get_chemical_symbols())),
                "output": _output_record(output, "structure-top-side-figure", "image/png"),
            }
            for item, output in zip(loaded, figure_paths)
        ],
        "overview": _output_record(overview_path, "structure-overview", "image/png"),
        "limitations": [
            "The renderer shows one crystallographic cell plus boundary-equivalent images and does not search for a chemically complete cluster outside it.",
            "Element colors and radii are display mappings; graphical connections must not be interpreted as calculated bond orders.",
        ],
    }
    write_json_atomic(metadata_path, metadata)
    return {
        "figures": figure_paths,
        "overview": overview_path,
        "metadata": metadata_path,
    }
