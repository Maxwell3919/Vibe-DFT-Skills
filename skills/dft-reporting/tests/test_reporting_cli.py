from __future__ import annotations

import contextlib
import copy
import ast
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(REPO / "tools"))

import reporting_cli as cli
import validate_candidate_decision_table as decision_validator


class ReportingCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(cli._reset_io_bindings)
        self.work = Path(self.directory.name)

    def fixture(self, name: str) -> Path:
        return ROOT / "fixtures" / name

    def write_json(self, name: str, value: dict) -> Path:
        path = self.work / name
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def load_request(self) -> dict:
        return json.loads(self.fixture("valid-report-request.json").read_text(encoding="utf-8"))

    def load_map(self) -> dict:
        return json.loads(self.fixture("valid-claim-map.json").read_text(encoding="utf-8"))

    def invoke(self, arguments: list[str]) -> tuple[int, dict]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli.main(arguments)
        return code, json.loads(output.getvalue())

    def build_valid_plan_and_audit(self) -> tuple[Path, Path]:
        plan = self.work / "plan.json"
        code, _ = self.invoke([
            "plan", "--request", str(self.fixture("valid-report-request.json")),
            "--claim-map", str(self.fixture("valid-claim-map.json")), "--out", str(plan),
        ])
        self.assertEqual(code, 0)
        audit = self.work / "audit.json"
        code, _ = self.invoke(["audit", "--plan", str(plan), "--out", str(audit)])
        self.assertEqual(code, 0)
        return plan, audit

    def test_strict_json_rejects_duplicate_key(self) -> None:
        path = self.work / "duplicate.json"
        path.write_bytes(b'{"a":1,"a":2}')
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(path)

    def test_strict_json_rejects_bom_nan_and_concatenation(self) -> None:
        for index, raw in enumerate((b'\xef\xbb\xbf{}', b'{"x":NaN}', b'{}{}')):
            path = self.work / f"invalid-{index}.json"
            path.write_bytes(raw)
            with self.assertRaises(cli.InputFailure):
                cli.strict_load(path)

    def test_strict_json_rejects_symlink(self) -> None:
        target = self.work / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = self.work / "link.json"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(link)

    def test_strict_json_rejects_hardlink(self) -> None:
        target = self.work / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = self.work / "hardlink.json"
        try:
            link.hardlink_to(target)
        except OSError:
            self.skipTest("hardlinks unavailable")
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(link)

    def test_strict_json_detects_path_replacement_during_fd_read(self) -> None:
        path = self.write_json("race.json", {"value": "stable"})
        original_read = cli.os.read
        replaced = False

        def racing_read(descriptor: int, count: int) -> bytes:
            nonlocal replaced
            chunk = original_read(descriptor, count)
            if not replaced:
                replacement = self.work / "replacement.json"
                replacement.write_bytes(path.read_bytes())
                cli.os.replace(replacement, path)
                replaced = True
            return chunk

        with mock.patch.object(cli.os, "read", side_effect=racing_read):
            with self.assertRaises(cli.InputFailure):
                cli.strict_load(path)

    def test_intermediate_directory_symlink_swap_is_rejected(self) -> None:
        base = self.work / "base"
        subdirectory = base / "sub"
        outside = self.work / "outside"
        subdirectory.mkdir(parents=True)
        outside.mkdir()
        target = subdirectory / "input.json"
        target.write_text('{"inside":true}\n', encoding="utf-8")
        (outside / target.name).write_text('{"outside":true}\n', encoding="utf-8")
        moved = base / "sub-original"
        original_open = cli.os.open
        swapped = False

        def racing_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            nonlocal swapped
            if os.fspath(path) == "sub" and kwargs.get("dir_fd") is not None and not swapped:
                subdirectory.rename(moved)
                subdirectory.symlink_to(outside, target_is_directory=True)
                swapped = True
            return original_open(path, flags, *args, **kwargs)

        cli._reset_io_bindings()
        with mock.patch.object(cli.os, "open", side_effect=racing_open):
            with self.assertRaises(cli.InputFailure):
                cli.strict_load(target)
        cli._reset_io_bindings()

    def test_request_evidence_base_identity_is_retained_between_reads(self) -> None:
        base = self.work / "bound-base"
        base.mkdir()
        first = base / "request.json"
        second = base / "evidence.json"
        first.write_text('{"request":true}\n', encoding="utf-8")
        second.write_text('{"evidence":true}\n', encoding="utf-8")
        moved = self.work / "bound-base-original"
        cli._reset_io_bindings()
        cli.strict_load(first)
        base.rename(moved)
        base.mkdir()
        (base / second.name).write_text('{"attacker":true}\n', encoding="utf-8")
        with self.assertRaises(cli.InputFailure):
            cli.strict_load(base / second.name)
        cli._reset_io_bindings()

    def test_fifo_input_is_rejected_without_blocking(self) -> None:
        fifo = self.work / "blocked.json"
        try:
            os.mkfifo(fifo)
        except (AttributeError, OSError):
            self.skipTest("FIFO creation unavailable")
        program = """
import importlib.util
import pathlib
import sys
spec = importlib.util.spec_from_file_location('guard_under_test', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.strict_load(pathlib.Path(sys.argv[2]))
except module.InputFailure:
    raise SystemExit(0)
raise SystemExit(1)
"""
        completed = subprocess.run(
            [sys.executable, "-B", "-c", program, str(Path(cli.__file__)), str(fifo)],
            check=False,
            capture_output=True,
            timeout=1.0,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_staging_path_substitution_cannot_publish_attacker_bytes(self) -> None:
        output = self.work / "substitution.json"
        original_link = cli.os.link
        substituted = False

        def substituting_link(source: object, target: object, *args: object, **kwargs: object) -> None:
            nonlocal substituted
            if not substituted:
                directory_fd = kwargs["src_dir_fd"]
                os.unlink(source, dir_fd=directory_fd)
                attacker_fd = os.open(
                    source, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600,
                    dir_fd=directory_fd,
                )
                os.write(attacker_fd, b"ATTACKER_BYTES")
                os.close(attacker_fd)
                substituted = True
            original_link(source, target, *args, **kwargs)

        with mock.patch.object(cli.os, "link", side_effect=substituting_link):
            with self.assertRaises(cli.InputFailure):
                cli.write_new(output, {"safe": True})
        self.assertFalse(output.exists())
        self.assertEqual(list(self.work.glob(f".{output.name}.*.tmp")), [])

    def test_late_target_creation_is_not_overwritten(self) -> None:
        output = self.work / "late-target.json"
        victim = b'{"victim":true}\n'
        original_link = cli.os.link
        created = False

        def racing_link(source: object, target: object, *args: object, **kwargs: object) -> None:
            nonlocal created
            if not created:
                directory_fd = kwargs["dst_dir_fd"]
                target_fd = os.open(
                    target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600,
                    dir_fd=directory_fd,
                )
                os.write(target_fd, victim)
                os.close(target_fd)
                created = True
            original_link(source, target, *args, **kwargs)

        with mock.patch.object(cli.os, "link", side_effect=racing_link):
            with self.assertRaises(cli.InputFailure):
                cli.write_new(output, {"safe": True})
        self.assertEqual(output.read_bytes(), victim)
        self.assertEqual(list(self.work.glob(f".{output.name}.*.tmp")), [])

    def test_write_and_fsync_failures_leave_no_partial_output(self) -> None:
        write_output = self.work / "write-failure.json"
        with mock.patch.object(cli.os, "write", side_effect=OSError("synthetic write failure")):
            with self.assertRaises(cli.InputFailure):
                cli.write_new(write_output, {"safe": True})
        self.assertFalse(write_output.exists())

        file_sync_output = self.work / "file-fsync-failure.json"
        with mock.patch.object(cli.os, "fsync", side_effect=OSError("synthetic file fsync failure")):
            with self.assertRaises(cli.InputFailure):
                cli.write_new(file_sync_output, {"safe": True})
        self.assertFalse(file_sync_output.exists())

        directory_sync_output = self.work / "directory-fsync-failure.json"
        original_fsync = cli.os.fsync

        def fail_directory_fsync(descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError("synthetic directory fsync failure")
            original_fsync(descriptor)

        with mock.patch.object(cli.os, "fsync", side_effect=fail_directory_fsync):
            with self.assertRaises(cli.InputFailure):
                cli.write_new(directory_sync_output, {"safe": True})
        self.assertFalse(directory_sync_output.exists())
        self.assertEqual(list(self.work.glob(".*.tmp")), [])

    def test_valid_plan_is_stable_and_draft_only(self) -> None:
        outputs = []
        for name in ("one.json", "two.json"):
            path = self.work / name
            code, summary = self.invoke([
                "plan", "--request", str(self.fixture("valid-report-request.json")),
                "--claim-map", str(self.fixture("valid-claim-map.json")), "--out", str(path),
            ])
            self.assertEqual(code, 0)
            self.assertEqual(summary["status"], "pass")
            outputs.append(path.read_bytes())
        self.assertEqual(outputs[0], outputs[1])
        plan = json.loads(outputs[0])
        self.assertFalse(plan["publication_ready"])
        self.assertFalse(plan["external_message_sent"])
        self.assertEqual(plan["tool_claim_ceiling"], "no_positive_claim")

    def test_hash_mismatch_is_invalid(self) -> None:
        request = self.load_request()
        request["claim_map_ref"]["sha256"] = "f" * 64
        output = self.work / "blocked.json"
        code, summary = self.invoke([
            "plan", "--request", str(self.write_json("request.json", request)),
            "--claim-map", str(self.fixture("valid-claim-map.json")), "--out", str(output),
        ])
        self.assertEqual(code, 2)
        self.assertIn("REPORT.HASH.MISMATCH", summary["finding_codes"])

    def test_unsupported_claim_is_blocked(self) -> None:
        claim_map = self.load_map()
        claim_map["claims"][0]["status"] = "blocked"
        claim_map["claims"][0]["blocker_codes"] = ["synthetic-blocker"]
        map_path = self.write_json("map.json", claim_map)
        _value, digest = cli.strict_load(map_path)
        request = self.load_request()
        request["claim_map_ref"]["sha256"] = digest
        output = self.work / "blocked.json"
        code, summary = self.invoke([
            "plan", "--request", str(self.write_json("request.json", request)),
            "--claim-map", str(map_path), "--out", str(output),
        ])
        self.assertEqual(code, 3)
        self.assertIn("REPORT.CLAIM.UNSUPPORTED", summary["finding_codes"])

    def test_missing_evidence_is_blocked(self) -> None:
        claim_map = self.load_map()
        claim_map["evidence"][0]["status"] = "missing"
        map_path = self.write_json("map.json", claim_map)
        _value, digest = cli.strict_load(map_path)
        request = self.load_request()
        request["claim_map_ref"]["sha256"] = digest
        code, summary = self.invoke([
            "plan", "--request", str(self.write_json("request.json", request)),
            "--claim-map", str(map_path), "--out", str(self.work / "plan.json"),
        ])
        self.assertEqual(code, 3)
        self.assertIn("REPORT.EVIDENCE.NOT_PRESENT", summary["finding_codes"])

    def test_nonpassing_gate_is_blocked(self) -> None:
        claim_map = self.load_map()
        claim_map["gates"][0]["status"] = "blocked"
        map_path = self.write_json("map.json", claim_map)
        _value, digest = cli.strict_load(map_path)
        request = self.load_request()
        request["claim_map_ref"]["sha256"] = digest
        code, summary = self.invoke([
            "plan", "--request", str(self.write_json("request.json", request)),
            "--claim-map", str(map_path), "--out", str(self.work / "plan.json"),
        ])
        self.assertEqual(code, 3)
        self.assertIn("REPORT.GATE.NOT_PASSING", summary["finding_codes"])

    def test_thin_self_declared_gate_is_invalid(self) -> None:
        claim_map = self.load_map()
        claim_map["gates"][0] = {"check_id": "technical-completion", "status": "pass"}
        map_path = self.write_json("map.json", claim_map)
        _value, digest = cli.strict_load(map_path)
        request = self.load_request()
        request["claim_map_ref"]["sha256"] = digest
        code, summary = self.invoke([
            "plan", "--request", str(self.write_json("request.json", request)),
            "--claim-map", str(map_path), "--out", str(self.work / "plan.json"),
        ])
        self.assertEqual(code, 2)
        self.assertIn("REPORT.GATE.SHAPE_INVALID", summary["finding_codes"])

    def test_missing_citation_locator_is_blocked(self) -> None:
        request = self.load_request()
        request["citation_locators"] = []
        code, summary = self.invoke([
            "plan", "--request", str(self.write_json("request.json", request)),
            "--claim-map", str(self.fixture("valid-claim-map.json")), "--out", str(self.work / "plan.json"),
        ])
        self.assertEqual(code, 3)
        self.assertIn("REPORT.CITATION.LOCATOR_MISSING", summary["finding_codes"])

    def test_private_path_is_invalid(self) -> None:
        request = self.load_request()
        request["title"] = "Result from /" + "Users/example/private"
        code, summary = self.invoke([
            "plan", "--request", str(self.write_json("request.json", request)),
            "--claim-map", str(self.fixture("valid-claim-map.json")), "--out", str(self.work / "plan.json"),
        ])
        self.assertEqual(code, 2)
        self.assertIn("REPORT.PRIVACY.UNSAFE_TEXT", summary["finding_codes"])
        self.assertFalse((self.work / "plan.json").exists())

    def test_positive_upstream_claim_requires_external_bundle_and_is_redacted(self) -> None:
        claim_map = self.load_map()
        sentinel = "SENTINEL_POSITIVE_SCIENTIFIC_ASSERTION"
        claim_map["claim_ceiling"] = "technical_run_gates_only"
        claim_map["claims"][0]["claim_level"] = "technical_run_gates_only"
        claim_map["claims"][0]["statement"] = sentinel
        map_path = self.write_json("positive-map.json", claim_map)
        _value, digest = cli.strict_load(map_path)
        request = self.load_request()
        request["claim_map_ref"]["sha256"] = digest
        output = self.work / "positive-plan.json"
        code, summary = self.invoke([
            "plan", "--request", str(self.write_json("positive-request.json", request)),
            "--claim-map", str(map_path), "--out", str(output),
        ])
        self.assertEqual(code, 3)
        self.assertEqual(summary["first_decisive_finding"], "REPORT.EXTERNAL_BUNDLE.REQUIRED")
        self.assertNotIn(sentinel.encode(), output.read_bytes())

    def test_bilingual_render_is_explicitly_blocked_until_validated(self) -> None:
        request = self.load_request()
        request["language"] = "bilingual"
        code, summary = self.invoke([
            "plan", "--request", str(self.write_json("request.json", request)),
            "--claim-map", str(self.fixture("valid-claim-map.json")), "--out", str(self.work / "plan.json"),
        ])
        self.assertEqual(code, 3)
        self.assertIn("REPORT.BILINGUAL.NOT_VALIDATED", summary["finding_codes"])

    def test_audit_and_render_bind_exact_plan(self) -> None:
        plan, audit = self.build_valid_plan_and_audit()
        package = self.work / "package.json"
        code, summary = self.invoke([
            "render-package", "--plan", str(plan), "--audit", str(audit), "--out", str(package),
        ])
        self.assertEqual(code, 0)
        self.assertEqual(summary["status"], "pass")
        value = json.loads(package.read_text(encoding="utf-8"))
        self.assertTrue(value["draft_only"])
        self.assertFalse(value["publication_ready"])
        self.assertFalse(value["external_message_sent"])

    def test_stale_audit_blocks_render(self) -> None:
        plan, audit = self.build_valid_plan_and_audit()
        audit_value = json.loads(audit.read_text(encoding="utf-8"))
        audit_value["subject_ref"]["sha256"] = "f" * 64
        stale = self.write_json("stale-audit.json", audit_value)
        code, summary = self.invoke([
            "render-package", "--plan", str(plan), "--audit", str(stale), "--out", str(self.work / "package.json"),
        ])
        self.assertEqual(code, 3)
        self.assertIn("REPORT.RENDER.AUDIT_MISMATCH", summary["finding_codes"])
        self.assertFalse((self.work / "package.json").exists())

    def test_forged_pass_audit_cannot_authorize_modified_plan(self) -> None:
        plan, audit = self.build_valid_plan_and_audit()
        changed = json.loads(plan.read_text(encoding="utf-8"))
        changed["limitations"].append("manually changed after audit")
        changed_plan = self.write_json("changed-plan.json", changed)
        _value, changed_sha = cli.strict_load(changed_plan)
        forged = json.loads(audit.read_text(encoding="utf-8"))
        forged["subject_ref"]["sha256"] = changed_sha
        forged_path = self.write_json("forged-audit.json", forged)
        output = self.work / "forged-package.json"
        code, summary = self.invoke(["render-package", "--plan", str(changed_plan), "--audit", str(forged_path), "--out", str(output)])
        self.assertEqual(code, 3)
        self.assertEqual(summary["first_decisive_finding"], "REPORT.RENDER.AUDIT_MISMATCH")
        self.assertFalse(output.exists())

    def test_audit_blocks_hand_raised_positive_plan_claim(self) -> None:
        plan, _audit = self.build_valid_plan_and_audit()
        value = json.loads(plan.read_text(encoding="utf-8"))
        value["claims"][0]["claim_level"] = "technical_run_gates_only"
        value["claims"][0]["statement"] = "SENTINEL_HAND_RAISED_POSITIVE_CLAIM"
        forged_plan = self.write_json("positive-forged-plan.json", value)
        audit_out = self.work / "positive-forged-audit.json"
        code, summary = self.invoke(["audit", "--plan", str(forged_plan), "--out", str(audit_out)])
        self.assertEqual(code, 3)
        self.assertEqual(summary["first_decisive_finding"], "REPORT.EXTERNAL_BUNDLE.REQUIRED")
        self.assertNotIn(b"SENTINEL_HAND_RAISED_POSITIVE_CLAIM", audit_out.read_bytes())

    def test_output_cannot_alias_any_input(self) -> None:
        request_path = self.fixture("valid-report-request.json")
        map_path = self.fixture("valid-claim-map.json")
        for output in (request_path, map_path):
            before = output.read_bytes()
            code, summary = self.invoke([
                "plan", "--request", str(request_path),
                "--claim-map", str(map_path), "--out", str(output),
            ])
            self.assertEqual(code, 2)
            self.assertIn("REPORT.JSON.INVALID", summary["finding_codes"])
            self.assertEqual(output.read_bytes(), before)
        hardlink = self.work / "claim-map-output-alias.json"
        try:
            hardlink.hardlink_to(map_path)
        except OSError:
            self.skipTest("hardlinks unavailable")
        code, _summary = self.invoke(["plan", "--request", str(request_path), "--claim-map", str(map_path), "--out", str(hardlink)])
        self.assertEqual(code, 2)
        hardlink.unlink()
        plan, audit = self.build_valid_plan_and_audit()
        plan_before = plan.read_bytes()
        code, _summary = self.invoke(["audit", "--plan", str(plan), "--out", str(plan)])
        self.assertEqual(code, 2)
        self.assertEqual(plan.read_bytes(), plan_before)
        audit_before = audit.read_bytes()
        code, _summary = self.invoke(["render-package", "--plan", str(plan), "--audit", str(audit), "--out", str(audit)])
        self.assertEqual(code, 2)
        self.assertEqual(audit.read_bytes(), audit_before)

    def test_output_overwrite_is_rejected(self) -> None:
        output = self.work / "plan.json"
        output.write_text("{}", encoding="utf-8")
        code, summary = self.invoke([
            "plan", "--request", str(self.fixture("valid-report-request.json")),
            "--claim-map", str(self.fixture("valid-claim-map.json")), "--out", str(output),
        ])
        self.assertEqual(code, 2)
        self.assertIn("REPORT.JSON.INVALID", summary["finding_codes"])

    def test_canonical_weak_model_decision_table_and_executable_cases(self) -> None:
        path = ROOT / "references" / "weak-model-decision-table.json"
        self.assertEqual(decision_validator.validate_file(path, expected_skill_id="dft-reporting"), [])
        table = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(table["default_case_id"], table["cases"][-1]["case_id"])
        self.assertEqual(table["cases"][-1]["required_evidence"], [])
        self.assertEqual([item["priority"] for item in table["cases"]], list(range(1, len(table["cases"]) + 1)))
        for case in table["cases"]:
            with self.subTest(case_id=case["case_id"]):
                self.assertEqual(case["current_claim"], "no_positive_claim")
                self.assertIs(case["execution_authorized"], False)
                self.assertIs(case["promotion_authorized"], False)
                if case["case_id"] in {"report-unsafe-input-identity", table["default_case_id"]}:
                    continue
                request = self.load_request()
                claim_map = self.load_map()
                scenario = case["case_id"]
                if scenario == "report-unsupported-claim":
                    claim_map["claims"][0]["status"] = "blocked"
                    claim_map["claims"][0]["blocker_codes"] = ["synthetic-blocker"]
                elif scenario == "report-evidence-missing":
                    claim_map["evidence"][0]["status"] = "missing"
                elif scenario == "report-gate-blocked":
                    claim_map["gates"][0]["status"] = "blocked"
                elif scenario == "report-citation-missing":
                    request["citation_locators"] = []
                elif scenario == "report-section-unmapped":
                    request["sections"][0]["claim_ids"] = []
                elif scenario == "report-bilingual-unvalidated":
                    request["language"] = "bilingual"
                elif scenario == "report-positive-upstream":
                    claim_map["claim_ceiling"] = "technical_run_gates_only"
                    claim_map["claims"][0]["claim_level"] = "technical_run_gates_only"
                elif scenario == "report-private-path":
                    request["title"] = "private /Users/example/result"
                elif scenario == "report-unknown-claim":
                    request["selected_claim_ids"] = ["missing-claim"]
                    request["sections"][0]["claim_ids"] = []
                elif scenario == "report-thin-gate":
                    claim_map["gates"][0] = {"check_id": "technical-completion", "status": "pass"}
                elif scenario not in {"report-valid-no-positive", "report-hash-mismatch", "report-unsupported-claim"}:
                    self.fail(f"unhandled canonical scenario: {scenario}")
                map_path = self.write_json(f"{case['case_id']}-map.json", claim_map)
                _value, digest = cli.strict_load(map_path)
                request["claim_map_ref"]["sha256"] = "f" * 64 if scenario == "report-hash-mismatch" else digest
                request_path = self.write_json(f"{case['case_id']}-request.json", request)
                output = self.work / f"{case['case_id']}-plan.json"
                code, summary = self.invoke(["plan", "--request", str(request_path), "--claim-map", str(map_path), "--out", str(output)])
                self.assertIn(code, case["expected_exit_codes"])
                if case["finding_codes"]:
                    self.assertIn(summary["first_decisive_finding"], case["finding_codes"])
                else:
                    self.assertIsNone(summary["first_decisive_finding"])
                self.assertEqual(summary["maximum_claim"], case["current_claim"])
                self.assertFalse(summary["positive_claim_made"])
                self.assertFalse(summary["execute"])
                self.assertFalse(summary["send"])
                self.assertFalse(summary["publish"])
                self.assertFalse(summary["external_execution_performed"])
                self.assertEqual(summary["local_write_performed"], code in {0, 3})
                self.assertEqual(
                    summary["tool_invocation_mode"],
                    "execute-local-candidate-write" if code in {0, 3} else "execute-local-validation-only",
                )
                if code == 2:
                    self.assertFalse(output.exists())

    def test_skill_links_and_cross_contract_manual_are_complete(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for relative in re.findall(r"\]\(([^)]+)\)", skill):
            if "://" not in relative:
                self.assertTrue((ROOT / relative).is_file(), relative)
        manual = (ROOT / "references" / "repository-interface-manual.md").read_text(encoding="utf-8")
        for marker in (
            "Request and artifact schemas", "workflow-plan@1.0", "execution-lease@1.0",
            "workflow-event@1.0", "agent-action-envelope@1.0",
            "validate_agent_answer.py", "Evidence and citation handoff",
            "local_write_performed", "external_execution_performed",
        ):
            self.assertIn(marker, manual)

    def test_finding_catalog_exhaustively_matches_cli_literals(self) -> None:
        catalog = json.loads((ROOT / "references" / "finding-catalog.json").read_text(encoding="utf-8"))
        indexed = {item["code"]: (item["severity"], item["next_action"]) for item in catalog["findings"]}
        self.assertEqual(len(indexed), len(catalog["findings"]))
        discovered = {}
        tree = ast.parse((ROOT / "scripts" / "reporting_cli.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "finding" and len(node.args) >= 5:
                if all(isinstance(node.args[index], ast.Constant) and isinstance(node.args[index].value, str) for index in (0, 3, 4)):
                    discovered[node.args[0].value] = (node.args[4].value, node.args[3].value)
        self.assertEqual(indexed, discovered)


if __name__ == "__main__":
    unittest.main()
