from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
