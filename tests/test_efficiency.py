from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EFF_SCRIPTS = ROOT / "skills" / "dft-campaign-efficiency" / "scripts"
sys.path.insert(0, str(EFF_SCRIPTS))

from campaign_efficiency.recommend import recommendation  # noqa: E402
from campaign_efficiency.convert import campaign_from_run  # noqa: E402
from campaign_efficiency.store import ingest, validate_record  # noqa: E402


def record(record_id: str, configuration: str, core_hours: float, wall_time: float, *, accepted: bool = True, protocol: str = "protocol-001") -> dict:
    return {
        "schema_version": "1.0",
        "record_id": record_id,
        "run_manifest_id": "run-" + record_id,
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
            "status": "accepted" if accepted else "rejected",
            "accuracy_metrics": {"energy_delta_ev": 0.0005},
            "failure_code": None,
        },
        "recorded_utc": datetime(2026, 7, 17, tzinfo=timezone.utc).isoformat(),
    }


class EfficiencyTests(unittest.TestCase):
    def test_cli_init_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "experience.sqlite3"
            result = subprocess.run(
                [sys.executable, str(EFF_SCRIPTS / "dft_efficiency_cli.py"), "init", "--db", str(db)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(db.is_file())

    def test_convert_accepted_run_manifest(self) -> None:
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
            result = campaign_from_run(run_path, "anon-2d-small", 12, "A")
            self.assertEqual(result["run_manifest_id"], "run-anon-001")
            self.assertTrue(result["outcome"]["scientifically_accepted"])
            self.assertEqual(validate_record(result), [])

    def test_privacy_field_rejected(self) -> None:
        value = record("rec-private", "A", 10, 100)
        value["configuration"]["project_name"] = "secret"
        failures = validate_record(value)
        self.assertTrue(any("forbidden private-identity" in item for item in failures))

    def test_duplicate_idempotent_and_collision_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "experience.sqlite3"
            value = record("rec-001", "A", 10, 100)
            self.assertEqual(ingest(db, value), "inserted")
            self.assertEqual(ingest(db, value), "already-present")
            changed = record("rec-001", "A", 11, 100)
            with self.assertRaisesRegex(ValueError, "collision"):
                ingest(db, changed)

    def test_recommendation_requires_repeated_accepted_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "experience.sqlite3"
            for value in (
                record("rec-a1", "A", 12.0, 120),
                record("rec-a2", "A", 10.0, 110),
                record("rec-b1", "B", 7.0, 90),
                record("rec-b2", "B", 5.0, 80),
                record("rec-bad", "C", 1.0, 10, accepted=False),
            ):
                ingest(db, value)
            result = recommendation(db, "qe", "7.5", "scf", "anon-2d-small", 12, "protocol-001")
            self.assertEqual(result["status"], "validated-for-this-campaign")
            self.assertEqual(result["baseline_configuration_id"], "A")
            self.assertEqual(result["recommended_configuration_id"], "B")
            self.assertAlmostEqual(result["estimated_savings_fraction"], 5 / 11)
            self.assertNotIn("rec-bad", result["evidence_record_ids"])

    def test_incomparable_protocol_is_insufficient(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "experience.sqlite3"
            ingest(db, record("rec-a1", "A", 12, 120, protocol="p1"))
            ingest(db, record("rec-a2", "A", 11, 110, protocol="p1"))
            ingest(db, record("rec-b1", "B", 5, 50, protocol="p2"))
            ingest(db, record("rec-b2", "B", 4, 40, protocol="p2"))
            result = recommendation(db, "qe", "7.5", "scf", "anon-2d-small", 12, "p1")
            self.assertEqual(result["status"], "insufficient-evidence")


if __name__ == "__main__":
    unittest.main(verbosity=2)
