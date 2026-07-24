#!/usr/bin/env python3
"""Offline tests for the SIESTA production-pack catalog generator."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import sync_source_pack_catalog as catalog


class SiestaSourcePackCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalogs = catalog.build_catalogs()
        catalog.validate_catalogs(cls.catalogs)

    def test_release_inventory_is_exact_bounded_47_plus_6(self) -> None:
        release = self.catalogs["release"]
        self.assertEqual(len(release["sources"]), 53)
        self.assertFalse(release["upstream_universe_complete"])
        self.assertEqual(
            sum(
                source["external_identity"]["raw_bytes"]
                for source in release["sources"]
            ),
            717382,
        )
        for source in release["sources"]:
            self.assertIn("/-/raw/", source["locator"])
            self.assertNotIn("/-/blob/", source["locator"])
            self.assertNotIn("#", source["locator"])
            self.assertIn("external_identity", source)
            self.assertNotIn("content_ref", source)

    def test_fdf_subjects_are_collision_safe_and_complete(self) -> None:
        ids = {
            item["subject_id"]
            for item in self.catalogs["release"]["subjects"]
        }
        fdf_ids = {sid for sid in ids if sid.startswith("siesta.fdf.")}
        self.assertEqual(len(fdf_ids), 572)
        mmcutoff = [
            item
            for item in self.catalogs["release"]["subjects"]
            if "MM.Cutoff" in item["title"]
        ]
        self.assertEqual(len(mmcutoff), 2)
        self.assertEqual(len({item["subject_id"] for item in mmcutoff}), 2)
        source_ids = {
            source["source_id"]
            for source in self.catalogs["release"]["sources"]
        }
        self.assertEqual(len(source_ids), 53)
        self.assertTrue(
            all(len(source_id) <= 200 for source_id in source_ids)
        )

    def test_scope_covers_tasks_keywords_outputs_and_local_claims(self) -> None:
        subjects = self.catalogs["scope"]["subjects"]
        ids = {item["subject_id"] for item in subjects}
        self.assertEqual(
            len([sid for sid in ids if sid.startswith("siesta.task.")]),
            11,
        )
        self.assertGreater(
            len(
                [
                    sid
                    for sid in ids
                    if sid.startswith("siesta.profile-keyword.")
                ]
            ),
            50,
        )
        self.assertEqual(
            len(
                [
                    sid
                    for sid in ids
                    if sid.startswith("siesta.profile-output.")
                ]
            ),
            2,
        )
        self.assertTrue(
            any(
                item["evidence_class"] == "scientific-methodology"
                for item in subjects
            )
        )
        self.assertTrue(
            any(
                item["evidence_class"] == "deterministic-tool-behavior"
                for item in subjects
            )
        )

    def test_provider_subjects_resolve_to_scope_and_slices(self) -> None:
        scope = {
            item["subject_id"]: item
            for item in self.catalogs["scope"]["subjects"]
        }
        for catalog_name, provider_id in (
            ("portal", "siesta-portal"),
            ("release", "siesta-release"),
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

    def test_portal_and_release_authority_and_license_remain_separate(self) -> None:
        portal_license = self.catalogs["portal"]["license"]
        release_license = self.catalogs["release"]["license"]
        self.assertEqual(
            portal_license["identity"]["identifier"],
            "CC-BY-NC-SA-4.0",
        )
        self.assertEqual(
            release_license["identity"]["identifier"], "GPL-3.0-only"
        )
        self.assertNotEqual(
            portal_license["official_terms_locator"],
            release_license["official_terms_locator"],
        )
        self.assertNotIn(
            "embedded-open", release_license["allowed_storage_modes"]
        )

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
                ("siesta-portal", "siesta-official-docs", "siesta"),
                (
                    "siesta-release",
                    "siesta-release-source-docs",
                    "siesta",
                ),
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
