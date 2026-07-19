from __future__ import annotations

import contextlib
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

import literature_plan_cli as cli
import validate_candidate_decision_table as decision_validator


class LiteraturePlanCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(cli._reset_io_bindings)
        self.work = Path(self.directory.name)

    def fixture(self) -> Path:
        return ROOT / "fixtures" / "valid-literature-request.json"

    def request(self) -> dict:
        return json.loads(self.fixture().read_text(encoding="utf-8"))

    def write_json(self, name: str, value: dict) -> Path:
        path = self.work / name
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def invoke(self, arguments: list[str]) -> tuple[int, dict]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli.main(arguments)
        return code, json.loads(output.getvalue())

    def plan(self, request_path: Path | None = None, name: str = "plan.json") -> tuple[int, dict, Path]:
        output = self.work / name
        code, summary = self.invoke(["plan", "--request", str(request_path or self.fixture()), "--out", str(output)])
        return code, summary, output

    def valid_plan_and_audit(self) -> tuple[Path, Path]:
        code, _summary, plan = self.plan()
        self.assertEqual(code, 0)
        audit = self.work / "audit.json"
        code, _summary = self.invoke(["audit", "--plan", str(plan), "--out", str(audit)])
        self.assertEqual(code, 0)
        return plan, audit

    def test_strict_json_rejects_duplicate_bom_nan_and_concatenation(self) -> None:
        values = (b'{"a":1,"a":2}', b'\xef\xbb\xbf{}', b'{"x":NaN}', b'{}{}')
        for index, raw in enumerate(values):
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

    def test_valid_plan_is_stable_and_separates_layers(self) -> None:
        first_code, _first, first = self.plan(name="first.json")
        second_code, _second, second = self.plan(name="second.json")
        self.assertEqual((first_code, second_code), (0, 0))
        self.assertEqual(first.read_bytes(), second.read_bytes())
        plan = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(plan["status"], "pass")
        self.assertEqual(plan["claim_ceiling"], "no_positive_claim")
        self.assertFalse(plan["network_access_performed"])
        self.assertFalse(plan["calculation_authorized"])
        self.assertFalse(plan["execution_started"])
        self.assertEqual(len(plan["retrieval_evidence"]), 1)
        self.assertEqual(len(plan["source_assertions"]), 1)
        self.assertEqual(len(plan["quoted_numerical_facts"]), 0)
        self.assertEqual(len(plan["proposed_inferences"]), 1)
        self.assertEqual(len(plan["project_choices"]), 1)
        self.assertEqual(len(plan["new_claim_proposals"]), 1)
        self.assertEqual(plan["source_assertions"][0]["classification"], "source-assertion")
        self.assertEqual(plan["project_choices"][0]["classification"], "project-choice")

    def test_metadata_only_source_cannot_support_fact(self) -> None:
        value = self.request()
        source = value["sources"][0]
        source["retrieval_status"] = "metadata-only"
        source["content_sha256"] = None
        source["source_record_ref"] = None
        code, summary, _ = self.plan(self.write_json("request.json", value))
        self.assertEqual(code, 3)
        self.assertIn("LIT.FACT.NOT_EXTRACTABLE", summary["finding_codes"])

    def test_official_manual_without_version_blocks(self) -> None:
        value = self.request()
        source = value["sources"][0]
        source["source_kind"] = "official-manual"
        source["version"] = None
        source["license_status"] = "known-open"
        source["source_record_ref"]["contract_name"] = "official-source-record"
        code, summary, _ = self.plan(self.write_json("request.json", value))
        self.assertEqual(code, 3)
        self.assertIn("LIT.SOURCE.VERSION_MISSING", summary["finding_codes"])

    def test_resolved_source_without_hash_blocks(self) -> None:
        value = self.request()
        value["sources"][0]["content_sha256"] = None
        code, summary, _ = self.plan(self.write_json("request.json", value))
        self.assertEqual(code, 3)
        self.assertIn("LIT.SOURCE.RETRIEVAL_EVIDENCE_MISSING", summary["finding_codes"])

    def test_unknown_inference_premise_is_invalid(self) -> None:
        value = self.request()
        value["inferences"][0]["premise_fact_ids"] = ["missing-fact"]
        code, summary, _ = self.plan(self.write_json("request.json", value))
        self.assertEqual(code, 2)
        self.assertIn("LIT.INFERENCE.PREMISE_INVALID", summary["finding_codes"])

    def test_fact_and_assumption_id_collision_is_invalid(self) -> None:
        value = self.request()
        value["assumptions"][0]["assumption_id"] = value["facts"][0]["fact_id"]
        code, summary, _ = self.plan(self.write_json("request.json", value))
        self.assertEqual(code, 2)
        self.assertIn("LIT.CLASSIFICATION.ID_COLLISION", summary["finding_codes"])

    def test_assumption_cannot_self_declare_external_validation(self) -> None:
        value = self.request()
        value["assumptions"][0]["status"] = "evidence-validated"
        value["assumptions"][0]["validation_evidence_ids"] = ["arbitrary-evidence"]
        code, summary, _ = self.plan(self.write_json("request.json", value))
        self.assertEqual(code, 3)
        self.assertIn("LIT.ASSUMPTION.EXTERNAL_EVIDENCE_REQUIRED", summary["finding_codes"])

    def test_planned_route_blocks_without_rerouting(self) -> None:
        value = self.request()
        value["calculation_steps"][0]["route_lifecycle"] = "planned"
        code, summary, _ = self.plan(self.write_json("request.json", value))
        self.assertEqual(code, 3)
        self.assertIn("LIT.STEP.ROUTE_NOT_ACTIVE", summary["finding_codes"])

    def test_execution_authorization_requirement_cannot_be_removed(self) -> None:
        value = self.request()
        value["calculation_steps"][0]["authorization_required"] = False
        code, summary, _ = self.plan(self.write_json("request.json", value))
        self.assertEqual(code, 2)
        self.assertIn("LIT.STEP.AUTHORITY_INVALID", summary["finding_codes"])

    def test_private_path_is_invalid(self) -> None:
        value = self.request()
        value["objective"] = "Inspect /" + "home/example/private output"
        code, summary, _ = self.plan(self.write_json("request.json", value))
        self.assertEqual(code, 2)
        self.assertIn("LIT.PRIVACY.UNSAFE_TEXT", summary["finding_codes"])
        self.assertFalse((self.work / "plan.json").exists())

    def test_citation_metadata_is_not_paper_content_evidence(self) -> None:
        value = self.request()
        source = value["sources"][0]
        source["retrieval_status"] = "metadata-only"
        source["content_sha256"] = None
        source["source_record_ref"] = None
        source["citation_label"] = "Complete-looking citation metadata is still not content"
        code, summary, output = self.plan(self.write_json("metadata-request.json", value))
        self.assertEqual(code, 3)
        self.assertIn("LIT.FACT.NOT_EXTRACTABLE", summary["finding_codes"])
        self.assertTrue(output.exists())

    def test_raw_paper_body_field_is_rejected_without_echo(self) -> None:
        value = self.request()
        sentinel = "SENTINEL_PRIVATE_PAPER_BODY"
        value["sources"][0]["body"] = sentinel
        output = self.work / "body-plan.json"
        code, summary, _ = self.plan(self.write_json("body-request.json", value), name=output.name)
        self.assertEqual(code, 2)
        self.assertEqual(summary["first_decisive_finding"], "LIT.SOURCE.INVALID")
        self.assertFalse(output.exists())

    def test_quoted_numerical_fact_requires_structured_quantity(self) -> None:
        value = self.request()
        fact = value["facts"][0]
        fact["classification"] = "quoted-numerical-fact"
        fact["text_mode"] = "structured-numerical"
        fact["quantity"] = {"value": 1.25, "unit": "eV", "reported_precision": "0.01 eV"}
        code, summary, output = self.plan(self.write_json("numeric-request.json", value))
        self.assertEqual(code, 0)
        self.assertEqual(summary["maximum_claim"], "no_positive_claim")
        plan = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(len(plan["quoted_numerical_facts"]), 1)
        self.assertEqual(len(plan["source_assertions"]), 0)

    def test_audit_and_render_bind_exact_plan(self) -> None:
        plan, audit = self.valid_plan_and_audit()
        package = self.work / "package.json"
        code, summary = self.invoke(["render-package", "--plan", str(plan), "--audit", str(audit), "--out", str(package)])
        self.assertEqual(code, 0)
        self.assertEqual(summary["status"], "pass")
        value = json.loads(package.read_text(encoding="utf-8"))
        self.assertTrue(value["draft_only"])
        self.assertFalse(value["network_access_performed"])
        self.assertFalse(value["execution_started"])

    def test_stale_audit_blocks_render(self) -> None:
        plan, audit = self.valid_plan_and_audit()
        value = json.loads(audit.read_text(encoding="utf-8"))
        value["subject_ref"]["sha256"] = "f" * 64
        stale = self.write_json("stale.json", value)
        code, summary = self.invoke(["render-package", "--plan", str(plan), "--audit", str(stale), "--out", str(self.work / "package.json")])
        self.assertEqual(code, 3)
        self.assertIn("LIT.RENDER.AUDIT_MISMATCH", summary["finding_codes"])
        self.assertFalse((self.work / "package.json").exists())

    def test_forged_pass_audit_cannot_authorize_modified_plan(self) -> None:
        plan, audit = self.valid_plan_and_audit()
        changed = json.loads(plan.read_text(encoding="utf-8"))
        changed["limitations"].append("manual post-audit edit")
        changed_plan = self.write_json("changed-plan.json", changed)
        _value, digest = cli.strict_load(changed_plan)
        forged = json.loads(audit.read_text(encoding="utf-8"))
        forged["subject_ref"]["sha256"] = digest
        forged_path = self.write_json("forged-audit.json", forged)
        output = self.work / "forged-package.json"
        code, summary = self.invoke(["render-package", "--plan", str(changed_plan), "--audit", str(forged_path), "--out", str(output)])
        self.assertEqual(code, 3)
        self.assertEqual(summary["first_decisive_finding"], "LIT.RENDER.AUDIT_MISMATCH")
        self.assertFalse(output.exists())

    def test_audit_rejects_forged_plan_with_embedded_source_body(self) -> None:
        plan, _audit = self.valid_plan_and_audit()
        value = json.loads(plan.read_text(encoding="utf-8"))
        value["retrieval_evidence"][0]["body"] = "SENTINEL_FORGED_PAPER_BODY"
        forged_plan = self.write_json("body-forged-plan.json", value)
        audit_out = self.work / "body-forged-audit.json"
        code, summary = self.invoke(["audit", "--plan", str(forged_plan), "--out", str(audit_out)])
        self.assertEqual(code, 2)
        self.assertIn("LIT.SOURCE.INVALID", summary["finding_codes"])
        self.assertFalse(audit_out.exists())

    def test_output_cannot_alias_input(self) -> None:
        request_path = self.fixture()
        before = request_path.read_bytes()
        code, summary = self.invoke(["plan", "--request", str(request_path), "--out", str(request_path)])
        self.assertEqual(code, 2)
        self.assertIn("LIT.JSON.INVALID", summary["finding_codes"])
        self.assertEqual(request_path.read_bytes(), before)
        hardlink = self.work / "request-output-alias.json"
        try:
            hardlink.hardlink_to(request_path)
        except OSError:
            self.skipTest("hardlinks unavailable")
        code, _summary = self.invoke(["plan", "--request", str(request_path), "--out", str(hardlink)])
        self.assertEqual(code, 2)
        hardlink.unlink()
        plan, audit = self.valid_plan_and_audit()
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
        code, summary = self.invoke(["plan", "--request", str(self.fixture()), "--out", str(output)])
        self.assertEqual(code, 2)
        self.assertIn("LIT.JSON.INVALID", summary["finding_codes"])

    def test_canonical_weak_model_decision_table_and_executable_cases(self) -> None:
        path = ROOT / "references" / "weak-model-decision-table.json"
        self.assertEqual(decision_validator.validate_file(path, expected_skill_id="literature-to-dft-plan"), [])
        table = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(table["default_case_id"], table["cases"][-1]["case_id"])
        self.assertEqual(table["cases"][-1]["required_evidence"], [])
        self.assertEqual([item["priority"] for item in table["cases"]], list(range(1, len(table["cases"]) + 1)))
        for case in table["cases"]:
            with self.subTest(case_id=case["case_id"]):
                self.assertEqual(case["current_claim"], "no_positive_claim")
                self.assertIs(case["execution_authorized"], False)
                self.assertIs(case["promotion_authorized"], False)
                if case["case_id"] in {"lit-unsafe-input-identity", table["default_case_id"]}:
                    continue
                value = self.request()
                scenario = case["case_id"]
                source = value["sources"][0]
                fact = value["facts"][0]
                if scenario == "lit-metadata-is-not-content":
                    source["retrieval_status"] = "metadata-only"
                    source["content_sha256"] = None
                    source["source_record_ref"] = None
                elif scenario == "lit-retrieval-hash-missing":
                    source["content_sha256"] = None
                elif scenario == "lit-official-version-missing":
                    source["source_kind"] = "official-manual"
                    source["version"] = None
                    source["license_status"] = "known-open"
                    source["source_record_ref"]["contract_name"] = "official-source-record"
                elif scenario == "lit-fact-locator-missing":
                    fact["locator"] = ""
                elif scenario == "lit-numerical-fact-unstructured":
                    fact["classification"] = "quoted-numerical-fact"
                elif scenario == "lit-inference-premise-unknown":
                    value["inferences"][0]["premise_fact_ids"] = ["missing-fact"]
                elif scenario == "lit-project-choice-self-validates":
                    value["assumptions"][0]["status"] = "evidence-validated"
                    value["assumptions"][0]["validation_evidence_ids"] = ["external-evidence"]
                elif scenario == "lit-new-claim-premise-unknown":
                    value["new_claims"][0]["premise_inference_ids"] = ["missing-inference"]
                elif scenario == "lit-planned-route-not-active":
                    value["calculation_steps"][0]["route_lifecycle"] = "planned"
                elif scenario == "lit-execution-authority-removed":
                    value["calculation_steps"][0]["authorization_required"] = False
                elif scenario == "lit-paper-body-forbidden":
                    source["body"] = "SENTINEL_BODY_MUST_NOT_BE_EMITTED"
                elif scenario == "lit-private-local-path":
                    value["objective"] = "inspect /home/example/private output"
                elif scenario != "lit-valid-five-way-separation":
                    self.fail(f"unhandled canonical scenario: {scenario}")
                request_path = self.write_json(f"{case['case_id']}-request.json", value)
                output = self.work / f"{case['case_id']}-plan.json"
                code, summary = self.invoke(["plan", "--request", str(request_path), "--out", str(output)])
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
            "validate_agent_answer.py", "Source and citation evidence",
            "local_write_performed", "external_execution_performed",
        ):
            self.assertIn(marker, manual)

    def test_finding_catalog_exhaustively_matches_cli_literals(self) -> None:
        catalog = json.loads((ROOT / "references" / "finding-catalog.json").read_text(encoding="utf-8"))
        indexed = {item["code"]: (item["severity"], item["next_action"]) for item in catalog["findings"]}
        self.assertEqual(len(indexed), len(catalog["findings"]))
        discovered = {}
        tree = ast.parse((ROOT / "scripts" / "literature_plan_cli.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "finding" and len(node.args) >= 5:
                if all(isinstance(node.args[index], ast.Constant) and isinstance(node.args[index].value, str) for index in (0, 3, 4)):
                    discovered[node.args[0].value] = (node.args[4].value, node.args[3].value)
        self.assertEqual(indexed, discovered)


if __name__ == "__main__":
    unittest.main()
