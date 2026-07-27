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
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
IMAGES = ROOT / "docs" / "images"
CIF_ANALYZER = ROOT / "skills" / "cif-structure-analysis" / "scripts" / "analyze_cif.py"
DFTPOST = ROOT / "skills" / "dft-postprocess" / "scripts" / "dftpost_cli.py"
PLOT_STYLE = ROOT / "skills" / "dft-postprocess" / "assets" / "dft-publication.mplstyle"
SOFTWARE_REGISTRY = ROOT / "registry" / "software-registry.yaml"

INK = "#18202d"
OXIDE = "#8b2525"
BLUE = "#0b6fa4"
TEAL = "#4fb6b8"
GOLD = "#e3a000"
PALE_BLUE = "#e8f2f7"
PALE_GOLD = "#fbf1d5"
PALE_GRAY = "#f3f4f6"


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
            "_audit_creation_method 'Vibe-DFT-Skills synthetic README showcase'",
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


def convergence_series() -> dict[str, list[float]]:
    """Return deterministic synthetic convergence traces for visual use."""
    cutoffs = [30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
    delta_energy = [18.4, 8.7, 3.9, 1.7, 0.72, 0.29, 0.12]
    force_error = [58.0, 31.0, 16.0, 7.8, 3.4, 1.5, 0.68]
    k_mesh = [3.0, 5.0, 7.0, 9.0, 11.0, 13.0]
    k_energy = [14.2, 6.1, 2.5, 0.91, 0.34, 0.13]
    return {
        "cutoffs": cutoffs,
        "delta_energy": delta_energy,
        "force_error": force_error,
        "k_mesh": k_mesh,
        "k_energy": k_energy,
    }


def save_figure(figure: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        destination,
        dpi=220,
        facecolor="white",
        metadata={
            "Software": "Vibe-DFT-Skills deterministic README showcase",
            "Title": "Synthetic demonstration; not scientific data",
        },
    )
    destination.chmod(0o644)


def generate_convergence_figure(destination: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    series = convergence_series()
    with plt.style.context(str(PLOT_STYLE)):
        figure, axes = plt.subplots(1, 3, figsize=(12.4, 3.8))
        energy_axis, sampling_axis, force_axis = axes

        energy_axis.semilogy(
            series["cutoffs"],
            series["delta_energy"],
            marker="o",
            color=OXIDE,
        )
        energy_axis.axhline(1.0, color=INK, linestyle="--", linewidth=1.0)
        energy_axis.set_xlabel("representation cutoff (Ry)")
        energy_axis.set_ylabel(r"change in energy (meV atom$^{-1}$)")
        energy_axis.set_title("(a) basis or grid")

        sampling_axis.semilogy(
            series["k_mesh"],
            series["k_energy"],
            marker="s",
            color=BLUE,
        )
        sampling_axis.axhline(1.0, color=INK, linestyle="--", linewidth=1.0)
        sampling_axis.set_xlabel(r"uniform $k$-mesh ($N \times N \times 1$)")
        sampling_axis.set_ylabel(r"change in energy (meV atom$^{-1}$)")
        sampling_axis.set_title("(b) Brillouin-zone sampling")

        force_axis.semilogy(
            series["cutoffs"],
            series["force_error"],
            marker="o",
            color=TEAL,
        )
        force_axis.axhline(2.0, color=INK, linestyle="--", linewidth=1.0)
        force_axis.set_xlabel("plane-wave or grid cutoff (Ry)")
        force_axis.set_ylabel(r"change in max force (meV $\AA^{-1}$)")
        force_axis.set_title("(c) force-sensitive convergence")

        figure.suptitle(
            "Observable-specific convergence on a synthetic dataset",
            fontsize=12,
            y=1.02,
        )
        figure.text(
            0.5,
            -0.02,
            "Illustrative traces only; thresholds and values are not recommendations.",
            ha="center",
            fontsize=8.5,
            color="#505762",
        )
        figure.tight_layout()
        save_figure(figure, destination)
        plt.close(figure)


def _software_groups() -> list[tuple[str, list[str]]]:
    import yaml

    registry = yaml.safe_load(SOFTWARE_REGISTRY.read_text(encoding="utf-8"))
    combined = {
        **registry.get("software", {}),
        **registry.get("planned_software", {}),
    }
    role_titles = [
        ("calculation-engine", "Electronic structure\nand atomistic engines"),
        ("ml-potential-framework", "Machine-learned\ninteratomic potentials"),
        ("postprocess-tool", "Phonons, wavefunctions,\nand postprocessing"),
        ("structure-library", "Structure construction and chemistry"),
        ("scientific-workflow-tool", "Kinetics and scientific workflows"),
        ("visualization-tool", "Trajectory analysis and visualization"),
    ]
    groups: list[tuple[str, list[str]]] = []
    for role, title in role_titles:
        names = [
            str(metadata["display_name"])
            for metadata in combined.values()
            if metadata.get("role", "calculation-engine") == role
        ]
        if names:
            groups.append((title, names))
    expected = len(combined)
    observed = sum(len(names) for _, names in groups)
    if observed != expected:
        raise RuntimeError(
            f"software landscape grouped {observed} identities, expected {expected}"
        )
    return groups


def generate_software_landscape(destination: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    groups = _software_groups()
    with plt.style.context(str(PLOT_STYLE)):
        figure, axis = plt.subplots(figsize=(12.0, 6.5))
        axis.set_xlim(0.0, 12.0)
        axis.set_ylim(0.0, 7.1)
        axis.axis("off")
        axis.set_title(
            "Scientific software represented in the repository registry",
            loc="left",
            fontsize=14,
            color=INK,
            pad=14,
        )
        axis.text(
            0.0,
            6.72,
            "Equal visual treatment; current repository involvement is reported in the README table.",
            fontsize=9,
            color="#505762",
        )

        columns = 3
        box_width = 3.72
        box_height = 2.55
        x_gap = 0.25
        y_positions = [3.75, 0.72]
        fills = [PALE_BLUE, PALE_GOLD, PALE_GRAY, "#eef6ed", "#f4ecf6", "#f6eeee"]
        for index, (title, names) in enumerate(groups):
            row, column = divmod(index, columns)
            x = column * (box_width + x_gap)
            y = y_positions[row]
            box = FancyBboxPatch(
                (x, y),
                box_width,
                box_height,
                boxstyle="round,pad=0.04,rounding_size=0.06",
                linewidth=0.9,
                edgecolor="#8b929c",
                facecolor=fills[index],
            )
            axis.add_patch(box)
            axis.text(
                x + 0.18,
                y + box_height - 0.28,
                title,
                fontsize=10.5,
                fontweight="bold",
                color=INK,
                va="top",
            )
            lines: list[str] = []
            current = ""
            for name in names:
                candidate = name if not current else f"{current} · {name}"
                if len(candidate) > 41:
                    lines.append(current)
                    current = name
                else:
                    current = candidate
            if current:
                lines.append(current)
            axis.text(
                x + 0.18,
                y + box_height - 0.70,
                "\n".join(lines),
                fontsize=9.2,
                color=INK,
                va="top",
                linespacing=1.45,
            )

        axis.text(
            12.0,
            0.12,
            "23 registered identities · generated from registry/software-registry.yaml",
            ha="right",
            fontsize=8.5,
            color="#505762",
        )
        figure.tight_layout()
        save_figure(figure, destination)
        plt.close(figure)


def generate_evidence_workflow_figure(destination: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Polygon

    with plt.style.context(str(PLOT_STYLE)):
        figure, axes = plt.subplots(
            1,
            3,
            figsize=(13.2, 4.3),
            gridspec_kw={"width_ratios": [1.0, 1.12, 1.55]},
        )
        structure_axis, convergence_axis, electronic_axis = axes

        # Panel A: a compact, synthetic MX2 layer built from the same fixture
        # that is validated by the CIF analyzer earlier in this script.
        structure_axis.set_aspect("equal")
        structure_axis.axis("off")
        a_vector = (1.0, 0.0)
        b_vector = (0.5, math.sqrt(3.0) / 2.0)
        mo_sites: list[tuple[float, float]] = []
        s_sites: list[tuple[float, float]] = []
        for i in range(4):
            for j in range(4):
                x = i * a_vector[0] + j * b_vector[0]
                y = i * a_vector[1] + j * b_vector[1]
                mo_sites.append((x, y))
                s_sites.append((x + 0.5, y + math.sqrt(3.0) / 6.0))
        for mx, my in mo_sites:
            nearest = sorted(
                s_sites,
                key=lambda site: (site[0] - mx) ** 2 + (site[1] - my) ** 2,
            )[:3]
            for sx, sy in nearest:
                if (sx - mx) ** 2 + (sy - my) ** 2 < 0.55:
                    structure_axis.plot([mx, sx], [my, sy], color="#b6bac0", linewidth=1.1)
        structure_axis.scatter(
            [site[0] for site in s_sites],
            [site[1] for site in s_sites],
            s=68,
            color=GOLD,
            edgecolor=INK,
            linewidth=0.65,
            zorder=3,
            label="X",
        )
        structure_axis.scatter(
            [site[0] for site in mo_sites],
            [site[1] for site in mo_sites],
            s=92,
            color=TEAL,
            edgecolor=INK,
            linewidth=0.65,
            zorder=4,
            label="M",
        )
        cell = Polygon(
            [[0, 0], [3, 0], [4.5, 3 * math.sqrt(3.0) / 2.0], [1.5, 3 * math.sqrt(3.0) / 2.0]],
            closed=True,
            fill=False,
            edgecolor=OXIDE,
            linewidth=1.25,
        )
        structure_axis.add_patch(cell)
        structure_axis.legend(loc="lower right", fontsize=8, handletextpad=0.3)
        structure_axis.set_title("(a) traceable structure", fontsize=11)

        # Panel B: two numerical dimensions and explicit target bands.
        series = convergence_series()
        convergence_axis.semilogy(
            series["cutoffs"],
            [value / 1.0 for value in series["delta_energy"]],
            marker="o",
            color=OXIDE,
            label=r"$|\Delta E| / 1$ meV atom$^{-1}$",
        )
        convergence_axis.semilogy(
            series["cutoffs"],
            [value / 2.0 for value in series["force_error"]],
            marker="s",
            color=BLUE,
            label=r"$|\Delta F_{\max}| / 2$ meV $\AA^{-1}$",
        )
        convergence_axis.axhspan(0.08, 1.0, color=PALE_BLUE, alpha=0.9)
        convergence_axis.axhline(1.0, color=INK, linestyle="--", linewidth=0.9)
        convergence_axis.set_xlabel("representation cutoff (Ry)")
        convergence_axis.set_ylabel("error / target tolerance")
        convergence_axis.set_title("(b) observable convergence", fontsize=11)
        convergence_axis.legend(fontsize=8)

        # Panel C: a simplified band path plus a provenance record.
        electronic_axis.set_xlim(0.0, 3.0)
        electronic_axis.set_ylim(-2.6, 2.8)
        x_values = [3.0 * index / 160.0 for index in range(161)]
        for band_index in range(7):
            center = -2.15 + 0.72 * band_index
            phase = 0.35 * band_index
            energy = [
                center + (0.17 + 0.025 * band_index) * math.cos(math.pi * x + phase)
                for x in x_values
            ]
            electronic_axis.plot(x_values, energy, color=OXIDE, linewidth=1.15)
        for boundary in (0.0, 1.0, 2.0, 3.0):
            electronic_axis.axvline(boundary, color="#9ca2aa", linewidth=0.7)
        electronic_axis.axhline(0.0, color=INK, linestyle="--", linewidth=0.9)
        electronic_axis.set_xticks([0.0, 1.0, 2.0, 3.0], [r"$\Gamma$", "M", "K", r"$\Gamma$"])
        electronic_axis.set_ylabel(r"$E-E_{\mathrm{ref}}$ (eV)")
        electronic_axis.set_title("(c) normalized observable", fontsize=11)
        record = FancyBboxPatch(
            (1.93, -2.30),
            0.92,
            0.83,
            boxstyle="round,pad=0.05,rounding_size=0.04",
            linewidth=0.8,
            edgecolor=BLUE,
            facecolor=PALE_BLUE,
            transform=electronic_axis.transData,
        )
        electronic_axis.add_patch(record)
        electronic_axis.text(
            2.39,
            -1.88,
            "parent hash\nunits · zero\nplot metadata",
            ha="center",
            va="center",
            fontsize=7.8,
            color=INK,
        )

        figure.suptitle(
            "From a structure model to a reviewable DFT claim",
            fontsize=14,
            color=INK,
            y=1.02,
        )
        figure.text(
            0.5,
            -0.01,
            "Synthetic demonstration generated by repository code; no material result is asserted.",
            ha="center",
            fontsize=8.5,
            color="#505762",
        )
        figure.tight_layout()
        save_figure(figure, destination)
        plt.close(figure)


def generate() -> dict[str, object]:
    IMAGES.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []
    with tempfile.TemporaryDirectory(prefix="vibe-dft-showcase-") as temporary_name:
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

        convergence_figure = IMAGES / "synthetic-convergence.png"
        generate_convergence_figure(convergence_figure)
        outputs.append(convergence_figure.relative_to(ROOT).as_posix())

        software_landscape = IMAGES / "software-landscape.png"
        generate_software_landscape(software_landscape)
        outputs.append(software_landscape.relative_to(ROOT).as_posix())

        evidence_workflow = IMAGES / "dft-evidence-workflow.png"
        generate_evidence_workflow_figure(evidence_workflow)
        outputs.append(evidence_workflow.relative_to(ROOT).as_posix())

    return {
        "status": "ok",
        "fixture_scope": "synthetic visualization only; not scientific data",
        "outputs": outputs,
    }


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
