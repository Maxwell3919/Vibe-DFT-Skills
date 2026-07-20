from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import audit_semantic_obligations as audit


class SemanticObligationRegistryTests(unittest.TestCase):
    def _contract(self, declaration: object) -> object:
        return SimpleNamespace(
            name="example-contract",
            version="1.0",
            filename="example-contract.schema.json",
            schema={"x-vibe-semantic-obligations": declaration},
        )

    def test_list_form_uses_bundle_dispatcher(self) -> None:
        declaration, findings = audit.parse_declaration(
            self._contract(["EXAMPLE_OBLIGATION"])
        )
        self.assertEqual(findings, [])
        self.assertIsNotNone(declaration)
        self.assertEqual(declaration.validator_id, "bundle-semantic-dispatcher")

    def test_object_form_preserves_explicit_validator(self) -> None:
        declaration, findings = audit.parse_declaration(
            self._contract(
                {
                    "validator": "commit-aware-promotion-validator",
                    "required_checks": ["example-check"],
                }
            )
        )
        self.assertEqual(findings, [])
        self.assertIsNotNone(declaration)
        self.assertEqual(
            declaration.validator_id,
            "commit-aware-promotion-validator",
        )

    def test_duplicate_obligation_is_rejected(self) -> None:
        declaration, findings = audit.parse_declaration(
            self._contract(["EXAMPLE_OBLIGATION", "EXAMPLE_OBLIGATION"])
        )
        self.assertIsNone(declaration)
        self.assertIn(
            "SEMANTIC_OBLIGATION_DUPLICATE",
            {finding.code for finding in findings},
        )

    def test_repository_semantic_registry_is_closed(self) -> None:
        findings, report = audit.audit(ROOT)
        self.assertEqual(findings, [])
        self.assertGreater(report["contracts_with_obligations"], 0)
        self.assertIn(
            "commit-aware-promotion-validator",
            {item["validator_id"] for item in report["validators"]},
        )


if __name__ == "__main__":
    unittest.main()
