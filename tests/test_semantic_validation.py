from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_semantics  # noqa: E402


HASH = "0" * 64


def codes(kind: str, value: dict) -> set[str]:
    return {finding.code for finding in validate_semantics.semantic_findings(kind, value)}


def run_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "record_id": "run-example-001",
        "code": "qe",
        "code_version": "7.5",
        "task_type": "scf",
        "case_id": "case-anonymous",
        "scientific_protocol_id": "protocol-001",
        "status": "completed",
        "scientific_acceptance": "not_assessed",
        "configuration": {},
        "metrics": {},
        "evidence": [{"role": "main-output", "label": "output.log", "sha256": HASH, "status": "present"}],
        "limitations": ["physical validity remains unassessed"],
        "provenance": {"collector": "test", "collector_version": "1", "generated_utc": "2026-07-18T00:00:00Z"},
    }


def plan_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "plan_id": "plan-example-001",
        "observable": "bands",
        "code": "qe",
        "status": "planned",
        "source_root_label": "source-run",
        "output_root_label": "derived-output",
        "source_files": [{"role": "bands-output", "path": "bands.dat", "required": True, "present": True}],
        "parameters": {},
        "backend": {"id": "qe-bands", "kind": "builtin-python", "maturity": "real-artifact-validated", "available": True},
        "steps": [{
            "step_id": "normalize",
            "operation": "normalize",
            "adapter": "qe-bands",
            "action": "python",
            "command": ["python", "normalize.py"],
            "inputs": ["bands.dat"],
            "outputs": ["bands.csv"],
            "timeout_s": 60,
            "overwrite": False,
        }],
        "blockers": [],
        "provenance": {"planner": "test", "planner_version": "1", "generated_utc": "2026-07-18T00:00:00Z"},
    }


def execution_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "execution_id": "execution-example-001",
        "plan_id": "plan-example-001",
        "step_id": "normalize",
        "backend": "qe-bands",
        "command": ["python", "normalize.py"],
        "working_directory_label": "work-anonymous",
        "dry_run": False,
        "status": "succeeded",
        "started_utc": "2026-07-18T00:00:00Z",
        "finished_utc": "2026-07-18T00:00:01Z",
        "duration_s": 1.0,
        "return_code": 0,
        "inputs": [{"role": "input", "path": "input.dat", "sha256": HASH, "bytes": 1}],
        "outputs": [{"role": "output", "path": "output.dat", "sha256": HASH, "bytes": 1}],
        "stdout": {"path": "execution.stdout", "sha256": HASH, "bytes": 0},
        "stderr": {"path": "execution.stderr", "sha256": HASH, "bytes": 0},
        "limitations": [],
    }


def dataset_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "dataset_id": "dataset-example-001",
        "observable": "bands",
        "code": "qe",
        "maturity": "real-artifact-validated",
        "representation": "table",
        "source_files": [{"role": "bands-output", "label": "bands.dat", "bytes": 1, "sha256": HASH, "hash_status": "present"}],
        "dimensions": {"rows": 1},
        "columns": [{"name": "energy", "dtype": "float", "unit": "eV", "role": "energy"}],
        "data_files": [{"role": "table", "path": "bands.csv", "format": "csv", "sha256": HASH, "bytes": 1}],
        "transformations": [],
        "validation": {"status": "pass", "checks": [{"id": "finite", "status": "pass", "message": "finite"}]},
        "limitations": [],
        "provenance": {"producer": "test", "producer_version": "1", "generated_utc": "2026-07-18T00:00:00Z", "tool_execution_ids": []},
    }


def artifact_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "artifact_id": "artifact-example-001",
        "source_run_ids": ["run-example-001"],
        "code": "qe",
        "artifact_type": "bands-table",
        "status": "complete",
        "data_files": [{"role": "table", "path": "bands.csv", "sha256": HASH, "bytes": 1}],
        "figure_files": [],
        "validation": {"status": "pass", "checks": ["finite-energy"]},
        "claim_boundary": ["technical postprocessing only"],
        "provenance": {"tool": "test", "tool_version": "1", "generated_utc": "2026-07-18T00:00:00Z", "command": ["test"]},
    }


class SemanticValidationTests(unittest.TestCase):
    def test_positive_manifests_pass(self) -> None:
        for kind, value in (
            ("run", run_manifest()),
            ("plan", plan_manifest()),
            ("execution", execution_manifest()),
            ("dataset", dataset_manifest()),
            ("artifact", artifact_manifest()),
        ):
            self.assertEqual(validate_semantics.semantic_findings(kind, value), [], kind)

    def test_run_schema_blocks_self_declared_acceptance_before_semantics(self) -> None:
        value = run_manifest()
        value["status"] = "accepted"
        self.assertEqual(codes("run", value), {"schema-invalid"})

        value = run_manifest()
        value["scientific_acceptance"] = "accepted"
        self.assertEqual(codes("run", value), {"schema-invalid"})

    def test_run_evidence_hash_status_is_consistent(self) -> None:
        value = run_manifest()
        value["evidence"][0]["sha256"] = None
        self.assertEqual(codes("run", value), {"schema-invalid"})
        value["evidence"][0]["status"] = "missing"
        value["evidence"][0]["sha256"] = HASH
        self.assertEqual(codes("run", value), {"schema-invalid"})

    def test_plan_requires_executable_evidence(self) -> None:
        value = plan_manifest()
        value["backend"]["maturity"] = "design-only"
        value["source_files"][0]["present"] = False
        value["blockers"] = ["known blocker"]
        found = codes("plan", value)
        self.assertTrue({"plan-design-only-backend", "plan-required-source-missing", "plan-ready-with-blockers"}.issubset(found))

        blocked = plan_manifest()
        blocked["status"] = "blocked"
        blocked["backend"] = None
        blocked["steps"] = []
        self.assertIn("plan-blocked-without-reason", codes("plan", blocked))

    def test_execution_state_is_not_inferred_from_exit_alone(self) -> None:
        value = execution_manifest()
        value["return_code"] = 1
        self.assertIn("execution-success-return-code", codes("execution", value))

        dry = execution_manifest()
        dry["dry_run"] = True
        self.assertIn("execution-dry-run-status-mismatch", codes("execution", dry))
        self.assertIn("execution-dry-run-runtime-present", codes("execution", dry))

    def test_dataset_and_artifact_positive_claims_require_matching_checks(self) -> None:
        value = dataset_manifest()
        value["maturity"] = "design-only"
        value["validation"]["checks"][0]["status"] = "not-run"
        found = codes("dataset", value)
        self.assertIn("dataset-design-only-positive", found)
        self.assertIn("dataset-pass-check-mismatch", found)

        artifact = artifact_manifest()
        artifact["validation"]["status"] = "block"
        artifact["data_files"] = []
        artifact["claim_boundary"] = []
        found = codes("artifact", artifact)
        self.assertTrue({
            "artifact-complete-validation-blocked",
            "artifact-complete-without-files",
            "artifact-complete-without-boundary",
            "artifact-validation-status-mismatch",
        }.issubset(found))

    def test_privacy_scan_blocks_paths_fields_and_secret_like_text(self) -> None:
        for injected, expected in (
            ({"private_path": "/Users/example/private/run"}, "privacy-absolute-path"),
            ({"command_hint": "--out=/Users/example/private/run"}, "privacy-absolute-path"),
            ({"host": "cluster.internal"}, "privacy-forbidden-field"),
            ({"note": "../outside"}, "privacy-path-traversal"),
            ({"note": "sk-abcdefghijklmnopqrstuvwxyz"}, "privacy-secret-text"),
        ):
            value = run_manifest()
            value["configuration"] = injected
            self.assertIn(expected, codes("run", value))

    def test_schema_errors_stop_semantic_interpretation(self) -> None:
        value = copy.deepcopy(run_manifest())
        value["unknown"] = "/private/path"
        self.assertEqual(codes("run", value), {"schema-invalid"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
