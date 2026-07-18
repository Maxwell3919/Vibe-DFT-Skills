#!/usr/bin/env python3
"""Regenerate the synthetic, non-scientific figures embedded in the root README."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
IMAGES = ROOT / "docs" / "images"
CIF_ANALYZER = ROOT / "skills" / "cif-structure-analysis" / "scripts" / "analyze_cif.py"
DFTPOST = ROOT / "skills" / "dft-postprocess" / "scripts" / "dftpost_cli.py"


def run_checked(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def synthetic_layered_cif() -> str:
    """Return a 3x3 P1 MoS2-like layer used only for a visual demonstration."""
    rows = []
    site_index = 0
    base_sites = (
        ("Mo", 0.0, 0.0, 0.500),
        ("S", 1.0 / 3.0, 2.0 / 3.0, 0.370),
        ("S", 2.0 / 3.0, 1.0 / 3.0, 0.630),
    )
    for shift_a in range(3):
        for shift_b in range(3):
            for symbol, fractional_a, fractional_b, fractional_c in base_sites:
                site_index += 1
                rows.append(
                    f"{symbol}{site_index} {symbol} "
                    f"{(fractional_a + shift_a) / 3.0:.9f} "
                    f"{(fractional_b + shift_b) / 3.0:.9f} "
                    f"{fractional_c:.9f} 1.0"
                )
    return "\n".join(
        [
            "# Synthetic visualization fixture; not a research structure.",
            "data_showcase_layer",
            "_audit_creation_method 'DFT-Codex-Skills synthetic README showcase'",
            "_cell_length_a 9.540000",
            "_cell_length_b 9.540000",
            "_cell_length_c 12.000000",
            "_cell_angle_alpha 90.000000",
            "_cell_angle_beta 90.000000",
            "_cell_angle_gamma 120.000000",
            "_symmetry_space_group_name_H-M 'P 1'",
            "_symmetry_Int_Tables_number 1",
            "loop_",
            "_atom_site_label",
            "_atom_site_type_symbol",
            "_atom_site_fract_x",
            "_atom_site_fract_y",
            "_atom_site_fract_z",
            "_atom_site_occupancy",
            *rows,
            "",
        ]
    )


def gaussian(value: float, center: float, width: float, amplitude: float) -> float:
    return amplitude * math.exp(-0.5 * ((value - center) / width) ** 2)


def write_synthetic_electronic_tables(directory: Path) -> tuple[Path, Path]:
    bands_path = directory / "synthetic-bands.csv"
    dos_path = directory / "synthetic-dos.csv"

    with bands_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("k_index", "k_distance", "band_index", "energy_relative_ev"))
        for k_index in range(121):
            path_coordinate = 3.0 * k_index / 120.0
            phase = math.pi * path_coordinate
            energies = (
                -3.35 + 0.30 * math.cos(phase),
                -2.55 + 0.34 * math.sin(phase + 0.4),
                -1.65 + 0.36 * math.cos(phase * 1.35),
                -0.62 - 0.20 * math.cos(phase * 2.0),
                0.82 + 0.22 * math.cos(phase * 1.6 + 0.3),
                1.62 + 0.32 * math.sin(phase * 1.2),
                2.55 + 0.38 * math.cos(phase * 0.8 + 0.5),
                3.30 + 0.25 * math.sin(phase * 1.7),
            )
            for band_index, energy in enumerate(energies, start=1):
                writer.writerow((k_index, f"{path_coordinate:.8f}", band_index, f"{energy:.8f}"))

    with dos_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("energy_relative_ev", "channel_label", "channel_type", "dos_states_per_ev"))
        for index in range(321):
            energy = -4.0 + index * 0.025
            mo_d = (
                gaussian(energy, -1.45, 0.42, 1.65)
                + gaussian(energy, 1.25, 0.38, 1.35)
                + gaussian(energy, 2.55, 0.55, 0.85)
            )
            s_p = (
                gaussian(energy, -3.05, 0.45, 1.10)
                + gaussian(energy, -2.15, 0.40, 1.45)
                + gaussian(energy, 2.05, 0.48, 0.45)
            )
            total = mo_d + s_p + gaussian(energy, -0.75, 0.24, 0.35)
            writer.writerow((f"{energy:.8f}", "TDOS", "total", f"{total:.8f}"))
            writer.writerow((f"{energy:.8f}", "Mo d", "projected", f"{mo_d:.8f}"))
            writer.writerow((f"{energy:.8f}", "S p", "projected", f"{s_p:.8f}"))
    return bands_path, dos_path


def generate() -> dict[str, object]:
    IMAGES.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []
    with tempfile.TemporaryDirectory(prefix="dft-codex-showcase-") as temporary_name:
        temporary = Path(temporary_name)
        cif_path = temporary / "synthetic-layer.cif"
        cif_path.write_text(synthetic_layered_cif(), encoding="utf-8")
        view_directory = temporary / "views"
        run_checked(
            [
                sys.executable,
                str(CIF_ANALYZER),
                "--input",
                str(cif_path),
                "--json",
                str(temporary / "structure-manifest.json"),
                "--markdown",
                str(temporary / "structure-analysis.md"),
                "--views-dir",
                str(view_directory),
                "--match-elements",
                "Mo-S",
                "--match-bond-length",
                "2.41",
                "--match-bond-tolerance",
                "0.10",
            ]
        )
        structure_manifest = json.loads(
            (temporary / "structure-manifest.json").read_text(encoding="utf-8")
        )
        bond_match_status = structure_manifest["structure"]["nearest_distances"][
            "bond_length_match"
        ]["status"]
        if bond_match_status != "MATCHED":
            raise RuntimeError(
                f"synthetic showcase bond matcher returned {bond_match_status!r}, expected 'MATCHED'"
            )
        for axis in ("a", "b", "c"):
            destination = IMAGES / f"cif-layer-view-{axis}.png"
            shutil.copyfile(view_directory / f"view_along_{axis}.png", destination)
            destination.chmod(0o644)
            outputs.append(destination.relative_to(ROOT).as_posix())

        bands_path, dos_path = write_synthetic_electronic_tables(temporary)
        electronic_figure = IMAGES / "synthetic-bands-dos.png"
        run_checked(
            [
                sys.executable,
                str(DFTPOST),
                "bands-dos",
                "--bands-table",
                str(bands_path),
                "--dos-table",
                str(dos_path),
                "--energy-window",
                "-4",
                "4",
                "--out",
                str(electronic_figure),
                "--metadata-out",
                str(temporary / "synthetic-bands-dos.plot.json"),
                "--overwrite",
            ]
        )
        electronic_figure.chmod(0o644)
        outputs.append(electronic_figure.relative_to(ROOT).as_posix())

    return {
        "status": "ok",
        "fixture_scope": "synthetic visualization only; not scientific data",
        "outputs": outputs,
    }


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
