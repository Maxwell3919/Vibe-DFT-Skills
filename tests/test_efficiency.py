from __future__ import annotations

from datetime import datetime, timezone
from contextlib import closing, redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sqlite3
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EFF_SCRIPTS = ROOT / "skills" / "dft-campaign-efficiency" / "scripts"
sys.path.insert(0, str(EFF_SCRIPTS))

from campaign_efficiency.recommend import recommendation  # noqa: E402
from campaign_efficiency.convert import campaign_from_run  # noqa: E402
from campaign_efficiency.store import ingest, validate_record  # noqa: E402
from campaign_efficiency import cli as efficiency_cli  # noqa: E402
from unittest.mock import patch


def record(
    record_id: str,
    configuration: str,
    core_hours: float,
    wall_time: float,
    *,
    accepted: bool = False,
    protocol: str = "protocol-001",
) -> dict:
    source_sha256 = "a" * 64
    acceptance_evidence = {
        "calculation_record_ref": None,
        "decision_ref": None,
        "postdecision_claim_map_ref": None,
    }
    if accepted:
        acceptance_evidence = {
            "calculation_record_ref": {
                "contract_name": "calculation-record-envelope",
                "schema_version": "1.0",
                "record_id": "calculation-" + record_id,
                "sha256": "b" * 64,
                "role": "scientific-candidate",
            },
            "decision_ref": {
                "contract_name": "decision-record",
                "schema_version": "1.0",
                "record_id": "decision-" + record_id,
                "sha256": "c" * 64,
                "role": "scientific-acceptance",
            },
            "postdecision_claim_map_ref": {
                "contract_name": "claim-evidence-map",
                "schema_version": "1.0",
                "record_id": "claim-map-" + record_id,
                "sha256": "d" * 64,
                "role": "postdecision-claim-map",
            },
        }
    return {
        "schema_version": "1.0",
        "record_id": record_id,
        "run_manifest_id": "run-" + record_id,
        "source_run_ref": {
            "contract_name": "run-manifest",
            "schema_version": "1.0",
            "record_id": "run-" + record_id,
            "sha256": source_sha256,
            "role": "source-run",
        },
        "code": "qe",
        "code_version": "7.5",
        "task_type": "scf",
        "system_class": "anon-2d-small",
        "atom_count": 12,
        "scientific_protocol_id": protocol,
        "configuration_id": configuration,
        "configuration": {"parallel_layout": configuration},
        "metrics": {"wall_time_s": wall_time, "core_hours": core_hours},
        "outcome": {
            "scientifically_accepted": accepted,
            "scientific_acceptance": "accepted" if accepted else "not_assessed",
            "status": "accepted" if accepted else "completed-unreviewed",
            "accuracy_metrics": {"energy_delta_ev": 0.0005},
            "failure_code": None,
        },
        "acceptance_evidence": acceptance_evidence,
        "source_manifest_sha256": source_sha256,
        "recorded_utc": datetime(2026, 7, 17, tzinfo=timezone.utc).isoformat(),
    }


class EfficiencyTests(unittest.TestCase):
    def test_cli_init_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "experience.sqlite3"
            result = subprocess.run(
                [sys.executable, "-B", str(EFF_SCRIPTS / "dft_efficiency_cli.py"), "init", "--db", str(db)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(db.is_file())

    def test_cli_registry_failure_is_stable_exit_two_without_traceback(self) -> None:
        stderr = io.StringIO()
        with patch.object(
            efficiency_cli,
            "calculation_codes",
            side_effect=ValueError("invalid registry snapshot: synthetic drift"),
        ), redirect_stderr(stderr):
            result = efficiency_cli.main(["init", "--db", "private.sqlite3"])
        self.assertEqual(result, 2)
        self.assertIn("invalid registry snapshot", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_v1_database_is_refused_without_in_place_schema_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "legacy.sqlite3"
            with closing(sqlite3.connect(db)) as connection:
                with connection:
                    connection.executescript(
                        """
                        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                        INSERT INTO metadata(key, value) VALUES('schema_version', '1');
                        CREATE TABLE campaign_records (
                            record_id TEXT PRIMARY KEY,
                            accepted INTEGER NOT NULL,
                            payload_json TEXT NOT NULL
                        );
                        """
                    )
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(EFF_SCRIPTS / "dft_efficiency_cli.py"),
                    "init",
                    "--db",
                    str(db),
                ],
                capture_output=True,
                text=True,
            )
            with closing(sqlite3.connect(db)) as connection:
                version = connection.execute(
                    "SELECT value FROM metadata WHERE key='schema_version'"
                ).fetchone()[0]
                columns = {
                    row[1]
                    for row in connection.execute(
                        "PRAGMA table_info(campaign_records)"
                    ).fetchall()
                }
        self.assertEqual(result.returncode, 2)
        self.assertIn("unsupported database schema version: 1", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(version, "1")
        self.assertNotIn("acceptance_verified", columns)

    def test_v1_fixture_is_clean_under_resourcewarning_error(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-W",
                "error::ResourceWarning",
                "-m",
                "unittest",
                (
                    "tests.test_efficiency.EfficiencyTests."
                    "test_v1_database_is_refused_without_in_place_schema_mutation"
                ),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("ResourceWarning", result.stderr)
        self.assertNotIn("Exception ignored", result.stderr)

    def test_convert_self_declared_accepted_run_manifest_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_path = Path(directory) / "run.json"
            run_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "record_id": "run-anon-001",
                        "code": "qe",
                        "code_version": "7.5",
                        "task_type": "scf",
                        "case_id": "case-anon-001",
                        "scientific_protocol_id": "protocol-001",
                        "status": "accepted",
                        "scientific_acceptance": "accepted",
                        "configuration": {"parallel_layout": "A"},
                        "metrics": {"wall_time_s": 100.0, "core_hours": 10.0},
                        "evidence": [],
                        "limitations": [],
                        "provenance": {
                            "collector": "test",
                            "collector_version": "1.0",
                            "generated_utc": "2026-07-17T00:00:00+00:00"
                        }
                    }
                )
            )
            with self.assertRaisesRegex(ValueError, "invalid"):
                campaign_from_run(run_path, "anon-2d-small", 12, "A")

    def test_convert_terminal_cp2k_manifest_without_promoting_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_path = Path(directory) / "cp2k-run.json"
            run_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "record_id": "run-cp2k-anon-001",
                        "code": "cp2k",
                        "code_version": "2026.2",
                        "task_type": "static",
                        "case_id": "case-cp2k-anon-001",
                        "scientific_protocol_id": "protocol-cp2k-001",
                        "status": "failed",
                        "scientific_acceptance": "not_assessed",
                        "configuration": {"parallel_layout": "layout-a"},
                        "metrics": {"wall_time_s": 40.0, "core_hours": 2.0},
                        "evidence": [],
                        "limitations": ["technical run failed before scientific assessment"],
                        "provenance": {
                            "collector": "test",
                            "collector_version": "1.0",
                            "generated_utc": "2026-07-18T00:00:00+00:00",
                        },
                    }
                )
            )
            result = campaign_from_run(run_path, "anon-bulk-small", 8, "layout-a")
            self.assertEqual(result["code"], "cp2k")
            self.assertEqual(result["outcome"]["status"], "failed")
            self.assertFalse(result["outcome"]["scientifically_accepted"])
            self.assertEqual(validate_record(result), [])

    def test_privacy_field_rejected(self) -> None:
        value = record("rec-private", "A", 10, 100, accepted=False)
        value["configuration"]["project_name"] = "secret"
        failures = validate_record(value)
        self.assertTrue(any("forbidden private-identity" in item for item in failures))

    def test_duplicate_idempotent_and_collision_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "experience.sqlite3"
            value = record("rec-001", "A", 10, 100, accepted=False)
            self.assertEqual(ingest(db, value), "inserted")
            self.assertEqual(ingest(db, value), "already-present")
            changed = record("rec-001", "A", 11, 100, accepted=False)
            with self.assertRaisesRegex(ValueError, "collision"):
                ingest(db, changed)

    def test_store_blocks_self_filled_acceptance_and_unreviewed_costs_do_not_recommend(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "experience.sqlite3"
            with self.assertRaisesRegex(ValueError, "external human trust"):
                ingest(
                    db,
                    record(
                        "rec-self-accepted",
                        "A",
                        12.0,
                        120,
                        accepted=True,
                    ),
                )
            for value in (
                record("rec-a1", "A", 12.0, 120, accepted=False),
                record("rec-a2", "A", 10.0, 110, accepted=False),
                record("rec-b1", "B", 7.0, 90, accepted=False),
                record("rec-b2", "B", 5.0, 80, accepted=False),
                record("rec-bad", "C", 1.0, 10, accepted=False),
            ):
                ingest(db, value)
            result = recommendation(db, "qe", "7.5", "scf", "anon-2d-small", 12, "protocol-001")
            self.assertEqual(result["status"], "insufficient-evidence")
            self.assertIsNone(result["baseline_configuration_id"])
            self.assertIsNone(result["recommended_configuration_id"])
            self.assertEqual(result["evidence_record_refs"], [])

    def test_incomparable_protocol_is_insufficient(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "experience.sqlite3"
            ingest(db, record("rec-a1", "A", 12, 120, accepted=False, protocol="p1"))
            ingest(db, record("rec-a2", "A", 11, 110, accepted=False, protocol="p1"))
            ingest(db, record("rec-b1", "B", 5, 50, accepted=False, protocol="p2"))
            ingest(db, record("rec-b2", "B", 4, 40, accepted=False, protocol="p2"))
            result = recommendation(db, "qe", "7.5", "scf", "anon-2d-small", 12, "p1")
            self.assertEqual(result["status"], "insufficient-evidence")


if __name__ == "__main__":
    unittest.main(verbosity=2)
