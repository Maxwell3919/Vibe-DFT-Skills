from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
OPERATIONAL_GUIDE = ROOT / "references" / "operational-workflows.md"
SPEC = importlib.util.spec_from_file_location(
    "gromacs_manual", ROOT / "scripts" / "gromacs_manual.py"
)
assert SPEC is not None and SPEC.loader is not None
MANUAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MANUAL)


class GromacsManualTests(unittest.TestCase):
    def test_operational_guide_is_version_bound_and_content_complete(self) -> None:
        text = OPERATIONAL_GUIDE.read_text(encoding="utf-8")
        for required in (
            "GROMACS 2026.3",
            "Official behavior",
            "Operational heuristic",
            "System preparation",
            "MDP audit",
            "Restart and segment lineage",
            "Failure triage",
            "Trajectory and analysis checks",
            "Performance work",
            "no_positive_claim",
        ):
            self.assertIn(required, text)
        self.assertIn(
            "https://manual.gromacs.org/documentation/2026.3/",
            text,
        )
        self.assertNotIn("native execution passed", text.lower())

    def test_catalogs_are_version_pinned_and_linked(self) -> None:
        result = MANUAL.validate_catalogs()
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["pinned_version"], "2026.3")
        self.assertGreaterEqual(result["command_count"], 30)
        self.assertGreaterEqual(result["recipe_count"], 15)
        self.assertEqual(result["native_state"], "native-not-run")

    def test_search_and_recipe_readiness_are_fail_closed(self) -> None:
        commands = MANUAL.list_commands("grompp", None)
        self.assertTrue(
            any(item["name"] == "gmx grompp" for item in commands["commands"])
        )
        recipes = MANUAL.list_recipes("checkpoint", None)
        self.assertGreater(recipes["count"], 0)

        with self.assertRaises(MANUAL.ManualError) as missing:
            MANUAL.show_recipe("not-a-recipe", False)
        self.assertTrue(missing.exception.incomplete)
        self.assertEqual(missing.exception.code, "GROMACS.MANUAL.RECIPE_NOT_FOUND")

        with self.assertRaises(MANUAL.ManualError) as unresolved:
            MANUAL.show_recipe("prepare-biomolecular-system", True)
        self.assertTrue(unresolved.exception.incomplete)
        self.assertEqual(unresolved.exception.code, "GROMACS.MANUAL.UNRESOLVED_PARAMETERS")

        ready = MANUAL.show_recipe("production-md", True)
        self.assertEqual(ready["recipe"]["unresolved_parameters"], [])

    def test_density_profile_recipe_is_manual_grounded_and_fail_closed(self) -> None:
        commands = MANUAL.list_commands("gmx density", None)["commands"]
        density_command = next(
            item for item in commands if item["name"] == "gmx density"
        )
        self.assertEqual(
            density_command["recipe_ids"], ["spatial-density-profile"]
        )

        result = MANUAL.show_recipe("spatial-density-profile", False)
        recipe = result["recipe"]
        argv = recipe["argv_templates"][0]
        for token in ("-d", "-sl", "-dens", "-ng", "-b", "-e", "-dt"):
            self.assertIn(token, argv)
        self.assertEqual(
            recipe["sources"],
            [
                "https://manual.gromacs.org/documentation/2026.3/onlinehelp/gmx-density.html"
            ],
        )
        content = str(recipe)
        for required in (
            "mass",
            "number",
            "charge",
            "electron",
            "kg/m^3",
            "PBC",
            "normalization",
            "center",
            "symmetrization",
            "atom names",
            "gmx energy",
        ):
            self.assertIn(required, content)

        with self.assertRaises(MANUAL.ManualError) as unresolved:
            MANUAL.show_recipe("spatial-density-profile", True)
        self.assertEqual(
            unresolved.exception.code,
            "GROMACS.MANUAL.UNRESOLVED_PARAMETERS",
        )

    def test_safe_probe_invokes_only_version_and_command_help(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "gmx-test"
            executable.write_text(
                "#!/bin/sh\n"
                "if [ \"$#\" -eq 1 ] && [ \"$1\" = \"--version\" ]; then\n"
                "  echo 'GROMACS version:    2026.3'\n"
                "  exit 0\n"
                "fi\n"
                "if [ \"$#\" -eq 2 ] && [ \"$1\" = \"help\" ] && [ \"$2\" = \"commands\" ]; then\n"
                "  echo 'grompp mdrun check energy'\n"
                "  exit 0\n"
                "fi\n"
                "exit 99\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            code, result = MANUAL.probe_native(str(executable))

        self.assertEqual(code, 0)
        self.assertEqual(result["state"], "native-validated")
        self.assertEqual(result["parsed_version"], "2026.3")
        self.assertEqual(
            [item["argv"][1:] for item in result["probes"]],
            [["--version"], ["help", "commands"]],
        )
        self.assertTrue(all(result["required_help_tokens"].values()))

    def test_probe_rejects_missing_or_wrong_version(self) -> None:
        code, result = MANUAL.probe_native("definitely-no-such-gmx-executable")
        self.assertEqual(code, 3)
        self.assertEqual(result["state"], "native-not-run")

        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "gmx-wrong"
            executable.write_text(
                "#!/bin/sh\n"
                "echo 'GROMACS version: 2025.4 grompp mdrun check energy'\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            code, result = MANUAL.probe_native(str(executable))
        self.assertEqual(code, 3)
        self.assertFalse(result["version_match"])


if __name__ == "__main__":
    unittest.main()
