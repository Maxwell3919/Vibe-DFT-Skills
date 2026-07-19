from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "lasp_evidence_guard.py"
SPEC = importlib.util.spec_from_file_location("vibe_lasp_evidence_guard_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load LASP guard from candidate root")
lasp_evidence_guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lasp_evidence_guard
SPEC.loader.exec_module(lasp_evidence_guard)


EXAMPLES = ROOT / "examples"


class LaspEvidenceGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name).resolve()

    def invoke(self, args: list[str]) -> tuple[int, dict]:
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = lasp_evidence_guard.main(args)
        return code, json.loads(stream.getvalue())

    def plan(self, request: Path | None = None, name: str = "plan.json") -> Path:
        out = self.work / name
        code = lasp_evidence_guard.main(["plan", "--request", str(request or EXAMPLES / "plan-request.json"), "--out", str(out)])
        self.assertEqual(code, 0)
        return out

    def provenance(self, input_path: Path, model_path: Path) -> Path:
        value = {
            "fixture_license": "CC0-1.0",
            "scope": "project-authored test fixture",
            "artifacts": [
                {"label": input_path.name, "sha256": lasp_evidence_guard.sha256_file(input_path), "source_url": "https://example.invalid/test/input", "license_status": "verified"},
                {"label": model_path.name, "sha256": lasp_evidence_guard.sha256_file(model_path), "source_url": "https://example.invalid/test/model", "license_status": "verified"},
            ],
        }
        path = self.work / ("provenance-" + str(len(list(self.work.glob("provenance-*.json")))) + ".json")
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def input_inventory(self, plan: Path, *, input_path: Path | None = None, model_path: Path | None = None, provenance: Path | None = None, documentation: Path | None = None, name: str = "input.json") -> Path:
        out = self.work / name
        code = lasp_evidence_guard.main([
            "audit-input", "--plan", str(plan), "--input", str(input_path or EXAMPLES / "opaque-input.txt"),
            "--model", str(model_path or EXAMPLES / "opaque-model.extxyz"),
            "--provenance", str(provenance or EXAMPLES / "model-provenance.json"),
            "--documentation-attestation", str(documentation or EXAMPLES / "documentation-attestation.json"),
            "--out", str(out),
        ])
        self.assertEqual(code, 3)
        return out

    def output_inventory(self, plan: Path, input_inventory: Path, *, output_path: Path | None = None, attestation: Path | None = None, name: str = "output.json") -> Path:
        out = self.work / name
        code = lasp_evidence_guard.main([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_inventory),
            "--output", str(output_path or EXAMPLES / "synthetic-output.txt"),
            "--attestation", str(attestation or EXAMPLES / "output-attestation.json"), "--out", str(out),
        ])
        self.assertEqual(code, 3)
        return out

    def test_plan_pass_is_stable_but_never_positive(self) -> None:
        first = self.plan(name="one.json")
        second = self.plan(name="two.json")
        self.assertEqual(first.read_text(encoding="utf-8"), second.read_text(encoding="utf-8"))
        report = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(report["decision"], "pass")
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["future_gate_ceiling"], "no_positive_claim")
        self.assertFalse(report["promotion_ready"])
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["report_authenticity"], "unsigned-candidate-output")
        self.assertEqual(report["metrics"]["documented_operational_interfaces"], 1)

    def test_minimal_forged_upstream_is_rejected_by_shape(self) -> None:
        forged = self.work / "forged-plan.json"
        forged.write_text('{"engine":"lasp","command":"plan","decision":"pass"}', encoding="utf-8")
        code, report = self.invoke([
            "audit-input", "--plan", str(forged), "--input", str(EXAMPLES / "opaque-input.txt"),
            "--model", str(EXAMPLES / "opaque-model.extxyz"),
            "--provenance", str(EXAMPLES / "model-provenance.json"),
            "--documentation-attestation", str(EXAMPLES / "documentation-attestation.json"),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "LASP.UPSTREAM.SHAPE")

    def test_semantic_reformat_breaks_raw_lineage_binding(self) -> None:
        plan = self.plan()
        input_inventory = self.input_inventory(plan)
        original = plan.read_bytes()
        value = json.loads(original.decode("utf-8"))
        plan.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        self.assertNotEqual(plan.read_bytes(), original)
        code, report = self.invoke([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_inventory),
            "--output", str(EXAMPLES / "synthetic-output.txt"),
            "--attestation", str(EXAMPLES / "output-attestation.json"),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "LASP.UPSTREAM.MISMATCH")

    def test_self_fabricated_full_report_stays_unsigned_and_no_positive(self) -> None:
        plan_value = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        fabricated = lasp_evidence_guard.make_report(
            "plan", [], [lasp_evidence_guard.evidence(EXAMPLES / "plan-request.json", "plan-request")],
            {"documented_operational_interfaces": 1, "known_evidence_gaps": 9},
            extra={
                "plan_request_sha256": lasp_evidence_guard.sha256_file(EXAMPLES / "plan-request.json"),
                "plan": plan_value,
            },
        )
        path = self.work / "self-fabricated-plan.json"
        path.write_text(json.dumps(fabricated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lasp_evidence_guard._reset_snapshot_cache()
        loaded, raw_sha256 = lasp_evidence_guard.load_upstream_report(path, "plan", {"pass"})
        self.assertEqual(raw_sha256, lasp_evidence_guard.sha256_bytes(path.read_bytes()))
        self.assertEqual(loaded["report_authenticity"], "unsigned-candidate-output")
        self.assertEqual(loaded["claim_ceiling"], "no_positive_claim")
        self.assertFalse(loaded["promotion_ready"])
        self.assertFalse(loaded["promotion_authorized"])
        self.assertFalse(loaded["execution_authorized"])

    def test_other_version_is_incomplete(self) -> None:
        request = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        request["lasp_version"] = "4.0"
        path = self.work / "request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(path)])
        self.assertEqual(code, 3)
        self.assertIn("LASP.PLAN.VERSION_CONTEXT", {item["code"] for item in report["findings"]})

    def test_literature_family_version_is_not_an_exact_distribution(self) -> None:
        request = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        request["lasp_version"] = "3.7"
        path = self.work / "request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(path)])
        self.assertEqual(code, 3)
        self.assertIn("LASP.PLAN.VERSION_CONTEXT", {item["code"] for item in report["findings"]})

    def test_public_page_facts_must_not_be_erased_from_attestation(self) -> None:
        request = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        request["documents"]["public_executable_entry_available"] = False
        path = self.work / "request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(path)])
        self.assertEqual(code, 3)
        self.assertIn("LASP.DOCS.UNREVIEWED_CLAIM", {item["code"] for item in report["findings"]})

    def test_unreviewed_document_claim_is_incomplete(self) -> None:
        request = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        request["documents"]["version_matched_manual_available"] = True
        path = self.work / "request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(path)])
        self.assertEqual(code, 3)
        self.assertIn("LASP.DOCS.UNREVIEWED_CLAIM", {item["code"] for item in report["findings"]})

    def test_execution_authorization_is_rejected(self) -> None:
        request = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        request["authorization"]["execute_external_software"] = True
        path = self.work / "request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(path)])
        self.assertEqual(code, 2)
        self.assertIn("LASP.EXECUTION.NOT_AUTHORIZED", {item["code"] for item in report["findings"]})

    def test_input_inventory_is_useful_but_incomplete(self) -> None:
        plan = self.plan()
        inventory = self.input_inventory(plan)
        report = json.loads(inventory.read_text(encoding="utf-8"))
        self.assertEqual(report["decision"], "incomplete")
        self.assertEqual(report["input_inventory"]["syntax_interpretation"], "none")
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("LASP.DOCS.VERSION_MATCHED_MANUAL_MISSING", codes)
        self.assertIn("LASP.ENVIRONMENT.EXACT_BUILD_UNVERIFIED", codes)
        self.assertIn("LASP.LICENSE.ENGINE_TERMS_UNRESOLVED", codes)
        self.assertNotIn("LASP.DOCS.UNREVIEWED_ATTESTATION", codes)

    def test_public_execution_facts_are_precise_but_fail_closed(self) -> None:
        sources = json.loads((ROOT / "references" / "official-sources.json").read_text(encoding="utf-8"))
        self.assertEqual(sources["distribution_version_context"], "3.7.3")
        facts = sources["verified_public_operational_facts"]
        self.assertEqual(facts["executable_basename"], "lasp")
        self.assertEqual(facts["direct_command"], "[LASP Installation DIR]/Src/lasp")
        self.assertEqual(facts["mpi_example"], "mpirun -np 4 [LASP Installation DIR]/Src/lasp")
        self.assertIn("Intel MPI", facts["environment_summary"])
        self.assertIn("authorized retained complete 3.7.3 manual and examples", sources["not_verified"])
        execution_map = (ROOT / "references" / "execution-and-executable-map.md").read_text(encoding="utf-8")
        self.assertIn("Do not invent `lasp --version`", execution_map)
        self.assertIn("opaque-state-continuation", execution_map)
        self.assertIn("execution_authorized=false", execution_map)

    def test_provenance_hash_mismatch_blocks(self) -> None:
        plan = self.plan()
        value = json.loads((EXAMPLES / "model-provenance.json").read_text(encoding="utf-8"))
        value["artifacts"][0]["sha256"] = "0" * 64
        provenance = self.work / "provenance.json"
        provenance.write_text(json.dumps(value), encoding="utf-8")
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(EXAMPLES / "opaque-input.txt"),
            "--model", str(EXAMPLES / "opaque-model.extxyz"), "--provenance", str(provenance),
            "--documentation-attestation", str(EXAMPLES / "documentation-attestation.json"),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LASP.MODEL.PROVENANCE", {item["code"] for item in report["findings"]})

    def test_documentation_version_mismatch_blocks(self) -> None:
        plan = self.plan()
        value = json.loads((EXAMPLES / "documentation-attestation.json").read_text(encoding="utf-8"))
        value["engine_version"] = "4.0"
        documentation = self.work / "documentation.json"
        documentation.write_text(json.dumps(value), encoding="utf-8")
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(EXAMPLES / "opaque-input.txt"),
            "--model", str(EXAMPLES / "opaque-model.extxyz"), "--provenance", str(EXAMPLES / "model-provenance.json"),
            "--documentation-attestation", str(documentation),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LASP.DOCS.VERSION_MISMATCH", {item["code"] for item in report["findings"]})

    def test_private_path_marker_blocks_without_echoing_path(self) -> None:
        plan = self.plan()
        input_path = self.work / "opaque-input.txt"
        input_path.write_text("private_location=/Users/example/restricted\n", encoding="ascii")
        provenance = self.provenance(input_path, EXAMPLES / "opaque-model.extxyz")
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(input_path), "--model", str(EXAMPLES / "opaque-model.extxyz"),
            "--provenance", str(provenance), "--documentation-attestation", str(EXAMPLES / "documentation-attestation.json"),
        ])
        self.assertEqual(code, 2)
        rendered = json.dumps(report)
        self.assertIn("LASP.PRIVACY.SENSITIVE_MARKER", rendered)
        self.assertNotIn("/Users/example/restricted", rendered)

    def test_output_inventory_never_claims_completion(self) -> None:
        plan = self.plan()
        input_inventory = self.input_inventory(plan)
        output_inventory = self.output_inventory(plan, input_inventory)
        report = json.loads(output_inventory.read_text(encoding="utf-8"))
        self.assertEqual(report["decision"], "incomplete")
        self.assertEqual(report["output_inventory"]["technical_completion"], "unverified")
        self.assertEqual(report["metrics"]["observables_extracted"], 0)

    def test_adverse_output_marker_blocks(self) -> None:
        plan = self.plan()
        input_inventory = self.input_inventory(plan)
        output = self.work / "output.txt"
        output.write_text("fatal synthetic adverse marker\n", encoding="ascii")
        code, report = self.invoke([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_inventory),
            "--output", str(output), "--attestation", str(EXAMPLES / "output-attestation.json"),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LASP.OUTPUT.ADVERSE_MARKER", {item["code"] for item in report["findings"]})

    def test_contradictory_output_attestation_blocks(self) -> None:
        plan = self.plan()
        input_inventory = self.input_inventory(plan)
        value = json.loads((EXAMPLES / "output-attestation.json").read_text(encoding="utf-8"))
        value["software_generated"] = True
        attestation = self.work / "attestation.json"
        attestation.write_text(json.dumps(value), encoding="utf-8")
        code, report = self.invoke([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_inventory),
            "--output", str(EXAMPLES / "synthetic-output.txt"), "--attestation", str(attestation),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LASP.OUTPUT.ATTESTATION", {item["code"] for item in report["findings"]})

    def test_generic_trajectory_integrity_does_not_claim_lasp(self) -> None:
        plan = self.plan()
        input_inventory = self.input_inventory(plan)
        output_inventory = self.output_inventory(plan, input_inventory)
        trajectory_inventory = self.work / "trajectory.json"
        code = lasp_evidence_guard.main([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_inventory),
            "--output-audit", str(output_inventory), "--trajectory", str(EXAMPLES / "trajectory.extxyz"),
            "--frame-index", str(EXAMPLES / "frame-index.json"), "--out", str(trajectory_inventory),
        ])
        self.assertEqual(code, 3)
        report = json.loads(trajectory_inventory.read_text(encoding="utf-8"))
        self.assertTrue(report["metrics"]["generic_format_integrity"])
        self.assertFalse(report["metrics"]["engine_provenance_verified"])
        self.assertEqual(report["trajectory_inventory"]["shared_contract_status"], "not-ready")

    def test_frame_index_hash_mismatch_blocks(self) -> None:
        plan = self.plan()
        input_inventory = self.input_inventory(plan)
        output_inventory = self.output_inventory(plan, input_inventory)
        value = json.loads((EXAMPLES / "frame-index.json").read_text(encoding="utf-8"))
        value["trajectory_sha256"] = "0" * 64
        index = self.work / "frame-index.json"
        index.write_text(json.dumps(value), encoding="utf-8")
        code, report = self.invoke([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_inventory),
            "--output-audit", str(output_inventory), "--trajectory", str(EXAMPLES / "trajectory.extxyz"), "--frame-index", str(index),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LASP.TRAJECTORY.FRAME_INDEX", {item["code"] for item in report["findings"]})

    def test_species_order_change_blocks(self) -> None:
        plan = self.plan()
        input_inventory = self.input_inventory(plan)
        output_inventory = self.output_inventory(plan, input_inventory)
        trajectory = self.work / "trajectory.extxyz"
        text = (EXAMPLES / "trajectory.extxyz").read_text(encoding="ascii")
        position = text.rfind("Si 2.01")
        trajectory.write_text(text[:position] + text[position:].replace("Si 2.01", "C 2.01", 1), encoding="ascii")
        index_value = json.loads((EXAMPLES / "frame-index.json").read_text(encoding="utf-8"))
        index_value["trajectory_sha256"] = lasp_evidence_guard.sha256_file(trajectory)
        index = self.work / "frame-index.json"
        index.write_text(json.dumps(index_value), encoding="utf-8")
        code, report = self.invoke([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_inventory),
            "--output-audit", str(output_inventory), "--trajectory", str(trajectory), "--frame-index", str(index),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LASP.TRAJECTORY.SITE_ORDER", {item["code"] for item in report["findings"]})

    def test_singular_generic_cell_blocks(self) -> None:
        plan = self.plan()
        input_inventory = self.input_inventory(plan)
        output_inventory = self.output_inventory(plan, input_inventory)
        trajectory = self.work / "trajectory.extxyz"
        trajectory.write_text((EXAMPLES / "trajectory.extxyz").read_text(encoding="ascii").replace("10 0 0 0 10 0 0 0 10", "10 0 0 20 0 0 0 0 10"), encoding="ascii")
        index_value = json.loads((EXAMPLES / "frame-index.json").read_text(encoding="utf-8"))
        index_value["trajectory_sha256"] = lasp_evidence_guard.sha256_file(trajectory)
        index = self.work / "frame-index.json"
        index.write_text(json.dumps(index_value), encoding="utf-8")
        code, report = self.invoke([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_inventory),
            "--output-audit", str(output_inventory), "--trajectory", str(trajectory), "--frame-index", str(index),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "LASP.TRAJECTORY.CELL")

    def test_nonmonotonic_frame_index_blocks(self) -> None:
        plan = self.plan()
        input_inventory = self.input_inventory(plan)
        output_inventory = self.output_inventory(plan, input_inventory)
        value = json.loads((EXAMPLES / "frame-index.json").read_text(encoding="utf-8"))
        value["frames"][1]["step"] = 0
        value["frames"][1]["time"] = 0.0
        index = self.work / "frame-index.json"
        index.write_text(json.dumps(value), encoding="utf-8")
        code, report = self.invoke([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_inventory),
            "--output-audit", str(output_inventory), "--trajectory", str(EXAMPLES / "trajectory.extxyz"), "--frame-index", str(index),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LASP.TRAJECTORY.CADENCE", {item["code"] for item in report["findings"]})

    def test_report_overwrite_is_refused(self) -> None:
        occupied = self.work / "occupied.json"
        occupied.write_text("preserve", encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(EXAMPLES / "plan-request.json"), "--out", str(occupied)])
        self.assertEqual(code, 2)
        self.assertEqual(occupied.read_text(encoding="utf-8"), "preserve")
        self.assertEqual(report["findings"][0]["code"], "LASP.IO.OVERWRITE")

    def test_duplicate_json_key_is_rejected(self) -> None:
        request = self.work / "duplicate.json"
        request.write_text('{"case_id":"a","case_id":"b"}', encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(request)])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "LASP.JSON.INVALID")

    def test_fixture_manifest_declares_no_lasp_content(self) -> None:
        manifest = json.loads((ROOT / "references" / "fixture-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["contains_lasp_syntax"])
        self.assertFalse(manifest["contains_lasp_generated_output"])
        self.assertFalse(manifest["contains_third_party_model"])
        self.assertTrue(all(item["redistributable"] for item in manifest["artifacts"]))
        self.assertEqual(manifest["decision_table"]["contract"], "candidate-decision-table@1.0")
        self.assertTrue(manifest["decision_table"]["redistributable"])

    def test_output_cannot_alias_and_destroy_input(self) -> None:
        request = self.work / "request.json"
        request.write_bytes((EXAMPLES / "plan-request.json").read_bytes())
        original = request.read_bytes()
        code, report = self.invoke(["plan", "--request", str(request), "--out", str(request)])
        self.assertEqual(code, 2)
        self.assertEqual(request.read_bytes(), original)
        self.assertEqual(report["findings"][0]["code"], "LASP.IO.OUTPUT_ALIASES_INPUT")

    def test_identity_drift_during_single_fd_read_is_rejected(self) -> None:
        path = self.work / "drift.txt"
        path.write_text("bounded snapshot", encoding="ascii")
        lasp_evidence_guard._reset_snapshot_cache()
        original_fstat = lasp_evidence_guard.os.fstat
        target = path.stat()
        target_calls = 0

        def drifting_fstat(descriptor: int):
            nonlocal target_calls
            value = original_fstat(descriptor)
            if (value.st_dev, value.st_ino) == (target.st_dev, target.st_ino):
                target_calls += 1
            if target_calls == 2 and (value.st_dev, value.st_ino) == (target.st_dev, target.st_ino):
                return types.SimpleNamespace(
                    st_mode=value.st_mode, st_dev=value.st_dev, st_ino=value.st_ino,
                    st_nlink=value.st_nlink, st_size=value.st_size,
                    st_mtime_ns=value.st_mtime_ns + 1, st_ctime_ns=value.st_ctime_ns,
                )
            return value

        with mock.patch.object(lasp_evidence_guard.os, "fstat", side_effect=drifting_fstat):
            with self.assertRaises(lasp_evidence_guard.GuardFailure) as captured:
                lasp_evidence_guard.read_bytes(path, 1024)
        self.assertEqual(captured.exception.code, "LASP.IO.CHANGED_DURING_READ")

    def test_intermediate_directory_symlink_swap_is_rejected(self) -> None:
        subdirectory = self.work / "sub"
        subdirectory.mkdir()
        source = subdirectory / "evidence.json"
        source.write_text("{}\n", encoding="utf-8")
        moved = self.work / "sub-original"
        outside = self.work / "outside"
        outside.mkdir()
        (outside / source.name).write_text('{"outside":true}\n', encoding="utf-8")
        original_open = lasp_evidence_guard.os.open
        swapped = False

        def racing_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            nonlocal swapped
            if path == "sub" and kwargs.get("dir_fd") is not None and not swapped:
                subdirectory.rename(moved)
                subdirectory.symlink_to(outside, target_is_directory=True)
                swapped = True
            return original_open(path, flags, *args, **kwargs)

        lasp_evidence_guard._reset_snapshot_cache()
        with mock.patch.object(lasp_evidence_guard.os, "open", side_effect=racing_open):
            with self.assertRaises(lasp_evidence_guard.GuardFailure):
                lasp_evidence_guard.read_bytes(source, 1024)

    def test_fifo_input_is_rejected_without_blocking(self) -> None:
        fifo = self.work / "blocked.json"
        os.mkfifo(fifo)
        program = """
import importlib.util
import pathlib
import sys
spec = importlib.util.spec_from_file_location('guard_under_test', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.read_bytes(pathlib.Path(sys.argv[2]), 1024)
except module.GuardFailure:
    raise SystemExit(0)
raise SystemExit(1)
"""
        completed = subprocess.run(
            [sys.executable, "-B", "-c", program, str(MODULE_PATH), str(fifo)],
            check=False,
            capture_output=True,
            timeout=1.0,
        )
        self.assertEqual(completed.returncode, 0)

    def test_staging_path_substitution_cannot_publish_attacker_bytes(self) -> None:
        output = self.work / "substitution-report.json"
        original_link = os.link
        substituted = False

        def substituting_link(staging: str, target: str, **kwargs: object) -> None:
            nonlocal substituted
            directory_fd = kwargs["src_dir_fd"]
            assert isinstance(directory_fd, int)
            if not substituted:
                os.unlink(staging, dir_fd=directory_fd)
                attacker_fd = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory_fd)
                os.write(attacker_fd, b"ATTACKER_BYTES")
                os.close(attacker_fd)
                substituted = True
            original_link(staging, target, **kwargs)

        lasp_evidence_guard._reset_snapshot_cache()
        with mock.patch.object(lasp_evidence_guard.os, "link", substituting_link):
            with self.assertRaises(lasp_evidence_guard.GuardFailure):
                lasp_evidence_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(".*.candidate-*.tmp")), [])

    def test_late_target_creation_is_not_overwritten(self) -> None:
        output = self.work / "late-target.json"
        victim = b'{"victim":true}\n'
        original_publish = lasp_evidence_guard._publish_hard_link
        created = False

        def racing_publish(directory_fd: int, staging: str, target: str, staging_fd: int, payload: bytes) -> None:
            nonlocal created
            if not created:
                target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory_fd)
                os.write(target_fd, victim)
                os.close(target_fd)
                created = True
            original_publish(directory_fd, staging, target, staging_fd, payload)

        lasp_evidence_guard._reset_snapshot_cache()
        with mock.patch.object(lasp_evidence_guard, "_publish_hard_link", racing_publish):
            with self.assertRaises(lasp_evidence_guard.GuardFailure):
                lasp_evidence_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertEqual(output.read_bytes(), victim)
        self.assertEqual(list(self.work.glob(".*.candidate-*.tmp")), [])

    def test_post_publish_verification_failure_rolls_back_own_target(self) -> None:
        output = self.work / "post-publish-failure.json"
        original_verify = lasp_evidence_guard._verify_directory_edges
        calls = 0

        def fail_second_verification(directory: Path, edges: object) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise lasp_evidence_guard.GuardFailure("LASP.IO.CHANGED_DURING_READ", "synthetic directory drift")
            original_verify(directory, edges)

        lasp_evidence_guard._reset_snapshot_cache()
        with mock.patch.object(lasp_evidence_guard, "_verify_directory_edges", fail_second_verification):
            with self.assertRaises(lasp_evidence_guard.GuardFailure):
                lasp_evidence_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(".*.candidate-*.tmp")), [])

    def test_immediate_post_link_stat_failure_rolls_back_retained_inode(self) -> None:
        output = self.work / "post-link-stat-failure.json"
        original_link = os.link
        original_stat = os.stat
        original_publish = lasp_evidence_guard._publish_hard_link
        linked = False
        injected = False

        def tracking_link(source: object, target: object, *args: object, **kwargs: object) -> None:
            nonlocal linked
            original_link(source, target, *args, **kwargs)
            linked = True

        def transient_stat(path: object, *args: object, **kwargs: object) -> os.stat_result:
            nonlocal injected
            if linked and not injected and path == output.name:
                injected = True
                raise OSError("injected immediate post-link stat failure")
            return original_stat(path, *args, **kwargs)

        def transient_publish(directory_fd: int, staging: str, target: str, staging_fd: int, payload: bytes) -> os.stat_result:
            with mock.patch.object(lasp_evidence_guard.os, "link", tracking_link), mock.patch.object(lasp_evidence_guard.os, "stat", transient_stat):
                return original_publish(directory_fd, staging, target, staging_fd, payload)

        lasp_evidence_guard._reset_snapshot_cache()
        with mock.patch.object(lasp_evidence_guard, "_publish_hard_link", transient_publish):
            with self.assertRaises(lasp_evidence_guard.GuardFailure):
                lasp_evidence_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertTrue(injected)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(".*.candidate-*.tmp")), [])

    def test_weak_model_decision_table_is_machine_enforceable(self) -> None:
        table = json.loads((ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8"))
        self.assertEqual(table["contract_name"], "candidate-decision-table")
        self.assertEqual(table["schema_version"], "1.0")
        self.assertEqual(table["skill_id"], "lasp-rigorous-simulations")
        self.assertEqual(table["lifecycle"], "development")
        self.assertEqual(table["selection_policy"], "first-match-by-ascending-priority")
        self.assertEqual(table["current_claim"], "no_positive_claim")
        self.assertFalse(table["promotion_authorized"])
        self.assertFalse(table["execution_authorized"])
        cases = table["cases"]
        self.assertGreaterEqual(len(cases), 10)
        identifiers = [item["case_id"] for item in cases]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        priorities = [item["priority"] for item in cases]
        self.assertEqual(priorities, list(range(1, len(cases) + 1)))
        self.assertEqual(len(priorities), len(set(priorities)))
        actions = [item["minimum_next_action"] for item in cases]
        self.assertEqual(len(actions), len(set(actions)))
        self.assertEqual(table["default_case_id"], cases[-1]["case_id"])
        self.assertEqual(cases[-1]["required_evidence"], [])
        self.assertIn(cases[-1]["action_state"], {"needs_evidence", "local_gate_blocked"})
        for item in cases:
            self.assertIn(item["severity"], {"P0", "P1", "P2"})
            self.assertTrue(item["condition"].strip())
            self.assertIsInstance(item["required_evidence"], list)
            self.assertIsInstance(item["finding_codes"], list)
            self.assertIn(item["action_state"], {"needs_evidence", "ready_for_deterministic_check", "local_gate_blocked", "local_gate_passed_limited"})
            self.assertTrue(item["expected_exit_codes"])
            self.assertTrue(item["minimum_next_action"].strip())
            self.assertEqual(item["current_claim"], "no_positive_claim")
            self.assertFalse(item["promotion_authorized"])
            self.assertFalse(item["execution_authorized"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
