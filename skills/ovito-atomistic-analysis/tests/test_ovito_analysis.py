from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ovito_analysis.py"
FIXTURES = ROOT / "fixtures"


def run_cli(*arguments: object, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(item) for item in arguments)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )


def make_inventory(directory: Path, source: Path | None = None) -> Path:
    inventory_path = directory / "inventory.json"
    result = run_cli("inventory", source or FIXTURES / "two-frame.extxyz", "--out", inventory_path)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return inventory_path


def fake_ovito(directory: Path, version: str = "3.15.5") -> dict[str, str]:
    package = directory / "ovito"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(f'version_string = "{version}"\n', encoding="utf-8")
    (package / "io.py").write_text(
        """
class Property:
    def __init__(self, name):
        self.name = name

class Particles:
    count = 2
    def values(self):
        return [Property("Particle Type"), Property("Position")]

class Cell:
    pbc = (True, True, True)
    matrix = ((5.0, 0.0, 0.0), (0.0, 5.0, 0.0), (0.0, 0.0, 5.0))
    def __getitem__(self, key):
        row, column = key
        return self.matrix[row][column]

class Data:
    particles = Particles()
    cell = Cell()

class Pipeline:
    def compute(self, frame):
        return Data()

def import_file(path, *, sort_particles=False):
    if sort_particles is not False:
        raise ValueError("candidate must preserve source storage order")
    return Pipeline()
""".lstrip(),
        encoding="utf-8",
    )
    metadata = directory / "ovito-3.15.5.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: ovito\nVersion: 3.15.5\n",
        encoding="utf-8",
    )
    environment = dict(os.environ)
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(directory) if not existing else str(directory) + os.pathsep + existing
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


class OvitoCandidateCliTests(unittest.TestCase):
    def test_inventory_parses_extxyz_without_claiming_ovito_execution(self) -> None:
        result = run_cli("inventory", FIXTURES / "two-frame.extxyz")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["format"], "extxyz")
        self.assertEqual(report["frame_count"], 2)
        self.assertEqual(report["atom_count"], 2)
        self.assertEqual(report["available_properties"], ["force", "pos", "species"])
        self.assertEqual(report["pbc_status"], "explicit")
        self.assertEqual(report["cell_status"], "present-all")
        self.assertEqual(report["parser_state"], "parser-only")
        self.assertFalse(report["ovito_executed"])
        self.assertEqual(report["analysis_readiness"], "ready")
        self.assertEqual(report["length_unit"], "undeclared-source-native")
        self.assertEqual(report["particle_identifier_status"], "absent-all")

    def test_inventory_blocks_changed_species_order_and_strict_readiness(self) -> None:
        result = run_cli("inventory", FIXTURES / "changing-order.xyz")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["format"], "xyz")
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["species_order_constant"])
        self.assertIn("TRAJECTORY_SPECIES_ORDER_CHANGED", {item["finding_id"] for item in report["findings"]})
        strict = run_cli("inventory", FIXTURES / "changing-order.xyz", "--require-analysis-ready")
        self.assertEqual(strict.returncode, 2)

    def test_stable_extxyz_ids_allow_reordering_without_losing_mapping(self) -> None:
        trajectory_text = """2
Lattice=\"5 0 0 0 5 0 0 0 5\" Properties=species:S:1:pos:R:3:id:I:1 pbc=\"T T T\"
C 0 0 0 10
H 1 0 0 20
2
Lattice=\"5 0 0 0 5 0 0 0 5\" Properties=species:S:1:pos:R:3:id:I:1 pbc=\"T T T\"
H 1.1 0 0 20
C 0.1 0 0 10
"""
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            trajectory = directory_path / "stable-ids.extxyz"
            trajectory.write_text(trajectory_text, encoding="utf-8")
            inventory_path = directory_path / "inventory.json"
            inventory_result = run_cli("inventory", trajectory, "--out", inventory_path, "--require-analysis-ready")
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            spec = json.loads((FIXTURES / "metadata-pipeline.json").read_text(encoding="utf-8"))
            spec["source"]["sha256"] = inventory["source"]["sha256"]
            spec["frame_selection"] = {"mode": "indices", "indices": [0]}
            spec["mapping_policy"] = "require-stable-site-ids"
            spec_path = directory_path / "pipeline.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            plan = run_cli("plan", "--inventory", inventory_path, "--pipeline", spec_path, "--require-execution-ready")
        self.assertEqual(inventory_result.returncode, 0, inventory_result.stderr)
        self.assertEqual(inventory["particle_identifier_status"], "present-stable")
        self.assertEqual(inventory["site_order_status"], "stable-site-ids")
        self.assertFalse(inventory["species_order_constant"])
        self.assertIn("TRAJECTORY_STORAGE_ORDER_CHANGED_WITH_IDS", {item["finding_id"] for item in inventory["findings"]})
        self.assertEqual(plan.returncode, 0, plan.stderr)

    def test_stable_ids_block_when_species_association_changes_but_species_order_does_not(self) -> None:
        trajectory_text = """2
Lattice="5 0 0 0 5 0 0 0 5" Properties=species:S:1:pos:R:3:id:I:1 pbc="T T T"
C 0 0 0 10
H 1 0 0 20
2
Lattice="5 0 0 0 5 0 0 0 5" Properties=species:S:1:pos:R:3:id:I:1 pbc="T T T"
C 0.1 0 0 20
H 1.1 0 0 10
"""
        with tempfile.TemporaryDirectory() as directory:
            trajectory = Path(directory) / "changed-id-species.extxyz"
            trajectory.write_text(trajectory_text, encoding="utf-8")
            result = run_cli("inventory", trajectory)
            strict_result = run_cli("inventory", trajectory, "--require-analysis-ready")
        inventory = json.loads(result.stdout)
        self.assertEqual(strict_result.returncode, 2)
        self.assertTrue(inventory["species_order_constant"])
        self.assertEqual(inventory["particle_identifier_status"], "present-stable")
        self.assertIn(
            "TRAJECTORY_IDENTIFIER_SPECIES_CHANGED",
            {item["finding_id"] for item in inventory["findings"]},
        )
        self.assertEqual(inventory["analysis_readiness"], "blocked")

    def test_missing_pbc_and_unknown_cutoff_unit_fail_closed_at_plan_boundary(self) -> None:
        trajectory_text = """1
Lattice=\"5 0 0 0 5 0 0 0 5\" Properties=species:S:1:pos:R:3
Si 0 0 0
"""
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            trajectory = directory_path / "undeclared-pbc.extxyz"
            trajectory.write_text(trajectory_text, encoding="utf-8")
            inventory_path = directory_path / "inventory.json"
            inventory_result = run_cli("inventory", trajectory, "--out", inventory_path)
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            spec = json.loads((FIXTURES / "metadata-pipeline.json").read_text(encoding="utf-8"))
            spec["source"]["sha256"] = inventory["source"]["sha256"]
            spec["frame_selection"] = {"mode": "indices", "indices": [0]}
            spec_path = directory_path / "pipeline.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            blocked_plan = run_cli("plan", "--inventory", inventory_path, "--pipeline", spec_path)

            ready_directory = directory_path / "ready"
            ready_directory.mkdir()
            ready_inventory = make_inventory(ready_directory)
            cutoff_spec = json.loads((FIXTURES / "metadata-pipeline.json").read_text(encoding="utf-8"))
            cutoff_spec["operations"] = [{
                "operation_id": "coordination-0",
                "kind": "coordination-analysis",
                "parameters": {"cutoff_source_units": 3.0, "number_of_bins": 100},
                "evidence_role": "numerical-analysis",
            }]
            cutoff_spec["outputs"] = [{"output_id": "rdf-table-0", "kind": "data-table", "label": "rdf.txt"}]
            cutoff_path = directory_path / "cutoff.json"
            cutoff_path.write_text(json.dumps(cutoff_spec), encoding="utf-8")
            unknown_unit = run_cli("plan", "--inventory", ready_inventory, "--pipeline", cutoff_path)
        self.assertEqual(inventory_result.returncode, 0, inventory_result.stderr)
        self.assertEqual(inventory["analysis_readiness"], "requires-decision")
        self.assertEqual(blocked_plan.returncode, 0, blocked_plan.stderr)
        blocked_report = json.loads(blocked_plan.stdout)
        self.assertEqual(blocked_report["execution_readiness"], "blocked")
        self.assertIn("INVENTORY_ANALYSIS_NOT_READY", {item["finding_id"] for item in blocked_report["findings"]})
        self.assertEqual(unknown_unit.returncode, 2)
        self.assertEqual(json.loads(unknown_unit.stderr)["finding_id"], "LENGTH_UNIT_UNRESOLVED")

    def test_duplicate_extxyz_particle_identifiers_are_refused(self) -> None:
        trajectory_text = """2
Properties=species:S:1:pos:R:3:id:I:1 pbc=\"F F F\"
C 0 0 0 7
H 1 0 0 7
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate-ids.extxyz"
            path.write_text(trajectory_text, encoding="utf-8")
            result = run_cli("inventory", path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "EXTXYZ_PARTICLE_IDENTIFIER_INVALID")

    def test_truncated_xyz_fails_closed(self) -> None:
        result = run_cli("inventory", FIXTURES / "truncated.xyz")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(result.stderr)["finding_id"], "XYZ_FRAME_TRUNCATED")

    def test_metadata_pipeline_is_a_plan_not_a_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory = make_inventory(Path(directory))
            result = run_cli(
                "plan",
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
                "--require-execution-ready",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["execution_readiness"], "ready")
        self.assertEqual(report["execution_state"], "planned-not-executed")
        self.assertFalse(report["ovito_executed"])
        self.assertNotIn("frames", report)

    def test_plan_only_and_pro_entitlement_boundaries_block_execution_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory = make_inventory(Path(directory))
            planned = run_cli(
                "plan",
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "pro-render-pipeline.json",
            )
            strict = run_cli(
                "plan",
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "pro-render-pipeline.json",
                "--require-execution-ready",
            )
        self.assertEqual(planned.returncode, 0, planned.stderr)
        report = json.loads(planned.stdout)
        self.assertEqual(report["execution_readiness"], "blocked")
        self.assertEqual(
            {item["finding_id"] for item in report["findings"]},
            {"OPERATION_PLAN_ONLY", "PRO_ENTITLEMENT_NOT_VERIFIED"},
        )
        self.assertEqual(strict.returncode, 2)

    def test_pipeline_source_hash_and_unknown_operations_are_refused(self) -> None:
        spec = json.loads((FIXTURES / "metadata-pipeline.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            inventory = make_inventory(directory_path)
            bad_hash = directory_path / "bad-hash.json"
            spec["source"]["sha256"] = "0" * 64
            bad_hash.write_text(json.dumps(spec), encoding="utf-8")
            result = run_cli("plan", "--inventory", inventory, "--pipeline", bad_hash)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stderr)["finding_id"], "PIPELINE_SOURCE_MISMATCH")
            spec = json.loads((FIXTURES / "metadata-pipeline.json").read_text(encoding="utf-8"))
            spec["operations"][0]["kind"] = "invented-analysis"
            unknown = directory_path / "unknown.json"
            unknown.write_text(json.dumps(spec), encoding="utf-8")
            result = run_cli("plan", "--inventory", inventory, "--pipeline", unknown)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "OPERATION_UNSUPPORTED")

    def test_duplicate_json_keys_and_symlink_source_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            duplicate = directory_path / "duplicate.json"
            duplicate.write_text('{"contract_name":"x","contract_name":"y"}', encoding="utf-8")
            result = run_cli("plan", "--inventory", duplicate, "--pipeline", duplicate)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stderr)["finding_id"], "JSON_INVALID")
            linked = directory_path / "linked.xyz"
            linked.symlink_to(FIXTURES / "two-frame.extxyz")
            result = run_cli("inventory", linked)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "TRAJECTORY_NOT_REGULAR")

    def test_probe_is_metadata_only_even_if_distribution_is_present(self) -> None:
        result = run_cli("probe")
        self.assertIn(result.returncode, {0, 3})
        report = json.loads(result.stdout)
        self.assertFalse(report["module_imported"])
        self.assertFalse(report["pipeline_executed"])
        self.assertFalse(report["license_entitlement_verified"])

    def test_execution_requires_explicit_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory = make_inventory(Path(directory))
            result = run_cli(
                "execute",
                "--source",
                FIXTURES / "two-frame.extxyz",
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
            )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "EXECUTION_NOT_AUTHORIZED")

    def test_authorized_execution_records_real_boundary_with_synthetic_api_double(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            inventory = make_inventory(directory_path)
            plan = run_cli(
                "plan",
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
            )
            self.assertEqual(plan.returncode, 0, plan.stderr)
            scope = json.loads(plan.stdout)["authorization_scope_sha256"]
            output = directory_path / "execution.json"
            environment = fake_ovito(directory_path / "fake-provider")
            result = run_cli(
                "execute",
                "--source",
                FIXTURES / "two-frame.extxyz",
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
                "--authorize-execution",
                "--authorization-scope",
                scope,
                "--out",
                output,
                environment=environment,
            )
            report = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {}
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertTrue(report["ovito_executed"])
        self.assertEqual(report["execution_state"], "actual-external-execution")
        self.assertEqual(report["provider"]["version"], "3.15.5")
        self.assertEqual([frame["particle_count"] for frame in report["frames"]], [2, 2])
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["future_gate_ceiling"], "technical_run_gates_only")
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["license_entitlement_verified"])

    def test_authorized_execution_rejects_wrong_imported_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            inventory = make_inventory(directory_path)
            plan = run_cli(
                "plan",
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
            )
            self.assertEqual(plan.returncode, 0, plan.stderr)
            scope = json.loads(plan.stdout)["authorization_scope_sha256"]
            output = directory_path / "execution.json"
            environment = fake_ovito(directory_path / "fake-provider", version="3.15.4")
            result = run_cli(
                "execute",
                "--source",
                FIXTURES / "two-frame.extxyz",
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
                "--authorize-execution",
                "--authorization-scope",
                scope,
                "--out",
                output,
                environment=environment,
            )
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "OVITO_VERSION_MISMATCH")
        self.assertFalse(output.exists())

    def test_output_overwrite_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            first = run_cli("inventory", FIXTURES / "two-frame.extxyz", "--out", output)
            second = run_cli("inventory", FIXTURES / "two-frame.extxyz", "--out", output)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 2)
        self.assertEqual(json.loads(second.stderr)["finding_id"], "OUTPUT_EXISTS")

    def test_schemas_and_json_fixtures_are_valid_json(self) -> None:
        paths = sorted((ROOT / "schemas").glob("*.json")) + sorted(FIXTURES.glob("*.json"))
        for path in paths:
            with self.subTest(path=path.name):
                self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)
        manifest = json.loads((ROOT / "references" / "fixture-manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["fixtures"]:
            path = ROOT / entry["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"])


if __name__ == "__main__":
    unittest.main()
