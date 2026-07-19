from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lobster_catalog as catalog_cli


class LobsterCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.recipe_catalog, cls.sources = catalog_cli.load_data()
        cls.capabilities = catalog_cli.flatten_capabilities(cls.catalog)
        cls.recipes = catalog_cli.flatten_recipes(cls.recipe_catalog)
        catalog_cli.validate_source_links(cls.capabilities, cls.recipes, cls.sources)

    def test_pinned_provider_and_public_capability_coverage(self) -> None:
        self.assertEqual(self.catalog["provider_target"], "LOBSTER 5.1.1")
        self.assertGreaterEqual(len(self.capabilities), 15)
        for record_id in (
            "provider.parent.vasp",
            "provider.parent.qe",
            "analysis.projected-cohp",
            "analysis.projected-coop",
            "analysis.projected-dos",
            "quality.spilling",
            "native.execution",
            "postprocess.lobsterpy",
        ):
            self.assertIn(record_id, self.capabilities)
        self.assertEqual(
            self.capabilities["native.execution"]["evidence_state"],
            "manual-required",
        )

    def test_official_sources_include_release_license_science_and_companion(self) -> None:
        source_ids = {item["id"] for item in self.sources["sources"]}
        self.assertIn("LOB-DOWNLOAD-511", source_ids)
        self.assertIn("LOB-LICENSE-511", source_ids)
        self.assertIn("LOB-PROJECTION-OVERVIEW", source_ids)
        self.assertIn("LOB-FAQ", source_ids)
        self.assertIn("LOB-PAPER-2020", source_ids)
        self.assertIn("LOB-LOBSTERPY-CLI", source_ids)
        license_source = next(
            item for item in self.sources["sources"] if item["id"] == "LOB-LICENSE-511"
        )
        self.assertIn("fileID=18", license_source["url"])
        for record in [*self.capabilities.values(), *self.recipes.values()]:
            self.assertTrue(set(record["source_ids"]) <= source_ids)

    def test_blocked_native_recipes_contain_no_invented_calls(self) -> None:
        blocked_states = {"manual-required", "design-only"}
        blocked = [
            recipe
            for recipe in self.recipes.values()
            if recipe["recipe_state"] in blocked_states
        ]
        self.assertGreaterEqual(len(blocked), 6)
        self.assertTrue(all(recipe["calls"] == [] for recipe in blocked))
        self.assertEqual(
            self.recipes["recipe.native-run"]["recipe_state"], "manual-required"
        )
        self.assertEqual(
            self.recipes["recipe.qe-parent-handoff"]["recipe_state"], "design-only"
        )

    def test_native_and_vasp_plans_fail_closed_for_manual(self) -> None:
        for recipe_id in (
            "recipe.native-run",
            "recipe.vasp-parent-handoff",
            "recipe.cohp-analysis",
            "recipe.coop-analysis",
            "recipe.projected-dos",
        ):
            with self.subTest(recipe=recipe_id):
                report, exit_code = catalog_cli.plan_report(self.recipes, recipe_id)
                self.assertEqual(exit_code, 3)
                self.assertEqual(report["status"], "blocked")
                self.assertEqual(
                    report["finding"], "LOBSTER_AUTHORIZED_MANUAL_REQUIRED"
                )
                self.assertFalse(report["execution_authorized"])
                self.assertFalse(report["native_execution_performed"])
                self.assertEqual(report["claim_ceiling"], "no_positive_claim")

    def test_qe_plan_is_design_only(self) -> None:
        report, exit_code = catalog_cli.plan_report(
            self.recipes, "recipe.qe-parent-handoff"
        )
        self.assertEqual(exit_code, 3)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["finding"], "LOBSTER_PROVIDER_ROUTE_DESIGN_ONLY")
        self.assertFalse(report["execution_authorized"])

    def test_local_guard_and_companion_are_documentation_plans_only(self) -> None:
        for recipe_id in (
            "recipe.declarative-audit",
            "recipe.lobsterpy-description",
            "recipe.dft-postprocess-handoff",
        ):
            with self.subTest(recipe=recipe_id):
                report, exit_code = catalog_cli.plan_report(self.recipes, recipe_id)
                self.assertEqual(exit_code, 0)
                self.assertEqual(report["status"], "documentation-plan")
                self.assertFalse(report["execution_authorized"])
                self.assertFalse(report["native_execution_performed"])

    def test_companion_call_is_exact_but_not_native_authority(self) -> None:
        recipe = self.recipes["recipe.lobsterpy-description"]
        self.assertEqual(
            recipe["calls"],
            [
                "lobsterpy description -fcharge CHARGE.lobster -fcohp COHPCAR.lobster -ficohp ICOHPLIST.lobster -fstruct POSCAR.lobster -fjson summary.json"
            ],
        )
        capability = self.capabilities["postprocess.lobsterpy"]
        self.assertIn("LobsterPy calls only", capability["call_contract"])

    def test_search_and_group_reports_are_machine_readable(self) -> None:
        result = catalog_cli.search_report(self.capabilities, "projected COHP")
        ids = {item["id"] for item in result["capabilities"]}
        self.assertIn("analysis.projected-cohp", ids)
        listed = catalog_cli.list_report(
            self.capabilities, "native-interface", "manual-required"
        )
        self.assertEqual(listed["count"], 3)
        groups = catalog_cli.groups_report(self.capabilities)
        self.assertTrue(
            any(item["group"] == "projection-quality" for item in groups["groups"])
        )

    def test_probe_never_runs_help_version_or_binary(self) -> None:
        mapping = {
            "lobster": "/opt/private/lobster",
            "lobster-5.1.1": None,
            "lobster-5.1.0": None,
        }
        with mock.patch.object(
            catalog_cli.shutil, "which", side_effect=lambda name: mapping[name]
        ):
            report = catalog_cli.probe_report()
        self.assertEqual(report["status"], "available-unverified")
        self.assertEqual(report["found_candidates"], {"lobster": "/opt/private/lobster"})
        self.assertFalse(report["executable_name_authoritative"])
        self.assertFalse(report["help_or_version_executed"])
        self.assertFalse(report["native_execution_performed"])
        self.assertFalse(report["authorization_established"])
        self.assertFalse(report["provider_version_established"])
        self.assertEqual(report["scientific_capability_claim"], "none")

    def test_cli_outputs_json_and_manual_block_exit(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            exit_code = catalog_cli.main(["plan", "recipe.native-run"])
        self.assertEqual(exit_code, 3)
        report = json.loads(stream.getvalue())
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["finding"], "LOBSTER_AUTHORIZED_MANUAL_REQUIRED")

    def test_calling_reference_and_skill_routes_exist(self) -> None:
        calling = ROOT / "references" / "calling-and-recipes.md"
        self.assertTrue(calling.is_file())
        text = calling.read_text(encoding="utf-8")
        for token in (
            "manual-required",
            "vasp-rigorous-calculations",
            "qe-rigorous-calculations",
            "dft-postprocess",
            "native-not-run",
            "lobsterpy description",
        ):
            self.assertIn(token, text)
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/lobster_catalog.py", skill)
        self.assertIn("calling-and-recipes.md", skill)


if __name__ == "__main__":
    unittest.main()
