from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "structure_prepare.py"
FIXTURES = ROOT / "fixtures"


def run_cli(*arguments: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(item) for item in arguments)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class StructurePrepareCliTests(unittest.TestCase):
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
