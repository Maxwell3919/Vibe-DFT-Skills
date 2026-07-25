#!/usr/bin/env python3
"""Offline integrity tests for DeePMD provider source-pack inputs."""

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
    def setUp(self) -> None:
        self.seed_path = REFERENCES / "source-pack-seed.json"
        self.seed = load_json(self.seed_path)
        self.scope_path = REFERENCES / "source-pack-scope-catalog.json"
        self.scope = load_json(self.scope_path)

    def test_strict_input_schemas(self) -> None:
        pairs = [
            (
                ROOT / "contracts/official-document-pack-seed.schema.json",
                self.seed_path,
            ),
            (
                ROOT / "contracts/official-document-scope-catalog.schema.json",
                self.scope_path,
            ),
        ]
        pairs.extend(
            (
                ROOT
                / "contracts/official-document-source-catalog-1.1.schema.json",
                ROOT / provider["source_ref"]["path"],
            )
            for provider in self.seed["providers"]
        )
        for schema_path, instance_path in pairs:
            with self.subTest(instance=instance_path.name):
                schema = load_json(schema_path)
                Draft202012Validator.check_schema(schema)
                errors = list(
                    Draft202012Validator(
                        schema, format_checker=FormatChecker()
                    ).iter_errors(load_json(instance_path))
                )
                self.assertEqual([], [error.message for error in errors])

    def test_seed_hashes_and_locality(self) -> None:
        refs = [self.seed["scope_catalog_ref"]]
        refs.extend(provider["source_ref"] for provider in self.seed["providers"])
        for ref in refs:
            path = ROOT / ref["path"]
            with self.subTest(path=ref["path"]):
                path.resolve().relative_to(SKILL_ROOT.resolve())
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())
                self.assertEqual(ref["sha256"], sha256(path))

    def test_provider_subjects_are_exactly_partitioned_and_blocked(self) -> None:
        input_ids = {
            provider["input_id"] for provider in self.seed["providers"]
        }
        scoped = {input_id: set() for input_id in input_ids}
        for subject in self.scope["subjects"]:
            if subject["evidence_class"] == "official-provider-required":
                self.assertEqual("blocked", subject["expected_disposition"])
                for input_id in subject["provider_input_ids"]:
                    self.assertIn(input_id, input_ids)
                    scoped[input_id].add(subject["subject_id"])
            else:
                self.assertEqual([], subject["provider_input_ids"])
            for origin in subject["origin_refs"]:
                self.assertEqual(
                    origin["sha256"], sha256(ROOT / origin["path"])
                )
        for provider in self.seed["providers"]:
            catalog = load_json(ROOT / provider["source_ref"]["path"])
            self.assertEqual("1.1", catalog["schema_version"])
            self.assertEqual(provider["authority_id"], catalog["authority_id"])
            self.assertEqual(provider["provider_id"], catalog["provider_id"])
            self.assertEqual(
                set(catalog["subjects"]),
                scoped[provider["input_id"]],
            )
            included_subjects = {
                subject_id
                for source in catalog["discovered_sources"].values()
                if source["disposition"] == "included"
                for subject_id in source["subject_ids"]
            }
            self.assertEqual(set(catalog["subjects"]), included_subjects)

    def test_tree_receipts_cover_every_recorded_path_once(self) -> None:
        expected = {
            "deepmd": "source-pack-inventory-deepmd.json",
            "dpdata": "source-pack-inventory-dpdata.json",
            "dpgen": "source-pack-inventory-dpgen.json",
        }
        for provider_id, filename in expected.items():
            inventory = load_json(REFERENCES / filename)
            with self.subTest(provider=provider_id):
                self.assertEqual(provider_id, inventory["provider_id"])
                self.assertTrue(SHA1.fullmatch(inventory["commit_id"]))
                self.assertTrue(SHA1.fullmatch(inventory["root_tree_object_id"]))
                paths = [entry["path"] for entry in inventory["entries"]]
                self.assertEqual(inventory["entry_count"], len(paths))
                self.assertEqual(len(paths), len(set(paths)))
                self.assertEqual(paths, sorted(paths))
                for entry in inventory["entries"]:
                    self.assertTrue(SHA1.fullmatch(entry["object_id"]))
                    self.assertIn(entry["object_type"], {"blob", "commit"})

    def test_proposal_adds_missing_providers_without_promotion(self) -> None:
        proposal = load_json(
            REFERENCES / "source-pack-authority-proposal.json"
        )
        self.assertEqual("none", proposal["lifecycle_effect"])
        self.assertEqual(
            {"dpdata", "dpgen"},
            {
                item["provider_id"]
                for item in proposal["provider_registry_proposals"]
            },
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
