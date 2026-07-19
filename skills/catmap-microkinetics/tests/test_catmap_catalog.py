from __future__ import annotations

import contextlib
import importlib.machinery
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import catmap_catalog as catalog_cli


class CatmapCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.recipe_catalog, cls.sources = catalog_cli.load_data()
        cls.capabilities = catalog_cli.flatten_capabilities(cls.catalog)
        cls.recipes = catalog_cli.flatten_recipes(cls.recipe_catalog)
        catalog_cli.validate_source_links(cls.capabilities, cls.recipes, cls.sources)

    def test_pinned_catalog_identity_and_coverage(self) -> None:
        self.assertEqual(self.catalog["provider_target"], "CatMAP v0.4.1")
        self.assertEqual(self.catalog["evidence_state"], "official-feature")
        self.assertGreaterEqual(len(self.catalog["modules"]), 35)
        self.assertGreaterEqual(len(self.catalog["features"]), 15)
        self.assertEqual(len(self.capabilities), len(set(self.capabilities)))
        self.assertIn("module.catmap.solvers.numbers_solver", self.capabilities)
        self.assertIn("feature.cli.import", self.capabilities)
        self.assertIn("feature.analysis.matrix-map", self.capabilities)

    def test_official_source_links_are_complete_and_first_party_led(self) -> None:
        source_ids = {item["id"] for item in self.sources["sources"]}
        self.assertIn("CAT-REL-041", source_ids)
        self.assertIn("CAT-CLI-041", source_ids)
        self.assertIn("CAT-TUT-MODEL", source_ids)
        self.assertIn("CAT-PAPER-2015", source_ids)
        numbers_source = next(
            item
            for item in self.sources["sources"]
            if item["id"] == "CAT-PAPER-NUMBERS"
        )
        self.assertEqual(numbers_source["url"], "https://doi.org/10.1002/jcc.27263")
        for record in [*self.capabilities.values(), *self.recipes.values()]:
            self.assertTrue(record["source_ids"])
            self.assertTrue(set(record["source_ids"]) <= source_ids)

    def test_recipe_states_separate_calls_from_native_validation(self) -> None:
        self.assertEqual(self.recipe_catalog["native_validation_state"], "native-not-run")
        self.assertGreaterEqual(len(self.recipes), 12)
        self.assertEqual(
            self.recipes["recipe.run-mkm-model"]["calls"],
            [
                "from catmap import ReactionModel",
                "model = ReactionModel(setup_file='model.mkm')",
                "model.run()",
                "python mkm_job.py",
            ],
        )
        self.assertEqual(
            self.recipes["recipe.inspect-setup-interactively"]["calls"][0],
            "catmap import model.mkm",
        )
        self.assertEqual(
            self.recipes["recipe.render-reaction-graph"]["calls"],
            ["catmap graphviz model.mkm"],
        )
        self.assertEqual(
            self.recipes["recipe.first-order-interactions"]["recipe_state"],
            "feature-only",
        )
        self.assertEqual(
            self.recipes["recipe.electrochemistry"]["recipe_state"], "feature-only"
        )

    def test_documented_plan_never_executes_or_authorizes(self) -> None:
        report, exit_code = catalog_cli.plan_report(
            self.recipes, "recipe.run-mkm-model"
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "documentation-plan")
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["native_execution_performed"])
        self.assertEqual(report["native_validation_state"], "native-not-run")
        self.assertIn("setup/log/Python", report["trust_boundary"])
        self.assertEqual(
            report["guard_handoff"],
            "Run catmap_guard.py only on the declarative JSON interchange.",
        )

    def test_feature_only_modes_fail_closed(self) -> None:
        for recipe_id in (
            "recipe.first-order-interactions",
            "recipe.electrochemistry",
        ):
            with self.subTest(recipe=recipe_id):
                report, exit_code = catalog_cli.plan_report(self.recipes, recipe_id)
                self.assertEqual(exit_code, 3)
                self.assertEqual(report["status"], "blocked")
                self.assertEqual(
                    report["finding"], "CATMAP_FEATURE_ONLY_NO_VALIDATED_RECIPE"
                )
                self.assertFalse(report["execution_authorized"])

    def test_search_and_group_listing_are_machine_readable(self) -> None:
        result = catalog_cli.search_report(self.capabilities, "steady state")
        ids = {item["id"] for item in result["capabilities"]}
        self.assertIn("module.catmap.solvers.steady_state_solver", ids)
        listed = catalog_cli.list_report(self.capabilities, "analysis", None)
        self.assertGreaterEqual(listed["count"], 5)
        self.assertEqual(
            {item["kind"] for item in listed["capabilities"]},
            {"module", "feature"},
        )
        groups = catalog_cli.groups_report(self.capabilities)
        self.assertTrue(any(item["group"] == "solving" for item in groups["groups"]))

    def test_probe_uses_metadata_only_and_never_imports_or_executes(self) -> None:
        fake_spec = importlib.machinery.ModuleSpec("catmap", loader=None)

        def fake_version(name: str) -> str:
            if name == "python-catmap":
                return "0.3.1"
            raise catalog_cli.importlib.metadata.PackageNotFoundError(name)

        with (
            mock.patch.object(catalog_cli.shutil, "which", return_value="/opt/bin/catmap"),
            mock.patch.object(catalog_cli.importlib.util, "find_spec", return_value=fake_spec),
            mock.patch.object(catalog_cli.importlib.metadata, "version", side_effect=fake_version),
        ):
            report = catalog_cli.probe_report()
        self.assertEqual(report["status"], "available-unverified")
        self.assertEqual(report["executable"], "/opt/bin/catmap")
        self.assertEqual(report["distributions"]["python-catmap"], "0.3.1")
        self.assertTrue(report["module_discoverable"])
        self.assertFalse(report["module_imported"])
        self.assertFalse(report["help_or_version_executed"])
        self.assertFalse(report["native_execution_performed"])
        self.assertEqual(report["scientific_capability_claim"], "none")

    def test_cli_outputs_json_and_blocking_exit_code(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            exit_code = catalog_cli.main(["plan", "recipe.electrochemistry"])
        self.assertEqual(exit_code, 3)
        report = json.loads(stream.getvalue())
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["native_execution_performed"])

    def test_calling_reference_and_skill_route_exist(self) -> None:
        calling = ROOT / "references" / "calling-and-recipes.md"
        self.assertTrue(calling.is_file())
        text = calling.read_text(encoding="utf-8")
        for token in (
            "catmap import model.mkm",
            "catmap graphviz model.mkm",
            "ReactionModel(setup_file='model.mkm')",
            "dft-postprocess",
            "native-not-run",
        ):
            self.assertIn(token, text)
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/catmap_catalog.py", skill)
        self.assertIn("calling-and-recipes.md", skill)


if __name__ == "__main__":
    unittest.main()
