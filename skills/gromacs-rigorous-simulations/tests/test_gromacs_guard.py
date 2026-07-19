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
MODULE_PATH = ROOT / "scripts" / "gromacs_guard.py"
SPEC = importlib.util.spec_from_file_location("vibe_gromacs_guard_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load GROMACS guard from candidate root")
gromacs_guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gromacs_guard
SPEC.loader.exec_module(gromacs_guard)


EXAMPLES = ROOT / "examples"


class GromacsGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def run_plan(self, request: Path | None = None, name: str = "plan.json") -> Path:
        out = self.work / name
        code = gromacs_guard.main(["plan", "--request", str(request or EXAMPLES / "plan-request.json"), "--out", str(out)])
        self.assertEqual(code, 0)
        return out

    def run_input(self, plan: Path, name: str = "input.json", mdp: Path | None = None, topology: Path | None = None) -> Path:
        out = self.work / name
        code = gromacs_guard.main([
            "audit-input", "--plan", str(plan), "--mdp", str(mdp or EXAMPLES / "production.mdp"),
            "--coordinates", str(EXAMPLES / "start.gro"), "--topology", str(topology or EXAMPLES / "topol.top"),
            "--provenance", str(EXAMPLES / "model-provenance.json"), "--out", str(out),
        ])
        self.assertEqual(code, 0)
        return out

    def run_output(self, plan: Path, input_audit: Path, name: str = "output.json") -> Path:
        out = self.work / name
        code = gromacs_guard.main([
            "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
            "--log", str(EXAMPLES / "synthetic-md.log"), "--series", str(EXAMPLES / "thermo.csv"),
            "--out", str(out),
        ])
        self.assertEqual(code, 0)
        return out

    def test_plan_is_stable_and_fail_closed(self) -> None:
        first = self.run_plan(name="first.json")
        second = self.run_plan(name="second.json")
        self.assertEqual(first.read_text(encoding="utf-8"), second.read_text(encoding="utf-8"))
        report = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(report["decision"], "pass")
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["plan_id"], report["metrics"]["plan_id"])

    def test_plan_rejects_missing_seed_and_wrong_units(self) -> None:
        request = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        request["seed"] = {"mode": "explicit", "value": -1}
        request["units"]["length"] = "angstrom"
        path = self.work / "bad-request.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main(["plan", "--request", str(path)])
        self.assertEqual(code, 2)
        codes = {item["code"] for item in json.loads(stream.getvalue())["findings"]}
        self.assertIn("GROMACS.INPUT.SEED_POLICY", codes)
        self.assertIn("GROMACS.UNITS.MISMATCH", codes)

    def test_unknown_version_is_incomplete(self) -> None:
        request = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        request["gromacs_version"] = "2025.4"
        path = self.work / "old-version.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main(["plan", "--request", str(path)])
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(stream.getvalue())["decision"], "incomplete")

    def test_input_fixture_passes_with_topology_closure(self) -> None:
        plan = self.run_plan()
        audit = self.run_input(plan)
        report = json.loads(audit.read_text(encoding="utf-8"))
        self.assertEqual(report["inventory"]["atom_count"], 2)
        self.assertEqual(report["inventory"]["topology_file_count"], 2)
        self.assertEqual(report["inventory"]["expected_final_step"], 12)

    def test_duplicate_mdp_key_blocks_even_when_gromacs_would_override(self) -> None:
        plan = self.run_plan()
        mdp = self.work / "duplicate.mdp"
        mdp.write_text((EXAMPLES / "production.mdp").read_text(encoding="ascii") + "dt = 0.004\n", encoding="ascii")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main([
                "audit-input", "--plan", str(plan), "--mdp", str(mdp),
                "--coordinates", str(EXAMPLES / "start.gro"), "--topology", str(EXAMPLES / "topol.top"),
                "--provenance", str(EXAMPLES / "model-provenance.json"),
            ])
        self.assertEqual(code, 2)
        self.assertIn("GROMACS.INPUT.DUPLICATE_MDP_KEY", {item["code"] for item in json.loads(stream.getvalue())["findings"]})

    def test_include_escape_blocks(self) -> None:
        plan = self.run_plan()
        top = self.work / "escape.top"
        top.write_text('#include "../outside.itp"\n[ system ]\nx\n[ molecules ]\nX 1\n', encoding="ascii")
        (self.work.parent / "outside.itp").write_text("[ moleculetype ]\nX 1\n[ atoms ]\n1 X 1 X X 1 0 1\n", encoding="ascii")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main([
                "audit-input", "--plan", str(plan), "--mdp", str(EXAMPLES / "production.mdp"),
                "--coordinates", str(EXAMPLES / "start.gro"), "--topology", str(top),
                "--provenance", str(EXAMPLES / "model-provenance.json"),
            ])
        self.assertEqual(code, 2)
        self.assertIn("GROMACS.TOPOLOGY.INCLUDE_ESCAPE", {item["code"] for item in json.loads(stream.getvalue())["findings"]})

    def test_full_offline_pipeline_passes_only_technical_gates(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        output_audit = self.run_output(plan, input_audit)
        trajectory = self.work / "trajectory.json"
        code = gromacs_guard.main([
            "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_audit),
            "--output-audit", str(output_audit), "--trajectory", str(EXAMPLES / "trajectory.gro"),
            "--out", str(trajectory),
        ])
        self.assertEqual(code, 0)
        report = json.loads(trajectory.read_text(encoding="utf-8"))
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["future_gate_ceiling"], "technical_run_gates_only")
        self.assertFalse(report["promotion_ready"])
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["metrics"]["handoff_ready"])
        self.assertTrue(report["metrics"]["wrapped_coordinates"])
        self.assertFalse(report["metrics"]["unwrapped_coordinates"])

    def test_minimal_forged_upstream_report_is_rejected(self) -> None:
        plan = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        forged = {
            "engine": "gromacs",
            "command": "plan",
            "decision": "pass",
            "plan_id": gromacs_guard.canonical_hash(plan),
            "plan": plan,
        }
        path = self.work / "minimal-forged-plan.json"
        path.write_text(json.dumps(forged), encoding="utf-8")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main([
                "audit-input", "--plan", str(path), "--mdp", str(EXAMPLES / "production.mdp"),
                "--coordinates", str(EXAMPLES / "start.gro"), "--topology", str(EXAMPLES / "topol.top"),
                "--provenance", str(EXAMPLES / "model-provenance.json"),
            ])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stream.getvalue())["findings"][0]["code"], "GROMACS.UPSTREAM.INVALID_SHAPE")

    def test_semantically_equal_raw_plan_change_breaks_existing_binding(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        value = json.loads(plan.read_text(encoding="utf-8"))
        plan.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main([
                "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
                "--log", str(EXAMPLES / "synthetic-md.log"), "--series", str(EXAMPLES / "thermo.csv"),
            ])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stream.getvalue())["findings"][0]["code"], "GROMACS.UPSTREAM.LINEAGE_MISMATCH")

    def test_self_fabricated_full_report_remains_unsigned_and_unauthorized(self) -> None:
        plan = json.loads((EXAMPLES / "plan-request.json").read_text(encoding="utf-8"))
        plan_id = gromacs_guard.canonical_hash(plan)
        report = gromacs_guard.make_report(
            "plan",
            [],
            [{"role": "plan-request", "label": "fabricated.json", "sha256": "0" * 64}],
            {"plan_id": plan_id},
            extra={"plan_id": plan_id, "plan": plan},
        )
        path = self.work / "self-fabricated-full-report.json"
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        loaded, raw_sha256 = gromacs_guard.load_verified_upstream(path, "plan")
        self.assertEqual(raw_sha256, gromacs_guard.sha256_file(path))
        self.assertEqual(loaded["report_authenticity"], "unsigned-candidate-output")
        self.assertEqual(loaded["claim_ceiling"], "no_positive_claim")
        self.assertFalse(loaded["promotion_ready"])
        self.assertFalse(loaded["promotion_authorized"])
        self.assertFalse(loaded["execution_authorized"])

    def test_truncated_or_concatenated_output_blocks(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        log = self.work / "truncated.log"
        log.write_text("GROMACS: gmx mdrun, version 2026.3\nStep = 8\n", encoding="ascii")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main([
                "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
                "--log", str(log), "--series", str(EXAMPLES / "thermo.csv"),
            ])
        self.assertEqual(code, 2)
        codes = {item["code"] for item in json.loads(stream.getvalue())["findings"]}
        self.assertIn("GROMACS.OUTPUT.TRUNCATED_OR_CONCATENATED", codes)
        self.assertIn("GROMACS.OUTPUT.STEP_MISMATCH", codes)

    def test_constraint_warning_blocks_completion(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        log = self.work / "warning.log"
        log.write_text((EXAMPLES / "synthetic-md.log").read_text(encoding="ascii") + "LINCS WARNING\n", encoding="ascii")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main([
                "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
                "--log", str(log), "--series", str(EXAMPLES / "thermo.csv"),
            ])
        self.assertEqual(code, 2)
        self.assertIn("GROMACS.OUTPUT.ADVERSE_MARKER", {item["code"] for item in json.loads(stream.getvalue())["findings"]})

    def test_low_effective_sample_size_blocks(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        series = self.work / "correlated.csv"
        series.write_text("step,total_energy,temperature\n0,0,280\n2,1,285\n4,2,290\n6,3,295\n8,4,300\n10,5,305\n12,6,310\n", encoding="ascii")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main([
                "audit-output", "--plan", str(plan), "--input-audit", str(input_audit),
                "--log", str(EXAMPLES / "synthetic-md.log"), "--series", str(series),
            ])
        self.assertEqual(code, 2)
        codes = {item["code"] for item in json.loads(stream.getvalue())["findings"]}
        self.assertTrue({"GROMACS.SAMPLING.INSUFFICIENT_ESS", "GROMACS.SAMPLING.UNCERTAINTY_EXCEEDED"}.intersection(codes))

    def test_site_order_mismatch_blocks_trajectory(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        output_audit = self.run_output(plan, input_audit)
        trajectory = self.work / "swapped.gro"
        text = (EXAMPLES / "trajectory.gro").read_text(encoding="ascii")
        trajectory.write_text(text.replace("    1LJ    AR1    1", "    1LJ    XX1    1", 1), encoding="ascii")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main([
                "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_audit),
                "--output-audit", str(output_audit), "--trajectory", str(trajectory),
            ])
        self.assertEqual(code, 2)
        self.assertIn("GROMACS.TRAJECTORY.SITE_ORDER_MISMATCH", {item["code"] for item in json.loads(stream.getvalue())["findings"]})

    def test_binary_trajectory_is_explicitly_unsupported(self) -> None:
        plan = self.run_plan()
        input_audit = self.run_input(plan)
        output_audit = self.run_output(plan, input_audit)
        trajectory = self.work / "traj.xtc"
        trajectory.write_bytes(b"project-authored-not-an-xtc")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main([
                "audit-trajectory", "--plan", str(plan), "--input-audit", str(input_audit),
                "--output-audit", str(output_audit), "--trajectory", str(trajectory),
            ])
        self.assertEqual(code, 3)
        report = json.loads(stream.getvalue())
        self.assertEqual(report["decision"], "incomplete")
        self.assertEqual(report["maturity"], "unsupported")

    def test_report_overwrite_is_refused(self) -> None:
        occupied = self.work / "occupied.json"
        occupied.write_text("preserve", encoding="utf-8")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main(["plan", "--request", str(EXAMPLES / "plan-request.json"), "--out", str(occupied)])
        self.assertEqual(code, 2)
        self.assertEqual(occupied.read_text(encoding="utf-8"), "preserve")
        self.assertEqual(json.loads(stream.getvalue())["findings"][0]["code"], "GROMACS.IO.OVERWRITE")

    def test_ambiguous_json_is_rejected(self) -> None:
        request = self.work / "duplicate.json"
        request.write_text('{"case_id":"a","case_id":"b"}', encoding="utf-8")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main(["plan", "--request", str(request)])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(stream.getvalue())["findings"][0]["code"], "GROMACS.JSON.INVALID")

    def test_fixture_manifest_declares_no_software_output(self) -> None:
        manifest = json.loads((ROOT / "references" / "fixture-manifest.json").read_text(encoding="utf-8"))
        fixture = manifest["fixtures"][0]
        self.assertEqual(fixture["origin"], "project-authored")
        self.assertFalse(fixture["software_generated"])
        self.assertEqual(fixture["scientific_meaning"], "none")
        self.assertEqual(manifest["decision_table"]["contract"], "candidate-decision-table@1.0")
        self.assertTrue(manifest["decision_table"]["redistributable"])

    def test_official_sources_pin_2026_3_and_isolate_rolling_discovery(self) -> None:
        source_index = json.loads((ROOT / "references" / "official-sources.json").read_text(encoding="utf-8"))
        self.assertEqual(source_index["supported_documentary_version"], "2026.3")
        self.assertEqual(source_index["rolling_discovery_url"], "https://manual.gromacs.org/current/index.html")
        for source in source_index["sources"]:
            self.assertTrue(source["url"].startswith("https://manual.gromacs.org/documentation/2026.3/"))
            self.assertNotIn("/current/", source["url"])

    def test_output_cannot_alias_and_destroy_input(self) -> None:
        request = self.work / "request.json"
        request.write_bytes((EXAMPLES / "plan-request.json").read_bytes())
        original = request.read_bytes()
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = gromacs_guard.main(["plan", "--request", str(request), "--out", str(request)])
        self.assertEqual(code, 2)
        self.assertEqual(request.read_bytes(), original)
        self.assertEqual(json.loads(stream.getvalue())["findings"][0]["code"], "GROMACS.IO.OUTPUT_ALIASES_INPUT")

    def test_identity_drift_during_single_fd_read_is_rejected(self) -> None:
        path = self.work / "drift.txt"
        path.write_text("bounded snapshot", encoding="ascii")
        gromacs_guard._reset_snapshot_cache()
        original_fstat = gromacs_guard.os.fstat
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

        with mock.patch.object(gromacs_guard.os, "fstat", side_effect=drifting_fstat):
            with self.assertRaises(gromacs_guard.GuardFailure) as captured:
                gromacs_guard.read_bytes(path, 1024)
        self.assertEqual(captured.exception.code, "GROMACS.IO.CHANGED_DURING_READ")

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
        original_open = gromacs_guard.os.open
        swapped = False

        def racing_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            nonlocal swapped
            if os.fspath(path) == "sub" and kwargs.get("dir_fd") is not None and not swapped:
                subdirectory.rename(moved)
                subdirectory.symlink_to(outside, target_is_directory=True)
                swapped = True
            return original_open(path, flags, *args, **kwargs)

        gromacs_guard._reset_snapshot_cache()
        with mock.patch.object(gromacs_guard.os, "open", side_effect=racing_open):
            with self.assertRaises(gromacs_guard.GuardFailure):
                gromacs_guard.read_bytes(target, 1024)
        gromacs_guard._reset_snapshot_cache()

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
        original_link = gromacs_guard.os.link
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

        with mock.patch.object(gromacs_guard.os, "link", side_effect=substituting_link):
            with self.assertRaises(gromacs_guard.GuardFailure):
                gromacs_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(f".{output.name}.candidate-*.tmp")), [])

    def test_late_target_creation_is_not_overwritten(self) -> None:
        output = self.work / "late-target.json"
        victim = b'{"victim":true}\n'
        original_link = gromacs_guard.os.link
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

        with mock.patch.object(gromacs_guard.os, "link", side_effect=racing_link):
            with self.assertRaises(gromacs_guard.GuardFailure):
                gromacs_guard._atomic_write_new(output, b'{"safe":true}\n')
        self.assertEqual(output.read_bytes(), victim)
        self.assertEqual(list(self.work.glob(f".{output.name}.candidate-*.tmp")), [])

    def test_post_link_exception_rolls_back_only_our_target(self) -> None:
        output = self.work / "post-link-failure.json"
        original_metadata_at = gromacs_guard._metadata_at
        published_target_seen = False

        def failing_metadata_at(directory_fd: int, name: str) -> os.stat_result | None:
            nonlocal published_target_seen
            metadata = original_metadata_at(directory_fd, name)
            if name == output.name and metadata is not None:
                published_target_seen = True
                raise gromacs_guard.GuardFailure("GROMACS.IO.WRITE", "Injected post-link failure.")
            return metadata

        with mock.patch.object(gromacs_guard, "_metadata_at", side_effect=failing_metadata_at):
            with self.assertRaises(gromacs_guard.GuardFailure):
                gromacs_guard._atomic_write_new(output, b'{"safe":true}\n')
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
        self.assertEqual(table["skill_id"], "gromacs-rigorous-simulations")
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
