from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
import sys

sys.path.insert(0, str(SCRIPTS))
import vaspkit_guard as guard


class VaspkitGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_path = ROOT / "examples" / "synthetic-source.json"
        self.transcript_path = ROOT / "examples" / "synthetic-211-transcript.txt"
        self.band_path = ROOT / "examples" / "synthetic-BAND.dat"
        self.klabels_path = ROOT / "examples" / "synthetic-KLABELS"
        self.source = json.loads(self.source_path.read_text(encoding="utf-8"))
        self.parent_manifest_path = ROOT / "examples" / "vasp-band-parent-run-manifest.json"
        self.parent_audit_path = ROOT / "examples" / "vasp-band-parent-audit.json"
        self.parent_request_path = ROOT / "examples" / "vasp-band-parent-handoff-request.json"

    def clone(self) -> dict:
        return json.loads(json.dumps(self.source))

    def resign_calculation(self, value: dict) -> None:
        value["calculation"]["evidence_projection_sha256"] = guard.calculation_evidence_projection_sha256(
            value["calculation"]
        )

    def write_json(self, directory: Path, name: str, value: object) -> Path:
        path = directory / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def write_text(self, directory: Path, name: str, value: str) -> Path:
        path = directory / name
        path.write_text(value, encoding="utf-8")
        return path

    def bound_parent_fixture(
        self,
        directory: Path,
        *,
        mutate_manifest=None,
        mutate_audit=None,
        mutate_request=None,
    ) -> tuple[Path, Path, Path]:
        manifest = json.loads(self.parent_manifest_path.read_text(encoding="utf-8"))
        audit = json.loads(self.parent_audit_path.read_text(encoding="utf-8"))
        request = json.loads(self.parent_request_path.read_text(encoding="utf-8"))
        if mutate_audit is not None:
            mutate_audit(audit)
        audit_path = self.write_json(directory, "parent-audit.json", audit)
        audit_hash = hashlib.sha256(audit_path.read_bytes()).hexdigest()
        for item in manifest["evidence"]:
            if item["role"] == "vasp_audit_report":
                item["sha256"] = audit_hash
        if mutate_manifest is not None:
            mutate_manifest(manifest)
        manifest_path = self.write_json(directory, "run-manifest.json", manifest)
        request["expected_parent"]["run_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        request["expected_parent"]["audit_report_sha256"] = audit_hash
        request["artifacts"]["audit_report"]["sha256"] = audit_hash
        request["artifacts"]["audit_report"]["bytes"] = len(audit_path.read_bytes())
        if mutate_request is not None:
            mutate_request(request)
        request_path = self.write_json(directory, "handoff-request.json", request)
        return manifest_path, audit_path, request_path

    def test_source_audit_passes_without_path_leak(self) -> None:
        report = guard.audit_source(self.source_path)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["future_gate_ceiling"], "technical-vasp-parent-and-adapter-provenance")
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["source"]["adapter_request"]["task"], "211")
        self.assertNotIn(str(ROOT), json.dumps(report))

    def test_candidate_lifecycle_never_raises_claim_or_authority_on_failure(self) -> None:
        for blocked, status in ((False, "fail"), (True, "blocked")):
            report = guard.error_report(
                "audit-source",
                guard.GuardError("VK_SOURCE_INVALID", "synthetic", blocked=blocked),
            )
            self.assertEqual(report["status"], status)
            self.assertEqual(report["claim_ceiling"], "no_positive_claim")
            self.assertEqual(report["future_gate_ceiling"], "none")
            self.assertFalse(report["promotion_authorized"])
            self.assertFalse(report["execution_authorized"])

    def test_machine_decision_table_locks_lifecycle_and_has_complete_unique_cases(self) -> None:
        path = ROOT / "references" / "weak-model-decision-table.json"
        table, _ = guard.read_json(path)
        self.assertEqual(table["contract_name"], "candidate-decision-table")
        self.assertEqual(table["schema_version"], "1.0")
        self.assertEqual(table["skill_id"], "vaspkit-postprocess")
        self.assertEqual(table["lifecycle"], "development")
        self.assertEqual(table["selection_policy"], "first-match-by-ascending-priority")
        self.assertEqual(table["current_claim"], "no_positive_claim")
        self.assertFalse(table["execution_authorized"])
        self.assertFalse(table["promotion_authorized"])
        cases = table["cases"]
        self.assertEqual(len(cases), 24)
        case_ids = [case["case_id"] for case in cases]
        priorities = [case["priority"] for case in cases]
        self.assertEqual(len(case_ids), len(set(case_ids)))
        self.assertEqual(priorities, list(range(1, len(cases) + 1)))
        self.assertEqual(
            len({case["minimum_next_action"] for case in cases}),
            len(cases),
        )
        self.assertTrue(all(isinstance(priority, int) and not isinstance(priority, bool) for priority in priorities))
        default = cases[-1]
        self.assertEqual(table["default_case_id"], default["case_id"])
        self.assertEqual(default["required_evidence"], [])
        self.assertEqual(default["action_state"], "local_gate_blocked")
        expected_findings = {
            "VK_SOURCE_INVALID", "VK_PARENT_EVIDENCE_MISMATCH", "VK_PARENT_ACCEPTANCE_FAILED",
            "VK_REQUIRED_INPUT_MISSING", "VK_ENERGY_REFERENCE_INVALID", "VK_SPIN_LAYOUT_UNSUPPORTED",
            "VK_PROFILE_UNKNOWN", "VK_PROFILE_BLOCKED", "VK_TASK_UNSUPPORTED", "VK_VERSION_MISMATCH",
            "VK_PROMPT_DRIFT", "VK_FATAL_SENTINEL", "VK_ARTIFACT_HASH_MISMATCH",
            "VK_BAND_TABLE_INVALID", "VK_KLABELS_INVALID", "VK_OUTPUT_EXISTS",
            "VK_OUTPUT_INPUT_ALIAS", "VK_OUTPUT_WRITE_FAILED",
            "VK_DOCUMENTATION_CONFLICT", "VK_RECIPE_NOT_ESTABLISHED",
            "VK_NONINTERACTIVE_NOT_ESTABLISHED", "VK_DECISION_NO_MATCH",
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

    def test_parent_projection_fixture_is_stable_and_file_order_is_not_semantic(self) -> None:
        expected = "5d3e60ed502b0d7fefcabe1728f188e17321645fd86e591c201c63568e1708b6"
        self.assertEqual(guard.calculation_evidence_projection_sha256(self.source["calculation"]), expected)
        value = self.clone()
        value["calculation"]["files"].reverse()
        self.assertEqual(guard.calculation_evidence_projection_sha256(value["calculation"]), expected)
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_json(Path(temp), "source.json", value)
            self.assertEqual(guard.audit_source(path)["status"], "pass")

    def test_unsigned_parent_and_raw_record_hash_detachment_fail(self) -> None:
        value = self.clone()
        del value["calculation"]["evidence_projection_sha256"]
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_json(Path(temp), "unsigned.json", value)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(path)
            self.assertEqual(caught.exception.code, "VK_SOURCE_INVALID")
        value = self.clone()
        value["calculation"]["record_sha256"] = "9" * 64
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_json(Path(temp), "detached.json", value)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(path)
            self.assertEqual(caught.exception.code, "VK_PARENT_EVIDENCE_MISMATCH")

    def test_every_projected_parent_semantic_mutation_requires_a_new_projection(self) -> None:
        mutations = {
            "record-id": lambda calc: calc.__setitem__("record_id", "synthetic-vasp-run-002"),
            "code": lambda calc: calc.__setitem__("code", "cp2k"),
            "version": lambda calc: calc.__setitem__("code_version", "synthetic-version-2"),
            "structure": lambda calc: calc.__setitem__("structure_fingerprint", "sha256:" + "9" * 64),
            "completion": lambda calc: calc.__setitem__("completion", "running"),
            "spin": lambda calc: calc.__setitem__("spin_channels", 2),
            "gate": lambda calc: calc["acceptance_gates"].__setitem__("electronic", "fail"),
            "role-and-label": lambda calc: calc["files"][-1].update({"role": "KPATH.in", "label": "KPATH.in"}),
            "artifact-hash": lambda calc: calc["files"][1].__setitem__("sha256", "a" * 64),
            "artifact-bytes": lambda calc: calc["files"][1].__setitem__("bytes", 1025),
        }
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name, mutate in mutations.items():
                value = self.clone()
                mutate(value["calculation"])
                path = self.write_json(directory, f"{name}.json", value)
                with self.subTest(name=name), self.assertRaises(guard.GuardError) as caught:
                    guard.audit_source(path)
                self.assertEqual(caught.exception.code, "VK_PARENT_EVIDENCE_MISMATCH")

    def test_resigned_parent_must_still_pass_all_four_acceptance_gates(self) -> None:
        for gate in ("input", "output", "electronic", "band_task"):
            value = self.clone()
            value["calculation"]["acceptance_gates"][gate] = "fail"
            self.resign_calculation(value)
            with tempfile.TemporaryDirectory() as temp:
                path = self.write_json(Path(temp), f"{gate}.json", value)
                with self.assertRaises(guard.GuardError) as caught:
                    guard.audit_source(path)
                self.assertEqual(caught.exception.code, "VK_PARENT_ACCEPTANCE_FAILED")

    def test_211_plan_is_literal_dry_run(self) -> None:
        report = guard.plan_menu(self.source_path, "vaspkit-1.5.0-macos-intel", "211")
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["execution_performed"])
        self.assertEqual(report["stdin_tokens"], ["211", "0"])
        self.assertEqual(report["argv_template"], ["<vaspkit-executable>"])

    def test_252_plan_has_separate_kpath_contract(self) -> None:
        value = self.clone()
        value["adapter_request"]["task"] = "252"
        del value["adapter_evidence"]
        for record in value["calculation"]["files"]:
            if record["role"] == "KPOINTS":
                record["role"] = "KPATH.in"
                record["label"] = "KPATH.in"
        self.resign_calculation(value)
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_json(Path(temp), "source.json", value)
            report = guard.plan_menu(path, "vaspkit-1.5.0-macos-intel", "252")
        self.assertIn("KPATH.in", report["required_inputs"])
        self.assertNotIn("KPOINTS", report["required_inputs"])

    def test_plan_profile_and_task_must_match_the_source_request(self) -> None:
        for profile, task in (
            ("vaspkit-1.5.0-macos-intel", "252"),
            ("vaspkit-1.5.1-linux-x64", "211"),
        ):
            with self.subTest(profile=profile, task=task), self.assertRaises(guard.GuardError) as caught:
                guard.plan_menu(self.source_path, profile, task)
            self.assertIn(caught.exception.code, {"VK_SOURCE_INVALID", "VK_PROFILE_BLOCKED"})

    def test_151_profile_is_blocked_without_version_specific_regression(self) -> None:
        with self.assertRaises(guard.GuardError) as caught:
            guard.plan_menu(self.source_path, "vaspkit-1.5.1-linux-x64", "211")
        self.assertTrue(caught.exception.blocked)
        self.assertEqual(caught.exception.code, "VK_PROFILE_BLOCKED")

    def test_unknown_menu_task_is_blocked(self) -> None:
        with self.assertRaises(guard.GuardError) as caught:
            guard.plan_menu(self.source_path, "vaspkit-1.5.0-macos-intel", "999")
        self.assertEqual(caught.exception.code, "VK_TASK_UNSUPPORTED")

    def test_required_parent_role_and_completion_fail_closed(self) -> None:
        value = self.clone()
        value["calculation"]["files"] = [item for item in value["calculation"]["files"] if item["role"] != "DOSCAR"]
        self.resign_calculation(value)
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_json(Path(temp), "source.json", value)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(path)
            self.assertEqual(caught.exception.code, "VK_REQUIRED_INPUT_MISSING")
        value = self.clone()
        value["calculation"]["completion"] = "running"
        self.resign_calculation(value)
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_json(Path(temp), "source.json", value)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(path)
            self.assertEqual(caught.exception.code, "VK_PARENT_INCOMPLETE")

    def test_parent_role_basename_is_exact(self) -> None:
        value = self.clone()
        value["calculation"]["files"][0]["label"] = "renamed-INCAR"
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_json(Path(temp), "source.json", value)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_source(path)
            self.assertEqual(caught.exception.code, "VK_SOURCE_INVALID")

    def test_transcript_audit_passes_exact_banner_and_prompts(self) -> None:
        report = guard.audit_transcript(self.transcript_path, "vaspkit-1.5.0-macos-intel", "211")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["verified_events"][-1], "main-menu-return")

    def test_banner_drift_repetition_and_fatal_sentinel_fail(self) -> None:
        original = self.transcript_path.read_text(encoding="utf-8")
        cases = [
            (original.replace("1.5.0", "1.5.1"), "VK_VERSION_MISMATCH"),
            (original + original, "VK_VERSION_MISMATCH"),
            (original + "Fatal error\n", "VK_FATAL_SENTINEL"),
        ]
        with tempfile.TemporaryDirectory() as temp:
            for index, (text, code) in enumerate(cases):
                path = self.write_text(Path(temp), f"case-{index}.txt", text)
                with self.assertRaises(guard.GuardError) as caught:
                    guard.audit_transcript(path, "vaspkit-1.5.0-macos-intel", "211")
                self.assertEqual(caught.exception.code, code)

    def test_prompt_order_and_default_token_are_required(self) -> None:
        original = self.transcript_path.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            missing = self.write_text(Path(temp), "missing.txt", original.replace("\n0\n", "\n1\n"))
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_transcript(missing, "vaspkit-1.5.0-macos-intel", "211")
            self.assertEqual(caught.exception.code, "VK_PROMPT_DRIFT")
            reordered = self.write_text(
                Path(temp),
                "reordered.txt",
                original.replace(
                    "-->> (02) Reading Fermi-Energy from DOSCAR File...\n-->> (03) Reading Energy-Levels From EIGENVAL File...",
                    "-->> (03) Reading Energy-Levels From EIGENVAL File...\n-->> (02) Reading Fermi-Energy from DOSCAR File...",
                ),
            )
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_transcript(reordered, "vaspkit-1.5.0-macos-intel", "211")
            self.assertEqual(caught.exception.code, "VK_PROMPT_DRIFT")

    def test_band_parser_normalizes_explicit_energy_reference(self) -> None:
        report = guard.parse_bands(self.source_path, self.transcript_path, self.band_path, self.klabels_path)
        dataset = report["dataset"]
        self.assertEqual(dataset["dimensions"], {"kpoints": 3, "bands": 2, "spin_channels": 1, "rows": 6})
        self.assertEqual(dataset["high_symmetry_points"][0]["label"], "GAMMA")
        self.assertEqual(dataset["energy_transform"]["additive_offset_ev"], 0.0)

    def test_explicit_energy_offset_is_applied_not_inferred(self) -> None:
        value = self.clone()
        value["energy_reference"]["additive_offset_ev"] = 0.5
        value["energy_reference"]["target_reference"] = "explicit-user-reference"
        with tempfile.TemporaryDirectory() as temp:
            source = self.write_json(Path(temp), "source.json", value)
            report = guard.parse_bands(source, self.transcript_path, self.band_path, self.klabels_path)
        first = report["dataset"]["rows"][0]
        self.assertEqual(first["energy_input_ev"], -1.0)
        self.assertEqual(first["energy_relative_ev"], -0.5)
        self.assertEqual(report["dataset"]["energy_transform"]["source_role"], "DOSCAR")
        self.assertEqual(report["dataset"]["energy_transform"]["unit"], "eV")
        self.assertEqual(report["dataset"]["energy_transform"]["sign_convention"], "additive")

    def test_energy_unit_and_sign_convention_are_exact(self) -> None:
        for key, replacement in (("unit", "Ry"), ("sign_convention", "subtractive")):
            value = self.clone()
            value["energy_reference"][key] = replacement
            with tempfile.TemporaryDirectory() as temp:
                source = self.write_json(Path(temp), f"{key}.json", value)
                with self.assertRaises(guard.GuardError) as caught:
                    guard.audit_source(source)
                self.assertEqual(caught.exception.code, "VK_ENERGY_REFERENCE_INVALID")

    def test_default_fermi_route_is_exact_and_doscar_hash_bound(self) -> None:
        cases = (
            ("input_table_reference", "unknown-reference"),
            ("source_role", "EIGENVAL"),
            ("source_sha256", "a" * 64),
        )
        for key, replacement in cases:
            value = self.clone()
            value["energy_reference"][key] = replacement
            with tempfile.TemporaryDirectory() as temp:
                source = self.write_json(Path(temp), f"{key}.json", value)
                with self.assertRaises(guard.GuardError) as caught:
                    guard.audit_source(source)
                self.assertEqual(caught.exception.code, "VK_ENERGY_REFERENCE_INVALID")

    def test_artifact_and_transcript_hashes_are_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            changed = self.write_text(Path(temp), "band.dat", self.band_path.read_text(encoding="utf-8") + "\n")
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_bands(self.source_path, self.transcript_path, changed, self.klabels_path)
            self.assertEqual(caught.exception.code, "VK_ARTIFACT_HASH_MISMATCH")
            changed_transcript = self.write_text(Path(temp), "transcript.txt", self.transcript_path.read_text(encoding="utf-8") + " \n")
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_bands(self.source_path, changed_transcript, self.band_path, self.klabels_path)
            self.assertEqual(caught.exception.code, "VK_ARTIFACT_HASH_MISMATCH")

    def test_parser_uses_verified_artifact_bytes_without_a_second_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            band = directory / "BAND.dat"
            band.write_bytes(self.band_path.read_bytes())
            labels = directory / "KLABELS"
            labels.write_bytes(self.klabels_path.read_bytes())
            original_reader = guard._read_bounded_file
            band_reads = 0

            def read_then_replace(path: Path, limit: int, code: str, description: str) -> bytes:
                nonlocal band_reads
                raw = original_reader(path, limit, code, description)
                if path == band:
                    band_reads += 1
                    band.write_bytes(b"0.0 not-a-number\n1.0 2.0\n")
                return raw

            with mock.patch.object(guard, "_read_bounded_file", side_effect=read_then_replace):
                report = guard.parse_bands(self.source_path, self.transcript_path, band, labels)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(band_reads, 1)
            self.assertIn(b"not-a-number", band.read_bytes())

    def test_spin_two_layout_blocks_before_table_interpretation(self) -> None:
        value = self.clone()
        value["calculation"]["spin_channels"] = 2
        self.resign_calculation(value)
        with tempfile.TemporaryDirectory() as temp:
            source = self.write_json(Path(temp), "source.json", value)
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_bands(source, self.transcript_path, self.band_path, self.klabels_path)
            self.assertTrue(caught.exception.blocked)
            self.assertEqual(caught.exception.code, "VK_SPIN_LAYOUT_UNSUPPORTED")

    def test_table_parser_rejects_nonnumeric_ragged_and_decreasing_paths(self) -> None:
        cases = [
            b"0.0 1.0\n0.5 bad\n",
            b"0.0 1.0 2.0\n0.5 2.0\n",
            b"0.0 1.0\n0.5 2.0\n0.4 3.0\n",
        ]
        for raw in cases:
            with self.assertRaises(guard.GuardError) as caught:
                guard._parse_band(raw)
            self.assertEqual(caught.exception.code, "VK_BAND_TABLE_INVALID")

    def test_klabels_parser_rejects_out_of_range_and_reordering(self) -> None:
        for raw in (b"GAMMA 0\nX 2\n", b"X 0.5\nGAMMA 0.0\n"):
            with self.assertRaises(guard.GuardError) as caught:
                guard._parse_klabels(raw, 0.0, 1.0)
            self.assertEqual(caught.exception.code, "VK_KLABELS_INVALID")

    def test_strict_json_rejects_duplicate_bom_nan_and_nonobject(self) -> None:
        cases = [b'{"x":1,"x":2}', b"\xef\xbb\xbf{}", b'{"x":NaN}', b'[]']
        with tempfile.TemporaryDirectory() as temp:
            for index, raw in enumerate(cases):
                path = Path(temp) / f"case-{index}.json"
                path.write_bytes(raw)
                with self.assertRaises(guard.GuardError):
                    guard.read_json(path)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "requires O_NOFOLLOW")
    def test_source_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            link = Path(temp) / "source-link.json"
            link.symlink_to(self.source_path)
            with self.assertRaises(guard.GuardError) as caught:
                guard.read_json(link)
            self.assertEqual(caught.exception.code, "VK_JSON_INVALID")

    def test_report_publish_is_durable_exclusive_and_cleans_its_temp_link(self) -> None:
        report = guard._base("synthetic", "pass", "synthetic-future-only")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            output = directory / "report.json"
            guard.write_report(report, output)
            decoded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(decoded["claim_ceiling"], "no_positive_claim")
            self.assertEqual(output.stat().st_nlink, 1)
            self.assertEqual(list(directory.glob(".report.json.*.tmp")), [])

    def test_report_write_failure_never_publishes_a_target(self) -> None:
        report = guard._base("synthetic", "pass", "synthetic-future-only")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            output = directory / "report.json"
            with mock.patch.object(guard, "_write_fully_and_sync", side_effect=OSError("synthetic short write")):
                with self.assertRaises(guard.GuardError) as caught:
                    guard.write_report(report, output)
            self.assertEqual(caught.exception.code, "VK_OUTPUT_WRITE_FAILED")
            self.assertFalse(os.path.lexists(output))
            self.assertEqual(list(directory.glob(".report.json.*.tmp")), [])

    def test_report_rejects_existing_broken_symlink_and_input_identity(self) -> None:
        report = guard._base("synthetic", "pass", "synthetic-future-only")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            existing = directory / "existing.json"
            existing.write_text("preserve-me", encoding="utf-8")
            with mock.patch.object(guard, "_write_fully_and_sync") as writer:
                with self.assertRaises(guard.GuardError) as caught:
                    guard.write_report(report, existing)
            self.assertEqual(caught.exception.code, "VK_OUTPUT_EXISTS")
            self.assertEqual(existing.read_text(encoding="utf-8"), "preserve-me")
            writer.assert_not_called()

            broken = directory / "broken.json"
            broken.symlink_to(directory / "missing-target")
            with self.assertRaises(guard.GuardError) as caught:
                guard.write_report(report, broken)
            self.assertEqual(caught.exception.code, "VK_OUTPUT_EXISTS")
            self.assertTrue(broken.is_symlink())

            with self.assertRaises(guard.GuardError) as caught:
                guard.write_report(report, existing, input_paths=(existing,))
            self.assertEqual(caught.exception.code, "VK_OUTPUT_INPUT_ALIAS")
            self.assertEqual(existing.read_text(encoding="utf-8"), "preserve-me")

    def test_cli_exit_codes_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(guard.main(["audit-source", "--source", str(self.source_path), "--out", str(output)]), 0)
                original_output = output.read_bytes()
                self.assertEqual(guard.main(["audit-source", "--source", str(self.source_path), "--out", str(output)]), 2)
                self.assertEqual(output.read_bytes(), original_output)
                self.assertEqual(
                    guard.main(
                        [
                            "plan-menu",
                            "--source",
                            str(self.source_path),
                            "--profile",
                            "vaspkit-1.5.1-linux-x64",
                            "--task",
                            "211",
                        ]
                    ),
                    3,
                )


if __name__ == "__main__":
    unittest.main()
