from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
VALIDATOR = TOOLS / "validate_bundle.py"
sys.path.insert(0, str(TOOLS))

import strict_json  # noqa: E402


NOW = "2026-07-18T15:55:00Z"


def raw_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def records() -> list[tuple[str, str, dict[str, Any]]]:
    run = {
        "schema_version": "1.0",
        "record_id": "run-cost-only-001",
        "code": "qe",
        "code_version": "7.5-test",
        "task_type": "scf",
        "case_id": "case-anonymous-001",
        "scientific_protocol_id": "protocol-cost-only-001",
        "status": "completed",
        "scientific_acceptance": "requires_human_review",
        "configuration": {"configuration_id": "layout-a"},
        "metrics": {"wall_time_s": 120.0, "core_hours": 8.0},
        "evidence": [],
        "limitations": ["No scientific decision is included in this bundle."],
        "provenance": {
            "collector": "run-campaign-bundle-test",
            "collector_version": "1.0",
            "generated_utc": NOW,
        },
    }
    run_raw = raw_json(run)
    campaign = {
        "schema_version": "1.0",
        "record_id": "campaign-cost-only-001",
        "run_manifest_id": run["record_id"],
        "source_run_ref": {
            "contract_name": "run-manifest",
            "schema_version": "1.0",
            "record_id": run["record_id"],
            "sha256": sha256(run_raw),
            "role": "source-run",
        },
        "code": run["code"],
        "code_version": run["code_version"],
        "task_type": run["task_type"],
        "system_class": "anonymous-small-periodic",
        "atom_count": 12,
        "scientific_protocol_id": run["scientific_protocol_id"],
        "configuration_id": "layout-a",
        "configuration": run["configuration"],
        "metrics": run["metrics"],
        "outcome": {
            "scientifically_accepted": False,
            "scientific_acceptance": "requires_human_review",
            "status": "completed-unreviewed",
            "accuracy_metrics": {},
            "failure_code": None,
        },
        "acceptance_evidence": {
            "calculation_record_ref": None,
            "decision_ref": None,
            "postdecision_claim_map_ref": None,
        },
        "source_manifest_sha256": sha256(run_raw),
        "recorded_utc": NOW,
    }
    recommendation = {
        "schema_version": "1.0",
        "recommendation_id": "recommendation-cost-only-001",
        "status": "insufficient-evidence",
        "applicability": {
            "code": run["code"],
            "code_version": run["code_version"],
            "task_type": run["task_type"],
            "system_class": campaign["system_class"],
            "atom_count": campaign["atom_count"],
            "scientific_protocol_id": run["scientific_protocol_id"],
        },
        "baseline_configuration_id": None,
        "recommended_configuration_id": None,
        "evidence_record_ids": [],
        "evidence_record_refs": [],
        "estimated_savings_fraction": None,
        "confidence": "none",
        "scientific_gate": (
            "No positive recommendation until accepted campaign evidence is "
            "resolved by production bundle validation."
        ),
        "limitations": ["This bundle records cost only."],
        "generated_utc": NOW,
    }
    return [
        ("run-manifest", run["record_id"], run),
        ("campaign-record", campaign["record_id"], campaign),
        (
            "recommendation-record",
            recommendation["recommendation_id"],
            recommendation,
        ),
    ]


def write_bundle(
    directory: Path,
    documents: list[tuple[str, str, dict[str, Any]]],
) -> tuple[Path, Path]:
    entries: list[dict[str, Any]] = []
    for index, (contract_name, record_id, document) in enumerate(documents):
        path = f"record-{index}.json"
        raw = raw_json(document)
        directory.joinpath(path).write_bytes(raw)
        entries.append(
            {
                "topological_index": index,
                "path": path,
                "label": f"record-{index}",
                "contract_name": contract_name,
                "schema_version": "1.0",
                "record_id": record_id,
                "sha256": sha256(raw),
            }
        )
    manifest = {
        "contract_name": "bundle-manifest",
        "schema_version": "1.0",
        "bundle_id": "bundle-run-campaign-migration-001",
        "bundle_mode": "portable-public",
        "created_utc": NOW,
        "records": entries,
        "artifacts": [],
        "privacy_policy": {
            "reject_credentials": True,
            "reject_private_identifiers": True,
            "reject_absolute_paths": True,
            "reject_path_traversal": True,
            "reject_restricted_payloads": True,
        },
        "producer": {
            "skill_id": "vibe-dft-skills",
            "skill_version": "1.0",
            "tool_id": "run-campaign-bundle-test",
            "tool_version": "1.0",
            "generated_utc": NOW,
        },
        "limitations": ["Synthetic portable integration fixture."],
    }
    manifest_path = directory / "bundle.json"
    report_path = directory / "report.json"
    manifest_path.write_bytes(raw_json(manifest))
    return manifest_path, report_path


def validate(manifest_path: Path, report_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(VALIDATOR),
            str(manifest_path),
            "--report",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


class RunCampaignBundleIntegrationTests(unittest.TestCase):
    def test_unreviewed_cost_inventory_bundle_passes_without_positive_claim(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            manifest, report_path = write_bundle(Path(raw_directory), records())
            result = validate(manifest, report_path)
            report = strict_json.loads_object(
                report_path.read_bytes(), "bundle report"
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(
            report["assurance"], "integrity-verified-no-positive-claim"
        )
        self.assertEqual(
            [item["status"] for item in report["record_results"]],
            ["pass", "pass", "pass"],
        )

    def test_schema_valid_cross_record_mutations_fail_in_production_bundle(self) -> None:
        mutations = []

        wrong_source_hash = records()
        wrong_source_hash[1][2]["source_manifest_sha256"] = "f" * 64
        mutations.append(
            (wrong_source_hash, "CAMPAIGN_SOURCE_RUN_BINDING_MATCH")
        )

        detached_recommendation_ids = records()
        detached_recommendation_ids[2][2]["evidence_record_ids"] = [
            detached_recommendation_ids[1][1]
        ]
        mutations.append(
            (
                detached_recommendation_ids,
                "RECOMMENDATION_EVIDENCE_CAMPAIGNS_MATCH",
            )
        )

        for documents, expected_code in mutations:
            with self.subTest(expected_code=expected_code), tempfile.TemporaryDirectory() as raw_directory:
                manifest, report_path = write_bundle(Path(raw_directory), documents)
                result = validate(manifest, report_path)
                report = strict_json.loads_object(
                    report_path.read_bytes(), "bundle report"
                )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(report["status"], "fail")
            self.assertIn(
                expected_code,
                {finding["code"] for finding in report["findings"]},
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
