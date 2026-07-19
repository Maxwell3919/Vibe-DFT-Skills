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
import interface_registry  # noqa: E402
import bundle_semantics  # noqa: E402
import validate_contract  # noqa: E402


HASH = "0" * 64
NOW = "2026-07-18T12:00:00Z"
CHECK_IDS = [
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
]
ACTIVE_SKILLS = [
    "cif-structure-analysis",
    "qe-rigorous-calculations",
    "vasp-rigorous-calculations",
    "cp2k-rigorous-calculations",
    "siesta-rigorous-calculations",
    "dft-postprocess",
    "dft-campaign-efficiency",
]


def maturity_evidence(
    axis: str,
    level: str,
    *,
    provider_version: str | None = "0.3.14",
    evidence_id: str | None = None,
) -> dict:
    kinds = {
        "invocation": {
            "design-only": "design-record",
            "synthetic-validated": "invocation-synthetic-test",
            "format-fixture-validated": "invocation-format-fixture-test",
            "real-artifact-validated": "invocation-real-artifact-test",
            "tool-integration-validated": "invocation-tool-integration-test",
        },
        "parser": {
            "design-only": "design-record",
            "synthetic-validated": "parser-synthetic-test",
            "format-fixture-validated": "parser-format-fixture-test",
            "real-artifact-validated": "parser-real-artifact-test",
            "tool-integration-validated": "parser-tool-integration-test",
        },
        "scientific_validation": {
            "design-only": "design-record",
            "synthetic-validated": "scientific-synthetic-validation",
            "format-fixture-validated": "scientific-format-fixture-validation",
            "real-artifact-validated": "scientific-real-artifact-validation",
            "tool-integration-validated": "task-specific-scientific-validation",
        },
    }
    selected_id = evidence_id or f"{axis}-{level}-001"
    return {
        "evidence_id": selected_id,
        "axis": axis,
        "maturity_level": level,
        "kind": kinds[axis][level],
        "provider_version": provider_version,
        "source": "skill-local",
        "path": f"skills/ml-potential-workflows/validation/{selected_id}.json",
        "external_record_ref": None,
        "sha256": HASH,
    }


def supplemental_evidence(
    kind: str,
    evidence_id: str,
    *,
    axis: str = "invocation",
    level: str = "real-artifact-validated",
    provider_version: str | None = "0.3.14",
) -> dict:
    value = maturity_evidence(
        axis,
        level,
        provider_version=provider_version,
        evidence_id=evidence_id,
    )
    value["kind"] = kind
    return value


def task_maturity_catalog() -> dict:
    return {
        "schema_version": "1.0",
        "contract_name": "task-maturity",
        "catalog_id": "catalog-ml-example-001",
        "skill_id": "ml-potential-workflows",
        "aggregate": True,
        "routes": [
            {
                "route_id": "mace/inference/core",
                "provider_id": "mace",
                "provider_lifecycle": "active",
                "task_id": "inference/core",
                "parent_route": None,
                "provider_version": "0.3.14",
                "implementation": "implemented",
                "invocation_maturity": "real-artifact-validated",
                "parser_maturity": "real-artifact-validated",
                "scientific_validation_maturity": "real-artifact-validated",
                "overall_maturity": {
                    "declared": "real-artifact-validated",
                    "computed": "real-artifact-validated",
                },
                "claim_ceiling": "technical_run_gates_only",
                "advertised": True,
                "execution_capability": False,
                "unknown_version_policy": "block",
                "evidence": [
                    maturity_evidence("invocation", "real-artifact-validated"),
                    maturity_evidence("parser", "real-artifact-validated"),
                    maturity_evidence("scientific_validation", "real-artifact-validated"),
                    supplemental_evidence(
                        "official-source-evidence", "official-source-mace-001"
                    ),
                ],
                "limitations": ["Scientific acceptance remains an expert decision."],
            },
            {
                "route_id": "nequip/inference/core",
                "provider_id": "nequip",
                "provider_lifecycle": "planned",
                "task_id": "inference/core",
                "parent_route": None,
                "provider_version": None,
                "implementation": "unsupported",
                "invocation_maturity": "design-only",
                "parser_maturity": "design-only",
                "scientific_validation_maturity": "design-only",
                "overall_maturity": {
                    "declared": "design-only",
                    "computed": "design-only",
                },
                "claim_ceiling": "no_positive_claim",
                "advertised": False,
                "execution_capability": False,
                "unknown_version_policy": "block",
                "evidence": [],
                "limitations": ["The provider remains planned and is not routable."],
            },
        ],
        "provenance": {
            "producer": "test-wave0-governance",
            "producer_version": "1.0",
            "generated_utc": NOW,
        },
    }


def checklist() -> dict:
    checks = []
    for index, check_id in enumerate(CHECK_IDS):
        checks.append(
            {
                "check_id": check_id,
                "status": "pass",
                "evidence": [
                    {
                        "evidence_id": f"check-evidence-{index:02d}",
                        "kind": "test-report",
                        "path": (
                            "skills/gaussian-rigorous-calculations/validation/"
                            f"check-{index:02d}.json"
                        ),
                        "sha256": HASH,
                    }
                ],
                "reviewer": {
                    "reviewer_id": f"reviewer-{index:02d}",
                    "role": "independent-technical-reviewer",
                    "independent_of_implementation": True,
                },
                "validated_utc": NOW,
                "not_applicable_reason": None,
                "limitations": [],
            }
        )
    return {
        "schema_version": "1.0",
        "contract_name": "activation-checklist",
        "checklist_id": "activation-example-001",
        "subject": {
            "skill_id": "gaussian-rigorous-calculations",
            "software_ids": ["gaussian"],
            "candidate_commit": "a" * 40,
        },
        "profile_ids": ["calculation-engine"],
        "checks": checks,
        "summary": {"decision": "eligible", "blocker_check_ids": [], "limitations": []},
        "provenance": {
            "producer": "test-wave0-governance",
            "producer_version": "1.0",
            "generated_utc": NOW,
        },
    }


def file_ref(path: str) -> dict:
    return {"path": path, "sha256": HASH}


def record_ref(record_id: str = "external-parent-001") -> dict:
    return {
        "contract_name": "calculation-record-envelope",
        "schema_version": "1.0",
        "record_id": record_id,
        "sha256": HASH,
        "role": "parent-calculation",
    }


def report_ref(report_id: str) -> dict:
    return {
        "report_id": report_id,
        "path": f"skills/gaussian-rigorous-calculations/validation/{report_id}.json",
        "sha256": HASH,
        "status": "pass",
        "validated_utc": NOW,
    }


def promotion_delta() -> dict:
    promoted = "gaussian-rigorous-calculations"
    return {
        "schema_version": "1.0",
        "contract_name": "promotion-delta",
        "promotion_id": "promotion-gaussian-001",
        "skill_id": promoted,
        "skill_kind": "calculation",
        "software_backed": True,
        "base_commit": "a" * 40,
        "candidate_commit": "b" * 40,
        "base_registry_sha256": HASH,
        "lifecycle_transition": {"from": "development", "to": "active"},
        "path_transition": {
            "from": f"skills/{promoted}",
            "to": f"skills/{promoted}",
            "source_tree_sha256": HASH,
        },
        "domain_owned_files_changed": [
            f"skills/{promoted}/SKILL.md",
            f"skills/{promoted}/validation/task-maturity.json",
        ],
        "shared_files_changed": [
            "registry/skill-registry.yaml",
            "registry/software-registry.yaml",
            "registry/interface-registry.yaml",
            "registry/operation-routes.yaml",
            "registry/environment-profiles.yaml",
        ],
        "software_entries_moved": [
            {"software_id": "gaussian", "from": "planned", "to": "active"}
        ],
        "interface_changes": [
            {
                "interface_id": "molecular-structure-manifest@1.0",
                "action": "activate",
                "schema_ref": file_ref("contracts/molecular-structure-manifest.schema.json"),
            },
            {
                "interface_id": "quantum-chemistry-run-manifest@1.0",
                "action": "activate",
                "schema_ref": file_ref("contracts/quantum-chemistry-run-manifest.schema.json"),
            },
        ],
        "contracts_changed": [
            {
                "path": "contracts/molecular-structure-manifest.schema.json",
                "sha256": HASH,
                "change": "add",
            },
            {
                "path": "contracts/quantum-chemistry-run-manifest.schema.json",
                "sha256": HASH,
                "change": "add",
            }
        ],
        "observable_route_decisions": [
            {
                "observable_id": "bands",
                "provider_id": "gaussian",
                "decision": "not-applicable",
                "evidence": file_ref(
                    "skills/gaussian-rigorous-calculations/validation/observable-decisions.json"
                ),
            }
        ],
        "task_maturity_catalog": file_ref(
            f"skills/{promoted}/validation/task-maturity.json"
        ),
        "activation_checklist": file_ref(
            "skills/gaussian-rigorous-calculations/validation/activation-checklist.json"
        ),
        "installer_set": {
            "before": ACTIVE_SKILLS,
            "after": [*ACTIVE_SKILLS, promoted],
            "added": [promoted],
            "removed": [],
        },
        "reports": {
            "privacy_license": report_ref("privacy-license-gaussian-001"),
            "forward_tests": [report_ref("forward-test-gaussian-001")],
        },
        "known_limitations": ["Only the explicitly mature task routes are advertised."],
        "blockers": [],
        "decision": "eligible",
        "provenance": {
            "producer": "test-wave0-governance",
            "producer_version": "1.0",
            "generated_utc": NOW,
        },
    }


class InterfaceRegistryTests(unittest.TestCase):
    def test_registry_hashes_and_schema_identity_are_fresh(self) -> None:
        registry = interface_registry.load_registry()
        self.assertEqual(interface_registry.validation_errors(registry, ROOT), [])
        active = interface_registry.active_interface_ids(root=ROOT)
        self.assertEqual(
            set(active),
            {
                "structure-manifest@1.0",
                "run-manifest@1.0",
                "postprocess-plan@1.0",
                "tool-execution@1.0",
                "normalized-dataset@1.0",
                "artifact-manifest@1.0",
                "campaign-record@1.0",
                "recommendation-record@1.0",
                "structure-snapshot@1.0",
                "molecular-structure-manifest@1.0",
                "structure-transformation-manifest@1.0",
                "structure-export-manifest@1.0",
                "atomistic-trajectory-manifest@1.0",
                "calculation-record-envelope@1.0",
                "workflow-plan@1.0",
                "workflow-event@1.0",
                "decision-record@1.0",
                "execution-request@1.0",
                "execution-record@1.0",
                "execution-lease@1.0",
                "claim-evidence-map@1.0",
                "agent-action-envelope@1.0",
                "official-source-record@1.0",
                "evidence-record@1.0",
                "bundle-manifest@1.0",
                "bundle-validation-report@1.0",
            },
        )

    def test_all_reserved_interfaces_remain_fail_closed(self) -> None:
        planned = set(interface_registry.planned_interface_ids(root=ROOT))
        expected = {
            "environment-profile@1.0",
            "ovito-pipeline-spec@1.0",
            "quantum-chemistry-run-manifest@1.0",
            "simulation-system-manifest@1.0",
            "md-run-manifest@1.0",
            "ml-dataset-manifest@1.0",
            "ml-training-run@1.0",
            "electronic-wavefunction-source@1.0",
            "phonon-workflow-manifest@1.0",
            "microkinetic-model-manifest@1.0",
            "review-evidence-map@1.0",
            "scientific-report@1.0",
            "activation-checklist@1.0",
            "promotion-delta@1.0",
            "task-maturity@1.0",
            "validation-report@1.0",
        }
        self.assertTrue(expected.issubset(planned))
        registry = interface_registry.load_registry()
        for name in planned:
            self.assertIsNone(registry["interfaces"][name]["schema_path"])
            self.assertIsNone(registry["interfaces"][name]["schema_sha256"])

    def test_governance_interfaces_have_evidence_backed_lifecycle_and_never_route(self) -> None:
        registry = interface_registry.load_registry()
        active_governance = {
            "bundle-manifest@1.0": "content-addressed-record",
            "bundle-validation-report@1.0": "content-addressed-record",
            "agent-action-envelope@1.0": "projection",
        }
        for interface_id, document_kind in active_governance.items():
            with self.subTest(interface_id=interface_id):
                item = registry["interfaces"][interface_id]
                self.assertEqual(item["lifecycle"], "active")
                self.assertIsInstance(item["schema_path"], str)
                self.assertIsInstance(item["schema_sha256"], str)
                self.assertEqual(item["classification"]["document_kind"], document_kind)
                self.assertEqual(item["classification"]["routing_scope"], "governance-only")

        planned_governance = {
            "activation-checklist@1.0": "content-addressed-record",
            "promotion-delta@1.0": "content-addressed-record",
            "task-maturity@1.0": "content-addressed-record",
            "validation-report@1.0": "projection",
        }
        for interface_id, document_kind in planned_governance.items():
            with self.subTest(interface_id=interface_id):
                item = registry["interfaces"][interface_id]
                self.assertEqual(item["lifecycle"], "planned")
                self.assertIsNone(item["schema_path"])
                self.assertIsNone(item["schema_sha256"])
                self.assertEqual(item["classification"]["document_kind"], document_kind)
                self.assertEqual(item["classification"]["routing_scope"], "governance-only")
                with self.assertRaisesRegex(ValueError, "not active"):
                    interface_registry.get_interface(interface_id, root=ROOT)

        invalid = copy.deepcopy(registry)
        invalid["interfaces"]["validation-report@1.0"]["classification"][
            "document_kind"
        ] = "content-record"
        self.assertTrue(
            any(
                "classification/document_kind" in finding
                for finding in interface_registry.validation_errors(invalid, ROOT)
            )
        )

    def test_every_active_semantic_obligation_has_one_production_owner(self) -> None:
        registry = interface_registry.load_registry()
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        self.assertEqual(bundle_semantics.builtin_ownership_errors(), [])
        for interface_id, specification in registry["interfaces"].items():
            if specification["lifecycle"] != "active":
                continue
            contract = catalog.resolve(interface_id.split("@", 1)[0])
            obligations = contract.schema.get("x-vibe-semantic-obligations")
            if obligations is None:
                self.assertIn(contract.name, {"bundle-manifest", "bundle-validation-report"})
                self.assertTrue((ROOT / "tools" / "validate_bundle.py").is_file())
            elif contract.name == "agent-action-envelope":
                self.assertTrue((ROOT / "tools" / "validate_agent_answer.py").is_file())
            else:
                self.assertIsNotNone(
                    bundle_semantics.builtin_evaluator(contract.name),
                    f"active semantic contract has no exact-one owner: {contract.name}",
                )

    def test_hash_drift_is_rejected(self) -> None:
        registry = copy.deepcopy(interface_registry.load_registry())
        registry["interfaces"]["run-manifest@1.0"]["schema_sha256"] = "f" * 64
        failures = interface_registry.validation_errors(registry, ROOT)
        self.assertTrue(any("declared" in item and "actual" in item for item in failures))

    def test_planned_interface_cannot_publish_a_schema(self) -> None:
        registry = copy.deepcopy(interface_registry.load_registry())
        item = registry["interfaces"]["ovito-pipeline-spec@1.0"]
        item["schema_path"] = "contracts/run-manifest.schema.json"
        item["schema_sha256"] = HASH
        failures = interface_registry.validation_errors(registry, ROOT)
        self.assertTrue(any("planned interfaces require null" in item for item in failures))

    def test_unknown_or_inactive_interface_cannot_be_resolved_as_active(self) -> None:
        with self.assertRaisesRegex(KeyError, "unknown interface"):
            interface_registry.get_interface("made-up@1.0", root=ROOT)
        with self.assertRaisesRegex(ValueError, "not active"):
            interface_registry.get_interface("ovito-pipeline-spec@1.0", root=ROOT)
        metadata = interface_registry.get_interface(
            "ovito-pipeline-spec@1.0", root=ROOT, require_active=False
        )
        self.assertEqual(metadata["lifecycle"], "planned")

    def test_planned_cli_query_requires_explicit_metadata_mode(self) -> None:
        command = [
            sys.executable,
            str(ROOT / "tools" / "interface_registry.py"),
            "--interface",
            "ovito-pipeline-spec@1.0",
        ]
        blocked = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(blocked.returncode, 3)
        self.assertIn("status=planned-not-active", blocked.stderr)
        metadata = subprocess.run(
            [*command, "--allow-planned-metadata"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(metadata.returncode, 0, metadata.stderr)
        self.assertIn("status=planned-metadata-only", metadata.stdout)


class GovernanceSchemaTests(unittest.TestCase):
    def test_governance_json_cli_rejects_ambiguous_or_nonobject_input_without_path_leak(self) -> None:
        cases = {
            "duplicate": b'{"schema_version":"1.0","schema_version":"1.0"}',
            "bom": b"\xef\xbb\xbf{}",
            "nan": b'{"value":NaN}',
            "nonobject": b"[]",
        }
        for label, raw in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / f"private-{label}.json"
                path.write_bytes(raw)
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "tools" / "interface_registry.py"),
                        "--validate-governance",
                        "task-maturity",
                        "--json-file",
                        str(path),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(str(path), result.stderr)

    def test_governance_schema_loader_rejects_duplicate_keys_bom_nan_and_nonobject(self) -> None:
        cases = {
            "duplicate": b'{"$schema":"x","$schema":"y"}',
            "bom": b"\xef\xbb\xbf{}",
            "nan": b'{"value":NaN}',
            "nonobject": b"[]",
        }
        for label, raw in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                contracts = root / "contracts"
                contracts.mkdir()
                contracts.joinpath("task-maturity.schema.json").write_bytes(raw)
                with self.assertRaises(ValueError):
                    interface_registry.load_governance_schema("task-maturity", root)

    def test_governance_schemas_are_valid_draft_2020_12(self) -> None:
        for kind in interface_registry.GOVERNANCE_SCHEMAS:
            schema = interface_registry.load_governance_schema(kind, ROOT)
            Draft202012Validator.check_schema(schema)
            self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")
            self.assertIn("contract_name", schema["required"])
            self.assertEqual(schema["properties"]["contract_name"]["const"], kind)
            self.assertEqual(schema["$id"], f"urn:vibe-dft-skills:contract:{kind}:1.0")
            self.assertEqual(schema["x-vibe-document-kind"], "content-addressed-record")
            self.assertEqual(
                schema["x-vibe-record-id-field"],
                {
                    "activation-checklist": "checklist_id",
                    "promotion-delta": "promotion_id",
                    "task-maturity": "catalog_id",
                }[kind],
            )
            obligations = schema["x-vibe-semantic-obligations"]
            self.assertEqual(obligations["validator"], "commit-aware-promotion-validator")
            self.assertTrue(obligations["required_checks"])

        promotion_schema = interface_registry.load_governance_schema(
            "promotion-delta", ROOT
        )
        self.assertIn(
            "scientific-workflow",
            promotion_schema["properties"]["skill_kind"]["enum"],
        )

    def test_maturity_axes_and_claim_enum_match_the_frozen_common_vocabulary(self) -> None:
        schema = interface_registry.load_governance_schema("task-maturity", ROOT)
        common = json.loads(
            (ROOT / "contracts" / "common-definitions-1.0.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            schema["$defs"]["implementation"]["enum"],
            ["unsupported", "contract-only", "implemented"],
        )
        self.assertEqual(
            schema["$defs"]["maturityLevel"]["enum"],
            [
                "design-only",
                "synthetic-validated",
                "format-fixture-validated",
                "real-artifact-validated",
                "tool-integration-validated",
            ],
        )
        self.assertEqual(
            schema["$defs"]["maturityLevel"]["enum"],
            common["$defs"]["maturity"]["properties"]["validation"]["enum"],
        )
        route_fields = set(schema["$defs"]["route"]["required"])
        self.assertTrue(
            {
                "invocation_maturity",
                "parser_maturity",
                "scientific_validation_maturity",
                "overall_maturity",
                "implementation",
                "claim_ceiling",
            }.issubset(route_fields)
        )
        self.assertNotIn("validation", route_fields)
        self.assertEqual(
            schema["$defs"]["claimCeiling"]["enum"],
            [
                "no_positive_claim",
                "documented_behavior_only",
                "input_gates_only",
                "technical_run_gates_only",
                "numerical_candidate_only",
                "eligible_for_expert_review",
            ],
        )
        self.assertEqual(
            schema["$defs"]["claimCeiling"]["enum"],
            common["$defs"]["claimCeiling"]["enum"],
        )

    def test_aggregate_skill_can_activate_one_provider_only(self) -> None:
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "task-maturity", task_maturity_catalog(), ROOT
            ),
            [],
        )
        value = task_maturity_catalog()
        value["routes"][0]["advertised"] = False
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            ),
            [],
        )

    def test_illegal_maturity_combinations_are_rejected(self) -> None:
        mutations = []

        value = task_maturity_catalog()
        value["routes"][1]["advertised"] = True
        mutations.append(value)

        value = task_maturity_catalog()
        value["routes"][1]["claim_ceiling"] = "documented_behavior_only"
        mutations.append(value)

        value = task_maturity_catalog()
        route = value["routes"][1]
        route["implementation"] = "contract-only"
        route["provider_version"] = "planned-format"
        route["invocation_maturity"] = "format-fixture-validated"
        route["parser_maturity"] = "format-fixture-validated"
        route["scientific_validation_maturity"] = "format-fixture-validated"
        route["overall_maturity"] = {
            "declared": "format-fixture-validated",
            "computed": "format-fixture-validated",
        }
        route["evidence"] = [
            maturity_evidence(
                axis,
                "format-fixture-validated",
                provider_version="planned-format",
            )
            for axis in ("invocation", "parser", "scientific_validation")
        ]
        route["advertised"] = True
        mutations.append(value)

        value = task_maturity_catalog()
        value["routes"][0]["execution_capability"] = True
        mutations.append(value)

        value = task_maturity_catalog()
        value["routes"][0]["overall_maturity"]["declared"] = "tool-integration-validated"
        mutations.append(value)

        value = task_maturity_catalog()
        value["routes"][0]["overall_maturity"]["computed"] = "synthetic-validated"
        mutations.append(value)

        for index, invalid in enumerate(mutations):
            with self.subTest(index=index):
                self.assertTrue(
                    interface_registry.governance_validation_errors(
                        "task-maturity", invalid, ROOT
                    )
                )

    def test_each_non_design_axis_requires_exact_hashed_evidence_even_unadvertised(self) -> None:
        for axis in ("invocation", "parser", "scientific_validation"):
            value = task_maturity_catalog()
            value["routes"][0]["advertised"] = False
            value["routes"][0]["evidence"] = [
                item for item in value["routes"][0]["evidence"] if item["axis"] != axis
            ]
            with self.subTest(axis=axis):
                errors = interface_registry.governance_validation_errors(
                    "task-maturity", value, ROOT
                )
                self.assertTrue(any("missing hashed evidence" in item for item in errors))

        value = task_maturity_catalog()
        value["routes"][0]["evidence"][0]["sha256"] = "not-a-hash"
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            )
        )

        value = task_maturity_catalog()
        value["routes"][0]["evidence"][0]["kind"] = "parser-real-artifact-test"
        self.assertTrue(
            any(
                "missing hashed evidence" in item
                for item in interface_registry.governance_validation_errors(
                    "task-maturity", value, ROOT
                )
            )
        )

        value = task_maturity_catalog()
        value["routes"][0]["advertised"] = False
        value["routes"][0]["claim_ceiling"] = "eligible_for_expert_review"
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            ),
            "advertised=false must not bypass the overall-maturity claim ceiling",
        )

    def test_task_evidence_is_skill_scoped_or_an_explicit_external_record(self) -> None:
        for bad_path in (
            ".git/config",
            "docs/mace-validation.json",
            "skills/another-skill/validation/mace.json",
        ):
            value = task_maturity_catalog()
            value["routes"][0]["evidence"][0]["path"] = bad_path
            with self.subTest(path=bad_path):
                self.assertTrue(
                    any(
                        "local evidence must be below" in item
                        for item in interface_registry.governance_validation_errors(
                            "task-maturity", value, ROOT
                        )
                    )
                )

        value = task_maturity_catalog()
        external = value["routes"][0]["evidence"][0]
        external["source"] = "external-record"
        external["path"] = None
        external["external_record_ref"] = record_ref("external-evidence-001")
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            ),
            [],
        )

        external["external_record_ref"]["sha256"] = "1" * 64
        self.assertTrue(
            any(
                "must equal the evidence sha256" in item
                for item in interface_registry.governance_validation_errors(
                    "task-maturity", value, ROOT
                )
            )
        )

    def test_format_real_and_tool_maturity_bind_exact_provider_version(self) -> None:
        value = task_maturity_catalog()
        value["routes"][0]["provider_version"] = None
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            )
        )

        for bad_version in (
            "unknown",
            "latest",
            "dev",
            "x",
            "X",
            "1.x",
            "^1.2",
            "~1.2",
            "1.0,2.0",
            "1.0|2.0",
            "1.0 - 2.0",
            "1.0 2.0",
            "1.0.dev1",
        ):
            value = task_maturity_catalog()
            value["routes"][0]["provider_version"] = bad_version
            for item in value["routes"][0]["evidence"]:
                item["provider_version"] = bad_version
            with self.subTest(version=bad_version):
                self.assertTrue(
                    any(
                        "expected an exact version" in item
                        for item in interface_registry.governance_validation_errors(
                            "task-maturity", value, ROOT
                        )
                    )
                )

        value = task_maturity_catalog()
        exact_label = "MACE 0.3.14 build cuda12"
        value["routes"][0]["provider_version"] = exact_label
        for item in value["routes"][0]["evidence"]:
            item["provider_version"] = exact_label
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            ),
            [],
        )

        value = task_maturity_catalog()
        value["routes"][0]["evidence"][1]["provider_version"] = "0.3.13"
        errors = interface_registry.governance_validation_errors(
            "task-maturity", value, ROOT
        )
        self.assertTrue(any("exact route provider_version" in item for item in errors))

        value = task_maturity_catalog()
        route = value["routes"][0]
        route["invocation_maturity"] = "tool-integration-validated"
        route["execution_capability"] = True
        route["evidence"][0] = maturity_evidence(
            "invocation", "tool-integration-validated"
        )
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            ),
            [],
        )
        route["evidence"] = [
            item for item in route["evidence"] if item["axis"] != "invocation"
        ]
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            )
        )

    def test_executable_route_does_not_promote_scientific_maturity(self) -> None:
        value = task_maturity_catalog()
        route = value["routes"][0]
        route["invocation_maturity"] = "tool-integration-validated"
        route["parser_maturity"] = "real-artifact-validated"
        route["scientific_validation_maturity"] = "design-only"
        route["overall_maturity"] = {
            "declared": "design-only",
            "computed": "design-only",
        }
        route["claim_ceiling"] = "no_positive_claim"
        route["advertised"] = False
        route["execution_capability"] = True
        route["evidence"] = [
            maturity_evidence("invocation", "tool-integration-validated"),
            maturity_evidence("parser", "real-artifact-validated"),
        ]
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            ),
            [],
        )

    def test_claim_evidence_cannot_be_replaced_by_smoke_tests(self) -> None:
        value = task_maturity_catalog()
        route = value["routes"][0]
        route["evidence"] = [
            item for item in route["evidence"] if item["kind"] != "official-source-evidence"
        ]
        self.assertTrue(
            any(
                "require official-source-evidence" in item
                for item in interface_registry.governance_validation_errors(
                    "task-maturity", value, ROOT
                )
            )
        )

        value = task_maturity_catalog()
        route = value["routes"][0]
        route["invocation_maturity"] = "tool-integration-validated"
        route["parser_maturity"] = "tool-integration-validated"
        route["scientific_validation_maturity"] = "tool-integration-validated"
        route["overall_maturity"] = {
            "declared": "tool-integration-validated",
            "computed": "tool-integration-validated",
        }
        route["claim_ceiling"] = "eligible_for_expert_review"
        route["execution_capability"] = True
        route["evidence"] = [
            maturity_evidence("invocation", "tool-integration-validated"),
            maturity_evidence("parser", "tool-integration-validated"),
            maturity_evidence("scientific_validation", "tool-integration-validated"),
            supplemental_evidence(
                "official-source-evidence",
                "official-source-tool-route-001",
                level="tool-integration-validated",
            ),
            supplemental_evidence(
                "expert-readiness-review",
                "expert-readiness-tool-route-001",
                axis="scientific_validation",
                level="tool-integration-validated",
            ),
        ]
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            ),
            [],
        )

        route["evidence"][2]["kind"] = "invocation-tool-integration-test"
        errors = interface_registry.governance_validation_errors(
            "task-maturity", value, ROOT
        )
        self.assertTrue(any("scientific_validation" in item for item in errors))
        self.assertTrue(any("task-specific scientific validation" in item for item in errors))

        value = task_maturity_catalog()
        route = value["routes"][0]
        route["invocation_maturity"] = "tool-integration-validated"
        route["parser_maturity"] = "tool-integration-validated"
        route["scientific_validation_maturity"] = "tool-integration-validated"
        route["overall_maturity"] = {
            "declared": "tool-integration-validated",
            "computed": "tool-integration-validated",
        }
        route["claim_ceiling"] = "eligible_for_expert_review"
        route["execution_capability"] = True
        route["evidence"] = [
            maturity_evidence("invocation", "tool-integration-validated"),
            maturity_evidence("parser", "tool-integration-validated"),
            maturity_evidence("scientific_validation", "tool-integration-validated"),
            supplemental_evidence(
                "official-source-evidence",
                "official-source-without-review-001",
                level="tool-integration-validated",
            ),
        ]
        self.assertTrue(
            any(
                "expert-readiness-review" in item
                for item in interface_registry.governance_validation_errors(
                    "task-maturity", value, ROOT
                )
            )
        )

    def test_synthetic_axis_can_be_versionless_without_claiming_provider_support(self) -> None:
        value = task_maturity_catalog()
        route = value["routes"][1]
        route["implementation"] = "contract-only"
        route["invocation_maturity"] = "synthetic-validated"
        route["evidence"] = [
            maturity_evidence(
                "invocation",
                "synthetic-validated",
                provider_version=None,
            )
        ]
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            ),
            [],
        )
        self.assertFalse(route["advertised"])
        self.assertEqual(route["claim_ceiling"], "no_positive_claim")

    def test_nonaggregate_catalog_cannot_hide_multiple_providers(self) -> None:
        value = task_maturity_catalog()
        value["aggregate"] = False
        errors = interface_registry.governance_validation_errors("task-maturity", value, ROOT)
        self.assertIn("routes: a non-aggregate catalog must use exactly one provider", errors)

    def test_task_provider_version_parent_scope_cannot_be_duplicated(self) -> None:
        value = task_maturity_catalog()
        duplicate = copy.deepcopy(value["routes"][0])
        duplicate["route_id"] = "mace/inference/duplicate"
        value["routes"].append(duplicate)
        errors = interface_registry.governance_validation_errors(
            "task-maturity", value, ROOT
        )
        self.assertIn(
            "routes: provider/task/version/parent routes must be unique",
            errors,
        )

        value = task_maturity_catalog()
        value["routes"][0]["evidence"][1]["evidence_id"] = value["routes"][0][
            "evidence"
        ][0]["evidence_id"]
        self.assertTrue(
            any(
                "evidence_id values must be unique" in item
                for item in interface_registry.governance_validation_errors(
                    "task-maturity", value, ROOT
                )
            )
        )

        value = task_maturity_catalog()
        borrowed = copy.deepcopy(value["routes"][0])
        borrowed["route_id"] = "mace/other-task/core"
        borrowed["task_id"] = "other-task/core"
        value["routes"].append(borrowed)
        errors = interface_registry.governance_validation_errors(
            "task-maturity", value, ROOT
        )
        self.assertTrue(
            any("cannot be borrowed" in item for item in errors),
            "Maturity evidence is scoped to one task/provider/version route.",
        )

    def test_parent_route_is_a_local_dag_or_hashed_external_record(self) -> None:
        value = task_maturity_catalog()
        value["routes"][0]["parent_route"] = {
            "scope": "external-record",
            "route_id": None,
            "record_ref": record_ref(),
        }
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            ),
            [],
        )

        value = task_maturity_catalog()
        value["routes"][0]["parent_route"] = {
            "scope": "catalog",
            "route_id": "missing/provider/route",
            "record_ref": None,
        }
        self.assertTrue(
            any(
                "local parent does not exist" in item
                for item in interface_registry.governance_validation_errors(
                    "task-maturity", value, ROOT
                )
            )
        )

        value = task_maturity_catalog()
        first, second = value["routes"]
        first["parent_route"] = {
            "scope": "catalog",
            "route_id": second["route_id"],
            "record_ref": None,
        }
        second["parent_route"] = {
            "scope": "catalog",
            "route_id": first["route_id"],
            "record_ref": None,
        }
        self.assertTrue(
            any(
                "parent graph contains a cycle" in item
                for item in interface_registry.governance_validation_errors(
                    "task-maturity", value, ROOT
                )
            )
        )

        value = task_maturity_catalog()
        value["routes"][0]["parent_route"] = "arbitrary-parent-label"
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "task-maturity", value, ROOT
            )
        )

    def test_complete_thirteen_check_activation_evidence_passes(self) -> None:
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "activation-checklist", checklist(), ROOT
            ),
            [],
        )

        value = checklist()
        value["checks"][0]["evidence"][0]["path"] = (
            "skills/another-skill/validation/identity-routing.json"
        )
        self.assertTrue(
            any(
                "must be located below skills/gaussian-rigorous-calculations/validation/" in item
                for item in interface_registry.governance_validation_errors(
                    "activation-checklist", value, ROOT
                )
            )
        )

    def test_empty_evidence_and_one_character_requirement_are_rejected(self) -> None:
        value = checklist()
        value["checks"][0]["evidence"] = []
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "activation-checklist", value, ROOT
            )
        )
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "activation-checklist", {"activation_requirements": ["x"]}, ROOT
            )
        )

    def test_not_applicable_check_requires_reason_and_hashed_record(self) -> None:
        valid = checklist()
        item = valid["checks"][8]
        item["status"] = "not-applicable"
        item["not_applicable_reason"] = (
            "This read-only route has no retry, recovery, cancellation, or execution state."
        )
        item["evidence"][0]["kind"] = "not-applicable-record"
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "activation-checklist", valid, ROOT
            ),
            [],
        )

        invalid = copy.deepcopy(valid)
        invalid["checks"][8]["not_applicable_reason"] = "n/a"
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "activation-checklist", invalid, ROOT
            )
        )

    def test_blocker_summary_must_exactly_match_failed_checks(self) -> None:
        value = checklist()
        value["checks"][0]["status"] = "fail"
        value["summary"] = {
            "decision": "blocked",
            "blocker_check_ids": ["identity-and-routing"],
            "limitations": [],
        }
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "activation-checklist", value, ROOT
            ),
            [],
        )
        value["summary"]["blocker_check_ids"] = ["privacy-and-license"]
        self.assertIn(
            "summary/blocker_check_ids: must exactly match fail and not-assessed checks",
            interface_registry.governance_validation_errors(
                "activation-checklist", value, ROOT
            ),
        )

    def test_single_skill_atomic_promotion_delta_passes(self) -> None:
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "promotion-delta", promotion_delta(), ROOT
            ),
            [],
        )

    def test_promotion_requires_distinct_commits_and_scoped_references(self) -> None:
        mutations = []

        value = promotion_delta()
        value["candidate_commit"] = value["base_commit"]
        mutations.append(value)

        value = promotion_delta()
        value["contracts_changed"][0]["path"] = "docs/not-a-contract.schema.json"
        mutations.append(value)

        value = promotion_delta()
        value["task_maturity_catalog"]["path"] = "validation/task-maturity.json"
        mutations.append(value)

        value = promotion_delta()
        value["activation_checklist"]["path"] = "docs/activation.json"
        mutations.append(value)

        value = promotion_delta()
        value["reports"]["privacy_license"]["path"] = "docs/privacy.json"
        mutations.append(value)

        value = promotion_delta()
        value["path_transition"]["from"] = "skills/another-skill"
        mutations.append(value)

        value = promotion_delta()
        value["domain_owned_files_changed"][0] = "skills/another-skill/SKILL.md"
        mutations.append(value)

        for index, invalid in enumerate(mutations):
            with self.subTest(index=index):
                self.assertTrue(
                    interface_registry.governance_validation_errors(
                        "promotion-delta", invalid, ROOT
                    )
                )

    def test_eligible_promotion_requires_all_shared_truth_files(self) -> None:
        for required in (
            "registry/skill-registry.yaml",
            "registry/interface-registry.yaml",
            "registry/operation-routes.yaml",
            "registry/software-registry.yaml",
            "registry/environment-profiles.yaml",
        ):
            value = promotion_delta()
            value["shared_files_changed"].remove(required)
            with self.subTest(required=required):
                self.assertTrue(
                    interface_registry.governance_validation_errors(
                        "promotion-delta", value, ROOT
                    )
                )

        value = promotion_delta()
        value["skill_kind"] = "advisory"
        value["software_backed"] = False
        errors = interface_registry.governance_validation_errors(
            "promotion-delta", value, ROOT
        )
        self.assertIn(
            "software_backed: must be true when software registry entries are promoted",
            errors,
        )

        value = promotion_delta()
        value["software_backed"] = False
        value["software_entries_moved"] = []
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "promotion-delta", value, ROOT
            ),
            "A calculation Skill cannot opt out of its software/environment truth files.",
        )

        value = promotion_delta()
        value["skill_id"] = "vaspkit-postprocess"
        value["skill_kind"] = "postprocess"
        value["software_backed"] = False
        value["software_entries_moved"] = []
        errors = interface_registry.governance_validation_errors(
            "promotion-delta", value, ROOT
        )
        self.assertIn(
            "software_backed: actual software-registry ownership requires true",
            errors,
        )
        self.assertTrue(
            any("must promote at least one software-registry entry" in item for item in errors)
        )

    def test_promotion_validation_refs_cannot_be_borrowed_from_another_skill(self) -> None:
        mutations = []

        value = promotion_delta()
        value["activation_checklist"]["path"] = "skills/another-skill/validation/activation.json"
        mutations.append(value)

        value = promotion_delta()
        value["observable_route_decisions"][0]["evidence"]["path"] = (
            "skills/another-skill/validation/observable.json"
        )
        mutations.append(value)

        value = promotion_delta()
        value["reports"]["forward_tests"][0]["path"] = (
            "skills/another-skill/validation/forward.json"
        )
        mutations.append(value)

        for index, invalid in enumerate(mutations):
            with self.subTest(index=index):
                errors = interface_registry.governance_validation_errors(
                    "promotion-delta", invalid, ROOT
                )
                self.assertTrue(any("must be located below skills/" in item for item in errors))

    def test_interface_activation_must_match_changed_contract_path_and_hash(self) -> None:
        value = promotion_delta()
        value["interface_changes"][0]["schema_ref"]["sha256"] = "1" * 64
        errors = interface_registry.governance_validation_errors(
            "promotion-delta", value, ROOT
        )
        self.assertTrue(any("must match a contracts_changed path/hash" in item for item in errors))

        value = promotion_delta()
        value["contracts_changed"] = value["contracts_changed"][1:]
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "promotion-delta", value, ROOT
            )
        )

    def test_declared_hashes_are_not_misrepresented_as_cross_file_verification(self) -> None:
        value = promotion_delta()
        replacement = "1" * 64
        value["base_registry_sha256"] = replacement
        value["task_maturity_catalog"]["sha256"] = replacement
        value["activation_checklist"]["sha256"] = replacement
        value["observable_route_decisions"][0]["evidence"]["sha256"] = replacement
        value["reports"]["privacy_license"]["sha256"] = replacement
        value["reports"]["forward_tests"][0]["sha256"] = replacement
        for contract, interface in zip(
            value["contracts_changed"], value["interface_changes"], strict=True
        ):
            contract["sha256"] = replacement
            interface["schema_ref"]["sha256"] = replacement
        self.assertEqual(
            interface_registry.governance_validation_errors(
                "promotion-delta", value, ROOT
            ),
            [],
            "Cross-file hash reads belong to the later commit-aware promotion validator.",
        )

    def test_promotion_cannot_add_two_skills_or_mismatch_installer_set(self) -> None:
        value = promotion_delta()
        value["installer_set"]["added"].append("another-skill")
        value["installer_set"]["after"].append("another-skill")
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "promotion-delta", value, ROOT
            )
        )

        value = promotion_delta()
        value["installer_set"]["added"] = ["another-skill"]
        value["installer_set"]["after"] = [*ACTIVE_SKILLS, "another-skill"]
        errors = interface_registry.governance_validation_errors(
            "promotion-delta", value, ROOT
        )
        self.assertIn("installer_set/added: atomic promotion must add exactly skill_id", errors)

    def test_promotion_ownership_and_reports_are_fail_closed(self) -> None:
        value = promotion_delta()
        value["domain_owned_files_changed"][0] = "registry/skill-registry.yaml"
        errors = interface_registry.governance_validation_errors(
            "promotion-delta", value, ROOT
        )
        self.assertTrue(any("domain_owned_files_changed/0" in item for item in errors))

        value = promotion_delta()
        value["shared_files_changed"][0] = "skills/another-skill/SKILL.md"
        errors = interface_registry.governance_validation_errors(
            "promotion-delta", value, ROOT
        )
        self.assertTrue(any("shared_files_changed" in item for item in errors))

        value = promotion_delta()
        value["reports"]["privacy_license"]["status"] = "block"
        self.assertTrue(
            interface_registry.governance_validation_errors(
                "promotion-delta", value, ROOT
            )
        )

        value = promotion_delta()
        value["reports"]["forward_tests"][0]["path"] = value["reports"][
            "privacy_license"
        ]["path"]
        self.assertIn(
            "reports: report paths must be unique",
            interface_registry.governance_validation_errors(
                "promotion-delta", value, ROOT
            ),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
