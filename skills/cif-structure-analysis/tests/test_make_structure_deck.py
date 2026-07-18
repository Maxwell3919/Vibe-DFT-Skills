import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "make_structure_deck.py"


def sample_report(tmp: Path) -> Path:
    view_paths = {}
    for axis in ["a", "b", "c"]:
        image = tmp / f"view_along_{axis}.png"
        image.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
            b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT"
            b"\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA"
            b"\xbf\x83\x8f\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        view_paths[axis] = str(image)

    report = {
        "status": "PASS",
        "input": {"path": str(tmp / "structure.cif"), "name": "structure.cif"},
        "execution": {"command": "analyze", "ase_version": "3.29.0"},
        "structure": {
            "formula": "Br2HfSe2Ti",
            "atom_count": 6,
            "element_counts": {"Br": 2, "Hf": 1, "Se": 2, "Ti": 1},
            "pbc": [True, True, True],
            "cell": {
                "a": 3.473,
                "b": 3.473,
                "c": 30.0,
                "alpha": 90.0,
                "beta": 90.0,
                "gamma": 120.0,
                "rank": 3,
            },
            "volume_ang3": 313.372912,
            "density_g_cm3": 2.883181,
            "coordinates": {
                "coordinate_sample": [
                    {"index": 0, "symbol": "Hf", "cartesian_ang": [0.0, 0.0, 11.4], "fractional": [0.0, 0.0, 0.38]},
                    {"index": 1, "symbol": "Br", "cartesian_ang": [1.7, 1.0, 13.2], "fractional": [0.667, 0.333, 0.44]},
                    {"index": 2, "symbol": "Ti", "cartesian_ang": [1.7, 1.0, 18.9], "fractional": [0.667, 0.333, 0.63]},
                ],
                "cartesian_ang": {
                    "x": {"min": 0.0, "max": 1.7, "span": 1.7},
                    "y": {"min": 0.0, "max": 1.0, "span": 1.0},
                    "z": {"min": 11.4, "max": 18.9, "span": 7.5},
                },
                "fractional": {
                    "x": {"min": 0.0, "max": 0.667, "span": 0.667},
                    "y": {"min": 0.0, "max": 0.333, "span": 0.333},
                    "z": {"min": 0.38, "max": 0.63, "span": 0.25},
                },
            },
            "nearest_distances": {
                "min_distance_ang": 2.701515,
                "nearest_pairs_sample": [
                    {"i": 0, "j": 1, "symbols": ["Hf", "Br"], "distance_ang": 2.701515},
                    {"i": 2, "j": 1, "symbols": ["Ti", "Br"], "distance_ang": 3.1},
                ],
                "nearest_neighbor_bond_pairs": [
                    {"i": 0, "j": 1, "symbols": ["Hf", "Br"], "distance_ang": 2.701515},
                ],
                "nearest_neighbor_bond_tolerance_ang": 0.05,
                "nearest_neighbor_bond_count": 1,
            },
            "axis_gap_estimates": [
                {"axis": "a", "largest_gap_ang": 1.15, "occupied_span_estimate_ang": 2.31},
                {"axis": "b", "largest_gap_ang": 1.15, "occupied_span_estimate_ang": 2.31},
                {"axis": "c", "largest_gap_ang": 18.06, "occupied_span_estimate_ang": 11.93},
            ],
            "symmetry_attempt": {"status": "DETECTED", "international": "P3m1", "number": 156, "symprec": 0.001},
        },
        "flags": {"short_distances": []},
        "views": [
            {"axis": "a", "path": view_paths["a"], "x_axis": "b", "y_axis": "c", "projection": "view along a"},
            {"axis": "b", "path": view_paths["b"], "x_axis": "c", "y_axis": "a", "projection": "view along b"},
            {"axis": "c", "path": view_paths["c"], "x_axis": "a", "y_axis": "b", "projection": "view along c"},
        ],
        "limitations": [],
        "not_assessed": ["DFT setup advice", "physics credibility"],
    }
    path = tmp / "analysis.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


class MakeStructureDeckTests(unittest.TestCase):
    def test_writes_single_page_html_deck_with_interactive_three_scene_and_embedded_views(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            analysis = sample_report(tmp)
            output = tmp / "deck.html"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--analysis-json",
                    str(analysis),
                    "--output",
                    str(output),
                    "--title",
                    "HfBr2 / TiSe2 Stack 02",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text()
            self.assertIn("HfBr2 / TiSe2 Stack 02", html)
            self.assertIn("const THREE_SOURCE =", html)
            self.assertIn("const THREE = await import", html)
            self.assertIn("const REPORT =", html)
            self.assertIn("id=\"three-canvas\"", html)
            self.assertIn("class=\"sheet report-brief\"", html)
            self.assertIn("data:image/png;base64", html)
            self.assertIn("view along a", html)
            self.assertIn("Br2HfSe2Ti", html)
            self.assertIn("CIF Structure Analysis Brief", html)
            self.assertIn("class=\"evidence-chip evidence-pass\"", html)
            self.assertIn("Source of truth: analysis JSON / Markdown", html)
            self.assertIn("Reference Views", html)
            self.assertIn("coordinate-gap estimate, not a physical vacuum conclusion", html)
            self.assertNotIn("class=\"slide", html)
            self.assertNotIn("URLSearchParams(location.search)", html)

    def test_writes_centered_3d_controls_bonds_and_bond_length_picker(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            analysis = sample_report(tmp)
            output = tmp / "deck.html"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--analysis-json",
                    str(analysis),
                    "--output",
                    str(output),
                    "--title",
                    "HfBr2 / TiSe2 Stack 02",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text()
            self.assertIn("data-view-axis=\"a\"", html)
            self.assertIn("data-view-axis=\"b\"", html)
            self.assertIn("data-view-axis=\"c\"", html)
            self.assertIn("data-view-axis=\"reset\"", html)
            self.assertIn("const TARGET = new THREE.Vector3(0, 0, 0)", html)
            self.assertIn("structureCenter", html)
            self.assertIn("function setViewAxis(axis)", html)
            self.assertIn("const BOND_RADIUS =", html)
            self.assertIn("new THREE.CylinderGeometry(radius", html)
            self.assertIn("nearest_neighbor_bond_pairs", html)
            self.assertIn("const bondPairs = REPORT.structure.nearest_distances.nearest_neighbor_bond_pairs", html)
            self.assertNotIn("(REPORT.structure.nearest_distances.nearest_pairs_sample || []).forEach(addBond)", html)
            self.assertIn(".view-card {", html)
            self.assertIn("overflow:hidden", html)
            self.assertIn("max-height:100%", html)
            self.assertIn("const raycaster = new THREE.Raycaster()", html)
            self.assertIn("id=\"bond-tooltip\"", html)
            self.assertIn("measurement-tooltip", html)
            self.assertIn("bondData.distance_ang.toFixed(4)", html)
            self.assertIn("intersectObjects(bondPickTargets", html)

    def test_html_does_not_expose_private_input_or_view_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            analysis = sample_report(tmp)
            output = tmp / "deck.html"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--analysis-json",
                    str(analysis),
                    "--output",
                    str(output),
                    "--title",
                    "HfBr2 / TiSe2 Stack 02",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text()
            leaks = [
                "Input CIF:",
                str(tmp),
                '"path":',
                "view_along_a.png",
                "structure.cif",
            ]
            leaked = [item for item in leaks if item in html]
            if leaked:
                self.fail(f"private path details leaked into HTML: {leaked}")


if __name__ == "__main__":
    unittest.main()
