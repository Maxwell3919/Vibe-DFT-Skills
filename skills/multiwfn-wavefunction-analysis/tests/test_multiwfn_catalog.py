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
import multiwfn_catalog


class MultiwfnCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.recipes = multiwfn_catalog.load_data()
        cls.functions = multiwfn_catalog._function_records(cls.catalog)

    def test_versions_and_complete_main_function_index(self) -> None:
        self.assertEqual(self.catalog["program_version"], "2026.7.15")
        self.assertEqual(self.catalog["manual_version"], "2026.7.10")
        main = {
            record["id"]: record
            for record in self.functions
            if record["kind"] == "main-function"
        }
        self.assertEqual(len(main), 29)
        self.assertEqual(
            set(main),
            {str(value) for value in range(26)} | {"100", "200", "300"},
        )
        self.assertIn("Population", main["7"]["title"])
        self.assertIn("weak interactions", main["20"]["title"])

    def test_representative_subfunctions_are_explicitly_indexed(self) -> None:
        subfunctions = {
            record["id"]: record
            for record in self.functions
            if record["kind"] == "subfunction"
        }
        self.assertEqual(len(subfunctions), 168)
        for subfunction_id, phrase in {
            "7.1": "Hirshfeld",
            "7.15": "Hirshfeld-I",
            "8.1": "Mulliken orbital",
            "9.1": "Mayer",
            "13.20": "duplicate grid",
            "18.1": "Hole/electron",
            "20.11": "IGMH",
            "25.14": "NICS-2D",
            "100.9": "Connectivity",
            "200.3": "Cube for multiple orbitals",
            "300.7": "Geometry operations",
        }.items():
            with self.subTest(subfunction=subfunction_id):
                self.assertIn(subfunction_id, subfunctions)
                self.assertIn(phrase.casefold(), subfunctions[subfunction_id]["title"].casefold())
                self.assertEqual(
                    subfunctions[subfunction_id]["evidence"],
                    "manual-index-listing-only",
                )

    def test_official_invocation_arguments_and_input_families_are_recorded(self) -> None:
        invocation = self.catalog["invocation"]
        self.assertEqual(
            invocation["documented_arguments"], ["-nt", "-uf", "-silent", "-set"]
        )
        self.assertEqual(
            invocation["documented_example"],
            [
                "Multiwfn",
                "COCl2.fch",
                "-nt",
                "36",
                "-set",
                "/sob/tmp/settings.ini",
                "-silent",
            ],
        )
        families = {item["id"]: item for item in self.catalog["input_families"]}
        self.assertEqual(len(families), 7)
        self.assertIn(".wfx", families["gtf-wavefunction"]["formats"])
        self.assertIn("CHGCAR", families["grid-with-structure"]["formats"])
        self.assertIn("POSCAR", families["structure-only"]["formats"])

    def test_exact_official_recipe_sequences_are_preserved(self) -> None:
        recipes = self.recipes["recipes"]
        self.assertEqual(
            recipes["orbital-composition-mulliken"]["stdin_sequence"],
            ["8", "1", "1", "2", "3"],
        )
        self.assertEqual(recipes["elf-cube"]["stdin_sequence"], ["5", "9", "2", "2"])
        self.assertIn("ELF.cub", recipes["elf-cube"]["expected_outputs"])
        self.assertEqual(recipes["mulliken-population"]["stdin_sequence"], ["7", "5", "1"])
        self.assertEqual(recipes["hirshfeld-charge"]["stdin_sequence"], ["7", "1", "1"])
        self.assertEqual(recipes["adch-charge"]["stdin_sequence"], ["7", "11", "1"])
        self.assertEqual(recipes["hirshfeld-i-charge"]["stdin_sequence"], ["7", "15", "1"])
        self.assertEqual(recipes["mayer-bond-order"]["stdin_sequence"], ["9", "1"])
        self.assertIn("bndmat.txt", " ".join(recipes["mayer-bond-order"]["expected_outputs"]))
        self.assertEqual(recipes["fuzzy-bond-order"]["stdin_sequence"], ["9", "7"])
        self.assertEqual(recipes["tdos-plot"]["stdin_sequence"], ["10", "0"])

    def test_complex_recipes_record_io_and_noninteractive_boundary(self) -> None:
        recipes = self.recipes["recipes"]
        self.assertEqual(
            recipes["aim-topology"]["stdin_sequence"],
            ["2", "2", "3", "0", "<close-GUI>", "8", "0"],
        )
        self.assertEqual(recipes["aim-topology"]["mode"], "interactive-gui")
        self.assertFalse(recipes["aim-topology"]["batch_ready"])
        self.assertEqual(
            recipes["igmh-interfragment"]["stdin_sequence"],
            ["20", "11", "2", "1-12", "13-25", "2", "3"],
        )
        self.assertTrue(
            {"sl2r.cub", "dg_inter.cub"}.issubset(
                recipes["igmh-interfragment"]["expected_outputs"]
            )
        )
        self.assertEqual(
            recipes["hole-electron-cubes"]["stdin_sequence"],
            ["18", "1", "<excited-state-output>", "2", "1", "3", "10", "11"],
        )
        self.assertEqual(
            recipes["hole-electron-cubes"]["expected_outputs"],
            ["hole.cub", "electron.cub"],
        )

    def test_catalog_listing_is_not_silently_promoted_to_recipe(self) -> None:
        shown = multiwfn_catalog.show_report(self.catalog, self.recipes, "13.20")
        self.assertEqual(shown["record"]["kind"], "subfunction")
        self.assertEqual(shown["record"]["evidence"], "manual-index-listing-only")
        report, exit_code = multiwfn_catalog.plan_report(
            self.catalog, self.recipes, "grid-duplicate"
        )
        self.assertEqual(exit_code, 3)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["finding"], "MULTIWFN_RECIPE_NOT_ESTABLISHED")
        self.assertFalse(report["execution_authorized"])

    def test_documented_plan_is_structured_but_never_executes(self) -> None:
        report, exit_code = multiwfn_catalog.plan_report(
            self.catalog, self.recipes, "elf-cube"
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "documentation-plan")
        self.assertEqual(report["stdin_file_text"], "5\n9\n2\n2\n")
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["native_execution_performed"])
        self.assertEqual(report["native_validation"]["state"], "not_run")

    def test_families_search_and_main_list_are_machine_readable(self) -> None:
        families = multiwfn_catalog.families_report(self.catalog, self.recipes)
        self.assertEqual(families["main_function_count"], 29)
        self.assertEqual(families["indexed_subfunction_count"], 168)
        self.assertEqual(families["recipe_count"], 15)
        result = multiwfn_catalog.search_report(self.catalog, self.recipes, "hole electron")
        self.assertTrue(
            {"18.1", "hole-electron-cubes"}.issubset(
                {record["id"] for record in result["records"]}
            )
        )
        listed = multiwfn_catalog.list_report(self.catalog, self.recipes, True)
        self.assertEqual(listed["count"], 29)
        self.assertTrue(all(record["kind"] == "main-function" for record in listed["records"]))

    def test_probe_resolves_identity_without_launching_multiwfn(self) -> None:
        with mock.patch.object(
            multiwfn_catalog.shutil, "which", return_value=None
        ) as which_mock, mock.patch.object(
            multiwfn_catalog.importlib.metadata,
            "version",
            side_effect=importlib.metadata.PackageNotFoundError,
        ) as version_mock:
            report = multiwfn_catalog.probe_report()
        self.assertEqual(which_mock.call_count, 2)
        version_mock.assert_called_once_with("multiwfn")
        self.assertEqual(report["status"], "tool-unavailable")
        self.assertFalse(report["banner_or_help_executed"])
        self.assertFalse(report["native_execution_performed"])

    def test_cli_outputs_json_and_blocked_plan_exit_code(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            exit_code = multiwfn_catalog.main(["plan", "grid-duplicate"])
        self.assertEqual(exit_code, 3)
        report = json.loads(stream.getvalue())
        self.assertEqual(report["finding"], "MULTIWFN_RECIPE_NOT_ESTABLISHED")
        self.assertFalse(report["native_execution_performed"])

    def test_strict_loader_rejects_duplicate_keys_and_nonfinite_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            duplicate = directory / "duplicate.json"
            duplicate.write_text('{"x": 1, "x": 2}', encoding="utf-8")
            nonfinite = directory / "nonfinite.json"
            nonfinite.write_text('{"x": NaN}', encoding="utf-8")
            for path in (duplicate, nonfinite):
                with self.subTest(path=path.name):
                    with self.assertRaises(multiwfn_catalog.CatalogError):
                        multiwfn_catalog._load_json(path)

    def test_skill_and_calling_guide_expose_manual_first_boundary(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        guide = (ROOT / "references" / "calling-and-recipes.md").read_text(
            encoding="utf-8"
        )
        for snippet in (
            "official-function-catalog.json",
            "multiwfn_catalog.py",
            "2026.7.15",
            "native-not-run",
            "Multiwfn <input-file> -silent < commands.in",
        ):
            self.assertIn(snippet, skill)
        for snippet in (
            "29 main functions",
            "Orbital composition",
            "ELF cube",
            "AIM topology",
            "IGMH",
            "Hole/electron cubes",
            "Failure semantics",
            "Official sources used",
        ):
            self.assertIn(snippet, guide)


if __name__ == "__main__":
    unittest.main()
