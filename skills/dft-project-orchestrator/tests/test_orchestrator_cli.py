from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import orchestrator_cli as cli


def gate(status: str = "pass") -> dict:
    check_status = "pass" if status == "pass" else "blocked"
    return {
        "status": status,
        "maximum_action": "request-execution-authorization" if status == "pass" else "plan-only",
        "claim_ceiling": "input_gates_only" if status == "pass" else "no_positive_claim",
        "checks": [
            {
                "check_id": "synthetic-gate",
                "status": check_status,
                "decisive": True,
                "finding_codes": [] if status == "pass" else ["synthetic-blocker"],
                "evidence_refs": [],
                "validated_by": {
                    "actor_type": "deterministic-tool",
                    "actor_id": "synthetic-validator",
                    "role": "validator",
                },
                "validated_utc": "2026-07-19T00:00:00Z",
                "limitations": ["Synthetic test gate."],
            }
        ],
    }


def record_ref(contract: str, record_id: str, digest: str, role: str) -> dict:
    return {
        "contract_name": contract,
        "schema_version": "1.0",
        "record_id": record_id,
        "sha256": digest,
        "role": role,
    }


def request() -> dict:
    return {
        "schema_version": "1.0",
        "contract_name": "execution-request",
        "request_id": "synthetic-request-001",
        "created_utc": "2026-07-18T23:00:00Z",
        "requested_by": {"actor_type": "agent", "actor_id": "synthetic-agent", "role": "requester"},
        "workflow_plan_ref": record_ref("workflow-plan", "synthetic-plan-001", "a" * 64, "workflow-plan"),
        "workflow_step_id": "synthetic-step-001",
        "operation_id": "audit-and-run-scf",
        "execution_mode": "execute",
        "command_kind": "argv",
        "shell": False,
        "argv": ["pw.x", "-in", "scf.in"],
        "working_directory_label": "synthetic-campaign/run-001",
        "environment_profile_id": "synthetic-env-001",
        "resources": {
            "scheduler_profile_id": "synthetic-slurm-001",
            "nodes": 1,
            "mpi_ranks": 4,
            "threads_per_rank": 1,
            "gpus": 0,
            "memory_mb": 4096,
            "walltime_s": 900,
        },
        "inputs": [
            {
                "role": "main-input",
                "label": "scf.in",
                "media_type": "text/plain",
                "format": "qe-input",
                "format_version": "1.0",
                "availability": "present",
                "sha256": "b" * 64,
                "bytes": 128,
                "sensitivity": "public",
                "redistribution": "redistributable",
            }
        ],
        "expected_outputs": [
            {
                "role": "main-output",
                "label": "qe-output.log",
                "media_type": "text/plain",
                "format": "qe-output",
                "format_version": "1.0",
                "availability": "missing",
                "sha256": None,
                "bytes": None,
                "sensitivity": "public",
                "redistribution": "redistributable",
            }
        ],
        "parent_records": [],
        "timeout_s": 900,
        "retry_policy": {"maximum_attempts": 1, "automatic_retry": False, "retryable_finding_codes": []},
        "authorization_requirement": {
            "required": True,
            "side_effects": ["scheduler-submit"],
            "scope_labels": ["synthetic-campaign/run-001"],
            "reason": "Submit one synthetic request.",
        },
        "state": "prepared",
        "blocker_codes": [],
        "gates": gate(),
        "producer": {
            "skill_id": "dft-project-orchestrator",
            "skill_version": "0.1.0-candidate",
            "tool_id": "synthetic-builder",
            "tool_version": "1.0",
            "generated_utc": "2026-07-18T23:00:00Z",
        },
    }


def decision(request_digest: str) -> dict:
    exact = record_ref("execution-request", "synthetic-request-001", request_digest, "execution-subject")
    evidence = copy.deepcopy(exact)
    evidence["role"] = "evidence"
    return {
        "schema_version": "1.0",
        "contract_name": "decision-record",
        "decision_id": "synthetic-decision-001",
        "decision_type": "execution-authorization",
        "subject_ref": exact,
        "outcome": "approved",
        "scientific_acceptance": "not_assessed",
        "decided_by": {"actor_type": "human", "actor_id": "synthetic-owner", "role": "request-owner"},
        "decided_utc": "2026-07-18T23:30:00Z",
        "evidence_ids": ["synthetic-request-001"],
        "evidence_refs": [evidence],
        "rationale": "Approve the exact synthetic request.",
        "scope_labels": ["synthetic-campaign/run-001"],
        "valid_until_utc": "2026-07-20T00:00:00Z",
        "claim_ceiling": "input_gates_only",
        "limitations": ["Synthetic authorization only."],
        "producer": {
            "skill_id": "dft-project-orchestrator",
            "skill_version": "0.1.0-candidate",
            "tool_id": "synthetic-builder",
            "tool_version": "1.0",
            "generated_utc": "2026-07-18T23:30:00Z",
        },
    }


class StrictJsonTests(unittest.TestCase):
    def write_bytes(self, raw: bytes) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "input.json"
        path.write_bytes(raw)
        return path

    def test_rejects_duplicate_key(self) -> None:
        path = self.write_bytes(b'{"a":1,"a":2}')
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(path)

    def test_rejects_concatenated_documents(self) -> None:
        path = self.write_bytes(b'{}{}')
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(path)

    def test_rejects_nan(self) -> None:
        path = self.write_bytes(b'{"x":NaN}')
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(path)

    def test_rejects_overflowing_float(self) -> None:
        path = self.write_bytes(b'{"x":1e999}')
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(path)

    def test_rejects_lone_unicode_surrogate(self) -> None:
        path = self.write_bytes(b'{"x":"\\ud800"}')
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(path)

    def test_rejects_excessive_nesting_before_decode(self) -> None:
        raw = b'{"x":' + b"[" * (cli.MAX_JSON_DEPTH + 1) + b"0" + b"]" * (cli.MAX_JSON_DEPTH + 1) + b"}"
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(self.write_bytes(raw))

    def test_rejects_bom(self) -> None:
        path = self.write_bytes(b'\xef\xbb\xbf{}')
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(path)

    def test_rejects_symlink(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        target = Path(directory.name) / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = Path(directory.name) / "link.json"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(link)

    def test_rejects_hardlink(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        target = Path(directory.name) / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = Path(directory.name) / "hardlink.json"
        try:
            os.link(target, link)
        except OSError:
            self.skipTest("hardlink creation unavailable")
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(link)

    def test_rejects_toctou_mutation(self) -> None:
        path = self.write_bytes(b'{"stable":true}')
        original = cli.os.read
        changed = False

        def mutate_after_read(descriptor: int, size: int) -> bytes:
            nonlocal changed
            raw = original(descriptor, size)
            if raw and not changed:
                changed = True
                path.write_bytes(raw + b" ")
            return raw

        with mock.patch.object(cli.os, "read", new=mutate_after_read):
            with self.assertRaises(cli.InputFailure):
                cli.strict_load(path)

    def test_rejects_same_size_mutation_with_restored_mtime(self) -> None:
        path = self.write_bytes(b'{"stable":true}')
        before = path.stat()
        original = cli.os.read
        changed = False

        def mutate_and_restore_mtime(descriptor: int, size: int) -> bytes:
            nonlocal changed
            raw = original(descriptor, size)
            if raw and not changed:
                changed = True
                path.write_bytes(b'{"stable":null}')
                os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            return raw

        with mock.patch.object(cli.os, "read", new=mutate_and_restore_mtime):
            with self.assertRaises(cli.InputFailure):
                cli.strict_load(path)

    def test_rejects_hardlink_created_during_read(self) -> None:
        path = self.write_bytes(b'{"stable":true}')
        link = path.parent / "late-hardlink.json"
        original = cli.os.read
        changed = False

        def link_after_read(descriptor: int, size: int) -> bytes:
            nonlocal changed
            raw = original(descriptor, size)
            if raw and not changed:
                changed = True
                os.link(path, link)
            return raw

        with mock.patch.object(cli.os, "read", new=link_after_read):
            with self.assertRaises(cli.InputFailure):
                cli.strict_load(path)

    def test_rejects_same_inode_reintroduced_through_symlink_during_read(self) -> None:
        path = self.write_bytes(b'{"stable":true}')
        moved = path.parent / "moved.json"
        original = cli.os.read
        changed = False

        def replace_path_after_read(descriptor: int, size: int) -> bytes:
            nonlocal changed
            raw = original(descriptor, size)
            if raw and not changed:
                changed = True
                path.rename(moved)
                path.symlink_to(moved)
            return raw

        with mock.patch.object(cli.os, "read", new=replace_path_after_read):
            with self.assertRaises(cli.InputFailure):
                cli.strict_load(path)

    def test_rejects_intermediate_directory_symlink_swap(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        trusted = root / "trusted"
        attacker = root / "attacker"
        trusted.mkdir()
        attacker.mkdir()
        path = trusted / "input.json"
        path.write_text('{"origin":"trusted"}', encoding="utf-8")
        (attacker / "input.json").write_text('{"origin":"attacker"}', encoding="utf-8")
        moved = root / "trusted-moved"
        original = cli.os.open
        changed = False

        def swap_before_component_open(
            path_value: str | bytes | os.PathLike[str] | os.PathLike[bytes],
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> int:
            nonlocal changed
            supplied = os.fspath(path_value)
            is_old_full_path_open = dir_fd is None and Path(supplied) == path
            is_component_open = dir_fd is not None and supplied == "trusted"
            if not changed and (is_old_full_path_open or is_component_open):
                changed = True
                trusted.rename(moved)
                trusted.symlink_to(attacker, target_is_directory=True)
            if dir_fd is None:
                return original(path_value, flags, mode)
            return original(path_value, flags, mode, dir_fd=dir_fd)

        with mock.patch.object(cli.os, "open", new=swap_before_component_open):
            with self.assertRaises(cli.InputFailure):
                cli.strict_load(path)

    def test_rejects_intermediate_directory_symlink_swap_during_read(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        trusted = root / "trusted"
        attacker = root / "attacker"
        trusted.mkdir()
        attacker.mkdir()
        path = trusted / "input.json"
        path.write_text('{"origin":"trusted"}', encoding="utf-8")
        (attacker / "input.json").write_text('{"origin":"attacker"}', encoding="utf-8")
        moved = root / "trusted-moved"
        original = cli.os.read
        changed = False

        def swap_after_read(descriptor: int, size: int) -> bytes:
            nonlocal changed
            raw = original(descriptor, size)
            if raw and not changed:
                changed = True
                trusted.rename(moved)
                trusted.symlink_to(attacker, target_is_directory=True)
            return raw

        with mock.patch.object(cli.os, "read", new=swap_after_read):
            with self.assertRaises(cli.InputFailure):
                cli.strict_load(path)

    def test_nested_relative_path_is_supported_by_stable_anchor(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        nested = root / "nested"
        nested.mkdir()
        (nested / "input.json").write_text('{"stable":true}', encoding="utf-8")
        absolute_value, _digest = cli.strict_load(nested / "input.json")
        self.assertTrue(absolute_value["stable"])
        previous = Path.cwd()
        try:
            os.chdir(root)
            value, _digest = cli.strict_load(Path("nested/input.json"))
        finally:
            os.chdir(previous)
        self.assertTrue(value["stable"])

    def test_fifo_without_writer_fails_before_subprocess_timeout(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        fifo = Path(directory.name) / "input.json"
        os.mkfifo(fifo)
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "orchestrator_cli.py"),
                "audit-plan",
                "--plan",
                str(fifo),
            ],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        report = json.loads(completed.stdout)
        self.assertEqual(report["findings"][0]["code"], "ORCH.JSON.INVALID")


class PlanAuditTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))

    def codes(self, value: dict) -> set[str]:
        return {item["code"] for item in cli.audit_plan(value)}

    def test_ready_fixture_passes_and_routes_to_request(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        findings = cli.audit_plan(plan)
        self.assertEqual(findings, [])
        self.assertEqual(
            cli.minimum_next_action(plan, findings),
            "prepare-immutable-execution-request-for-synthetic-step-001",
        )

    def test_cycle_fixture_is_rejected(self) -> None:
        self.assertIn("ORCH.DAG.CYCLE", self.codes(self.load_fixture("cycle-plan.json")))

    def test_long_acyclic_graph_does_not_depend_on_python_recursion(self) -> None:
        step_ids = [f"step-{index:04d}" for index in range(1500)]
        dependencies = {
            step_id: [] if index == len(step_ids) - 1 else [step_ids[index + 1]]
            for index, step_id in enumerate(step_ids)
        }
        self.assertIsNone(cli._cycle(step_ids, dependencies))

    def test_long_cycle_is_reported_without_python_recursion(self) -> None:
        step_ids = [f"step-{index:04d}" for index in range(1500)]
        dependencies = {
            step_id: [step_ids[(index + 1) % len(step_ids)]]
            for index, step_id in enumerate(step_ids)
        }
        cycle = cli._cycle(step_ids, dependencies)
        self.assertIsNotNone(cycle)
        self.assertEqual((cycle[0], cycle[-1], len(cycle)), (step_ids[0], step_ids[0], 1501))

    def test_nonactive_route_blocks(self) -> None:
        for lifecycle in ("development", "planned"):
            with self.subTest(lifecycle=lifecycle):
                plan = self.load_fixture("ready-plan.json")
                plan["steps"][0]["route_lifecycle"] = lifecycle
                findings = cli.audit_plan(plan)
                self.assertIn("ORCH.ROUTE.NOT_ACTIVE", {item["code"] for item in findings})
                self.assertEqual(
                    next(item for item in findings if item["code"] == "ORCH.ROUTE.NOT_ACTIVE")["severity"],
                    "blocking",
                )

    def test_duplicate_step_is_rejected(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["steps"].append(copy.deepcopy(plan["steps"][0]))
        self.assertIn("ORCH.DAG.DUPLICATE_STEP", self.codes(plan))

    def test_unknown_dependency_is_rejected(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["steps"][0]["dependencies"] = ["missing-step"]
        self.assertIn("ORCH.DAG.UNKNOWN_DEPENDENCY", self.codes(plan))

    def test_ready_step_with_blocked_gate_is_blocked(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["steps"][0]["gates"] = gate("blocked")
        self.assertIn("ORCH.STEP.NOT_READY", self.codes(plan))

    def test_side_effect_requires_human_and_lease_policy(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["authorization_policy"]["human_decision_required"] = False
        findings = cli.audit_plan(plan)
        self.assertIn("ORCH.AUTH.POLICY_MISSING", {item["code"] for item in findings})
        self.assertEqual(next(item for item in findings if item["code"] == "ORCH.AUTH.POLICY_MISSING")["severity"], "blocking")

    def test_invalid_producer_is_rejected(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["producer"]["generated_utc"] = "not-a-time"
        self.assertIn("ORCH.CONTRACT.INVALID", self.codes(plan))

    def test_plan_cannot_embed_reverse_request_reference(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["steps"][0]["execution_request_ref"] = record_ref(
            "execution-request", "synthetic-request-001", "a" * 64, "request"
        )
        self.assertIn("ORCH.IDENTITY.MISMATCH", self.codes(plan))

    def test_unknown_gate_maximum_action_is_rejected(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["gates"]["maximum_action"] = "execute-without-review"
        self.assertIn("ORCH.CONTRACT.INVALID", self.codes(plan))

    def test_pass_gate_cannot_carry_adverse_finding(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["gates"]["checks"][0]["finding_codes"] = ["synthetic-adverse"]
        self.assertIn("ORCH.CONTRACT.INVALID", self.codes(plan))

    def test_completed_step_cannot_advance_before_dependency(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        successor = copy.deepcopy(plan["steps"][0])
        successor["step_id"] = "synthetic-step-002"
        successor["dependencies"] = ["synthetic-step-001"]
        successor["state"] = "completed"
        plan["steps"].append(successor)
        self.assertIn("ORCH.STEP.NOT_READY", self.codes(plan))

    def test_completed_workflow_requires_terminal_steps(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["status"] = "completed"
        self.assertIn("ORCH.STATE.CONFLATED", self.codes(plan))

    def test_blocked_workflow_requires_blocked_gate(self) -> None:
        plan = self.load_fixture("ready-plan.json")
        plan["status"] = "blocked"
        plan["blocker_codes"] = ["synthetic-blocker"]
        self.assertIn("ORCH.CONTRACT.INVALID", self.codes(plan))


class AuthorizationTests(unittest.TestCase):
    def materialize(self, request_value: dict, mutate_decision=None) -> tuple[Path, Path]:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        request_path = Path(directory.name) / "request.json"
        request_raw = (json.dumps(request_value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        request_path.write_bytes(request_raw)
        decision_value = decision(hashlib.sha256(request_raw).hexdigest())
        if mutate_decision:
            mutate_decision(decision_value)
        decision_path = Path(directory.name) / "decision.json"
        decision_path.write_text(json.dumps(decision_value, sort_keys=True), encoding="utf-8")
        return request_path, decision_path

    def invoke(self, request_path: Path, decision_path: Path) -> tuple[int, dict]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli.main([
                "authorize-check", "--request", str(request_path), "--decision", str(decision_path),
                "--at-utc", "2026-07-19T00:00:00Z",
            ])
        return code, json.loads(output.getvalue())

    def test_exact_human_authorization_passes_without_executing(self) -> None:
        request_path, decision_path = self.materialize(request())
        code, report = self.invoke(request_path, decision_path)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "pass")
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["minimum_next_action"], "request-bounded-single-use-lease")
        expected = {
            "execution-request": hashlib.sha256(request_path.read_bytes()).hexdigest(),
            "decision-record": hashlib.sha256(decision_path.read_bytes()).hexdigest(),
        }
        self.assertEqual(
            {item["contract_name"]: item["sha256"] for item in report["decisive_evidence"]},
            expected,
        )

    def test_request_bytes_drift_blocks_stale_authorization(self) -> None:
        request_path, decision_path = self.materialize(request())
        request_path.write_bytes(request_path.read_bytes() + b" ")
        code, report = self.invoke(request_path, decision_path)
        self.assertEqual(code, 3)
        self.assertIn("ORCH.AUTH.SUBJECT_MISMATCH", {item["code"] for item in report["findings"]})

    def test_hash_mismatch_blocks(self) -> None:
        def mutate(value: dict) -> None:
            value["subject_ref"]["sha256"] = "f" * 64

        code, report = self.invoke(*self.materialize(request(), mutate))
        self.assertEqual(code, 3)
        self.assertIn("ORCH.AUTH.SUBJECT_MISMATCH", {item["code"] for item in report["findings"]})

    def test_nonhuman_decision_blocks(self) -> None:
        def mutate(value: dict) -> None:
            value["decided_by"]["actor_type"] = "agent"

        code, _report = self.invoke(*self.materialize(request(), mutate))
        self.assertEqual(code, 3)

    def test_expired_decision_blocks(self) -> None:
        def mutate(value: dict) -> None:
            value["valid_until_utc"] = "2026-07-18T23:59:59Z"

        code, _report = self.invoke(*self.materialize(request(), mutate))
        self.assertEqual(code, 3)

    def test_scope_broadening_blocks(self) -> None:
        def mutate(value: dict) -> None:
            value["scope_labels"].append("synthetic-campaign/run-002")

        code, _report = self.invoke(*self.materialize(request(), mutate))
        self.assertEqual(code, 3)

    def test_secret_like_argv_is_contract_invalid(self) -> None:
        value = request()
        secret_value = "api_" + "key=synthetic-placeholder"
        value["argv"].append(secret_value)
        code, report = self.invoke(*self.materialize(value))
        self.assertEqual(code, 2)
        self.assertIn("ORCH.REQUEST.INVALID", {item["code"] for item in report["findings"]})
        self.assertNotIn(secret_value, json.dumps(report))

    def test_nonprinting_control_in_argv_is_contract_invalid(self) -> None:
        value = request()
        value["argv"].append("unsafe\x1bargument")
        code, report = self.invoke(*self.materialize(value))
        self.assertEqual(code, 2)
        self.assertIn("ORCH.REQUEST.INVALID", {item["code"] for item in report["findings"]})

    def test_retry_policy_requires_bounded_unique_finding_codes(self) -> None:
        value = request()
        value["retry_policy"]["retryable_finding_codes"] = ["bad code", "bad code"]
        code, report = self.invoke(*self.materialize(value))
        self.assertEqual(code, 2)
        self.assertIn("ORCH.REQUEST.INVALID", {item["code"] for item in report["findings"]})

    def test_boolean_resource_is_not_an_integer(self) -> None:
        value = request()
        value["resources"]["nodes"] = True
        code, report = self.invoke(*self.materialize(value))
        self.assertEqual(code, 2)
        self.assertIn("ORCH.REQUEST.INVALID", {item["code"] for item in report["findings"]})

    def test_decision_subject_role_is_contract_bound(self) -> None:
        def mutate(value: dict) -> None:
            value["subject_ref"]["role"] = "unrelated"

        code, report = self.invoke(*self.materialize(request(), mutate))
        self.assertEqual(code, 2)
        self.assertIn("ORCH.CONTRACT.INVALID", {item["code"] for item in report["findings"]})

    def test_execution_decision_cannot_claim_review_eligibility(self) -> None:
        def mutate(value: dict) -> None:
            value["claim_ceiling"] = "eligible_for_expert_review"

        code, report = self.invoke(*self.materialize(request(), mutate))
        self.assertEqual(code, 2)
        self.assertIn("ORCH.CONTRACT.INVALID", {item["code"] for item in report["findings"]})

    def test_decision_evidence_id_must_resolve_to_evidence_ref(self) -> None:
        def mutate(value: dict) -> None:
            value["evidence_ids"] = ["unrelated-record"]

        code, report = self.invoke(*self.materialize(request(), mutate))
        self.assertEqual(code, 2)
        self.assertIn("ORCH.CONTRACT.INVALID", {item["code"] for item in report["findings"]})


class CliIntegrationTests(unittest.TestCase):
    def test_audit_is_read_only_and_creates_no_implicit_output(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        plan_path = root / "plan.json"
        plan_path.write_bytes((ROOT / "fixtures" / "ready-plan.json").read_bytes())
        before = {item.name: item.read_bytes() for item in root.iterdir()}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(["audit-plan", "--plan", str(plan_path)]), 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "pass")
        after = {item.name: item.read_bytes() for item in root.iterdir()}
        self.assertEqual(after, before)

    def test_audit_command_emits_one_json_report(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli.main(["audit-plan", "--plan", str(ROOT / "fixtures" / "ready-plan.json")])
        report = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertFalse(report["promotion_authorized"])
        self.assertEqual(report["report_authenticity"], "unsigned-candidate-output")
        expected = hashlib.sha256((ROOT / "fixtures" / "ready-plan.json").read_bytes()).hexdigest()
        self.assertEqual(report["decisive_evidence"][0]["sha256"], expected)

    def test_cycle_command_has_stable_failure_exit(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli.main(["audit-plan", "--plan", str(ROOT / "fixtures" / "cycle-plan.json")])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "fail")

    def test_whitespace_mutation_changes_exact_input_binding(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        original = (ROOT / "fixtures" / "ready-plan.json").read_bytes()
        first = Path(temporary.name) / "first.json"
        second = Path(temporary.name) / "second.json"
        first.write_bytes(original)
        second.write_bytes(original + b" ")
        reports = []
        for path in (first, second):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(cli.main(["audit-plan", "--plan", str(path)]), 0)
            reports.append(json.loads(output.getvalue()))
        self.assertNotEqual(
            reports[0]["decisive_evidence"][0]["sha256"],
            reports[1]["decisive_evidence"][0]["sha256"],
        )

    def test_missing_secret_named_path_is_not_echoed(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        marker = "synthetic-sensitive-path-marker"
        path = Path(temporary.name) / (marker + ".json")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(["audit-plan", "--plan", str(path)]), 2)
        self.assertNotIn(marker, output.getvalue())

    def test_development_claim_ceiling_is_constant_across_commands(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.main(["next-action", "--plan", str(ROOT / "fixtures" / "ready-plan.json")])
        report = json.loads(output.getvalue())
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertFalse(report["execution_authorized"])
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["side_effect_performed"])
        self.assertFalse(report["lease_issued"])
        self.assertFalse(report["workflow_event_emitted"])

    def test_markdown_decision_table_matches_canonical_actions(self) -> None:
        lines = (ROOT / "references" / "decision-table.md").read_text(encoding="utf-8").splitlines()
        rows = [line for line in lines if re.match(r"^\|\s*\d+\s*\|", line)]
        self.assertEqual(len(rows), 11)
        actions = [row.split("|")[5].strip().strip("`") for row in rows]
        self.assertEqual(len(actions), len(set(actions)))
        table = json.loads((ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8"))
        self.assertEqual(actions, [item["minimum_next_action"] for item in table["cases"]])

    def test_canonical_decision_table_is_unique_first_match_and_fail_closed(self) -> None:
        table = json.loads((ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8"))
        self.assertEqual(set(table), {
            "contract_name", "schema_version", "skill_id", "lifecycle",
            "selection_policy", "default_case_id", "current_claim",
            "execution_authorized", "promotion_authorized", "cases",
        })
        self.assertEqual(table["contract_name"], "candidate-decision-table")
        self.assertEqual(table["schema_version"], "1.0")
        self.assertEqual(table["skill_id"], "dft-project-orchestrator")
        self.assertEqual(table["lifecycle"], "development")
        self.assertEqual(table["selection_policy"], "first-match-by-ascending-priority")
        self.assertEqual(table["current_claim"], "no_positive_claim")
        self.assertFalse(table["execution_authorized"])
        self.assertFalse(table["promotion_authorized"])
        cases = table["cases"]
        required = {
            "case_id", "priority", "severity", "condition", "required_evidence",
            "finding_codes", "action_state", "expected_exit_codes", "current_claim",
            "execution_authorized", "promotion_authorized", "minimum_next_action",
        }
        self.assertGreaterEqual(len(cases), 10)
        self.assertTrue(all(set(item) == required for item in cases))
        self.assertEqual([item["priority"] for item in cases], list(range(1, len(cases) + 1)))
        self.assertEqual(len({item["case_id"] for item in cases}), len(cases))
        self.assertEqual(len({item["priority"] for item in cases}), len(cases))
        self.assertEqual(len({item["minimum_next_action"] for item in cases}), len(cases))
        self.assertTrue(all(item["current_claim"] == "no_positive_claim" for item in cases))
        self.assertTrue(all(item["execution_authorized"] is False for item in cases))
        self.assertTrue(all(item["promotion_authorized"] is False for item in cases))
        default = cases[-1]
        self.assertEqual(default["case_id"], table["default_case_id"])
        self.assertEqual(default["required_evidence"], [])
        self.assertEqual(default["action_state"], "local_gate_blocked")
        catalog = json.loads((ROOT / "references" / "finding-catalog.json").read_text(encoding="utf-8"))
        known_codes = {item["code"] for item in catalog["findings"]}
        self.assertTrue(all(set(item["finding_codes"]).issubset(known_codes) for item in cases))
        matching = {cases[1]["case_id"], cases[7]["case_id"]}
        selected = next(item for item in cases if item["case_id"] in matching)
        self.assertEqual(selected["priority"], 2)

    def test_fixture_manifest_tracks_canonical_decision_table(self) -> None:
        manifest = json.loads((ROOT / "references" / "fixture-manifest.json").read_text(encoding="utf-8"))
        paths = {item["path"] for item in manifest["fixtures"]}
        self.assertIn("references/weak-model-decision-table.json", paths)

    def test_untrusted_unknown_field_name_is_not_echoed(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        marker = "synthetic-private-field-marker"
        plan = json.loads((ROOT / "fixtures" / "ready-plan.json").read_text(encoding="utf-8"))
        plan["/" + "home" + "/" + marker] = True
        path = Path(temporary.name) / "plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(["audit-plan", "--plan", str(path)]), 2)
        self.assertNotIn(marker, output.getvalue())

    def test_unsigned_report_mutation_changes_external_digest(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(["audit-plan", "--plan", str(ROOT / "fixtures" / "ready-plan.json")]), 0)
        report = json.loads(output.getvalue())
        original = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
        forged = copy.deepcopy(report)
        forged["execution_authorized"] = True
        altered = json.dumps(forged, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertNotEqual(hashlib.sha256(original).hexdigest(), hashlib.sha256(altered).hexdigest())
        self.assertEqual(report["downstream_binding_required"], "sha256-of-exact-report-bytes-in-external-manifest")

    def test_skill_links_and_cross_contract_manual_are_complete(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for relative in re.findall(r"\]\(([^)]+)\)", skill):
            if "://" not in relative:
                self.assertTrue((ROOT / relative).is_file(), relative)
        manual = (ROOT / "references" / "repository-interface-manual.md").read_text(encoding="utf-8")
        for marker in (
            "Plan, lease, event, evidence, and answer protocol", "execution-request@1.0",
            "execution-lease@1.0", "workflow-event@1.0", "agent-action-envelope@1.0",
            "validate_agent_answer.py", "Dry-run, execute, and acceptable workflow",
        ):
            self.assertIn(marker, manual)


if __name__ == "__main__":
    unittest.main()
