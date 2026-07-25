#!/usr/bin/env python3
"""Offline integrity tests for CatMAP source-pack inputs."""

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
        self.provider = self.seed["providers"][0]
        self.catalog_path = ROOT / self.provider["source_ref"]["path"]
        self.catalog = load_json(self.catalog_path)

    def test_all_inputs_match_strict_schemas(self) -> None:
        pairs = [
            (
                ROOT / "contracts/official-document-pack-seed.schema.json",
                self.seed_path,
            ),
            (
                ROOT / "contracts/official-document-scope-catalog.schema.json",
                self.scope_path,
            ),
            (
                ROOT
                / "contracts/official-document-source-catalog-1.1.schema.json",
                self.catalog_path,
            ),
        ]
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

    def test_seed_hashes_and_skill_locality(self) -> None:
        for ref in [
            self.seed["scope_catalog_ref"],
            self.provider["source_ref"],
        ]:
            path = ROOT / ref["path"]
            path.resolve().relative_to(SKILL_ROOT.resolve())
            self.assertFalse(path.is_symlink())
            self.assertEqual(ref["sha256"], sha256(path))

    def test_every_provider_feature_is_blocked_not_erased(self) -> None:
        scoped = {
            subject["subject_id"]
            for subject in self.scope["subjects"]
            if subject["evidence_class"] == "official-provider-required"
        }
        self.assertEqual(
            set(self.catalog["subjects"]),
            scoped,
        )
        self.assertEqual("1.1", self.catalog["schema_version"])
        self.assertEqual(
            self.provider["authority_id"], self.catalog["authority_id"]
        )
        self.assertEqual(self.provider["provider_id"], self.catalog["provider_id"])
        included_subjects = {
            subject_id
            for source in self.catalog["discovered_sources"].values()
            if source["disposition"] == "included"
            for subject_id in source["subject_ids"]
        }
        self.assertEqual(set(self.catalog["subjects"]), included_subjects)
        for subject in self.scope["subjects"]:
            if subject["evidence_class"] == "official-provider-required":
                self.assertEqual("blocked", subject["expected_disposition"])
                self.assertEqual(
                    ["catmap-docs"], subject["provider_input_ids"]
                )
            else:
                self.assertEqual([], subject["provider_input_ids"])
            for origin in subject["origin_refs"]:
                self.assertEqual(
                    origin["sha256"], sha256(ROOT / origin["path"])
                )

    def test_tree_inventory_is_exact_and_path_complete(self) -> None:
        inventory = load_json(
            REFERENCES / "source-pack-inventory-catmap.json"
        )
        self.assertTrue(SHA1.fullmatch(inventory["commit_id"]))
        self.assertTrue(SHA1.fullmatch(inventory["root_tree_object_id"]))
        paths = [entry["path"] for entry in inventory["entries"]]
        self.assertEqual(inventory["entry_count"], len(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(paths, sorted(paths))
        self.assertTrue(any(path.startswith("docs/") for path in paths))
        self.assertTrue(any(path.startswith("tutorials/") for path in paths))

    def test_version_conflict_and_lifecycle_boundary_are_explicit(self) -> None:
        blocker_codes = {
            blocker["code"] for blocker in self.catalog["blockers"]
        }
        self.assertIn("CAT.VERSION.SOURCE_CONFLICT", blocker_codes)
        proposal = load_json(
            REFERENCES / "source-pack-authority-proposal.json"
        )
        self.assertEqual("none", proposal["lifecycle_effect"])
        self.assertEqual("blocked", self.seed["status_ceiling"])


if __name__ == "__main__":
    unittest.main()
