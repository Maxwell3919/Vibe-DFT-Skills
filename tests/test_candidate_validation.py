from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from jsonschema import Draft202012Validator, FormatChecker
import yaml


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools" / "validate_candidate.py"
REPORT_SCHEMA = json.loads((ROOT / "contracts" / "validation-report.schema.json").read_text(encoding="utf-8"))
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_candidate  # noqa: E402


SKILL = "candidate-rigorous-calculations"
CODE = "candidate-code"
SEATBELT_AVAILABLE = validate_candidate.seatbelt_backend_identity() is not None
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dump_yaml(path: Path, value: object) -> None:
    write_text(path, yaml.safe_dump(value, sort_keys=False, allow_unicode=True))


def dump_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


class CandidateValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.repo = self.base / "repo"
        self.candidate = self.repo / "candidates" / SKILL
        self.report = self.base / "candidate-report.json"
        self.changed = self.base / "changed-files.json"
        self._create_valid_repository()

    def _create_valid_repository(self) -> None:
        active_source = self.repo / "skills" / "active-skill"
        write_text(active_source / "SKILL.md", "# Active Skill\n")
        active_hash = validate_candidate.source_tree_digest(active_source).sha256
        skill_registry = {
            "schema_version": "1.0",
            "skills": {
                "active-skill": {
                    "display_name": "Active Skill",
                    "kind": "calculation",
                    "lifecycle": "active",
                    "path": "skills/active-skill",
                    "source_tree_sha256": active_hash,
                    "side_effects": ["local-write"],
                    "consumes": [],
                    "produces": ["run-manifest@1.0"],
                    "activation_requirements": {
                        "software_profiles": [],
                        "interface_ids": [],
                        "activation_check_ids": [],
                        "task_catalog_ids": [],
                    },
                },
                SKILL: {
                    "display_name": "Candidate Skill",
                    "kind": "calculation",
                    "lifecycle": "planned",
                    "path": None,
                    "source_tree_sha256": None,
                    "side_effects": ["local-write"],
                    "consumes": [],
                    "produces": ["run-manifest@1.0"],
                    "activation_requirements": {
                        "software_profiles": [],
                        "interface_ids": ["run-manifest@1.0"],
                        "activation_check_ids": [
                            "identity-and-routing",
                            "primary-source-provenance",
                            "capability-boundary",
                            "deterministic-gates",
                            "lineage-and-hashes",
                            "scientific-gate-separation",
                            "shared-interfaces",
                            "side-effect-boundary",
                            "idempotency-recovery-cancel",
                            "validation-evidence",
                            "privacy-and-license",
                            "portability-and-environment",
                            "maintenance-and-forward-test",
                        ],
                        "task_catalog_ids": [],
                    },
                },
            },
        }
        software_registry = {
            "schema_version": "1.0",
            "aggregate_codes": ["mixed"],
            "software": {
                "qe": {
                    "display_name": "QE",
                    "calculation_skill": "active-skill",
                    "capability_catalog": {
                        "path": "references/fail-closed-contract.md",
                        "format": "markdown",
                    },
                    "lifecycle": "active",
                    "interfaces": {
                        "run_manifest": "required",
                        "postprocess": "maturity-gated",
                        "campaign_efficiency": "enabled",
                    },
                }
            },
            "planned_software": {
                CODE: {
                    "display_name": "Candidate Code",
                    "role": "calculation-engine",
                    "scope": "dft-core",
                    "intended_integration": "calculation-skill",
                    "intended_skill": SKILL,
                    "activation_profile": "calculation-engine",
                    "environment_profiles": {
                        "selection_policy": "all_of",
                        "profile_ids": ["candidate-code-test"],
                    },
                    "required_check_ids": [
                        "identity-and-routing",
                        "primary-source-provenance",
                        "capability-boundary",
                        "deterministic-gates",
                        "lineage-and-hashes",
                        "scientific-gate-separation",
                        "shared-interfaces",
                        "side-effect-boundary",
                        "idempotency-recovery-cancel",
                        "validation-evidence",
                        "privacy-and-license",
                        "portability-and-environment",
                        "maintenance-and-forward-test",
                    ],
                    "lifecycle": "planned",
                }
            },
        }
        dump_yaml(self.repo / "registry" / "skill-registry.yaml", skill_registry)
        dump_yaml(self.repo / "registry" / "software-registry.yaml", software_registry)
        dump_yaml(
            self.repo / "registry" / "operation-routes.yaml",
            {
                "schema_version": "1.0",
                "routes": {
                    SKILL: {
                        "lifecycle": "planned",
                        "routable": False,
                        "first_tool": {},
                        "tool_sequence": {},
                        "actions": {},
                    }
                },
            },
        )
        dump_json(
            self.repo / "contracts" / "run-manifest.schema.json",
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"code": {"enum": ["qe"]}},
            },
        )
        dump_yaml(
            self.repo / "skills" / "dft-postprocess" / "references" / "observable-registry.yaml",
            {
                "schema_version": "1.0",
                "backends": {"python.qe": {"kind": "builtin-python", "implemented": True}},
                "observables": {
                    "bands": {
                        "codes": {
                            "qe": {"maturity": "real-artifact-validated", "backends": ["python.qe"]}
                        }
                    }
                },
            },
        )
        description = (
            "Use this candidate to design and audit a narrow deterministic calculation route with "
            "versioned evidence, fail-closed decisions, and explicit scientific limitations."
        )
        write_text(
            self.candidate / "SKILL.md",
            "---\n"
            f"name: {SKILL}\n"
            f"description: {description}\n"
            "---\n\n"
            "# Candidate workflow\n\n"
            "Read [the contract](references/contract.md), then run the deterministic checker.\n",
        )
        write_text(
            self.candidate / "references" / "contract.md",
            "# Contract\n\nMissing evidence blocks every positive conclusion.\n",
        )
        write_text(
            self.candidate / "scripts" / "candidate_guard.py",
            "def validate(value: object) -> bool:\n    return isinstance(value, dict)\n",
        )
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "import unittest\n\n"
            "class SmokeTests(unittest.TestCase):\n"
            "    def test_true(self):\n"
            "        self.assertTrue(True)\n\n"
            "if __name__ == '__main__':\n"
            "    unittest.main()\n",
        )
        dump_json(
            self.changed,
            {
                "changed_files": [
                    f"candidates/{SKILL}/SKILL.md",
                    f"candidates/{SKILL}/references/contract.md",
                    f"candidates/{SKILL}/scripts/candidate_guard.py",
                    f"candidates/{SKILL}/tests/test_smoke.py",
                ]
            },
        )

    def _run(
        self,
        *,
        level: str = "L1",
        use_changed_fixture: bool = True,
        base_ref: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        command = [
            sys.executable,
            str(CLI),
            "--skill",
            SKILL,
            "--candidate-dir",
            str(self.candidate),
            "--level",
            level,
            "--report",
            str(self.report),
        ]
        if use_changed_fixture:
            command.extend(["--changed-files", str(self.changed)])
        if base_ref is not None:
            command.extend(["--base-ref", base_ref])
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        return result, report

    @staticmethod
    def _codes(report: dict) -> dict[str, str]:
        return {item["check_id"]: item["status"] for item in report["checks"]}

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_planned_candidate_passes_l1_with_strict_redacted_report(self) -> None:
        result, report = self._run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        Draft202012Validator(REPORT_SCHEMA, format_checker=FormatChecker()).validate(report)
        self.assertEqual(report["contract_name"], "validation-report")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["routing_state"], "planned-not-routable")
        self.assertIs(report["promotion_authorized"], False)
        self.assertEqual(report["requested_level"], "L1")
        self.assertEqual(report["subject"]["candidate_label"], f"candidates/{SKILL}")
        self.assertEqual(report["source"]["changed_files_mode"], "fixture")
        self.assertEqual(report["summary"]["total"], len(report["checks"]))
        self.assertEqual(self._codes(report)["CANDIDATE.TESTS.RESULT"], "pass")
        self.assertEqual(self._codes(report)["CANDIDATE.TESTS.ISOLATION_BACKEND"], "pass")
        boundary = report["execution_boundary"]
        self.assertIs(boundary["report_is_complete_security_sandbox"], False)
        self.assertEqual(boundary["backend_status"], "enforced")
        self.assertEqual(boundary["backend_id"], "macos-seatbelt-sandbox-exec")
        self.assertTrue(boundary["backend_version"].startswith("macos-"))
        for field in (
            "backend_sha256",
            "profile_sha256",
            "source_tree_sha256",
            "isolated_copy_sha256",
            "enforcement_probe_sha256",
        ):
            self.assertRegex(boundary[field], SHA256, field)
        self.assertEqual(boundary["source_tree_sha256"], boundary["isolated_copy_sha256"])
        self.assertEqual(boundary["enforcement_probe_status"], "pass")
        for field in (
            "workspace_io_enforcement",
            "host_read_enforcement",
            "host_write_enforcement",
            "network_enforcement",
            "subprocess_inheritance_enforcement",
        ):
            self.assertEqual(boundary[field], "pass", field)
        self.assertEqual(boundary["process_resource_limits_status"], "applied")
        self.assertRegex(boundary["process_resource_limits_sha256"], SHA256)
        self.assertEqual(boundary["process_new_session_status"], "applied")
        self.assertEqual(
            boundary["candidate_test_execution"],
            "attempted-under-enforced-backend",
        )
        self.assertTrue(
            any("not a complete security sandbox" in item for item in report["limitations"])
        )
        rendered = json.dumps(report, sort_keys=True)
        self.assertNotIn(str(self.repo), rendered)
        self.assertNotIn(str(self.repo), result.stdout)
        self.assertNotIn(str(self.repo), result.stderr)

    def test_active_installable_code_enum_and_executable_routes_are_rejected(self) -> None:
        active_candidate = self.repo / "skills" / SKILL
        validate_candidate.copy_candidate_tree(self.candidate, active_candidate)
        skills = yaml.safe_load((self.repo / "registry" / "skill-registry.yaml").read_text())
        skills["skills"][SKILL]["lifecycle"] = "active"
        skills["skills"][SKILL]["path"] = f"skills/{SKILL}"
        skills["skills"][SKILL]["source_tree_sha256"] = validate_candidate.source_tree_digest(
            active_candidate
        ).sha256
        skills["skills"][SKILL]["activation_requirements"] = {
            "software_profiles": [],
            "interface_ids": [],
            "activation_check_ids": [],
            "task_catalog_ids": [],
        }
        dump_yaml(self.repo / "registry" / "skill-registry.yaml", skills)

        schema = json.loads((self.repo / "contracts" / "run-manifest.schema.json").read_text())
        schema["properties"]["code"]["enum"].append(CODE)
        dump_json(self.repo / "contracts" / "run-manifest.schema.json", schema)

        dump_yaml(
            self.repo / "skills" / "dft-postprocess" / "references" / "observable-registry.yaml",
            {
                "schema_version": "1.0",
                "backends": {f"{CODE}.tool": {"kind": "external-executable", "implemented": True}},
                "observables": {
                    "bands": {"codes": {CODE: {"backends": [f"{CODE}.tool"]}}}
                },
            },
        )
        dump_yaml(
            self.repo / "registry" / "operation-routes.yaml",
            {
                "schema_version": "1.0",
                "routes": {
                    SKILL: {
                        "lifecycle": "active",
                        "routable": True,
                        "first_tool": {"design": f"{CODE}.run"},
                        "tool_sequence": {"design": [f"{CODE}.run"]},
                        "actions": {
                            f"{CODE}.run": {
                                "argv": ["python3", "candidate.py"],
                                "success_exit_codes": [0],
                                "limited_exit_codes": [],
                                "side_effect": "local-write",
                                "requires_authorization": False,
                                "maximum_claim": "no-positive-claim",
                            }
                        },
                    }
                },
            },
        )
        result, report = self._run(level="L0")
        self.assertEqual(result.returncode, 2)
        codes = self._codes(report)
        for code in (
            "CANDIDATE.REGISTRY.PLANNED",
            "CANDIDATE.REGISTRY.PATH_NULL",
            "CANDIDATE.ROUTING.ACTIVE",
            "CANDIDATE.ROUTING.INSTALL",
            "CANDIDATE.ROUTING.CODE_ENUM",
            "CANDIDATE.ROUTING.OBSERVABLE",
            "CANDIDATE.ROUTING.OPERATION",
        ):
            self.assertEqual(codes[code], "fail", code)
        self.assertIs(report["promotion_authorized"], False)

    def test_design_only_unimplemented_observable_reservation_is_not_executable_exposure(self) -> None:
        observable = self.repo / "skills" / "dft-postprocess" / "references" / "observable-registry.yaml"
        dump_yaml(
            observable,
            {
                "schema_version": "1.0",
                "backends": {
                    f"phonon.{CODE}": {
                        "kind": "external-executable",
                        "capability_key": f"phonon.{CODE}",
                    }
                },
                "observables": {
                    "phonon": {
                        "codes": {
                            CODE: {
                                "maturity": "design-only",
                                "backends": [f"phonon.{CODE}"],
                            }
                        }
                    }
                },
            },
        )

        check = validate_candidate.check_observable_routes(self.repo, SKILL, {CODE})

        self.assertEqual(check.status, "pass")

    def test_non_design_candidate_code_route_and_implemented_backend_are_exposure(self) -> None:
        observable = self.repo / "skills" / "dft-postprocess" / "references" / "observable-registry.yaml"
        dump_yaml(
            observable,
            {
                "schema_version": "1.0",
                "backends": {
                    f"phonon.{CODE}": {
                        "kind": "external-executable",
                        "capability_key": f"phonon.{CODE}",
                        "implemented": True,
                    }
                },
                "observables": {
                    "phonon": {
                        "codes": {
                            CODE: {
                                "maturity": "synthetic-validated",
                                "backends": [f"phonon.{CODE}"],
                            }
                        }
                    }
                },
            },
        )

        check = validate_candidate.check_observable_routes(self.repo, SKILL, {CODE})

        self.assertEqual(check.status, "fail")

    def test_shared_file_ownership_violation_is_rejected(self) -> None:
        dump_json(
            self.changed,
            {
                "changed_files": [
                    f"candidates/{SKILL}/SKILL.md",
                    "registry/skill-registry.yaml",
                ]
            },
        )
        result, report = self._run(level="L0")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            self._codes(report)["CANDIDATE.OWNERSHIP.CHANGED_FILES"],
            "fail",
        )
        self.assertNotIn(str(self.repo), json.dumps(report))

    def test_dangerous_execution_surfaces_have_stable_finding_codes(self) -> None:
        write_text(
            self.candidate / "scripts" / "unsafe.py",
            "import os\n"
            "import pickle\n"
            "import subprocess\n\n"
            "eval('1')\n"
            "exec('value = 1')\n"
            "os.system('true')\n"
            "subprocess.run(['ssh', 'example.invalid'], shell=True)\n"
            "pickle.loads(b'not-a-pickle')\n",
        )
        result, report = self._run(level="L0")
        self.assertEqual(result.returncode, 2)
        codes = self._codes(report)
        for code in (
            "CANDIDATE.SAFETY.EVAL",
            "CANDIDATE.SAFETY.EXEC",
            "CANDIDATE.SAFETY.OS_SYSTEM",
            "CANDIDATE.SAFETY.SHELL_TRUE",
            "CANDIDATE.SAFETY.SSH",
            "CANDIDATE.SAFETY.PICKLE_LOAD",
        ):
            self.assertEqual(codes[code], "fail", code)

    def test_process_control_surfaces_block_execution_with_stable_codes(self) -> None:
        write_text(
            self.candidate / "scripts" / "process_control.py",
            "import ctypes\n"
            "import multiprocessing\n"
            "import os\n"
            "import resource\n"
            "import signal\n"
            "import subprocess\n\n"
            "os.kill(1, 0)\n"
            "os.killpg(1, 0)\n"
            "os.fork()\n"
            "os.posix_spawn('/usr/bin/true', ['/usr/bin/true'], {})\n"
            "signal.pthread_kill(1, 0)\n"
            "resource.setrlimit(resource.RLIMIT_CPU, (1, 1))\n"
            "subprocess.run(['/bin/kill', '-0', '1'], check=False)\n"
            "subprocess.run(['/usr/bin/true'], start_new_session=True, check=False)\n"
            "subprocess.Popen(['/usr/bin/true'], process_group=0)\n",
        )

        result, report = self._run(level="L0")

        self.assertEqual(result.returncode, 2)
        codes = self._codes(report)
        for code in (
            "CANDIDATE.SAFETY.PROCESS_SIGNAL",
            "CANDIDATE.SAFETY.PROCESS_SPAWN",
            "CANDIDATE.SAFETY.MULTIPROCESSING",
            "CANDIDATE.SAFETY.CTYPES",
            "CANDIDATE.SAFETY.RESOURCE_CONTROL",
        ):
            self.assertEqual(codes[code], "fail", code)
        self.assertEqual(codes["CANDIDATE.TESTS.RESULT"], "not-run")

    def test_candidates_root_is_canonical_and_same_name_active_collision_is_rejected(self) -> None:
        collision = self.repo / "skills" / SKILL
        write_text(collision / "SKILL.md", "# Forbidden active collision\n")

        result, report = self._run(level="L0")

        self.assertEqual(result.returncode, 2)
        codes = self._codes(report)
        self.assertEqual(codes["CANDIDATE.IDENTITY.DIRECTORY"], "pass")
        self.assertEqual(codes["CANDIDATE.IDENTITY.ACTIVE_COLLISION"], "fail")
        self.assertEqual(report["subject"]["candidate_label"], f"candidates/{SKILL}")

    def test_legacy_skills_root_candidate_is_not_accepted(self) -> None:
        legacy = self.repo / "skills" / SKILL
        write_text(legacy / "SKILL.md", (self.candidate / "SKILL.md").read_text(encoding="utf-8"))

        report = validate_candidate.validate_candidate(
            SKILL,
            legacy,
            "L0",
            changed_fixture=self.changed,
        )
        validate_candidate.validate_report(report)

        codes = self._codes(report)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(codes["CANDIDATE.IDENTITY.DIRECTORY"], "fail")
        self.assertEqual(codes["CANDIDATE.IDENTITY.ACTIVE_COLLISION"], "fail")

    def test_duplicate_skill_registry_key_fails_closed(self) -> None:
        registry = self.repo / "registry" / "skill-registry.yaml"
        with registry.open("a", encoding="utf-8") as handle:
            handle.write("\nskills: {}\n")

        result, report = self._run(level="L0")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            self._codes(report)["CANDIDATE.REGISTRY.SKILL_REGISTRY"],
            "fail",
        )

    def test_changed_files_fixture_uses_strict_bounded_json(self) -> None:
        valid_roots = (
            b'["candidates/candidate-rigorous-calculations/SKILL.md"]',
            b'{"changed_files":["candidates/candidate-rigorous-calculations/SKILL.md"]}',
        )
        for raw in valid_roots:
            self.changed.write_bytes(raw)
            self.assertEqual(
                validate_candidate.load_changed_files_fixture(self.changed),
                [f"candidates/{SKILL}/SKILL.md"],
            )

        invalid = {
            "duplicate": b'{"changed_files":[],"changed_files":[]}',
            "bom": b'\xef\xbb\xbf[]',
            "nan": b'[NaN]',
            "scalar": b'1',
        }
        for label, raw in invalid.items():
            with self.subTest(label=label):
                self.changed.write_bytes(raw)
                with self.assertRaises(ValueError):
                    validate_candidate.load_changed_files_fixture(self.changed)

    def test_contract_enum_scan_and_probe_reject_ambiguous_json(self) -> None:
        schema_path = self.repo / "contracts" / "run-manifest.schema.json"
        ambiguous_schemas = {
            "duplicate": b'{"properties":{},"properties":{}}',
            "bom": b'\xef\xbb\xbf{}',
            "nan": b'{"value":NaN}',
            "array": b'[]',
        }
        for label, raw in ambiguous_schemas.items():
            with self.subTest(schema=label):
                schema_path.write_bytes(raw)
                self.assertEqual(
                    validate_candidate.check_contract_enums(self.repo, {CODE}).status,
                    "fail",
                )

        probe = json.dumps(validate_candidate.SEATBELT_PROBE_EXPECTED).encode("utf-8")
        self.assertEqual(
            validate_candidate.parse_seatbelt_probe(probe),
            validate_candidate.SEATBELT_PROBE_EXPECTED,
        )
        for raw in (
            b'{"workspace_read":"allowed","workspace_read":"denied"}',
            b'\xef\xbb\xbf{}',
            b'{"workspace_read":NaN}',
            b'[]',
        ):
            self.assertIsNone(validate_candidate.parse_seatbelt_probe(raw))

    def test_todo_and_readme_are_rejected(self) -> None:
        write_text(self.candidate / "README.md", "Candidate notes\n")
        with (self.candidate / "references" / "contract.md").open("a", encoding="utf-8") as handle:
            handle.write("\nTODO unresolved work\n")
        result, report = self._run(level="L0")
        self.assertEqual(result.returncode, 2)
        codes = self._codes(report)
        self.assertEqual(codes["CANDIDATE.CONTENT.README"], "fail")
        self.assertEqual(codes["CANDIDATE.CONTENT.TODO"], "fail")

    def test_frontmatter_duplicate_unsafe_tag_and_nonmapping_fail_closed(self) -> None:
        cases = {
            "duplicate": (
                "---\n"
                f"name: {SKILL}\n"
                f"name: {SKILL}\n"
                "description: Duplicate keys must fail closed.\n"
                "---\n\n# Candidate\n"
            ),
            "unsafe-tag": (
                "---\n"
                f"name: {SKILL}\n"
                "description: !!python/object/apply:builtins.str [unsafe]\n"
                "---\n\n# Candidate\n"
            ),
            "nonmapping": (
                "---\n"
                f"- name: {SKILL}\n"
                "- description: A sequence root is not frontmatter.\n"
                "---\n\n# Candidate\n"
            ),
        }
        for label, source in cases.items():
            with self.subTest(label=label):
                write_text(self.candidate / "SKILL.md", source)
                result, report = self._run(level="L0")
                self.assertEqual(result.returncode, 2)
                codes = self._codes(report)
                self.assertEqual(codes["CANDIDATE.IDENTITY.FRONTMATTER"], "fail")
                self.assertEqual(codes["CANDIDATE.IDENTITY.NAME"], "fail")

    def test_candidate_cache_and_copy_like_source_are_rejected(self) -> None:
        write_text(self.candidate / "scripts" / "__pycache__" / "guard.pyc", "synthetic-cache")
        write_text(self.candidate / "scripts" / "candidate_guard 2.py", "VALUE = 2\n")

        result, report = self._run(level="L0")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            self._codes(report)["CANDIDATE.CONTENT.SOURCE_INVENTORY"],
            "fail",
        )

    def test_missing_private_test_hook_is_rejected(self) -> None:
        (self.candidate / "tests" / "test_smoke.py").unlink()
        result, report = self._run(level="L1")
        self.assertEqual(result.returncode, 2)
        codes = self._codes(report)
        self.assertEqual(codes["CANDIDATE.TESTS.HOOK"], "fail")
        self.assertEqual(codes["CANDIDATE.TESTS.RESULT"], "fail")

    def test_line_limit_nested_references_and_broken_links_are_rejected(self) -> None:
        description = "A sufficiently explicit candidate description for deterministic validation and safe routing behavior."
        lines = [
            "---",
            f"name: {SKILL}",
            f"description: {description}",
            "---",
            "# Candidate",
            "Read [missing](references/missing.md).",
        ] + ["bounded instruction"] * 494
        write_text(self.candidate / "SKILL.md", "\n".join(lines) + "\n")
        write_text(self.candidate / "references" / "nested" / "detail.md", "# Nested\n")
        result, report = self._run(level="L0")
        self.assertEqual(result.returncode, 2)
        codes = self._codes(report)
        self.assertEqual(codes["CANDIDATE.CONTENT.LINE_LIMIT"], "fail")
        self.assertEqual(codes["CANDIDATE.CONTENT.REFERENCES_DEPTH"], "fail")
        self.assertEqual(codes["CANDIDATE.CONTENT.LINKS"], "fail")

    def test_unavailable_base_ref_returns_blocked_exit_three(self) -> None:
        result, report = self._run(
            level="L0",
            use_changed_fixture=False,
            base_ref="origin/main",
        )
        self.assertEqual(result.returncode, 3)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(
            self._codes(report)["CANDIDATE.OWNERSHIP.CHANGED_FILES"],
            "blocked",
        )
        self.assertEqual(report["routing_state"], "planned-not-routable")
        self.assertIs(report["promotion_authorized"], False)

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_l1_sandbox_denies_builtin_os_and_pathlib_host_writes(self) -> None:
        markers = {
            "builtin": self.base / "builtin-open-escape-marker",
            "os": self.base / "os-open-escape-marker",
            "pathlib": self.base / "pathlib-escape-marker",
        }
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "from pathlib import Path\n"
            "import builtins\n"
            "import os\n"
            "import unittest\n\n"
            "class EscapeTests(unittest.TestCase):\n"
            "    def test_builtin_open_denied(self):\n"
            "        with self.assertRaises(PermissionError):\n"
            f"            builtins.open({str(markers['builtin'])!r}, 'w', encoding='utf-8')\n"
            "    def test_os_open_denied(self):\n"
            "        with self.assertRaises(PermissionError):\n"
            f"            os.open({str(markers['os'])!r}, os.O_WRONLY | os.O_CREAT, 0o600)\n"
            "    def test_pathlib_denied(self):\n"
            "        with self.assertRaises(PermissionError):\n"
            f"            Path({str(markers['pathlib'])!r}).write_text('escaped', encoding='utf-8')\n",
        )

        result, report = self._run()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(all(not marker.exists() for marker in markers.values()))
        codes = self._codes(report)
        self.assertEqual(codes["CANDIDATE.TESTS.ISOLATION_BACKEND"], "pass")
        self.assertEqual(codes["CANDIDATE.TESTS.RESULT"], "pass")
        rendered = json.dumps(report, sort_keys=True)
        for marker in markers.values():
            self.assertNotIn(str(marker), rendered)

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_l1_sandbox_denies_host_reads_and_redacts_controlled_secret(self) -> None:
        marker = self.base / "host-read-control-marker"
        secret = "CONTROLLED_HOST_READ_SECRET_7fdb9a"
        marker.write_text(secret, encoding="utf-8")
        user_project_file = ROOT / "AGENTS.md"
        self.assertTrue(user_project_file.is_file())
        child = (
            "from pathlib import Path; import sys; p=Path(sys.argv[1]);\n"
            "try: p.read_text(encoding='utf-8')\n"
            "except PermissionError: print('denied')\n"
            "else: print('allowed')"
        )
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "from pathlib import Path\n"
            "import builtins\n"
            "import os\n"
            "import subprocess\n"
            "import sys\n"
            "import unittest\n\n"
            "class ReadEscapeTests(unittest.TestCase):\n"
            "    def test_builtin_open_denied(self):\n"
            "        with self.assertRaises(PermissionError):\n"
            f"            builtins.open({str(marker)!r}, 'r', encoding='utf-8')\n"
            "    def test_os_open_denied(self):\n"
            "        with self.assertRaises(PermissionError):\n"
            f"            os.open({str(marker)!r}, os.O_RDONLY)\n"
            "    def test_pathlib_denied(self):\n"
            "        with self.assertRaises(PermissionError):\n"
            f"            Path({str(marker)!r}).read_text(encoding='utf-8')\n"
            "    def test_user_project_path_denied(self):\n"
            "        with self.assertRaises(PermissionError):\n"
            f"            Path({str(user_project_file)!r}).read_text(encoding='utf-8')\n"
            "    def test_child_inherits_read_denial(self):\n"
            f"        result = subprocess.run([sys.executable, '-c', {child!r}, {str(marker)!r}], "
            "capture_output=True, text=True, timeout=10, check=False)\n"
            "        self.assertEqual(result.returncode, 0)\n"
            "        self.assertEqual(result.stdout.strip(), 'denied')\n",
        )

        result, report = self._run()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(marker.read_text(encoding="utf-8"), secret)
        self.assertEqual(report["execution_boundary"]["host_read_enforcement"], "pass")
        rendered = json.dumps(report, sort_keys=True)
        self.assertNotIn(secret, rendered)
        self.assertNotIn(secret, result.stdout)
        self.assertNotIn(secret, result.stderr)
        self.assertNotIn(str(marker), rendered)
        self.assertNotIn(str(user_project_file), rendered)

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_l1_sandbox_denies_subprocess_child_host_write(self) -> None:
        marker = self.base / "subprocess-escape-marker"
        child = (
            "from pathlib import Path; import sys; p=Path(sys.argv[1]);\n"
            "try: p.write_text('escaped', encoding='utf-8')\n"
            "except PermissionError: print('denied')\n"
            "else: print('allowed')"
        )
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "import subprocess\n"
            "import sys\n"
            "import unittest\n\n"
            "class ChildEscapeTests(unittest.TestCase):\n"
            "    def test_child_inherits_sandbox(self):\n"
            f"        result = subprocess.run([sys.executable, '-c', {child!r}, {str(marker)!r}], "
            "capture_output=True, text=True, check=False)\n"
            "        self.assertEqual(result.returncode, 0)\n"
            "        self.assertEqual(result.stdout.strip(), 'denied')\n",
        )

        result, report = self._run()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(
            self._codes(report)["CANDIDATE.TESTS.ISOLATION_BACKEND"],
            "pass",
        )
        self.assertEqual(self._codes(report)["CANDIDATE.TESTS.RESULT"], "pass")
        self.assertNotIn(str(marker), json.dumps(report, sort_keys=True))

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_l1_sandbox_denies_socket_bind_and_connect(self) -> None:
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "import socket\n"
            "import unittest\n\n"
            "def bind_loopback():\n"
            "    sock = socket.socket()\n"
            "    try:\n"
            "        sock.bind(('127.0.0.1', 0))\n"
            "    finally:\n"
            "        sock.close()\n\n"
            "def connect_loopback():\n"
            "    sock = socket.socket()\n"
            "    try:\n"
            "        sock.connect(('127.0.0.1', 9))\n"
            "    finally:\n"
            "        sock.close()\n\n"
            "class NetworkEscapeTests(unittest.TestCase):\n"
            "    def test_bind_denied(self):\n"
            "        with self.assertRaises(PermissionError):\n"
            "            bind_loopback()\n"
            "    def test_connect_denied(self):\n"
            "        with self.assertRaises(PermissionError):\n"
            "            connect_loopback()\n",
        )

        result, report = self._run()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            self._codes(report)["CANDIDATE.TESTS.ISOLATION_BACKEND"],
            "pass",
        )
        self.assertEqual(self._codes(report)["CANDIDATE.TESTS.RESULT"], "pass")

    def test_missing_backend_blocks_without_starting_candidate(self) -> None:
        marker = self.base / "must-not-run-without-backend"
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('escaped', encoding='utf-8')\n",
        )
        with mock.patch.object(validate_candidate, "SANDBOX_EXEC", self.base / "missing-sandbox-exec"):
            report = validate_candidate.validate_candidate(
                SKILL,
                self.candidate,
                "L1",
                changed_fixture=self.changed,
            )
        validate_candidate.validate_report(report)

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(marker.exists())
        self.assertEqual(
            self._codes(report)["CANDIDATE.TESTS.ISOLATION_BACKEND"],
            "blocked",
        )
        self.assertEqual(self._codes(report)["CANDIDATE.TESTS.RESULT"], "not-run")
        self.assertEqual(report["execution_boundary"]["backend_status"], "unavailable")

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_unavailable_resource_limits_block_without_starting_candidate(self) -> None:
        marker = self.base / "must-not-run-without-resource-limits"
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('escaped', encoding='utf-8')\n",
        )
        with mock.patch.object(
            validate_candidate,
            "subprocess_resource_limits",
            side_effect=ValueError("controlled missing limit"),
        ):
            report = validate_candidate.validate_candidate(
                SKILL,
                self.candidate,
                "L1",
                changed_fixture=self.changed,
            )
        validate_candidate.validate_report(report)

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(marker.exists())
        boundary = report["execution_boundary"]
        self.assertEqual(boundary["backend_status"], "unavailable")
        self.assertEqual(boundary["process_resource_limits_status"], "not-run")
        self.assertEqual(self._codes(report)["CANDIDATE.TESTS.RESULT"], "not-run")

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_candidate_output_overflow_is_bounded_redacted_and_fails(self) -> None:
        sentinel = "CONTROLLED_OUTPUT_OVERFLOW_291c"
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "import sys\n"
            f"sys.stdout.write({sentinel!r} * 200000)\n",
        )

        result, report = self._run()

        self.assertEqual(result.returncode, 2)
        self.assertEqual(self._codes(report)["CANDIDATE.TESTS.RESULT"], "fail")
        rendered = json.dumps(report, sort_keys=True)
        self.assertNotIn(sentinel, rendered)
        self.assertNotIn(sentinel, result.stdout)
        self.assertNotIn(sentinel, result.stderr)
        result_check = next(
            check for check in report["checks"] if check["check_id"] == "CANDIDATE.TESTS.RESULT"
        )
        self.assertTrue(
            any("return-codes:125" in item["label"] for item in result_check["evidence"])
        )

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_failed_enforcement_probe_blocks_candidate_execution(self) -> None:
        marker = self.base / "must-not-run-after-probe-failure"
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('escaped', encoding='utf-8')\n",
        )
        with mock.patch.object(validate_candidate, "SEATBELT_PROBE_SOURCE", "raise SystemExit(91)"):
            report = validate_candidate.validate_candidate(
                SKILL,
                self.candidate,
                "L1",
                changed_fixture=self.changed,
            )
        validate_candidate.validate_report(report)

        self.assertEqual(report["status"], "blocked")
        self.assertFalse(marker.exists())
        self.assertEqual(report["execution_boundary"]["backend_status"], "probe-failed")
        self.assertEqual(report["execution_boundary"]["enforcement_probe_status"], "fail")
        self.assertEqual(self._codes(report)["CANDIDATE.TESTS.RESULT"], "not-run")

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_copy_hash_mismatch_blocks_probe_and_candidate_execution(self) -> None:
        marker = self.base / "must-not-run-after-copy-mismatch"
        write_text(
            self.candidate / "tests" / "test_smoke.py",
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('escaped', encoding='utf-8')\n",
        )
        real_copytree = validate_candidate.copy_candidate_tree

        def corrupt_copy(source: Path, destination: Path, **kwargs: object) -> Path:
            copied = real_copytree(source, destination, **kwargs)
            write_text(Path(copied) / "scripts" / "candidate_guard.py", "# corrupted isolated copy\n")
            return Path(copied)

        with mock.patch.object(validate_candidate, "copy_candidate_tree", side_effect=corrupt_copy):
            report = validate_candidate.validate_candidate(
                SKILL,
                self.candidate,
                "L1",
                changed_fixture=self.changed,
            )
        validate_candidate.validate_report(report)

        boundary = report["execution_boundary"]
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(marker.exists())
        self.assertEqual(boundary["backend_status"], "setup-failed")
        self.assertNotEqual(boundary["source_tree_sha256"], boundary["isolated_copy_sha256"])
        self.assertEqual(boundary["enforcement_probe_status"], "not-run")
        self.assertEqual(self._codes(report)["CANDIDATE.TESTS.RESULT"], "not-run")

    def test_report_semantics_reject_inconsistent_status_totals_and_next_actions(self) -> None:
        result, report = self._run(level="L0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        inconsistent_total = json.loads(json.dumps(report))
        inconsistent_total["summary"]["total"] += 1
        with self.assertRaises(ValueError):
            validate_candidate.validate_report(inconsistent_total)

        inconsistent_status = json.loads(json.dumps(report))
        inconsistent_status["status"] = "fail"
        with self.assertRaises(ValueError):
            validate_candidate.validate_report(inconsistent_status)

        pass_with_action = json.loads(json.dumps(report))
        pass_with_action["checks"][0]["next_action"] = "A passing check cannot prescribe remediation."
        with self.assertRaises(ValueError):
            validate_candidate.validate_report(pass_with_action)

        fail_without_action = json.loads(json.dumps(report))
        first = fail_without_action["checks"][0]
        first["status"] = "fail"
        first["next_action"] = None
        fail_without_action["status"] = "fail"
        fail_without_action["summary"]["passed"] -= 1
        fail_without_action["summary"]["failed"] += 1
        with self.assertRaises(ValueError):
            validate_candidate.validate_report(fail_without_action)

    @unittest.skipUnless(SEATBELT_AVAILABLE, "requires the macOS Seatbelt backend")
    def test_report_semantics_reject_inconsistent_backend_and_probe_claims(self) -> None:
        result, report = self._run()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        mismatched_copy = json.loads(json.dumps(report))
        mismatched_copy["execution_boundary"]["isolated_copy_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_candidate.validate_report(mismatched_copy)

        failed_probe_claimed_enforced = json.loads(json.dumps(report))
        failed_probe_claimed_enforced["execution_boundary"]["enforcement_probe_status"] = "fail"
        with self.assertRaises(ValueError):
            validate_candidate.validate_report(failed_probe_claimed_enforced)

        failed_host_read_claimed_enforced = json.loads(json.dumps(report))
        failed_host_read_claimed_enforced["execution_boundary"]["host_read_enforcement"] = "fail"
        with self.assertRaises(ValueError):
            validate_candidate.validate_report(failed_host_read_claimed_enforced)

        missing_limits_claimed_enforced = json.loads(json.dumps(report))
        missing_limits_claimed_enforced["execution_boundary"]["process_resource_limits_sha256"] = None
        with self.assertRaises(ValueError):
            validate_candidate.validate_report(missing_limits_claimed_enforced)

        execution_without_backend = json.loads(json.dumps(report))
        execution_without_backend["execution_boundary"]["backend_status"] = "unavailable"
        with self.assertRaises(ValueError):
            validate_candidate.validate_report(execution_without_backend)

    def test_validation_report_uses_offline_contract_urn(self) -> None:
        self.assertEqual(
            REPORT_SCHEMA["$id"],
            "urn:vibe-dft-skills:contract:validation-report:1.0",
        )
        self.assertEqual(REPORT_SCHEMA["properties"]["contract_name"]["const"], "validation-report")
        self.assertIn("contract_name", REPORT_SCHEMA["required"])
        self.assertEqual(REPORT_SCHEMA["x-vibe-document-kind"], "projection")
        self.assertNotIn("x-vibe-record-id-field", REPORT_SCHEMA)

    def test_cli_exposes_no_self_declared_isolation_authorization(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("attestation", result.stdout.casefold())


if __name__ == "__main__":
    unittest.main(verbosity=2)
