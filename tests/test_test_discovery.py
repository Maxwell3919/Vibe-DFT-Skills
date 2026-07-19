from __future__ import annotations

from contextlib import redirect_stderr
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_tests  # noqa: E402


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()

    def _write_registry(self, entries: list[tuple[str, str]]) -> None:
        skills = {
            name: {
                "lifecycle": lifecycle,
                "path": f"skills/{name}",
            }
            for name, lifecycle in entries
        }
        write_text(
            self.repo / "registry" / "skill-registry.yaml",
            yaml.safe_dump(
                {"schema_version": "1.0", "skills": skills},
                sort_keys=False,
            ),
        )

    def _add_skill(self, name: str) -> Path:
        skill = self.repo / "skills" / name
        write_text(skill / "SKILL.md", f"# {name}\n")
        return skill

    def test_active_skill_without_hook_fails_discovery(self) -> None:
        self._write_registry([("missing-hooks", "active")])
        self._add_skill("missing-hooks")

        with self.assertRaises(run_tests.DiscoveryError) as caught:
            run_tests.discover_skill_commands(
                self.repo,
                sys.executable,
                root_test_covered=frozenset(),
            )

        self.assertEqual(caught.exception.code, "ACTIVE_SKILL_TEST_HOOK_MISSING")

    def test_duplicate_registry_key_fails_closed(self) -> None:
        write_text(
            self.repo / "registry" / "skill-registry.yaml",
            "schema_version: '1.0'\nskills: {}\nskills: {}\n",
        )

        with self.assertRaises(run_tests.DiscoveryError) as caught:
            run_tests.load_active_skills(self.repo)

        self.assertEqual(caught.exception.code, "REGISTRY_UNREADABLE")

    def test_runner_forces_bytecode_off_and_active_hook_creates_no_cache(self) -> None:
        self._write_registry([("cache-safe", "active")])
        skill = self._add_skill("cache-safe")
        write_text(skill / "scripts" / "helper_module.py", "VALUE = 7\n")
        write_text(
            skill / "scripts" / "test_environment.py",
            "from pathlib import Path\n"
            "import os\n"
            "import helper_module\n"
            "assert helper_module.VALUE == 7\n"
            "Path('observed-bytecode-env').write_text("
            "os.environ.get('PYTHONDONTWRITEBYTECODE', '<missing>'), encoding='utf-8')\n",
        )
        commands = run_tests.discover_skill_commands(
            self.repo,
            sys.executable,
            root_test_covered=frozenset(),
        )

        with mock.patch.dict(run_tests.os.environ, {"PYTHONDONTWRITEBYTECODE": "0"}):
            result = run_tests.execute_commands(commands)

        self.assertEqual(result, 0)
        self.assertTrue(run_tests.sys.dont_write_bytecode)
        self.assertEqual(
            (skill / "observed-bytecode-env").read_text(encoding="utf-8"),
            "1",
        )
        self.assertFalse(any(path.name == "__pycache__" for path in skill.rglob("*")))
        self.assertFalse(any(skill.rglob("*.pyc")))

    def test_missing_bytecode_environment_fails_before_hook_execution(self) -> None:
        marker = self.repo / "must-not-run-without-bytecode-policy"
        command = run_tests.Command(
            label="temporary:environment-policy",
            argv=(
                sys.executable,
                "-c",
                "from pathlib import Path; Path('must-not-run-without-bytecode-policy').touch()",
            ),
            cwd=self.repo,
        )

        with mock.patch.object(run_tests, "child_environment", return_value={}):
            result = run_tests.execute_commands((command,))

        self.assertEqual(result, 2)
        self.assertFalse(marker.exists())

    def test_development_skill_tree_is_not_scanned_or_executed(self) -> None:
        self._write_registry(
            [
                ("development-code", "development"),
                ("active-code", "active"),
            ]
        )
        active = self._add_skill("active-code")
        development = self._add_skill("development-code")
        write_text(active / "scripts" / "test_active.py", "raise SystemExit(0)\n")
        development_marker = development / "development-ran"
        write_text(
            development / "scripts" / "test_development.py",
            "from pathlib import Path\nPath('development-ran').touch()\nraise SystemExit(91)\n",
        )
        # A noncanonical matching filename would fail discovery if the development
        # directory were inspected at all.
        write_text(development / "scripts" / "test_bad name.py", "raise SystemExit(92)\n")

        commands = run_tests.discover_skill_commands(
            self.repo,
            sys.executable,
            root_test_covered=frozenset(),
        )

        self.assertEqual(
            [command.label for command in commands],
            [
                "skill:active-code:script-test:test_active.py",
                "skill:active-code:compile:skills/active-code",
            ],
        )
        rendered = "\n".join(
            (command.label + " " + " ".join(command.argv) + " " + str(command.cwd))
            for command in commands
        )
        self.assertNotIn("development-code", rendered)
        self.assertEqual(run_tests.execute_commands(commands), 0)
        self.assertFalse(development_marker.exists())

    def test_discovery_order_is_stable_and_sync_checks_are_retained(self) -> None:
        # Deliberately write the registry and hook files out of desired order.
        self._write_registry([("zeta-code", "active"), ("alpha-code", "active")])
        zeta = self._add_skill("zeta-code")
        alpha = self._add_skill("alpha-code")
        write_text(zeta / "scripts" / "sync_zeta.py", self._sync_hook_source())
        write_text(zeta / "scripts" / "check_alpha.py", "raise SystemExit(0)\n")
        write_text(zeta / "scripts" / "test_beta.py", "raise SystemExit(0)\n")
        write_text(zeta / "tests" / "test_zeta.py", "import unittest\n")
        write_text(alpha / "scripts" / "test_zulu.py", "raise SystemExit(0)\n")

        first = run_tests.discover_skill_commands(
            self.repo,
            sys.executable,
            root_test_covered=frozenset(),
        )
        second = run_tests.discover_skill_commands(
            self.repo,
            sys.executable,
            root_test_covered=frozenset(),
        )

        expected_labels = [
            "skill:alpha-code:script-test:test_zulu.py",
            "skill:alpha-code:compile:skills/alpha-code",
            "skill:zeta-code:unittest:tests",
            "skill:zeta-code:script-test:test_beta.py",
            "skill:zeta-code:check:check_alpha.py",
            "skill:zeta-code:check:sync_zeta.py",
            "skill:zeta-code:compile:skills/zeta-code",
        ]
        self.assertEqual([command.label for command in first], expected_labels)
        self.assertEqual(first, second)
        sync = next(command for command in first if command.label.endswith("sync_zeta.py"))
        self.assertEqual(sync.argv[-2:], ("scripts/sync_zeta.py", "--check"))

    def test_sync_hook_without_explicit_check_mode_fails_discovery(self) -> None:
        self._write_registry([("unsafe-sync", "active")])
        skill = self._add_skill("unsafe-sync")
        write_text(skill / "scripts" / "sync_reference.py", "raise SystemExit(0)\n")

        with self.assertRaises(run_tests.DiscoveryError) as caught:
            run_tests.discover_skill_commands(
                self.repo,
                sys.executable,
                root_test_covered=frozenset(),
            )

        self.assertEqual(caught.exception.code, "CHECK_HOOK_FLAG_MISSING")

    def test_noncanonical_matching_hook_fails_discovery(self) -> None:
        self._write_registry([("bad-hook", "active")])
        skill = self._add_skill("bad-hook")
        write_text(skill / "scripts" / "test_bad name.py", "raise SystemExit(0)\n")

        with self.assertRaises(run_tests.DiscoveryError) as caught:
            run_tests.discover_skill_commands(
                self.repo,
                sys.executable,
                root_test_covered=frozenset(),
            )

        self.assertEqual(caught.exception.code, "TEST_HOOK_NAME_INVALID")

    def test_duplicate_command_fails_discovery(self) -> None:
        command = run_tests.Command(
            label="temporary:duplicate",
            argv=(sys.executable, "-c", "raise SystemExit(0)"),
            cwd=self.repo,
        )

        with self.assertRaises(run_tests.DiscoveryError) as caught:
            run_tests.ensure_unique_commands((command, command))

        self.assertEqual(caught.exception.code, "TEST_COMMAND_DUPLICATE")

    def test_script_failure_is_propagated_and_stops_execution(self) -> None:
        marker = self.repo / "must-not-run"
        fail = run_tests.Command(
            label="temporary:fail",
            argv=(sys.executable, "-c", "raise SystemExit(7)"),
            cwd=self.repo,
        )
        after = run_tests.Command(
            label="temporary:after",
            argv=(
                sys.executable,
                "-c",
                "from pathlib import Path; Path('must-not-run').touch()",
            ),
            cwd=self.repo,
        )

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            normalized = run_tests.execute_commands((fail, after))

        self.assertEqual(normalized, 2)
        self.assertIn("normalized_exit=2", stderr.getvalue())
        self.assertIn("raw_exit=7", stderr.getvalue())
        self.assertFalse(marker.exists())

    def test_discovered_unittest_failure_returns_nonzero(self) -> None:
        self._write_registry([("module-failure", "active")])
        skill = self._add_skill("module-failure")
        write_text(
            skill / "tests" / "test_failure.py",
            "import unittest\n\n"
            "class FailureTests(unittest.TestCase):\n"
            "    def test_failure(self):\n"
            "        self.fail('intentional temporary-tree failure')\n",
        )
        commands = run_tests.discover_skill_commands(
            self.repo,
            sys.executable,
            root_test_covered=frozenset(),
        )
        unittest_command = next(command for command in commands if ":unittest:" in command.label)

        completed = subprocess.run(
            unittest_command.argv,
            cwd=unittest_command.cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("FAILED", completed.stderr)

    @staticmethod
    def _sync_hook_source() -> str:
        return (
            "import argparse\n\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--check', action='store_true')\n"
            "arguments = parser.parse_args()\n"
            "raise SystemExit(0 if arguments.check else 3)\n"
        )


if __name__ == "__main__":
    unittest.main()
