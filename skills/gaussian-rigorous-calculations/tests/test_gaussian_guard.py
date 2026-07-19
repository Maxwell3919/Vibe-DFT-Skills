from __future__ import annotations

import copy
import hashlib
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
import gaussian_guard as guard  # noqa: E402


def request(task: str = "optimization_frequency") -> dict[str, object]:
    return {
        "schema_version": "candidate-1.0",
        "case_id": "water-minimum-001",
        "gaussian_revision": "G16 C.02",
        "task": task,
        "model_chemistry": {"method": "B3LYP", "basis": "6-31G(d)"},
        "charge": 0,
        "multiplicity": 1,
        "atom_count": 3,
        "structure_manifest_sha256": "d" * 64,
        "target": {
            "observable": "harmonic_frequencies" if "frequency" in task else "electronic_energy",
            "unit": "cm^-1" if "frequency" in task else "hartree",
            "absolute_tolerance": 1.0 if "frequency" in task else 1e-6,
        },
        "stationary_point": "minimum" if "frequency" in task else (
            "not_applicable" if task == "single_point" else "not_assessed"
        ),
        "expected_checkpoint": "water.chk",
        "parent_checkpoint_ref": None,
    }


def input_text(task: str = "optimization_frequency", *, route_extra: str = "") -> str:
    keywords = {
        "single_point": "",
        "optimization": " Opt",
        "frequency": " Freq",
        "optimization_frequency": " Opt Freq",
    }[task]
    return (
        "%Chk=water.chk\n"
        f"# B3LYP/6-31G(d){keywords} {route_extra}\n\n"
        "Private title must not enter report\n\n"
        "0 1\n"
        "O 0.000000 0.000000 0.117300\n"
        "H 0.000000 0.757200 -0.469200\n"
        "H 0.000000 -0.757200 -0.469200\n\n"
    )


def output_text(
    *,
    optimization: bool = True,
    frequencies: str | None = "1595.0 3657.0 3756.0",
    revision: str = "C.02",
    normal_count: int = 1,
    error: bool = False,
) -> str:
    lines = [
        f"Gaussian 16, Revision {revision}",
        "SCF Done: E(RB3LYP) = -76.0000000000 A.U. after 8 cycles",
    ]
    if optimization:
        lines.append("Optimization completed.")
    if frequencies is not None:
        lines.append(f"Frequencies -- {frequencies}")
    if error:
        lines.append("Error termination")
    lines.extend("Normal termination of Gaussian 16" for _ in range(normal_count))
    return "\n".join(lines) + "\n"


def execution_record(
    input_value: str,
    output_value: str,
    *,
    checkpoint: str | None = "water.chk",
    plan_raw: bytes | None = None,
) -> dict[str, object]:
    if plan_raw is None:
        _, plan_raw = plan_record()
    return {
        "schema_version": "candidate-1.0",
        "record_type": "gaussian-execution-record",
        "issuer": "trusted-platform",
        "gaussian_revision": "G16 C.02",
        "environment_attestation_sha256": "a" * 64,
        "authorization_decision_sha256": "b" * 64,
        "plan_sha256": hashlib.sha256(plan_raw).hexdigest(),
        "input_sha256": hashlib.sha256(input_value.encode()).hexdigest(),
        "output_sha256": hashlib.sha256(output_value.encode()).hexdigest(),
        "exit_code": 0,
        "status": "completed",
        "checkpoint_output": None if checkpoint is None else {
            "source_label": checkpoint,
            "sha256": "c" * 64,
            "bytes": 1024,
        },
    }


def plan_record(value: dict[str, object] | None = None) -> tuple[dict[str, object], bytes]:
    selected = value or request()
    raw = json.dumps(selected, sort_keys=True).encode("utf-8")
    return guard.make_plan(selected, raw), raw


class PlanTests(unittest.TestCase):
    def test_valid_plan_is_deterministic_and_stays_no_positive(self) -> None:
        value = request()
        raw = json.dumps(value, sort_keys=True).encode()
        first = guard.make_plan(value, raw)
        second = guard.make_plan(copy.deepcopy(value), raw)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "pass")
        self.assertEqual(first["claim_ceiling"], "no_positive_claim")
        self.assertEqual(first["candidate_lifecycle"], "development")

    def test_plan_never_defaults_decisive_fields(self) -> None:
        for field in ("gaussian_revision", "task", "model_chemistry", "charge", "target"):
            with self.subTest(field=field):
                value = request()
                del value[field]
                findings = guard.validate_request(value)
                self.assertIn("PLAN_FIELDS_INVALID", {item["code"] for item in findings})

    def test_revision_and_frequency_stationary_point_are_fail_closed(self) -> None:
        value = request()
        value["gaussian_revision"] = "G16 D.01"
        value["stationary_point"] = "not_assessed"
        codes = {item["code"] for item in guard.validate_request(value)}
        self.assertIn("PLAN_REVISION_UNSUPPORTED", codes)
        self.assertIn("PLAN_STATIONARY_POINT_REQUIRED", codes)

    def test_only_registered_model_chemistry_and_stationary_profiles_pass(self) -> None:
        value = request()
        value["model_chemistry"] = {"method": "CCSD(T)", "basis": "cc-pVTZ"}
        self.assertIn("PLAN_MODEL_CHEMISTRY_UNSUPPORTED", {item["code"] for item in guard.validate_request(value)})
        value = request()
        value["stationary_point"] = "transition_state"
        self.assertIn("PLAN_STATIONARY_POINT_CONFLICT", {item["code"] for item in guard.validate_request(value)})

    def test_checkpoint_and_parent_references_cannot_leak_paths(self) -> None:
        value = request()
        value["expected_checkpoint"] = "/private/project/water.chk"
        value["parent_checkpoint_ref"] = {
            "source_label": "../old.chk",
            "sha256": "A" * 64,
        }
        codes = {item["code"] for item in guard.validate_request(value)}
        self.assertIn("PLAN_CHECKPOINT_LABEL_INVALID", codes)
        self.assertIn("PLAN_PARENT_REF_INVALID", codes)

    def test_plan_record_identity_binds_exact_plan_content(self) -> None:
        plan, _ = plan_record()
        self.assertEqual(guard.validate_plan_record(plan), [])
        changed = copy.deepcopy(plan)
        changed["plan"]["charge"] = 1
        self.assertIn(
            "PLAN_RECORD_ID_MISMATCH",
            {item["code"] for item in guard.validate_plan_record(changed)},
        )
        changed = copy.deepcopy(plan)
        changed["evidence"][0]["sha256"] = "b" * 64
        self.assertIn(
            "PLAN_RECORD_EVIDENCE_INVALID",
            {item["code"] for item in guard.validate_plan_record(changed)},
        )


class InputAuditTests(unittest.TestCase):
    def audit(self, text: str, value: dict[str, object] | None = None) -> dict[str, object]:
        plan, plan_raw = plan_record(value)
        raw = text.encode()
        return guard.audit_input_data(text, raw, plan, plan_raw)

    def test_supported_input_passes_only_input_candidate_gates(self) -> None:
        report = self.audit(input_text())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["future_gate_ceiling"], "input_gates_only")
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["observations"]["atom_count"], 3)

    def test_method_task_charge_and_atom_mutations_are_blocked(self) -> None:
        mutations = {
            "INPUT_MODEL_CHEMISTRY_MISMATCH": input_text().replace("B3LYP", "PBE0"),
            "INPUT_TASK_MISMATCH": input_text().replace(" Opt Freq", " Opt"),
            "INPUT_CHARGE_MULTIPLICITY_MISMATCH": input_text().replace("0 1", "1 2"),
            "INPUT_ATOM_COUNT_MISMATCH": input_text().replace("H 0.000000 -0.757200 -0.469200\n", ""),
        }
        for expected, text in mutations.items():
            with self.subTest(expected=expected):
                report = self.audit(text)
                self.assertEqual(report["status"], "blocked")
                self.assertIn(expected, {item["code"] for item in report["findings"]})

    def test_element_identity_and_electron_multiplicity_are_fail_closed(self) -> None:
        invalid_element = self.audit(input_text().replace("O 0.000000", "Xx 0.000000"))
        self.assertIn("INPUT_ELEMENT_UNSUPPORTED", {item["code"] for item in invalid_element["findings"]})
        value = request()
        value["multiplicity"] = 2
        invalid_spin = self.audit(input_text().replace("0 1", "0 2"), value)
        self.assertIn("INPUT_ELECTRON_MULTIPLICITY_INVALID", {item["code"] for item in invalid_spin["findings"]})

    def test_unprofiled_features_and_link1_are_blocked(self) -> None:
        for expected, text in (
            ("INPUT_FEATURE_ONIOM_UNSUPPORTED", input_text(route_extra="ONIOM")),
            ("INPUT_FEATURE_SOLVENT_UNSUPPORTED", input_text(route_extra="SCRF=(PCM)")),
            ("INPUT_ROUTE_TOKEN_UNSUPPORTED", input_text(route_extra="NoSymm")),
            ("INPUT_LINK1_UNSUPPORTED", input_text() + "--Link1--\n# B3LYP/6-31G(d)\n"),
        ):
            with self.subTest(expected=expected):
                report = self.audit(text)
                self.assertIn(expected, {item["code"] for item in report["findings"]})

    def test_unparsed_input_sections_and_link0_directives_are_blocked(self) -> None:
        cases = (
            (
                "INPUT_LINK0_UNSUPPORTED",
                input_text().replace("%Chk=water.chk", "%Chk=water.chk\n%RWF=/private/scratch"),
            ),
            (
                "INPUT_TRAILING_SECTION_UNSUPPORTED",
                input_text() + "B 1 2 F\n",
            ),
            (
                "INPUT_TITLE_MISSING",
                input_text().replace("\nPrivate title must not enter report\n\n", "\n\n"),
            ),
        )
        for expected, text in cases:
            with self.subTest(expected=expected):
                report = self.audit(text)
                self.assertIn(expected, {item["code"] for item in report["findings"]})

    def test_model_chemistry_requires_one_exact_route_token(self) -> None:
        prefixed = input_text().replace("B3LYP/6-31G(d)", "NotB3LYP/6-31G(d)")
        report = self.audit(prefixed)
        self.assertIn("INPUT_MODEL_CHEMISTRY_MISMATCH", {item["code"] for item in report["findings"]})
        duplicate = input_text(route_extra="PBE0/def2SVP")
        report = self.audit(duplicate)
        self.assertIn("INPUT_MODEL_CHEMISTRY_MISMATCH", {item["code"] for item in report["findings"]})

    def test_checkpoint_read_requires_exact_hash_bound_parent(self) -> None:
        text = input_text().replace("%Chk=water.chk", "%Chk=water.chk\n%OldChk=old.chk")
        missing = self.audit(text)
        self.assertIn("INPUT_PARENT_LINEAGE_MISSING", {item["code"] for item in missing["findings"]})
        value = request()
        value["parent_checkpoint_ref"] = {"source_label": "old.chk", "sha256": "a" * 64}
        present = self.audit(text, value)
        self.assertEqual(present["status"], "pass")

    def test_guess_read_without_oldchk_binds_parent_to_current_chk_label(self) -> None:
        text = input_text(route_extra="Guess=Read")
        value = request()
        value["parent_checkpoint_ref"] = {"source_label": "old.chk", "sha256": "a" * 64}
        mismatch = self.audit(text, value)
        self.assertIn("INPUT_PARENT_LINEAGE_MISSING", {item["code"] for item in mismatch["findings"]})
        value["parent_checkpoint_ref"] = {"source_label": "water.chk", "sha256": "a" * 64}
        self.assertEqual(self.audit(text, value)["status"], "pass")

    def test_unrequested_parent_is_blocked_as_stale_lineage(self) -> None:
        value = request()
        value["parent_checkpoint_ref"] = {"source_label": "old.chk", "sha256": "a" * 64}
        report = self.audit(input_text(), value)
        self.assertIn("INPUT_PARENT_LINEAGE_UNEXPECTED", {item["code"] for item in report["findings"]})

    def test_report_does_not_echo_route_title_coordinates_or_path(self) -> None:
        report = self.audit(input_text())
        serialized = json.dumps(report, sort_keys=True)
        self.assertNotIn("Private title", serialized)
        self.assertNotIn("B3LYP/6-31G", serialized)
        self.assertNotIn("0.757200", serialized)
        self.assertNotIn("/private/", serialized)


class RunAuditTests(unittest.TestCase):
    def audit(
        self,
        output: str,
        *,
        task: str = "optimization_frequency",
        stationary: str | None = None,
    ) -> dict[str, object]:
        value = request(task)
        if stationary is not None:
            value["stationary_point"] = stationary
        plan, plan_raw = plan_record(value)
        input_value = input_text(task)
        record = execution_record(input_value, output, plan_raw=plan_raw)
        record_raw = json.dumps(record, sort_keys=True).encode()
        return guard.audit_run_data(
            input_value,
            input_value.encode(),
            output,
            output.encode(),
            plan,
            plan_raw,
            record,
            record_raw,
        )

    def test_minimum_opt_freq_passes_local_sentinels_but_not_claim_boundary(self) -> None:
        report = self.audit(output_text())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["future_gate_ceiling"], "numerical_candidate_only")
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["observations"]["negative_frequency_count"], 0)
        self.assertIn("output-identity", {item["id"] for item in report["gates"]})
        self.assertIn("execution-record-binding", {item["id"] for item in report["gates"]})

    def test_missing_or_detached_execution_record_blocks_a_log_self_report(self) -> None:
        value = request()
        plan, plan_raw = plan_record(value)
        input_value = input_text()
        output_value = output_text()
        missing = guard.audit_run_data(
            input_value,
            input_value.encode(),
            output_value,
            output_value.encode(),
            plan,
            plan_raw,
        )
        self.assertIn("EXECUTION_RECORD_MISSING", {item["code"] for item in missing["findings"]})
        record = execution_record(input_value, output_value)
        record["output_sha256"] = "0" * 64
        detached = guard.audit_run_data(
            input_value,
            input_value.encode(),
            output_value,
            output_value.encode(),
            plan,
            plan_raw,
            record,
            json.dumps(record).encode(),
        )
        self.assertIn("EXECUTION_RECORD_BYTE_BINDING_MISMATCH", {item["code"] for item in detached["findings"]})

    def test_execution_record_checkpoint_and_completion_are_exact(self) -> None:
        value = request()
        plan, plan_raw = plan_record(value)
        input_value = input_text()
        output_value = output_text()
        record = execution_record(input_value, output_value)
        record["exit_code"] = False
        record["checkpoint_output"]["source_label"] = "other.chk"
        result = guard.audit_run_data(
            input_value,
            input_value.encode(),
            output_value,
            output_value.encode(),
            plan,
            plan_raw,
            record,
            json.dumps(record).encode(),
        )
        codes = {item["code"] for item in result["findings"]}
        self.assertTrue({"EXECUTION_RECORD_COMPLETION_INVALID", "EXECUTION_RECORD_CHECKPOINT_MISMATCH"}.issubset(codes))

    def test_execution_record_cannot_reuse_one_hash_for_distinct_trust_roles(self) -> None:
        value = request()
        plan, plan_raw = plan_record(value)
        input_value = input_text()
        output_value = output_text()
        record = execution_record(input_value, output_value)
        record["authorization_decision_sha256"] = record["environment_attestation_sha256"]
        result = guard.audit_run_data(
            input_value, input_value.encode(), output_value, output_value.encode(),
            plan, plan_raw, record, json.dumps(record).encode(),
        )
        self.assertIn("EXECUTION_RECORD_ROLE_HASH_COLLISION", {item["code"] for item in result["findings"]})

    def test_execution_record_must_bind_exact_plan_report(self) -> None:
        value = request()
        plan, plan_raw = plan_record(value)
        input_value = input_text()
        output_value = output_text()
        record = execution_record(input_value, output_value, plan_raw=plan_raw)
        record["plan_sha256"] = "0" * 64
        result = guard.audit_run_data(
            input_value, input_value.encode(), output_value, output_value.encode(),
            plan, plan_raw, record, json.dumps(record).encode(),
        )
        self.assertIn("EXECUTION_RECORD_PLAN_BINDING_MISMATCH", {item["code"] for item in result["findings"]})

    def test_revision_error_and_ambiguous_termination_are_blocked(self) -> None:
        cases = (
            ("OUTPUT_REVISION_MISMATCH", output_text(revision="D.01")),
            ("OUTPUT_TERMINATION_INVALID", output_text(error=True)),
            ("OUTPUT_TERMINATION_INVALID", output_text(normal_count=2)),
            ("OUTPUT_TERMINATION_INVALID", output_text() + "trailing unverified text\n"),
            ("OUTPUT_REVISION_MISMATCH", "Gaussian 16, Revision C.02\n" + output_text()),
        )
        for expected, output in cases:
            with self.subTest(expected=expected):
                report = self.audit(output)
                self.assertIn(expected, {item["code"] for item in report["findings"]})

    def test_requested_optimization_and_frequency_markers_are_required(self) -> None:
        missing_opt = self.audit(output_text(optimization=False))
        self.assertIn("OUTPUT_OPTIMIZATION_INCOMPLETE", {item["code"] for item in missing_opt["findings"]})
        missing_freq = self.audit(output_text(frequencies=None))
        self.assertIn("OUTPUT_FREQUENCIES_MISSING", {item["code"] for item in missing_freq["findings"]})

    def test_known_scf_nonconvergence_sentinel_blocks(self) -> None:
        output = output_text().replace("SCF Done:", "Convergence failure\nSCF Done:")
        report = self.audit(output)
        self.assertIn("OUTPUT_SCF_CONVERGENCE_FAILURE", {item["code"] for item in report["findings"]})

    def test_minimum_and_transition_state_frequency_counts_are_exact(self) -> None:
        minimum = self.audit(output_text(frequencies="-500.0 1000.0 1500.0"))
        self.assertIn("OUTPUT_STATIONARY_POINT_MISMATCH", {item["code"] for item in minimum["findings"]})
        transition = self.audit(
            output_text(frequencies="-500.0 1000.0 1500.0"),
            task="frequency",
            stationary="transition_state",
        )
        self.assertEqual(transition["status"], "pass")
        two_negative = self.audit(
            output_text(frequencies="-500.0 -10.0 1500.0"),
            task="frequency",
            stationary="transition_state",
        )
        self.assertIn("OUTPUT_STATIONARY_POINT_MISMATCH", {item["code"] for item in two_negative["findings"]})

    def test_near_zero_frequency_is_reported_as_limitation(self) -> None:
        report = self.audit(output_text(frequencies="10.0 1000.0 1500.0"))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["observations"]["near_zero_frequency_count"], 1)
        self.assertTrue(any("20 cm^-1" in item for item in report["limitations"]))

    def test_single_point_does_not_require_opt_or_frequency(self) -> None:
        report = self.audit(output_text(optimization=False, frequencies=None), task="single_point")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["future_gate_ceiling"], "technical_run_gates_only")


class BoundaryAndCliTests(unittest.TestCase):
    def test_duplicate_json_key_and_nonfinite_number_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "request.json"
            path.write_text('{"schema_version":"candidate-1.0","schema_version":"candidate-1.0"}', encoding="utf-8")
            with self.assertRaisesRegex(guard.BoundaryError, "duplicate"):
                guard.load_json(path, "REQUEST")
            path.write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(guard.BoundaryError, "non-finite"):
                guard.load_json(path, "REQUEST")

    def test_cli_round_trip_uses_stable_exit_codes_and_safe_report(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            base = Path(directory)
            request_path = base / "request.json"
            plan_path = base / "plan.json"
            input_path = base / "case.gjf"
            output_path = base / "case.log"
            execution_path = base / "execution.json"
            report_path = base / "run.json"
            blocked_report_path = base / "blocked-run.json"
            request_path.write_text(json.dumps(request()), encoding="utf-8")
            input_path.write_text(input_text(), encoding="utf-8")
            output_path.write_text(output_text(), encoding="utf-8")
            self.assertEqual(guard.main(["plan", "--request", str(request_path), "--out", str(plan_path)]), 0)
            execution_path.write_text(json.dumps(execution_record(input_text(), output_text(), plan_raw=plan_path.read_bytes())), encoding="utf-8")
            self.assertEqual(
                guard.main([
                    "audit-run", "--input", str(input_path), "--output", str(output_path),
                    "--plan", str(plan_path), "--execution-record", str(execution_path), "--out", str(report_path),
                ]),
                0,
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["claim_ceiling"], "no_positive_claim")
            output_path.write_text(output_text(error=True), encoding="utf-8")
            execution_path.write_text(json.dumps(execution_record(input_text(), output_text(error=True), plan_raw=plan_path.read_bytes())), encoding="utf-8")
            self.assertEqual(
                guard.main([
                    "audit-run", "--input", str(input_path), "--output", str(output_path),
                    "--plan", str(plan_path), "--execution-record", str(execution_path), "--out", str(blocked_report_path),
                ]),
                2,
            )

    def test_environment_probe_never_authenticates_its_own_attestation(self) -> None:
        attestation = {
            "schema_version": "candidate-1.0",
            "provider_id": "gaussian-g16-c02",
            "expected_identity": "Gaussian 16 Rev C.02 Apple M-Series",
            "platform": "macos",
            "architecture": "arm64",
            "license_authorized": True,
            "supported_host": True,
            "issuer": "trusted-platform",
            "evidence_sha256": "a" * 64,
        }
        raw = json.dumps(attestation).encode()
        report = guard.probe_environment(attestation, raw)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["action_state"], "needs_authorization")
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertTrue(any("cannot authenticate" in item for item in report["limitations"]))

    def test_source_has_no_external_execution_path(self) -> None:
        source = (ROOT / "scripts" / "gaussian_guard.py").read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.system", "os.replace", "shell=True", "paramiko", " g16 ", "formchk("):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_evidence_hashes_bind_exact_bytes(self) -> None:
        plan, plan_raw = plan_record()
        text = input_text()
        report = guard.audit_input_data(text, text.encode(), plan, plan_raw)
        expected = hashlib.sha256(text.encode()).hexdigest()
        self.assertEqual(report["evidence"][0]["sha256"], expected)
        changed = text + "\n"
        changed_report = guard.audit_input_data(changed, changed.encode(), plan, plan_raw)
        self.assertNotEqual(changed_report["evidence"][0]["sha256"], expected)

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
            evidence_root = base / "gaussian-evidence-root"
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
                "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import gaussian_guard as g; "
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
                guard.atomic_write_json(output, {"status": "new"})
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
                    guard.atomic_write_json(output, {"status": "new"})
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
                    guard.atomic_write_json(output, {"status": "trusted"})
            self.assertFalse(output.exists())
            self.assertEqual(list(base.glob(".gaussian-guard-*.tmp")), [])

    def test_output_cannot_replace_an_evidence_file(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "request.json"
            original = json.dumps(request()).encode()
            path.write_bytes(original)
            self.assertEqual(
                guard.main(["plan", "--request", str(path), "--out", str(path)]),
                2,
            )
            self.assertEqual(path.read_bytes(), original)
            alias = Path(directory) / "alias.json"
            os.link(path, alias)
            self.assertEqual(
                guard.main(["plan", "--request", str(path), "--out", str(alias)]),
                2,
            )
            self.assertEqual(path.read_bytes(), original)

    def test_weak_model_decision_table_is_unique_and_never_authorizes(self) -> None:
        table = json.loads((ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8"))
        self.assertEqual(set(table), {"contract_name", "schema_version", "skill_id", "lifecycle", "selection_policy", "default_case_id", "current_claim", "execution_authorized", "promotion_authorized", "cases"})
        self.assertEqual(table["contract_name"], "candidate-decision-table")
        self.assertEqual(table["schema_version"], "1.0")
        self.assertEqual(table["skill_id"], "gaussian-rigorous-calculations")
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


class ProviderCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads(
            (ROOT / "references" / "feature-catalog.json").read_text(encoding="utf-8")
        )
        self.recipe_book = json.loads(
            (ROOT / "references" / "task-recipes.json").read_text(encoding="utf-8")
        )

    def test_catalog_sources_and_features_are_traceable_and_unique(self) -> None:
        self.assertEqual(self.catalog["catalog_contract"], "provider-feature-catalog@1.0")
        sources = self.catalog["sources"]
        source_ids = [item["source_id"] for item in sources]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertTrue(all(item["url"].startswith("https://") for item in sources))
        features = self.catalog["features"]
        feature_ids = [item["feature_id"] for item in features]
        self.assertEqual(len(feature_ids), len(set(feature_ids)))
        self.assertGreaterEqual(len(features), 14)
        for item in features:
            self.assertEqual(item["state"], "official-documented-native-not-run")
            self.assertIn(
                item["guard_support"],
                {"guard-supported-synthetic-only", "guard-not-supported"},
            )
            self.assertTrue(item["source_ids"])
            self.assertTrue(set(item["source_ids"]).issubset(source_ids))
            self.assertTrue(item["failure_semantics"].strip())
            self.assertTrue(item["scientific_gate"].strip())

    def test_native_state_is_explicit_and_no_provider_probe_was_fabricated(self) -> None:
        native = self.catalog["native_validation"]
        self.assertEqual(native["state"], "native-not-run")
        self.assertEqual(native["executables_found"], [])
        self.assertEqual(native["probes_attempted"], [])

    def test_recipes_have_complete_contracts_and_never_authorize_execution(self) -> None:
        self.assertEqual(self.recipe_book["recipe_contract"], "provider-task-recipes@1.0")
        self.assertIs(self.recipe_book["execution_policy"]["execution_authorized"], False)
        source_ids = {item["source_id"] for item in self.catalog["sources"]}
        recipes = self.recipe_book["recipes"]
        recipe_ids = [item["recipe_id"] for item in recipes]
        self.assertEqual(len(recipe_ids), len(set(recipe_ids)))
        self.assertGreaterEqual(len(recipes), 8)
        required = {
            "recipe_id", "purpose", "guard_support", "execution_authorized",
            "preconditions", "input_contract", "invocation", "expected_outputs",
            "success_signals", "failure_semantics", "restart_semantics",
            "scientific_acceptance", "source_ids",
        }
        for item in recipes:
            self.assertEqual(set(item), required)
            self.assertIs(item["execution_authorized"], False)
            self.assertTrue(item["preconditions"])
            self.assertTrue(item["expected_outputs"])
            self.assertTrue(item["success_signals"])
            self.assertTrue(item["failure_semantics"])
            self.assertTrue(item["scientific_acceptance"])
            self.assertTrue(set(item["source_ids"]).issubset(source_ids))

    def test_real_entry_points_are_exact_without_invented_version_flag(self) -> None:
        by_id = {item["recipe_id"]: item for item in self.recipe_book["recipes"]}
        self.assertEqual(
            by_id["gaussian.run.by-job-name@G16-C.02"]["invocation"]["argv"],
            ["g16", "job-name"],
        )
        self.assertEqual(
            by_id["gaussian.formchk@G16-C.02"]["invocation"]["argv"],
            ["formchk", "case.chk", "case.fchk"],
        )
        self.assertEqual(
            by_id["gaussian.cubegen-density@G16-C.02"]["invocation"]["argv"],
            ["cubegen", "0", "Density=SCF", "case.fchk", "density.cube", "0", "h"],
        )
        serialized = json.dumps(self.recipe_book, sort_keys=True)
        self.assertNotIn("g16 --version", serialized)


if __name__ == "__main__":
    unittest.main()
