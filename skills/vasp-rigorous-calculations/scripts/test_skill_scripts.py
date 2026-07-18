#!/usr/bin/env python3
"""Unit tests for the deterministic VASP skill scripts."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import analyze_convergence  # noqa: E402
import audit_vasp_case  # noqa: E402
import resolve_official_sources  # noqa: E402
import sync_official_wiki  # noqa: E402
import validate_claim_package  # noqa: E402


class ConvergenceTests(unittest.TestCase):
    def evidence_row(self, x: float, y: float, index: int) -> dict[str, object]:
        return {
            "x": x,
            "y": y,
            "run_id": f"run-{index}",
            "observable": "energy_per_atom",
            "unit": "eV/atom",
            "comparability_group": "protocol-a",
            "state_label": "nonmagnetic-state-a",
            "audit_sha256": f"{index:064x}",
            "task_type": "static",
        }

    def write_audit(self, path: Path, *, electronic: str = "pass") -> None:
        path.write_text(
            json.dumps(
                {
                    "audit_schema_version": "2.0",
                    "auditor": "audit_vasp_case.py",
                    "mode": "run",
                    "task_type": "static",
                    "case_id": "case-anonymous",
                    "verdict": "technical_run_gates_passed_scientific_claim_blocked",
                    "gates": {
                        "input_integrity": "pass",
                        "input_reproducibility": "pass",
                        "execution_completion": "pass",
                        "electronic_convergence": electronic,
                        "ionic_convergence": "not_applicable",
                        "output_warnings": "pass",
                        "version_identity": "pass",
                        "task_specific_validation": "not_evaluated",
                        "numerical_convergence": "not_evaluated_by_single_case",
                        "physical_validity": "not_evaluated_by_single_case",
                        "scientific_claim": "blocked",
                    },
                    "summary": {"errors": 0, "warnings": 0, "info": 1},
                    "files": {"INCAR": {"selected_values": {}}},
                }
            )
        )

    def write_series(self, root: Path, *, duplicate_x: bool = False, states: tuple[str, str, str] = ("state-a", "state-a", "state-a")) -> Path:
        path = root / "series.csv"
        fieldnames = [
            "run_id",
            "encut",
            "energy",
            "observable",
            "unit",
            "comparability_group",
            "state_label",
            "audit_json",
        ]
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for index, (x, y, state) in enumerate(zip((400, 400 if duplicate_x else 500, 600), (-9.0, -9.09, -9.1), states), 1):
                audit = root / f"audit-{index}.json"
                self.write_audit(audit)
                writer.writerow(
                    {
                        "run_id": f"run-{index}",
                        "encut": x,
                        "energy": y,
                        "observable": "energy_per_atom",
                        "unit": "eV/atom",
                        "comparability_group": "protocol-a",
                        "state_label": state,
                        "audit_json": audit.name,
                    }
                )
        return path

    def test_stable_tail(self) -> None:
        rows = [
            self.evidence_row(300.0, -9.0, 1),
            self.evidence_row(400.0, -9.08, 2),
            self.evidence_row(500.0, -9.0995, 3),
            self.evidence_row(600.0, -9.1000, 4),
            self.evidence_row(700.0, -9.1002, 5),
        ]
        result = analyze_convergence.analyze(rows, abs_tol=0.001, rel_tol=0.0, min_tail=3)
        self.assertEqual(result["status"], "candidate_found")
        self.assertEqual(result["candidate_x"], 500.0)
        self.assertEqual(result["gates"]["technical_run_evidence"], "pass")
        self.assertEqual(result["gates"]["physical_validity"], "not_assessed")

    def test_csv_duplicate_x_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_series(Path(directory), duplicate_x=True)
            with self.assertRaises(ValueError):
                analyze_convergence.load_series(path, "encut", "energy")

    def test_csv_requires_audit_evidence_columns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "series.csv"
            path.write_text("encut,energy\n400,-9.0\n500,-9.1\n600,-9.1\n")
            with self.assertRaisesRegex(ValueError, "missing required columns"):
                analyze_convergence.load_series(path, "encut", "energy")

    def test_blocked_run_audit_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_series(root)
            self.write_audit(root / "audit-2.json", electronic="fail")
            with self.assertRaisesRegex(ValueError, "blocked technical gates"):
                analyze_convergence.load_series(path, "encut", "energy")

    def test_state_change_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_series(Path(directory), states=("state-a", "state-b", "state-a"))
            with self.assertRaisesRegex(ValueError, "state_label differs"):
                analyze_convergence.load_series(path, "encut", "energy")

    def test_two_point_tail_is_rejected(self) -> None:
        rows = [self.evidence_row(400.0, -9.0, 1), self.evidence_row(500.0, -9.1, 2), self.evidence_row(600.0, -9.1, 3)]
        with self.assertRaisesRegex(ValueError, "at least 3"):
            analyze_convergence.analyze(rows, abs_tol=0.001, rel_tol=0.0, min_tail=2)


class AuditTests(unittest.TestCase):
    def make_case(self, root: Path, incar: str) -> Path:
        root.joinpath("INCAR").write_text(incar)
        root.joinpath("POSCAR").write_text(
            "Si\n1.0\n1 0 0\n0 1 0\n0 0 1\nSi\n2\nDirect\n0 0 0\n0.25 0.25 0.25\n"
        )
        root.joinpath("KPOINTS").write_text("mesh\n0\nGamma\n6 6 6\n0 0 0\n")
        root.joinpath("POTCAR").write_text(
            "TITEL = PAW_PBE Si 05Jan2001\nLEXCH = PE\nENMAX = 245.000; ENMIN = 180.000\nEnd of Dataset\n"
        )
        return root

    def test_consistent_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nEDIFF=1E-6\nISMEAR=0\nSIGMA=0.05\n")
            result = audit_vasp_case.audit(case)
            self.assertEqual(result["summary"]["errors"], 0)
            self.assertEqual(result["files"]["POTCAR"]["datasets"], 1)
            self.assertNotIn("POTCAR", json.dumps(result["files"]["POTCAR"]["titles"]))
            self.assertEqual(result["gates"]["input_integrity"], "pass")
            self.assertEqual(result["gates"]["scientific_claim"], "blocked")
            self.assertNotIn(str(case), json.dumps(result))
            self.assertNotIn("comment", result["files"]["POSCAR"])

    def test_fixed_charge_requires_chgcar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nICHARG=11\n")
            result = audit_vasp_case.audit(case)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("missing-chgcar", codes)

    def test_icharg_12_does_not_require_chgcar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nICHARG=12\n")
            result = audit_vasp_case.audit(case)
            codes = {item["code"] for item in result["findings"]}
            self.assertNotIn("missing-chgcar", codes)

    def test_species_order_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("POSCAR").write_text(
                "C\n1.0\n1 0 0\n0 1 0\n0 0 1\nC\n2\nDirect\n0 0 0\n0.25 0.25 0.25\n"
            )
            result = audit_vasp_case.audit(case)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("species-potcar-order-mismatch", codes)

    def test_truncated_potcar_boundary_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("POTCAR").write_text(
                "TITEL = PAW_PBE Si 05Jan2001\nLEXCH = PE\nENMAX = 245.000; ENMIN = 180.000\n"
            )
            result = audit_vasp_case.audit(case)
            self.assertIn("potcar-dataset-boundary-mismatch", {item["code"] for item in result["findings"]})

    def test_poscar_coordinate_count_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("POSCAR").write_text(
                "Si\n1.0\n1 0 0\n0 1 0\n0 0 1\nSi\n2\nDirect\n0 0 0\n"
            )
            result = audit_vasp_case.audit(case)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("input-parse-error", codes)
            self.assertEqual(result["gates"]["input_integrity"], "fail")

    def test_invalid_automatic_kmesh_is_audit_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("KPOINTS").write_text("mesh\n0\nGamma\nnot a mesh\n")
            result = audit_vasp_case.audit(case)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("kpoints-parse-error", codes)

    def test_nonpositive_automatic_kmesh_is_audit_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("KPOINTS").write_text("mesh\n0\nGamma\n6 0 6\n0 0 0\n")
            result = audit_vasp_case.audit(case)
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("kpoints-parse-error", codes)

    def test_official_fractional_line_mode_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("KPOINTS").write_text(
                "band path\n40\nline mode\nfractional\n0 0 0 Gamma\n0.5 0 0 X\n"
            )
            result = audit_vasp_case.audit(case)
            self.assertEqual(result["files"]["KPOINTS"]["mode"], "line")

    def test_official_generalized_automatic_mesh_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("KPOINTS").write_text(
                "generalized mesh\n0\nReciprocal\n0.25 0 0\n0 0.25 0\n0 0 0.25\n0 0 0\n"
            )
            result = audit_vasp_case.audit(case)
            self.assertEqual(result["files"]["KPOINTS"]["mode"], "generalized_automatic")

    def test_official_kpoints_inline_comments_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("KPOINTS").write_text(
                "regular mesh\n0 ! automatic count\nGamma ! centered\n6 6 6 ! subdivisions\n0 0 0 ! shift\n"
            )
            result = audit_vasp_case.audit(case)
            self.assertEqual(result["files"]["KPOINTS"]["mesh"], [6, 6, 6])

    def test_run_mode_requires_outcar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nEDIFF=1E-6\nISMEAR=0\nSIGMA=0.05\n")
            result = audit_vasp_case.audit(case, mode="run", task_type="static")
            self.assertEqual(result["gates"]["execution_completion"], "fail")
            self.assertEqual(result["verdict"], "blocked")

    def test_completed_run_passes_technical_gates_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nEDIFF=1E-6\nNELM=60\nISMEAR=0\nSIGMA=0.05\n")
            case.joinpath("OUTCAR").write_text(
                "vasp.6.4.3\n ENCUT = 400\n EDIFF = 1E-6\n NELM = 60\n NKPTS = 8\n"
                " Iteration 1( 1)\n Elapsed time (sec): 10.0\n"
            )
            result = audit_vasp_case.audit(case, mode="run", task_type="static")
            self.assertEqual(result["gates"]["execution_completion"], "pass")
            self.assertEqual(result["gates"]["electronic_convergence"], "pass")
            self.assertEqual(result["gates"]["physical_validity"], "not_evaluated_by_single_case")
            self.assertEqual(result["gates"]["scientific_claim"], "blocked")
            self.assertEqual(result["verdict"], "technical_run_gates_passed_scientific_claim_blocked")

    def test_nelm_exhaustion_blocks_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nEDIFF=1E-6\nNELM=2\nISMEAR=0\nSIGMA=0.05\n")
            case.joinpath("OUTCAR").write_text(
                "vasp.6.4.3\n ENCUT = 400\n NELM = 2\n Iteration 1( 2)\n Elapsed time (sec): 10.0\n"
            )
            result = audit_vasp_case.audit(case, mode="run", task_type="static")
            self.assertEqual(result["gates"]["electronic_convergence"], "fail")
            self.assertEqual(result["verdict"], "blocked")

    def test_stopcar_marker_blocks_completed_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nEDIFF=1E-6\nNELM=60\nISMEAR=0\nSIGMA=0.05\n")
            case.joinpath("OUTCAR").write_text(
                "vasp.6.4.3\n ENCUT = 400\n NELM = 60\n Iteration 1( 1)\n"
                "STOPCAR detected: soft stop\n Elapsed time (sec): 10.0\n"
            )
            result = audit_vasp_case.audit(case, mode="run", task_type="static")
            self.assertEqual(result["gates"]["execution_completion"], "fail")
            self.assertIn("outcar-stopped", {item["code"] for item in result["findings"]})

    def test_duplicate_incar_tag_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nENCUT=500\n")
            result = audit_vasp_case.audit(case)
            self.assertEqual(result["gates"]["input_integrity"], "fail")
            self.assertIn("duplicate-incar-tag", {item["code"] for item in result["findings"]})

    def test_nonfinite_or_expression_scalar_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=NaN\nEDIFF=1E-6 extra\n")
            result = audit_vasp_case.audit(case)
            self.assertIn("invalid-numeric-tag", {item["code"] for item in result["findings"]})

    def test_singular_lattice_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("POSCAR").write_text(
                "private-material\n1.0\n1 0 0\n2 0 0\n0 0 1\nSi\n2\nDirect\n0 0 0\n0.25 0.25 0.25\n"
            )
            result = audit_vasp_case.audit(case)
            self.assertIn("input-parse-error", {item["code"] for item in result["findings"]})

    def test_exact_duplicate_coordinates_are_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("POSCAR").write_text(
                "private-material\n1.0\n1 0 0\n0 1 0\n0 0 1\nSi\n2\nDirect\n0 0 0\n0 0 0\n"
            )
            result = audit_vasp_case.audit(case)
            self.assertIn("duplicate-poscar-coordinates", {item["code"] for item in result["findings"]})

    def test_dftu_vector_must_match_potcar_datasets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(
                Path(directory),
                "ENCUT=400\nLDAU=.TRUE.\nLDAUL=2 -1\nLDAUU=4.0 0\nLDAUJ=0 0\n",
            )
            result = audit_vasp_case.audit(case)
            self.assertIn("dftu-vector-length-mismatch", {item["code"] for item in result["findings"]})

    def test_relax_profile_requires_relaxation_setup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nNSW=0\nIBRION=-1\n")
            result = audit_vasp_case.audit(case, task_type="relax")
            self.assertIn("task-profile-mismatch", {item["code"] for item in result["findings"]})

    def test_warning_text_is_not_emitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nEDIFF=1E-6\nNELM=60\nISMEAR=0\nSIGMA=0.05\n")
            case.joinpath("OUTCAR").write_text(
                "vasp.6.4.3\n ENCUT = 400\n NELM = 60\n Iteration 1( 1)\n"
                "WARNING read /synthetic/hidden/path\n Elapsed time (sec): 10.0\n"
            )
            result = audit_vasp_case.audit(case, mode="run", task_type="static")
            warning = result["files"]["OUTCAR"]["warnings"][0]
            self.assertEqual(warning["category"], "unclassified-warning")
            self.assertTrue(warning["text_redacted"])
            self.assertNotIn("text", warning)
            self.assertNotIn("/synthetic/hidden", json.dumps(result))


class OfficialSourceTests(unittest.TestCase):
    def test_exact_tag_resolves_with_revision(self) -> None:
        result = resolve_official_sources.resolve(["ENCUT", "vasprun.xml"])
        self.assertEqual(result["status"], "pass")
        self.assertTrue(all(item["revision"] for item in result["resolved"]))

    def test_missing_local_page_blocks_official_claim(self) -> None:
        result = resolve_official_sources.resolve(["IMAGINARY_NOT_A_VASP_TAG"])
        self.assertEqual(result["status"], "blocked_local_official_source")
        self.assertEqual(result["missing"], ["IMAGINARY_NOT_A_VASP_TAG"])

    def test_hash_mismatch_blocks_official_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "skill"
            official = skill / "references" / "official-wiki"
            official.mkdir(parents=True)
            page = skill / "references" / "official-wiki" / "page.md"
            page.write_text("tampered\n")
            manifest = official / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "scope": "test",
                        "retrieved_utc": "2026-01-01T00:00:00+00:00",
                        "pages": [
                            {
                                "title": "ENCUT",
                                "url": "https://www.vasp.at/wiki/ENCUT",
                                "revid": 1,
                                "markdown_path": "references/official-wiki/page.md",
                                "markdown_sha256": "0" * 64,
                                "pageid": 1,
                            }
                        ],
                    }
                )
            )
            result = resolve_official_sources.resolve(["ENCUT"], manifest)
            self.assertEqual(result["status"], "blocked_local_official_source")
            self.assertEqual(result["corrupt"], ["ENCUT"])


class ClaimPackageTests(unittest.TestCase):
    def make_package(
        self,
        root: Path,
        *,
        task_type: str = "static",
        omit_check: bool = False,
        wrong_audit_hash: bool = False,
        selected_values: dict[str, str] | None = None,
    ) -> Path:
        selected_values = selected_values or {}
        audit_path = root / "private-audit-path.json"
        audit_path.write_text(
            json.dumps(
                {
                    "audit_schema_version": "2.0",
                    "auditor": "audit_vasp_case.py",
                    "mode": "run",
                    "task_type": task_type,
                    "case_id": "case-anonymous",
                    "verdict": "technical_run_gates_passed_scientific_claim_blocked",
                    "gates": {
                        "input_integrity": "pass",
                        "input_reproducibility": "pass",
                        "execution_completion": "pass",
                        "electronic_convergence": "pass",
                        "ionic_convergence": "not_applicable",
                        "output_warnings": "pass",
                        "version_identity": "pass",
                        "task_specific_validation": "not_evaluated",
                        "numerical_convergence": "not_evaluated_by_single_case",
                        "physical_validity": "not_evaluated_by_single_case",
                        "scientific_claim": "blocked",
                    },
                    "summary": {"errors": 0, "warnings": 0, "info": 1},
                    "files": {"INCAR": {"selected_values": selected_values}},
                }
            )
        )
        audit_hash = audit_vasp_case.sha256_file(audit_path)
        convergence_path = root / "private-convergence-path.json"
        convergence_path.write_text(
            json.dumps(
                {
                    "convergence_schema_version": "2.0",
                    "analyzer": "analyze_convergence.py",
                    "status": "candidate_found",
                    "task_type": task_type,
                    "observable": "energy_per_atom",
                    "unit": "eV/atom",
                    "criterion": {"absolute_tolerance": 0.001, "relative_tolerance": 0.0},
                    "gates": {
                        "technical_run_evidence": "pass",
                        "declared_comparability": "pass",
                        "declared_state_continuity": "pass",
                        "numerical_stable_tail": "pass",
                        "physical_validity": "not_assessed",
                    },
                    "series": [{"audit_sha256": "0" * 64 if wrong_audit_hash else audit_hash}],
                }
            )
        )
        _, required = validate_claim_package.required_checks(task_type)
        required |= validate_claim_package.conditional_checks(selected_values)
        evidence_path = root / "evidence-record.json"
        evidence_path.write_text('{"evidence": "synthetic"}\n')
        checks = [
            {"id": check_id, "status": "pass", "evidence_files": [evidence_path.name]}
            for check_id in sorted(required)
        ]
        if omit_check and checks:
            checks.pop()
        package_path = root / "claim-package.json"
        package_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "claim_id": "claim-anonymous",
                    "task_type": task_type,
                    "observable": "energy_per_atom",
                    "unit": "eV/atom",
                    "absolute_tolerance": 0.001,
                    "relative_tolerance": 0.0,
                    "audit_json": audit_path.name,
                    "convergence_json": convergence_path.name,
                    "checks": checks,
                }
            )
        )
        return package_path

    def test_complete_package_is_only_eligible_for_expert_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = validate_claim_package.validate_package(self.make_package(Path(directory)))
            self.assertEqual(result["status"], "eligible_for_expert_review")
            self.assertEqual(result["gates"]["scientific_acceptance"], "requires_expert_review")
            self.assertNotEqual(result["gates"]["physical_validity"], "pass")
            self.assertNotIn(directory, json.dumps(result))

    def test_missing_task_check_blocks_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = validate_claim_package.validate_package(self.make_package(Path(directory), omit_check=True))
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["gates"]["task_specific_evidence_package"], "blocked")

    def test_generic_task_cannot_support_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = validate_claim_package.validate_package(self.make_package(Path(directory), task_type="generic"))
            self.assertEqual(result["status"], "blocked")
            self.assertIn("generic task profile", result["blockers"][0])

    def test_selected_run_must_be_in_convergence_series(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = validate_claim_package.validate_package(
                self.make_package(Path(directory), wrong_audit_hash=True)
            )
            self.assertEqual(result["status"], "blocked")
            self.assertIn("selected run audit is not part", " ".join(result["blockers"]))

    def test_missing_evidence_file_blocks_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package_path = self.make_package(Path(directory))
            package = json.loads(package_path.read_text())
            package["checks"][0]["evidence_files"] = ["does-not-exist.json"]
            package_path.write_text(json.dumps(package))
            result = validate_claim_package.validate_package(package_path)
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(result["checks"]["malformed"])

    def test_method_flags_add_nonoptional_evidence_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = validate_claim_package.validate_package(
                self.make_package(
                    Path(directory),
                    selected_values={"ISPIN": "2", "MAGMOM": "2*1", "LDAU": ".TRUE."},
                )
            )
            self.assertEqual(result["status"], "eligible_for_expert_review")
            self.assertIn("magnetic-state-search-and-final-moments", result["checks"]["required"])
            self.assertIn("dftu-formulation-mapping-and-parameter-provenance", result["checks"]["required"])


class CliContractTests(unittest.TestCase):
    def make_case(self, root: Path) -> Path:
        root.joinpath("INCAR").write_text("ENCUT=400\nEDIFF=1E-6\nISMEAR=0\nSIGMA=0.05\n")
        root.joinpath("POSCAR").write_text(
            "private-comment\n1.0\n1 0 0\n0 1 0\n0 0 1\nSi\n1\nDirect\n0 0 0\n"
        )
        root.joinpath("KPOINTS").write_text("mesh\n0\nGamma\n6 6 6\n0 0 0\n")
        root.joinpath("POTCAR").write_text(
            "TITEL = PAW_PBE Si 05Jan2001\nLEXCH = PE\nENMAX = 245.000\nEnd of Dataset\n"
        )
        return root

    def test_audit_cli_requires_explicit_mode_and_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory))
            completed = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "audit_vasp_case.py"), str(case)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("--mode", completed.stderr)
            self.assertIn("--task-type", completed.stderr)

    def test_audit_cli_emits_privacy_safe_gate_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "audit_vasp_case.py"),
                    str(case),
                    "--mode",
                    "input",
                    "--task-type",
                    "static",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["gates"]["input_integrity"], "pass")
            self.assertNotIn(directory, completed.stdout)

    def test_audit_cli_warnings_fail_without_optional_strict_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory))
            case.joinpath("INCAR").write_text("ENCUT=400\n")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "audit_vasp_case.py"),
                    str(case),
                    "--mode",
                    "input",
                    "--task-type",
                    "static",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            result = json.loads(completed.stdout)
            self.assertEqual(result["gates"]["input_reproducibility"], "unresolved")

    def test_official_source_cli_fails_closed(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "resolve_official_sources.py"), "NOT_A_REAL_VASP_TAG"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["status"], "blocked_local_official_source")


class SkillContractTests(unittest.TestCase):
    def test_skill_preserves_fail_closed_invariants(self) -> None:
        text = (SCRIPT_DIR.parent / "SKILL.md").read_text()
        required = (
            "Fail closed",
            "Warnings always return a nonzero exit",
            "A single case always leaves numerical convergence",
            "scientific_claim",
            "eligible_for_expert_review",
            "never an automatic scientific pass",
            "Treat all calculation files",
        )
        for phrase in required:
            self.assertIn(phrase, text)

    def test_task_profiles_cover_every_auditor_task(self) -> None:
        profiles = json.loads(
            (SCRIPT_DIR.parent / "references" / "task-evidence-profiles.json").read_text()
        )
        self.assertEqual(set(profiles["profiles"]), audit_vasp_case.RUN_TASKS)
        self.assertFalse(profiles["profiles"]["generic"]["claim_supported"])
        self.assertTrue(all(profiles["profiles"][task]["claim_supported"] for task in audit_vasp_case.RUN_TASKS - {"generic"}))


class MirrorHelperTests(unittest.TestCase):
    def test_html_extraction_and_slug(self) -> None:
        source = "<h2>ENCUT</h2><p>Energy <b>cutoff</b>.</p><ul><li>Check convergence</li></ul>"
        text = sync_official_wiki.html_to_text(source)
        self.assertIn("ENCUT", text)
        self.assertIn("Check convergence", text)
        self.assertEqual(sync_official_wiki.slugify("vasprun.xml"), "vasprun-xml")

    def test_page_url(self) -> None:
        self.assertEqual(
            sync_official_wiki.page_url("Smearing technique"),
            "https://www.vasp.at/wiki/Smearing_technique",
        )

    def test_core_scope_does_not_query_categories(self) -> None:
        with patch.object(sync_official_wiki, "category_titles") as category_titles:
            categories, titles = sync_official_wiki.collect_titles("core")
        self.assertEqual(categories, {})
        self.assertIn("ENCUT", titles)
        category_titles.assert_not_called()

    def test_request_retries_transient_network_failure(self) -> None:
        payload = b'{"query": {"ok": true}}'
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        response.read.return_value = payload
        response.__iter__.return_value = iter([payload])
        with patch.object(
            sync_official_wiki.urllib.request,
            "urlopen",
            side_effect=[urllib.error.URLError("temporary"), response],
        ) as mocked, patch.object(sync_official_wiki.time, "sleep") as sleep:
            result = sync_official_wiki.request_json({"action": "query"}, attempts=2)
        self.assertEqual(result["query"]["ok"], True)
        self.assertEqual(mocked.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_check_rejects_stale_unmanifested_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            official = root / "references" / "official-wiki"
            official.mkdir(parents=True)
            official.joinpath("raw").mkdir()
            official.joinpath("manifest.json").write_text(
                json.dumps(
                    {
                        "official_root": sync_official_wiki.OFFICIAL_ROOT,
                        "page_count": 0,
                        "pages": [],
                    }
                )
            )
            root.joinpath("references", "official-wiki-index.md").write_text("# index\n")
            official.joinpath("page-999-stale.md").write_text("stale\n")
            self.assertEqual(sync_official_wiki.check(root), 1)

    def test_install_snapshot_replaces_old_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            stage = Path(directory) / "stage"
            old = root / "references" / "official-wiki"
            old.mkdir(parents=True)
            old.joinpath("page-999-stale.md").write_text("stale\n")
            staged = stage / "references" / "official-wiki"
            staged.mkdir(parents=True)
            staged.joinpath("manifest.json").write_text("{}\n")
            stage.joinpath("references", "official-wiki-index.md").write_text("# new index\n")
            sync_official_wiki.install_snapshot(root, stage)
            self.assertFalse(old.joinpath("page-999-stale.md").exists())
            self.assertEqual(old.joinpath("manifest.json").read_text(), "{}\n")
            self.assertEqual(root.joinpath("references", "official-wiki-index.md").read_text(), "# new index\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
