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
import deepmd_guard as guard  # noqa: E402


def hashed(number: int) -> str:
    return f"{number:064x}"


def raw(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def array(name: str, shape: list[int], number: int) -> dict[str, object]:
    return {"name": name, "sha256": hashed(number), "bytes": 1024 + number, "dtype": "float64", "shape": shape}


def system(name: str, split: str, number: int, *, periodic: bool = False, virial: bool = False) -> dict[str, object]:
    nframes = 2
    natoms = 3
    arrays = [
        array("coord.npy", [nframes, natoms, 3], number * 10 + 1),
        array("energy.npy", [nframes], number * 10 + 2),
        array("force.npy", [nframes, natoms, 3], number * 10 + 3),
    ]
    if periodic:
        arrays.append(array("box.npy", [nframes, 3, 3], number * 10 + 4))
    if virial:
        arrays.append(array("virial.npy", [nframes, 9], number * 10 + 5))
    return {
        "system_id": name,
        "group_id": f"group-{name}",
        "split": split,
        "periodic": periodic,
        "nframes": nframes,
        "natoms": natoms,
        "type_raw_sha256": hashed(number * 10 + 6),
        "type_map_raw_sha256": "a" * 64,
        "source_frame_index_sha256": hashed(number * 10 + 7),
        "arrays": arrays,
    }


def layout_manifest(*, periodic: bool = False, virial: bool = False) -> dict[str, object]:
    return {
        "schema_version": "candidate-1.0",
        "deepmd_version": "3.1.3",
        "backend": "pytorch",
        "dataset_id": "synthetic-water",
        "type_map": ["H", "O"],
        "type_map_sha256": "a" * 64,
        "units": copy.deepcopy(guard.UNITS),
        "reference_protocol_sha256": "b" * 64,
        "source_dataset_audit_sha256": "f" * 64,
        "virial_policy": "all_systems" if virial else "absent",
        "licenses": {
            "framework": "LGPL-3.0-only",
            "backend": "BSD-style",
            "dataset": "synthetic-test-data",
            "reference_data": "synthetic-test-data",
        },
        "systems": [
            system("train-system", "train", 1, periodic=periodic, virial=virial),
            system("validation-system", "validation", 2, periodic=periodic, virial=virial),
            system("test-system", "test", 3, periodic=periodic, virial=virial),
            system("ood-system", "ood", 4, periodic=periodic, virial=virial),
        ],
    }


def layout_chain() -> tuple[dict[str, object], bytes]:
    value = layout_manifest()
    result = guard.audit_layout(value, raw(value))
    return result, raw(result)


def config_projection(layout_raw: bytes, *, mode: str = "from_scratch") -> dict[str, object]:
    return {
        "schema_version": "candidate-1.0",
        "deepmd_version": "3.1.3",
        "backend": "pytorch",
        "workflow_id": "water-dp-001",
        "mode": mode,
        "layout_audit_sha256": guard.digest(layout_raw),
        "environment_sha256": "c" * 64,
        "provider_schema_sha256": "d" * 64,
        "type_map": ["H", "O"],
        "training_systems": ["train-system"],
        "validation_systems": ["validation-system"],
        "descriptor": {
            "type": "se_e2_a",
            "rcut": 6.0,
            "rcut_smth": 5.5,
            "sel": [32, 16],
            "neurons": [25, 50, 100],
            "axis_neuron": 16,
            "seed": 1,
        },
        "fitting_net": {"type": "ener", "neurons": [240, 240, 240], "resnet_dt": True, "seed": 2},
        "learning_rate": {"type": "exp", "start": 0.001, "stop": 1e-8, "decay_steps": 5000},
        "loss": {
            "start_energy": 0.02,
            "limit_energy": 1.0,
            "start_force": 1000.0,
            "limit_force": 1.0,
            "start_virial": 0.0,
            "limit_virial": 0.0,
        },
        "training": {
            "seed": 3,
            "numb_steps": 10000,
            "disp_freq": 100,
            "save_freq": 1000,
            "training_batch_size": 1,
            "validation_batch_size": 1,
        },
        "restart_parent_checkpoint_sha256": None if mode == "from_scratch" else "e" * 64,
        "restart_parent_run_audit_sha256": None if mode == "from_scratch" else "6" * 64,
        "evaluation_thresholds": {
            "energy_rmse_ev_per_atom": 0.01,
            "force_rmse_ev_per_angstrom": 0.05,
        },
    }


def config_chain(*, mode: str = "from_scratch") -> tuple[dict[str, object], bytes, dict[str, object], bytes]:
    layout, layout_raw = layout_chain()
    value = config_projection(layout_raw, mode=mode)
    result = guard.audit_config(value, raw(value), layout, layout_raw)
    return result, raw(result), layout, layout_raw


def run_record(config: dict[str, object], config_raw: bytes, layout_raw: bytes) -> dict[str, object]:
    observations = config["observations"]
    return {
        "schema_version": "candidate-1.0",
        "run_id": "water-run-001",
        "deepmd_version": observations["deepmd_version"],
        "backend": observations["backend"],
        "layout_audit_sha256": guard.digest(layout_raw),
        "config_audit_sha256": guard.digest(config_raw),
        "source_dataset_audit_sha256": observations["source_dataset_audit_sha256"],
        "environment_sha256": observations["environment_sha256"],
        "authorization_decision_sha256": "f" * 64,
        "execution_record_sha256": "7" * 64,
        "output_log_sha256": "8" * 64,
        "rendered_config_sha256": "9" * 64,
        "status": "completed",
        "exit_code": 0,
        "final_step": observations["numb_steps"],
        "checkpoint_sha256": "1" * 64,
        "learning_curve_sha256": "2" * 64,
        "nonfinite_detected": False,
        "restart_parent_checkpoint_sha256": observations["restart_parent_checkpoint_sha256"],
        "restart_parent_run_audit_sha256": observations["restart_parent_run_audit_sha256"],
        "metrics": {
            "training_energy_rmse_ev_per_atom": 0.004,
            "validation_energy_rmse_ev_per_atom": 0.006,
            "training_force_rmse_ev_per_angstrom": 0.03,
            "validation_force_rmse_ev_per_angstrom": 0.04,
        },
    }


def run_chain(*, mode: str = "from_scratch") -> tuple[dict[str, object], bytes, dict[str, object], bytes]:
    config, config_raw, layout, layout_raw = config_chain(mode=mode)
    value = run_record(config, config_raw, layout_raw)
    result = guard.audit_run(value, raw(value), config, config_raw, layout, layout_raw)
    return result, raw(result), config, config_raw


def model_manifest(run: dict[str, object], run_raw: bytes, config: dict[str, object], config_raw: bytes) -> dict[str, object]:
    observations = config["observations"]
    return {
        "schema_version": "candidate-1.0",
        "model_id": "water-dp-model-001",
        "deepmd_version": observations["deepmd_version"],
        "backend": observations["backend"],
        "artifact_sha256": "3" * 64,
        "artifact_bytes": 2048,
        "source_checkpoint_sha256": run["observations"]["checkpoint_sha256"],
        "run_audit_sha256": guard.digest(run_raw),
        "config_audit_sha256": guard.digest(config_raw),
        "source_dataset_audit_sha256": observations["source_dataset_audit_sha256"],
        "type_map": observations["type_map"],
        "rcut": observations["rcut"],
        "units": copy.deepcopy(guard.UNITS),
        "energy_reference_convention": "reference-dft-total-energy-v1",
        "rendered_config_sha256": run["observations"]["rendered_config_sha256"],
        "provider_schema_sha256": observations["provider_schema_sha256"],
        "licenses": {
            "framework": "LGPL-3.0-only",
            "backend": "BSD-style",
            "model": "private-model",
            "dataset": "private-data",
        },
        "status": "frozen_unloaded",
    }


class LayoutTests(unittest.TestCase):
    def test_valid_layout_metadata_passes_without_reading_arrays(self) -> None:
        result, _ = layout_chain()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["claim_ceiling"], "no_positive_claim")
        self.assertEqual(result["observations"]["frame_count"], 8)

    def test_version_backend_type_map_and_units_are_exact(self) -> None:
        value = layout_manifest()
        value["deepmd_version"] = "latest"
        value["backend"] = "automatic"
        value["type_map"] = ["O", "H"]
        value["units"]["forces"] = "Ha/bohr"
        codes = {item["code"] for item in guard.audit_layout(value, raw(value))["findings"]}
        self.assertTrue({"LAYOUT_VERSION_BACKEND_INVALID", "LAYOUT_UNITS_INVALID"}.issubset(codes))

    def test_group_leakage_and_missing_ood_are_blocked(self) -> None:
        value = layout_manifest()
        value["systems"][1]["group_id"] = value["systems"][0]["group_id"]
        value["systems"] = [item for item in value["systems"] if item["split"] != "ood"]
        codes = {item["code"] for item in guard.audit_layout(value, raw(value))["findings"]}
        self.assertIn("LAYOUT_GROUP_LEAKAGE", codes)
        self.assertIn("LAYOUT_SPLIT_MISSING", codes)

    def test_array_shape_dtype_set_and_hash_are_fail_closed(self) -> None:
        value = layout_manifest()
        value["systems"][0]["arrays"][0]["shape"] = [2, 9]
        value["systems"][1]["arrays"][1]["dtype"] = "float16"
        value["systems"][2]["arrays"][2]["sha256"] = value["systems"][0]["arrays"][2]["sha256"]
        value["systems"][3]["arrays"].pop()
        value["systems"][0]["arrays"][1]["bytes"] = 1
        codes = {item["code"] for item in guard.audit_layout(value, raw(value))["findings"]}
        self.assertTrue({"LAYOUT_ARRAY_SHAPE_OR_DTYPE_MISMATCH", "LAYOUT_ARRAY_BYTE_COUNT_IMPOSSIBLE", "LAYOUT_ARRAY_IDENTITY_INVALID", "LAYOUT_ARRAY_SET_INVALID"}.issubset(codes))

    def test_periodic_and_virial_policies_require_matching_arrays(self) -> None:
        value = layout_manifest(periodic=True, virial=True)
        passed = guard.audit_layout(value, raw(value))
        self.assertEqual(passed["status"], "pass")
        value["systems"][0]["arrays"] = [item for item in value["systems"][0]["arrays"] if item["name"] != "box.npy"]
        blocked = guard.audit_layout(value, raw(value))
        self.assertIn("LAYOUT_ARRAY_SET_INVALID", {item["code"] for item in blocked["findings"]})

    def test_type_files_protocol_and_license_inventory_are_required(self) -> None:
        value = layout_manifest()
        value["systems"][0]["type_map_raw_sha256"] = "0" * 64
        value["reference_protocol_sha256"] = None
        value["source_dataset_audit_sha256"] = None
        value["systems"][0]["source_frame_index_sha256"] = None
        value["licenses"] = {"framework": "LGPL"}
        codes = {item["code"] for item in guard.audit_layout(value, raw(value))["findings"]}
        self.assertTrue({"LAYOUT_TYPE_FILE_IDENTITY_INVALID", "LAYOUT_REFERENCE_PROTOCOL_INVALID", "LAYOUT_SOURCE_DATASET_AUDIT_INVALID", "LAYOUT_SOURCE_FRAME_INDEX_INVALID", "LAYOUT_LICENSES_INVALID"}.issubset(codes))


class ConfigTests(unittest.TestCase):
    def test_valid_projection_is_explicit_and_needs_external_authorization(self) -> None:
        result, _, _, _ = config_chain()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["action_state"], "needs_authorization")
        self.assertEqual(result["claim_ceiling"], "no_positive_claim")

    def test_layout_hash_version_backend_type_map_and_systems_bind(self) -> None:
        layout, layout_raw = layout_chain()
        value = config_projection(layout_raw)
        value["layout_audit_sha256"] = "0" * 64
        value["backend"] = "jax"
        value["type_map"] = ["O", "H"]
        value["training_systems"] = ["test-system"]
        codes = {item["code"] for item in guard.audit_config(value, raw(value), layout, layout_raw)["findings"]}
        self.assertTrue({"CONFIG_LAYOUT_HASH_MISMATCH", "CONFIG_LAYOUT_IDENTITY_MISMATCH", "CONFIG_SYSTEM_SPLIT_MISMATCH"}.issubset(codes))

    def test_jax_layout_cannot_be_promoted_to_a_training_projection(self) -> None:
        layout_value = layout_manifest()
        layout_value["backend"] = "jax"
        layout = guard.audit_layout(layout_value, raw(layout_value))
        layout_raw = raw(layout)
        value = config_projection(layout_raw)
        value["backend"] = "jax"
        result = guard.audit_config(value, raw(value), layout, layout_raw)
        self.assertIn("CONFIG_BACKEND_TRAINING_UNSUPPORTED", {item["code"] for item in result["findings"]})

    def test_descriptor_fitting_learning_loss_and_training_do_not_default(self) -> None:
        layout, layout_raw = layout_chain()
        value = config_projection(layout_raw)
        value["descriptor"]["sel"] = [32]
        value["fitting_net"]["seed"] = None
        value["learning_rate"]["start"] = 1e-9
        value["loss"]["start_force"] = "auto"
        value["training"]["save_freq"] = 0
        codes = {item["code"] for item in guard.audit_config(value, raw(value), layout, layout_raw)["findings"]}
        self.assertTrue({"CONFIG_DESCRIPTOR_INVALID", "CONFIG_FITTING_INVALID", "CONFIG_LEARNING_RATE_INVALID", "CONFIG_LOSS_INVALID", "CONFIG_TRAINING_INVALID"}.issubset(codes))

    def test_restart_and_thresholds_are_explicit(self) -> None:
        layout, layout_raw = layout_chain()
        value = config_projection(layout_raw)
        value["restart_parent_checkpoint_sha256"] = "e" * 64
        del value["evaluation_thresholds"]["force_rmse_ev_per_angstrom"]
        codes = {item["code"] for item in guard.audit_config(value, raw(value), layout, layout_raw)["findings"]}
        self.assertTrue({"CONFIG_RESTART_LINEAGE_INVALID", "CONFIG_THRESHOLDS_INVALID"}.issubset(codes))
        restart = config_projection(layout_raw, mode="restart")
        self.assertEqual(guard.audit_config(restart, raw(restart), layout, layout_raw)["status"], "pass")

    def test_cadence_cannot_exceed_total_training_steps(self) -> None:
        layout, layout_raw = layout_chain()
        value = config_projection(layout_raw)
        value["training"]["save_freq"] = value["training"]["numb_steps"] + 1
        result = guard.audit_config(value, raw(value), layout, layout_raw)
        self.assertIn("CONFIG_TRAINING_INVALID", {item["code"] for item in result["findings"]})

    def test_forged_minimal_or_reordered_upstream_report_is_rejected(self) -> None:
        layout, layout_raw = layout_chain()
        value = config_projection(layout_raw)
        minimal = {
            "schema_version": "candidate-1.0",
            "contract_name": "deepmd-candidate-audit",
            "command": "audit-layout",
            "candidate_lifecycle": "development",
            "status": "pass",
            "claim_ceiling": "no_positive_claim",
            "findings": [],
        }
        result = guard.audit_config(value, raw(value), minimal, raw(minimal))
        self.assertIn("UPSTREAM_REPORT_INVALID", {item["code"] for item in result["findings"]})
        changed = copy.deepcopy(layout)
        changed["gates"] = list(reversed(changed["gates"]))
        changed_value = config_projection(raw(changed))
        result = guard.audit_config(changed_value, raw(changed_value), changed, raw(changed))
        self.assertIn("UPSTREAM_REPORT_GATES_INVALID", {item["code"] for item in result["findings"]})


class RunTests(unittest.TestCase):
    def test_valid_technical_run_passes_without_implying_test_accuracy(self) -> None:
        result, _, _, _ = run_chain()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["future_gate_ceiling"], "technical_run_gates_only")
        self.assertTrue(any("do not establish" in item for item in result["limitations"]))

    def test_upstream_environment_and_authorization_hashes_are_exact(self) -> None:
        config, config_raw, layout, layout_raw = config_chain()
        value = run_record(config, config_raw, layout_raw)
        value["config_audit_sha256"] = "0" * 64
        value["environment_sha256"] = "1" * 64
        value["authorization_decision_sha256"] = None
        codes = {item["code"] for item in guard.audit_run(value, raw(value), config, config_raw, layout, layout_raw)["findings"]}
        self.assertTrue({"RUN_UPSTREAM_HASH_MISMATCH", "RUN_AUTHORIZATION_OR_EXECUTION_RECORD_MISSING"}.issubset(codes))

    def test_completion_nonfinite_final_step_and_artifacts_fail_closed(self) -> None:
        config, config_raw, layout, layout_raw = config_chain()
        value = run_record(config, config_raw, layout_raw)
        value["exit_code"] = False
        value["final_step"] -= 1
        value["nonfinite_detected"] = True
        value["checkpoint_sha256"] = None
        codes = {item["code"] for item in guard.audit_run(value, raw(value), config, config_raw, layout, layout_raw)["findings"]}
        self.assertTrue({"RUN_COMPLETION_INVALID", "RUN_ARTIFACT_IDENTITY_INVALID"}.issubset(codes))

    def test_restart_parent_and_all_finite_metrics_are_required(self) -> None:
        config, config_raw, layout, layout_raw = config_chain(mode="restart")
        value = run_record(config, config_raw, layout_raw)
        value["restart_parent_checkpoint_sha256"] = "0" * 64
        value["restart_parent_run_audit_sha256"] = "0" * 64
        del value["metrics"]["validation_force_rmse_ev_per_angstrom"]
        codes = {item["code"] for item in guard.audit_run(value, raw(value), config, config_raw, layout, layout_raw)["findings"]}
        self.assertTrue({"RUN_RESTART_LINEAGE_MISMATCH", "RUN_METRICS_INVALID"}.issubset(codes))

    def test_run_record_cannot_reuse_one_hash_for_distinct_evidence_roles(self) -> None:
        config, config_raw, layout, layout_raw = config_chain()
        value = run_record(config, config_raw, layout_raw)
        value["execution_record_sha256"] = value["authorization_decision_sha256"]
        result = guard.audit_run(value, raw(value), config, config_raw, layout, layout_raw)
        self.assertIn("RUN_EVIDENCE_ROLE_COLLISION", {item["code"] for item in result["findings"]})


class ModelTests(unittest.TestCase):
    def test_valid_frozen_model_stays_unloaded_and_needs_evaluation(self) -> None:
        run, run_raw, config, config_raw = run_chain()
        value = model_manifest(run, run_raw, config, config_raw)
        result = guard.audit_model(value, raw(value), run, run_raw, config, config_raw)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["action_state"], "needs_authorization")
        self.assertTrue(any("never opened" in item for item in result["limitations"]))

    def test_model_lineage_artifact_and_config_identity_mutations_block(self) -> None:
        run, run_raw, config, config_raw = run_chain()
        value = model_manifest(run, run_raw, config, config_raw)
        value["run_audit_sha256"] = "0" * 64
        value["artifact_sha256"] = None
        value["source_checkpoint_sha256"] = "0" * 64
        value["source_dataset_audit_sha256"] = "0" * 64
        value["type_map"] = ["O", "H"]
        value["provider_schema_sha256"] = "1" * 64
        codes = {item["code"] for item in guard.audit_model(value, raw(value), run, run_raw, config, config_raw)["findings"]}
        self.assertTrue({"MODEL_LINEAGE_MISMATCH", "MODEL_DATASET_LINEAGE_MISMATCH", "MODEL_CHECKPOINT_LINEAGE_MISMATCH", "MODEL_ARTIFACT_IDENTITY_INVALID", "MODEL_CONFIG_IDENTITY_MISMATCH", "MODEL_PROVIDER_CONFIG_OR_SCHEMA_INVALID"}.issubset(codes))

    def test_units_energy_convention_and_license_roles_are_required(self) -> None:
        run, run_raw, config, config_raw = run_chain()
        value = model_manifest(run, run_raw, config, config_raw)
        value["units"]["virial"] = "eV/angstrom^3"
        value["energy_reference_convention"] = ""
        value["licenses"] = {"framework": "LGPL"}
        codes = {item["code"] for item in guard.audit_model(value, raw(value), run, run_raw, config, config_raw)["findings"]}
        self.assertTrue({"MODEL_UNITS_OR_ENERGY_CONVENTION_INVALID", "MODEL_LICENSES_INVALID"}.issubset(codes))

    def test_model_manifest_cannot_reuse_checkpoint_as_frozen_artifact(self) -> None:
        run, run_raw, config, config_raw = run_chain()
        value = model_manifest(run, run_raw, config, config_raw)
        value["artifact_sha256"] = value["source_checkpoint_sha256"]
        result = guard.audit_model(value, raw(value), run, run_raw, config, config_raw)
        self.assertIn("MODEL_EVIDENCE_ROLE_COLLISION", {item["code"] for item in result["findings"]})


class BoundaryAndCliTests(unittest.TestCase):
    def test_duplicate_and_nonfinite_json_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"x":1,"x":2}', encoding="utf-8")
            with self.assertRaisesRegex(guard.BoundaryError, "duplicate"):
                guard.read_json(path, "TEST")
            path.write_text('{"x":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(guard.BoundaryError, "non-finite"):
                guard.read_json(path, "TEST")

    def test_bom_symlink_and_hardlink_json_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            base = Path(directory)
            bom = base / "bom.json"
            bom.write_bytes(b"\xef\xbb\xbf{}")
            with self.assertRaisesRegex(guard.BoundaryError, "BOM"):
                guard.read_json(bom, "TEST")
            regular = base / "regular.json"
            regular.write_text("{}", encoding="utf-8")
            linked = base / "linked.json"
            linked.symlink_to(regular)
            with self.assertRaisesRegex(guard.BoundaryError, "regular file"):
                guard.read_json(linked, "TEST")
            hard = base / "hard.json"
            os.link(regular, hard)
            with self.assertRaisesRegex(guard.BoundaryError, "hard-linked"):
                guard.read_json(regular, "TEST")

    def test_intermediate_directory_swap_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            base = Path(directory)
            evidence_root = base / "deepmd-evidence-root"
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
                        guard.read_json(evidence, "TEST")
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
                "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import deepmd_guard as g; "
                "\ntry: g.read_json(Path(sys.argv[2]), 'TEST')\nexcept g.BoundaryError: raise SystemExit(0)\n"
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
                guard.write_json(output, {"status": "new"})
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
                    guard.write_json(output, {"status": "new"})
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
                    guard.write_json(output, {"status": "trusted"})
            self.assertFalse(output.exists())
            self.assertEqual(list(base.glob(".deepmd-guard-*.tmp")), [])

    def test_cli_layout_config_chain_has_stable_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            base = Path(directory)
            layout_path = base / "layout.json"
            layout_report = base / "layout-audit.json"
            projection_path = base / "projection.json"
            config_report = base / "config-audit.json"
            blocked_config_report = base / "blocked-config-audit.json"
            layout_path.write_text(json.dumps(layout_manifest()), encoding="utf-8")
            self.assertEqual(guard.main(["audit-layout", "--manifest", str(layout_path), "--out", str(layout_report)]), 0)
            projection_path.write_text(json.dumps(config_projection(layout_report.read_bytes())), encoding="utf-8")
            self.assertEqual(guard.main(["audit-config", "--projection", str(projection_path), "--layout-audit", str(layout_report), "--out", str(config_report)]), 0)
            changed = config_projection(layout_report.read_bytes())
            changed["backend"] = "automatic"
            projection_path.write_text(json.dumps(changed), encoding="utf-8")
            self.assertEqual(guard.main(["audit-config", "--projection", str(projection_path), "--layout-audit", str(layout_report), "--out", str(blocked_config_report)]), 2)

    def test_source_never_imports_or_executes_provider_payloads(self) -> None:
        source = (ROOT / "scripts" / "deepmd_guard.py").read_text(encoding="utf-8")
        for forbidden in ("import numpy", "import deepmd", "import torch", "import tensorflow", "pickle", "subprocess"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertNotIn("os.replace", source)

    def test_output_cannot_replace_an_evidence_file(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "layout.json"
            original = json.dumps(layout_manifest()).encode()
            path.write_bytes(original)
            self.assertEqual(
                guard.main(["audit-layout", "--manifest", str(path), "--out", str(path)]),
                2,
            )
            self.assertEqual(path.read_bytes(), original)
            alias = Path(directory) / "alias.json"
            os.link(path, alias)
            self.assertEqual(
                guard.main(["audit-layout", "--manifest", str(path), "--out", str(alias)]),
                2,
            )
            self.assertEqual(path.read_bytes(), original)

    def test_weak_model_decision_table_is_unique_and_never_authorizes(self) -> None:
        table = json.loads((ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8"))
        self.assertEqual(set(table), {"contract_name", "schema_version", "skill_id", "lifecycle", "selection_policy", "default_case_id", "current_claim", "execution_authorized", "promotion_authorized", "cases"})
        self.assertEqual(table["contract_name"], "candidate-decision-table")
        self.assertEqual(table["schema_version"], "1.0")
        self.assertEqual(table["skill_id"], "deepmd-rigorous-workflows")
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

    def test_reports_never_echo_system_paths_or_array_content(self) -> None:
        value = layout_manifest()
        result = guard.audit_layout(value, raw(value))
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("coord.npy", serialized)
        self.assertNotIn("/Users/", serialized)


class ProviderWorkflowCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads(
            (ROOT / "references" / "workflow-catalog.json").read_text(encoding="utf-8")
        )
        self.recipe_book = json.loads(
            (ROOT / "references" / "workflow-recipes.json").read_text(encoding="utf-8")
        )

    def test_provider_versions_sources_and_entries_are_traceable(self) -> None:
        self.assertEqual(self.catalog["catalog_contract"], "provider-workflow-catalog@1.0")
        providers = {item["provider_id"]: item for item in self.catalog["providers"]}
        self.assertEqual(
            {key: value["version"] for key, value in providers.items()},
            {"deepmd-kit": "3.1.3", "dpdata": "1.0.2", "dpgen": "0.13.3"},
        )
        sources = [source for provider in providers.values() for source in provider["sources"]]
        source_ids = [item["source_id"] for item in sources]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        entries = self.catalog["entries"]
        entry_ids = [item["entry_id"] for item in entries]
        self.assertEqual(len(entry_ids), len(set(entry_ids)))
        self.assertGreaterEqual(len(entries), 20)
        for item in entries:
            self.assertIn(item["provider_id"], providers)
            self.assertEqual(item["state"], "listed")
            self.assertTrue(set(item["source_ids"]).issubset(source_ids))

    def test_native_validation_is_explicitly_not_run(self) -> None:
        native = self.catalog["native_validation"]
        self.assertEqual(native["state"], "native-not-run")
        self.assertEqual(native["executables_found"], [])
        self.assertEqual(native["distributions_found"], [])
        self.assertEqual(native["probes_attempted"], [])

    def test_every_concrete_catalog_recipe_resolves_and_never_authorizes(self) -> None:
        recipes = self.recipe_book["recipes"]
        recipe_ids = [item["recipe_id"] for item in recipes]
        self.assertEqual(len(recipe_ids), len(set(recipe_ids)))
        source_ids = {
            source["source_id"]
            for provider in self.catalog["providers"]
            for source in provider["sources"]
        }
        required = {
            "recipe_id", "provider_id", "provider_version", "operation", "state",
            "execution_authorized", "preconditions", "steps", "restart", "units",
            "failure_modes", "scientific_checks", "source_ids",
        }
        for item in recipes:
            self.assertEqual(set(item), required)
            self.assertEqual(item["state"], "official-recipe")
            self.assertIs(item["execution_authorized"], False)
            self.assertTrue(item["preconditions"])
            self.assertTrue(item["steps"])
            self.assertTrue(item["failure_modes"])
            self.assertTrue(item["scientific_checks"])
            self.assertTrue(set(item["source_ids"]).issubset(source_ids))
            for step in item["steps"]:
                self.assertTrue(step.get("outputs"))
        known = set(recipe_ids)
        for entry in self.catalog["entries"]:
            if entry["recipe_id"] is None:
                self.assertTrue(entry.get("gap"))
            else:
                self.assertIn(entry["recipe_id"], known)

    def test_pytorch_install_does_not_confuse_tensorflow_cpu_extra(self) -> None:
        by_id = {item["recipe_id"]: item for item in self.recipe_book["recipes"]}
        recipe = by_id["deepmd.install.pytorch-cpu-pip@3.1.3"]
        argvs = [step["argv"] for step in recipe["steps"]]
        self.assertEqual(
            argvs[0],
            ["python", "-m", "pip", "install", "torch", "--index-url", "https://download.pytorch.org/whl/cpu"],
        )
        self.assertEqual(argvs[1], ["python", "-m", "pip", "install", "deepmd-kit==3.1.3"])
        self.assertIn(["dp", "--pt", "-h"], argvs)
        self.assertNotIn("deepmd-kit[cpu]==3.1.3", json.dumps(recipe, sort_keys=True))

    def test_schema_and_mixed_format_routes_are_exact(self) -> None:
        by_id = {item["recipe_id"]: item for item in self.recipe_book["recipes"]}
        self.assertEqual(
            by_id["deepmd.schema.training-input@3.1.3"]["steps"][0]["argv"],
            ["dp", "--pt", "doc-train-input", "--out-type", "json_schema"],
        )
        sources = {
            source["source_id"]: source["url"]
            for provider in self.catalog["providers"]
            for source in provider["sources"]
        }
        self.assertEqual(
            sources["dpdata-mixed"],
            "https://docs.deepmodeling.com/projects/dpdata/en/stable/formats/DeePMDMixedFormat.html",
        )


if __name__ == "__main__":
    unittest.main()
