#!/usr/bin/env python3
"""Offline tests for the CP2K production-pack catalog generator."""

from __future__ import annotations

import copy
import hashlib
import unittest
from unittest.mock import patch

import sync_source_pack_catalog as catalog


class Cp2kSourcePackCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.legacy = catalog.build_legacy_projection_inputs()
        cls.catalogs = catalog.build_catalogs(cls.legacy)
        catalog.validate_catalogs(cls.catalogs)
        cls.seed = catalog.build_seed(cls.catalogs)

    def test_manual_discovery_universe_is_exact_partition(self) -> None:
        manual = self.catalogs["manual"]
        included = {
            source_id
            for source_id, item in manual["discovered_sources"].items()
            if item["disposition"] == "included"
        }
        excluded = {
            source_id
            for source_id, item in manual["discovered_sources"].items()
            if item["disposition"] == "excluded"
        }
        self.assertEqual(len(included), 86)
        self.assertEqual(len(excluded), 2860)
        self.assertFalse(included & excluded)
        self.assertEqual(len(included | excluded), 2946)
        self.assertTrue(manual["upstream_universe_complete"])

    def test_raw_and_derived_identities_are_not_confused(self) -> None:
        manual = self.catalogs["manual"]
        for source in manual["discovered_sources"].values():
            if source["disposition"] != "included":
                continue
            self.assertEqual(
                source["content"]["content_mode"], "external-content"
            )
            self.assertTrue(source["content"]["locator"].endswith(".html"))
            identity = source["content"]["receipt"]
            self.assertGreater(identity["raw_bytes"], 0)
            self.assertEqual(len(identity["raw_sha256"]), 64)
            for sliced in source["selectors"]:
                self.assertEqual(sliced["layer"], "raw-source")
                self.assertEqual(
                    sliced["selected_identity"]["sha256"],
                    identity["raw_sha256"],
                )
                self.assertEqual(
                    sliced["selected_identity"]["bytes"],
                    identity["raw_bytes"],
                )

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
            declared = set(provider["subjects"])
            sliced = {
                subject_id
                for source in provider["discovered_sources"].values()
                if source["disposition"] == "included"
                for sliced in source["selectors"]
                for subject_id in sliced["subject_ids"]
            }
            self.assertEqual(declared, sliced)
            for subject_id in declared:
                self.assertIn(subject_id, scope)
                self.assertIn(
                    provider_id, scope[subject_id]["provider_input_ids"]
                )

    def test_v11_outputs_are_policy_free_and_self_identified(self) -> None:
        for name in ("manual", "release"):
            generated = self.catalogs[name]
            self.assertEqual(generated["schema_version"], "1.1")
            self.assertFalse(
                {"license", "sources", "reviewed_exclusions"} & set(generated)
            )
            processor = generated["discovery_processor"]
            self.assertEqual(
                processor["input_sha256"],
                generated["inventory_identity"]["sha256"],
            )
            self.assertEqual(
                processor["output_sha256"],
                hashlib.sha256(
                    catalog.canonical_projection_bytes(
                        generated["discovered_sources"]
                    )
                ).hexdigest(),
            )

    def test_exact_version_exclusion_locator_is_preserved(self) -> None:
        manual = self.catalogs["manual"]
        excluded = [
            source
            for source in manual["discovered_sources"].values()
            if source["disposition"] == "excluded"
        ]
        self.assertEqual(len(excluded), 2860)
        self.assertTrue(
            all(
                source["content"]["locator"].startswith(
                    "https://manual.cp2k.org/cp2k-2026_2-branch/"
                )
                for source in excluded
            )
        )

        mutated = copy.deepcopy(self.catalogs)
        mutated["manual"]["discovery_processor"]["output_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            ValueError, "discovery output identity mismatch"
        ):
            catalog.validate_catalogs(mutated)

    def test_scope_has_no_legacy_official_path_dependency(self) -> None:
        for subject in self.catalogs["scope"]["subjects"]:
            for origin in subject["origin_refs"]:
                self.assertNotIn("/official-", origin["path"])

    def test_seed_has_strict_v11_identity_closure(self) -> None:
        seed = self.seed
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
        expected_hashes = {
            catalog.OUTPUTS[name].relative_to(catalog.REPO_ROOT).as_posix():
            hashlib.sha256(
                catalog.canonical_v11_json_bytes(self.catalogs[name])
            ).hexdigest()
            for name in ("manual", "release", "scope")
        }
        refs = [
            seed["scope_catalog_ref"],
            *(provider["source_ref"] for provider in seed["providers"]),
        ]
        self.assertEqual(
            {item["path"]: item["sha256"] for item in refs},
            expected_hashes,
        )

    def test_check_mode_is_offline(self) -> None:
        with patch.object(
            catalog, "refresh_external_identities"
        ) as refresh:
            result = catalog.synchronize(check=True, refresh=False)
        self.assertEqual(result, 0)
        refresh.assert_not_called()

    def test_checked_in_bytes_match_every_managed_output(self) -> None:
        outputs = {**self.catalogs, "seed": self.seed}
        for name, path in catalog.OUTPUTS.items():
            with self.subTest(name=name):
                self.assertEqual(
                    path.read_bytes(),
                    catalog.canonical_v11_json_bytes(outputs[name]),
                )


if __name__ == "__main__":
    unittest.main()
