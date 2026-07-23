#!/usr/bin/env python3
"""Regression tests for the fail-closed QE guard."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import ssl
import urllib.error


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPT_DIR / "qe_guard.py"
spec = importlib.util.spec_from_file_location("qe_guard", MODULE_PATH)
assert spec and spec.loader
qe_guard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = qe_guard
spec.loader.exec_module(qe_guard)


VALID_INPUT = """&CONTROL
  calculation = 'scf',
  prefix = 'anon',
  outdir = './scratch',
  pseudo_dir = './pseudo',
/
&SYSTEM
  ibrav = 0,
  nat = 1,
  ntyp = 1,
  ecutwfc = 50.0,
  ecutrho = 400.0,
  occupations = 'fixed',
/
&ELECTRONS
  conv_thr = 1.0d-10,
/
ATOMIC_SPECIES
Si 28.085 Si.upf
ATOMIC_POSITIONS crystal
Si 0.0 0.0 0.0
K_POINTS automatic
4 4 4 0 0 0
CELL_PARAMETERS angstrom
5.4 0.0 0.0
0.0 5.4 0.0
0.0 0.0 5.4
"""


class QeGuardTests(unittest.TestCase):
    def run_cli(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-B", str(MODULE_PATH), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def make_plan(self, root: Path, task_type: str = "scf", absolute_tolerance: float = 1e-5) -> Path:
        plan = root / "qe_plan.json"
        self.run_cli(
            "plan",
            "--case-id",
            "anon-case",
            "--protocol-id",
            "protocol-001",
            "--task-type",
            task_type,
            "--qe-version",
            "7.5",
            "--objective",
            "Synthetic regression objective",
            "--observable",
            "total_energy",
            "--observable-unit",
            "Ry",
            "--absolute-tolerance",
            str(absolute_tolerance),
            "--out",
            str(plan),
        )
        return plan

    def make_pseudo_manifest(self, root: Path, pseudo_dir: Path) -> Path:
        pseudo = pseudo_dir / "Si.upf"
        manifest = root / "pseudo-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "pseudopotentials": [
                        {
                            "filename": pseudo.name,
                            "sha256": qe_guard.sha256_file(pseudo),
                            "source": "Synthetic regression fixture",
                            "source_url": "https://example.invalid/synthetic-regression-fixture",
                            "xc_functional": "PBE",
                            "relativistic": "scalar",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return manifest

    def test_valid_input_with_plan_and_pseudopotential_passes_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            input_path = root / "scf.in"
            input_path.write_text(VALID_INPUT, encoding="ascii")
            pseudo_dir = root / "pseudo"
            pseudo_dir.mkdir()
            (root / "scratch").mkdir()
            (pseudo_dir / "Si.upf").write_text(
                "<UPF version='2.0.1'><PP_HEADER functional='PBE' pseudo_type='NC' "
                "relativistic='scalar' has_so='.false.'/></UPF>\n",
                encoding="ascii",
            )
            pseudo_manifest = self.make_pseudo_manifest(root, pseudo_dir)
            plan = self.make_plan(root)
            report = root / "audit.json"
            self.run_cli(
                "audit",
                "--input",
                str(input_path),
                "--pseudo-dir",
                str(pseudo_dir),
                "--pseudo-manifest",
                str(pseudo_manifest),
                "--run-dir",
                str(root),
                "--expected-version",
                "7.5",
                "--plan",
                str(plan),
                "--out",
                str(report),
            )
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["decision"], "pass")
            self.assertEqual(payload["scientific_claim_decision"], "blocked")
            self.assertEqual(payload["gates"]["observable_convergence"], "not_assessed")
            self.assertNotIn(str(root), json.dumps(payload))
            self.assertNotIn("example.invalid", json.dumps(payload))

    def test_missing_plan_and_pseudopotentials_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            input_path = Path(tempdir) / "scf.in"
            input_path.write_text(VALID_INPUT, encoding="ascii")
            result = self.run_cli(
                "audit",
                "--input",
                str(input_path),
                "--run-dir",
                str(Path(tempdir)),
                "--expected-version",
                "7.5",
                expected=2,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "blocked")
            self.assertEqual(payload["gates"]["plan"], "incomplete")
            self.assertEqual(payload["gates"]["pseudopotential_provenance"], "incomplete")

    def test_audit_report_cannot_overwrite_an_evidence_file(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            input_path = root / "scf.in"
            input_path.write_text(VALID_INPUT, encoding="ascii")
            original = input_path.read_bytes()
            result = self.run_cli(
                "audit",
                "--input",
                str(input_path),
                "--run-dir",
                str(root),
                "--expected-version",
                "7.5",
                "--out",
                str(input_path),
                expected=2,
            )
            self.assertIn("must not overwrite", result.stderr)
            self.assertEqual(input_path.read_bytes(), original)

    def test_structural_input_errors_have_stable_codes(self) -> None:
        broken = VALID_INPUT.replace("ecutwfc = 50.0,\n", "").replace("4 4 4 0 0 0", "4 0 4 0 2 0")
        summary, findings = qe_guard.validate_pw_input(broken)
        codes = {item.code for item in findings}
        self.assertEqual(summary["calculation"], "scf")
        self.assertIn("QE.PW.REQUIRED.ECUTWFC", codes)
        self.assertIn("QE.PW.K_POINTS.AUTOMATIC_VALUES", codes)

    def test_unsupported_or_ambiguous_input_syntax_is_rejected(self) -> None:
        duplicate = VALID_INPUT.replace("ecutwfc = 50.0,", "ecutwfc = 40.0,\n  ecutwfc = 50.0,")
        _, findings = qe_guard.validate_pw_input(duplicate)
        self.assertIn("QE.INPUT.DUPLICATE_ASSIGNMENT", {item.code for item in findings})

        unsupported = VALID_INPUT.replace("occupations = 'fixed',", "occupations = 'fixed',\n  nspin = 2,")
        _, findings = qe_guard.validate_pw_input(unsupported)
        self.assertIn("QE.INPUT.UNSUPPORTED_ASSIGNMENT", {item.code for item in findings})

        expression = VALID_INPUT.replace("Si 0.0 0.0 0.0", "Si 1/2 0.0 0.0")
        _, findings = qe_guard.validate_pw_input(expression)
        self.assertIn("QE.PW.ATOMIC_POSITION_ROW", {item.code for item in findings})

        nonfinite = VALID_INPUT.replace("ecutwfc = 50.0", "ecutwfc = NaN")
        _, findings = qe_guard.validate_pw_input(nonfinite)
        self.assertIn("QE.PW.INVALID.ECUTWFC", {item.code for item in findings})

        unsupported_card = VALID_INPUT + "\nHUBBARD atomic\nU Si-3p 4.0\n"
        _, findings = qe_guard.validate_pw_input(unsupported_card)
        self.assertIn("QE.INPUT.UNSUPPORTED_CARD", {item.code for item in findings})

    def test_ibrav_cell_contract_is_enforced(self) -> None:
        broken = VALID_INPUT.replace("ibrav = 0,", "ibrav = 1,\n  A = 5.4,")
        _, findings = qe_guard.validate_pw_input(broken)
        self.assertIn("QE.PW.FORBIDDEN.CELL_PARAMETERS", {item.code for item in findings})

    def test_bands_requires_parent_manifest_before_decision_bundle(self) -> None:
        bands = VALID_INPUT.replace("calculation = 'scf'", "calculation = 'bands'")
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            input_path = root / "bands.in"
            input_path.write_text(bands, encoding="ascii")
            pseudo_dir = root / "pseudo"
            pseudo_dir.mkdir()
            (root / "scratch").mkdir()
            (pseudo_dir / "Si.upf").write_text("synthetic", encoding="ascii")
            pseudo_manifest = self.make_pseudo_manifest(root, pseudo_dir)
            plan = self.make_plan(root, "bands")
            result = self.run_cli(
                "audit",
                "--input",
                str(input_path),
                "--pseudo-dir",
                str(pseudo_dir),
                "--pseudo-manifest",
                str(pseudo_manifest),
                "--run-dir",
                str(root),
                "--expected-version",
                "7.5",
                "--plan",
                str(plan),
                expected=2,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["gates"]["parent_ancestry"], "fail")
            self.assertIn("QE.ANCESTRY.MISSING", {item["code"] for item in payload["findings"]})

    def test_bands_parent_requires_external_decision_bundle_verification(self) -> None:
        plan = {"case_id": "anon-case", "scientific_protocol_id": "protocol-001"}
        parent = {
            "schema_version": "1.0",
            "record_id": "run-parent",
            "code": "qe",
            "code_version": "7.5",
            "task_type": "scf",
            "case_id": "anon-case",
            "scientific_protocol_id": "protocol-001",
            "status": "completed",
            "scientific_acceptance": "requires_human_review",
            "configuration": {"prefix": "anon"},
            "metrics": {},
            "evidence": [
                {
                    "role": "charge_density",
                    "label": "density",
                    "status": "present",
                    "sha256": "a" * 64,
                }
            ],
            "limitations": [],
            "provenance": {
                "collector": "test",
                "collector_version": "1.0",
                "generated_utc": "2026-07-18T00:00:00+00:00",
            },
        }
        findings: list[qe_guard.Finding] = []
        self.assertEqual(
            qe_guard.validate_parent_manifest(parent, "bands", "from_scratch", "7.5", plan, "anon", findings),
            "fail",
        )
        self.assertIn(
            "QE.ANCESTRY.DECISION_BUNDLE_REQUIRED",
            {item.code for item in findings},
        )
        parent["scientific_protocol_id"] = "other"
        parent["evidence"] = []
        findings = []
        self.assertEqual(
            qe_guard.validate_parent_manifest(parent, "bands", "from_scratch", "7.5", plan, "anon", findings),
            "fail",
        )
        codes = {item.code for item in findings}
        self.assertIn("QE.ANCESTRY.PROTOCOL", codes)
        self.assertIn("QE.ANCESTRY.DENSITY_EVIDENCE", codes)

    def test_restart_requires_completed_parent_and_hash_bound_checkpoint(self) -> None:
        plan = {"case_id": "anon-case", "scientific_protocol_id": "protocol-001"}
        parent = {
            "schema_version": "1.0",
            "record_id": "run-restart-parent",
            "code": "qe",
            "code_version": "7.5",
            "task_type": "scf",
            "case_id": "anon-case",
            "scientific_protocol_id": "protocol-001",
            "status": "completed",
            "scientific_acceptance": "not_assessed",
            "configuration": {"prefix": "anon"},
            "metrics": {},
            "evidence": [
                {
                    "role": "restart_checkpoint",
                    "label": "restart-data",
                    "status": "present",
                    "sha256": "a" * 64,
                }
            ],
            "limitations": ["Scientific review is not required for restart reuse."],
            "provenance": {
                "collector": "test",
                "collector_version": "1.0",
                "generated_utc": "2026-07-18T00:00:00+00:00",
            },
        }
        findings: list[qe_guard.Finding] = []
        self.assertEqual(
            qe_guard.validate_parent_manifest(
                parent, "scf", "restart", "7.5", plan, "anon", findings
            ),
            "pass",
        )

        parent["status"] = "failed"
        findings = []
        self.assertEqual(
            qe_guard.validate_parent_manifest(
                parent, "scf", "restart", "7.5", plan, "anon", findings
            ),
            "fail",
        )
        self.assertIn(
            "QE.ANCESTRY.RESTART_PARENT_NOT_COMPLETED",
            {item.code for item in findings},
        )

    def test_unrecognized_pseudopotential_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            input_path = root / "scf.in"
            input_path.write_text(VALID_INPUT, encoding="ascii")
            pseudo_dir = root / "pseudo"
            pseudo_dir.mkdir()
            (root / "scratch").mkdir()
            (pseudo_dir / "Si.upf").write_text("not a pseudopotential\n", encoding="ascii")
            pseudo_manifest = self.make_pseudo_manifest(root, pseudo_dir)
            plan = self.make_plan(root)
            result = self.run_cli(
                "audit",
                "--input",
                str(input_path),
                "--pseudo-dir",
                str(pseudo_dir),
                "--pseudo-manifest",
                str(pseudo_manifest),
                "--run-dir",
                str(root),
                "--expected-version",
                "7.5",
                "--plan",
                str(plan),
                expected=2,
            )
            payload = json.loads(result.stdout)
            self.assertIn("QE.PSEUDO.UNRECOGNIZED_FORMAT", {item["code"] for item in payload["findings"]})

    def test_pseudopotential_manifest_is_required_and_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            input_path = root / "scf.in"
            input_path.write_text(VALID_INPUT, encoding="ascii")
            pseudo_dir = root / "pseudo"
            pseudo_dir.mkdir()
            (root / "scratch").mkdir()
            pseudo = pseudo_dir / "Si.upf"
            pseudo.write_text(
                "<UPF version='2.0.1'><PP_HEADER functional='PBE' pseudo_type='NC' "
                "relativistic='scalar' has_so='.false.'/></UPF>\n",
                encoding="ascii",
            )
            plan = self.make_plan(root)
            result = self.run_cli(
                "audit",
                "--input",
                str(input_path),
                "--pseudo-dir",
                str(pseudo_dir),
                "--run-dir",
                str(root),
                "--expected-version",
                "7.5",
                "--plan",
                str(plan),
                expected=2,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["gates"]["pseudopotential_provenance"], "incomplete")
            manifest = self.make_pseudo_manifest(root, pseudo_dir)
            pseudo.write_text(pseudo.read_text(encoding="ascii") + "tampered\n", encoding="ascii")
            result = self.run_cli(
                "audit",
                "--input",
                str(input_path),
                "--pseudo-dir",
                str(pseudo_dir),
                "--pseudo-manifest",
                str(manifest),
                "--run-dir",
                str(root),
                "--expected-version",
                "7.5",
                "--plan",
                str(plan),
                expected=2,
            )
            self.assertIn(
                "QE.PSEUDO.MANIFEST_HASH",
                {item["code"] for item in json.loads(result.stdout)["findings"]},
            )

    def test_output_echo_mismatch_blocks_completed_run(self) -> None:
        findings: list[qe_guard.Finding] = []
        status, _ = qe_guard.validate_output(
            "Program PWSCF v.7.5\n"
            "bravais-lattice index = 0\n"
            "number of atoms/cell = 2\n"
            "number of atomic types = 1\n"
            "kinetic-energy cutoff = 50.0 Ry\n"
            "convergence has been achieved\nJOB DONE.\n",
            "scf",
            findings,
            expected_summary={"ibrav": 0, "nat": 1, "ntyp": 1, "ecutwfc_ry": 50.0},
        )
        self.assertEqual(status, "fail")
        self.assertIn("QE.OUTPUT.INPUT_MISMATCH", {item.code for item in findings})

    def test_concatenated_outputs_are_rejected(self) -> None:
        output = (
            "Program PWSCF v.7.5\nconvergence has been achieved\nJOB DONE.\n"
            "Program PWSCF v.7.5\nconvergence has been achieved\nJOB DONE.\n"
        )
        findings: list[qe_guard.Finding] = []
        status, _ = qe_guard.validate_output(output, "scf", findings)
        self.assertEqual(status, "fail")
        codes = {item.code for item in findings}
        self.assertIn("QE.OUTPUT.MULTIPLE_RUNS", codes)
        self.assertIn("QE.OUTPUT.MULTIPLE_JOB_DONE", codes)

    def test_signalling_floating_point_stderr_blocks_runtime_diagnostics(self) -> None:
        findings: list[qe_guard.Finding] = []
        status, summary = qe_guard.validate_stderr(
            "Note: The following floating-point exceptions are signalling: "
            "IEEE_INVALID_FLAG IEEE_DIVIDE_BY_ZERO\n",
            findings,
        )
        self.assertEqual(status, "fail")
        self.assertGreater(summary["floating_point_exception_lines"], 0)
        self.assertIn("QE.STDERR.FLOATING_POINT_EXCEPTION", {item.code for item in findings})

    def test_empty_stderr_passes_runtime_diagnostics(self) -> None:
        findings: list[qe_guard.Finding] = []
        status, summary = qe_guard.validate_stderr("", findings)
        self.assertEqual(status, "pass")
        self.assertEqual(summary["nonempty_lines"], 0)

    def test_runtime_pseudo_directory_must_match_input_resolution(self) -> None:
        summary, findings = qe_guard.validate_pw_input(VALID_INPUT)
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "scratch").mkdir()
            other = root / "other-pseudo"
            other.mkdir()
            status = qe_guard.validate_runtime_paths(summary, root, other, findings)
        self.assertEqual(status, "fail")
        self.assertIn("QE.RUNTIME.PSEUDO_DIR_MISMATCH", {item.code for item in findings})

    def test_skill_text_preserves_fail_closed_rules(self) -> None:
        skill = (SCRIPT_DIR.parent / "SKILL.md").read_text(encoding="utf-8")
        contract = (SCRIPT_DIR.parent / "references" / "fail-closed-contract.md").read_text(encoding="utf-8")
        self.assertIn("Treat any nonzero exit", skill)
        self.assertIn("scientific_claim_decision: blocked", skill)
        for command in ["plan", "reference", "audit", "convergence"]:
            self.assertIn(f"`{command}`", contract)

    def test_job_done_does_not_hide_scf_failure(self) -> None:
        findings: list[qe_guard.Finding] = []
        status, summary = qe_guard.validate_output(
            "Program PWSCF v.7.5\nconvergence NOT achieved after 100 iterations\nJOB DONE.\n",
            "scf",
            findings,
        )
        self.assertEqual(status, "fail")
        self.assertTrue(summary["job_done"])
        self.assertIn("QE.OUTPUT.SCF_NOT_CONVERGED", {item.code for item in findings})

    def test_offline_reference_lookup_is_labeled_cached_only(self) -> None:
        self.assertEqual(qe_guard.manual_record("pw.x")["name"], "INPUT_PW")
        result = self.run_cli(
            "reference",
            "--executable",
            "pw.x",
            "--term",
            "ecutwfc",
            "--qe-version",
            "7.5",
            "--offline",
            expected=3,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "cached_only")
        self.assertEqual(len(payload["matches"]), 1)
        self.assertEqual(payload["matches"][0]["manual_version"], "7.5")

    def test_reference_version_mismatch_is_blocked(self) -> None:
        result = self.run_cli(
            "reference",
            "--executable",
            "pw.x",
            "--term",
            "ecutwfc",
            "--qe-version",
            "7.4",
            "--offline",
            expected=2,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "blocked_version_mismatch")
        self.assertIn("Exact behavior for QE 7.4", payload["required_disclosure"])

    def test_live_fetch_uses_tls_verified_curl_for_missing_python_ca_bundle(self) -> None:
        certificate_error = ssl.SSLCertVerificationError(1, "missing local issuer")
        completed = subprocess.CompletedProcess(["curl"], 0, stdout=b"official", stderr=b"")
        with (
            mock.patch.object(qe_guard.urllib.request, "urlopen", side_effect=urllib.error.URLError(certificate_error)),
            mock.patch.object(qe_guard.shutil, "which", return_value="/usr/bin/curl"),
            mock.patch.object(qe_guard.subprocess, "run", return_value=completed) as run,
        ):
            self.assertEqual(qe_guard.live_fetch("https://example.invalid/manual", 7.0), b"official")
        command = run.call_args.args[0]
        self.assertIn("--fail", command)
        self.assertNotIn("--insecure", command)

    def make_convergence_artifacts(
        self, root: Path, points: list[tuple[float, float, str]]
    ) -> list[tuple[float, float, str, str, str, str, str]]:
        pseudo_dir = root / "pseudo"
        pseudo_dir.mkdir()
        (root / "scratch").mkdir()
        (pseudo_dir / "Si.upf").write_text(
            "<UPF version='2.0.1'><PP_HEADER functional='PBE' pseudo_type='NC' "
            "relativistic='scalar' has_so='.false.'/></UPF>\n",
            encoding="ascii",
        )
        pseudo_manifest = self.make_pseudo_manifest(root, pseudo_dir)
        plan = self.make_plan(root, absolute_tolerance=0.1)
        rows: list[tuple[float, float, str, str, str, str, str]] = []
        for index, (setting, observable, protocol_id) in enumerate(points, start=1):
            input_path = root / f"point-{index}.in"
            output_path = root / f"point-{index}.out"
            stderr_path = root / f"point-{index}.err"
            audit_path = root / f"point-{index}.audit.json"
            input_path.write_text(
                VALID_INPUT.replace("ecutwfc = 50.0", f"ecutwfc = {setting}"), encoding="ascii"
            )
            output_path.write_text(
                "Program PWSCF v.7.5\n"
                "bravais-lattice index = 0\n"
                "number of atoms/cell = 1\n"
                "number of atomic types = 1\n"
                f"kinetic-energy cutoff = {setting} Ry\n"
                "charge density cutoff = 400.0 Ry\n"
                "iteration # 1\n"
                f"!    total energy = {observable} Ry\n"
                "convergence has been achieved\n"
                "JOB DONE.\n",
                encoding="ascii",
            )
            stderr_path.write_text("", encoding="ascii")
            self.run_cli(
                "audit",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--stderr",
                str(stderr_path),
                "--pseudo-dir",
                str(pseudo_dir),
                "--pseudo-manifest",
                str(pseudo_manifest),
                "--run-dir",
                str(root),
                "--expected-version",
                "7.5",
                "--plan",
                str(plan),
                "--out",
                str(audit_path),
            )
            rows.append(
                (
                    setting,
                    observable,
                    protocol_id,
                    audit_path.name,
                    input_path.name,
                    output_path.name,
                    stderr_path.name,
                )
            )
        return rows

    def write_convergence_csv(
        self, path: Path, points: list[tuple[float, float, str, str, str, str, str]]
    ) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "setting",
                    "observable",
                    "protocol_id",
                    "audit_report",
                    "input_file",
                    "output_file",
                    "stderr_file",
                ]
            )
            writer.writerows(points)

    def test_stable_tail_passes_but_physical_claim_remains_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            path = root / "convergence.csv"
            rows = self.make_convergence_artifacts(
                root,
                [(30, -10.0, "protocol-001"), (40, -10.05, "protocol-001"), (50, -10.050004, "protocol-001")],
            )
            self.write_convergence_csv(path, rows)
            result = self.run_cli(
                "convergence",
                "--csv",
                str(path),
                "--plan",
                str(root / "qe_plan.json"),
                "--protocol-id",
                "protocol-001",
                "--parameter",
                "ecutwfc",
                "--parameter-unit",
                "Ry",
                "--observable",
                "total_energy",
                "--observable-unit",
                "Ry",
                "--direction",
                "increasing",
                "--absolute-tolerance",
                "0.1",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "pass")
            self.assertEqual(payload["scientific_claim_decision"], "blocked")
            self.assertTrue(all("audit_sha256" in point for point in payload["points"]))
            self.assertNotIn(str(root), json.dumps(payload))

    def test_mixed_protocol_convergence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            path = root / "convergence.csv"
            rows = self.make_convergence_artifacts(
                root,
                [(30, -10.0, "protocol-001"), (40, -10.01, "other"), (50, -10.011, "protocol-001")],
            )
            self.write_convergence_csv(path, rows)
            result = self.run_cli(
                "convergence",
                "--csv",
                str(path),
                "--plan",
                str(root / "qe_plan.json"),
                "--protocol-id",
                "protocol-001",
                "--parameter",
                "ecutwfc",
                "--parameter-unit",
                "Ry",
                "--observable",
                "total_energy",
                "--observable-unit",
                "Ry",
                "--direction",
                "increasing",
                "--absolute-tolerance",
                "0.1",
                expected=2,
            )
            payload = json.loads(result.stdout)
            self.assertIn("QE.CONVERGENCE.PROTOCOL_MISMATCH", {item["code"] for item in payload["findings"]})

    def test_reused_audit_input_and_output_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            path = root / "convergence.csv"
            rows = self.make_convergence_artifacts(
                root,
                [(30, -10.0, "protocol-001"), (40, -10.01, "protocol-001"), (50, -10.011, "protocol-001")],
            )
            rows[1] = (40, -10.01, "protocol-001", rows[0][3], rows[0][4], rows[0][5], rows[1][6])
            self.write_convergence_csv(path, rows)
            result = self.run_cli(
                "convergence",
                "--csv",
                str(path),
                "--plan",
                str(root / "qe_plan.json"),
                "--protocol-id",
                "protocol-001",
                "--parameter",
                "ecutwfc",
                "--parameter-unit",
                "Ry",
                "--observable",
                "total_energy",
                "--observable-unit",
                "Ry",
                "--direction",
                "increasing",
                "--absolute-tolerance",
                "0.1",
                expected=2,
            )
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertTrue(
                {"QE.CONVERGENCE.DUPLICATE_AUDIT", "QE.CONVERGENCE.DUPLICATE_INPUT", "QE.CONVERGENCE.DUPLICATE_OUTPUT"}.issubset(codes)
            )

    def test_tampered_output_and_unsupported_observable_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            path = root / "convergence.csv"
            rows = self.make_convergence_artifacts(
                root,
                [(30, -10.0, "protocol-001"), (40, -10.01, "protocol-001"), (50, -10.011, "protocol-001")],
            )
            (root / rows[1][5]).write_text("tampered\n", encoding="ascii")
            self.write_convergence_csv(path, rows)
            result = self.run_cli(
                "convergence",
                "--csv",
                str(path),
                "--plan",
                str(root / "qe_plan.json"),
                "--protocol-id",
                "protocol-001",
                "--parameter",
                "ecutwfc",
                "--parameter-unit",
                "Ry",
                "--observable",
                "band_gap",
                "--observable-unit",
                "eV",
                "--direction",
                "increasing",
                "--absolute-tolerance",
                "0.1",
                expected=2,
            )
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("QE.CONVERGENCE.OUTPUT_HASH", codes)
            self.assertIn("QE.CONVERGENCE.OBSERVABLE_UNSUPPORTED", codes)

    def test_tampered_stderr_is_rejected_by_convergence_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            path = root / "convergence.csv"
            rows = self.make_convergence_artifacts(
                root,
                [(30, -10.0, "protocol-001"), (40, -10.01, "protocol-001"), (50, -10.011, "protocol-001")],
            )
            (root / rows[1][6]).write_text("changed after audit\n", encoding="ascii")
            self.write_convergence_csv(path, rows)
            result = self.run_cli(
                "convergence",
                "--csv",
                str(path),
                "--plan",
                str(root / "qe_plan.json"),
                "--protocol-id",
                "protocol-001",
                "--parameter",
                "ecutwfc",
                "--parameter-unit",
                "Ry",
                "--observable",
                "total_energy",
                "--observable-unit",
                "Ry",
                "--direction",
                "increasing",
                "--absolute-tolerance",
                "0.1",
                expected=2,
            )
            self.assertIn(
                "QE.CONVERGENCE.STDERR_HASH",
                {item["code"] for item in json.loads(result.stdout)["findings"]},
            )

    def test_plan_changed_after_audits_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            path = root / "convergence.csv"
            rows = self.make_convergence_artifacts(
                root,
                [(30, -10.0, "protocol-001"), (40, -10.01, "protocol-001"), (50, -10.011, "protocol-001")],
            )
            self.write_convergence_csv(path, rows)
            plan_path = root / "qe_plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["objective"] = "Changed after the run audits"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            result = self.run_cli(
                "convergence",
                "--csv",
                str(path),
                "--plan",
                str(plan_path),
                "--protocol-id",
                "protocol-001",
                "--parameter",
                "ecutwfc",
                "--parameter-unit",
                "Ry",
                "--observable",
                "total_energy",
                "--observable-unit",
                "Ry",
                "--direction",
                "increasing",
                "--absolute-tolerance",
                "0.1",
                expected=2,
            )
            codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
            self.assertIn("QE.CONVERGENCE.PLAN_HASH", codes)

    def test_incomplete_csv_row_blocks_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            plan = self.make_plan(root, absolute_tolerance=0.1)
            path = root / "convergence.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "setting",
                        "observable",
                        "protocol_id",
                        "audit_report",
                        "input_file",
                        "output_file",
                        "stderr_file",
                    ]
                )
                writer.writerow([30, -10.0, "protocol-001"])
            result = self.run_cli(
                "convergence",
                "--csv",
                str(path),
                "--plan",
                str(plan),
                "--protocol-id",
                "protocol-001",
                "--parameter",
                "ecutwfc",
                "--parameter-unit",
                "Ry",
                "--observable",
                "total_energy",
                "--observable-unit",
                "Ry",
                "--direction",
                "increasing",
                "--absolute-tolerance",
                "0.1",
                expected=2,
            )
            payload = json.loads(result.stdout)
            self.assertIn("QE.CONVERGENCE.AUDIT_REPORT_MISSING", {item["code"] for item in payload["findings"]})


if __name__ == "__main__":
    unittest.main(verbosity=2)
