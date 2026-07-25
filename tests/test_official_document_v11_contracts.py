from __future__ import annotations

import copy
import types
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
sys.path.insert(0, str(ROOT / "tools"))

import validate_contract  # noqa: E402
import build_official_document_packs as builder  # noqa: E402


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
        "selected_identity": {
            "sha256": ONE,
            "bytes": 1024,
        },
        "subject_ids": ["subject-one"],
        "loss_ids": [],
    }


def qe_compact_manifest() -> dict[str, object]:
    manuals = []
    for ordinal in range(35):
        section_count = 33 + (1 if ordinal < 4 else 0)
        sections = [
            {
                "order": section_index,
                "section_id": f"prefix-{ordinal}-{section_index}",
                "title": "Prefix",
                "selected_sha256": THREE,
                "selected_bytes": 17,
                "payload_hash_basis": (
                    "utf-8 bytes of the fenced text payload after "
                    "removing the single wrapper separator newline"
                ),
                "wrapper_sha256": FOUR,
                "wrapper_bytes": 64,
            }
            for section_index in range(section_count)
        ]
        manuals.append(
            {
                "name": f"INPUT_{ordinal + 1:02d}",
                "version": "7.5",
                "url": (
                    "https://www.quantum-espresso.org/Doc/"
                    f"INPUT_{ordinal + 1:02d}_LD1.html"
                ),
                "retrieved_utc": "2026-07-24T00:00:00Z",
                "raw_sha256": ONE,
                "raw_bytes": 512,
                "sections": sections,
            }
        )
    manuals.append(
        {
            "name": "INPUT_LD1",
            "version": "7.4",
            "url": (
                "https://www.quantum-espresso.org/Doc/INPUT_LD1.html"
            ),
            "retrieved_utc": "2026-07-24T00:00:00Z",
            "raw_sha256": ONE,
            "raw_bytes": 512,
            "sections": [
                {
                    "order": 0,
                    "section_id": "ld1-excluded",
                    "title": "LD1",
                    "selected_sha256": THREE,
                    "selected_bytes": 17,
                    "payload_hash_basis": (
                        "utf-8 bytes of the fenced text payload after "
                        "removing the single wrapper separator newline"
                    ),
                    "wrapper_sha256": FOUR,
                    "wrapper_bytes": 64,
                },
            ],
        }
    )
    return {
        "schema_version": "1.0",
        "contract_name": "qe-source-pack-input",
        "catalog_type": "qe-input-manifest-metadata-v1",
        "skill_id": "qe-rigorous-calculations",
        "source_root": "https://www.quantum-espresso.org/Doc/",
        "retrieved_utc": "2026-07-24T00:00:00Z",
        "legacy_manifest_sha256": TWO,
        "manuals": manuals,
        "limitations": ["test limitation"],
    }


def vasp_compact_manifest() -> dict[str, object]:
    pages: list[dict[str, object]] = []
    for pageid in range(1, 82):
        pages.append(
            {
                "pageid": pageid,
                "revid": 9000 + pageid,
                "title": "VASP Section",
                "url": (
                    f"https://www.vasp.at/wiki/index.php/VASP_Section_{pageid}"
                ),
                "api_request_url": (
                    "https://www.vasp.at/w/api.php?action=parse&page=VASP_Section"
                ),
                "raw_json_sha256": ONE,
                "raw_json_bytes": 128 + pageid,
                "wikitext_sha256": TWO,
                "wikitext_bytes": 64 + pageid,
            }
        )
    return {
        "schema_version": "1.0",
        "contract_name": "vasp-source-pack-input",
        "catalog_type": "vasp-wiki-page-metadata-v1",
        "skill_id": "vasp-rigorous-calculations",
        "official_root": "https://www.vasp.at/",
        "api_url": "https://www.vasp.at/w/api.php",
        "pages": pages,
        "retrieved_utc": "2026-07-24T00:00:00Z",
        "legacy_manifest_sha256": TWO,
        "limitations": ["test limitation"],
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
                "selectors": [
                    {
                        **selector("selector-embedded"),
                        "selected_identity": {
                            "sha256": ONE,
                            "bytes": 128,
                        },
                    }
                ],
                "subject_ids": ["subject-one"],
                "loss_ids": [],
            },
            "doc-external": {
                "disposition": "included",
                "title": "External manual",
                "source_kind": "reference-page",
                "content": external_content(),
                "selectors": [
                    {
                        **selector("selector-external"),
                        "selected_identity": {
                            "sha256": TWO,
                            "bytes": 256,
                        },
                    }
                ],
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

    def _build_context(self) -> builder.BuildContext:
        return builder.BuildContext(
            root=Path("/tmp").resolve(),
            snapshot=types.SimpleNamespace(),
            skill_id="sample-skill",
            skill_root=ROOT,
            seed_path=ROOT / "tests" / "seed.json",
            seed={"providers": [{"input_id": "one"}]},
        )

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

    def test_selector_selected_identity_required(self) -> None:
        malformed = catalog_record()
        malformed["discovered_sources"]["doc-embedded"]["selectors"][0].pop(
            "selected_identity"
        )
        self.assert_invalid("official-document-source-catalog@1.1", malformed)

        malformed = catalog_record()
        malformed["discovered_sources"]["doc-embedded"]["selectors"][0][
            "selected_identity"
        ]["bytes"] = 0
        self.assert_invalid("official-document-source-catalog@1.1", malformed)

    def test_slice_from_catalog_selected_identity_exact_contract(self) -> None:
        context = self._build_context()
        provider = {"input_id": "one"}
        source = {"source_id": "source-one"}
        identity = {
            "content_mode": "external-content",
            "locator": "https://docs.example.org/manual.html",
            "receipt": {
                "retrieval_method": "https-get",
                "retrieved_utc": "2026-07-24T00:00:00Z",
                "raw_sha256": TWO,
                "raw_bytes": 128,
            },
        }
        with self.assertRaises(builder.PackBuildError):
            builder._slice_from_catalog(
                context=context,
                provider=provider,
                source=source,
                identity=identity,
                selector={
                    "selector_id": "external-byte-range",
                    "layer": "raw-source",
                    "kind": "byte-range",
                    "value": "16:32",
                    "subject_ids": [],
                    "loss_ids": [],
                    "selected_identity": {
                        "sha256": ONE,
                    },
                },
                raw_source_extent_bytes=128,
            )
        with self.assertRaises(builder.PackBuildError):
            builder._slice_from_catalog(
                context=context,
                provider=provider,
                source=source,
                identity=identity,
                selector={
                    "selector_id": "external-byte-range",
                    "layer": "raw-source",
                    "kind": "byte-range",
                    "value": "16:32",
                    "subject_ids": [],
                    "loss_ids": [],
                    "selected_identity": {
                        "sha256": ONE,
                        "bytes": False,
                    },
                },
                raw_source_extent_bytes=128,
            )
        with self.assertRaises(builder.PackBuildError):
            builder._slice_from_catalog(
                context=context,
                provider=provider,
                source=source,
                identity=identity,
                selector={
                    "selector_id": "external-byte-range",
                    "layer": "raw-source",
                    "kind": "byte-range",
                    "value": "16:32",
                    "subject_ids": [],
                    "loss_ids": [],
                    "selected_identity": {
                        "sha256": ONE,
                        "bytes": 32,
                        "extra": "ignore",
                    },
                },
                raw_source_extent_bytes=128,
            )

    def test_qe_adapter_selector_includes_selected_identity(self) -> None:
        manifest = qe_compact_manifest()
        catalog_bytes = builder.canonical_json_bytes(manifest)
        catalog_ref = {
            "path": "references/qe-manifest.json",
            "sha256": builder.sha256_bytes(catalog_bytes),
            "bytes": len(catalog_bytes),
        }
        context = builder.BuildContext(
            root=ROOT,
            snapshot=types.SimpleNamespace(),
            skill_id="qe-rigorous-calculations",
            skill_root=ROOT,
            seed_path=ROOT / "tests" / "seed.json",
            seed={"providers": [{"input_id": "one"}]},
        )
        captured: dict[str, dict[str, object]] = {}
        expected_subject = "qe-subject"

        def _read_catalog(_context, _ref, *, label):  # noqa: ARG001
            return ROOT / "tests" / "seed.json", catalog_bytes

        original_slice = builder._slice_from_catalog

        def _traced_slice(*args, **kwargs):
            selector = kwargs["selector"]
            if "selector" not in captured:
                captured["selector"] = copy.deepcopy(selector)
            return original_slice(*args, **kwargs)

        provider = {
            "input_id": "one",
            "authority_id": "sample-authority",
            "provider_id": "sample-provider",
            "adapter_id": "qe-input-manifest-v1",
            "source_ref": catalog_ref,
            "options_ref": catalog_ref,
        }
        with mock.patch.object(builder, "_read_catalog_ref", side_effect=_read_catalog), \
             mock.patch.object(
                 builder,
                 "_scope_catalog",
                 return_value={
                     "subjects": [
                         {
                             "subject_id": expected_subject,
                             "evidence_class": "official-provider-required",
                             "provider_input_ids": ["one"],
                             "statement": "qetest",
                         }
                     ],
                 },
             ), \
             mock.patch.object(
                 builder,
                 "_authority",
                 return_value=(
                     {
                         "provider_id": "sample-provider",
                         "lifecycle": "active",
                     },
                     {"version_scopes": []},
                 ),
             ), \
             mock.patch.object(builder, "_attest_replayed_catalog", return_value=None), \
             mock.patch.object(builder, "_require_registered_version_scope", return_value=None), \
             mock.patch.object(builder, "_slice_from_catalog", side_effect=_traced_slice):
            build = builder._qe_adapter(context, provider)

        self.assertEqual(
            captured["selector"]["selected_identity"],
            {
                "sha256": THREE,
                "bytes": 17,
            },
        )
        self.assertGreater(len(build.slice_sources), 0)

    def test_vasp_adapter_selector_includes_selected_identity(self) -> None:
        manifest = vasp_compact_manifest()
        catalog_bytes = builder.canonical_json_bytes(manifest)
        catalog_ref = {
            "path": "references/vasp-manifest.json",
            "sha256": builder.sha256_bytes(catalog_bytes),
            "bytes": len(catalog_bytes),
        }
        context = builder.BuildContext(
            root=ROOT,
            snapshot=types.SimpleNamespace(),
            skill_id="vasp-rigorous-calculations",
            skill_root=ROOT,
            seed_path=ROOT / "tests" / "seed.json",
            seed={"providers": [{"input_id": "one"}]},
        )
        captured: dict[str, dict[str, object]] = {}
        tag_subject = builder._safe_id("vasp-safe-tag", "VASP Section")

        def _read_catalog(_context, _ref, *, label):  # noqa: ARG001
            return ROOT / "tests" / "seed.json", catalog_bytes

        original_slice = builder._slice_from_catalog

        def _traced_slice(*args, **kwargs):
            selector = kwargs["selector"]
            if "selector" not in captured:
                captured["selector"] = copy.deepcopy(selector)
            return original_slice(*args, **kwargs)

        provider = {
            "input_id": "one",
            "authority_id": "sample-authority",
            "provider_id": "sample-provider",
            "adapter_id": "vasp-wiki-manifest-v1",
            "source_ref": catalog_ref,
            "options_ref": catalog_ref,
        }
        with mock.patch.object(builder, "_read_catalog_ref", side_effect=_read_catalog), \
             mock.patch.object(
                 builder,
                 "_scope_catalog",
                 return_value={
                     "subjects": [
                         {
                             "subject_id": tag_subject,
                             "evidence_class": "official-provider-required",
                             "provider_input_ids": ["one"],
                             "statement": "VASP section",
                         }
                     ],
                 },
             ), \
             mock.patch.object(
                 builder,
                 "_authority",
                 return_value=(
                     {
                         "provider_id": "sample-provider",
                         "lifecycle": "active",
                     },
                     {"version_scopes": []},
                 ),
             ), \
             mock.patch.object(builder, "_attest_replayed_catalog", return_value=None), \
             mock.patch.object(builder, "_require_registered_version_scope", return_value=None), \
             mock.patch.object(builder, "_slice_from_catalog", side_effect=_traced_slice):
            build = builder._vasp_adapter(context, provider)

        self.assertEqual(
            captured["selector"]["selected_identity"],
            {
                "sha256": ONE,
                "bytes": 129,
            },
        )
        self.assertEqual(len(build.slice_sources), 162)

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

    def test_selector_smoke_cases(self) -> None:
        context = self._build_context()
        provider = {"input_id": "one"}
        source = {"source_id": "source-one"}
        external_identity = {
            "content_mode": "external-content",
            "locator": "https://docs.example.org/manual.html",
            "receipt": {
                "retrieval_method": "https-get",
                "retrieved_utc": "2026-07-24T00:00:00Z",
                "raw_sha256": TWO,
                "raw_bytes": 128,
            },
        }

        with self.assertRaises(builder.PackBuildError):
            builder._slice_from_catalog(
                context=context,
                provider=provider,
                source=source,
                identity=external_identity,
                selector={
                    "selector_id": "external-whole-mismatch",
                    "layer": "raw-source",
                    "kind": "whole-source",
                    "value": "*",
                    "selected_identity": {
                        "sha256": ONE,
                        "bytes": 128,
                    },
                    "subject_ids": [],
                    "loss_ids": [],
                },
                raw_source_extent_bytes=128,
            )

        exact_nonwhole = builder._slice_from_catalog(
            context=context,
            provider=provider,
            source=source,
            identity=external_identity,
            selector={
                "selector_id": "external-byte-range",
                "layer": "raw-source",
                "kind": "byte-range",
                "value": "16:32",
                "selected_identity": {
                    "sha256": THREE,
                    "bytes": 32,
                },
                "subject_ids": [],
                "loss_ids": [],
            },
            raw_source_extent_bytes=128,
        )
        self.assertEqual(
            exact_nonwhole["content"]["identity"],
            {
                "sha256": THREE,
                "bytes": 32,
            },
        )
        self.assertEqual(
            exact_nonwhole["raw_byte_range"],
            {"start_byte": 16, "byte_count": 32},
        )
        self.assertEqual(
            exact_nonwhole["selector"],
            {
                "layer": "raw-source",
                "kind": "byte-range",
                "value": "16:32",
            },
        )

        with self.assertRaises(builder.PackBuildError):
            builder._slice_from_catalog(
                context=context,
                provider=provider,
                source=source,
                identity=external_identity,
                selector={
                    "selector_id": "external-pointer",
                    "layer": "raw-source",
                    "kind": "json-pointer",
                    "value": "/sections/intro",
                    "selected_identity": {
                        "sha256": FOUR,
                        "bytes": 16,
                    },
                    "subject_ids": [],
                    "loss_ids": [],
                },
                raw_source_extent_bytes=128,
            )

        derived_pointer = builder._slice_from_catalog(
            context=context,
            provider=provider,
            source=source,
            identity=external_identity,
            selector={
                "selector_id": "external-derived-pointer",
                "layer": "derived-artifact",
                "kind": "json-pointer",
                "value": "/sections/intro",
                "selected_identity": {
                    "sha256": FOUR,
                    "bytes": 16,
                },
                "subject_ids": [],
                "loss_ids": [],
            },
            raw_source_extent_bytes=128,
        )
        self.assertEqual(
            derived_pointer["content"]["identity"],
            {
                "sha256": FOUR,
                "bytes": 16,
            },
        )
        self.assertEqual(
            derived_pointer["raw_byte_range"],
            {"start_byte": 0, "byte_count": 128},
        )

        with self.assertRaises(builder.PackBuildError):
            builder._slice_from_catalog(
                context=context,
                provider=provider,
                source=source,
                identity={
                    "content_mode": "embedded-content",
                    "locator": "content/manual.txt",
                    "sha256": TWO,
                    "bytes": 128,
                },
                selector={
                    "selector_id": "embedded-mismatch",
                    "layer": "raw-source",
                    "kind": "whole-source",
                    "value": "*",
                    "selected_identity": {
                        "sha256": ONE,
                        "bytes": 128,
                    },
                    "subject_ids": [],
                    "loss_ids": [],
                },
                raw_source_extent_bytes=128,
            )

    def test_blocker_dimensions_isolated_by_corpus_and_slices(self) -> None:
        blockers = [
            {
                "code": "a-issue",
                "description": "A corpus issue.",
                "dimensions": ["corpus"],
            },
            {
                "code": "b-issue",
                "description": "A slices issue.",
                "dimensions": ["slices"],
            },
            {
                "code": "c-issue",
                "description": "A coverage issue.",
                "dimensions": ["coverage"],
            },
        ]
        self.assertEqual(
            builder._output_blockers(
                blockers,
                label="smoke",
                dimension="corpus",
            ),
            [
                {"code": "a-issue", "description": "A corpus issue."},
            ],
        )
        self.assertEqual(
            builder._output_blockers(
                blockers,
                label="smoke",
                dimension="slices",
            ),
            [
                {"code": "b-issue", "description": "A slices issue."},
            ],
        )

    def test_output_closure_rejects_reversed_lists(self) -> None:
        context = self._build_context()
        context.seed["providers"] = [
            {"input_id": "one"},
            {"input_id": "two"},
        ]
        outputs = {
            "bundle.json": builder.canonical_json_bytes(
                {
                    "bundle_type": "official-document-coverage",
                    "schema_version": "1.0",
                    "skill_id": "sample-skill",
                    "records": {
                        "corpora": ["corpus-two.json", "corpus-one.json"],
                        "slice_manifests": [
                            "slices-one.json",
                            "slices-two.json",
                        ],
                        "scope_inventory": "scope-inventory.json",
                        "coverage": "coverage.json",
                    },
                }
            ),
            "corpus-one.json": builder.canonical_json_bytes({}),
            "corpus-two.json": builder.canonical_json_bytes({}),
            "slices-one.json": builder.canonical_json_bytes({}),
            "slices-two.json": builder.canonical_json_bytes({}),
            "scope-inventory.json": builder.canonical_json_bytes({}),
            "coverage.json": builder.canonical_json_bytes({}),
        }
        with self.assertRaises(builder.PackBuildError):
            builder._validate_output_closure(context, outputs)

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
