from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import migrate_contract
import validate_contract


CHECK_IDS = [
    "identity-and-routing",
    "primary-source-provenance",
    "capability-boundary",
    "deterministic-gates",
    "lineage-and-hashes",
    "scientific-gate-separation",
    "shared-interfaces",
    "side-effect-boundary",
    "idempotency-recovery-cancel",
    "validation-evidence",
    "privacy-and-license",
    "portability-and-environment",
    "maintenance-and-forward-test",
]


def _source_record() -> dict[str, object]:
    evidence_hash = hashlib.sha256(b"synthetic migration evidence\n").hexdigest()
    checks = []
    for index, check_id in enumerate(CHECK_IDS):
        checks.append(
            {
                "check_id": check_id,
                "status": "pass",
                "evidence": [
                    {
                        "evidence_id": f"migration-evidence-{index:02d}",
                        "kind": "test-report",
                        "path": "skills/example-skill/validation/evidence.txt",
                        "sha256": evidence_hash,
                    }
                ],
                "reviewer": {
                    "reviewer_id": f"migration-reviewer-{index:02d}",
                    "role": "independent-technical-reviewer",
                    "independent_of_implementation": True,
                },
                "validated_utc": "2026-07-21T00:00:00Z",
                "not_applicable_reason": None,
                "limitations": [],
            }
        )
    return {
        "schema_version": "1.0",
        "contract_name": "activation-checklist",
        "checklist_id": "migration-source-checklist",
        "subject": {
            "skill_id": "example-skill",
            "software_ids": [],
            "candidate_commit": "a" * 40,
        },
        "profile_ids": ["example-profile"],
        "checks": checks,
        "summary": {
            "decision": "eligible",
            "blocker_check_ids": [],
            "limitations": ["Synthetic contract-migration fixture only"],
        },
        "provenance": {
            "producer": "contract-migration-test",
            "producer_version": "1.0",
            "generated_utc": "2026-07-21T00:00:00Z",
        },
    }


def _plan(*, operations: list[dict[str, str]] | None = None) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "contract_name": "contract-migration-plan",
        "plan_id": "activation-1.0-to-1.1",
        "source_contract": {"name": "activation-checklist", "version": "1.0"},
        "target_contract": {"name": "activation-checklist", "version": "1.1"},
        "source_path": "records/source.json",
        "output_path": "records/target.json",
        "migration_record_path": "records/migration.json",
        "target_record_id": "migration-target-checklist",
        "operations": operations or [],
        "provenance": {
            "producer": "contract-migration-test",
            "producer_version": "1.0",
            "generated_utc": "2026-07-21T00:00:00Z",
        },
    }


class ContractMigrationTests(unittest.TestCase):
    def _repository(
        self,
        root: Path,
        *,
        plan: dict[str, object] | None = None,
    ) -> Path:
        source = _source_record()
        source_path = root / "records" / "source.json"
        source_path.parent.mkdir(parents=True)
        source_path.write_text(
            json.dumps(source, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        plan_path = root / "plans" / "migration.json"
        plan_path.parent.mkdir(parents=True)
        plan_path.write_text(
            json.dumps(plan or _plan(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return plan_path

    def test_valid_activation_migration_writes_valid_target_and_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = self._repository(root)
            findings, record, target = migrate_contract.migrate(
                root,
                plan_path,
                contracts_dir=ROOT / "contracts",
                write=True,
            )
            self.assertEqual(findings, [])
            self.assertIsNotNone(target)
            self.assertEqual(target["schema_version"], "1.1")
            self.assertEqual(target["checklist_id"], "migration-target-checklist")
            self.assertEqual(target["summary"]["decision"], "eligible")
            self.assertEqual(record["evidence_boundary"]["scientific_values_synthesized"], False)
            target_path = root / "records" / "target.json"
            migration_path = root / "records" / "migration.json"
            self.assertTrue(target_path.is_file())
            self.assertTrue(migration_path.is_file())
            target_data = json.loads(target_path.read_text(encoding="utf-8"))
            migration_data = json.loads(migration_path.read_text(encoding="utf-8"))
            self.assertEqual(
                validate_contract.validation_errors(
                    "activation-checklist@1.1",
                    target_data,
                    ROOT / "contracts",
                ),
                [],
            )
            self.assertEqual(
                validate_contract.validation_errors(
                    "contract-migration-record@1.0",
                    migration_data,
                    ROOT / "contracts",
                ),
                [],
            )

    def test_dry_run_does_not_write_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = self._repository(root)
            findings, _record, target = migrate_contract.migrate(
                root,
                plan_path,
                contracts_dir=ROOT / "contracts",
                write=False,
            )
            self.assertEqual(findings, [])
            self.assertIsNotNone(target)
            self.assertFalse((root / "records" / "target.json").exists())
            self.assertFalse((root / "records" / "migration.json").exists())

    def test_protected_summary_removal_is_blocked_without_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = self._repository(
                root,
                plan=_plan(operations=[{"op": "remove", "from": "/summary"}]),
            )
            findings, _record, _target = migrate_contract.migrate(
                root,
                plan_path,
                contracts_dir=ROOT / "contracts",
                write=True,
            )
            codes = {finding.code for finding in findings}
            self.assertIn("MIGRATION_PROTECTED_FIELD_CHANGED", codes)
            self.assertFalse((root / "records" / "target.json").exists())
            self.assertFalse((root / "records" / "migration.json").exists())

    def test_required_unprotected_field_removal_fails_target_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = self._repository(
                root,
                plan=_plan(operations=[{"op": "remove", "from": "/profile_ids"}]),
            )
            findings, _record, _target = migrate_contract.migrate(
                root,
                plan_path,
                contracts_dir=ROOT / "contracts",
                write=True,
            )
            self.assertIn(
                "MIGRATION_SCHEMA_INVALID",
                {finding.code for finding in findings},
            )
            self.assertFalse((root / "records" / "target.json").exists())

    def test_existing_output_blocks_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan_path = self._repository(root)
            output = root / "records" / "target.json"
            output.write_text("do not overwrite\n", encoding="utf-8")
            findings, _record, _target = migrate_contract.migrate(
                root,
                plan_path,
                contracts_dir=ROOT / "contracts",
                write=True,
            )
            self.assertIn(
                "MIGRATION_OUTPUT_EXISTS",
                {finding.code for finding in findings},
            )
            self.assertEqual(output.read_text(encoding="utf-8"), "do not overwrite\n")

    def test_same_version_migration_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = _plan()
            plan["target_contract"] = {
                "name": "activation-checklist",
                "version": "1.0",
            }
            plan_path = self._repository(root, plan=plan)
            findings, _record, _target = migrate_contract.migrate(
                root,
                plan_path,
                contracts_dir=ROOT / "contracts",
                write=True,
            )
            self.assertIn(
                "MIGRATION_VERSION_UNCHANGED",
                {finding.code for finding in findings},
            )
            self.assertFalse((root / "records" / "target.json").exists())


if __name__ == "__main__":
    unittest.main()
