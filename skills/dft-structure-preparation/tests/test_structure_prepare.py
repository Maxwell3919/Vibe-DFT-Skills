from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "structure_prepare.py"
FIXTURES = ROOT / "fixtures"
CIF_SCRIPT = ROOT.parents[1] / "skills" / "cif-structure-analysis" / "scripts" / "analyze_cif.py"
sys.path.insert(0, str(ROOT / "scripts"))
import structure_prepare  # noqa: E402
from structure_prepare import (  # noqa: E402
    GateError,
    enforce_minimum_distance,
    minimum_distance,
)


def run_cli(*arguments: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(item) for item in arguments)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class StructurePrepareCliTests(unittest.TestCase):
    def test_cif_manifest_import_closes_the_active_intake_handoff(self) -> None:
        cif_text = """\
data_si
_cell_length_a 5.43
_cell_length_b 5.43
_cell_length_c 5.43
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_space_group_name_H-M_alt 'P 1'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
Si1 Si 0 0 0 1
"""
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            cif_path = directory_path / "input.cif"
            manifest_path = directory_path / "manifest.json"
            markdown_path = directory_path / "manifest.md"
            cif_path.write_text(cif_text, encoding="utf-8")
            analyzed = subprocess.run(
                [
                    sys.executable,
                    str(CIF_SCRIPT),
                    "--input",
                    str(cif_path),
                    "--json",
                    str(manifest_path),
                    "--markdown",
                    str(markdown_path),
                ],
                cwd=ROOT.parents[1],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(analyzed.returncode, 0, analyzed.stderr)
            imported = run_cli("import-cif-manifest", manifest_path)
            self.assertEqual(imported.returncode, 0, imported.stderr)
            report = json.loads(imported.stdout)
            self.assertEqual(report["contract_name"], "structure-preparation-import")
            self.assertEqual(report["upstream_contract"], "structure-manifest@1.0")
            self.assertEqual(report["child"]["structure_kind"], "periodic-crystal")
            self.assertEqual(report["child"]["sites"][0]["site_id"], "Si-0")
            self.assertEqual(report["site_mapping"][0]["upstream_site_index"], 0)
            self.assertEqual(report["child"]["charge_state"]["status"], "unknown")
            self.assertEqual(report["claim_ceiling"], "no_positive_claim")
            self.assertFalse(report["promotion_authorized"])
            self.assertFalse(report["execution_authorized"])

            rounded = json.loads(manifest_path.read_text(encoding="utf-8"))
            rounded["structure"]["sites"][0]["cartesian_ang"][0] = 0.000005
            rounded_path = directory_path / "rounded-cartesian.json"
            rounded_path.write_text(json.dumps(rounded), encoding="utf-8")
            rounded_import = run_cli("import-cif-manifest", rounded_path)
            self.assertEqual(rounded_import.returncode, 0, rounded_import.stderr)

            unresolved = json.loads(manifest_path.read_text(encoding="utf-8"))
            unresolved["document"]["metadata"]["partial_occupancy_rows"] = [0]
            unresolved_path = directory_path / "unresolved-occupancy.json"
            unresolved_path.write_text(json.dumps(unresolved), encoding="utf-8")
            occupancy_refused = run_cli("import-cif-manifest", unresolved_path)
            self.assertEqual(occupancy_refused.returncode, 2)
            self.assertEqual(
                json.loads(occupancy_refused.stderr)["finding_id"],
                "MANIFEST_OCCUPANCY_MODEL_UNRESOLVED",
            )

            tampered = json.loads(manifest_path.read_text(encoding="utf-8"))
            tampered["structure_identity"]["fingerprint_input"]["sites"][0]["fractional"][0] = 0.125
            tampered_path = directory_path / "tampered.json"
            tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
            refused = run_cli("import-cif-manifest", tampered_path)
        self.assertEqual(refused.returncode, 2)
        self.assertEqual(json.loads(refused.stderr)["finding_id"], "MANIFEST_IDENTITY_HASH_MISMATCH")

    def test_periodic_audit_records_separate_identity_digests(self) -> None:
        result = run_cli("audit", FIXTURES / "si-periodic.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["calculation_readiness"], "requires-decision")
        self.assertIn(
            "SYMMETRY_VERIFICATION_PROVENANCE_UNRESOLVED",
            {item["finding_id"] for item in report["findings"]},
        )
        self.assertEqual(report["periodicity"]["dimensions"], 3)
        self.assertEqual(len(report["identity"]["structure_sha256"]), 64)
        self.assertNotEqual(report["identity"]["structure_sha256"], report["identity"]["site_order_sha256"])
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["future_gate_ceiling"], "input_gates_only")
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["execution_authorized"])
        strict = run_cli("audit", FIXTURES / "si-periodic.json", "--require-calculation-ready")
        self.assertEqual(strict.returncode, 2)

    def test_periodic_roundtrip_detects_reorder_and_image_shift_as_equivalent(self) -> None:
        result = run_cli(
            "roundtrip",
            FIXTURES / "si-periodic.json",
            FIXTURES / "si-wrapped-reordered.json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["roundtrip"]["classification"], "equivalent")
        mapping = {item["parent_site_id"]: item for item in report["roundtrip"]["site_mapping"]}
        self.assertEqual(mapping["Si-1"]["child_to_parent_image_shift"], [1, 0, 0])
        self.assertEqual(mapping["Si-1"]["residual_ang"], 0.0)
        self.assertNotEqual(
            report["roundtrip"]["parent_identity"]["site_order_sha256"],
            report["roundtrip"]["child_identity"]["site_order_sha256"],
        )

    def test_wrap_transform_preserves_mapping_and_is_equivalent(self) -> None:
        result = run_cli("transform", FIXTURES / "si-periodic.json", "--operation", "wrap")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["roundtrip"]["classification"], "equivalent")
        self.assertEqual(report["child"]["sites"][1]["fractional"], [0.25, 0.25, 0.25])
        self.assertEqual(report["site_mapping"][1]["child_to_parent_image_shift"], [1, 0, 0])

    def test_reorder_transform_requires_exact_site_set(self) -> None:
        accepted = run_cli(
            "transform",
            FIXTURES / "si-periodic.json",
            "--operation",
            "reorder",
            "--order",
            "Si-1,Si-0",
        )
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        child = json.loads(accepted.stdout)["child"]
        self.assertEqual([site["site_id"] for site in child["sites"]], ["Si-1", "Si-0"])
        refused = run_cli(
            "transform",
            FIXTURES / "si-periodic.json",
            "--operation",
            "reorder",
            "--order",
            "Si-0,Si-0",
        )
        self.assertEqual(refused.returncode, 2)
        self.assertEqual(json.loads(refused.stderr)["finding_id"], "SITE_ORDER_INVALID")

    def test_supercell_replication_is_explicit_and_invalidates_symmetry(self) -> None:
        result = run_cli(
            "transform",
            FIXTURES / "si-periodic.json",
            "--operation",
            "supercell",
            "--repeat",
            2,
            1,
            1,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(len(report["child"]["sites"]), 4)
        self.assertEqual(report["child"]["cell_ang"][0], [10.86, 0.0, 0.0])
        self.assertEqual(report["child"]["symmetry"]["status"], "unresolved")
        self.assertTrue(all(item["relation"] == "replicated" for item in report["site_mapping"]))
        si_one_mappings = [item for item in report["site_mapping"] if item["parent_site_id"] == "Si-1"]
        self.assertTrue(all(item["parent_image_shift_to_canonical"] == [1, 0, 0] for item in si_one_mappings))
        self.assertEqual([item["replica_shift"] for item in si_one_mappings], [[0, 0, 0], [1, 0, 0]])
        self.assertTrue(all(0.0 <= site["fractional"][0] < 1.0 for site in report["child"]["sites"]))
        self.assertEqual(report["roundtrip"]["classification"], "not-applicable-derived-structure")

    def test_general_integer_supercell_and_strain_are_bounded_and_traceable(self) -> None:
        general = run_cli(
            "transform",
            FIXTURES / "si-periodic.json",
            "--operation",
            "supercell",
            "--matrix",
            1,
            1,
            0,
            0,
            2,
            0,
            0,
            0,
            1,
        )
        self.assertEqual(general.returncode, 0, general.stderr)
        general_report = json.loads(general.stdout)
        self.assertEqual(len(general_report["child"]["sites"]), 4)
        self.assertEqual(general_report["child"]["cell_ang"][0], [5.43, 5.43, 0.0])
        self.assertEqual(general_report["child"]["cell_ang"][1], [0.0, 10.86, 0.0])
        self.assertTrue(
            all("replica_lattice_translation" in item for item in general_report["site_mapping"])
        )

        strained = run_cli(
            "transform",
            FIXTURES / "si-periodic.json",
            "--operation",
            "strain",
            "--deformation",
            1.05,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            1,
            "--max-strain",
            0.1,
        )
        self.assertEqual(strained.returncode, 0, strained.stderr)
        strained_report = json.loads(strained.stdout)
        self.assertAlmostEqual(strained_report["child"]["cell_ang"][0][0], 5.7015)
        self.assertEqual(strained_report["child"]["symmetry"]["status"], "unresolved")
        refused = run_cli(
            "transform",
            FIXTURES / "si-periodic.json",
            "--operation",
            "strain",
            "--deformation",
            1.2,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            1,
            "--max-strain",
            0.1,
        )
        self.assertEqual(refused.returncode, 2)
        self.assertEqual(json.loads(refused.stderr)["finding_id"], "STRAIN_BUDGET_EXCEEDED")

    def test_slab_and_interface_construction_record_bounded_geometry_search(self) -> None:
        slab = run_cli(
            "make-slab",
            FIXTURES / "si-periodic.json",
            "--axis",
            2,
            "--layers",
            2,
            "--vacuum-ang",
            12,
        )
        self.assertEqual(slab.returncode, 0, slab.stderr)
        slab_report = json.loads(slab.stdout)
        slab_child = slab_report["child"]
        self.assertEqual(slab_report["operation"], "slab")
        self.assertEqual(slab_child["structure_kind"], "periodic-slab")
        self.assertEqual(slab_child["pbc"], [True, True, False])
        self.assertEqual(len(slab_child["sites"]), 4)
        self.assertEqual(slab_child["symmetry"]["status"], "unresolved")
        self.assertIn("does not enumerate Miller indices", " ".join(slab_report["limitations"]))

        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            skewed_parent = json.loads(
                (FIXTURES / "si-periodic.json").read_text(encoding="utf-8")
            )
            skewed_parent["cell_ang"][2][0] = 1.0
            for site in skewed_parent["sites"]:
                site["cartesian_ang"] = [
                    sum(
                        site["fractional"][i] * skewed_parent["cell_ang"][i][j]
                        for i in range(3)
                    )
                    for j in range(3)
                ]
            skewed_path = directory_path / "skewed.json"
            skewed_path.write_text(json.dumps(skewed_parent), encoding="utf-8")
            skewed = run_cli(
                "make-slab",
                skewed_path,
                "--axis",
                2,
                "--layers",
                2,
                "--vacuum-ang",
                12,
            )
            self.assertEqual(skewed.returncode, 2)
            self.assertEqual(
                json.loads(skewed.stderr)["finding_id"],
                "SLAB_AXIS_NOT_SURFACE_NORMAL",
            )

            substrate = directory_path / "substrate.json"
            film = directory_path / "film.json"
            substrate.write_text(json.dumps(slab_child), encoding="utf-8")
            film.write_text(json.dumps(slab_child), encoding="utf-8")
            outside_insertion = run_cli(
                "site-edit",
                substrate,
                "--operation",
                "insert",
                "--site-id",
                "Li-outside-0",
                "--element",
                "Li",
                "--fractional",
                0.5,
                0.5,
                1.5,
            )
            interface = run_cli(
                "build-interface",
                substrate,
                film,
                "--max-repeat",
                2,
                "--max-strain",
                0.01,
                "--max-angle-deg",
                0.1,
                "--gap-ang",
                2.0,
                "--vacuum-ang",
                12.0,
                "--registry-shift",
                0.5,
                0.5,
            )
            interface_repeat = run_cli(
                "build-interface",
                substrate,
                film,
                "--max-repeat",
                2,
                "--max-strain",
                0.01,
                "--max-angle-deg",
                0.1,
                "--gap-ang",
                2.0,
                "--vacuum-ang",
                12.0,
                "--registry-shift",
                0.5,
                0.5,
            )
            self.assertEqual(interface.stdout, interface_repeat.stdout)
            mismatched_film = json.loads(json.dumps(slab_child))
            mismatched_film["cell_ang"][0] = [
                component * 1.04 for component in mismatched_film["cell_ang"][0]
            ]
            for site in mismatched_film["sites"]:
                site["cartesian_ang"] = [
                    sum(
                        site["fractional"][i] * mismatched_film["cell_ang"][i][j]
                        for i in range(3)
                    )
                    for j in range(3)
                ]
            film.write_text(json.dumps(mismatched_film), encoding="utf-8")
            strict_mismatch = run_cli(
                "build-interface",
                substrate,
                film,
                "--max-repeat",
                1,
                "--max-strain",
                0.01,
                "--max-angle-deg",
                0.1,
                "--gap-ang",
                2.0,
                "--vacuum-ang",
                12.0,
            )
            accepted_strain = run_cli(
                "build-interface",
                substrate,
                film,
                "--max-repeat",
                1,
                "--max-strain",
                0.05,
                "--max-angle-deg",
                0.1,
                "--gap-ang",
                2.0,
                "--vacuum-ang",
                12.0,
            )
        self.assertEqual(interface.returncode, 0, interface.stderr)
        self.assertEqual(outside_insertion.returncode, 2)
        self.assertEqual(
            json.loads(outside_insertion.stderr)["finding_id"],
            "INSERTION_OUTSIDE_CELL",
        )
        interface_report = json.loads(interface.stdout)
        self.assertEqual(interface_report["operation"], "merge")
        self.assertEqual(interface_report["operation_status"], "completed")
        self.assertEqual(interface_report["geometry_eligibility"], "eligible")
        self.assertEqual(
            interface_report["calculation_handoff"],
            interface_report["child_calculation_readiness"],
        )
        self.assertEqual(interface_report["scientific_stability"], "not-assessed")
        self.assertEqual(interface_report["operation_family"], "interface")
        self.assertEqual(interface_report["match_search"]["selected"]["substrate_repeat"], [1, 1])
        self.assertEqual(interface_report["match_search"]["selected"]["film_repeat"], [1, 1])
        self.assertGreaterEqual(interface_report["match_search"]["accepted_candidate_count"], 1)
        self.assertLessEqual(
            len(interface_report["match_search"]["accepted_candidate_sample"]),
            interface_report["match_search"]["accepted_candidate_sample_limit"],
        )
        self.assertEqual(len(interface_report["child"]["sites"]), 8)
        self.assertEqual(interface_report["mapping_status"], "exact")
        self.assertIsNotNone(
            interface_report["construction_metrics"]["closest_cross_interface_pair"]
        )
        self.assertIn("not an energetic stability result", " ".join(interface_report["limitations"]))
        self.assertEqual(strict_mismatch.returncode, 2)
        self.assertEqual(json.loads(strict_mismatch.stderr)["finding_id"], "INTERFACE_MATCH_NOT_FOUND")
        self.assertEqual(accepted_strain.returncode, 0, accepted_strain.stderr)
        strained_match = json.loads(accepted_strain.stdout)["match_search"]["selected"]
        self.assertAlmostEqual(strained_match["film_length_strain"][0], -0.038461538462)

    def test_minimum_distance_solves_skew_periodic_closest_vectors(self) -> None:
        periodic = {
            "cell_ang": [
                [1.0, 0.0, 0.0],
                [10.1, 0.1, 0.0],
                [0.0, 0.0, 10.0],
            ],
            "pbc": [True, True, False],
            "sites": [
                {
                    "site_id": "X-0",
                    "fractional": [0.0, 0.0, 0.5],
                    "cartesian_ang": [0.0, 0.0, 5.0],
                }
            ],
        }
        closest = minimum_distance(periodic)
        self.assertIsNotNone(closest)
        self.assertEqual(closest["site_ids"], ["X-0", "X-0"])
        self.assertEqual(closest["relation"], "periodic-self-image")
        self.assertAlmostEqual(closest["distance_ang"], 2.0**0.5 / 10.0)
        with self.assertRaises(GateError):
            enforce_minimum_distance(periodic, 0.5)

        periodic["sites"].append(
            {
                "site_id": "X-1",
                "fractional": [0.2, 0.2, 0.5],
                "cartesian_ang": [2.22, 0.02, 5.0],
            }
        )
        closest_distinct = minimum_distance(
            periodic,
            left_ids={"X-0"},
            right_ids={"X-1"},
        )
        self.assertIsNotNone(closest_distinct)
        self.assertEqual(closest_distinct["site_ids"], ["X-0", "X-1"])
        self.assertEqual(closest_distinct["relation"], "distinct-sites")
        self.assertAlmostEqual(closest_distinct["distance_ang"], 0.0208**0.5)

        with mock.patch.object(
            structure_prepare,
            "MAX_PERIODIC_IMAGE_EVALUATIONS",
            10,
        ):
            with self.assertRaises(GateError) as caught:
                minimum_distance(periodic)
        self.assertEqual(
            caught.exception.finding_id,
            "PERIODIC_IMAGE_SEARCH_BUDGET_EXCEEDED",
        )

    def test_minimum_distance_keeps_full_precision_at_threshold(self) -> None:
        near_threshold = {
            "cell_ang": None,
            "pbc": [False, False, False],
            "sites": [
                {
                    "site_id": "A-0",
                    "fractional": None,
                    "cartesian_ang": [0.0, 0.0, 0.0],
                },
                {
                    "site_id": "B-0",
                    "fractional": None,
                    "cartesian_ang": [0.5999999999996, 0.0, 0.0],
                },
            ],
        }
        with self.assertRaises(GateError):
            enforce_minimum_distance(near_threshold, 0.6)

    def test_result_schema_requires_decoupled_state_axes(self) -> None:
        generated = run_cli(
            "make-slab",
            FIXTURES / "si-periodic.json",
            "--axis",
            2,
            "--layers",
            2,
            "--vacuum-ang",
            12,
        )
        self.assertEqual(generated.returncode, 0, generated.stderr)
        report = json.loads(generated.stdout)
        schema = json.loads(
            (ROOT / "schemas" / "structure-preparation-output.schema.json").read_text(
                encoding="utf-8"
            )
        )
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        self.assertEqual(list(validator.iter_errors(report)), [])

        tampered_values = {
            "operation_status": "pending",
            "geometry_eligibility": "stable",
            "calculation_handoff": "completed",
            "scientific_stability": "stable",
        }
        for field, value in tampered_values.items():
            with self.subTest(tampered=field):
                tampered = json.loads(json.dumps(report))
                tampered[field] = value
                self.assertTrue(list(validator.iter_errors(tampered)))

        for field in tampered_values:
            with self.subTest(missing=field):
                missing = json.loads(json.dumps(report))
                del missing[field]
                self.assertTrue(list(validator.iter_errors(missing)))

    def test_site_edits_preserve_created_removed_and_substitution_lineage(self) -> None:
        inserted = run_cli(
            "site-edit",
            FIXTURES / "si-periodic.json",
            "--operation",
            "insert",
            "--site-id",
            "Li-interstitial-0",
            "--element",
            "Li",
            "--fractional",
            0.5,
            0.5,
            0.5,
        )
        self.assertEqual(inserted.returncode, 0, inserted.stderr)
        inserted_report = json.loads(inserted.stdout)
        self.assertEqual(inserted_report["operation"], "interstitial")
        self.assertEqual(len(inserted_report["child"]["sites"]), 3)
        self.assertIn("created", {item["relation"] for item in inserted_report["site_mapping"]})
        self.assertEqual(inserted_report["child"]["charge_state"]["status"], "unknown")

        collision = run_cli(
            "site-edit",
            FIXTURES / "si-periodic.json",
            "--operation",
            "insert",
            "--site-id",
            "Li-collision-0",
            "--element",
            "Li",
            "--fractional",
            0,
            0,
            0,
        )
        self.assertEqual(collision.returncode, 2)
        self.assertEqual(json.loads(collision.stderr)["finding_id"], "MINIMUM_DISTANCE_VIOLATION")

        removed = run_cli(
            "site-edit",
            FIXTURES / "si-periodic.json",
            "--operation",
            "remove",
            "--site-id",
            "Si-1",
        )
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertIn("removed", {item["relation"] for item in json.loads(removed.stdout)["site_mapping"]})

        substituted = run_cli(
            "site-edit",
            FIXTURES / "si-periodic.json",
            "--operation",
            "substitute",
            "--site-id",
            "Si-1",
            "--element",
            "Ge",
        )
        self.assertEqual(substituted.returncode, 0, substituted.stderr)
        substituted_child = json.loads(substituted.stdout)["child"]
        species = {site["site_id"]: site["species"] for site in substituted_child["sites"]}
        self.assertEqual(species["Si-1"], [{"element": "Ge", "occupancy": 1.0}])

    def test_adsorbate_and_host_guest_placement_are_explicit_not_stability_claims(self) -> None:
        slab = run_cli(
            "make-slab",
            FIXTURES / "si-periodic.json",
            "--layers",
            2,
            "--vacuum-ang",
            14,
        )
        self.assertEqual(slab.returncode, 0, slab.stderr)
        with tempfile.TemporaryDirectory() as directory:
            host = Path(directory) / "host.json"
            host.write_text(json.dumps(json.loads(slab.stdout)["child"]), encoding="utf-8")
            adsorbate = run_cli(
                "place-guest",
                host,
                FIXTURES / "water-molecule.json",
                "--mode",
                "adsorbate",
                "--anchor-site",
                "O-0",
                "--surface-frac",
                0.5,
                0.5,
                "--height-ang",
                2.0,
                "--rotation-deg",
                0,
                0,
                30,
            )
        self.assertEqual(adsorbate.returncode, 0, adsorbate.stderr)
        adsorbate_report = json.loads(adsorbate.stdout)
        self.assertEqual(adsorbate_report["operation"], "adsorbate")
        self.assertEqual(len(adsorbate_report["child"]["sites"]), 7)
        self.assertIn("guest-O-0", {site["site_id"] for site in adsorbate_report["child"]["sites"]})
        self.assertIn("does not search adsorption", " ".join(adsorbate_report["limitations"]))

        host_guest = run_cli(
            "place-guest",
            FIXTURES / "si-periodic.json",
            FIXTURES / "water-molecule.json",
            "--mode",
            "host-guest",
            "--anchor-site",
            "O-0",
            "--target-cart",
            2.715,
            2.715,
            2.715,
            "--min-distance-ang",
            0.1,
        )
        self.assertEqual(host_guest.returncode, 0, host_guest.stderr)
        host_guest_report = json.loads(host_guest.stdout)
        self.assertEqual(host_guest_report["operation"], "merge")
        self.assertEqual(len(host_guest_report["parent_identities"]), 2)

    def test_disorder_is_preserved_but_blocks_calculation_readiness(self) -> None:
        audit = run_cli("audit", FIXTURES / "disordered-site.json")
        self.assertEqual(audit.returncode, 0, audit.stderr)
        report = json.loads(audit.stdout)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["calculation_readiness"], "blocked")
        self.assertIn("OCCUPANCY_DISORDER_PRESENT", {item["finding_id"] for item in report["findings"]})
        strict = run_cli("audit", FIXTURES / "disordered-site.json", "--require-calculation-ready")
        self.assertEqual(strict.returncode, 2)

    def test_coordinate_mismatch_fails_closed(self) -> None:
        result = run_cli("audit", FIXTURES / "coordinate-mismatch.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(result.stderr)["finding_id"], "COORDINATE_REPRESENTATION_MISMATCH")

    def test_molecular_charge_multiplicity_parity_is_checked(self) -> None:
        value = json.loads((FIXTURES / "water-molecule.json").read_text(encoding="utf-8"))
        value["spin_state"]["multiplicity"] = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-spin.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            result = run_cli("audit", path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "CHARGE_SPIN_PARITY_MISMATCH")

    def test_export_plan_is_non_executed_and_keeps_site_order(self) -> None:
        result = run_cli("plan-export", FIXTURES / "water-molecule.json", "--target", "qe")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["execution_state"], "not-executed")
        self.assertEqual([item["site_id"] for item in report["atom_order_mapping"]], ["O-0", "H-0", "H-1"])

    def test_duplicate_keys_and_nonfinite_tolerance_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text('{"contract_name":"x","contract_name":"y"}', encoding="utf-8")
            result = run_cli("audit", duplicate)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "JSON_INVALID")
        result = run_cli("audit", FIXTURES / "si-periodic.json", "--tolerance-ang", "nan")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "TOLERANCE_INVALID")

    def test_symlink_input_and_output_overwrite_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            linked = directory_path / "linked.json"
            linked.symlink_to(FIXTURES / "si-periodic.json")
            refused_input = run_cli("audit", linked)
            self.assertEqual(refused_input.returncode, 2)
            self.assertEqual(json.loads(refused_input.stderr)["finding_id"], "INPUT_NOT_REGULAR")
            output = directory_path / "report.json"
            first = run_cli("audit", FIXTURES / "si-periodic.json", "--out", output)
            second = run_cli("audit", FIXTURES / "si-periodic.json", "--out", output)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(json.loads(second.stderr)["finding_id"], "OUTPUT_EXISTS")

    def test_backend_probe_never_claims_execution(self) -> None:
        result = run_cli("probe-backends")
        self.assertIn(result.returncode, {0, 3})
        report = json.loads(result.stdout)
        self.assertFalse(report["imports_performed"])
        self.assertFalse(report["operations_executed"])
        self.assertEqual(
            {item["distribution"] for item in report["distributions"]},
            {"ase", "pymatgen", "pymatgen-core", "rdkit"},
        )

    def test_candidate_schemas_and_fixtures_are_strict_json(self) -> None:
        paths = (
            sorted((ROOT / "schemas").glob("*.json"))
            + sorted(FIXTURES.glob("*.json"))
            + [ROOT / "references" / "provider-capabilities.json"]
        )
        for path in paths:
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(value, dict)
        catalog = json.loads((ROOT / "references" / "provider-capabilities.json").read_text(encoding="utf-8"))
        capability_ids = [item["capability_id"] for item in catalog["capabilities"]]
        self.assertEqual(len(capability_ids), len(set(capability_ids)))
        self.assertTrue(all(item["official_docs"] for item in catalog["capabilities"]))
        self.assertTrue(
            all(item["native_state"] in {"native-api-tested", "native-not-run"} for item in catalog["capabilities"])
        )
        manifest = json.loads((ROOT / "references" / "fixture-manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["fixtures"]:
            path = ROOT / entry["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"])


if __name__ == "__main__":
    unittest.main()
