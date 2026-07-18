from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .band_views import plot_band_comparison, plot_projection_panels
from .capabilities import detect_capabilities
from .electronic import normalize_qe_bands, normalize_qe_dos, normalize_qe_fatband, plot_bands_dos
from .inventory import build_inventory
from .manifests import SCHEMAS, build_artifact_manifest, validate_manifest
from .neb_optical import normalize_neb_table, normalize_optical_table
from .parsers import extract_summary
from .planning import build_postprocess_plan
from .plotting import plot_table
from .phonon_epc import normalize_qe_epc, normalize_qe_phonon
from .realspace import combine_cube_grids, normalize_bader_acf, normalize_grid_field
from .registry import load_registry, registered_aggregate_codes, registered_codes, validate_registry
from .runtrace import normalize_run_trace
from .structure_views import render_structure_views
from .utils import write_json_atomic
from .vasp_electronic import normalize_vasp_bands, normalize_vasp_dos, normalize_vasp_fatband
from .vaspkit import normalize_vaspkit_bands
from .vesta import render_vesta_isosurface


def _key_value_mapping(specifications: list[str], label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for specification in specifications:
        if "=" not in specification:
            raise ValueError(f"{label} specifications must use key=value")
        key, value = specification.split("=", 1)
        if not key or not value:
            raise ValueError(f"{label} specifications require nonempty key and value")
        if key in result:
            raise ValueError(f"duplicate {label} key: {key}")
        result[key] = value
    return result


def _optical_component_mapping(specifications: list[str]) -> dict[str, tuple[str, str]]:
    raw = _key_value_mapping(specifications, "component")
    result: dict[str, tuple[str, str]] = {}
    for label, value in raw.items():
        columns = [item.strip() for item in value.split(",")]
        if len(columns) != 2 or not all(columns):
            raise ValueError("component specifications must use label=real_column,imaginary_column")
        result[label] = (columns[0], columns[1])
    return result


def _coefficient_paths(specifications: list[str]) -> list[tuple[float, Path]]:
    result: list[tuple[float, Path]] = []
    for specification in specifications:
        if "=" not in specification:
            raise ValueError("grid components must use coefficient=path")
        coefficient_text, path_text = specification.split("=", 1)
        if not coefficient_text or not path_text:
            raise ValueError("grid components require a nonempty coefficient and path")
        try:
            coefficient = float(coefficient_text)
        except ValueError as exc:
            raise ValueError(f"invalid grid coefficient: {coefficient_text}") from exc
        result.append((coefficient, Path(path_text)))
    return result


def _labeled_paths(specifications: list[str], label: str) -> list[tuple[str, Path]]:
    return [(key, Path(value)) for key, value in _key_value_mapping(specifications, label).items()]


def _float_mapping(specifications: list[str], label: str) -> dict[str, float]:
    result: dict[str, float] = {}
    for key, value in _key_value_mapping(specifications, label).items():
        try:
            result[key] = float(value)
        except ValueError as exc:
            raise ValueError(f"{label} value must be numeric: {key}={value}") from exc
    return result


def _bond_mapping(specifications: list[str]) -> dict[frozenset[str], float]:
    result: dict[frozenset[str], float] = {}
    for pair, value in _float_mapping(specifications, "bond").items():
        symbols = [item.strip() for item in pair.split("-")]
        if len(symbols) != 2 or not all(symbols):
            raise ValueError("bond specifications must use Element-Element=maximum_angstrom")
        key = frozenset(symbols)
        if key in result:
            raise ValueError(f"duplicate bond pair: {pair}")
        result[key] = value
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dftpost", description="Deterministic, maturity-gated DFT postprocessing foundation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    capabilities = subparsers.add_parser("capabilities")
    capabilities.add_argument("--out", type=Path, required=True)

    registry = subparsers.add_parser("registry")
    registry.add_argument("--out", type=Path, required=True)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--plan-id", required=True)
    plan.add_argument("--observable", required=True)
    plan.add_argument("--code", choices=registered_codes(), required=True)
    plan.add_argument("--source-root", type=Path, required=True)
    plan.add_argument("--output-root", type=Path, required=True)
    plan.add_argument("--evidence", action="append", default=[])
    plan.add_argument("--parameter", action="append", default=[])
    plan.add_argument("--out", type=Path, required=True)

    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("root", type=Path)
    inventory.add_argument("--out", type=Path, required=True)
    inventory.add_argument("--max-files", type=int, default=20000)
    inventory.add_argument("--hash-limit-mb", type=float, default=20.0)

    summary = subparsers.add_parser("extract-summary")
    summary.add_argument("output", type=Path)
    summary.add_argument("--code", choices=("auto", "qe", "vasp"), default="auto")
    summary.add_argument("--out", type=Path, required=True)

    run_trace = subparsers.add_parser("run-trace")
    run_trace.add_argument("output", type=Path)
    run_trace.add_argument("--code", choices=("qe", "vasp"), required=True)
    run_trace.add_argument("--dataset-id", required=True)
    run_trace.add_argument("--figure", type=Path)
    run_trace.add_argument("--overwrite", action="store_true")
    run_trace.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    run_trace.add_argument("--out-dir", type=Path, required=True)

    plot = subparsers.add_parser("plot-table")
    plot.add_argument("table", type=Path)
    plot.add_argument("--x", required=True)
    plot.add_argument("--y", required=True)
    plot.add_argument("--group")
    plot.add_argument("--xlabel", required=True)
    plot.add_argument("--ylabel", required=True)
    plot.add_argument("--title")
    plot.add_argument("--out", type=Path, required=True)
    plot.add_argument("--metadata-out", type=Path, required=True)

    qe_bands = subparsers.add_parser("qe-bands")
    qe_bands.add_argument("bands", type=Path)
    qe_bands.add_argument("--energy-reference", type=Path, required=True)
    qe_bands.add_argument("--dataset-id", required=True)
    qe_bands.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    qe_bands.add_argument("--figure", type=Path)
    qe_bands.add_argument("--overwrite", action="store_true")
    qe_bands.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    qe_bands.add_argument("--out-dir", type=Path, required=True)

    qe_dos = subparsers.add_parser("qe-dos")
    qe_dos.add_argument("dos", type=Path)
    qe_dos.add_argument("--energy-reference", type=Path)
    qe_dos.add_argument("--projected", type=Path, action="append", default=[])
    qe_dos.add_argument("--dataset-id", required=True)
    qe_dos.add_argument("--group-by", choices=("species", "orbital", "species-orbital", "atom", "atom-orbital"), default="species-orbital")
    qe_dos.add_argument("--integration-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    qe_dos.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    qe_dos.add_argument("--figure", type=Path)
    qe_dos.add_argument("--overwrite", action="store_true")
    qe_dos.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    qe_dos.add_argument("--out-dir", type=Path, required=True)

    qe_fatband = subparsers.add_parser("qe-fatband")
    qe_fatband.add_argument("bands", type=Path)
    qe_fatband.add_argument("--filproj", type=Path, required=True)
    qe_fatband.add_argument("--energy-reference", type=Path, required=True)
    qe_fatband.add_argument("--select", action="append", required=True)
    qe_fatband.add_argument("--dataset-id", required=True)
    qe_fatband.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    qe_fatband.add_argument("--marker-scale", type=float, default=8.0)
    qe_fatband.add_argument("--render-mode", choices=("line-width", "bubble"), default="line-width")
    qe_fatband.add_argument("--projection-label")
    qe_fatband.add_argument("--bands-label", default="Bands")
    qe_fatband.add_argument("--figure", type=Path)
    qe_fatband.add_argument("--overwrite", action="store_true")
    qe_fatband.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    qe_fatband.add_argument("--out-dir", type=Path, required=True)

    vasp_bands = subparsers.add_parser("vasp-bands")
    vasp_bands.add_argument("--eigenval", type=Path, required=True)
    vasp_bands.add_argument("--kpoints", type=Path, required=True)
    vasp_bands.add_argument("--poscar", type=Path, required=True)
    vasp_bands.add_argument("--outcar", type=Path, required=True)
    vasp_bands.add_argument("--dataset-id", required=True)
    vasp_bands.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    vasp_bands.add_argument("--figure", type=Path)
    vasp_bands.add_argument("--overwrite", action="store_true")
    vasp_bands.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    vasp_bands.add_argument("--out-dir", type=Path, required=True)

    vasp_dos = subparsers.add_parser("vasp-dos")
    vasp_dos.add_argument("--doscar", type=Path, required=True)
    vasp_dos.add_argument("--poscar", type=Path, required=True)
    vasp_dos.add_argument("--outcar", type=Path, required=True)
    vasp_dos.add_argument("--dataset-id", required=True)
    vasp_dos.add_argument("--group-by", choices=("species", "orbital", "species-orbital", "atom", "atom-orbital"), default="species-orbital")
    vasp_dos.add_argument("--integration-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    vasp_dos.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    vasp_dos.add_argument("--figure", type=Path)
    vasp_dos.add_argument("--overwrite", action="store_true")
    vasp_dos.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    vasp_dos.add_argument("--out-dir", type=Path, required=True)

    vasp_fatband = subparsers.add_parser("vasp-fatband")
    vasp_fatband.add_argument("--eigenval", type=Path, required=True)
    vasp_fatband.add_argument("--kpoints", type=Path, required=True)
    vasp_fatband.add_argument("--poscar", type=Path, required=True)
    vasp_fatband.add_argument("--outcar", type=Path, required=True)
    vasp_fatband.add_argument("--procar", type=Path, required=True)
    vasp_fatband.add_argument("--select", action="append", required=True)
    vasp_fatband.add_argument("--dataset-id", required=True)
    vasp_fatband.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    vasp_fatband.add_argument("--marker-scale", type=float, default=8.0)
    vasp_fatband.add_argument("--render-mode", choices=("line-width", "bubble"), default="line-width")
    vasp_fatband.add_argument("--projection-label")
    vasp_fatband.add_argument("--bands-label", default="Bands")
    vasp_fatband.add_argument("--figure", type=Path)
    vasp_fatband.add_argument("--overwrite", action="store_true")
    vasp_fatband.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    vasp_fatband.add_argument("--out-dir", type=Path, required=True)

    vaspkit_bands = subparsers.add_parser("vaspkit-bands")
    vaspkit_bands.add_argument("--band-data", type=Path, required=True)
    vaspkit_bands.add_argument("--klabels", type=Path, required=True)
    vaspkit_bands.add_argument("--energy-offset-ev", type=float, required=True)
    vaspkit_bands.add_argument("--energy-reference-description", required=True)
    vaspkit_bands.add_argument("--dataset-id", required=True)
    vaspkit_bands.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    vaspkit_bands.add_argument("--figure", type=Path)
    vaspkit_bands.add_argument("--overwrite", action="store_true")
    vaspkit_bands.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="synthetic-validated")
    vaspkit_bands.add_argument("--out-dir", type=Path, required=True)

    qe_phonon = subparsers.add_parser("qe-phonon")
    qe_phonon.add_argument("frequencies", type=Path)
    qe_phonon.add_argument("--frequency-unit", required=True)
    qe_phonon.add_argument("--imaginary-threshold", type=float, default=0.0)
    qe_phonon.add_argument("--dataset-id", required=True)
    qe_phonon.add_argument("--figure", type=Path)
    qe_phonon.add_argument("--overwrite", action="store_true")
    qe_phonon.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    qe_phonon.add_argument("--out-dir", type=Path, required=True)

    qe_epc = subparsers.add_parser("qe-epc")
    qe_epc.add_argument("--alpha2f", type=Path, required=True)
    qe_epc.add_argument("--lambda-table", type=Path, required=True)
    qe_epc.add_argument("--elph", type=Path, action="append", default=[])
    qe_epc.add_argument("--select-smearing-index", type=int, action="append", default=[])
    qe_epc.add_argument("--qmode-smearing-index", type=int, default=1)
    qe_epc.add_argument("--dataset-id", required=True)
    qe_epc.add_argument("--figure", type=Path)
    qe_epc.add_argument("--qmode-figure", type=Path)
    qe_epc.add_argument("--overwrite", action="store_true")
    qe_epc.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    qe_epc.add_argument("--out-dir", type=Path, required=True)

    grid_field = subparsers.add_parser("grid-field")
    grid_field.add_argument("grid", type=Path)
    grid_field.add_argument("--code", choices=("qe", "vasp", "mixed"), required=True)
    grid_field.add_argument("--field-kind", choices=("charge-density", "charge-density-difference", "electron-localization", "electrostatic-potential", "other"), required=True)
    grid_field.add_argument("--field-unit", required=True)
    grid_field.add_argument("--axis", type=int, choices=(0, 1, 2), default=2)
    grid_field.add_argument("--slice-index", type=int)
    grid_field.add_argument("--slice-hkl", type=int, nargs=3, metavar=("H", "K", "L"))
    grid_field.add_argument("--slice-offset", type=float)
    grid_field.add_argument("--slice-resolution", type=int, nargs=2, metavar=("NU", "NV"))
    grid_field.add_argument("--slice-origin", type=float, nargs=2, metavar=("U0", "V0"), default=(0.0, 0.0))
    grid_field.add_argument("--slice-window", type=float, nargs=4, metavar=("UMIN", "UMAX", "VMIN", "VMAX"))
    grid_field.add_argument("--atom-overlay", choices=("none", "near-plane", "all-projected"), default="near-plane")
    grid_field.add_argument("--atom-plane-tolerance", type=float)
    grid_field.add_argument("--no-atom-labels", action="store_true")
    grid_field.add_argument("--colormap")
    grid_field.add_argument("--value-range", type=float, nargs=2, metavar=("VMIN", "VMAX"))
    grid_field.add_argument("--potential-to-ev", type=float)
    grid_field.add_argument("--fermi-energy-ev", type=float)
    grid_field.add_argument("--fermi-energy-file", type=Path)
    grid_field.add_argument("--vacuum-window", type=float, nargs=2, metavar=("MIN_ANGSTROM", "MAX_ANGSTROM"))
    grid_field.add_argument("--dataset-id", required=True)
    grid_field.add_argument("--figure", type=Path)
    grid_field.add_argument("--slice-figure", type=Path)
    grid_field.add_argument("--overwrite", action="store_true")
    grid_field.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    grid_field.add_argument("--out-dir", type=Path, required=True)

    grid_combine = subparsers.add_parser("grid-combine")
    grid_combine.add_argument("--component", action="append", required=True, help="coefficient=path")
    grid_combine.add_argument("--field-unit", required=True)
    grid_combine.add_argument("--structure-component-index", type=int, default=0)
    grid_combine.add_argument("--code", choices=("qe", "vasp", "mixed"), default="mixed")
    grid_combine.add_argument("--dataset-id", required=True)
    grid_combine.add_argument("--overwrite", action="store_true")
    grid_combine.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    grid_combine.add_argument("--out-dir", type=Path, required=True)

    vesta_isosurface = subparsers.add_parser("vesta-isosurface")
    vesta_isosurface.add_argument("grid", type=Path)
    vesta_isosurface.add_argument("--code", choices=("qe", "vasp", "mixed"), required=True)
    vesta_isosurface.add_argument("--field-kind", required=True)
    vesta_isosurface.add_argument("--field-unit", required=True)
    vesta_isosurface.add_argument("--isosurface-level", type=float, required=True)
    vesta_isosurface.add_argument("--level-unit", required=True)
    vesta_isosurface.add_argument("--surface-mode", choices=("positive", "negative", "positive-negative"), default="positive-negative")
    vesta_isosurface.add_argument("--positive-color", type=int, nargs=3, metavar=("R", "G", "B"), default=(255, 210, 0))
    vesta_isosurface.add_argument("--negative-color", type=int, nargs=3, metavar=("R", "G", "B"), default=(0, 200, 255))
    vesta_isosurface.add_argument("--opacity-parallel", type=int, default=160)
    vesta_isosurface.add_argument("--opacity-perpendicular", type=int, default=230)
    vesta_isosurface.add_argument("--export-scale", type=int, default=2)
    vesta_isosurface.add_argument("--model-scale", type=float, default=2.0)
    vesta_isosurface.add_argument("--rotate", type=float, nargs=3, metavar=("X_DEG", "Y_DEG", "Z_DEG"), default=(0.0, 0.0, 0.0))
    vesta_isosurface.add_argument("--vesta-executable", type=Path)
    vesta_isosurface.add_argument("--timeout-seconds", type=float, default=30.0)
    vesta_isosurface.add_argument("--dataset-id", required=True)
    vesta_isosurface.add_argument("--figure", type=Path)
    vesta_isosurface.add_argument("--overwrite", action="store_true")
    vesta_isosurface.add_argument(
        "--maturity",
        choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated", "tool-integration-validated"),
        default="tool-integration-validated",
    )
    vesta_isosurface.add_argument("--out-dir", type=Path, required=True)

    bader_acf = subparsers.add_parser("bader-acf")
    bader_acf.add_argument("acf", type=Path)
    bader_acf.add_argument("--code", choices=("qe", "vasp", "mixed"), required=True)
    bader_acf.add_argument("--reference-electron", type=float, action="append", default=[])
    bader_acf.add_argument("--electron-closure-tolerance", type=float, default=1.0e-3)
    bader_acf.add_argument("--dataset-id", required=True)
    bader_acf.add_argument("--figure", type=Path)
    bader_acf.add_argument("--overwrite", action="store_true")
    bader_acf.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    bader_acf.add_argument("--out-dir", type=Path, required=True)

    neb_table = subparsers.add_parser("neb-table")
    neb_table.add_argument("table", type=Path)
    neb_table.add_argument("--code", choices=("qe", "vasp", "mixed"), required=True)
    neb_table.add_argument("--coordinate-column", required=True)
    neb_table.add_argument("--energy-column", required=True)
    neb_table.add_argument("--coordinate-unit", required=True)
    neb_table.add_argument("--energy-unit", required=True)
    neb_table.add_argument("--reference", choices=("initial", "minimum", "none"), required=True)
    neb_table.add_argument("--force-column")
    neb_table.add_argument("--force-unit")
    neb_table.add_argument("--dataset-id", required=True)
    neb_table.add_argument("--figure", type=Path)
    neb_table.add_argument("--overwrite", action="store_true")
    neb_table.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="synthetic-validated")
    neb_table.add_argument("--out-dir", type=Path, required=True)

    optical_table = subparsers.add_parser("optical-table")
    optical_table.add_argument("table", type=Path)
    optical_table.add_argument("--code", choices=("qe", "vasp", "mixed"), required=True)
    optical_table.add_argument("--energy-column", required=True)
    optical_table.add_argument("--component", action="append", required=True)
    optical_table.add_argument("--broadening", required=True)
    optical_table.add_argument("--dataset-id", required=True)
    optical_table.add_argument("--figure", type=Path)
    optical_table.add_argument("--overwrite", action="store_true")
    optical_table.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="synthetic-validated")
    optical_table.add_argument("--out-dir", type=Path, required=True)

    bands_dos = subparsers.add_parser("bands-dos")
    bands_dos.add_argument("--bands-table", type=Path, required=True)
    bands_dos.add_argument("--dos-table", type=Path, required=True)
    bands_dos.add_argument(
        "--pdos-channel",
        action="append",
        default=[],
        help="projected DOS channel to include; repeat as needed (default: all projected channels)",
    )
    bands_dos.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    bands_dos.add_argument("--out", type=Path, required=True)
    bands_dos.add_argument("--metadata-out", type=Path, required=True)
    bands_dos.add_argument("--overwrite", action="store_true")

    bands_compare = subparsers.add_parser("bands-compare")
    bands_compare.add_argument("--series", action="append", required=True, help="repeat label=normalized-bands.csv")
    bands_compare.add_argument("--series-metadata", action="append", default=[], help="optional matching label=bands.plot.json")
    bands_compare.add_argument("--layout", choices=("row", "column"), default="row")
    bands_compare.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    bands_compare.add_argument("--out", type=Path, required=True)
    bands_compare.add_argument("--metadata-out", type=Path, required=True)
    bands_compare.add_argument("--overwrite", action="store_true")

    band_projections = subparsers.add_parser("band-projections")
    band_projections.add_argument("--bands-table", type=Path, required=True)
    band_projections.add_argument("--projection", action="append", required=True, help="repeat label=normalized-fatband.csv")
    band_projections.add_argument("--bands-metadata", type=Path)
    band_projections.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    band_projections.add_argument("--render-mode", choices=("line-width", "bubble"), default="line-width")
    band_projections.add_argument("--marker-scale", type=float, default=8.0)
    band_projections.add_argument("--bands-label", default="Bands")
    band_projections.add_argument("--panels-out", type=Path, required=True)
    band_projections.add_argument("--overview-out", type=Path)
    band_projections.add_argument("--metadata-out", type=Path, required=True)
    band_projections.add_argument("--overwrite", action="store_true")

    structure_views = subparsers.add_parser("structure-views")
    structure_views.add_argument("structures", nargs="+", type=Path)
    structure_views.add_argument("--bond-mode", choices=("none", "covalent", "explicit"), default="covalent")
    structure_views.add_argument("--bond-scale", type=float, default=1.15)
    structure_views.add_argument("--bond", action="append", default=[], help="explicit Element-Element=maximum_angstrom")
    structure_views.add_argument("--element-color", action="append", default=[], help="repeat Element=#RRGGBB")
    structure_views.add_argument("--element-radius", action="append", default=[], help="repeat Element=radius_angstrom")
    structure_views.add_argument("--overwrite", action="store_true")
    structure_views.add_argument("--out-dir", type=Path, required=True)

    validate = subparsers.add_parser("validate-manifest")
    validate.add_argument("kind", choices=tuple(sorted(SCHEMAS)))
    validate.add_argument("manifest", type=Path)

    artifact = subparsers.add_parser("artifact-manifest")
    artifact.add_argument("--artifact-id", required=True)
    artifact.add_argument("--source-run-id", action="append", required=True)
    artifact.add_argument("--code", choices=registered_codes() + registered_aggregate_codes(), required=True)
    artifact.add_argument("--artifact-type", required=True)
    artifact.add_argument("--status", choices=("complete", "partial", "failed", "blocked"), required=True)
    artifact.add_argument("--artifact-root", type=Path, required=True)
    artifact.add_argument("--data", action="append", default=[])
    artifact.add_argument("--figure", action="append", default=[])
    artifact.add_argument("--validation-status", choices=("pass", "warn", "block"), required=True)
    artifact.add_argument("--check", action="append", default=[])
    artifact.add_argument("--claim-boundary", action="append", default=[])
    artifact.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "capabilities":
            write_json_atomic(args.out, detect_capabilities())
        elif args.command == "registry":
            registry = load_registry()
            failures = validate_registry(registry)
            if failures:
                raise ValueError("invalid observable registry: " + "; ".join(failures))
            write_json_atomic(args.out, registry)
        elif args.command == "plan":
            evidence = _key_value_mapping(args.evidence, "evidence")
            parameters = _key_value_mapping(args.parameter, "parameter")
            plan = build_postprocess_plan(
                args.plan_id,
                args.observable,
                args.code,
                args.source_root,
                args.output_root,
                evidence,
                detect_capabilities(),
                parameters,
            )
            write_json_atomic(args.out, plan)
        elif args.command == "inventory":
            write_json_atomic(args.out, build_inventory(args.root, args.max_files, int(args.hash_limit_mb * 1024 * 1024)))
        elif args.command == "extract-summary":
            write_json_atomic(args.out, extract_summary(args.output, args.code))
        elif args.command == "run-trace":
            outputs = normalize_run_trace(
                args.output,
                args.code,
                args.out_dir,
                args.dataset_id,
                figure_output=args.figure,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "plot-table":
            style = Path(__file__).resolve().parents[2] / "assets" / "dft-publication.mplstyle"
            metadata = plot_table(args.table, args.out, args.x, args.y, args.group, args.xlabel, args.ylabel, args.title, style)
            metadata["command"] = list(sys.argv if argv is None else ["dftpost", *argv])
            write_json_atomic(args.metadata_out, metadata)
        elif args.command == "qe-bands":
            outputs = normalize_qe_bands(
                args.bands,
                args.energy_reference,
                args.out_dir,
                args.dataset_id,
                figure_output=args.figure,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "qe-dos":
            outputs = normalize_qe_dos(
                args.dos,
                args.projected,
                args.out_dir,
                args.dataset_id,
                energy_reference_path=args.energy_reference,
                figure_output=args.figure,
                group_by=args.group_by,
                integration_window_ev=tuple(args.integration_window) if args.integration_window else None,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "qe-fatband":
            outputs = normalize_qe_fatband(
                args.bands,
                args.filproj,
                args.energy_reference,
                args.out_dir,
                args.dataset_id,
                _key_value_mapping(args.select, "selector"),
                figure_output=args.figure,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                marker_scale=args.marker_scale,
                render_mode=args.render_mode,
                projection_label=args.projection_label,
                bands_label=args.bands_label,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "vasp-bands":
            outputs = normalize_vasp_bands(
                args.eigenval,
                args.kpoints,
                args.poscar,
                args.outcar,
                args.out_dir,
                args.dataset_id,
                figure_output=args.figure,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "vasp-dos":
            outputs = normalize_vasp_dos(
                args.doscar,
                args.poscar,
                args.outcar,
                args.out_dir,
                args.dataset_id,
                figure_output=args.figure,
                group_by=args.group_by,
                integration_window_ev=tuple(args.integration_window) if args.integration_window else None,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "vasp-fatband":
            outputs = normalize_vasp_fatband(
                args.eigenval,
                args.kpoints,
                args.poscar,
                args.outcar,
                args.procar,
                args.out_dir,
                args.dataset_id,
                _key_value_mapping(args.select, "selector"),
                figure_output=args.figure,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                marker_scale=args.marker_scale,
                render_mode=args.render_mode,
                projection_label=args.projection_label,
                bands_label=args.bands_label,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "vaspkit-bands":
            outputs = normalize_vaspkit_bands(
                args.band_data,
                args.klabels,
                args.out_dir,
                args.dataset_id,
                energy_offset_ev=args.energy_offset_ev,
                energy_reference_description=args.energy_reference_description,
                figure_output=args.figure,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "qe-phonon":
            outputs = normalize_qe_phonon(
                args.frequencies,
                args.out_dir,
                args.dataset_id,
                frequency_unit=args.frequency_unit,
                imaginary_threshold=args.imaginary_threshold,
                figure_output=args.figure,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "qe-epc":
            outputs = normalize_qe_epc(
                args.alpha2f,
                args.lambda_table,
                args.elph,
                args.out_dir,
                args.dataset_id,
                selected_smearing_indices=args.select_smearing_index or None,
                qmode_smearing_index=args.qmode_smearing_index,
                figure_output=args.figure,
                qmode_figure_output=args.qmode_figure,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "grid-field":
            outputs = normalize_grid_field(
                args.grid,
                args.code,
                args.out_dir,
                args.dataset_id,
                field_kind=args.field_kind,
                field_unit=args.field_unit,
                axis=args.axis,
                slice_index=args.slice_index,
                slice_hkl=tuple(args.slice_hkl) if args.slice_hkl else None,
                slice_offset=args.slice_offset,
                slice_resolution=tuple(args.slice_resolution) if args.slice_resolution else None,
                slice_origin=tuple(args.slice_origin),
                slice_window=tuple(args.slice_window) if args.slice_window else None,
                atom_overlay=args.atom_overlay,
                atom_plane_tolerance_angstrom=args.atom_plane_tolerance,
                atom_labels=not args.no_atom_labels,
                colormap=args.colormap,
                value_range=tuple(args.value_range) if args.value_range else None,
                potential_to_ev=args.potential_to_ev,
                fermi_energy_ev=args.fermi_energy_ev,
                fermi_energy_path=args.fermi_energy_file,
                vacuum_window_angstrom=tuple(args.vacuum_window) if args.vacuum_window else None,
                figure_output=args.figure,
                slice_figure_output=args.slice_figure,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "grid-combine":
            outputs = combine_cube_grids(
                _coefficient_paths(args.component),
                args.out_dir,
                args.dataset_id,
                field_unit=args.field_unit,
                structure_component_index=args.structure_component_index,
                code=args.code,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "vesta-isosurface":
            outputs = render_vesta_isosurface(
                args.grid,
                args.code,
                args.out_dir,
                args.dataset_id,
                field_kind=args.field_kind,
                field_unit=args.field_unit,
                level=args.isosurface_level,
                level_unit=args.level_unit,
                mode=args.surface_mode,
                positive_color=tuple(args.positive_color),
                negative_color=tuple(args.negative_color),
                opacity_parallel=args.opacity_parallel,
                opacity_perpendicular=args.opacity_perpendicular,
                export_scale=args.export_scale,
                model_scale=args.model_scale,
                rotations_degrees=tuple(args.rotate),
                executable=args.vesta_executable,
                timeout_seconds=args.timeout_seconds,
                figure_output=args.figure,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "bader-acf":
            outputs = normalize_bader_acf(
                args.acf,
                args.code,
                args.out_dir,
                args.dataset_id,
                reference_electrons=args.reference_electron or None,
                electron_closure_tolerance=args.electron_closure_tolerance,
                figure_output=args.figure,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "neb-table":
            outputs = normalize_neb_table(
                args.table,
                args.code,
                args.out_dir,
                args.dataset_id,
                coordinate_column=args.coordinate_column,
                energy_column=args.energy_column,
                coordinate_unit=args.coordinate_unit,
                energy_unit=args.energy_unit,
                reference=args.reference,
                force_column=args.force_column,
                force_unit=args.force_unit,
                figure_output=args.figure,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "optical-table":
            outputs = normalize_optical_table(
                args.table,
                args.code,
                args.out_dir,
                args.dataset_id,
                energy_column=args.energy_column,
                components=_optical_component_mapping(args.component),
                broadening_declaration=args.broadening,
                figure_output=args.figure,
                maturity=args.maturity,
                overwrite=args.overwrite,
            )
            print(json.dumps({key: str(value) for key, value in outputs.items()}, sort_keys=True))
            return 0
        elif args.command == "bands-dos":
            if args.metadata_out.exists() and not args.overwrite:
                raise ValueError(f"refusing to overwrite output: {args.metadata_out}")
            metadata = plot_bands_dos(
                args.bands_table,
                args.dos_table,
                args.out,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                pdos_channel_labels=args.pdos_channel or None,
                overwrite=args.overwrite,
            )
            metadata["command"] = list(sys.argv if argv is None else ["dftpost", *argv])
            write_json_atomic(args.metadata_out, metadata)
        elif args.command == "bands-compare":
            if args.metadata_out.exists() and not args.overwrite:
                raise ValueError(f"refusing to overwrite output: {args.metadata_out}")
            metadata = plot_band_comparison(
                _labeled_paths(args.series, "series"),
                args.out,
                metadata_paths={label: path for label, path in _labeled_paths(args.series_metadata, "series metadata")},
                layout=args.layout,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                overwrite=args.overwrite,
            )
            metadata["command"] = list(sys.argv if argv is None else ["dftpost", *argv])
            write_json_atomic(args.metadata_out, metadata)
        elif args.command == "band-projections":
            if args.metadata_out.exists() and not args.overwrite:
                raise ValueError(f"refusing to overwrite output: {args.metadata_out}")
            metadata = plot_projection_panels(
                args.bands_table,
                _labeled_paths(args.projection, "projection"),
                args.panels_out,
                overview_output=args.overview_out,
                bands_metadata_path=args.bands_metadata,
                energy_window_ev=tuple(args.energy_window) if args.energy_window else None,
                render_mode=args.render_mode,
                marker_scale=args.marker_scale,
                bands_label=args.bands_label,
                overwrite=args.overwrite,
            )
            metadata["command"] = list(sys.argv if argv is None else ["dftpost", *argv])
            write_json_atomic(args.metadata_out, metadata)
            print(args.panels_out)
            return 0
        elif args.command == "structure-views":
            outputs = render_structure_views(
                args.structures,
                args.out_dir,
                bond_mode=args.bond_mode,
                bond_scale=args.bond_scale,
                explicit_bond_limits=_bond_mapping(args.bond),
                element_colors=_key_value_mapping(args.element_color, "element color"),
                element_radii_angstrom=_float_mapping(args.element_radius, "element radius"),
                overwrite=args.overwrite,
            )
            print(json.dumps({
                "figures": [str(path) for path in outputs["figures"]],
                "overview": str(outputs["overview"]),
                "metadata": str(outputs["metadata"]),
            }, sort_keys=True))
            return 0
        elif args.command == "validate-manifest":
            errors = validate_manifest(args.kind, args.manifest)
            if errors:
                for item in errors:
                    print(item, file=sys.stderr)
                return 2
            print(f"PASS: {args.manifest}")
            return 0
        elif args.command == "artifact-manifest":
            manifest = build_artifact_manifest(
                args.artifact_id,
                args.source_run_id,
                args.code,
                args.artifact_type,
                args.status,
                args.artifact_root,
                args.data,
                args.figure,
                args.validation_status,
                args.check,
                args.claim_boundary,
                list(sys.argv if argv is None else ["dftpost", *argv]),
            )
            write_json_atomic(args.out, manifest)
        else:
            raise AssertionError(args.command)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
