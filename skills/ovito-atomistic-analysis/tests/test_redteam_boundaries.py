from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


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


def write_text(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


def make_inventory(directory: Path, source: Path) -> Path:
    path = directory / "inventory.json"
    result = run_cli("inventory", source, "--out", path)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return path


def make_spec(directory: Path, source: Path, output_kind: str = "json-data") -> Path:
    value = json.loads((FIXTURES / "metadata-pipeline.json").read_text(encoding="utf-8"))
    raw = source.read_bytes()
    value["source"]["sha256"] = hashlib.sha256(raw).hexdigest()
    value["source"]["format"] = "extxyz"
    value["outputs"][0]["kind"] = output_kind
    path = directory / f"pipeline-{output_kind}.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def plan_scope(inventory: Path, pipeline: Path) -> str | None:
    result = run_cli("plan", "--inventory", inventory, "--pipeline", pipeline)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout).get("authorization_scope_sha256")


def execute_args(source: Path, inventory: Path, pipeline: Path, output: Path) -> list[object]:
    arguments: list[object] = [
        "execute",
        "--source",
        source,
        "--inventory",
        inventory,
        "--pipeline",
        pipeline,
        "--authorize-execution",
        "--out",
        output,
    ]
    scope = plan_scope(inventory, pipeline)
    if scope is not None:
        arguments.extend(["--authorization-scope", scope])
    return arguments


def fake_provider(
    directory: Path,
    source: Path,
    *,
    distribution: bool = True,
    mutate_source: bool = False,
    marker: Path | None = None,
    fail_compute: bool = False,
) -> dict[str, str]:
    package = directory / "ovito"
    package.mkdir(parents=True)
    mutation = ""
    if mutate_source:
        mutation = (
            "from pathlib import Path\n"
            "import os\n"
            "Path(os.environ['OVITO_MUTATE_SOURCE']).write_text('1\\nmutated\\nSi 9 9 9\\n', encoding='utf-8')\n"
        )
    (package / "__init__.py").write_text(mutation + 'version_string = "3.15.5"\n', encoding="utf-8")
    (package / "io.py").write_text(
        """
import hashlib
import os
from pathlib import Path

class Property:
    def __init__(self, name):
        self.name = name

class Particles:
    def __init__(self, count):
        self.count = count
    def values(self):
        return [Property("Particle Type"), Property("Position")]

class Cell:
    pbc = (True, True, True)
    matrix = ((5.0, 0.0, 0.0), (0.0, 5.0, 0.0), (0.0, 0.0, 5.0))
    def __getitem__(self, key):
        row, column = key
        return self.matrix[row][column]

class Data:
    def __init__(self, count):
        self.particles = Particles(count)
        self.cell = Cell()

class Pipeline:
    def __init__(self, count):
        self.count = count
    def compute(self, frame):
        marker = os.environ.get("OVITO_MARKER")
        if marker:
            Path(marker).write_text(str(frame), encoding="utf-8")
        if os.environ.get("OVITO_FAIL_COMPUTE") == "1":
            raise RuntimeError("synthetic compute failure")
        return Data(self.count)

def import_file(path, *, sort_particles=False):
    if sort_particles is not False:
        raise ValueError("candidate must preserve source storage order")
    observed = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    expected = os.environ["OVITO_EXPECTED_SOURCE_SHA256"]
    return Pipeline(2 if observed == expected else 99)
""".lstrip(),
        encoding="utf-8",
    )
    if distribution:
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
    environment["OVITO_EXPECTED_SOURCE_SHA256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    if mutate_source:
        environment["OVITO_MUTATE_SOURCE"] = str(source)
    if marker is not None:
        environment["OVITO_MARKER"] = str(marker)
    if fail_compute:
        environment["OVITO_FAIL_COMPUTE"] = "1"
    return environment


class OvitoBoundaryRedTeamTests(unittest.TestCase):
    def test_plain_xyz_refuses_untyped_extra_columns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "untyped-extra.xyz"
            path.write_text("1\nplain XYZ\nSi 0 0 0 99\n", encoding="utf-8")
            result = run_cli("inventory", path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "XYZ_ATOM_LINE_INVALID")

    def test_single_fd_snapshot_detects_link_count_and_final_path_mutations(self) -> None:
        spec = importlib.util.spec_from_file_location("ovito_analysis_redteam", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            for mutation_kind in ("hardlink", "replace-path"):
                with self.subTest(mutation_kind=mutation_kind):
                    source = directory_path / f"source-{mutation_kind}.extxyz"
                    source.write_bytes((FIXTURES / "two-frame.extxyz").read_bytes())
                    alias = directory_path / f"alias-{mutation_kind}.extxyz"
                    moved = directory_path / f"moved-{mutation_kind}.extxyz"
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
                            module._regular_bytes(str(source), module.MAX_TRAJECTORY_BYTES, "TRAJECTORY")
                    self.assertEqual(caught.exception.finding_id, "TRAJECTORY_CHANGED_DURING_READ")

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
        self.assertEqual(table["skill_id"], "ovito-atomistic-analysis")
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

    def test_every_nonexecuting_candidate_report_is_lifecycle_capped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            inventory_path = make_inventory(directory_path, FIXTURES / "two-frame.extxyz")
            commands = {
                "inventory": ("inventory", FIXTURES / "two-frame.extxyz"),
                "plan": (
                    "plan",
                    "--inventory",
                    inventory_path,
                    "--pipeline",
                    FIXTURES / "metadata-pipeline.json",
                ),
                "probe": ("probe",),
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

    def test_blocked_envelope_is_lifecycle_capped(self) -> None:
        result = run_cli("inventory", FIXTURES / "truncated.xyz")
        self.assertEqual(result.returncode, 2)
        envelope = json.loads(result.stderr)
        self.assertEqual(envelope["claim_ceiling"], "no_positive_claim")
        self.assertFalse(envelope["promotion_authorized"])
        self.assertFalse(envelope["execution_authorized"])
        self.assertEqual(envelope["contract_name"], "ovito-candidate-error")
        self.assertEqual(envelope["schema_version"], "0.1")
        self.assertEqual(
            envelope["provenance"],
            {"tool": "ovito_analysis.py", "tool_version": "0.1.0-candidate"},
        )

    def test_atomic_output_refuses_trajectory_path_and_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            source = directory_path / "source.extxyz"
            source.write_bytes((FIXTURES / "two-frame.extxyz").read_bytes())
            expected_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
            hardlink = directory_path / "hardlink.extxyz"
            hardlink.hardlink_to(source)
            symlink = directory_path / "symlink.extxyz"
            symlink.symlink_to(source)
            for label, output in {"same": source, "hardlink": hardlink, "symlink": symlink}.items():
                with self.subTest(label=label):
                    result = run_cli("inventory", source, "--out", output)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(json.loads(result.stderr)["finding_id"], "OUTPUT_EXISTS")
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), expected_sha256)
            fresh = directory_path / "fresh.json"
            result = run_cli("inventory", source, "--out", fresh)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(fresh.read_text(encoding="utf-8"))["status"], "pass")
            self.assertEqual(list(directory_path.glob("*.candidate-*.tmp")), [])

    def test_extxyz_validates_all_typed_properties_and_unique_names(self) -> None:
        cases = {
            "bad-real.extxyz": (
                '1\nProperties=species:S:1:pos:R:3:force:R:3\nSi 0 0 0 bad 0 0\n',
                "EXTXYZ_PROPERTY_VALUE_INVALID",
            ),
            "duplicate-property.extxyz": (
                '1\nProperties=species:S:1:pos:R:3:force:R:3:force:R:3\nSi 0 0 0 1 2 3 4 5 6\n',
                "EXTXYZ_PROPERTY_DUPLICATE",
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            for name, (content, finding_id) in cases.items():
                with self.subTest(name=name):
                    source = write_text(directory_path, name, content)
                    result = run_cli("inventory", source)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stderr)["finding_id"], finding_id)

    def test_property_schema_drift_blocks_cross_frame_analysis(self) -> None:
        content = (
            '1\nProperties=species:S:1:pos:R:3:force:R:3\nSi 0 0 0 1 2 3\n'
            '1\nProperties=species:S:1:pos:R:3:energy:R:1\nSi 0.1 0 0 -1.2\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            source = write_text(Path(directory), "schema-drift.extxyz", content)
            result = run_cli("inventory", source)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["property_schema_constant"])
        self.assertIn("TRAJECTORY_PROPERTY_SCHEMA_CHANGED", {item["finding_id"] for item in report["findings"]})

    def test_cell_drift_is_explicit_while_mixed_frame_state_blocks(self) -> None:
        variable = (
            '1\nLattice="5 0 0 0 5 0 0 0 5" Properties=species:S:1:pos:R:3 pbc="T T T"\nSi 0 0 0\n'
            '1\nLattice="5.1 0 0 0 5 0 0 0 5" Properties=species:S:1:pos:R:3 pbc="T T T"\nSi 0.1 0 0\n'
        )
        mixed = (
            '2\nLattice="5 0 0 0 5 0 0 0 5" Properties=species:S:1:pos:R:3 pbc="T T T"\nSi 0 0 0\nSi 1 1 1\n'
            '1\nProperties=species:S:1:pos:R:3 pbc="F F F"\nSi 0 0 0\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            variable_result = run_cli("inventory", write_text(directory_path, "variable.extxyz", variable))
            mixed_result = run_cli("inventory", write_text(directory_path, "mixed.extxyz", mixed))
        self.assertEqual(variable_result.returncode, 0, variable_result.stderr)
        variable_report = json.loads(variable_result.stdout)
        self.assertEqual(variable_report["cell_mode"], "variable")
        self.assertIn("TRAJECTORY_CELL_CHANGED", {item["finding_id"] for item in variable_report["findings"]})
        self.assertEqual(mixed_result.returncode, 0, mixed_result.stderr)
        mixed_findings = {item["finding_id"] for item in json.loads(mixed_result.stdout)["findings"]}
        self.assertTrue(
            {"TRAJECTORY_ATOM_COUNT_CHANGED", "TRAJECTORY_PBC_CHANGED", "TRAJECTORY_CELL_PRESENCE_CHANGED"}
            .issubset(mixed_findings)
        )

    def test_forged_inventory_frame_index_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            inventory = make_inventory(directory_path, FIXTURES / "two-frame.extxyz")
            value = json.loads(inventory.read_text(encoding="utf-8"))
            value["frames"][0]["frame_index"] = 7
            inventory.write_text(json.dumps(value), encoding="utf-8")
            result = run_cli("plan", "--inventory", inventory, "--pipeline", FIXTURES / "metadata-pipeline.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "INVENTORY_FRAME_INDEX_INVALID")

    def test_execution_cross_checks_forged_inventory_against_verified_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for mutation_kind in ("source-bytes", "particle-count", "species-order"):
                with self.subTest(mutation_kind=mutation_kind):
                    directory_path = root / mutation_kind
                    directory_path.mkdir()
                    source = FIXTURES / "two-frame.extxyz"
                    inventory = make_inventory(directory_path, source)
                    value = json.loads(inventory.read_text(encoding="utf-8"))
                    if mutation_kind == "source-bytes":
                        value["source"]["bytes"] += 1
                    elif mutation_kind == "particle-count":
                        value["atom_count"] = 3
                        for frame in value["frames"]:
                            frame["atom_count"] = 3
                            frame["species_order"].append("Si")
                    else:
                        for frame in value["frames"]:
                            frame["species_order"][0] = "C"
                    inventory.write_text(json.dumps(value), encoding="utf-8")
                    output = directory_path / "result.json"
                    provider_env = fake_provider(directory_path / "provider", source)
                    result = run_cli(
                        *execute_args(source, inventory, FIXTURES / "metadata-pipeline.json", output),
                        environment=provider_env,
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stderr)["finding_id"], "OVITO_INVENTORY_MISMATCH")
                    self.assertFalse(output.exists())

    def test_output_kind_must_match_operation_and_claim_role(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            source = FIXTURES / "two-frame.extxyz"
            inventory = make_inventory(directory_path, source)
            image_spec = make_spec(directory_path, source, output_kind="image")
            result = run_cli("plan", "--inventory", inventory, "--pipeline", image_spec)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "OUTPUT_OPERATION_MISMATCH")

    def test_plan_emits_source_and_pipeline_bound_authorization_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            inventory = make_inventory(directory_path, FIXTURES / "two-frame.extxyz")
            result = run_cli(
                "plan",
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertRegex(report["authorization_scope_sha256"], r"^[a-f0-9]{64}$")
        self.assertEqual(report["authorization_scope"]["source_sha256"], report["inventory_source_sha256"])
        self.assertEqual(
            report["authorization_scope"]["inventory_record_sha256"],
            report["inventory_record_source"]["sha256"],
        )
        self.assertEqual(report["authorization_scope"]["pipeline_spec_sha256"], report["spec_source"]["sha256"])

    def test_execution_requires_exact_authorization_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            source = FIXTURES / "two-frame.extxyz"
            inventory = make_inventory(directory_path, source)
            output = directory_path / "result.json"
            provider_env = fake_provider(directory_path / "provider", source)
            missing = run_cli(
                "execute",
                "--source",
                source,
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
                "--authorize-execution",
                "--out",
                output,
                environment=provider_env,
            )
            wrong = run_cli(
                "execute",
                "--source",
                source,
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
                "--authorize-execution",
                "--authorization-scope",
                "0" * 64,
                "--out",
                output,
                environment=provider_env,
            )
            original_scope = plan_scope(inventory, FIXTURES / "metadata-pipeline.json")
            inventory_value = json.loads(inventory.read_text(encoding="utf-8"))
            inventory.write_text(json.dumps(inventory_value, indent=2), encoding="utf-8")
            stale_inventory_scope = run_cli(
                "execute",
                "--source",
                source,
                "--inventory",
                inventory,
                "--pipeline",
                FIXTURES / "metadata-pipeline.json",
                "--authorize-execution",
                "--authorization-scope",
                original_scope,
                "--out",
                output,
                environment=provider_env,
            )
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(json.loads(missing.stderr)["finding_id"], "AUTHORIZATION_SCOPE_MISSING")
        self.assertEqual(wrong.returncode, 2)
        self.assertEqual(json.loads(wrong.stderr)["finding_id"], "AUTHORIZATION_SCOPE_MISMATCH")
        self.assertEqual(stale_inventory_scope.returncode, 2)
        self.assertEqual(json.loads(stale_inventory_scope.stderr)["finding_id"], "AUTHORIZATION_SCOPE_MISMATCH")

    def test_execution_imports_verified_snapshot_not_mutated_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            source = directory_path / "mutable.extxyz"
            source.write_bytes((FIXTURES / "two-frame.extxyz").read_bytes())
            inventory = make_inventory(directory_path, source)
            pipeline = make_spec(directory_path, source)
            output = directory_path / "result.json"
            provider_env = fake_provider(
                directory_path / "provider",
                source,
                mutate_source=True,
            )
            result = run_cli(*execute_args(source, inventory, pipeline, output), environment=provider_env)
            report = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {}
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([item["particle_count"] for item in report["frames"]], [2, 2])
        self.assertEqual(report["import_source"], "verified-private-snapshot")

    def test_module_without_matching_distribution_metadata_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            source = FIXTURES / "two-frame.extxyz"
            inventory = make_inventory(directory_path, source)
            pipeline = FIXTURES / "metadata-pipeline.json"
            output = directory_path / "result.json"
            provider_env = fake_provider(directory_path / "provider", source, distribution=False)
            result = run_cli(*execute_args(source, inventory, pipeline, output), environment=provider_env)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stderr)["finding_id"], "OVITO_DISTRIBUTION_MISMATCH")
        self.assertFalse(output.exists())

    def test_existing_output_blocks_before_backend_compute_and_failure_leaves_no_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            source = FIXTURES / "two-frame.extxyz"
            inventory = make_inventory(directory_path, source)
            pipeline = FIXTURES / "metadata-pipeline.json"
            existing = directory_path / "existing.json"
            existing.write_text("preserve", encoding="utf-8")
            marker = directory_path / "compute.marker"
            provider_env = fake_provider(directory_path / "provider-one", source, marker=marker)
            repeated = run_cli(*execute_args(source, inventory, pipeline, existing), environment=provider_env)
            failed_output = directory_path / "failed.json"
            failure_env = fake_provider(
                directory_path / "provider-two",
                source,
                fail_compute=True,
            )
            failed = run_cli(*execute_args(source, inventory, pipeline, failed_output), environment=failure_env)
            self.assertEqual(existing.read_text(encoding="utf-8"), "preserve")
            self.assertFalse(marker.exists())
            self.assertFalse(failed_output.exists())
        self.assertEqual(repeated.returncode, 2)
        self.assertEqual(json.loads(repeated.stderr)["finding_id"], "OUTPUT_EXISTS")
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(json.loads(failed.stderr)["finding_id"], "OVITO_EXECUTION_FAILED")

    def test_source_label_is_content_derived_privacy_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            labels = []
            for name in ("patient secret.extxyz", "patient_secret.extxyz"):
                source = Path(directory) / name
                source.write_bytes((FIXTURES / "two-frame.extxyz").read_bytes())
                result = run_cli("inventory", source)
                self.assertEqual(result.returncode, 0, result.stderr)
                labels.append(json.loads(result.stdout)["source"]["label"])
        for label in labels:
            self.assertRegex(label, r"^source-[a-f0-9]{12}\.extxyz$")
            self.assertNotIn("patient", label)


if __name__ == "__main__":
    unittest.main()
