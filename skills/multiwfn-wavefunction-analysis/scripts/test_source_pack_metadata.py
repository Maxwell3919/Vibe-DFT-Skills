#!/usr/bin/env python3
"""Offline integrity tests for multiwfn-wavefunction-analysis source-pack inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCES = SKILL_ROOT / "references"
TOOLS = str(ROOT / "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import validate_contract  # noqa: E402


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
        self.seed = load(self.seed_path)
        self.scope = load(self.scope_path)
        self.catalog_paths = [
            ROOT / provider["source_ref"]["path"]
            for provider in self.seed["providers"]
        ]
        self.catalogs = [load(path) for path in self.catalog_paths]

    def test_strict_schemas(self) -> None:
        pairs = [
            ("official-document-pack-seed@1.0", self.seed_path),
            ("official-document-scope-catalog@1.0", self.scope_path),
        ]
        pairs.extend(
            ("official-document-source-catalog@1.1", path)
            for path in self.catalog_paths
        )
        contracts = validate_contract.load_catalog(ROOT / "contracts")
        for selector, instance_path in pairs:
            contract = contracts.resolve(selector)
            errors = list(
                Draft202012Validator(
                    contract.schema,
                    registry=contracts.registry,
                    format_checker=validate_contract.FORMAT_CHECKER,
                ).iter_errors(load(instance_path))
            )
            self.assertEqual([], [error.message for error in errors])

    def test_seed_hashes_are_skill_local_and_exact(self) -> None:
        refs = [self.seed["scope_catalog_ref"]]
        refs.extend(provider["source_ref"] for provider in self.seed["providers"])
        for item in refs:
            path = ROOT / item["path"]
            path.resolve().relative_to(SKILL_ROOT.resolve())
            self.assertFalse(path.is_symlink())
            self.assertEqual(item["sha256"], digest(path))

    def test_semantic_scope_and_origins_are_closed(self) -> None:
        expected = {
            item["subject_id"]
            for item in self.scope["subjects"]
            if item["evidence_class"] == "official-provider-required"
        }
        cataloged = {
            subject_id
            for catalog in self.catalogs
            for subject_id in catalog["subjects"]
        }
        self.assertEqual(expected, cataloged)
        provider_ids = {
            provider["input_id"] for provider in self.seed["providers"]
        }
        for item in self.scope["subjects"]:
            if item["evidence_class"] == "official-provider-required":
                self.assertTrue(item["provider_input_ids"])
                self.assertLessEqual(set(item["provider_input_ids"]), provider_ids)
            else:
                self.assertEqual([], item["provider_input_ids"])
            for origin in item["origin_refs"]:
                self.assertEqual(origin["sha256"], digest(ROOT / origin["path"]))

    def test_actual_sources_are_external_receipts_only(self) -> None:
        for catalog in self.catalogs:
            for source in catalog["discovered_sources"].values():
                if source["disposition"] != "included":
                    continue
                content = source["content"]
                self.assertEqual("external-content", content["content_mode"])
                receipt = content["receipt"]
                for selector in source["selectors"]:
                    if selector["kind"] == "whole-source":
                        self.assertEqual("*", selector["value"])
                    self.assertEqual(
                        selector["selected_identity"],
                        {
                            "sha256": receipt["raw_sha256"],
                            "bytes": receipt["raw_bytes"],
                        },
                    )

    def test_inventory_and_lifecycle_boundaries(self) -> None:
        proposal = load(REFERENCES / "source-pack-authority-proposal.json")
        self.assertEqual("none", proposal["lifecycle_effect"])
        self.assertEqual("blocked", self.seed["status_ceiling"])
        for authority in proposal["authorities"]:
            self.assertEqual("software", authority["provider_class"])
            self.assertEqual([], authority["content_policy"]["allowed_query_urls"])
            self.assertEqual("forbidden", authority["content_policy"]["query_policy"])
            self.assertEqual("forbidden", authority["redistribution_policy"]["bundle_content"])
            self.assertEqual("none", authority["consumer_binding"]["claim_effect"])

        inventory = load(REFERENCES / "source-pack-inventory-multiwfn.json")
        manual = next(item for item in inventory["documents"] if item["document_id"] == "multiwfn-manual-2026-7-10")
        self.assertEqual(36_639_888, manual["bytes"])
        self.assertEqual(1_150, manual["pages"])
        self.assertEqual("81de19c5c9d0fcbdcc03705b94301ab08e0bd2455e81db0e31651ffcdab6bd37", manual["sha256"])
        authority = proposal["authorities"][0]
        self.assertEqual("known-restricted", authority["license_policy"]["status"])
        self.assertEqual({"runtime-only", "restricted"}, set(authority["redistribution_policy"]["allowed_values"]))


if __name__ == "__main__":
    unittest.main()
