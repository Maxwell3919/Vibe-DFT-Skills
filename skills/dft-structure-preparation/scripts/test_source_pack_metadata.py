#!/usr/bin/env python3
"""Offline integrity tests for the structure-preparation source-pack inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCES = SKILL_ROOT / "references"
SHA1 = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: JSON root is not an object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourcePackMetadataTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.seed_path = REFERENCES / "source-pack-seed.json"
        self.seed = load_json(self.seed_path)
        self.scope_path = REFERENCES / "source-pack-scope-catalog.json"
        self.scope = load_json(self.scope_path)

    def test_seed_and_catalogs_match_strict_schemas(self) -> None:
        checks = [
            (
                ROOT / "contracts/official-document-pack-seed.schema.json",
                self.seed_path,
            ),
            (
                ROOT / "contracts/official-document-scope-catalog.schema.json",
                self.scope_path,
            ),
        ]
        for provider in self.seed["providers"]:
            checks.append(
                (
                    ROOT
                    / "contracts/official-document-source-catalog-1.1.schema.json",
                    ROOT / provider["source_ref"]["path"],
                )
            )
        for schema_path, instance_path in checks:
            with self.subTest(instance=instance_path.name):
                schema = load_json(schema_path)
                Draft202012Validator.check_schema(schema)
                errors = sorted(
                    Draft202012Validator(
                        schema, format_checker=FormatChecker()
                    ).iter_errors(load_json(instance_path)),
                    key=lambda error: tuple(str(part) for part in error.absolute_path),
                )
                self.assertEqual([], [error.message for error in errors])

    def test_seed_references_are_exact_and_skill_local(self) -> None:
        refs = [self.seed["scope_catalog_ref"]]
        refs.extend(provider["source_ref"] for provider in self.seed["providers"])
        for ref in refs:
            with self.subTest(path=ref["path"]):
                path = ROOT / ref["path"]
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())
                path.resolve().relative_to(SKILL_ROOT.resolve())
                self.assertEqual(ref["sha256"], sha256(path))

    def test_semantic_scope_cannot_hide_provider_subjects(self) -> None:
        provider_ids = {
            provider["input_id"] for provider in self.seed["providers"]
        }
        scoped_by_provider = {provider_id: set() for provider_id in provider_ids}
        for subject in self.scope["subjects"]:
            if subject["evidence_class"] == "official-provider-required":
                self.assertEqual("blocked", subject["expected_disposition"])
                self.assertTrue(subject["provider_input_ids"])
                for provider_id in subject["provider_input_ids"]:
                    self.assertIn(provider_id, provider_ids)
                    scoped_by_provider[provider_id].add(subject["subject_id"])
            else:
                self.assertEqual([], subject["provider_input_ids"])
                self.assertIn(
                    subject["expected_disposition"],
                    {"not-applicable", "excluded"},
                )
            for origin in subject["origin_refs"]:
                origin_path = ROOT / origin["path"]
                self.assertEqual(origin["sha256"], sha256(origin_path))

        for provider in self.seed["providers"]:
            catalog = load_json(ROOT / provider["source_ref"]["path"])
            self.assertEqual("1.1", catalog["schema_version"])
            self.assertEqual(provider["authority_id"], catalog["authority_id"])
            self.assertEqual(provider["provider_id"], catalog["provider_id"])
            catalog_subjects = set(catalog["subjects"])
            self.assertEqual(
                catalog_subjects,
                scoped_by_provider[provider["input_id"]],
                provider["input_id"],
            )
            included_subjects = {
                subject_id
                for source in catalog["discovered_sources"].values()
                if source["disposition"] == "included"
                for subject_id in source["subject_ids"]
            }
            self.assertEqual(catalog_subjects, included_subjects)

    def test_full_git_tree_metadata_inventories_are_closed(self) -> None:
        expected = {
            "ase": "source-pack-inventory-ase.json",
            "pymatgen": "source-pack-inventory-pymatgen.json",
            "spglib": "source-pack-inventory-spglib.json",
            "rdkit": "source-pack-inventory-rdkit.json",
        }
        for provider_id, filename in expected.items():
            with self.subTest(provider=provider_id):
                inventory = load_json(REFERENCES / filename)
                self.assertEqual(provider_id, inventory["provider_id"])
                self.assertTrue(SHA1.fullmatch(inventory["commit_id"]))
                self.assertTrue(SHA1.fullmatch(inventory["root_tree_object_id"]))
                entries = inventory["entries"]
                self.assertEqual(inventory["entry_count"], len(entries))
                paths = [entry["path"] for entry in entries]
                self.assertEqual(len(paths), len(set(paths)))
                self.assertEqual(paths, sorted(paths))
                for entry in entries:
                    self.assertIn(entry["object_type"], {"blob", "commit"})
                    self.assertTrue(SHA1.fullmatch(entry["object_id"]))

    def test_proposal_preserves_lifecycle_and_records_missing_providers(self) -> None:
        proposal = load_json(
            REFERENCES / "source-pack-authority-proposal.json"
        )
        self.assertEqual("none", proposal["lifecycle_effect"])
        self.assertEqual(
            {"ase", "spglib"},
            {
                item["provider_id"]
                for item in proposal["provider_registry_proposals"]
            },
        )
        self.assertTrue(
            any(
                "pymatgen-core 2026.5.18" in blocker
                for blocker in proposal["central_blockers"]
            )
        )
        self.assertEqual(
            {provider["authority_id"] for provider in self.seed["providers"]},
            {
                authority["authority_id"]
                for authority in proposal["authorities"]
            },
        )


if __name__ == "__main__":
    unittest.main()
