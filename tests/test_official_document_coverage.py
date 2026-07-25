from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import validate_contract  # noqa: E402
import validate_official_document_coverage as validator  # noqa: E402


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def loaded(path: str, data: dict[str, object]) -> validator.LoadedRecord:
    raw = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return validator.LoadedRecord(
        path=Path(path),
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        data=data,
    )


def loss(loss_id: str, *, severity: str = "non-blocking") -> dict[str, object]:
    return {
        "loss_id": loss_id,
        "disposition": "accepted",
        "severity": severity,
        "rationale": "Synthetic technical fixture.",
    }


def external_identity() -> dict[str, object]:
    return {
        "content_mode": "external-content",
        "locator": "https://docs.example.org/manual.html",
        "receipt": {
            "retrieval_method": "https-get",
            "retrieved_utc": "2026-07-25T00:00:00Z",
            "raw_sha256": SHA_A,
            "raw_bytes": 4,
        },
    }


def external_slice(
    *,
    layer: str = "raw-source",
    kind: str = "byte-range",
    selected_sha256: str = SHA_B,
    selected_bytes: int = 2,
    slice_losses: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if kind == "whole-source":
        raw_range = {"start_byte": 0, "byte_count": 4}
        selector_value = "*"
    else:
        raw_range = {"start_byte": 0, "byte_count": 2}
        selector_value = "0:2"
    return {
        "slice_id": "slice-one",
        "selector": {
            "layer": layer,
            "kind": kind,
            "value": selector_value,
        },
        "raw_byte_range": raw_range,
        "content": {
            "content_mode": "external-content",
            "locator": "https://docs.example.org/manual.html",
            "receipt": {
                "retrieval_method": "https-get",
                "retrieved_utc": "2026-07-25T00:00:00Z",
                "raw_sha256": SHA_A,
                "raw_bytes": 4,
                "selected_content": {
                    "sha256": selected_sha256,
                    "bytes": selected_bytes,
                },
            },
            "hash_basis": "external-receipt-bytes",
        },
        "subject_ids": [],
        "loss_accounting": {
            "closure_status": "complete",
            "entries": copy.deepcopy(slice_losses or []),
        },
    }


def slice_bundle(
    *,
    slice_item: dict[str, object] | None = None,
    source_losses: list[dict[str, object]] | None = None,
) -> tuple[validator.LoadedRecord, validator.LoadedRecord]:
    source_loss_entries = copy.deepcopy(source_losses or [])
    identity = external_identity()
    corpus_data: dict[str, object] = {
        "schema_version": "1.1",
        "contract_name": "official-corpus-manifest",
        "corpus_id": "corpus-one",
        "status": "partial",
        "source_inventory": {
            "source-one": {
                "disposition": "included",
                "source_identity": copy.deepcopy(identity),
                "subject_ids": [],
                "loss_ids": [
                    item["loss_id"] for item in source_loss_entries
                ],
            }
        },
    }
    corpus = loaded("corpus.json", corpus_data)
    slices = [copy.deepcopy(slice_item or external_slice())]
    accounting = {
        "closure_status": "complete",
        "entries": source_loss_entries,
    }
    processor_output = canonical_sha256(
        {
            "slices": slices,
            "source_loss_accounting": accounting,
        }
    )
    slice_data: dict[str, object] = {
        "schema_version": "1.1",
        "contract_name": "document-slice-manifest",
        "slice_manifest_id": "slices-one",
        "corpus_ref": {
            "corpus_id": "corpus-one",
            "sha256": corpus.raw_sha256,
        },
        "status": "partial",
        "sources": {
            "source-one": {
                "source_identity": identity,
                "raw_source_extent_bytes": 4,
                "processor": {
                    "processor_id": "fixture-processor",
                    "processor_version": "1.0",
                    "assurance_mode": "unverified",
                    "input_sha256": SHA_A,
                    "output_sha256": processor_output,
                    "deterministic": True,
                    "attestations": [],
                },
                "slices": slices,
                "source_loss_accounting": accounting,
            }
        },
        "blockers": [],
    }
    return corpus, loaded("slices.json", slice_data)


def slice_findings(
    *,
    slice_item: dict[str, object] | None = None,
    source_losses: list[dict[str, object]] | None = None,
) -> list[validator.Finding]:
    corpus, slices = slice_bundle(
        slice_item=slice_item,
        source_losses=source_losses,
    )
    findings: list[validator.Finding] = []
    validator._slice_manifest_findings(
        slices,
        corpora={"corpus-one": corpus},
        authorities={},
        authority_projection={},
        consumer_registry={"processors": {}},
        consumer_registry_sha256=SHA_C,
        source_root=ROOT,
        repository_root=ROOT,
        findings=findings,
    )
    return findings


def minimal_coverage(
    *,
    blockers: list[dict[str, object]] | None = None,
    producer_skill_id: object = "sample-skill",
) -> validator.LoadedRecord:
    return loaded(
        "coverage.json",
        {
            "coverage_id": "coverage-one",
            "skill_id": "sample-skill",
            "status": {
                "overall": "complete",
                "corpus": "complete",
                "slices": "complete",
                "scope": "complete",
                "mappings": "complete",
            },
            "corpus_refs": [],
            "slice_manifest_refs": [],
            "scope_inventory_ref": {
                "inventory_id": "scope-one",
                "sha256": SHA_A,
            },
            "mappings": {},
            "blockers": copy.deepcopy(blockers or []),
            "producer": {"skill_id": producer_skill_id},
        },
    )


def coverage_findings(
    record: validator.LoadedRecord,
) -> list[validator.Finding]:
    findings: list[validator.Finding] = []
    validator._coverage_findings(
        record,
        corpora={},
        slice_manifests={},
        scope_inventories={},
        consumer_registry={"bindings": []},
        consumer_registry_sha256=SHA_C,
        repository_root=ROOT,
        findings=findings,
    )
    return findings


class FourRecordInterfaceTests(unittest.TestCase):
    def test_validate_files_has_exact_four_record_inputs(self) -> None:
        parameters = inspect.signature(validator.validate_files).parameters
        record_inputs = {
            name
            for name in parameters
            if name.endswith("_path") or name.endswith("_paths")
        }
        self.assertEqual(
            record_inputs,
            {
                "corpus_paths",
                "slice_paths",
                "scope_inventory_path",
                "coverage_path",
            },
        )

    def test_active_contract_selectors_are_the_four_record_protocol(self) -> None:
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        selectors = (
            "official-corpus-manifest@1.1",
            "document-slice-manifest@1.1",
            "skill-document-scope-inventory@1.0",
            "skill-document-coverage@1.1",
        )
        for selector in selectors:
            with self.subTest(selector=selector):
                name, version = selector.rsplit("@", 1)
                contract = catalog.resolve(selector)
                self.assertEqual((contract.name, contract.version), (name, version))

    def test_cli_rejects_removed_fifth_record_option(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "validate_official_document_coverage.py"),
                "--corpus",
                "corpus.json",
                "--slices",
                "slices.json",
                "--scope-inventory",
                "scope.json",
                "--coverage",
                "coverage.json",
                "--license-review",
                "legacy.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments: --license-review", result.stderr)


class StrictRecordLoadingTests(unittest.TestCase):
    def test_duplicate_key_and_nonfinite_number_are_strictly_rejected(self) -> None:
        cases = {
            "duplicate": b'{"corpus_id":"one","corpus_id":"two"}',
            "nan": b'{"corpus_id":"one","value":NaN}',
        }
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for label, raw in cases.items():
                with self.subTest(label=label):
                    path = directory / f"{label}.json"
                    path.write_bytes(raw)
                    records, findings = validator._load_records(
                        [path],
                        catalog=catalog,
                        selector="official-corpus-manifest@1.1",
                        id_field="corpus_id",
                        label="corpus",
                    )
                    self.assertEqual(records, [])
                    self.assertEqual(
                        {finding.code for finding in findings},
                        {"STRICT_JSON_INVALID"},
                    )

    def test_invalid_producer_is_reported_at_exact_field(self) -> None:
        cases = (None, 7, "another-skill")
        for producer_skill_id in cases:
            with self.subTest(producer_skill_id=producer_skill_id):
                findings = coverage_findings(
                    minimal_coverage(producer_skill_id=producer_skill_id)
                )
                producer_findings = [
                    finding
                    for finding in findings
                    if finding.code == "COVERAGE_PRODUCER_INVALID"
                ]
                self.assertEqual(len(producer_findings), 1)
                self.assertTrue(
                    producer_findings[0].location.endswith(
                        "producer/skill_id"
                    )
                )


class SelectorIdentityTests(unittest.TestCase):
    def test_source_identity_projection_is_exact_and_bool_safe(self) -> None:
        cases = (
            (
                {
                    "content_mode": "embedded-content",
                    "sha256": SHA_A,
                    "bytes": 4,
                },
                (SHA_A, 4),
            ),
            (external_identity(), (SHA_A, 4)),
            (
                {
                    "content_mode": "metadata-only",
                    "identity": {"sha256": SHA_B, "bytes": 2},
                },
                (SHA_B, 2),
            ),
            (
                {
                    "content_mode": "metadata-only",
                    "identity": {"sha256": SHA_B, "bytes": True},
                },
                None,
            ),
        )
        for identity, expected in cases:
            with self.subTest(mode=identity["content_mode"], expected=expected):
                self.assertEqual(
                    validator._slice_source_identity_projection(identity),
                    expected,
                )

    def test_external_receipt_requires_selected_identity(self) -> None:
        item = external_slice()
        del item["content"]["receipt"]["selected_content"]
        findings = slice_findings(slice_item=item)
        self.assertIn(
            "SLICE_CONTENT_INVALID",
            {finding.code for finding in findings},
        )
        self.assertTrue(
            any(
                finding.location.endswith(
                    "/content/receipt/selected_content"
                )
                for finding in findings
            )
        )

    def test_raw_whole_source_selected_identity_matches_source(self) -> None:
        bad = external_slice(
            kind="whole-source",
            selected_sha256=SHA_B,
            selected_bytes=4,
        )
        good = external_slice(
            kind="whole-source",
            selected_sha256=SHA_A,
            selected_bytes=4,
        )
        bad_codes = {finding.code for finding in slice_findings(slice_item=bad)}
        good_messages = {
            finding.message for finding in slice_findings(slice_item=good)
        }
        self.assertIn("SLICE_CONTENT_EXTERNAL_MISMATCH", bad_codes)
        self.assertFalse(
            any(
                "whole-source selection must match source raw identity"
                in message
                for message in good_messages
            )
        )

    def test_derived_whole_source_is_rejected(self) -> None:
        item = external_slice(
            layer="derived-artifact",
            kind="whole-source",
            selected_sha256=SHA_A,
            selected_bytes=4,
        )
        findings = slice_findings(slice_item=item)
        self.assertTrue(
            any(
                finding.code == "SLICE_SELECTOR_INVALID"
                and "cannot target derived-artifact" in finding.message
                for finding in findings
            )
        )

    def test_derived_range_may_have_independent_selected_hash(self) -> None:
        item = external_slice(
            layer="derived-artifact",
            selected_sha256=SHA_B,
            selected_bytes=2,
        )
        findings = slice_findings(slice_item=item)
        self.assertFalse(
            any(
                finding.code == "SLICE_CONTENT_EXTERNAL_MISMATCH"
                and "selected_content" in finding.location
                for finding in findings
            )
        )


class BlockerAndLossClosureTests(unittest.TestCase):
    def test_blocker_dimensions_are_the_exact_four_allowed_values(self) -> None:
        for dimension in ("corpus", "slices", "scope", "mappings"):
            with self.subTest(dimension=dimension):
                findings = coverage_findings(
                    minimal_coverage(
                        blockers=[
                            {
                                "blocker_id": f"block-{dimension}",
                                "dimension": dimension,
                                "code": "TECHNICAL_GAP",
                                "message": "Synthetic technical blocker.",
                            }
                        ]
                    )
                )
                self.assertNotIn(
                    "COVERAGE_BLOCKERS_INVALID",
                    {finding.code for finding in findings},
                )

    def test_unknown_or_missing_blocker_dimension_is_rejected(self) -> None:
        for blocker in (
            {"blocker_id": "missing"},
            {"blocker_id": "unknown", "dimension": "all"},
            {"blocker_id": "many", "dimension": ["corpus", "slices"]},
        ):
            with self.subTest(blocker=blocker):
                findings = coverage_findings(
                    minimal_coverage(blockers=[blocker])
                )
                self.assertIn(
                    "COVERAGE_BLOCKERS_INVALID",
                    {finding.code for finding in findings},
                )

    def test_loss_union_must_equal_source_loss_set(self) -> None:
        source_loss = loss("loss-one")
        findings = slice_findings(source_losses=[source_loss])
        self.assertIn(
            "SLICE_LOSS_COVERAGE_INCOMPLETE",
            {finding.code for finding in findings},
        )

        closed_item = external_slice(slice_losses=[source_loss])
        closed_findings = slice_findings(
            slice_item=closed_item,
            source_losses=[source_loss],
        )
        self.assertNotIn(
            "SLICE_LOSS_COVERAGE_INCOMPLETE",
            {finding.code for finding in closed_findings},
        )

    def test_loss_union_rejects_unknown_and_nonidentical_entries(self) -> None:
        source_loss = loss("loss-one")
        cases = (
            [loss("loss-two")],
            [loss("loss-one", severity="blocking")],
        )
        for slice_losses in cases:
            with self.subTest(slice_losses=slice_losses):
                findings = slice_findings(
                    slice_item=external_slice(slice_losses=slice_losses),
                    source_losses=[source_loss],
                )
                self.assertIn(
                    "SLICE_LOSS_ENTRY_MISMATCH",
                    {finding.code for finding in findings},
                )

    def test_blocking_loss_caps_accounting(self) -> None:
        findings: list[validator.Finding] = []
        ceiling = validator._slice_loss_accounting_ceiling(
            {
                "closure_status": "complete",
                "entries": [loss("loss-one", severity="blocking")],
            },
            dimension="source/slice/loss",
            location="slices/source/slice/loss_accounting",
            findings=findings,
        )
        self.assertEqual(ceiling, "blocked")
        self.assertEqual(findings, [])


class ExactQueryAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = {
            "allowed_https_origins": ["https://docs.example.org"],
            "content_policy": {
                "allowed_path_prefixes": ["/api/"],
                "query_policy": "exact-allowlist",
                "allowed_query_urls": [
                    "https://docs.example.org/api/index?format=json&page=1"
                ],
                "fragment_policy": "forbidden",
            },
        }

    def test_exact_query_allowlist_is_byte_exact(self) -> None:
        cases = {
            "https://docs.example.org/api/index?format=json&page=1": True,
            "https://docs.example.org/api/index?page=1&format=json": False,
            "https://docs.example.org/api/index?format=json&page=2": False,
            "https://docs.example.org/api/index?format=json&page=1#top": False,
            "http://docs.example.org/api/index?format=json&page=1": False,
            "https://user@docs.example.org/api/index?format=json&page=1": False,
            "https://docs.example.org:444/api/index?format=json&page=1": False,
            "https://other.example.org/api/index?format=json&page=1": False,
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(
                    validator._url_matches_authority(url, self.authority),
                    expected,
                )

    def test_query_forbidden_rejects_every_query(self) -> None:
        authority = copy.deepcopy(self.authority)
        authority["content_policy"]["query_policy"] = "forbidden"
        authority["content_policy"]["allowed_query_urls"] = []
        self.assertTrue(
            validator._url_matches_authority(
                "https://docs.example.org/api/index",
                authority,
            )
        )
        self.assertFalse(
            validator._url_matches_authority(
                "https://docs.example.org/api/index?format=json",
                authority,
            )
        )


if __name__ == "__main__":
    unittest.main()
