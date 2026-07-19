from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
EFFICIENCY_SCRIPTS = ROOT / "skills" / "dft-campaign-efficiency" / "scripts"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(EFFICIENCY_SCRIPTS))

import validate_contract  # noqa: E402
import validate_semantics  # noqa: E402
from campaign_efficiency.convert import campaign_from_run  # noqa: E402


HASH = "0" * 64


def run_manifest(
    *,
    status: str = "completed",
    scientific_acceptance: str = "not_assessed",
    evidence_status: str = "present",
    evidence_sha256: str | None = HASH,
) -> dict:
    evidence = {
        "role": "main-output",
        "label": "anonymized-output.log",
        "status": evidence_status,
    }
    if evidence_sha256 is not None:
        evidence["sha256"] = evidence_sha256
    return {
        "schema_version": "1.0",
        "record_id": "run-anon-001",
        "code": "qe",
        "code_version": "7.5",
        "task_type": "scf",
        "case_id": "case-anon-001",
        "scientific_protocol_id": "protocol-001",
        "status": status,
        "scientific_acceptance": scientific_acceptance,
        "configuration": {"prefix": "anonymous"},
        "metrics": {"wall_time_s": 100.0, "core_hours": 10.0},
        "evidence": [evidence],
        "limitations": ["Scientific decision is recorded downstream."],
        "provenance": {
            "collector": "test",
            "collector_version": "1.0",
            "generated_utc": "2026-07-18T00:00:00Z",
        },
    }


class RunManifestSecurityMigrationTests(unittest.TestCase):
    def test_schema_is_strictly_predecision_and_advertises_production_obligations(self) -> None:
        schema = json.loads(
            (ROOT / "contracts" / "run-manifest.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["properties"]["status"]["enum"],
            ["planned", "running", "completed", "stopped", "failed"],
        )
        self.assertEqual(
            schema["properties"]["scientific_acceptance"]["enum"],
            ["not_assessed", "requires_human_review"],
        )
        self.assertEqual(
            set(schema["x-vibe-semantic-obligations"]),
            {
                "LEGACY_RUN_PREDECISION_SCIENTIFIC_STATE",
                "LEGACY_RUN_EVIDENCE_HASH_STATUS_MATCH",
            },
        )

    def test_schema_rejects_self_declared_scientific_verdicts(self) -> None:
        for status, acceptance in (
            ("failed", "accepted"),
            ("completed", "accepted"),
            ("completed", "rejected"),
            ("accepted", "accepted"),
        ):
            with self.subTest(status=status, acceptance=acceptance):
                self.assertTrue(
                    validate_contract.validation_errors(
                        "run", run_manifest(status=status, scientific_acceptance=acceptance)
                    )
                )

        self.assertEqual(
            validate_contract.validation_errors(
                "run",
                run_manifest(
                    status="completed",
                    scientific_acceptance="requires_human_review",
                ),
            ),
            [],
        )
        for status in ("planned", "running", "stopped", "failed"):
            with self.subTest(status=status):
                self.assertTrue(
                    validate_contract.validation_errors(
                        "run",
                        run_manifest(
                            status=status,
                            scientific_acceptance="requires_human_review",
                        ),
                    )
                )

    def test_evidence_hash_state_is_enforced_by_schema_and_semantics(self) -> None:
        present_unhashed = run_manifest(evidence_sha256=None)
        missing_hashed = run_manifest(evidence_status="missing", evidence_sha256=HASH)
        for value in (present_unhashed, missing_hashed):
            with self.subTest(value=value):
                self.assertTrue(validate_contract.validation_errors("run", value))
                self.assertTrue(validate_semantics.semantic_findings("run", value))

    def test_validate_semantics_cli_rejects_duplicate_keys_with_stable_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_bytes(b'{"schema_version":"1.0","schema_version":"1.0"}')
            result = subprocess.run(
                [sys.executable, "-B", str(TOOLS / "validate_semantics.py"), "run", str(path)],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate object key is forbidden", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_create_run_manifest_cli_rejects_duplicate_input_without_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            configuration = root / "configuration.json"
            output = root / "run.json"
            configuration.write_bytes(b'{"ecut":40,"ecut":50}')
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(TOOLS / "create_run_manifest.py"),
                    "--code",
                    "qe",
                    "--code-version",
                    "7.5",
                    "--task-type",
                    "scf",
                    "--case-id",
                    "case-anon-001",
                    "--protocol-id",
                    "protocol-001",
                    "--status",
                    "completed",
                    "--scientific-acceptance",
                    "not_assessed",
                    "--configuration",
                    str(configuration),
                    "--out",
                    str(output),
                ],
                capture_output=True,
                text=True,
            )
            self.assertFalse(output.exists())
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate object key is forbidden", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_create_run_manifest_cli_rejects_review_state_on_failed_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(TOOLS / "create_run_manifest.py"),
                    "--code",
                    "qe",
                    "--code-version",
                    "7.5",
                    "--task-type",
                    "scf",
                    "--case-id",
                    "case-anon-001",
                    "--protocol-id",
                    "protocol-001",
                    "--status",
                    "failed",
                    "--scientific-acceptance",
                    "requires_human_review",
                    "--out",
                    str(output),
                ],
                capture_output=True,
                text=True,
            )
            self.assertFalse(output.exists())
        self.assertEqual(result.returncode, 2)
        self.assertIn("schema-invalid", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_create_run_manifest_cli_reports_output_io_as_stable_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_directory = Path(directory) / "existing-directory"
            output_directory.mkdir()
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(TOOLS / "create_run_manifest.py"),
                    "--code",
                    "qe",
                    "--code-version",
                    "7.5",
                    "--task-type",
                    "scf",
                    "--case-id",
                    "case-anon-001",
                    "--protocol-id",
                    "protocol-001",
                    "--status",
                    "completed",
                    "--scientific-acceptance",
                    "not_assessed",
                    "--out",
                    str(output_directory),
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot write run manifest", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_completed_unreviewed_run_can_record_cost_without_becoming_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_path = Path(directory) / "run.json"
            run_path.write_text(json.dumps(run_manifest()), encoding="utf-8")
            exact_raw_sha256 = hashlib.sha256(run_path.read_bytes()).hexdigest()
            campaign = campaign_from_run(
                run_path,
                "anon-2d-small",
                12,
                "configuration-a",
            )
        self.assertEqual(campaign["outcome"]["status"], "completed-unreviewed")
        self.assertEqual(campaign["outcome"]["scientific_acceptance"], "not_assessed")
        self.assertFalse(campaign["outcome"]["scientifically_accepted"])
        self.assertEqual(campaign["source_manifest_sha256"], exact_raw_sha256)
        self.assertEqual(campaign["source_run_ref"]["sha256"], exact_raw_sha256)
        self.assertIsNone(campaign["acceptance_evidence"]["calculation_record_ref"])
        self.assertIsNone(campaign["acceptance_evidence"]["decision_ref"])
        self.assertIsNone(campaign["acceptance_evidence"]["postdecision_claim_map_ref"])

    def test_stopped_run_cost_is_preserved_without_scientific_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_path = Path(directory) / "run.json"
            run_path.write_text(
                json.dumps(run_manifest(status="stopped")),
                encoding="utf-8",
            )
            campaign = campaign_from_run(
                run_path,
                "anon-2d-small",
                12,
                "configuration-a",
            )
        self.assertEqual(campaign["outcome"]["status"], "stopped")
        self.assertEqual(campaign["outcome"]["scientific_acceptance"], "not_assessed")
        self.assertFalse(campaign["outcome"]["scientifically_accepted"])

    def test_converter_blocks_legacy_self_declared_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_path = Path(directory) / "run.json"
            value = run_manifest(status="accepted", scientific_acceptance="accepted")
            run_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pre-decision|decision|invalid"):
                campaign_from_run(
                    run_path,
                    "anon-2d-small",
                    12,
                    "configuration-a",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
