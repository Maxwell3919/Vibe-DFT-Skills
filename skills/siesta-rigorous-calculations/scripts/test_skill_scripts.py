#!/usr/bin/env python3
"""Offline contract, negative-path, and synthetic forward tests for SIESTA."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analyze_convergence import analyze, load_series, validate_plan_contract
from audit_siesta_case import audit, canonical, load_reference_contracts, pattern_matches, parse_output_text
from create_siesta_plan import build_plan, validate_plan
from resolve_official_sources import resolve, verified_fetch


def fdf_text(*, mesh: int = 250, atoms: int = 2, coordinate_rows: int = 2, kgrid: bool = True, pseudo_spec: str = "Si.psml", extra: str = "", relax: bool = False) -> str:
    coordinates = "\n".join(f"{index * 0.25:.2f} 0.0 0.0 1" for index in range(coordinate_rows))
    kgrid_block = """
%block kgrid.MonkhorstPack
  3 0 0 0.0
  0 3 0 0.0
  0 0 3 0.0
%endblock kgrid.MonkhorstPack
""" if kgrid else ""
    relax_text = """
MD.TypeOfRun CG
MD.MaxForceTol 0.04 eV/Ang
MD.Steps 40
MD.VariableCell false
GeometryMustConverge true
""" if relax else ""
    return f"""SystemName Synthetic silicon
SystemLabel synthetic-si
NumberOfAtoms {atoms}
NumberOfSpecies 1
LatticeConstant 1.0 Ang
%block LatticeVectors
  5.0 0.0 0.0
  0.0 5.0 0.0
  0.0 0.0 5.0
%endblock LatticeVectors
AtomicCoordinatesFormat Ang
%block ChemicalSpeciesLabel
  1 14 Si {pseudo_spec}
%endblock ChemicalSpeciesLabel
%block AtomicCoordinatesAndAtomicSpecies
{coordinates}
%endblock AtomicCoordinatesAndAtomicSpecies
XC.Functional GGA
XC.Authors PBE
Mesh.Cutoff {mesh} Ry
PAO.BasisSize DZP
PAO.EnergyShift 0.02 Ry
MaxSCFIterations 100
SCF.MustConverge true
SCF.DM.Tolerance 1e-5
SCF.H.Tolerance 1e-3 eV
Spin unpolarized
SolutionMethod diagon
OccupationFunction FD
ElectronicTemperature 300 K
{kgrid_block}{relax_text}{extra}"""


def output_text(input_text: str, *, energy: float = -10.0, version: str = "5.4.2", failure: str = "", warning: bool = False, relaxed: bool = False, force: float = 0.01, echo: bool = True, duplicate: bool = False) -> str:
    run = f"""Siesta Version  : {version}
>> Start of run: 18-JUL-2026 12:00:00
{('************************** Dump of input data file ****************************' + chr(10) + input_text + chr(10) + '************************** End of input data file *****************************') if echo else ''}
SCF cycle converged after 12 iterations
{failure}
{'WARNING: synthetic unresolved warning' if warning else ''}
siesta: Final energy (eV):
siesta:         Total = {energy:.8f}
siesta:         Fermi = -4.500000
siesta: Atomic forces (eV/Ang):
siesta:      1    {force:.8f}    0.000000    0.000000
siesta:      2   -{force:.8f}    0.000000    0.000000
siesta: ----------------------------------------
{('outcoor: Relaxed atomic coordinates (Ang):' + chr(10) + '0 0 0 1' + chr(10) + '1 0 0 1') if relaxed else ''}
timer: Elapsed wall time (sec) = 1.250
>> End of run: 18-JUL-2026 12:00:01
Job completed
"""
    return run + (run if duplicate else "")


def minimal_pbe_psml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<psml version="1.1">
  <exchange-correlation>
    <libxc-info number-of-functionals="2">
      <functional name="Perdew, Burke &amp; Ernzerhof (GGA)" type="exchange" id="101" />
      <functional name="Perdew, Burke &amp; Ernzerhof (GGA)" type="correlation" id="130" />
    </libxc-info>
  </exchange-correlation>
</psml>
"""


class CaseBuilder:
    def make_plan(self, root: Path, *, task: str = "scf", observable: str = "total_energy", abs_tol: float = 0.003, case_id: str = "case-siesta") -> Path:
        plan = build_plan(
            case_id=case_id,
            protocol_id="protocol-pbe-dzp",
            state_id="state-equilibrium",
            task_type=task,
            siesta_version="5.4.2",
            periodicity="bulk",
            workflow_stage="convergence",
            objective="Test a deterministic SIESTA evidence contract.",
            observable=observable,
            observable_unit="eV",
            normalization="per_cell",
            reference="most_converged_sample",
            absolute_tolerance=abs_tol,
            relative_tolerance=None,
            acceptance_criteria=["All declared technical gates pass."],
            features=[],
        )
        path = root / "scientific-plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def make_case(self, root: Path, text: str, *, pseudos: tuple[str, ...] = ("Si.psml",), manifest: bool = True, task: str = "scf", plan_path: Path | None = None) -> tuple[Path, Path]:
        input_path = root / "input.fdf"
        input_path.write_text(text, encoding="utf-8")
        for pseudo in pseudos:
            content = minimal_pbe_psml() if Path(pseudo).suffix.casefold() == ".psml" else "SYNTHETIC TEST PSEUDOPOTENTIAL CONTENT\n"
            (root / pseudo).write_text(content, encoding="utf-8")
        if manifest and pseudos:
            selected = root / pseudos[0]
            expected = hashlib.sha256(selected.read_bytes()).hexdigest()
            (root / "pseudopotential-manifest.json").write_text(json.dumps({
                "schema_version": "2.0",
                "pseudopotentials": [{
                    "species_index": 1,
                    "format": selected.suffix.lstrip("."),
                    "expected_sha256": expected,
                    "source": "https://example.invalid/synthetic-siesta-pseudo",
                    "xc_family": "GGA-PBE",
                    "relativistic_treatment": "scalar-relativistic",
                    "valence_configuration": "3s2-3p2",
                    "source_version": "synthetic-release-1",
                    "validation_id": "synthetic-test-only",
                }],
            }), encoding="utf-8")
        return input_path, plan_path or self.make_plan(root, task=task)

    def run_audit(self, input_path: Path, plan_path: Path, *, task: str = "scf", mode: str = "input", output_path: Path | None = None, parent: Path | None = None):
        return audit(input_path, mode, task, "bulk", output_path, plan_path, "5.4.2", None, parent)


class PlanAndReferenceTests(unittest.TestCase, CaseBuilder):
    def test_plan_builds_and_self_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan = json.loads(self.make_plan(Path(temporary)).read_text())
            self.assertEqual(validate_plan(plan), [])
            self.assertEqual(plan["documentation_line"], "5.4")

    def test_tampered_plan_version_blocks_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan = json.loads(self.make_plan(Path(temporary)).read_text())
            plan["siesta_version"] = "5.2.2"
            self.assertIn("PLAN_DOCUMENTATION_LINE_INVALID", {item["code"] for item in validate_plan(plan)})

    def test_pinned_index_and_profiles_are_internally_consistent(self) -> None:
        index, supplements, profiles = load_reference_contracts()
        self.assertEqual(index["entry_count"], 572)
        official = [item["label"] for item in index["entries"]] + [item["label"] for item in supplements["records"] if item.get("kind") == "fdf-source-definition"]
        labels = set(profiles["common"]["automated_labels"])
        for profile in profiles["profiles"].values():
            labels.update(profile["extra_automated_labels"])
            labels.update(profile["required_input_all"])
            for group in profile["required_input_any"]:
                labels.update(group)
        self.assertEqual([label for label in sorted(labels) if not any(pattern_matches(canonical(label), candidate) or pattern_matches(label, candidate) for candidate in official)], [])

    def test_official_artifact_manifest_is_explicitly_grammar_only(self) -> None:
        path = Path(__file__).resolve().parents[1] / "references" / "official-artifact-fixtures.json"
        manifest = json.loads(path.read_text())
        self.assertEqual(manifest["validation_scope"], "official-reference-output-parser-grammar-only")
        self.assertNotEqual(manifest["artifact_runtime_version"], manifest["source_tag"])
        self.assertEqual(len(manifest["artifacts"]), 4)


class SiestaAuditTests(unittest.TestCase, CaseBuilder):
    def test_valid_bulk_input_passes_technical_input_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_path, plan = self.make_case(Path(temporary), fdf_text())
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 0)
            self.assertEqual(report["decision"], "pass")
            self.assertEqual(report["gates"]["scientific_acceptance"], "blocked")
            self.assertEqual(report["evidence"]["convergence_parameters"]["mesh_cutoff"]["value"], 250.0)

    def test_valid_run_binds_input_echo_output_and_observable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            text = fdf_text()
            input_path, plan = self.make_case(root, text)
            output = root / "run.out"
            output.write_text(output_text(text, energy=-10.25), encoding="utf-8")
            report, status = self.run_audit(input_path, plan, mode="run", output_path=output)
            self.assertEqual(status, 0)
            self.assertEqual(report["evidence"]["input_echo"]["status"], "exact_normalized_match")
            self.assertEqual(report["evidence"]["observables"]["total_energy"]["value"], -10.25)
            self.assertEqual(report["maximum_conclusion"], "technical_run_gates_passed_scientific_claim_blocked")

    def test_runtime_version_header_from_siesta_5_4_2_is_recognized(self) -> None:
        parsed = parse_output_text("Version         : 5.4.2\n")
        self.assertEqual(parsed["versions"], ["5.4.2"])

    def test_psml_embedded_xc_disagreement_blocks_false_manifest_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path, plan = self.make_case(root, fdf_text())
            manifest_path = root / "pseudopotential-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["pseudopotentials"][0]["xc_family"] = "LDA-PW92"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("PSEUDO_PSML_XC_MISMATCH", {item["code"] for item in report["findings"]})

    def test_atom_count_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_path, plan = self.make_case(Path(temporary), fdf_text(atoms=2, coordinate_rows=1))
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("ATOM_COUNT_MISMATCH", {item["code"] for item in report["findings"]})

    def test_bulk_requires_explicit_kgrid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_path, plan = self.make_case(Path(temporary), fdf_text(kgrid=False))
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("KGRID_MISSING", {item["code"] for item in report["findings"]})

    def test_external_include_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_path, plan = self.make_case(Path(temporary), fdf_text(extra="%include external.fdf\n"))
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("FDF_EXTERNAL_INPUT_UNSUPPORTED", {item["code"] for item in report["findings"]})

    def test_official_but_unautomated_label_blocks_semantic_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_path, plan = self.make_case(Path(temporary), fdf_text(extra="OpticalCalculation true\n"))
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("FDF_LABEL_NOT_AUTOMATED", {item["code"] for item in report["findings"]})

    def test_unknown_label_blocks_official_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_path, plan = self.make_case(Path(temporary), fdf_text(extra="ImaginaryPrivateControl 1\n"))
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("FDF_LABEL_NOT_IN_PINNED_INDEX", {item["code"] for item in report["findings"]})

    def test_implicit_pseudopotential_precedence_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_path, plan = self.make_case(Path(temporary), fdf_text(pseudo_spec="Si"), pseudos=("Si.psf", "Si.psml"))
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("PSEUDO_PRECEDENCE_AMBIGUOUS", {item["code"] for item in report["findings"]})

    def test_pseudopotential_manifest_schema_one_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path, plan = self.make_case(root, fdf_text())
            manifest = json.loads((root / "pseudopotential-manifest.json").read_text())
            manifest["schema_version"] = "1.0"
            (root / "pseudopotential-manifest.json").write_text(json.dumps(manifest))
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("PSEUDO_MANIFEST_SCHEMA_INVALID", {item["code"] for item in report["findings"]})

    def test_pseudopotential_hash_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path, plan = self.make_case(root, fdf_text())
            manifest = json.loads((root / "pseudopotential-manifest.json").read_text())
            manifest["pseudopotentials"][0]["expected_sha256"] = "0" * 64
            (root / "pseudopotential-manifest.json").write_text(json.dumps(manifest))
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("PSEUDO_MANIFEST_IDENTITY_MISMATCH", {item["code"] for item in report["findings"]})

    def test_soc_feature_requires_fully_relativistic_pseudo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path, plan_path = self.make_case(root, fdf_text())
            plan = json.loads(plan_path.read_text())
            plan["declared_features"] = ["soc"]
            plan_path.write_text(json.dumps(plan))
            report, status = self.run_audit(input_path, plan_path)
            self.assertEqual(status, 2)
            self.assertIn("PSEUDO_SOC_INCOMPATIBLE", {item["code"] for item in report["findings"]})

    def test_output_version_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); text = fdf_text()
            input_path, plan = self.make_case(root, text)
            output = root / "run.out"; output.write_text(output_text(text, version="5.2.2"))
            report, status = self.run_audit(input_path, plan, mode="run", output_path=output)
            self.assertEqual(status, 2)
            self.assertIn("OUTPUT_VERSION_MISMATCH", {item["code"] for item in report["findings"]})

    def test_missing_input_echo_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); text = fdf_text()
            input_path, plan = self.make_case(root, text)
            output = root / "run.out"; output.write_text(output_text(text, echo=False))
            report, status = self.run_audit(input_path, plan, mode="run", output_path=output)
            self.assertEqual(status, 2)
            self.assertIn("INPUT_ECHO_MISMATCH", {item["code"] for item in report["findings"]})

    def test_concatenated_output_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); text = fdf_text()
            input_path, plan = self.make_case(root, text)
            output = root / "run.out"; output.write_text(output_text(text, duplicate=True))
            report, status = self.run_audit(input_path, plan, mode="run", output_path=output)
            self.assertEqual(status, 2)
            self.assertIn("RUN_BOUNDARY_MARKERS_INVALID", {item["code"] for item in report["findings"]})

    def test_scf_failure_marker_overrides_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); text = fdf_text()
            input_path, plan = self.make_case(root, text)
            output = root / "run.out"; output.write_text(output_text(text, failure="SCF_NOT_CONV: failed"))
            report, status = self.run_audit(input_path, plan, mode="run", output_path=output)
            self.assertEqual(status, 2)
            self.assertIn("SCF_NOT_CONV", {item["code"] for item in report["findings"]})

    def test_warning_marker_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); text = fdf_text()
            input_path, plan = self.make_case(root, text)
            output = root / "run.out"; output.write_text(output_text(text, warning=True))
            report, status = self.run_audit(input_path, plan, mode="run", output_path=output)
            self.assertEqual(status, 2)
            self.assertIn("WARNING_MARKER", {item["code"] for item in report["findings"]})

    def test_fixed_cell_relaxation_passes_force_and_marker_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); text = fdf_text(relax=True)
            input_path, plan = self.make_case(root, text, task="relax")
            output = root / "run.out"; output.write_text(output_text(text, relaxed=True, force=0.01))
            report, status = self.run_audit(input_path, plan, task="relax", mode="run", output_path=output)
            self.assertEqual(status, 0)
            self.assertEqual(report["gates"]["task_specific_validity"], "pass")

    def test_relaxation_force_above_tolerance_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); text = fdf_text(relax=True)
            input_path, plan = self.make_case(root, text, task="relax")
            output = root / "run.out"; output.write_text(output_text(text, relaxed=True, force=0.05))
            report, status = self.run_audit(input_path, plan, task="relax", mode="run", output_path=output)
            self.assertEqual(status, 2)
            self.assertIn("RELAX_FORCE_TOLERANCE_FAILED", {item["code"] for item in report["findings"]})

    def test_variable_cell_relaxation_is_explicitly_unassessed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            text = fdf_text(relax=True).replace("MD.VariableCell false", "MD.VariableCell true")
            input_path, plan = self.make_case(Path(temporary), text, task="relax")
            report, status = self.run_audit(input_path, plan, task="relax")
            self.assertEqual(status, 2)
            self.assertIn("VARIABLE_CELL_RELAX_NOT_AUTOMATED", {item["code"] for item in report["findings"]})

    def test_advanced_task_blocks_and_requires_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.make_plan(root, task="bands")
            input_path, _ = self.make_case(root, fdf_text(extra="%block BandLines\n1 0.0 0.0 0.0 G\n%endblock BandLines\n"), task="bands", plan_path=plan)
            report, status = self.run_audit(input_path, plan, task="bands")
            self.assertEqual(status, 2)
            codes = {item["code"] for item in report["findings"]}
            self.assertIn("TASK_INPUT_NOT_AUTOMATED", codes)
            self.assertIn("PARENT_MANIFEST_MISSING", codes)

    def test_downstream_parent_requires_external_decision_bundle_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = self.make_plan(root, task="bands")
            input_path, _ = self.make_case(
                root,
                fdf_text(
                    extra=(
                        "%block BandLines\n"
                        "1 0.0 0.0 0.0 G\n"
                        "%endblock BandLines\n"
                    )
                ),
                task="bands",
                plan_path=plan,
            )
            parent = root / "parent.json"
            parent.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "record_id": "run-parent-density",
                        "code": "siesta",
                        "code_version": "5.4.2",
                        "task_type": "scf",
                        "case_id": "case-siesta",
                        "scientific_protocol_id": "protocol-pbe-dzp",
                        "status": "completed",
                        "scientific_acceptance": "requires_human_review",
                        "configuration": {},
                        "metrics": {},
                        "evidence": [
                            {
                                "role": "density_matrix",
                                "label": "saved-density",
                                "status": "present",
                                "sha256": "a" * 64,
                            }
                        ],
                        "limitations": [
                            "Scientific acceptance is a downstream decision."
                        ],
                        "provenance": {
                            "collector": "create_run_manifest.py",
                            "collector_version": "1.2.0",
                            "generated_utc": "2026-07-18T00:00:00+00:00",
                        },
                    }
                ),
                encoding="utf-8",
            )
            report, status = self.run_audit(
                input_path,
                plan,
                task="bands",
                parent=parent,
            )
            self.assertEqual(status, 2)
            codes = {item["code"] for item in report["findings"]}
            self.assertIn("PARENT_SCIENTIFIC_DECISION_BUNDLE_REQUIRED", codes)
            self.assertNotIn("PARENT_NOT_SCIENTIFICALLY_ACCEPTED", codes)

    def test_restart_requires_hashed_parent_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_path, plan = self.make_case(Path(temporary), fdf_text(extra="UseSaveData true\n"))
            report, status = self.run_audit(input_path, plan)
            self.assertEqual(status, 2)
            self.assertIn("PARENT_MANIFEST_MISSING", {item["code"] for item in report["findings"]})

    def test_restart_with_hash_bound_parent_checkpoint_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path, plan = self.make_case(root, fdf_text(extra="UseSaveData true\n"))
            parent = root / "parent.json"
            parent.write_text(json.dumps({
                "schema_version": "1.0",
                "record_id": "run-parent-checkpoint",
                "code": "siesta",
                "code_version": "5.4.2",
                "task_type": "scf",
                "case_id": "case-siesta",
                "scientific_protocol_id": "protocol-pbe-dzp",
                "status": "completed",
                "scientific_acceptance": "not_assessed",
                "configuration": {},
                "metrics": {},
                "evidence": [{"role": "restart_checkpoint", "label": "saved-data", "status": "present", "sha256": "a" * 64}],
                "limitations": ["Synthetic test manifest."],
                "provenance": {"collector": "create_run_manifest.py", "collector_version": "1.0.0", "generated_utc": "2026-07-18T00:00:00+00:00"},
            }), encoding="utf-8")
            report, status = self.run_audit(input_path, plan, parent=parent)
            self.assertEqual(status, 0)
            self.assertEqual(report["gates"]["parent_ancestry"], "pass")

    def test_restart_rejects_failed_parent_even_with_checkpoint_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path, plan = self.make_case(root, fdf_text(extra="UseSaveData true\n"))
            parent = root / "parent.json"
            parent.write_text(json.dumps({
                "schema_version": "1.0", "record_id": "run-failed-parent", "code": "siesta", "code_version": "5.4.2",
                "task_type": "scf", "case_id": "case-siesta", "scientific_protocol_id": "protocol-pbe-dzp",
                "status": "failed", "scientific_acceptance": "not_assessed", "configuration": {}, "metrics": {},
                "evidence": [{"role": "restart_checkpoint", "label": "partial-checkpoint", "status": "present", "sha256": "a" * 64}],
                "limitations": ["Synthetic failed parent."],
                "provenance": {"collector": "create_run_manifest.py", "collector_version": "1.0.0", "generated_utc": "2026-07-18T00:00:00+00:00"},
            }), encoding="utf-8")
            report, status = self.run_audit(input_path, plan, parent=parent)
            self.assertEqual(status, 2)
            self.assertIn("RESTART_PARENT_NOT_COMPLETED", {item["code"] for item in report["findings"]})

    def test_report_exposes_no_paths_or_pseudopotential_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path, plan = self.make_case(root, fdf_text())
            report, _ = self.run_audit(input_path, plan)
            rendered = json.dumps(report)
            self.assertNotIn(str(root), rendered)
            self.assertNotIn("SYNTHETIC TEST PSEUDOPOTENTIAL CONTENT", rendered)
            self.assertNotIn("https://example.invalid/synthetic-siesta-pseudo", rendered)


class OutputParserTests(unittest.TestCase):
    def test_parser_extracts_final_energy_force_wall_and_boundaries(self) -> None:
        text = fdf_text()
        result = parse_output_text(output_text(text, energy=-3.125, force=0.02))
        self.assertEqual(result["versions"], ["5.4.2"])
        self.assertEqual(result["observables"]["total_energy"]["value"], -3.125)
        self.assertEqual(result["observables"]["max_force"]["value"], 0.02)
        self.assertEqual(result["observables"]["wall_time"]["value"], 1.25)

    def test_job_completed_does_not_remove_failure_marker(self) -> None:
        result = parse_output_text(output_text(fdf_text(), failure="SCF_NOT_CONV"))
        self.assertEqual(result["completion_markers"], 1)
        self.assertIn("SCF_NOT_CONV", result["fatal_markers"])


class OfficialResolverTests(unittest.TestCase):
    def test_parameter_and_topic_resolve_offline_as_cached_only(self) -> None:
        report, status = resolve(["Mesh.Cutoff", "fdf"])
        self.assertEqual(status, 3)
        self.assertEqual(report["decision"], "cached_only")
        self.assertEqual([item["kind"] for item in report["matches"]], ["parameter", "topic"])

    def test_wildcard_parameter_family_resolves(self) -> None:
        report, status = resolve(["DOS.kgrid.MonkhorstPack"])
        self.assertEqual(status, 3)
        self.assertEqual(report["matches"][0]["label"], "DOS.kgrid.?")

    def test_ambiguous_parameter_blocks(self) -> None:
        report, status = resolve(["MM.Cutoff"])
        self.assertEqual(status, 2)
        self.assertEqual(report["ambiguous_or_unresolved_terms"], ["MM.Cutoff"])

    def test_unknown_term_blocks(self) -> None:
        report, status = resolve(["not-a-siesta-topic"])
        self.assertEqual(status, 2)
        self.assertEqual(report["decision"], "block")

    def test_live_fetch_hashes_with_verified_tls_context(self) -> None:
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b"official synthetic body"
            def geturl(self): return "https://gitlab.com/siesta-project/siesta/-/raw/commit/file"
        expected = hashlib.sha256(b"official synthetic body").hexdigest()
        with patch("resolve_official_sources.urlopen", return_value=Response()) as mocked:
            result = verified_fetch("https://gitlab.com/test", expected)
        self.assertEqual(result["status"], "verified")
        self.assertIsNotNone(mocked.call_args.kwargs.get("context"))


class ConvergenceTests(unittest.TestCase, CaseBuilder):
    def make_series(self, root: Path) -> tuple[Path, Path]:
        plan_path = self.make_plan(root, abs_tol=0.003)
        rows = []
        for index, (mesh, energy) in enumerate(((150, -10.020), (200, -10.002), (250, -10.001), (300, -10.0005)), start=1):
            case = root / f"case-{index}"; case.mkdir()
            text = fdf_text(mesh=mesh)
            input_path, _ = self.make_case(case, text, plan_path=plan_path)
            output = case / "run.out"; output.write_text(output_text(text, energy=energy), encoding="utf-8")
            report, status = self.run_audit(input_path, plan_path, mode="run", output_path=output)
            self.assertEqual(status, 0)
            audit_path = case / "audit.json"; audit_path.write_text(json.dumps(report), encoding="utf-8")
            rows.append(f"{mesh},{energy},protocol-pbe-dzp,{case.name}/audit.json,{case.name}/input.fdf,{case.name}/run.out")
        csv_path = root / "series.csv"
        csv_path.write_text(",".join(["setting", "observable", "protocol_id", "audit_report", "input_file", "output_file"]) + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
        return csv_path, plan_path

    def test_evidence_bound_stable_tail_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            csv_path, plan = self.make_series(Path(temporary))
            plan_data = json.loads(plan.read_text())
            validate_plan_contract(plan_data, "protocol-pbe-dzp", "total_energy", "eV", 0.003, None)
            points = load_series(csv_path, plan, "protocol-pbe-dzp", "mesh_cutoff", "Ry", "total_energy", "eV")
            result = analyze(points, parameter="mesh_cutoff", parameter_unit="Ry", observable="total_energy", observable_unit="eV", protocol_id="protocol-pbe-dzp", absolute_tolerance=0.003, relative_tolerance=None, min_tail=3, direction="increasing")
            self.assertEqual(result["status"], "candidate_found")
            self.assertEqual(result["candidate_setting"], 200.0)
            self.assertEqual(result["gates"]["scientific_acceptance"], "blocked")

    def test_csv_observable_cannot_override_audited_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            csv_path, plan = self.make_series(Path(temporary))
            csv_path.write_text(csv_path.read_text().replace("150,-10.02", "150,-9.0"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "observable/unit differs"):
                load_series(csv_path, plan, "protocol-pbe-dzp", "mesh_cutoff", "Ry", "total_energy", "eV")

    def test_mutated_input_after_audit_blocks_series(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); csv_path, plan = self.make_series(root)
            path = root / "case-1" / "input.fdf"
            path.write_text(path.read_text().replace("Mesh.Cutoff 150", "Mesh.Cutoff 151"))
            with self.assertRaisesRegex(ValueError, "input hash differs"):
                load_series(csv_path, plan, "protocol-pbe-dzp", "mesh_cutoff", "Ry", "total_energy", "eV")

    def test_plan_tolerance_mismatch_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            plan_path = self.make_plan(Path(temporary), abs_tol=0.003)
            with self.assertRaisesRegex(ValueError, "absolute_tolerance"):
                validate_plan_contract(json.loads(plan_path.read_text()), "protocol-pbe-dzp", "total_energy", "eV", 0.004, None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
