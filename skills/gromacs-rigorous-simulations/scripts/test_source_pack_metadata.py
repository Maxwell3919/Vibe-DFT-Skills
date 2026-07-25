#!/usr/bin/env python3
"""Offline integrity tests for gromacs-rigorous-simulations source-pack inputs."""

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


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: JSON root is not an object")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourcePackMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seed_path = REFERENCES / "source-pack-seed.json"
        self.scope_path = REFERENCES / "source-pack-scope-catalog.json"
        self.catalog_path = REFERENCES / "source-pack-source-catalog-gromacs.json"
        self.seed = load(self.seed_path)
        self.scope = load(self.scope_path)
        self.catalog = load(self.catalog_path)

    def test_strict_schemas(self) -> None:
        pairs = [
            ("official-document-pack-seed.schema.json", self.seed_path),
            ("official-document-scope-catalog.schema.json", self.scope_path),
            (
                "official-document-source-catalog-1.1.schema.json",
                self.catalog_path,
            ),
        ]
        for schema_name, instance_path in pairs:
            schema = load(ROOT / "contracts" / schema_name)
            Draft202012Validator.check_schema(schema)
            errors = list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(load(instance_path))
            )
            self.assertEqual([], [error.message for error in errors])

    def test_seed_hashes_are_local_and_exact(self) -> None:
        provider = self.seed["providers"][0]
        self.assertEqual("gromacs-docs", provider["input_id"])
        self.assertEqual("gromacs-release-source-docs-2026-3", provider["authority_id"])
        for item in (self.seed["scope_catalog_ref"], provider["source_ref"]):
            path = ROOT / item["path"]
            path.resolve().relative_to(SKILL_ROOT.resolve())
            self.assertFalse(path.is_symlink())
            self.assertEqual(item["sha256"], digest(path))

    def test_semantic_scope_preserves_all_provider_subjects(self) -> None:
        scoped = {
            item["subject_id"]
            for item in self.scope["subjects"]
            if item["evidence_class"] == "official-provider-required"
        }
        self.assertEqual(
            set(self.catalog["subjects"]), scoped
        )
        provider = self.seed["providers"][0]
        self.assertEqual("1.1", self.catalog["schema_version"])
        self.assertEqual(provider["authority_id"], self.catalog["authority_id"])
        self.assertEqual(provider["provider_id"], self.catalog["provider_id"])
        included_subjects = {
            subject_id
            for source in self.catalog["discovered_sources"].values()
            if source["disposition"] == "included"
            for subject_id in source["subject_ids"]
        }
        self.assertEqual(set(self.catalog["subjects"]), included_subjects)
        for item in self.scope["subjects"]:
            if item["evidence_class"] == "official-provider-required":
                self.assertEqual("blocked", item["expected_disposition"])
                self.assertEqual(["gromacs-docs"], item["provider_input_ids"])
            else:
                self.assertEqual([], item["provider_input_ids"])
            for origin in item["origin_refs"]:
                self.assertEqual(origin["sha256"], digest(ROOT / origin["path"]))

    def test_tree_inventory_is_exact_and_path_complete(self) -> None:
        inventory = load(REFERENCES / "source-pack-inventory-gromacs.json")
        self.assertTrue(SHA1.fullmatch(inventory["commit_id"]))
        self.assertTrue(SHA1.fullmatch(inventory["root_tree_object_id"]))
        paths = [item["path"] for item in inventory["entries"]]
        self.assertEqual(inventory["entry_count"], len(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(paths, sorted(paths))
        self.assertTrue(any(path.startswith("docs/") for path in paths))

    def test_lifecycle_ceiling_stays_blocked(self) -> None:
        proposal = load(REFERENCES / "source-pack-authority-proposal.json")
        self.assertEqual("none", proposal["lifecycle_effect"])
        self.assertTrue(
            all(item["provider_class"] == "software" for item in proposal["authorities"])
        )
        self.assertEqual("blocked", self.seed["status_ceiling"])


if __name__ == "__main__":
    unittest.main()
