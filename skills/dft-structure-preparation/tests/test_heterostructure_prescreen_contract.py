from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "candidate-heterostructure-prescreen.schema.json"
REFERENCE_PATH = ROOT / "references" / "heterostructure-prescreen.md"


def sha256(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def role_deformation(scale: float) -> dict[str, object]:
    strain = (scale * scale - 1.0) / 2.0
    return {
        "deformation_gradient_2d": [[scale, 0.0], [0.0, scale]],
        "green_lagrange_strain_2d": [[strain, 0.0], [0.0, strain]],
        "principal_strains": [strain, strain],
        "max_abs_principal_strain": abs(strain),
    }


def gate_evaluations() -> list[dict[str, object]]:
    values = (
        ("atom_budget", "less_than_or_equal", 12, 24, "count"),
        ("principal_strain", "less_than_or_equal", 0.01005, 0.04, "fraction"),
        ("cell_angle", "less_than_or_equal", 0.3, 1.0, "degree"),
        ("interlayer_overlap", "greater_than_or_equal", 2.1, 1.5, "angstrom"),
        ("vacuum", "greater_than_or_equal", 15.0, 12.0, "angstrom"),
    )
    return [
        {
            "criterion": criterion,
            "comparator": comparator,
            "observed": observed,
            "threshold": threshold,
            "unit": unit,
            "outcome": "pass",
            "finding_id": None,
            "evidence_sha256": sha256(f"gate-evidence-{criterion}"),
        }
        for criterion, comparator, observed, threshold, unit in values
    ]


def synthetic_record() -> dict[str, object]:
    return {
        "contract_name": "candidate-heterostructure-prescreen",
        "schema_version": "1.0",
        "record_id": "synthetic-prescreen-001",
        "skill_id": "dft-structure-preparation",
        "lifecycle": "development",
        "implementation_state": "design-only",
        "semantic_validator_state": "not-implemented",
        "operational_use_authorized": False,
        "blocker_ids": [
            "HETEROSTRUCTURE_PRESCREEN_DESIGN_ONLY",
            "SEMANTIC_VALIDATOR_NOT_IMPLEMENTED",
            "OPERATIONAL_USE_NOT_AUTHORIZED",
            "SCHEMA_VALIDITY_IS_NOT_GEOMETRIC_VALIDITY",
        ],
        "semantic_validator_obligations": [
            "RECOMPUTE_HNF_AND_UNIMODULAR_ALGEBRA",
            "RECOMPUTE_DEFORMATION_AND_STRAIN",
            "RECOMPUTE_GATE_BOUNDS_AND_OUTCOMES",
            "VERIFY_PARENT_CHILD_ARTIFACT_HASHES_AND_PREIMAGES",
            "VERIFY_REFERENTIAL_INTEGRITY_AND_ROLE_HASHES",
            "VERIFY_COUNTS_AND_WORKFLOW_AGGREGATES",
            "VERIFY_PARETO_COMPARISON_UNIVERSE",
            "VERIFY_REGISTRY_EQUIVALENCE_AND_STABILITY_SET_COVERAGE",
            "VERIFY_MATERIALIZATION_AND_SELECTION_SET_EQUALITIES",
        ],
        "claim_ceiling": "no_positive_claim",
        "future_claim_ceiling": "geometric_eligibility_only",
        "stability_assessed": False,
        "energy_model_used": False,
        "promotion_authorized": False,
        "execution_authorized": False,
        "policy": {
            "policy_sha256": sha256("synthetic-policy"),
            "hard_rejection_basis": "explicit-geometric-gates-only",
            "aggregate_score_used": False,
            "single_registry_hard_rejection_allowed": False,
            "single_registry_can_establish_stability": False,
            "mechanism_preview_can_remove_stability_candidate": False,
            "parent_rich_audit_reuse_required": True,
            "child_receipt_kind": "lightweight-derived-child",
        },
        "parent_audit_cache": [
            {
                "parent_ref": "parent-bottom",
                "layer_role": "bottom",
                "source_snapshot_sha256": sha256("bottom-source"),
                "structure_manifest_sha256": sha256("bottom-manifest"),
                "rich_audit_artifact_ref": "audit-artifact-bottom",
                "rich_audit_artifact_sha256": sha256("bottom-audit-artifact"),
                "rich_audit_cache_preimage_ref": "audit-preimage-bottom",
                "rich_audit_cache_preimage": {
                    "source_snapshot_sha256": sha256("bottom-source"),
                    "structure_manifest_sha256": sha256("bottom-manifest"),
                    "audit_policy_sha256": sha256("audit-policy"),
                    "audit_producer_identity_sha256": sha256("audit-producer"),
                    "normalized_options_sha256": sha256("audit-options"),
                },
                "rich_audit_cache_preimage_sha256": sha256("bottom-cache-preimage"),
                "rich_audit_cache_key_sha256": sha256("bottom-cache"),
                "rich_audit_state": "pass",
                "cache_reuse_state": "reusable",
                "rich_audit_repeated_per_child": False,
            },
            {
                "parent_ref": "parent-top",
                "layer_role": "top",
                "source_snapshot_sha256": sha256("top-source"),
                "structure_manifest_sha256": sha256("top-manifest"),
                "rich_audit_artifact_ref": "audit-artifact-top",
                "rich_audit_artifact_sha256": sha256("top-audit-artifact"),
                "rich_audit_cache_preimage_ref": "audit-preimage-top",
                "rich_audit_cache_preimage": {
                    "source_snapshot_sha256": sha256("top-source"),
                    "structure_manifest_sha256": sha256("top-manifest"),
                    "audit_policy_sha256": sha256("audit-policy"),
                    "audit_producer_identity_sha256": sha256("audit-producer"),
                    "normalized_options_sha256": sha256("audit-options"),
                },
                "rich_audit_cache_preimage_sha256": sha256("top-cache-preimage"),
                "rich_audit_cache_key_sha256": sha256("top-cache"),
                "rich_audit_state": "pass",
                "cache_reuse_state": "reusable",
                "rich_audit_repeated_per_child": False,
            },
        ],
        "commensurate_search": {
            "algorithm_scope": (
                "general-2d-hnf-unimodular-full-deformation-shared-strain"
            ),
            "coverage": {
                "state": "partial",
                "general_2d_hnf": "partial",
                "unimodular_basis_changes": "partial",
                "full_2d_deformation": "complete",
                "shared_strain_split": "complete",
                "enumerated_candidate_count": 1,
                "evaluated_candidate_count": 1,
                "geometrically_eligible_candidate_count": 1,
                "excluded_space": [
                    "synthetic fixture enumerates one bounded matrix combination only"
                ],
            },
            "bounds": {
                "max_hnf_determinant": 4,
                "max_unimodular_entry_abs": 2,
                "max_total_atoms": 24,
                "max_abs_principal_strain": 0.04,
                "strain_measure": "principal-strain-from-full-2d-deformation",
                "shared_strain_objective": (
                    "minimize-maximum-absolute-principal-strain-across-roles"
                ),
            },
            "candidates": [
                {
                    "candidate_id": "cell-candidate-001",
                    "bottom_parent_ref": "parent-bottom",
                    "top_parent_ref": "parent-top",
                    "bottom_hnf": [[1, 0], [0, 2]],
                    "top_hnf": [[2, 0], [0, 1]],
                    "bottom_unimodular": [[1, 0], [0, 1]],
                    "top_unimodular": [[0, -1], [1, 0]],
                    "common_interface_basis_ang": [[4.0, 0.1], [0.2, 5.0]],
                    "shared_strain": {
                        "allocation_method": "minimax-principal-strain",
                        "objective_value": 0.01005,
                        "bottom": role_deformation(1.01),
                        "top": role_deformation(0.99),
                    },
                    "total_interface_atoms": 12,
                    "gate_evaluations": gate_evaluations(),
                    "geometric_gate": {
                        "state": "pass",
                        "finding_ids": [],
                    },
                    "pareto_state": {
                        "state": "nondominated",
                        "basis": "explicit-metric-vector-without-aggregate-score",
                        "comparison_universe_sha256": sha256(
                            "pareto-comparison-universe"
                        ),
                        "comparison_policy_sha256": sha256("pareto-policy"),
                        "comparison_universe_size": 1,
                        "metric_vector": [
                            {
                                "metric": "max_abs_principal_strain",
                                "value": 0.01005,
                                "direction": "minimize",
                                "unit": "fraction",
                            },
                            {
                                "metric": "total_interface_atoms",
                                "value": 12,
                                "direction": "minimize",
                                "unit": "count",
                            },
                            {
                                "metric": "interface_area",
                                "value": 19.98,
                                "direction": "minimize",
                                "unit": "angstrom_squared",
                            },
                            {
                                "metric": "cell_condition_number",
                                "value": 1.3,
                                "direction": "minimize",
                                "unit": "dimensionless",
                            },
                        ],
                    },
                }
            ],
        },
        "registry_equivalence": {
            "coverage_state": "partial",
            "method": "role-aware-periodic-geometry-equivalence",
            "layer_roles_preserved": True,
            "single_representative_is_stability_complete": False,
            "enumeration_policy": {
                "policy_ref": "registry-policy-001",
                "policy_version": "1.0",
                "policy_sha256": sha256("registry-policy"),
                "registry_set_preimage_sha256": sha256("registry-set-preimage"),
                "nominal_registry_ids_sha256": sha256("nominal-registry-ids"),
                "translation_domain": "fractional-in-plane",
                "vertical_ordering_policy": "explicit-in-enumeration-preimage",
                "layer_flip_policy": "explicit-in-enumeration-preimage",
                "initial_gap_policy_sha256": sha256("initial-gap-policy"),
            },
            "matcher": {
                "matcher_name": "synthetic-role-aware-matcher",
                "matcher_version": "1.0",
                "configuration_sha256": sha256("matcher-configuration"),
                "role_partition_required": True,
                "tolerances": {
                    "site_distance_ang": 0.01,
                    "lattice_length_relative": 0.001,
                    "lattice_angle_deg": 0.1,
                },
            },
            "periodic_axes": [True, True, False],
            "configuration_sha256": sha256("registry-configuration"),
            "nominal_registry_count": 2,
            "unique_role_aware_registry_count": 1,
            "excluded_space": [
                "synthetic fixture evaluates a bounded translation subset"
            ],
            "classes": [
                {
                    "class_id": "registry-class-001",
                    "representative_registry_id": "registry-001",
                    "member_registry_ids": ["registry-001", "registry-002"],
                    "bottom_role_membership_sha256": sha256("bottom-role-members"),
                    "top_role_membership_sha256": sha256("top-role-members"),
                    "equivalence_evidence_sha256": sha256("equivalence-evidence"),
                }
            ],
        },
        "lanes": {
            "mechanism_preview": {
                "purpose": "mechanism-preview-and-queue-ordering-only",
                "registry_scope": (
                    "optional-subset-of-geometrically-eligible-role-aware-registries"
                ),
                "single_registry_preview_allowed": True,
                "hard_rejection_authorized": False,
                "stability_assessment_authorized": False,
                "preview_execution_authorized": False,
                "outcome_can_remove_stability_candidate": False,
            },
            "stability": {
                "purpose": "downstream-stability-evidence-generation",
                "required_registry_scope": (
                    "all-geometrically-eligible-role-aware-unique-registries"
                ),
                "geometric_prescreen_is_sufficient": False,
                "consistent_relaxation_required": True,
                "common_refined_static_ranking_required": True,
                "result_recorded_by_this_contract": False,
            },
        },
        "workflow_states": {
            "coverage": {
                "state": "partial",
                "reasons": ["one bounded synthetic search slice was evaluated"],
            },
            "gate": {
                "state": "pass",
                "reasons": ["the emitted candidate passed declared geometry gates"],
            },
            "selection": {
                "state": "candidates_routed",
                "mechanism_preview_count": 1,
                "stability_lane_count": 1,
                "reasons": ["one role-aware representative was retained for both lanes"],
            },
            "materialization": {
                "state": "not_requested",
                "materialized_receipt_count": 0,
                "reasons": ["the synthetic receipt remains lazy"],
            },
        },
        "child_receipts": [
            {
                "receipt_id": "child-receipt-001",
                "receipt_kind": "lightweight-derived-child",
                "bottom_parent_ref": "parent-bottom",
                "top_parent_ref": "parent-top",
                "commensurate_candidate_id": "cell-candidate-001",
                "registry_id": "registry-001",
                "registry_shift_fractional_2d": [0.0, 0.5],
                "registry_equivalence_class_id": "registry-class-001",
                "bottom_role_membership_sha256": sha256("bottom-role-members"),
                "top_role_membership_sha256": sha256("top-role-members"),
                "transformation_parameters_sha256": sha256("transform-parameters"),
                "transformation_artifact_ref": "transformation-artifact-001",
                "transformation_artifact_sha256": sha256(
                    "transformation-artifact"
                ),
                "site_mapping_artifact_ref": "site-mapping-artifact-001",
                "site_mapping_sha256": sha256("site-mapping"),
                "gate_evaluations_sha256": sha256("gate-evaluations"),
                "parent_rich_audit_reused": True,
                "child_rich_audit_repeated": False,
                "child_snapshot_ref": None,
                "child_structure_id": None,
                "child_structure_sha256": None,
                "states": {
                    "coverage": "within_evaluated_scope",
                    "gate": "pass",
                    "selection": "retained_both_lanes",
                    "materialization": "not_requested",
                },
                "gate_findings": [],
            }
        ],
        "limitations": [
            "synthetic fixtures do not establish real-artifact validity",
            "geometric eligibility does not establish energetic or dynamic stability",
            "downstream calculation and scientific acceptance remain separate",
        ],
        "provenance": {
            "producer": "synthetic-contract-test",
            "producer_version": "1.0",
            "input_bundle_sha256": sha256("synthetic-input-bundle"),
        },
    }


class HeterostructurePrescreenContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def assert_valid(self, record: dict[str, object]) -> None:
        errors = sorted(
            self.validator.iter_errors(record),
            key=lambda error: tuple(str(item) for item in error.absolute_path),
        )
        self.assertEqual(
            errors,
            [],
            "\n".join(
                f"{'/'.join(str(item) for item in error.absolute_path)}: {error.message}"
                for error in errors
            ),
        )

    def assert_invalid(self, record: dict[str, object]) -> None:
        self.assertTrue(list(self.validator.iter_errors(record)))

    def test_schema_identity_and_anonymous_synthetic_record(self) -> None:
        self.assertEqual(
            self.schema["title"],
            "candidate-heterostructure-prescreen@1.0",
        )
        record = synthetic_record()
        self.assert_valid(record)
        serialized = json.dumps(record, sort_keys=True)
        self.assertNotIn("/", serialized)
        self.assertNotIn("\\", serialized)
        self.assertNotIn(".cif", serialized.lower())

    def test_claim_and_no_energy_boundaries_are_schema_constants(self) -> None:
        mutations = (
            ("claim_ceiling", "geometric_eligibility_only"),
            ("future_claim_ceiling", "stability"),
            ("stability_assessed", True),
            ("energy_model_used", True),
            ("promotion_authorized", True),
            ("execution_authorized", True),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                record = synthetic_record()
                record[key] = value
                self.assert_invalid(record)

        for key in (
            "aggregate_score_used",
            "single_registry_hard_rejection_allowed",
            "single_registry_can_establish_stability",
            "mechanism_preview_can_remove_stability_candidate",
        ):
            with self.subTest(policy=key):
                record = synthetic_record()
                record["policy"][key] = True
                self.assert_invalid(record)

        record = synthetic_record()
        record["commensurate_search"]["candidates"][0]["aggregate_score"] = 0.7
        self.assert_invalid(record)

    def test_design_only_state_and_semantic_validator_blockers_are_immutable(self) -> None:
        mutations = (
            ("implementation_state", "implemented"),
            ("semantic_validator_state", "implemented"),
            ("operational_use_authorized", True),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                record = synthetic_record()
                record[key] = value
                self.assert_invalid(record)

        record = synthetic_record()
        record["blocker_ids"].pop()
        self.assert_invalid(record)

        record = synthetic_record()
        record["blocker_ids"][0] = "OPERATIONAL"
        self.assert_invalid(record)

        record = synthetic_record()
        record["semantic_validator_obligations"][2] = "GATES_ALREADY_VALID"
        self.assert_invalid(record)

    def test_two_lanes_preserve_the_single_registry_boundary(self) -> None:
        record = synthetic_record()
        record["lanes"]["mechanism_preview"]["hard_rejection_authorized"] = True
        self.assert_invalid(record)

        record = synthetic_record()
        record["lanes"]["mechanism_preview"][
            "outcome_can_remove_stability_candidate"
        ] = True
        self.assert_invalid(record)

        record = synthetic_record()
        record["lanes"]["stability"][
            "required_registry_scope"
        ] = "one-selected-registry"
        self.assert_invalid(record)

        record = synthetic_record()
        record["lanes"]["stability"]["geometric_prescreen_is_sufficient"] = True
        self.assert_invalid(record)

    def test_coverage_can_be_fail_closed_without_claiming_general_search(self) -> None:
        record = synthetic_record()
        coverage = record["commensurate_search"]["coverage"]
        coverage.update(
            {
                "state": "not_implemented",
                "general_2d_hnf": "not_implemented",
                "unimodular_basis_changes": "not_implemented",
                "full_2d_deformation": "not_implemented",
                "shared_strain_split": "not_implemented",
                "enumerated_candidate_count": 0,
                "evaluated_candidate_count": 0,
                "geometrically_eligible_candidate_count": 0,
                "excluded_space": ["general 2D search is not implemented"],
            }
        )
        record["commensurate_search"]["candidates"] = []
        record["registry_equivalence"].update(
            {
                "coverage_state": "not_implemented",
                "nominal_registry_count": 0,
                "unique_role_aware_registry_count": 0,
                "excluded_space": ["registry enumeration is not implemented"],
                "classes": [],
            }
        )
        record["workflow_states"] = {
            "coverage": {
                "state": "not_implemented",
                "reasons": ["enumeration was not run"],
            },
            "gate": {
                "state": "not_evaluated",
                "reasons": ["no candidate exists"],
            },
            "selection": {
                "state": "not_run",
                "mechanism_preview_count": 0,
                "stability_lane_count": 0,
                "reasons": ["no candidate exists"],
            },
            "materialization": {
                "state": "not_requested",
                "materialized_receipt_count": 0,
                "reasons": ["no child receipt exists"],
            },
        }
        record["child_receipts"] = []
        self.assert_valid(record)

        incomplete = synthetic_record()
        incomplete["commensurate_search"]["coverage"]["state"] = "complete"
        self.assert_invalid(incomplete)

        false_not_implemented = deepcopy(record)
        false_not_implemented["commensurate_search"]["candidates"] = [
            synthetic_record()["commensurate_search"]["candidates"][0]
        ]
        self.assert_invalid(false_not_implemented)

        missing_exclusion = deepcopy(record)
        missing_exclusion["commensurate_search"]["coverage"]["excluded_space"] = []
        self.assert_invalid(missing_exclusion)

        missing_registry_exclusion = deepcopy(record)
        missing_registry_exclusion["registry_equivalence"]["excluded_space"] = []
        self.assert_invalid(missing_registry_exclusion)

    def test_complete_coverage_allows_a_reproducible_zero_survivor_result(self) -> None:
        record = synthetic_record()
        record["commensurate_search"]["coverage"].update(
            {
                "state": "complete",
                "general_2d_hnf": "complete",
                "unimodular_basis_changes": "complete",
                "full_2d_deformation": "complete",
                "shared_strain_split": "complete",
                "enumerated_candidate_count": 0,
                "evaluated_candidate_count": 0,
                "geometrically_eligible_candidate_count": 0,
                "excluded_space": [],
            }
        )
        record["commensurate_search"]["candidates"] = []
        record["registry_equivalence"].update(
            {
                "coverage_state": "complete",
                "nominal_registry_count": 0,
                "unique_role_aware_registry_count": 0,
                "excluded_space": [],
                "classes": [],
            }
        )
        record["workflow_states"] = {
            "coverage": {
                "state": "complete",
                "reasons": ["the bounded synthetic universe was fully enumerated"],
            },
            "gate": {
                "state": "not_evaluated",
                "reasons": ["the complete search emitted no candidate"],
            },
            "selection": {
                "state": "no_geometrically_eligible_candidate",
                "mechanism_preview_count": 0,
                "stability_lane_count": 0,
                "reasons": ["zero survivor is retained as the bounded result"],
            },
            "materialization": {
                "state": "not_requested",
                "materialized_receipt_count": 0,
                "reasons": ["there is no child to materialize"],
            },
        }
        record["child_receipts"] = []
        self.assert_valid(record)

    def test_role_aware_equivalence_and_parent_roles_are_mandatory(self) -> None:
        record = synthetic_record()
        record["registry_equivalence"]["layer_roles_preserved"] = False
        self.assert_invalid(record)

        record = synthetic_record()
        record["registry_equivalence"]["method"] = "atom-only-geometry"
        self.assert_invalid(record)

        record = synthetic_record()
        record["parent_audit_cache"][1]["layer_role"] = "bottom"
        self.assert_invalid(record)

        record = synthetic_record()
        del record["registry_equivalence"]["classes"][0][
            "top_role_membership_sha256"
        ]
        self.assert_invalid(record)

    def test_parent_cache_and_lightweight_child_receipt_are_fail_closed(self) -> None:
        record = synthetic_record()
        record["parent_audit_cache"][0]["rich_audit_repeated_per_child"] = True
        self.assert_invalid(record)

        record = synthetic_record()
        record["parent_audit_cache"][0]["rich_audit_state"] = "review_required"
        self.assert_invalid(record)

        record = synthetic_record()
        record["parent_audit_cache"][0]["cache_reuse_state"] = "unavailable"
        self.assert_invalid(record)

        record = synthetic_record()
        record["child_receipts"][0]["parent_rich_audit_reused"] = False
        self.assert_invalid(record)

        record = synthetic_record()
        record["child_receipts"][0]["child_rich_audit_repeated"] = True
        self.assert_invalid(record)

        for field in (
            "rich_audit_artifact_ref",
            "rich_audit_artifact_sha256",
            "rich_audit_cache_preimage_ref",
            "rich_audit_cache_preimage",
            "rich_audit_cache_preimage_sha256",
        ):
            with self.subTest(parent_evidence=field):
                record = synthetic_record()
                del record["parent_audit_cache"][0][field]
                self.assert_invalid(record)

        for field in (
            "transformation_artifact_ref",
            "transformation_artifact_sha256",
            "site_mapping_artifact_ref",
            "site_mapping_sha256",
            "gate_evaluations_sha256",
        ):
            with self.subTest(child_evidence=field):
                record = synthetic_record()
                del record["child_receipts"][0][field]
                self.assert_invalid(record)

        record = synthetic_record()
        record["child_receipts"][0]["states"]["materialization"] = "materialized"
        self.assert_invalid(record)

        record = synthetic_record()
        receipt = record["child_receipts"][0]
        receipt["states"]["materialization"] = "materialized"
        receipt["child_snapshot_ref"] = "child-snapshot-001"
        receipt["child_structure_id"] = "child-structure-001"
        receipt["child_structure_sha256"] = sha256("child-structure")
        record["workflow_states"]["materialization"].update(
            {
                "state": "complete",
                "materialized_receipt_count": 1,
                "reasons": ["the selected child was materialized"],
            }
        )
        self.assert_valid(record)

    def test_gate_evaluations_and_pareto_evidence_are_readable_and_strict(self) -> None:
        record = synthetic_record()
        record["commensurate_search"]["candidates"][0]["gate_evaluations"].pop()
        self.assert_invalid(record)

        record = synthetic_record()
        evaluation = record["commensurate_search"]["candidates"][0][
            "gate_evaluations"
        ][0]
        evaluation["unit"] = "angstrom"
        self.assert_invalid(record)

        record = synthetic_record()
        evaluation = record["commensurate_search"]["candidates"][0][
            "gate_evaluations"
        ][0]
        evaluation["outcome"] = "blocked"
        evaluation["finding_id"] = "ATOM_BUDGET_EXCEEDED"
        self.assert_invalid(record)

        for field in (
            "comparison_universe_sha256",
            "comparison_policy_sha256",
            "metric_vector",
        ):
            with self.subTest(pareto_evidence=field):
                record = synthetic_record()
                del record["commensurate_search"]["candidates"][0]["pareto_state"][
                    field
                ]
                self.assert_invalid(record)

    def test_registry_scope_policy_matcher_and_configuration_are_required(self) -> None:
        for field in (
            "enumeration_policy",
            "matcher",
            "periodic_axes",
            "configuration_sha256",
        ):
            with self.subTest(registry_evidence=field):
                record = synthetic_record()
                del record["registry_equivalence"][field]
                self.assert_invalid(record)

        record = synthetic_record()
        record["registry_equivalence"]["periodic_axes"] = [True, False, True]
        self.assert_invalid(record)

        record = synthetic_record()
        del record["registry_equivalence"]["matcher"]["tolerances"][
            "site_distance_ang"
        ]
        self.assert_invalid(record)

        record = synthetic_record()
        record["registry_equivalence"]["excluded_space"] = []
        self.assert_invalid(record)

    def test_coverage_gate_selection_and_materialization_remain_orthogonal(self) -> None:
        for axis in ("coverage", "gate", "selection", "materialization"):
            with self.subTest(axis=axis):
                record = synthetic_record()
                del record["workflow_states"][axis]
                self.assert_invalid(record)

        record = synthetic_record()
        record["workflow_states"]["status"] = "pass"
        self.assert_invalid(record)

        record = synthetic_record()
        receipt = record["child_receipts"][0]
        receipt["states"]["gate"] = "blocked"
        receipt["states"]["selection"] = "not_selected"
        receipt["gate_findings"] = [
            {
                "finding_id": "PRINCIPAL_STRAIN_LIMIT",
                "criterion": "principal_strain",
                "observed": 0.06,
                "threshold": 0.04,
                "unit": "fraction",
            }
        ]
        self.assert_valid(record)

        record = synthetic_record()
        receipt = record["child_receipts"][0]
        receipt["states"]["gate"] = "blocked"
        receipt["gate_findings"] = [
            {
                "finding_id": "PRINCIPAL_STRAIN_LIMIT",
                "criterion": "principal_strain",
                "observed": 0.06,
                "threshold": 0.04,
                "unit": "fraction",
            }
        ]
        self.assert_invalid(record)

    def test_reference_states_operational_non_goals(self) -> None:
        reference = REFERENCE_PATH.read_text(encoding="utf-8")
        for required_text in (
            "implementation_state=design-only",
            "semantic_validator_state=not-implemented",
            "operational_use_authorized=false",
            "SCHEMA_VALIDITY_IS_NOT_GEOMETRIC_VALIDITY",
            "claim_ceiling=no_positive_claim",
            "future_claim_ceiling=geometric_eligibility_only",
            "stability_assessed=false",
            "energy_model_used=false",
            "general two-dimensional commensuration",
            "role-aware-periodic-geometry-equivalence",
            "gate_evaluations",
            "comparison-universe hash",
            "Do not collapse the lanes into one scalar score",
            "No axis implies another",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, reference)


if __name__ == "__main__":
    unittest.main()
