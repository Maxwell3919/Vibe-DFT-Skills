from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import run_source_skill_tests as runner


class SourceSkillTestRunnerTests(unittest.TestCase):
    def _repository(self, root: Path, *, lifecycle: str = "development", with_test: bool = True) -> None:
        (root / "registry").mkdir(parents=True)
        (root / "tools").mkdir()
        (root / "tools" / "run_tests.py").write_text(
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        skill = root / "skills" / "example-skill"
        (skill / "tests").mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: example-skill\n---\n", encoding="utf-8")
        if with_test:
            (skill / "tests" / "test_example.py").write_text(
                "import unittest\n\n"
                "class Example(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )
        (root / "registry" / "skill-registry.yaml").write_text(
            "schema_version: \"1.0\"\n"
            "skills:\n"
            "  example-skill:\n"
            f"    lifecycle: {lifecycle}\n"
            "    path: skills/example-skill\n",
            encoding="utf-8",
        )

    def test_development_discovery_is_independent_of_routing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            commands = runner.discover_commands(
                root,
                frozenset({"development"}),
                python=sys.executable,
            )
            labels = [command.label for command in commands]
            self.assertEqual(
                labels,
                [
                    "development:example-skill:compile",
                    "development:example-skill:unittest",
                ],
            )

    def test_active_skill_is_not_selected_by_default_development_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, lifecycle="active")
            with self.assertRaises(runner.DiscoveryError) as context:
                runner.load_source_skills(root, frozenset({"development"}))
            self.assertEqual(context.exception.code, "SOURCE_SKILL_SET_EMPTY")

    def test_missing_behavior_hook_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root, with_test=False)
            with self.assertRaises(runner.DiscoveryError) as context:
                runner.discover_commands(root, frozenset({"development"}))
            self.assertEqual(context.exception.code, "SOURCE_SKILL_TEST_HOOK_MISSING")

    def test_invalid_lifecycle_selection_is_rejected(self) -> None:
        with self.assertRaises(runner.DiscoveryError) as context:
            runner._parse_lifecycles("planned")
        self.assertEqual(context.exception.code, "LIFECYCLE_SELECTION_INVALID")

    def test_network_policy_blocks_socket_access(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "network.py"
            script.write_text(
                "import socket\n"
                "socket.getaddrinfo('example.com', 443)\n",
                encoding="utf-8",
            )
            result = runner.execute_commands(
                root,
                [
                    runner.Command(
                        label="development:example:network",
                        argv=(sys.executable, str(script)),
                        cwd=root,
                    )
                ],
                timeout_seconds=30,
            )
            self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
