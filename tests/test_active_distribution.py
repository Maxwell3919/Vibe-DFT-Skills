from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import build_distribution
from skill_registry import source_tree_digest


class DistributionBuilderTests(unittest.TestCase):
    def _skill(self, root: Path, name: str, text: str) -> str:
        source = root / "skills" / name
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text(text, encoding="utf-8")
        return source_tree_digest(source).sha256

    def _repository(self, root: Path) -> None:
        active_hash = self._skill(root, "active-skill", "active\n")
        development_hash = self._skill(root, "development-skill", "development\n")
        (root / "registry").mkdir()
        (root / "registry" / "skill-registry.yaml").write_text(
            "schema_version: \"1.0\"\n"
            "skills:\n"
            "  active-skill:\n"
            "    lifecycle: active\n"
            "    path: skills/active-skill\n"
            f"    source_tree_sha256: \"{active_hash}\"\n"
            "  development-skill:\n"
            "    lifecycle: development\n"
            "    path: skills/development-skill\n"
            f"    source_tree_sha256: \"{development_hash}\"\n",
            encoding="utf-8",
        )

    def test_distribution_contains_only_active_skill_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            self._repository(root)
            output = Path(temporary) / "dist"
            manifest = build_distribution.build_distribution(root, output)
            self.assertEqual(
                [item["skill_id"] for item in manifest["skills"]],
                ["active-skill"],
            )
            self.assertTrue((output / "skills" / "active-skill" / "SKILL.md").is_file())
            self.assertFalse((output / "skills" / "development-skill").exists())
            self.assertEqual(build_distribution.validate_distribution(root, output), [])

    def test_tampered_distribution_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            self._repository(root)
            output = Path(temporary) / "dist"
            build_distribution.build_distribution(root, output)
            (output / "skills" / "active-skill" / "SKILL.md").write_text(
                "tampered\n",
                encoding="utf-8",
            )
            errors = build_distribution.validate_distribution(root, output)
            self.assertTrue(any("mismatch" in error for error in errors))

    def test_registry_hash_drift_blocks_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            self._repository(root)
            registry = root / "registry" / "skill-registry.yaml"
            registry.write_text(
                registry.read_text(encoding="utf-8").replace(
                    source_tree_digest(root / "skills" / "active-skill").sha256,
                    "0" * 64,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(build_distribution.DistributionError):
                build_distribution.build_distribution(root, Path(temporary) / "dist")


if __name__ == "__main__":
    unittest.main()
