from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
import sys

sys.path.insert(0, str(SCRIPTS))
import phonopy_guard as guard


class PhonopyGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest_path = ROOT / "examples" / "synthetic-workflow.json"
        self.table_path = ROOT / "examples" / "synthetic-band.txt"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.qe_parent_manifest_path = ROOT / "examples" / "qe-force-run-manifest.json"
        self.qe_parent_audit_path = ROOT / "examples" / "qe-force-audit.json"
        self.qe_parent_request_path = ROOT / "examples" / "qe-force-handoff-request.json"
        self.vasp_parent_manifest_path = ROOT / "examples" / "vasp-force-run-manifest.json"
        self.vasp_parent_audit_path = ROOT / "examples" / "vasp-force-audit.json"
        self.vasp_parent_request_path = ROOT / "examples" / "vasp-force-handoff-request.json"

    def write_json(self, directory: Path, name: str, value: object) -> Path:
        path = directory / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def write_text(self, directory: Path, name: str, value: str) -> Path:
        path = directory / name
        path.write_text(value, encoding="utf-8")
        return path

    def bind_band_artifact(self, value: dict, path: Path) -> None:
        raw = path.read_bytes()
        value["products"]["band"]["artifact"]["sha256"] = hashlib.sha256(raw).hexdigest()
        value["products"]["band"]["artifact"]["bytes"] = len(raw)

    def clone(self) -> dict:
        return json.loads(json.dumps(self.manifest))

    def bound_parent_fixture(
        self,
        directory: Path,
        *,
        code: str = "qe",
        mutate_manifest=None,
        mutate_audit=None,
        mutate_request=None,
    ) -> tuple[Path, Path, Path]:
        if code == "qe":
            manifest = json.loads(self.qe_parent_manifest_path.read_text(encoding="utf-8"))
            audit = json.loads(self.qe_parent_audit_path.read_text(encoding="utf-8"))
            request = json.loads(self.qe_parent_request_path.read_text(encoding="utf-8"))
        else:
            manifest = json.loads(self.vasp_parent_manifest_path.read_text(encoding="utf-8"))
            audit = json.loads(self.vasp_parent_audit_path.read_text(encoding="utf-8"))
            request = json.loads(self.vasp_parent_request_path.read_text(encoding="utf-8"))
        if mutate_audit is not None:
            mutate_audit(audit)
        audit_path = self.write_json(directory, "parent-audit.json", audit)
        audit_hash = hashlib.sha256(audit_path.read_bytes()).hexdigest()
        audit_role = request["artifacts"]["audit_report"]["role"]
        for item in manifest["evidence"]:
            if item["role"] == audit_role:
                item["sha256"] = audit_hash
        if mutate_manifest is not None:
            mutate_manifest(manifest)
        manifest_path = self.write_json(directory, "run-manifest.json", manifest)
        request["expected_parent"]["run_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        request["expected_parent"]["audit_report_sha256"] = audit_hash
        request["artifacts"]["audit_report"]["sha256"] = audit_hash
        if mutate_request is not None:
            mutate_request(request)
        request_path = self.write_json(directory, "handoff-request.json", request)
        return manifest_path, audit_path, request_path

    def assert_manifest_error(self, value: dict, code: str) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_json(Path(temp), "case.json", value)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_lineage(path)
            self.assertEqual(caught.exception.code, code)

    def test_complete_lineage_passes_without_path_leak(self) -> None:
        report = guard.audit_lineage(self.manifest_path)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["future_gate_ceiling"], "technical-phonon-workflow-lineage")
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["workflow"]["forces"]["count"], 2)
        self.assertEqual(set(report["workflow"]["products"]), {"mesh", "band", "dos", "nac"})
        self.assertNotIn(str(ROOT), json.dumps(report))

    def test_all_stage_plans_are_nonexecuting_and_nac_uses_no_removed_flag(self) -> None:
        for stage in ("displacements", "force-collection", "force-constants", "mesh", "band", "dos", "nac"):
            report = guard.plan_stage(self.manifest_path, stage)
            self.assertTrue(report["dry_run"])
            self.assertFalse(report["execution_performed"])
            self.assertNotIn("--nac", report["argv_template"])

    def test_wrong_version_blocks(self) -> None:
        value = self.clone()
        value["phonopy"]["version"] = "3.0.0"
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_json(Path(temp), "case.json", value)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_lineage(path)
            self.assertTrue(caught.exception.blocked)
            self.assertEqual(caught.exception.code, "PH_VERSION_UNSUPPORTED")

    def test_supercell_determinant_and_atom_count_close(self) -> None:
        value = self.clone()
        value["displacement_set"]["supercell_atom_count"] = 3
        self.assert_manifest_error(value, "PH_SUPERCELL_INVALID")
        value = self.clone()
        value["displacement_set"]["supercell_matrix"] = [[1, 0, 0], [0, 0, 0], [0, 0, 1]]
        self.assert_manifest_error(value, "PH_SUPERCELL_INVALID")

    def test_displacement_norm_and_duplicate_ids_fail(self) -> None:
        value = self.clone()
        value["displacement_set"]["displacements"][0]["vector_angstrom"] = [0.02, 0.0, 0.0]
        self.assert_manifest_error(value, "PH_DISPLACEMENT_INVALID")
        value = self.clone()
        value["displacement_set"]["displacements"][1]["id"] = "disp-001"
        self.assert_manifest_error(value, "PH_DISPLACEMENT_CLOSURE_FAILED")

    def test_displacement_preimage_hash_is_verified(self) -> None:
        value = self.clone()
        value["displacement_set"]["sha256"] = "f" * 64
        self.assert_manifest_error(value, "PH_DISPLACEMENT_CLOSURE_FAILED")

    def test_missing_duplicate_or_unknown_force_records_fail(self) -> None:
        value = self.clone()
        value["forces"]["records"].pop()
        self.assert_manifest_error(value, "PH_DISPLACEMENT_CLOSURE_FAILED")
        value = self.clone()
        value["forces"]["records"][1]["displacement_id"] = "disp-001"
        self.assert_manifest_error(value, "PH_DISPLACEMENT_CLOSURE_FAILED")
        value = self.clone()
        value["forces"]["records"][1]["displacement_id"] = "disp-999"
        self.assert_manifest_error(value, "PH_DISPLACEMENT_CLOSURE_FAILED")

    def test_force_unit_shape_completion_and_parent_fingerprint_fail(self) -> None:
        value = self.clone()
        value["forces"]["unit"] = "Ry/bohr"
        self.assert_manifest_error(value, "PH_FORCE_INVALID")
        value = self.clone()
        value["forces"]["records"][0]["shape"] = [1, 3]
        self.assert_manifest_error(value, "PH_FORCE_INVALID")
        value = self.clone()
        value["forces"]["records"][0]["parent_calculation"]["completion"] = "running"
        self.assert_manifest_error(value, "PH_FORCE_INVALID")
        value = self.clone()
        value["forces"]["records"][0]["parent_calculation"]["structure_fingerprint"] = "sha256:" + "1" * 64
        self.assert_manifest_error(value, "PH_FORCE_PARENT_MISMATCH")

    def test_force_parent_record_and_acceptance_gates_are_required(self) -> None:
        value = self.clone()
        value["forces"]["records"][0]["parent_calculation"]["record_sha256"] = "bad"
        self.assert_manifest_error(value, "PH_FORCE_INVALID")
        for gate in ("input_validation", "output_validation", "electronic_convergence", "force_acceptance"):
            value = self.clone()
            value["forces"]["records"][0]["parent_calculation"][gate] = "fail"
            self.assert_manifest_error(value, "PH_FORCE_INVALID")
        value = self.clone()
        value["forces"]["records"][0]["parent_calculation"]["code"] = "unknown-code"
        self.assert_manifest_error(value, "PH_FORCE_INVALID")

    def test_force_parent_raw_hash_and_projection_cannot_detach(self) -> None:
        value = self.clone()
        value["forces"]["records"][0]["parent_calculation"]["output_hash"] = "f" * 64
        self.assert_manifest_error(value, "PH_FORCE_PARENT_MISMATCH")
        value = self.clone()
        value["forces"]["records"][0]["parent_calculation"]["record_sha256"] = "e" * 64
        self.assert_manifest_error(value, "PH_FORCE_PARENT_MISMATCH")

    def test_force_collection_hash_is_verified(self) -> None:
        value = self.clone()
        value["forces"]["source_force_records_sha256"] = "f" * 64
        self.assert_manifest_error(value, "PH_FORCE_COLLECTION_HASH_MISMATCH")

    def test_force_constant_shape_and_both_parents_are_verified(self) -> None:
        value = self.clone()
        value["force_constants"]["shape"] = [1, 2, 3, 3]
        self.assert_manifest_error(value, "PH_FORCE_CONSTANTS_INVALID")
        value = self.clone()
        value["force_constants"]["source_displacement_set_sha256"] = "f" * 64
        self.assert_manifest_error(value, "PH_FORCE_CONSTANTS_INVALID")
        value = self.clone()
        value["force_constants"]["source_force_records_sha256"] = "f" * 64
        self.assert_manifest_error(value, "PH_FORCE_CONSTANTS_INVALID")

    def test_product_parent_and_dos_mesh_parent_are_verified(self) -> None:
        value = self.clone()
        value["products"]["band"]["parent_force_constants_sha256"] = "f" * 64
        self.assert_manifest_error(value, "PH_PRODUCT_PARENT_MISMATCH")
        value = self.clone()
        value["products"]["dos"]["parent_mesh_sha256"] = "f" * 64
        self.assert_manifest_error(value, "PH_PRODUCT_PARENT_MISMATCH")
        value = self.clone()
        value["products"]["band"]["dimensions"]["points"] = 12
        self.assert_manifest_error(value, "PH_PRODUCT_INVALID")

    def test_requested_products_must_close_exactly(self) -> None:
        value = self.clone()
        value["requested_products"].remove("nac")
        self.assert_manifest_error(value, "PH_PRODUCT_INVALID")
        value = self.clone()
        del value["products"]["mesh"]
        self.assert_manifest_error(value, "PH_PRODUCT_INVALID")
        value = self.clone()
        value["requested_products"] = [{"mesh": True}]
        self.assert_manifest_error(value, "PH_PRODUCT_INVALID")

    def test_nac_tensor_dimensions_and_source_hash_fail_closed(self) -> None:
        value = self.clone()
        value["products"]["nac"]["parameters"]["born_effective_charges"] = []
        self.assert_manifest_error(value, "PH_NAC_INVALID")
        value = self.clone()
        value["products"]["nac"]["parameters"]["dielectric_tensor"] = [[1.0, 0.0], [0.0, 1.0]]
        self.assert_manifest_error(value, "PH_NAC_INVALID")
        value = self.clone()
        value["products"]["nac"]["source"]["sha256"] = "bad"
        self.assert_manifest_error(value, "PH_NAC_INVALID")
        value = self.clone()
        value["products"]["nac"]["source"]["structure_fingerprint"] = "sha256:" + "1" * 64
        self.assert_manifest_error(value, "PH_NAC_INVALID")
        value = self.clone()
        value["products"]["nac"]["source"]["completion"] = "running"
        self.assert_manifest_error(value, "PH_NAC_INVALID")

    def test_primitive_identity_and_nac_projection_fail_closed(self) -> None:
        value = self.clone()
        value["structure"]["primitive_atom_count"] = 2
        self.assert_manifest_error(value, "PH_STRUCTURE_INVALID")
        value = self.clone()
        value["structure"]["primitive_matrix"] = [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
        self.assert_manifest_error(value, "PH_STRUCTURE_INVALID")
        value = self.clone()
        value["products"]["nac"]["source"]["evidence_projection_sha256"] = "e" * 64
        self.assert_manifest_error(value, "PH_NAC_INVALID")

    def test_frequency_table_preserves_negative_modes(self) -> None:
        report = guard.parse_frequency_table(self.manifest_path, self.table_path)
        dataset = report["dataset"]
        self.assertEqual(dataset["points"], 2)
        self.assertEqual(dataset["branches"], 3)
        self.assertEqual(dataset["imaginary_frequency_count"], 1)

    def test_frequency_parent_and_mode_closure_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            text = self.table_path.read_text(encoding="utf-8")
            parent_bad = self.write_text(directory, "parent.txt", text.replace("b" * 64, "f" * 64))
            parent_manifest = self.clone()
            self.bind_band_artifact(parent_manifest, parent_bad)
            parent_manifest_path = self.write_json(directory, "parent-manifest.json", parent_manifest)
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_frequency_table(parent_manifest_path, parent_bad)
            self.assertEqual(caught.exception.code, "PH_PRODUCT_PARENT_MISMATCH")
            truncated = self.write_text(directory, "truncated.txt", "\n".join(text.splitlines()[:-1]) + "\n")
            truncated_manifest = self.clone()
            self.bind_band_artifact(truncated_manifest, truncated)
            truncated_manifest_path = self.write_json(directory, "truncated-manifest.json", truncated_manifest)
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_frequency_table(truncated_manifest_path, truncated)
            self.assertEqual(caught.exception.code, "PH_TABLE_INVALID")

    def test_frequency_artifact_unit_and_q_path_are_hash_bound(self) -> None:
        original = self.table_path.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            changed = self.write_text(directory, "changed.txt", original + "\n")
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_frequency_table(self.manifest_path, changed)
            self.assertEqual(caught.exception.code, "PH_TABLE_INVALID")
            unit = self.write_text(directory, "unit.txt", original.replace("unit=THz", "unit=meV"))
            unit_manifest = self.clone()
            self.bind_band_artifact(unit_manifest, unit)
            unit_manifest_path = self.write_json(directory, "unit-manifest.json", unit_manifest)
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_frequency_table(unit_manifest_path, unit)
            self.assertEqual(caught.exception.code, "PH_TABLE_INVALID")
            coordinate = self.write_text(directory, "coordinate.txt", original.replace("2 1 0.5", "2 1 0.4").replace("2 2 0.5", "2 2 0.4").replace("2 3 0.5", "2 3 0.4"))
            coordinate_manifest = self.clone()
            self.bind_band_artifact(coordinate_manifest, coordinate)
            coordinate_manifest_path = self.write_json(directory, "coordinate-manifest.json", coordinate_manifest)
            with self.assertRaises(guard.GuardError) as caught:
                guard.parse_frequency_table(coordinate_manifest_path, coordinate)
            self.assertEqual(caught.exception.code, "PH_TABLE_INVALID")

    def test_frequency_parser_consumes_the_verified_bytes_not_a_second_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            table = self.write_text(Path(temp), "band.txt", self.table_path.read_text(encoding="utf-8"))
            original_reader = guard._read_text

            def read_then_mutate(path: Path):
                result = original_reader(path)
                path.write_text("mutated after verified read\n", encoding="utf-8")
                return result

            with mock.patch.object(guard, "_read_text", side_effect=read_then_mutate):
                report = guard.parse_frequency_table(self.manifest_path, table)
            self.assertEqual(report["status"], "pass")

    def test_strict_json_rejects_duplicate_bom_nan_and_non_object(self) -> None:
        cases = [
            b'{"x":1,"x":2}',
            b"\xef\xbb\xbf{}",
            b'{"x":NaN}',
            b'[]',
        ]
        with tempfile.TemporaryDirectory() as temp:
            for index, raw in enumerate(cases):
                path = Path(temp) / f"case-{index}.json"
                path.write_bytes(raw)
                with self.assertRaises(guard.GuardError):
                    guard.read_json(path)

    def test_machine_decision_table_is_development_unique_and_no_claim(self) -> None:
        path = ROOT / "references" / "weak-model-decision-table.json"
        value, _ = guard.read_json(path)
        self.assertEqual(value["contract_name"], "candidate-decision-table")
        self.assertEqual(value["schema_version"], "1.0")
        self.assertEqual(value["skill_id"], "phonopy-rigorous-workflows")
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
            "PH_VERSION_UNSUPPORTED", "PH_STRUCTURE_INVALID", "PH_SUPERCELL_INVALID",
            "PH_DISPLACEMENT_INVALID", "PH_DISPLACEMENT_CLOSURE_FAILED", "PH_FORCE_INVALID",
            "PH_FORCE_PARENT_MISMATCH", "PH_FORCE_COLLECTION_HASH_MISMATCH",
            "PH_FORCE_CONSTANTS_INVALID", "PH_PRODUCT_PARENT_MISMATCH", "PH_TABLE_INVALID",
            "PH_PRODUCT_INVALID", "PH_NAC_INVALID", "PH_OUTPUT_EXISTS",
            "PH_OUTPUT_WRITE_FAILED", "PH_NATIVE_UNAVAILABLE",
            "PH_V4_CLI_MISMATCH", "PH_RECIPE_NOT_ESTABLISHED",
            "PH_DOCUMENTATION_CONFLICT", "PH_DECISION_NO_MATCH",
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
    def test_manifest_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            link = Path(temp) / "manifest-link.json"
            link.symlink_to(self.manifest_path)
            with self.assertRaises(guard.GuardError) as caught:
                guard.read_json(link)
            self.assertEqual(caught.exception.code, "PH_JSON_INVALID")

    def test_cli_exit_codes_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(guard.main(["audit-lineage", "--manifest", str(self.manifest_path), "--out", str(output)]), 0)
                self.assertEqual(guard.main(["audit-lineage", "--manifest", str(self.manifest_path), "--out", str(output)]), 2)
                self.assertEqual(guard.main(["plan-stage", "--manifest", str(self.manifest_path), "--stage", "thermal-properties"]), 3)

    def test_durable_report_write_failure_leaves_no_target_and_preserves_old_file(self) -> None:
        report = guard.audit_lineage(self.manifest_path)
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            target = directory / "report.json"
            with mock.patch.object(guard, "_write_payload", side_effect=OSError("synthetic write failure")):
                with self.assertRaises(guard.GuardError) as caught:
                    guard.write_report(report, target, (self.manifest_path,))
            self.assertEqual(caught.exception.code, "PH_OUTPUT_WRITE_FAILED")
            self.assertFalse(target.exists())
            self.assertEqual(list(directory.glob(".phonopy-report-*")), [])

            old = "do-not-replace\n"
            target.write_text(old)
            with self.assertRaises(guard.GuardError) as caught:
                guard.write_report(report, target, (self.manifest_path,))
            self.assertEqual(caught.exception.code, "PH_OUTPUT_EXISTS")
            self.assertEqual(target.read_text(), old)

    def test_report_output_cannot_reuse_an_input_identity(self) -> None:
        report = guard.audit_lineage(self.manifest_path)
        original = self.manifest_path.read_bytes()
        with self.assertRaises(guard.GuardError) as caught:
            guard.write_report(report, self.manifest_path, (self.manifest_path,))
        self.assertEqual(caught.exception.code, "PH_OUTPUT_EXISTS")
        self.assertEqual(self.manifest_path.read_bytes(), original)

    def test_qe_and_vasp_parent_handoffs_project_only_verified_active_fields(self) -> None:
        fixtures = (
            (self.qe_parent_manifest_path, self.qe_parent_audit_path, self.qe_parent_request_path, "qe"),
            (self.vasp_parent_manifest_path, self.vasp_parent_audit_path, self.vasp_parent_request_path, "vasp"),
        )
        for manifest, audit, request, code in fixtures:
            report = guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["local_consistency"], "pass")
            self.assertEqual(report["claim_ceiling"], "no_positive_claim")
            self.assertFalse(report["promotion_authorized"])
            self.assertFalse(report["execution_authorized"])
            self.assertEqual(report["parent_projection"]["code"], code)
            self.assertEqual(report["parent_projection"]["gates"]["force_acceptance"], "not_evaluated_by_active_audit")
            self.assertFalse(report["eligible_for_workflow_manifest"])
            self.assertEqual(
                {item["code"] for item in report["findings"]},
                {"PH_PARENT_FORCE_GATE_MISSING", "PH_PARENT_AUTHENTICATION_UNAVAILABLE"},
            )
            for evidence in report["raw_evidence"].values():
                self.assertRegex(evidence["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(evidence["bytes"], 0)

    def test_parent_handoff_wrong_code_task_and_raw_hash_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            manifest, audit, request = self.bound_parent_fixture(
                directory,
                mutate_manifest=lambda value: value.update({"code": "cp2k", "code_version": "2026.1", "task_type": "energy"}),
                mutate_request=lambda value: value["expected_parent"].update({"code": "cp2k", "code_version": "2026.1", "task_type": "energy"}),
            )
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(caught.exception.code, "PH_PARENT_CODE_UNSUPPORTED")
            self.assertTrue(caught.exception.blocked)

        with tempfile.TemporaryDirectory() as temp:
            manifest, audit, request = self.bound_parent_fixture(
                Path(temp),
                mutate_manifest=lambda value: value.update({"task_type": "relax"}),
                mutate_request=lambda value: value["expected_parent"].update({"task_type": "relax"}),
            )
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(caught.exception.code, "PH_PARENT_IDENTITY_MISMATCH")

        with tempfile.TemporaryDirectory() as temp:
            manifest, audit, request = self.bound_parent_fixture(
                Path(temp),
                mutate_request=lambda value: value["expected_parent"].update({"audit_report_sha256": "f" * 64}),
            )
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(caught.exception.code, "PH_PARENT_HANDOFF_HASH_MISMATCH")

    def test_parent_handoff_gate_structure_and_displacement_mutations_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest, audit, request = self.bound_parent_fixture(
                Path(temp),
                mutate_audit=lambda value: (value.update({"decision": "blocked"}), value["gates"].update({"execution_completion": "fail"})),
            )
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(caught.exception.code, "PH_PARENT_AUDIT_GATE_FAILED")

        with tempfile.TemporaryDirectory() as temp:
            manifest, audit, request = self.bound_parent_fixture(
                Path(temp),
                mutate_manifest=lambda value: value["configuration"]["phonopy_force_parent"].update(
                    {"structure_fingerprint": "sha256:" + "9" * 64}
                ),
            )
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(caught.exception.code, "PH_PARENT_STRUCTURE_MISMATCH")

        with tempfile.TemporaryDirectory() as temp:
            manifest, audit, request = self.bound_parent_fixture(
                Path(temp),
                mutate_manifest=lambda value: value["configuration"]["phonopy_force_parent"].update(
                    {"displacement_id": "disp-999"}
                ),
            )
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(caught.exception.code, "PH_PARENT_DISPLACEMENT_MISMATCH")

    def test_forged_self_declared_audit_and_manifest_audit_drift_do_not_promote(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            def forge(value: dict) -> None:
                value["producer_signature"] = "self-declared-pass"
                value["gates"]["force_acceptance"] = "pass"

            manifest, audit, request = self.bound_parent_fixture(Path(temp), mutate_audit=forge)
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(caught.exception.code, "PH_PARENT_AUDIT_INVALID")

        with tempfile.TemporaryDirectory() as temp:
            manifest, audit, request = self.bound_parent_fixture(
                Path(temp),
                mutate_audit=lambda value: value["evidence"]["input"].update({"sha256": "9" * 64}),
            )
            with self.assertRaises(guard.GuardError) as caught:
                guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(caught.exception.code, "PH_PARENT_ARTIFACT_MISMATCH")

    def test_parent_handoff_uses_verified_single_fd_snapshots_and_cli_refuses_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            manifest, audit, request = self.bound_parent_fixture(directory)
            original = guard._read_json_evidence
            original_manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()

            def read_then_mutate(path: Path, code: str, description: str):
                evidence = original(path, code, description)
                if path == manifest:
                    path.write_bytes(path.read_bytes() + b"\n")
                return evidence

            with mock.patch.object(guard, "_read_json_evidence", side_effect=read_then_mutate):
                report = guard.audit_parent_handoff(manifest, audit, request)
            self.assertEqual(report["raw_evidence"]["run_manifest"]["sha256"], original_manifest_hash)
            self.assertEqual(report["local_consistency"], "pass")

        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            manifest, audit, request = self.bound_parent_fixture(directory)
            original_bytes = manifest.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = guard.main(
                    [
                        "audit-parent-handoff",
                        "--run-manifest", str(manifest),
                        "--audit-report", str(audit),
                        "--handoff-request", str(request),
                        "--out", str(manifest),
                    ]
                )
            self.assertEqual(exit_code, 2)
            self.assertEqual(manifest.read_bytes(), original_bytes)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY"), "requires dirfd no-follow")
    def test_component_walk_survives_intermediate_symlink_swap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            trusted = root / "trusted"
            parked = root / "trusted-original"
            attacker = root / "attacker"
            trusted.mkdir()
            attacker.mkdir()
            expected = {"value": "trusted"}
            (trusted / "evidence.json").write_text(json.dumps(expected), encoding="utf-8")
            (attacker / "evidence.json").write_text(json.dumps({"value": "attacker"}), encoding="utf-8")
            real_open = os.open
            swapped = False

            def racing_open(path, flags, mode=0o777, *, dir_fd=None):
                nonlocal swapped
                if path == "evidence.json" and not swapped:
                    swapped = True
                    trusted.rename(parked)
                    trusted.symlink_to(attacker, target_is_directory=True)
                return real_open(path, flags, mode, dir_fd=dir_fd)

            with mock.patch.object(guard.os, "open", side_effect=racing_open):
                value, _ = guard.read_json(trusted / "evidence.json")
            self.assertTrue(swapped)
            self.assertEqual(value, expected)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires FIFO support")
    def test_fifo_evidence_fails_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fifo = Path(temp) / "evidence.json"
            os.mkfifo(fifo)
            started = time.monotonic()
            with self.assertRaises(guard.GuardError) as caught:
                guard.read_json(fifo)
            self.assertLess(time.monotonic() - started, 1.0)
            self.assertEqual(caught.exception.code, "PH_JSON_INVALID")

    def test_writer_detects_staging_replacement_and_source_as_late_target(self) -> None:
        report = guard.audit_lineage(self.manifest_path)
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            target = directory / "report.json"
            real_link = os.link

            def replace_stage(src, dst, *, src_dir_fd=None, dst_dir_fd=None, follow_symlinks=True):
                os.unlink(src, dir_fd=src_dir_fd)
                descriptor = os.open(src, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=src_dir_fd)
                try:
                    os.write(descriptor, b"attacker-staging\n")
                finally:
                    os.close(descriptor)
                return real_link(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd, follow_symlinks=follow_symlinks)

            with mock.patch.object(guard.os, "link", side_effect=replace_stage):
                with self.assertRaises(guard.GuardError) as caught:
                    guard.write_report(report, target, (self.manifest_path,))
            self.assertEqual(caught.exception.code, "PH_OUTPUT_WRITE_FAILED")
            self.assertEqual(target.read_bytes(), b"attacker-staging\n")
            self.assertEqual(list(directory.glob(".phonopy-report-*")), [])

        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.json"
            source.write_bytes(self.manifest_path.read_bytes())
            target = directory / "report.json"
            report = guard.audit_lineage(source)
            source_bytes = source.read_bytes()
            real_link = os.link

            def source_becomes_target(src, dst, *, src_dir_fd=None, dst_dir_fd=None, follow_symlinks=True):
                source.rename(target)
                return real_link(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd, follow_symlinks=follow_symlinks)

            with mock.patch.object(guard.os, "link", side_effect=source_becomes_target):
                with self.assertRaises(guard.GuardError) as caught:
                    guard.write_report(report, target, (source,))
            self.assertEqual(caught.exception.code, "PH_OUTPUT_EXISTS")
            self.assertEqual(target.read_bytes(), source_bytes)


if __name__ == "__main__":
    unittest.main()
