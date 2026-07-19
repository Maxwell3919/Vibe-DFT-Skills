from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
GUARD_SPEC = importlib.util.spec_from_file_location(
    "vibe_dft_lobster_candidate_guard",
    ROOT / "scripts" / "lobster_guard.py",
)
if GUARD_SPEC is None or GUARD_SPEC.loader is None:
    raise RuntimeError("LOBSTER candidate guard module could not be loaded")
guard = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_SPEC.loader.exec_module(guard)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LobsterGuardTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        for source in FIXTURES.iterdir():
            if source.is_file():
                shutil.copyfile(source, self.base / source.name)
        self.request_path = self.base / "audit-request-pass.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def request(self) -> dict:
        return json.loads(self.request_path.read_text(encoding="utf-8"))

    def write_request(self, value: dict) -> None:
        self.request_path.write_text(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    def replace_artifact(self, request: dict, role: str, text: str) -> None:
        entry = next(item for item in request["artifacts"] if item["role"] == role)
        path = self.base / entry["file"]
        path.write_text(text, encoding="utf-8")
        entry["sha256"] = digest(path)

    def audit(self, request: dict | None = None) -> tuple[dict, int]:
        value = request if request is not None else self.request()
        return guard.audit_request(value, self.request_path)

    def test_synthetic_bonding_package_passes_all_gates(self) -> None:
        report, exit_code = self.audit()
        self.assertEqual(exit_code, guard.EXIT_OK)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["maturity"], "synthetic-validated")
        self.assertEqual(report["maximum_claim"], "no_positive_claim")
        self.assertEqual(set(report["gates"].values()), {"pass"})
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["metrics"]["cohp"]["maximum_integral_abs_error"], 0.0)

    def test_audit_is_deterministic(self) -> None:
        first, first_exit = self.audit()
        second, second_exit = self.audit()
        self.assertEqual(first_exit, second_exit)
        self.assertEqual(first, second)

    def test_parent_hash_mismatch_fails(self) -> None:
        request = self.request()
        request["parent"]["record_sha256"] = "a" * 64
        request["provider"]["execution_identity"]["parent_record_sha256"] = "a" * 64
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("LOB.PARENT.HASH_MISMATCH", {item["code"] for item in report["findings"]})
        self.assertEqual(report["gates"]["parent"], "fail")

    def test_execution_binding_mismatch_fails(self) -> None:
        request = self.request()
        request["provider"]["execution_identity"]["input_wavefunction_sha256"] = "a" * 64
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertEqual(report["gates"]["execution_binding"], "fail")

    def test_basis_mismatch_fails(self) -> None:
        request = self.request()
        request["basis"]["basis_by_element"]["Y"] = ["2s"]
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("LOB.BASIS.MISMATCH", {item["code"] for item in report["findings"]})

    def test_charge_spilling_threshold_is_not_silently_relaxed(self) -> None:
        request = self.request()
        request["thresholds"]["max_absolute_charge_spilling_percent"] = 1.0
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn(
            "LOB.PROJECTION.CHARGE_SPILLING_EXCEEDED",
            {item["code"] for item in report["findings"]},
        )

    def test_truncated_lobsterout_fails_completion(self) -> None:
        request = self.request()
        text = (self.base / "lobsterout.synthetic").read_text(encoding="utf-8")
        self.replace_artifact(request, "lobsterout", text.replace("LOBSTER run completed\n", ""))
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("LOB.COMPLETION.MARKER_MISSING", {item["code"] for item in report["findings"]})

    def test_unknown_curve_format_uses_parse_exit(self) -> None:
        request = self.request()
        self.replace_artifact(request, "cohp", "unrecognized curve\n")
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_PARSE)
        self.assertEqual(report["status"], "parse_failed")
        self.assertIn("LOB.PARSER.CURVE_FORMAT_UNSUPPORTED", {item["code"] for item in report["findings"]})

    def test_missing_sign_convention_uses_parse_exit(self) -> None:
        request = self.request()
        text = (self.base / "cohp.synthetic").read_text(encoding="utf-8")
        self.replace_artifact(request, "cohp", text.replace("# sign_convention=raw_cohp\n", ""))
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_PARSE)
        self.assertIn("LOB.CURVE.METADATA_MISSING", {item["code"] for item in report["findings"]})

    def test_integral_inconsistency_fails(self) -> None:
        request = self.request()
        text = (self.base / "cohp.synthetic").read_text(encoding="utf-8")
        self.replace_artifact(request, "cohp", text.replace("-1.0 -0.5 -0.75", "-1.0 -0.5 9.0"))
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("LOB.CURVE.INTEGRAL_INCONSISTENT", {item["code"] for item in report["findings"]})

    def test_dos_projection_closure_fails(self) -> None:
        request = self.request()
        text = (self.base / "dos.synthetic").read_text(encoding="utf-8")
        self.replace_artifact(request, "dos", text.replace("-1.0 2.0 1.95", "-1.0 2.0 0.20"))
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("LOB.DOS.PROJECTION_CLOSURE_FAILED", {item["code"] for item in report["findings"]})

    def test_scientific_claim_is_blocked(self) -> None:
        request = self.request()
        request["requested_claims"].append("bond-strength")
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_BLOCKED)
        self.assertEqual(report["status"], "blocked_external_evidence")
        self.assertEqual(report["maximum_claim"], "no_positive_claim")

    def test_real_artifact_route_stays_blocked(self) -> None:
        request = self.request()
        request["evidence_class"] = "real-artifact"
        request["provider"]["license_authorization"] = "attested-private-receipt"
        parent_path = self.base / request["parent"]["record_file"]
        parent = json.loads(parent_path.read_text(encoding="utf-8"))
        parent["evidence_class"] = "real-artifact"
        parent_path.write_text(json.dumps(parent, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        parent_hash = digest(parent_path)
        validation_path = self.base / request["parent"]["validation_file"]
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        validation["evidence_class"] = "real-artifact"
        validation["subject"]["record_sha256"] = parent_hash
        validation_path.write_text(
            json.dumps(validation, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validation_hash = digest(validation_path)
        request["parent"]["record_sha256"] = parent_hash
        request["parent"]["validation_sha256"] = validation_hash
        request["provider"]["execution_identity"]["parent_record_sha256"] = parent_hash
        request["provider"]["execution_identity"]["parent_validation_sha256"] = validation_hash
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_BLOCKED)
        self.assertIn(
            "LOB.ACTIVATION.REAL_ARTIFACT_VALIDATION_MISSING",
            {item["code"] for item in report["findings"]},
        )
        self.assertEqual(report["maturity"], "design-only")

    def test_version_drift_plan_is_blocked(self) -> None:
        plan = json.loads((ROOT / "examples" / "plan-request.json").read_text(encoding="utf-8"))
        plan["provider_version"] = "5.1.0"
        report = guard.make_plan(plan)
        status, exit_code = guard.determine_status(report["findings"])
        self.assertEqual(status, "blocked_external_evidence")
        self.assertEqual(exit_code, guard.EXIT_BLOCKED)

    def test_absolute_artifact_path_is_rejected_without_leak(self) -> None:
        request = self.request()
        request["artifacts"][0]["file"] = "/private/example/lobsterout"
        with self.assertRaises(guard.GuardError) as context:
            self.audit(request)
        self.assertEqual(context.exception.code, "LOB.INPUT.PRIVACY_VIOLATION")
        self.assertNotIn("/private/example", context.exception.message)

    def test_sensitive_key_is_rejected(self) -> None:
        request = self.request()
        request["provider"]["token"] = "synthetic-secret"
        with self.assertRaises(guard.GuardError) as context:
            self.audit(request)
        self.assertEqual(context.exception.code, "LOB.INPUT.PRIVACY_VIOLATION")
        self.assertNotIn("synthetic-secret", context.exception.message)

    def test_duplicate_json_key_is_rejected(self) -> None:
        path = self.base / "duplicate.json"
        path.write_text('{"contract_name":"a","contract_name":"b"}\n', encoding="utf-8")
        with self.assertRaises(guard.GuardError) as context:
            guard.load_json_object(path)
        self.assertEqual(context.exception.code, "LOB.INPUT.CONTRACT_INVALID")

    def test_utf8_bom_json_is_rejected(self) -> None:
        path = self.base / "bom.json"
        path.write_bytes(b"\xef\xbb\xbf{}\n")
        with self.assertRaises(guard.GuardError) as context:
            guard.load_json_object(path)
        self.assertEqual(context.exception.code, "LOB.INPUT.CONTRACT_INVALID")

    def test_nonfinite_json_number_is_rejected(self) -> None:
        path = self.base / "nan.json"
        path.write_text('{"value":NaN}\n', encoding="utf-8")
        with self.assertRaises(guard.GuardError) as context:
            guard.load_json_object(path)
        self.assertEqual(context.exception.code, "LOB.INPUT.CONTRACT_INVALID")

    def test_oversized_json_is_rejected(self) -> None:
        path = self.base / "oversized.json"
        path.write_bytes(b"{" + b" " * guard.MAX_JSON_BYTES)
        with self.assertRaises(guard.GuardError) as context:
            guard.load_json_object(path)
        self.assertEqual(context.exception.code, "LOB.INPUT.CONTRACT_INVALID")

    def test_symlink_input_is_rejected(self) -> None:
        target = self.base / "target.json"
        target.write_text("{}\n", encoding="utf-8")
        link = self.base / "linked.json"
        link.symlink_to(target.name)
        with self.assertRaises(guard.GuardError):
            guard.load_json_object(link)

    def test_symlink_artifact_is_rejected_through_audit(self) -> None:
        request = self.request()
        original = self.base / "lobsterout.synthetic"
        target = self.base / "lobsterout-target.synthetic"
        target.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(target.name)
        with self.assertRaises(guard.GuardError) as context:
            self.audit(request)
        self.assertEqual(context.exception.code, "LOB.INPUT.CONTRACT_INVALID")

    def test_hardlink_input_is_rejected(self) -> None:
        target = self.base / "target-hardlink.json"
        target.write_text("{}\n", encoding="utf-8")
        link = self.base / "hardlink.json"
        os.link(target, link)
        with self.assertRaises(guard.GuardError) as context:
            guard.load_json_object(link)
        self.assertEqual(context.exception.code, "LOB.INPUT.CONTRACT_INVALID")

    def test_file_change_during_read_is_rejected(self) -> None:
        target = self.base / "changing.json"
        target.write_text("{}\n", encoding="utf-8")
        moved = self.base / "changing-original.json"
        original_read = guard.os.read
        changed = False

        def changing_read(descriptor: int, size: int) -> bytes:
            nonlocal changed
            value = original_read(descriptor, size)
            if value and not changed:
                target.rename(moved)
                target.write_text("{}\n", encoding="utf-8")
                changed = True
            return value

        with mock.patch.object(guard.os, "read", changing_read):
            with self.assertRaises(guard.GuardError) as context:
                guard.load_json_object(target)
        self.assertEqual(context.exception.code, "LOB.INPUT.CONTRACT_INVALID")

    def test_hardlink_created_during_read_is_rejected(self) -> None:
        target = self.base / "read-time-hardlink.json"
        target.write_text("{}\n", encoding="utf-8")
        alias = self.base / "read-time-hardlink-alias.json"
        original_read = guard.os.read
        linked = False

        def linking_read(descriptor: int, size: int) -> bytes:
            nonlocal linked
            value = original_read(descriptor, size)
            if value and not linked:
                os.link(target, alias)
                linked = True
            return value

        with mock.patch.object(guard.os, "read", linking_read):
            with self.assertRaises(guard.GuardError) as context:
                guard.load_json_object(target)
        self.assertEqual(context.exception.code, "LOB.INPUT.CONTRACT_INVALID")

    def test_intermediate_directory_symlink_swap_is_rejected(self) -> None:
        subdirectory = self.base / "sub"
        subdirectory.mkdir()
        evidence = subdirectory / "evidence.synthetic"
        evidence.write_text("trusted\n", encoding="utf-8")
        moved = self.base / "sub-original"
        outside = self.base / "outside"
        outside.mkdir()
        (outside / evidence.name).write_text("outside\n", encoding="utf-8")
        original_open = guard.os.open
        swapped = False

        def racing_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
            nonlocal swapped
            if path == "sub" and kwargs.get("dir_fd") is not None and not swapped:
                subdirectory.rename(moved)
                subdirectory.symlink_to(outside, target_is_directory=True)
                swapped = True
            return original_open(path, flags, *args, **kwargs)

        with mock.patch.object(guard.os, "open", racing_open):
            with self.assertRaises(guard.GuardError):
                guard.read_relative_regular_bytes(self.base, "sub/evidence.synthetic", 1024)

    def test_request_bytes_and_evidence_share_one_stable_root(self) -> None:
        root = self.base / "stable-root"
        root.mkdir()
        request = root / "request.json"
        request.write_text("{}\n", encoding="utf-8")
        (root / "evidence.synthetic").write_text("trusted\n", encoding="utf-8")
        tracker = guard.InputTracker()
        guard.load_json_object(request, tracker, retain_parent=True)
        moved = self.base / "stable-root-original"
        root.rename(moved)
        root.mkdir()
        (root / "evidence.synthetic").write_text("replacement\n", encoding="utf-8")
        try:
            with self.assertRaises(guard.GuardError):
                guard.read_relative_regular_bytes(root, "evidence.synthetic", 1024, tracker)
        finally:
            tracker.close()

    def test_fifo_input_is_rejected_without_blocking(self) -> None:
        fifo = self.base / "blocked.json"
        os.mkfifo(fifo)
        previous_handler = signal.signal(signal.SIGALRM, lambda _signum, _frame: (_ for _ in ()).throw(TimeoutError()))
        signal.setitimer(signal.ITIMER_REAL, 1.0)
        try:
            with self.assertRaises(guard.GuardError):
                guard.load_json_object(fifo)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            signal.signal(signal.SIGALRM, previous_handler)

    def test_self_reported_parent_pass_without_bound_receipt_fails(self) -> None:
        request = self.request()
        parent_path = self.base / request["parent"]["record_file"]
        parent = json.loads(parent_path.read_text(encoding="utf-8"))
        self.assertEqual(set(parent["gates"].values()), {"pass"})
        parent["claim_ceiling"] = "self-reported-pass-is-not-independent-validation"
        parent_path.write_text(
            json.dumps(parent, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        parent_hash = digest(parent_path)
        request["parent"]["record_sha256"] = parent_hash
        request["provider"]["execution_identity"]["parent_record_sha256"] = parent_hash
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn(
            "LOB.PARENT.VALIDATION_DETACHED",
            {item["code"] for item in report["findings"]},
        )

    def test_parent_protocol_mismatch_fails(self) -> None:
        request = self.request()
        detached = "b" * 64
        request["parent"]["dft_protocol_sha256"] = detached
        request["provider"]["execution_identity"]["dft_protocol_sha256"] = detached
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("LOB.PARENT.IDENTITY_MISMATCH", {item["code"] for item in report["findings"]})

    def test_parent_potential_metadata_mismatch_fails(self) -> None:
        request = self.request()
        detached = "b" * 64
        request["parent"]["dft_input_hashes"]["potential_metadata_sha256"] = detached
        request["provider"]["execution_identity"]["dft_input_hashes"][
            "potential_metadata_sha256"
        ] = detached
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("LOB.PARENT.IDENTITY_MISMATCH", {item["code"] for item in report["findings"]})

    def test_incomplete_projected_band_population_fails(self) -> None:
        request = self.request()
        text = (self.base / "lobsterout.synthetic").read_text(encoding="utf-8")
        self.replace_artifact(request, "lobsterout", text.replace("projected band fraction: 1.0", "projected band fraction: 0.5"))
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("LOB.PROJECTION.INCOMPLETE", {item["code"] for item in report["findings"]})

    def test_curve_fermi_detachment_fails(self) -> None:
        request = self.request()
        text = (self.base / "cohp.synthetic").read_text(encoding="utf-8")
        self.replace_artifact(request, "cohp", text.replace("# fermi_energy_eV=0.0", "# fermi_energy_eV=0.1"))
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn(
            "LOB.CURVE.FERMI_ALIGNMENT_FAILED",
            {item["code"] for item in report["findings"]},
        )

    def test_each_task_profile_has_a_passing_mechanical_route(self) -> None:
        claims = {
            "projection-audit": ["projection-quality"],
            "cohp-audit": ["projection-quality", "cohp-curve"],
            "coop-audit": ["projection-quality", "coop-curve"],
            "dos-audit": ["projection-quality", "dos-projection-closure"],
            "bonding-package-audit": [
                "projection-quality",
                "cohp-curve",
                "coop-curve",
                "dos-projection-closure",
            ],
        }
        for task, requested_claims in claims.items():
            with self.subTest(task=task):
                request = self.request()
                request["task_id"] = task
                request["requested_claims"] = requested_claims
                expected_roles = set(guard.TASK_ARTIFACTS[task])
                request["artifacts"] = [
                    item for item in request["artifacts"] if item["role"] in expected_roles
                ]
                report, exit_code = self.audit(request)
                self.assertEqual(exit_code, guard.EXIT_OK)
                self.assertEqual(report["status"], "passed")

    def test_task_profile_rejects_ignored_extra_artifacts(self) -> None:
        request = self.request()
        request["task_id"] = "projection-audit"
        request["requested_claims"] = ["projection-quality"]
        report, exit_code = self.audit(request)
        self.assertEqual(exit_code, guard.EXIT_FAILED)
        self.assertIn("LOB.TASK.EVIDENCE_UNEXPECTED", {item["code"] for item in report["findings"]})

    def test_cli_emits_structured_report_and_stable_exit(self) -> None:
        output = self.base / "report.json"
        exit_code = guard.main(
            ["audit", "--request", str(self.request_path), "--output", str(output)]
        )
        self.assertEqual(exit_code, guard.EXIT_OK)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "passed")
        self.assertFalse(any(str(self.base) in json.dumps(item) for item in report["evidence"]))
        second_exit = guard.main(
            ["audit", "--request", str(self.request_path), "--output", str(output)]
        )
        self.assertEqual(second_exit, guard.EXIT_INPUT)
        original_report = output.read_bytes()
        overwrite_exit = guard.main(
            ["audit", "--request", str(self.request_path), "--output", str(output), "--overwrite"]
        )
        self.assertEqual(overwrite_exit, guard.EXIT_INPUT)
        self.assertEqual(output.read_bytes(), original_report)

    def test_cli_refuses_output_equal_to_request(self) -> None:
        original = self.request_path.read_bytes()
        exit_code = guard.main(
            [
                "audit",
                "--request",
                str(self.request_path),
                "--output",
                str(self.request_path),
            ]
        )
        self.assertEqual(exit_code, guard.EXIT_INPUT)
        self.assertEqual(self.request_path.read_bytes(), original)

    def test_cli_refuses_output_equal_to_artifact(self) -> None:
        artifact = self.base / "lobsterout.synthetic"
        original = artifact.read_bytes()
        exit_code = guard.main(
            [
                "audit",
                "--request",
                str(self.request_path),
                "--output",
                str(artifact),
            ]
        )
        self.assertEqual(exit_code, guard.EXIT_INPUT)
        self.assertEqual(artifact.read_bytes(), original)

    def test_output_hardlink_and_symlink_aliases_to_input_are_rejected(self) -> None:
        tracker = guard.InputTracker()
        guard.load_json_object(self.request_path, tracker)
        original = self.request_path.read_bytes()
        hardlink = self.base / "request-hardlink.json"
        symlink = self.base / "request-symlink.json"
        os.link(self.request_path, hardlink)
        symlink.symlink_to(self.request_path.name)
        for output in (hardlink, symlink):
            with self.subTest(output=output.name):
                with self.assertRaises(guard.GuardError):
                    guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, False, tracker)
        self.assertEqual(self.request_path.read_bytes(), original)

    def test_overwrite_is_rejected_and_preserves_existing_report(self) -> None:
        output = self.base / "preserved-report.json"
        original = b'{"old":"report"}\n'
        output.write_bytes(original)
        exit_code = guard.main(
            [
                "audit",
                "--request",
                str(self.request_path),
                "--output",
                str(output),
                "--overwrite",
            ]
        )
        self.assertEqual(exit_code, guard.EXIT_INPUT)
        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_staging_write_failure_leaves_no_report(self) -> None:
        output = self.base / "write-failure-report.json"
        with mock.patch.object(guard.os, "write", side_effect=OSError("synthetic write failure")):
            with self.assertRaises(guard.GuardError):
                guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, False)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_staging_path_substitution_cannot_publish_attacker_bytes(self) -> None:
        output = self.base / "substitution-report.json"
        original_link = guard.os.link
        substituted = False

        def substituting_link(source: str, target: str, *args: object, **kwargs: object) -> None:
            nonlocal substituted
            directory_fd = int(kwargs["src_dir_fd"])
            if not substituted:
                os.unlink(source, dir_fd=directory_fd)
                attacker_fd = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory_fd)
                os.write(attacker_fd, b"ATTACKER_BYTES")
                os.close(attacker_fd)
                substituted = True
            original_link(source, target, *args, **kwargs)

        with mock.patch.object(guard.os, "link", substituting_link):
            with self.assertRaises(guard.GuardError):
                guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, False)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_late_target_creation_is_not_overwritten(self) -> None:
        output = self.base / "late-target.json"
        original_link = guard.os.link
        victim = b'{"victim":true}\n'
        created = False

        def racing_link(source: str, target: str, *args: object, **kwargs: object) -> None:
            nonlocal created
            directory_fd = int(kwargs["dst_dir_fd"])
            if not created:
                target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory_fd)
                os.write(target_fd, victim)
                os.close(target_fd)
                created = True
            original_link(source, target, *args, **kwargs)

        with mock.patch.object(guard.os, "link", racing_link):
            with self.assertRaises(guard.GuardError):
                guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, False)
        self.assertEqual(output.read_bytes(), victim)
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_internal_overwrite_route_is_fail_closed(self) -> None:
        output = self.base / "exchange-target.json"
        original = b'{"old":true}\n'
        output.write_bytes(original)
        with self.assertRaises(guard.GuardError):
            guard.write_json_report(output, {"maximum_claim": "no_positive_claim"}, True)
        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(list(self.base.glob(".vibe-dft-report-*.tmp")), [])

    def test_reference_contracts_are_machine_readable(self) -> None:
        for name in (
            "finding-catalog.json",
            "fixture-manifest.json",
            "maturity-matrix.json",
            "task-evidence-profiles.json",
        ):
            value = json.loads((ROOT / "references" / name).read_text(encoding="utf-8"))
            self.assertEqual(value["schema_version"], "1.0")

    def test_canonical_weak_model_decision_table_is_fail_closed(self) -> None:
        value = json.loads(
            (ROOT / "references" / "weak-model-decision-table.json").read_text(encoding="utf-8")
        )
        cases = value["cases"]
        self.assertEqual(value["contract_name"], "candidate-decision-table")
        self.assertEqual(value["schema_version"], "1.0")
        self.assertEqual(value["skill_id"], "lobster-bonding-analysis")
        self.assertEqual(value["lifecycle"], "development")
        self.assertEqual(value["selection_policy"], "first-match-by-ascending-priority")
        self.assertEqual(value["current_claim"], "no_positive_claim")
        self.assertFalse(value["execution_authorized"])
        self.assertFalse(value["promotion_authorized"])
        self.assertEqual(len(cases), 11)
        self.assertEqual(len({item["case_id"] for item in cases}), 11)
        self.assertEqual([item["priority"] for item in cases], list(range(1, 12)))
        self.assertEqual({item["current_claim"] for item in cases}, {"no_positive_claim"})
        self.assertEqual({item["execution_authorized"] for item in cases}, {False})
        self.assertEqual({item["promotion_authorized"] for item in cases}, {False})
        self.assertTrue(all(item["minimum_next_action"] for item in cases))
        self.assertEqual(len({item["minimum_next_action"] for item in cases}), 11)
        self.assertEqual(value["default_case_id"], cases[-1]["case_id"])
        self.assertEqual(cases[-1]["required_evidence"], [])
        self.assertEqual(cases[-1]["action_state"], "local_gate_blocked")
        catalog = json.loads((ROOT / "references" / "finding-catalog.json").read_text(encoding="utf-8"))
        self.assertTrue({code for item in cases for code in item["finding_codes"]} <= set(catalog["findings"]))

    def test_skill_frontmatter_and_line_budget(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(text.splitlines()), 500)
        self.assertTrue(text.startswith("---\nname: lobster-bonding-analysis\n"))
        self.assertNotIn("\nTODO", text)


if __name__ == "__main__":
    unittest.main()
