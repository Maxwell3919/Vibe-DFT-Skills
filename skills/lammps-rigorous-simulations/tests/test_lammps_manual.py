from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "lammps_manual", ROOT / "scripts" / "lammps_manual.py"
)
assert SPEC is not None and SPEC.loader is not None
MANUAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MANUAL)


class LammpsManualTests(unittest.TestCase):
    def test_catalogs_are_version_pinned_and_linked(self) -> None:
        result = MANUAL.validate_catalogs()
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["pinned_version"], "4Jul2026")
        self.assertGreaterEqual(result["general_command_count"], 100)
        self.assertGreaterEqual(result["high_use_record_count"], 30)
        self.assertGreaterEqual(result["recipe_count"], 12)
        self.assertEqual(result["native_state"], "native-not-run")

    def test_search_rendering_and_readiness_are_fail_closed(self) -> None:
        commands = MANUAL.list_commands("restart", None)
        self.assertTrue(
            commands["high_use_records"] or commands["general_name_matches"]
        )
        recipes = MANUAL.list_recipes("restart", None)
        self.assertGreater(recipes["count"], 0)

        with self.assertRaises(MANUAL.ManualError) as missing:
            MANUAL.show_recipe("not-a-recipe", "lmp", False)
        self.assertTrue(missing.exception.incomplete)
        self.assertEqual(missing.exception.code, "LAMMPS.MANUAL.RECIPE_NOT_FOUND")

        with self.assertRaises(MANUAL.ManualError) as unresolved:
            MANUAL.show_recipe("npt-equilibration", "lmp", True)
        self.assertTrue(unresolved.exception.incomplete)
        self.assertEqual(unresolved.exception.code, "LAMMPS.MANUAL.UNRESOLVED_PARAMETERS")

        ready = MANUAL.show_recipe("official-lj-melt-smoke", "lmp-test", True)
        self.assertEqual(ready["unresolved_parameters"], [])
        self.assertEqual(ready["recipe"]["argv_templates"][0][0], "lmp-test")

    def test_safe_probe_invokes_only_help_and_checks_styles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "lmp-test"
            executable.write_text(
                "#!/bin/sh\n"
                "if [ \"$#\" -eq 1 ] && [ \"$1\" = \"-help\" ]; then\n"
                "  echo 'LAMMPS (4 Jul 2026)'\n"
                "  echo 'Installed styles: lj/cut nve nvt'\n"
                "  exit 0\n"
                "fi\n"
                "exit 99\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            code, result = MANUAL.probe_native(
                str(executable), ["lj/cut", "nve"]
            )

        self.assertEqual(code, 0)
        self.assertEqual(result["state"], "native-validated")
        self.assertEqual(result["parsed_banner"], "LAMMPS (4 Jul 2026)")
        self.assertEqual(result["probe"]["argv"][1:], ["-help"])
        self.assertTrue(all(result["required_style_presence"].values()))

    def test_probe_rejects_missing_executable_banner_or_style(self) -> None:
        code, result = MANUAL.probe_native(
            "definitely-no-such-lammps-executable", []
        )
        self.assertEqual(code, 3)
        self.assertEqual(result["state"], "native-not-run")

        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "lmp-wrong"
            executable.write_text(
                "#!/bin/sh\n"
                "echo 'LAMMPS (2 Apr 2025)'\n"
                "echo 'lj/cut'\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            code, result = MANUAL.probe_native(
                str(executable), ["lj/cut", "nve"]
            )
        self.assertEqual(code, 3)
        self.assertFalse(result["banner_match"])
        self.assertFalse(result["required_style_presence"]["nve"])


if __name__ == "__main__":
    unittest.main()
