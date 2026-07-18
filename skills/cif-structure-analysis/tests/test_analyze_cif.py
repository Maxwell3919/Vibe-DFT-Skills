import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_cif.py"


NACL_CIF = '''data_NaCl
_symmetry_space_group_name_H-M    'P 1'
_symmetry_Int_Tables_number       1
_cell_length_a    5.6402
_cell_length_b    5.6402
_cell_length_c    5.6402
_cell_angle_alpha 90
_cell_angle_beta  90
_cell_angle_gamma 90
loop_
_space_group_symop_operation_xyz
  'x, y, z'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
Na1 Na 0.0 0.0 0.0 1
Cl1 Cl 0.5 0.5 0.5 1
'''


HEX_CIF = '''data_hex
_symmetry_space_group_name_H-M    'P 1'
_symmetry_Int_Tables_number       1
_cell_length_a    3.0
_cell_length_b    3.0
_cell_length_c    10.0
_cell_angle_alpha 90
_cell_angle_beta  90
_cell_angle_gamma 120
loop_
_space_group_symop_operation_xyz
  'x, y, z'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
Hf1 Hf 0.0 0.0 0.5 1
Br1 Br 0.333333 0.333333 0.4 1
Br2 Br 0.666667 0.666667 0.6 1
'''


VACUUM_CIF = '''data_vacuum
_symmetry_space_group_name_H-M    'P 1'
_symmetry_Int_Tables_number       1
_cell_length_a    4.0
_cell_length_b    4.0
_cell_length_c    40.0
_cell_angle_alpha 90
_cell_angle_beta  90
_cell_angle_gamma 90
loop_
_space_group_symop_operation_xyz
  'x, y, z'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
Hf1 Hf 0.50 0.50 0.45 1
Br1 Br 0.50 0.50 0.50 1
Ti1 Ti 0.50 0.50 0.55 1
'''


class AnalyzeCifTests(unittest.TestCase):
    def test_analyzes_nacl_cif_and_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "nacl.cif"
            out_json = tmp / "nacl.analysis.json"
            out_md = tmp / "nacl.analysis.md"
            views_dir = tmp / "views"
            cif.write_text(NACL_CIF)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(cif),
                    "--json",
                    str(out_json),
                    "--markdown",
                    str(out_md),
                    "--views-dir",
                    str(views_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())

            data = json.loads(out_json.read_text())
            self.assertEqual(data["status"], "PASS")
            self.assertEqual(data["structure"]["atom_count"], 2)
            self.assertEqual(data["structure"]["element_counts"], {"Cl": 1, "Na": 1})
            self.assertAlmostEqual(data["structure"]["cell"]["a"], 5.6402, places=4)
            self.assertGreater(data["structure"]["nearest_distances"]["min_distance_ang"], 4.0)
            self.assertEqual(data["flags"]["short_distances"], [])
            self.assertEqual(
                sorted(path.name for path in views_dir.glob("*.png")),
                ["view_along_a.png", "view_along_b.png", "view_along_c.png"],
            )
            self.assertEqual(
                sorted(view["axis"] for view in data["views"]),
                ["a", "b", "c"],
            )
            view_by_axis = {view["axis"]: view for view in data["views"]}
            self.assertEqual(view_by_axis["a"]["x_axis"], "b")
            self.assertEqual(view_by_axis["a"]["y_axis"], "c")
            self.assertEqual(view_by_axis["b"]["x_axis"], "c")
            self.assertEqual(view_by_axis["b"]["y_axis"], "a")
            self.assertEqual(view_by_axis["c"]["x_axis"], "a")
            self.assertEqual(view_by_axis["c"]["y_axis"], "b")
            markdown = out_md.read_text()
            self.assertIn("Computed Structure Facts", markdown)
            self.assertIn("Detailed Cell", markdown)
            self.assertIn("Coordinate Sample", markdown)
            self.assertIn("Nearest Pair Sample", markdown)
            self.assertIn("Generated Views", markdown)
            self.assertIn("view_along_a.png", markdown)

    def test_views_use_real_cell_vectors_for_nonorthogonal_c_view(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "hex.cif"
            out_json = tmp / "hex.analysis.json"
            out_md = tmp / "hex.analysis.md"
            views_dir = tmp / "views"
            cif.write_text(HEX_CIF)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(cif),
                    "--json",
                    str(out_json),
                    "--markdown",
                    str(out_md),
                    "--views-dir",
                    str(views_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_json.read_text())
            c_view = {view["axis"]: view for view in data["views"]}["c"]
            polygon = c_view["cell_polygon_2d"]
            self.assertEqual(len(polygon), 5)
            self.assertAlmostEqual(polygon[1][1], 0.0, places=6)
            self.assertNotAlmostEqual(polygon[2][1], 0.0, places=6)
            self.assertNotAlmostEqual(polygon[3][0], 0.0, places=6)
            self.assertIn("cell-vector projection", c_view["projection"])

    def test_views_are_cropped_to_atom_extent_not_full_vacuum_cell(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "vacuum.cif"
            out_json = tmp / "vacuum.analysis.json"
            out_md = tmp / "vacuum.analysis.md"
            views_dir = tmp / "views"
            cif.write_text(VACUUM_CIF)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(cif),
                    "--json",
                    str(out_json),
                    "--markdown",
                    str(out_md),
                    "--views-dir",
                    str(views_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_json.read_text())
            a_view = {view["axis"]: view for view in data["views"]}["a"]
            self.assertEqual(a_view["view_window_mode"], "atom_extent")
            self.assertLess(a_view["view_window_2d"]["y_span_ang"], 12.0)
            self.assertGreater(data["structure"]["cell"]["c"], 30.0)

    def test_nearest_neighbor_bond_pairs_keep_only_per_atom_nearest_shell(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "hex.cif"
            out_json = tmp / "hex.analysis.json"
            out_md = tmp / "hex.analysis.md"
            cif.write_text(HEX_CIF)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(cif),
                    "--json",
                    str(out_json),
                    "--markdown",
                    str(out_md),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_json.read_text())
            nearest = data["structure"]["nearest_distances"]
            self.assertIn("nearest_neighbor_bond_pairs", nearest)
            bond_pairs = {(item["i"], item["j"]) for item in nearest["nearest_neighbor_bond_pairs"]}
            all_pairs = {(item["i"], item["j"]) for item in nearest["nearest_pairs_sample"]}
            self.assertLess(len(bond_pairs), len(all_pairs))
            self.assertEqual(nearest["nearest_neighbor_bond_tolerance_ang"], 0.05)

    def test_matches_nearest_neighbor_bond_by_unordered_elements_and_length(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "nacl.cif"
            out_json = tmp / "nacl.analysis.json"
            out_md = tmp / "nacl.analysis.md"
            cif.write_text(NACL_CIF)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(cif),
                    "--json",
                    str(out_json),
                    "--markdown",
                    str(out_md),
                    "--match-elements",
                    "Na-Cl",
                    "--match-bond-length",
                    "4.8846",
                    "--match-bond-tolerance",
                    "0.001",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_json.read_text())
            match = data["structure"]["nearest_distances"]["bond_length_match"]
            self.assertEqual(match["status"], "MATCHED")
            self.assertEqual(match["query"]["element_pair"], ["Cl", "Na"])
            self.assertEqual(match["query"]["target_distance_ang"], 4.8846)
            self.assertEqual(match["scope"], "nearest_neighbor_bond_pairs")
            self.assertEqual(match["candidate_count"], 1)
            self.assertEqual(match["match_count"], 1)
            self.assertEqual(match["matches"][0]["symbols"], ["Na", "Cl"])
            self.assertLess(match["matches"][0]["absolute_delta_ang"], 0.001)
            self.assertEqual(match["closest_candidate"], match["matches"][0])
            self.assertIn("Nearest-Neighbor Bond-Length Match", out_md.read_text())

    def test_no_bond_length_match_reports_closest_filtered_candidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "nacl.cif"
            out_json = tmp / "nacl.analysis.json"
            out_md = tmp / "nacl.analysis.md"
            cif.write_text(NACL_CIF)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(cif),
                    "--json",
                    str(out_json),
                    "--markdown",
                    str(out_md),
                    "--match-elements",
                    "Cl-Na",
                    "--match-bond-length",
                    "3.0",
                    "--match-bond-tolerance",
                    "0.01",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_json.read_text())
            match = data["structure"]["nearest_distances"]["bond_length_match"]
            self.assertEqual(match["status"], "NO_MATCH")
            self.assertEqual(match["match_count"], 0)
            self.assertEqual(match["matches"], [])
            self.assertIsNotNone(match["closest_candidate"])
            self.assertGreater(match["closest_candidate"]["distance_ang"], 4.0)
            self.assertGreater(match["closest_candidate"]["absolute_delta_ang"], 1.0)

    def test_invalid_match_element_pair_fails_without_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "nacl.cif"
            out_json = tmp / "nacl.analysis.json"
            out_md = tmp / "nacl.analysis.md"
            cif.write_text(NACL_CIF)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(cif),
                    "--json",
                    str(out_json),
                    "--markdown",
                    str(out_md),
                    "--match-elements",
                    "NaCl",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ELEMENT-ELEMENT", result.stderr)
            self.assertFalse(out_json.exists())
            self.assertFalse(out_md.exists())

    def test_invalid_cif_fails_without_success_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "invalid.cif"
            out_json = tmp / "invalid.analysis.json"
            out_md = tmp / "invalid.analysis.md"
            cif.write_text("not a valid cif")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(cif),
                    "--json",
                    str(out_json),
                    "--markdown",
                    str(out_md),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("failed", result.stderr.lower())
            self.assertFalse(out_json.exists())
            self.assertFalse(out_md.exists())


if __name__ == "__main__":
    unittest.main()
