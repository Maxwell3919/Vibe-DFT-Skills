#!/usr/bin/env python3
"""Offline tests for the CP2K production-pack catalog generator."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import sync_source_pack_catalog as catalog


class Cp2kSourcePackCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalogs = catalog.build_catalogs()
        catalog.validate_catalogs(cls.catalogs)

    def test_manual_discovery_universe_is_exact_partition(self) -> None:
        manual = self.catalogs["manual"]
        included = {item["source_id"] for item in manual["sources"]}
        excluded = {
            item["source_id"] for item in manual["reviewed_exclusions"]
        }
        self.assertEqual(len(included), 86)
        self.assertEqual(len(excluded), 2860)
        self.assertFalse(included & excluded)
        self.assertEqual(len(included | excluded), 2946)
        self.assertTrue(manual["upstream_universe_complete"])

    def test_raw_and_derived_identities_are_not_confused(self) -> None:
        manual = self.catalogs["manual"]
        for source in manual["sources"]:
            self.assertIn("external_identity", source)
            self.assertNotIn("content_ref", source)
            self.assertTrue(source["locator"].endswith(".html"))
            identity = source["external_identity"]
            self.assertGreater(identity["raw_bytes"], 0)
            self.assertEqual(len(identity["raw_sha256"]), 64)
            for sliced in source["slices"]:
                self.assertEqual(
                    sliced["selector"]["layer"], "raw-source"
                )
                self.assertIn("external_receipt", sliced)
                self.assertNotIn("content_ref", sliced)

    def test_scope_is_semantic_not_one_subject_per_file(self) -> None:
        subjects = self.catalogs["scope"]["subjects"]
        official = [
            item
            for item in subjects
            if item["evidence_class"] == "official-provider-required"
        ]
        local = [
            item
            for item in subjects
            if item["evidence_class"] != "official-provider-required"
        ]
        ids = {item["subject_id"] for item in official}
        self.assertTrue(
            {f"cp2k.task.{name}" for name in (
                "static", "relax", "md", "bands", "dos", "phonon", "neb",
                "generic",
            )}.issubset(ids)
        )
        self.assertEqual(
            len([sid for sid in ids if sid.startswith("cp2k.method.")]),
            14,
        )
        self.assertEqual(
            len([sid for sid in ids if sid.startswith("cp2k.topic.")]),
            86,
        )
        self.assertTrue(
            any(
                sid.startswith("cp2k.input-keyword.")
                for sid in ids
            )
        )
        self.assertTrue(
            any(
                item["evidence_class"] == "scientific-methodology"
                for item in local
            )
        )
        self.assertTrue(
            any(
                item["evidence_class"] == "deterministic-tool-behavior"
                for item in local
            )
        )

    def test_provider_subjects_resolve_to_scope_and_slices(self) -> None:
        scope = {
            item["subject_id"]: item
            for item in self.catalogs["scope"]["subjects"]
        }
        for catalog_name, provider_id in (
            ("manual", "cp2k-manual"),
            ("release", "cp2k-release"),
        ):
            provider = self.catalogs[catalog_name]
            declared = {item["subject_id"] for item in provider["subjects"]}
            sliced = {
                subject_id
                for source in provider["sources"]
                for sliced in source["slices"]
                for subject_id in sliced["subject_ids"]
            }
            self.assertEqual(declared, sliced)
            for subject_id in declared:
                self.assertIn(subject_id, scope)
                self.assertIn(
                    provider_id, scope[subject_id]["provider_input_ids"]
                )

    def test_manual_license_cannot_claim_unknown_obligations(self) -> None:
        license_record = self.catalogs["manual"]["license"]
        self.assertIsNone(license_record["identity"]["identifier"])
        self.assertEqual(
            license_record["identity"]["verification"], "unknown"
        )
        self.assertEqual(license_record["assessment"], "unresolved")
        self.assertNotIn("embedded-open", license_record["allowed_storage_modes"])

    def test_scope_has_no_legacy_official_path_dependency(self) -> None:
        for subject in self.catalogs["scope"]["subjects"]:
            for origin in subject["origin_refs"]:
                self.assertNotIn("/official-", origin["path"])

    def test_seed_and_local_proposal_preserve_central_ceiling(self) -> None:
        seed, proposal = catalog.build_seed_and_proposal(self.catalogs)
        self.assertEqual(seed["status_ceiling"], "partial")
        self.assertEqual(seed["blockers"], [])
        self.assertEqual(
            {
                (
                    item["input_id"],
                    item["authority_id"],
                    item["provider_id"],
                )
                for item in seed["providers"]
            },
            {
                ("cp2k-manual", "cp2k-official-manual", "cp2k"),
                ("cp2k-release", "cp2k-release-source-docs", "cp2k"),
            },
        )
        self.assertEqual(
            proposal["proposal_status"], "skill-local-non-authoritative"
        )
        self.assertTrue(
            all(
                item["consumer_binding"]["claim_ceiling"]
                == "registered-skill-scope"
                for item in proposal["providers"]
            )
        )

    def test_check_mode_is_offline(self) -> None:
        with patch.object(
            catalog, "refresh_external_identities"
        ) as refresh:
            result = catalog.synchronize(check=True, refresh=False)
        self.assertEqual(result, 0)
        refresh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
