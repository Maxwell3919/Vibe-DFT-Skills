from __future__ import annotations

import math
from pathlib import Path
import tempfile
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
    parse_qe_fermi_energy,
)
from .registry import resolve_backend_maturity
from .utils import utc_now, write_json_atomic


BOHR_TO_ANGSTROM = 0.529177210903
FIELD_KINDS = {
    "charge-density",
    "charge-density-difference",
    "electron-localization",
    "electrostatic-potential",
    "other",
}

ELEMENT_SYMBOLS = (
    "X", "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr",
    "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra",
    "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db",
    "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
)


def _element_symbol(atomic_number: int) -> str:
    return ELEMENT_SYMBOLS[atomic_number] if 0 < atomic_number < len(ELEMENT_SYMBOLS) else f"Z{atomic_number}"


def _finite_array(values: Any, label: str) -> Any:
    import numpy as np

    array = np.asarray(values, dtype=float)
    if array.ndim != 3 or min(array.shape) < 1:
        raise ValueError(f"{label}: expected a nonempty three-dimensional grid")
    if not np.isfinite(array).all():
        raise ValueError(f"{label}: grid contains non-finite values")
    return array


def _read_cube_payload(path: Path) -> tuple[Any, list[int], dict[str, Any]]:
    import numpy as np

    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError(f"cube source file is missing: {path}")
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        comments = [handle.readline().rstrip("\n"), handle.readline().rstrip("\n")]
        atom_line = handle.readline().split()
        if len(atom_line) < 4:
            raise ValueError(f"{path.name}: malformed cube atom/origin row")
        atom_count_raw = int(atom_line[0])
        atom_count = abs(atom_count_raw)
        origin = [float(value) for value in atom_line[1:4]]
        dimensions: list[int] = []
        vectors: list[list[float]] = []
        axis_units: list[str] = []
        for _ in range(3):
            fields = handle.readline().split()
            if len(fields) < 4:
                raise ValueError(f"{path.name}: malformed cube axis row")
            signed_count = int(fields[0])
            if signed_count == 0:
                raise ValueError(f"{path.name}: cube axis count cannot be zero")
            dimensions.append(abs(signed_count))
            vectors.append([float(value) for value in fields[1:4]])
            axis_units.append("angstrom" if signed_count < 0 else "bohr")
        if len(set(axis_units)) != 1:
            raise ValueError(f"{path.name}: mixed cube coordinate-unit signs are unsupported")
        atoms = []
        for atom_index in range(atom_count):
            fields = handle.readline().split()
            if len(fields) < 5:
                raise ValueError(f"{path.name}: malformed cube atom row {atom_index + 1}")
            atoms.append(
                {
                    "atomic_number": int(float(fields[0])),
                    "nuclear_charge": float(fields[1]),
                    "position": [float(value) for value in fields[2:5]],
                }
            )
        orbital_ids: list[int] = []
        if atom_count_raw < 0:
            orbital_fields = handle.readline().split()
            if not orbital_fields:
                raise ValueError(f"{path.name}: missing cube orbital-id row")
            try:
                orbital_count = int(orbital_fields[0])
                orbital_ids = [int(value) for value in orbital_fields[1:]]
            except ValueError as exc:
                raise ValueError(f"{path.name}: malformed cube orbital-id row") from exc
            if orbital_count < 1 or len(orbital_ids) != orbital_count:
                raise ValueError(
                    f"{path.name}: cube orbital-id row declares {orbital_count} fields "
                    f"but lists {len(orbital_ids)} ids"
                )
        flat_values = np.fromfile(handle, dtype=float, sep=" ")
    coordinate_unit = axis_units[0]
    factor = BOHR_TO_ANGSTROM if coordinate_unit == "bohr" else 1.0
    origin_angstrom = [component * factor for component in origin]
    step_vectors_angstrom = [[component * factor for component in vector] for vector in vectors]
    lattice_vectors_angstrom = [
        [component * dimensions[axis] for component in step_vectors_angstrom[axis]]
        for axis in range(3)
    ]
    normalized_atoms = []
    lattice = np.asarray(lattice_vectors_angstrom, dtype=float)
    try:
        inverse_lattice = np.linalg.inv(lattice)
    except np.linalg.LinAlgError as exc:
        raise ValueError(f"{path.name}: cube lattice vectors are singular") from exc
    for atom in atoms:
        position_angstrom = [component * factor for component in atom["position"]]
        fractional = (np.asarray(position_angstrom) - np.asarray(origin_angstrom)) @ inverse_lattice
        atomic_number = int(atom["atomic_number"])
        normalized_atoms.append(
            {
                **atom,
                "symbol": _element_symbol(atomic_number),
                "position_angstrom": position_angstrom,
                "fractional_coordinates": fractional.tolist(),
            }
        )
    metadata = {
        "format": "gaussian-cube",
        "comments": comments,
        "atom_count_raw": atom_count_raw,
        "atom_count": atom_count,
        "atoms": normalized_atoms,
        "grid_shape": dimensions,
        "origin_native": origin,
        "origin_angstrom": origin_angstrom,
        "coordinate_unit_native": coordinate_unit,
        "step_vectors_angstrom": step_vectors_angstrom,
        "lattice_vectors_angstrom": lattice_vectors_angstrom,
        "orbital_ids": orbital_ids,
    }
    return flat_values, dimensions, metadata


def _read_cube(path: Path) -> tuple[Any, list[list[float]], dict[str, Any]]:
    import numpy as np

    flat_values, dimensions, metadata = _read_cube_payload(path)
    expected = math.prod(dimensions)
    observed = int(flat_values.size)
    if observed != expected:
        if (
            int(metadata["atom_count_raw"]) >= 0
            and observed > expected
            and observed % expected == 0
        ):
            field_count = observed // expected
            raise ValueError(
                f"{Path(path).name}: header declares one field with {expected} values but payload "
                f"contains {observed} values ({field_count} complete fields); use cube-inspect "
                "and cube-split explicitly before normalization"
            )
        if int(metadata["atom_count_raw"]) < 0:
            raise ValueError(
                f"{Path(path).name}: standard orbital/multi-dataset Cube payloads are not supported "
                f"by grid-field (expected {expected} values, found {observed})"
            )
        raise ValueError(f"{Path(path).name}: expected {expected} grid values, found {observed}")
    values = flat_values.reshape(dimensions)
    if not np.isfinite(values).all():
        raise ValueError(f"{Path(path).name}: cube grid contains non-finite values")
    return values, metadata["step_vectors_angstrom"], metadata


def inspect_cube_fields(path: Path) -> dict[str, Any]:
    import numpy as np

    path = Path(path).resolve()
    flat_values, dimensions, metadata = _read_cube_payload(path)
    expected = math.prod(dimensions)
    observed = int(flat_values.size)
    divisible = expected > 0 and observed % expected == 0
    complete_field_count = observed // expected if divisible else None
    if int(metadata["atom_count_raw"]) < 0:
        status = "standard-orbital-cube-unsupported"
    elif observed == expected:
        status = "single-field"
    elif observed > expected and divisible:
        status = "legacy-concatenated-fields"
    else:
        status = "malformed-payload"
    return {
        "schema_version": "1.0",
        "status": status,
        "source": _source_record(path, "cube-source"),
        "grid_shape": dimensions,
        "declared_grid_value_count": expected,
        "observed_grid_value_count": observed,
        "complete_field_count": complete_field_count,
        "atom_count": int(metadata["atom_count"]),
        "negative_atom_count_convention": int(metadata["atom_count_raw"]) < 0,
        "orbital_ids": list(metadata["orbital_ids"]),
        "all_values_finite": bool(np.isfinite(flat_values).all()),
        "field_semantics": "unknown",
        "limitations": [
            "A positive atom count plus multiple complete payload fields is treated only as a legacy concatenation pattern.",
            "Field order and physical meaning are not inferred from comments, filenames, value ranges, or field count.",
            "Standard negative-atom-count orbital or multi-dataset Cube payloads are reported but are not split by this route.",
        ],
        "provenance": {
            "producer": "dftpost.cube-inspect",
            "producer_version": __version__,
            "generated_utc": utc_now(),
        },
    }


def _read_vasp_grid(path: Path) -> tuple[Any, list[list[float]], dict[str, Any]]:
    try:
        from pymatgen.io.vasp.outputs import Chgcar, Elfcar, Locpot
    except ImportError as exc:
        raise RuntimeError("pymatgen is required to parse VASP volumetric grids") from exc

    upper = path.name.upper()
    if upper.startswith("ELFCAR"):
        parsed = Elfcar.from_file(path)
        parser_name = "pymatgen.Elfcar"
    elif upper.startswith("LOCPOT"):
        parsed = Locpot.from_file(path)
        parser_name = "pymatgen.Locpot"
    elif upper.startswith("CHGCAR"):
        parsed = Chgcar.from_file(path)
        parser_name = "pymatgen.Chgcar"
    else:
        raise ValueError("VASP grid filename must begin with CHGCAR, ELFCAR, or LOCPOT")
    values = _finite_array(parsed.data["total"], path.name)
    lattice = parsed.structure.lattice.matrix.tolist()
    step_vectors = [
        [float(component) / int(values.shape[axis]) for component in lattice[axis]]
        for axis in range(3)
    ]
    metadata = {
        "format": "vasp-volumetric-grid",
        "parser": parser_name,
        "atom_count": len(parsed.structure),
        "atoms": [
            {
                "atomic_number": int(site.specie.Z),
                "symbol": str(site.specie.symbol),
                "position_angstrom": [float(value) for value in site.coords],
                "fractional_coordinates": [float(value) for value in site.frac_coords],
            }
            for site in parsed.structure
        ],
        "origin_angstrom": [0.0, 0.0, 0.0],
        "lattice_vectors_angstrom": lattice,
        "coordinate_unit_native": "angstrom",
        "step_vectors_angstrom": step_vectors,
        "available_channels": sorted(parsed.data),
        "selected_channel": "total",
    }
    return values, step_vectors, metadata


def _axis_positions(shape: tuple[int, int, int], step_vectors: list[list[float]], axis: int) -> list[float]:
    step_length = math.sqrt(sum(component * component for component in step_vectors[axis]))
    if step_length <= 0.0 or not math.isfinite(step_length):
        raise ValueError("grid axis has a nonpositive or non-finite spacing")
    return [index * step_length for index in range(shape[axis])]


def _normalized_hkl(hkl: tuple[int, int, int]) -> tuple[int, int, int]:
    if not any(hkl):
        raise ValueError("slice_hkl cannot be (0, 0, 0)")
    divisor = math.gcd(math.gcd(abs(hkl[0]), abs(hkl[1])), abs(hkl[2]))
    return tuple(int(value // divisor) for value in hkl)


def _plane_basis_fractional(hkl: tuple[int, int, int]) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    import numpy as np

    h, k, _ = hkl
    if h or k:
        divisor = math.gcd(abs(h), abs(k))
        first = (-k // divisor, h // divisor, 0)
    else:
        first = (1, 0, 0)
    second_array = np.cross(np.asarray(hkl, dtype=int), np.asarray(first, dtype=int))
    second_divisor = math.gcd(
        math.gcd(abs(int(second_array[0])), abs(int(second_array[1]))),
        abs(int(second_array[2])),
    )
    second = tuple(int(value // second_divisor) for value in second_array)
    return first, second


def _periodic_trilinear(values: Any, fractional_coordinates: Any) -> Any:
    import numpy as np

    fractional = np.asarray(fractional_coordinates, dtype=float)
    shape = np.asarray(values.shape, dtype=int)
    coordinates = np.mod(fractional, 1.0) * shape
    lower = np.floor(coordinates).astype(int) % shape
    fraction = coordinates - np.floor(coordinates)
    upper = (lower + 1) % shape

    result = np.zeros(fractional.shape[:-1], dtype=float)
    for corner_x in (0, 1):
        for corner_y in (0, 1):
            for corner_z in (0, 1):
                indices = tuple(
                    upper[..., axis] if corner else lower[..., axis]
                    for axis, corner in enumerate((corner_x, corner_y, corner_z))
                )
                weight = np.ones(result.shape, dtype=float)
                for axis, corner in enumerate((corner_x, corner_y, corner_z)):
                    weight *= fraction[..., axis] if corner else (1.0 - fraction[..., axis])
                result += weight * values[indices]
    return result


def _build_field_slice(
    values: Any,
    source_metadata: dict[str, Any],
    hkl: tuple[int, int, int],
    offset: float,
    *,
    resolution: tuple[int, int] | None,
    in_plane_origin: tuple[float, float],
    atom_overlay: str,
    atom_plane_tolerance_angstrom: float | None,
) -> dict[str, Any]:
    import numpy as np

    normalized_hkl = _normalized_hkl(hkl)
    lattice = np.asarray(source_metadata["lattice_vectors_angstrom"], dtype=float)
    if lattice.shape != (3, 3) or not np.isfinite(lattice).all():
        raise ValueError("slice plotting requires a finite 3x3 lattice")
    if abs(float(np.linalg.det(lattice))) <= 1.0e-14:
        raise ValueError("slice plotting requires a nonsingular lattice")
    basis_fractional = _plane_basis_fractional(normalized_hkl)
    first_cartesian = np.asarray(basis_fractional[0], dtype=float) @ lattice
    second_cartesian = np.asarray(basis_fractional[1], dtype=float) @ lattice
    first_length = float(np.linalg.norm(first_cartesian))
    first_direction = first_cartesian / first_length
    second_perpendicular = second_cartesian - np.dot(second_cartesian, first_direction) * first_direction
    second_perpendicular_length = float(np.linalg.norm(second_perpendicular))
    if first_length <= 0.0 or second_perpendicular_length <= 0.0:
        raise ValueError("slice_hkl produced a degenerate in-plane basis")
    second_direction = second_perpendicular / second_perpendicular_length

    if resolution is None:
        resolution = tuple(
            min(2000, max(2, int(sum(abs(component) * values.shape[axis] for axis, component in enumerate(vector)))))
            for vector in basis_fractional
        )
    if len(resolution) != 2 or any(int(value) < 2 for value in resolution):
        raise ValueError("slice_resolution must contain two integers of at least 2")
    resolution = (int(resolution[0]), int(resolution[1]))
    if len(in_plane_origin) != 2 or not all(math.isfinite(float(value)) for value in in_plane_origin):
        raise ValueError("slice_origin must contain two finite in-plane fractional coordinates")
    in_plane_origin = (float(in_plane_origin[0]), float(in_plane_origin[1]))

    normal_fractional = np.asarray(normalized_hkl, dtype=float)
    origin_fractional = float(offset) * normal_fractional / float(np.dot(normal_fractional, normal_fractional))
    first_centers = (np.arange(resolution[0], dtype=float) + 0.5) / resolution[0]
    second_centers = (np.arange(resolution[1], dtype=float) + 0.5) / resolution[1]
    first_grid, second_grid = np.meshgrid(first_centers, second_centers, indexing="ij")
    fractional_grid = (
        origin_fractional
        + (in_plane_origin[0] + first_grid)[..., None] * np.asarray(basis_fractional[0], dtype=float)
        + (in_plane_origin[1] + second_grid)[..., None] * np.asarray(basis_fractional[1], dtype=float)
    )
    plane = _periodic_trilinear(values, fractional_grid)

    first_edges = np.arange(resolution[0] + 1, dtype=float) / resolution[0]
    second_edges = np.arange(resolution[1] + 1, dtype=float) / resolution[1]
    first_edge_grid, second_edge_grid = np.meshgrid(first_edges, second_edges, indexing="ij")
    edge_cartesian = (
        first_edge_grid[..., None] * first_cartesian
        + second_edge_grid[..., None] * second_cartesian
    )
    x_edges = edge_cartesian @ first_direction
    y_edges = edge_cartesian @ second_direction

    if atom_overlay not in {"none", "near-plane", "all-projected"}:
        raise ValueError("atom_overlay must be none, near-plane, or all-projected")
    if atom_plane_tolerance_angstrom is None:
        atom_plane_tolerance_angstrom = max(
            float(np.linalg.norm(np.asarray(vector, dtype=float)))
            for vector in source_metadata["step_vectors_angstrom"]
        )
    if not math.isfinite(atom_plane_tolerance_angstrom) or atom_plane_tolerance_angstrom < 0.0:
        raise ValueError("atom_plane_tolerance_angstrom must be finite and nonnegative")

    inverse_lattice = np.linalg.inv(lattice)
    cartesian_normal = inverse_lattice @ normal_fractional
    normal_length = float(np.linalg.norm(cartesian_normal))
    normal_direction = cartesian_normal / normal_length
    cartesian_basis = np.column_stack((first_cartesian, second_cartesian))
    displayed_atoms = []
    if atom_overlay != "none":
        for atom in source_metadata.get("atoms", []):
            fractional = np.asarray(atom["fractional_coordinates"], dtype=float)
            phase = float(np.dot(normal_fractional, fractional) - float(offset))
            phase -= round(phase)
            distance = abs(phase) / normal_length
            if atom_overlay == "near-plane" and distance > atom_plane_tolerance_angstrom:
                continue
            cartesian = fractional @ lattice
            projected = cartesian - (phase / normal_length) * normal_direction
            coefficients = np.linalg.lstsq(cartesian_basis, projected, rcond=None)[0]
            wrapped = np.mod(coefficients - np.asarray(in_plane_origin), 1.0)
            display_cartesian = wrapped[0] * first_cartesian + wrapped[1] * second_cartesian
            displayed_atoms.append(
                {
                    "atomic_number": int(atom.get("atomic_number", 0)),
                    "symbol": str(atom.get("symbol") or _element_symbol(int(atom.get("atomic_number", 0)))),
                    "x_angstrom": float(np.dot(display_cartesian, first_direction)),
                    "y_angstrom": float(np.dot(display_cartesian, second_direction)),
                    "distance_to_plane_angstrom": distance,
                }
            )
    return {
        "values": plane,
        "x_edges": x_edges,
        "y_edges": y_edges,
        "plane_hkl": normalized_hkl,
        "plane_offset": float(offset),
        "basis_fractional": basis_fractional,
        "in_plane_origin": in_plane_origin,
        "resolution": resolution,
        "interpolation": "periodic-linear",
        "atom_overlay": atom_overlay,
        "atom_plane_tolerance_angstrom": float(atom_plane_tolerance_angstrom),
        "displayed_atoms": displayed_atoms,
    }


def _field_slice_style(
    field_kind: str,
    values: Any,
    colormap: str | None,
    value_range: tuple[float, float] | None,
) -> tuple[str, tuple[float, float]]:
    import numpy as np

    if value_range is not None:
        if len(value_range) != 2 or not all(math.isfinite(float(value)) for value in value_range):
            raise ValueError("value_range must contain two finite values")
        limits = (float(value_range[0]), float(value_range[1]))
        if limits[0] >= limits[1]:
            raise ValueError("value_range must be increasing")
    elif field_kind == "electron-localization":
        limits = (0.0, 1.0)
    elif field_kind == "charge-density-difference":
        maximum = float(np.max(np.abs(values)))
        maximum = maximum if maximum > 0.0 else 1.0
        limits = (-maximum, maximum)
    else:
        minimum = float(np.min(values))
        maximum = float(np.max(values))
        if minimum == maximum:
            padding = abs(minimum) * 0.05 if minimum else 1.0
            minimum -= padding
            maximum += padding
        limits = (minimum, maximum)
    default_colormap = {
        "electron-localization": "turbo",
        "charge-density-difference": "RdBu_r",
    }.get(field_kind, "viridis")
    return colormap or default_colormap, limits


def _draw_field_slice(
    axis: Any,
    slice_data: dict[str, Any],
    *,
    colormap: str,
    value_limits: tuple[float, float],
    atom_labels: bool,
    display_window: tuple[float, float, float, float] | None,
) -> Any:
    import matplotlib.pyplot as plt
    import numpy as np

    mesh = axis.pcolormesh(
        np.asarray(slice_data["x_edges"]).T,
        np.asarray(slice_data["y_edges"]).T,
        np.asarray(slice_data["values"]).T,
        cmap=colormap,
        vmin=value_limits[0],
        vmax=value_limits[1],
        shading="flat",
        rasterized=True,
    )
    atoms = slice_data["displayed_atoms"]
    if atoms:
        atom_colormap = plt.get_cmap("tab20")
        axis.scatter(
            [atom["x_angstrom"] for atom in atoms],
            [atom["y_angstrom"] for atom in atoms],
            s=58,
            c=[atom_colormap((atom["atomic_number"] % 20) / 19.0) for atom in atoms],
            edgecolors="black",
            linewidths=0.55,
            zorder=3,
        )
        if atom_labels:
            for atom in atoms:
                axis.annotate(
                    atom["symbol"],
                    (atom["x_angstrom"], atom["y_angstrom"]),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize="small",
                    color="black",
                    bbox={"boxstyle": "round,pad=0.12", "facecolor": "white", "edgecolor": "none", "alpha": 0.65},
                    zorder=4,
                )
    x_edges = np.asarray(slice_data["x_edges"])
    y_edges = np.asarray(slice_data["y_edges"])
    if display_window is None:
        x_limits = (float(np.min(x_edges)), float(np.max(x_edges)))
        y_limits = (float(np.min(y_edges)), float(np.max(y_edges)))
    else:
        if len(display_window) != 4 or not all(math.isfinite(float(value)) for value in display_window):
            raise ValueError("slice_window must contain four finite values")
        x_limits = (float(display_window[0]), float(display_window[1]))
        y_limits = (float(display_window[2]), float(display_window[3]))
        if x_limits[0] >= x_limits[1] or y_limits[0] >= y_limits[1]:
            raise ValueError("slice_window limits must be increasing")
        if x_limits[1] <= float(np.min(x_edges)) or x_limits[0] >= float(np.max(x_edges)):
            raise ValueError("slice_window does not intersect the sampled u range")
        if y_limits[1] <= float(np.min(y_edges)) or y_limits[0] >= float(np.max(y_edges)):
            raise ValueError("slice_window does not intersect the sampled v range")
    axis.set_xlim(*x_limits)
    axis.set_ylim(*y_limits)
    axis.margins(x=0, y=0)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("u (angstrom)")
    axis.set_ylabel("v (angstrom)")
    h, k, l = slice_data["plane_hkl"]
    axis.set_title(f"({h} {k} {l}) section; offset={slice_data['plane_offset']:.6g}")
    return mesh


def _plot_grid_field(
    positions: list[float],
    profile: list[float],
    slice_data: dict[str, Any],
    field_unit: str,
    axis: int,
    output: Path,
    slice_output: Path,
    *,
    field_kind: str,
    colormap: str | None,
    value_range: tuple[float, float] | None,
    atom_labels: bool,
    slice_window: tuple[float, float, float, float] | None,
    work_function: dict[str, Any] | None = None,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    selected_colormap, selected_limits = _field_slice_style(field_kind, slice_data["values"], colormap, value_range)
    field_label = {
        "electron-localization": "ELF",
        "charge-density-difference": "Charge-density difference",
        "charge-density": "Charge density",
        "electrostatic-potential": "Electrostatic potential",
        "other": "Field value",
    }[field_kind]
    colorbar_label = field_label if field_unit == "dimensionless" else f"{field_label} ({field_unit})"
    h, k, l = slice_data["plane_hkl"]
    slice_title = f"{field_label}; ({h} {k} {l}) section, offset={slice_data['plane_offset']:.6g}"
    with plt.style.context(str(style)):
        figure, (profile_axis, slice_axis) = plt.subplots(1, 2, figsize=(10.0, 4.0))
        profile_axis.plot(positions, profile, color="#7f1d1d", linewidth=1.1)
        profile_axis.set_xlabel(f"Axis {axis} position (angstrom)")
        profile_axis.set_ylabel(f"Planar average ({field_unit})")
        profile_axis.set_xlim(positions[0], positions[-1])
        profile_axis.margins(x=0)
        if work_function is not None:
            window = work_function["vacuum_window_angstrom"]
            profile_axis.axvspan(window[0], window[1], color="#d9b44a", alpha=0.22, linewidth=0)
            vacuum_native = work_function["vacuum_mean_ev"] / work_function["potential_to_ev"]
            profile_axis.axhline(vacuum_native, color="#d9b44a", linestyle="--", linewidth=0.9)
            profile_axis.text(
                0.02,
                0.04,
                f"selected window; Phi = {work_function['work_function_ev']:.6f} eV",
                transform=profile_axis.transAxes,
                fontsize="small",
            )
        image = _draw_field_slice(
            slice_axis,
            slice_data,
            colormap=selected_colormap,
            value_limits=selected_limits,
            atom_labels=atom_labels,
            display_window=slice_window,
        )
        slice_axis.set_title(slice_title)
        figure.colorbar(image, ax=slice_axis, label=colorbar_label)
        figure.tight_layout()
        _save_figure_atomic(figure, output)
        plt.close(figure)

        slice_figure, slice_axis = plt.subplots(1, 1, figsize=(5.5, 4.8))
        image = _draw_field_slice(
            slice_axis,
            slice_data,
            colormap=selected_colormap,
            value_limits=selected_limits,
            atom_labels=atom_labels,
            display_window=slice_window,
        )
        slice_axis.set_title(slice_title)
        slice_figure.colorbar(image, ax=slice_axis, label=colorbar_label)
        slice_figure.tight_layout()
        _save_figure_atomic(slice_figure, slice_output)
        plt.close(slice_figure)
    return {
        "schema_version": "1.0",
        "plot_type": "real-space-planar-and-crystallographic-section",
        "axis": axis,
        "x_limits": [positions[0], positions[-1]],
        "field_unit": field_unit,
        "work_function_window_shown": work_function is not None,
        "output": _output_record(output, "figure", "image/png"),
        "slice": {
            "plane_hkl": list(slice_data["plane_hkl"]),
            "plane_offset": slice_data["plane_offset"],
            "basis_fractional": [list(vector) for vector in slice_data["basis_fractional"]],
            "in_plane_origin": list(slice_data["in_plane_origin"]),
            "resolution": list(slice_data["resolution"]),
            "interpolation": slice_data["interpolation"],
            "colormap": selected_colormap,
            "value_limits": list(selected_limits),
            "atom_overlay": slice_data["atom_overlay"],
            "atom_labels": atom_labels,
            "atom_plane_tolerance_angstrom": slice_data["atom_plane_tolerance_angstrom"],
            "displayed_atom_count": len(slice_data["displayed_atoms"]),
            "display_window_angstrom": list(slice_window) if slice_window is not None else None,
            "output": _output_record(slice_output, "field-slice-figure", "image/png"),
        },
    }


def normalize_grid_field(
    grid_path: Path,
    code: str,
    output_directory: Path,
    dataset_id: str,
    *,
    field_kind: str,
    field_unit: str,
    axis: int = 2,
    slice_index: int | None = None,
    slice_hkl: tuple[int, int, int] | None = None,
    slice_offset: float | None = None,
    slice_resolution: tuple[int, int] | None = None,
    slice_origin: tuple[float, float] = (0.0, 0.0),
    slice_window: tuple[float, float, float, float] | None = None,
    atom_overlay: str = "near-plane",
    atom_plane_tolerance_angstrom: float | None = None,
    atom_labels: bool = True,
    colormap: str | None = None,
    value_range: tuple[float, float] | None = None,
    potential_to_ev: float | None = None,
    fermi_energy_ev: float | None = None,
    fermi_energy_path: Path | None = None,
    vacuum_window_angstrom: tuple[float, float] | None = None,
    figure_output: Path | None = None,
    slice_figure_output: Path | None = None,
    maturity: str | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    import numpy as np

    if code not in {"qe", "vasp", "siesta", "mixed"}:
        raise ValueError("code must be qe, vasp, siesta, or mixed")
    maturity = resolve_backend_maturity("real-space", code, "python.grid", maturity)
    _check_maturity(maturity)
    if field_kind not in FIELD_KINDS:
        raise ValueError(f"unknown field_kind: {field_kind}")
    if not field_unit.strip():
        raise ValueError("field_unit must be explicit and nonempty")
    if axis not in {0, 1, 2}:
        raise ValueError("axis must be 0, 1, or 2")
    if slice_hkl is not None and slice_index is not None:
        raise ValueError("slice_index is only valid for the axis-aligned compatibility slice; use slice_offset with slice_hkl")
    if slice_offset is not None and not math.isfinite(float(slice_offset)):
        raise ValueError("slice_offset must be finite")
    if fermi_energy_ev is not None and fermi_energy_path is not None:
        raise ValueError("supply only one of fermi_energy_ev and fermi_energy_path")
    if fermi_energy_path is not None:
        if code == "qe":
            fermi_energy_ev = parse_qe_fermi_energy(fermi_energy_path)
        elif code == "vasp":
            import re

            matches = re.findall(
                r"E-fermi\s*:\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)",
                fermi_energy_path.read_text(encoding="utf-8", errors="replace"),
                re.IGNORECASE,
            )
            if not matches:
                raise ValueError(f"could not parse an explicit VASP Fermi energy in {fermi_energy_path.name}")
            fermi_energy_ev = float(matches[-1])
        else:
            raise ValueError("fermi_energy_path parsing requires code=qe or code=vasp")
    work_function_arguments = (potential_to_ev, fermi_energy_ev, vacuum_window_angstrom)
    if any(value is not None for value in work_function_arguments) and not all(value is not None for value in work_function_arguments):
        raise ValueError("work-function evaluation requires potential_to_ev, a Fermi-energy value/file, and vacuum_window_angstrom together")
    if all(value is not None for value in work_function_arguments):
        if field_kind != "electrostatic-potential":
            raise ValueError("work-function evaluation requires field_kind=electrostatic-potential")
        if not math.isfinite(float(potential_to_ev)) or float(potential_to_ev) == 0.0:
            raise ValueError("potential_to_ev must be finite and nonzero")
        if not math.isfinite(float(fermi_energy_ev)):
            raise ValueError("fermi_energy_ev must be finite")
        if vacuum_window_angstrom[0] >= vacuum_window_angstrom[1]:
            raise ValueError("vacuum_window_angstrom must be increasing")

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    profile_path = output_directory / "planar-average.csv"
    slice_path = output_directory / "slice.csv"
    analysis_path = output_directory / "real-space.analysis.json"
    plot_metadata_path = output_directory / "real-space.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "real-space.png"
    slice_figure_path = slice_figure_output.resolve() if slice_figure_output is not None else output_directory / "field-slice.png"
    dataset_path = output_directory / "real-space.dataset.json"
    _refuse_existing_outputs((profile_path, slice_path, analysis_path, plot_metadata_path, figure_path, slice_figure_path, dataset_path), overwrite)

    if grid_path.suffix.lower() == ".cube":
        values, step_vectors, source_metadata = _read_cube(grid_path)
    elif code == "vasp":
        values, step_vectors, source_metadata = _read_vasp_grid(grid_path)
    else:
        raise ValueError("QE grid input currently requires a .cube file; VASP input requires CHGCAR/ELFCAR/LOCPOT naming")
    values = _finite_array(values, grid_path.name)
    positions = _axis_positions(values.shape, step_vectors, axis)
    other_axes = tuple(index for index in range(3) if index != axis)
    profile = np.mean(values, axis=other_axes).tolist()
    if slice_hkl is None:
        selected_slice = values.shape[axis] // 2 if slice_index is None else slice_index
        if selected_slice < 0 or selected_slice >= values.shape[axis]:
            raise ValueError(f"slice_index must be within 0..{values.shape[axis] - 1}")
        selected_hkl = tuple(1 if item == axis else 0 for item in range(3))
        selected_offset = selected_slice / values.shape[axis]
    else:
        selected_slice = None
        selected_hkl = tuple(int(value) for value in slice_hkl)
        selected_offset = 0.0 if slice_offset is None else float(slice_offset)
    slice_data = _build_field_slice(
        values,
        source_metadata,
        selected_hkl,
        selected_offset,
        resolution=slice_resolution,
        in_plane_origin=slice_origin,
        atom_overlay=atom_overlay,
        atom_plane_tolerance_angstrom=atom_plane_tolerance_angstrom,
    )
    plane = slice_data["values"]
    x_edges = np.asarray(slice_data["x_edges"], dtype=float)
    y_edges = np.asarray(slice_data["y_edges"], dtype=float)
    x_centers = 0.25 * (x_edges[:-1, :-1] + x_edges[1:, :-1] + x_edges[:-1, 1:] + x_edges[1:, 1:])
    y_centers = 0.25 * (y_edges[:-1, :-1] + y_edges[1:, :-1] + y_edges[:-1, 1:] + y_edges[1:, 1:])

    _write_csv_atomic(
        profile_path,
        ["grid_index", "position_angstrom", "planar_average"],
        (
            {"grid_index": index, "position_angstrom": position, "planar_average": value}
            for index, (position, value) in enumerate(zip(positions, profile))
        ),
    )
    _write_csv_atomic(
        slice_path,
        ["index_a", "index_b", "position_a_angstrom", "position_b_angstrom", "field_value"],
        (
            {
                "index_a": index_a,
                "index_b": index_b,
                "position_a_angstrom": float(x_centers[index_a, index_b]),
                "position_b_angstrom": float(y_centers[index_a, index_b]),
                "field_value": float(plane[index_a, index_b]),
            }
            for index_a in range(plane.shape[0])
            for index_b in range(plane.shape[1])
        ),
    )

    work_function = None
    checks = [
        {"id": "finite-grid", "status": "pass", "message": "All selected grid-channel values are finite."},
        {"id": "grid-shape", "status": "pass", "message": "A nonempty three-dimensional grid was parsed."},
        {"id": "coordinate-scale", "status": "pass", "message": "Axis positions were derived from explicit grid vectors."},
    ]
    if all(value is not None for value in work_function_arguments):
        selected = [
            value for position, value in zip(positions, profile)
            if vacuum_window_angstrom[0] <= position <= vacuum_window_angstrom[1]
        ]
        if len(selected) < 2:
            raise ValueError("vacuum window selects fewer than two grid planes")
        selected_ev = [value * float(potential_to_ev) for value in selected]
        vacuum_mean_ev = float(np.mean(selected_ev))
        vacuum_std_ev = float(np.std(selected_ev))
        work_function = {
            "potential_to_ev": float(potential_to_ev),
            "fermi_energy_ev": float(fermi_energy_ev),
            "vacuum_window_angstrom": list(vacuum_window_angstrom),
            "selected_plane_count": len(selected),
            "vacuum_mean_ev": vacuum_mean_ev,
            "vacuum_std_ev": vacuum_std_ev,
            "work_function_ev": vacuum_mean_ev - float(fermi_energy_ev),
            "definition": "work_function_ev = mean(planar potential in caller-selected vacuum window, converted to eV) - fermi_energy_ev",
        }
        checks.append({"id": "work-function-inputs", "status": "pass", "message": "Potential conversion, Fermi energy, and vacuum window were supplied explicitly."})
    else:
        checks.append({"id": "work-function-inputs", "status": "not-run", "message": "No work function was computed because the complete explicit input triple was not supplied."})

    limitations = [
        "The selected field kind and field unit are caller-declared and are not inferred from a material or value range.",
        "The planar average is an arithmetic mean over grid planes; no macroscopic smoothing is applied.",
        "The displayed two-dimensional section is a periodic linear interpolation on a caller-selected crystallographic plane, not an isosurface analysis.",
        "Atom overlay tolerance, in-plane origin, crop window, colormap, and value range are recorded rendering choices and do not define physical regions.",
        "Work-function evaluation never detects a vacuum plateau automatically; it requires an explicit unit conversion, Fermi energy, and vacuum window.",
    ]
    analysis = {
        "schema_version": "1.0",
        "field_kind": field_kind,
        "field_unit": field_unit,
        "grid_shape": list(values.shape),
        "axis": axis,
        "axis_length_sampled_angstrom": positions[-1] if positions else 0.0,
        "slice_index": selected_slice,
        "slice_plane": {
            "hkl": list(slice_data["plane_hkl"]),
            "offset": slice_data["plane_offset"],
            "basis_fractional": [list(vector) for vector in slice_data["basis_fractional"]],
            "in_plane_origin": list(slice_data["in_plane_origin"]),
            "resolution": list(slice_data["resolution"]),
            "interpolation": slice_data["interpolation"],
            "atom_overlay": slice_data["atom_overlay"],
            "atom_plane_tolerance_angstrom": slice_data["atom_plane_tolerance_angstrom"],
            "displayed_atoms": slice_data["displayed_atoms"],
        },
        "field_min": float(np.min(values)),
        "field_max": float(np.max(values)),
        "field_mean": float(np.mean(values)),
        "source_metadata": source_metadata,
        "work_function": work_function,
        "limitations": limitations,
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_grid_field(
        positions,
        profile,
        slice_data,
        field_unit,
        axis,
        figure_path,
        slice_figure_path,
        field_kind=field_kind,
        colormap=colormap,
        value_range=value_range,
        atom_labels=atom_labels,
        slice_window=slice_window,
        work_function=work_function,
    )
    write_json_atomic(plot_metadata_path, plot_metadata)
    source_role = {
        "charge-density": "charge-density-grid",
        "charge-density-difference": "charge-density-difference-grid",
        "electron-localization": "electron-localization-grid",
        "electrostatic-potential": "potential-grid",
        "other": "real-space-grid",
    }[field_kind]
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "real-space",
        "code": code,
        "maturity": maturity,
        "representation": "grid",
        "source_files": [_source_record(grid_path, source_role)] + (
            [_source_record(fermi_energy_path, "energy-reference")] if fermi_energy_path is not None else []
        ),
        "dimensions": {
            "grid_x": int(values.shape[0]),
            "grid_y": int(values.shape[1]),
            "grid_z": int(values.shape[2]),
            "profile_points": len(profile),
            "slice_points": int(plane.size),
        },
        "columns": [
            {"name": "position_angstrom", "dtype": "float", "unit": "angstrom", "role": "axis-position"},
            {"name": "planar_average", "dtype": "float", "unit": field_unit, "role": "plane-mean-field"},
            {"name": "field_value", "dtype": "float", "unit": field_unit, "role": "slice-field"},
        ],
        "data_files": [
            _output_record(profile_path, "planar-average-table", "text/csv"),
            _output_record(slice_path, "slice-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [
            {
                "operation": "planar-arithmetic-mean",
                "parameters": {"axis": axis},
                "input_columns": ["field_value"],
                "output_columns": ["planar_average"],
            },
            {
                "operation": "periodic-crystallographic-section",
                "parameters": {
                    "hkl": list(slice_data["plane_hkl"]),
                    "offset": slice_data["plane_offset"],
                    "resolution": list(slice_data["resolution"]),
                    "in_plane_origin": list(slice_data["in_plane_origin"]),
                    "interpolation": slice_data["interpolation"],
                },
                "input_columns": ["field_value"],
                "output_columns": ["field_value"],
            },
        ],
        "validation": {"status": "pass", "checks": checks},
        "limitations": limitations,
        "provenance": {"producer": "dftpost.grid-field", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {
        "profile": profile_path,
        "slice": slice_path,
        "analysis": analysis_path,
        "plot_metadata": plot_metadata_path,
        "figure": figure_path,
        "slice_figure": slice_figure_path,
        "dataset": dataset_path,
    }


def _write_cube_atomic(
    path: Path,
    values: Any,
    source_metadata: dict[str, Any],
    *,
    title: str = "dftpost linear combination",
    description: str = "coordinates are written in bohr; coefficients and hashes are in companion metadata",
) -> None:
    import numpy as np

    array = _finite_array(values, path.name)
    origin = [value / BOHR_TO_ANGSTROM for value in source_metadata["origin_angstrom"]]
    step_vectors = [
        [value / BOHR_TO_ANGSTROM for value in vector]
        for vector in source_metadata["step_vectors_angstrom"]
    ]
    atoms = source_metadata.get("atoms", [])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(title.rstrip("\n") + "\n")
            handle.write(description.rstrip("\n") + "\n")
            handle.write(f"{len(atoms):5d} {origin[0]: .10e} {origin[1]: .10e} {origin[2]: .10e}\n")
            for dimension, vector in zip(array.shape, step_vectors):
                handle.write(f"{int(dimension):5d} {vector[0]: .10e} {vector[1]: .10e} {vector[2]: .10e}\n")
            for atom in atoms:
                position = [value / BOHR_TO_ANGSTROM for value in atom["position_angstrom"]]
                handle.write(
                    f"{int(atom['atomic_number']):5d} {float(atom.get('nuclear_charge', atom['atomic_number'])): .10e} "
                    f"{position[0]: .10e} {position[1]: .10e} {position[2]: .10e}\n"
                )
            flat = np.asarray(array, dtype=float).reshape(-1)
            for start in range(0, flat.size, 6):
                handle.write(" ".join(f"{value: .10e}" for value in flat[start:start + 6]) + "\n")
            handle.flush()
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def split_cube_fields(
    source: Path,
    output_directory: Path,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    import numpy as np

    source = Path(source).resolve()
    flat_values, dimensions, metadata = _read_cube_payload(source)
    expected = math.prod(dimensions)
    observed = int(flat_values.size)
    if int(metadata["atom_count_raw"]) < 0:
        raise ValueError(
            "cube-split does not support the standard negative-atom-count orbital or "
            "multi-dataset Cube convention"
        )
    if observed == expected:
        raise ValueError(f"{source.name}: payload contains exactly one field; no split is needed")
    if expected < 1 or observed <= expected or observed % expected != 0:
        raise ValueError(
            f"{source.name}: payload has {observed} values for a {expected}-value grid and is "
            "not an integer number of complete fields"
        )
    if not np.isfinite(flat_values).all():
        raise ValueError(f"{source.name}: cube payload contains non-finite values")

    field_count = observed // expected
    output_directory = Path(output_directory).resolve()
    field_paths = [output_directory / f"field-{index:03d}.cube" for index in range(field_count)]
    manifest_path = output_directory / "cube-split.manifest.json"
    _refuse_existing_outputs((*field_paths, manifest_path), overwrite)
    output_directory.mkdir(parents=True, exist_ok=True)

    for index, field_path in enumerate(field_paths):
        start = index * expected
        values = flat_values[start:start + expected].reshape(dimensions)
        _write_cube_atomic(
            field_path,
            values,
            metadata,
            title=f"dftpost extracted field {index:03d}",
            description=(
                "field semantics are unknown; source identity, index, and hashes are in "
                "cube-split.manifest.json"
            ),
        )

    manifest = {
        "schema_version": "1.0",
        "operation": "legacy-concatenated-cube-split",
        "source": _source_record(source, "cube-source"),
        "grid_shape": dimensions,
        "values_per_field": expected,
        "observed_grid_value_count": observed,
        "field_count": field_count,
        "field_semantics": "unknown",
        "outputs": [
            {
                "field_index": index,
                **_output_record(path, "extracted-grid-field", "chemical/x-gaussian-cube"),
            }
            for index, path in enumerate(field_paths)
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {
                    "id": "exact-field-division",
                    "status": "pass",
                    "message": "The payload divides exactly into complete fields using the declared grid shape.",
                },
                {
                    "id": "finite-values",
                    "status": "pass",
                    "message": "Every extracted field value is finite.",
                },
                {
                    "id": "semantic-neutrality",
                    "status": "pass",
                    "message": "Outputs retain neutral numeric indices and no physical field meaning is inferred.",
                },
            ],
        },
        "limitations": [
            "This compatibility route accepts only positive-atom-count Cube headers followed by an exact multiple of the declared grid size.",
            "The output field order is the payload order; field semantics and units remain caller-supplied evidence.",
            "Use grid-combine only after independently establishing coefficients, units, and the physical meaning of every component.",
        ],
        "provenance": {
            "producer": "dftpost.cube-split",
            "producer_version": __version__,
            "generated_utc": utc_now(),
        },
    }
    write_json_atomic(manifest_path, manifest)
    return {"manifest": manifest_path, "fields": field_paths}


def _cube_geometry_aligns(reference_values: Any, reference_metadata: dict[str, Any], values: Any, metadata: dict[str, Any]) -> bool:
    import numpy as np

    return (
        tuple(reference_values.shape) == tuple(values.shape)
        and np.allclose(reference_metadata["origin_angstrom"], metadata["origin_angstrom"], rtol=1.0e-10, atol=1.0e-8)
        and np.allclose(reference_metadata["step_vectors_angstrom"], metadata["step_vectors_angstrom"], rtol=1.0e-10, atol=1.0e-8)
    )


def combine_cube_grids(
    components: list[tuple[float, Path]],
    output_directory: Path,
    dataset_id: str,
    *,
    field_unit: str,
    structure_component_index: int = 0,
    code: str = "mixed",
    maturity: str | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    import numpy as np

    if code not in {"qe", "vasp", "mixed"}:
        raise ValueError("code must be qe, vasp, or mixed")
    maturity = resolve_backend_maturity("real-space", code, "python.grid", maturity)
    _check_maturity(maturity)
    if len(components) < 2:
        raise ValueError("grid combination requires at least two coefficient=path components")
    if not field_unit.strip():
        raise ValueError("field_unit must be explicit and nonempty")
    if structure_component_index < 0 or structure_component_index >= len(components):
        raise ValueError("structure_component_index is outside the component list")
    normalized_components = []
    for coefficient, path in components:
        if not math.isfinite(float(coefficient)):
            raise ValueError("grid coefficients must be finite")
        path = Path(path).resolve()
        if path.suffix.lower() != ".cube":
            raise ValueError("grid combination currently requires Gaussian .cube components")
        normalized_components.append((float(coefficient), path))

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    grid_path = output_directory / "combined-grid.cube"
    analysis_path = output_directory / "grid-combination.analysis.json"
    dataset_path = output_directory / "grid-combination.dataset.json"
    _refuse_existing_outputs((grid_path, analysis_path, dataset_path), overwrite)

    reference_values, _, reference_metadata = _read_cube(normalized_components[0][1])
    combined = np.zeros(reference_values.shape, dtype=float)
    selected_metadata = reference_metadata if structure_component_index == 0 else None
    for index, (coefficient, path) in enumerate(normalized_components):
        if index == 0:
            values, metadata = reference_values, reference_metadata
        else:
            values, _, metadata = _read_cube(path)
            if not _cube_geometry_aligns(reference_values, reference_metadata, values, metadata):
                raise ValueError(f"grid geometry does not align for component {index}: {path.name}")
        combined += coefficient * values
        if index == structure_component_index:
            selected_metadata = metadata
    if selected_metadata is None:
        raise AssertionError("structure source metadata was not selected")
    _write_cube_atomic(grid_path, combined, selected_metadata)

    limitations = [
        "All component coefficients and the output field unit are caller-declared; no material-specific subtraction convention is inferred.",
        "Components must share the same grid shape, origin, and step vectors; atom lists may differ and are taken only from the selected structure component.",
        "No physical interpretation, charge-transfer partition, or isosurface threshold is inferred from the combined field.",
    ]
    analysis = {
        "schema_version": "1.0",
        "operation": "linear-grid-combination",
        "coefficients": [coefficient for coefficient, _ in normalized_components],
        "structure_component_index": structure_component_index,
        "field_unit": field_unit,
        "output_coordinate_unit": "bohr",
        "grid_shape": list(combined.shape),
        "field_min": float(np.min(combined)),
        "field_max": float(np.max(combined)),
        "field_mean": float(np.mean(combined)),
        "geometry_tolerance": {"relative": 1.0e-10, "absolute_angstrom": 1.0e-8},
        "limitations": limitations,
    }
    write_json_atomic(analysis_path, analysis)
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "real-space",
        "code": code,
        "maturity": maturity,
        "representation": "grid",
        "source_files": [_source_record(path, "grid-component") for _, path in normalized_components],
        "dimensions": {
            "grid_x": int(combined.shape[0]),
            "grid_y": int(combined.shape[1]),
            "grid_z": int(combined.shape[2]),
            "component_count": len(normalized_components),
        },
        "columns": [
            {"name": "field_value", "dtype": "float", "unit": field_unit, "role": "combined-grid-field"},
        ],
        "data_files": [
            _output_record(grid_path, "combined-grid", "chemical/x-gaussian-cube"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
        ],
        "transformations": [
            {
                "operation": "linear-grid-combination",
                "parameters": {
                    "coefficients": [coefficient for coefficient, _ in normalized_components],
                    "structure_component_index": structure_component_index,
                    "output_coordinate_unit": "bohr",
                },
                "input_columns": ["field_value"],
                "output_columns": ["field_value"],
            }
        ],
        "validation": {
            "status": "pass",
            "checks": [
                {"id": "finite-grid", "status": "pass", "message": "All component and combined grid values are finite."},
                {"id": "grid-alignment", "status": "pass", "message": "Grid shape, origin, and step vectors align within recorded tolerances."},
                {"id": "explicit-coefficients", "status": "pass", "message": "Every source grid has a finite caller-declared coefficient."},
            ],
        },
        "limitations": limitations,
        "provenance": {"producer": "dftpost.grid-combine", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {"grid": grid_path, "analysis": analysis_path, "dataset": dataset_path}


def _parse_bader_acf(path: Path) -> tuple[list[dict[str, float | int]], dict[str, float]]:
    records: list[dict[str, float | int]] = []
    footer: dict[str, float] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or set(stripped) == {"-"}:
            continue
        fields = stripped.split()
        if fields[0].isdigit() and len(fields) >= 7:
            try:
                values = [float(value) for value in fields[1:7]]
            except ValueError as exc:
                raise ValueError(f"{path.name}:{line_number}: malformed Bader atom row") from exc
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"{path.name}:{line_number}: non-finite Bader atom row")
            records.append(
                {
                    "atom_index": int(fields[0]),
                    "x_angstrom": values[0],
                    "y_angstrom": values[1],
                    "z_angstrom": values[2],
                    "basin_electrons": values[3],
                    "min_distance_angstrom": values[4],
                    "atomic_volume_angstrom3": values[5],
                }
            )
        elif ":" in stripped:
            label, value = stripped.split(":", 1)
            try:
                footer[label.strip().lower().replace(" ", "_")] = float(value.split()[0])
            except (ValueError, IndexError):
                continue
    if not records:
        raise ValueError(f"{path.name}: no Bader atom rows found")
    if [record["atom_index"] for record in records] != list(range(1, len(records) + 1)):
        raise ValueError(f"{path.name}: Bader atom indices must be consecutive from 1")
    return records, footer


def _plot_bader(records: list[dict[str, Any]], has_reference: bool, output: Path) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
    panel_count = 2 if has_reference else 1
    with plt.style.context(str(style)):
        figure, axes = plt.subplots(panel_count, 1, figsize=(7.0, 3.4 * panel_count), squeeze=False)
        axis = axes[0][0]
        indices = [record["atom_index"] for record in records]
        axis.bar(indices, [record["basin_electrons"] for record in records], color="#7f1d1d")
        axis.set_ylabel("Basin electrons (e)")
        axis.set_xlim(0.5, len(records) + 0.5)
        if has_reference:
            delta_axis = axes[1][0]
            delta_axis.bar(indices, [record["reference_minus_basin_electrons"] for record in records], color="#2f6f9f")
            delta_axis.axhline(0.0, color="black", linestyle="--", linewidth=0.8)
            delta_axis.set_ylabel("Reference - basin (e)")
            delta_axis.set_xlim(0.5, len(records) + 0.5)
            delta_axis.set_xlabel("Atom index")
        else:
            axis.set_xlabel("Atom index")
        figure.tight_layout()
        _save_figure_atomic(figure, output)
        plt.close(figure)
    return {
        "schema_version": "1.0",
        "plot_type": "bader-basin-electrons",
        "reference_difference_shown": has_reference,
        "x_limits": [0.5, len(records) + 0.5],
        "output": _output_record(output, "figure", "image/png"),
    }


def normalize_bader_acf(
    acf_path: Path,
    code: str,
    output_directory: Path,
    dataset_id: str,
    *,
    reference_electrons: list[float] | None = None,
    electron_closure_tolerance: float = 1.0e-3,
    figure_output: Path | None = None,
    maturity: str | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    if code not in {"qe", "vasp", "mixed"}:
        raise ValueError("code must be qe, vasp, or mixed")
    maturity = resolve_backend_maturity("real-space", code, "python.bader-acf", maturity)
    _check_maturity(maturity)
    if electron_closure_tolerance < 0.0:
        raise ValueError("electron_closure_tolerance must be nonnegative")
    records, footer = _parse_bader_acf(acf_path)
    if reference_electrons is not None:
        if len(reference_electrons) != len(records):
            raise ValueError("reference_electrons count must match Bader atom count")
        if not all(math.isfinite(value) for value in reference_electrons):
            raise ValueError("reference_electrons contains non-finite values")
        for record, reference in zip(records, reference_electrons):
            record["reference_electrons"] = reference
            record["reference_minus_basin_electrons"] = reference - float(record["basin_electrons"])

    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    table_path = output_directory / "bader.csv"
    analysis_path = output_directory / "bader.analysis.json"
    plot_metadata_path = output_directory / "bader.plot.json"
    figure_path = figure_output.resolve() if figure_output is not None else output_directory / "bader.png"
    dataset_path = output_directory / "bader.dataset.json"
    _refuse_existing_outputs((table_path, analysis_path, plot_metadata_path, figure_path, dataset_path), overwrite)
    fields = [
        "atom_index", "x_angstrom", "y_angstrom", "z_angstrom", "basin_electrons",
        "min_distance_angstrom", "atomic_volume_angstrom3",
    ]
    if reference_electrons is not None:
        fields.extend(["reference_electrons", "reference_minus_basin_electrons"])
    _write_csv_atomic(table_path, fields, records)

    basin_sum = sum(float(record["basin_electrons"]) for record in records)
    reported_total = footer.get("number_of_electrons")
    closure_difference = None if reported_total is None else basin_sum + footer.get("vacuum_charge", 0.0) - reported_total
    closure_status = "not-run" if closure_difference is None else ("pass" if abs(closure_difference) <= electron_closure_tolerance else "warn")
    limitations = [
        "ACF.dat CHARGE is reported as basin electron population; it is not relabeled as an oxidation state or ionic charge.",
        "Reference-minus-basin values are emitted only when the caller supplies one explicit reference-electron value per atom.",
        "No chemical grouping, oxidation-state assignment, or material-specific interpretation is performed.",
    ]
    analysis = {
        "schema_version": "1.0",
        "atom_count": len(records),
        "basin_electron_sum": basin_sum,
        "footer": footer,
        "electron_closure_tolerance": electron_closure_tolerance,
        "electron_closure_difference": closure_difference,
        "electron_closure_status": closure_status,
        "reference_electrons_supplied": reference_electrons is not None,
        "reference_minus_basin_sum": None if reference_electrons is None else sum(float(record["reference_minus_basin_electrons"]) for record in records),
        "limitations": limitations,
    }
    write_json_atomic(analysis_path, analysis)
    plot_metadata = _plot_bader(records, reference_electrons is not None, figure_path)
    write_json_atomic(plot_metadata_path, plot_metadata)
    checks = [
        {"id": "atom-index", "status": "pass", "message": "Atom indices are consecutive from one."},
        {"id": "finite-table", "status": "pass", "message": "All parsed atom-table values are finite."},
        {
            "id": "electron-closure",
            "status": closure_status,
            "message": "Footer electron closure was not available." if closure_difference is None else f"Basin plus vacuum minus reported electrons = {closure_difference:.8g} e.",
        },
    ]
    dataset = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "observable": "real-space",
        "code": code,
        "maturity": maturity,
        "representation": "table",
        "source_files": [_source_record(acf_path, "bader-acf")],
        "dimensions": {"atoms": len(records), "rows": len(records)},
        "columns": [
            {"name": "atom_index", "dtype": "integer", "unit": None, "role": "atom-index"},
            {"name": "basin_electrons", "dtype": "float", "unit": "electron", "role": "bader-basin-population"},
            {"name": "reference_minus_basin_electrons", "dtype": "float", "unit": "electron", "role": "caller-reference-minus-basin"},
        ] if reference_electrons is not None else [
            {"name": "atom_index", "dtype": "integer", "unit": None, "role": "atom-index"},
            {"name": "basin_electrons", "dtype": "float", "unit": "electron", "role": "bader-basin-population"},
        ],
        "data_files": [
            _output_record(table_path, "normalized-table", "text/csv"),
            _output_record(analysis_path, "numerical-analysis", "application/json"),
            _output_record(plot_metadata_path, "plot-metadata", "application/json"),
        ],
        "transformations": [] if reference_electrons is None else [
            {
                "operation": "caller-reference-minus-basin",
                "parameters": {"reference_source": "explicit-cli-values"},
                "input_columns": ["reference_electrons", "basin_electrons"],
                "output_columns": ["reference_minus_basin_electrons"],
            }
        ],
        "validation": {"status": "warn" if closure_status == "warn" else "pass", "checks": checks},
        "limitations": limitations,
        "provenance": {"producer": "dftpost.bader-acf", "producer_version": __version__, "generated_utc": utc_now(), "tool_execution_ids": []},
    }
    _validated_dataset(dataset, dataset_path)
    return {"table": table_path, "analysis": analysis_path, "plot_metadata": plot_metadata_path, "figure": figure_path, "dataset": dataset_path}
