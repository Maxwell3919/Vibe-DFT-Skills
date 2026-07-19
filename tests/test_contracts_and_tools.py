from __future__ import annotations

import copy
import json
import os
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
import skill_registry  # noqa: E402
import software_registry  # noqa: E402
from registry_yaml import load_yaml_strict  # noqa: E402
import sync_contract_codes  # noqa: E402


class ContractTests(unittest.TestCase):
    def test_postprocess_core_schemas_are_registered(self) -> None:
        expected = {
            "dataset": "normalized-dataset.schema.json",
            "plan": "postprocess-plan.schema.json",
            "execution": "tool-execution.schema.json",
            "structure": "structure-manifest.schema.json",
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

    def test_software_registry_is_the_canonical_provider_mapping(self) -> None:
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

    def test_planned_software_is_excluded_from_active_interfaces(self) -> None:
        registry = software_registry.load_registry()
        active_codes = set(software_registry.calculation_codes())
        planned_codes = set(software_registry.planned_software_codes())
        self.assertTrue({"gaussian", "lammps", "phonopy", "mace"}.issubset(planned_codes))
        self.assertFalse(active_codes.intersection(planned_codes))
        self.assertIn("gaussian-rigorous-calculations", software_registry.planned_skill_names())
        self.assertNotIn("gaussian-rigorous-calculations", skill_registry.active_skill_names())
        schema = json.loads((ROOT / "contracts" / "run-manifest.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(schema["properties"]["code"]["enum"]), active_codes)
        self.assertFalse(planned_codes.intersection(schema["properties"]["code"]["enum"]))
        self.assertEqual(registry["planned_software"]["vaspkit"]["lifecycle"], "planned")

    def test_planned_software_requires_an_activation_profile_and_planned_lifecycle(self) -> None:
        registry = software_registry.load_registry()
        invalid_profile = copy.deepcopy(registry)
        invalid_profile["planned_software"]["gaussian"]["activation_profile"] = "missing-profile"
        self.assertTrue(
            any("must equal provider role" in item for item in software_registry.validation_errors(invalid_profile))
        )
        invalid_lifecycle = copy.deepcopy(registry)
        invalid_lifecycle["planned_software"]["gaussian"]["lifecycle"] = "active"
        self.assertTrue(
            any("expected 'planned'" in item for item in software_registry.validation_errors(invalid_lifecycle))
        )

    def test_skill_registry_separates_active_development_and_planned_routes(self) -> None:
        registry = skill_registry.load_registry()
        software = software_registry.load_registry()
        interfaces = load_yaml_strict(ROOT / "registry" / "interface-registry.yaml")
        environments = load_yaml_strict(ROOT / "registry" / "environment-profiles.yaml")
        self.assertEqual(
            skill_registry.validation_errors(
                registry,
                software_data=software,
                interface_data=interfaces,
                environment_data=environments,
            ),
            [],
        )
        active = {
            name for name, entry in registry["skills"].items() if entry["lifecycle"] == "active"
        }
        development = {
            name for name, entry in registry["skills"].items() if entry["lifecycle"] == "development"
        }
        planned = {
            name for name, entry in registry["skills"].items() if entry["lifecycle"] == "planned"
        }
        self.assertEqual(active, set(skill_registry.active_skill_names()))
        self.assertEqual(development, set(skill_registry.development_skill_names()))
        self.assertEqual(
            active,
            {
                "cif-structure-analysis",
                "qe-rigorous-calculations",
                "vasp-rigorous-calculations",
                "cp2k-rigorous-calculations",
                "siesta-rigorous-calculations",
                "dft-postprocess",
                "dft-campaign-efficiency",
            },
        )
        self.assertIn("dft-project-orchestrator", development)
        self.assertIn("gaussian-rigorous-calculations", development)
        self.assertEqual(planned, set())
        self.assertFalse(active.intersection(development))
        self.assertTrue(
            all(registry["skills"][name]["path"] == f"skills/{name}" for name in development)
        )

        missing_source_path = copy.deepcopy(registry)
        missing_source_path["skills"]["gaussian-rigorous-calculations"]["path"] = None
        self.assertTrue(
            any(
                "development skill must use" in item
                for item in skill_registry.validation_errors(missing_source_path)
            )
        )

    def test_repository_interfaces_are_aligned(self) -> None:
        self.assertEqual(sync_contract_codes.contract_drift(ROOT), [])
        self.assertEqual(audit_repository.repository_errors(ROOT), [])

    def test_capability_catalog_json_is_strict_and_object_rooted(self) -> None:
        cases = {
            "duplicate": b'{"schema_version":"1.0","profiles":{},"profiles":{"x":{}}}',
            "bom": b'\xef\xbb\xbf{"schema_version":"1.0","profiles":{"x":{}}}',
            "nan": b'{"schema_version":"1.0","profiles":{"x":NaN}}',
            "array": b'[]',
        }
        for label, raw in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "catalog.json"
                path.write_bytes(raw)
                failures = audit_repository.capability_catalog_errors(path)
                self.assertTrue(failures)
                self.assertTrue(
                    any(
                        marker in " ".join(failures)
                        for marker in ("duplicate", "BOM", "non-finite", "root")
                    )
                )

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

    def test_install_accepts_tool_agnostic_target_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["VIBE_DFT_SKILLS_TARGET"] = directory
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "install_skills.py"),
                    "--skill",
                    "cif-structure-analysis",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(directory, result.stdout)

    def test_install_requires_an_explicit_target(self) -> None:
        environment = os.environ.copy()
        environment.pop("VIBE_DFT_SKILLS_TARGET", None)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "install_skills.py"),
                "--skill",
                "cif-structure-analysis",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            env=environment,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--target is required", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
