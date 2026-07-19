from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import validate_candidate_decision_table as validator  # noqa: E402


def valid_table(
    skill_id: str = "example-rigorous-workflow",
    lifecycle: str = "development",
) -> dict:
    cases = []
    for priority in range(1, 11):
        is_default = priority == 10
        cases.append(
            {
                "case_id": "default-fail-closed" if is_default else f"case-{priority:02d}",
                "priority": priority,
                "severity": "P0" if priority < 5 else "P1",
                "condition": (
                    "No earlier condition can be established from exact evidence."
                    if is_default
                    else f"Exact evidence condition {priority} is present."
                ),
                "required_evidence": [] if is_default else [f"evidence-{priority:02d}"],
                "finding_codes": [f"EXAMPLE.GATE_{priority:02d}"],
                "action_state": "local_gate_blocked" if is_default else "needs_evidence",
                "expected_exit_codes": [2] if is_default else [0, 2],
                "current_claim": "no_positive_claim",
                "execution_authorized": False,
                "promotion_authorized": False,
                "minimum_next_action": f"Perform bounded corrective action {priority}.",
            }
        )
    return {
        "contract_name": "candidate-decision-table",
        "schema_version": "1.0",
        "skill_id": skill_id,
        "lifecycle": lifecycle,
        "selection_policy": "first-match-by-ascending-priority",
        "default_case_id": "default-fail-closed",
        "current_claim": "no_positive_claim",
        "execution_authorized": False,
        "promotion_authorized": False,
        "cases": cases,
    }


class CandidateDecisionTableTests(unittest.TestCase):
    def test_valid_table_passes_schema_and_semantics(self) -> None:
        self.assertEqual(validator.semantic_errors(valid_table()), [])
        prepared = validator._prepared_contract_validator()
        self.assertEqual(
            validator.semantic_errors(valid_table(), prepared=prepared),
            [],
        )

    def test_schema_rejects_authority_and_unknown_fields(self) -> None:
        for label, mutate in {
            "execution": lambda value: value.update(execution_authorized=True),
            "promotion": lambda value: value.update(promotion_authorized=True),
            "claim": lambda value: value.update(current_claim="input_gates_only"),
            "extra": lambda value: value.update(notes="free-form escape hatch"),
        }.items():
            with self.subTest(label=label):
                value = valid_table()
                mutate(value)
                self.assertTrue(validator.semantic_errors(value))

    def test_needs_authorization_is_a_safe_nonexecuting_candidate_state(self) -> None:
        value = valid_table()
        value["cases"][0]["action_state"] = "needs_authorization"
        self.assertEqual(validator.semantic_errors(value), [])

    def test_priority_and_default_semantics_fail_closed(self) -> None:
        mutations = {
            "duplicate-priority": lambda value: value["cases"][1].update(priority=1),
            "out-of-order": lambda value: value["cases"].reverse(),
            "duplicate-case": lambda value: value["cases"][1].update(case_id="case-01"),
            "duplicate-action": lambda value: value["cases"][1].update(
                minimum_next_action=value["cases"][0]["minimum_next_action"]
            ),
            "unknown-default": lambda value: value.update(default_case_id="missing-case"),
            "nonfinal-default": lambda value: value.update(default_case_id="case-01"),
            "default-needs-evidence": lambda value: value["cases"][-1].update(
                required_evidence=["unavailable-evidence"]
            ),
            "default-does-not-block": lambda value: value["cases"][-1].update(
                action_state="local_gate_passed_limited"
            ),
            "blocked-without-code": lambda value: value["cases"][-1].update(
                finding_codes=[]
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                value = valid_table()
                mutate(value)
                self.assertTrue(validator.semantic_errors(value))

    def test_file_reader_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            path = Path(raw_directory) / "table.json"
            path.write_bytes(
                b'{"contract_name":"candidate-decision-table",'
                b'"contract_name":"candidate-decision-table"}'
            )
            errors = validator.validate_file(path)
        self.assertTrue(any("duplicate object key" in item for item in errors))

    def test_expected_skill_directory_identity_is_bound(self) -> None:
        errors = validator.semantic_errors(
            valid_table("alpha-workflow"), expected_skill_id="beta-workflow"
        )
        self.assertTrue(any("candidate directory" in item for item in errors))

    def test_repository_scan_binds_table_lifecycle_to_development_registry(self) -> None:
        self.assertEqual(
            validator.semantic_errors(
                valid_table(), expected_lifecycle="development"
            ),
            [],
        )
        errors = validator.semantic_errors(
            valid_table(lifecycle="planned"), expected_lifecycle="development"
        )
        self.assertTrue(any("registry lifecycle" in item for item in errors))

    def test_all_development_requires_one_canonical_table_per_skill(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            (root / "registry").mkdir()
            (root / "skills" / "alpha-workflow" / "references").mkdir(parents=True)
            (root / "registry" / "skill-registry.yaml").write_text(
                "schema_version: '1.0'\nskills:\n"
                "  alpha-workflow:\n    lifecycle: development\n"
                "  active-workflow:\n    lifecycle: active\n",
                encoding="utf-8",
            )
            table_path = (
                root
                / "skills"
                / "alpha-workflow"
                / "references"
                / "weak-model-decision-table.json"
            )
            table_path.write_text(
                json.dumps(valid_table("alpha-workflow")), encoding="utf-8"
            )
            self.assertEqual(validator.validate_all_development(root), [])
            table_path.unlink()
            failures = validator.validate_all_development(root)
        self.assertEqual(len(failures), 1)
        self.assertIn("missing skills/alpha-workflow", failures[0])

    def test_repository_all_development_tables_validate(self) -> None:
        self.assertEqual(validator.validate_all_development(ROOT), [])

    def test_cli_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            path = Path(raw_directory) / "table.json"
            path.write_text(json.dumps(valid_table()), encoding="utf-8")
            command = [
                sys.executable,
                "-B",
                str(TOOLS / "validate_candidate_decision_table.py"),
                "--file",
                str(path),
                "--skill-id",
                "example-rigorous-workflow",
            ]
            first = subprocess.run(command, capture_output=True, text=True, check=False)
            second = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stderr, second.stderr)


if __name__ == "__main__":
    unittest.main()
