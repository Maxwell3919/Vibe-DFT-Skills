#!/usr/bin/env python3
"""Unit tests for the deterministic VASP skill scripts."""

from __future__ import annotations

import csv
import json
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
import sync_official_wiki  # noqa: E402


class ConvergenceTests(unittest.TestCase):
    def test_stable_tail(self) -> None:
        rows = [
            {"x": 300.0, "y": -9.0},
            {"x": 400.0, "y": -9.08},
            {"x": 500.0, "y": -9.0995},
            {"x": 600.0, "y": -9.1000},
            {"x": 700.0, "y": -9.1002},
        ]
        result = analyze_convergence.analyze(rows, abs_tol=0.001, rel_tol=0.0, min_tail=3)
        self.assertEqual(result["status"], "candidate_found")
        self.assertEqual(result["candidate_x"], 500.0)

    def test_csv_duplicate_x_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "series.csv"
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["x", "y"])
                writer.writeheader()
                writer.writerows([{"x": 1, "y": 2}, {"x": 1, "y": 3}])
            with self.assertRaises(ValueError):
                analyze_convergence.load_series(path, "x", "y")


class AuditTests(unittest.TestCase):
    def make_case(self, root: Path, incar: str) -> Path:
        root.joinpath("INCAR").write_text(incar)
        root.joinpath("POSCAR").write_text(
            "Si\n1.0\n1 0 0\n0 1 0\n0 0 1\nSi\n2\nDirect\n0 0 0\n0.25 0.25 0.25\n"
        )
        root.joinpath("KPOINTS").write_text("mesh\n0\nGamma\n6 6 6\n0 0 0\n")
        root.joinpath("POTCAR").write_text(
            "TITEL = PAW_PBE Si 05Jan2001\nLEXCH = PE\nENMAX = 245.000; ENMIN = 180.000\n"
        )
        return root

    def test_consistent_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\nEDIFF=1E-6\nISMEAR=0\nSIGMA=0.05\n")
            result = audit_vasp_case.audit(case)
            self.assertEqual(result["summary"]["errors"], 0)
            self.assertEqual(result["files"]["POTCAR"]["datasets"], 1)
            self.assertNotIn("POTCAR", json.dumps(result["files"]["POTCAR"]["titles"]))

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

    def test_poscar_coordinate_count_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            case = self.make_case(Path(directory), "ENCUT=400\n")
            case.joinpath("POSCAR").write_text(
                "Si\n1.0\n1 0 0\n0 1 0\n0 0 1\nSi\n2\nDirect\n0 0 0\n"
            )
            with self.assertRaisesRegex(ValueError, "declares 2 atoms but contains 1 coordinate rows"):
                audit_vasp_case.audit(case)

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
