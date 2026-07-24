#!/usr/bin/env python3
"""Offline tests for the campaign-efficiency source-pack extractor."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


SCRIPT = Path(__file__).with_name("sync_source_pack_catalog.py")
SPEC = importlib.util.spec_from_file_location("campaign_source_pack", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ROOT = MODULE.repository_root()
PROVIDER_CLASSES = {
    "software",
    "standard",
    "platform",
    "repository",
    "model-artifact",
    "dataset",
    "publisher",
}


class SourcePackCatalogTests(unittest.TestCase):
    def test_generated_inputs_are_current(self) -> None:
        self.assertEqual(MODULE.sync(check=True), ())

    def test_scope_contains_exact_cli_and_provider_sets(self) -> None:
        catalog = MODULE.scope_catalog(ROOT)
        subjects = {item["subject_id"]: item for item in catalog["subjects"]}
        expected_commands = {
            f"cli:{item}"
            for item in MODULE.literal_subcommands(
                ROOT
                / "skills"
                / MODULE.SKILL_ID
                / "scripts"
                / "campaign_efficiency"
                / "cli.py"
            )
        }
        self.assertEqual(
            {item for item in subjects if item.startswith("cli:")},
            expected_commands,
        )
        self.assertEqual(
            {item for item in subjects if item.startswith("qe:")},
            {item[0] for item in MODULE.QE_SUBJECTS},
        )
        self.assertEqual(
            subjects["qe:epw:coarse-fine-restart-artifacts"][
                "expected_disposition"
            ],
            "blocked",
        )

    def test_authority_proposal_covers_every_seed_provider(self) -> None:
        refs = ROOT / "skills" / MODULE.SKILL_ID / "references"
        seed = json.loads((refs / "source-pack-seed.json").read_text())
        proposal = json.loads(
            (refs / "source-pack-authority-proposal.json").read_text()
        )
        entries = [
            *proposal["authorities"],
            *proposal["existing_authority_bindings"],
        ]
        self.assertEqual(
            {
                (item["authority_id"], item["provider_id"])
                for item in entries
            },
            {
                (item["authority_id"], item["provider_id"])
                for item in seed["providers"]
            },
        )
        for item in [
            *entries,
            *proposal["provider_registry_proposals"],
        ]:
            self.assertIn(item["provider_class"], PROVIDER_CLASSES)
        for item in entries:
            binding = item["consumer_binding"]
            self.assertEqual(binding["consumer_skill_id"], MODULE.SKILL_ID)
            self.assertEqual(binding["authority_id"], item["authority_id"])
            self.assertEqual(binding["provider_id"], item["provider_id"])

    def test_seed_and_catalogs_match_strict_schemas(self) -> None:
        checks = [
            (
                "contracts/official-document-pack-seed.schema.json",
                f"skills/{MODULE.SKILL_ID}/references/source-pack-seed.json",
            ),
            (
                "contracts/official-document-scope-catalog.schema.json",
                f"skills/{MODULE.SKILL_ID}/references/source-pack-scope.json",
            ),
            (
                "contracts/official-document-source-catalog.schema.json",
                (
                    f"skills/{MODULE.SKILL_ID}/references/"
                    "source-pack-inputs/qe-phonon-epw.json"
                ),
            ),
        ]
        for schema_path, value_path in checks:
            with self.subTest(path=value_path):
                schema = json.loads((ROOT / schema_path).read_text(encoding="utf-8"))
                value = json.loads((ROOT / value_path).read_text(encoding="utf-8"))
                errors = sorted(
                    Draft202012Validator(
                        schema, format_checker=FormatChecker()
                    ).iter_errors(value),
                    key=lambda item: tuple(str(part) for part in item.absolute_path),
                )
                self.assertEqual([item.message for item in errors], [])

    def test_every_declared_loss_is_exactly_linked_by_affected_source(self) -> None:
        catalog = MODULE.qe_catalog()
        expected_by_source = {
            source["source_id"]: set()
            for source in catalog["sources"]
        }
        for loss in catalog["losses"]:
            for source_id in loss["affected_source_ids"]:
                self.assertIn(source_id, expected_by_source)
                expected_by_source[source_id].add(loss["loss_id"])

        for source in catalog["sources"]:
            self.assertEqual(len(source["slices"]), 1)
            actual = source["slices"][0]["loss_ids"]
            self.assertEqual(len(actual), len(set(actual)))
            self.assertEqual(
                set(actual),
                expected_by_source[source["source_id"]],
            )


if __name__ == "__main__":
    unittest.main()
