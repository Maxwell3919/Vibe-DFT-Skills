from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
POST_SCRIPTS = ROOT / "skills" / "dft-postprocess" / "scripts"
sys.path.insert(0, str(POST_SCRIPTS))

from dftpost.capabilities import detect_capabilities  # noqa: E402
from dftpost.inventory import build_inventory  # noqa: E402
from dftpost.manifests import build_artifact_manifest, validation_errors  # noqa: E402
from dftpost.parsers import extract_summary  # noqa: E402
from dftpost.plotting import plot_table  # noqa: E402


class PostprocessTests(unittest.TestCase):
    def test_observable_registry_is_machine_validated(self) -> None:
        from dftpost.registry import load_registry, validate_registry

        registry = load_registry()
        self.assertEqual(validate_registry(registry), [])
        self.assertEqual(
            set(registry["observables"]),
            {"run-trace", "bands", "dos-pdos", "phonon", "epc", "real-space", "neb", "optical"},
        )
        self.assertEqual(registry["observables"]["run-trace"]["codes"]["qe"]["maturity"], "real-artifact-validated")
        self.assertEqual(registry["observables"]["bands"]["codes"]["vasp"]["maturity"], "real-artifact-validated")
        self.assertEqual(registry["observables"]["run-trace"]["codes"]["cp2k"]["maturity"], "design-only")
        self.assertEqual(registry["observables"]["run-trace"]["codes"]["siesta"]["maturity"], "design-only")

    def test_registry_rejects_unknown_maturity_and_special_case_content(self) -> None:
        from copy import deepcopy
        from dftpost.registry import load_registry, validate_registry

        invalid = deepcopy(load_registry())
        invalid["observables"]["bands"]["codes"]["qe"]["maturity"] = "looks-good"
        invalid["observables"]["bands"]["scope"] = "Use /home/example/project for one material"
        failures = validate_registry(invalid)
        self.assertTrue(any("unknown maturity" in item for item in failures))
        self.assertTrue(any("non-general content" in item for item in failures))

    def test_planner_blocks_design_only_and_builds_supported_route(self) -> None:
        from dftpost.planning import build_postprocess_plan

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            output = root / "derived"
            source.mkdir()
            source.joinpath("main.out").write_text("Program PWSCF v.7.5\nJOB DONE.\n")
            capabilities = detect_capabilities()

            supported = build_postprocess_plan(
                "plan-run-001", "run-trace", "qe", source, output,
                {"main-output": "main.out"}, capabilities,
            )
            self.assertEqual(supported["status"], "planned")
            self.assertEqual(supported["backend"]["id"], "python.qe-text")
            self.assertEqual(validation_errors("plan", supported), [])

            for code in ("cp2k", "siesta"):
                blocked_new_code = build_postprocess_plan(
                    f"plan-{code}-run-001", "run-trace", code, source, output,
                    {"main-output": "main.out"}, capabilities,
                )
                self.assertEqual(blocked_new_code["status"], "blocked")
                self.assertIn(f"workflow maturity is design-only: run-trace/{code}", blocked_new_code["blockers"])
                self.assertIn(f"no implemented available backend: run-trace/{code}", blocked_new_code["blockers"])
                self.assertEqual(validation_errors("plan", blocked_new_code), [])

            electronic = build_postprocess_plan(
                "plan-band-001", "bands", "qe", source, output,
                {"eigenvalues": "main.out", "energy-reference": "main.out"}, capabilities,
            )
            self.assertEqual(electronic["status"], "planned")
            self.assertEqual(electronic["backend"]["id"], "python.qe-bands")
            self.assertIn("qe-bands", electronic["steps"][0]["command"])

            blocked_phonon = build_postprocess_plan(
                "plan-phonon-blocked-001", "phonon", "qe", source, output,
                {"phonon-frequencies": "main.out"}, capabilities,
            )
            self.assertEqual(blocked_phonon["status"], "blocked")
            self.assertIn("missing required parameter: frequency-unit", blocked_phonon["blockers"])
            phonon = build_postprocess_plan(
                "plan-phonon-001", "phonon", "qe", source, output,
                {"phonon-frequencies": "main.out"}, capabilities,
                {"frequency-unit": "cm-1"},
            )
            self.assertEqual(phonon["status"], "planned")
            self.assertIn("cm-1", phonon["steps"][0]["command"])

            vasp_electronic = build_postprocess_plan(
                "plan-vasp-band-001", "bands", "vasp", source, output,
                {
                    "eigenvalues": "main.out",
                    "k-path": "main.out",
                    "structure": "main.out",
                    "energy-reference": "main.out",
                },
                capabilities,
            )
            self.assertEqual(vasp_electronic["status"], "planned")
            self.assertEqual(vasp_electronic["backend"]["id"], "python.vasp-bands")
            self.assertIn("vasp-bands", vasp_electronic["steps"][0]["command"])

            incomplete_optical = build_postprocess_plan(
                "plan-optical-001", "optical", "qe", source, output,
                {"dielectric-data": "main.out"}, capabilities,
            )
            self.assertEqual(incomplete_optical["status"], "blocked")
            self.assertTrue(any("missing required parameter" in item for item in incomplete_optical["blockers"]))
            optical = build_postprocess_plan(
                "plan-optical-002", "optical", "qe", source, output,
                {"dielectric-data": "main.out"}, capabilities,
                {"energy-column": "energy", "components": "xx=xx_re,xx_im", "broadening": "explicit-test"},
            )
            self.assertEqual(optical["status"], "planned")
            self.assertIn("optical-table", optical["steps"][0]["command"])

    def test_tool_runner_dry_run_and_success_records(self) -> None:
        from dftpost.runner import run_external_command

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / "work"
            records = root / "records"
            work.mkdir()
            source = root / "source.dat"
            source.write_text("source\n")
            command = [
                sys.executable,
                "-c",
                "from pathlib import Path; Path('result.dat').write_text('result\\n'); print('tool stdout')",
            ]

            dry = run_external_command(
                execution_id="exec-dry-001",
                plan_id="plan-run-001",
                step_id="extract-01",
                backend="test.python",
                command=command,
                working_directory=work,
                record_directory=records,
                input_files={"source": source},
                expected_outputs={"result": Path("result.dat")},
                timeout_s=10,
                dry_run=True,
            )
            self.assertEqual(dry["status"], "dry-run")
            self.assertFalse(work.joinpath("result.dat").exists())
            self.assertEqual(validation_errors("execution", dry), [])
            self.assertEqual(dry["working_directory_label"], "working-directory")
            self.assertEqual(dry["command"][0], Path(sys.executable).name)
            self.assertEqual(dry["inputs"][0]["path"], "source.dat")

            completed = run_external_command(
                execution_id="exec-run-001",
                plan_id="plan-run-001",
                step_id="extract-01",
                backend="test.python",
                command=command,
                working_directory=work,
                record_directory=records,
                input_files={"source": source},
                expected_outputs={"result": Path("result.dat")},
                timeout_s=10,
            )
            self.assertEqual(completed["status"], "succeeded")
            self.assertEqual(completed["return_code"], 0)
            self.assertEqual(validation_errors("execution", completed), [])
            self.assertEqual(completed["outputs"][0]["path"], "result.dat")
            self.assertEqual(completed["stdout"]["path"], "exec-run-001.stdout")
            self.assertIn("tool stdout", records.joinpath(completed["stdout"]["path"]).read_text())

            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                run_external_command(
                    execution_id="exec-run-002",
                    plan_id="plan-run-001",
                    step_id="extract-01",
                    backend="test.python",
                    command=command,
                    working_directory=work,
                    record_directory=records,
                    input_files={"source": source},
                    expected_outputs={"result": Path("result.dat")},
                    timeout_s=10,
                )

    def test_external_fixture_root_must_be_outside_repository(self) -> None:
        from dftpost.fixtures import external_fixture_root

        with tempfile.TemporaryDirectory() as directory:
            root = external_fixture_root({"DFTPOST_FIXTURE_ROOT": directory}, ROOT)
            self.assertEqual(root, Path(directory).resolve())
        with self.assertRaisesRegex(ValueError, "outside the source repository"):
            external_fixture_root({"DFTPOST_FIXTURE_ROOT": str(ROOT / "tests")}, ROOT)

    def test_skill_requires_general_only_and_visible_validation_evidence(self) -> None:
        skill_root = ROOT / "skills" / "dft-postprocess"
        skill = skill_root.joinpath("SKILL.md").read_text(encoding="utf-8")
        policy = skill_root.joinpath("references", "validation-data-policy.md").read_text(encoding="utf-8")
        self.assertIn("## Keep implementations general", skill)
        self.assertIn("Do not encode a material name", skill)
        self.assertIn("Display every completed validation figure directly to the user", skill)
        self.assertIn("Do not call a real-data validation complete", skill)
        self.assertIn("Keep bundled code independent of material names", policy)
        self.assertIn("source table containing the runtime host/path", policy)
        self.assertIn("every generated figure embedded from an absolute local path", policy)

    def test_cli_capabilities_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capabilities.json"
            result = subprocess.run(
                [sys.executable, str(POST_SCRIPTS / "dftpost_cli.py"), "capabilities", "--out", str(output)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("external_tools", json.loads(output.read_text()))

    def test_cli_registry_and_plan_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            source.joinpath("main.out").write_text("Program PWSCF v.7.5\nJOB DONE.\n")
            registry_out = root / "registry.json"
            registry_result = subprocess.run(
                [sys.executable, str(POST_SCRIPTS / "dftpost_cli.py"), "registry", "--out", str(registry_out)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(registry_result.returncode, 0, registry_result.stderr)
            self.assertIn("bands", json.loads(registry_out.read_text())["observables"])

            plan_out = root / "plan.json"
            plan_result = subprocess.run(
                [
                    sys.executable,
                    str(POST_SCRIPTS / "dftpost_cli.py"),
                    "plan",
                    "--plan-id", "plan-cli-001",
                    "--observable", "run-trace",
                    "--code", "qe",
                    "--source-root", str(source),
                    "--output-root", str(root / "derived"),
                    "--evidence", "main-output=main.out",
                    "--out", str(plan_out),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(plan_result.returncode, 0, plan_result.stderr)
            self.assertEqual(json.loads(plan_out.read_text())["status"], "planned")

    def test_capability_shape(self) -> None:
        result = detect_capabilities()
        self.assertIn("qe.bands", result["external_tools"])
        self.assertIn("cp2k.output_parse", result["external_tools"])
        self.assertIn("matplotlib", result["python_packages"])

    def test_inventory_redacts_potcar_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.joinpath("INCAR").write_text("ENCUT=400\n")
            root.joinpath("POTCAR").write_text("licensed placeholder\n")
            result = build_inventory(root)
            files = {item["path"]: item for item in result["files"]}
            self.assertEqual(result["code"], "vasp")
            self.assertIsNone(files["POTCAR"]["sha256"])
            self.assertEqual(files["POTCAR"]["hash_status"], "redacted-licensed")

    def test_extract_qe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pw.out"
            output.write_text(
                "Program PWSCF v.7.5 starts\niteration # 1\nconvergence has been achieved\n"
                "!    total energy              =   -10.000000 Ry\nJOB DONE.\n"
            )
            result = extract_summary(output)
            self.assertEqual(result["code"], "qe")
            self.assertTrue(result["completed"])
            self.assertAlmostEqual(result["final_energy_ev"], -136.05693122994)

    def test_extract_vasp_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "OUTCAR"
            output.write_text(
                "vasp.6.4.3\nfree  energy   TOTEN  =       -5.500000 eV\n"
                "reached required accuracy\nGeneral timing and accounting informations for this job\n"
            )
            result = extract_summary(output)
            self.assertEqual(result["code"], "vasp")
            self.assertTrue(result["completed"])
            self.assertEqual(result["final_energy_ev"], -5.5)

    def test_plot_and_artifact_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table = root / "dos.csv"
            with table.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=("energy_ev", "dos"))
                writer.writeheader()
                writer.writerows([{"energy_ev": -1, "dos": 0.2}, {"energy_ev": 0, "dos": 1.0}, {"energy_ev": 1, "dos": 0.3}])
            figure = root / "dos.png"
            style = ROOT / "skills" / "dft-postprocess" / "assets" / "dft-publication.mplstyle"
            metadata = plot_table(table, figure, "energy_ev", "dos", None, "Energy (eV)", "DOS", None, style)
            metadata_path = root / "dos.plot.json"
            metadata_path.write_text(json.dumps(metadata))
            manifest = build_artifact_manifest(
                "artifact-dos-001", ["run-anon-001"], "qe", "dos", "complete", root,
                ["dos-table=dos.csv", "plot-metadata=dos.plot.json"], ["dos-figure=dos.png"],
                "pass", ["finite data", "figure written"], ["No orbital claim"], ["dftpost", "plot-table"],
            )
            self.assertEqual(validation_errors("artifact", manifest), [])
            self.assertGreater(figure.stat().st_size, 0)

    def test_plot_rejects_nonfinite_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table = root / "bad.csv"
            table.write_text("x,y\n0,nan\n")
            style = ROOT / "skills" / "dft-postprocess" / "assets" / "dft-publication.mplstyle"
            with self.assertRaisesRegex(ValueError, "non-finite"):
                plot_table(table, root / "bad.png", "x", "y", None, "x", "y", None, style)

    def test_qe_bands_normalizer_uses_explicit_energy_reference(self) -> None:
        from dftpost.electronic import normalize_qe_bands

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "bands.gnu"
            source.write_text(
                "0.0 -1.0\n0.5 -0.5\n1.0 -1.0\n\n"
                "0.0 1.0\n0.5 0.4\n1.0 1.0\n",
                encoding="utf-8",
            )
            reference = root / "nscf.out"
            reference.write_text("the Fermi energy is 0.2500 ev\n", encoding="utf-8")
            output = root / "derived"
            result = normalize_qe_bands(
                source,
                reference,
                output,
                "dataset-bands-001",
                maturity="format-fixture-validated",
            )
            dataset = json.loads(result["dataset"].read_text(encoding="utf-8"))
            analysis = json.loads(result["analysis"].read_text(encoding="utf-8"))
            self.assertEqual(validation_errors("dataset", dataset), [])
            self.assertEqual(dataset["dimensions"], {"bands": 2, "kpoints": 3, "rows": 6})
            self.assertEqual(analysis["energy_reference_ev"], 0.25)
            self.assertAlmostEqual(analysis["sampled_vbm_ev"], -0.75)
            self.assertAlmostEqual(analysis["sampled_cbm_ev"], 0.15)
            self.assertGreater(result["figure"].stat().st_size, 0)

    def test_qe_pdos_total_accepts_separate_reference_and_preserves_both_totals(self) -> None:
        from dftpost.electronic import normalize_qe_dos

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            total = root / "sample.pdos_tot"
            total.write_text("# E (eV) dos(E) pdos(E)\n-1 1.0 0.8\n0 2.0 1.7\n1 1.0 0.8\n")
            reference = root / "nscf.out"
            reference.write_text("the Fermi energy is 0.0 ev\n")
            result = normalize_qe_dos(
                total,
                [],
                root / "derived",
                "dataset-pdos-total-001",
                energy_reference_path=reference,
                maturity="format-fixture-validated",
            )
            analysis = json.loads(result["analysis"].read_text(encoding="utf-8"))
            self.assertEqual([item["label"] for item in analysis["channels"]], ["total", "projected-total"])

    def test_qe_electronic_cli_forwards_energy_reference_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "nscf.out"
            reference.write_text("the Fermi energy is 0.0 ev\n")
            bands = root / "bands.gnu"
            bands.write_text("0 -1\n1 -0.5\n\n0 1\n1 0.5\n")
            band_result = subprocess.run(
                [
                    sys.executable, str(POST_SCRIPTS / "dftpost_cli.py"), "qe-bands", str(bands),
                    "--energy-reference", str(reference), "--dataset-id", "dataset-cli-bands-001",
                    "--out-dir", str(root / "bands-out"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(band_result.returncode, 0, band_result.stderr)

            pdos_total = root / "sample.pdos_tot"
            pdos_total.write_text("# E (eV) dos(E) pdos(E)\n-1 1 0.8\n0 2 1.7\n1 1 0.8\n")
            dos_result = subprocess.run(
                [
                    sys.executable, str(POST_SCRIPTS / "dftpost_cli.py"), "qe-dos", str(pdos_total),
                    "--energy-reference", str(reference), "--dataset-id", "dataset-cli-dos-001",
                    "--out-dir", str(root / "dos-out"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(dos_result.returncode, 0, dos_result.stderr)

            combined_result = subprocess.run(
                [
                    sys.executable, str(POST_SCRIPTS / "dftpost_cli.py"), "bands-dos",
                    "--bands-table", str(root / "bands-out" / "bands.csv"),
                    "--dos-table", str(root / "dos-out" / "dos.csv"),
                    "--pdos-channel", "projected-total",
                    "--out", str(root / "bands-tdos-pdos.png"),
                    "--metadata-out", str(root / "bands-tdos-pdos.plot.json"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(combined_result.returncode, 0, combined_result.stderr)
            combined_metadata = json.loads(
                (root / "bands-tdos-pdos.plot.json").read_text(encoding="utf-8")
            )
            self.assertEqual(combined_metadata["dos_content"], "tdos+pdos")
            self.assertEqual(combined_metadata["tdos_channel_labels"], ["total"])
            self.assertEqual(combined_metadata["pdos_channel_labels"], ["projected-total"])

    def test_qe_dos_normalizer_aggregates_standard_projected_files(self) -> None:
        from dftpost.electronic import normalize_qe_dos

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            total = root / "sample.dos"
            total.write_text(
                "# E (eV) dos(E) Int dos(E) EFermi = 0.000 eV\n"
                "-1.0 1.0 0.0\n0.0 2.0 1.5\n1.0 1.0 3.0\n",
                encoding="utf-8",
            )
            first = root / "sample.pdos_atm#1(A)_wfc#1(s)"
            second = root / "sample.pdos_atm#2(A)_wfc#1(s)"
            first.write_text("# E (eV) ldos(E) pdos(E)\n-1 0.2 0.2\n0 0.4 0.4\n1 0.2 0.2\n")
            second.write_text("# E (eV) ldos(E) pdos(E)\n-1 0.3 0.3\n0 0.6 0.6\n1 0.3 0.3\n")
            result = normalize_qe_dos(
                total,
                [first, second],
                root / "derived",
                "dataset-dos-001",
                group_by="species-orbital",
                integration_window_ev=(-1.0, 1.0),
                maturity="format-fixture-validated",
            )
            dataset = json.loads(result["dataset"].read_text(encoding="utf-8"))
            analysis = json.loads(result["analysis"].read_text(encoding="utf-8"))
            self.assertEqual(validation_errors("dataset", dataset), [])
            self.assertEqual(dataset["dimensions"]["channels"], 2)
            projected = next(item for item in analysis["channels"] if item["channel_type"] == "projected")
            self.assertEqual(projected["label"], "A:s")
            self.assertAlmostEqual(projected["value_at_reference"], 1.0)
            self.assertAlmostEqual(projected["window_integral"], 1.5)
            self.assertGreater(result["figure"].stat().st_size, 0)

    def test_qe_filproj_fatband_requires_and_applies_selector(self) -> None:
        from dftpost.electronic import (
            _bubble_marker_areas,
            _projection_line_widths,
            normalize_qe_fatband,
        )

        self.assertEqual(
            _bubble_marker_areas([0.0, 0.25, 1.0], marker_scale=8.0),
            [0.0, 16.0, 64.0],
        )
        self.assertEqual(
            _projection_line_widths([0.0, 0.25, 1.0], marker_scale=8.0),
            [0.0, 0.9, 3.6],
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bands = root / "bands.gnu"
            bands.write_text("0 -1\n1 -0.5\n\n0 1\n1 0.5\n")
            reference = root / "nscf.out"
            reference.write_text("the Fermi energy is 0.0 ev\n")
            filproj = root / "filproj.dat"
            filproj.write_text(
                "1 2 2\nF F\n"
                "1 1 A 2P 1 1 1\n"
                "1 1 0.1\n1 2 0.2\n2 1 0.3\n2 2 0.4\n"
                "2 1 B 3D 2 2 1\n"
                "1 1 0.5\n1 2 0.6\n2 1 0.7\n2 2 0.8\n"
            )
            with self.assertRaisesRegex(ValueError, "selector"):
                normalize_qe_fatband(
                    bands, filproj, reference, root / "blocked", "dataset-fat-000", {},
                    maturity="format-fixture-validated",
                )
            result = normalize_qe_fatband(
                bands,
                filproj,
                reference,
                root / "derived",
                "dataset-fat-001",
                {"species": "B", "l": "2"},
                energy_window_ev=(-2.0, 2.0),
                marker_scale=8.0,
                render_mode="bubble",
                projection_label="B-d channel",
                bands_label="Reference bands",
                maturity="format-fixture-validated",
            )
            analysis = json.loads(result["analysis"].read_text(encoding="utf-8"))
            plot_metadata = json.loads(result["plot_metadata"].read_text(encoding="utf-8"))
            self.assertEqual(analysis["selected_state_count"], 1)
            self.assertAlmostEqual(analysis["weight_sum"], 2.6)
            self.assertEqual(plot_metadata["render_mode"], "bubble")
            self.assertEqual(plot_metadata["projection_label"], "B-d channel")
            self.assertEqual(plot_metadata["background_label"], "Reference bands")
            self.assertEqual(plot_metadata["legend_labels"], ["Reference bands", "B-d channel"])
            self.assertEqual(
                plot_metadata["bubble_area_mapping"],
                "marker_area_pt2 = marker_scale^2 * projection_weight",
            )
            self.assertEqual(plot_metadata["marker_scale"], 8.0)
            self.assertEqual(plot_metadata["x_limits"], [0.0, 1.0])
            self.assertGreater(result["figure"].stat().st_size, 0)

    def test_combined_bands_dos_plot_has_exact_horizontal_limits(self) -> None:
        from dftpost.electronic import normalize_qe_bands, normalize_qe_dos, plot_bands_dos

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bands_source = root / "bands.gnu"
            bands_source.write_text("0 -1\n1 -0.5\n2 -1\n\n0 1\n1 0.5\n2 1\n")
            reference = root / "nscf.out"
            reference.write_text("the Fermi energy is 0.0 ev\n")
            dos_source = root / "sample.dos"
            dos_source.write_text(
                "# E (eV) dos(E) Int dos(E) EFermi = 0.0 eV\n"
                "-10 1000 0\n-1 0.5 0\n0 2.0 1\n1 0.5 2\n"
            )
            pdos_source = root / "sample.pdos_atm#1(A)_wfc#1(s)"
            pdos_source.write_text(
                "# E (eV) ldos(E) pdos(E)\n"
                "-10 500 500\n-1 0.25 0.25\n0 1.0 1.0\n1 0.25 0.25\n"
            )
            bands_result = normalize_qe_bands(
                bands_source, reference, root / "bands-out", "dataset-combined-bands-001"
            )
            dos_result = normalize_qe_dos(
                dos_source, [pdos_source], root / "dos-out", "dataset-combined-dos-001"
            )
            metadata = plot_bands_dos(
                bands_result["table"],
                dos_result["table"],
                root / "bands-dos.png",
                energy_window_ev=(-1.5, 1.5),
            )
            self.assertEqual(metadata["band_x_limits"], [0.0, 2.0])
            self.assertEqual(metadata["dos_x_limits"], [0.0, 2.0])
            self.assertEqual(metadata["band_color"], "#7f1d1d")
            self.assertEqual(metadata["dos_content"], "tdos+pdos")
            self.assertEqual(metadata["tdos_channel_labels"], ["total"])
            self.assertEqual(metadata["pdos_channel_labels"], ["A:s"])
            self.assertEqual(metadata["dos_channel_labels"], ["total", "A:s"])
            self.assertGreater((root / "bands-dos.png").stat().st_size, 0)

    def test_combined_bands_dos_keeps_tdos_when_pdos_is_filtered(self) -> None:
        from dftpost.electronic import normalize_qe_bands, plot_bands_dos

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bands_source = root / "bands.gnu"
            bands_source.write_text("0 -1\n1 -0.5\n\n0 1\n1 0.5\n")
            reference = root / "nscf.out"
            reference.write_text("the Fermi energy is 0.0 ev\n")
            bands_result = normalize_qe_bands(
                bands_source, reference, root / "bands-out", "dataset-filtered-bands-001"
            )
            dos_table = root / "dos.csv"
            dos_table.write_text(
                "energy_relative_ev,channel_label,channel_type,dos_states_per_ev\n"
                "-1,total,total,0.5\n0,total,total,2.0\n1,total,total,0.5\n"
                "-1,A:s,projected,0.2\n0,A:s,projected,0.8\n1,A:s,projected,0.2\n"
                "-1,B:p,projected,0.3\n0,B:p,projected,1.1\n1,B:p,projected,0.3\n"
            )
            metadata = plot_bands_dos(
                bands_result["table"],
                dos_table,
                root / "filtered.png",
                pdos_channel_labels=["B:p"],
            )
            self.assertEqual(metadata["tdos_channel_labels"], ["total"])
            self.assertEqual(metadata["pdos_channel_labels"], ["B:p"])
            self.assertEqual(metadata["dos_channel_labels"], ["total", "B:p"])

            missing_pdos = root / "total-only.csv"
            missing_pdos.write_text(
                "energy_relative_ev,channel_label,channel_type,dos_states_per_ev\n"
                "-1,total,total,0.5\n0,total,total,2.0\n1,total,total,0.5\n"
            )
            with self.assertRaisesRegex(ValueError, "TDOS \\+ PDOS"):
                plot_bands_dos(
                    bands_result["table"], missing_pdos, root / "must-fail.png"
                )

    def test_qe_electronic_outputs_require_explicit_atomic_overwrite(self) -> None:
        from dftpost.electronic import normalize_qe_bands, plot_bands_dos

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bands_source = root / "bands.gnu"
            bands_source.write_text("0 -1\n1 -0.5\n\n0 1\n1 0.5\n")
            reference = root / "nscf.out"
            reference.write_text("the Fermi energy is 0.0 ev\n")
            output = root / "bands-out"
            first = normalize_qe_bands(
                bands_source, reference, output, "dataset-overwrite-bands-001"
            )
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                normalize_qe_bands(
                    bands_source, reference, output, "dataset-overwrite-bands-001"
                )
            second = normalize_qe_bands(
                bands_source,
                reference,
                output,
                "dataset-overwrite-bands-001",
                overwrite=True,
            )
            self.assertEqual(first, second)
            self.assertGreater(second["figure"].stat().st_size, 0)

            dos_table = root / "dos.csv"
            dos_table.write_text(
                "energy_relative_ev,channel_label,channel_type,dos_states_per_ev\n"
                "-1,total,total,0.5\n0,total,total,2.0\n1,total,total,0.5\n"
                "-1,A:s,projected,0.2\n0,A:s,projected,0.8\n1,A:s,projected,0.2\n"
            )
            combined = root / "bands-dos.png"
            plot_bands_dos(second["table"], dos_table, combined)
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                plot_bands_dos(second["table"], dos_table, combined)
            metadata = plot_bands_dos(
                second["table"], dos_table, combined, overwrite=True
            )
            self.assertEqual(metadata["band_color"], "#7f1d1d")
            self.assertGreater(combined.stat().st_size, 0)

    def test_vasp_electronic_normalizers_share_generic_schemas(self) -> None:
        from dftpost.vasp_electronic import (
            normalize_vasp_bands,
            normalize_vasp_dos,
            normalize_vasp_fatband,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            poscar = root / "POSCAR"
            poscar.write_text(
                "fixture\n1.0\n1 0 0\n0 1 0\n0 0 8\nA B\n1 1\nDirect\n0 0 0\n0.5 0.5 0.5\n"
            )
            outcar = root / "OUTCAR"
            outcar.write_text(
                " ISPIN = 1\n LORBIT = 11\n E-fermi : 0.2500\n General timing and accounting informations\n"
            )
            kpoints = root / "KPOINTS"
            kpoints.write_text(
                "path\n2\nLine-mode\nReciprocal\n"
                "0 0 0 GAMMA\n0.5 0 0 X\n"
            )
            eigenval = root / "EIGENVAL"
            eigenval.write_text(
                " 2 2 1 1\nheader\nheader\nheader\nfixture\n2 2 2\n\n"
                "0 0 0 0.5\n1 -1.0 1.0\n2 1.0 0.0\n\n"
                "0.5 0 0 0.5\n1 -0.5 1.0\n2 0.6 0.0\n"
            )
            bands = normalize_vasp_bands(
                eigenval,
                kpoints,
                poscar,
                outcar,
                root / "bands-out",
                "dataset-vasp-bands-001",
                energy_window_ev=(-2.0, 2.0),
            )
            band_dataset = json.loads(bands["dataset"].read_text())
            band_analysis = json.loads(bands["analysis"].read_text())
            band_plot = json.loads(bands["plot_metadata"].read_text())
            self.assertEqual(validation_errors("dataset", band_dataset), [])
            self.assertEqual(band_dataset["dimensions"]["spin_channels"], 1)
            self.assertEqual(band_analysis["energy_reference_ev"], 0.25)
            self.assertEqual(band_plot["band_color"], "#7f1d1d")
            self.assertEqual(band_plot["x_limits"][0], 0.0)
            self.assertGreater(band_plot["x_limits"][1], 0.0)

            doscar = root / "DOSCAR"
            doscar.write_text(
                "2 2 1 0\nheader\nheader\nheader\nfixture\n"
                "2 -2 3 0.25 1\n"
                "-2 1 0\n0 2 1\n2 1 2\n"
                "2 -2 3 0.25 1\n"
                "-2 1 1 1 1 1 1 1 1 1\n0 2 2 2 2 2 2 2 2 2\n2 1 1 1 1 1 1 1 1 1\n"
                "2 -2 3 0.25 1\n"
                "-2 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5\n"
                "0 1 1 1 1 1 1 1 1 1\n2 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5\n"
            )
            dos = normalize_vasp_dos(
                doscar,
                poscar,
                outcar,
                root / "dos-out",
                "dataset-vasp-dos-001",
                group_by="species-orbital",
                integration_window_ev=(-1.0, 1.0),
            )
            dos_dataset = json.loads(dos["dataset"].read_text())
            dos_analysis = json.loads(dos["analysis"].read_text())
            self.assertEqual(validation_errors("dataset", dos_dataset), [])
            self.assertEqual(dos_dataset["dimensions"]["channels"], 7)
            self.assertEqual(
                [item["label"] for item in dos_analysis["channels"]],
                ["total", "A:s", "A:p", "A:d", "B:s", "B:p", "B:d"],
            )

            procar = root / "PROCAR"
            procar.write_text(
                "PROCAR lm decomposed\n"
                "# of k-points: 2 # of bands: 2 # of ions: 2\n\n"
                "k-point 1 : 0 0 0 weight = 0.5\n\n"
                "band 1 # energy -1.0 # occ. 2\n\n"
                "ion s py pz px dxy dyz dz2 dxz x2-y2 tot\n"
                "1 0.1 0 0 0 0 0 0 0 0 0.1\n2 0 0.1 0.2 0.3 0 0 0 0 0 0.6\n"
                "tot 0.1 0.1 0.2 0.3 0 0 0 0 0 0.7\n\n"
                "band 2 # energy 1.0 # occ. 0\n\n"
                "ion s py pz px dxy dyz dz2 dxz x2-y2 tot\n"
                "1 0.2 0 0 0 0 0 0 0 0 0.2\n2 0 0.2 0.1 0.1 0 0 0 0 0 0.4\n"
                "tot 0.2 0.2 0.1 0.1 0 0 0 0 0 0.6\n\n"
                "k-point 2 : 0.5 0 0 weight = 0.5\n\n"
                "band 1 # energy -0.5 # occ. 2\n\n"
                "ion s py pz px dxy dyz dz2 dxz x2-y2 tot\n"
                "1 0.1 0 0 0 0 0 0 0 0 0.1\n2 0 0.2 0.2 0.2 0 0 0 0 0 0.6\n"
                "tot 0.1 0.2 0.2 0.2 0 0 0 0 0 0.7\n\n"
                "band 2 # energy 0.6 # occ. 0\n\n"
                "ion s py pz px dxy dyz dz2 dxz x2-y2 tot\n"
                "1 0.2 0 0 0 0 0 0 0 0 0.2\n2 0 0.1 0.1 0.1 0 0 0 0 0 0.3\n"
                "tot 0.2 0.1 0.1 0.1 0 0 0 0 0 0.5\n"
            )
            fatband = normalize_vasp_fatband(
                eigenval,
                kpoints,
                poscar,
                outcar,
                procar,
                root / "fatband-out",
                "dataset-vasp-fatband-001",
                {"species": "B", "l": "1"},
                energy_window_ev=(-2.0, 2.0),
            )
            fat_analysis = json.loads(fatband["analysis"].read_text())
            fat_plot = json.loads(fatband["plot_metadata"].read_text())
            self.assertEqual(fat_analysis["selected_atom_count"], 1)
            self.assertAlmostEqual(fat_analysis["weight_sum"], 1.9)
            self.assertEqual(fat_plot["render_mode"], "line-width")
            self.assertEqual(fat_plot["projection_label"], "B-p")
            self.assertEqual(fat_plot["background_label"], "Bands")
            self.assertEqual(fat_plot["legend_labels"], ["Bands", "B-p"])

    def test_run_trace_normalizes_qe_and_vasp_without_equating_completion_with_geometry_convergence(self) -> None:
        from dftpost.runtrace import normalize_run_trace

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            qe = root / "qe.out"
            qe.write_text(
                "Program PWSCF v.7.5\n"
                "iteration # 1\nestimated scf accuracy < 0.10 Ry\n"
                "iteration # 2\nestimated scf accuracy < 0.01 Ry\n"
                "! total energy = -10.0 Ry\n"
                "convergence has been achieved in 2 iterations\n"
                "Total force = 0.020 Total SCF correction = 0.001\n"
                "JOB DONE.\n"
            )
            qe_result = normalize_run_trace(
                qe, "qe", root / "qe-trace", "dataset-qe-trace-001"
            )
            qe_analysis = json.loads(qe_result["analysis"].read_text())
            qe_dataset = json.loads(qe_result["dataset"].read_text())
            self.assertEqual(validation_errors("dataset", qe_dataset), [])
            self.assertTrue(qe_analysis["run_complete"])
            self.assertTrue(qe_analysis["electronic_converged"])
            self.assertIsNone(qe_analysis["geometry_converged"])
            self.assertEqual(qe_analysis["electronic_iteration_count"], 2)
            self.assertAlmostEqual(qe_analysis["final_energy_ev"], -136.05693122994)

            vasp = root / "OUTCAR"
            vasp.write_text(
                "Iteration 1( 1)\nIteration 1( 2)\n"
                "POSITION TOTAL-FORCE (eV/Angst)\n"
                "---\n0 0 0 0.1 0.0 0.0\n0 0 0 0.0 0.3 0.4\n---\n"
                "free  energy   TOTEN  = -5.0 eV\n"
                "General timing and accounting informations for this job:\n"
            )
            vasp_result = normalize_run_trace(
                vasp, "vasp", root / "vasp-trace", "dataset-vasp-trace-001"
            )
            vasp_analysis = json.loads(vasp_result["analysis"].read_text())
            self.assertTrue(vasp_analysis["run_complete"])
            self.assertIsNone(vasp_analysis["electronic_converged"])
            self.assertFalse(vasp_analysis["geometry_converged"])
            self.assertEqual(vasp_analysis["ionic_step_count"], 1)
            self.assertEqual(vasp_analysis["electronic_iteration_count"], 2)
            self.assertAlmostEqual(vasp_analysis["final_max_force_ev_per_angstrom"], 0.5)

    def test_qe_phonon_and_epc_normalizers_keep_units_and_q_weight_limitations_explicit(self) -> None:
        from dftpost.phonon_epc import normalize_qe_epc, normalize_qe_phonon

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            frequencies = root / "sample.freq.gp"
            frequencies.write_text("0.0 -0.2 0.0 2.0\n1.0 0.1 1.0 3.0\n")
            phonon = normalize_qe_phonon(
                frequencies,
                root / "phonon-out",
                "dataset-phonon-001",
                frequency_unit="cm-1",
                imaginary_threshold=0.05,
            )
            phonon_analysis = json.loads(phonon["analysis"].read_text())
            self.assertEqual(phonon_analysis["imaginary_frequency_count"], 1)
            self.assertEqual(phonon_analysis["frequency_unit"], "cm-1")

            alpha2f = root / "alpha2F.dat"
            alpha2f.write_text(
                "# E(THz) 0.001 0.002\n"
                "0.0 0.0 0.0\n1.0 0.5 0.25\n2.0 0.5 0.25\n"
            )
            lambda_table = root / "lambda.dat"
            lambda_table.write_text(
                "# degauss lambda int-alpha2F logw nef\n"
                "0.001 1.0 1.0 100 2\n0.002 0.5 0.5 100 2\n"
            )
            elph = root / "elph.inp_lambda.1"
            elph.write_text(
                "0 0 0 2 2\n1.0 2.0\n"
                "Gaussian Broadening: 0.001 Ry, ngauss=0\n"
                "lambda(1)=0.2 gamma=1.0 GHz\nlambda(2)=0.3 gamma=2.0 GHz\n"
                "Gaussian Broadening: 0.002 Ry, ngauss=0\n"
                "lambda(1)=0.1 gamma=0.5 GHz\nlambda(2)=0.2 gamma=1.0 GHz\n"
            )
            epc = normalize_qe_epc(
                alpha2f,
                lambda_table,
                [elph],
                root / "epc-out",
                "dataset-epc-001",
                selected_smearing_indices=[1, 2],
                qmode_smearing_index=1,
            )
            epc_dataset = json.loads(epc["dataset"].read_text())
            epc_analysis = json.loads(epc["analysis"].read_text())
            self.assertEqual(validation_errors("dataset", epc_dataset), [])
            self.assertEqual(epc_dataset["dimensions"]["smearing_channels"], 2)
            self.assertEqual(epc_dataset["dimensions"]["q_mode_rows"], 2)
            self.assertEqual(epc_analysis["q_weight_closure_status"], "not-run")

    def test_real_space_grid_and_bader_require_explicit_physical_references(self) -> None:
        from dftpost.realspace import normalize_bader_acf, normalize_grid_field

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cube = root / "potential.cube"
            cube.write_text(
                "synthetic cube\n"
                "potential with explicit caller unit\n"
                "1 0 0 0\n"
                "2 1 0 0\n"
                "2 0 1 0\n"
                "3 0 0 1\n"
                "1 1.0 0 0 0\n"
                "1 2 3 1 2 3 1 2 3 1 2 3\n"
            )
            grid = normalize_grid_field(
                cube,
                "qe",
                root / "grid-out",
                "dataset-real-space-grid-001",
                field_kind="electrostatic-potential",
                field_unit="caller-native",
                axis=2,
                potential_to_ev=2.0,
                fermi_energy_ev=1.0,
                vacuum_window_angstrom=(0.5, 1.1),
            )
            grid_dataset = json.loads(grid["dataset"].read_text())
            grid_analysis = json.loads(grid["analysis"].read_text())
            grid_plot = json.loads(grid["plot_metadata"].read_text())
            self.assertEqual(validation_errors("dataset", grid_dataset), [])
            self.assertEqual(grid_dataset["dimensions"]["grid_z"], 3)
            self.assertAlmostEqual(grid_analysis["work_function"]["work_function_ev"], 4.0)
            self.assertEqual(grid_plot["x_limits"], [0.0, 2 * 0.529177210903])
            with self.assertRaisesRegex(ValueError, "requires potential_to_ev"):
                normalize_grid_field(
                    cube,
                    "qe",
                    root / "incomplete-work-function",
                    "dataset-real-space-grid-002",
                    field_kind="electrostatic-potential",
                    field_unit="caller-native",
                    fermi_energy_ev=1.0,
                )

            acf = root / "ACF.dat"
            acf.write_text(
                "# X Y Z CHARGE MIN DIST ATOMIC VOL\n"
                "--------------------------------\n"
                "1 0 0 0 1.2 0.5 10\n"
                "2 1 0 0 1.8 0.5 10\n"
                "--------------------------------\n"
                "VACUUM CHARGE: 0.0\n"
                "NUMBER OF ELECTRONS: 3.0\n"
            )
            bader = normalize_bader_acf(
                acf,
                "vasp",
                root / "bader-out",
                "dataset-real-space-bader-001",
                reference_electrons=[1.0, 2.0],
            )
            bader_dataset = json.loads(bader["dataset"].read_text())
            bader_analysis = json.loads(bader["analysis"].read_text())
            self.assertEqual(validation_errors("dataset", bader_dataset), [])
            self.assertEqual(bader_analysis["electron_closure_status"], "pass")
            self.assertAlmostEqual(bader_analysis["reference_minus_basin_sum"], 0.0)
            with self.assertRaisesRegex(ValueError, "count must match"):
                normalize_bader_acf(
                    acf,
                    "vasp",
                    root / "bad-reference",
                    "dataset-real-space-bader-002",
                    reference_electrons=[2.0],
                )

    def test_real_space_slice_style_atoms_and_miller_plane_are_explicit(self) -> None:
        from dftpost.realspace import normalize_grid_field

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cube = root / "elf.cube"
            cube.write_text(
                "synthetic ELF\n"
                "dimensionless field with atoms on the periodic (110) plane\n"
                "2 0 0 0\n"
                "-2 1 0 0\n"
                "-2 0 1 0\n"
                "-3 0 0 1\n"
                "1 1.0 0 0 0\n"
                "8 8.0 0.5 0.5 1.0\n"
                "0.0 0.2 0.4 0.6 0.8 1.0 0.9 0.7 0.5 0.3 0.1 0.0\n"
            )
            result = normalize_grid_field(
                cube,
                "qe",
                root / "elf-out",
                "dataset-real-space-elf-slice-001",
                field_kind="electron-localization",
                field_unit="dimensionless",
                slice_hkl=(1, 1, 0),
                slice_offset=0.0,
                atom_overlay="near-plane",
            )
            plot = json.loads(result["plot_metadata"].read_text())
            analysis = json.loads(result["analysis"].read_text())
            self.assertTrue(result["slice_figure"].is_file())
            self.assertEqual(plot["slice"]["plane_hkl"], [1, 1, 0])
            self.assertEqual(plot["slice"]["colormap"], "turbo")
            self.assertEqual(plot["slice"]["value_limits"], [0.0, 1.0])
            self.assertEqual(plot["slice"]["atom_overlay"], "near-plane")
            self.assertEqual(plot["slice"]["displayed_atom_count"], 2)
            self.assertEqual(analysis["slice_plane"]["interpolation"], "periodic-linear")

            signed_cube = root / "difference.cube"
            signed_cube.write_text(
                cube.read_text().replace("synthetic ELF", "synthetic difference").replace(
                    "0.0 0.2 0.4 0.6 0.8 1.0 0.9 0.7 0.5 0.3 0.1 0.0",
                    "-0.6 -0.4 -0.2 0.0 0.2 0.4 0.6 0.4 0.2 0.0 -0.2 -0.4",
                )
            )
            signed = normalize_grid_field(
                signed_cube,
                "qe",
                root / "difference-out",
                "dataset-real-space-difference-slice-001",
                field_kind="charge-density-difference",
                field_unit="caller-native",
            )
            signed_plot = json.loads(signed["plot_metadata"].read_text())
            self.assertEqual(signed_plot["slice"]["colormap"], "RdBu_r")
            self.assertLess(signed_plot["slice"]["value_limits"][0], 0.0)
            self.assertEqual(
                signed_plot["slice"]["value_limits"][0],
                -signed_plot["slice"]["value_limits"][1],
            )

    def test_cube_grid_combination_checks_alignment_and_records_coefficients(self) -> None:
        from dftpost.realspace import _read_cube, combine_cube_grids

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            header = (
                "synthetic density\n"
                "aligned component\n"
                "1 0 0 0\n"
                "-2 1 0 0\n"
                "-2 0 1 0\n"
                "-2 0 0 1\n"
                "1 1.0 0 0 0\n"
            )
            hetero = root / "hetero.cube"
            host = root / "host.cube"
            partner = root / "partner.cube"
            hetero.write_text(header + "3 3 3 3 3 3 3 3\n")
            host.write_text(header + "1 1 1 1 1 1 1 1\n")
            partner.write_text(header + "0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5\n")
            result = combine_cube_grids(
                [(1.0, hetero), (-1.0, host), (-1.0, partner)],
                root / "combine-out",
                "dataset-grid-combination-001",
                field_unit="caller-native",
            )
            values, _, _ = _read_cube(result["grid"])
            self.assertTrue((values == 1.5).all())
            analysis = json.loads(result["analysis"].read_text())
            dataset = json.loads(result["dataset"].read_text())
            self.assertEqual(analysis["coefficients"], [1.0, -1.0, -1.0])
            self.assertEqual(validation_errors("dataset", dataset), [])

            misaligned = root / "misaligned.cube"
            misaligned.write_text(header.replace("-2 0 0 1", "-2 0 0 2") + "1 1 1 1 1 1 1 1\n")
            with self.assertRaisesRegex(ValueError, "grid geometry does not align"):
                combine_cube_grids(
                    [(1.0, hetero), (-1.0, misaligned)],
                    root / "misaligned-out",
                    "dataset-grid-combination-002",
                    field_unit="caller-native",
                )

    def test_vesta_project_surfaces_and_nonzero_success_quirk_are_fail_closed(self) -> None:
        from dftpost.vesta import classify_conversion_result, configure_density_path, configure_isosurfaces

        project = (
            "#VESTA_FORMAT_VERSION 3.5.4\n"
            "IMPORT_DENSITY 1\n+1.000000 relative.cube\nSTYLE\nSURFS   0  1  1\nISURF\n  0   0   0   0\nTEX3P\nCOMPS 1\n"
        )
        configured = configure_isosurfaces(
            project,
            level=0.01,
            mode="positive-negative",
            positive_color=(255, 210, 0),
            negative_color=(0, 200, 255),
            opacity_parallel=160,
            opacity_perpendicular=230,
        )
        self.assertIn("  1   0", configured)
        self.assertNotIn("  2   2", configured)
        self.assertIn("255 210   0", configured)
        configured_path = configure_density_path(configured, Path("/tmp/signed-grid.cube"))
        self.assertIn(f"+1.000000 {Path('/tmp/signed-grid.cube').resolve()}", configured_path)
        self.assertTrue(classify_conversion_result(0, "", "", configured))
        self.assertTrue(classify_conversion_result(255, "Saved data to: probe.vesta", "", configured))
        self.assertFalse(classify_conversion_result(255, "", "", configured))
        self.assertFalse(classify_conversion_result(7, "Saved data to: probe.vesta", "", configured))

    def test_band_comparison_and_projection_panels_consume_normalized_tables(self) -> None:
        from dftpost.band_views import plot_band_comparison, plot_projection_panels

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            header = "k_index,k_distance,band_index,energy_relative_ev\n"
            rows_a = (
                "1,0.0,1,-1.0\n2,0.5,1,-0.5\n3,1.0,1,-1.0\n"
                "1,0.0,2,1.0\n2,0.5,2,0.4\n3,1.0,2,1.0\n"
            )
            rows_b = (
                "1,0.0,1,-0.8\n2,0.5,1,-0.3\n3,1.0,1,-0.8\n"
                "1,0.0,2,1.2\n2,0.5,2,0.6\n3,1.0,2,1.2\n"
            )
            bands_a = root / "bands-a.csv"
            bands_b = root / "bands-b.csv"
            bands_a.write_text(header + rows_a)
            bands_b.write_text(header + rows_b)
            meta_a = root / "bands-a.plot.json"
            meta_a.write_text(json.dumps({
                "high_symmetry_points": [
                    {"label": "GAMMA", "k_distance": 0.0},
                    {"label": "X", "k_distance": 1.0},
                ]
            }))

            comparison = plot_band_comparison(
                [("case A", bands_a), ("case B", bands_b)],
                root / "compare.png",
                metadata_paths={"case A": meta_a},
                layout="row",
                energy_window_ev=(-2.0, 2.0),
            )
            self.assertEqual(comparison["plot_type"], "bands-comparison")
            self.assertEqual(comparison["band_color"], "#7f1d1d")
            self.assertEqual(comparison["layout"], "row")
            self.assertEqual(comparison["series"][0]["x_limits"], [0.0, 1.0])
            self.assertGreater((root / "compare.png").stat().st_size, 0)

            projection_header = (
                "k_index,k_distance,band_index,energy_relative_ev,projection_weight\n"
            )
            projection_one = root / "projection-one.csv"
            projection_two = root / "projection-two.csv"
            projection_one.write_text(
                projection_header
                + rows_a.replace("\n", ",0.2\n").replace("energy_relative_ev,0.2", "energy_relative_ev")
            )
            projection_two.write_text(
                projection_header
                + rows_a.replace("\n", ",0.7\n").replace("energy_relative_ev,0.7", "energy_relative_ev")
            )
            panels = plot_projection_panels(
                bands_a,
                [("channel 1", projection_one), ("channel 2", projection_two)],
                root / "projection-panels.png",
                overview_output=root / "projection-overview.png",
                bands_metadata_path=meta_a,
                energy_window_ev=(-2.0, 2.0),
                render_mode="bubble",
                bands_label="Reference bands",
            )
            self.assertEqual(panels["plot_type"], "projected-bands-panels")
            self.assertEqual(panels["primary_representation"], "separated-projection-panels")
            self.assertEqual(panels["render_mode"], "bubble")
            self.assertEqual([item["label"] for item in panels["projections"]], ["channel 1", "channel 2"])
            self.assertEqual(
                panels["legend_labels"],
                ["Reference bands", "channel 1", "channel 2"],
            )
            self.assertEqual(
                panels["panel_legend_labels"],
                {
                    "channel 1": ["Reference bands", "channel 1"],
                    "channel 2": ["Reference bands", "channel 2"],
                },
            )
            self.assertEqual(
                panels["bubble_area_mapping"],
                "marker_area_pt2 = marker_scale^2 * projection_weight",
            )
            self.assertGreater((root / "projection-panels.png").stat().st_size, 0)
            self.assertGreater((root / "projection-overview.png").stat().st_size, 0)

            cli_result = subprocess.run(
                [
                    sys.executable,
                    str(POST_SCRIPTS / "dftpost_cli.py"),
                    "band-projections",
                    "--bands-table",
                    str(bands_a),
                    "--projection",
                    f"channel 1={projection_one}",
                    "--bands-label",
                    "Reference bands",
                    "--panels-out",
                    str(root / "cli-projection-panels.png"),
                    "--metadata-out",
                    str(root / "cli-projection-panels.plot.json"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(cli_result.returncode, 0, cli_result.stderr)

            misaligned = root / "misaligned.csv"
            misaligned.write_text(projection_one.read_text().replace("2,0.5,1", "2,0.6,1", 1))
            with self.assertRaisesRegex(ValueError, "align"):
                plot_projection_panels(
                    bands_a,
                    [("bad", misaligned)],
                    root / "must-fail.png",
                )

    def test_vaspkit_band_adapter_requires_explicit_energy_transform(self) -> None:
        from dftpost.vaspkit import normalize_vaspkit_bands

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            band_data = root / "BAND.dat"
            band_data.write_text("0.0 -1.0 1.0\n0.5 -0.5 0.4\n1.0 -1.0 1.0\n")
            labels = root / "KLABELS"
            labels.write_text(
                "K-Label    Coordinate in line-mode\n"
                "GAMMA 0.0\nX 0.5\nM 1.0\n"
            )
            result = normalize_vaspkit_bands(
                band_data,
                labels,
                root / "derived",
                "dataset-vaspkit-bands-001",
                energy_offset_ev=-0.25,
                energy_reference_description="caller-declared offset to the selected reference",
            )
            with result["table"].open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            dataset = json.loads(result["dataset"].read_text())
            analysis = json.loads(result["analysis"].read_text())
            self.assertEqual(validation_errors("dataset", dataset), [])
            self.assertEqual(dataset["maturity"], "synthetic-validated")
            self.assertAlmostEqual(float(rows[0]["energy_relative_ev"]), -1.25)
            self.assertEqual(analysis["energy_transform"], "energy_relative_ev = energy_input_ev + energy_offset_ev")
            self.assertEqual(analysis["high_symmetry_points"][0]["label"], "GAMMA")
            self.assertGreater(result["figure"].stat().st_size, 0)

            with self.assertRaisesRegex(ValueError, "description"):
                normalize_vaspkit_bands(
                    band_data,
                    labels,
                    root / "blocked",
                    "dataset-vaspkit-bands-002",
                    energy_offset_ev=0.0,
                    energy_reference_description="",
                )

    def test_structure_views_parameterize_graphical_connectivity(self) -> None:
        from dftpost.structure_views import render_structure_views

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            poscar = root / "POSCAR"
            poscar.write_text(
                "synthetic two-element cell\n"
                "1.0\n"
                "3.0 0.0 0.0\n0.0 3.0 0.0\n0.0 0.0 5.0\n"
                "C O\n1 1\nDirect\n"
                "0.0 0.0 0.0\n0.5 0.5 0.0\n"
            )
            result = render_structure_views(
                [poscar],
                root / "views",
                bond_mode="explicit",
                explicit_bond_limits={frozenset(("C", "O")): 2.3},
                element_colors={"C": "#555555", "O": "#ff0d0d"},
                element_radii_angstrom={"C": 0.70, "O": 0.60},
            )
            metadata = json.loads(result["metadata"].read_text())
            self.assertEqual(metadata["bond_mode"], "explicit")
            self.assertEqual(metadata["structures"][0]["source_atom_count"], 2)
            self.assertGreater(metadata["structures"][0]["displayed_site_count"], 2)
            self.assertEqual(metadata["views"], ["top-[001]", "side-[010]"])
            self.assertGreater(result["figures"][0].stat().st_size, 0)
            self.assertGreater(result["overview"].stat().st_size, 0)

            default_result = render_structure_views(
                [poscar],
                root / "default-views",
                bond_mode="covalent",
            )
            default_metadata = json.loads(default_result["metadata"].read_text())
            self.assertEqual(default_metadata["display_radius_source"], "0.55 * ASE covalent radius")
            self.assertLess(default_metadata["element_radii_angstrom"]["C"], 0.5)
            self.assertLess(default_metadata["element_radii_angstrom"]["O"], 0.5)

    def test_neb_and_optical_generic_tables_keep_mapping_and_maturity_explicit(self) -> None:
        from dftpost.neb_optical import normalize_neb_table, normalize_optical_table

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            neb_source = root / "neb-fixture.csv"
            neb_source.write_text(
                "coordinate,energy,max_force\n"
                "0.0,0.0,0.10\n0.5,1.2,0.05\n1.0,0.2,0.02\n"
            )
            neb = normalize_neb_table(
                neb_source,
                "qe",
                root / "neb-out",
                "dataset-neb-synthetic-001",
                coordinate_column="coordinate",
                energy_column="energy",
                coordinate_unit="dimensionless",
                energy_unit="eV",
                reference="initial",
                force_column="max_force",
                force_unit="eV/angstrom",
            )
            neb_analysis = json.loads(neb["analysis"].read_text())
            neb_dataset = json.loads(neb["dataset"].read_text())
            self.assertEqual(validation_errors("dataset", neb_dataset), [])
            self.assertEqual(neb_dataset["maturity"], "synthetic-validated")
            self.assertAlmostEqual(neb_analysis["forward_barrier"], 1.2)
            self.assertAlmostEqual(neb_analysis["reverse_barrier"], 1.0)

            optical_source = root / "optical-fixture.csv"
            optical_source.write_text(
                "energy,xx_re,xx_im,zz_re,zz_im\n"
                "0.5,2.0,0.1,1.5,0.2\n"
                "1.0,2.5,0.5,1.7,0.4\n"
                "2.0,1.5,1.0,2.0,0.8\n"
            )
            optical = normalize_optical_table(
                optical_source,
                "vasp",
                root / "optical-out",
                "dataset-optical-synthetic-001",
                energy_column="energy",
                components={"xx": ("xx_re", "xx_im"), "zz": ("zz_re", "zz_im")},
                broadening_declaration="synthetic fixture; no physical broadening",
            )
            optical_analysis = json.loads(optical["analysis"].read_text())
            optical_dataset = json.loads(optical["dataset"].read_text())
            self.assertEqual(validation_errors("dataset", optical_dataset), [])
            self.assertEqual(optical_dataset["maturity"], "synthetic-validated")
            self.assertEqual(optical_analysis["component_count"], 2)
            self.assertGreater(optical_analysis["component_extrema"]["xx"]["absorption_max_cm_1"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
