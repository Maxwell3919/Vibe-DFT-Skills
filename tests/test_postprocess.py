from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
POST_SCRIPTS = ROOT / "skills" / "dft-postprocess" / "scripts"
sys.path.insert(0, str(POST_SCRIPTS))

from dftpost.capabilities import detect_capabilities  # noqa: E402
from dftpost.inventory import build_inventory  # noqa: E402
from dftpost.manifests import build_artifact_manifest, validation_errors  # noqa: E402
from dftpost.parsers import extract_summary  # noqa: E402
from dftpost.plotting import plot_table  # noqa: E402


class PostprocessTests(unittest.TestCase):
    def test_cli_capabilities_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capabilities.json"
            result = subprocess.run(
                [sys.executable, str(POST_SCRIPTS / "dftpost_cli.py"), "capabilities", "--out", str(output)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("external_tools", json.loads(output.read_text()))

    def test_capability_shape(self) -> None:
        result = detect_capabilities()
        self.assertIn("qe.bands", result["external_tools"])
        self.assertIn("matplotlib", result["python_packages"])

    def test_inventory_redacts_potcar_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.joinpath("INCAR").write_text("ENCUT=400\n")
            root.joinpath("POTCAR").write_text("licensed placeholder\n")
            result = build_inventory(root)
            files = {item["path"]: item for item in result["files"]}
            self.assertEqual(result["code"], "vasp")
            self.assertIsNone(files["POTCAR"]["sha256"])
            self.assertEqual(files["POTCAR"]["hash_status"], "redacted-licensed")

    def test_extract_qe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pw.out"
            output.write_text(
                "Program PWSCF v.7.5 starts\niteration # 1\nconvergence has been achieved\n"
                "!    total energy              =   -10.000000 Ry\nJOB DONE.\n"
            )
            result = extract_summary(output)
            self.assertEqual(result["code"], "qe")
            self.assertTrue(result["completed"])
            self.assertAlmostEqual(result["final_energy_ev"], -136.05693122994)

    def test_extract_vasp_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "OUTCAR"
            output.write_text(
                "vasp.6.4.3\nfree  energy   TOTEN  =       -5.500000 eV\n"
                "reached required accuracy\nGeneral timing and accounting informations for this job\n"
            )
            result = extract_summary(output)
            self.assertEqual(result["code"], "vasp")
            self.assertTrue(result["completed"])
            self.assertEqual(result["final_energy_ev"], -5.5)

    def test_plot_and_artifact_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table = root / "dos.csv"
            with table.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=("energy_ev", "dos"))
                writer.writeheader()
                writer.writerows([{"energy_ev": -1, "dos": 0.2}, {"energy_ev": 0, "dos": 1.0}, {"energy_ev": 1, "dos": 0.3}])
            figure = root / "dos.png"
            style = ROOT / "skills" / "dft-postprocess" / "assets" / "dft-publication.mplstyle"
            metadata = plot_table(table, figure, "energy_ev", "dos", None, "Energy (eV)", "DOS", None, style)
            metadata_path = root / "dos.plot.json"
            metadata_path.write_text(json.dumps(metadata))
            manifest = build_artifact_manifest(
                "artifact-dos-001", ["run-anon-001"], "qe", "dos", "complete", root,
                ["dos-table=dos.csv", "plot-metadata=dos.plot.json"], ["dos-figure=dos.png"],
                "pass", ["finite data", "figure written"], ["No orbital claim"], ["dftpost", "plot-table"],
            )
            self.assertEqual(validation_errors("artifact", manifest), [])
            self.assertGreater(figure.stat().st_size, 0)

    def test_plot_rejects_nonfinite_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table = root / "bad.csv"
            table.write_text("x,y\n0,nan\n")
            style = ROOT / "skills" / "dft-postprocess" / "assets" / "dft-publication.mplstyle"
            with self.assertRaisesRegex(ValueError, "non-finite"):
                plot_table(table, root / "bad.png", "x", "y", None, "x", "y", None, style)


if __name__ == "__main__":
    unittest.main(verbosity=2)
