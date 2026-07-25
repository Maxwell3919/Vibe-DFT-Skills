from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


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


def fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def write_value(directory: Path, name: str, value: dict[str, object]) -> Path:
    path = directory / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


class StructureMutationRedTeamTests(unittest.TestCase):
    def test_finding_catalog_covers_every_gate_error_literal(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        codes = set(re.findall(r'GateError\(\s*"([A-Z][A-Z0-9_]+)"', source))
        catalog = (ROOT / "references" / "finding-catalog.md").read_text(encoding="utf-8")
        missing = sorted(code for code in codes if f"`{code}`" not in catalog)
        self.assertEqual(missing, [])

    def test_unwrapped_notice_applies_only_to_periodic_axes(self) -> None:
        value = fixture("si-periodic.json")
        value["structure_kind"] = "periodic-slab"
        value["pbc"] = [True, True, False]
        value["sites"][0]["fractional"] = [0.0, 0.0, 1.25]
        value["sites"][0]["cartesian_ang"] = [0.0, 0.0, 6.7875]
        value["sites"][1]["fractional"] = [0.25, 0.25, 0.25]
        value["sites"][1]["cartesian_ang"] = [1.3575, 1.3575, 1.3575]
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            nonperiodic = write_value(directory_path, "nonperiodic-z.json", value)
            report = run_cli("audit", nonperiodic)
            self.assertEqual(report.returncode, 0, report.stderr)
            finding_ids = {item["finding_id"] for item in json.loads(report.stdout)["findings"]}
            self.assertNotIn("PERIODIC_IMAGE_UNWRAPPED", finding_ids)

            value["sites"][0]["fractional"][0] = 1.25
            value["sites"][0]["cartesian_ang"][0] = 6.7875
            periodic = write_value(directory_path, "periodic-x.json", value)
            report = run_cli("audit", periodic)
            self.assertEqual(report.returncode, 0, report.stderr)
            finding_ids = {item["finding_id"] for item in json.loads(report.stdout)["findings"]}
            self.assertIn("PERIODIC_IMAGE_UNWRAPPED", finding_ids)

    def test_single_fd_snapshot_detects_link_count_and_final_path_mutations(self) -> None:
        spec = importlib.util.spec_from_file_location("structure_prepare_redteam", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            for mutation_kind in ("hardlink", "replace-path"):
                with self.subTest(mutation_kind=mutation_kind):
                    source = directory_path / f"source-{mutation_kind}.json"
                    source.write_bytes((FIXTURES / "si-periodic.json").read_bytes())
                    alias = directory_path / f"alias-{mutation_kind}.json"
                    moved = directory_path / f"moved-{mutation_kind}.json"
                    real_fdopen = module.os.fdopen

                    class MutatingHandle:
                        def __init__(self, handle: object) -> None:
                            self.handle = handle
                            self.mutated = False

                        def __enter__(self) -> "MutatingHandle":
                            return self

                        def __exit__(self, *exc: object) -> None:
                            self.handle.close()

                        def fileno(self) -> int:
                            return self.handle.fileno()

                        def read(self, *args: object) -> bytes:
                            raw = self.handle.read(*args)
                            if not self.mutated:
                                self.mutated = True
                                if mutation_kind == "hardlink":
                                    alias.hardlink_to(source)
                                else:
                                    source.rename(moved)
                                    source.write_bytes(raw)
                            return raw

                    def mutating_fdopen(*args: object, **kwargs: object) -> MutatingHandle:
                        return MutatingHandle(real_fdopen(*args, **kwargs))

                    with mock.patch.object(module.os, "fdopen", side_effect=mutating_fdopen):
                        with self.assertRaises(module.GateError) as caught:
                            module.load_json(str(source))
                    self.assertEqual(caught.exception.finding_id, "INPUT_CHANGED_DURING_READ")

    def test_machine_decision_table_is_strict_and_lifecycle_safe(self) -> None:
        def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
            value: dict[str, object] = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError(f"duplicate key: {key}")
                value[key] = item
            return value

        table = json.loads(
            (ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8"),
            object_pairs_hook=no_duplicates,
        )
        self.assertEqual(
            set(table),
            {
                "contract_name", "schema_version", "skill_id", "lifecycle", "selection_policy",
                "default_case_id", "current_claim", "execution_authorized",
                "promotion_authorized", "cases",
            },
        )
        self.assertEqual(table["contract_name"], "candidate-decision-table")
        self.assertEqual(table["schema_version"], "1.0")
        self.assertEqual(table["skill_id"], "dft-structure-preparation")
        self.assertEqual(table["lifecycle"], "development")
        self.assertEqual(table["selection_policy"], "first-match-by-ascending-priority")
        self.assertEqual(table["current_claim"], "no_positive_claim")
        self.assertFalse(table["execution_authorized"])
        self.assertFalse(table["promotion_authorized"])
        cases = table["cases"]
        self.assertGreaterEqual(len(cases), 10)
        required = {
            "case_id", "priority", "severity", "condition", "required_evidence",
            "finding_codes", "action_state", "expected_exit_codes", "current_claim",
            "execution_authorized", "promotion_authorized", "minimum_next_action",
        }
        case_ids = []
        actions = []
        for priority, case in enumerate(cases, start=1):
            self.assertEqual(set(case), required)
            self.assertRegex(case["case_id"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            case_ids.append(case["case_id"])
            self.assertIs(type(case["priority"]), int)
            self.assertEqual(case["priority"], priority)
            self.assertIn(case["severity"], {"P0", "P1", "P2"})
            self.assertIn(
                case["action_state"],
                {"needs_evidence", "ready_for_deterministic_check", "local_gate_blocked", "local_gate_passed_limited"},
            )
            for field in ("condition", "minimum_next_action"):
                self.assertIsInstance(case[field], str)
                self.assertTrue(case[field].strip())
            actions.append(case["minimum_next_action"])
            self.assertEqual(len(case["required_evidence"]), len(set(case["required_evidence"])))
            self.assertEqual(len(case["finding_codes"]), len(set(case["finding_codes"])))
            for finding_id in case["finding_codes"]:
                self.assertRegex(finding_id, r"^[A-Z][A-Z0-9_.-]+$")
            self.assertTrue(case["expected_exit_codes"])
            self.assertEqual(len(case["expected_exit_codes"]), len(set(case["expected_exit_codes"])))
            self.assertEqual(case["current_claim"], "no_positive_claim")
            self.assertFalse(case["execution_authorized"])
            self.assertFalse(case["promotion_authorized"])
        self.assertEqual(len(case_ids), len(set(case_ids)))
        self.assertEqual(len(actions), len(set(actions)))
        self.assertEqual(table["default_case_id"], cases[-1]["case_id"])
        self.assertEqual(cases[-1]["required_evidence"], [])
        self.assertIn(cases[-1]["action_state"], {"needs_evidence", "local_gate_blocked"})

    def test_every_candidate_report_is_lifecycle_capped(self) -> None:
        commands = {
            "audit": ("audit", FIXTURES / "si-periodic.json"),
            "roundtrip": (
                "roundtrip",
                FIXTURES / "si-periodic.json",
                FIXTURES / "si-periodic.json",
            ),
            "transform": (
                "transform",
                FIXTURES / "si-periodic.json",
                "--operation",
                "wrap",
            ),
            "export-plan": (
                "plan-export",
                FIXTURES / "water-molecule.json",
                "--target",
                "qe",
            ),
            "probe": ("probe-backends",),
        }
        for label, command in commands.items():
            with self.subTest(label=label):
                result = run_cli(*command)
                self.assertIn(result.returncode, {0, 3}, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["claim_ceiling"], "no_positive_claim")
                self.assertFalse(report["promotion_authorized"])
                self.assertFalse(report["execution_authorized"])
                self.assertIn(
                    report["future_gate_ceiling"],
                    {"input_gates_only", "documented_behavior_only"},
                )

    def test_blocked_envelope_is_lifecycle_capped_and_source_label_is_private(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            labels = []
            for name in ("patient secret.json", "patient_secret.json"):
                private_source = directory_path / name
                private_source.write_bytes((FIXTURES / "si-periodic.json").read_bytes())
                success = run_cli("audit", private_source)
                self.assertEqual(success.returncode, 0, success.stderr)
                labels.append(json.loads(success.stdout)["source"]["label"])
            invalid = directory_path / "invalid.json"
            invalid.write_text('{"x": 1, "x": 2}', encoding="utf-8")
            blocked = run_cli("audit", invalid)
        for label in labels:
            self.assertRegex(label, r"^source-[a-f0-9]{12}\.json$")
            self.assertNotIn("patient", label)
        self.assertEqual(blocked.returncode, 2)
        envelope = json.loads(blocked.stderr)
        self.assertEqual(envelope["claim_ceiling"], "no_positive_claim")
        self.assertFalse(envelope["promotion_authorized"])
        self.assertFalse(envelope["execution_authorized"])
        self.assertEqual(envelope["contract_name"], "structure-preparation-error")
        self.assertEqual(envelope["schema_version"], "1.0")
        self.assertEqual(
            envelope["provenance"],
            {"tool": "structure_prepare.py", "tool_version": "0.2.0-candidate"},
        )

    def test_atomic_output_refuses_input_path_and_hardlink_or_symlink_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            source = directory_path / "source.json"
            source.write_bytes((FIXTURES / "si-periodic.json").read_bytes())
            expected_sha256 = __import__("hashlib").sha256(source.read_bytes()).hexdigest()
            hardlink = directory_path / "hardlink.json"
            hardlink.hardlink_to(source)
            symlink = directory_path / "symlink.json"
            symlink.symlink_to(source)
            for label, output in {"same": source, "hardlink": hardlink, "symlink": symlink}.items():
                with self.subTest(label=label):
                    result = run_cli("audit", source, "--out", output)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(json.loads(result.stderr)["finding_id"], "OUTPUT_EXISTS")
                    self.assertEqual(__import__("hashlib").sha256(source.read_bytes()).hexdigest(), expected_sha256)
            fresh = directory_path / "fresh.json"
            result = run_cli("audit", source, "--out", fresh)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(fresh.read_text(encoding="utf-8"))["status"], "pass")
            self.assertEqual(list(directory_path.glob("*.candidate-*.tmp")), [])

    def test_identity_exposes_decoupled_domain_hashes(self) -> None:
        result = run_cli("audit", FIXTURES / "si-periodic.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        identity = json.loads(result.stdout)["identity"]
        self.assertTrue(
            {
                "geometry_sha256",
                "labeled_structure_sha256",
                "site_order_sha256",
                "periodicity_sha256",
                "composition_occupancy_sha256",
                "electronic_state_sha256",
                "symmetry_sha256",
                "representation_sha256",
            }.issubset(identity)
        )

    def test_charge_spin_and_symmetry_mutations_cannot_upgrade_to_equivalent(self) -> None:
        parent = fixture("si-periodic.json")
        mutations = []
        charge = json.loads(json.dumps(parent))
        charge["charge_state"]["net_charge_e"] = 1
        mutations.append(("charge", charge, "electronic-state"))
        spin = json.loads(json.dumps(parent))
        spin["spin_state"] = {"status": "known", "multiplicity": 2}
        mutations.append(("spin", spin, "electronic-state"))
        symmetry = json.loads(json.dumps(parent))
        symmetry["symmetry"]["status"] = "declared"
        symmetry["symmetry"]["backend"] = None
        symmetry["symmetry"]["backend_version"] = None
        mutations.append(("symmetry", symmetry, "symmetry"))
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            for label, child, expected_difference in mutations:
                with self.subTest(label=label):
                    child_path = write_value(directory_path, f"{label}.json", child)
                    result = run_cli("roundtrip", FIXTURES / "si-periodic.json", child_path)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report["roundtrip"]["classification"], "lossy")
                    self.assertIn(expected_difference, report["roundtrip"]["differences"])

    def test_cell_mutation_inside_tolerance_is_equivalent_but_not_exact(self) -> None:
        child = fixture("si-periodic.json")
        child["cell_ang"][0][0] += 5.0e-9
        for site in child["sites"]:
            fractional = site["fractional"]
            site["cartesian_ang"] = [
                sum(fractional[i] * child["cell_ang"][i][j] for i in range(3)) for j in range(3)
            ]
        with tempfile.TemporaryDirectory() as directory:
            child_path = write_value(Path(directory), "near-cell.json", child)
            result = run_cli("roundtrip", FIXTURES / "si-periodic.json", child_path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["roundtrip"]["classification"], "equivalent")

    def test_nonperiodic_axis_shift_cannot_be_treated_as_periodic_image(self) -> None:
        parent = fixture("si-periodic.json")
        parent["structure_id"] = "slab-parent-fixture"
        parent["structure_kind"] = "periodic-slab"
        parent["pbc"] = [True, True, False]
        parent["symmetry"] = {
            "status": "unresolved",
            "number": None,
            "symbol": None,
            "tolerance_ang": None,
            "backend": None,
            "backend_version": None,
        }
        child = json.loads(json.dumps(parent))
        child["structure_id"] = "slab-child-fixture"
        child["sites"][1]["fractional"][2] += 1.0
        child["sites"][1]["cartesian_ang"][2] += child["cell_ang"][2][2]
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            parent_path = write_value(directory_path, "parent-slab.json", parent)
            child_path = write_value(directory_path, "child-slab.json", child)
            result = run_cli("roundtrip", parent_path, child_path)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["roundtrip"]["classification"], "lossy")
        self.assertIn("coordinate:Si-1", report["roundtrip"]["differences"])

    def test_isolated_cluster_charge_spin_parity_is_not_skipped(self) -> None:
        cluster = fixture("water-molecule.json")
        cluster["structure_kind"] = "isolated-cluster"
        cluster["spin_state"]["multiplicity"] = 2
        with tempfile.TemporaryDirectory() as directory:
            cluster_path = write_value(Path(directory), "cluster.json", cluster)
            result = run_cli("audit", cluster_path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "CHARGE_SPIN_PARITY_MISMATCH")

    def test_supercell_budget_blocks_before_large_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "large.json"
            result = run_cli(
                "transform",
                FIXTURES / "si-periodic.json",
                "--operation",
                "supercell",
                "--repeat",
                2049,
                1,
                1,
                "--out",
                output,
            )
            self.assertFalse(output.exists())
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "SUPERCELL_BUDGET_EXCEEDED")

    def test_transform_rejects_irrelevant_parameters_and_nonpositive_matrix(self) -> None:
        conflict = run_cli(
            "transform",
            FIXTURES / "si-periodic.json",
            "--operation",
            "wrap",
            "--repeat",
            2,
            1,
            1,
        )
        self.assertEqual(conflict.returncode, 2)
        self.assertEqual(json.loads(conflict.stderr)["finding_id"], "PARAMETER_CONFLICT")
        reflected = run_cli(
            "transform",
            FIXTURES / "si-periodic.json",
            "--operation",
            "supercell",
            "--matrix",
            -1,
            0,
            0,
            0,
            1,
            0,
            0,
            0,
            1,
        )
        self.assertEqual(reflected.returncode, 2)
        self.assertEqual(json.loads(reflected.stderr)["finding_id"], "SUPERCELL_MATRIX_INVALID")

    def test_export_plan_cannot_claim_target_writes_or_parameter_choices(self) -> None:
        result = run_cli("plan-export", FIXTURES / "water-molecule.json", "--target", "vasp")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["target_write_performed"])
        self.assertFalse(report["target_parameter_selection_performed"])
        self.assertEqual(report["generated_target_files"], [])
        self.assertEqual(report["target_coordinate_unit"], "unresolved-by-target-skill")
        self.assertEqual(report["source_coordinate_unit"], "angstrom")
        self.assertNotIn("planned_files", report)

    def test_transform_binds_mapping_content_to_a_hash(self) -> None:
        result = run_cli(
            "transform",
            FIXTURES / "si-periodic.json",
            "--operation",
            "reorder",
            "--order",
            "Si-1,Si-0",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertRegex(report["site_mapping_sha256"], r"^[a-f0-9]{64}$")

    def test_exact_equivalent_and_lossy_classes_are_monotonic(self) -> None:
        parent = fixture("si-periodic.json")
        exact = json.loads(json.dumps(parent))
        exact["structure_id"] = "same-content-new-record"
        reordered = fixture("si-wrapped-reordered.json")
        lossy = json.loads(json.dumps(parent))
        lossy["sites"][0]["species"][0]["occupancy"] = 0.999999999999
        cases = [("exact", exact, 0), ("equivalent", reordered, 0), ("lossy", lossy, 2)]
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            for expected, value, exit_code in cases:
                with self.subTest(expected=expected):
                    child_path = write_value(directory_path, f"{expected}.json", value)
                    result = run_cli("roundtrip", FIXTURES / "si-periodic.json", child_path)
                    self.assertEqual(result.returncode, exit_code, result.stdout + result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report["roundtrip"]["classification"], expected)
                    if expected == "lossy":
                        self.assertEqual([item["finding_id"] for item in report["findings"]], ["ROUNDTRIP_LOSSY"])


if __name__ == "__main__":
    unittest.main()
