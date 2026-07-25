#!/usr/bin/env python3
"""Offline tests for the postprocess source-pack extractor."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker


SCRIPT = Path(__file__).with_name("sync_source_pack_catalog.py")
SPEC = importlib.util.spec_from_file_location("postprocess_source_pack", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ROOT = MODULE.repository_root()
import validate_contract  # noqa: E402


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

    def test_dynamic_surface_sets_are_exact(self) -> None:
        catalog = MODULE.scope_catalog(ROOT)
        subjects = {item["subject_id"]: item for item in catalog["subjects"]}
        registry = MODULE.observable_registry(ROOT)
        expected_observables = {
            f"observable:{item}" for item in registry["observables"]
        }
        expected_backends = {f"backend:{item}" for item in registry["backends"]}
        expected_routes = {
            f"route:{observable_id}:{code}:{MODULE.safe_id(backend_id)}"
            for observable_id, observable in registry["observables"].items()
            for code, group in observable["codes"].items()
            for backend_id in group["backend_routes"]
        }
        expected_cli = {
            f"cli:{item}"
            for item in MODULE.literal_subcommands(
                ROOT / "skills" / MODULE.SKILL_ID / "scripts" / "dftpost" / "cli.py"
            )
        }
        external, packages = MODULE.capability_inventory(ROOT)
        expected_capabilities = {
            *(f"capability:external:{MODULE.safe_id(item)}" for item in external),
            *(f"capability:python:{MODULE.safe_id(item)}" for item in packages),
        }
        self.assertEqual(
            {item for item in subjects if item.startswith("observable:")},
            expected_observables,
        )
        self.assertEqual(
            {item for item in subjects if item.startswith("backend:")},
            expected_backends,
        )
        self.assertEqual(
            {item for item in subjects if item.startswith("route:")},
            expected_routes,
        )
        self.assertEqual(
            {item for item in subjects if item.startswith("cli:")},
            expected_cli,
        )
        self.assertEqual(
            {item for item in subjects if item.startswith("capability:")},
            expected_capabilities,
        )
        self.assertEqual(len(expected_observables), 8)
        self.assertEqual(len(expected_routes), 77)
        self.assertEqual(len(expected_cli), 30)
        self.assertEqual(len(expected_capabilities), 37)
        self.assertEqual(len(expected_backends), len(registry["backends"]))

    def test_route_maturity_is_copied_without_promotion(self) -> None:
        subjects = {
            item["subject_id"]: item
            for item in MODULE.scope_catalog(ROOT)["subjects"]
        }
        registry = MODULE.observable_registry(ROOT)
        for observable_id, observable in registry["observables"].items():
            for code, group in observable["codes"].items():
                for backend_id, route in group["backend_routes"].items():
                    subject = subjects[
                        f"route:{observable_id}:{code}:{MODULE.safe_id(backend_id)}"
                    ]
                    self.assertIn(repr(route["maturity"]), subject["statement"])
                    self.assertEqual(
                        subject["expected_disposition"],
                        (
                            "excluded"
                            if route["maturity"] == "design-only"
                            else "not-applicable"
                        ),
                    )

    def test_cp2k_catalog_exactly_partitions_curated_manifest(self) -> None:
        manifest_path = (
            ROOT
            / "skills"
            / "cp2k-rigorous-calculations"
            / "references"
            / "official-manual"
            / "manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = {
            item["source_path"].lower().replace("/", "."): item
            for item in manifest["pages"].values()
        }
        catalog = MODULE.provider_catalogs(ROOT)["cp2k-2026-2-postprocess"]
        included = {
            source_id: item
            for source_id, item in catalog["discovered_sources"].items()
            if item["disposition"] == "included"
        }
        excluded = {
            source_id: item
            for source_id, item in catalog["discovered_sources"].items()
            if item["disposition"] == "excluded"
        }

        self.assertFalse(catalog["upstream_universe_complete"])
        self.assertEqual(set(included) & set(excluded), set())
        self.assertEqual(set(included) | set(excluded), set(expected))
        self.assertEqual(len(included), 3)
        self.assertEqual(len(excluded), len(expected) - 3)

        expected_included = {
            "cp2k_input.force_eval.dft.print.band_structure.html",
            "cp2k_input.force_eval.dft.print.dos.html",
            "cp2k_input.force_eval.dft.print.e_density_cube.html",
        }
        self.assertEqual(set(included), expected_included)
        for source_id, source in included.items():
            page = expected[source_id]
            self.assertEqual(source["content"]["locator"], page["source_url"])
            self.assertEqual(
                source["content"]["receipt"]["raw_sha256"],
                page["raw_sha256"],
            )
            self.assertEqual(
                source["content"]["receipt"]["raw_bytes"],
                page["raw_bytes"],
            )
            self.assertEqual(len(source["selectors"]), 1)
            source_slice = source["selectors"][0]
            self.assertEqual(
                source_slice["subject_ids"],
                ["cp2k:postprocess-artifacts"],
            )
            self.assertEqual(
                source_slice["selected_identity"]["sha256"],
                page["raw_sha256"],
            )
            self.assertEqual(
                source_slice["selected_identity"]["bytes"],
                page["raw_bytes"],
            )

    def test_v11_catalogs_preserve_preimage_and_subject_closure(self) -> None:
        legacy_catalogs = MODULE.legacy_provider_catalogs(ROOT)
        catalogs = MODULE.provider_catalogs(ROOT)
        expected_subjects: dict[str, set[str]] = {}
        for subject_id, _kind, _statement, input_id, _disposition in (
            MODULE.PROVIDER_SUBJECTS
        ):
            expected_subjects.setdefault(input_id, set()).add(subject_id)

        self.assertEqual(set(catalogs), set(MODULE.PROVIDER_SPECS))
        for input_id, catalog in catalogs.items():
            with self.subTest(input_id=input_id):
                legacy_bytes = MODULE.canonical_json_bytes(
                    legacy_catalogs[input_id]
                )
                self.assertEqual(catalog["schema_version"], "1.1")
                self.assertNotIn("license", catalog)
                self.assertEqual(
                    catalog["inventory_identity"],
                    {
                        "sha256": MODULE.sha256_bytes(legacy_bytes),
                        "bytes": len(legacy_bytes),
                    },
                )
                self.assertEqual(
                    set(catalog["subjects"]),
                    expected_subjects[input_id],
                )
                for source in catalog["discovered_sources"].values():
                    if source["disposition"] != "included":
                        continue
                    selector_subjects = {
                        subject_id
                        for selector in source["selectors"]
                        for subject_id in selector["subject_ids"]
                    }
                    self.assertEqual(
                        selector_subjects,
                        set(source["subject_ids"]),
                    )
                    self.assertLessEqual(
                        selector_subjects,
                        set(catalog["subjects"]),
                    )

    def test_seed_hashes_close_over_generated_v11_catalogs(self) -> None:
        outputs = MODULE.build_outputs(ROOT)
        refs = ROOT / "skills" / MODULE.SKILL_ID / "references"
        seed_path = refs / "source-pack-seed.json"
        seed = json.loads(outputs[seed_path])
        scope_path = ROOT / seed["scope_catalog_ref"]["path"]
        self.assertEqual(
            seed["scope_catalog_ref"]["sha256"],
            MODULE.sha256_bytes(outputs[scope_path]),
        )
        for provider in seed["providers"]:
            source_path = ROOT / provider["source_ref"]["path"]
            self.assertEqual(
                provider["source_ref"]["sha256"],
                MODULE.sha256_bytes(outputs[source_path]),
            )
            catalog = json.loads(outputs[source_path])
            self.assertEqual(catalog["schema_version"], "1.1")

    def test_authority_proposal_covers_every_seed_provider(self) -> None:
        refs = ROOT / "skills" / MODULE.SKILL_ID / "references"
        seed = json.loads(
            (refs / "source-pack-seed.json").read_text(encoding="utf-8")
        )
        proposal = json.loads(
            (refs / "source-pack-authority-proposal.json").read_text(
                encoding="utf-8"
            )
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
        refs = ROOT / "skills" / MODULE.SKILL_ID / "references"
        checks = [
            (
                "official-document-pack-seed@1.0",
                refs / "source-pack-seed.json",
            ),
            (
                "official-document-scope-catalog@1.0",
                refs / "source-pack-scope.json",
            ),
        ]
        checks.extend(
            (
                "official-document-source-catalog@1.1",
                path,
            )
            for path in sorted((refs / "source-pack-inputs").glob("*.json"))
        )
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        for selector, value_path in checks:
            with self.subTest(path=value_path.name):
                contract = catalog.resolve(selector)
                value = json.loads(value_path.read_text(encoding="utf-8"))
                errors = sorted(
                    Draft202012Validator(
                        contract.schema,
                        registry=catalog.registry,
                        format_checker=FormatChecker(),
                    ).iter_errors(value),
                    key=lambda item: tuple(str(part) for part in item.absolute_path),
                )
                self.assertEqual([item.message for item in errors], [])


if __name__ == "__main__":
    unittest.main()
