from __future__ import annotations

from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
import io
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import validate_all_skills  # noqa: E402


class ValidateAllSkillsStrictInputTests(unittest.TestCase):
    def make_skill(self, directory: str, frontmatter: str, body: str = "# Test\n") -> Path:
        skill = Path(directory) / "test-skill"
        skill.mkdir()
        skill.joinpath("SKILL.md").write_text(
            f"---\n{frontmatter}\n---\n{body}",
            encoding="utf-8",
        )
        agents = skill / "agents"
        agents.mkdir()
        agents.joinpath("openai.yaml").write_text(
            "interface:\n"
            "  short_description: A sufficiently descriptive local test interface\n"
            "  default_prompt: Use $test-skill for this isolated validation test.\n",
            encoding="utf-8",
        )
        return skill

    def test_frontmatter_duplicate_unsafe_tag_and_nonmapping_fail_closed(self) -> None:
        cases = {
            "duplicate": (
                "name: test-skill\n"
                "description: A long deterministic description used only for strict validation coverage.\n"
                "description: A second value must never override the first one."
            ),
            "unsafe": "name: !!python/object/apply:os.system [echo]\ndescription: invalid",
            "nonmapping": "- name: test-skill\n- description: invalid sequence root",
        }
        for label, frontmatter in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                skill = self.make_skill(directory, frontmatter)
                failures = validate_all_skills.validate_skill(skill)
                self.assertTrue(any("frontmatter" in item for item in failures))

    def test_skill_markdown_rejects_bom_invalid_utf8_and_root_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            valid = (
                "name: test-skill\n"
                "description: A long deterministic description used only for strict validation coverage."
            )
            skill = self.make_skill(directory, valid, "[escape](/etc/passwd)\n")
            self.assertTrue(
                any("escapes the Skill root" in item for item in validate_all_skills.validate_skill(skill))
            )

            skill.joinpath("SKILL.md").write_bytes(b"\xef\xbb\xbf---\n")
            self.assertTrue(any("BOM" in item for item in validate_all_skills.validate_skill(skill)))

            skill.joinpath("SKILL.md").write_bytes(b"\xff")
            self.assertTrue(
                any("strict UTF-8" in item for item in validate_all_skills.validate_skill(skill))
            )

    def test_main_runs_official_document_audit_and_preserves_strict_exit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            valid = (
                "name: test-skill\n"
                "description: A deliberately long deterministic description used only to exercise "
                "strict repository validation and official-document release-gate integration."
            )
            self.make_skill(str(root / "skills"), valid)
            with (
                mock.patch.object(
                    validate_all_skills,
                    "validate_source_skills",
                    return_value=("test-skill",),
                ),
                mock.patch.object(
                    validate_all_skills.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 0),
                ),
                mock.patch.object(
                    validate_all_skills.official_document_bundles,
                    "run_audit",
                    return_value=3,
                ) as audit,
                mock.patch.object(
                    validate_all_skills.official_document_storage,
                    "run_audit",
                    return_value=0,
                ) as storage_audit,
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                status = validate_all_skills.main(
                    [
                        "--strict-release",
                        "--baseline-ref",
                        "synthetic-base",
                    ],
                    root=root,
                )

        self.assertEqual(status, 3)
        audit.assert_called_once_with(
            root,
            strict_release=True,
            baseline_ref="synthetic-base",
        )
        storage_audit.assert_called_once_with(
            root,
            strict_release=True,
            baseline_ref="synthetic-base",
        )

    def test_main_preserves_strict_storage_blocker_after_complete_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            valid = (
                "name: test-skill\n"
                "description: A deliberately long deterministic description used only to exercise "
                "strict repository validation and official-document storage integration."
            )
            self.make_skill(str(root / "skills"), valid)
            with (
                mock.patch.object(
                    validate_all_skills,
                    "validate_source_skills",
                    return_value=("test-skill",),
                ),
                mock.patch.object(
                    validate_all_skills.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 0),
                ),
                mock.patch.object(
                    validate_all_skills.official_document_bundles,
                    "run_audit",
                    return_value=0,
                ),
                mock.patch.object(
                    validate_all_skills.official_document_storage,
                    "run_audit",
                    return_value=3,
                ),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                status = validate_all_skills.main(
                    ["--strict-release"],
                    root=root,
                )

        self.assertEqual(status, 3)

    def test_main_checks_generated_packs_before_bundle_and_storage_audits(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            valid = (
                "name: test-skill\n"
                "description: A deliberately long deterministic description used only to exercise "
                "the generated pack freshness check ordering."
            )
            self.make_skill(str(root / "skills"), valid)
            order: list[str] = []

            def run_builder(
                *args: object,
                **kwargs: object,
            ) -> subprocess.CompletedProcess[object]:
                order.append("builder")
                return subprocess.CompletedProcess(args[0], 0)

            def run_bundle(*args: object, **kwargs: object) -> int:
                order.append("bundle")
                return 0

            def run_storage(*args: object, **kwargs: object) -> int:
                order.append("storage")
                return 0

            with (
                mock.patch.object(
                    validate_all_skills,
                    "validate_source_skills",
                    return_value=("test-skill",),
                ),
                mock.patch.object(
                    validate_all_skills.subprocess,
                    "run",
                    side_effect=run_builder,
                ) as builder_check,
                mock.patch.object(
                    validate_all_skills.official_document_bundles,
                    "run_audit",
                    side_effect=run_bundle,
                ),
                mock.patch.object(
                    validate_all_skills.official_document_storage,
                    "run_audit",
                    side_effect=run_storage,
                ),
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                status = validate_all_skills.main([], root=root)

        self.assertEqual(status, 0)
        self.assertEqual(order, ["builder", "bundle", "storage"])
        builder_check.assert_called_once_with(
            [
                sys.executable,
                str(ROOT / "tools" / "build_official_document_packs.py"),
                "--all",
                "--check",
                "--root",
                str(root.resolve()),
            ],
            cwd=root.resolve(),
            check=False,
        )

    def test_main_propagates_pack_builder_failure_before_audits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            valid = (
                "name: test-skill\n"
                "description: A deliberately long deterministic description used only to exercise "
                "fail-closed generated pack validation."
            )
            self.make_skill(str(root / "skills"), valid)
            with (
                mock.patch.object(
                    validate_all_skills,
                    "validate_source_skills",
                    return_value=("test-skill",),
                ),
                mock.patch.object(
                    validate_all_skills.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 7),
                ),
                mock.patch.object(
                    validate_all_skills.official_document_bundles,
                    "run_audit",
                ) as bundle_audit,
                mock.patch.object(
                    validate_all_skills.official_document_storage,
                    "run_audit",
                ) as storage_audit,
                redirect_stdout(io.StringIO()),
                redirect_stderr(io.StringIO()),
            ):
                status = validate_all_skills.main([], root=root)

        self.assertEqual(status, 7)
        bundle_audit.assert_not_called()
        storage_audit.assert_not_called()

    def test_main_fails_closed_when_pack_builder_cannot_start(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            valid = (
                "name: test-skill\n"
                "description: A deliberately long deterministic description used only to exercise "
                "the generated pack subprocess launch boundary."
            )
            self.make_skill(str(root / "skills"), valid)
            stderr = io.StringIO()
            with (
                mock.patch.object(
                    validate_all_skills,
                    "validate_source_skills",
                    return_value=("test-skill",),
                ),
                mock.patch.object(
                    validate_all_skills.subprocess,
                    "run",
                    side_effect=OSError("synthetic launch failure"),
                ),
                mock.patch.object(
                    validate_all_skills.official_document_bundles,
                    "run_audit",
                ) as bundle_audit,
                mock.patch.object(
                    validate_all_skills.official_document_storage,
                    "run_audit",
                ) as storage_audit,
                redirect_stdout(io.StringIO()),
                redirect_stderr(stderr),
            ):
                status = validate_all_skills.main([], root=root)

        self.assertEqual(status, 2)
        self.assertIn(
            "official-document pack freshness check could not run: OSError",
            stderr.getvalue(),
        )
        bundle_audit.assert_not_called()
        storage_audit.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
