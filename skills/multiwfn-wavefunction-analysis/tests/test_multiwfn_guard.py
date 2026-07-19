from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
import sys

sys.path.insert(0, str(SCRIPTS))
import multiwfn_guard as guard


class MultiwfnGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_path = ROOT / "examples" / "synthetic-wavefunction-source.json"
        self.wavefunction_path = ROOT / "examples" / "synthetic.wfx"
        self.transcript_path = ROOT / "examples" / "synthetic-inventory-transcript.txt"
        self.charges_path = ROOT / "examples" / "synthetic-charges.txt"
        self.source = json.loads(self.source_path.read_text(encoding="utf-8"))

    def clone(self) -> dict:
        return json.loads(json.dumps(self.source))

    def reproject(self, value: dict) -> dict:
        value["parent_calculation"]["evidence_projection_sha256"] = guard.compute_evidence_projection(value)
        return value

    def write(self, directory: Path, name: str, text: str) -> Path:
        path = directory / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_source_audit_passes_and_redacts_path(self) -> None:
        report = guard.audit_source(self.source_path, self.wavefunction_path)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["verified_wavefunction"]["sha256"], self.source["file"]["sha256"])
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["future_gate_ceiling"], "technical-wavefunction-source-provenance")
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["execution_authorized"])
        self.assertNotIn(str(ROOT), json.dumps(report))

    def test_plan_is_dry_run_with_literal_exit_token(self) -> None:
        report = guard.plan_menu(
            self.source_path, self.wavefunction_path, "multiwfn-2026.7.15-linux-nogui", "wavefunction-inventory"
        )
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["execution_performed"])
        self.assertEqual(report["stdin_tokens"], ["q"])

    def test_community_macos_is_blocked(self) -> None:
        with self.assertRaises(guard.GuardError) as caught:
            guard.plan_menu(self.source_path, self.wavefunction_path, "multiwfn-community-macos", "wavefunction-inventory")
        self.assertTrue(caught.exception.blocked)
        self.assertEqual(caught.exception.code, "MW_PROFILE_BLOCKED")

    def test_unverified_menu_task_is_blocked(self) -> None:
        with self.assertRaises(guard.GuardError) as caught:
            guard.plan_menu(self.source_path, self.wavefunction_path, "multiwfn-2026.7.15-linux-nogui", "atomic-charge-menu")
        self.assertEqual(caught.exception.code, "MW_TASK_UNSUPPORTED")

    def test_transcript_audit_passes(self) -> None:
        report = guard.audit_transcript(self.transcript_path, "multiwfn-2026.7.15-linux-nogui", "wavefunction-inventory")
        self.assertEqual(report["verified_events"][-1], "graceful-exit")

    def test_repeated_banner_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = self.write(Path(temp), "joined.txt", self.transcript_path.read_text() * 2)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_transcript(path, "multiwfn-2026.7.15-linux-nogui", "wavefunction-inventory")
            self.assertEqual(caught.exception.code, "MW_VERSION_MISMATCH")

    def test_fatal_sentinel_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            text = self.transcript_path.read_text() + "Fatal error\n"
            path = self.write(Path(temp), "fatal.txt", text)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_transcript(path, "multiwfn-2026.7.15-linux-nogui", "wavefunction-inventory")
            self.assertEqual(caught.exception.code, "MW_FATAL_SENTINEL")

    def test_charge_table_normalizes_and_closes(self) -> None:
        report = guard.parse_charge_table(self.source_path, self.wavefunction_path, self.charges_path)
        dataset = report["dataset"]
        self.assertEqual(dataset["atom_count"], 3)
        self.assertAlmostEqual(dataset["charge_sum_e"], 0.0)

    def test_charge_atom_order_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            text = self.charges_path.read_text().replace("1 O", "1 H")
            path = self.write(Path(temp), "bad.txt", text)
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_charge_table(self.source_path, self.wavefunction_path, path)
            self.assertEqual(caught.exception.code, "MW_ATOM_MAPPING_MISMATCH")

    def test_charge_closure_failure_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            text = self.charges_path.read_text().replace("3 H 0.100000", "3 H 0.200000")
            path = self.write(Path(temp), "bad.txt", text)
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_charge_table(self.source_path, self.wavefunction_path, path)
            self.assertEqual(caught.exception.code, "MW_CHARGE_CLOSURE_FAILED")

    def test_duplicate_json_key_and_nan_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            duplicate = self.write(directory, "duplicate.json", '{"schema_version":"x","schema_version":"y"}')
            nan = self.write(directory, "nan.json", '{"value":NaN}')
            for path in (duplicate, nan):
                with self.assertRaises(guard.GuardError):
                    guard.read_json_object(path)

    def test_machine_decision_table_is_development_unique_and_no_claim(self) -> None:
        path = ROOT / "references" / "weak-model-decision-table.json"
        value, _ = guard.read_json_object(path)
        self.assertEqual(value["contract_name"], "candidate-decision-table")
        self.assertEqual(value["schema_version"], "1.0")
        self.assertEqual(value["skill_id"], "multiwfn-wavefunction-analysis")
        self.assertEqual(value["lifecycle"], "development")
        self.assertEqual(value["selection_policy"], "first-match-by-ascending-priority")
        self.assertEqual(value["current_claim"], "no_positive_claim")
        self.assertFalse(value["execution_authorized"])
        self.assertFalse(value["promotion_authorized"])
        cases = value["cases"]
        self.assertEqual(len(cases), 17)
        self.assertEqual(len({case["case_id"] for case in cases}), len(cases))
        self.assertEqual([case["priority"] for case in cases], list(range(1, len(cases) + 1)))
        self.assertEqual(len({case["minimum_next_action"] for case in cases}), len(cases))
        default = cases[-1]
        self.assertEqual(value["default_case_id"], default["case_id"])
        self.assertEqual(default["required_evidence"], [])
        self.assertEqual(default["action_state"], "local_gate_blocked")
        expected_findings = {
            "MW_SOURCE_INVALID", "MW_SOURCE_PROVENANCE_INCOMPLETE", "MW_WAVEFUNCTION_HASH_MISMATCH",
            "MW_PARENT_ACCEPTANCE_FAILED", "MW_PARENT_PROJECTION_MISMATCH", "MW_PROFILE_UNKNOWN",
            "MW_PROFILE_BLOCKED", "MW_TASK_UNSUPPORTED", "MW_VERSION_MISMATCH", "MW_PROMPT_DRIFT",
            "MW_FATAL_SENTINEL", "MW_TABLE_INVALID", "MW_ATOM_MAPPING_MISMATCH",
            "MW_CHARGE_CLOSURE_FAILED", "MW_OUTPUT_EXISTS", "MW_OUTPUT_WRITE_FAILED",
            "MW_NATIVE_UNAVAILABLE", "MW_RECIPE_NOT_ESTABLISHED",
            "MW_EXECUTION_MODE_INCOMPATIBLE", "MW_INPUT_INELIGIBLE",
            "MW_DECISION_NO_MATCH",
        }
        self.assertTrue(expected_findings.issubset({code for case in cases for code in case["finding_codes"]}))
        for case in cases:
            self.assertIn(case["severity"], {"P0", "P1", "P2"})
            self.assertTrue(case["condition"].strip())
            self.assertEqual(len(case["required_evidence"]), len(set(case["required_evidence"])))
            self.assertEqual(len(case["finding_codes"]), len(set(case["finding_codes"])))
            self.assertIn(case["action_state"], {"needs_evidence", "ready_for_deterministic_check", "local_gate_blocked", "local_gate_passed_limited"})
            self.assertTrue(case["expected_exit_codes"])
            self.assertEqual(case["current_claim"], "no_positive_claim")
            self.assertFalse(case["execution_authorized"])
            self.assertFalse(case["promotion_authorized"])
            self.assertTrue(case["minimum_next_action"].strip())

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
    def test_source_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            link = Path(temp) / "source-link.json"
            link.symlink_to(self.source_path)
            with self.assertRaises(guard.GuardError) as caught:
                guard.read_json_object(link)
            self.assertEqual(caught.exception.code, "MW_SOURCE_INVALID")

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
    def test_wavefunction_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            link = Path(temp) / "synthetic.wfx"
            link.symlink_to(self.wavefunction_path)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(self.source_path, link)
            self.assertEqual(caught.exception.code, "MW_WAVEFUNCTION_HASH_MISMATCH")

    def test_source_hash_and_electron_parity_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bad = json.loads(json.dumps(self.source))
            bad["file"]["sha256"] = "not-a-hash"
            path = self.write(Path(temp), "bad.json", json.dumps(bad))
            with self.assertRaises(guard.GuardError):
                guard.audit_source(path, self.wavefunction_path)
            bad = json.loads(json.dumps(self.source))
            bad["electronic_state"]["multiplicity"] = 2
            path = self.write(Path(temp), "parity.json", json.dumps(bad))
            with self.assertRaises(guard.GuardError):
                guard.audit_source(path, self.wavefunction_path)

    def test_element_electron_charge_and_ecp_closure_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            bad = json.loads(json.dumps(self.source))
            bad["electronic_state"]["electron_count"] = 8
            path = self.write(directory, "electron.json", json.dumps(bad))
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(path, self.wavefunction_path)
            self.assertEqual(caught.exception.code, "MW_SOURCE_PROVENANCE_INCOMPLETE")
            bad = json.loads(json.dumps(self.source))
            bad["structure"]["elements"][0] = "Xx"
            path = self.write(directory, "element.json", json.dumps(bad))
            with self.assertRaises(guard.GuardError):
                guard.audit_source(path, self.wavefunction_path)
            ecp = self.clone()
            ecp["basis"]["ecp_core_electrons"] = 2
            ecp["electronic_state"]["electron_count"] = 8
            self.reproject(ecp)
            path = self.write(directory, "ecp.json", json.dumps(ecp))
            self.assertEqual(guard.audit_source(path, self.wavefunction_path)["status"], "pass")

    def test_parent_raw_hash_projection_and_semantics_cannot_detach(self) -> None:
        mutations = (
            ("raw-record", lambda value: value["parent_calculation"].__setitem__("record_sha256", "f" * 64)),
            ("output", lambda value: value["parent_calculation"].__setitem__("output_hash", "a" * 64)),
            ("producer-version", lambda value: value["producer"].__setitem__("version", "1.1")),
            ("spin", lambda value: value["electronic_state"].__setitem__("spin_treatment", "unrestricted")),
        )
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name, mutate in mutations:
                value = self.clone()
                mutate(value)
                path = self.write(directory, f"{name}.json", json.dumps(value))
                with self.assertRaises(guard.GuardError) as caught:
                    guard.audit_source(path, self.wavefunction_path)
                self.assertEqual(caught.exception.code, "MW_PARENT_PROJECTION_MISMATCH")

    def test_parent_acceptance_gates_are_not_unsigned_self_reports(self) -> None:
        value = self.clone()
        value["parent_calculation"]["acceptance"]["electronic_convergence"] = "unknown"
        with tempfile.TemporaryDirectory() as temp:
            path = self.write(Path(temp), "source.json", json.dumps(value))
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(path, self.wavefunction_path)
        self.assertEqual(caught.exception.code, "MW_PARENT_ACCEPTANCE_FAILED")

    def test_wavefunction_actual_bytes_and_declared_format_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            changed = directory / "synthetic.wfx"
            changed.write_bytes(self.wavefunction_path.read_bytes() + b"changed\n")
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(self.source_path, changed)
            self.assertEqual(caught.exception.code, "MW_WAVEFUNCTION_HASH_MISMATCH")
            value = self.clone()
            value["file"]["label"] = "synthetic.wfn"
            source = self.write(directory, "format.json", json.dumps(value))
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(source, self.wavefunction_path)
            self.assertEqual(caught.exception.code, "MW_SOURCE_PROVENANCE_INCOMPLETE")

    def test_charge_sign_and_unit_mutations_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            wrong_unit = self.write(directory, "unit.txt", self.charges_path.read_text().replace("unit=e", "unit=electron"))
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_charge_table(self.source_path, self.wavefunction_path, wrong_unit)
            self.assertEqual(caught.exception.code, "MW_TABLE_INVALID")
            wrong_sign = self.clone()
            wrong_sign["electronic_state"]["charge"] = -1
            source = self.write(directory, "sign.json", json.dumps(wrong_sign))
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(source, self.wavefunction_path)
            self.assertEqual(caught.exception.code, "MW_SOURCE_PROVENANCE_INCOMPLETE")

    def test_wavefunction_verification_is_not_followed_by_a_second_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "synthetic.wfx"
            path.write_bytes(self.wavefunction_path.read_bytes())
            original = guard.verify_wavefunction

            def verify_then_mutate(candidate: Path, normalized: dict) -> dict:
                evidence = original(candidate, normalized)
                candidate.write_bytes(candidate.read_bytes() + b"post-verification mutation\n")
                return evidence

            with mock.patch.object(guard, "verify_wavefunction", side_effect=verify_then_mutate):
                report = guard.audit_source(self.source_path, path)
        self.assertEqual(report["status"], "pass")

    def test_charge_parser_consumes_verified_bytes_not_a_second_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = self.write(Path(temp), "charges.txt", self.charges_path.read_text())
            original = guard.read_text

            def read_then_mutate(candidate: Path, code: str, description: str) -> tuple[str, str, int]:
                evidence = original(candidate, code, description)
                candidate.write_text(candidate.read_text().replace("3 H 0.100000", "3 H 0.900000"))
                return evidence

            with mock.patch.object(guard, "read_text", side_effect=read_then_mutate):
                report = guard.parse_charge_table(self.source_path, self.wavefunction_path, path)
        self.assertAlmostEqual(report["dataset"]["charge_sum_e"], 0.0)

    def test_cli_exit_codes_and_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report.json"
            with contextlib.redirect_stdout(io.StringIO()):
                base = ["audit-source", "--source", str(self.source_path), "--wavefunction", str(self.wavefunction_path)]
                self.assertEqual(guard.main([*base, "--out", str(output)]), 0)
                self.assertEqual(guard.main([*base, "--out", str(output)]), 2)
                self.assertEqual(
                    guard.main(
                        [
                            "plan-menu",
                            "--source",
                            str(self.source_path),
                            "--wavefunction",
                            str(self.wavefunction_path),
                            "--profile",
                            "multiwfn-community-macos",
                            "--task",
                            "wavefunction-inventory",
                        ]
                    ),
                    3,
                )

    def test_durable_report_write_failure_leaves_no_target_and_preserves_old_file(self) -> None:
        report = guard.audit_source(self.source_path, self.wavefunction_path)
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            target = directory / "report.json"
            with mock.patch.object(guard, "_write_payload", side_effect=OSError("synthetic write failure")):
                with self.assertRaises(guard.GuardError) as caught:
                    guard.write_report(report, target, (self.source_path, self.wavefunction_path))
            self.assertEqual(caught.exception.code, "MW_OUTPUT_WRITE_FAILED")
            self.assertFalse(target.exists())
            self.assertEqual(list(directory.glob(".multiwfn-report-*")), [])

            old = "do-not-replace\n"
            target.write_text(old)
            with self.assertRaises(guard.GuardError) as caught:
                guard.write_report(report, target, (self.source_path, self.wavefunction_path))
            self.assertEqual(caught.exception.code, "MW_OUTPUT_EXISTS")
            self.assertEqual(target.read_text(), old)

    def test_report_output_cannot_reuse_an_input_identity(self) -> None:
        report = guard.audit_source(self.source_path, self.wavefunction_path)
        original = self.source_path.read_bytes()
        with self.assertRaises(guard.GuardError) as caught:
            guard.write_report(report, self.source_path, (self.source_path, self.wavefunction_path))
        self.assertEqual(caught.exception.code, "MW_OUTPUT_EXISTS")
        self.assertEqual(self.source_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
