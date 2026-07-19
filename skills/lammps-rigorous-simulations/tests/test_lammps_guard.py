from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "lammps_guard.py"
SPEC = importlib.util.spec_from_file_location("vibe_lammps_guard_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load LAMMPS guard from candidate root")
lammps_guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lammps_guard
SPEC.loader.exec_module(lammps_guard)


EXAMPLES = ROOT / "examples"


class LammpsGuardRegressionTests(unittest.TestCase):
    def test_full_pipeline_reaches_trajectory_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            plan = work / "plan.json"
            input_audit = work / "input.json"
            output_audit = work / "output.json"
            trajectory_audit = work / "trajectory.json"
            self.assertEqual(lammps_guard.main(["plan", "--request", str(EXAMPLES / "plan-request.json"), "--out", str(plan)]), 0)
            self.assertEqual(lammps_guard.main([
                "audit-input", "--plan", str(plan), "--input", str(EXAMPLES / "in.lammps"),
                "--data", str(EXAMPLES / "system.data"), "--build-manifest", str(EXAMPLES / "build-manifest.json"),
                "--provenance", str(EXAMPLES / "model-provenance.json"), "--out", str(input_audit),
            ]), 0)
            self.assertEqual(lammps_guard.main([
                "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
                "--log", str(EXAMPLES / "synthetic-log.lammps"), "--out", str(output_audit),
            ]), 0)
            self.assertEqual(lammps_guard.main([
                "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_audit),
                "--output-audit", str(output_audit), "--trajectory", str(EXAMPLES / "trajectory.lammpstrj"),
                "--out", str(trajectory_audit),
            ]), 0)
            report = json.loads(trajectory_audit.read_text(encoding="utf-8"))
            self.assertTrue(report["trajectory"]["orthogonal_unwrapping_reconstructable"])
            self.assertEqual(report["claim_ceiling"], "no_positive_claim")
            self.assertEqual(report["future_gate_ceiling"], "technical_run_gates_only")
            self.assertFalse(report["promotion_ready"])
            self.assertFalse(report["promotion_authorized"])
            self.assertFalse(report["execution_authorized"])


class LammpsGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def invoke(self, args: list[str]) -> tuple[int, dict]:
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = lammps_guard.main(args)
        return code, json.loads(stream.getvalue())

    def plan(self, request: Path | None = None, name: str = "plan.json") -> Path:
        out = self.work / name
        self.assertEqual(lammps_guard.main(["plan", "--request", str(request or EXAMPLES / "plan-request.json"), "--out", str(out)]), 0)
        return out

    def provenance(self, paths: list[Path]) -> Path:
        value = {
            "fixture_license": "CC0-1.0",
            "scope": "project-authored test fixture",
            "artifacts": [
                {
                    "label": path.name,
                    "sha256": lammps_guard.sha256_file(path),
                    "source_url": "https://example.invalid/test/" + path.name,
                    "license_status": "verified",
                }
                for path in paths
            ],
        }
        out = self.work / ("provenance-" + str(len(list(self.work.glob("provenance-*.json")))) + ".json")
        out.write_text(json.dumps(value), encoding="utf-8")
        return out

    def input_audit(self, plan: Path, *, script: Path | None = None, data: Path | None = None, build: Path | None = None, provenance: Path | None = None, name: str = "input.json") -> Path:
        script = script or EXAMPLES / "in.lammps"
        data = data or EXAMPLES / "system.data"
        out = self.work / name
        self.assertEqual(lammps_guard.main([
            "audit-input", "--plan", str(plan), "--input", str(script), "--data", str(data),
            "--build-manifest", str(build or EXAMPLES / "build-manifest.json"),
            "--provenance", str(provenance or EXAMPLES / "model-provenance.json"), "--out", str(out),
        ]), 0)
        return out

    def output_audit(self, plan: Path, input_audit: Path, name: str = "output.json") -> Path:
        out = self.work / name
        self.assertEqual(lammps_guard.main([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
            "--log", str(EXAMPLES / "synthetic-log.lammps"), "--out", str(out),
        ]), 0)
        return out

    def test_plan_is_stable_and_has_no_positive_claim(self) -> None:
        first = self.plan(name="one.json")
        second = self.plan(name="two.json")
        self.assertEqual(first.read_text(encoding="utf-8"), second.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(first.read_text(encoding="utf-8"))["claim_ceiling"], "no_positive_claim")

    def test_unknown_release_is_incomplete(self) -> None:
        request = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        request["lammps_version"] = "3Mar2026"
        path = self.work / "request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(path)])
        self.assertEqual(code, 3)
        self.assertIn("LAMMPS.VERSION.UNSUPPORTED", {item["code"] for item in report["findings"]})

    def test_units_are_not_silently_converted(self) -> None:
        request = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        request["units_style"] = "metal"
        request["unit_map"]["time"] = "ps"
        path = self.work / "request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(path)])
        self.assertEqual(code, 2)
        self.assertIn("LAMMPS.UNITS.MISMATCH", {item["code"] for item in report["findings"]})

    def test_input_fixture_binds_build_and_topology(self) -> None:
        plan = self.plan()
        audit = self.input_audit(plan)
        report = json.loads(audit.read_text(encoding="utf-8"))
        self.assertEqual(report["input"]["site_types"], {"1": 1, "2": 1})
        self.assertEqual(report["input"]["expected_dump_steps"], [0, 4, 8, 12])

    def test_minimal_forged_upstream_report_is_rejected(self) -> None:
        plan = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        forged = {"engine": "lammps", "command": "plan", "decision": "pass", "plan": plan}
        forged["report_fingerprint"] = lammps_guard.canonical_hash(forged)
        path = self.work / "minimal-forged-plan.json"
        path.write_text(json.dumps(forged), encoding="utf-8")
        code, report = self.invoke([
            "audit-input", "--plan", str(path), "--input", str(EXAMPLES / "in.lammps"),
            "--data", str(EXAMPLES / "system.data"), "--build-manifest", str(EXAMPLES / "build-manifest.json"),
            "--provenance", str(EXAMPLES / "model-provenance.json"),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "LAMMPS.UPSTREAM.INVALID_SHAPE")

    def test_semantically_equal_raw_plan_change_breaks_existing_binding(self) -> None:
        plan = self.plan()
        input_audit = self.input_audit(plan)
        value = json.loads(plan.read_text(encoding="utf-8"))
        plan.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        code, report = self.invoke([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
            "--log", str(EXAMPLES / "synthetic-log.lammps"),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "LAMMPS.UPSTREAM.LINEAGE_MISMATCH")

    def test_self_fabricated_full_report_remains_unsigned_and_unauthorized(self) -> None:
        plan = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        report = lammps_guard.make_report(
            "plan",
            [],
            [{"role": "plan-request", "label": "fabricated.json", "sha256": "0" * 64}],
            {"required_gate_count": 15, "supported_task_count": 1},
            extra={"plan_request_sha256": "0" * 64, "plan": plan},
        )
        path = self.work / "self-fabricated-full-report.json"
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        loaded, raw_sha256 = lammps_guard.load_verified_upstream(path, "plan")
        self.assertEqual(raw_sha256, lammps_guard.sha256_file(path))
        self.assertEqual(loaded["report_authenticity"], "unsigned-candidate-output")
        self.assertEqual(loaded["claim_ceiling"], "no_positive_claim")
        self.assertFalse(loaded["promotion_ready"])
        self.assertFalse(loaded["promotion_authorized"])
        self.assertFalse(loaded["execution_authorized"])

    def test_shell_command_is_blocked(self) -> None:
        plan = self.plan()
        script = self.work / "in.lammps"
        script.write_text((EXAMPLES / "in.lammps").read_text(encoding="ascii") + "shell touch marker\n", encoding="ascii")
        provenance = self.provenance([script, EXAMPLES / "system.data"])
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(script), "--data", str(EXAMPLES / "system.data"),
            "--build-manifest", str(EXAMPLES / "build-manifest.json"), "--provenance", str(provenance),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LAMMPS.SCRIPT.UNSAFE_COMMAND", {item["code"] for item in report["findings"]})

    def test_variable_expansion_is_incomplete_without_execution(self) -> None:
        plan = self.plan()
        script = self.work / "in.lammps"
        script.write_text("variable x equal $y\n" + (EXAMPLES / "in.lammps").read_text(encoding="ascii"), encoding="ascii")
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(script), "--data", str(EXAMPLES / "system.data"),
            "--build-manifest", str(EXAMPLES / "build-manifest.json"), "--provenance", str(EXAMPLES / "model-provenance.json"),
        ])
        self.assertEqual(code, 3)
        self.assertEqual(report["findings"][0]["code"], "LAMMPS.SCRIPT.DYNAMIC")

    def test_literal_in_root_include_passes_and_is_hash_bound(self) -> None:
        plan = self.plan()
        script = self.work / "in.lammps"
        include = self.work / "coeff.inc"
        include.write_text("pair_coeff * * 1.0 1.0 2.5\n", encoding="ascii")
        script.write_text((EXAMPLES / "in.lammps").read_text(encoding="ascii").replace("pair_coeff * * 1.0 1.0 2.5\n", "include coeff.inc\n"), encoding="ascii")
        provenance = self.provenance([script, include, EXAMPLES / "system.data"])
        audit = self.input_audit(plan, script=script, provenance=provenance)
        report = json.loads(audit.read_text(encoding="utf-8"))
        self.assertEqual(report["metrics"]["include_files"], 2)
        self.assertIn("coeff.inc", report["input"]["input_closure_hashes"])

    def test_include_escape_is_blocked(self) -> None:
        plan = self.plan()
        root = self.work / "root"
        root.mkdir()
        script = root / "in.lammps"
        outside = self.work / "outside.inc"
        outside.write_text("pair_coeff * * 1.0 1.0 2.5\n", encoding="ascii")
        script.write_text((EXAMPLES / "in.lammps").read_text(encoding="ascii").replace("pair_coeff * * 1.0 1.0 2.5\n", "include ../outside.inc\n"), encoding="ascii")
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(script), "--data", str(EXAMPLES / "system.data"),
            "--build-manifest", str(EXAMPLES / "build-manifest.json"), "--provenance", str(EXAMPLES / "model-provenance.json"),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "LAMMPS.INCLUDE.ESCAPE")

    def test_include_cycle_is_blocked(self) -> None:
        plan = self.plan()
        script = self.work / "in.lammps"
        include = self.work / "cycle.inc"
        script.write_text("include cycle.inc\n" + (EXAMPLES / "in.lammps").read_text(encoding="ascii"), encoding="ascii")
        include.write_text("include in.lammps\n", encoding="ascii")
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(script), "--data", str(EXAMPLES / "system.data"),
            "--build-manifest", str(EXAMPLES / "build-manifest.json"), "--provenance", str(EXAMPLES / "model-provenance.json"),
        ])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "LAMMPS.INCLUDE.CYCLE")

    def test_double_integration_blocks(self) -> None:
        plan = self.plan()
        script = self.work / "in.lammps"
        script.write_text((EXAMPLES / "in.lammps").read_text(encoding="ascii").replace("fix integrate all nve\n", "fix integrate all nve\nfix second all nve\n"), encoding="ascii")
        provenance = self.provenance([script, EXAMPLES / "system.data"])
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(script), "--data", str(EXAMPLES / "system.data"),
            "--build-manifest", str(EXAMPLES / "build-manifest.json"), "--provenance", str(provenance),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LAMMPS.INTEGRATOR.MULTIPLE_OR_MISSING", {item["code"] for item in report["findings"]})

    def test_missing_build_style_blocks(self) -> None:
        plan = self.plan()
        build = json.loads((EXAMPLES / "build-manifest.json").read_text(encoding="utf-8"))
        build["styles"]["pair"] = []
        path = self.work / "build.json"
        path.write_text(json.dumps(build), encoding="utf-8")
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(EXAMPLES / "in.lammps"), "--data", str(EXAMPLES / "system.data"),
            "--build-manifest", str(path), "--provenance", str(EXAMPLES / "model-provenance.json"),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LAMMPS.BUILD.STYLES", {item["code"] for item in report["findings"]})

    def test_minimum_image_violation_blocks(self) -> None:
        plan = self.plan()
        data = self.work / "system.data"
        data.write_text((EXAMPLES / "system.data").read_text(encoding="ascii").replace("0.0 10.0", "0.0 4.0"), encoding="ascii")
        provenance = self.provenance([EXAMPLES / "in.lammps", data])
        code, report = self.invoke([
            "audit-input", "--plan", str(plan), "--input", str(EXAMPLES / "in.lammps"), "--data", str(data),
            "--build-manifest", str(EXAMPLES / "build-manifest.json"), "--provenance", str(provenance),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LAMMPS.MODEL.MINIMUM_IMAGE", {item["code"] for item in report["findings"]})

    def test_warning_in_log_blocks(self) -> None:
        plan = self.plan()
        input_audit = self.input_audit(plan)
        log = self.work / "log.lammps"
        log.write_text((EXAMPLES / "synthetic-log.lammps").read_text(encoding="ascii") + "WARNING: synthetic adverse marker\n", encoding="ascii")
        code, report = self.invoke(["audit-output", "--plan", str(plan), "--input-audit", str(input_audit), "--log", str(log)])
        self.assertEqual(code, 2)
        self.assertIn("LAMMPS.OUTPUT.ADVERSE_MARKER", {item["code"] for item in report["findings"]})

    def test_missing_loop_marker_blocks(self) -> None:
        plan = self.plan()
        input_audit = self.input_audit(plan)
        log = self.work / "log.lammps"
        lines = [line for line in (EXAMPLES / "synthetic-log.lammps").read_text(encoding="ascii").splitlines() if not line.startswith("Loop time")]
        log.write_text("\n".join(lines) + "\n", encoding="ascii")
        code, report = self.invoke(["audit-output", "--plan", str(plan), "--input-audit", str(input_audit), "--log", str(log)])
        self.assertEqual(code, 2)
        self.assertIn("LAMMPS.OUTPUT.COMPLETION", {item["code"] for item in report["findings"]})

    def test_large_uncertainty_blocks(self) -> None:
        plan = self.plan()
        input_audit = self.input_audit(plan)
        text = (EXAMPLES / "synthetic-log.lammps").read_text(encoding="ascii")
        text = text.replace("6 1.00 -1.10 0.20 -0.90 0.010", "6 10.0 -10.0 0.2 -9.8 0.010")
        text = text.replace("8 1.01 -0.90 0.21 -0.69 0.010", "8 20.0 10.0 0.2 10.2 0.010")
        text = text.replace("10 0.99 -1.10 0.19 -0.91 0.010", "10 30.0 -10.0 0.2 -9.8 0.010")
        text = text.replace("12 1.00 -1.00 0.20 -0.80 0.010", "12 40.0 10.0 0.2 10.2 0.010")
        log = self.work / "log.lammps"
        log.write_text(text, encoding="ascii")
        code, report = self.invoke(["audit-output", "--plan", str(plan), "--input-audit", str(input_audit), "--log", str(log)])
        self.assertEqual(code, 2)
        self.assertTrue({"LAMMPS.STATISTICS.LOW_ESS", "LAMMPS.STATISTICS.UNCERTAINTY"}.intersection({item["code"] for item in report["findings"]}))

    def test_trajectory_site_type_change_blocks(self) -> None:
        plan = self.plan()
        input_audit = self.input_audit(plan)
        output_audit = self.output_audit(plan, input_audit)
        trajectory = self.work / "trajectory.lammpstrj"
        trajectory.write_text((EXAMPLES / "trajectory.lammpstrj").read_text(encoding="ascii").replace("2 1 7.98", "2 2 7.98", 1), encoding="ascii")
        code, report = self.invoke([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_audit),
            "--output-audit", str(output_audit), "--trajectory", str(trajectory),
        ])
        self.assertEqual(code, 2)
        self.assertIn("LAMMPS.TRAJECTORY.SITE_TYPE", {item["code"] for item in report["findings"]})

    def test_triclinic_dump_is_incomplete_not_guessed(self) -> None:
        plan = self.plan()
        input_audit = self.input_audit(plan)
        output_audit = self.output_audit(plan, input_audit)
        trajectory = self.work / "trajectory.lammpstrj"
        trajectory.write_text((EXAMPLES / "trajectory.lammpstrj").read_text(encoding="ascii").replace("ITEM: BOX BOUNDS pp pp pp", "ITEM: BOX BOUNDS xy xz yz pp pp pp", 1), encoding="ascii")
        code, report = self.invoke([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_audit),
            "--output-audit", str(output_audit), "--trajectory", str(trajectory),
        ])
        self.assertEqual(code, 3)
        self.assertEqual(report["findings"][0]["code"], "LAMMPS.TRAJECTORY.UNSUPPORTED_BOX")

    def test_report_overwrite_is_refused(self) -> None:
        occupied = self.work / "occupied.json"
        occupied.write_text("preserve", encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(EXAMPLES / "plan-request.json"), "--out", str(occupied)])
        self.assertEqual(code, 2)
        self.assertEqual(occupied.read_text(encoding="utf-8"), "preserve")
        self.assertEqual(report["findings"][0]["code"], "LAMMPS.IO.OVERWRITE")

    def test_duplicate_json_key_is_rejected(self) -> None:
        request = self.work / "duplicate.json"
        request.write_text('{"case_id":"a","case_id":"b"}', encoding="utf-8")
        code, report = self.invoke(["plan", "--request", str(request)])
        self.assertEqual(code, 2)
        self.assertEqual(report["findings"][0]["code"], "LAMMPS.JSON.INVALID")

    def test_fixture_manifest_declares_legal_synthetic_origin(self) -> None:
        manifest = json.loads((ROOT / "references" / "fixture-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["contains_copied_lammps_output"])
        self.assertFalse(manifest["contains_third_party_potential"])
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
        self.assertEqual(report["findings"][0]["code"], "LAMMPS.IO.OUTPUT_ALIASES_INPUT")

    def test_identity_drift_during_single_fd_read_is_rejected(self) -> None:
        path = self.work / "drift.txt"
        path.write_text("bounded snapshot", encoding="ascii")
        lammps_guard._reset_snapshot_cache()
        original_fstat = lammps_guard.os.fstat
        regular_calls = 0

        def drifting_fstat(descriptor: int):
            nonlocal regular_calls
            value = original_fstat(descriptor)
            if stat.S_ISREG(value.st_mode):
                regular_calls += 1
            if stat.S_ISREG(value.st_mode) and regular_calls == 2:
                return types.SimpleNamespace(
                    st_mode=value.st_mode, st_dev=value.st_dev, st_ino=value.st_ino,
                    st_nlink=value.st_nlink, st_size=value.st_size,
                    st_mtime_ns=value.st_mtime_ns + 1, st_ctime_ns=value.st_ctime_ns,
                )
            return value

        with mock.patch.object(lammps_guard.os, "fstat", side_effect=drifting_fstat):
            with self.assertRaises(lammps_guard.GuardFailure) as captured:
                lammps_guard.read_bytes(path, 1024)
        self.assertEqual(captured.exception.code, "LAMMPS.IO.CHANGED_DURING_READ")

    def test_intermediate_directory_symlink_swap_is_rejected(self) -> None:
        base = self.work / "base"
        subdirectory = base / "sub"
        outside = self.work / "outside"
        subdirectory.mkdir(parents=True)
        outside.mkdir()
        target = subdirectory / "evidence.json"
        target.write_text('{"inside":true}\n', encoding="utf-8")
        (outside / target.name).write_text('{"outside":true}\n', encoding="utf-8")
        moved = base / "sub-original"
        original_open = lammps_guard.os.open
        swapped = False

        def racing_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            nonlocal swapped
            if os.fspath(path) == "sub" and kwargs.get("dir_fd") is not None and not swapped:
                subdirectory.rename(moved)
                subdirectory.symlink_to(outside, target_is_directory=True)
                swapped = True
            return original_open(path, flags, *args, **kwargs)

        lammps_guard._reset_snapshot_cache()
        with mock.patch.object(lammps_guard.os, "open", side_effect=racing_open):
            with self.assertRaises(lammps_guard.GuardFailure):
                lammps_guard.read_bytes(target, 1024)
        lammps_guard._reset_snapshot_cache()

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
        output = self.work / "substitution.json"
        original_link = lammps_guard.os.link
        substituted = False

        def substituting_link(source: object, target: object, *args: object, **kwargs: object) -> None:
            nonlocal substituted
            if not substituted:
                directory_fd = kwargs["src_dir_fd"]
                os.unlink(source, dir_fd=directory_fd)
                attacker_fd = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory_fd)
                os.write(attacker_fd, b"ATTACKER_BYTES")
                os.close(attacker_fd)
                substituted = True
            original_link(source, target, *args, **kwargs)

        with mock.patch.object(lammps_guard.os, "link", side_effect=substituting_link):
            with self.assertRaises(lammps_guard.GuardFailure):
                lammps_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(f".{output.name}.candidate-*.tmp")), [])

    def test_late_target_creation_is_not_overwritten(self) -> None:
        output = self.work / "late-target.json"
        victim = b'{"victim":true}\n'
        original_link = lammps_guard.os.link
        created = False

        def racing_link(source: object, target: object, *args: object, **kwargs: object) -> None:
            nonlocal created
            if not created:
                directory_fd = kwargs["dst_dir_fd"]
                target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory_fd)
                os.write(target_fd, victim)
                os.close(target_fd)
                created = True
            original_link(source, target, *args, **kwargs)

        with mock.patch.object(lammps_guard.os, "link", side_effect=racing_link):
            with self.assertRaises(lammps_guard.GuardFailure):
                lammps_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertEqual(output.read_bytes(), victim)
        self.assertEqual(list(self.work.glob(f".{output.name}.candidate-*.tmp")), [])

    def test_post_link_exception_rolls_back_only_our_target(self) -> None:
        output = self.work / "post-link-failure.json"
        original_metadata_at = lammps_guard._metadata_at
        published_target_seen = False

        def failing_metadata_at(directory_fd: int, name: str) -> os.stat_result | None:
            nonlocal published_target_seen
            metadata = original_metadata_at(directory_fd, name)
            if name == output.name and metadata is not None:
                published_target_seen = True
                raise lammps_guard.GuardFailure("LAMMPS.IO.WRITE", "Injected post-link failure.")
            return metadata

        with mock.patch.object(lammps_guard, "_metadata_at", side_effect=failing_metadata_at):
            with self.assertRaises(lammps_guard.GuardFailure):
                lammps_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertTrue(published_target_seen)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(f".{output.name}.candidate-*.tmp")), [])

    def test_weak_model_decision_table_is_machine_enforceable(self) -> None:
        table = json.loads((ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8"))
        self.assertEqual(
            set(table),
            {"contract_name", "schema_version", "skill_id", "lifecycle", "selection_policy", "default_case_id", "current_claim", "execution_authorized", "promotion_authorized", "cases"},
        )
        self.assertEqual(table["contract_name"], "candidate-decision-table")
        self.assertEqual(table["schema_version"], "1.0")
        self.assertEqual(table["skill_id"], "lammps-rigorous-simulations")
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
            self.assertEqual(
                set(item),
                {"case_id", "priority", "severity", "condition", "required_evidence", "finding_codes", "action_state", "expected_exit_codes", "current_claim", "execution_authorized", "promotion_authorized", "minimum_next_action"},
            )
            self.assertIn(item["severity"], {"P0", "P1", "P2"})
            self.assertTrue(item["condition"].strip())
            self.assertIsInstance(item["required_evidence"], list)
            self.assertIsInstance(item["finding_codes"], list)
            self.assertIn(item["action_state"], {"needs_evidence", "needs_authorization", "ready_for_deterministic_check", "local_gate_blocked", "local_gate_passed_limited"})
            self.assertTrue(item["expected_exit_codes"])
            self.assertTrue(item["minimum_next_action"].strip())
            self.assertEqual(item["current_claim"], "no_positive_claim")
            self.assertFalse(item["promotion_authorized"])
            self.assertFalse(item["execution_authorized"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
