from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

import sys

sys.path.insert(0, str(SCRIPTS))
import vaspkit_catalog as catalog_cli


class VaspkitCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.recipes = catalog_cli.load_data()
        cls.tasks = catalog_cli.flatten_tasks(cls.catalog)

    def test_catalog_matches_pinned_official_feature_snapshot(self) -> None:
        self.assertEqual(self.catalog["documentation_series"], "1.5")
        self.assertEqual(
            self.catalog["source_snapshot"]["documentation_commit"],
            "383a7103505b5b9436dedbf04df42ebb6e248638",
        )
        self.assertEqual(
            self.catalog["source_snapshot"]["raw_sha256"],
            "454271ce1eab377a1a5539dab52e16b8aaec8e1413d0f739fa12840608772ccd",
        )
        self.assertEqual(len(self.catalog["categories"]), 25)
        self.assertEqual(len(self.tasks), 174)
        self.assertEqual(len(set(self.tasks)), 174)
        self.assertEqual(len(self.catalog["top_level_only_categories"]), 4)

    def test_major_families_and_tasks_are_not_hidden_behind_211(self) -> None:
        expected = {
            "102": "KPOINTS",
            "203": "OUTCAR",
            "303": "bulk",
            "401": "supercell",
            "503": "band center",
            "601": "symmetry",
            "803": "surface",
            "111": "DOS",
            "211": "band structure",
            "251": "hybrid",
            "263": "Fermi",
            "282": "effective band",
            "314": "charge-density difference",
            "426": "planar average",
            "511": "wave function",
            "621": "anisotropy",
            "652": "spin texture",
            "682": "transport",
            "711": "optical",
            "721": "mean-squared",
            "781": "BoltzTraP",
            "912": "effective mass",
            "927": "vacuum",
        }
        for task_id, phrase in expected.items():
            with self.subTest(task=task_id):
                self.assertIn(task_id, self.tasks)
                self.assertIn(phrase.casefold(), self.tasks[task_id]["purpose"].casefold())

    def test_task_ids_have_complete_recipe_state_separate_from_listing(self) -> None:
        recipes = self.recipes["recipes"]
        established = {
            "102",
            "301",
            "302",
            "303",
            "111",
            "112",
            "113",
            "114",
            "115",
            "211",
            "212",
            "213",
            "214",
            "251",
            "252",
            "311",
            "312",
            "313",
            "314",
            "400",
            "401",
            "426",
            "427",
            "503",
            "601",
            "602",
            "711",
            "721",
            "911",
            "912",
            "923",
            "927",
        }
        self.assertTrue(established.issubset(recipes))
        for task_id in established:
            with self.subTest(task=task_id):
                self.assertIn("status", recipes[task_id])
                self.assertIn("mode", recipes[task_id])
                self.assertIn("required_files", recipes[task_id])
                self.assertIn("expected_outputs", recipes[task_id])
                self.assertIn("source", recipes[task_id])
                self.assertIn("caution", recipes[task_id])
        self.assertEqual(self.recipes["execution_validation"], "not_run")

    def test_official_call_modes_and_high_use_exact_tokens_are_preserved(self) -> None:
        recipes = self.recipes["recipes"]
        self.assertEqual(
            recipes["102"]["argv_template"],
            [
                "vaspkit",
                "-task",
                "102",
                "-file",
                "POSCAR",
                "-kpr",
                "<converged-resolution>",
            ],
        )
        self.assertEqual(recipes["211"]["stdin_template"], ["211", "0"])
        self.assertEqual(recipes["252"]["stdin_template"], ["252", "0"])
        self.assertEqual(
            recipes["211"]["required_files"],
            ["INCAR", "DOSCAR", "EIGENVAL", "POSCAR", "KPOINTS"],
        )
        self.assertEqual(
            recipes["211"]["expected_outputs"],
            [
                "BAND.dat",
                "BAND_REFORMATTED.dat",
                "KLINES.dat",
                "KLABELS",
                "BAND_GAP",
            ],
        )

    def test_documentation_conflicts_fail_closed(self) -> None:
        for task_id in ("109", "604", "711", "926"):
            with self.subTest(task=task_id):
                report, exit_code = catalog_cli.plan_report(
                    self.catalog, self.recipes, task_id
                )
                self.assertEqual(exit_code, 3)
                self.assertEqual(report["status"], "blocked")
                self.assertEqual(
                    report["finding"], "VASPKIT_DOCUMENTATION_CONFLICT"
                )
                self.assertTrue(report["documentation_conflicts"])
                self.assertFalse(report["execution_authorized"])
                self.assertFalse(report["native_execution_performed"])

    def test_feature_listing_without_recipe_does_not_create_a_command(self) -> None:
        for task_id, finding in (
            ("200", "VASPKIT_RECIPE_NOT_ESTABLISHED"),
            ("215", "VASPKIT_FEATURE_LISTING_ONLY"),
        ):
            with self.subTest(task=task_id):
                report, exit_code = catalog_cli.plan_report(
                    self.catalog, self.recipes, task_id
                )
                self.assertEqual(exit_code, 3)
                self.assertEqual(report["status"], "blocked")
                self.assertEqual(report["finding"], finding)
                self.assertFalse(report["execution_authorized"])

    def test_documented_plan_is_structured_but_never_executes(self) -> None:
        report, exit_code = catalog_cli.plan_report(
            self.catalog, self.recipes, "211"
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "documentation-plan")
        self.assertEqual(report["stdin_file_text"], "211\n0\n")
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["native_execution_performed"])
        self.assertEqual(report["native_validation"]["state"], "not_run")

    def test_search_and_category_listing_are_machine_readable(self) -> None:
        result = catalog_cli.search_report(self.catalog, "projected band")
        ids = {item["task"] for item in result["tasks"]}
        self.assertTrue({"212", "213", "214"}.issubset(ids))
        listed = catalog_cli.list_report(self.catalog, "21")
        self.assertEqual(listed["count"], 6)
        self.assertEqual(
            [item["task"] for item in listed["tasks"]],
            ["211", "212", "213", "214", "215", "216"],
        )

    def test_show_reports_tutorial_only_task_712_honestly(self) -> None:
        report = catalog_cli.show_report(self.catalog, self.recipes, "712")
        record = report["record"]
        self.assertEqual(record["catalog_evidence"], "official-tutorial-only")
        self.assertIsNone(record["recipe"])
        self.assertTrue(record["documentation_conflicts"])
        self.assertFalse(report["native_execution_performed"])

    def test_probe_never_runs_help_or_banner(self) -> None:
        with mock.patch.object(catalog_cli.shutil, "which", return_value="/opt/bin/vaspkit"):
            report = catalog_cli.probe_report()
        self.assertEqual(report["status"], "available-unverified")
        self.assertEqual(report["resolved_path"], "/opt/bin/vaspkit")
        self.assertFalse(report["help_or_banner_executed"])
        self.assertFalse(report["native_execution_performed"])
        self.assertEqual(report["scientific_capability_claim"], "none")

    def test_cli_outputs_json_and_conflict_exit_code(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            exit_code = catalog_cli.main(["plan", "711"])
        self.assertEqual(exit_code, 3)
        report = json.loads(stream.getvalue())
        self.assertEqual(report["finding"], "VASPKIT_DOCUMENTATION_CONFLICT")
        self.assertFalse(report["native_execution_performed"])

    def test_strict_loader_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "duplicate.json"
            path.write_text('{"x": 1, "x": 2}', encoding="utf-8")
            with self.assertRaises(catalog_cli.CatalogError):
                catalog_cli._load_json(path)

    def test_skill_teaches_actual_calls_and_points_to_manual_content(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        recipes = (ROOT / "references" / "calling-and-recipes.md").read_text(
            encoding="utf-8"
        )
        for snippet in (
            "vaspkit -task 102 -kpr 0.04",
            "printf '102\\n2\\n0.04\\n' | vaspkit",
            "vaspkit < cmd.in",
            "vaspkit.stdout",
            "native_validation",
            "official-task-catalog.json",
            "calling-and-recipes.md",
        ):
            self.assertIn(snippet, skill)
        for snippet in (
            "The five official calling modes",
            "Task 211",
            "Tasks 111–115",
            "Tasks 426 and 427",
            "Task 711",
            "Tasks 721–728",
            "Official sources used",
        ):
            self.assertIn(snippet, recipes)

    def test_docs_state_native_absence_without_claiming_execution(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        environment = (
            ROOT / "references" / "environment-and-license.md"
        ).read_text(encoding="utf-8")
        self.assertIn("had no `vaspkit` command", skill)
        self.assertIn("No VASPKIT banner", environment)
        self.assertIn("native-not-run", environment)
        self.assertNotIn("native VASPKIT execution passed", skill)


if __name__ == "__main__":
    unittest.main()
