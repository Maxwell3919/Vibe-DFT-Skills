from __future__ import annotations

import contextlib
import importlib.metadata
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import phonopy_catalog


class PhonopyCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.recipes = phonopy_catalog.load_data()

    def test_snapshot_and_complete_entrypoint_index(self) -> None:
        self.assertEqual(self.catalog["documentation_version"], "4.3.1")
        self.assertEqual(
            self.catalog["source_snapshot"]["tag_commit"],
            "baf530aed09071e1221b3c191918a168fc5f1d9b",
        )
        entrypoints = {item["id"] for item in self.catalog["entrypoints"]}
        self.assertEqual(len(entrypoints), 15)
        self.assertTrue(
            {
                "phonopy",
                "phonopy-init",
                "phonopy-load",
                "phonopy-qha",
                "phonopy-gruneisen",
                "phonopy-qe-born",
            }.issubset(entrypoints)
        )
        self.assertEqual(len(self.catalog["calculator_interfaces"]), 17)
        self.assertEqual(len(self.catalog["capabilities"]), 20)

    def test_v4_split_and_documentation_drift_are_explicit(self) -> None:
        entrypoints = {item["id"]: item for item in self.catalog["entrypoints"]}
        self.assertEqual(entrypoints["phonopy-load"]["status"], "deprecated-alias")
        conflicts = {item["id"]: item for item in self.catalog["documentation_conflicts"]}
        self.assertIn("main-cli-nac", conflicts)
        self.assertIn("force-collection-command", conflicts)
        self.assertIn("propplot-spelling", conflicts)
        self.assertIn("Never generate phonopy --nac", conflicts["main-cli-nac"]["resolution"])
        self.assertEqual(len(conflicts), 15)
        current_options = {
            option
            for group in self.catalog["option_groups"]
            if group["id"] != "deprecated-or-removed"
            for option in group["options"]
        }
        self.assertFalse({"--nac", "--symfc", "--br", "--st"} & current_options)

    def test_search_covers_options_interfaces_and_recipes(self) -> None:
        result = phonopy_catalog.search_report(self.catalog, self.recipes, "projected DOS")
        ids = {item["id"] for item in result["records"]}
        self.assertTrue({"calc.pdos", "projected-dos"}.issubset(ids))
        option_result = phonopy_catalog.search_report(
            self.catalog, self.recipes, "--legacy-backend"
        )
        self.assertIn(
            "frequency-temperature-and-output",
            {item["id"] for item in option_result["records"]},
        )

    def test_high_use_recipes_preserve_v4_commands(self) -> None:
        recipes = self.recipes["recipes"]
        self.assertEqual(
            recipes["vasp-finite-displacement"]["commands"][0]["argv"][:2],
            ["phonopy-init", "-d"],
        )
        self.assertEqual(
            recipes["qe-finite-displacement"]["commands"][0]["argv"][:3],
            ["phonopy-init", "--qe", "-d"],
        )
        self.assertEqual(
            recipes["band-auto"]["commands"][0]["argv"],
            ["phonopy", "--band", "auto", "-p", "phonopy_params.yaml"],
        )
        self.assertNotIn(
            "--nac", recipes["band-explicit-with-nac"]["commands"][0]["argv"]
        )

    def test_documentation_plan_never_authorizes_execution(self) -> None:
        report, code = phonopy_catalog.plan_report(
            self.catalog, self.recipes, "thermal-properties"
        )
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "documentation-plan")
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["native_execution_performed"])
        self.assertEqual(report["native_validation"]["state"], "not_run")

    def test_feature_without_recipe_is_blocked(self) -> None:
        report, code = phonopy_catalog.plan_report(
            self.catalog, self.recipes, "pypolymlp-temperature-dependent-fc"
        )
        self.assertEqual(code, 3)
        self.assertEqual(report["finding"], "PHONOPY_RECIPE_NOT_ESTABLISHED")

    def test_probe_does_not_launch_any_entrypoint(self) -> None:
        with mock.patch.object(phonopy_catalog.shutil, "which", return_value=None), mock.patch.object(
            phonopy_catalog.importlib.metadata,
            "version",
            side_effect=importlib.metadata.PackageNotFoundError,
        ):
            report = phonopy_catalog.probe_report()
        self.assertEqual(report["status"], "tool-unavailable")
        self.assertFalse(report["help_or_version_executed"])
        self.assertFalse(report["native_execution_performed"])

    def test_cli_is_machine_readable(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = phonopy_catalog.main(["plan", "band-auto"])
        self.assertEqual(code, 0)
        report = json.loads(stream.getvalue())
        self.assertEqual(report["recipe"], "band-auto")

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text('{"x": 1, "x": 2}', encoding="utf-8")
            with self.assertRaises(phonopy_catalog.CatalogError):
                phonopy_catalog._load_json(path)

    def test_skill_and_calling_guide_expose_manual_first_layers(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        guide = (ROOT / "references" / "calling-and-recipes.md").read_text(
            encoding="utf-8"
        )
        for snippet in (
            "phonopy-init",
            "official-command-catalog.json",
            "task-recipes.json",
            "native-not-run",
        ):
            self.assertIn(snippet, skill)
        for snippet in (
            "VASP finite displacement",
            "Quantum ESPRESSO finite displacement",
            "Quasi-harmonic approximation",
            "Documentation drift",
        ):
            self.assertIn(snippet, guide)


if __name__ == "__main__":
    unittest.main()
