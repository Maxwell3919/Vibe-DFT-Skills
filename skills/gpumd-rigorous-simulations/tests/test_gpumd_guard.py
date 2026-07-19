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
MODULE_PATH = ROOT / "scripts" / "gpumd_guard.py"
SPEC = importlib.util.spec_from_file_location("vibe_gpumd_guard_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load GPUMD guard from candidate root")
gpumd_guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gpumd_guard
SPEC.loader.exec_module(gpumd_guard)


EXAMPLES = ROOT / "examples"


class GpumdGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name).resolve()

    def run_plan(self, request: Path | None = None, name: str = "plan.json") -> Path:
        out = self.work / name
        code = gpumd_guard.main(["plan", "--request", str(request or EXAMPLES / "plan-request.json"), "--out", str(out)])
        self.assertEqual(code, 0)
        return out

    def provenance_for(self, run_in: Path, model: Path, potential: Path) -> Path:
        value = json.loads((EXAMPLES / "model-provenance.json").read_text(encoding="utf-8"))
        paths = {item["label"]: path for item, path in zip(value["artifacts"], (run_in, model, potential))}
        for item in value["artifacts"]:
            path = paths[item["label"]]
            item["label"] = path.name
            item["sha256"] = gpumd_guard.sha256_file(path)
        out = self.work / ("prov-" + str(len(list(self.work.glob("prov-*.json")))) + ".json")
        out.write_text(json.dumps(value), encoding="utf-8")
        return out

    def run_input(self, plan: Path, *, run_in: Path | None = None, model: Path | None = None, potential: Path | None = None, provenance: Path | None = None, name: str = "input.json") -> Path:
        run_in = run_in or EXAMPLES / "run.in"
        model = model or EXAMPLES / "model.xyz"
        potential = potential or EXAMPLES / "lj.txt"
        out = self.work / name
        code = gpumd_guard.main([
            "audit-input", "--plan", str(plan), "--run-in", str(run_in),
            "--model", str(model), "--potential", str(potential),
            "--provenance", str(provenance or EXAMPLES / "model-provenance.json"), "--out", str(out),
        ])
        self.assertEqual(code, 0)
        return out

    def run_output(self, plan: Path, input_audit: Path, name: str = "output.json") -> Path:
        out = self.work / name
        code = gpumd_guard.main([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
            "--stdout", str(EXAMPLES / "synthetic-gpumd.stdout"), "--thermo", str(EXAMPLES / "thermo.out"),
            "--out", str(out),
        ])
        self.assertEqual(code, 0)
        return out

    def invoke_stdout(self, args: list[str]) -> tuple[int, dict]:
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gpumd_guard.main(args)
        return code, json.loads(stream.getvalue())

    def test_plan_is_stable_and_no_claim(self) -> None:
        first = self.run_plan(name="one.json")
        second = self.run_plan(name="two.json")
        self.assertEqual(first.read_text(encoding="utf-8"), second.read_text(encoding="utf-8"))
        report = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["report_authenticity"], "unsigned-candidate-output")

    def test_minimal_forged_upstream_is_rejected_by_shape(self) -> None:
        forged = self.work / "forged-plan.json"
        forged.write_text('{"engine":"gpumd","command":"plan","decision":"pass"}', encoding="utf-8")
        code, report = self.invoke_stdout([
            "audit-input", "--plan", str(forged), "--run-in", str(EXAMPLES / "run.in"),
            "--model", str(EXAMPLES / "model.xyz"), "--potential", str(EXAMPLES / "lj.txt"),
            "--provenance", str(EXAMPLES / "model-provenance.json"),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "GPUMD.UPSTREAM.SHAPE")

    def test_semantic_reformat_breaks_raw_lineage_binding(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        original = plan.read_bytes()
        value = json.loads(original.decode("utf-8"))
        plan.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        self.assertNotEqual(plan.read_bytes(), original)
        code, report = self.invoke_stdout([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
            "--stdout", str(EXAMPLES / "synthetic-gpumd.stdout"), "--thermo", str(EXAMPLES / "thermo.out"),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "GPUMD.UPSTREAM.MISMATCH")

    def test_self_fabricated_full_report_stays_unsigned_and_no_positive(self) -> None:
        plan_value = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        fabricated = gpumd_guard.make_report(
            "plan", [], [gpumd_guard.artifact(EXAMPLES / "plan-request.json", "plan-request")],
            {"required_gate_count": 14, "supported_task_count": 1},
            extra={
                "plan_request_sha256": gpumd_guard.sha256_file(EXAMPLES / "plan-request.json"),
                "plan": plan_value,
            },
        )
        path = self.work / "self-fabricated-plan.json"
        path.write_text(json.dumps(fabricated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        gpumd_guard._reset_snapshot_cache()
        loaded, raw_sha256 = gpumd_guard.load_upstream_report(path, "plan", {"pass"})
        self.assertEqual(raw_sha256, gpumd_guard.sha256_bytes(path.read_bytes()))
        self.assertEqual(loaded["report_authenticity"], "unsigned-candidate-output")
        self.assertEqual(loaded["claim_ceiling"], "no_positive_claim")
        self.assertFalse(loaded["promotion_ready"])
        self.assertFalse(loaded["promotion_authorized"])
        self.assertFalse(loaded["execution_authorized"])

    def test_wrong_version_is_incomplete(self) -> None:
        value = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        value["gpumd_version"] = "5.5"
        path = self.work / "version.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        code, report = self.invoke_stdout(["plan", "--request", str(path)])
        self.assertEqual(code, 3)
        self.assertIn("GPUMD.VERSION.UNSUPPORTED", {item["code"] for item in report["findings"]})

    def test_wrong_units_and_seed_block(self) -> None:
        value = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        value["units"]["length"] = "nm"
        value["seed"]["value"] = 0
        path = self.work / "bad.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        code, report = self.invoke_stdout(["plan", "--request", str(path)])
        self.assertEqual(code, 2)
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("GPUMD.UNITS.MISMATCH", codes)
        self.assertIn("GPUMD.SEED.POLICY", codes)

    def test_input_fixture_and_minimum_image_pass(self) -> None:
        plan = self.run_plan()
        audit = self.run_input(plan)
        report = json.loads(audit.read_text(encoding="utf-8"))
        self.assertEqual(report["input"]["atom_count"], 2)
        self.assertEqual(report["input"]["run_blocks"], 1)
        self.assertGreater(min(report["input"]["cell_thickness_angstrom"]), 10.0)

    def test_missing_nonpropagating_control_blocks(self) -> None:
        plan = self.run_plan()
        run_in = self.work / "run.in"
        run_in.write_text((EXAMPLES / "run.in").read_text(encoding="ascii").replace("dump_restart 4\n", ""), encoding="ascii")
        provenance = self.provenance_for(run_in, EXAMPLES / "model.xyz", EXAMPLES / "lj.txt")
        code, report = self.invoke_stdout([
            "audit-input", "--plan", str(plan), "--run-in", str(run_in), "--model", str(EXAMPLES / "model.xyz"),
            "--potential", str(EXAMPLES / "lj.txt"), "--provenance", str(provenance),
        ])
        self.assertEqual(code, 2)
        self.assertIn("GPUMD.RUN_BLOCK.NONPROPAGATING", {item["code"] for item in report["findings"]})

    def test_unknown_command_is_incomplete(self) -> None:
        plan = self.run_plan()
        run_in = self.work / "run.in"
        run_in.write_text("compute_phonon 1 2 3\n" + (EXAMPLES / "run.in").read_text(encoding="ascii"), encoding="ascii")
        provenance = self.provenance_for(run_in, EXAMPLES / "model.xyz", EXAMPLES / "lj.txt")
        code, report = self.invoke_stdout([
            "audit-input", "--plan", str(plan), "--run-in", str(run_in), "--model", str(EXAMPLES / "model.xyz"),
            "--potential", str(EXAMPLES / "lj.txt"), "--provenance", str(provenance),
        ])
        self.assertEqual(code, 3)
        self.assertIn("GPUMD.INPUT.UNSUPPORTED_COMMAND", {item["code"] for item in report["findings"]})

    def test_expansion_is_rejected_incomplete(self) -> None:
        plan = self.run_plan()
        run_in = self.work / "run.in"
        run_in.write_text((EXAMPLES / "run.in").read_text(encoding="ascii").replace("lj.txt", "$MODEL"), encoding="ascii")
        provenance = self.provenance_for(run_in, EXAMPLES / "model.xyz", EXAMPLES / "lj.txt")
        code, report = self.invoke_stdout([
            "audit-input", "--plan", str(plan), "--run-in", str(run_in), "--model", str(EXAMPLES / "model.xyz"),
            "--potential", str(EXAMPLES / "lj.txt"), "--provenance", str(provenance),
        ])
        self.assertEqual(code, 3)
        self.assertEqual(report["findings"][0]["code"], "GPUMD.INPUT.AMBIGUOUS")

    def test_small_periodic_cell_blocks(self) -> None:
        plan = self.run_plan()
        model = self.work / "model.xyz"
        model.write_text((EXAMPLES / "model.xyz").read_text(encoding="ascii").replace("20 0 0 0 20 0 0 0 20", "8 0 0 0 8 0 0 0 8"), encoding="ascii")
        provenance = self.provenance_for(EXAMPLES / "run.in", model, EXAMPLES / "lj.txt")
        code, report = self.invoke_stdout([
            "audit-input", "--plan", str(plan), "--run-in", str(EXAMPLES / "run.in"), "--model", str(model),
            "--potential", str(EXAMPLES / "lj.txt"), "--provenance", str(provenance),
        ])
        self.assertEqual(code, 2)
        self.assertIn("GPUMD.POTENTIAL.MINIMUM_IMAGE", {item["code"] for item in report["findings"]})

    def test_provenance_hash_mismatch_blocks(self) -> None:
        plan = self.run_plan()
        value = json.loads((EXAMPLES / "model-provenance.json").read_text(encoding="utf-8"))
        value["artifacts"][0]["sha256"] = "0" * 64
        provenance = self.work / "bad-provenance.json"
        provenance.write_text(json.dumps(value), encoding="utf-8")
        code, report = self.invoke_stdout([
            "audit-input", "--plan", str(plan), "--run-in", str(EXAMPLES / "run.in"), "--model", str(EXAMPLES / "model.xyz"),
            "--potential", str(EXAMPLES / "lj.txt"), "--provenance", str(provenance),
        ])
        self.assertEqual(code, 2)
        self.assertIn("GPUMD.POTENTIAL.PROVENANCE", {item["code"] for item in report["findings"]})

    def test_full_pipeline_passes_only_technical_gates(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        output_audit = self.run_output(plan, input_audit)
        trajectory = self.work / "trajectory-audit.json"
        code = gpumd_guard.main([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_audit),
            "--output-audit", str(output_audit), "--trajectory", str(EXAMPLES / "trajectory.xyz"), "--out", str(trajectory),
        ])
        self.assertEqual(code, 0)
        report = json.loads(trajectory.read_text(encoding="utf-8"))
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["future_gate_ceiling"], "technical_run_gates_only")
        self.assertFalse(report["promotion_ready"])
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["trajectory"]["shared_contract_status"], "handoff-inventory-only")

    def test_missing_completion_marker_blocks(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        stdout = self.work / "stdout"
        stdout.write_text((EXAMPLES / "synthetic-gpumd.stdout").read_text(encoding="ascii").replace("Finished running GPUMD.\n", ""), encoding="ascii")
        code, report = self.invoke_stdout([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
            "--stdout", str(stdout), "--thermo", str(EXAMPLES / "thermo.out"),
        ])
        self.assertEqual(code, 2)
        self.assertIn("GPUMD.OUTPUT.COMPLETION", {item["code"] for item in report["findings"]})

    def test_nonfinite_thermo_blocks(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        thermo = self.work / "thermo.out"
        thermo.write_text((EXAMPLES / "thermo.out").read_text(encoding="ascii").replace("298.0", "nan", 1), encoding="ascii")
        code, report = self.invoke_stdout([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
            "--stdout", str(EXAMPLES / "synthetic-gpumd.stdout"), "--thermo", str(thermo),
        ])
        self.assertEqual(code, 2)
        self.assertIn("GPUMD.OUTPUT.NONFINITE", {item["code"] for item in report["findings"]})

    def test_high_uncertainty_blocks(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        rows = []
        for index, temperature in enumerate((10, 20, 100, 200, 300, 400)):
            rows.append(f"{temperature} 0.1 {-1 + index * 10} 0 0 0 0 0 0 20 0 0 0 20 0 0 0 20")
        thermo = self.work / "thermo.out"
        thermo.write_text("\n".join(rows) + "\n", encoding="ascii")
        code, report = self.invoke_stdout([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
            "--stdout", str(EXAMPLES / "synthetic-gpumd.stdout"), "--thermo", str(thermo),
        ])
        self.assertEqual(code, 2)
        self.assertTrue({"GPUMD.STATISTICS.LOW_ESS", "GPUMD.STATISTICS.UNCERTAINTY"}.intersection({item["code"] for item in report["findings"]}))

    def test_wrong_trajectory_time_blocks(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        output_audit = self.run_output(plan, input_audit)
        trajectory = self.work / "trajectory.xyz"
        trajectory.write_text((EXAMPLES / "trajectory.xyz").read_text(encoding="ascii").replace("Time=8.00000000", "Time=9.00000000"), encoding="ascii")
        code, report = self.invoke_stdout([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_audit),
            "--output-audit", str(output_audit), "--trajectory", str(trajectory),
        ])
        self.assertEqual(code, 2)
        self.assertIn("GPUMD.TRAJECTORY.CADENCE", {item["code"] for item in report["findings"]})

    def test_missing_unwrapped_position_is_incomplete(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        output_audit = self.run_output(plan, input_audit)
        source = (EXAMPLES / "trajectory.xyz").read_text(encoding="ascii")
        source = source.replace(":unwrapped_position:R:3", "")
        source = "\n".join(" ".join(line.split()[:-3]) if line.startswith("Ar ") else line for line in source.splitlines()) + "\n"
        trajectory = self.work / "wrapped.xyz"
        trajectory.write_text(source, encoding="ascii")
        code, report = self.invoke_stdout([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_audit),
            "--output-audit", str(output_audit), "--trajectory", str(trajectory),
        ])
        self.assertEqual(code, 3)
        self.assertIn("GPUMD.TRAJECTORY.PROPERTY", {item["code"] for item in report["findings"]})

    def test_report_overwrite_is_refused(self) -> None:
        occupied = self.work / "occupied.json"
        occupied.write_text("preserve", encoding="utf-8")
        code, report = self.invoke_stdout(["plan", "--request", str(EXAMPLES / "plan-request.json"), "--out", str(occupied)])
        self.assertEqual(code, 2)
        self.assertEqual(occupied.read_text(encoding="utf-8"), "preserve")
        self.assertEqual(report["findings"][0]["code"], "GPUMD.IO.OVERWRITE")

    def test_duplicate_json_key_is_rejected(self) -> None:
        path = self.work / "duplicate.json"
        path.write_text('{"case_id":"a","case_id":"b"}', encoding="utf-8")
        code, report = self.invoke_stdout(["plan", "--request", str(path)])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "GPUMD.JSON.INVALID")

    def test_fixture_manifest_is_legal_and_not_engine_output(self) -> None:
        manifest = json.loads((ROOT / "references" / "fixture-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["contains_copied_gpumd_output"])
        self.assertFalse(manifest["contains_third_party_model"])
        self.assertTrue(all(item["redistributable"] for item in manifest["artifacts"]))
        self.assertEqual(manifest["decision_table"]["contract"], "candidate-decision-table@1.0")
        self.assertTrue(manifest["decision_table"]["redistributable"])

    def test_output_cannot_alias_and_destroy_input(self) -> None:
        request = self.work / "request.json"
        request.write_bytes((EXAMPLES / "plan-request.json").read_bytes())
        original = request.read_bytes()
        code, report = self.invoke_stdout(["plan", "--request", str(request), "--out", str(request)])
        self.assertEqual(code, 2)
        self.assertEqual(request.read_bytes(), original)
        self.assertEqual(report["findings"][0]["code"], "GPUMD.IO.OUTPUT_ALIASES_INPUT")

    def test_identity_drift_during_single_fd_read_is_rejected(self) -> None:
        path = self.work / "drift.txt"
        path.write_text("bounded snapshot", encoding="ascii")
        gpumd_guard._reset_snapshot_cache()
        original_fstat = gpumd_guard.os.fstat
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

        with mock.patch.object(gpumd_guard.os, "fstat", side_effect=drifting_fstat):
            with self.assertRaises(gpumd_guard.GuardFailure) as captured:
                gpumd_guard.read_bytes(path, 1024)
        self.assertEqual(captured.exception.code, "GPUMD.IO.CHANGED_DURING_READ")

    def test_intermediate_directory_symlink_swap_is_rejected(self) -> None:
        subdirectory = self.work / "sub"
        subdirectory.mkdir()
        source = subdirectory / "evidence.json"
        source.write_text("{}\n", encoding="utf-8")
        moved = self.work / "sub-original"
        outside = self.work / "outside"
        outside.mkdir()
        (outside / source.name).write_text('{"outside":true}\n', encoding="utf-8")
        original_open = gpumd_guard.os.open
        swapped = False

        def racing_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            nonlocal swapped
            if path == "sub" and kwargs.get("dir_fd") is not None and not swapped:
                subdirectory.rename(moved)
                subdirectory.symlink_to(outside, target_is_directory=True)
                swapped = True
            return original_open(path, flags, *args, **kwargs)

        gpumd_guard._reset_snapshot_cache()
        with mock.patch.object(gpumd_guard.os, "open", side_effect=racing_open):
            with self.assertRaises(gpumd_guard.GuardFailure):
                gpumd_guard.read_bytes(source, 1024)

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

        gpumd_guard._reset_snapshot_cache()
        with mock.patch.object(gpumd_guard.os, "link", substituting_link):
            with self.assertRaises(gpumd_guard.GuardFailure):
                gpumd_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(".*.candidate-*.tmp")), [])

    def test_late_target_creation_is_not_overwritten(self) -> None:
        output = self.work / "late-target.json"
        victim = b'{"victim":true}\n'
        original_publish = gpumd_guard._publish_hard_link
        created = False

        def racing_publish(directory_fd: int, staging: str, target: str, staging_fd: int, payload: bytes) -> None:
            nonlocal created
            if not created:
                target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory_fd)
                os.write(target_fd, victim)
                os.close(target_fd)
                created = True
            original_publish(directory_fd, staging, target, staging_fd, payload)

        gpumd_guard._reset_snapshot_cache()
        with mock.patch.object(gpumd_guard, "_publish_hard_link", racing_publish):
            with self.assertRaises(gpumd_guard.GuardFailure):
                gpumd_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertEqual(output.read_bytes(), victim)
        self.assertEqual(list(self.work.glob(".*.candidate-*.tmp")), [])

    def test_post_publish_verification_failure_rolls_back_own_target(self) -> None:
        output = self.work / "post-publish-failure.json"
        original_verify = gpumd_guard._verify_directory_edges
        calls = 0

        def fail_second_verification(directory: Path, edges: object) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise gpumd_guard.GuardFailure("GPUMD.IO.CHANGED_DURING_READ", "synthetic directory drift")
            original_verify(directory, edges)

        gpumd_guard._reset_snapshot_cache()
        with mock.patch.object(gpumd_guard, "_verify_directory_edges", fail_second_verification):
            with self.assertRaises(gpumd_guard.GuardFailure):
                gpumd_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(".*.candidate-*.tmp")), [])

    def test_immediate_post_link_stat_failure_rolls_back_retained_inode(self) -> None:
        output = self.work / "post-link-stat-failure.json"
        original_link = os.link
        original_stat = os.stat
        original_publish = gpumd_guard._publish_hard_link
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
            with mock.patch.object(gpumd_guard.os, "link", tracking_link), mock.patch.object(gpumd_guard.os, "stat", transient_stat):
                return original_publish(directory_fd, staging, target, staging_fd, payload)

        gpumd_guard._reset_snapshot_cache()
        with mock.patch.object(gpumd_guard, "_publish_hard_link", transient_publish):
            with self.assertRaises(gpumd_guard.GuardFailure):
                gpumd_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertTrue(injected)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(".*.candidate-*.tmp")), [])

    def test_weak_model_decision_table_is_machine_enforceable(self) -> None:
        table = json.loads((ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8"))
        self.assertEqual(table["contract_name"], "candidate-decision-table")
        self.assertEqual(table["schema_version"], "1.0")
        self.assertEqual(table["skill_id"], "gpumd-rigorous-simulations")
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

    def test_official_execution_map_pins_real_no_argument_entry(self) -> None:
        sources = json.loads((ROOT / "references" / "official-sources.json").read_text(encoding="utf-8"))
        self.assertEqual(sources["pin"]["version"], "5.3")
        self.assertEqual(sources["pin"]["commit"], gpumd_guard.PINNED_COMMIT)
        self.assertFalse(sources["native_validation"]["gpumd_executable_available"])
        execution_map = (ROOT / "references" / "execution-and-executable-map.md").read_text(encoding="utf-8")
        self.assertIn("<absolute-path-to-v5.3-gpumd> > gpumd.stdout 2> gpumd.stderr", execution_map)
        self.assertIn("does not implement a documented `--version` or `-h`", execution_map)
        self.assertIn("state-file continuation", execution_map)
        self.assertIn("process/scheduler exit state", execution_map)


if __name__ == "__main__":
    unittest.main(verbosity=2)
