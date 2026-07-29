from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import vibedft_readiness


class VibeDFTReadinessTests(unittest.TestCase):
    def test_report_is_deterministic_and_fail_closed(self) -> None:
        first = vibedft_readiness.render_report(ROOT)
        second = vibedft_readiness.render_report(ROOT)
        self.assertEqual(first, second)
        report = json.loads(first)
        self.assertEqual(report["schema_version"], "1.0")
        self.assertEqual(report["aggregate_readiness"], "not-ready")
        self.assertEqual(
            report["aggregate_readiness_basis"],
            ["activation_evidence_readiness", "operational_readiness"],
        )
        self.assertEqual(len(report["active_skills"]), 7)
        self.assertTrue(
            all(
                item["activation_evidence_status"] == "legacy-unclosed"
                for item in report["active_skills"]
            )
        )
        self.assertTrue(
            all(item["routable_actions"] for item in report["active_skills"])
        )
        self.assertEqual(
            report["activation_evidence_readiness"]["status"],
            "not-ready",
        )
        self.assertEqual(
            report["activation_evidence_readiness"]["legacy_unclosed_count"],
            7,
        )
        self.assertEqual(report["operational_readiness"]["status"], "not-ready")
        missing = {
            item["intent"]
            for item in report["operational_readiness"]["missing_route_intents"]
        }
        self.assertIn("scheduler-submit", missing)
        self.assertIn("scheduler-control", missing)
        self.assertNotIn("scientific-acceptance-decision", missing)
        self.assertNotIn("external-publish", missing)
        self.assertNotIn("destructive-delete", missing)

        automation = report["automation_coverage"]
        self.assertEqual(automation["status"], "none")
        self.assertEqual(automation["automatable_intent_count"], 7)
        self.assertEqual(automation["automated_intent_count"], 0)
        self.assertEqual(automation["coverage_ratio"], 0.0)
        self.assertIn(
            "scientific-acceptance-decision",
            automation["human_boundary_intents"],
        )
        self.assertIn(
            "execution-authorization",
            automation["human_boundary_intents"],
        )
        self.assertEqual(
            automation["intentionally_disabled_intents"],
            ["destructive-delete", "external-publish"],
        )
        self.assertIn(
            "ACTIVE_EVIDENCE_LEGACY_UNCLOSED",
            report["finding_codes"],
        )
        self.assertIn("OPERATIONAL_ROUTE_MISSING", report["finding_codes"])
        self.assertNotIn("TERMINAL_INTENT_BLOCKED", report["finding_codes"])
        self.assertIn(
            "independent-activation-review-complete",
            report["claim_readiness_limitations"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
