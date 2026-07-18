from __future__ import annotations

import copy
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
import audit_repository  # noqa: E402
import software_registry  # noqa: E402
import sync_contract_codes  # noqa: E402


class ContractTests(unittest.TestCase):
    def test_postprocess_core_schemas_are_registered(self) -> None:
        expected = {
            "dataset": "normalized-dataset.schema.json",
            "plan": "postprocess-plan.schema.json",
            "execution": "tool-execution.schema.json",
        }
        for kind, filename in expected.items():
            self.assertEqual(validate_contract.SCHEMAS[kind], filename)
            self.assertTrue(ROOT.joinpath("contracts", filename).is_file())

    def test_all_schemas_are_valid_draft_202012(self) -> None:
        for path in sorted((ROOT / "contracts").glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)

    def test_create_run_manifest_and_validate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run_manifest.json"
            evidence = Path(directory) / "evidence.json"
            evidence.write_text(
                json.dumps(
                    [
                        {
                            "role": "main-output",
                            "label": "anonymized terminal output",
                            "sha256": "0" * 64,
                            "status": "present",
                        }
                    ]
                ),
                encoding="utf-8",
            )
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
                    "--evidence", str(evidence),
                    "--out", str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(validate_contract.validate_file("run", output), [])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["evidence"][0]["role"], "main-output")

    def test_shared_run_manifest_accepts_all_calculation_codes(self) -> None:
        schema = json.loads((ROOT / "contracts" / "run-manifest.schema.json").read_text(encoding="utf-8"))
        registered = software_registry.calculation_codes()
        self.assertEqual(tuple(schema["properties"]["code"]["enum"]), registered)
        with tempfile.TemporaryDirectory() as directory:
            for code in registered:
                output = Path(directory) / f"{code}.json"
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "tools" / "create_run_manifest.py"),
                        "--code", code,
                        "--code-version", "test-version",
                        "--task-type", "static",
                        "--case-id", f"case-{code}-anonymous",
                        "--protocol-id", "protocol-test",
                        "--status", "completed",
                        "--scientific-acceptance", "not_assessed",
                        "--out", str(output),
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(validate_contract.validate_file("run", output), [])

    def test_software_registry_is_the_canonical_extension_point(self) -> None:
        registry = software_registry.load_registry()
        self.assertEqual(software_registry.validation_errors(registry, ROOT), [])
        extended = copy.deepcopy(registry)
        extended["software"]["abinit"] = {
            "display_name": "ABINIT",
            "calculation_skill": "abinit-rigorous-calculations",
            "capability_catalog": {
                "path": "references/task-evidence-profiles.json",
                "format": "json",
            },
            "lifecycle": "experimental",
            "interfaces": {
                "run_manifest": "required",
                "postprocess": "maturity-gated",
                "campaign_efficiency": "enabled",
            },
        }
        self.assertEqual(software_registry.validation_errors(extended), [])
        missing_skill = software_registry.validation_errors(extended, ROOT)
        self.assertTrue(any("abinit-rigorous-calculations" in item for item in missing_skill))

    def test_repository_interfaces_are_aligned(self) -> None:
        self.assertEqual(sync_contract_codes.contract_drift(ROOT), [])
        self.assertEqual(audit_repository.repository_errors(ROOT), [])

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

    def test_install_dry_run_accepts_cif_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "install_skills.py"),
                    "--target",
                    str(target),
                    "--skill",
                    "cif-structure-analysis",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("link", result.stdout)
            self.assertIn("cif-structure-analysis", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
