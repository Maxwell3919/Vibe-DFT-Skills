from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import operation_routes  # noqa: E402
import environment_profiles  # noqa: E402
import interface_registry  # noqa: E402
import skill_registry  # noqa: E402
import software_registry  # noqa: E402
import registry_yaml  # noqa: E402
import validate_agent_answer  # noqa: E402


SCHEMA = json.loads((ROOT / "contracts" / "agent-action-envelope.schema.json").read_text(encoding="utf-8"))
COMMON = json.loads((ROOT / "contracts" / "common-definitions-1.0.schema.json").read_text(encoding="utf-8"))
ROUTES = operation_routes.load_registry()
SKILLS = skill_registry.load_registry()
INTERFACES = interface_registry.load_registry()
SOFTWARE = software_registry.load_registry()
ENVIRONMENTS = environment_profiles.load_registry()

_ISOLATED_TEMP: tempfile.TemporaryDirectory[str] | None = None
ISOLATED_ROOT = ROOT
ISOLATED_SKILLS = SKILLS
ISOLATED_INTERFACES = INTERFACES
ISOLATED_REGISTRY_PATHS: dict[str, Path] = {}


def _clean_skill_ignore(_: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        suffix = Path(name).suffix.lower()
        if (
            name in skill_registry._CACHE_DIRECTORIES
            or name in skill_registry._CACHE_FILES
            or suffix in skill_registry._BYTECODE_SUFFIXES
            or skill_registry._COPY_SUFFIX.fullmatch(name)
        ):
            ignored.add(name)
    return ignored


def setUpModule() -> None:
    """Build one clean, content-hashed registry snapshot for semantic counterexamples."""

    global _ISOLATED_TEMP, ISOLATED_ROOT, ISOLATED_SKILLS, ISOLATED_INTERFACES, ISOLATED_REGISTRY_PATHS
    _ISOLATED_TEMP = tempfile.TemporaryDirectory()
    ISOLATED_ROOT = Path(_ISOLATED_TEMP.name)
    shutil.copytree(ROOT / "contracts", ISOLATED_ROOT / "contracts")
    isolated_interfaces = copy.deepcopy(INTERFACES)
    for entry in isolated_interfaces["interfaces"].values():
        if entry["lifecycle"] != "active":
            continue
        schema_file = ISOLATED_ROOT / entry["schema_path"]
        entry["schema_sha256"] = hashlib.sha256(schema_file.read_bytes()).hexdigest()
    (ISOLATED_ROOT / "skills").mkdir()
    isolated_skills = copy.deepcopy(SKILLS)
    for name, entry in isolated_skills["skills"].items():
        if entry["lifecycle"] not in {"active", "development"}:
            continue
        source = ROOT / entry["path"]
        target = ISOLATED_ROOT / entry["path"]
        shutil.copytree(source, target, ignore=_clean_skill_ignore)
        entry["source_tree_sha256"] = skill_registry.source_tree_digest(target).sha256
    (ISOLATED_ROOT / "tools").mkdir()
    shutil.copy2(ROOT / "tools" / "validate_contract.py", ISOLATED_ROOT / "tools" / "validate_contract.py")
    registry_directory = ISOLATED_ROOT / "registry"
    registry_directory.mkdir()
    shutil.copy2(ROOT / "registry" / "skill-registry.yaml", registry_directory / "skill-registry.yaml")
    shutil.copy2(ROOT / "registry" / "operation-routes.yaml", registry_directory / "operation-routes.yaml")
    snapshots = {
        "operation-routes": ROUTES,
        "skill-registry": isolated_skills,
        "interface-registry": isolated_interfaces,
        "software-registry": SOFTWARE,
        "environment-profiles": ENVIRONMENTS,
    }
    ISOLATED_REGISTRY_PATHS = {}
    for label, snapshot in snapshots.items():
        path = registry_directory / f"{label}.json"
        path.write_text(json.dumps(snapshot), encoding="utf-8")
        ISOLATED_REGISTRY_PATHS[label] = path
    ISOLATED_SKILLS = isolated_skills
    ISOLATED_INTERFACES = isolated_interfaces


def tearDownModule() -> None:
    global _ISOLATED_TEMP
    if _ISOLATED_TEMP is not None:
        _ISOLATED_TEMP.cleanup()
        _ISOLATED_TEMP = None


def record_ref(contract_name: str, record_id: str, sha256: str, role: str) -> dict[str, str]:
    return {
        "contract_name": contract_name,
        "schema_version": "1.0",
        "record_id": record_id,
        "sha256": sha256,
        "role": role,
    }


def add_handoff_manifest_evidence(
    data: dict[str, object],
    contract: str,
    *,
    evidence_id: str = "ev-manifest",
    manifest_id: str = "manifest-001",
    sha256: str = "e" * 64,
) -> dict[str, str]:
    contract_name, schema_version = contract.rsplit("@", 1)
    manifest_ref = {
        "contract_name": contract_name,
        "schema_version": schema_version,
        "record_id": manifest_id,
        "sha256": sha256,
        "role": "handoff-manifest",
    }
    data["evidence"]["items"].append(  # type: ignore[index]
        {
            "id": evidence_id,
            "role": "handoff-manifest",
            "status": "present",
            "sha256": sha256,
            "record_ref": copy.deepcopy(manifest_ref),
            "source_label": f"{manifest_id}.json",
            "limitations": [],
        }
    )
    return manifest_ref


def grant_execution_authorization(data: dict[str, object]) -> None:
    decision_ref = record_ref(
        "decision-record",
        "decision-execution-authorization",
        "b" * 64,
        "execution-authorization",
    )
    data["evidence"]["items"].append(  # type: ignore[index]
        {
            "id": "ev-authorization",
            "role": "human-execution-authorization-record",
            "status": "present",
            "sha256": "b" * 64,
            "record_ref": copy.deepcopy(decision_ref),
            "source_label": "execution-authorization.json",
            "limitations": [],
        }
    )
    data["authorization"] = {
        "state": "granted",
        "side_effects": ["network-read", "local-write", "local-execution"],
        "scope": ["Run only the exact registered QE action for request req-001."],
        "evidence_ids": ["ev-authorization"],
        "decision_ref": decision_ref,
    }
    # A valid authorization record does not outrank an existing hard blocker.
    data["action_state"] = "local_gate_blocked"


def valid_qe_envelope() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "contract_name": "agent-action-envelope",
        "request": {"request_id": "req-001", "mode": "audit_input"},
        "route": {
            "state": "selected_active",
            "skill": "qe-rigorous-calculations",
            "lifecycle": "active",
            "software": "qe",
            "task": "scf",
        },
        "action_state": "local_gate_blocked",
        "claim_ceiling": "input_gates_only",
        "claim_scope": {
            "claim_id": "scope-input",
            "scope_kind": "computed-fact",
            "statement": "QE input integrity for the exact audited input and evidence inventory.",
            "observable": "input-integrity",
            "unit": None,
            "absolute_tolerance": None,
            "relative_tolerance": None,
            "evidence_ids": ["ev-audit"],
            "limitations": ["This scope does not include execution or scientific validity."],
        },
        "scientific_acceptance": "not_assessed",
        "scientific_decision_ref": None,
        "authorization": {
            "state": "not_required",
            "side_effects": ["network-read", "local-write", "local-execution"],
            "scope": [],
            "evidence_ids": [],
            "decision_ref": None,
        },
        "evidence": {
            "items": [
                {
                    "id": "ev-plan",
                    "role": "scientific-plan",
                    "status": "present",
                    "sha256": "a" * 64,
                    "record_ref": None,
                    "source_label": "qe-plan.json",
                    "limitations": [],
                },
                {
                    "id": "ev-official",
                    "role": "official-source-snapshot",
                    "status": "present",
                    "sha256": "f" * 64,
                    "record_ref": record_ref(
                        "official-source-record",
                        "qe-official-source",
                        "f" * 64,
                        "official-source",
                    ),
                    "source_label": "qe-official-source.json",
                    "limitations": [],
                },
                {
                    "id": "ev-reference",
                    "role": "official-source-resolution-report",
                    "status": "present",
                    "sha256": "9" * 64,
                    "record_ref": record_ref(
                        "tool-execution",
                        "tool-reference",
                        "9" * 64,
                        "tool-report",
                    ),
                    "source_label": "qe-reference-report.json",
                    "limitations": [],
                },
                {
                    "id": "ev-audit",
                    "role": "input-audit",
                    "status": "present",
                    "sha256": "c" * 64,
                    "record_ref": record_ref("tool-execution", "tool-audit", "c" * 64, "tool-report"),
                    "source_label": "qe-input-audit.json",
                    "limitations": [],
                },
            ],
            "missing": ["observable-specific numerical convergence evidence"],
            "conflicts": [],
        },
        "tool_runs": [
            {
                "id": "tool-audit",
                "action_id": "qe.audit-input",
                "tool": "qe_guard.py audit",
                "required": True,
                "status": "succeeded",
                "exit_code": 0,
                "report_sha256": "c" * 64,
                "gate_ids": ["input-integrity"],
                "finding_codes": [],
            },
            {
                "id": "tool-reference",
                "action_id": "qe.reference",
                "tool": "qe_guard.py reference --live-check",
                "required": True,
                "status": "succeeded",
                "exit_code": 0,
                "report_sha256": "9" * 64,
                "gate_ids": ["official-source-coverage"],
                "finding_codes": [],
            }
        ],
        "gates": [
            {
                "id": "official-source-coverage",
                "native_status": "pass",
                "status": "pass",
                "evidence_ids": ["ev-official", "ev-reference"],
                "finding_codes": [],
            },
            {
                "id": "input-integrity",
                "native_status": "pass",
                "status": "pass",
                "evidence_ids": ["ev-plan", "ev-audit"],
                "finding_codes": [],
            },
            {
                "id": "scientific-claim",
                "native_status": "blocked",
                "status": "blocked",
                "evidence_ids": ["ev-audit"],
                "finding_codes": ["SCIENTIFIC_CLAIM_BLOCKED"],
            },
        ],
        "supported_facts": [
            {
                "id": "fact-input",
                "statement": "The implemented deterministic QE input-integrity gate passed for this evidence set.",
                "claim_level": "input_gates_only",
                "evidence_ids": ["ev-audit"],
            }
        ],
        "blocked_claims": [
            {
                "id": "claim-science",
                "statement": "Scientific acceptance is not established by one input audit.",
                "gate_ids": ["scientific-claim"],
                "finding_codes": ["SCIENTIFIC_CLAIM_BLOCKED"],
            }
        ],
        "smallest_next_action": {
            "gate_id": "scientific-claim",
            "finding_code": "SCIENTIFIC_CLAIM_BLOCKED",
            "action": "Provide evidence-linked convergence runs for the named observable and tolerance.",
            "required_inputs": ["audited fixed-protocol convergence series"],
            "requires_authorization": False,
            "why_minimal": "The local input gate already passed; numerical evidence is the next unresolved scientific layer.",
        },
        "handoffs": [],
        "limitations": ["No execution, numerical convergence, task validity, or physical validity is claimed."],
    }


def development_gaussian_envelope() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "contract_name": "agent-action-envelope",
        "request": {"request_id": "req-plan-001", "mode": "design"},
        "route": {
            "state": "inactive_development",
            "skill": "gaussian-rigorous-calculations",
            "lifecycle": "development",
            "software": "gaussian",
            "task": "single-point",
        },
        "action_state": "local_gate_blocked",
        "claim_ceiling": "no_positive_claim",
        "claim_scope": None,
        "scientific_acceptance": "not_assessed",
        "scientific_decision_ref": None,
        "authorization": {
            "state": "not_required",
            "side_effects": ["local-write", "local-execution"],
            "scope": [],
            "evidence_ids": [],
            "decision_ref": None,
        },
        "evidence": {"items": [], "missing": ["activated and validated Gaussian Skill"], "conflicts": []},
        "tool_runs": [],
        "gates": [
            {
                "id": "route-availability",
                "native_status": "development",
                "status": "blocked",
                "evidence_ids": [],
                "finding_codes": ["ROUTE_PLANNED_NOT_ROUTABLE"],
            }
        ],
        "supported_facts": [],
        "blocked_claims": [
            {
                "id": "claim-route",
                "statement": "The development Gaussian Skill cannot be invoked.",
                "gate_ids": ["route-availability"],
                "finding_codes": ["ROUTE_PLANNED_NOT_ROUTABLE"],
            }
        ],
        "smallest_next_action": {
            "gate_id": "route-availability",
            "finding_code": "ROUTE_PLANNED_NOT_ROUTABLE",
            "action": "Complete the registered activation profile before attempting this route.",
            "required_inputs": ["reviewed promotion evidence"],
            "requires_authorization": False,
            "why_minimal": "A development Skill is source-backed but has no callable route.",
        },
        "handoffs": [],
        "limitations": ["Registry identity is not implemented software support."],
    }


def no_positive_active_qe_envelope() -> dict[str, object]:
    data = valid_qe_envelope()
    data["action_state"] = "local_gate_blocked"
    data["claim_ceiling"] = "no_positive_claim"
    data["claim_scope"] = None
    data["evidence"]["items"] = [data["evidence"]["items"][0]]  # type: ignore[index]
    data["tool_runs"] = []
    data["gates"] = [
        {
            "id": "scientific-claim",
            "native_status": "blocked",
            "status": "blocked",
            "evidence_ids": ["ev-plan"],
            "finding_codes": ["SCIENTIFIC_CLAIM_BLOCKED"],
        }
    ]
    data["supported_facts"] = []
    data["blocked_claims"] = [
        {
            "id": "claim-science",
            "statement": "No positive claim is established.",
            "gate_ids": ["scientific-claim"],
            "finding_codes": ["SCIENTIFIC_CLAIM_BLOCKED"],
        }
    ]
    data["smallest_next_action"] = {
        "gate_id": "scientific-claim",
        "finding_code": "SCIENTIFIC_CLAIM_BLOCKED",
        "action": "Provide the missing deterministic evidence.",
        "required_inputs": ["hashed evidence"],
        "requires_authorization": False,
        "why_minimal": "This is the first unresolved gate.",
    }
    data["limitations"] = ["No positive technical or scientific claim is made."]
    return data


def documented_qe_envelope() -> dict[str, object]:
    data = valid_qe_envelope()
    data["request"]["mode"] = "explain"  # type: ignore[index]
    data["claim_ceiling"] = "documented_behavior_only"
    data["claim_scope"] = {
        "claim_id": "scope-documented",
        "scope_kind": "documented-behavior",
        "statement": "The named QE behavior is documented by an official source snapshot.",
        "observable": None,
        "unit": None,
        "absolute_tolerance": None,
        "relative_tolerance": None,
        "evidence_ids": ["ev-official"],
        "limitations": ["No input, execution, convergence, or scientific result is claimed."],
    }
    data["tool_runs"] = []
    data["gates"] = [  # type: ignore[index]
        {
            "id": "official-source-coverage",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-official"],
            "finding_codes": [],
        },
        data["gates"][-1],  # type: ignore[index]
    ]
    data["supported_facts"] = [
        {
            "id": "fact-documented",
            "statement": "The bounded behavior is present in the recorded official QE source.",
            "claim_level": "documented_behavior_only",
            "evidence_ids": ["ev-official"],
        }
    ]
    return data


def accepted_qe_envelope() -> dict[str, object]:
    data = valid_qe_envelope()
    data["request"]["mode"] = "handoff"  # type: ignore[index]
    data["action_state"] = "complete"
    data["claim_ceiling"] = "eligible_for_expert_review"
    data["claim_scope"] = {
        "claim_id": "scope-review",
        "scope_kind": "scientific-claim",
        "statement": "The bounded QE SCF claim was accepted for the recorded protocol and evidence set.",
        "observable": "total-energy",
        "unit": "eV",
        "absolute_tolerance": 0.001,
        "relative_tolerance": None,
        "evidence_ids": ["ev-audit", "ev-review"],
        "limitations": ["Acceptance does not transfer to a different structure, protocol, or observable."],
    }
    data["scientific_acceptance"] = "accepted"
    data["scientific_decision_ref"] = record_ref(
        "decision-record",
        "decision-qe-acceptance",
        "d" * 64,
        "scientific-acceptance",
    )
    data["evidence"]["items"].append(  # type: ignore[index]
        {
            "id": "ev-review",
            "role": "human-expert-decision-record",
            "status": "present",
            "sha256": "d" * 64,
            "record_ref": record_ref(
                "decision-record",
                "decision-qe-acceptance",
                "d" * 64,
                "scientific-acceptance",
            ),
            "source_label": "expert-review.json",
            "limitations": [],
        }
    )
    data["evidence"]["items"].append(  # type: ignore[index]
        {
            "id": "ev-handoff",
            "role": "contract-validation-report",
            "status": "present",
            "sha256": "e" * 64,
            "record_ref": record_ref(
                "tool-execution",
                "tool-validate-handoff",
                "e" * 64,
                "tool-report",
            ),
            "source_label": "run-manifest-validation.json",
            "limitations": [],
        }
    )
    data["evidence"]["missing"] = []  # type: ignore[index]
    data["tool_runs"] = [
        {
            "id": "tool-audit-run",
            "action_id": "qe.audit-run",
            "tool": "qe_guard.py audit --output",
            "required": True,
            "status": "succeeded",
            "exit_code": 0,
            "report_sha256": "c" * 64,
            "gate_ids": ["input-integrity", "execution-completion", "numerical-convergence"],
            "finding_codes": [],
        },
        {
            "id": "tool-reference",
            "action_id": "qe.reference",
            "tool": "qe_guard.py reference --live-check",
            "required": True,
            "status": "succeeded",
            "exit_code": 0,
            "report_sha256": "9" * 64,
            "gate_ids": ["official-source-coverage"],
            "finding_codes": [],
        },
        {
            "id": "tool-validate-handoff",
            "action_id": "qe.validate-handoff",
            "tool": "validate_contract.py run",
            "required": True,
            "status": "succeeded",
            "exit_code": 0,
            "report_sha256": "e" * 64,
            "gate_ids": [
                "task-specific-validation",
                "expert-review-readiness",
                "physical-validity",
                "scientific-claim",
                "expert-scientific-review",
            ],
            "finding_codes": [],
        },
    ]
    data["gates"] = [
        {
            "id": "official-source-coverage",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-official", "ev-reference"],
            "finding_codes": [],
        },
        {
            "id": "input-integrity",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-audit"],
            "finding_codes": [],
        },
        {
            "id": "execution-completion",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-audit"],
            "finding_codes": [],
        },
        {
            "id": "numerical-convergence",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-audit"],
            "finding_codes": [],
        },
        {
            "id": "task-specific-validation",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-handoff", "ev-review"],
            "finding_codes": [],
        },
        {
            "id": "expert-review-readiness",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-handoff", "ev-review"],
            "finding_codes": [],
        },
        {
            "id": "physical-validity",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-review"],
            "finding_codes": [],
        },
        {
            "id": "scientific-claim",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-review"],
            "finding_codes": [],
        },
        {
            "id": "expert-scientific-review",
            "native_status": "pass",
            "status": "pass",
            "evidence_ids": ["ev-review"],
            "finding_codes": [],
        },
    ]
    data["supported_facts"] = [
        {
            "id": "fact-review",
            "statement": "The bounded claim has an explicit hashed expert-review acceptance record.",
            "claim_level": "eligible_for_expert_review",
            "evidence_ids": ["ev-audit", "ev-review"],
        }
    ]
    data["blocked_claims"] = []
    data["smallest_next_action"] = None
    data["limitations"] = ["Acceptance is scoped only to the recorded expert-reviewed claim."]
    return data


def finding_codes(data: dict[str, object]) -> set[str]:
    return {
        item["code"]
        for item in validate_agent_answer.validation_findings(
            data,
            schema=SCHEMA,
            routes=ROUTES,
            skills=ISOLATED_SKILLS,
            interfaces=ISOLATED_INTERFACES,
            software=SOFTWARE,
            environments=ENVIRONMENTS,
            source_root=ISOLATED_ROOT,
        )
    }


def route_findings(
    routes: dict[str, object],
    *,
    skills: dict[str, object] | None = None,
    interfaces: dict[str, object] | None = None,
    dependency_source_validation: bool = True,
) -> list[dict[str, str]]:
    return operation_routes.validation_findings(
        routes,
        source_root=ISOLATED_ROOT,
        skill_data=skills if skills is not None else ISOLATED_SKILLS,
        interface_data=interfaces if interfaces is not None else ISOLATED_INTERFACES,
        software_data=SOFTWARE,
        environment_data=ENVIRONMENTS,
        dependency_source_validation=dependency_source_validation,
    )


class RouteRegistryTests(unittest.TestCase):
    def test_response_policy_is_exact_machine_facing_single_truth(self) -> None:
        self.assertEqual(ROUTES["response_policy"], operation_routes.RESPONSE_POLICY)
        self.assertEqual(
            ROUTES["response_policy"]["action_state_precedence"],
            [
                "failed_terminal",
                "failed_recoverable",
                "local_gate_blocked",
                "needs_evidence",
                "needs_authorization",
                "ready_for_deterministic_check",
                "deterministic_check_running",
                "ready_for_authorized_execution",
                "execution_in_progress",
                "handoff_ready",
                "local_gate_passed_limited",
                "complete",
            ],
        )
        self.assertEqual(
            ROUTES["response_policy"]["unverified_claim_ceiling"],
            "no_positive_claim",
        )

        mutations = []
        missing = copy.deepcopy(ROUTES)
        del missing["response_policy"]
        mutations.append(missing)
        prose_as_evidence = copy.deepcopy(ROUTES)
        prose_as_evidence["response_policy"]["natural_language_evidence"] = "trusted"
        mutations.append(prose_as_evidence)
        reordered = copy.deepcopy(ROUTES)
        reordered["response_policy"]["action_state_precedence"] = [
            "failed_recoverable", "failed_terminal", "local_gate_blocked", "needs_evidence"
        ]
        mutations.append(reordered)
        for mutation in mutations:
            with self.subTest(mutation=mutation.get("response_policy")):
                codes = {item["code"] for item in route_findings(mutation)}
                self.assertTrue(
                    {"ROUTE_FIELDS_INVALID", "ROUTE_RESPONSE_POLICY_INVALID"}.intersection(codes)
                )

    def test_claim_ceiling_enum_matches_common_contract_exactly(self) -> None:
        canonical = tuple(COMMON["$defs"]["claimCeiling"]["enum"])
        self.assertEqual(operation_routes.CLAIM_CEILINGS, canonical)
        self.assertEqual(tuple(SCHEMA["$defs"]["claim_ceiling"]["enum"]), canonical)

    def test_active_claim_profiles_monotonically_inherit_all_of_gates(self) -> None:
        """A stronger claim may add mandatory gates, but must not discard one."""

        for skill_name, route in ROUTES["routes"].items():
            if route["lifecycle"] != "active":
                continue
            maximum_index = operation_routes.CLAIM_CEILINGS.index(route["maximum_claim"])
            inherited: set[str] = set()
            for level in operation_routes.CLAIM_CEILINGS[: maximum_index + 1]:
                profile = route["claim_gate_profile"][level]
                # No structured waiver exists in schema 1.0. Adding one must be
                # an explicit contract change rather than an unreviewed escape.
                self.assertEqual(set(profile), {"all_of", "any_of"})
                current = set(profile["all_of"])
                self.assertFalse(
                    inherited - current,
                    (
                        f"{skill_name} {level} dropped mandatory gates "
                        f"{sorted(inherited - current)} from a weaker claim profile"
                    ),
                )
                inherited.update(current)

    def test_stronger_profiles_preserve_documented_behavior_prerequisites(self) -> None:
        """Higher claims must still satisfy the documented-behavior gate."""

        targeted_routes = {
            "cif-structure-analysis",
            "qe-rigorous-calculations",
            "vasp-rigorous-calculations",
            "cp2k-rigorous-calculations",
            "dft-postprocess",
            "dft-campaign-efficiency",
        }
        for skill_name in sorted(targeted_routes):
            route = ROUTES["routes"][skill_name]
            documented = route["claim_gate_profile"]["documented_behavior_only"]
            documented_all = set(documented["all_of"])
            documented_any = set(documented["any_of"])
            maximum_index = operation_routes.CLAIM_CEILINGS.index(route["maximum_claim"])
            stronger_levels = operation_routes.CLAIM_CEILINGS[2 : maximum_index + 1]
            for level in stronger_levels:
                with self.subTest(skill=skill_name, level=level):
                    stronger = route["claim_gate_profile"][level]
                    stronger_all = set(stronger["all_of"])
                    stronger_any = set(stronger["any_of"])
                    self.assertTrue(
                        documented_all <= stronger_all,
                        (
                            f"{skill_name} {level} dropped documented-behavior "
                            f"all_of gates {sorted(documented_all - stronger_all)}"
                        ),
                    )
                    if documented_any:
                        # An earlier any_of remains mandatory only if the same
                        # (or a narrower) choice set remains, or one option is
                        # promoted to an unconditional all_of requirement.
                        preserved = bool(documented_any & stronger_all) or (
                            bool(stronger_any) and stronger_any <= documented_any
                        )
                        self.assertTrue(
                            preserved,
                            (
                                f"{skill_name} {level} no longer requires any "
                                "documented-behavior alternative from "
                                f"{sorted(documented_any)}"
                            ),
                        )

    def test_action_templates_include_conditionally_required_arguments(self) -> None:
        expected_pairs = {
            ("qe-rigorous-calculations", "qe.audit-run"): ("--stderr", "<stderr>"),
            ("qe-rigorous-calculations", "qe.convergence"): ("--direction", "<direction>"),
            ("vasp-rigorous-calculations", "vasp.audit-run"): (
                "--expected-vasp-version",
                "<expected_vasp_version>",
            ),
        }
        for (skill_name, action_id), (flag, placeholder) in expected_pairs.items():
            with self.subTest(skill=skill_name, action=action_id):
                actions = ROUTES["routes"][skill_name]["actions"]
                argv = actions[action_id]["argv"]
                self.assertEqual(argv.count(flag), 1)
                index = argv.index(flag)
                self.assertLess(index + 1, len(argv))
                self.assertEqual(argv[index + 1], placeholder)

    def test_stronger_calculation_modes_register_official_source_resolver(self) -> None:
        """Require a resolver step; exact-set coverage remains a separate contract."""

        resolvers = {
            "qe-rigorous-calculations": "qe.reference",
            "vasp-rigorous-calculations": "vasp.reference",
            "cp2k-rigorous-calculations": "cp2k.reference",
        }
        for skill_name, resolver in resolvers.items():
            route = ROUTES["routes"][skill_name]
            for mode, sequence in route["tool_sequence"].items():
                maximum = max(
                    (
                        route["actions"][action_id]["maximum_claim"]
                        for action_id in sequence
                    ),
                    key=operation_routes.CLAIM_CEILINGS.index,
                )
                if operation_routes.CLAIM_CEILINGS.index(maximum) <= 1:
                    continue
                with self.subTest(skill=skill_name, mode=mode):
                    self.assertIn(
                        resolver,
                        sequence,
                        f"{skill_name} {mode} cannot satisfy its inherited official-source gate",
                    )

    def test_siesta_run_and_stronger_profiles_require_output_observables(self) -> None:
        profiles = ROUTES["routes"]["siesta-rigorous-calculations"]["claim_gate_profile"]
        for level in (
            "technical_run_gates_only",
            "numerical_candidate_only",
            "eligible_for_expert_review",
        ):
            with self.subTest(level=level):
                self.assertIn("output-observables", profiles[level]["all_of"])

    def test_vasp_run_and_stronger_profiles_require_input_output_consistency(self) -> None:
        route = ROUTES["routes"]["vasp-rigorous-calculations"]
        profiles = route["claim_gate_profile"]
        self.assertNotIn("input-output-consistency", profiles["input_gates_only"]["all_of"])
        for level in (
            "technical_run_gates_only",
            "numerical_candidate_only",
            "eligible_for_expert_review",
        ):
            with self.subTest(level=level):
                self.assertIn("input-output-consistency", profiles[level]["all_of"])

        # The VASP auditor emits snake_case gate IDs. The central profile uses
        # kebab-case, and the answer validator must normalize the exact pair
        # while retaining a succeeded audit report as gate evidence.
        audit_gate_ids = {
            "input_integrity",
            "input_reproducibility",
            "input_output_consistency",
            "execution_completion",
            "electronic_convergence",
            "output_warnings",
            "version_identity",
        }
        data = valid_qe_envelope()
        data["request"]["mode"] = "audit_run"  # type: ignore[index]
        data["route"].update(  # type: ignore[union-attr]
            {
                "skill": "vasp-rigorous-calculations",
                "software": "vasp",
                "task": "static",
            }
        )
        data["authorization"]["side_effects"] = ["local-execution"]  # type: ignore[index]
        data["claim_ceiling"] = "technical_run_gates_only"
        data["claim_scope"] = {
            "claim_id": "scope-vasp-run",
            "scope_kind": "computed-fact",
            "statement": "The VASP technical run gates passed for the exact audited case.",
            "observable": "technical-run-gates",
            "unit": None,
            "absolute_tolerance": None,
            "relative_tolerance": None,
            "evidence_ids": ["ev-audit"],
            "limitations": ["Numerical convergence and scientific acceptance remain unproved."],
        }
        data["tool_runs"][0].update(  # type: ignore[index]
            {
                "action_id": "vasp.audit-run",
                "tool": "audit_vasp_case.py --mode run",
                "gate_ids": sorted(audit_gate_ids),
            }
        )
        data["tool_runs"][1].update(  # type: ignore[index]
            {
                "action_id": "vasp.reference",
                "tool": "resolve_official_sources.py",
                "gate_ids": ["official_source_coverage"],
            }
        )
        data["gates"] = [
            {
                "id": "official_source_coverage",
                "native_status": "pass",
                "status": "pass",
                "evidence_ids": ["ev-official", "ev-reference"],
                "finding_codes": [],
            },
            *[
                {
                    "id": gate_id,
                    "native_status": "pass",
                    "status": "pass",
                    "evidence_ids": ["ev-audit"],
                    "finding_codes": [],
                }
                for gate_id in sorted(audit_gate_ids)
            ],
            {
                "id": "scientific_claim",
                "native_status": "blocked",
                "status": "blocked",
                "evidence_ids": ["ev-audit"],
                "finding_codes": ["SCIENTIFIC_CLAIM_BLOCKED"],
            },
        ]
        data["supported_facts"] = [
            {
                "id": "fact-vasp-run",
                "statement": "The implemented deterministic VASP technical-run gates passed.",
                "claim_level": "technical_run_gates_only",
                "evidence_ids": ["ev-audit"],
            }
        ]
        data["blocked_claims"] = [
            {
                "id": "claim-vasp-science",
                "statement": "Scientific acceptance is not established.",
                "gate_ids": ["scientific_claim"],
                "finding_codes": ["SCIENTIFIC_CLAIM_BLOCKED"],
            }
        ]
        data["smallest_next_action"]["gate_id"] = "scientific_claim"  # type: ignore[index]
        data["evidence"]["missing"] = ["observable-specific numerical convergence evidence"]  # type: ignore[index]
        self.assertEqual(finding_codes(data), set())

    def test_side_effect_vocabulary_and_registry_sets_match_common_contract(self) -> None:
        canonical = tuple(COMMON["$defs"]["sideEffect"]["enum"])
        self.assertEqual(operation_routes.SIDE_EFFECTS, canonical)
        for name, route in ROUTES["routes"].items():
            with self.subTest(route=name):
                self.assertTrue(route["side_effects"])
                self.assertEqual(
                    route["side_effects"],
                    sorted(route["side_effects"], key=operation_routes.SIDE_EFFECT_ORDER.__getitem__),
                )
                self.assertTrue(set(route["side_effects"]).issubset(canonical))
                self.assertEqual(route["side_effects"], SKILLS["skills"][name]["side_effects"])
                for action in route["actions"].values():
                    self.assertEqual(action["argv"][:2], ["python3", "-B"])
                    self.assertTrue(action["side_effects"])
                    self.assertIn("local-execution", action["side_effects"])
                    self.assertTrue(set(action["side_effects"]).issubset(route["side_effects"]))

    def test_route_registry_covers_every_skill_exactly(self) -> None:
        self.assertEqual(route_findings(ROUTES), [])
        routes = ROUTES["routes"]
        self.assertEqual(set(routes), set(SKILLS["skills"]))
        active = [name for name, route in routes.items() if route["lifecycle"] == "active"]
        development = [name for name, route in routes.items() if route["lifecycle"] == "development"]
        planned = [name for name, route in routes.items() if route["lifecycle"] == "planned"]
        self.assertEqual(len(active), 7)
        self.assertEqual(len(development), 19)
        self.assertEqual(len(planned), 0)

    def test_active_routes_have_tools_and_nonactive_routes_are_fail_closed(self) -> None:
        for name, route in ROUTES["routes"].items():
            with self.subTest(name=name):
                if route["lifecycle"] == "active":
                    self.assertTrue(route["routable"])
                    self.assertTrue(route["actions"])
                    self.assertEqual(set(route["first_tool"]), set(route["tool_sequence"]))
                    for mode, first_action in route["first_tool"].items():
                        self.assertEqual(first_action, route["tool_sequence"][mode][0])
                        self.assertIn(first_action, route["actions"])
                    self.assertEqual(route["handoff"]["status"], "enabled")
                    self.assertTrue(
                        all(SKILLS["skills"][name]["lifecycle"] == "active" for name in route["handoff"]["consumers"])
                    )
                    self.assertTrue(
                        all(
                            SKILLS["skills"][name]["lifecycle"] in {"development", "planned"}
                            for name in route["handoff"]["future_consumers"]
                        )
                    )
                else:
                    self.assertFalse(route["routable"])
                    self.assertEqual(
                        route["required_reads"],
                        [
                            "registry/skill-registry.yaml",
                            "registry/operation-routes.yaml",
                            f"skills/{name}/SKILL.md",
                            f"skills/{name}/references/weak-model-decision-table.json",
                        ],
                    )
                    self.assertEqual(route["first_tool"], {})
                    self.assertEqual(route["tool_sequence"], {})
                    self.assertEqual(route["actions"], {})
                    self.assertEqual(route["maximum_claim"], "no_positive_claim")
                    self.assertEqual(route["handoff"]["status"], "blocked")

    def test_development_route_cannot_borrow_another_skills_instructions(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["routes"]["gaussian-rigorous-calculations"]["required_reads"][2:] = [
            "skills/dft-reporting/SKILL.md",
            "skills/dft-reporting/references/weak-model-decision-table.json",
        ]
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_PLANNED_READ_SET_INVALID", codes)

    def test_missing_development_instruction_blocks_registry(self) -> None:
        table = (
            ISOLATED_ROOT
            / "skills"
            / "gaussian-rigorous-calculations"
            / "references"
            / "weak-model-decision-table.json"
        )
        hidden = table.with_suffix(".hidden")
        table.rename(hidden)
        try:
            findings = route_findings(ROUTES, dependency_source_validation=False)
        finally:
            hidden.rename(table)
        self.assertTrue(
            any(
                item["code"] == "ROUTE_READ_MISSING"
                and item["location"]
                == "routes/gaussian-rigorous-calculations/required_reads/3"
                for item in findings
            )
        )

    def test_active_and_development_cli_decisions_have_stable_exit_codes(self) -> None:
        registry_args = [
            "--registry",
            str(ISOLATED_REGISTRY_PATHS["operation-routes"]),
            "--skill-registry",
            str(ISOLATED_REGISTRY_PATHS["skill-registry"]),
            "--interface-registry",
            str(ISOLATED_REGISTRY_PATHS["interface-registry"]),
            "--software-registry",
            str(ISOLATED_REGISTRY_PATHS["software-registry"]),
            "--environment-profiles",
            str(ISOLATED_REGISTRY_PATHS["environment-profiles"]),
            "--root",
            str(ISOLATED_ROOT),
        ]
        active = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "operation_routes.py"),
                *registry_args,
                "route",
                "qe-rigorous-calculations",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(active.returncode, 0, active.stderr)
        active_result = json.loads(active.stdout)
        self.assertEqual(active_result["decision"], "route_selected")
        self.assertEqual(active_result["response_policy"], operation_routes.RESPONSE_POLICY)
        development = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "operation_routes.py"),
                *registry_args,
                "route",
                "gaussian-rigorous-calculations",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(development.returncode, 2)
        development_result = json.loads(development.stdout)
        self.assertEqual(development_result["finding_codes"], ["ROUTE_PLANNED_NOT_ROUTABLE"])
        self.assertEqual(development_result["response_policy"], operation_routes.RESPONSE_POLICY)
        self.assertEqual(
            development_result["route"]["required_reads"],
            [
                "registry/skill-registry.yaml",
                "registry/operation-routes.yaml",
                "skills/gaussian-rigorous-calculations/SKILL.md",
                "skills/gaussian-rigorous-calculations/references/weak-model-decision-table.json",
            ],
        )
        self.assertEqual(development_result["route"]["maximum_claim"], "no_positive_claim")
        self.assertEqual(development_result["route"]["actions"], {})

    def test_unknown_route_is_blocked(self) -> None:
        code, result = operation_routes.route_decision(
            "invented-dft-skill",
            data=ROUTES,
            source_root=ISOLATED_ROOT,
            skill_data=ISOLATED_SKILLS,
            interface_data=ISOLATED_INTERFACES,
            software_data=SOFTWARE,
            environment_data=ENVIRONMENTS,
        )
        self.assertEqual(code, 2)
        self.assertEqual(result["finding_codes"], ["ROUTE_UNKNOWN_SKILL"])

    def test_duplicate_yaml_keys_are_rejected_before_routing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "routes.yaml"
            path.write_text("schema_version: '1.0'\nroutes: {}\nroutes: {}\n", encoding="utf-8")
            with self.assertRaises(registry_yaml.RegistryYAMLError) as caught:
                operation_routes.load_registry(path)
        self.assertEqual(caught.exception.code, "YAML_DUPLICATE_KEY")
        self.assertNotIn(directory, str(caught.exception))

    def test_invalid_skill_snapshot_blocks_before_route_action_parsing(self) -> None:
        mutated_routes = copy.deepcopy(ROUTES)
        mutated_routes["routes"]["qe-rigorous-calculations"]["actions"]["qe.audit-input"][
            "argv"
        ][0] = "python3 or use memory"
        mutated_skills = copy.deepcopy(ISOLATED_SKILLS)
        mutated_skills["schema_version"] = "999.0"
        findings = operation_routes.validation_findings(
            mutated_routes,
            source_root=ISOLATED_ROOT,
            skill_data=mutated_skills,
            interface_data=ISOLATED_INTERFACES,
            software_data=SOFTWARE,
            environment_data=ENVIRONMENTS,
        )
        codes = {item["code"] for item in findings}
        self.assertIn("ROUTE_SKILL_REGISTRY_INVALID", codes)
        self.assertNotIn("ROUTE_ACTION_NOT_DETERMINISTIC", codes)
        self.assertTrue(any("schema_version" in item["message"] for item in findings))

    def test_explicit_environment_snapshot_is_validated_without_disk_reload(self) -> None:
        mutated_environments = copy.deepcopy(ENVIRONMENTS)
        mutated_environments["schema_version"] = "999.0"
        findings = operation_routes.validation_findings(
            ROUTES,
            source_root=ISOLATED_ROOT,
            skill_data=ISOLATED_SKILLS,
            interface_data=ISOLATED_INTERFACES,
            software_data=SOFTWARE,
            environment_data=mutated_environments,
        )
        self.assertIn(
            "ROUTE_ENVIRONMENT_REGISTRY_INVALID",
            {item["code"] for item in findings},
        )

    def test_explicit_software_snapshot_is_validated_without_disk_reload(self) -> None:
        mutated_software = copy.deepcopy(SOFTWARE)
        mutated_software["schema_version"] = "999.0"
        findings = operation_routes.validation_findings(
            ROUTES,
            source_root=ISOLATED_ROOT,
            skill_data=ISOLATED_SKILLS,
            interface_data=ISOLATED_INTERFACES,
            software_data=mutated_software,
            environment_data=ENVIRONMENTS,
        )
        self.assertIn(
            "ROUTE_SOFTWARE_REGISTRY_INVALID",
            {item["code"] for item in findings},
        )

    def test_central_audit_can_skip_only_duplicate_source_inventory(self) -> None:
        dirty_copy = ISOLATED_ROOT / "skills" / "qe-rigorous-calculations" / "SKILL 2.md"
        dirty_copy.write_text("temporary duplicate", encoding="utf-8")
        try:
            strict_codes = {item["code"] for item in route_findings(ROUTES)}
            route_only_findings = route_findings(
                ROUTES,
                dependency_source_validation=False,
            )
        finally:
            dirty_copy.unlink()
        self.assertIn("ROUTE_SKILL_REGISTRY_INVALID", strict_codes)
        self.assertEqual(route_only_findings, [])

    def test_governance_only_interface_cannot_enter_skill_handoff_routing(self) -> None:
        mutated_interfaces = copy.deepcopy(ISOLATED_INTERFACES)
        mutated_interfaces["interfaces"]["run-manifest@1.0"]["classification"] = {
            "document_kind": "content-addressed-record",
            "routing_scope": "governance-only",
        }
        codes = {
            item["code"]
            for item in route_findings(ROUTES, interfaces=mutated_interfaces)
        }
        self.assertIn("ROUTE_HANDOFF_INTERFACE_GOVERNANCE_ONLY", codes)

    def test_mutation_cannot_make_development_route_routable(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["routes"]["gaussian-rigorous-calculations"]["routable"] = True
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_PLANNED_ROUTABLE", codes)

    def test_mutation_cannot_hide_a_registered_skill(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        del mutated["routes"]["dft-postprocess"]
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_SET_MISMATCH", codes)

    def test_mutation_cannot_skip_first_tool(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["routes"]["qe-rigorous-calculations"]["first_tool"]["audit_input"] = "qe.reference"
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_TOOL_SEQUENCE_INVALID", codes)

    def test_action_argv_cannot_contain_prose_or_shell_fragments(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["routes"]["qe-rigorous-calculations"]["actions"]["qe.audit-input"]["argv"][0] = (
            "python3 or answer from memory"
        )
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_ACTION_NOT_DETERMINISTIC", codes)

    def test_action_script_must_be_a_real_safe_repository_entrypoint(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["routes"]["qe-rigorous-calculations"]["actions"]["qe.audit-input"]["argv"][2] = (
            "skills/qe-rigorous-calculations/scripts/missing_guard.py"
        )
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_ACTION_SCRIPT_INVALID", codes)

    def test_python_no_bytecode_flag_is_required_in_exact_position(self) -> None:
        for label, argv_prefix in (
            ("missing", ["python3"]),
            ("misplaced", ["python3", "skills/qe-rigorous-calculations/scripts/qe_guard.py", "-B"]),
        ):
            with self.subTest(label=label):
                mutated = copy.deepcopy(ROUTES)
                argv = mutated["routes"]["qe-rigorous-calculations"]["actions"]["qe.audit-input"]["argv"]
                script_and_args = argv[2:]
                argv[:] = argv_prefix + (script_and_args if label == "missing" else script_and_args[1:])
                codes = {item["code"] for item in route_findings(mutated)}
                self.assertIn("ROUTE_ACTION_NOT_DETERMINISTIC", codes)

    def test_unreachable_action_is_rejected(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["routes"]["qe-rigorous-calculations"]["actions"]["qe.unreachable"] = copy.deepcopy(
            mutated["routes"]["qe-rigorous-calculations"]["actions"]["qe.audit-input"]
        )
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_ACTION_UNREACHABLE", codes)

    def test_action_success_codes_and_side_effects_cannot_exceed_wrapper_contract(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        action = mutated["routes"]["qe-rigorous-calculations"]["actions"]["qe.audit-input"]
        action["success_exit_codes"] = [4]
        action["side_effects"] = ["local-execution", "scheduler-submit"]
        action["requires_authorization"] = False
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_ACTION_INVALID", codes)

    def test_legacy_side_effect_labels_and_singular_field_are_rejected(self) -> None:
        for legacy in ("external-execution", "remote-execution"):
            with self.subTest(legacy=legacy):
                mutated = copy.deepcopy(ROUTES)
                action = mutated["routes"]["qe-rigorous-calculations"]["actions"]["qe.audit-input"]
                action["side_effects"] = [legacy]
                codes = {
                    item["code"] for item in route_findings(mutated)
                }
                self.assertIn("ROUTE_ACTION_INVALID", codes)
        mutated = copy.deepcopy(ROUTES)
        route = mutated["routes"]["qe-rigorous-calculations"]
        route["side_effect"] = route.pop("side_effects")
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_FIELDS_INVALID", codes)

        mutated_skills = copy.deepcopy(ISOLATED_SKILLS)
        skill = mutated_skills["skills"]["qe-rigorous-calculations"]
        skill["side_effect_class"] = skill.pop("side_effects")
        codes = {
            item["code"]
            for item in route_findings(ROUTES, skills=mutated_skills)
        }
        self.assertIn("ROUTE_SKILL_REGISTRY_INVALID", codes)

    def test_route_side_effect_sets_are_nonempty_unique_and_canonically_ordered(self) -> None:
        mutations = (
            [],
            ["local-execution", "local-write"],
            ["local-write", "local-write", "local-execution"],
            ["read-only", "local-execution"],
        )
        for side_effects in mutations:
            with self.subTest(side_effects=side_effects):
                mutated = copy.deepcopy(ROUTES)
                mutated["routes"]["cif-structure-analysis"]["side_effects"] = side_effects
                codes = {
                    item["code"] for item in route_findings(mutated)
                }
                self.assertTrue({"ROUTE_ENTRY_INVALID", "ROUTE_SIDE_EFFECT_MISMATCH"}.intersection(codes))

    def test_handoff_interfaces_and_consumers_resolve_without_planned_activation(self) -> None:
        mutations = {
            "unknown-interface": (
                lambda route: route["handoff"]["produces"].append("invented-interface@1.0"),
                "ROUTE_HANDOFF_INTERFACE_UNKNOWN",
            ),
            "planned-interface-on-active-route": (
                lambda route: route["handoff"]["produces"].append("ovito-pipeline-spec@1.0"),
                "ROUTE_HANDOFF_INTERFACE_INACTIVE",
            ),
            "unknown-consumer": (
                lambda route: route["handoff"]["consumers"].append("invented-skill"),
                "ROUTE_HANDOFF_CONSUMER_UNKNOWN",
            ),
            "planned-consumer-in-active-set": (
                lambda route: route["handoff"]["consumers"].append("gaussian-rigorous-calculations"),
                "ROUTE_HANDOFF_CONSUMER_LIFECYCLE_INVALID",
            ),
        }
        for label, (mutate, expected_code) in mutations.items():
            with self.subTest(mutation=label):
                mutated = copy.deepcopy(ROUTES)
                mutate(mutated["routes"]["cif-structure-analysis"])
                codes = {item["code"] for item in route_findings(mutated)}
                self.assertIn(expected_code, codes)

    def test_active_automatic_handoff_graph_must_remain_acyclic(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["routes"]["dft-postprocess"]["handoff"]["consumers"].append(
            "qe-rigorous-calculations"
        )
        codes = {item["code"] for item in route_findings(mutated)}
        self.assertIn("ROUTE_HANDOFF_CYCLE", codes)

    def test_action_templates_match_live_entrypoint_help(self) -> None:
        bytecode_before = {
            path.relative_to(ROOT).as_posix() for path in (ROOT / "skills").rglob("*.pyc")
        }
        subprocess_environment = os.environ.copy()
        subprocess_environment.pop("PYTHONDONTWRITEBYTECODE", None)
        for skill_name, route in ROUTES["routes"].items():
            for action_id, action in route["actions"].items():
                argv = action["argv"]
                prefix = argv[:3]
                for token in argv[3:]:
                    if token.startswith("-") or token.startswith("<"):
                        break
                    prefix.append(token)
                with self.subTest(skill=skill_name, action=action_id):
                    result = subprocess.run(
                        [sys.executable, *prefix[1:], "--help"],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        env=subprocess_environment,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    help_text = result.stdout + result.stderr
                    for flag in {token for token in argv if token.startswith("--")}:
                        self.assertIn(flag, help_text)
        bytecode_after = {
            path.relative_to(ROOT).as_posix() for path in (ROOT / "skills").rglob("*.pyc")
        }
        self.assertEqual(
            bytecode_after,
            bytecode_before,
            "registered python3 -B actions must not create source-tree bytecode",
        )


class EnvelopeSchemaTests(unittest.TestCase):
    def test_schema_is_valid_draft_202012_and_strict(self) -> None:
        Draft202012Validator.check_schema(SCHEMA)
        self.assertEqual(
            SCHEMA["$id"],
            "urn:vibe-dft-skills:contract:agent-action-envelope:1.0",
        )
        self.assertEqual(SCHEMA["properties"]["contract_name"], {"const": "agent-action-envelope"})
        self.assertIn("contract_name", SCHEMA["required"])
        self.assertEqual(SCHEMA["x-vibe-document-kind"], "projection")
        self.assertNotIn("x-vibe-record-id-field", SCHEMA)
        self.assertEqual(
            SCHEMA["x-vibe-semantic-obligations"],
            list(validate_agent_answer.EXTERNAL_SEMANTIC_OBLIGATIONS),
        )
        data = valid_qe_envelope()
        validator = validate_agent_answer.build_schema_validator(SCHEMA)
        self.assertEqual(list(validator.iter_errors(data)), [])
        data["invented"] = True
        self.assertTrue(list(validator.iter_errors(data)))

    def test_scientific_acceptance_and_side_effects_reference_frozen_common_contract(self) -> None:
        common_urn = "urn:vibe-dft-skills:contract:common-definitions:1.0"
        self.assertEqual(
            SCHEMA["properties"]["scientific_acceptance"]["$ref"],
            f"{common_urn}#/$defs/scientificAcceptance",
        )
        self.assertEqual(
            SCHEMA["$defs"]["authorization"]["properties"]["side_effects"]["$ref"],
            f"{common_urn}#/$defs/sideEffectSet",
        )
        self.assertEqual(
            COMMON["$defs"]["scientificAcceptance"]["enum"],
            ["not_assessed", "requires_human_review", "accepted", "rejected"],
        )

    def test_legacy_acceptance_and_side_effect_shapes_fail_closed(self) -> None:
        data = valid_qe_envelope()
        data["scientific_acceptance"] = "requires_expert_review"
        self.assertIn("ANSWER_SCHEMA_INVALID", finding_codes(data))

        data = valid_qe_envelope()
        authorization = data["authorization"]
        authorization["side_effect"] = authorization.pop("side_effects")  # type: ignore[union-attr]
        self.assertIn("ANSWER_SCHEMA_INVALID", finding_codes(data))

        for invalid in ([], ["external-execution"], ["remote-execution"], ["local-execution", "local-execution"]):
            with self.subTest(side_effects=invalid):
                data = valid_qe_envelope()
                data["authorization"]["side_effects"] = invalid  # type: ignore[index]
                self.assertIn("ANSWER_SCHEMA_INVALID", finding_codes(data))

    def test_nested_objects_reject_extra_fields(self) -> None:
        data = valid_qe_envelope()
        data["authorization"]["implicit_permission"] = True  # type: ignore[index]
        self.assertIn("ANSWER_SCHEMA_INVALID", finding_codes(data))

    def test_local_record_ref_shape_is_equivalent_to_frozen_common_contract(self) -> None:
        local = SCHEMA["$defs"]["record_ref"]
        common = COMMON["$defs"]["recordRef"]
        self.assertEqual(local["required"], common["required"])
        self.assertFalse(local["additionalProperties"])
        self.assertEqual(
            local["properties"]["contract_name"]["pattern"],
            COMMON["$defs"]["contractName"]["pattern"],
        )
        self.assertEqual(
            local["properties"]["schema_version"]["pattern"],
            COMMON["$defs"]["schemaVersion"]["pattern"],
        )
        self.assertEqual(
            local["properties"]["record_id"]["pattern"],
            COMMON["$defs"]["safeId"]["pattern"],
        )
        self.assertEqual(
            local["properties"]["role"]["pattern"],
            COMMON["$defs"]["contractName"]["pattern"],
        )

    def test_valid_limited_qe_answer_passes(self) -> None:
        self.assertEqual(finding_codes(valid_qe_envelope()), set())

    def test_external_semantic_obligations_cannot_be_dropped_by_schema_override(self) -> None:
        mutated_schema = copy.deepcopy(SCHEMA)
        mutated_schema["x-vibe-semantic-obligations"] = []
        codes = {
            item["code"]
            for item in validate_agent_answer.validation_findings(
                valid_qe_envelope(),
                schema=mutated_schema,
                routes=ROUTES,
                skills=ISOLATED_SKILLS,
                interfaces=ISOLATED_INTERFACES,
                software=SOFTWARE,
                environments=ENVIRONMENTS,
                source_root=ISOLATED_ROOT,
            )
        }
        self.assertIn("ANSWER_SCHEMA_SEMANTIC_OBLIGATIONS_INVALID", codes)

    def test_official_documented_fact_can_pass_without_tool_execution(self) -> None:
        self.assertEqual(finding_codes(documented_qe_envelope()), set())

    def test_safe_development_route_block_answer_passes(self) -> None:
        self.assertEqual(finding_codes(development_gaussian_envelope()), set())

    def test_answer_cannot_bypass_an_invalid_dependency_snapshot(self) -> None:
        mutated_environments = copy.deepcopy(ENVIRONMENTS)
        mutated_environments["schema_version"] = "999.0"
        codes = {
            item["code"]
            for item in validate_agent_answer.validation_findings(
                development_gaussian_envelope(),
                schema=SCHEMA,
                routes=ROUTES,
                skills=ISOLATED_SKILLS,
                interfaces=ISOLATED_INTERFACES,
                software=SOFTWARE,
                environments=mutated_environments,
                source_root=ISOLATED_ROOT,
            )
        }
        self.assertIn("ANSWER_ROUTE_REGISTRY_INVALID", codes)

    def test_explicit_expert_acceptance_with_hashed_review_passes(self) -> None:
        self.assertEqual(finding_codes(accepted_qe_envelope()), set())


class MutationAndNegativeTests(unittest.TestCase):
    def test_action_state_must_equal_canonical_derivation(self) -> None:
        canonical = "local_gate_blocked"
        action_states = SCHEMA["properties"]["action_state"]["enum"]
        self.assertEqual(len(action_states), 12)
        for action_state in action_states:
            with self.subTest(action_state=action_state):
                data = valid_qe_envelope()
                data["action_state"] = action_state
                codes = finding_codes(data)
                if action_state == canonical:
                    self.assertNotIn("ANSWER_ACTION_STATE_NONCANONICAL", codes)
                else:
                    self.assertIn("ANSWER_ACTION_STATE_NONCANONICAL", codes)

    def test_claim_ceiling_must_equal_highest_supported_level(self) -> None:
        canonical = "input_gates_only"
        claim_ceilings = SCHEMA["$defs"]["claim_ceiling"]["enum"]
        self.assertEqual(len(claim_ceilings), 6)
        for claim_ceiling in claim_ceilings:
            with self.subTest(claim_ceiling=claim_ceiling):
                data = valid_qe_envelope()
                data["action_state"] = "local_gate_blocked"
                data["claim_ceiling"] = claim_ceiling
                if claim_ceiling == "no_positive_claim":
                    data["claim_scope"] = None
                    data["supported_facts"] = []
                else:
                    data["supported_facts"][0]["claim_level"] = claim_ceiling  # type: ignore[index]
                codes = finding_codes(data)
                if claim_ceiling == canonical:
                    self.assertNotIn("ANSWER_CLAIM_CEILING_NONCANONICAL", codes)
                else:
                    self.assertIn("ANSWER_CLAIM_CEILING_NONCANONICAL", codes)

    def test_development_route_cannot_emit_positive_fact(self) -> None:
        data = development_gaussian_envelope()
        data["evidence"]["items"].append(  # type: ignore[index]
            {
                "id": "ev-fake",
                "role": "fake-output",
                "status": "present",
                "sha256": "f" * 64,
                "record_ref": None,
                "source_label": "fake.json",
                "limitations": [],
            }
        )
        data["claim_ceiling"] = "documented_behavior_only"
        data["supported_facts"] = [
            {
                "id": "fact-fake",
                "statement": "Gaussian is ready to run.",
                "claim_level": "documented_behavior_only",
                "evidence_ids": ["ev-fake"],
            }
        ]
        codes = finding_codes(data)
        self.assertIn("ANSWER_PLANNED_ROUTE_INVOCATION", codes)
        self.assertIn("ANSWER_CLAIM_EXCEEDS_ROUTE", codes)

    def test_development_route_cannot_run_a_tool(self) -> None:
        data = development_gaussian_envelope()
        data["tool_runs"] = [
            {
                "id": "tool-fake",
                "action_id": "gaussian.run",
                "tool": "g16 job.com",
                "required": True,
                "status": "succeeded",
                "exit_code": 0,
                "report_sha256": "1" * 64,
                "gate_ids": ["route-availability"],
                "finding_codes": [],
            }
        ]
        self.assertIn("ANSWER_PLANNED_ROUTE_INVOCATION", finding_codes(data))

    def test_required_tool_failure_forbids_positive_claim(self) -> None:
        data = valid_qe_envelope()
        tool = data["tool_runs"][0]  # type: ignore[index]
        tool["status"] = "failed"
        tool["exit_code"] = 2
        codes = finding_codes(data)
        self.assertIn("ANSWER_TOOL_FAILURE_POSITIVE_CLAIM", codes)

    def test_nonzero_exit_cannot_be_called_success(self) -> None:
        data = valid_qe_envelope()
        data["tool_runs"][0]["exit_code"] = 2  # type: ignore[index]
        codes = finding_codes(data)
        self.assertIn("ANSWER_TOOL_SUCCESS_INVALID", codes)
        self.assertIn("ANSWER_NONZERO_EXIT_MISCLASSIFIED", codes)
        self.assertIn("ANSWER_ACTION_EXIT_STATUS_MISMATCH", codes)

    def test_tool_report_hash_must_be_bound_to_evidence_inventory(self) -> None:
        data = valid_qe_envelope()
        data["tool_runs"][0]["report_sha256"] = "8" * 64  # type: ignore[index]
        codes = finding_codes(data)
        self.assertIn("ANSWER_TOOL_REPORT_EVIDENCE_MISSING", codes)
        self.assertIn("ANSWER_POSITIVE_FACT_TOOL_EVIDENCE_MISSING", codes)

    def test_tool_report_record_type_and_role_must_align(self) -> None:
        data = valid_qe_envelope()
        audit = next(  # type: ignore[index]
            item for item in data["evidence"]["items"] if item["id"] == "ev-audit"
        )
        audit["record_ref"]["role"] = "source"
        codes = finding_codes(data)
        self.assertIn("ANSWER_TOOL_EVIDENCE_RECORD_INVALID", codes)
        self.assertIn("ANSWER_TOOL_REPORT_EVIDENCE_MISSING", codes)

    def test_evidence_and_record_reference_hashes_must_match(self) -> None:
        data = valid_qe_envelope()
        data["evidence"]["items"][1]["record_ref"]["sha256"] = "9" * 64  # type: ignore[index]
        codes = finding_codes(data)
        self.assertIn("ANSWER_EVIDENCE_RECORD_HASH_MISMATCH", codes)

    def test_record_reference_must_be_structured(self) -> None:
        data = valid_qe_envelope()
        data["evidence"]["items"][1]["record_ref"] = "trust me"  # type: ignore[index]
        self.assertIn("ANSWER_SCHEMA_INVALID", finding_codes(data))

    def test_blocker_cannot_be_hidden(self) -> None:
        data = valid_qe_envelope()
        data["blocked_claims"] = []
        self.assertIn("ANSWER_BLOCKER_HIDDEN", finding_codes(data))

    def test_blocker_requires_smallest_next_action(self) -> None:
        data = valid_qe_envelope()
        data["smallest_next_action"] = None
        self.assertIn("ANSWER_NEXT_ACTION_MISSING", finding_codes(data))

    def test_next_action_must_reference_its_finding(self) -> None:
        data = valid_qe_envelope()
        data["smallest_next_action"]["finding_code"] = "INVENTED_FIX"  # type: ignore[index]
        self.assertIn("ANSWER_NEXT_ACTION_UNLINKED", finding_codes(data))

    def test_fact_cannot_exceed_envelope_claim_ceiling(self) -> None:
        data = valid_qe_envelope()
        data["supported_facts"][0]["claim_level"] = "eligible_for_expert_review"  # type: ignore[index]
        self.assertIn("ANSWER_CLAIM_EXCEEDS_CEILING", finding_codes(data))

    def test_positive_claim_cannot_bypass_tools_and_layered_gates(self) -> None:
        data = valid_qe_envelope()
        data["claim_ceiling"] = "eligible_for_expert_review"
        data["claim_scope"] = {
            "claim_id": "scope-bypass",
            "scope_kind": "scientific-claim",
            "statement": "An unsupported elevated claim.",
            "observable": "total-energy",
            "unit": "eV",
            "absolute_tolerance": 0.001,
            "relative_tolerance": None,
            "evidence_ids": ["ev-audit"],
            "limitations": [],
        }
        data["gates"] = []
        data["tool_runs"] = []
        data["blocked_claims"] = []
        data["smallest_next_action"] = None
        data["supported_facts"][0]["claim_level"] = "eligible_for_expert_review"  # type: ignore[index]
        codes = finding_codes(data)
        self.assertIn("ANSWER_CLAIM_GATE_PROFILE_INCOMPLETE", codes)
        self.assertIn("ANSWER_POSITIVE_FACT_TOOL_EVIDENCE_MISSING", codes)
        self.assertIn("ANSWER_ACTION_CLAIM_CEILING_EXCEEDED", codes)

    def test_accepted_status_cannot_use_ordinary_audit_as_human_review(self) -> None:
        data = accepted_qe_envelope()
        data["claim_scope"]["evidence_ids"] = ["ev-audit"]  # type: ignore[index]
        for gate in data["gates"]:  # type: ignore[union-attr]
            gate["evidence_ids"] = [
                "ev-audit" if evidence_id == "ev-review" else evidence_id
                for evidence_id in gate["evidence_ids"]
            ]
        data["evidence"]["items"] = [  # type: ignore[index]
            item for item in data["evidence"]["items"] if item["id"] != "ev-review"  # type: ignore[index]
        ]
        for item in data["evidence"]["items"]:  # type: ignore[union-attr]
            if item["id"] == "ev-audit":
                item["role"] = "human-expert-decision-record"
        data["supported_facts"][0]["evidence_ids"] = ["ev-audit"]  # type: ignore[index]
        codes = finding_codes(data)
        self.assertIn("ANSWER_HUMAN_EVIDENCE_RECORD_INVALID", codes)
        self.assertIn("ANSWER_HUMAN_DECISION_EVIDENCE_MISSING", codes)
        self.assertIn("ANSWER_ACCEPTANCE_CLAIM_SCOPE_INVALID", codes)
        self.assertIn("ANSWER_SCIENTIFIC_DECISION_EVIDENCE_MISMATCH", codes)

    def test_ordinary_tool_record_cannot_become_official_by_role_relabeling(self) -> None:
        data = valid_qe_envelope()
        data["request"]["mode"] = "explain"  # type: ignore[index]
        data["claim_ceiling"] = "documented_behavior_only"
        data["claim_scope"] = {
            "claim_id": "scope-fake-official",
            "scope_kind": "documented-behavior",
            "statement": "A role-only official-source impersonation attempt.",
            "observable": None,
            "unit": None,
            "absolute_tolerance": None,
            "relative_tolerance": None,
            "evidence_ids": ["ev-audit"],
            "limitations": [],
        }
        data["tool_runs"] = []
        data["gates"][0]["id"] = "official-source-coverage"  # type: ignore[index]
        data["gates"][0]["evidence_ids"] = ["ev-audit"]  # type: ignore[index]
        data["supported_facts"][0].update(  # type: ignore[index]
            {"claim_level": "documented_behavior_only", "evidence_ids": ["ev-audit"]}
        )
        audit = next(  # type: ignore[index]
            item for item in data["evidence"]["items"] if item["id"] == "ev-audit"
        )
        audit["role"] = "official-source-snapshot"
        codes = finding_codes(data)
        self.assertIn("ANSWER_OFFICIAL_EVIDENCE_RECORD_INVALID", codes)
        self.assertIn("ANSWER_POSITIVE_FACT_TOOL_EVIDENCE_MISSING", codes)

    def test_scientific_decision_ref_must_exactly_match_human_evidence_record(self) -> None:
        data = accepted_qe_envelope()
        data["scientific_decision_ref"]["record_id"] = "decision-mismatch"  # type: ignore[index]
        self.assertIn("ANSWER_SCIENTIFIC_DECISION_EVIDENCE_MISMATCH", finding_codes(data))

    def test_rejected_verdict_also_requires_a_hashed_human_decision_record(self) -> None:
        missing = valid_qe_envelope()
        missing["scientific_acceptance"] = "rejected"
        codes = finding_codes(missing)
        self.assertIn("ANSWER_SCHEMA_INVALID", codes)
        self.assertIn("ANSWER_SCIENTIFIC_DECISION_REF_INVALID", codes)

        unbound = accepted_qe_envelope()
        unbound["scientific_acceptance"] = "rejected"
        unbound["evidence"]["items"] = [  # type: ignore[index]
            item
            for item in unbound["evidence"]["items"]  # type: ignore[index]
            if item["id"] != "ev-review"
        ]
        self.assertIn("ANSWER_SCIENTIFIC_DECISION_EVIDENCE_MISMATCH", finding_codes(unbound))

    def test_explicit_evidenced_not_applicable_gate_can_satisfy_acceptance_profile(self) -> None:
        data = accepted_qe_envelope()
        for gate in data["gates"]:  # type: ignore[union-attr]
            if gate["id"] == "task-specific-validation":
                gate["native_status"] = "not_applicable"
                gate["status"] = "not_applicable"
                gate["finding_codes"] = ["TASK_VALIDATION_NOT_APPLICABLE"]
        self.assertEqual(finding_codes(data), set())

    def test_undeclared_tool_action_is_blocked(self) -> None:
        data = valid_qe_envelope()
        data["tool_runs"][0]["action_id"] = "qe.answer-from-memory"  # type: ignore[index]
        self.assertIn("ANSWER_TOOL_ACTION_UNDECLARED", finding_codes(data))

    def test_envelope_cannot_skip_mode_first_action(self) -> None:
        data = valid_qe_envelope()
        data["tool_runs"][0]["action_id"] = "qe.reference"  # type: ignore[index]
        self.assertIn("ANSWER_FIRST_TOOL_SKIPPED", finding_codes(data))

    def test_envelope_tool_actions_must_follow_registered_order(self) -> None:
        data = accepted_qe_envelope()
        data["tool_runs"] = list(reversed(data["tool_runs"]))  # type: ignore[arg-type]
        codes = finding_codes(data)
        self.assertIn("ANSWER_FIRST_TOOL_SKIPPED", codes)
        self.assertIn("ANSWER_TOOL_SEQUENCE_VIOLATION", codes)

    def test_execution_blocker_caps_claim_at_input_gates(self) -> None:
        data = valid_qe_envelope()
        data["claim_ceiling"] = "technical_run_gates_only"
        data["supported_facts"][0]["claim_level"] = "technical_run_gates_only"  # type: ignore[index]
        data["gates"].insert(  # type: ignore[union-attr]
            1,
            {
                "id": "execution-completion",
                "native_status": "incomplete",
                "status": "blocked",
                "evidence_ids": ["ev-audit"],
                "finding_codes": ["EXECUTION_INCOMPLETE"],
            },
        )
        data["blocked_claims"].append(  # type: ignore[union-attr]
            {
                "id": "claim-execution",
                "statement": "Execution completion is blocked.",
                "gate_ids": ["execution-completion"],
                "finding_codes": ["EXECUTION_INCOMPLETE"],
            }
        )
        codes = finding_codes(data)
        self.assertIn("ANSWER_GATE_CEILING_EXCEEDED", codes)

    def test_fact_requires_existing_evidence_id(self) -> None:
        data = valid_qe_envelope()
        data["supported_facts"][0]["evidence_ids"] = ["ev-missing"]  # type: ignore[index]
        self.assertIn("ANSWER_EVIDENCE_LINK_MISSING", finding_codes(data))

    def test_fact_requires_present_hashed_evidence(self) -> None:
        data = valid_qe_envelope()
        audit = next(  # type: ignore[index]
            item for item in data["evidence"]["items"] if item["id"] == "ev-audit"
        )
        audit["status"] = "missing"
        audit["sha256"] = None
        codes = finding_codes(data)
        self.assertIn("ANSWER_EVIDENCE_NOT_USABLE", codes)

    def test_native_status_cannot_be_silently_remapped(self) -> None:
        data = valid_qe_envelope()
        scientific_claim = next(  # type: ignore[index]
            gate for gate in data["gates"] if gate["id"] == "scientific-claim"
        )
        scientific_claim["status"] = "pass"
        self.assertIn("ANSWER_NATIVE_STATUS_MISMATCH", finding_codes(data))

    def test_unknown_native_status_is_rejected(self) -> None:
        data = valid_qe_envelope()
        data["gates"][0]["native_status"] = "looks fine"  # type: ignore[index]
        self.assertIn("ANSWER_NATIVE_STATUS_UNMAPPED", finding_codes(data))

    def test_accepted_claim_requires_expert_review_gate(self) -> None:
        data = accepted_qe_envelope()
        data["gates"] = [  # type: ignore[assignment]
            gate for gate in data["gates"] if gate["id"] != "expert-scientific-review"  # type: ignore[index]
        ]
        self.assertIn("ANSWER_EXPERT_ACCEPTANCE_MISSING", finding_codes(data))

    def test_accepted_claim_cannot_hide_physical_blocker(self) -> None:
        data = accepted_qe_envelope()
        for gate in data["gates"]:  # type: ignore[union-attr]
            if gate["id"] == "physical-validity":
                gate["native_status"] = "blocked"
                gate["status"] = "blocked"
                gate["finding_codes"] = ["PHYSICAL_VALIDITY_BLOCKED"]
        data["blocked_claims"] = [
            {
                "id": "claim-physical",
                "statement": "Physical validity is blocked.",
                "gate_ids": ["physical-validity"],
                "finding_codes": ["PHYSICAL_VALIDITY_BLOCKED"],
            }
        ]
        data["smallest_next_action"] = {
            "gate_id": "physical-validity",
            "finding_code": "PHYSICAL_VALIDITY_BLOCKED",
            "action": "Obtain independent physical validation.",
            "required_inputs": ["expert physical-model evidence"],
            "requires_authorization": False,
            "why_minimal": "Physical validity is the first unresolved scientific gate.",
        }
        self.assertIn("ANSWER_ACCEPTANCE_WITH_BLOCKER", finding_codes(data))

    def test_private_absolute_path_is_rejected(self) -> None:
        data = valid_qe_envelope()
        data["limitations"].append("Source was copied from /Users/alice/private/run.out")  # type: ignore[union-attr]
        self.assertIn("ANSWER_PRIVATE_PATH_EXPOSED", finding_codes(data))

    def test_official_https_url_is_not_misclassified_as_private_path(self) -> None:
        data = valid_qe_envelope()
        data["limitations"].append("Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.html")  # type: ignore[union-attr]
        self.assertNotIn("ANSWER_PRIVATE_PATH_EXPOSED", finding_codes(data))

    def test_credential_like_content_is_rejected(self) -> None:
        data = valid_qe_envelope()
        data["limitations"].append("api_key=do-not-record-this")  # type: ignore[union-attr]
        self.assertIn("ANSWER_SECRET_EXPOSED", finding_codes(data))

    def test_handoff_requires_declared_contract(self) -> None:
        data = valid_qe_envelope()
        data["action_state"] = "handoff_ready"
        manifest_ref = add_handoff_manifest_evidence(data, "artifact-manifest@1.0")
        data["handoffs"] = [
            {
                "producer_skill": "qe-rigorous-calculations",
                "consumer_skill": "dft-postprocess",
                "contract": "artifact-manifest@1.0",
                "manifest_ref": manifest_ref,
                "status": "ready",
                "source_evidence_ids": ["ev-manifest"],
                "claim_ceiling": "input_gates_only",
                "limitations": [],
            }
        ]
        self.assertIn("ANSWER_HANDOFF_CONTRACT_UNDECLARED", finding_codes(data))

    def test_ready_handoff_requires_present_hashed_source_evidence(self) -> None:
        data = valid_qe_envelope()
        data["action_state"] = "handoff_ready"
        manifest_ref = add_handoff_manifest_evidence(data, "run-manifest@1.0")
        data["evidence"]["items"][-1]["status"] = "external"  # type: ignore[index]
        data["evidence"]["items"][-1]["sha256"] = None  # type: ignore[index]
        data["handoffs"] = [
            {
                "producer_skill": "qe-rigorous-calculations",
                "consumer_skill": "dft-postprocess",
                "contract": "run-manifest@1.0",
                "manifest_ref": manifest_ref,
                "status": "ready",
                "source_evidence_ids": ["ev-manifest"],
                "claim_ceiling": "input_gates_only",
                "limitations": [],
            }
        ]
        self.assertIn("ANSWER_EVIDENCE_NOT_USABLE", finding_codes(data))

    def test_ready_handoff_accepts_only_active_declared_consumers(self) -> None:
        def add_handoff(data: dict[str, object], consumer: str) -> None:
            # This test isolates handoff routing, so remove the fixture's
            # higher-precedence scientific hard blocker first.
            data["evidence"]["missing"] = []  # type: ignore[index]
            data["gates"] = [  # type: ignore[index]
                gate
                for gate in data["gates"]  # type: ignore[index]
                if gate["id"] != "scientific-claim"
            ]
            data["blocked_claims"] = []
            data["smallest_next_action"] = None
            data["action_state"] = "handoff_ready"
            manifest_ref = add_handoff_manifest_evidence(data, "run-manifest@1.0")
            data["handoffs"] = [
                {
                    "producer_skill": "qe-rigorous-calculations",
                    "consumer_skill": consumer,
                    "contract": "run-manifest@1.0",
                    "manifest_ref": manifest_ref,
                    "status": "ready",
                    "source_evidence_ids": ["ev-manifest"],
                    "claim_ceiling": "input_gates_only",
                    "limitations": [],
                }
            ]

        active = valid_qe_envelope()
        add_handoff(active, "dft-postprocess")
        self.assertEqual(finding_codes(active), set())

        development = valid_qe_envelope()
        add_handoff(development, "dft-project-orchestrator")
        self.assertIn("ANSWER_HANDOFF_CONSUMER_INACTIVE", finding_codes(development))

        wrong_contract_consumer = valid_qe_envelope()
        add_handoff(wrong_contract_consumer, "cif-structure-analysis")
        self.assertIn("ANSWER_HANDOFF_CONTRACT_NOT_CONSUMED", finding_codes(wrong_contract_consumer))

    def test_ready_handoff_binds_contract_record_id_hash_and_evidence(self) -> None:
        for field, replacement in (
            ("contract_name", "artifact-manifest"),
            ("schema_version", "9.9"),
            ("record_id", "different-manifest"),
            ("sha256", "f" * 64),
        ):
            with self.subTest(field=field):
                data = valid_qe_envelope()
                data["action_state"] = "handoff_ready"
                manifest_ref = add_handoff_manifest_evidence(data, "run-manifest@1.0")
                manifest_ref[field] = replacement
                data["handoffs"] = [
                    {
                        "producer_skill": "qe-rigorous-calculations",
                        "consumer_skill": "dft-postprocess",
                        "contract": "run-manifest@1.0",
                        "manifest_ref": manifest_ref,
                        "status": "ready",
                        "source_evidence_ids": ["ev-manifest"],
                        "claim_ceiling": "input_gates_only",
                        "limitations": [],
                    }
                ]
                codes = finding_codes(data)
                self.assertTrue(
                    {
                        "ANSWER_HANDOFF_MANIFEST_REF_MISMATCH",
                        "ANSWER_HANDOFF_MANIFEST_EVIDENCE_MISMATCH",
                    }.intersection(codes)
                )

    def test_ready_handoff_rejects_arbitrary_present_hash_as_manifest_evidence(self) -> None:
        data = valid_qe_envelope()
        data["action_state"] = "handoff_ready"
        data["handoffs"] = [
            {
                "producer_skill": "qe-rigorous-calculations",
                "consumer_skill": "dft-postprocess",
                "contract": "run-manifest@1.0",
                "manifest_ref": {
                    "contract_name": "run-manifest",
                    "schema_version": "1.0",
                    "record_id": "manifest-001",
                    "sha256": "c" * 64,
                    "role": "handoff-manifest",
                },
                "status": "ready",
                "source_evidence_ids": ["ev-audit"],
                "claim_ceiling": "input_gates_only",
                "limitations": [],
            }
        ]
        self.assertIn("ANSWER_HANDOFF_MANIFEST_EVIDENCE_MISMATCH", finding_codes(data))

    def test_granted_authorization_requires_hashed_evidence_and_scope(self) -> None:
        data = valid_qe_envelope()
        data["authorization"]["state"] = "granted"  # type: ignore[index]
        self.assertIn("ANSWER_AUTHORIZATION_EVIDENCE_MISSING", finding_codes(data))

    def test_granted_authorization_rejects_arbitrary_present_agent_note(self) -> None:
        data = valid_qe_envelope()
        data["authorization"] = {
            "state": "granted",
            "side_effects": ["network-read", "local-write", "local-execution"],
            "scope": ["Execute the registered action."],
            "evidence_ids": ["ev-plan"],
            "decision_ref": record_ref(
                "decision-record",
                "decision-execution-authorization",
                "a" * 64,
                "execution-authorization",
            ),
        }
        data["action_state"] = "ready_for_authorized_execution"
        self.assertIn("ANSWER_AUTHORIZATION_DECISION_EVIDENCE_MISMATCH", finding_codes(data))

    def test_exact_human_authorization_is_internally_consistent_but_external_trust(self) -> None:
        data = valid_qe_envelope()
        grant_execution_authorization(data)
        self.assertEqual(finding_codes(data), set())
        self.assertTrue(validate_agent_answer.requires_bundle_verification(data))

    def test_development_route_cannot_enter_ready_complete_or_execution_states(self) -> None:
        for action_state in (
            "ready_for_deterministic_check",
            "ready_for_authorized_execution",
            "execution_in_progress",
            "handoff_ready",
            "complete",
        ):
            with self.subTest(action_state=action_state):
                data = development_gaussian_envelope()
                data["action_state"] = action_state
                self.assertIn("ANSWER_PLANNED_ACTION_STATE_INVALID", finding_codes(data))

    def test_authorization_side_effect_set_must_match_selected_route(self) -> None:
        data = valid_qe_envelope()
        data["authorization"]["side_effects"] = ["local-write", "local-execution"]  # type: ignore[index]
        self.assertIn("ANSWER_SIDE_EFFECT_MISMATCH", finding_codes(data))

    def test_authorization_gated_action_cannot_execute_without_grant(self) -> None:
        routes = copy.deepcopy(ROUTES)
        route = routes["routes"]["qe-rigorous-calculations"]
        route["side_effects"] = ["network-read", "local-write", "local-execution", "scheduler-submit"]
        action = route["actions"]["qe.audit-input"]
        action["side_effects"] = ["local-write", "local-execution", "scheduler-submit"]
        action["requires_authorization"] = True
        data = valid_qe_envelope()
        data["authorization"]["side_effects"] = route["side_effects"]  # type: ignore[index]
        codes = {
            item["code"]
            for item in validate_agent_answer.validation_findings(
                data,
                schema=SCHEMA,
                routes=routes,
                skills=ISOLATED_SKILLS,
                interfaces=ISOLATED_INTERFACES,
                software=SOFTWARE,
                environments=ENVIRONMENTS,
                source_root=ISOLATED_ROOT,
            )
        }
        self.assertIn("ANSWER_UNAUTHORIZED_SIDE_EFFECT", codes)

    def test_human_review_state_uses_common_snake_case_vocabulary(self) -> None:
        data = valid_qe_envelope()
        data["scientific_acceptance"] = "requires_human_review"
        self.assertIn("ANSWER_EXPERT_REVIEW_PREMATURE", finding_codes(data))

    def test_ambiguous_route_cannot_emit_fact_or_run_tool(self) -> None:
        data = valid_qe_envelope()
        data["route"] = {
            "state": "ambiguous",
            "skill": None,
            "lifecycle": "unknown",
            "software": None,
            "task": None,
        }
        self.assertIn("ANSWER_UNROUTED_POSITIVE_CLAIM", finding_codes(data))

    def test_cached_only_route_must_disclose_and_limit_claim(self) -> None:
        data = valid_qe_envelope()
        data["request"]["mode"] = "explain"  # type: ignore[index]
        data["claim_ceiling"] = "input_gates_only"
        data["tool_runs"][0].update(  # type: ignore[index]
            {
                "action_id": "qe.reference",
                "tool": "qe_guard.py reference --offline",
                "status": "cached_only",
                "exit_code": 3,
            }
        )
        data["limitations"] = []
        codes = finding_codes(data)
        self.assertIn("ANSWER_CACHED_ONLY_CLAIM_EXCEEDED", codes)
        self.assertIn("ANSWER_CACHED_ONLY_UNDISCLOSED", codes)

    def test_duplicate_ids_are_rejected(self) -> None:
        data = valid_qe_envelope()
        data["evidence"]["items"].append(copy.deepcopy(data["evidence"]["items"][0]))  # type: ignore[index]
        self.assertIn("ANSWER_DUPLICATE_ID", finding_codes(data))


class ValidatorCliTests(unittest.TestCase):
    def run_cli(self, data: dict[str, object]) -> subprocess.CompletedProcess[str]:
        return self.run_cli_bytes(json.dumps(data).encode("utf-8"))

    def run_cli_bytes(self, raw: bytes) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "answer.json"
            path.write_bytes(raw)
            return subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "validate_agent_answer.py"),
                    str(path),
                    "--routes",
                    str(ISOLATED_REGISTRY_PATHS["operation-routes"]),
                    "--skill-registry",
                    str(ISOLATED_REGISTRY_PATHS["skill-registry"]),
                    "--interface-registry",
                    str(ISOLATED_REGISTRY_PATHS["interface-registry"]),
                    "--software-registry",
                    str(ISOLATED_REGISTRY_PATHS["software-registry"]),
                    "--environment-profiles",
                    str(ISOLATED_REGISTRY_PATHS["environment-profiles"]),
                    "--root",
                    str(ISOLATED_ROOT),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

    def test_cli_strict_json_rejects_duplicate_bom_nonfinite_and_nonobject_inputs(self) -> None:
        cases = {
            "duplicate-top": b'{"schema_version":"1.0","schema_version":"1.0"}',
            "duplicate-nested": b'{"outer":{"key":1,"key":2}}',
            "bom": b'\xef\xbb\xbf{"schema_version":"1.0"}',
            "nan": b'{"value":NaN}',
            "infinity": b'{"value":Infinity}',
            "negative-infinity": b'{"value":-Infinity}',
            "array-root": b'[]',
            "null-root": b'null',
            "string-root": b'"answer"',
        }
        for label, raw in cases.items():
            with self.subTest(case=label):
                result = self.run_cli_bytes(raw)
                self.assertEqual(result.returncode, validate_agent_answer.EXIT_INVALID)
                report = json.loads(result.stdout)
                self.assertEqual(report["decision"], "blocked")
                self.assertEqual(report["finding_codes"], ["ANSWER_JSON_INVALID"])
                self.assertNotIn("Traceback", result.stderr)

    def test_cli_positive_answer_requires_bundle_verification_with_exit_three(self) -> None:
        result = self.run_cli(valid_qe_envelope())
        self.assertEqual(
            result.returncode,
            validate_agent_answer.EXIT_BUNDLE_VERIFICATION_REQUIRED,
            result.stderr,
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["decision"], "needs_bundle_verification")
        self.assertEqual(report["assurance"], "internally-consistent")
        self.assertEqual(report["bundle_validation"], "required")
        self.assertEqual(
            report["unresolved_semantic_obligations"],
            list(validate_agent_answer.EXTERNAL_SEMANTIC_OBLIGATIONS),
        )
        self.assertEqual(
            report["finding_codes"],
            [validate_agent_answer.BUNDLE_VERIFICATION_REQUIRED_CODE],
        )

    def test_cli_no_positive_development_block_can_exit_zero(self) -> None:
        result = self.run_cli(development_gaussian_envelope())
        self.assertEqual(
            result.returncode,
            validate_agent_answer.EXIT_INTERNAL_NO_POSITIVE_CLAIM,
            result.stderr,
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["decision"], "pass")
        self.assertEqual(report["assurance"], "internally-consistent")
        self.assertEqual(report["bundle_validation"], "not_required")
        self.assertEqual(report["unresolved_semantic_obligations"], [])
        self.assertEqual(report["finding_codes"], [])

    def test_cli_human_execution_authorization_requires_bundle_verification(self) -> None:
        data = no_positive_active_qe_envelope()
        grant_execution_authorization(data)
        result = self.run_cli(data)
        self.assertEqual(result.returncode, validate_agent_answer.EXIT_BUNDLE_VERIFICATION_REQUIRED)
        report = json.loads(result.stdout)
        self.assertEqual(report["decision"], "needs_bundle_verification")
        self.assertEqual(report["assurance"], "internally-consistent")

    def test_cli_ready_handoff_requires_bundle_verification_without_other_positive_claim(self) -> None:
        data = no_positive_active_qe_envelope()
        data["evidence"]["missing"] = []  # type: ignore[index]
        data["gates"] = []
        data["blocked_claims"] = []
        data["smallest_next_action"] = None
        manifest_ref = add_handoff_manifest_evidence(data, "run-manifest@1.0")
        data["request"]["mode"] = "handoff"  # type: ignore[index]
        data["action_state"] = "handoff_ready"
        data["handoffs"] = [
            {
                "producer_skill": "qe-rigorous-calculations",
                "consumer_skill": "dft-postprocess",
                "contract": "run-manifest@1.0",
                "manifest_ref": manifest_ref,
                "status": "ready",
                "source_evidence_ids": ["ev-manifest"],
                "claim_ceiling": "no_positive_claim",
                "limitations": ["Raw manifest bytes still require external bundle validation."],
            }
        ]
        result = self.run_cli(data)
        self.assertEqual(result.returncode, validate_agent_answer.EXIT_BUNDLE_VERIFICATION_REQUIRED)
        report = json.loads(result.stdout)
        self.assertEqual(report["decision"], "needs_bundle_verification")

    def test_present_trust_bearing_record_ref_requires_bundle_even_without_positive_fact(self) -> None:
        data = development_gaussian_envelope()
        data["evidence"]["items"].append(  # type: ignore[index]
            {
                "id": "ev-official",
                "role": "official-source-snapshot",
                "status": "present",
                "sha256": "f" * 64,
                "record_ref": record_ref(
                    "official-source-record",
                    "gaussian-official-source",
                    "f" * 64,
                    "official-source",
                ),
                "source_label": "unverified-official-source-record.json",
                "limitations": ["Content bytes have not been resolved by an external bundle validator."],
            }
        )
        result = self.run_cli(data)
        self.assertEqual(result.returncode, 3, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["decision"], "needs_bundle_verification")
        self.assertEqual(report["bundle_validation"], "required")

    def test_cli_exit_two_and_stable_code_for_failed_tool_claim(self) -> None:
        data = valid_qe_envelope()
        data["tool_runs"][0]["status"] = "failed"  # type: ignore[index]
        data["tool_runs"][0]["exit_code"] = 2  # type: ignore[index]
        result = self.run_cli(data)
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertEqual(report["decision"], "blocked")
        self.assertEqual(report["assurance"], "not-established")
        self.assertEqual(report["bundle_validation"], "not_performed")
        self.assertIn("ANSWER_TOOL_FAILURE_POSITIVE_CLAIM", report["finding_codes"])

    def test_cli_never_calls_accepted_envelope_evidence_authenticated_without_bundle(self) -> None:
        result = self.run_cli(accepted_qe_envelope())
        self.assertEqual(result.returncode, 3, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["decision"], "needs_bundle_verification")
        self.assertEqual(report["assurance"], "internally-consistent")
        self.assertEqual(report["bundle_validation"], "required")
        self.assertNotIn("evidence-authenticated", json.dumps(report))

    def test_forged_complete_record_refs_never_receive_exit_zero(self) -> None:
        cases = {
            "tool": valid_qe_envelope(),
            "official": documented_qe_envelope(),
            "human-decision": accepted_qe_envelope(),
        }
        for label, data in cases.items():
            with self.subTest(record_type=label):
                result = self.run_cli(data)
                self.assertEqual(result.returncode, 3, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["decision"], "needs_bundle_verification")
                self.assertEqual(report["bundle_validation"], "required")
                self.assertEqual(report["assurance"], "internally-consistent")
                self.assertNotIn("authenticated", json.dumps(report).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
