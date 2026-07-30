import json
import copy
import hashlib
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator
from ase import Atoms


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_cif.py"
REPO_ROOT = ROOT.parents[1]
SCHEMA = REPO_ROOT / "contracts" / "structure-manifest.schema.json"
POSTPROCESS_CLI = REPO_ROOT / "skills" / "dft-postprocess" / "scripts" / "dftpost_cli.py"
sys.path.insert(0, str(ROOT / "scripts"))
from ciftool.document import (  # noqa: E402
    inspect_cif_document,
    materialize_selected_block,
    parse_cif_number,
)
from ciftool.local_geometry import analyze_local_geometry  # noqa: E402
from ciftool.neighbors import analyze_periodic_neighbors  # noqa: E402
from ciftool.snapshot import capture_input_snapshot  # noqa: E402


NACL_CIF = '''data_NaCl
_symmetry_space_group_name_H-M    'P 1'
_symmetry_Int_Tables_number       1
_chemical_formula_sum             'Na Cl'
_cell_formula_units_Z             1
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


SIMPLE_CUBIC_CIF = '''data_simple_cubic
_symmetry_space_group_name_H-M    'P m -3 m'
_symmetry_Int_Tables_number       221
_cell_length_a    3.0
_cell_length_b    3.0
_cell_length_c    3.0
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
Po1 Po 0.0 0.0 0.0 1
'''

PASS_CIF = SIMPLE_CUBIC_CIF.replace(
    "_cell_length_a",
    "_chemical_formula_sum 'Po'\n_cell_formula_units_Z 1\n_cell_length_a",
)

LAYERED_SI_CIF = '''data_layered_si
_symmetry_space_group_name_H-M    'P 1'
_symmetry_Int_Tables_number       1
_cell_length_a    2.2
_cell_length_b    2.2
_cell_length_c    20.0
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
Si1 Si 0.0 0.0 0.5 1
'''


MULTIBLOCK_CIF = '''data_first
_symmetry_space_group_name_H-M 'P 1'
_cell_length_a 4
_cell_length_b 4
_cell_length_c 4
_cell_angle_alpha 90
_cell_angle_beta 90
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
Si1 Si 0 0 0

data_second
_symmetry_space_group_name_H-M 'P 1'
_cell_length_a 5
_cell_length_b 5
_cell_length_c 5
_cell_angle_alpha 90
_cell_angle_beta 90
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
C1 C 0 0 0
'''


MULTIBLOCK_WITH_METADATA_CIF = '''data_metadata_only
_audit_creation_method 'metadata only'

data_first_structure
_symmetry_space_group_name_H-M 'P 1'
_cell_length_a 4
_cell_length_b 4
_cell_length_c 4
_cell_angle_alpha 90
_cell_angle_beta 90
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
C1 C 0 0 0

data_second_structure
_symmetry_space_group_name_H-M 'P 1'
_cell_length_a 5
_cell_length_b 5
_cell_length_c 5
_cell_angle_alpha 90
_cell_angle_beta 90
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
N1 N 0.25 0.25 0.25
'''


PARTIAL_OCCUPANCY_CIF = '''data_partial
_symmetry_space_group_name_H-M 'P 1'
_cell_length_a 5.43(2)
_cell_length_b 5.43(2)
_cell_length_c 5.43(2)
_cell_angle_alpha 90
_cell_angle_beta 90
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
_atom_site_site_symmetry_multiplicity
_atom_site_disorder_assembly
_atom_site_disorder_group
Si1 Si 0 0 0 0.5 1 A 1
'''


SHORT_CONTACT_CIF = '''data_short_contact
_symmetry_space_group_name_H-M 'P 1'
_chemical_formula_sum 'He2'
_cell_formula_units_Z 1
_cell_length_a 10
_cell_length_b 10
_cell_length_c 10
_cell_angle_alpha 90
_cell_angle_beta 90
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
He1 He 0.00 0 0 1
He2 He 0.05 0 0 1
'''


INVALID_OCCUPANCY_CIF = '''data_invalid_occupancy
_symmetry_space_group_name_H-M 'P 1'
_cell_length_a 5
_cell_length_b 5
_cell_length_c 5
_cell_angle_alpha 90
_cell_angle_beta 90
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
Si1 Si 0 0 0 1.2
'''


CIF2 = '''#\\#CIF_2.0
data_cif2
_symmetry_space_group_name_H-M 'P 1'
_cell_length_a 4
_cell_length_b 4
_cell_length_c 4
_cell_angle_alpha 90
_cell_angle_beta 90
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
Ge1 Ge 0 0 0
'''


class AnalyzeCifTests(unittest.TestCase):
    def test_parses_cif_standard_uncertainty_with_and_without_exponent(self):
        ordinary = parse_cif_number("5.43(2)")
        scientific = parse_cif_number("3.45E1(12)")
        missing = parse_cif_number("?")
        self.assertEqual(ordinary["raw"], "5.43(2)")
        self.assertAlmostEqual(ordinary["value"], 5.43)
        self.assertAlmostEqual(ordinary["standard_uncertainty"], 0.02)
        self.assertAlmostEqual(scientific["value"], 34.5)
        self.assertAlmostEqual(scientific["standard_uncertainty"], 1.2)
        self.assertIsNone(missing["value"])
        self.assertIsNone(missing["standard_uncertainty"])

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
            validator = Draft202012Validator(json.loads(SCHEMA.read_text()))
            self.assertEqual(list(validator.iter_errors(data)), [])
            identity = data["structure_identity"]
            self.assertEqual(
                identity["canonicalization"],
                "json-sort-keys-compact-utf8-v1",
            )
            fingerprint_bytes = json.dumps(
                identity["fingerprint_input"],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("utf-8")
            self.assertEqual(
                identity["value"], hashlib.sha256(fingerprint_bytes).hexdigest()
            )
            backward_compatible = copy.deepcopy(data)
            backward_compatible["structure_identity"].pop("fingerprint_input")
            backward_compatible["structure_identity"].pop("canonicalization")
            self.assertEqual(
                list(validator.iter_errors(backward_compatible)), []
            )
            incomplete_preimage = copy.deepcopy(data)
            incomplete_preimage["structure_identity"].pop("fingerprint_input")
            self.assertTrue(list(validator.iter_errors(incomplete_preimage)))
            misspelled = copy.deepcopy(data)
            misspelled["structure"]["atom_cout"] = misspelled["structure"]["atom_count"]
            self.assertTrue(list(validator.iter_errors(misspelled)))
            inconsistent = copy.deepcopy(data)
            inconsistent["status"] = "PASS"
            self.assertTrue(list(validator.iter_errors(inconsistent)))
            validation = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_CLI),
                    "validate-manifest",
                    "structure",
                    str(out_json),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr)
            self.assertEqual(data["status"], "WARN")
            self.assertEqual(data["validation"]["status"], "warn")
            self.assertEqual(
                data["structure"]["symmetry_attempt"]["declared_comparison"]["status"],
                "MISMATCH",
            )
            self.assertEqual(data["structure"]["atom_count"], 2)
            self.assertEqual(data["structure"]["element_counts"], {"Cl": 1, "Na": 1})
            self.assertAlmostEqual(data["structure"]["cell"]["a"], 5.6402, places=4)
            self.assertGreater(data["structure"]["nearest_distances"]["min_distance_ang"], 4.0)
            self.assertEqual(data["flags"]["short_distances"], [])
            intelligence = data["structure"]
            self.assertEqual(
                intelligence["quality_analysis"]["formula_consistency"]["status"],
                "MATCH",
            )
            self.assertEqual(
                intelligence["optimization_guidance"]["ranking_status"],
                "NOT_RANKED",
            )
            self.assertFalse(
                intelligence["optimization_guidance"]["stability_assessed"]
            )
            self.assertFalse(
                intelligence["optimization_guidance"]["energy_model_used"]
            )
            self.assertEqual(
                data["provenance"]["command_options"]["topology_scale_factors"],
                [1.0, 1.15, 1.3],
            )
            self.assertEqual(
                sorted(path.name for path in views_dir.glob("*.png")),
                [
                    f"analysis-{data['analysis_key'][:16]}-view-along-a.png",
                    f"analysis-{data['analysis_key'][:16]}-view-along-b.png",
                    f"analysis-{data['analysis_key'][:16]}-view-along-c.png",
                ],
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
            self.assertIn("Structure Quality Screening", markdown)
            self.assertIn("Local Geometry Hints", markdown)
            self.assertIn("Multi-Scale Periodic Connectivity", markdown)
            self.assertIn("Structure-Only Property Screening", markdown)
            self.assertIn("Optimization Starting-Point Guidance", markdown)
            self.assertIn("Generated Views", markdown)
            self.assertIn(
                f"analysis-{data['analysis_key'][:16]}-view-along-a.png",
                markdown,
            )

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
            self.assertEqual(match["scope"], "periodic_nearest_neighbor_bond_pairs")
            self.assertEqual(match["candidate_count"], 8)
            self.assertEqual(match["match_count"], 8)
            self.assertEqual(match["matches"][0]["symbols"], ["Na", "Cl"])
            self.assertEqual(len(match["matches"][0]["shift"]), 3)
            self.assertLess(match["matches"][0]["absolute_delta_ang"], 0.001)
            self.assertEqual(match["closest_candidate"], match["matches"][0])
            self.assertIn("Nearest-Neighbor Bond-Length Match", out_md.read_text())

    def test_enumerates_self_image_neighbors_and_coordination_for_one_site_cell(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "simple.cif"
            out_json = tmp / "simple.analysis.json"
            out_md = tmp / "simple.analysis.md"
            cif.write_text(SIMPLE_CUBIC_CIF)

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
                    "--topology-scale-factors",
                    "1.2",
                    "1.3",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            structure = json.loads(out_json.read_text())["structure"]
            nearest = structure["nearest_distances"]
            self.assertTrue(nearest["periodic_images_enumerated"])
            self.assertTrue(nearest["self_image_neighbors_enumerated"])
            self.assertEqual(nearest["periodic_edge_count"], 3)
            self.assertEqual(nearest["directed_neighbor_count"], 6)
            self.assertAlmostEqual(nearest["min_distance_ang"], 3.0)
            self.assertEqual(
                nearest["coordination_by_atom"][0]["nearest_shell_coordination"], 6
            )
            self.assertTrue(
                all(item["i"] == item["j"] == 0 for item in nearest["nearest_neighbor_bond_pairs"])
            )
            local = structure["local_geometry"]["sites"][0]
            self.assertEqual(local["coordination"], 6)
            self.assertEqual(local["geometry_hint"], "octahedral-like")
            connectivity = structure["connectivity_analysis"]
            self.assertTrue(connectivity["stable_across_scales"])
            self.assertEqual(connectivity["dimensionality_candidate"], "3D")
            screening = structure["property_screening"]
            self.assertTrue(screening["symmetry"]["centrosymmetric"])
            self.assertFalse(
                screening["symmetry"]["piezoelectric_symmetry_allowed"]
            )
            guidance = structure["optimization_guidance"]
            self.assertEqual(guidance["ranking_status"], "NOT_RANKED")
            self.assertTrue(
                any(
                    item["candidate_id"] == "symmetry-idealized-primitive"
                    and item["available"]
                    for item in guidance["starting_points"]
                )
            )

    def test_reports_robust_2d_graph_as_candidate_and_adds_layer_control(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "layered.cif"
            out_json = tmp / "layered.analysis.json"
            out_md = tmp / "layered.analysis.md"
            cif.write_text(LAYERED_SI_CIF)

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
                    "--topology-scale-factors",
                    "1.0",
                    "1.1",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            structure = json.loads(out_json.read_text())["structure"]
            connectivity = structure["connectivity_analysis"]
            self.assertTrue(connectivity["stable_across_scales"])
            self.assertEqual(connectivity["dimensionality_candidate"], "2D")
            self.assertTrue(
                all(
                    scale["components"][0]["translation_rank"] == 2
                    for scale in connectivity["scales"]
                )
            )
            self.assertIn(
                "connectivity-dimensionality-screen",
                {
                    item["id"]
                    for item in structure["property_screening"]["hypotheses"]
                },
            )
            self.assertIn(
                "enumerate-layer-registry-candidates",
                {
                    item["id"]
                    for item in structure["optimization_guidance"][
                        "recommended_controls"
                    ]
                },
            )

    def test_selects_named_block_and_records_all_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "multi.cif"
            out_json = tmp / "multi.analysis.json"
            out_md = tmp / "multi.analysis.md"
            cif.write_text(MULTIBLOCK_CIF)

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
                    "--block-name",
                    "SECOND",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_json.read_text())
            self.assertEqual(data["document"]["selected_block"], {"index": 1, "name": "second"})
            self.assertEqual([block["name"] for block in data["document"]["blocks"]], ["first", "second"])
            self.assertEqual(data["structure"]["element_counts"], {"C": 1})
            self.assertEqual(data["source"]["data_block"], {"index": 1, "name": "second"})

    def test_raw_block_selection_does_not_drift_across_metadata_only_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "multi-with-metadata.cif"
            out_json = tmp / "multi.analysis.json"
            out_md = tmp / "multi.analysis.md"
            cif.write_text(MULTIBLOCK_WITH_METADATA_CIF)

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
                    "--block-index",
                    "1",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_json.read_text())
            self.assertEqual(
                data["document"]["selected_block"],
                {"index": 1, "name": "first_structure"},
            )
            self.assertEqual(data["structure"]["element_counts"], {"C": 1})
            self.assertEqual(
                data["document"]["metadata"]["atom_sites"][0]["type_symbol"]["value"],
                "C",
            )

    def test_metadata_only_selected_block_fails_instead_of_using_next_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "multi-with-metadata.cif"
            out_json = tmp / "multi.analysis.json"
            out_md = tmp / "multi.analysis.md"
            cif.write_text(MULTIBLOCK_WITH_METADATA_CIF)

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
                    "--block-index",
                    "0",
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("selected CIF data block", result.stderr)
            self.assertFalse(out_json.exists())
            self.assertFalse(out_md.exists())

    def test_neighbor_decisions_use_unrounded_distances(self):
        atoms = Atoms(
            "He2",
            positions=[[0.0, 0.0, 0.0], [0.5999996, 0.0, 0.0]],
            cell=[10.0, 10.0, 10.0],
            pbc=False,
        )
        summary, short_flags, directed_shell = analyze_periodic_neighbors(
            atoms,
            0.6,
            requested_cutoff=1.0,
            maximum_cutoff=1.0,
            shell_tolerance=0.0,
        )
        self.assertEqual(len(short_flags), 1)
        self.assertLess(short_flags[0]["distance_ang"], 0.6)
        self.assertEqual(len(directed_shell), 2)
        self.assertLess(
            summary["nearest_neighbor_bond_pairs"][0]["distance_ang"],
            0.6,
        )

    def test_local_geometry_consumes_each_centers_directed_nearest_shell(self):
        atoms = Atoms(
            "He3",
            positions=[
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [1.2, 0.0, 0.0],
            ],
            cell=[10.0, 10.0, 10.0],
            pbc=False,
        )
        summary, _, directed_shell = analyze_periodic_neighbors(
            atoms,
            0.1,
            requested_cutoff=2.0,
            maximum_cutoff=2.0,
            shell_tolerance=0.0,
        )
        local = analyze_local_geometry(atoms, directed_shell)
        expected = [
            item["nearest_shell_coordination"]
            for item in summary["coordination_by_atom"]
        ]
        observed = [item["coordination"] for item in local["sites"]]
        self.assertEqual(expected, [1, 1, 1])
        self.assertEqual(observed, expected)

    def test_preserves_uncertainty_and_warns_for_partial_occupancy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "partial.cif"
            out_json = tmp / "partial.analysis.json"
            out_md = tmp / "partial.analysis.md"
            cif.write_text(PARTIAL_OCCUPANCY_CIF)

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
            cell_a = data["document"]["metadata"]["cell"]["a"]
            self.assertEqual(cell_a["raw"], "5.43(2)")
            self.assertAlmostEqual(cell_a["value"], 5.43)
            self.assertAlmostEqual(cell_a["standard_uncertainty"], 0.02)
            self.assertEqual(data["document"]["metadata"]["partial_occupancy_rows"], [0])
            self.assertEqual(data["document"]["metadata"]["disorder_rows"], [0])
            site = data["document"]["metadata"]["atom_sites"][0]
            self.assertEqual(site["site_symmetry_multiplicity"]["value"], 1.0)
            self.assertEqual(site["disorder_assembly"]["value"], "A")
            self.assertEqual(site["disorder_group"]["value"], "1")
            self.assertFalse(data["structure"]["density_occupancy_weighted"])
            self.assertEqual(data["status"], "WARN")
            check_ids = {item["id"] for item in data["validation"]["checks"]}
            self.assertIn("partial-occupancy-present", check_ids)
            self.assertIn("atom-site-disorder-metadata-present", check_ids)
            self.assertIn("density-partial-occupancy-limitation", check_ids)
            self.assertIn("representative-structure-disorder-limitation", check_ids)
            eligibility = data["structure"]["screening_eligibility"]["scopes"]
            self.assertEqual(eligibility["calculation_handoff"]["status"], "BLOCK")
            self.assertEqual(
                eligibility["symmetry_property_screening"]["status"],
                "NOT_ASSESSED",
            )
            self.assertEqual(
                data["structure"]["property_screening"]["hypotheses"][0]["status"],
                "NOT_ASSESSED",
            )
            self.assertFalse(
                any(
                    item["recommended_for_screening"]
                    for item in data["structure"]["optimization_guidance"][
                        "starting_points"
                    ]
                )
            )

    def test_short_contacts_block_handoff_and_all_optimization_recommendations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "short.cif"
            out_json = tmp / "short.analysis.json"
            out_md = tmp / "short.analysis.md"
            cif.write_text(SHORT_CONTACT_CIF)

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
                    "--short-distance-threshold",
                    "0.6",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(out_json.read_text())
            self.assertEqual(data["status"], "WARN")
            self.assertEqual(len(data["flags"]["short_distances"]), 1)
            eligibility = data["structure"]["screening_eligibility"]
            self.assertEqual(
                eligibility["scopes"]["calculation_handoff"]["status"],
                "BLOCK",
            )
            guidance = data["structure"]["optimization_guidance"]
            self.assertTrue(guidance["blockers"])
            self.assertFalse(
                any(
                    item["recommended_for_screening"]
                    for item in guidance["starting_points"]
                )
            )

    def test_out_of_range_occupancy_blocks_the_artifact(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "invalid-occupancy.cif"
            out_json = tmp / "invalid-occupancy.analysis.json"
            out_md = tmp / "invalid-occupancy.analysis.md"
            cif.write_text(INVALID_OCCUPANCY_CIF)

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

            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertTrue(out_json.is_file())
            self.assertTrue(out_md.is_file())
            data = json.loads(out_json.read_text())
            self.assertEqual(data["status"], "BLOCK")
            by_id = {
                item["id"]: item["status"]
                for item in data["validation"]["checks"]
            }
            self.assertEqual(by_id["atom-site-occupancy-range"], "fail")
            scopes = data["structure"]["screening_eligibility"]["scopes"]
            self.assertEqual(
                {
                    name: payload["status"]
                    for name, payload in scopes.items()
                },
                {
                    "artifact_generation": "BLOCK",
                    "geometry_screening": "BLOCK",
                    "symmetry_property_screening": "NOT_ASSESSED",
                    "connectivity_screening": "BLOCK",
                    "calculation_handoff": "BLOCK",
                },
            )
            self.assertEqual(
                [
                    (item["id"], item["status"])
                    for item in data["structure"]["property_screening"]["hypotheses"]
                ],
                [("property-screening-eligibility", "NOT_ASSESSED")],
            )
            self.assertFalse(
                any(
                    item["recommended_for_screening"]
                    for item in data["structure"]["optimization_guidance"][
                        "starting_points"
                    ]
                )
            )

    def test_pass_artifact_has_zero_exit_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "pass.cif"
            out_json = tmp / "pass.analysis.json"
            out_md = tmp / "pass.analysis.md"
            cif.write_text(PASS_CIF)

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
                    "--topology-scale-factors",
                    "1.0",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(out_json.read_text())["status"], "PASS")

    def test_uses_cif2_parser_and_does_not_leak_absolute_input_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "syntax2.cif"
            out_json = tmp / "syntax2.analysis.json"
            out_md = tmp / "syntax2.analysis.md"
            cif.write_text(CIF2)

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
            artifact_text = out_json.read_text()
            data = json.loads(artifact_text)
            self.assertEqual(data["source"]["format"], "cif2.0")
            self.assertEqual(data["parser"]["name"], "PyCifRW")
            self.assertNotIn(str(tmp), artifact_text)
            self.assertNotIn(str(tmp), out_md.read_text())

    def test_invalid_block_and_cutoff_options_fail_without_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "multi.cif"
            cif.write_text(MULTIBLOCK_CIF)
            cases = [
                ["--block-index", "9"],
                ["--block-name", "missing"],
                ["--neighbor-cutoff", "5", "--maximum-neighbor-cutoff", "4"],
                ["--angle-tolerance", "-0.5"],
                ["--topology-scale-factors", "1.0", "0"],
            ]
            for index, extra in enumerate(cases):
                with self.subTest(extra=extra):
                    out_json = tmp / f"invalid-{index}.json"
                    out_md = tmp / f"invalid-{index}.md"
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
                            *extra,
                        ],
                        text=True,
                        capture_output=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(out_json.exists())
                    self.assertFalse(out_md.exists())

    def test_refuses_output_path_collisions_without_overwriting_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cif = tmp / "input.cif"
            cif.write_text(NACL_CIF)
            original = cif.read_text()
            shared = tmp / "same.out"
            cases = [
                ["--json", str(shared), "--markdown", str(shared)],
                ["--json", str(cif), "--markdown", str(tmp / "safe.md")],
                ["--json", str(tmp / "safe.json"), "--markdown", str(cif)],
            ]
            for extra in cases:
                with self.subTest(extra=extra):
                    result = subprocess.run(
                        [sys.executable, str(SCRIPT), "--input", str(cif), *extra],
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(cif.read_text(), original)
            self.assertFalse(shared.exists())

    def test_snapshot_binds_document_and_structure_to_initial_bytes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "mutable.cif"
            source.write_text(NACL_CIF)
            expected_bytes = source.read_bytes()
            snapshot_dir = tmp / "snapshot"
            snapshot_dir.mkdir()

            snapshot = capture_input_snapshot(source, snapshot_dir)
            source.write_text(SIMPLE_CUBIC_CIF)
            document = inspect_cif_document(snapshot.path)
            atoms = materialize_selected_block(
                snapshot.path,
                document["selected_block"],
                document["blocks"],
            )

            self.assertEqual(
                snapshot.sha256,
                hashlib.sha256(expected_bytes).hexdigest(),
            )
            self.assertEqual(document["sha256"], snapshot.sha256)
            self.assertEqual(document["bytes"], len(expected_bytes))
            self.assertEqual(atoms.get_chemical_symbols(), ["Na", "Cl"])
            self.assertEqual(snapshot.path.stat().st_mode & 0o777, 0o600)

    def test_analysis_key_ignores_path_and_mtime_but_tracks_semantic_options(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            first_source = tmp / "first-name.cif"
            second_source = tmp / "second-name.cif"
            first_source.write_text(NACL_CIF)
            second_source.write_text(NACL_CIF)
            first_source.touch()
            reports = []
            for index, source in enumerate((first_source, second_source)):
                out_json = tmp / f"analysis-{index}.json"
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--input",
                        str(source),
                        "--json",
                        str(out_json),
                        "--markdown",
                        str(tmp / f"analysis-{index}.md"),
                    ],
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                reports.append(json.loads(out_json.read_text()))

            changed_json = tmp / "analysis-changed.json"
            changed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(first_source),
                    "--json",
                    str(changed_json),
                    "--markdown",
                    str(tmp / "analysis-changed.md"),
                    "--symprec",
                    "0.002",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(changed.returncode, 0, changed.stderr)
            changed_report = json.loads(changed_json.read_text())
            self.assertEqual(reports[0]["analysis_key"], reports[1]["analysis_key"])
            self.assertEqual(
                reports[0]["structure_identity"],
                reports[1]["structure_identity"],
            )
            self.assertNotEqual(
                reports[0]["analysis_key"],
                changed_report["analysis_key"],
            )

    def test_dftpost_recomputes_analysis_key_and_screening_eligibility(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source.cif"
            original = tmp / "analysis.json"
            source.write_text(NACL_CIF)
            generated = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(source),
                    "--json",
                    str(original),
                    "--markdown",
                    str(tmp / "analysis.md"),
                    "--symprec",
                    "0.00123456789",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)

            valid = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_CLI),
                    "validate-manifest",
                    "structure",
                    str(original),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)

            data = json.loads(original.read_text())
            self.assertEqual(data["provenance"]["producer_version"], "3.0.0")
            forged_key = copy.deepcopy(data)
            forged_key["analysis_key"] = "f" * 64
            forged_key_path = tmp / "forged-key.json"
            forged_key_path.write_text(json.dumps(forged_key))
            key_validation = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_CLI),
                    "validate-manifest",
                    "structure",
                    str(forged_key_path),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(key_validation.returncode, 2)
            self.assertIn("analysis_key", key_validation.stderr)

            missing_key = copy.deepcopy(data)
            missing_key.pop("analysis_key")
            missing_key_path = tmp / "missing-key.json"
            missing_key_path.write_text(json.dumps(missing_key))
            missing_key_validation = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_CLI),
                    "validate-manifest",
                    "structure",
                    str(missing_key_path),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(missing_key_validation.returncode, 2)
            self.assertIn("analysis_key", missing_key_validation.stderr)

            blocked_source = tmp / "blocked.cif"
            blocked_original = tmp / "blocked.json"
            blocked_source.write_text(INVALID_OCCUPANCY_CIF)
            blocked_generated = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(blocked_source),
                    "--json",
                    str(blocked_original),
                    "--markdown",
                    str(tmp / "blocked.md"),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(blocked_generated.returncode, 3, blocked_generated.stderr)
            blocked_validation = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_CLI),
                    "validate-manifest",
                    "structure",
                    str(blocked_original),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(blocked_validation.returncode, 0, blocked_validation.stderr)
            forged_eligibility = json.loads(blocked_original.read_text())
            forged_eligibility["structure"]["screening_eligibility"]["scopes"][
                "calculation_handoff"
            ] = {"status": "PASS", "reason_ids": []}
            forged_eligibility_path = tmp / "forged-eligibility.json"
            forged_eligibility_path.write_text(json.dumps(forged_eligibility))
            eligibility_validation = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_CLI),
                    "validate-manifest",
                    "structure",
                    str(forged_eligibility_path),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(eligibility_validation.returncode, 2)
            self.assertIn("screening_eligibility", eligibility_validation.stderr)

            forged_cascade = json.loads(blocked_original.read_text())
            forged_cascade["structure"]["property_screening"]["hypotheses"].append(
                {
                    "id": "forged-positive",
                    "status": "CANDIDATE",
                    "basis": "synthetic tamper",
                    "limitation": "must be rejected",
                }
            )
            forged_cascade["structure"]["optimization_guidance"]["starting_points"][
                0
            ]["recommended_for_screening"] = True
            forged_cascade_path = tmp / "forged-cascade.json"
            forged_cascade_path.write_text(json.dumps(forged_cascade))
            cascade_validation = subprocess.run(
                [
                    sys.executable,
                    str(POSTPROCESS_CLI),
                    "validate-manifest",
                    "structure",
                    str(forged_cascade_path),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(cascade_validation.returncode, 2)
            self.assertIn("property_screening", cascade_validation.stderr)
            self.assertIn("optimization_guidance", cascade_validation.stderr)

    def test_refuses_symlink_cif_input_without_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source.cif"
            linked = tmp / "linked.cif"
            out_json = tmp / "analysis.json"
            out_md = tmp / "analysis.md"
            source.write_text(NACL_CIF)
            linked.symlink_to(source)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(linked),
                    "--json",
                    str(out_json),
                    "--markdown",
                    str(out_md),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("INPUT_NOT_REGULAR", result.stderr)
            self.assertFalse(out_json.exists())
            self.assertFalse(out_md.exists())

    def test_atomic_bundle_is_complete_and_no_clobber(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source.cif"
            bundle = tmp / "analysis-bundle"
            source.write_text(NACL_CIF)
            command = [
                sys.executable,
                str(SCRIPT),
                "--input",
                str(source),
                "--bundle-dir",
                str(bundle),
            ]

            first = subprocess.run(command, text=True, capture_output=True)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue((bundle / "analysis.json").is_file())
            self.assertTrue((bundle / "analysis.md").is_file())
            data = json.loads((bundle / "analysis.json").read_text())
            expected_views = {
                f"analysis-{data['analysis_key'][:16]}-view-along-{axis}.png"
                for axis in ("a", "b", "c")
            }
            self.assertEqual(
                {path.name for path in (bundle / "views").glob("*.png")},
                expected_views,
            )
            before = {
                path.relative_to(bundle).as_posix(): path.read_bytes()
                for path in bundle.rglob("*")
                if path.is_file()
            }

            second = subprocess.run(command, text=True, capture_output=True)

            self.assertEqual(second.returncode, 2)
            self.assertIn("OUTPUT_EXISTS", second.stderr)
            after = {
                path.relative_to(bundle).as_posix(): path.read_bytes()
                for path in bundle.rglob("*")
                if path.is_file()
            }
            self.assertEqual(after, before)

    def test_refuses_existing_symlink_in_any_output_ancestor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source.cif"
            source.write_text(NACL_CIF)
            real_parent = tmp / "real-parent"
            real_parent.mkdir()
            linked_parent = tmp / "linked-parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)

            loose = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(source),
                    "--json",
                    str(linked_parent / "nested" / "analysis.json"),
                    "--markdown",
                    str(linked_parent / "nested" / "analysis.md"),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(loose.returncode, 2)
            self.assertIn("OUTPUT_PARENT_INVALID", loose.stderr)
            self.assertFalse((real_parent / "nested" / "analysis.json").exists())
            self.assertFalse((real_parent / "nested" / "analysis.md").exists())

            (real_parent / "bundle-parent").mkdir()
            bundle = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(source),
                    "--bundle-dir",
                    str(linked_parent / "bundle-parent" / "bundle"),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(bundle.returncode, 2)
            self.assertIn("OUTPUT_PARENT_INVALID", bundle.stderr)
            self.assertFalse((real_parent / "bundle-parent" / "bundle").exists())

    def test_view_targets_cannot_alias_input_or_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source = tmp / "source.cif"
            source.write_text(NACL_CIF)
            views = tmp / "views"
            views.mkdir()
            original = source.read_bytes()
            probe_json = tmp / "probe.json"
            probe_md = tmp / "probe.md"
            probe = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(source),
                    "--json",
                    str(probe_json),
                    "--markdown",
                    str(probe_md),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            analysis = json.loads(probe_json.read_text())
            view_a = views / (
                f"analysis-{analysis['analysis_key'][:16]}-view-along-a.png"
            )
            probe_json.unlink()
            probe_md.unlink()
            view_a.symlink_to(source)

            symlink_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(source),
                    "--json",
                    str(tmp / "safe.json"),
                    "--markdown",
                    str(tmp / "safe.md"),
                    "--views-dir",
                    str(views),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(symlink_result.returncode, 2)
            self.assertIn("OUTPUT_EXISTS", symlink_result.stderr)
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse((tmp / "safe.json").exists())
            self.assertFalse((tmp / "safe.md").exists())
            view_a.unlink()

            collision_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(source),
                    "--json",
                    str(view_a),
                    "--markdown",
                    str(tmp / "other.md"),
                    "--views-dir",
                    str(views),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(collision_result.returncode, 2)
            self.assertIn("OUTPUT_COLLISION", collision_result.stderr)
            self.assertFalse(view_a.exists())
            self.assertFalse((tmp / "other.md").exists())

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
