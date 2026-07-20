from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import activation_ledger
from skill_registry import source_tree_digest


class ActivationLedgerTests(unittest.TestCase):
    def _repository(self, root: Path) -> None:
        skill = root / "skills" / "example-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("example\n", encoding="utf-8")
        digest = source_tree_digest(skill).sha256
        (root / "registry").mkdir()
        (root / "docs").mkdir()
        (root / "docs" / "baseline.json").write_text("{}\n", encoding="utf-8")
        (skill / "route.json").write_text("{}\n", encoding="utf-8")
        (root / "registry" / "skill-registry.yaml").write_text(
            "schema_version: \"1.0\"\n"
            "skills:\n"
            "  example-skill:\n"
            "    lifecycle: active\n"
            "    path: skills/example-skill\n"
            f"    source_tree_sha256: \"{digest}\"\n",
            encoding="utf-8",
        )
        (root / "registry" / "activation-ledger.yaml").write_text(
            "schema_version: \"1.0\"\n"
            "ledger_id: test-ledger\n"
            "baseline_source_commit: abc\n"
            "governance_commit: def\n"
            "records:\n"
            "  example-skill:\n"
            "    lifecycle: active\n"
            "    activation_state: legacy-active-review-required\n"
            f"    source_tree_sha256: \"{digest}\"\n"
            "    baseline_record: docs/baseline.json\n"
            "    independent_promotion_evidence: false\n"
            "    native_execution_claimed: false\n"
            "    scientific_acceptance_claimed: false\n"
            "    required_next_actions: [independent-review]\n",
            encoding="utf-8",
        )
        triggers = "\n".join(
            f"  - {item}" for item in sorted(activation_ledger.REQUIRED_REVIEW_TRIGGERS)
        )
        dimensions = ", ".join(activation_ledger.EXPECTED_DIMENSIONS)
        (root / "registry" / "maturity-ledger.yaml").write_text(
            "schema_version: \"1.0\"\n"
            "ledger_id: maturity-test\n"
            "entries:\n"
            "  example-skill:\n"
            "    lifecycle: active\n"
            "    review_status: review-required\n"
            "    route_catalog: skills/example-skill/route.json\n"
            f"    dimensions: [{dimensions}]\n"
            "    repository_behavior: validated\n"
            "    native_execution: not-assessed\n"
            "    scientific_validation: not-assessed\n"
            "    claim_ceiling: documented_behavior_only\n"
            "    version_scope: []\n"
            "automatic_review_triggers:\n"
            f"{triggers}\n",
            encoding="utf-8",
        )

    def test_matching_ledgers_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            self.assertEqual(activation_ledger.audit(root), [])

    def test_source_hash_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            (root / "skills" / "example-skill" / "SKILL.md").write_text(
                "changed\n",
                encoding="utf-8",
            )
            codes = {finding.code for finding in activation_ledger.audit(root)}
            self.assertIn("ACTIVATION_SOURCE_BYTES_MISMATCH", codes)

    def test_unassessed_science_cannot_claim_expert_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            ledger = root / "registry" / "maturity-ledger.yaml"
            ledger.write_text(
                ledger.read_text(encoding="utf-8").replace(
                    "documented_behavior_only",
                    "eligible_for_expert_review",
                ),
                encoding="utf-8",
            )
            codes = {finding.code for finding in activation_ledger.audit(root)}
            self.assertIn("MATURITY_CLAIM_CEILING_OVERSTATED", codes)


if __name__ == "__main__":
    unittest.main()
