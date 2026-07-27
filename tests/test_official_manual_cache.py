from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
MODULE_PATH = ROOT / "tools" / "sync_official_manual_cache.py"
SPEC = importlib.util.spec_from_file_location("sync_official_manual_cache", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
manual_cache = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = manual_cache
SPEC.loader.exec_module(manual_cache)


class OfficialManualCacheTests(unittest.TestCase):
    def test_inventory_covers_every_registered_skill_pack(self) -> None:
        records = manual_cache.discover_records(ROOT)
        skill_ids = {record.skill_id for record in records}
        self.assertEqual(26, len(skill_ids))
        self.assertGreaterEqual(len(records), 450)
        self.assertIn("qe-rigorous-calculations", skill_ids)
        self.assertIn("vasp-rigorous-calculations", skill_ids)
        self.assertIn("cp2k-rigorous-calculations", skill_ids)
        by_source_id = {record.source_id: record for record in records}
        self.assertEqual("guide", by_source_id["mace-foundation-models-page"].source_kind)
        self.assertEqual("index", by_source_id["mace-rtd-search-index"].source_kind)

    def test_lossless_source_fence_preserves_unicode_and_backticks(self) -> None:
        source = "标题 αβ\\n```\\nMesh.Cutoff 300 Ry\\n"
        result = manual_cache.fenced_source(source, "text")
        self.assertIn(source.rstrip(), result)
        self.assertNotIn("\ufffd", result)
        self.assertTrue(result.startswith("````"))

    def test_html_cleanup_and_control_normalization_are_readable(self) -> None:
        cleaned = manual_cache.strip_noncontent_html(
            "<html><style>.noise{color:red}</style><body><h1>Manual</h1>"
            "<script>bad()</script><p>正文</p></body></html>"
        )
        self.assertNotIn("noise", cleaned)
        self.assertNotIn("bad()", cleaned)
        self.assertIn("Manual", cleaned)
        normalized, changed = manual_cache.normalize_visible_controls(
            "item\x88 text\f equation\x0f"
        )
        self.assertTrue(changed)
        self.assertIn("item• text", normalized)
        self.assertIn("source page break U+000C", normalized)
        self.assertIn("⟦source-control-U+000F⟧", normalized)
        self.assertFalse(
            any(
                manual_cache.unicodedata.category(character) == "Cc"
                and character not in "\n\r\t"
                for character in normalized
            )
        )
        pretty = manual_cache.pretty_json_source('{"β":[1,2],"a":true}')
        self.assertIsNotNone(pretty)
        assert pretty is not None
        self.assertIn('"β": [\n    1,\n    2', pretty)
        self.assertEqual(
            {"a": True, "β": [1, 2]},
            json.loads("\n".join(pretty.splitlines()[1:-1])),
        )

    def test_cache_validation_rejects_changed_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cache = Path(temporary)
            document = cache / "skill" / "authority" / "page.md"
            document.parent.mkdir(parents=True)
            document.write_text("# readable\\n中文 α\\n", encoding="utf-8")
            manifest = {
                "schema_version": "1.0",
                "entries": [
                    {
                        "markdown_path": "skill/authority/page.md",
                        "markdown_bytes": document.stat().st_size,
                        "markdown_sha256": manual_cache.sha256_file(document),
                    }
                ],
            }
            (cache / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            manual_cache.validate_cache(cache)
            document.write_text("# changed\\n", encoding="utf-8")
            with self.assertRaises(manual_cache.CacheError):
                manual_cache.validate_cache(cache)

    def test_repository_pinned_html2md_identity_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            executable = Path(temporary) / "html2md"
            executable.write_text(
                "#!/bin/sh\nprintf '%s\\n' "
                "'{\"upstream_url\":\"https://example.invalid\",\"git_commit\":\"bad\"}'\n",
                encoding="utf-8",
            )
            executable.chmod(0o755)
            with self.assertRaises(manual_cache.CacheError):
                manual_cache.html2md_identity(str(executable))

    def test_exact_repository_archive_and_manual_tree_filter(self) -> None:
        self.assertEqual(
            "https://codeload.github.com/org/repo/tar.gz/" + "a" * 40,
            manual_cache.archive_url("https://github.com/org/repo", "a" * 40),
        )
        self.assertTrue(manual_cache.manual_tree_entry("docs/user-guide/run.rst"))
        self.assertTrue(manual_cache.manual_tree_entry("doc/README"))
        self.assertFalse(manual_cache.manual_tree_entry("doc/images/logo.svg"))
        self.assertFalse(manual_cache.manual_tree_entry("src/engine.cpp"))
        self.assertEqual(
            Path("docs/index.rst.md"),
            manual_cache.markdown_tree_path(Path("docs/index.rst")),
        )
        self.assertEqual(
            Path("docs/index.md"),
            manual_cache.markdown_tree_path(Path("docs/index.md")),
        )

    def test_manual_tree_links_are_local_when_mirrored_and_official_otherwise(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            first = Path("skill/authority/tree/docs/first.md")
            second = Path("skill/authority/tree/docs/second.md")
            formula = Path("skill/authority/tree/docs/formula.md")
            (target / first).parent.mkdir(parents=True)
            (target / first).write_text(
                "[local](second.rst#details) [license](../LICENSE)\n"
                "[![logo](assets/logo.png)](second.rst#logo)\n"
                "![ORCID][orcid logo]\n"
                "[orcid logo]: assets/orcid.svg\n"
                r"\left[1-x\right](\vec{p}\bullet\vec{r})" + "\n"
                "```markdown\n[example](second.rst)\n```\n",
                encoding="utf-8",
            )
            (target / second).write_text("# Details\n", encoding="utf-8")
            (target / formula).write_text(
                r"\left[1-x\right](\vec{p}\bullet\vec{r})" + "\n",
                encoding="utf-8",
            )
            results = [
                {
                    "conversion": "identity-markdown",
                    "markdown_path": first.as_posix(),
                    "official_source": (
                        "https://github.com/org/repo/blob/" + "a" * 40 + "/docs/first.md"
                    ),
                },
                {
                    "conversion": "rst",
                    "markdown_path": second.as_posix(),
                    "official_source": (
                        "https://github.com/org/repo/blob/" + "a" * 40 + "/docs/second.rst"
                    ),
                },
                {
                    "conversion": "rst",
                    "markdown_path": formula.as_posix(),
                    "official_source": (
                        "https://github.com/org/repo/blob/" + "a" * 40 + "/docs/formula.rst"
                    ),
                },
            ]
            manual_cache.rewrite_tree_internal_links(
                target,
                {
                    "docs/first.md": first,
                    "docs/second.rst": second,
                    "docs/formula.rst": formula,
                },
                results,
            )
            text = (target / first).read_text(encoding="utf-8")
            formula_text = (target / formula).read_text(encoding="utf-8")
        self.assertIn("[local](second.md#details)", text)
        self.assertIn(
            "[![logo](https://github.com/org/repo/blob/"
            + "a" * 40
            + "/docs/assets/logo.png)](second.md#logo)",
            text,
        )
        self.assertIn(
            "[license](https://github.com/org/repo/blob/"
            + "a" * 40
            + "/LICENSE)",
            text,
        )
        self.assertIn(
            "[orcid logo]: https://github.com/org/repo/blob/"
            + "a" * 40
            + "/docs/assets/orcid.svg",
            text,
        )
        self.assertIn("[example](second.rst)", text)
        self.assertIn(r"\left[1-x\right]\(\vec{p}\bullet\vec{r})", text)
        self.assertEqual(
            r"\left[1-x\right]\(\vec{p}\bullet\vec{r})" + "\n",
            formula_text,
        )
        self.assertEqual(2, results[0]["internal_link_rewrite_count"])
        self.assertEqual(3, results[0]["external_official_link_rewrite_count"])

    def test_known_raw_snapshot_link_rewrites_to_exact_official_url(self) -> None:
        rewritten, count = manual_cache.rewrite_known_official_links(
            "- Raw: [source](official-raw/INPUT_PW.txt)\n"
            "```markdown\n[example](official-raw/INPUT_PW.txt)\n```\n",
            current_path="official-manual-pw-index.md",
            official_urls={
                "official-raw/INPUT_PW.txt": (
                    "https://www.quantum-espresso.org/Doc/INPUT_PW.txt"
                )
            },
        )
        self.assertEqual(1, count)
        self.assertIn(
            "[source](https://www.quantum-espresso.org/Doc/INPUT_PW.txt)",
            rewritten,
        )
        self.assertIn("[example](official-raw/INPUT_PW.txt)", rewritten)

    def test_github_blob_uses_exact_raw_transport(self) -> None:
        self.assertEqual(
            "https://raw.githubusercontent.com/org/repo/" + "a" * 40 + "/docs/run.md",
            manual_cache.retrieval_transport_url(
                "https://github.com/org/repo/blob/" + "a" * 40 + "/docs/run.md"
            ),
        )
        self.assertEqual(
            "https://github.com/org/repo/tree/v1/docs",
            manual_cache.retrieval_transport_url(
                "https://github.com/org/repo/tree/v1/docs"
            ),
        )
        self.assertEqual(
            ("https://github.com/org/repo", "a" * 40, "docs"),
            manual_cache.github_tree_spec(
                "https://github.com/org/repo/tree/" + "a" * 40 + "/docs"
            ),
        )
        self.assertEqual(
            "https://api.github.com/repos/org/repo/contents/docs/run.md?ref=" + "a" * 40,
            manual_cache.github_api_raw_url(
                "https://raw.githubusercontent.com/org/repo/"
                + "a" * 40
                + "/docs/run.md"
            ),
        )
        tree_record = manual_cache.SourceRecord(
            skill_id="example",
            authority_id="official",
            source_id="code-tree",
            title="AutoAPI source tree",
            source_kind="source-documentation",
            locator="https://github.com/org/repo/tree/" + "a" * 40 + "/src",
            retrieval_method="git-object",
            raw_bytes=1,
            raw_sha256="0" * 64,
        )
        self.assertTrue(manual_cache.is_exact_repository_tree_record(tree_record))

    def test_pinned_archive_recovers_unique_registered_receipt_when_locator_is_stale(self) -> None:
        body = b"official license body\n"
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "source.tar.gz"
            with tarfile.open(archive, "w:gz") as handle:
                info = tarfile.TarInfo("repo-commit/LICENSE.md")
                info.size = len(body)
                handle.addfile(info, io.BytesIO(body))
            recovered, path = manual_cache.find_registered_receipt_in_archive(
                archive,
                expected_path="LICENSE",
                expected_bytes=len(body),
                expected_sha256=manual_cache.sha256_bytes(body),
            )
            exact = manual_cache.read_exact_path_from_archive(archive, "LICENSE.md")
        self.assertEqual(body, recovered)
        self.assertEqual("LICENSE.md", path)
        self.assertEqual(body, exact)

    def test_fetch_uses_curl_before_python_https_when_available(self) -> None:
        body = b"# official manual\n"
        record = manual_cache.SourceRecord(
            skill_id="example",
            authority_id="official",
            source_id="manual",
            title="Manual",
            source_kind="manual",
            locator="https://raw.githubusercontent.com/org/repo/" + "a" * 40 + "/manual.md",
            retrieval_method="https-get",
            raw_bytes=len(body),
            raw_sha256=manual_cache.sha256_bytes(body),
        )

        def fake_run(argv: list[str], **_: object) -> object:
            output = Path(argv[argv.index("--output") + 1])
            output.write_bytes(body)
            return type("Result", (), {"returncode": 0, "stdout": b"", "stderr": b""})()

        with (
            mock.patch.object(manual_cache.shutil, "which", return_value="/usr/bin/curl"),
            mock.patch.object(manual_cache, "github_api_has_capacity", return_value=True),
            mock.patch.object(manual_cache.subprocess, "run", side_effect=fake_run),
            mock.patch.object(
                manual_cache,
                "urlopen",
                side_effect=AssertionError("Python HTTPS must be a fallback"),
            ),
        ):
            data, status, locator = manual_cache.fetch_bytes(
                record,
                allow_live_drift=False,
            )
        self.assertEqual(body, data)
        self.assertEqual("verified-registered-receipt-via-official-api", status)
        self.assertEqual(record.locator, locator)

    def test_pinned_official_api_receipt_mismatch_is_explicit_drift_when_allowed(self) -> None:
        body = b"# actual pinned official manual\n"
        record = manual_cache.SourceRecord(
            skill_id="example",
            authority_id="official",
            source_id="manual",
            title="Manual",
            source_kind="manual",
            locator="https://raw.githubusercontent.com/org/repo/" + "a" * 40 + "/manual.md",
            retrieval_method="git-object",
            raw_bytes=len(body),
            raw_sha256="0" * 64,
        )

        def fake_run(argv: list[str], **_: object) -> object:
            output = Path(argv[argv.index("--output") + 1])
            output.write_bytes(body)
            return type("Result", (), {"returncode": 0, "stdout": b"", "stderr": b""})()

        with (
            mock.patch.object(manual_cache.shutil, "which", return_value="/usr/bin/curl"),
            mock.patch.object(manual_cache, "github_api_has_capacity", return_value=True),
            mock.patch.object(manual_cache.subprocess, "run", side_effect=fake_run),
            mock.patch.object(
                manual_cache,
                "recover_registered_github_blob",
                side_effect=AssertionError("drift must not be disguised as archive recovery"),
            ),
        ):
            data, status, locator = manual_cache.fetch_bytes(
                record,
                allow_live_drift=True,
            )
        self.assertEqual(body, data)
        self.assertEqual("registered-receipt-mismatch-at-pinned-official-source", status)
        self.assertEqual(record.locator, locator)

    def test_authority_repository_recovers_registered_readthedocs_source(self) -> None:
        body = b"official guide body\n"
        record = manual_cache.SourceRecord(
            skill_id="example",
            authority_id="official-docs",
            source_id="guide",
            title="Guide",
            source_kind="guide",
            locator="https://example.readthedocs.io/en/latest/_sources/guide.rst.txt",
            retrieval_method="https-get",
            raw_bytes=len(body),
            raw_sha256=manual_cache.sha256_bytes(body),
        )
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "source.tar.gz"
            with tarfile.open(archive, "w:gz") as handle:
                info = tarfile.TarInfo("repo-commit/docs/guide.rst")
                info.size = len(body)
                handle.addfile(info, io.BytesIO(body))
            with mock.patch.object(manual_cache, "cached_archive", return_value=archive):
                recovered = manual_cache.recover_registered_receipt_from_repositories(
                    record,
                    (("https://github.com/org/repo", "a" * 40),),
                )
        self.assertIsNotNone(recovered)
        assert recovered is not None
        data, locator = recovered
        self.assertEqual(body, data)
        self.assertEqual(
            "https://github.com/org/repo/blob/" + "a" * 40 + "/docs/guide.rst",
            locator,
        )


if __name__ == "__main__":
    unittest.main()
