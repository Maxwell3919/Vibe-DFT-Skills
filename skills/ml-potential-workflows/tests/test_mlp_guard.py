from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_official_source_scope as source_scope  # noqa: E402
import mlp_guard as guard  # noqa: E402


def raw(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def dataset_manifest() -> dict[str, object]:
    return json.loads((ROOT / "examples" / "synthetic-dataset.json").read_text(encoding="utf-8"))


def dataset_chain() -> tuple[dict[str, object], bytes]:
    value = dataset_manifest()
    result = guard.audit_dataset(value, raw(value))
    return result, raw(result)


def training_request(dataset_report_raw: bytes, *, mode: str = "train_from_scratch") -> dict[str, object]:
    return {
        "schema_version": "candidate-1.0",
        "workflow_id": "water-mace-001",
        "provider_profile": "mace-python",
        "provider_version": "0.3.16",
        "mode": mode,
        "dataset_audit_sha256": guard.sha256(dataset_report_raw),
        "species_order": ["H", "O"],
        "seeds": {"split": 1, "initialization": 2, "training": 3},
        "precision": "float64",
        "cutoff_angstrom": 5.0,
        "loss_weights": {"energy": 1.0, "forces": 10.0, "stress": 0.0},
        "stopping": {
            "max_epochs": 100,
            "patience": 20,
            "selection_metric": "force_mae_ev_per_angstrom",
            "checkpoint_interval": 5,
        },
        "thresholds": {
            "energy_mae_ev_per_atom": 0.01,
            "energy_rmse_ev_per_atom": 0.02,
            "energy_p95_abs_ev_per_atom": 0.03,
            "force_mae_ev_per_angstrom": 0.05,
            "force_rmse_ev_per_angstrom": 0.08,
            "force_p95_abs_ev_per_angstrom": 0.15,
        },
        "required_slices": ["per_species", "configuration_class", "ood"],
        "required_slice_ids": {
            "per_species": ["h", "o"],
            "configuration_class": ["molecular"],
            "ood": ["ood-main"],
        },
        "environment_sha256": "a" * 64,
        "provider_config_sha256": "b" * 64,
        "parent_model_sha256": None if mode == "train_from_scratch" else "c" * 64,
        "parent_model_record_sha256": None if mode == "train_from_scratch" else "9" * 64,
    }


def plan_chain(*, mode: str = "train_from_scratch") -> tuple[dict[str, object], bytes, dict[str, object], bytes]:
    dataset, dataset_raw = dataset_chain()
    request = training_request(dataset_raw, mode=mode)
    result = guard.plan_training(request, raw(request), dataset, dataset_raw)
    return result, raw(result), dataset, dataset_raw


def model_manifest(plan: dict[str, object], plan_raw: bytes, *, mode: str = "train_from_scratch") -> dict[str, object]:
    observations = plan["observations"]
    return {
        "schema_version": "candidate-1.0",
        "model_id": "water-model-001",
        "provider_profile": observations["provider_profile"],
        "provider_version": observations["provider_version"],
        "mode": mode,
        "artifact_sha256": observations["parent_model_sha256"] if mode == "evaluate_pretrained" else "d" * 64,
        "artifact_bytes": 1024,
        "dataset_audit_sha256": observations["dataset_audit_sha256"],
        "training_plan_sha256": guard.sha256(plan_raw),
        "training_run_sha256": "e" * 64 if mode in {"train_from_scratch", "fine_tune"} else None,
        "official_model_record_sha256": None if mode in {"train_from_scratch", "fine_tune"} else observations["parent_model_record_sha256"],
        "parent_model_sha256": observations["parent_model_sha256"],
        "parent_model_record_sha256": observations["parent_model_record_sha256"],
        "species_order": observations["species_order"],
        "units": copy.deepcopy(guard.EXACT_UNITS),
        "cutoff_angstrom": observations["cutoff_angstrom"],
        "precision": observations["precision"],
        "energy_reference_convention": "reference-dft-total-energy-v1",
        "licenses": {"framework": "MIT", "model": "private-model", "dataset": "private-data"},
        "status": "training_completed" if mode in {"train_from_scratch", "fine_tune"} else "pretrained_unloaded",
    }


def model_chain(*, mode: str = "train_from_scratch") -> tuple[dict[str, object], bytes, dict[str, object], bytes, dict[str, object], bytes]:
    plan, plan_raw, dataset, dataset_raw = plan_chain(mode=mode)
    manifest = model_manifest(plan, plan_raw, mode=mode)
    result = guard.audit_model(manifest, raw(manifest), plan, plan_raw)
    return result, raw(result), plan, plan_raw, dataset, dataset_raw


def evaluation_record(model_raw: bytes, dataset_raw: bytes, plan_raw: bytes) -> dict[str, object]:
    plan = json.loads(plan_raw)
    metric_values = {
        "energy_mae_ev_per_atom": 0.005,
        "energy_rmse_ev_per_atom": 0.01,
        "energy_p95_abs_ev_per_atom": 0.02,
        "force_mae_ev_per_angstrom": 0.03,
        "force_rmse_ev_per_angstrom": 0.05,
        "force_p95_abs_ev_per_angstrom": 0.10,
    }
    slice_metrics = {
        "per_species": [
            {"slice_id": "h", "metrics": copy.deepcopy(metric_values)},
            {"slice_id": "o", "metrics": copy.deepcopy(metric_values)},
        ],
        "configuration_class": [
            {"slice_id": "molecular", "metrics": copy.deepcopy(metric_values)}
        ],
        "ood": [
            {"slice_id": "ood-main", "metrics": copy.deepcopy(metric_values)}
        ],
    }
    return {
        "schema_version": "candidate-1.0",
        "evaluation_id": "water-evaluation-001",
        "model_audit_sha256": guard.sha256(model_raw),
        "dataset_audit_sha256": guard.sha256(dataset_raw),
        "training_plan_sha256": guard.sha256(plan_raw),
        "evaluator_sha256": "1" * 64,
        "test_policy": "held_out_once_after_freeze",
        "test_influenced_selection": False,
        "metrics": metric_values,
        "slice_coverage": ["per_species", "configuration_class", "ood"],
        "slice_metrics": slice_metrics,
        "slice_metrics_sha256": guard.sha256(
            json.dumps(slice_metrics, sort_keys=True, separators=(",", ":")).encode()
        ),
        "thresholds_frozen_sha256": plan["observations"]["thresholds_sha256"],
    }


def evaluation_chain() -> tuple[dict[str, object], bytes, dict[str, object], bytes]:
    model, model_raw, plan, plan_raw, dataset, dataset_raw = model_chain()
    value = evaluation_record(model_raw, dataset_raw, plan_raw)
    result = guard.audit_evaluation(value, raw(value), model, model_raw, dataset, dataset_raw, plan, plan_raw)
    return result, raw(result), model, model_raw


def deployment_record(evaluation_raw: bytes, model_raw: bytes) -> dict[str, object]:
    return {
        "schema_version": "candidate-1.0",
        "deployment_id": "water-pilot-001",
        "model_audit_sha256": guard.sha256(model_raw),
        "evaluation_audit_sha256": guard.sha256(evaluation_raw),
        "target_engine": "lammps",
        "target_version": "reviewed-version",
        "adapter_sha256": "4" * 64,
        "species_order": ["H", "O"],
        "units": copy.deepcopy(guard.EXACT_UNITS),
        "observables": ["energy", "forces"],
        "domain": {
            "composition_id": "water-only",
            "structure_classes": ["liquid", "molecular"],
            "temperature_k": [250.0, 350.0],
            "pressure_gpa": [0.0, 0.1],
        },
        "max_timestep_fs": 0.5,
        "ensembles": ["nve", "nvt"],
        "monitor": {
            "kind": "committee-disagreement",
            "threshold": 0.2,
            "unit": "eV/angstrom",
            "fail_action": "stop_and_record",
        },
        "rollback_model_sha256": "5" * 64,
        "pilot": {"max_steps": 1000, "max_atoms": 1000},
        "authorization_decision_sha256": "6" * 64,
        "licenses_cleared": True,
    }


class DatasetTests(unittest.TestCase):
    def test_valid_metadata_dataset_passes_only_input_gates(self) -> None:
        value = dataset_manifest()
        result = guard.audit_dataset(value, raw(value))
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["claim_ceiling"], "no_positive_claim")
        self.assertEqual(result["future_gate_ceiling"], "input_gates_only")
        self.assertEqual(result["observations"]["split_counts"], {"train": 1, "validation": 1, "test": 1, "ood": 1})

    def test_group_leakage_is_blocked_even_when_structure_hashes_differ(self) -> None:
        value = dataset_manifest()
        value["frames"][1]["group_id"] = value["frames"][0]["group_id"]
        result = guard.audit_dataset(value, raw(value))
        self.assertIn("DATASET_GROUP_LEAKAGE", {item["code"] for item in result["findings"]})

    def test_same_source_run_cannot_hide_across_different_group_ids(self) -> None:
        value = dataset_manifest()
        value["frames"][1]["source_run_sha256"] = value["frames"][0]["source_run_sha256"]
        result = guard.audit_dataset(value, raw(value))
        self.assertIn("DATASET_SOURCE_RUN_LEAKAGE", {item["code"] for item in result["findings"]})

    def test_exact_structure_and_label_duplicates_are_blocked(self) -> None:
        value = dataset_manifest()
        value["frames"][1]["structure_sha256"] = value["frames"][0]["structure_sha256"]
        value["frames"][2]["labels_sha256"] = value["frames"][0]["labels_sha256"]
        codes = {item["code"] for item in guard.audit_dataset(value, raw(value))["findings"]}
        self.assertIn("DATASET_STRUCTURE_DUPLICATE", codes)
        self.assertIn("DATASET_LABEL_DUPLICATE", codes)

    def test_units_species_labels_and_stress_are_exact(self) -> None:
        value = dataset_manifest()
        value["units"]["forces"] = "Ha/bohr"
        value["frames"][0]["elements"] = ["O", "H"]
        value["frames"][1]["has_forces"] = False
        value["frames"][2]["has_stress"] = True
        codes = {item["code"] for item in guard.audit_dataset(value, raw(value))["findings"]}
        self.assertTrue({"DATASET_UNITS_INVALID", "DATASET_FRAME_SPECIES_INVALID", "DATASET_REQUIRED_LABEL_MISSING", "DATASET_STRESS_COVERAGE_MISMATCH"}.issubset(codes))

    def test_source_acceptance_and_all_required_splits_are_mandatory(self) -> None:
        value = dataset_manifest()
        value["frames"][0]["source_acceptance_sha256"] = None
        value["frames"] = [item for item in value["frames"] if item["split"] != "ood"]
        codes = {item["code"] for item in guard.audit_dataset(value, raw(value))["findings"]}
        self.assertIn("DATASET_SOURCE_LINEAGE_MISSING", codes)
        self.assertIn("DATASET_SPLIT_MISSING", codes)

    def test_source_acceptance_cannot_self_alias_run_or_label_evidence(self) -> None:
        value = dataset_manifest()
        value["frames"][0]["source_acceptance_sha256"] = value["frames"][0]["source_run_sha256"]
        result = guard.audit_dataset(value, raw(value))
        self.assertIn("DATASET_SOURCE_ROLE_COLLISION", {item["code"] for item in result["findings"]})


class PlanTests(unittest.TestCase):
    def test_valid_plan_binds_dataset_and_exposes_no_execution(self) -> None:
        result, _, _, _ = plan_chain()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["action_state"], "needs_authorization")
        self.assertEqual(result["claim_ceiling"], "no_positive_claim")

    def test_provider_version_mode_matrix_is_exact(self) -> None:
        dataset, dataset_raw = dataset_chain()
        request = training_request(dataset_raw)
        request["provider_version"] = "latest"
        result = guard.plan_training(request, raw(request), dataset, dataset_raw)
        self.assertIn("PLAN_PROVIDER_MODE_INVALID", {item["code"] for item in result["findings"]})
        request = training_request(dataset_raw)
        request["provider_profile"] = "fairchem-v2-uma"
        request["provider_version"] = "2.21.0"
        request["mode"] = "train_from_scratch"
        result = guard.plan_training(request, raw(request), dataset, dataset_raw)
        self.assertIn("PLAN_PROVIDER_MODE_INVALID", {item["code"] for item in result["findings"]})

    def test_dataset_hash_seed_and_parent_lineage_mutations_block(self) -> None:
        dataset, dataset_raw = dataset_chain()
        request = training_request(dataset_raw)
        request["dataset_audit_sha256"] = "0" * 64
        request["seeds"]["training"] = None
        request["parent_model_sha256"] = "c" * 64
        codes = {item["code"] for item in guard.plan_training(request, raw(request), dataset, dataset_raw)["findings"]}
        self.assertTrue({"PLAN_DATASET_BINDING_MISMATCH", "PLAN_SEEDS_INVALID", "PLAN_PARENT_MODEL_INVALID"}.issubset(codes))

    def test_environment_and_provider_config_must_be_distinct_artifacts(self) -> None:
        dataset, dataset_raw = dataset_chain()
        request = training_request(dataset_raw)
        request["provider_config_sha256"] = request["environment_sha256"]
        result = guard.plan_training(request, raw(request), dataset, dataset_raw)
        self.assertIn("PLAN_PROVENANCE_ROLE_COLLISION", {item["code"] for item in result["findings"]})

    def test_metrics_slices_and_stress_loss_cannot_be_defaulted(self) -> None:
        dataset, dataset_raw = dataset_chain()
        request = training_request(dataset_raw)
        del request["thresholds"]["force_p95_abs_ev_per_angstrom"]
        request["required_slices"] = ["per_species"]
        request["required_slice_ids"]["per_species"] = ["h"]
        request["loss_weights"]["stress"] = 1.0
        codes = {item["code"] for item in guard.plan_training(request, raw(request), dataset, dataset_raw)["findings"]}
        self.assertTrue({"PLAN_THRESHOLDS_INVALID", "PLAN_SLICES_INVALID", "PLAN_SLICE_IDS_INVALID", "PLAN_STRESS_LOSS_WITHOUT_LABELS"}.issubset(codes))

    def test_selection_and_checkpoint_policy_must_fit_the_frozen_metric_and_budget(self) -> None:
        dataset, dataset_raw = dataset_chain()
        request = training_request(dataset_raw)
        request["stopping"]["selection_metric"] = "test_score"
        request["stopping"]["patience"] = 101
        result = guard.plan_training(request, raw(request), dataset, dataset_raw)
        self.assertIn("PLAN_STOPPING_INVALID", {item["code"] for item in result["findings"]})

    def test_forged_minimal_or_mutated_upstream_pass_report_is_rejected(self) -> None:
        dataset, dataset_raw = dataset_chain()
        request = training_request(dataset_raw)
        minimal = {
            "schema_version": "candidate-1.0",
            "contract_name": "mlp-candidate-audit",
            "command": "audit-dataset",
            "candidate_lifecycle": "development",
            "status": "pass",
            "claim_ceiling": "no_positive_claim",
            "findings": [],
        }
        result = guard.plan_training(request, raw(request), minimal, raw(minimal))
        self.assertIn("UPSTREAM_REPORT_INVALID", {item["code"] for item in result["findings"]})
        changed = copy.deepcopy(dataset)
        changed["gates"] = list(reversed(changed["gates"]))
        result = guard.plan_training(training_request(raw(changed)), raw(request), changed, raw(changed))
        self.assertIn("UPSTREAM_REPORT_GATES_INVALID", {item["code"] for item in result["findings"]})


class ModelTests(unittest.TestCase):
    def test_trained_model_manifest_passes_without_loading_artifact(self) -> None:
        result, _, _, _, _, _ = model_chain()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["action_state"], "needs_authorization")
        self.assertTrue(any("never opened" in item for item in result["limitations"]))

    def test_model_artifact_plan_species_and_precision_mutations_block(self) -> None:
        plan, plan_raw, _, _ = plan_chain()
        value = model_manifest(plan, plan_raw)
        value["artifact_sha256"] = "not-a-hash"
        value["species_order"] = ["O", "H"]
        value["precision"] = "float32"
        codes = {item["code"] for item in guard.audit_model(value, raw(value), plan, plan_raw)["findings"]}
        self.assertTrue({"MODEL_ARTIFACT_IDENTITY_INVALID", "MODEL_PLAN_MISMATCH", "MODEL_NUMERIC_CONVENTION_INVALID"}.issubset(codes))

    def test_pretrained_origin_is_separate_from_training_run(self) -> None:
        plan, plan_raw, _, _ = plan_chain(mode="evaluate_pretrained")
        value = model_manifest(plan, plan_raw, mode="evaluate_pretrained")
        passed = guard.audit_model(value, raw(value), plan, plan_raw)
        self.assertEqual(passed["status"], "pass")
        value["training_run_sha256"] = "e" * 64
        blocked = guard.audit_model(value, raw(value), plan, plan_raw)
        self.assertIn("MODEL_ORIGIN_INVALID", {item["code"] for item in blocked["findings"]})

    def test_fine_tune_and_pretrained_model_parent_lineage_is_exact(self) -> None:
        plan, plan_raw, _, _ = plan_chain(mode="fine_tune")
        value = model_manifest(plan, plan_raw, mode="fine_tune")
        value["parent_model_record_sha256"] = "0" * 64
        result = guard.audit_model(value, raw(value), plan, plan_raw)
        self.assertIn("MODEL_PARENT_LINEAGE_MISMATCH", {item["code"] for item in result["findings"]})

    def test_license_roles_must_remain_separate(self) -> None:
        plan, plan_raw, _, _ = plan_chain()
        value = model_manifest(plan, plan_raw)
        value["licenses"] = {"framework": "MIT"}
        result = guard.audit_model(value, raw(value), plan, plan_raw)
        self.assertIn("MODEL_LICENSE_INVENTORY_INVALID", {item["code"] for item in result["findings"]})


class EvaluationTests(unittest.TestCase):
    def test_valid_evaluation_passes_frozen_metrics_but_not_science(self) -> None:
        result, _, _, _ = evaluation_chain()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["future_gate_ceiling"], "numerical_candidate_only")
        self.assertEqual(result["claim_ceiling"], "no_positive_claim")

    def test_upstream_hash_and_test_reuse_are_blocked(self) -> None:
        model, model_raw, plan, plan_raw, dataset, dataset_raw = model_chain()
        value = evaluation_record(model_raw, dataset_raw, plan_raw)
        value["model_audit_sha256"] = "0" * 64
        value["test_influenced_selection"] = True
        codes = {item["code"] for item in guard.audit_evaluation(value, raw(value), model, model_raw, dataset, dataset_raw, plan, plan_raw)["findings"]}
        self.assertTrue({"EVALUATION_LINEAGE_MISMATCH", "EVALUATION_TEST_LEAKAGE"}.issubset(codes))

    def test_threshold_failure_cannot_be_hidden_by_other_low_means(self) -> None:
        model, model_raw, plan, plan_raw, dataset, dataset_raw = model_chain()
        value = evaluation_record(model_raw, dataset_raw, plan_raw)
        value["metrics"]["force_p95_abs_ev_per_angstrom"] = 0.151
        result = guard.audit_evaluation(value, raw(value), model, model_raw, dataset, dataset_raw, plan, plan_raw)
        self.assertIn("EVALUATION_THRESHOLD_FAILED", {item["code"] for item in result["findings"]})
        self.assertIn("force_p95_abs_ev_per_angstrom", result["observations"]["failed_metrics"])

    def test_missing_ood_slice_and_metric_are_blocked(self) -> None:
        model, model_raw, plan, plan_raw, dataset, dataset_raw = model_chain()
        value = evaluation_record(model_raw, dataset_raw, plan_raw)
        value["slice_coverage"] = ["per_species", "configuration_class"]
        del value["metrics"]["energy_p95_abs_ev_per_atom"]
        codes = {item["code"] for item in guard.audit_evaluation(value, raw(value), model, model_raw, dataset, dataset_raw, plan, plan_raw)["findings"]}
        self.assertTrue({"EVALUATION_SLICE_COVERAGE_MISSING", "EVALUATION_METRICS_INVALID"}.issubset(codes))

    def test_slice_ids_are_frozen_before_evaluation_and_cover_every_species(self) -> None:
        model, model_raw, plan, plan_raw, dataset, dataset_raw = model_chain()
        value = evaluation_record(model_raw, dataset_raw, plan_raw)
        value["slice_metrics"]["per_species"] = [value["slice_metrics"]["per_species"][0]]
        value["slice_metrics"]["configuration_class"][0]["slice_id"] = "selected-after-test"
        value["slice_metrics_sha256"] = guard.sha256(
            json.dumps(value["slice_metrics"], sort_keys=True, separators=(",", ":")).encode()
        )
        result = guard.audit_evaluation(value, raw(value), model, model_raw, dataset, dataset_raw, plan, plan_raw)
        self.assertIn("EVALUATION_SLICE_METRICS_INVALID", {item["code"] for item in result["findings"]})

    def test_inline_slice_metrics_are_hash_bound_and_thresholded(self) -> None:
        model, model_raw, plan, plan_raw, dataset, dataset_raw = model_chain()
        value = evaluation_record(model_raw, dataset_raw, plan_raw)
        value["slice_metrics"]["ood"][0]["metrics"]["force_mae_ev_per_angstrom"] = 0.051
        result = guard.audit_evaluation(value, raw(value), model, model_raw, dataset, dataset_raw, plan, plan_raw)
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("EVALUATION_SLICE_HASH_MISMATCH", codes)
        self.assertIn("EVALUATION_SLICE_THRESHOLD_FAILED", codes)
        self.assertEqual(result["observations"]["slice_threshold_failure_count"], 1)

    def test_threshold_record_must_match_frozen_plan(self) -> None:
        model, model_raw, plan, plan_raw, dataset, dataset_raw = model_chain()
        value = evaluation_record(model_raw, dataset_raw, plan_raw)
        value["thresholds_frozen_sha256"] = "0" * 64
        result = guard.audit_evaluation(value, raw(value), model, model_raw, dataset, dataset_raw, plan, plan_raw)
        self.assertIn("EVALUATION_THRESHOLDS_HASH_MISMATCH", {item["code"] for item in result["findings"]})

    def test_evaluation_evidence_roles_cannot_alias(self) -> None:
        model, model_raw, plan, plan_raw, dataset, dataset_raw = model_chain()
        value = evaluation_record(model_raw, dataset_raw, plan_raw)
        value["evaluator_sha256"] = value["model_audit_sha256"]
        result = guard.audit_evaluation(value, raw(value), model, model_raw, dataset, dataset_raw, plan, plan_raw)
        self.assertIn("EVALUATION_EVIDENCE_ROLE_COLLISION", {item["code"] for item in result["findings"]})


class DeploymentTests(unittest.TestCase):
    def test_valid_envelope_remains_unexecuted_and_needs_trusted_authorization(self) -> None:
        evaluation, evaluation_raw, model, model_raw = evaluation_chain()
        value = deployment_record(evaluation_raw, model_raw)
        result = guard.audit_deployment(value, raw(value), evaluation, evaluation_raw, model, model_raw)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["action_state"], "needs_authorization")
        self.assertEqual(result["claim_ceiling"], "no_positive_claim")

    def test_lineage_species_units_and_adapter_are_exact(self) -> None:
        evaluation, evaluation_raw, model, model_raw = evaluation_chain()
        value = deployment_record(evaluation_raw, model_raw)
        value["model_audit_sha256"] = "0" * 64
        value["species_order"] = ["O", "H"]
        value["adapter_sha256"] = None
        codes = {item["code"] for item in guard.audit_deployment(value, raw(value), evaluation, evaluation_raw, model, model_raw)["findings"]}
        self.assertTrue({"DEPLOYMENT_LINEAGE_MISMATCH", "DEPLOYMENT_SPECIES_OR_UNITS_MISMATCH", "DEPLOYMENT_ADAPTER_INVALID"}.issubset(codes))

    def test_monitor_rollback_pilot_and_authorization_are_fail_closed(self) -> None:
        evaluation, evaluation_raw, model, model_raw = evaluation_chain()
        value = deployment_record(evaluation_raw, model_raw)
        value["monitor"]["fail_action"] = "continue"
        value["rollback_model_sha256"] = model["observations"]["artifact_sha256"]
        value["pilot"]["max_steps"] = 1000001
        value["authorization_decision_sha256"] = None
        codes = {item["code"] for item in guard.audit_deployment(value, raw(value), evaluation, evaluation_raw, model, model_raw)["findings"]}
        self.assertTrue({"DEPLOYMENT_MONITOR_INVALID", "DEPLOYMENT_ROLLBACK_INVALID", "DEPLOYMENT_PILOT_INVALID", "DEPLOYMENT_AUTHORIZATION_OR_LICENSE_MISSING"}.issubset(codes))

    def test_domain_bounds_timestep_and_ensembles_are_bounded(self) -> None:
        evaluation, evaluation_raw, model, model_raw = evaluation_chain()
        value = deployment_record(evaluation_raw, model_raw)
        value["domain"]["temperature_k"] = [400.0, 200.0]
        value["max_timestep_fs"] = 20.0
        value["ensembles"] = ["nvt", "nvt"]
        codes = {item["code"] for item in guard.audit_deployment(value, raw(value), evaluation, evaluation_raw, model, model_raw)["findings"]}
        self.assertTrue({"DEPLOYMENT_DOMAIN_BOUNDS_INVALID", "DEPLOYMENT_TIMESTEP_INVALID", "DEPLOYMENT_ENSEMBLES_INVALID"}.issubset(codes))

    def test_stress_deployment_requires_all_frame_stress_evidence(self) -> None:
        evaluation, evaluation_raw, model, model_raw = evaluation_chain()
        value = deployment_record(evaluation_raw, model_raw)
        value["observables"] = ["energy", "forces", "stress"]
        result = guard.audit_deployment(value, raw(value), evaluation, evaluation_raw, model, model_raw)
        self.assertIn("DEPLOYMENT_STRESS_UNVALIDATED", {item["code"] for item in result["findings"]})

    def test_npt_deployment_requires_evaluated_stress_observable(self) -> None:
        evaluation, evaluation_raw, model, model_raw = evaluation_chain()
        value = deployment_record(evaluation_raw, model_raw)
        value["ensembles"] = ["npt"]
        result = guard.audit_deployment(value, raw(value), evaluation, evaluation_raw, model, model_raw)
        self.assertIn("DEPLOYMENT_NPT_REQUIRES_STRESS", {item["code"] for item in result["findings"]})

    def test_deployment_evidence_roles_cannot_alias(self) -> None:
        evaluation, evaluation_raw, model, model_raw = evaluation_chain()
        value = deployment_record(evaluation_raw, model_raw)
        value["authorization_decision_sha256"] = value["adapter_sha256"]
        result = guard.audit_deployment(value, raw(value), evaluation, evaluation_raw, model, model_raw)
        self.assertIn("DEPLOYMENT_EVIDENCE_ROLE_COLLISION", {item["code"] for item in result["findings"]})


class BoundaryAndCliTests(unittest.TestCase):
    def test_duplicate_keys_and_nonfinite_json_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"a":1,"a":2}', encoding="utf-8")
            with self.assertRaisesRegex(guard.BoundaryError, "duplicate"):
                guard.load_json(path, "TEST")
            path.write_text('{"a":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(guard.BoundaryError, "non-finite"):
                guard.load_json(path, "TEST")

    def test_bom_symlink_and_hardlink_json_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            base = Path(directory)
            bom = base / "bom.json"
            bom.write_bytes(b"\xef\xbb\xbf{}")
            with self.assertRaisesRegex(guard.BoundaryError, "BOM"):
                guard.load_json(bom, "TEST")
            regular = base / "regular.json"
            regular.write_text("{}", encoding="utf-8")
            linked = base / "linked.json"
            linked.symlink_to(regular)
            with self.assertRaisesRegex(guard.BoundaryError, "regular file"):
                guard.load_json(linked, "TEST")
            hard = base / "hard.json"
            os.link(regular, hard)
            with self.assertRaisesRegex(guard.BoundaryError, "hard-linked"):
                guard.load_json(regular, "TEST")

    def test_intermediate_directory_swap_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            base = Path(directory)
            evidence_root = base / "mlp-evidence-root"
            evidence_root.mkdir()
            evidence = evidence_root / "request.json"
            evidence.write_text("{}", encoding="utf-8")
            moved = base / "moved-evidence-root"
            outside = base / "outside"
            outside.mkdir()
            original_open = guard.os.open
            swapped = False

            def swap_after_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
                nonlocal swapped
                descriptor = original_open(path, flags, *args, **kwargs)
                if path == evidence_root.name and kwargs.get("dir_fd") is not None and not swapped:
                    evidence_root.rename(moved)
                    evidence_root.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return descriptor

            try:
                with mock.patch.object(guard.os, "open", side_effect=swap_after_open):
                    with self.assertRaises(guard.BoundaryError):
                        guard.load_json(evidence, "TEST")
            finally:
                if evidence_root.is_symlink():
                    evidence_root.unlink()
                if moved.exists():
                    moved.rename(evidence_root)

    def test_fifo_input_is_rejected_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            fifo = Path(directory) / "request.fifo"
            os.mkfifo(fifo)
            program = (
                "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import mlp_guard as g; "
                "\ntry: g.load_json(Path(sys.argv[2]), 'TEST')\nexcept g.BoundaryError: raise SystemExit(0)\n"
                "raise SystemExit(1)"
            )
            result = subprocess.run(
                [sys.executable, "-B", "-c", program, str(ROOT / "scripts"), str(fifo)],
                check=False,
                timeout=2,
            )
            self.assertEqual(result.returncode, 0)

    def test_existing_output_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "report.json"
            original = b"existing-report\n"
            output.write_bytes(original)
            with self.assertRaisesRegex(guard.BoundaryError, "already exists"):
                guard.write_report(output, {"status": "new"})
            self.assertEqual(output.read_bytes(), original)

    def test_late_output_creation_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "report.json"
            original_link = guard.os.link
            original_open = guard.os.open
            victim = b"concurrent-owner\n"

            def create_target_then_link(source: str, target: str, **kwargs: object) -> None:
                descriptor = original_open(
                    target,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=kwargs["dst_dir_fd"],
                )
                try:
                    os.write(descriptor, victim)
                finally:
                    os.close(descriptor)
                original_link(source, target, **kwargs)

            with mock.patch.object(guard.os, "link", side_effect=create_target_then_link):
                with self.assertRaisesRegex(guard.BoundaryError, "appeared during publication"):
                    guard.write_report(output, {"status": "new"})
            self.assertEqual(output.read_bytes(), victim)

    def test_staging_name_substitution_cannot_publish_attacker_bytes(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            base = Path(directory)
            output = base / "report.json"
            original_link = guard.os.link
            original_open = guard.os.open
            original_unlink = guard.os.unlink

            def substitute_then_link(source: str, target: str, **kwargs: object) -> None:
                directory_fd = kwargs["src_dir_fd"]
                original_unlink(source, dir_fd=directory_fd)
                descriptor = original_open(
                    source,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=directory_fd,
                )
                try:
                    os.write(descriptor, b"attacker-bytes\n")
                finally:
                    os.close(descriptor)
                original_link(source, target, **kwargs)

            with mock.patch.object(guard.os, "link", side_effect=substitute_then_link):
                with self.assertRaisesRegex(guard.BoundaryError, "not the staged payload"):
                    guard.write_report(output, {"status": "trusted"})
            self.assertFalse(output.exists())
            self.assertEqual(list(base.glob(".mlp-guard-*.tmp")), [])

    def test_cli_dataset_and_plan_chain_has_stable_codes(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            base = Path(directory)
            dataset_path = base / "dataset.json"
            dataset_report_path = base / "dataset-audit.json"
            request_path = base / "request.json"
            plan_path = base / "plan.json"
            blocked_plan_path = base / "blocked-plan.json"
            dataset_path.write_text(json.dumps(dataset_manifest()), encoding="utf-8")
            self.assertEqual(guard.main(["audit-dataset", "--manifest", str(dataset_path), "--out", str(dataset_report_path)]), 0)
            dataset_report_raw = dataset_report_path.read_bytes()
            request_path.write_text(json.dumps(training_request(dataset_report_raw)), encoding="utf-8")
            self.assertEqual(guard.main(["plan-training", "--request", str(request_path), "--dataset-audit", str(dataset_report_path), "--out", str(plan_path)]), 0)
            changed = training_request(dataset_report_raw)
            changed["dataset_audit_sha256"] = "0" * 64
            request_path.write_text(json.dumps(changed), encoding="utf-8")
            self.assertEqual(guard.main(["plan-training", "--request", str(request_path), "--dataset-audit", str(dataset_report_path), "--out", str(blocked_plan_path)]), 2)

    def test_source_never_imports_provider_or_deserializes_models(self) -> None:
        source = (ROOT / "scripts" / "mlp_guard.py").read_text(encoding="utf-8")
        for forbidden in ("torch", "pickle", "joblib", "subprocess", "mace", "nequip", "deepmd", "fairchem"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(f"import {forbidden}", source)
        self.assertNotIn("os.replace", source)

    def test_output_cannot_replace_an_evidence_file(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "dataset.json"
            original = json.dumps(dataset_manifest()).encode()
            path.write_bytes(original)
            self.assertEqual(
                guard.main(["audit-dataset", "--manifest", str(path), "--out", str(path)]),
                2,
            )
            self.assertEqual(path.read_bytes(), original)
            alias = Path(directory) / "alias.json"
            os.link(path, alias)
            self.assertEqual(
                guard.main(["audit-dataset", "--manifest", str(path), "--out", str(alias)]),
                2,
            )
            self.assertEqual(path.read_bytes(), original)

    def test_weak_model_decision_table_is_unique_and_never_authorizes(self) -> None:
        table = json.loads((ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8"))
        self.assertEqual(set(table), {"contract_name", "schema_version", "skill_id", "lifecycle", "selection_policy", "default_case_id", "current_claim", "execution_authorized", "promotion_authorized", "cases"})
        self.assertEqual(table["contract_name"], "candidate-decision-table")
        self.assertEqual(table["schema_version"], "1.0")
        self.assertEqual(table["skill_id"], "ml-potential-workflows")
        self.assertEqual(table["lifecycle"], "development")
        self.assertEqual(table["selection_policy"], "first-match-by-ascending-priority")
        self.assertEqual(table["current_claim"], "no_positive_claim")
        self.assertIs(table["execution_authorized"], False)
        self.assertIs(table["promotion_authorized"], False)
        self.assertGreaterEqual(len(table["cases"]), 10)
        ids = [item["case_id"] for item in table["cases"]]
        priorities = [item["priority"] for item in table["cases"]]
        actions = [item["minimum_next_action"] for item in table["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(priorities, list(range(1, len(priorities) + 1)))
        self.assertEqual(len(actions), len(set(actions)))
        for item in table["cases"]:
            self.assertEqual(
                set(item),
                {"case_id", "priority", "severity", "condition", "required_evidence", "finding_codes", "action_state", "expected_exit_codes", "current_claim", "execution_authorized", "promotion_authorized", "minimum_next_action"},
            )
            self.assertEqual(item["current_claim"], "no_positive_claim")
            self.assertIs(item["execution_authorized"], False)
            self.assertIs(item["promotion_authorized"], False)
            self.assertIn(item["action_state"], {"local_gate_blocked", "needs_evidence", "ready_for_deterministic_check", "local_gate_passed_limited"})
            self.assertTrue(item["expected_exit_codes"])
            if item["action_state"] == "local_gate_blocked":
                self.assertTrue(item["finding_codes"])
            self.assertIsInstance(item["minimum_next_action"], str)
            self.assertTrue(item["minimum_next_action"].strip())
        self.assertEqual(table["default_case_id"], ids[-1])
        self.assertEqual(table["cases"][-1]["required_evidence"], [])
        self.assertEqual(table["cases"][-1]["action_state"], "local_gate_blocked")

    def test_reports_do_not_echo_frame_ids_or_source_paths(self) -> None:
        value = dataset_manifest()
        value["frames"][0]["frame_id"] = "private-frame"
        result = guard.audit_dataset(value, raw(value))
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("private-frame", serialized)
        self.assertNotIn("/Users/", serialized)


class OfficialSourceSeedTests(unittest.TestCase):
    def source_inputs(self) -> dict[str, object]:
        return source_scope.load_json(
            ROOT / "references" / "source-pack-inputs.json"
        )

    def generated_json(self, relative: str) -> dict[str, object]:
        return json.loads(
            (source_scope.REPOSITORY_ROOT / relative).read_text(encoding="utf-8")
        )

    def test_generated_outputs_match_canonical_renderer(self) -> None:
        outputs = source_scope.render_outputs()
        self.assertEqual(len(outputs), 10)
        for relative, expected in outputs.items():
            with self.subTest(relative=relative):
                self.assertEqual(
                    (source_scope.REPOSITORY_ROOT / relative).read_bytes(),
                    expected,
                )
        self.assertEqual(source_scope.write_or_check(check=True), ())

    def test_seed_is_multi_provider_hash_bound_and_blocked(self) -> None:
        seed = self.generated_json(
            "skills/ml-potential-workflows/references/source-pack-seed.json"
        )
        self.assertEqual(seed["status_ceiling"], "blocked")
        self.assertEqual(
            seed["scope_extractor_id"],
            "ml-provider-source-scope-v1",
        )
        self.assertEqual(
            [item["input_id"] for item in seed["providers"]],
            [
                "mace-framework",
                "mace-docs",
                "nequip-framework",
                "fairchem-v1",
                "fairchem-v2",
                "uma-models",
                "fairchem-datasets",
            ],
        )
        scope_ref = seed["scope_catalog_ref"]
        scope_raw = (source_scope.REPOSITORY_ROOT / scope_ref["path"]).read_bytes()
        self.assertEqual(scope_ref["sha256"], source_scope.sha256_bytes(scope_raw))
        for provider in seed["providers"]:
            source_ref = provider["source_ref"]
            source_raw = (
                source_scope.REPOSITORY_ROOT / source_ref["path"]
            ).read_bytes()
            self.assertEqual(
                source_ref["sha256"],
                source_scope.sha256_bytes(source_raw),
            )
        self.assertGreaterEqual(len(seed["blockers"]), 6)
        self.assertFalse(
            any(
                "central authority" in blocker.casefold()
                and (
                    "not reviewed" in blocker.casefold()
                    or "not activated" in blocker.casefold()
                )
                for blocker in seed["blockers"]
            )
        )

    def test_every_catalog_is_external_only_and_subject_complete(self) -> None:
        seed = self.generated_json(
            "skills/ml-potential-workflows/references/source-pack-seed.json"
        )
        for provider in seed["providers"]:
            catalog = self.generated_json(provider["source_ref"]["path"])
            declared = set(catalog["subjects"])
            sliced: set[str] = set()
            for source_id, source in catalog["discovered_sources"].items():
                with self.subTest(
                    input_id=provider["input_id"],
                    source_id=source_id,
                ):
                    self.assertNotIn("content_ref", source)
                    content = source["content"]
                    locator = content["locator"].lower()
                    self.assertNotIn("/resolve/", locator)
                    self.assertNotIn("/download/", locator)
                    self.assertFalse(locator.endswith(source_scope.MODEL_SUFFIXES))
                    if source["disposition"] == "excluded":
                        self.assertEqual(content["content_mode"], "excluded")
                        continue
                    self.assertEqual(source["disposition"], "included")
                    self.assertEqual(content["content_mode"], "external-content")
                    self.assertIn("receipt", content)
                    for item in source["selectors"]:
                        self.assertNotIn("content_ref", item)
                        self.assertEqual(item["layer"], "raw-source")
                        self.assertIn("selected_identity", item)
                        sliced.update(item["subject_ids"])
            self.assertEqual(sliced, declared)
            self.assertIs(catalog["upstream_universe_complete"], False)
            self.assertTrue(catalog["blockers"])

    def test_every_catalog_loss_is_exactly_linked_by_affected_source(self) -> None:
        seed = self.generated_json(
            "skills/ml-potential-workflows/references/source-pack-seed.json"
        )
        for provider in seed["providers"]:
            catalog = self.generated_json(provider["source_ref"]["path"])
            expected_by_source = {
                source_id: set()
                for source_id in catalog["discovered_sources"]
            }
            for loss_id, loss in catalog["losses"].items():
                for source_id in loss["affected_source_ids"]:
                    self.assertIn(source_id, expected_by_source)
                    expected_by_source[source_id].add(loss_id)

            for source_id, source in catalog["discovered_sources"].items():
                with self.subTest(
                    input_id=provider["input_id"],
                    source_id=source_id,
                ):
                    if source["disposition"] == "excluded":
                        continue
                    self.assertEqual(len(source["selectors"]), 1)
                    actual = source["selectors"][0].get("loss_ids", [])
                    self.assertEqual(len(actual), len(set(actual)))
                    self.assertEqual(
                        set(actual),
                        expected_by_source[source_id],
                    )

    def test_technical_identity_and_version_boundaries_are_not_collapsed(
        self,
    ) -> None:
        seed = self.generated_json(
            "skills/ml-potential-workflows/references/source-pack-seed.json"
        )
        catalogs = {
            item["input_id"]: self.generated_json(item["source_ref"]["path"])
            for item in seed["providers"]
        }
        self.assertTrue(all("license" not in catalog for catalog in catalogs.values()))
        self.assertNotEqual(
            catalogs["mace-framework"]["inventory_identity"],
            catalogs["mace-docs"]["inventory_identity"],
        )
        self.assertNotEqual(
            catalogs["mace-framework"]["authority_revision"],
            catalogs["mace-docs"]["authority_revision"],
        )
        self.assertNotEqual(
            catalogs["fairchem-v1"]["authority_revision"],
            catalogs["fairchem-v2"]["authority_revision"],
        )
        self.assertEqual(
            catalogs["uma-models"]["provider_id"],
            "fairchem-uma",
        )
        self.assertEqual(
            catalogs["fairchem-datasets"]["provider_id"],
            "fairchem-datasets",
        )

    def test_scope_preserves_separate_artifact_identity_layers(self) -> None:
        scope = self.generated_json(
            "skills/ml-potential-workflows/references/source-pack-scope-catalog.json"
        )
        by_id = {item["subject_id"]: item for item in scope["subjects"]}
        required = {
            "mace.framework.artifact-identity",
            "mace.docs.model.identity.split",
            "nequip.framework.artifact-identity.boundary",
            "fairchem.v1.weights.identity.unknown",
            "fairchem.v2.framework.identity",
            "uma.model.artifact.gated",
            "fairchem.dataset.identities.four-layer",
            "fairchem.reference-dft.restricted-components",
            "ml.boundary.four-rights-records",
        }
        self.assertTrue(required.issubset(by_id))
        official = [
            item
            for item in scope["subjects"]
            if item["evidence_class"] == "official-provider-required"
        ]
        self.assertTrue(official)
        self.assertNotIn("covered", {item["expected_disposition"] for item in official})
        for item in scope["subjects"]:
            if item["evidence_class"] == "official-provider-required":
                self.assertTrue(item["provider_input_ids"])
            else:
                self.assertEqual(item["provider_input_ids"], [])

    def test_authority_proposal_is_machine_readable_and_bundle_forbidden(self) -> None:
        proposal = self.generated_json(
            "skills/ml-potential-workflows/references/source-pack-authority-proposal.json"
        )
        self.assertEqual(proposal["proposal_status"], "review-required")
        self.assertEqual(
            {item["provider_class"] for item in proposal["authorities"]},
            {"software", "model-artifact", "dataset"},
        )
        self.assertEqual(
            {item["consumer_binding"]["input_id"] for item in proposal["authorities"]},
            {
                "mace-framework",
                "mace-docs",
                "nequip-framework",
                "fairchem-v1",
                "fairchem-v2",
                "uma-models",
                "fairchem-datasets",
            },
        )
        for item in proposal["authorities"]:
            self.assertEqual(item["proposed_lifecycle"], "active")
            self.assertEqual(item["storage_policy"]["bundle_content"], "forbidden")
            self.assertEqual(
                item["consumer_binding"]["status_ceiling"],
                "blocked",
            )

    def test_extractor_rejects_embedded_or_checkpoint_sources(self) -> None:
        value = self.source_inputs()
        source = value["providers"][5]["sources"][0]
        source["content_ref"] = {
            "path": "skills/ml-potential-workflows/SKILL.md",
            "sha256": "a" * 64,
            "bytes": 1,
        }
        with self.assertRaisesRegex(
            source_scope.SourceSeedError,
            "external_identity only",
        ):
            source_scope.render_outputs(value)

        value = self.source_inputs()
        value["providers"][5]["sources"][0]["locator"] = (
            "https://huggingface.co/facebook/UMA/blob/main/uma-s-1p2.pt"
        )
        with self.assertRaisesRegex(
            source_scope.SourceSeedError,
            "serialized model bytes",
        ):
            source_scope.render_outputs(value)

    def test_extractor_rejects_duplicate_provider_input(self) -> None:
        value = self.source_inputs()
        value["providers"][1]["input_id"] = value["providers"][0]["input_id"]
        with self.assertRaisesRegex(
            source_scope.SourceSeedError,
            "duplicate identifier",
        ):
            source_scope.render_outputs(value)

    def test_extractor_rejects_nested_or_escaping_catalog_filename(self) -> None:
        for filename in (
            "../source-catalog-escape.json",
            "nested/source-catalog-escape.json",
            "catalog-without-reviewed-prefix.json",
        ):
            with self.subTest(filename=filename):
                value = self.source_inputs()
                value["providers"][0]["catalog_filename"] = filename
                with self.assertRaisesRegex(
                    source_scope.SourceSeedError,
                    "direct references/source-catalog",
                ):
                    source_scope.render_outputs(value)

    def test_extractor_source_has_no_network_provider_or_model_loader(self) -> None:
        source = (
            ROOT / "scripts" / "extract_official_source_scope.py"
        ).read_text(encoding="utf-8")
        self.assertIn("DEVELOPMENT_MAINTENANCE_CHECK_IS_OFFLINE = True", source)
        for forbidden in (
            "import requests",
            "import urllib",
            "import socket",
            "import subprocess",
            "import torch",
            "import pickle",
            "import mace",
            "import nequip",
            "import fairchem",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_check_cli_passes_without_writing(self) -> None:
        self.assertEqual(source_scope.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
