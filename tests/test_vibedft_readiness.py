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
        self.assertEqual(report["aggregate_readiness"], "blocked")
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
        self.assertTrue(report["blocked_terminal_intents"])
        self.assertIn(
            "ACTIVE_EVIDENCE_LEGACY_UNCLOSED",
            report["finding_codes"],
        )
        self.assertIn("TERMINAL_INTENT_BLOCKED", report["finding_codes"])
        self.assertIn(
            "independent-activation-review-complete",
            report["claim_readiness_limitations"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
