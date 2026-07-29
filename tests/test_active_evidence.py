from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import active_evidence
import skill_registry


class ActiveEvidenceTests(unittest.TestCase):
    def _fixture(
        self,
        root: Path,
    ) -> tuple[dict[str, object], dict[str, object]]:
        skill = root / "skills" / "example-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("example\n", encoding="utf-8")
        route_catalog = skill / "route-catalog.json"
        route_catalog.write_text("{}\n", encoding="utf-8")
        source_hash = skill_registry.source_tree_digest(skill).sha256
        route_hash = hashlib.sha256(route_catalog.read_bytes()).hexdigest()
        skill_data: dict[str, object] = {
            "schema_version": "1.0",
            "skills": {
                "example-skill": {
                    "lifecycle": "active",
                    "path": "skills/example-skill",
                    "source_tree_sha256": source_hash,
                }
            },
        }
        evidence_data: dict[str, object] = {
            "schema_version": "1.0",
            "registry_id": "active-evidence-test",
            "records": {
                "example-skill": {
                    "skill_id": "example-skill",
                    "lifecycle": "active",
                    "source_tree_sha256": source_hash,
                    "activation_evidence_status": "legacy-unclosed",
                    "promotion_evidence": None,
                    "route_maturity_refs": [
                        {
                            "path": "skills/example-skill/route-catalog.json",
                            "sha256": route_hash,
                            "scope": "route-specific deterministic behavior only",
                        }
                    ],
                    "context_refs": [],
                    "known_limitations": [
                        "No independently reviewed promotion evidence is retained."
                    ],
                    "closure_requirements": [
                        "Complete a two-phase promotion review with immutable evidence."
                    ],
                    "prohibited_claims": [
                        "independent-activation-review-complete",
                        "active-lifecycle-evidence-closed",
                        "aggregate-maturity-upgraded-from-activation-status",
                    ],
                }
            },
        }
        return skill_data, evidence_data

    def _codes(
        self,
        data: dict[str, object],
        root: Path,
        skills: dict[str, object],
    ) -> set[str]:
        return {
            finding.code
            for finding in active_evidence.validation_findings(
                data,
                root=root,
                skill_data=skills,
            )
        }

    def test_canonical_active_evidence_is_complete_and_legacy_truthful(self) -> None:
        data = active_evidence.load_registry()
        skills = skill_registry.load_registry()
        self.assertEqual(
            active_evidence.validation_findings(
                data,
                root=ROOT,
                skill_data=skills,
            ),
            [],
        )
        active = {
            name
            for name, entry in skills["skills"].items()
            if entry["lifecycle"] == "active"
        }
        self.assertEqual(set(data["records"]), active)
        self.assertEqual(len(active), 7)
        for record in data["records"].values():
            self.assertEqual(record["activation_evidence_status"], "legacy-unclosed")
            self.assertIsNone(record["promotion_evidence"])
            self.assertNotIn("claim_ceiling", record)
            self.assertTrue(record["route_maturity_refs"])

    def test_missing_active_entry_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills, data = self._fixture(root)
            data["records"] = {}
            self.assertIn(
                "ACTIVE_EVIDENCE_SET_MISMATCH",
                self._codes(data, root, skills),
            )

    def test_skill_id_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills, data = self._fixture(root)
            data["records"]["example-skill"]["skill_id"] = "different-skill"
            self.assertIn(
                "ACTIVE_EVIDENCE_SKILL_ID_MISMATCH",
                self._codes(data, root, skills),
            )

    def test_source_tree_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills, data = self._fixture(root)
            (root / "skills" / "example-skill" / "SKILL.md").write_text(
                "changed\n",
                encoding="utf-8",
            )
            self.assertIn(
                "ACTIVE_EVIDENCE_SOURCE_BYTES_MISMATCH",
                self._codes(data, root, skills),
            )

    def test_missing_route_maturity_reference_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills, data = self._fixture(root)
            data["records"]["example-skill"]["route_maturity_refs"][0][
                "path"
            ] = "skills/example-skill/missing.json"
            self.assertIn(
                "ACTIVE_EVIDENCE_REF_MISSING",
                self._codes(data, root, skills),
            )

    def test_route_maturity_reference_hash_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills, data = self._fixture(root)
            data["records"]["example-skill"]["route_maturity_refs"][0][
                "sha256"
            ] = "0" * 64
            self.assertIn(
                "ACTIVE_EVIDENCE_REF_HASH_MISMATCH",
                self._codes(data, root, skills),
            )

    def test_verified_status_without_real_evidence_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills, data = self._fixture(root)
            record = data["records"]["example-skill"]
            record["activation_evidence_status"] = "verified"
            record["promotion_evidence"] = None
            self.assertIn(
                "ACTIVE_EVIDENCE_VERIFIED_REFS_MISSING",
                self._codes(data, root, skills),
            )

    def test_legacy_status_cannot_carry_promotion_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills, data = self._fixture(root)
            record = data["records"]["example-skill"]
            record["promotion_evidence"] = {
                "activation_record": {},
                "task_maturity_catalog": {},
                "promotion_delta": {},
                "validation_report": {},
            }
            self.assertIn(
                "ACTIVE_EVIDENCE_LEGACY_REFS_FORBIDDEN",
                self._codes(data, root, skills),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
