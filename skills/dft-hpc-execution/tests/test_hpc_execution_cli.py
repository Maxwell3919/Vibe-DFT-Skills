from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import hpc_execution_cli as cli


def fixture(name: str) -> dict:
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> str:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class Bundle:
    def __init__(self, scheduler: str = "slurm") -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.request = fixture("slurm-request.json")
        self.decision = fixture("slurm-decision.json")
        self.lease = fixture("slurm-lease.json")
        profile = {
            "slurm": "synthetic-slurm-001",
            "openpbs": "synthetic-pbs-001",
            "local": "synthetic-local-001",
        }[scheduler]
        self.request["resources"]["scheduler_profile_id"] = profile
        self.lease["grant"]["scheduler_profile_ids"] = [profile]
        self.request_path = root / "request.json"
        self.decision_path = root / "decision.json"
        self.lease_path = root / "lease.json"
        self.rebind()

    def close(self) -> None:
        self.temporary.cleanup()

    def rebind(self) -> None:
        request_sha = write_json(self.request_path, self.request)
        for field in ("subject_ref",):
            self.decision[field]["record_id"] = self.request["request_id"]
            self.decision[field]["sha256"] = request_sha
        self.decision["evidence_refs"][0]["record_id"] = self.request["request_id"]
        self.decision["evidence_refs"][0]["sha256"] = request_sha
        decision_sha = write_json(self.decision_path, self.decision)
        self.lease["request_ref"]["record_id"] = self.request["request_id"]
        self.lease["request_ref"]["sha256"] = request_sha
        self.lease["authorization_decision_ref"]["record_id"] = self.decision["decision_id"]
        self.lease["authorization_decision_ref"]["sha256"] = decision_sha
        self.lease["grant"]["argv_sha256"] = cli.canonical_argv_sha256(self.request["argv"])
        self.lease["grant"]["input_sha256"] = [item["sha256"] for item in self.request["inputs"]]
        self.lease["grant"]["output_labels"] = [item["label"] for item in self.request["expected_outputs"]]
        self.lease["grant"]["environment_profile_ids"] = [self.request["environment_profile_id"]]
        profile = self.request["resources"]["scheduler_profile_id"]
        self.lease["grant"]["scheduler_profile_ids"] = [] if profile is None else [profile]
        self.lease["grant"]["side_effects"] = list(self.request["authorization_requirement"]["side_effects"])
        self.lease["grant"]["resource_ceiling"] = {
            key: self.request["resources"][key] for key in cli.LEASE_RESOURCE_KEYS
        }
        write_json(self.lease_path, self.lease)


def invoke(arguments: list[str]) -> tuple[int, dict]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = cli.main(arguments)
    return code, json.loads(output.getvalue())


class StrictJsonTests(unittest.TestCase):
    def write_bytes(self, raw: bytes) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "value.json"
        path.write_bytes(raw)
        return path

    def test_duplicate_key_rejected(self) -> None:
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(self.write_bytes(b'{"x":1,"x":2}'))

    def test_concatenated_json_rejected(self) -> None:
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(self.write_bytes(b'{}{}'))

    def test_bom_rejected(self) -> None:
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(self.write_bytes(b'\xef\xbb\xbf{}'))

    def test_non_object_rejected(self) -> None:
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(self.write_bytes(b'[]'))

    def test_overflowing_float_rejected(self) -> None:
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(self.write_bytes(b'{"x":1e999}'))

    def test_lone_unicode_surrogate_rejected(self) -> None:
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(self.write_bytes(b'{"x":"\\ud800"}'))

    def test_excessive_nesting_rejected_before_decode(self) -> None:
        raw = b'{"x":' + b"[" * (cli.MAX_JSON_DEPTH + 1) + b"0" + b"]" * (cli.MAX_JSON_DEPTH + 1) + b"}"
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(self.write_bytes(raw))

    def test_symlink_rejected(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        target = Path(temporary.name) / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = Path(temporary.name) / "link.json"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(link)

    def test_hardlink_rejected(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        target = Path(temporary.name) / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = Path(temporary.name) / "hardlink.json"
        try:
            os.link(target, link)
        except OSError:
            self.skipTest("hardlink creation unavailable")
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(link)

    def test_toctou_mutation_rejected(self) -> None:
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

    def test_same_size_mutation_with_restored_mtime_rejected(self) -> None:
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

    def test_hardlink_created_during_read_rejected(self) -> None:
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

    def test_same_inode_reintroduced_through_symlink_during_read_rejected(self) -> None:
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

    def test_intermediate_directory_symlink_swap_rejected(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
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

    def test_intermediate_directory_symlink_swap_during_read_rejected(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
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

    def test_nested_relative_path_uses_stable_directory_anchor(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
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
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        fifo = Path(temporary.name) / "input.json"
        os.mkfifo(fifo)
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "hpc_execution_cli.py"),
                "validate-request",
                "--request",
                str(fifo),
            ],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        report = json.loads(completed.stdout)
        self.assertEqual(report["findings"][0]["code"], "HPC.JSON.INVALID")


class RequestValidationTests(unittest.TestCase):
    def codes(self, request: dict) -> tuple[set[str], set[str]]:
        invalid, blocked = cli.validate_request(request)
        return {item["code"] for item in invalid}, {item["code"] for item in blocked}

    def test_synthetic_request_passes(self) -> None:
        self.assertEqual(self.codes(fixture("slurm-request.json")), (set(), set()))

    def test_shell_executable_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["argv"] = ["bash", "-c", "pw.x -in scf.in"]
        self.assertIn("HPC.COMMAND.UNSAFE", self.codes(value)[0])

    def test_newline_in_argv_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["argv"].append("bad\nargument")
        self.assertIn("HPC.COMMAND.UNSAFE", self.codes(value)[0])

    def test_nonprinting_control_in_argv_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["argv"].append("bad\x1bargument")
        self.assertIn("HPC.COMMAND.UNSAFE", self.codes(value)[0])

    def test_secret_like_argument_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["argv"].append("access_" + "token=synthetic-placeholder")
        self.assertIn("HPC.COMMAND.UNSAFE", self.codes(value)[0])

    def test_absolute_working_path_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["working_directory_label"] = "/" + "home" + "/synthetic/run"
        self.assertIn("HPC.REQUEST.INVALID", self.codes(value)[0])

    def test_missing_input_hash_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["inputs"][0]["sha256"] = None
        self.assertIn("HPC.ARTIFACT.INVALID", self.codes(value)[0])

    def test_present_expected_output_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["expected_outputs"][0]["availability"] = "present"
        value["expected_outputs"][0]["sha256"] = "c" * 64
        value["expected_outputs"][0]["bytes"] = 1
        self.assertIn("HPC.ARTIFACT.INVALID", self.codes(value)[0])

    def test_automatic_retry_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["retry_policy"]["automatic_retry"] = True
        self.assertIn("HPC.REQUEST.INVALID", self.codes(value)[0])

    def test_unresolved_nonsynthetic_profile_blocks(self) -> None:
        value = fixture("slurm-request.json")
        value["environment_profile_id"] = "unknown-production-profile"
        self.assertIn("HPC.PROFILE.UNRESOLVED", self.codes(value)[1])

    def test_unknown_top_level_field_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["environment"] = {"TOKEN": "synthetic"}
        self.assertIn("HPC.REQUEST.INVALID", self.codes(value)[0])

    def test_invalid_producer_rejected(self) -> None:
        value = fixture("slurm-request.json")
        value["producer"]["generated_utc"] = "not-a-time"
        self.assertIn("HPC.REQUEST.INVALID", self.codes(value)[0])

    def test_unknown_synthetic_environment_profile_blocks(self) -> None:
        value = fixture("slurm-request.json")
        value["environment_profile_id"] = "synthetic-unregistered-env"
        self.assertIn("HPC.PROFILE.UNRESOLVED", self.codes(value)[1])

    def test_workflow_plan_reference_role_is_bound(self) -> None:
        value = fixture("slurm-request.json")
        value["workflow_plan_ref"]["role"] = "unrelated"
        self.assertIn("HPC.REQUEST.INVALID", self.codes(value)[0])

    def test_retry_finding_codes_are_unique_safe_ids(self) -> None:
        value = fixture("slurm-request.json")
        value["retry_policy"]["retryable_finding_codes"] = ["bad code", "bad code"]
        self.assertIn("HPC.REQUEST.INVALID", self.codes(value)[0])

    def test_boolean_resource_is_not_an_integer(self) -> None:
        value = fixture("slurm-request.json")
        value["resources"]["nodes"] = True
        self.assertIn("HPC.REQUEST.INVALID", self.codes(value)[0])

    def test_pass_gate_cannot_carry_adverse_finding(self) -> None:
        value = fixture("slurm-request.json")
        value["gates"]["checks"][0]["finding_codes"] = ["synthetic-adverse"]
        self.assertIn("HPC.REQUEST.INVALID", self.codes(value)[0])


class AuthorizationLeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = Bundle()
        self.addCleanup(self.bundle.close)

    def validate(self) -> tuple[list[dict], list[dict]]:
        request, request_sha = cli.strict_load(self.bundle.request_path)
        decision, decision_sha = cli.strict_load(self.bundle.decision_path)
        lease, lease_sha = cli.strict_load(self.bundle.lease_path)
        at = cli._parse_utc("2026-07-19T00:00:00Z")
        assert at is not None
        decision_invalid, decision_blocked = cli.validate_decision(decision, request, request_sha, at)
        lease_invalid, lease_blocked = cli.validate_lease(
            lease, lease_sha, request, request_sha, decision, decision_sha, at
        )
        return decision_invalid + lease_invalid, decision_blocked + lease_blocked

    def test_exact_authorization_and_lease_pass(self) -> None:
        self.assertEqual(self.validate(), ([], []))

    def test_request_hash_mismatch_blocks(self) -> None:
        self.bundle.decision["subject_ref"]["sha256"] = "f" * 64
        write_json(self.bundle.decision_path, self.bundle.decision)
        self.assertIn("HPC.AUTH.HASH_MISMATCH", {item["code"] for item in self.validate()[1]})

    def test_nonhuman_authorization_blocks(self) -> None:
        self.bundle.decision["decided_by"]["actor_type"] = "agent"
        self.bundle.rebind()
        self.assertIn("HPC.AUTH.NOT_GRANTED", {item["code"] for item in self.validate()[1]})

    def test_expired_authorization_blocks(self) -> None:
        self.bundle.decision["valid_until_utc"] = "2026-07-18T23:59:59Z"
        self.bundle.rebind()
        self.assertIn("HPC.AUTH.NOT_GRANTED", {item["code"] for item in self.validate()[1]})

    def test_broader_scope_blocks(self) -> None:
        self.bundle.decision["scope_labels"].append("synthetic-campaign/run-002")
        self.bundle.rebind()
        self.assertIn("HPC.AUTH.NOT_GRANTED", {item["code"] for item in self.validate()[1]})

    def test_consumed_lease_blocks_reuse(self) -> None:
        self.bundle.lease["status"] = "consumed"
        write_json(self.bundle.lease_path, self.bundle.lease)
        self.assertIn("HPC.IDEMPOTENCY.BLOCKED", {item["code"] for item in self.validate()[1]})

    def test_resource_broadening_blocks(self) -> None:
        self.bundle.lease["grant"]["resource_ceiling"]["nodes"] = 2
        write_json(self.bundle.lease_path, self.bundle.lease)
        self.assertIn("HPC.LEASE.INVALID", {item["code"] for item in self.validate()[1]})

    def test_argv_hash_mismatch_blocks(self) -> None:
        self.bundle.lease["grant"]["argv_sha256"] = "d" * 64
        write_json(self.bundle.lease_path, self.bundle.lease)
        self.assertIn("HPC.LEASE.INVALID", {item["code"] for item in self.validate()[1]})

    def test_decision_subject_role_is_contract_bound(self) -> None:
        self.bundle.decision["subject_ref"]["role"] = "unrelated"
        self.bundle.rebind()
        self.assertIn("HPC.AUTH.NOT_GRANTED", {item["code"] for item in self.validate()[0]})

    def test_execution_decision_cannot_claim_review_eligibility(self) -> None:
        self.bundle.decision["claim_ceiling"] = "eligible_for_expert_review"
        self.bundle.rebind()
        self.assertIn("HPC.AUTH.NOT_GRANTED", {item["code"] for item in self.validate()[0]})

    def test_decision_evidence_id_must_resolve(self) -> None:
        self.bundle.decision["evidence_ids"] = ["unrelated-record"]
        self.bundle.rebind()
        self.assertIn("HPC.AUTH.NOT_GRANTED", {item["code"] for item in self.validate()[0]})

    def test_scope_order_is_semantically_irrelevant(self) -> None:
        self.bundle.request["authorization_requirement"]["scope_labels"] = [
            "synthetic-campaign/run-001", "synthetic-campaign/run-aux"
        ]
        self.bundle.decision["scope_labels"] = [
            "synthetic-campaign/run-aux", "synthetic-campaign/run-001"
        ]
        self.bundle.rebind()
        self.assertEqual(self.validate(), ([], []))

    def test_boolean_maximum_execution_is_contract_invalid(self) -> None:
        self.bundle.lease["grant"]["maximum_executions"] = True
        write_json(self.bundle.lease_path, self.bundle.lease)
        self.assertIn("HPC.LEASE.INVALID", {item["code"] for item in self.validate()[0]})


class RendererTests(unittest.TestCase):
    def render(self, scheduler: str, bundle: Bundle) -> tuple[int, dict]:
        return invoke([
            "render-dry-run",
            "--request", str(bundle.request_path),
            "--decision", str(bundle.decision_path),
            "--lease", str(bundle.lease_path),
            "--scheduler", scheduler,
            "--at-utc", "2026-07-19T00:00:00Z",
        ])

    def test_slurm_render_is_side_effect_free(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        directory = bundle.request_path.parent
        before = sorted(item.name for item in directory.iterdir())
        code, report = self.render("slurm", bundle)
        after = sorted(item.name for item in directory.iterdir())
        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertFalse(report["side_effect_performed"])
        self.assertIsNone(report["scheduler_job_id"])
        self.assertEqual(report["proposed_submission_argv"], ["sbatch", "synthetic-job.sh"])
        self.assertIn("#SBATCH --nodes=1", report["rendered_script"])

    def test_openpbs_render(self) -> None:
        bundle = Bundle("openpbs")
        self.addCleanup(bundle.close)
        bundle.request["resources"]["nodes"] = 2
        bundle.request["resources"]["mpi_ranks"] = 4
        bundle.rebind()
        code, report = self.render("openpbs", bundle)
        self.assertEqual(code, 0)
        self.assertEqual(report["proposed_submission_argv"], ["qsub", "synthetic-job.sh"])
        self.assertIn("#PBS -l select=2:ncpus=2:mpiprocs=2:ompthreads=1", report["rendered_script"])

    def test_openpbs_indivisible_ranks_block(self) -> None:
        bundle = Bundle("openpbs")
        self.addCleanup(bundle.close)
        bundle.request["resources"]["nodes"] = 2
        bundle.request["resources"]["mpi_ranks"] = 3
        bundle.rebind()
        code, report = self.render("openpbs", bundle)
        self.assertEqual(code, 3)
        self.assertIsNone(report["rendered_script"])

    def test_scheduler_profile_mismatch_blocks(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        code, report = self.render("openpbs", bundle)
        self.assertEqual(code, 3)
        self.assertIn("HPC.SCHEDULER.UNSUPPORTED", {item["code"] for item in report["findings"]})

    def test_ambiguous_profile_name_cannot_match_by_substring(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        bundle.request["resources"]["scheduler_profile_id"] = "synthetic-slurm-pbs-local-001"
        bundle.rebind()
        code, report = self.render("slurm", bundle)
        self.assertEqual(code, 3)
        self.assertIn("HPC.PROFILE.UNRESOLVED", {item["code"] for item in report["findings"]})

    def test_local_render_never_executes(self) -> None:
        bundle = Bundle("local")
        self.addCleanup(bundle.close)
        code, report = self.render("local", bundle)
        self.assertEqual(code, 0)
        self.assertEqual(report["proposed_submission_argv"][0], "local-dry-run-only")
        self.assertFalse(report["execution_authorized"])

    def test_control_authorization_cannot_enter_submission_renderer(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        bundle.request["authorization_requirement"]["side_effects"] = ["scheduler-control"]
        bundle.rebind()
        code, report = self.render("slurm", bundle)
        self.assertEqual(code, 3)
        self.assertIn("HPC.AUTH.NOT_GRANTED", {item["code"] for item in report["findings"]})

    def test_exact_request_bytes_drift_blocks_stale_decision_and_lease(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        bundle.request_path.write_bytes(bundle.request_path.read_bytes() + b" ")
        code, report = self.render("slurm", bundle)
        self.assertEqual(code, 3)
        codes = {item["code"] for item in report["findings"]}
        self.assertTrue({"HPC.AUTH.HASH_MISMATCH", "HPC.LEASE.INVALID"}.issubset(codes))

    def test_repeated_dry_run_is_deterministic_and_never_consumes_lease(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        first_code, first = self.render("slurm", bundle)
        second_code, second = self.render("slurm", bundle)
        self.assertEqual((first_code, second_code), (0, 0))
        self.assertEqual(first, second)
        self.assertFalse(first["side_effect_performed"])
        self.assertFalse(first["execution_authorized"])


class StatusTests(unittest.TestCase):
    def classify(self, **updates) -> tuple[list[dict], str]:
        value = fixture("scheduler-success-app-failure.json")
        value.update(updates)
        return cli.classify_status(value)

    def test_all_three_layers_required_for_success(self) -> None:
        findings, normalized = self.classify(
            native_application_status="JOB DONE",
            application_status="completed",
        )
        self.assertEqual(findings, [])
        self.assertEqual(normalized, "succeeded")

    def test_scheduler_success_does_not_override_application_failure(self) -> None:
        findings, normalized = self.classify()
        self.assertEqual(normalized, "failed")
        self.assertIn("HPC.RUNTIME.FAILED", {item["code"] for item in findings})

    def test_unknown_terminal_evidence_blocks(self) -> None:
        findings, normalized = self.classify(
            native_scheduler_status="UNKNOWN",
            scheduler_status="unknown",
            native_process_status=None,
            process_status="unknown",
            native_application_status=None,
            application_status="unknown",
            return_code=None,
        )
        self.assertEqual(normalized, "blocked")
        self.assertIn("HPC.STATUS.UNKNOWN", {item["code"] for item in findings})

    def test_running_is_not_success(self) -> None:
        _findings, normalized = self.classify(
            native_scheduler_status="RUNNING",
            scheduler_status="running",
            native_process_status="running",
            process_status="running",
            native_application_status="running",
            application_status="running",
            return_code=None,
        )
        self.assertEqual(normalized, "running")

    def test_cancelled_and_timed_out_remain_distinct(self) -> None:
        self.assertEqual(self.classify(native_scheduler_status="CANCELLED", scheduler_status="cancelled")[1], "cancelled")
        self.assertEqual(self.classify(process_status="timed-out", return_code=None)[1], "timed-out")

    def test_native_scheduler_state_cannot_be_relabelled_success(self) -> None:
        findings, normalized = self.classify(
            native_scheduler_status="FAILED",
            scheduler_status="succeeded",
            native_application_status="JOB DONE",
            application_status="completed",
        )
        self.assertEqual(normalized, "blocked")
        self.assertIn("HPC.STATUS.UNKNOWN", {item["code"] for item in findings})


class CliIntegrationTests(unittest.TestCase):
    def test_render_is_read_only_and_creates_no_implicit_output(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        root = bundle.request_path.parent
        before = {item.name: item.read_bytes() for item in root.iterdir()}
        code, report = invoke([
            "render-dry-run",
            "--request", str(bundle.request_path),
            "--decision", str(bundle.decision_path),
            "--lease", str(bundle.lease_path),
            "--scheduler", "slurm",
            "--at-utc", "2026-07-19T00:00:00Z",
        ])
        self.assertEqual(code, 0)
        self.assertFalse(report["side_effect_performed"])
        after = {item.name: item.read_bytes() for item in root.iterdir()}
        self.assertEqual(after, before)

    def test_fixture_render_command_passes(self) -> None:
        code, report = invoke([
            "render-dry-run",
            "--request", str(ROOT / "fixtures" / "slurm-request.json"),
            "--decision", str(ROOT / "fixtures" / "slurm-decision.json"),
            "--lease", str(ROOT / "fixtures" / "slurm-lease.json"),
            "--scheduler", "slurm",
            "--at-utc", "2026-07-19T00:00:00Z",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")
        self.assertEqual(report["report_authenticity"], "unsigned-candidate-output")
        expected = {
            "execution-request": hashlib.sha256((ROOT / "fixtures" / "slurm-request.json").read_bytes()).hexdigest(),
            "decision-record": hashlib.sha256((ROOT / "fixtures" / "slurm-decision.json").read_bytes()).hexdigest(),
            "execution-lease": hashlib.sha256((ROOT / "fixtures" / "slurm-lease.json").read_bytes()).hexdigest(),
        }
        self.assertEqual(
            {item["contract_name"]: item["sha256"] for item in report["decisive_evidence"]},
            expected,
        )

    def test_status_command_emits_failed_not_succeeded(self) -> None:
        code, report = invoke([
            "classify-status",
            "--observation", str(ROOT / "fixtures" / "scheduler-success-app-failure.json"),
        ])
        self.assertEqual(code, 0)
        self.assertEqual(report["states"]["normalized_execution"], "failed")
        self.assertNotEqual(report["states"]["application"], "completed")
        self.assertIn("HPC.RUNTIME.FAILED", {item["code"] for item in report["findings"]})
        self.assertEqual(report["claim_ceiling"], "no_positive_claim")

    def test_secret_value_and_missing_path_are_not_echoed(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        marker = "synthetic-sensitive-value-marker"
        bundle.request["argv"].append("api_" + "key=" + marker)
        write_json(bundle.request_path, bundle.request)
        code, report = invoke(["validate-request", "--request", str(bundle.request_path)])
        self.assertEqual(code, 2)
        self.assertNotIn(marker, json.dumps(report))
        missing_marker = "synthetic-sensitive-path-marker"
        missing = bundle.request_path.parent / (missing_marker + ".json")
        code, report = invoke(["validate-request", "--request", str(missing)])
        self.assertEqual(code, 2)
        self.assertNotIn(missing_marker, json.dumps(report))

    def test_automatic_retry_mutation_changes_pass_to_fail(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        pass_code, _pass_report = invoke(["validate-request", "--request", str(bundle.request_path)])
        bundle.request["retry_policy"]["automatic_retry"] = True
        write_json(bundle.request_path, bundle.request)
        fail_code, fail_report = invoke(["validate-request", "--request", str(bundle.request_path)])
        self.assertEqual((pass_code, fail_code), (0, 2))
        self.assertIn("HPC.REQUEST.INVALID", {item["code"] for item in fail_report["findings"]})

    def test_unknown_scheduler_status_command_blocks(self) -> None:
        value = fixture("scheduler-success-app-failure.json")
        value.update({
            "native_scheduler_status": "UNRECOGNIZED",
            "scheduler_status": "unknown",
            "native_process_status": None,
            "process_status": "unknown",
            "native_application_status": None,
            "application_status": "unknown",
            "return_code": None,
        })
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "observation.json"
        write_json(path, value)
        code, report = invoke(["classify-status", "--observation", str(path)])
        self.assertEqual(code, 3)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["states"]["normalized_execution"], "blocked")

    def test_every_command_remains_at_development_claim_ceiling(self) -> None:
        bundle = Bundle("slurm")
        self.addCleanup(bundle.close)
        invocations = [
            ["validate-request", "--request", str(bundle.request_path)],
            [
                "render-dry-run", "--request", str(bundle.request_path),
                "--decision", str(bundle.decision_path), "--lease", str(bundle.lease_path),
                "--scheduler", "slurm", "--at-utc", "2026-07-19T00:00:00Z",
            ],
            ["classify-status", "--observation", str(ROOT / "fixtures" / "scheduler-success-app-failure.json")],
        ]
        for arguments in invocations:
            _code, report = invoke(arguments)
            self.assertEqual(report["claim_ceiling"], "no_positive_claim")
            self.assertFalse(report["execution_authorized"])
            self.assertFalse(report["side_effect_performed"])
            self.assertFalse(report["external_execution_performed"])
            self.assertFalse(report["lease_consumed"])
            self.assertFalse(report["workflow_event_emitted"])

    def test_unsigned_report_mutation_changes_external_digest(self) -> None:
        code, report = invoke(["validate-request", "--request", str(ROOT / "fixtures" / "slurm-request.json")])
        self.assertEqual(code, 0)
        original = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
        forged = copy.deepcopy(report)
        forged["side_effect_performed"] = True
        altered = json.dumps(forged, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertNotEqual(hashlib.sha256(original).hexdigest(), hashlib.sha256(altered).hexdigest())
        self.assertEqual(report["downstream_binding_required"], "sha256-of-exact-report-bytes-in-external-manifest")

    def test_markdown_decision_table_matches_canonical_actions(self) -> None:
        lines = (ROOT / "references" / "decision-table.md").read_text(encoding="utf-8").splitlines()
        rows = [line for line in lines if re.match(r"^\|\s*\d+\s*\|", line)]
        self.assertEqual(len(rows), 13)
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
        self.assertEqual(table["skill_id"], "dft-hpc-execution")
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
        matching = {cases[2]["case_id"], cases[8]["case_id"]}
        selected = next(item for item in cases if item["case_id"] in matching)
        self.assertEqual(selected["priority"], 3)

    def test_fixture_manifest_tracks_canonical_decision_table(self) -> None:
        manifest = json.loads((ROOT / "references" / "fixture-manifest.json").read_text(encoding="utf-8"))
        paths = {item["path"] for item in manifest["fixtures"]}
        self.assertIn("references/weak-model-decision-table.json", paths)

    def test_skill_links_and_cross_contract_manual_are_complete(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for relative in re.findall(r"\]\(([^)]+)\)", skill):
            if "://" not in relative:
                self.assertTrue((ROOT / relative).is_file(), relative)
        manual = (ROOT / "references" / "repository-interface-manual.md").read_text(encoding="utf-8")
        for marker in (
            "Request, lease, record, event, and answer protocol", "execution-request@1.0",
            "execution-lease@1.0", "workflow-event@1.0", "agent-action-envelope@1.0",
            "validate_agent_answer.py", "Dry-run versus execute acceptance",
        ):
            self.assertIn(marker, manual)

    def test_untrusted_status_value_is_not_echoed(self) -> None:
        value = fixture("scheduler-success-app-failure.json")
        marker = "synthetic-private-status-marker"
        value["scheduler_status"] = "/" + "home" + "/" + marker
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "observation.json"
        write_json(path, value)
        code, report = invoke(["classify-status", "--observation", str(path)])
        self.assertEqual(code, 2)
        self.assertNotIn(marker, json.dumps(report))
        self.assertEqual(report["states"]["scheduler"], "unknown")


class OfficialSourcePackMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = ROOT.parents[1]
        self.references = ROOT / "references"
        self.seed_path = self.references / "source-pack-seed.json"
        self.seed = json.loads(self.seed_path.read_text(encoding="utf-8"))
        self.scope_path = self.references / "source-pack-scope-catalog.json"
        self.scope = json.loads(self.scope_path.read_text(encoding="utf-8"))

    @staticmethod
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def catalogs(self) -> dict[str, dict]:
        return {
            provider["input_id"]: json.loads(
                (self.repository / provider["source_ref"]["path"]).read_text(
                    encoding="utf-8"
                )
            )
            for provider in self.seed["providers"]
        }

    def test_source_pack_records_match_frozen_schemas_and_hashes(self) -> None:
        pairs = [
            ("official-document-pack-seed.schema.json", self.seed_path),
            ("official-document-scope-catalog.schema.json", self.scope_path),
        ]
        for provider in self.seed["providers"]:
            pairs.append(
                (
                    "official-document-source-catalog.schema.json",
                    self.repository / provider["source_ref"]["path"],
                )
            )
        for schema_name, instance_path in pairs:
            schema = json.loads(
                (self.repository / "contracts" / schema_name).read_text(
                    encoding="utf-8"
                )
            )
            Draft202012Validator.check_schema(schema)
            errors = sorted(
                Draft202012Validator(schema).iter_errors(
                    json.loads(instance_path.read_text(encoding="utf-8"))
                ),
                key=lambda error: tuple(str(item) for item in error.absolute_path),
            )
            self.assertEqual([], [error.message for error in errors])
        refs = [self.seed["scope_catalog_ref"]]
        refs.extend(provider["source_ref"] for provider in self.seed["providers"])
        for ref in refs:
            path = self.repository / ref["path"]
            path.resolve().relative_to(ROOT.resolve())
            self.assertEqual(ref["sha256"], self.digest(path))

    def test_scope_and_catalog_subjects_are_exactly_partitioned(self) -> None:
        provider_ids = {item["input_id"] for item in self.seed["providers"]}
        external = {provider_id: set() for provider_id in provider_ids}
        for subject in self.scope["subjects"]:
            for origin in subject["origin_refs"]:
                self.assertEqual(
                    origin["sha256"], self.digest(self.repository / origin["path"])
                )
            if subject["evidence_class"] == "official-provider-required":
                self.assertTrue(subject["provider_input_ids"])
                for provider_id in subject["provider_input_ids"]:
                    self.assertIn(provider_id, provider_ids)
                    external[provider_id].add(subject["subject_id"])
            else:
                self.assertEqual([], subject["provider_input_ids"])
                self.assertIn(
                    subject["expected_disposition"],
                    {"not-applicable", "excluded"},
                )
        for provider_id, catalog in self.catalogs().items():
            self.assertEqual(
                {item["subject_id"] for item in catalog["subjects"]},
                external[provider_id],
            )

    def test_scope_is_complete_and_every_origin_is_skill_local(self) -> None:
        inputs = json.loads(
            (self.references / "source-pack-inputs.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            [item["subject_id"] for item in inputs["scope_subjects"]],
            [item["subject_id"] for item in self.scope["subjects"]],
        )
        for subject in inputs["scope_subjects"]:
            for origin_path in subject["origin_paths"]:
                (self.repository / origin_path).resolve().relative_to(ROOT.resolve())
        for subject in self.scope["subjects"]:
            for origin in subject["origin_refs"]:
                (self.repository / origin["path"]).resolve().relative_to(
                    ROOT.resolve()
                )

    def test_scope_generator_rejects_cross_root_origins(self) -> None:
        generator = runpy.run_path(
            str(ROOT / "scripts" / "extract_official_source_scope.py")
        )
        with self.assertRaisesRegex(ValueError, "scope origin must remain below"):
            generator["scope_origin_ref"](
                "contracts/execution-request.schema.json",
                {},
            )
        relative = (
            "skills/dft-hpc-execution/references/"
            "source-catalog-json-schema-2020-12.json"
        )
        planned = b'{"planned":"current-pass"}\n'
        ref = generator["scope_origin_ref"](
            relative,
            {self.repository / relative: planned},
        )
        self.assertEqual(hashlib.sha256(planned).hexdigest(), ref["sha256"])

    def test_scheduler_catalogs_are_complete_for_declared_candidate_scope(self) -> None:
        catalogs = self.catalogs()
        slurm = catalogs["slurm-26-05-live"]
        self.assertEqual("latest-at-retrieval", slurm["version_scope"]["kind"])
        self.assertEqual(
            {
                "https://slurm.schedmd.com/sbatch.html",
                "https://slurm.schedmd.com/squeue.html",
                "https://slurm.schedmd.com/sacct.html",
                "https://slurm.schedmd.com/scontrol.html",
                "https://slurm.schedmd.com/scancel.html",
                "https://slurm.schedmd.com/job_state_codes.html",
                "https://slurm.schedmd.com/job_exit_code.html",
                "https://slurm.schedmd.com/job_array.html",
                "https://slurm.schedmd.com/gres.html",
            },
            {source["locator"] for source in slurm["sources"]},
        )
        openpbs = catalogs["openpbs-23-06-06"]
        self.assertEqual(3, len(openpbs["sources"]))
        self.assertIn(
            "OPENPBS.NGPUS.UNRESOLVED",
            {item["code"] for item in openpbs["blockers"]},
        )
        local = next(
            item
            for item in self.scope["subjects"]
            if item["subject_id"] == "hpc.openpbs.template-divisibility-local"
        )
        self.assertEqual([], local["provider_input_ids"])

    def test_catalogs_are_metadata_only_and_proposal_classes_are_bounded(self) -> None:
        for catalog in self.catalogs().values():
            self.assertNotIn("content_ref", json.dumps(catalog, sort_keys=True))
            for source in catalog["sources"]:
                self.assertIn("external_identity", source)
                for slice_record in source["slices"]:
                    self.assertEqual("whole-source", slice_record["selector"]["kind"])
                    self.assertEqual("*", slice_record["selector"]["value"])
                    self.assertIn("external_receipt", slice_record)
        proposal = json.loads(
            (self.references / "source-pack-authority-proposal.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("blocked", self.seed["status_ceiling"])
        self.assertEqual("none", proposal["lifecycle_effect"])
        self.assertEqual(
            {
                "vibe-dft-skills-repository-contracts": "repository",
                "json-schema-standard-2020-12": "standard",
                "slurm-live-manual-26-05": "platform",
                "openpbs-release-docs-23-06-06": "platform",
            },
            {
                authority_id: entry["provider_class"]
                for authority_id, entry in proposal["authority_entries"].items()
            },
        )
        for authority in proposal["authority_entries"].values():
            self.assertEqual([], authority["content_policy"]["allowed_query_urls"])
            if authority["license_policy"]["status"] == "unknown":
                self.assertEqual([], authority["license_policy"]["terms_urls"])
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "extract_official_source_scope.py"),
                "--check",
            ],
            cwd=self.repository,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        table = json.loads(
            (self.references / "weak-model-decision-table.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("development", table["lifecycle"])
        self.assertEqual("no_positive_claim", table["current_claim"])


if __name__ == "__main__":
    unittest.main()
