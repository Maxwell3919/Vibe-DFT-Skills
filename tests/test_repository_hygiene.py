from __future__ import annotations

import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import audit_hygiene  # noqa: E402


class RepositoryHygieneTests(unittest.TestCase):
    def _repository(self, *, planned: tuple[str, ...] = ()) -> tempfile.TemporaryDirectory[str]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        subprocess.run(
            ["git", "init", "--quiet", str(root)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        registry = root / "registry" / "skill-registry.yaml"
        registry.parent.mkdir(parents=True)
        entries = [
            "  active-skill:",
            "    lifecycle: active",
        ]
        for name in planned:
            entries.extend((f"  {name}:", "    lifecycle: planned"))
        registry.write_text(
            "schema_version: \"1.0\"\nskills:\n" + "\n".join(entries) + "\n",
            encoding="utf-8",
        )
        return temporary

    def test_finding_code_and_exit_status_contract_is_stable(self) -> None:
        self.assertEqual(audit_hygiene.EXIT_OK, 0)
        self.assertEqual(audit_hygiene.EXIT_FINDINGS, 2)
        self.assertEqual(audit_hygiene.COPY_SUFFIX_PATH, "HYGIENE_COPY_SUFFIX_PATH")
        self.assertEqual(
            audit_hygiene.DUPLICATE_FILE_IDENTICAL,
            "HYGIENE_DUPLICATE_FILE_IDENTICAL",
        )
        self.assertEqual(
            audit_hygiene.DUPLICATE_FILE_DIVERGED,
            "HYGIENE_DUPLICATE_FILE_DIVERGED",
        )
        self.assertEqual(
            audit_hygiene.EMPTY_COPIED_DIRECTORY,
            "HYGIENE_EMPTY_COPIED_DIRECTORY",
        )
        self.assertEqual(
            audit_hygiene.PLANNED_SKILL_DIRECTORY,
            "HYGIENE_PLANNED_SKILL_DIRECTORY",
        )
        self.assertEqual(
            audit_hygiene.VISIBLE_CACHE_ARTIFACT,
            "HYGIENE_VISIBLE_CACHE_ARTIFACT",
        )
        self.assertEqual(
            audit_hygiene.ABNORMAL_SKILL_FILENAME,
            "HYGIENE_ABNORMAL_SKILL_FILENAME",
        )
        self.assertEqual(audit_hygiene.GIT_SCAN_FAILED, "HYGIENE_GIT_SCAN_FAILED")
        self.assertEqual(
            audit_hygiene.SKILL_REGISTRY_INVALID,
            "HYGIENE_SKILL_REGISTRY_INVALID",
        )

    def test_identical_and_stale_duplicate_files_use_stable_codes(self) -> None:
        with self._repository() as temporary:
            root = Path(temporary)
            scripts = root / "skills" / "active-skill" / "scripts"
            references = root / "skills" / "active-skill" / "references"
            scripts.mkdir(parents=True)
            references.mkdir(parents=True)
            (scripts / "guard.py").write_text("print('same')\n", encoding="utf-8")
            (scripts / "guard 2.py").write_text("print('same')\n", encoding="utf-8")
            (references / "contract.md").write_text("current\n", encoding="utf-8")
            (references / "contract 2.md").write_text("stale\n", encoding="utf-8")
            (scripts / "phase_2.py").write_text("normal\n", encoding="utf-8")

            findings = audit_hygiene.audit_repository(root)
            by_path = {(finding.code, finding.path) for finding in findings}

            self.assertIn(
                (audit_hygiene.DUPLICATE_FILE_IDENTICAL, "skills/active-skill/scripts/guard 2.py"),
                by_path,
            )
            self.assertIn(
                (audit_hygiene.DUPLICATE_FILE_DIVERGED, "skills/active-skill/references/contract 2.md"),
                by_path,
            )
            self.assertFalse(any(finding.path.endswith("phase_2.py") for finding in findings))
            duplicate = next(
                finding
                for finding in findings
                if finding.path == "skills/active-skill/scripts/guard 2.py"
            )
            self.assertIn("sha256=", duplicate.detail)
            self.assertEqual(duplicate.related_path, "skills/active-skill/scripts/guard.py")

    def test_empty_copied_directory_and_planned_directory_are_rejected(self) -> None:
        with self._repository(planned=("future-skill",)) as temporary:
            root = Path(temporary)
            (root / "skills" / "active-skill" / "references" / "manual 2").mkdir(parents=True)
            (root / "skills" / "future-skill").mkdir(parents=True)

            findings = audit_hygiene.audit_repository(root)
            pairs = {(finding.code, finding.path) for finding in findings}

            self.assertIn(
                (
                    audit_hygiene.EMPTY_COPIED_DIRECTORY,
                    "skills/active-skill/references/manual 2",
                ),
                pairs,
            )
            self.assertIn(
                (audit_hygiene.PLANNED_SKILL_DIRECTORY, "skills/future-skill"),
                pairs,
            )

    def test_ignored_cache_is_opt_in_but_visible_cache_is_always_rejected(self) -> None:
        with self._repository() as temporary:
            root = Path(temporary)
            (root / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
            ignored = root / "skills" / "active-skill" / "scripts" / "__pycache__"
            ignored.mkdir(parents=True)
            (ignored / "guard.pyc").write_bytes(b"canonical")
            (ignored / "guard 2.pyc").write_bytes(b"copy")
            visible = root / "visible-cache.pyc"
            visible.write_bytes(b"tracked bytecode")
            subprocess.run(
                ["git", "-C", str(root), "add", "-f", "visible-cache.pyc"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            default_findings = audit_hygiene.audit_repository(root)
            included_findings = audit_hygiene.audit_repository(root, include_ignored=True)

            self.assertTrue(
                any(
                    finding.code == audit_hygiene.VISIBLE_CACHE_ARTIFACT
                    and finding.path == "visible-cache.pyc"
                    for finding in default_findings
                )
            )
            self.assertFalse(any("guard 2.pyc" in finding.path for finding in default_findings))
            self.assertTrue(
                any(
                    finding.code == audit_hygiene.DUPLICATE_FILE_DIVERGED
                    and finding.path.endswith("guard 2.pyc")
                    for finding in included_findings
                )
            )
            self.assertTrue(
                any(
                    finding.code == audit_hygiene.VISIBLE_CACHE_ARTIFACT
                    and finding.path.endswith("guard 2.pyc")
                    for finding in included_findings
                )
            )

    def test_abnormal_skill_filename_is_rejected_and_clean_names_pass(self) -> None:
        with self._repository() as temporary:
            root = Path(temporary)
            skill = root / "skills" / "active-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("canonical\n", encoding="utf-8")
            (skill / "SKILL 2.md").write_text("canonical\n", encoding="utf-8")
            (skill / "references").mkdir()
            (skill / "references" / "skill-notes.md").write_text("normal\n", encoding="utf-8")

            findings = audit_hygiene.audit_repository(root)

            self.assertTrue(
                any(
                    finding.code == audit_hygiene.ABNORMAL_SKILL_FILENAME
                    and finding.path == "skills/active-skill/SKILL 2.md"
                    for finding in findings
                )
            )
            self.assertFalse(any(finding.path.endswith("skill-notes.md") for finding in findings))

    def test_duplicate_registry_key_fails_closed_without_key_disclosure(self) -> None:
        with self._repository() as temporary:
            root = Path(temporary)
            registry = root / "registry" / "skill-registry.yaml"
            secret = "credential_token_do_not_echo"
            registry.write_text(
                f"schema_version: '1.0'\n{secret}: one\n{secret}: two\n",
                encoding="utf-8",
            )
            findings = audit_hygiene.audit_repository(root)
            invalid = [
                finding
                for finding in findings
                if finding.code == audit_hygiene.SKILL_REGISTRY_INVALID
            ]
            self.assertEqual(len(invalid), 1)
            self.assertIn("YAML_DUPLICATE_KEY", invalid[0].detail)
            self.assertNotIn(secret, invalid[0].detail)

    def test_cli_exit_codes_are_zero_for_clean_and_two_for_findings(self) -> None:
        with self._repository() as temporary:
            root = Path(temporary)
            clean_stderr = io.StringIO()
            clean_stdout = io.StringIO()
            with mock.patch("sys.stdout", clean_stdout), mock.patch("sys.stderr", clean_stderr):
                clean_code = audit_hygiene.main(["--root", str(root)])
            self.assertEqual(clean_code, audit_hygiene.EXIT_OK)
            self.assertIn("PASS", clean_stdout.getvalue())
            self.assertEqual(clean_stderr.getvalue(), "")

            (root / "script.py").write_text("current\n", encoding="utf-8")
            (root / "script 2.py").write_text("current\n", encoding="utf-8")
            dirty_stderr = io.StringIO()
            with mock.patch("sys.stderr", dirty_stderr):
                dirty_code = audit_hygiene.main(["--root", str(root)])
            self.assertEqual(dirty_code, audit_hygiene.EXIT_FINDINGS)
            self.assertIn(audit_hygiene.DUPLICATE_FILE_IDENTICAL, dirty_stderr.getvalue())

    def test_standalone_cli_does_not_create_bytecode_without_environment_policy(self) -> None:
        with self._repository() as temporary:
            root = Path(temporary)
            tools = root / "tools"
            tools.mkdir()
            shutil.copy2(ROOT / "tools" / "audit_hygiene.py", tools)
            shutil.copy2(ROOT / "tools" / "registry_yaml.py", tools)

            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            result = subprocess.run(
                [
                    sys.executable,
                    str(tools / "audit_hygiene.py"),
                    "--root",
                    str(root),
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            bytecode = sorted(
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}
            )

            self.assertEqual(result.returncode, audit_hygiene.EXIT_OK, result.stderr)
            self.assertEqual(bytecode, [])

    def test_repository_audit_entrypoint_does_not_create_import_bytecode(self) -> None:
        with self._repository() as temporary:
            root = Path(temporary)
            tools = root / "tools"
            tools.mkdir()
            for name in ("audit_repository.py", "audit_hygiene.py", "registry_yaml.py"):
                shutil.copy2(ROOT / "tools" / name, tools)
            stubs = {
                "skill_registry.py": (
                    "def planned_skill_names(*args, **kwargs): return ()\n"
                    "def validate_active_sources(*args, **kwargs): return ()\n"
                ),
                "registry_snapshot.py": (
                    "class RegistrySnapshot: pass\n"
                    "class RegistrySnapshotError(Exception): pass\n"
                    "def load_registry_snapshot(*args, **kwargs): return RegistrySnapshot()\n"
                ),
                "software_registry.py": "def repo_root(): raise AssertionError('not called')\n",
                "sync_contract_codes.py": "CONTRACT_CODE_KINDS = {}\n",
                "validate_contract.py": (
                    "class CatalogError(Exception): pass\n"
                    "def load_catalog(*args, **kwargs): raise AssertionError('not called')\n"
                ),
                "strict_json.py": (
                    "class StrictJSONError(ValueError): pass\n"
                    "def load_object(*args, **kwargs): raise AssertionError('not called')\n"
                ),
            }
            for name, content in stubs.items():
                (tools / name).write_text(content, encoding="utf-8")

            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            result = subprocess.run(
                [sys.executable, str(tools / "audit_repository.py"), "--help"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            bytecode = sorted(
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--check-installed", result.stdout)
            self.assertEqual(bytecode, [])


if __name__ == "__main__":
    unittest.main()
