from __future__ import annotations

from contextlib import redirect_stderr
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_development_tests  # noqa: E402


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class DevelopmentTestDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()

    def _write_registry(
        self,
        entries: list[tuple[str, str, str | None]],
    ) -> None:
        skills = {
            name: {
                "lifecycle": lifecycle,
                "path": path,
            }
            for name, lifecycle, path in entries
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

    @staticmethod
    def _allowlist(**entries: set[str]) -> dict[str, frozenset[str]]:
        return {
            name.replace("_", "-"): frozenset(paths)
            for name, paths in entries.items()
        }

    @staticmethod
    def _offline_check_source(exit_code: int = 0) -> str:
        return (
            "import argparse\n\n"
            "DEVELOPMENT_MAINTENANCE_CHECK_IS_OFFLINE = True\n\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--check', action='store_true')\n"
            "arguments = parser.parse_args()\n"
            f"raise SystemExit({exit_code} if arguments.check else 93)\n"
        )

    def test_only_source_backed_development_skills_are_discovered_in_stable_order(
        self,
    ) -> None:
        self._write_registry(
            [
                ("zeta-code", "development", "skills/zeta-code"),
                ("active-code", "active", "skills/active-code"),
                ("planned-code", "planned", None),
                ("alpha-code", "development", "skills/alpha-code"),
            ]
        )
        alpha = self._add_skill("alpha-code")
        zeta = self._add_skill("zeta-code")
        active = self._add_skill("active-code")
        write_text(alpha / "scripts" / "test_alpha.py", "raise SystemExit(0)\n")
        write_text(zeta / "tests" / "test_zeta.py", "import unittest\n")
        write_text(zeta / "scripts" / "sync_zeta.py", self._offline_check_source())
        # The maintenance lane must never inspect active trees or arbitrary
        # business/native execution scripts.
        write_text(active / "scripts" / "test_bad name.py", "raise SystemExit(91)\n")
        write_text(alpha / "scripts" / "run_native.py", "raise SystemExit(92)\n")

        first = run_development_tests.discover_skill_commands(
            self.repo,
            sys.executable,
            reviewed_hooks=self._allowlist(
                alpha_code={"scripts/test_alpha.py"},
                zeta_code={
                    "tests/test_zeta.py",
                    "scripts/sync_zeta.py",
                },
            ),
        )
        second = run_development_tests.discover_skill_commands(
            self.repo,
            sys.executable,
            reviewed_hooks=self._allowlist(
                alpha_code={"scripts/test_alpha.py"},
                zeta_code={
                    "tests/test_zeta.py",
                    "scripts/sync_zeta.py",
                },
            ),
        )

        expected_labels = [
            "development:alpha-code:compile:skills/alpha-code",
            "development:alpha-code:script-test:test_alpha.py",
            "development:zeta-code:compile:skills/zeta-code",
            "development:zeta-code:unittest:test_zeta.py",
            "development:zeta-code:check:sync_zeta.py",
        ]
        self.assertEqual([command.label for command in first], expected_labels)
        self.assertEqual(first, second)
        rendered = "\n".join(
            command.label + " " + " ".join(command.argv) for command in first
        )
        self.assertNotIn("active-code", rendered)
        self.assertNotIn("planned-code", rendered)
        self.assertNotIn("run_native.py", rendered)
        sync = next(command for command in first if command.label.endswith("sync_zeta.py"))
        self.assertEqual(sync.argv[-2:], ("scripts/sync_zeta.py", "--check"))

    def test_development_skill_without_behavioral_hook_is_compiled_and_reported(
        self,
    ) -> None:
        self._write_registry(
            [("missing-hooks", "development", "skills/missing-hooks")]
        )
        self._add_skill("missing-hooks")

        plan = run_development_tests.discover_maintenance_plan(
            self.repo,
            sys.executable,
            reviewed_hooks={},
        )

        self.assertEqual(
            [command.label for command in plan.commands],
            ["development:missing-hooks:compile:skills/missing-hooks"],
        )
        self.assertEqual(
            plan.skipped,
            ("development:missing-hooks:no-controlled-behavioral-hook",),
        )

    def test_check_hook_requires_literal_check_flag(self) -> None:
        self._write_registry(
            [("unsafe-check", "development", "skills/unsafe-check")]
        )
        skill = self._add_skill("unsafe-check")
        write_text(
            skill / "scripts" / "check_reference.py",
            "DEVELOPMENT_MAINTENANCE_CHECK_IS_OFFLINE = True\n"
            "raise SystemExit(0)\n",
        )

        with self.assertRaises(run_development_tests.DiscoveryError) as caught:
            run_development_tests.discover_skill_commands(
                self.repo,
                sys.executable,
                reviewed_hooks=self._allowlist(
                    unsafe_check={"scripts/check_reference.py"},
                ),
            )

        self.assertEqual(caught.exception.code, "CHECK_HOOK_FLAG_MISSING")

    def test_check_hook_requires_literal_offline_marker(self) -> None:
        self._write_registry(
            [("unsafe-check", "development", "skills/unsafe-check")]
        )
        skill = self._add_skill("unsafe-check")
        write_text(
            skill / "scripts" / "check_reference.py",
            "import argparse\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('--check', action='store_true')\n",
        )

        with self.assertRaises(run_development_tests.DiscoveryError) as caught:
            run_development_tests.discover_skill_commands(
                self.repo,
                sys.executable,
                reviewed_hooks=self._allowlist(
                    unsafe_check={"scripts/check_reference.py"},
                ),
            )

        self.assertEqual(
            caught.exception.code,
            "CHECK_HOOK_OFFLINE_MARKER_MISSING",
        )

    def test_runner_forces_maintenance_environment_and_creates_no_cache(
        self,
    ) -> None:
        self._write_registry(
            [("cache-safe", "development", "skills/cache-safe")]
        )
        skill = self._add_skill("cache-safe")
        write_text(skill / "scripts" / "helper_module.py", "VALUE = 7\n")
        write_text(
            skill / "scripts" / "test_environment.py",
            "from pathlib import Path\n"
            "import os\n"
            "import helper_module\n"
            "assert helper_module.VALUE == 7\n"
            "Path('observed-environment').write_text("
            "os.environ.get('PYTHONDONTWRITEBYTECODE', '<missing>') + ':' + "
            "os.environ.get('VIBE_DFT_DEVELOPMENT_MAINTENANCE', '<missing>'), "
            "encoding='utf-8')\n",
        )
        commands = run_development_tests.discover_skill_commands(
            self.repo,
            sys.executable,
            reviewed_hooks=self._allowlist(
                cache_safe={"scripts/test_environment.py"},
            ),
        )

        with mock.patch.dict(
            run_development_tests.os.environ,
            {
                "PYTHONDONTWRITEBYTECODE": "0",
                "VIBE_DFT_DEVELOPMENT_MAINTENANCE": "0",
            },
        ):
            result = run_development_tests.execute_commands(commands)

        self.assertEqual(result, 0)
        self.assertTrue(run_development_tests.sys.dont_write_bytecode)
        self.assertEqual(
            (skill / "observed-environment").read_text(encoding="utf-8"),
            "1:1",
        )
        self.assertFalse(any(path.name == "__pycache__" for path in skill.rglob("*")))
        self.assertFalse(any(skill.rglob("*.pyc")))

    def test_unreviewed_matching_hook_is_skipped_and_reported(self) -> None:
        self._write_registry(
            [("review-needed", "development", "skills/review-needed")]
        )
        skill = self._add_skill("review-needed")
        marker = skill / "unreviewed-ran"
        write_text(
            skill / "scripts" / "test_unreviewed.py",
            "from pathlib import Path\n"
            "Path('unreviewed-ran').touch()\n"
            "raise SystemExit(91)\n",
        )

        plan = run_development_tests.discover_maintenance_plan(
            self.repo,
            sys.executable,
            reviewed_hooks={},
        )

        self.assertEqual(
            [command.label for command in plan.commands],
            ["development:review-needed:compile:skills/review-needed"],
        )
        self.assertEqual(
            plan.skipped,
            (
                "development:review-needed:unreviewed-hook:"
                "scripts/test_unreviewed.py",
            ),
        )
        self.assertEqual(
            run_development_tests.execute_commands(plan.commands),
            0,
        )
        self.assertFalse(marker.exists())

    def test_allowlisted_hook_must_exist_and_remain_canonical(self) -> None:
        self._write_registry(
            [("stale-entry", "development", "skills/stale-entry")]
        )
        self._add_skill("stale-entry")

        with self.assertRaises(run_development_tests.DiscoveryError) as caught:
            run_development_tests.discover_maintenance_plan(
                self.repo,
                sys.executable,
                reviewed_hooks=self._allowlist(
                    stale_entry={"tests/test_missing.py"},
                ),
            )

        self.assertEqual(
            caught.exception.code,
            "MAINTENANCE_ALLOWLIST_ENTRY_MISSING",
        )

    def test_allowlisted_hook_cannot_import_network_or_provider_module(self) -> None:
        self._write_registry(
            [("network-hook", "development", "skills/network-hook")]
        )
        skill = self._add_skill("network-hook")
        write_text(
            skill / "tests" / "test_network.py",
            "import urllib.request\n",
        )

        with self.assertRaises(run_development_tests.DiscoveryError) as caught:
            run_development_tests.discover_maintenance_plan(
                self.repo,
                sys.executable,
                reviewed_hooks=self._allowlist(
                    network_hook={"tests/test_network.py"},
                ),
            )

        self.assertEqual(
            caught.exception.code,
            "MAINTENANCE_HOOK_IMPORT_FORBIDDEN",
        )

    def test_allowlisted_hook_cannot_launch_native_or_scheduler_command(
        self,
    ) -> None:
        self._write_registry(
            [("native-hook", "development", "skills/native-hook")]
        )
        skill = self._add_skill("native-hook")
        write_text(
            skill / "tests" / "test_native.py",
            "import subprocess\n"
            "subprocess.run(['sbatch', 'job.sh'], check=False)\n",
        )

        with self.assertRaises(run_development_tests.DiscoveryError) as caught:
            run_development_tests.discover_maintenance_plan(
                self.repo,
                sys.executable,
                reviewed_hooks=self._allowlist(
                    native_hook={"tests/test_native.py"},
                ),
            )

        self.assertEqual(
            caught.exception.code,
            "MAINTENANCE_HOOK_EXTERNAL_PROCESS_FORBIDDEN",
        )

    def test_list_mode_is_stable_and_does_not_execute_hooks(self) -> None:
        self._write_registry(
            [("list-only", "development", "skills/list-only")]
        )
        skill = self._add_skill("list-only")
        marker = skill / "must-not-run-in-list-mode"
        write_text(
            skill / "scripts" / "test_list.py",
            "from pathlib import Path\n"
            "Path('must-not-run-in-list-mode').touch()\n",
        )
        reviewed = self._allowlist(
            list_only={"scripts/test_list.py"},
        )

        with mock.patch.object(
            run_development_tests,
            "REVIEWED_MAINTENANCE_HOOKS",
            reviewed,
        ):
            # Default arguments are bound at definition time, so pass the
            # reviewed table through a patched discovery call used by main.
            original = run_development_tests.discover_maintenance_plan

            def discover(root, python, *, skills=None):
                return original(
                    root,
                    python,
                    skills=skills,
                    reviewed_hooks=reviewed,
                )

            with mock.patch.object(
                run_development_tests,
                "discover_maintenance_plan",
                side_effect=discover,
            ):
                output = io.StringIO()
                with mock.patch("sys.stdout", output):
                    result = run_development_tests.main(
                        root=self.repo,
                        argv=("--list",),
                    )

        self.assertEqual(result, 0)
        self.assertIn(
            "LIST: [development:list-only:script-test:test_list.py]",
            output.getvalue(),
        )
        self.assertIn(
            "PLAN: skills=1 reviewed_hooks=1 commands=2 skipped=0",
            output.getvalue(),
        )
        self.assertFalse(marker.exists())

    def test_hook_failure_is_propagated_and_stops_execution(self) -> None:
        marker = self.repo / "must-not-run"
        fail = run_development_tests.Command(
            label="development:temporary:script-test:fail",
            argv=(sys.executable, "-c", "raise SystemExit(7)"),
            cwd=self.repo,
        )
        after = run_development_tests.Command(
            label="development:temporary:script-test:after",
            argv=(
                sys.executable,
                "-c",
                "from pathlib import Path; Path('must-not-run').touch()",
            ),
            cwd=self.repo,
        )

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            normalized = run_development_tests.execute_commands((fail, after))

        self.assertEqual(normalized, 2)
        self.assertIn("normalized_exit=2", stderr.getvalue())
        self.assertIn("raw_exit=7", stderr.getvalue())
        self.assertFalse(marker.exists())

    def test_repository_allowlist_plans_every_canonical_hook_once(self) -> None:
        plan = run_development_tests.discover_maintenance_plan(
            ROOT,
            sys.executable,
        )

        expected_new_labels = {
            "development:catmap-microkinetics:script-test:"
            "test_source_pack_metadata.py",
            "development:deepmd-rigorous-workflows:script-test:"
            "test_source_pack_metadata.py",
            "development:dft-structure-preparation:script-test:"
            "test_source_pack_metadata.py",
            "development:gaussian-rigorous-calculations:unittest:"
            "test_official_document_seed.py",
            "development:gpumd-rigorous-simulations:script-test:"
            "test_source_pack_metadata.py",
            "development:gromacs-rigorous-simulations:script-test:"
            "test_source_pack_metadata.py",
            "development:lammps-rigorous-simulations:script-test:"
            "test_source_pack_metadata.py",
            "development:lasp-rigorous-simulations:unittest:"
            "test_official_document_seed.py",
            "development:lobster-bonding-analysis:unittest:"
            "test_official_document_seed.py",
            "development:multiwfn-wavefunction-analysis:script-test:"
            "test_source_pack_metadata.py",
            "development:ovito-atomistic-analysis:script-test:"
            "test_source_pack_metadata.py",
            "development:phonopy-rigorous-workflows:script-test:"
            "test_source_pack_metadata.py",
            "development:vaspkit-postprocess:script-test:"
            "test_source_pack_metadata.py",
        }
        labels = [command.label for command in plan.commands]
        behavioral_labels = [
            label for label in labels if ":compile:" not in label
        ]

        self.assertEqual(plan.skill_count, 19)
        self.assertEqual(plan.reviewed_hook_count, 41)
        self.assertEqual(len(plan.commands), 60)
        self.assertEqual(plan.skipped, ())
        self.assertEqual(len(behavioral_labels), plan.reviewed_hook_count)
        self.assertEqual(len(behavioral_labels), len(set(behavioral_labels)))
        self.assertLessEqual(expected_new_labels, set(behavioral_labels))


if __name__ == "__main__":
    unittest.main()
