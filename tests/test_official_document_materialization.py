from __future__ import annotations

import ast
import copy
from dataclasses import fields
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import official_document_materialization as materialization  # noqa: E402
import validate_contract  # noqa: E402


CONTENT = b"abcdefghij"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def request_fixture(*, mode: str = "materialize") -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "contract_name": "official-document-materialization-request",
        "request_id": "request-synthetic-001",
        "adapter_id": "explicit-user-materialization-v1",
        "authority_id": "synthetic-official-docs",
        "provider_id": "synthetic",
        "version": "1.0.0",
        "revision": "0123456789abcdef",
        "source_root": "https://example.invalid/docs/0123456789abcdef",
        "discovered_sources": ["guide-source", "excluded-source"],
        "included_sources": [
            {
                "source_id": "guide-source",
                "locator": (
                    "https://example.invalid/docs/0123456789abcdef/guide.txt"
                ),
                "import_path": "inputs/guide.txt",
                "raw_sha256": sha256(CONTENT),
                "raw_bytes": len(CONTENT),
                "media_type": "text/plain",
                "output_path": "raw/guide.txt",
                "preservation": {
                    "mode": "full-source",
                    "preserved_ranges": [],
                },
                "segments": [
                    {
                        "segment_id": "segment-alpha",
                        "ordinal": 0,
                        "byte_range": {"start": 0, "end": 4},
                        "output_path": "segments/alpha.txt",
                        "subject_ids": ["subject-alpha"],
                    },
                    {
                        "segment_id": "segment-beta",
                        "ordinal": 1,
                        "byte_range": {"start": 4, "end": 10},
                        "output_path": "segments/beta.txt",
                        "subject_ids": ["subject-beta"],
                    },
                ],
                "subject_ids": ["subject-alpha", "subject-beta"],
                "loss_ids": [],
            }
        ],
        "reviewed_exclusions": [
            {
                "source_id": "excluded-source",
                "disposition": "outside-requested-scope",
            }
        ],
        "subjects": [
            {
                "subject_id": "subject-alpha",
                "source_id": "guide-source",
                "segment_ids": ["segment-alpha"],
            },
            {
                "subject_id": "subject-beta",
                "source_id": "guide-source",
                "segment_ids": ["segment-beta"],
            },
        ],
        "losses": [],
        "content_mode": mode,
        "processor_lock": {
            "processor_id": "explicit-user-materialization-v1",
            "processor_version": "1.0",
            "range_semantics": "zero-based-half-open-v1",
            "byte_transform": "none",
        },
    }


def write_import_root(root: Path, content: bytes = CONTENT) -> Path:
    target = root / "inputs" / "guide.txt"
    target.parent.mkdir(parents=True)
    target.write_bytes(content)
    return target


def tree_snapshot(root: Path) -> dict[str, tuple[int, int, str]]:
    result: dict[str, tuple[int, int, str]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        status = path.lstat()
        digest = sha256(path.read_bytes()) if path.is_file() else ""
        result[relative] = (status.st_mode, status.st_size, digest)
    return result


def finding_codes(result: materialization.EvaluationResult) -> set[str]:
    return {finding.code for finding in result.findings}


class OfficialDocumentMaterializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = validate_contract.load_catalog(ROOT / "contracts")
        cls.request_contract = cls.catalog.resolve(
            "official-document-materialization-request@1.0"
        )
        cls.manifest_contract = cls.catalog.resolve(
            "official-document-artifact-manifest@1.0"
        )

    def test_catalog_discovers_both_closed_contracts(self) -> None:
        self.assertEqual(
            self.request_contract.document_kind,
            "projection",
        )
        self.assertEqual(
            self.manifest_contract.document_kind,
            "content-addressed-record",
        )
        self.assertEqual(
            self.manifest_contract.record_id_field,
            "manifest_id",
        )

    def test_materialize_happy_path_is_deterministic_and_read_only(self) -> None:
        request = request_fixture()
        with tempfile.TemporaryDirectory() as directory:
            import_root = Path(directory)
            write_import_root(import_root)
            before = tree_snapshot(import_root)

            first = materialization.evaluate_request(request, import_root)
            second = materialization.evaluate_request(
                copy.deepcopy(request),
                import_root,
            )

            self.assertEqual(first.exit_code, 0)
            self.assertEqual(first.findings, ())
            self.assertFalse(first.mutation_performed)
            self.assertEqual(first.artifact_manifest, second.artifact_manifest)
            self.assertEqual(dict(first.proposed_bytes), dict(second.proposed_bytes))
            self.assertEqual(tree_snapshot(import_root), before)
            self.assertEqual(
                dict(first.proposed_bytes),
                {
                    "raw/guide.txt": CONTENT,
                    "segments/alpha.txt": b"abcd",
                    "segments/beta.txt": b"efghij",
                },
            )
            self.assertEqual(len(first.artifacts), 3)

            validator = Draft202012Validator(
                self.manifest_contract.schema,
                registry=self.catalog.registry,
                format_checker=FormatChecker(),
            )
            self.assertEqual(
                list(validator.iter_errors(first.artifact_manifest)),
                [],
            )

    def test_preserved_ranges_and_loss_ledger_close_exactly(self) -> None:
        request = request_fixture()
        source = request["included_sources"][0]
        source["preservation"] = {
            "mode": "preserved-ranges",
            "preserved_ranges": [
                {"start": 0, "end": 4},
                {"start": 6, "end": 10},
            ],
        }
        source["segments"][1]["byte_range"] = {"start": 6, "end": 10}
        source["loss_ids"] = ["loss-middle"]
        request["losses"] = [
            {
                "loss_id": "loss-middle",
                "source_id": "guide-source",
                "byte_range": {"start": 4, "end": 6},
                "disposition": "excluded-from-segmentation",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            import_root = Path(directory)
            write_import_root(import_root)
            result = materialization.evaluate_request(request, import_root)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.proposed_bytes["segments/beta.txt"], b"ghij")

    def test_external_only_returns_zero_without_inspecting_import_root(self) -> None:
        request = request_fixture(mode="external-only")
        with mock.patch.object(
            materialization,
            "inspect_import_root",
            side_effect=AssertionError("import root must not be inspected"),
        ):
            result = materialization.evaluate_request(
                request,
                Path("/definitely/not/present"),
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.artifacts, ())
        self.assertIsNone(result.artifact_manifest)
        self.assertEqual(dict(result.proposed_bytes), {})
        self.assertFalse(result.mutation_performed)

    def test_corpus_partition_gap_and_overlap_fail(self) -> None:
        gap = request_fixture()
        gap["discovered_sources"] = ["guide-source"]
        self.assertIn(
            "CORPUS_PARTITION_GAP",
            finding_codes(materialization.evaluate_request(gap)),
        )

        overlap = request_fixture()
        overlap["reviewed_exclusions"][0]["source_id"] = "guide-source"
        result = materialization.evaluate_request(overlap)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("CORPUS_PARTITION_OVERLAP", finding_codes(result))

    def test_content_mode_is_structurally_required(self) -> None:
        missing = request_fixture()
        missing.pop("content_mode")
        result = materialization.evaluate_request(missing)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("REQUEST_SCHEMA_INVALID", finding_codes(result))

        unsupported = request_fixture()
        unsupported["content_mode"] = "automatic"
        result = materialization.evaluate_request(unsupported)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("REQUEST_SCHEMA_INVALID", finding_codes(result))

    def test_unsafe_import_paths_fail_before_read(self) -> None:
        for path in ("/absolute/guide.txt", "../guide.txt", "inputs/../guide.txt"):
            with self.subTest(path=path):
                request = request_fixture()
                request["included_sources"][0]["import_path"] = path
                result = materialization.evaluate_request(
                    request,
                    Path("/definitely/not/present"),
                )
                self.assertEqual(result.exit_code, 2)
                self.assertIn("REQUEST_SCHEMA_INVALID", finding_codes(result))

    def test_declared_size_and_hash_mismatches_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            import_root = Path(directory)
            target = write_import_root(import_root, CONTENT[:-1])

            bad_size = request_fixture()
            result = materialization.evaluate_request(bad_size, import_root)
            self.assertEqual(result.exit_code, 2)
            self.assertIn("IMPORT_PATH_SIZE_MISMATCH", finding_codes(result))

            target.write_bytes(CONTENT)
            bad_hash = request_fixture()
            bad_hash["included_sources"][0]["raw_sha256"] = "0" * 64
            result = materialization.evaluate_request(bad_hash, import_root)
            self.assertEqual(result.exit_code, 2)
            self.assertIn("IMPORT_PATH_HASH_MISMATCH", finding_codes(result))

    def test_symlink_and_hardlink_imports_are_rejected(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symbolic links unavailable")
        request = request_fixture()
        with tempfile.TemporaryDirectory() as directory:
            import_root = Path(directory)
            target = import_root / "target.txt"
            target.write_bytes(CONTENT)
            link = import_root / "inputs" / "guide.txt"
            link.parent.mkdir()
            link.symlink_to(target)
            result = materialization.evaluate_request(request, import_root)
            self.assertEqual(result.exit_code, 2)
            self.assertIn("IMPORT_PATH_SYMLINK", finding_codes(result))

        if not hasattr(os, "link"):
            self.skipTest("hard links unavailable")
        with tempfile.TemporaryDirectory() as directory:
            import_root = Path(directory)
            target = import_root / "target.txt"
            target.write_bytes(CONTENT)
            link = import_root / "inputs" / "guide.txt"
            link.parent.mkdir()
            os.link(target, link)
            result = materialization.evaluate_request(request, import_root)
            self.assertEqual(result.exit_code, 2)
            self.assertIn("IMPORT_PATH_HARDLINK", finding_codes(result))

    def test_segment_range_gap_and_overlap_are_distinct_failures(self) -> None:
        gap = request_fixture()
        gap["included_sources"][0]["segments"][1]["byte_range"]["start"] = 5
        result = materialization.evaluate_request(gap)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("SEGMENT_RANGE_GAP", finding_codes(result))

        overlap = request_fixture()
        overlap["included_sources"][0]["segments"][1]["byte_range"]["start"] = 3
        result = materialization.evaluate_request(overlap)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("SEGMENT_RANGE_OVERLAP", finding_codes(result))

    def test_subject_and_loss_ledgers_are_bidirectionally_closed(self) -> None:
        bad_subject = request_fixture()
        bad_subject["subjects"][0]["segment_ids"] = ["segment-beta"]
        result = materialization.evaluate_request(bad_subject)
        self.assertEqual(result.exit_code, 2)
        self.assertTrue(
            {
                "SUBJECT_SEGMENT_SOURCE_MISMATCH",
                "SEGMENT_SUBJECT_CLOSURE_INVALID",
            }.intersection(finding_codes(result))
        )

        bad_loss = request_fixture()
        bad_loss["included_sources"][0]["loss_ids"] = ["loss-middle"]
        bad_loss["losses"] = [
            {
                "loss_id": "loss-middle",
                "source_id": "guide-source",
                "byte_range": {"start": 4, "end": 6},
                "disposition": "excluded-from-segmentation",
            }
        ]
        result = materialization.evaluate_request(bad_loss)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("LOSS_RANGE_CLOSURE_INVALID", finding_codes(result))

    def test_planner_rejects_stale_inspection_without_payloads(self) -> None:
        request = request_fixture()
        stale = materialization.ImportInspection(
            (),
            (
                materialization.ImportedSource(
                    source_id="guide-source",
                    import_path="inputs/guide.txt",
                    raw_sha256="0" * 64,
                    raw_bytes=len(CONTENT),
                    media_type="text/plain",
                    content=CONTENT,
                ),
            ),
        )
        planned = materialization.plan_artifacts(request, stale)
        self.assertEqual(
            {finding.code for finding in planned.findings},
            {"IMPORTED_SOURCE_IDENTITY_MISMATCH"},
        )
        self.assertIsNone(planned.manifest)
        self.assertEqual(dict(planned.proposed_bytes), {})

    def test_all_failure_paths_report_zero_mutation(self) -> None:
        request = request_fixture()
        with tempfile.TemporaryDirectory() as directory:
            import_root = Path(directory)
            write_import_root(import_root, b"changed")
            before = tree_snapshot(import_root)
            result = materialization.evaluate_request(request, import_root)
            after = tree_snapshot(import_root)
        self.assertEqual(result.exit_code, 2)
        self.assertFalse(result.mutation_performed)
        self.assertEqual(before, after)

    def test_public_result_fields_do_not_encode_content_policy_semantics(self) -> None:
        field_names = {field.name for field in fields(materialization.EvaluationResult)}
        forbidden_fragments = {
            "license",
            "legal",
            "rights",
            "terms",
            "trust",
            "notice",
            "attribution",
            "reviewer",
        }
        self.assertFalse(
            {
                fragment
                for fragment in forbidden_fragments
                if any(fragment in name for name in field_names)
            }
        )

    def test_isolated_import_without_bytecode_environment_is_clean(self) -> None:
        module_source = (
            ROOT / "tools" / "official_document_materialization.py"
        ).read_text(encoding="utf-8")
        syntax = ast.parse(module_source)
        guard_lines = [
            node.lineno
            for node in syntax.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "sys"
                and target.attr == "dont_write_bytecode"
                for target in node.targets
            )
        ]
        later_import_lines = [
            node.lineno
            for node in syntax.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            and not (
                isinstance(node, ast.Import)
                and [alias.name for alias in node.names] == ["sys"]
            )
            and not (
                isinstance(node, ast.ImportFrom)
                and node.module == "__future__"
            )
        ]
        self.assertEqual(len(guard_lines), 1)
        self.assertLess(guard_lines[0], min(later_import_lines))

        with tempfile.TemporaryDirectory() as directory:
            isolated_root = Path(directory)
            tools = isolated_root / "tools"
            contracts = isolated_root / "contracts"
            tools.mkdir()
            contracts.mkdir()
            shutil.copy2(
                ROOT / "tools" / "official_document_materialization.py",
                tools,
            )
            for filename in (
                "official-document-materialization-request.schema.json",
                "official-document-artifact-manifest.schema.json",
            ):
                shutil.copy2(ROOT / "contracts" / filename, contracts)
            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            environment["PYTHONPATH"] = str(tools)
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        "import official_document_materialization as module; "
                        "assert module.sys.dont_write_bytecode"
                    ),
                ],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(isolated_root.rglob("*.pyc")), [])
            self.assertEqual(list(isolated_root.rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()
