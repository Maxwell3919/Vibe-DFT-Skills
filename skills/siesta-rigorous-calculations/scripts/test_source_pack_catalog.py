#!/usr/bin/env python3
"""Offline tests for the SIESTA production-pack catalog generator."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import sync_source_pack_catalog as catalog


class SiestaSourcePackCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalogs = catalog.build_catalogs()
        catalog.validate_catalogs(cls.catalogs)

    @staticmethod
    def included_sources(provider: dict[str, object]) -> list[dict[str, object]]:
        return [
            source
            for source in provider["discovered_sources"].values()
            if source["disposition"] == "included"
        ]

    def test_release_inventory_is_exact_bounded_47_plus_6(self) -> None:
        release = self.catalogs["release"]
        sources = self.included_sources(release)
        self.assertEqual(release["schema_version"], "1.1")
        self.assertEqual(len(sources), 53)
        self.assertFalse(release["upstream_universe_complete"])
        self.assertEqual(
            sum(
                source["content"]["receipt"]["raw_bytes"]
                for source in sources
            ),
            717382,
        )
        for source in sources:
            content = source["content"]
            self.assertEqual(content["content_mode"], "external-content")
            self.assertIn("/-/raw/", content["locator"])
            self.assertNotIn("/-/blob/", content["locator"])
            self.assertNotIn("#", content["locator"])
            self.assertEqual(len(source["selectors"]), 1)
            self.assertEqual(source["selectors"][0]["kind"], "whole-source")
            self.assertEqual(source["selectors"][0]["layer"], "raw-source")
            self.assertEqual(
                source["selectors"][0]["selected_identity"],
                {
                    "sha256": content["receipt"]["raw_sha256"],
                    "bytes": content["receipt"]["raw_bytes"],
                },
            )

    def test_fdf_subjects_are_collision_safe_and_complete(self) -> None:
        subjects = self.catalogs["release"]["subjects"]
        ids = set(subjects)
        fdf_ids = {sid for sid in ids if sid.startswith("siesta.fdf.")}
        self.assertEqual(len(fdf_ids), 572)
        mmcutoff = [
            item for item in subjects.values() if "MM.Cutoff" in item["title"]
        ]
        self.assertEqual(len(mmcutoff), 2)
        source_ids = set(self.catalogs["release"]["discovered_sources"])
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
            declared = set(provider["subjects"])
            sliced = {
                subject_id
                for source in self.included_sources(provider)
                for selector in source["selectors"]
                for subject_id in selector["subject_ids"]
            }
            self.assertEqual(declared, sliced)
            for subject_id in declared:
                self.assertIn(subject_id, scope)
                self.assertIn(
                    provider_id, scope[subject_id]["provider_input_ids"]
                )

    def test_portal_and_release_are_policy_free_separate_technical_authorities(
        self,
    ) -> None:
        portal = self.catalogs["portal"]
        release = self.catalogs["release"]
        self.assertEqual(portal["authority_id"], "siesta-official-docs")
        self.assertEqual(
            release["authority_id"], "siesta-release-source-docs"
        )
        self.assertNotEqual(
            portal["authority_root"],
            release["authority_root"],
        )
        self.assertEqual(portal["version_scope"]["value"], "5.4")
        self.assertEqual(release["version_scope"]["value"], "5.4.2")
        self.assertNotIn("license", portal)
        self.assertNotIn("license", release)
        self.assertNotIn("review", " ".join(portal["limitations"]).lower())
        for provider in (portal, release):
            serialized = json.dumps(provider, ensure_ascii=False).lower()
            for policy_term in (
                "copyright",
                "licence",
                "license",
                "non-commercial",
                "redistribut",
            ):
                self.assertNotIn(policy_term, serialized)

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
        self.assertEqual(
            {
                item["source_ref"]["sha256"]
                for item in seed["providers"]
            },
            {
                catalog.sha256_bytes(
                    catalog.output_json_bytes(name, self.catalogs[name])
                )
                for name in ("portal", "release")
            },
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
