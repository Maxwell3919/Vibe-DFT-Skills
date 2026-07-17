from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_contract  # noqa: E402


class ContractTests(unittest.TestCase):
    def test_all_schemas_are_valid_draft_202012(self) -> None:
        for path in sorted((ROOT / "contracts").glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)

    def test_create_run_manifest_and_validate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run_manifest.json"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "create_run_manifest.py"),
                    "--code", "qe",
                    "--code-version", "7.5",
                    "--task-type", "scf",
                    "--case-id", "case-anon-001",
                    "--protocol-id", "protocol-001",
                    "--status", "completed",
                    "--scientific-acceptance", "not_assessed",
                    "--out", str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(validate_contract.validate_file("run", output), [])

    def test_invalid_run_manifest_is_rejected(self) -> None:
        failures = validate_contract.validation_errors("run", {"schema_version": "1.0"})
        self.assertTrue(failures)

    def test_install_dry_run_refuses_existing_real_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            target.joinpath("qe-rigorous-calculations").mkdir()
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "install_skills.py"), "--target", str(target), "--skill", "qe-rigorous-calculations", "--dry-run"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("refusing to replace existing path", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
