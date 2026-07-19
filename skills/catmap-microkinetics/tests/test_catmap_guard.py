from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
GUARD_SPEC = importlib.util.spec_from_file_location(
    "vibe_dft_catmap_candidate_guard",
    ROOT / "scripts" / "catmap_guard.py",
)
if GUARD_SPEC is None or GUARD_SPEC.loader is None:
    raise RuntimeError("CatMAP candidate guard module could not be loaded")
guard = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_SPEC.loader.exec_module(guard)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CatmapGuardTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        for source in FIXTURES.iterdir():
            if source.is_file():
                shutil.copyfile(source, self.base / source.name)
        self.request_path = self.base / "audit-request-pass.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def request(self) -> dict:
        return json.loads(self.request_path.read_text(encoding="utf-8"))

    def artifact_value(self, role: str) -> dict:
        return json.loads((self.base / f"{role}.json").read_text(encoding="utf-8"))

    def write_artifact(self, request: dict, role: str, value: dict) -> str:
        entry = next(item for item in request["artifacts"] if item["role"] == role)
        path = self.base / entry["file"]
        path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        entry["sha256"] = digest(path)
        return entry["sha256"]

    def select_task(self, request: dict, task: str, roles: set[str], claims: list[str]) -> None:
        request["task_id"] = task
        request["artifacts"] = [item for item in request["artifacts"] if item["role"] in roles]
        request["requested_claims"] = claims

    def audit(self, request: dict | None = None) -> tuple[dict, int]:
        return guard.audit_request(request if request is not None else self.request(), self.request_path)

    def test_full_synthetic_package_passes(self) -> None:
        report, exit_code = self.audit()
        self.assertEqual(exit_code, guard.EXIT_OK)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["maturity"], "synthetic-validated")
        self.assertEqual(report["maximum_claim"], "no_positive_claim")
        self.assertEqual(set(report["gates"].values()), {"pass"})
        self.assertEqual(report["metrics"]["network"]["maximum_element_balance_error"], 0.0)

    def test_report_is_deterministic(self) -> None:
        first, first_exit = self.audit()
        second, second_exit = self.audit()
        self.assertEqual(first_exit, second_exit)
        self.assertEqual(first, second)

    def test_network_task_does_not_claim_solver_evidence(self) -> None:
        request = self.request()
        self.select_task(request, "network-audit", {"network"}, ["network-balance"])
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_OK)
        self.assertEqual(report["gates"]["network"], "pass")
        self.assertEqual(report["gates"]["solver"], "not_evaluated")

    def test_element_imbalance_fails(self) -> None:
        request = self.request()
        self.select_task(request, "network-audit", {"network"}, ["network-balance"])
        network = self.artifact_value("network")
        next(item for item in network["species"] if item["id"] == "P_star")["composition"]["X"] = 2
        self.write_artifact(request, "network", network)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.NETWORK.ELEMENT_IMBALANCE", {item["code"] for item in report["findings"]})

    def test_site_imbalance_fails(self) -> None:
        request = self.request()
        self.select_task(request, "network-audit", {"network"}, ["network-balance"])
        network = self.artifact_value("network")
        next(item for item in network["reactions"] if item["id"] == "r1")["stoichiometry"]["star"] = -2
        self.write_artifact(request, "network", network)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.NETWORK.SITE_IMBALANCE", {item["code"] for item in report["findings"]})

    def test_unsupported_units_fail(self) -> None:
        request = self.request()
        self.select_task(
            request,
            "thermochemistry-audit",
            {"network", "thermochemistry"},
            ["network-balance", "thermochemistry-consistency"],
        )
        thermo = self.artifact_value("thermochemistry")
        thermo["units"]["energy"] = "kJ mol^-1"
        self.write_artifact(request, "thermochemistry", thermo)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.UNITS.UNSUPPORTED", {item["code"] for item in report["findings"]})

    def test_missing_species_energy_fails(self) -> None:
        request = self.request()
        self.select_task(
            request,
            "thermochemistry-audit",
            {"network", "thermochemistry"},
            ["thermochemistry-consistency"],
        )
        thermo = self.artifact_value("thermochemistry")
        del thermo["species_free_energies_eV"]["P_star"]
        self.write_artifact(request, "thermochemistry", thermo)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.THERMO.ENERGY_MISSING", {item["code"] for item in report["findings"]})

    def test_barrier_cycle_inconsistency_fails(self) -> None:
        request = self.request()
        self.select_task(
            request,
            "thermochemistry-audit",
            {"network", "thermochemistry"},
            ["thermochemistry-consistency"],
        )
        thermo = self.artifact_value("thermochemistry")
        next(item for item in thermo["barriers"] if item["reaction_id"] == "r2")["reverse_barrier_eV"] = 0.1
        self.write_artifact(request, "thermochemistry", thermo)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.THERMO.BARRIER_INCONSISTENT", {item["code"] for item in report["findings"]})

    def test_solver_nonconvergence_fails(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        result["solver"]["converged"] = False
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.SOLVER.NOT_CONVERGED", {item["code"] for item in report["findings"]})

    def test_solver_tolerance_cannot_be_changed_afterward(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        result["solver"]["residual_tolerance"] = 1e-06
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.SOLVER.RESIDUAL_EXCEEDED", {item["code"] for item in report["findings"]})

    def test_coverage_bounds_fail(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        result["points"][0]["coverages"]["I_star"] = -0.1
        result["points"][0]["coverages"]["star"] = 0.9
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.COVERAGE.BOUNDS_FAILED", {item["code"] for item in report["findings"]})

    def test_site_closure_fails(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        result["points"][0]["coverages"]["star"] = 0.4
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.COVERAGE.SITE_CLOSURE_FAILED", {item["code"] for item in report["findings"]})

    def test_surface_species_rate_residual_fails(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        result["points"][0]["elementary_rates"]["r2"] = 0.04
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.RATE.SPECIES_RESIDUAL_FAILED", {item["code"] for item in report["findings"]})

    def test_one_scale_sensitivity_fails(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        result["sensitivity"]["perturbations_eV"] = [0.01]
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.SENSITIVITY.EVIDENCE_INCOMPLETE", {item["code"] for item in report["findings"]})

    def test_uncertainty_interval_order_fails(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        interval = result["uncertainty"]["output_intervals"]["tof:P_g"]
        interval["q05"] = 0.07
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.UNCERTAINTY.EVIDENCE_INCOMPLETE", {item["code"] for item in report["findings"]})

    def test_lineage_hash_mismatch_fails(self) -> None:
        request = self.request()
        next(item for item in request["artifacts"] if item["role"] == "network")["sha256"] = "f" * 64
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.LINEAGE.HASH_MISMATCH", {item["code"] for item in report["findings"]})

    def test_malformed_artifact_uses_parse_exit(self) -> None:
        request = self.request()
        network_path = self.base / "network.json"
        network_path.write_text("{\n", encoding="utf-8")
        next(item for item in request["artifacts"] if item["role"] == "network")["sha256"] = digest(network_path)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_PARSE)
        self.assertEqual(report["status"], "parse_failed")
        self.assertIn("CAT.PARSER.ARTIFACT_UNSUPPORTED", {item["code"] for item in report["findings"]})

    def test_malformed_result_point_fails_closed_with_report(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        result["points"] = [{}]
        self.write_artifact(request, "result", result)
        self.request_path.write_text(
            json.dumps(request, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        output = self.base / "malformed-point-report.json"

        exit_code = guard.main(
            ["audit", "--request", str(self.request_path), "--output", str(output)]
        )

        self.assertEqual(exit_code, guard.EXIT_INPUT)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "invalid_input")
        self.assertIn(
            "CAT.INPUT.CONTRACT_INVALID",
            {item["code"] for item in report["findings"]},
        )

    def test_native_mkm_input_is_rejected(self) -> None:
        request = self.request()
        request["artifacts"][0]["file"] = "model.mkm"
        with self.assertRaises(guard.GuardError) as context:
            self.audit(request)
        self.assertEqual(context.exception.code, "CAT.INPUT.NATIVE_FORMAT_FORBIDDEN")

    def test_private_path_and_secret_key_are_rejected(self) -> None:
        request = self.request()
        request["artifacts"][0]["file"] = "/private/model.json"
        with self.assertRaises(guard.GuardError) as path_context:
            self.audit(request)
        self.assertEqual(path_context.exception.code, "CAT.INPUT.PRIVACY_VIOLATION")
        request = self.request()
        request["token"] = "synthetic-secret"
        with self.assertRaises(guard.GuardError) as secret_context:
            self.audit(request)
        self.assertEqual(secret_context.exception.code, "CAT.INPUT.PRIVACY_VIOLATION")
        self.assertNotIn("synthetic-secret", secret_context.exception.message)

    def test_duplicate_json_key_is_rejected(self) -> None:
        path = self.base / "duplicate.json"
        path.write_text('{"task_id":"a","task_id":"b"}\n', encoding="utf-8")
        with self.assertRaises(guard.GuardError) as context:
            guard.load_json_object(path)
        self.assertEqual(context.exception.code, "CAT.INPUT.CONTRACT_INVALID")

    def test_utf8_bom_json_is_rejected(self) -> None:
        path = self.base / "bom.json"
        path.write_bytes(b"\xef\xbb\xbf{}\n")
        with self.assertRaises(guard.GuardError) as context:
            guard.load_json_object(path)
        self.assertEqual(context.exception.code, "CAT.INPUT.CONTRACT_INVALID")

    def test_nonfinite_json_number_is_rejected(self) -> None:
        path = self.base / "nan.json"
        path.write_text('{"value":NaN}\n', encoding="utf-8")
        with self.assertRaises(guard.GuardError) as context:
            guard.load_json_object(path)
        self.assertEqual(context.exception.code, "CAT.INPUT.CONTRACT_INVALID")

    def test_oversized_json_is_rejected(self) -> None:
        path = self.base / "oversized.json"
        path.write_bytes(b"{" + b" " * guard.MAX_JSON_BYTES)
        with self.assertRaises(guard.GuardError) as context:
            guard.load_json_object(path)
        self.assertEqual(context.exception.code, "CAT.INPUT.CONTRACT_INVALID")

    def test_symlink_artifact_is_rejected_through_audit(self) -> None:
        request = self.request()
        original = self.base / "network.json"
        target = self.base / "network-target.json"
        target.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(target.name)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_INPUT)
        self.assertIn("CAT.INPUT.CONTRACT_INVALID", {item["code"] for item in report["findings"]})

    def test_hardlink_artifact_is_rejected_through_audit(self) -> None:
        request = self.request()
        original = self.base / "network.json"
        target = self.base / "network-target.json"
        original.rename(target)
        os.link(target, original)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_INPUT)
        self.assertIn("CAT.INPUT.CONTRACT_INVALID", {item["code"] for item in report["findings"]})

    def test_file_change_during_read_is_rejected(self) -> None:
        target = self.base / "changing.json"
        target.write_text("{}\n", encoding="utf-8")
        moved = self.base / "changing-original.json"
        original_read = guard.os.read
        changed = False

        def changing_read(descriptor: int, size: int) -> bytes:
            nonlocal changed
            value = original_read(descriptor, size)
            if value and not changed:
                target.rename(moved)
                target.write_text("{}\n", encoding="utf-8")
                changed = True
            return value

        with mock.patch.object(guard.os, "read", changing_read):
            with self.assertRaises(guard.GuardError) as context:
                guard.load_json_object(target)
        self.assertEqual(context.exception.code, "CAT.INPUT.CONTRACT_INVALID")

    def test_hardlink_created_during_read_is_rejected(self) -> None:
        target = self.base / "read-time-hardlink.json"
        target.write_text("{}\n", encoding="utf-8")
        alias = self.base / "read-time-hardlink-alias.json"
        original_read = guard.os.read
        linked = False

        def linking_read(descriptor: int, size: int) -> bytes:
            nonlocal linked
            value = original_read(descriptor, size)
            if value and not linked:
                os.link(target, alias)
                linked = True
            return value

        with mock.patch.object(guard.os, "read", linking_read):
            with self.assertRaises(guard.GuardError) as context:
                guard.load_json_object(target)
        self.assertEqual(context.exception.code, "CAT.INPUT.CONTRACT_INVALID")

    def test_intermediate_directory_symlink_swap_is_rejected(self) -> None:
        subdirectory = self.base / "sub"
        subdirectory.mkdir()
        evidence = subdirectory / "evidence.json"
        evidence.write_text("{}\n", encoding="utf-8")
        moved = self.base / "sub-original"
        outside = self.base / "outside"
        outside.mkdir()
        (outside / evidence.name).write_text('{"outside":true}\n', encoding="utf-8")
        original_open = guard.os.open
        swapped = False

        def racing_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            nonlocal swapped
            if path == "sub" and kwargs.get("dir_fd") is not None and not swapped:
                subdirectory.rename(moved)
                subdirectory.symlink_to(outside, target_is_directory=True)
                swapped = True
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(guard.os, "open", racing_open):
            with self.assertRaises(guard.GuardError):
                guard.read_relative_regular_bytes(self.base, "sub/evidence.json")

    def test_request_bytes_and_evidence_share_one_stable_root(self) -> None:
        root = self.base / "stable-root"
        root.mkdir()
        request = root / "request.json"
        request.write_text("{}\n", encoding="utf-8")
        (root / "evidence.json").write_text("{}\n", encoding="utf-8")
        tracker = guard.InputTracker()
        guard.load_json_object(request, tracker, retain_parent=True)
        moved = self.base / "stable-root-original"
        root.rename(moved)
        root.mkdir()
        (root / "evidence.json").write_text('{"replacement":true}\n', encoding="utf-8")
        try:
            with self.assertRaises(guard.GuardError):
                guard.read_relative_regular_bytes(root, "evidence.json", tracker)
        finally:
            tracker.close()

    def test_fifo_input_is_rejected_without_blocking(self) -> None:
        fifo = self.base / "blocked.json"
        os.mkfifo(fifo)
        previous_handler = signal.signal(signal.SIGALRM, lambda _signum, _frame: (_ for _ in ()).throw(TimeoutError()))
        signal.setitimer(signal.ITIMER_REAL, 1.0)
        try:
            with self.assertRaises(guard.GuardError):
                guard.load_json_object(fifo)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            signal.signal(signal.SIGALRM, previous_handler)

    def test_result_hash_update_cannot_detach_model_lineage(self) -> None:
        request = self.request()
        thermo = self.artifact_value("thermochemistry")
        thermo["reference_state"]["description"] = "synthetic-reissued-reference"
        self.write_artifact(request, "thermochemistry", thermo)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.LINEAGE.HASH_MISMATCH", {item["code"] for item in report["findings"]})

    def test_solver_self_reported_pass_with_failed_trial_fails(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        self.assertTrue(result["solver"]["converged"])
        result["solver"]["initialization_trials"][1]["converged"] = False
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn(
            "CAT.SOLVER.MULTISTART_INCONSISTENT",
            {item["code"] for item in report["findings"]},
        )

    def test_multiple_initial_states_with_competing_coverages_fail(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        trial = result["solver"]["initialization_trials"][1]
        trial["final_coverages"]["P_star"] = 0.25
        trial["final_coverages"]["star"] = 0.45
        trial["solution_fingerprint"] = guard.coverage_fingerprint(trial["final_coverages"])
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn(
            "CAT.SOLVER.MULTISTART_INCONSISTENT",
            {item["code"] for item in report["findings"]},
        )

    def test_rate_normalization_mismatch_fails(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        result["rate_normalization"]["site_id"] = "unknown-site"
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.RATE.NORMALIZATION_INVALID", {item["code"] for item in report["findings"]})

    def test_calibration_evaluation_leakage_fails_even_with_matching_hash(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        partition = result["data_partition"]
        partition["evaluation_data_ids"] = list(partition["calibration_data_ids"])
        partition["declared_overlap_count"] = 1
        canonical = json.dumps(
            {
                "calibration_data_ids": sorted(partition["calibration_data_ids"]),
                "evaluation_data_ids": sorted(partition["evaluation_data_ids"]),
                "purpose": partition["purpose"],
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        partition["partition_sha256"] = hashlib.sha256(canonical).hexdigest()
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.DATA.PARTITION_LEAKAGE", {item["code"] for item in report["findings"]})

    def test_sensitivity_branch_detachment_fails(self) -> None:
        request = self.request()
        result = self.artifact_value("result")
        result["sensitivity"]["branch_identity"] = "detached-branch"
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn(
            "CAT.SENSITIVITY.EVIDENCE_INCOMPLETE",
            {item["code"] for item in report["findings"]},
        )

    def test_unique_steady_state_claim_is_blocked(self) -> None:
        request = self.request()
        request["requested_claims"].append("unique-steady-state")
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_BLOCKED)
        self.assertIn(
            "CAT.CLAIM.MECHANISM_AUTOMATION_FORBIDDEN",
            {item["code"] for item in report["findings"]},
        )

    def test_each_task_profile_has_a_passing_mechanical_route(self) -> None:
        claims = {
            "network-audit": ["network-balance"],
            "thermochemistry-audit": ["network-balance", "thermochemistry-consistency"],
            "steady-state-audit": [
                "network-balance",
                "thermochemistry-consistency",
                "steady-state-solution",
                "coverage",
                "elementary-rates",
            ],
            "sensitivity-audit": [
                "network-balance",
                "thermochemistry-consistency",
                "steady-state-solution",
                "coverage",
                "elementary-rates",
                "sensitivity-coefficients",
            ],
            "uncertainty-audit": [
                "network-balance",
                "thermochemistry-consistency",
                "steady-state-solution",
                "coverage",
                "elementary-rates",
                "uncertainty-intervals",
            ],
            "microkinetic-package-audit": sorted(guard.ALLOWED_CLAIMS),
        }
        for task, requested_claims in claims.items():
            with self.subTest(task=task):
                request = self.request()
                self.select_task(request, task, set(guard.TASK_ARTIFACTS[task]), requested_claims)
                report, exit_code = self.audit(request)
                self.assertEqual(exit_code, guard.EXIT_OK)
                self.assertEqual(report["status"], "passed")

    def test_task_profile_rejects_ignored_extra_artifacts(self) -> None:
        request = self.request()
        request["task_id"] = "network-audit"
        request["requested_claims"] = ["network-balance"]
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("CAT.TASK.EVIDENCE_UNEXPECTED", {item["code"] for item in report["findings"]})

    def test_mechanism_claim_is_blocked(self) -> None:
        request = self.request()
        request["requested_claims"].append("rate-determining-step")
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_BLOCKED)
        self.assertEqual(report["status"], "blocked_external_evidence")
        self.assertEqual(report["maximum_claim"], "no_positive_claim")

    def test_real_artifact_route_stays_blocked(self) -> None:
        request = self.request()
        request["evidence_class"] = "real-artifact"
        network = self.artifact_value("network")
        network["evidence_class"] = "real-artifact"
        network_hash = self.write_artifact(request, "network", network)
        thermo = self.artifact_value("thermochemistry")
        thermo["evidence_class"] = "real-artifact"
        thermo["network_sha256"] = network_hash
        thermo_hash = self.write_artifact(request, "thermochemistry", thermo)
        result = self.artifact_value("result")
        result["evidence_class"] = "real-artifact"
        result["model_binding"]["network_sha256"] = network_hash
        result["model_binding"]["thermochemistry_sha256"] = thermo_hash
        result["provider"]["python_version"] = "3.11.9"
        self.write_artifact(request, "result", result)
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_BLOCKED)
        self.assertIn(
            "CAT.ACTIVATION.REAL_ARTIFACT_VALIDATION_MISSING",
            {item["code"] for item in report["findings"]},
        )
        self.assertEqual(report["maturity"], "design-only")

    def test_version_drift_plan_is_blocked(self) -> None:
        plan = json.loads((ROOT / "examples" / "plan-request.json").read_text(encoding="utf-8"))
        plan["provider_version"] = "0.3.2"
        report = guard.make_plan(plan)
        status, exit_code = guard.determine_status(report["findings"])
        self.assertEqual(status, "blocked_external_evidence")
        self.assertEqual(exit_code, guard.EXIT_BLOCKED)

    def test_cli_emits_report_and_refuses_silent_overwrite(self) -> None:
        output = self.base / "report.json"
        first = guard.main(["audit", "--request", str(self.request_path), "--output", str(output)])
        self.assertEqual(first, guard.EXIT_OK)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "passed")
        self.assertNotIn(str(self.base), json.dumps(report))
        second = guard.main(["audit", "--request", str(self.request_path), "--output", str(output)])
        self.assertEqual(second, guard.EXIT_INPUT)
        original_report = output.read_bytes()
        overwrite = guard.main(
            ["audit", "--request", str(self.request_path), "--output", str(output), "--overwrite"]
        )
        self.assertEqual(overwrite, guard.EXIT_INPUT)
        self.assertEqual(output.read_bytes(), original_report)

    def test_cli_refuses_output_equal_to_request(self) -> None:
        original = self.request_path.read_bytes()
        exit_code = guard.main(
            [
                "audit",
                "--request",
                str(self.request_path),
                "--output",
                str(self.request_path),
            ]
        )
        self.assertEqual(exit_code, guard.EXIT_INPUT)
        self.assertEqual(self.request_path.read_bytes(), original)

    def test_cli_refuses_output_equal_to_artifact(self) -> None:
        artifact = self.base / "network.json"
        original = artifact.read_bytes()
        exit_code = guard.main(
            [
                "audit",
                "--request",
                str(self.request_path),
                "--output",
                str(artifact),
            ]
        )
        self.assertEqual(exit_code, guard.EXIT_INPUT)
        self.assertEqual(artifact.read_bytes(), original)

    def test_output_hardlink_and_symlink_aliases_to_input_are_rejected(self) -> None:
        tracker = guard.InputTracker()
        guard.load_json_object(self.request_path, tracker)
        original = self.request_path.read_bytes()
        hardlink = self.base / "request-hardlink.json"
        symlink = self.base / "request-symlink.json"
        os.link(self.request_path, hardlink)
        symlink.symlink_to(self.request_path.name)
        for output in (hardlink, symlink):
            with self.subTest(output=output.name):
                with self.assertRaises(guard.GuardError):
                    guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, False, tracker)
        self.assertEqual(self.request_path.read_bytes(), original)

    def test_overwrite_is_rejected_and_preserves_existing_report(self) -> None:
        output = self.base / "preserved-report.json"
        original = b'{"old":"report"}\n'
        output.write_bytes(original)
        exit_code = guard.main(
            [
                "audit",
                "--request",
                str(self.request_path),
                "--output",
                str(output),
                "--overwrite",
            ]
        )
        self.assertEqual(exit_code, guard.EXIT_INPUT)
        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_staging_write_failure_leaves_no_report(self) -> None:
        output = self.base / "write-failure-report.json"
        with mock.patch.object(guard.os, "write", side_effect=OSError("synthetic write failure")):
            with self.assertRaises(guard.GuardError):
                guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, False)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_staging_path_substitution_cannot_publish_attacker_bytes(self) -> None:
        output = self.base / "substitution-report.json"
        original_link = guard.os.link
        substituted = False

        def substituting_link(source: str, target: str, *args: object, **kwargs: object) -> None:
            nonlocal substituted
            directory_fd = int(kwargs["src_dir_fd"])
            if not substituted:
                os.unlink(source, dir_fd=directory_fd)
                attacker_fd = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory_fd)
                os.write(attacker_fd, b"ATTACKER_BYTES")
                os.close(attacker_fd)
                substituted = True
            original_link(source, target, *args, **kwargs)

        with mock.patch.object(guard.os, "link", substituting_link):
            with self.assertRaises(guard.GuardError):
                guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, False)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_late_target_creation_is_not_overwritten(self) -> None:
        output = self.base / "late-target.json"
        original_link = guard.os.link
        victim = b'{"victim":true}\n'
        created = False

        def racing_link(source: str, target: str, *args: object, **kwargs: object) -> None:
            nonlocal created
            directory_fd = int(kwargs["dst_dir_fd"])
            if not created:
                target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory_fd)
                os.write(target_fd, victim)
                os.close(target_fd)
                created = True
            original_link(source, target, *args, **kwargs)

        with mock.patch.object(guard.os, "link", racing_link):
            with self.assertRaises(guard.GuardError):
                guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, False)
        self.assertEqual(output.read_bytes(), victim)
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_internal_overwrite_route_is_fail_closed(self) -> None:
        output = self.base / "exchange-target.json"
        original = b'{"old":true}\n'
        output.write_bytes(original)
        with self.assertRaises(guard.GuardError):
            guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, True)
        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_reference_contracts_and_skill_budget(self) -> None:
        for name in (
            "finding-catalog.json",
            "fixture-manifest.json",
            "maturity-matrix.json",
            "task-evidence-profiles.json",
        ):
            value = json.loads((ROOT / "references" / name).read_text(encoding="utf-8"))
            self.assertEqual(value["schema_version"], "1.0")
        decision_table = json.loads(
            (ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8")
        )
        cases = decision_table["cases"]
        self.assertEqual(decision_table["contract_name"], "candidate-decision-table")
        self.assertEqual(decision_table["schema_version"], "1.0")
        self.assertEqual(decision_table["skill_id"], "catmap-microkinetics")
        self.assertEqual(decision_table["lifecycle"], "development")
        self.assertEqual(decision_table["selection_policy"], "first-match-by-ascending-priority")
        self.assertEqual(decision_table["current_claim"], "no_positive_claim")
        self.assertFalse(decision_table["execution_authorized"])
        self.assertFalse(decision_table["promotion_authorized"])
        self.assertEqual(len(cases), 11)
        self.assertEqual(len({item["case_id"] for item in cases}), 11)
        self.assertEqual([item["priority"] for item in cases], list(range(1, 12)))
        self.assertEqual({item["current_claim"] for item in cases}, {"no_positive_claim"})
        self.assertEqual({item["execution_authorized"] for item in decision_table["cases"]}, {False})
        self.assertEqual({item["promotion_authorized"] for item in cases}, {False})
        self.assertTrue(all(item["minimum_next_action"] for item in cases))
        self.assertEqual(len({item["minimum_next_action"] for item in cases}), 11)
        self.assertEqual(decision_table["default_case_id"], cases[-1]["case_id"])
        self.assertEqual(cases[-1]["required_evidence"], [])
        self.assertEqual(cases[-1]["action_state"], "local_gate_blocked")
        catalog = json.loads((ROOT / "references" / "finding-catalog.json").read_text(encoding="utf-8"))
        self.assertTrue({code for item in cases for code in item["finding_codes"]} <= set(catalog["findings"]))
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(skill.splitlines()), 500)
        self.assertTrue(skill.startswith("---\nname: catmap-microkinetics\n"))
        self.assertNotIn("\nTODO", skill)


if __name__ == "__main__":
    unittest.main()
