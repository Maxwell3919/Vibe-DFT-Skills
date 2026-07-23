#!/usr/bin/env python3
"""Synthetic tests for the deterministic CP2K skill tools."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import analyze_convergence  # noqa: E402
import audit_cp2k_case  # noqa: E402
import probe_cp2k_tools  # noqa: E402
import resolve_official_sources  # noqa: E402
import sync_official_manuals  # noqa: E402
import sync_forward_fixtures  # noqa: E402
import validate_claim_package  # noqa: E402


def cp2k_input(run_type: str = "ENERGY", cutoff: int = 400) -> str:
    task_block = ""
    if run_type == "GEO_OPT":
        task_block = """&MOTION
  &GEO_OPT
    MAX_ITER 100
  &END GEO_OPT
&END MOTION
"""
    elif run_type == "MD":
        task_block = """&MOTION
  &MD
    ENSEMBLE NVE
    STEPS 10
    TIMESTEP 0.5
  &END MD
&END MOTION
"""
    return f"""&GLOBAL
  PROJECT_NAME anonymous
  RUN_TYPE {run_type}
&END GLOBAL
&FORCE_EVAL
  METHOD QS
  &DFT
    BASIS_SET_FILE_NAME BASIS_MOLOPT
    POTENTIAL_FILE_NAME GTH_POTENTIALS
    &MGRID
      CUTOFF {cutoff}
      REL_CUTOFF 50
    &END MGRID
    &POISSON
      PERIODIC NONE
    &END POISSON
    &SCF
      EPS_SCF 1.0E-6
      MAX_SCF 50
    &END SCF
    &XC
      &XC_FUNCTIONAL PBE
      &END XC_FUNCTIONAL
    &END XC
  &END DFT
  &SUBSYS
    &CELL
      ABC 10 10 10
      PERIODIC NONE
    &END CELL
    &COORD
      O 5.0 5.0 5.0
      H 5.7 5.0 5.5
      H 4.3 5.0 5.5
    &END COORD
    &KIND O
      BASIS_SET DZVP-MOLOPT-GTH
      POTENTIAL GTH-PBE-q6
    &END KIND
    &KIND H
      BASIS_SET DZVP-MOLOPT-GTH
      POTENTIAL GTH-PBE-q1
    &END KIND
  &END SUBSYS
&END FORCE_EVAL
{task_block}
"""


def cp2k_output(run_type: str = "ENERGY", *, warnings: int = 0, relax_marker: str | None = None) -> str:
    warning_line = "*** WARNING in synthetic_test :: redacted detail\n" if warnings else ""
    marker = f"{relax_marker}\n" if relax_marker else ""
    return (
        "CP2K| version string:                 CP2K version 2026.2\n"
        f"GLOBAL| Run type                                      {run_type}\n"
        "GLOBAL| Project name                                      anonymous\n"
        "GLOBAL| Basis set file name                            BASIS_MOLOPT\n"
        "GLOBAL| Potential file name                          GTH_POTENTIALS\n"
        "PROGRAM STARTED AT 2026-01-01 00:00:00\n"
        "*** SCF run converged in     5 steps ***\n"
        "ENERGY| Total FORCE_EVAL ( QS ) energy [hartree] -10.000000\n"
        f"{marker}{warning_line}The number of warnings for this run is : {warnings}\n"
        "PROGRAM ENDED AT 2026-01-01 00:00:01\n"
    )


class Fixture:
    def __init__(self, root: Path, run_type: str = "ENERGY", cutoff: int = 400) -> None:
        self.root = root
        self.input = root / "input.inp"
        self.output = root / "main.out"
        self.basis = root / "BASIS_MOLOPT"
        self.potential = root / "GTH_POTENTIALS"
        self.input.write_text(cp2k_input(run_type, cutoff), encoding="utf-8")
        self.basis.write_text("synthetic basis fixture\n", encoding="utf-8")
        self.potential.write_text("synthetic potential fixture\n", encoding="utf-8")

    @property
    def data(self) -> list[Path]:
        return [self.basis, self.potential]


class AuditTests(unittest.TestCase):
    def test_supported_input_passes_only_input_gates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            result = audit_cp2k_case.audit(fixture.input, task_type="static", data_files=fixture.data)
            self.assertEqual(result["decision"], "pass")
            self.assertEqual(result["gates"]["input_integrity"], "pass")
            self.assertEqual(result["gates"]["scientific_claim"], "blocked")
            self.assertEqual(result["files"]["input"]["safe_settings"]["kind_count"], 2)
            self.assertNotIn(directory, json.dumps(result))
            self.assertNotIn("anonymous", json.dumps(result))

    def test_unambiguous_cp2k_fixed_width_data_file_echo_passes_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fixture.output.write_text(
                cp2k_output().replace("BASIS_MOLOPT", "BASIS_M").replace("GTH_POTENTIALS", "GTH_POT"),
                encoding="utf-8",
            )
            result = audit_cp2k_case.audit(
                fixture.input,
                mode="run",
                task_type="static",
                output_path=fixture.output,
                data_files=fixture.data,
            )
            self.assertEqual(result["gates"]["input_output_binding"], "pass")

    def test_missing_data_hash_evidence_blocks_reproducibility(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            result = audit_cp2k_case.audit(fixture.input, task_type="static")
            self.assertEqual(result["decision"], "blocked")
            self.assertIn("missing-data-evidence", {item["code"] for item in result["findings"]})

    def test_preprocessor_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fixture.input.write_text("@SET X 1\n" + fixture.input.read_text(encoding="utf-8"), encoding="utf-8")
            result = audit_cp2k_case.audit(fixture.input, task_type="static", data_files=fixture.data)
            self.assertIn("unsupported-preprocessor", {item["code"] for item in result["findings"]})
            self.assertEqual(result["gates"]["input_integrity"], "fail")

    def test_mismatched_section_end_blocks(self) -> None:
        sections, findings = audit_cp2k_case.parse_input("&GLOBAL\nRUN_TYPE ENERGY\n&END FORCE_EVAL\n")
        self.assertTrue(sections)
        self.assertIn("mismatched-section-end", {item["code"] for item in findings})

    def test_task_run_type_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory), run_type="MD")
            result = audit_cp2k_case.audit(fixture.input, task_type="static", data_files=fixture.data)
            self.assertIn("task-run-type-mismatch", {item["code"] for item in result["findings"]})

    def test_relax_run_type_must_match_its_motion_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory), run_type="GEO_OPT")
            text = fixture.input.read_text(encoding="utf-8").replace("RUN_TYPE GEO_OPT", "RUN_TYPE CELL_OPT")
            fixture.input.write_text(text, encoding="utf-8")
            result = audit_cp2k_case.audit(fixture.input, task_type="relax", data_files=fixture.data)
            self.assertEqual(result["decision"], "blocked")
            self.assertIn("task-run-type-section-mismatch", {item["code"] for item in result["findings"]})

    def test_generic_profile_is_never_a_positive_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            result = audit_cp2k_case.audit(fixture.input, data_files=fixture.data)
            self.assertEqual(result["decision"], "blocked")
            self.assertIn("unsupported-generic-task-profile", {item["code"] for item in result["findings"]})

    def test_noncore_method_is_detected_and_blocks_deterministic_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            text = fixture.input.read_text(encoding="utf-8").replace(
                "&SCF\n", "&SCF\n      &OT\n      &END OT\n", 1
            )
            fixture.input.write_text(text, encoding="utf-8")
            result = audit_cp2k_case.audit(fixture.input, task_type="static", data_files=fixture.data)
            self.assertEqual(result["decision"], "blocked")
            self.assertEqual(result["gates"]["method_profile"], "not_evaluated")
            self.assertIn("ot", {item["name"] for item in result["profiles"]["methods"]})

    def test_completed_run_passes_technical_gates_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fixture.output.write_text(cp2k_output(), encoding="utf-8")
            result = audit_cp2k_case.audit(
                fixture.input,
                mode="run",
                task_type="static",
                output_path=fixture.output,
                data_files=fixture.data,
            )
            self.assertEqual(result["decision"], "pass")
            self.assertEqual(result["verdict"], "technical_run_gates_passed_scientific_claim_blocked")
            self.assertEqual(result["gates"]["execution_completion"], "pass")
            self.assertEqual(result["gates"]["electronic_convergence"], "pass")
            self.assertEqual(result["gates"]["input_output_binding"], "pass")
            self.assertEqual(result["gates"]["physical_validity"], "not_evaluated_by_single_case")
            self.assertEqual(result["scientific_claim_decision"], "blocked")

    def test_nonconverged_scf_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fixture.output.write_text(cp2k_output().replace("SCF run converged in     5 steps", "SCF run NOT converged"), encoding="utf-8")
            result = audit_cp2k_case.audit(
                fixture.input, mode="run", task_type="static", output_path=fixture.output, data_files=fixture.data
            )
            self.assertEqual(result["gates"]["electronic_convergence"], "fail")
            self.assertIn("scf-not-converged", {item["code"] for item in result["findings"]})

    def test_unrelated_output_identity_blocks_pairing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fixture.output.write_text(cp2k_output().replace("BASIS_MOLOPT", "UNRELATED_BASIS"), encoding="utf-8")
            result = audit_cp2k_case.audit(
                fixture.input, mode="run", task_type="static", output_path=fixture.output, data_files=fixture.data
            )
            serialized = json.dumps(result)
            self.assertEqual(result["gates"]["input_output_binding"], "fail")
            self.assertIn("input-output-identity-mismatch", {item["code"] for item in result["findings"]})
            self.assertNotIn("UNRELATED_BASIS", serialized)
            self.assertNotIn("anonymous", serialized)

    def test_warning_blocks_without_emitting_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fixture.output.write_text(cp2k_output(warnings=1), encoding="utf-8")
            result = audit_cp2k_case.audit(
                fixture.input, mode="run", task_type="static", output_path=fixture.output, data_files=fixture.data
            )
            serialized = json.dumps(result)
            self.assertEqual(result["gates"]["output_warnings"], "fail")
            self.assertNotIn("synthetic_test", serialized)
            self.assertNotIn("redacted detail", serialized)

    def test_relax_requires_supported_completion_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory), run_type="GEO_OPT")
            final_structure = Path(directory) / "final.xyz"
            force_history = Path(directory) / "forces.dat"
            final_structure.write_text("synthetic final structure\n", encoding="utf-8")
            force_history.write_text("synthetic force history\n", encoding="utf-8")
            evidence = [("final-structure", final_structure), ("force-history", force_history)]
            fixture.output.write_text(cp2k_output("GEO_OPT"), encoding="utf-8")
            blocked = audit_cp2k_case.audit(
                fixture.input,
                mode="run",
                task_type="relax",
                output_path=fixture.output,
                data_files=fixture.data,
                evidence_files=evidence,
            )
            self.assertEqual(blocked["gates"]["ionic_or_task_completion"], "fail")
            fixture.output.write_text(cp2k_output("GEO_OPT", relax_marker="GEOMETRY OPTIMIZATION COMPLETED"), encoding="utf-8")
            passed = audit_cp2k_case.audit(
                fixture.input,
                mode="run",
                task_type="relax",
                output_path=fixture.output,
                data_files=fixture.data,
                evidence_files=evidence,
            )
            self.assertEqual(passed["gates"]["ionic_or_task_completion"], "pass")
            self.assertEqual(passed["decision"], "pass")

    def test_relax_missing_evidence_blocks_without_leaking_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory), run_type="GEO_OPT")
            fixture.output.write_text(cp2k_output("GEO_OPT", relax_marker="GEOMETRY OPTIMIZATION COMPLETED"), encoding="utf-8")
            result = audit_cp2k_case.audit(
                fixture.input, mode="run", task_type="relax", output_path=fixture.output, data_files=fixture.data
            )
            serialized = json.dumps(result)
            self.assertEqual(result["gates"]["evidence_inventory"], "fail")
            self.assertIn("missing-run-evidence", {item["code"] for item in result["findings"]})
            self.assertNotIn(directory, serialized)

    def test_md_profile_can_validate_input_but_run_completion_stays_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory), run_type="MD")
            input_result = audit_cp2k_case.audit(fixture.input, task_type="md", data_files=fixture.data)
            self.assertEqual(input_result["decision"], "pass")
            self.assertEqual(input_result["profiles"]["task"]["run_audit_maturity"], "evidence-profile")

            fixture.output.write_text(cp2k_output("MD"), encoding="utf-8")
            evidence = []
            for role in ("trajectory", "energy-history", "restart-lineage"):
                path = Path(directory) / f"{role}.dat"
                path.write_text(f"synthetic {role}\n", encoding="utf-8")
                evidence.append((role, path))
            run_result = audit_cp2k_case.audit(
                fixture.input,
                mode="run",
                task_type="md",
                output_path=fixture.output,
                data_files=fixture.data,
                evidence_files=evidence,
            )
            self.assertEqual(run_result["gates"]["evidence_inventory"], "pass")
            self.assertEqual(run_result["gates"]["ionic_or_task_completion"], "not_evaluated")
            self.assertEqual(run_result["decision"], "blocked")
            self.assertIn("task-completion-not-deterministically-validated", {item["code"] for item in run_result["findings"]})

    def test_unknown_evidence_role_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            unknown = Path(directory) / "secret-hostname.dat"
            unknown.write_text("private content must not be emitted\n", encoding="utf-8")
            result = audit_cp2k_case.audit(
                fixture.input,
                task_type="static",
                data_files=fixture.data,
                evidence_files=[("typo-role", unknown)],
            )
            serialized = json.dumps(result)
            self.assertEqual(result["decision"], "blocked")
            self.assertIn("unknown-evidence-role", {item["code"] for item in result["findings"]})
            self.assertNotIn("secret-hostname", serialized)
            self.assertNotIn("private content", serialized)

    def test_cli_exit_code_tracks_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "audit_cp2k_case.py"),
                    str(fixture.input),
                    "--task-type",
                    "static",
                    "--data-file",
                    str(fixture.basis),
                    "--data-file",
                    str(fixture.potential),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "pass")


class OfficialSourceTests(unittest.TestCase):
    def test_fetch_retries_a_transient_network_failure(self) -> None:
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = b"official"
        response.geturl.return_value = "https://manual.cp2k.org/trunk/CP2K_INPUT.html"
        response.status = 200
        transient = urllib.error.URLError("temporary")
        with patch.object(
            resolve_official_sources.urllib.request,
            "urlopen",
            side_effect=[transient, response],
        ) as urlopen, patch.object(resolve_official_sources.time, "sleep") as sleep:
            result = resolve_official_sources.fetch_url("https://manual.cp2k.org/trunk/CP2K_INPUT.html")
        self.assertEqual(result["http_status"], 200)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once()

    def test_fetch_uses_an_explicit_verified_ca_context(self) -> None:
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = b"official"
        response.geturl.return_value = "https://manual.cp2k.org/trunk/CP2K_INPUT.html"
        response.status = 200
        with patch.object(resolve_official_sources.urllib.request, "urlopen", return_value=response) as urlopen:
            resolve_official_sources.fetch_url("https://manual.cp2k.org/trunk/CP2K_INPUT.html")
        context = urlopen.call_args.kwargs.get("context")
        self.assertIsNotNone(context)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode.name, "CERT_REQUIRED")

    def test_versioned_offline_urls_are_exact(self) -> None:
        result = resolve_official_sources.resolve(["GLOBAL", "eps_scf"], "2025.2", live_check=False)
        self.assertEqual(result["status"], "resolved_url_only")
        self.assertTrue(all("/cp2k-2025_2-branch/" in item["url"] for item in result["resolved"]))
        self.assertTrue(all(item["verification"] == "url_only_not_live_verified" for item in result["resolved"]))

    def test_current_offline_snapshot_is_version_matched_and_hash_checked(self) -> None:
        result = resolve_official_sources.resolve(["GLOBAL", "eps_scf"], "2026.2", live_check=False)
        self.assertEqual(result["status"], "pass_cached_version_matched")
        self.assertTrue(all(item["verification"] == "cached_version_matched" for item in result["resolved"]))
        self.assertTrue(all(item["local_reference"].startswith("references/official-manual/") for item in result["resolved"]))

    def test_version_specific_source_path_override(self) -> None:
        current = resolve_official_sources.resolve(["pdos"], "2026.2", live_check=False)
        older = resolve_official_sources.resolve(["pdos"], "2025.2", live_check=False)
        self.assertTrue(current["resolved"][0]["url"].endswith("/DFT/PRINT/DOS/PDOS.html"))
        self.assertTrue(older["resolved"][0]["url"].endswith("/DFT/PRINT/PDOS.html"))

    def test_live_check_records_hash(self) -> None:
        def fake_fetch(url: str) -> dict[str, object]:
            return {
                "http_status": 200,
                "final_url": url,
                "content_sha256": "a" * 64,
                "bytes": 10,
                "retrieved_utc": "2026-07-18T00:00:00+00:00",
            }

        result = resolve_official_sources.resolve(["scf"], "2026.2", live_check=True, fetcher=fake_fetch)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["resolved"][0]["content_sha256"], "a" * 64)

    def test_unknown_topic_blocks(self) -> None:
        result = resolve_official_sources.resolve(["not-a-cp2k-topic"], "2026.2", live_check=False)
        self.assertEqual(result["status"], "blocked_official_source")
        self.assertEqual(result["missing"], ["not-a-cp2k-topic"])

    def test_invalid_version_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit CP2K release"):
            resolve_official_sources.manual_branch("latest")


class OfficialMirrorTests(unittest.TestCase):
    def test_readthedocs_role_main_is_extracted(self) -> None:
        body = b"""<html><body><nav>private navigation</nav>
        <div class='document' role='main'><section><h1>FORCE_EVAL</h1>
        <p>Official section content.</p><p>Second official paragraph.</p>
        </section></div></body></html>"""
        rendered = sync_official_manuals.page_to_markdown(
            "force-eval",
            "https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT/FORCE_EVAL.html",
            body,
        ).decode("utf-8")
        self.assertIn("Official section content.", rendered)
        self.assertNotIn("private navigation", rendered)

    def test_checked_in_snapshot_matches_registry_and_inventory(self) -> None:
        result = sync_official_manuals.check_snapshot()
        self.assertEqual(result["status"], "ok", result["errors"])
        self.assertGreaterEqual(result["index_page_count"], 2900)
        self.assertGreaterEqual(result["mirrored_topic_count"], 80)


class ForwardFixtureTests(unittest.TestCase):
    def test_checked_in_official_derived_fixture_matches_manifest(self) -> None:
        result = sync_forward_fixtures.check()
        self.assertEqual(result["status"], "ok", result["errors"])

    def test_cp2k_9_fixture_exercises_markers_and_blocks_runtime_warning(self) -> None:
        fixture = sync_forward_fixtures.OUTPUT_PATH.read_text(encoding="utf-8")
        findings: list[dict[str, str]] = []
        summary, gates = audit_cp2k_case.inspect_output(
            fixture,
            "static",
            "ENERGY_FORCE",
            {
                "project": "fixture-project",
                "basis_files": {"BASIS_SET"},
                "potential_files": {"GTH_POTENTIALS"},
            },
            findings,
        )
        self.assertEqual(summary["version"], "CP2K version 9.0 (Development Version)")
        self.assertEqual(gates["execution_completion"], "pass")
        self.assertEqual(gates["electronic_convergence"], "pass")
        self.assertEqual(gates["input_output_binding"], "pass")
        self.assertEqual(gates["runtime_environment"], "fail")
        self.assertIn("runtime-environment-warning", {item["code"] for item in findings})
        self.assertNotIn("fixture-host", json.dumps({"summary": summary, "findings": findings}))

    def test_forward_fixture_contains_no_private_source_identity(self) -> None:
        text = sync_forward_fixtures.OUTPUT_PATH.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"/(?:Users|home|users|data)/", text))
        self.assertIn("PROGRAM STARTED ON", text)
        self.assertIn("fixture-host", text)
        self.assertIn("fixture-user", text)


class ToolProbeTests(unittest.TestCase):
    def test_probe_detects_capabilities_without_paths_or_execution(self) -> None:
        def fake_which(command: str) -> str | None:
            return f"/private/bin/{command}" if command in {"cp2k.psmp", "cp2kparse"} else None

        def fake_version(package: str) -> str:
            if package == "cp2k-output-tools":
                return "0.6.0"
            raise probe_cp2k_tools.importlib.metadata.PackageNotFoundError

        with patch.object(probe_cp2k_tools.shutil, "which", side_effect=fake_which), patch.object(
            probe_cp2k_tools.importlib.metadata, "version", side_effect=fake_version
        ):
            result = probe_cp2k_tools.probe()
        serialized = json.dumps(result)
        self.assertTrue(result["capabilities"]["cp2k-runtime"]["available"])
        self.assertTrue(result["capabilities"]["output-parse"]["available"])
        self.assertEqual(result["capabilities"]["output-parse"]["package_version"], "0.6.0")
        self.assertFalse(result["capabilities"]["output-parse"]["execution_performed"])
        self.assertNotIn("/private/bin", serialized)
        self.assertNotIn('"path"', serialized)


class SkillContractTests(unittest.TestCase):
    def test_profiles_cover_auditor_tasks_and_every_official_topic(self) -> None:
        self.assertEqual(set(audit_cp2k_case.TASK_PROFILES), set(audit_cp2k_case.TASK_RUN_TYPES))
        self.assertEqual(
            {profile["run_audit_maturity"] for profile in audit_cp2k_case.TASK_PROFILES.values()},
            {"deterministic-core", "evidence-profile", "blocked"},
        )
        topics: set[str] = set()
        for profile in audit_cp2k_case.TASK_PROFILES.values():
            topics.update(profile.get("required_source_topics", []))
        for profile in audit_cp2k_case.METHOD_PROFILES.values():
            topics.update(profile.get("source_topics", []))
        result = resolve_official_sources.resolve(sorted(topics), "2026.2", live_check=False)
        self.assertEqual(result["status"], "pass_cached_version_matched", result)
        self.assertEqual({record["topic"] for record in result["resolved"]}, topics)

    def test_skill_text_preserves_maturity_and_claim_boundaries(self) -> None:
        skill = (SCRIPT_DIR.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(skill.splitlines()), 500)
        self.assertIn("eligible_for_expert_review", skill)
        self.assertIn("does not raise CP2K 2026.2 or postprocessing maturity", skill)
        self.assertIn("input/output identity binding", skill)


class ConvergenceTests(unittest.TestCase):
    def write_passing_audit(self, root: Path, index: int, cutoff: int) -> Path:
        case = root / f"case-{index}"
        case.mkdir()
        fixture = Fixture(case, cutoff=cutoff)
        fixture.output.write_text(cp2k_output(), encoding="utf-8")
        result = audit_cp2k_case.audit(
            fixture.input, mode="run", task_type="static", output_path=fixture.output, data_files=fixture.data
        )
        audit_path = root / f"audit-{index}.json"
        audit_path.write_text(json.dumps(result), encoding="utf-8")
        return audit_path

    def test_evidence_linked_stable_tail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            series = root / "series.csv"
            with series.open("w", newline="", encoding="utf-8") as handle:
                fieldnames = [
                    "run_id", "cutoff", "energy", "observable", "unit", "protocol_id",
                    "comparability_group", "state_label", "audit_json",
                ]
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for index, (cutoff, energy) in enumerate(((400, -10.0), (500, -10.0005), (600, -10.0004)), 1):
                    audit = self.write_passing_audit(root, index, cutoff)
                    writer.writerow(
                        {
                            "run_id": f"run-{index}",
                            "cutoff": cutoff,
                            "energy": energy,
                            "observable": "total_energy",
                            "unit": "hartree",
                            "protocol_id": "protocol-a",
                            "comparability_group": "group-a",
                            "state_label": "state-a",
                            "audit_json": audit.name,
                        }
                    )
            rows = analyze_convergence.load_series(series, "cutoff", "energy")
            result = analyze_convergence.analyze(rows, abs_tol=0.001, rel_tol=0, min_tail=3)
            self.assertEqual(result["status"], "candidate_found")
            self.assertEqual(result["gates"]["physical_validity"], "not_assessed")
            self.assertIn("numerical convergence candidate", result["allowed_evidence_label"])

    def test_two_point_tail_is_rejected(self) -> None:
        rows = [
            {
                "x": 400.0,
                "y": -10.0,
                "run_id": "run-1",
                "observable": "energy",
                "unit": "hartree",
                "protocol_id": "p",
                "comparability_group": "g",
                "state_label": "s",
                "audit_sha256": "a" * 64,
                "task_type": "static",
            },
            {
                "x": 500.0,
                "y": -10.1,
                "run_id": "run-2",
                "observable": "energy",
                "unit": "hartree",
                "protocol_id": "p",
                "comparability_group": "g",
                "state_label": "s",
                "audit_sha256": "b" * 64,
                "task_type": "static",
            },
        ]
        with self.assertRaisesRegex(ValueError, "at least 3"):
            analyze_convergence.analyze(rows, abs_tol=0.001, rel_tol=0, min_tail=2)


class ClaimPackageTests(unittest.TestCase):
    def make_package(self, root: Path, *, omit_check: bool = False, tamper_source: bool = False) -> Path:
        audit_paths: list[Path] = []
        rows: list[dict[str, object]] = []
        for index, (cutoff, energy) in enumerate(((400, -10.0), (500, -10.0005), (600, -10.0004)), 1):
            case = root / f"claim-case-{index}"
            case.mkdir()
            fixture = Fixture(case, cutoff=cutoff)
            fixture.output.write_text(cp2k_output(), encoding="utf-8")
            audit = audit_cp2k_case.audit(
                fixture.input, mode="run", task_type="static", output_path=fixture.output, data_files=fixture.data
            )
            audit_path = root / f"claim-audit-{index}.json"
            audit_path.write_text(json.dumps(audit), encoding="utf-8")
            audit_paths.append(audit_path)
            rows.append(
                {
                    "x": float(cutoff),
                    "y": energy,
                    "run_id": f"claim-run-{index}",
                    "observable": "total_energy",
                    "unit": "hartree",
                    "protocol_id": "protocol-a",
                    "comparability_group": "group-a",
                    "state_label": "state-a",
                    "audit_sha256": analyze_convergence.sha256_file(audit_path),
                    "task_type": "static",
                }
            )
        convergence = analyze_convergence.analyze(rows, abs_tol=0.001, rel_tol=0.0, min_tail=3)
        convergence_path = root / "convergence.json"
        convergence_path.write_text(json.dumps(convergence), encoding="utf-8")

        selected_audit = json.loads(audit_paths[-1].read_text(encoding="utf-8"))
        topics = set(selected_audit["profiles"]["task"]["required_source_topics"])
        for method in selected_audit["profiles"]["methods"]:
            topics.update(method["source_topics"])
        official = resolve_official_sources.resolve(sorted(topics), "2026.2", live_check=False)
        if tamper_source:
            official["resolved"][0]["snapshot_sha256"] = "0" * 64
        official_path = root / "official-sources.json"
        official_path.write_text(json.dumps(official), encoding="utf-8")

        review = root / "review.md"
        review.write_text("synthetic expert-review fixture\n", encoding="utf-8")
        _, required = validate_claim_package.load_task_profile("static")
        check_ids = sorted(required)
        if omit_check:
            check_ids = check_ids[1:]
        package = {
            "schema_version": "1.0",
            "claim_id": "claim-static-001",
            "task_type": "static",
            "observable": "total_energy",
            "unit": "hartree",
            "absolute_tolerance": 0.001,
            "relative_tolerance": 0.0,
            "audit_json": audit_paths[-1].name,
            "convergence_json": convergence_path.name,
            "official_sources_json": official_path.name,
            "checks": [
                {"id": check_id, "status": "pass", "evidence_files": [review.name]}
                for check_id in check_ids
            ],
        }
        package_path = root / "claim-package.json"
        package_path.write_text(json.dumps(package), encoding="utf-8")
        return package_path

    def test_complete_package_is_only_eligible_for_expert_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = validate_claim_package.validate_package(self.make_package(Path(directory)))
            self.assertEqual(result["status"], "eligible_for_expert_review")
            self.assertEqual(result["gates"]["scientific_acceptance"], "requires_expert_review")
            self.assertIn("not automatically accepted", result["maximum_allowed_conclusion"])
            self.assertNotIn(directory, json.dumps(result))

    def test_missing_claim_check_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = validate_claim_package.validate_package(self.make_package(Path(directory), omit_check=True))
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(result["checks"]["missing"])

    def test_tampered_cached_official_source_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory), tamper_source=True)
            with self.assertRaisesRegex(ValueError, "snapshot hashes"):
                validate_claim_package.validate_package(package)

    def test_selected_audit_must_be_in_convergence_series(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = self.make_package(root)
            package = json.loads(package_path.read_text(encoding="utf-8"))
            unrelated = root / "unrelated-audit.json"
            audit = json.loads((root / package["audit_json"]).read_text(encoding="utf-8"))
            audit["case_id"] = "cp2k-unrelated-safe-id"
            unrelated.write_text(json.dumps(audit), encoding="utf-8")
            package["audit_json"] = unrelated.name
            package_path.write_text(json.dumps(package), encoding="utf-8")
            result = validate_claim_package.validate_package(package_path)
            self.assertEqual(result["status"], "blocked")
            self.assertIn("selected run audit is not part of the convergence series", result["blockers"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
