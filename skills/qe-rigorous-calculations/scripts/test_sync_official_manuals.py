#!/usr/bin/env python3
"""Regression checks for the official QE manual mirror generator."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
MODULE_PATH = SCRIPT_DIR / "sync_official_manuals.py"

spec = importlib.util.spec_from_file_location("sync_official_manuals", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class OfficialMirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.references = SKILL_ROOT / "references"
        cls.manifest = json.loads((cls.references / "official-manifest.json").read_text(encoding="utf-8"))

    def check_html_input_manual(self, filename: str, expected_items: int, expected_sections: int) -> None:
        source = (self.references / "official-raw" / filename).read_text(encoding="utf-8")
        extracted = module.InputHtmlTextExtractor(source)
        sections = module.split_input_manual(extracted.text, extracted.item_labels, extracted.section_labels)
        item_sections = [section for section in sections if " — Item: " in section[1]]
        self.assertEqual(len(extracted.item_labels), expected_items, filename)
        self.assertEqual(len(extracted.section_labels), expected_sections, filename)
        self.assertEqual(len(item_sections), expected_items, filename)
        self.assertTrue(all(marker not in body for _, _, body in sections for marker in extracted.item_labels))

    def test_html_input_boundaries(self) -> None:
        self.check_html_input_manual("INPUT_PH.html", 70, 5)
        self.check_html_input_manual("INPUT_PP.html", 43, 2)
        source = (self.references / "official-raw" / "INPUT_PH.html").read_text(encoding="utf-8")
        extracted = module.InputHtmlTextExtractor(source)
        sections = module.split_input_manual(extracted.text, extracted.item_labels, extracted.section_labels)
        xq_title = next(title for _, title, _ in sections if title.endswith("Item: xq(1) xq(2) xq(3)"))
        atom_title = next(
            title for _, title, _ in sections if title.endswith("Item: atom(1) atom(2) ... atom(nat_todo)")
        )
        self.assertTrue(xq_title.startswith("LINE OF INPUT"), xq_title)
        self.assertTrue(atom_title.startswith("LINE OF INPUT"), atom_title)

    def test_txt_input_split_is_lossless(self) -> None:
        source = (self.references / "official-raw" / "INPUT_PW.txt").read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        sections = module.split_input_manual(source)
        self.assertEqual("".join(body for _, _, body in sections), source)
        self.assertEqual(
            sum(title.endswith("Variable: ecutrho") for _, title, _ in sections),
            1,
        )

    def test_release_note_split_is_lossless(self) -> None:
        source = (self.references / "official-raw" / "release-notes").read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        sections = module.split_release_notes(source)
        self.assertEqual("".join(body for _, _, body in sections), source)
        self.assertGreater(len(sections), 100)

    def test_guide_extraction_removes_noncontent(self) -> None:
        guide = next(item for item in self.manifest["user_guides"] if item["id"] == "pw")
        page = next(item for item in guide["pages"] if "troubleshooting" in item["title"].lower())
        source = (self.references / page["raw_file"]).read_text(encoding="utf-8")
        text = module.GuideTextExtractor(source).text
        self.assertIn("Troubleshooting", text)
        self.assertNotIn("<script", text.lower())
        self.assertNotIn("<style", text.lower())

    def test_pdf_page_extraction_matches_manifest(self) -> None:
        record = next(item for item in self.manifest["pdf_manuals"] if item["name"] == "constraints_HOWTO.pdf")
        page_count, pages = module.extract_pdf_pages(self.references / record["raw_file"])
        self.assertEqual(page_count, record["page_count"])
        self.assertEqual(len(pages), record["page_count"])

    def test_cached_fetch_preserves_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            raw_path = Path(tempdir) / "source.txt"
            raw_path.write_bytes(b"official-cache")
            metadata = {
                "url": "https://www.quantum-espresso.org/Doc/source.txt",
                "content_type": "text/plain",
                "last_modified": "Mon, 01 Jan 2024 00:00:00 GMT",
                "retrieved_utc": "2024-01-02T00:00:00+00:00",
                "sha256": hashlib.sha256(b"official-cache").hexdigest(),
            }
            fetched = module.cached_fetch(metadata["url"], raw_path, metadata)
            self.assertTrue(fetched.from_cache)
            self.assertEqual(fetched.retrieved_utc, metadata["retrieved_utc"])
            self.assertEqual(fetched.last_modified, metadata["last_modified"])
            self.assertEqual(fetched.content_type, metadata["content_type"])

    def test_cached_fetch_rejects_untracked_content_change(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            raw_path = Path(tempdir) / "source.txt"
            raw_path.write_bytes(b"changed")
            metadata = {
                "url": "https://www.quantum-espresso.org/Doc/source.txt",
                "content_type": "text/plain",
                "last_modified": None,
                "retrieved_utc": "2024-01-02T00:00:00+00:00",
                "sha256": hashlib.sha256(b"original").hexdigest(),
            }
            with self.assertRaisesRegex(RuntimeError, "hash does not match"):
                module.cached_fetch(metadata["url"], raw_path, metadata)

    def test_cache_only_sync_preserves_source_retrieval_time(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            copied_root = Path(tempdir) / SKILL_ROOT.name
            shutil.copytree(SKILL_ROOT, copied_root)
            before = json.loads((copied_root / "references" / "official-manifest.json").read_text(encoding="utf-8"))
            module.sync(copied_root)
            after = json.loads((copied_root / "references" / "official-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(after["retrieval_mode"], "cache")
            self.assertEqual(after["retrieved_utc"], before["retrieved_utc"])
            self.assertGreaterEqual(after["generated_utc"], before["generated_utc"])
            before_pw = next(item for item in before["input_manuals"] if item["name"] == "INPUT_PW")
            after_pw = next(item for item in after["input_manuals"] if item["name"] == "INPUT_PW")
            self.assertEqual(after_pw["last_modified"], before_pw["last_modified"])
            self.assertEqual(after_pw["retrieved_utc"], before_pw["retrieved_utc"])

    def test_failed_build_preserves_existing_references(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill_root = Path(tempdir) / "qe-official-params"
            references = skill_root / "references"
            references.mkdir(parents=True)
            sentinel = references / "sentinel.txt"
            sentinel.write_text("working mirror", encoding="utf-8")
            with mock.patch.object(module, "_build_in_place", side_effect=RuntimeError("simulated fetch failure")):
                with self.assertRaisesRegex(RuntimeError, "simulated fetch failure"):
                    module.sync(skill_root, refresh=True)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "working mirror")

    def test_integrity_check_uses_discovery_not_snapshot_counts(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        for obsolete_guard in ("!= 36", "!= 95", "!= 11", 'get("INPUT_PH") != 76', 'get("INPUT_PP") != 46'):
            self.assertNotIn(obsolete_guard, source)

    def test_skill_requires_version_mismatch_disclosure(self) -> None:
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Version Gate", skill_text)
        self.assertIn("do not project the current manual backward", skill_text)
        self.assertIn("Exact behavior for QE <version> is not verified", skill_text)


def main() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OfficialMirrorTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
