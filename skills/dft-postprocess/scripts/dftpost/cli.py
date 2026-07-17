from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .capabilities import detect_capabilities
from .electronic import normalize_qe_bands, normalize_qe_dos, normalize_qe_fatband, plot_bands_dos
from .inventory import build_inventory
from .manifests import build_artifact_manifest, validate_manifest
from .neb_optical import normalize_neb_table, normalize_optical_table
from .parsers import extract_summary
from .planning import build_postprocess_plan
from .plotting import plot_table
from .phonon_epc import normalize_qe_epc, normalize_qe_phonon
from .realspace import normalize_bader_acf, normalize_grid_field
from .registry import load_registry, validate_registry
from .runtrace import normalize_run_trace
from .utils import write_json_atomic
from .vasp_electronic import normalize_vasp_bands, normalize_vasp_dos, normalize_vasp_fatband


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dftpost", description="Deterministic QE/VASP postprocessing foundation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    capabilities = subparsers.add_parser("capabilities")
    capabilities.add_argument("--out", type=Path, required=True)

    registry = subparsers.add_parser("registry")
    registry.add_argument("--out", type=Path, required=True)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--plan-id", required=True)
    plan.add_argument("--observable", required=True)
    plan.add_argument("--code", choices=("qe", "vasp"), required=True)
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
    qe_fatband.add_argument("--marker-scale", type=float, default=45.0)
    qe_fatband.add_argument("--render-mode", choices=("line-width", "bubble"), default="line-width")
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
    vasp_fatband.add_argument("--marker-scale", type=float, default=45.0)
    vasp_fatband.add_argument("--render-mode", choices=("line-width", "bubble"), default="line-width")
    vasp_fatband.add_argument("--figure", type=Path)
    vasp_fatband.add_argument("--overwrite", action="store_true")
    vasp_fatband.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    vasp_fatband.add_argument("--out-dir", type=Path, required=True)

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
    grid_field.add_argument("--field-kind", choices=("charge-density", "electron-localization", "electrostatic-potential", "other"), required=True)
    grid_field.add_argument("--field-unit", required=True)
    grid_field.add_argument("--axis", type=int, choices=(0, 1, 2), default=2)
    grid_field.add_argument("--slice-index", type=int)
    grid_field.add_argument("--potential-to-ev", type=float)
    grid_field.add_argument("--fermi-energy-ev", type=float)
    grid_field.add_argument("--fermi-energy-file", type=Path)
    grid_field.add_argument("--vacuum-window", type=float, nargs=2, metavar=("MIN_ANGSTROM", "MAX_ANGSTROM"))
    grid_field.add_argument("--dataset-id", required=True)
    grid_field.add_argument("--figure", type=Path)
    grid_field.add_argument("--overwrite", action="store_true")
    grid_field.add_argument("--maturity", choices=("synthetic-validated", "format-fixture-validated", "real-artifact-validated"), default="format-fixture-validated")
    grid_field.add_argument("--out-dir", type=Path, required=True)

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
    bands_dos.add_argument("--dos-channel", action="append", default=[])
    bands_dos.add_argument("--energy-window", type=float, nargs=2, metavar=("MIN_EV", "MAX_EV"))
    bands_dos.add_argument("--out", type=Path, required=True)
    bands_dos.add_argument("--metadata-out", type=Path, required=True)
    bands_dos.add_argument("--overwrite", action="store_true")

    validate = subparsers.add_parser("validate-manifest")
    validate.add_argument("kind", choices=("run", "artifact", "campaign", "recommendation", "dataset", "plan", "execution"))
    validate.add_argument("manifest", type=Path)

    artifact = subparsers.add_parser("artifact-manifest")
    artifact.add_argument("--artifact-id", required=True)
    artifact.add_argument("--source-run-id", action="append", required=True)
    artifact.add_argument("--code", choices=("qe", "vasp", "mixed"), required=True)
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
                potential_to_ev=args.potential_to_ev,
                fermi_energy_ev=args.fermi_energy_ev,
                fermi_energy_path=args.fermi_energy_file,
                vacuum_window_angstrom=tuple(args.vacuum_window) if args.vacuum_window else None,
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
                dos_channel_labels=args.dos_channel or None,
                overwrite=args.overwrite,
            )
            metadata["command"] = list(sys.argv if argv is None else ["dftpost", *argv])
            write_json_atomic(args.metadata_out, metadata)
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
