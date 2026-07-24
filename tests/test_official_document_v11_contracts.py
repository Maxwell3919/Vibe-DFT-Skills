from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
sys.path.insert(0, str(ROOT / "tools"))

import validate_contract  # noqa: E402


ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64
FOUR = "4" * 64


def file_identity(path: str, digest: str = ONE, size: int = 32) -> dict[str, object]:
    return {
        "path": path,
        "sha256": digest,
        "bytes": size,
    }


def processor() -> dict[str, object]:
    return {
        "processor_id": "catalog-builder",
        "processor_version": "1.0",
        "assurance_mode": "pinned",
        "implementation_ref": file_identity("tools/catalog_builder.py", ONE),
        "configuration_ref": file_identity("config/catalog.json", TWO),
        "dependency_lock_ref": file_identity("config/dependencies.lock", THREE),
        "input_sha256": ZERO,
        "output_sha256": FOUR,
        "attestation_id": None,
        "deterministic": True,
    }


def embedded_content(path: str = "content/manual.txt") -> dict[str, object]:
    return {
        "content_mode": "embedded-content",
        "locator": path,
        "sha256": ONE,
        "bytes": 128,
    }


def external_content() -> dict[str, object]:
    return {
        "content_mode": "external-content",
        "locator": "https://docs.example.org/manual.html",
        "receipt": {
            "retrieval_method": "https-get",
            "retrieved_utc": "2026-07-24T00:00:00Z",
            "raw_sha256": TWO,
            "raw_bytes": 256,
        },
    }


def metadata_content() -> dict[str, object]:
    return {
        "content_mode": "metadata-only",
        "locator": "https://docs.example.org/index.json",
        "identity": {
            "sha256": THREE,
            "bytes": 64,
        },
    }


def excluded_content() -> dict[str, object]:
    return {
        "content_mode": "excluded",
        "locator": "https://docs.example.org/navigation.html",
        "inventory_entry_identity": {
            "sha256": FOUR,
            "bytes": 48,
        },
    }


def selector(label: str) -> dict[str, object]:
    return {
        "selector_id": label,
        "layer": "raw-source",
        "kind": "whole-source",
        "value": "*",
        "subject_ids": ["subject-one"],
        "loss_ids": [],
    }


def catalog_record() -> dict[str, object]:
    return {
        "schema_version": "1.1",
        "contract_name": "official-document-source-catalog",
        "authority_id": "sample-docs",
        "provider_id": "sample-provider",
        "authority_root": "https://docs.example.org/",
        "version_scope": {
            "kind": "exact",
            "value": "2.4.0",
            "retrieved_utc": None,
            "snapshot_identity": None,
        },
        "authority_revision": "release-2.4.0",
        "upstream_universe_complete": True,
        "inventory_locator": "https://docs.example.org/index.json",
        "inventory_identity": {
            "sha256": ZERO,
            "bytes": 1024,
        },
        "discovery_processor": processor(),
        "discovered_sources": {
            "doc-embedded": {
                "disposition": "included",
                "title": "Embedded manual",
                "source_kind": "manual-page",
                "content": embedded_content(),
                "selectors": [selector("selector-embedded")],
                "subject_ids": ["subject-one"],
                "loss_ids": [],
            },
            "doc-external": {
                "disposition": "included",
                "title": "External manual",
                "source_kind": "reference-page",
                "content": external_content(),
                "selectors": [selector("selector-external")],
                "subject_ids": ["subject-one"],
                "loss_ids": [],
            },
            "doc-metadata": {
                "disposition": "included",
                "title": "Metadata entry",
                "source_kind": "api-record",
                "content": metadata_content(),
                "selectors": [],
                "subject_ids": [],
                "loss_ids": [],
            },
            "doc-excluded": {
                "disposition": "excluded",
                "title": "Navigation entry",
                "source_kind": "index",
                "content": excluded_content(),
                "reason_code": "navigation-only",
                "rationale": "The entry contains navigation only.",
            },
        },
        "subjects": {
            "subject-one": {
                "title": "Input parameter",
                "category": "input-parameter",
                "requirement_strength": "required",
                "statement": "The parameter has a documented form.",
            }
        },
        "losses": {},
        "limitations": [],
        "blockers": [],
    }


def corpus_record() -> dict[str, object]:
    catalog = catalog_record()
    sources = catalog["discovered_sources"]
    assert isinstance(sources, dict)
    source_inventory: dict[str, object] = {}
    for source_id, source in sources.items():
        assert isinstance(source, dict)
        if source["disposition"] == "included":
            source_inventory[source_id] = {
                "disposition": "included",
                "title": source["title"],
                "source_kind": source["source_kind"],
                "source_identity": copy.deepcopy(source["content"]),
                "subject_ids": copy.deepcopy(source["subject_ids"]),
                "loss_ids": copy.deepcopy(source["loss_ids"]),
            }
        else:
            source_inventory[source_id] = {
                "disposition": "excluded",
                "title": source["title"],
                "source_kind": source["source_kind"],
                "source_identity": copy.deepcopy(source["content"]),
                "reason_code": source["reason_code"],
                "rationale": source["rationale"],
            }
    return {
        "schema_version": "1.1",
        "contract_name": "official-corpus-manifest",
        "corpus_id": "sample-corpus",
        "authority_id": "sample-docs",
        "provider_id": "sample-provider",
        "version_scope": copy.deepcopy(catalog["version_scope"]),
        "status": "complete",
        "discovery": {
            "method": "official-index",
            "upstream_universe_complete": True,
            "inventory_scope": "upstream-universe",
            "authority_root": "https://docs.example.org/",
            "authority_revision": "release-2.4.0",
            "inventory_format": "source-map-v2",
            "inventory": embedded_content("inventory/source-map.json"),
            "processor": processor(),
        },
        "source_inventory": source_inventory,
        "blockers": [],
        "limitations": [],
        "producer": {
            "skill_id": "sample-skill",
            "skill_version": "1.0",
            "tool_id": "catalog-builder",
            "tool_version": "1.0",
            "generated_utc": "2026-07-24T00:00:00Z",
        },
    }


def loss_accounting() -> dict[str, object]:
    return {
        "closure_status": "complete",
        "entries": [],
    }


def slice_processor() -> dict[str, object]:
    return {
        "processor_id": "slice-builder",
        "processor_version": "1.0",
        "assurance_mode": "pinned",
        "input_sha256": ZERO,
        "output_sha256": ONE,
        "deterministic": True,
        "attestations": [
            {
                "attestation_id": "implementation-one",
                "kind": "implementation",
                "artifact": file_identity("tools/slice_builder.py", TWO),
            }
        ],
    }


def embedded_slice_content() -> dict[str, object]:
    return {
        "content_mode": "embedded-content",
        "artifact": file_identity("content/slice-embedded.txt", ONE, 16),
        "hash_basis": "exact-artifact-bytes",
    }


def external_slice_content() -> dict[str, object]:
    return {
        "content_mode": "external-content",
        "locator": "https://docs.example.org/manual.html",
        "receipt": {
            "retrieval_method": "https-get",
            "retrieved_utc": "2026-07-24T00:00:00Z",
            "raw_sha256": TWO,
            "raw_bytes": 256,
            "selected_content": {
                "sha256": THREE,
                "bytes": 24,
            },
        },
        "hash_basis": "external-receipt-bytes",
    }


def metadata_slice_content() -> dict[str, object]:
    return {
        "content_mode": "metadata-only",
        "locator": "https://docs.example.org/index.json",
        "identity": {
            "sha256": FOUR,
            "bytes": 12,
        },
        "hash_basis": "metadata-identity-bytes",
    }


def slice_record() -> dict[str, object]:
    return {
        "schema_version": "1.1",
        "contract_name": "document-slice-manifest",
        "slice_manifest_id": "sample-slices",
        "corpus_ref": {
            "corpus_id": "sample-corpus",
            "sha256": ZERO,
        },
        "status": "complete",
        "sources": {
            "doc-embedded": {
                "source_identity": embedded_content(),
                "raw_source_extent_bytes": 128,
                "processor": slice_processor(),
                "slices": [
                    {
                        "slice_id": "slice-embedded",
                        "selector": {
                            "layer": "raw-source",
                            "kind": "whole-source",
                            "value": "*",
                        },
                        "raw_byte_range": {
                            "start_byte": 0,
                            "byte_count": 16,
                        },
                        "content": embedded_slice_content(),
                        "subject_ids": ["subject-one"],
                        "loss_accounting": loss_accounting(),
                    },
                    {
                        "slice_id": "slice-external",
                        "selector": {
                            "layer": "raw-source",
                            "kind": "byte-range",
                            "value": "16:24",
                        },
                        "raw_byte_range": {
                            "start_byte": 16,
                            "byte_count": 24,
                        },
                        "content": external_slice_content(),
                        "subject_ids": ["subject-one"],
                        "loss_accounting": loss_accounting(),
                    },
                    {
                        "slice_id": "slice-metadata",
                        "selector": {
                            "layer": "raw-source",
                            "kind": "byte-range",
                            "value": "40:12",
                        },
                        "raw_byte_range": {
                            "start_byte": 40,
                            "byte_count": 12,
                        },
                        "content": metadata_slice_content(),
                        "subject_ids": [],
                        "loss_accounting": loss_accounting(),
                    },
                ],
                "source_loss_accounting": loss_accounting(),
            }
        },
        "blockers": [],
        "limitations": [],
        "producer": {
            "skill_id": "sample-skill",
            "skill_version": "1.0",
            "tool_id": "slice-builder",
            "tool_version": "1.0",
            "generated_utc": "2026-07-24T00:00:00Z",
        },
    }


def coverage_record() -> dict[str, object]:
    return {
        "schema_version": "1.1",
        "contract_name": "skill-document-coverage",
        "coverage_id": "sample-coverage",
        "skill_id": "sample-skill",
        "status": {
            "overall": "complete",
            "corpus": "complete",
            "slices": "complete",
            "scope": "complete",
            "mappings": "complete",
        },
        "corpus_refs": [
            {
                "corpus_id": "sample-corpus",
                "sha256": ZERO,
            }
        ],
        "slice_manifest_refs": [
            {
                "slice_manifest_id": "sample-slices",
                "sha256": ONE,
            }
        ],
        "scope_inventory_ref": {
            "inventory_id": "sample-scope",
            "sha256": TWO,
        },
        "mappings": {
            "subject-one": {
                "mapping_status": "complete",
                "disposition": "covered",
                "slice_refs": [
                    {
                        "slice_manifest_id": "sample-slices",
                        "slice_id": "slice-embedded",
                    }
                ],
                "rationale": None,
                "limitations": [],
            }
        },
        "blockers": [],
        "limitations": [],
        "producer": {
            "skill_id": "sample-skill",
            "skill_version": "1.0",
            "tool_id": "coverage-builder",
            "tool_version": "1.0",
            "generated_utc": "2026-07-24T00:00:00Z",
        },
    }


class OfficialDocumentV11ContractTests(unittest.TestCase):
    def validation_errors(self, selector_name: str, value: object) -> list[str]:
        return validate_contract.validation_errors(
            selector_name,
            value,
            CONTRACTS,
        )

    def assert_valid(self, selector_name: str, value: object) -> None:
        self.assertEqual(self.validation_errors(selector_name, value), [])

    def assert_invalid(self, selector_name: str, value: object) -> None:
        self.assertNotEqual(self.validation_errors(selector_name, value), [])

    def test_dynamic_catalog_loads_both_versions(self) -> None:
        catalog = validate_contract.load_catalog(CONTRACTS)
        names = (
            "official-document-source-catalog",
            "official-corpus-manifest",
            "document-slice-manifest",
            "skill-document-coverage",
        )
        for name in names:
            with self.subTest(name=name):
                versions = tuple(item.version for item in catalog.by_name[name])
                self.assertEqual(versions, ("1.0", "1.1"))
                self.assertEqual(catalog.resolve(f"{name}@1.0").version, "1.0")
                self.assertEqual(catalog.resolve(f"{name}@1.1").version, "1.1")
                with self.assertRaises(validate_contract.ContractSelectionError):
                    catalog.resolve(name)

    def test_valid_embedded_external_and_metadata_records(self) -> None:
        self.assert_valid("official-document-source-catalog@1.1", catalog_record())
        self.assert_valid("official-corpus-manifest@1.1", corpus_record())
        self.assert_valid("document-slice-manifest@1.1", slice_record())
        self.assert_valid("skill-document-coverage@1.1", coverage_record())

    def test_partition_is_a_tagged_total_map(self) -> None:
        malformed = catalog_record()
        source = malformed["discovered_sources"]["doc-excluded"]
        source["disposition"] = "included"
        self.assert_invalid("official-document-source-catalog@1.1", malformed)

        malformed = corpus_record()
        source = malformed["source_inventory"]["doc-embedded"]
        source["disposition"] = "excluded"
        self.assert_invalid("official-corpus-manifest@1.1", malformed)

        malformed = catalog_record()
        source = malformed["discovered_sources"]["doc-metadata"]
        source["content"] = excluded_content()
        self.assert_invalid("official-document-source-catalog@1.1", malformed)

    def test_raw_range_and_digest_shapes_fail_closed(self) -> None:
        malformed = slice_record()
        malformed["sources"]["doc-embedded"]["slices"][0]["raw_byte_range"][
            "byte_count"
        ] = 0
        self.assert_invalid("document-slice-manifest@1.1", malformed)

        malformed = slice_record()
        malformed["sources"]["doc-embedded"]["slices"][0]["content"]["artifact"][
            "sha256"
        ] = "bad"
        self.assert_invalid("document-slice-manifest@1.1", malformed)

        malformed = catalog_record()
        malformed["inventory_identity"]["sha256"] = "f" * 63
        self.assert_invalid("official-document-source-catalog@1.1", malformed)

    def test_content_mode_branches_cannot_be_mixed(self) -> None:
        malformed = catalog_record()
        content = malformed["discovered_sources"]["doc-embedded"]["content"]
        content["locator"] = "https://docs.example.org/manual.html"
        self.assert_invalid("official-document-source-catalog@1.1", malformed)

        malformed = slice_record()
        content = malformed["sources"]["doc-embedded"]["slices"][1]["content"]
        content["locator"] = "content/local.txt"
        self.assert_invalid("document-slice-manifest@1.1", malformed)

        malformed = slice_record()
        content = malformed["sources"]["doc-embedded"]["slices"][0]["content"]
        content["receipt"] = external_slice_content()["receipt"]
        self.assert_invalid("document-slice-manifest@1.1", malformed)

        malformed = slice_record()
        content = malformed["sources"]["doc-embedded"]["slices"][0]["content"]
        content["release_override"] = True
        self.assert_invalid("document-slice-manifest@1.1", malformed)

    def test_coverage_status_is_derived_from_dimensions(self) -> None:
        malformed = coverage_record()
        malformed["status"]["scope"] = "partial"
        self.assert_invalid("skill-document-coverage@1.1", malformed)

        partial = coverage_record()
        partial["status"]["scope"] = "partial"
        partial["status"]["overall"] = "partial"
        partial["limitations"] = ["Scope mapping is incomplete."]
        self.assert_valid("skill-document-coverage@1.1", partial)

        blocked = coverage_record()
        blocked["status"]["slices"] = "blocked"
        blocked["status"]["overall"] = "blocked"
        blocked["blockers"] = [
            {
                "code": "slice-gap",
                "description": "A required slice is absent.",
                "dimension": "slices",
            }
        ]
        self.assert_valid("skill-document-coverage@1.1", blocked)

    def test_coverage_accepts_only_technical_record_refs(self) -> None:
        malformed = coverage_record()
        extra_key = ("lic" + "ense") + "_review_refs"
        malformed[extra_key] = []
        self.assert_invalid("skill-document-coverage@1.1", malformed)

        schema = validate_contract.load_catalog(CONTRACTS).resolve(
            "skill-document-coverage@1.1"
        ).schema
        self.assertEqual(
            set(schema["properties"]),
            {
                "schema_version",
                "contract_name",
                "coverage_id",
                "skill_id",
                "status",
                "corpus_refs",
                "slice_manifest_refs",
                "scope_inventory_ref",
                "mappings",
                "blockers",
                "limitations",
                "producer",
            },
        )

    def test_new_files_exclude_policy_vocabulary(self) -> None:
        fragments = (
            ("lic", "ense"),
            ("le", "gal"),
            ("ri", "ghts"),
            ("te", "rms"),
            ("tr", "ust"),
            ("rev", "iewer"),
            ("redis", "tribution"),
            ("open", "-content"),
            ("embedded", "-open"),
        )
        tokens = tuple("".join(parts) for parts in fragments)
        paths = (
            CONTRACTS / "official-document-source-catalog-1.1.schema.json",
            CONTRACTS / "official-corpus-manifest-1.1.schema.json",
            CONTRACTS / "document-slice-manifest-1.1.schema.json",
            CONTRACTS / "skill-document-coverage-1.1.schema.json",
            Path(__file__),
        )
        for path in paths:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8").lower()
                self.assertEqual([token for token in tokens if token in text], [])


if __name__ == "__main__":
    unittest.main()
