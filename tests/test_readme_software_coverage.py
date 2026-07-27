from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_readme_software_coverage as readme_coverage  # noqa: E402


class ReadmeSoftwareCoverageTests(unittest.TestCase):
    def _validate_mutation(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory(prefix="readme-coverage-test-") as temporary:
            readme = Path(temporary) / "README.md"
            readme.write_text(text, encoding="utf-8")
            return readme_coverage.validation_errors(ROOT, readme_path=readme)

    def test_repository_readme_is_complete(self) -> None:
        self.assertEqual(readme_coverage.validation_errors(ROOT), [])

    def test_missing_registered_software_row_fails(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        mutated = text.replace("| `qe` · ", "| `qe-missing` · ", 1)
        failures = self._validate_mutation(mutated)
        self.assertTrue(any("software 'qe' appears in 0 landscape rows" in item for item in failures))

    def test_missing_direct_requirement_acknowledgement_fails(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        mutated = text.replace("(`numpy`)", "(`array-library`)", 1)
        failures = self._validate_mutation(mutated)
        self.assertTrue(
            any("requirement 'numpy' appears 0 times" in item for item in failures)
        )

    def test_templated_contrast_prose_fails(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        failures = self._validate_mutation(text + "\n这不是一个记录，而是一个平台。\n")
        self.assertTrue(any("templated prose" in item for item in failures))

    def test_extra_status_column_fails(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        mutated = text.replace(
            readme_coverage.SOFTWARE_TABLE_HEADER,
            "| 软件 | 数值方法或科学角色 | 代表性任务 | Lifecycle |",
            1,
        )
        failures = self._validate_mutation(mutated)
        self.assertTrue(any("non-canonical software table header" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
