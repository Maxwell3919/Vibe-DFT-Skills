from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import interface_registry  # noqa: E402
import registry_yaml  # noqa: E402
import validate_contract  # noqa: E402
import validate_official_document_coverage as coverage_validator  # noqa: E402


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
CP2K_MANIFEST_PATH = (
    ROOT
    / "skills"
    / "cp2k-rigorous-calculations"
    / "references"
    / "official-manual"
    / "manifest.json"
)
CP2K_MANIFEST_RAW = CP2K_MANIFEST_PATH.read_bytes()
CP2K_MANIFEST = json.loads(CP2K_MANIFEST_RAW)
CP2K_TOPIC_ALIAS = "accelerators"
CP2K_PAGE = CP2K_MANIFEST["pages"][CP2K_TOPIC_ALIAS]
CP2K_SOURCE_ID = CP2K_PAGE["source_path"].lower().replace("/", ".")
CP2K_INDEX_PATH = CP2K_MANIFEST_PATH.parent / "index.json"
CP2K_INDEX_RAW = CP2K_INDEX_PATH.read_bytes()
CP2K_INDEX = json.loads(CP2K_INDEX_RAW)
CP2K_DISCOVERED_SOURCE_IDS = sorted(
    item.lower().replace("/", ".")
    for item in CP2K_INDEX["pages"]
)
CP2K_RAW_SHA256 = CP2K_PAGE["raw_sha256"]
CP2K_RAW_BYTES = CP2K_PAGE["raw_bytes"]
CP2K_SNAPSHOT_PATH = CP2K_MANIFEST_PATH.parent / CP2K_PAGE["path"]
CP2K_SNAPSHOT_RAW = CP2K_SNAPSHOT_PATH.read_bytes()
CP2K_SNAPSHOT_SHA256 = hashlib.sha256(CP2K_SNAPSHOT_RAW).hexdigest()
SKILL_REGISTRY_PATH = ROOT / "registry" / "skill-registry.yaml"
SKILL_REGISTRY_RAW = SKILL_REGISTRY_PATH.read_bytes()
SKILL_REGISTRY = registry_yaml.load_yaml_strict(
    SKILL_REGISTRY_PATH,
    "skill-registry.yaml",
)
CP2K_SKILL = SKILL_REGISTRY["skills"]["cp2k-rigorous-calculations"]
CP2K_SKILL_PATH = ROOT / CP2K_SKILL["path"]
CP2K_SKILL_MD = CP2K_SKILL_PATH / "SKILL.md"
CP2K_SKILL_MD_SHA256 = hashlib.sha256(CP2K_SKILL_MD.read_bytes()).hexdigest()
CONSUMER_REGISTRY_PATH = ROOT / "registry" / "official-document-consumers.yaml"
CONSUMER_REGISTRY_RAW = CONSUMER_REGISTRY_PATH.read_bytes()
CONSUMER_REGISTRY_SHA256 = hashlib.sha256(CONSUMER_REGISTRY_RAW).hexdigest()


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def producer() -> dict[str, object]:
    return {
        "skill_id": "cp2k-rigorous-calculations",
        "skill_version": "1.0",
        "tool_id": "official-doc-coverage-test",
        "tool_version": "1.0",
        "generated_utc": "2026-07-24T12:00:00Z",
    }


def corpus_record() -> dict[str, object]:
    excluded_ids = sorted(
        set(CP2K_DISCOVERED_SOURCE_IDS) - {CP2K_SOURCE_ID}
    )
    return {
        "schema_version": "1.0",
        "contract_name": "official-corpus-manifest",
        "corpus_id": "cp2k-docs-2026.2-core",
        "authority_id": "cp2k-official-manual",
        "provider_id": "cp2k",
        "version_scope": {
            "kind": "exact",
            "value": "2026.2",
            "retrieved_utc": None,
            "snapshot_identity": None,
        },
        "status": "partial",
        "discovery": {
            "method": "official-index",
            "upstream_universe_complete": True,
            "inventory_scope": "upstream-universe",
            "authority_root": (
                "https://manual.cp2k.org/cp2k-2026_2-branch/"
            ),
            "authority_revision": "2026.2",
            "inventory_format": "cp2k-official-index-v1",
            "inventory_storage_mode": "embedded-open",
            "inventory_locator": "references/cp2k-index.json",
            "inventory_sha256": hashlib.sha256(CP2K_INDEX_RAW).hexdigest(),
            "inventory_receipt": None,
            "enumerator": {
                "enumerator_id": "cp2k-manifest-pages",
                "enumerator_version": "1.0",
                "trust_mode": "unverified",
                "implementation_ref": None,
                "configuration_ref": None,
                "dependency_lock_ref": None,
                "input_sha256": hashlib.sha256(CP2K_INDEX_RAW).hexdigest(),
                "output_sha256": canonical_json_sha256(
                    {
                        "discovered_source_ids": (
                            CP2K_DISCOVERED_SOURCE_IDS
                        )
                    }
                ),
                "attestation_id": None,
            },
            "discovered_source_ids": CP2K_DISCOVERED_SOURCE_IDS,
        },
        "included_sources": [
            {
                "source_id": CP2K_SOURCE_ID,
                "source_kind": "manual-page",
                "locator": CP2K_PAGE["source_url"],
                "version_scope": {
                    "kind": "exact",
                    "value": "2026.2",
                    "retrieved_utc": None,
                    "snapshot_identity": None,
                },
                "identity": {
                    "kind": "canonical-manifest-metadata",
                    "value": CP2K_TOPIC_ALIAS,
                    "raw_sha256": CP2K_RAW_SHA256,
                    "raw_bytes": CP2K_RAW_BYTES,
                    "resolver_receipt": None,
                },
            }
        ],
        "reviewed_exclusions": [
            {
                "source_id": source_id,
                "reason_code": "out-of-scope",
                "rationale": "Outside this minimal contract fixture scope.",
                "reviewed_by": "contract-steward",
                "reviewed_utc": "2026-07-24T12:00:00Z",
            }
            for source_id in excluded_ids
        ],
        "blockers": [],
        "limitations": [
            "The source enumerator has no centrally pinned implementation, configuration, and dependency lock."
        ],
        "producer": producer(),
    }


def slice_record(
    corpus_sha256: str,
    source_identity: dict[str, object],
) -> dict[str, object]:
    extent = source_identity["raw_bytes"]
    value = {
        "schema_version": "1.0",
        "contract_name": "document-slice-manifest",
        "slice_manifest_id": "cp2k-docs-2026.2-slices",
        "corpus_ref": {
            "corpus_id": "cp2k-docs-2026.2-core",
            "sha256": corpus_sha256,
        },
        "status": "partial",
        "sources": [
            {
                "source_id": CP2K_SOURCE_ID,
                "source_identity": copy.deepcopy(source_identity),
                "raw_source_extent_bytes": extent,
                "transformer": {
                    "transformer_id": "cp2k-manual-snapshot",
                    "transformer_version": "1.0",
                    "trust_mode": "unverified",
                    "implementation_ref": None,
                    "configuration_ref": None,
                    "dependency_lock_ref": None,
                    "input_raw_sha256": source_identity["raw_sha256"],
                    "output_sha256": SHA_A,
                    "attestation_id": None,
                    "deterministic": True,
                },
                "slices": [
                    {
                        "slice_id": "cp2k-accelerators",
                        "ordinal": 0,
                        "selector": {
                            "layer": "raw-source",
                            "kind": "byte-range",
                            "value": f"0:{extent}",
                        },
                        "byte_range": {
                            "start_byte": 0,
                            "end_byte_exclusive": extent,
                        },
                        "artifact_kind": "metadata",
                        "source_material_class": "documentation-text",
                        "storage_mode": "metadata-only",
                        "content_locator": CP2K_PAGE["source_url"],
                        "hash_basis": "external-receipt-content-bytes",
                        "artifact_sha256": None,
                        "content_sha256": CP2K_RAW_SHA256,
                        "content_receipt": {
                            "receipt_id": "cp2k-accelerators-receipt",
                            "resolver_id": "cp2k-official-adapter",
                            "canonical_url": CP2K_PAGE["source_url"],
                            "retrieved_utc": "2026-07-24T12:00:00Z",
                            "raw_sha256": CP2K_RAW_SHA256,
                            "raw_bytes": CP2K_RAW_BYTES,
                            "selected_sha256": CP2K_RAW_SHA256,
                            "selected_bytes": CP2K_RAW_BYTES,
                            "selection_attestation_id": None,
                            "evidence_sha256": hashlib.sha256(
                                CP2K_MANIFEST_RAW
                            ).hexdigest(),
                            "trust_mode": "unverified",
                            "registry_path": "registry/official-document-consumers.yaml",
                            "registry_sha256": CONSUMER_REGISTRY_SHA256,
                            "trust_id": None,
                            "verification_status": "unverified",
                        },
                        "loss_ids": [],
                    },
                ],
                "reviewed_overlaps": [],
                "preserved_ranges": [],
                "reviewed_orphans": [],
                "loss_ledger": [],
            }
        ],
        "blockers": [],
        "limitations": [
            "Rendered CP2K manual text remains external and the transformer is not centrally pinned."
        ],
        "producer": producer(),
    }
    finalize_slice_processor(value)
    return value


def finalize_slice_processor(value: dict[str, object]) -> None:
    for source in value["sources"]:
        if "transformer" not in source:
            continue
        source["transformer"]["output_sha256"] = canonical_json_sha256(
            {
                "slices": source["slices"],
                "reviewed_overlaps": source["reviewed_overlaps"],
                "preserved_ranges": source["preserved_ranges"],
                "reviewed_orphans": source["reviewed_orphans"],
                "loss_ledger": source["loss_ledger"],
            }
        )


def license_record(corpus_sha256: str) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "contract_name": "official-source-license-review",
        "license_review_id": "cp2k-docs-license-review",
        "corpus_ref": {
            "corpus_id": "cp2k-docs-2026.2-core",
            "sha256": corpus_sha256,
        },
        "authority_id": "cp2k-official-manual",
        "status": "partial",
        "trust_attestation": {
            "trust_mode": "unverified",
            "registry_path": "registry/official-document-consumers.yaml",
            "registry_sha256": CONSUMER_REGISTRY_SHA256,
            "trust_id": None,
            "attestation_ref": None,
        },
        "license_identity": {
            "identifier": None,
            "terms_urls": [],
            "verification": "unknown",
        },
        "storage_rules": [
            {
                "artifact_kind": "metadata",
                "source_material_class": "documentation-text",
                "assessment": "unresolved",
                "allowed_storage_modes": [
                    "metadata-only",
                    "external-runtime-only",
                    "excluded",
                ],
                "conditions": [
                    "Keep rendered manual text external until build and license provenance is reviewed."
                ],
                "limitations": [
                    "Every license obligation remains unknown pending authoritative documentation-license evidence."
                ],
                "license_evidence_refs": ["cp2k-license-text"],
                "rights_holder": "Unknown pending documentation build provenance.",
                "attribution_required": "unknown",
                "notice_required": "unknown",
                "modified_content_marking_required": "unknown",
                "share_alike_required": "unknown",
                "source_offer_required": "unknown",
            }
        ],
        "evidence": [
            {
                "evidence_id": "cp2k-license-text",
                "locator": "https://github.com/cp2k/cp2k/blob/master/LICENSE",
                "revision": None,
                "sha256": None,
                "hash_basis": "unattested-external-locator",
                "terms_content_ref": None,
            }
        ],
        "review_expires_utc": None,
        "supersedes_review_ids": [],
        "blockers": [],
        "limitations": [
            "No central pinned license evidence, reviewer authority, or platform attestation exists."
        ],
        "reviewer": {
            "reviewer_id": "contract-steward",
            "role": "license-reviewer",
            "reviewed_utc": "2026-07-24T12:00:00Z",
        },
        "producer": producer(),
    }


def scope_subjects() -> list[dict[str, object]]:
    origin = {
        "path": f"{CP2K_SKILL['path']}/SKILL.md",
        "sha256": CP2K_SKILL_MD_SHA256,
        "selector": {"kind": "whole-file", "value": "*"},
    }
    return [
        {
            "subject_id": "cp2k-accelerator-controls",
            "subject_kind": "workflow",
            "evidence_class": "official-provider-required",
            "origin_refs": [copy.deepcopy(origin)],
            "statement": "CP2K accelerator guidance consumed by the Skill.",
        },
        {
            "subject_id": "cp2k-input-validation",
            "subject_kind": "workflow",
            "evidence_class": "deterministic-tool-behavior",
            "origin_refs": [copy.deepcopy(origin)],
            "statement": "Validate CP2K inputs before execution.",
        },
    ]


def scope_inventory_record() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "contract_name": "skill-document-scope-inventory",
        "inventory_id": "cp2k-doc-scope-inventory",
        "skill_id": "cp2k-rigorous-calculations",
        "skill_registry_binding": {
            "registry_path": "registry/skill-registry.yaml",
            "registry_sha256": hashlib.sha256(SKILL_REGISTRY_RAW).hexdigest(),
            "skill_path": CP2K_SKILL["path"],
            "lifecycle": CP2K_SKILL["lifecycle"],
            "source_tree_hash_domain": (
                coverage_validator.skill_registry.TREE_HASH_DOMAIN_NAME
            ),
            "source_tree_sha256": CP2K_SKILL["source_tree_sha256"],
        },
        "status": "partial",
        "skill_source_refs": [
            {
                "path": f"{CP2K_SKILL['path']}/SKILL.md",
                "sha256": CP2K_SKILL_MD_SHA256,
            }
        ],
        "enumeration": {
            "method": "canonical-reviewed-inventory",
            "scope_complete": True,
            "extractor": None,
            "reviewed_by": "contract-steward",
            "reviewed_utc": "2026-07-24T12:00:00Z",
        },
        "subjects": scope_subjects(),
        "blockers": [],
        "limitations": [
            "Canonical manual review is not a replayable complete claim-source inventory."
        ],
        "producer": producer(),
    }


def coverage_record(
    corpus_sha256: str,
    slice_sha256: str,
    license_sha256: str,
    scope_inventory_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "contract_name": "skill-document-coverage",
        "coverage_id": "cp2k-input-doc-coverage",
        "skill_id": "cp2k-rigorous-calculations",
        "consumer_binding_refs": [
            {
                "registry_path": "registry/official-document-consumers.yaml",
                "registry_sha256": CONSUMER_REGISTRY_SHA256,
                "binding_id": "cp2k-skill-cp2k-manual",
            }
        ],
        "status": "partial",
        "corpus_refs": [
            {
                "corpus_id": "cp2k-docs-2026.2-core",
                "sha256": corpus_sha256,
            }
        ],
        "slice_manifest_refs": [
            {
                "slice_manifest_id": "cp2k-docs-2026.2-slices",
                "sha256": slice_sha256,
            }
        ],
        "license_review_refs": [
            {
                "license_review_id": "cp2k-docs-license-review",
                "sha256": license_sha256,
            }
        ],
        "scope_inventory_ref": {
            "inventory_id": "cp2k-doc-scope-inventory",
            "sha256": scope_inventory_sha256,
        },
        "declared_scope": scope_subjects(),
        "mappings": [
            {
                "subject_id": "cp2k-accelerator-controls",
                "coverage_status": "partial",
                "official_disposition": "partial",
                "slice_refs": [
                    {
                        "slice_manifest_id": "cp2k-docs-2026.2-slices",
                        "slice_id": "cp2k-accelerators",
                    }
                ],
                "local_evidence_refs": [],
                "rationale": None,
                "limitations": [
                    "Coverage inherits unverified processor, scope, and license trust roots."
                ],
            },
            {
                "subject_id": "cp2k-input-validation",
                "coverage_status": "complete",
                "official_disposition": "not-applicable",
                "slice_refs": [],
                "local_evidence_refs": [
                    {
                        "path": f"{CP2K_SKILL['path']}/SKILL.md",
                        "sha256": CP2K_SKILL_MD_SHA256,
                    }
                ],
                "rationale": (
                    "Deterministic validator behavior is established from the "
                    "content-addressed local Skill source, not provider documentation."
                ),
                "limitations": [],
            },
        ],
        "blockers": [],
        "limitations": [
            "Complete official-document coverage is not yet supportable."
        ],
        "producer": producer(),
    }


def use_embedded_snapshot(value: dict[str, object]) -> None:
    source = value["sources"][0]
    item = source["slices"][0]
    item["selector"]["layer"] = "derived-artifact"
    item["selector"]["value"] = f"0:{len(CP2K_SNAPSHOT_RAW)}"
    item["byte_range"] = {
        "start_byte": 0,
        "end_byte_exclusive": len(CP2K_SNAPSHOT_RAW),
    }
    item["storage_mode"] = "embedded-open"
    item["content_locator"] = "references/accelerators.md"
    item["hash_basis"] = "artifact-and-payload-exact-bytes"
    item["artifact_sha256"] = CP2K_SNAPSHOT_SHA256
    item["content_sha256"] = CP2K_SNAPSHOT_SHA256
    item["content_receipt"] = None


def write_json(path: Path, value: dict[str, object]) -> str:
    raw = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def write_bundle(
    directory: Path,
    *,
    mutate_corpus=None,
    mutate_slices=None,
    mutate_license=None,
    mutate_scope_inventory=None,
    mutate_coverage=None,
) -> tuple[Path, Path, Path, Path, Path]:
    content_path = directory / "references" / "accelerators.md"
    content_path.parent.mkdir(parents=True)
    content_path.write_bytes(CP2K_SNAPSHOT_RAW)
    (directory / "references" / "cp2k-manifest.json").write_bytes(
        CP2K_MANIFEST_RAW
    )
    (directory / "references" / "cp2k-index.json").write_bytes(
        CP2K_INDEX_RAW
    )

    corpus = corpus_record()
    if mutate_corpus is not None:
        mutate_corpus(corpus)
    corpus_path = directory / "corpus.json"
    corpus_sha256 = write_json(corpus_path, corpus)

    source_identity = copy.deepcopy(corpus["included_sources"][0]["identity"])
    slices = slice_record(corpus_sha256, source_identity)
    if mutate_slices is not None:
        mutate_slices(slices)
    finalize_slice_processor(slices)
    slices_path = directory / "slices.json"
    slice_sha256 = write_json(slices_path, slices)

    license_review = license_record(corpus_sha256)
    if mutate_license is not None:
        mutate_license(license_review)
    license_path = directory / "license.json"
    license_sha256 = write_json(license_path, license_review)

    scope_inventory = scope_inventory_record()
    if mutate_scope_inventory is not None:
        mutate_scope_inventory(scope_inventory)
    scope_inventory_path = directory / "scope-inventory.json"
    scope_inventory_sha256 = write_json(scope_inventory_path, scope_inventory)

    coverage = coverage_record(
        corpus_sha256,
        slice_sha256,
        license_sha256,
        scope_inventory_sha256,
    )
    if mutate_coverage is not None:
        mutate_coverage(coverage)
    coverage_path = directory / "coverage.json"
    write_json(coverage_path, coverage)
    return (
        corpus_path,
        slices_path,
        license_path,
        scope_inventory_path,
        coverage_path,
    )


class OfficialDocumentCoverageTests(unittest.TestCase):
    def validate(self, paths: tuple[Path, Path, Path, Path, Path]):
        corpus, slices, license_review, scope_inventory, coverage = paths
        return coverage_validator.validate_files(
            corpus_paths=[corpus],
            slice_paths=[slices],
            license_review_paths=[license_review],
            scope_inventory_path=scope_inventory,
            coverage_path=coverage,
            source_root=corpus.parent,
        )

    @staticmethod
    def codes(result) -> set[str]:
        return {finding.code for finding in result.findings}

    def test_contracts_are_active_local_catalog_interfaces(self) -> None:
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        registry = interface_registry.load_registry()
        expected = {
            "official-corpus-manifest",
            "document-slice-manifest",
            "skill-document-coverage",
            "official-source-license-review",
            "skill-document-scope-inventory",
        }
        for name in expected:
            with self.subTest(name=name):
                contract = catalog.resolve(f"{name}@1.0")
                self.assertEqual(
                    validate_contract.runtime_interface_lifecycle(
                        contract, catalog
                    ),
                    "active",
                )
                self.assertEqual(
                    registry["interfaces"][f"{name}@1.0"]["domain"],
                    "official-documentation",
                )

    def test_honest_partial_bundle_passes_schema_hash_and_semantic_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            paths = write_bundle(Path(raw_directory))
            result = self.validate(paths)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.assurance_status, "partial")

    def test_scope_subjects_cannot_omit_evidence_classification(self) -> None:
        def missing_class(value):
            value["subjects"][0].pop("evidence_class")

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_scope_inventory=missing_class,
                )
            )
        self.assertIn("RECORD_SCHEMA_INVALID", self.codes(result))

    def test_unknown_cp2k_license_cannot_silently_assert_false_obligations(
        self,
    ) -> None:
        def false_certainty(value):
            value["storage_rules"][0]["attribution_required"] = False

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_license=false_certainty,
                )
            )
        self.assertIn("LICENSE_OBLIGATION_FALSE_CERTAINTY", self.codes(result))

    def test_registry_hash_cannot_masquerade_as_exact_terms_bytes(self) -> None:
        def forged_terms_hash(value):
            evidence = value["evidence"][0]
            evidence.update(
                revision="master-reviewed-2026-07-24",
                sha256=CONSUMER_REGISTRY_SHA256,
                hash_basis="exact-terms-content-bytes",
                terms_content_ref={
                    "path": (
                        "skills/cp2k-rigorous-calculations/references/"
                        "official-source-pack/license-terms/forged.txt"
                    ),
                    "sha256": CONSUMER_REGISTRY_SHA256,
                },
            )

        with tempfile.TemporaryDirectory() as raw_directory:
            paths = write_bundle(
                Path(raw_directory),
                mutate_license=forged_terms_hash,
            )
            result = self.validate(paths)
        self.assertIn("LICENSE_TERMS_CONTENT_HASH_MISMATCH", self.codes(result))

    def test_registry_bytes_cannot_be_declared_as_exact_terms_content(self) -> None:
        def forged_terms_reference(value):
            evidence = value["evidence"][0]
            evidence.update(
                revision="registry-bytes-2026-07-24",
                sha256=CONSUMER_REGISTRY_SHA256,
                hash_basis="exact-terms-content-bytes",
                terms_content_ref={
                    "path": "registry/official-document-consumers.yaml",
                    "sha256": CONSUMER_REGISTRY_SHA256,
                },
            )

        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            paths = write_bundle(
                directory,
                mutate_license=forged_terms_reference,
            )
            registry_path = (
                directory / "registry" / "official-document-consumers.yaml"
            )
            registry_path.parent.mkdir(parents=True)
            registry_path.write_bytes(CONSUMER_REGISTRY_RAW)
            result = self.validate(paths)
        self.assertIn("RECORD_SCHEMA_INVALID", self.codes(result))

    def test_central_trust_cannot_pin_registry_bytes_as_terms_content(self) -> None:
        consumer_registry = registry_yaml.load_yaml_strict(
            CONSUMER_REGISTRY_PATH,
            "official-document-consumers.yaml",
        )
        consumer_registry["license_trust"]["forged-registry-terms"] = {
            "authority_id": "cp2k-official-manual",
            "reviewer_ids": ["contract-steward"],
            "evidence": [
                {
                    "evidence_id": "forged-registry-license-evidence",
                    "locator": "https://www.cp2k.org/license",
                    "revision": "registry-bytes-2026-07-24",
                    "sha256": CONSUMER_REGISTRY_SHA256,
                    "hash_basis": "exact-terms-content-bytes",
                    "terms_content_ref": {
                        "path": "registry/official-document-consumers.yaml",
                        "sha256": CONSUMER_REGISTRY_SHA256,
                    },
                }
            ],
            "platform_attestation_ref": None,
        }
        authority_registry = registry_yaml.load_yaml_strict(
            ROOT / "registry" / "official-source-authorities.yaml",
            "official-source-authorities.yaml",
        )
        errors = coverage_validator.consumer_registry_validation_errors(
            consumer_registry,
            skills=SKILL_REGISTRY["skills"],
            authorities=authority_registry["authorities"],
            root=ROOT,
        )
        self.assertTrue(
            any(
                "exact license terms must live under a skill "
                "official-source-pack license-terms directory" in error
                for error in errors
            ),
            errors,
        )

    def test_active_authority_requires_a_valid_binding_but_planned_may_be_unbound(
        self,
    ) -> None:
        consumer_registry = registry_yaml.load_yaml_strict(
            CONSUMER_REGISTRY_PATH,
            "official-document-consumers.yaml",
        )
        authority_registry = registry_yaml.load_yaml_strict(
            ROOT / "registry" / "official-source-authorities.yaml",
            "official-source-authorities.yaml",
        )
        canonical_errors = (
            coverage_validator.consumer_registry_validation_errors(
                consumer_registry,
                skills=SKILL_REGISTRY["skills"],
                authorities=authority_registry["authorities"],
                root=ROOT,
            )
        )
        self.assertEqual(canonical_errors, [])
        planned_authority_ids = {
            authority_id
            for authority_id, authority in authority_registry[
                "authorities"
            ].items()
            if authority["lifecycle"] == "planned"
        }
        bound_authority_ids = {
            binding["authority_id"]
            for binding in consumer_registry["bindings"]
        }
        self.assertTrue(planned_authority_ids)
        self.assertTrue(planned_authority_ids.isdisjoint(bound_authority_ids))

        dangling = copy.deepcopy(consumer_registry)
        dangling["bindings"] = [
            binding
            for binding in dangling["bindings"]
            if binding["authority_id"]
            != "catmap-release-source-docs-0-4-1"
        ]
        dangling_errors = (
            coverage_validator.consumer_registry_validation_errors(
                dangling,
                skills=SKILL_REGISTRY["skills"],
                authorities=authority_registry["authorities"],
                root=ROOT,
            )
        )
        self.assertTrue(
            any(
                "every active official-source authority must be used" in error
                for error in dangling_errors
            ),
            dangling_errors,
        )

        planned_binding = copy.deepcopy(consumer_registry)
        template = copy.deepcopy(planned_binding["bindings"][0])
        planned_authority_id = sorted(planned_authority_ids)[0]
        planned_authority = authority_registry["authorities"][
            planned_authority_id
        ]
        template.update(
            binding_id="forged-active-consumer-planned-authority",
            authority_id=planned_authority_id,
            provider_id=planned_authority["provider_id"],
        )
        planned_binding["bindings"].append(template)
        planned_errors = (
            coverage_validator.consumer_registry_validation_errors(
                planned_binding,
                skills=SKILL_REGISTRY["skills"],
                authorities=authority_registry["authorities"],
                root=ROOT,
            )
        )
        self.assertTrue(
            any(
                "does not match an active official-source authority" in error
                for error in planned_errors
            ),
            planned_errors,
        )

    def test_repository_canonical_pack_pairs_close_the_central_registry(
        self,
    ) -> None:
        consumer_registry = registry_yaml.load_yaml_strict(
            CONSUMER_REGISTRY_PATH,
            "official-document-consumers.yaml",
        )
        findings = (
            coverage_validator.canonical_pack_binding_closure_findings(
                root=ROOT,
                skills=SKILL_REGISTRY["skills"],
                consumer_registry=consumer_registry,
            )
        )
        self.assertEqual(findings, ())

    def test_global_closure_rejects_an_omitted_central_binding(self) -> None:
        consumer_registry = registry_yaml.load_yaml_strict(
            CONSUMER_REGISTRY_PATH,
            "official-document-consumers.yaml",
        )
        consumer_registry["bindings"] = [
            binding
            for binding in consumer_registry["bindings"]
            if binding["binding_id"] != "cp2k-skill-cp2k-manual"
        ]
        findings = (
            coverage_validator.canonical_pack_binding_closure_findings(
                root=ROOT,
                skills=SKILL_REGISTRY["skills"],
                consumer_registry=consumer_registry,
            )
        )
        self.assertIn(
            "GLOBAL_PACK_BINDING_SET_MISMATCH",
            {finding.code for finding in findings},
        )

    def test_global_closure_rejects_a_pack_forged_authority_pair(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            pack = (
                root
                / "skills"
                / "source-skill"
                / "references"
                / "official-source-pack"
            )
            pack.mkdir(parents=True)
            write_json(
                pack / "bundle.json",
                {
                    "bundle_type": "official-document-coverage",
                    "schema_version": "1.0",
                    "skill_id": "source-skill",
                    "records": {"corpora": ["corpus.json"]},
                },
            )
            write_json(
                pack / "corpus.json",
                {
                    "authority_id": "forged-authority",
                    "provider_id": "forged-provider",
                },
            )
            findings = (
                coverage_validator.canonical_pack_binding_closure_findings(
                    root=root,
                    skills={
                        "source-skill": {
                            "lifecycle": "development",
                            "path": "skills/source-skill",
                        }
                    },
                    consumer_registry={
                        "bindings": [
                            {
                                "consumer_skill_id": "source-skill",
                                "authority_id": "central-authority",
                                "provider_id": "central-provider",
                            }
                        ]
                    },
                )
            )
        self.assertIn(
            "GLOBAL_PACK_BINDING_SET_MISMATCH",
            {finding.code for finding in findings},
        )

    def test_curated_cp2k_subset_cannot_claim_the_upstream_universe(self) -> None:
        def relabel_subset(value):
            curated_ids = sorted(
                item["source_path"].lower().replace("/", ".")
                for item in CP2K_MANIFEST["pages"].values()
            )
            value["discovery"].update(
                inventory_format="cp2k-canonical-manifest-v1",
                inventory_locator="references/cp2k-manifest.json",
                inventory_sha256=hashlib.sha256(CP2K_MANIFEST_RAW).hexdigest(),
                inventory_scope="upstream-universe",
                upstream_universe_complete=True,
                discovered_source_ids=curated_ids,
            )
            value["reviewed_exclusions"] = [
                {
                    "source_id": source_id,
                    "reason_code": "unavailable",
                    "rationale": "Synthetic bounded manifest exclusion.",
                    "reviewed_by": "contract-steward",
                    "reviewed_utc": "2026-07-24T12:00:00Z",
                }
                for source_id in curated_ids
                if source_id != CP2K_SOURCE_ID
            ]

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_corpus=relabel_subset,
                )
            )
        self.assertIn("CORPUS_UPSTREAM_UNIVERSE_OVERCLAIM", self.codes(result))

    def test_declarative_catalog_cannot_self_assert_upstream_universe(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            catalog_path = directory / "catalog.json"
            fixture = corpus_record()
            catalog_hash = write_json(
                catalog_path,
                {
                    "schema_version": "1.0",
                    "contract_name": "official-document-source-catalog",
                    "version_scope": {
                        "kind": "exact",
                        "value": "2026.2",
                        "retrieved_utc": None,
                        "snapshot_identity": None,
                    },
                    "upstream_universe_complete": True,
                    "inventory_locator": (
                        "https://manual.cp2k.org/cp2k-2026_2-branch/"
                    ),
                    "sources": [
                        {"source_id": item["source_id"]}
                        for item in fixture["included_sources"]
                    ],
                    "subjects": [],
                    "reviewed_exclusions": [
                        {"source_id": item["source_id"]}
                        for item in fixture["reviewed_exclusions"]
                    ],
                    "losses": [],
                    "license": {},
                    "limitations": [],
                    "blockers": [],
                },
            )

            def self_asserted(value):
                discovery = value["discovery"]
                discovery.update(
                    method="manual-inventory",
                    inventory_format="declarative-source-catalog-v1",
                    inventory_locator="catalog.json",
                    inventory_sha256=catalog_hash,
                    inventory_scope="upstream-universe",
                    upstream_universe_complete=True,
                )
                discovery["enumerator"]["input_sha256"] = catalog_hash

            with mock.patch.object(
                coverage_validator,
                "consumer_registry_validation_errors",
                return_value=[],
            ):
                result = self.validate(
                    write_bundle(directory, mutate_corpus=self_asserted)
                )
        self.assertIn(
            "CORPUS_CATALOG_SELF_ASSERTED_UNIVERSE",
            self.codes(result),
        )

    def test_latest_snapshot_must_match_recomputed_source_identity_aggregate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            catalog_path = directory / "catalog.json"
            fixture = corpus_record()
            catalog_hash = write_json(
                catalog_path,
                {
                    "schema_version": "1.0",
                    "contract_name": "official-document-source-catalog",
                    "version_scope": {
                        "kind": "latest-at-retrieval",
                        "value": None,
                        "retrieved_utc": "2026-07-24T12:00:00Z",
                        "snapshot_identity": None,
                    },
                    "upstream_universe_complete": False,
                    "inventory_locator": "https://vasp.at/wiki/",
                    "sources": [
                        {"source_id": item["source_id"]}
                        for item in fixture["included_sources"]
                    ],
                    "subjects": [],
                    "reviewed_exclusions": [
                        {"source_id": item["source_id"]}
                        for item in fixture["reviewed_exclusions"]
                    ],
                    "losses": [],
                    "license": {},
                    "limitations": [],
                    "blockers": [],
                },
            )

            def forged_catalog_snapshot(value):
                scope = {
                    "kind": "latest-at-retrieval",
                    "value": None,
                    "retrieved_utc": "2026-07-24T12:00:00Z",
                    "snapshot_identity": {
                        "kind": "sha256",
                        "value": catalog_hash,
                        "content_sha256": catalog_hash,
                    },
                }
                value["authority_id"] = "vasp-official-wiki"
                value["provider_id"] = "vasp"
                value["version_scope"] = scope
                value["included_sources"][0]["locator"] = (
                    "https://vasp.at/wiki/POSCAR"
                )
                value["included_sources"][0]["version_scope"] = {
                    **copy.deepcopy(scope),
                    "snapshot_identity": {
                        "kind": "sha256",
                        "value": value["included_sources"][0]["identity"][
                            "raw_sha256"
                        ],
                        "content_sha256": value["included_sources"][0][
                            "identity"
                        ]["raw_sha256"],
                    },
                }
                discovery = value["discovery"]
                discovery.update(
                    method="manual-inventory",
                    upstream_universe_complete=False,
                    inventory_scope="bounded-authority-subset",
                    authority_root="https://vasp.at/wiki/",
                    authority_revision="latest-at-2026-07-24T12:00:00Z",
                    inventory_format="declarative-source-catalog-v1",
                    inventory_locator="catalog.json",
                    inventory_sha256=catalog_hash,
                )
                discovery["enumerator"]["input_sha256"] = catalog_hash

            with mock.patch.object(
                coverage_validator,
                "consumer_registry_validation_errors",
                return_value=[],
            ):
                result = self.validate(
                    write_bundle(
                        directory,
                        mutate_corpus=forged_catalog_snapshot,
                    )
                )
        self.assertIn(
            "ROLLING_SNAPSHOT_IDENTITY_MISMATCH",
            self.codes(result),
        )

    def test_metadata_receipt_cannot_bind_a_derived_snapshot_as_raw_source(
        self,
    ) -> None:
        def derived_as_raw(value):
            identity = value["included_sources"][0]["identity"]
            identity["raw_sha256"] = CP2K_SNAPSHOT_SHA256
            identity["raw_bytes"] = len(CP2K_SNAPSHOT_RAW)

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_corpus=derived_as_raw,
                )
            )
        self.assertIn("SOURCE_RAW_DERIVED_IDENTITY_CONFUSED", self.codes(result))

    def test_non_byte_selector_cannot_claim_byte_closure(self) -> None:
        def page_selector(value):
            item = value["sources"][0]["slices"][0]
            item["selector"] = {
                "layer": "raw-source",
                "kind": "page-range",
                "value": "1-1",
            }
            item["byte_range"] = None
            value["status"] = "complete"
            value["limitations"] = []

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_slices=page_selector,
                )
            )
        self.assertIn("SLICE_SELECTOR_NO_BYTE_CLOSURE", self.codes(result))
        self.assertIn("PROCESSOR_TRUST_UNVERIFIED", self.codes(result))

    def test_discovered_sources_are_exact_disjoint_partition(self) -> None:
        mutations = {
            "missing": lambda value: value["reviewed_exclusions"].pop(),
            "overlap": lambda value: value["reviewed_exclusions"].append(
                {
                    "source_id": CP2K_SOURCE_ID,
                    "reason_code": "other",
                    "rationale": "Invalid overlap.",
                    "reviewed_by": "contract-steward",
                    "reviewed_utc": "2026-07-24T12:00:00Z",
                }
            ),
            "extra": lambda value: value["included_sources"].append(
                {
                    "source_id": "not-discovered",
                    "source_kind": "manual-page",
                    "locator": "https://example.invalid/not-discovered",
                    "version_scope": {
                        "kind": "exact",
                        "value": "2026.2",
                        "retrieved_utc": None,
                        "snapshot_identity": None,
                    },
                    "identity": {
                        "kind": "sha256",
                        "value": SHA_C,
                        "raw_sha256": SHA_C,
                        "raw_bytes": 1,
                        "resolver_receipt": None,
                    },
                }
            ),
        }
        for label, mutation in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_directory:
                result = self.validate(
                    write_bundle(Path(raw_directory), mutate_corpus=mutation)
                )
            self.assertIn("CORPUS_PARTITION_INVALID", self.codes(result))

    def test_discovery_inventory_bytes_and_exact_source_set_are_verified(
        self,
    ) -> None:
        def tiny_self_declared_universe(value):
            value["discovery"]["discovered_source_ids"] = [CP2K_SOURCE_ID]
            value["reviewed_exclusions"] = []

        def fake_inventory_hash(value):
            value["discovery"]["inventory_sha256"] = SHA_A

        cases = {
            "tiny-universe": (
                tiny_self_declared_universe,
                "CORPUS_INVENTORY_SET_MISMATCH",
            ),
            "fake-hash": (
                fake_inventory_hash,
                "CORPUS_INVENTORY_HASH_MISMATCH",
            ),
        }
        for label, (mutation, code) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_directory:
                result = self.validate(
                    write_bundle(Path(raw_directory), mutate_corpus=mutation)
                )
            self.assertIn(code, self.codes(result))

    def test_slice_sources_order_and_loss_ledger_are_fail_closed(self) -> None:
        def unknown_loss_slice(value):
            value["sources"][0]["loss_ledger"].append(
                {
                    "loss_id": "bad-loss",
                    "category": "layout",
                    "severity": "informational",
                    "disposition": "normalized",
                    "description": "Invalid reference fixture.",
                    "affected_slice_ids": ["unknown-slice"],
                }
            )

        mutations = {
            "missing-source": lambda value: (
                value.update(status="complete", limitations=[]),
                value["sources"].clear(),
            ),
            "noncontiguous-order": lambda value: value["sources"][0]["slices"][
                0
            ].update(ordinal=1),
            "missing-loss": lambda value: value["sources"][0]["slices"][0].update(
                loss_ids=["unknown-loss"]
            ),
            "unknown-loss-slice": unknown_loss_slice,
        }
        expected = {
            "missing-source": "SLICE_SOURCE_COVERAGE_INVALID",
            "noncontiguous-order": "SLICE_ORDER_INVALID",
            "missing-loss": "SLICE_LOSS_REF_INVALID",
            "unknown-loss-slice": "LOSS_SLICE_REF_INVALID",
        }
        for label, mutation in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_directory:
                result = self.validate(
                    write_bundle(Path(raw_directory), mutate_slices=mutation)
                )
            self.assertIn(expected[label], self.codes(result))

    def test_coverage_requires_exactly_one_slice_manifest_per_corpus(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            paths = write_bundle(directory)
            (
                corpus_path,
                slices_path,
                license_path,
                scope_inventory_path,
                coverage_path,
            ) = paths
            duplicate = json.loads(slices_path.read_bytes())
            duplicate["slice_manifest_id"] = (
                "cp2k-docs-2026.2-duplicate-slices"
            )
            duplicate_path = directory / "duplicate-slices.json"
            duplicate_sha256 = write_json(duplicate_path, duplicate)
            coverage = json.loads(coverage_path.read_bytes())
            coverage["slice_manifest_refs"].append(
                {
                    "slice_manifest_id": duplicate["slice_manifest_id"],
                    "sha256": duplicate_sha256,
                }
            )
            write_json(coverage_path, coverage)
            result = coverage_validator.validate_files(
                corpus_paths=[corpus_path],
                slice_paths=[slices_path, duplicate_path],
                license_review_paths=[license_path],
                scope_inventory_path=scope_inventory_path,
                coverage_path=coverage_path,
                source_root=directory,
            )
        self.assertIn(
            "COVERAGE_SLICE_CORPUS_PARTITION_INVALID",
            self.codes(result),
        )

    def test_slice_loss_links_are_bidirectionally_exact(self) -> None:
        def slice_only_link(value):
            source = value["sources"][0]
            source["slices"][0]["loss_ids"] = ["one-sided-loss"]
            source["loss_ledger"] = [
                {
                    "loss_id": "one-sided-loss",
                    "category": "other",
                    "severity": "material",
                    "disposition": "external-only",
                    "description": "The slice points to this loss.",
                    "affected_slice_ids": [],
                }
            ]

        def ledger_only_link(value):
            source = value["sources"][0]
            source["loss_ledger"] = [
                {
                    "loss_id": "one-sided-loss",
                    "category": "other",
                    "severity": "informational",
                    "disposition": "normalized",
                    "description": "Only the ledger points to the slice.",
                    "affected_slice_ids": ["cp2k-accelerators"],
                }
            ]

        for label, mutation in {
            "slice-only": slice_only_link,
            "ledger-only": ledger_only_link,
        }.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_directory:
                result = self.validate(
                    write_bundle(
                        Path(raw_directory),
                        mutate_slices=mutation,
                    )
                )
            self.assertIn(
                "SLICE_LOSS_LINKAGE_MISMATCH",
                self.codes(result),
            )

    def test_any_blocking_loss_caps_slice_manifest_at_blocked(self) -> None:
        def blocking_loss(value, disposition):
            source = value["sources"][0]
            source["slices"][0]["loss_ids"] = ["blocking-loss"]
            source["loss_ledger"] = [
                {
                    "loss_id": "blocking-loss",
                    "category": "other",
                    "severity": "blocking",
                    "disposition": disposition,
                    "description": "A blocking loss must cap the manifest.",
                    "affected_slice_ids": ["cp2k-accelerators"],
                }
            ]

        for disposition in ("preserved", "normalized", "external-only"):
            with (
                self.subTest(disposition=disposition),
                tempfile.TemporaryDirectory() as raw_directory,
            ):
                result = self.validate(
                    write_bundle(
                        Path(raw_directory),
                        mutate_slices=lambda value: blocking_loss(
                            value,
                            disposition,
                        ),
                    )
                )
            self.assertIn(
                "COMPLETENESS_STATUS_OVERCLAIM",
                self.codes(result),
            )

    def test_every_declared_subject_maps_to_existing_slice(self) -> None:
        mutations = {
            "missing-subject": lambda value: value["mappings"].pop(),
            "extra-subject": lambda value: value["mappings"].append(
                {
                    "subject_id": "undeclared",
                    "coverage_status": "complete",
                    "official_disposition": "covered",
                    "slice_refs": [
                        {
                            "slice_manifest_id": "cp2k-docs-2026.2-slices",
                            "slice_id": "cp2k-accelerators",
                        }
                    ],
                    "local_evidence_refs": [],
                    "rationale": None,
                    "limitations": [],
                }
            ),
            "missing-slice": lambda value: value["mappings"][0][
                "slice_refs"
            ][0].update(slice_id="unknown-slice"),
        }
        expected = {
            "missing-subject": "COVERAGE_SUBJECT_PARTITION_INVALID",
            "extra-subject": "COVERAGE_SUBJECT_PARTITION_INVALID",
            "missing-slice": "COVERAGE_SLICE_REF_INVALID",
        }
        for label, mutation in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_directory:
                result = self.validate(
                    write_bundle(Path(raw_directory), mutate_coverage=mutation)
                )
            self.assertIn(expected[label], self.codes(result))

    def test_blocked_official_subject_can_record_an_honest_zero_slice_gap(
        self,
    ) -> None:
        def blocked_gap(value):
            mapping = value["mappings"][0]
            mapping.update(
                coverage_status="blocked",
                official_disposition="blocked",
                slice_refs=[],
                rationale=(
                    "The licensed official source is unavailable; local or "
                    "literature evidence is not substituted."
                ),
                limitations=[
                    "No exact official slice is available for this subject."
                ],
            )
            value["status"] = "blocked"
            value["blockers"] = [
                {
                    "code": "official-subject-blocked",
                    "description": (
                        "One canonical provider subject has no exact official "
                        "slice."
                    ),
                }
            ]

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_coverage=blocked_gap,
                )
            )
        self.assertEqual(result.findings, ())
        self.assertEqual(result.assurance_status, "blocked")

    def test_partial_official_subject_cannot_omit_its_slice(self) -> None:
        def missing_slice(value):
            value["mappings"][0]["slice_refs"] = []

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_coverage=missing_slice,
                )
            )
        self.assertIn("RECORD_SCHEMA_INVALID", self.codes(result))

    def test_license_review_controls_actual_slice_storage_mode(self) -> None:
        def forbid_embedded(value):
            value["storage_rules"][0]["assessment"] = "conditional"
            value["storage_rules"][0]["allowed_storage_modes"] = [
                "external-runtime-only"
            ]

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(Path(raw_directory), mutate_license=forbid_embedded)
            )
        self.assertIn("LICENSE_STORAGE_MODE_FORBIDDEN", self.codes(result))

    def test_exact_record_reference_hashes_are_required(self) -> None:
        def corrupt_reference(value):
            value["slice_manifest_refs"][0]["sha256"] = "0" * 64

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(Path(raw_directory), mutate_coverage=corrupt_reference)
            )
        self.assertIn("RECORD_REF_HASH_MISMATCH", self.codes(result))

    def test_coverage_cannot_delete_a_real_inventory_subject_and_stay_complete(
        self,
    ) -> None:
        def delete_internal_scope(value):
            value["declared_scope"][0]["statement"] = (
                "A silently rewritten coverage-only statement."
            )

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_coverage=delete_internal_scope,
                )
            )
        self.assertIn("COVERAGE_SCOPE_INVENTORY_MISMATCH", self.codes(result))

    def test_complete_corpus_rejects_unversioned_scope(self) -> None:
        def unversioned(value):
            value["status"] = "complete"
            value["limitations"] = []
            value["version_scope"] = {
                "kind": "unversioned",
                "value": None,
                "retrieved_utc": None,
                "snapshot_identity": None,
            }

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(Path(raw_directory), mutate_corpus=unversioned)
            )
        self.assertIn("RECORD_SCHEMA_INVALID", self.codes(result))

    def test_forged_external_receipt_cannot_support_complete_corpus(self) -> None:
        def forged_receipt(value):
            value["included_sources"][0]["identity"] = {
                "kind": "external-receipt",
                "value": "claimed-receipt",
                "raw_sha256": SHA_B,
                "raw_bytes": 1,
                "resolver_receipt": {
                    "receipt_id": "different-receipt",
                    "resolver_id": "official-source-adapter",
                    "canonical_url": (
                        "https://www.quantum-espresso.org/Doc/INPUT_PW.html"
                    ),
                    "retrieved_utc": "2026-07-24T12:00:00Z",
                    "raw_sha256": SHA_C,
                    "raw_bytes": 1,
                    "selected_sha256": SHA_C,
                    "selected_bytes": 1,
                    "selection_attestation_id": None,
                    "evidence_sha256": SHA_A,
                    "trust_mode": "unverified",
                    "registry_path": (
                        "registry/official-document-consumers.yaml"
                    ),
                    "registry_sha256": CONSUMER_REGISTRY_SHA256,
                    "trust_id": None,
                    "verification_status": "unverified",
                },
            }

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(Path(raw_directory), mutate_corpus=forged_receipt)
            )
        self.assertIn("SOURCE_RECEIPT_INVALID", self.codes(result))

    def test_central_authority_forbids_embedded_qe_vasp_and_siesta_content(
        self,
    ) -> None:
        def switch(
            authority_id,
            provider_id,
            version_scope,
            locator,
        ):
            def mutate(value):
                value["authority_id"] = authority_id
                value["provider_id"] = provider_id
                value["version_scope"] = copy.deepcopy(version_scope)
                value["included_sources"][0]["locator"] = locator
                value["included_sources"][0]["version_scope"] = copy.deepcopy(
                    version_scope
                )

            return mutate

        exact_75 = {
            "kind": "exact",
            "value": "7.5",
            "retrieved_utc": None,
            "snapshot_identity": None,
        }
        exact_54 = {
            "kind": "exact",
            "value": "5.4",
            "retrieved_utc": None,
            "snapshot_identity": None,
        }
        rolling = {
            "kind": "latest-at-retrieval",
            "value": None,
            "retrieved_utc": "2026-07-24T12:00:00Z",
            "snapshot_identity": {
                "kind": "revision",
                "value": "123456",
                "content_sha256": CP2K_SNAPSHOT_SHA256,
            },
        }
        cases = {
            "qe": switch(
                "qe-official-docs",
                "qe",
                exact_75,
                "https://www.quantum-espresso.org/Doc/INPUT_PW.html",
            ),
            "vasp": switch(
                "vasp-official-wiki",
                "vasp",
                rolling,
                "https://vasp.at/wiki/POSCAR",
            ),
            "siesta": switch(
                "siesta-official-docs",
                "siesta",
                exact_54,
                "https://docs.siesta-project.org/projects/siesta/en/5.4/reference/siesta.html",
            ),
        }
        for label, mutation in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_directory:
                result = self.validate(
                    write_bundle(
                        Path(raw_directory),
                        mutate_corpus=mutation,
                        mutate_slices=use_embedded_snapshot,
                    )
                )
            self.assertIn(
                "AUTHORITY_STORAGE_CEILING_EXCEEDED",
                self.codes(result),
            )

    def test_cp2k_embedded_content_must_match_canonical_pinned_snapshot(
        self,
    ) -> None:
        def forged_canonical_identity(value):
            identity = value["included_sources"][0]["identity"]
            identity["value"] = SHA_A
            identity["raw_sha256"] = SHA_A

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_corpus=forged_canonical_identity,
                )
            )
        self.assertIn(
            "AUTHORITY_CANONICAL_SNAPSHOT_MISMATCH",
            self.codes(result),
        )

    def test_license_review_cannot_widen_unknown_central_authority(self) -> None:
        def qe_corpus(value):
            scope = {
                "kind": "exact",
                "value": "7.5",
                "retrieved_utc": None,
                "snapshot_identity": None,
            }
            value["authority_id"] = "qe-official-docs"
            value["provider_id"] = "qe"
            value["version_scope"] = copy.deepcopy(scope)
            value["included_sources"][0]["version_scope"] = copy.deepcopy(
                scope
            )
            value["included_sources"][0]["locator"] = (
                "https://www.quantum-espresso.org/Doc/INPUT_PW.html"
            )

        def forged_open_review(value):
            value["authority_id"] = "qe-official-docs"
            value["license_identity"] = {
                "identifier": "GPL-2.0-or-later",
                "terms_urls": [
                    "https://www.quantum-espresso.org/Doc/INPUT_PW.html"
                ],
                "verification": "verified",
            }

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_corpus=qe_corpus,
                    mutate_license=forged_open_review,
                )
            )
        self.assertIn("LICENSE_AUTHORITY_CEILING_EXCEEDED", self.codes(result))

    def test_per_source_version_and_authority_scope_are_exact(self) -> None:
        def mixed_source_version(value):
            value["included_sources"][0]["version_scope"]["value"] = "2025.1"

        def wrong_authority_scope(value):
            rolling = {
                "kind": "latest-at-retrieval",
                "value": None,
                "retrieved_utc": "2026-07-24T12:00:00Z",
                "snapshot_identity": {
                    "kind": "revision",
                    "value": "123",
                    "content_sha256": CP2K_SNAPSHOT_SHA256,
                },
            }
            value["version_scope"] = copy.deepcopy(rolling)
            value["included_sources"][0]["version_scope"] = copy.deepcopy(
                rolling
            )

        cases = {
            "mixed-source": (
                mixed_source_version,
                "SOURCE_VERSION_SCOPE_MISMATCH",
            ),
            "authority-scope": (
                wrong_authority_scope,
                "AUTHORITY_VERSION_SCOPE_MISMATCH",
            ),
        }
        for label, (mutation, code) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_directory:
                result = self.validate(
                    write_bundle(Path(raw_directory), mutate_corpus=mutation)
                )
            self.assertIn(code, self.codes(result))

    def test_authority_scope_compatibility_is_value_exact_and_fail_closed(
        self,
    ) -> None:
        exact = {
            "scope": "exact",
            "exact_version": "abc123",
            "minimum_version": None,
            "maximum_version": None,
            "release_series": None,
        }
        release_series = {
            "scope": "release-series",
            "exact_version": None,
            "minimum_version": None,
            "maximum_version": None,
            "release_series": "2026.x",
        }
        latest = {
            "scope": "latest-at-retrieval",
            "exact_version": None,
            "minimum_version": None,
            "maximum_version": None,
            "release_series": None,
        }
        unversioned = {
            "scope": "unversioned",
            "exact_version": None,
            "minimum_version": None,
            "maximum_version": None,
            "release_series": None,
        }
        cases = (
            ("exact", "abc123", [exact], True),
            ("revision", "abc123", [exact], True),
            ("revision", "descriptive alias", [exact], False),
            ("release-line", "2026.x", [release_series], True),
            ("release-line", "2026", [release_series], False),
            ("latest-at-retrieval", None, [latest], True),
            ("unversioned", None, [unversioned], True),
            ("unversioned", "descriptive label", [unversioned], False),
        )
        for kind, value, registered, expected in cases:
            with self.subTest(kind=kind, value=value):
                self.assertEqual(
                    coverage_validator.authority_version_scope_compatible(
                        {
                            "kind": kind,
                            "value": value,
                            "retrieved_utc": None,
                            "snapshot_identity": None,
                        },
                        registered,
                    ),
                    expected,
                )

    def test_source_scope_compatibility_covers_every_corpus_scope(self) -> None:
        for kind, value in (
            ("exact", "1.2.3"),
            ("revision", "abc123"),
            ("release-line", "2026.x"),
            ("unversioned", None),
        ):
            corpus_scope = {
                "kind": kind,
                "value": value,
                "retrieved_utc": None,
                "snapshot_identity": None,
            }
            with self.subTest(kind=kind):
                self.assertTrue(
                    coverage_validator.source_version_scope_compatible(
                        copy.deepcopy(corpus_scope),
                        corpus_scope,
                        raw_sha256=SHA_A,
                    )
                )
                changed = copy.deepcopy(corpus_scope)
                changed["value"] = "different"
                self.assertFalse(
                    coverage_validator.source_version_scope_compatible(
                        changed,
                        corpus_scope,
                        raw_sha256=SHA_A,
                    )
                )

        rolling = {
            "kind": "latest-at-retrieval",
            "value": None,
            "retrieved_utc": "2026-07-24T12:00:00Z",
            "snapshot_identity": {
                "kind": "sha256",
                "value": SHA_B,
                "content_sha256": SHA_B,
            },
        }
        source = copy.deepcopy(rolling)
        source["snapshot_identity"] = {
            "kind": "sha256",
            "value": SHA_A,
            "content_sha256": SHA_A,
        }
        self.assertTrue(
            coverage_validator.source_version_scope_compatible(
                source,
                rolling,
                raw_sha256=SHA_A,
            )
        )
        self.assertFalse(
            coverage_validator.source_version_scope_compatible(
                source,
                rolling,
                raw_sha256=SHA_C,
            )
        )

    def test_embedded_slice_bytes_are_confined_and_rehashed(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            paths = write_bundle(
                directory,
                mutate_slices=use_embedded_snapshot,
            )
            (directory / "references" / "accelerators.md").unlink()
            missing = self.validate(paths)
        self.assertIn("SLICE_ARTIFACT_UNAVAILABLE", self.codes(missing))

        def escape(value):
            value["sources"][0]["slices"][0]["content_locator"] = (
                "../outside.md"
            )

        def bad_artifact_hash(value):
            value["sources"][0]["slices"][0]["artifact_sha256"] = SHA_A

        for label, mutation, code in (
            ("escape", escape, "RECORD_SCHEMA_INVALID"),
            (
                "artifact-hash",
                bad_artifact_hash,
                "SLICE_ARTIFACT_HASH_MISMATCH",
            ),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_directory:
                result = self.validate(
                    write_bundle(
                        Path(raw_directory),
                        mutate_slices=lambda value: (
                            use_embedded_snapshot(value),
                            mutation(value),
                        ),
                    )
                )
            self.assertIn(code, self.codes(result))

    def test_payload_hash_cannot_be_confused_with_whole_file_hash(self) -> None:
        def wrong_payload_basis(value):
            use_embedded_snapshot(value)
            source = value["sources"][0]
            item = source["slices"][0]
            item["byte_range"] = {
                "start_byte": 0,
                "end_byte_exclusive": 10,
            }
            item["selector"]["value"] = "0:10"
            source["preserved_ranges"] = [
                {
                    "preservation_id": "tail-byte-preservation",
                    "start_byte": 10,
                    "end_byte_exclusive": len(CP2K_SNAPSHOT_RAW),
                    "content_sha256": hashlib.sha256(
                        CP2K_SNAPSHOT_RAW[10:]
                    ).hexdigest(),
                    "reason": "The remaining exact source bytes are preserved.",
                }
            ]

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_slices=wrong_payload_basis,
                )
            )
        self.assertIn("SLICE_CONTENT_HASH_MISMATCH", self.codes(result))

    def test_transformer_and_source_partition_are_required(self) -> None:
        def remove_transformer(value):
            value["sources"][0].pop("transformer")

        def unreviewed_orphan(value):
            source = value["sources"][0]
            item = source["slices"][0]
            end = source["raw_source_extent_bytes"] - 1
            item["byte_range"]["end_byte_exclusive"] = end
            item["selector"]["value"] = f"0:{end}"
            item["content_sha256"] = SHA_A
            item["content_receipt"]["selected_sha256"] = SHA_A
            item["content_receipt"]["selected_bytes"] = end

        cases = {
            "transformer": (remove_transformer, "RECORD_SCHEMA_INVALID"),
            "orphan": (unreviewed_orphan, "SLICE_ORPHAN_RANGE_INVALID"),
        }
        for label, (mutation, code) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw_directory:
                result = self.validate(
                    write_bundle(Path(raw_directory), mutate_slices=mutation)
                )
            self.assertIn(code, self.codes(result))

    def test_protected_material_can_never_be_generically_embedded(self) -> None:
        def protected(value):
            rule = value["storage_rules"][0]
            rule["source_material_class"] = "restricted-potential"
            rule["assessment"] = "allowed"
            rule["allowed_storage_modes"] = ["embedded-open"]

        def protected_slice(value):
            value["sources"][0]["slices"][0][
                "source_material_class"
            ] = "restricted-potential"

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_license=protected,
                    mutate_slices=protected_slice,
                )
            )
        self.assertIn("LICENSE_PROTECTED_MATERIAL_INVALID", self.codes(result))

    def test_valid_partial_bundle_is_blocked_from_complete_assurance(self) -> None:
        def partial_corpus(value):
            value["status"] = "partial"
            value["limitations"] = [
                "The reviewed exclusions keep corpus assurance partial."
            ]

        def partial_slices(value):
            value["status"] = "partial"
            value["limitations"] = ["The corpus discovery is partial."]

        def partial_coverage(value):
            value["status"] = "partial"
            value["limitations"] = ["Coverage inherits a partial corpus."]

        with tempfile.TemporaryDirectory() as raw_directory:
            paths = write_bundle(
                Path(raw_directory),
                mutate_corpus=partial_corpus,
                mutate_slices=partial_slices,
                mutate_coverage=partial_coverage,
            )
            result = self.validate(paths)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.assurance_status, "partial")

    def test_reviewed_orphan_is_loss_bound_and_cannot_remain_complete(self) -> None:
        def orphan_with_informational_loss(value):
            value["status"] = "complete"
            value["limitations"] = []
            source = value["sources"][0]
            extent = source["raw_source_extent_bytes"]
            end = extent - 1
            item = source["slices"][0]
            item["byte_range"]["end_byte_exclusive"] = end
            item["selector"]["value"] = f"0:{end}"
            item["content_sha256"] = SHA_A
            item["content_receipt"]["selected_sha256"] = SHA_A
            item["content_receipt"]["selected_bytes"] = end
            source["reviewed_orphans"] = [
                {
                    "start_byte": end,
                    "end_byte_exclusive": extent,
                    "loss_id": "orphan-byte",
                    "disposition": "omitted",
                    "reason": "One source byte is not represented by a slice.",
                }
            ]
            source["loss_ledger"] = [
                {
                    "loss_id": "orphan-byte",
                    "category": "other",
                    "severity": "informational",
                    "disposition": "omitted",
                    "description": "One source byte was omitted.",
                    "affected_slice_ids": ["cp2k-accelerators"],
                }
            ]

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_slices=orphan_with_informational_loss,
                )
            )
        self.assertIn("SLICE_ORPHAN_PRESENT", self.codes(result))
        self.assertIn("COMPLETENESS_STATUS_OVERCLAIM", self.codes(result))

    def test_arbitrary_skill_id_cannot_self_attest_scope_or_coverage(self) -> None:
        def arbitrary_scope(value):
            value["skill_id"] = "invented-rigorous-calculations"

        def arbitrary_coverage(value):
            value["skill_id"] = "invented-rigorous-calculations"

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_scope_inventory=arbitrary_scope,
                    mutate_coverage=arbitrary_coverage,
                )
            )
        self.assertIn("SCOPE_SKILL_UNREGISTERED", self.codes(result))

    def test_consumer_provider_pair_requires_central_allowlist_binding(self) -> None:
        qe_skill = SKILL_REGISTRY["skills"]["qe-rigorous-calculations"]
        qe_skill_md = ROOT / qe_skill["path"] / "SKILL.md"

        def qe_scope(value):
            value["skill_id"] = "qe-rigorous-calculations"
            value["skill_registry_binding"].update(
                skill_path=qe_skill["path"],
                lifecycle=qe_skill["lifecycle"],
                source_tree_sha256=qe_skill["source_tree_sha256"],
            )
            value["skill_source_refs"] = [
                {
                    "path": f"{qe_skill['path']}/SKILL.md",
                    "sha256": hashlib.sha256(qe_skill_md.read_bytes()).hexdigest(),
                }
            ]

        def qe_coverage(value):
            value["skill_id"] = "qe-rigorous-calculations"
            value["consumer_binding_refs"][0]["binding_id"] = "qe-skill-qe-docs"

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_scope_inventory=qe_scope,
                    mutate_coverage=qe_coverage,
                )
            )
        self.assertIn("COVERAGE_CONSUMER_BINDING_INVALID", self.codes(result))

    def test_manual_scope_review_and_self_appointed_license_reviewer_are_partial(
        self,
    ) -> None:
        def overclaim_scope(value):
            value["status"] = "complete"
            value["limitations"] = []

        def overclaim_license(value):
            value["status"] = "complete"
            value["limitations"] = []
            value["license_identity"] = {
                "identifier": "GPL-2.0-or-later",
                "terms_urls": [
                    "https://github.com/cp2k/cp2k/blob/master/LICENSE"
                ],
                "verification": "verified",
            }
            rule = value["storage_rules"][0]
            rule["assessment"] = "allowed"
            for field in (
                "attribution_required",
                "notice_required",
                "modified_content_marking_required",
                "share_alike_required",
                "source_offer_required",
            ):
                rule[field] = True

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_scope_inventory=overclaim_scope,
                    mutate_license=overclaim_license,
                )
            )
        codes = self.codes(result)
        self.assertIn("SCOPE_INVENTORY_TRUST_UNVERIFIED", codes)
        self.assertIn("LICENSE_TRUST_UNVERIFIED", codes)
        self.assertIn("COMPLETENESS_STATUS_OVERCLAIM", codes)

    def test_unbound_processor_hashes_cannot_support_complete(self) -> None:
        def overclaim(value):
            value["status"] = "complete"
            value["limitations"] = []

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_corpus=overclaim,
                    mutate_slices=overclaim,
                )
            )
        self.assertIn("PROCESSOR_TRUST_UNVERIFIED", self.codes(result))
        self.assertIn("COMPLETENESS_STATUS_OVERCLAIM", self.codes(result))

    def test_attested_external_byte_ranges_can_reach_multi_slice_closure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)

            def local_ref(name: str, payload: bytes) -> dict[str, str]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                return {
                    "path": name,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }

            processor_ref = local_ref(
                "trust/processor.py",
                b"# exact processor fixture\n",
            )
            configuration_ref = local_ref(
                "trust/configuration.json",
                b'{"schema_version":"1.0"}\n',
            )
            dependency_ref = local_ref(
                "trust/dependencies.lock",
                b"fixture==1.0\n",
            )
            platform_ref = local_ref(
                "trust/platform-attestation.json",
                b'{"platform":"attested"}\n',
            )
            processor_attestation_ref = local_ref(
                "trust/processor-run.json",
                b'{"run":"exact-input-output"}\n',
            )
            first_selection_ref = local_ref(
                "trust/selection-a.json",
                b'{"selection":"a"}\n',
            )
            second_selection_ref = local_ref(
                "trust/selection-b.json",
                b'{"selection":"b"}\n',
            )

            corpus_data = corpus_record()
            corpus_data["status"] = "complete"
            corpus_data["limitations"] = []
            corpus_sha256 = SHA_C
            source_identity = copy.deepcopy(
                corpus_data["included_sources"][0]["identity"]
            )
            slices_data = slice_record(corpus_sha256, source_identity)
            slices_data["status"] = "complete"
            slices_data["limitations"] = []
            source = slices_data["sources"][0]
            extent = source["raw_source_extent_bytes"]
            split = extent // 2
            first = source["slices"][0]
            first["slice_id"] = "cp2k-accelerators-a"
            first["selector"]["value"] = f"0:{split}"
            first["byte_range"]["end_byte_exclusive"] = split
            first["content_sha256"] = SHA_A
            first["content_receipt"].update(
                selected_sha256=SHA_A,
                selected_bytes=split,
                selection_attestation_id="selection-a",
                trust_mode="platform-attested",
                registry_sha256=SHA_C,
                trust_id="cp2k-exact-selections",
                verification_status="platform-attested",
            )
            second = copy.deepcopy(first)
            second["slice_id"] = "cp2k-accelerators-b"
            second["ordinal"] = 1
            second["selector"]["value"] = f"{split}:{extent}"
            second["byte_range"] = {
                "start_byte": split,
                "end_byte_exclusive": extent,
            }
            second["content_sha256"] = SHA_B
            second["content_receipt"].update(
                receipt_id="cp2k-accelerators-receipt-b",
                selected_sha256=SHA_B,
                selected_bytes=extent - split,
                selection_attestation_id="selection-b",
            )
            source["slices"] = [first, second]
            transformer = source["transformer"]
            transformer.update(
                trust_mode="platform-attested",
                implementation_ref=copy.deepcopy(processor_ref),
                configuration_ref=copy.deepcopy(configuration_ref),
                dependency_lock_ref=copy.deepcopy(dependency_ref),
                attestation_id="transformer-run",
            )
            finalize_slice_processor(slices_data)
            output_sha256 = transformer["output_sha256"]

            def selection(
                item: dict[str, object],
                attestation_ref: dict[str, str],
            ) -> dict[str, object]:
                receipt = item["content_receipt"]
                return {
                    "attestation_id": receipt["selection_attestation_id"],
                    "source_id": source["source_id"],
                    "raw_sha256": source_identity["raw_sha256"],
                    "raw_bytes": source_identity["raw_bytes"],
                    "selector": copy.deepcopy(item["selector"]),
                    "selected_sha256": item["content_sha256"],
                    "selected_bytes": receipt["selected_bytes"],
                    "attestation_ref": copy.deepcopy(attestation_ref),
                }

            processor_entry = {
                "kind": "transformer",
                "version": "1.0",
                "implementation_ref": copy.deepcopy(processor_ref),
                "configuration_ref": copy.deepcopy(configuration_ref),
                "dependency_lock_ref": copy.deepcopy(dependency_ref),
                "attested_runs": [
                    {
                        "attestation_id": "transformer-run",
                        "input_sha256": source_identity["raw_sha256"],
                        "output_sha256": output_sha256,
                        "attestation_ref": copy.deepcopy(
                            processor_attestation_ref
                        ),
                    }
                ],
            }
            resolver_entry = {
                "authority_id": "cp2k-official-manual",
                "resolver_id": "cp2k-official-adapter",
                "trust_mode": "platform-attested",
                "evidence_sha256": [
                    first["content_receipt"]["evidence_sha256"]
                ],
                "implementation_ref": copy.deepcopy(processor_ref),
                "configuration_ref": copy.deepcopy(configuration_ref),
                "dependency_lock_ref": copy.deepcopy(dependency_ref),
                "platform_attestation_ref": copy.deepcopy(platform_ref),
                "attested_selections": [
                    selection(first, first_selection_ref),
                    selection(second, second_selection_ref),
                ],
            }
            consumer_registry = registry_yaml.load_yaml_strict(
                CONSUMER_REGISTRY_PATH,
                "official-document-consumers.yaml",
            )
            consumer_registry["processors"] = {
                "cp2k-manual-snapshot": processor_entry,
            }
            consumer_registry["resolver_trust"] = {
                "cp2k-exact-selections": resolver_entry,
            }
            authorities_data = registry_yaml.load_yaml_strict(
                ROOT / "registry" / "official-source-authorities.yaml",
                "official-source-authorities.yaml",
            )
            software_data = registry_yaml.load_yaml_strict(
                ROOT / "registry" / "software-registry.yaml",
                "software-registry.yaml",
            )
            authority_failures, projection = (
                coverage_validator.official_source_authorities.validate_and_project(
                    authorities_data,
                    software_data=software_data,
                    source_root=ROOT,
                )
            )
            self.assertEqual(authority_failures, [])
            self.assertEqual(
                coverage_validator.consumer_registry_validation_errors(
                    consumer_registry,
                    skills=SKILL_REGISTRY["skills"],
                    authorities=authorities_data["authorities"],
                    root=root,
                ),
                [],
            )
            corpus = coverage_validator.LoadedRecord(
                path=root / "corpus.json",
                raw_sha256=corpus_sha256,
                data=corpus_data,
            )
            record = coverage_validator.LoadedRecord(
                path=root / "slices.json",
                raw_sha256=SHA_A,
                data=slices_data,
            )
            findings: list[coverage_validator.Finding] = []
            coverage_validator._slice_manifest_findings(
                record,
                corpora={corpus_data["corpus_id"]: corpus},
                authorities=authorities_data["authorities"],
                authority_projection=projection,
                consumer_registry=consumer_registry,
                consumer_registry_sha256=SHA_C,
                source_root=root,
                repository_root=root,
                findings=findings,
            )
            self.assertEqual(findings, [])

            resolver_entry["attested_selections"][1]["selector"]["value"] = (
                f"{split + 1}:{extent}"
            )
            forged_findings: list[coverage_validator.Finding] = []
            coverage_validator._slice_manifest_findings(
                record,
                corpora={corpus_data["corpus_id"]: corpus},
                authorities=authorities_data["authorities"],
                authority_projection=projection,
                consumer_registry=consumer_registry,
                consumer_registry_sha256=SHA_C,
                source_root=root,
                repository_root=root,
                findings=forged_findings,
            )
            self.assertIn(
                "RESOLVER_SELECTION_ATTESTATION_INVALID",
                {item.code for item in forged_findings},
            )

            resolver_entry["attested_selections"][1]["selector"]["value"] = (
                f"{split}:{extent}"
            )
            transformer["trust_mode"] = "central-pinned"
            transformer["attestation_id"] = None
            central_findings: list[coverage_validator.Finding] = []
            coverage_validator._slice_manifest_findings(
                record,
                corpora={corpus_data["corpus_id"]: corpus},
                authorities=authorities_data["authorities"],
                authority_projection=projection,
                consumer_registry=consumer_registry,
                consumer_registry_sha256=SHA_C,
                source_root=root,
                repository_root=root,
                findings=central_findings,
            )
            central_codes = {item.code for item in central_findings}
            self.assertIn("PROCESSOR_EXECUTION_UNATTESTED", central_codes)
            self.assertIn("COMPLETENESS_STATUS_OVERCLAIM", central_codes)

    def test_orphan_loss_reference_and_blocking_severity_are_enforced(self) -> None:
        def add_orphan(value, *, include_loss: bool, severity: str) -> None:
            source = value["sources"][0]
            extent = source["raw_source_extent_bytes"]
            end = extent - 1
            item = source["slices"][0]
            item["byte_range"]["end_byte_exclusive"] = end
            item["selector"]["value"] = f"0:{end}"
            item["content_sha256"] = SHA_A
            item["content_receipt"]["selected_sha256"] = SHA_A
            item["content_receipt"]["selected_bytes"] = end
            source["reviewed_orphans"] = [
                {
                    "start_byte": end,
                    "end_byte_exclusive": extent,
                    "loss_id": "orphan-byte",
                    "disposition": "omitted",
                    "reason": "The final source byte is omitted.",
                }
            ]
            if include_loss:
                source["loss_ledger"] = [
                    {
                        "loss_id": "orphan-byte",
                        "category": "other",
                        "severity": severity,
                        "disposition": "omitted",
                        "description": "The final source byte is omitted.",
                        "affected_slice_ids": [],
                    }
                ]

        with tempfile.TemporaryDirectory() as raw_directory:
            unresolved = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_slices=lambda value: add_orphan(
                        value,
                        include_loss=False,
                        severity="informational",
                    ),
                )
            )
        self.assertIn("SLICE_ORPHAN_LOSS_INVALID", self.codes(unresolved))

        def blocking_slice(value):
            value["status"] = "blocked"
            value["limitations"] = []
            value["blockers"] = [
                {
                    "code": "blocking-orphan",
                    "description": "A blocking source byte is omitted.",
                }
            ]
            add_orphan(value, include_loss=True, severity="blocking")

        def blocking_coverage(value):
            value["status"] = "blocked"
            value["limitations"] = []
            value["blockers"] = [
                {
                    "code": "blocking-slice",
                    "description": "Coverage inherits a blocking slice loss.",
                }
            ]

        with tempfile.TemporaryDirectory() as raw_directory:
            blocked = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_slices=blocking_slice,
                    mutate_coverage=blocking_coverage,
                )
            )
        self.assertEqual(blocked.findings, ())
        self.assertEqual(blocked.assurance_status, "blocked")

    def test_preserved_source_ranges_are_exactly_rehashed(self) -> None:
        def snapshot_as_raw_source(value):
            identity = value["included_sources"][0]["identity"]
            identity["raw_sha256"] = CP2K_SNAPSHOT_SHA256
            identity["raw_bytes"] = len(CP2K_SNAPSHOT_RAW)

        def forged_preservation(value):
            use_embedded_snapshot(value)
            source = value["sources"][0]
            item = source["slices"][0]
            item["selector"]["layer"] = "raw-source"
            item["byte_range"]["end_byte_exclusive"] = 10
            item["selector"]["value"] = "0:10"
            item["content_sha256"] = hashlib.sha256(
                CP2K_SNAPSHOT_RAW[:10]
            ).hexdigest()
            source["preserved_ranges"] = [
                {
                    "preservation_id": "tail-preservation",
                    "start_byte": 10,
                    "end_byte_exclusive": len(CP2K_SNAPSHOT_RAW),
                    "content_sha256": SHA_A,
                    "reason": "Claimed exact preservation with a forged hash.",
                }
            ]

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_corpus=snapshot_as_raw_source,
                    mutate_slices=forged_preservation,
                )
            )
        self.assertIn("SLICE_PRESERVED_HASH_MISMATCH", self.codes(result))

    def test_scope_sources_must_stay_inside_the_registered_skill(self) -> None:
        qe_path = ROOT / "skills" / "qe-rigorous-calculations" / "SKILL.md"

        def other_skill_source(value):
            value["skill_source_refs"] = [
                {
                    "path": "skills/qe-rigorous-calculations/SKILL.md",
                    "sha256": hashlib.sha256(qe_path.read_bytes()).hexdigest(),
                }
            ]

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_scope_inventory=other_skill_source,
                )
            )
        self.assertIn("SCOPE_SOURCE_SCOPE_MISMATCH", self.codes(result))

    def test_deterministic_scope_requires_the_entire_registered_source_tree(
        self,
    ) -> None:
        tool_path = ROOT / "tools" / "validate_official_document_coverage.py"
        tool_ref = {
            "path": "tools/validate_official_document_coverage.py",
            "sha256": hashlib.sha256(tool_path.read_bytes()).hexdigest(),
        }

        def incomplete_deterministic_inventory(value):
            value["enumeration"] = {
                "method": "deterministic-extractor",
                "scope_complete": True,
                "extractor": {
                    "tool_id": "official-document-scope-extractor",
                    "tool_version": "1.0",
                    "trust_mode": "central-pinned",
                    "implementation_ref": copy.deepcopy(tool_ref),
                    "configuration_ref": copy.deepcopy(tool_ref),
                    "dependency_lock_ref": copy.deepcopy(tool_ref),
                    "input_sha256": value["skill_registry_binding"][
                        "source_tree_sha256"
                    ],
                    "output_sha256": canonical_json_sha256(
                        value["subjects"]
                    ),
                    "attestation_id": None,
                },
                "reviewed_by": "contract-steward",
                "reviewed_utc": "2026-07-24T12:00:00Z",
            }

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_scope_inventory=incomplete_deterministic_inventory,
                )
            )
        self.assertIn("SCOPE_SOURCE_SET_INCOMPLETE", self.codes(result))
        self.assertIn("PROCESSOR_TRUST_INVALID", self.codes(result))

    def test_scope_exact_tree_uses_the_canonical_non_pack_hash_domain(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            skill_path = Path("skills/example-skill")
            skill_root = root / skill_path
            claim_path = skill_root / "references" / "claims.md"
            pack_path = (
                skill_root
                / "references"
                / "official-source-pack"
                / "scope.json"
            )
            tool_path = root / "tools" / "scope_extractor.py"
            claim_path.parent.mkdir(parents=True)
            pack_path.parent.mkdir(parents=True)
            tool_path.parent.mkdir(parents=True)
            (skill_root / "SKILL.md").write_text(
                "# Example Skill\n",
                encoding="utf-8",
            )
            claim_path.write_text("claim\n", encoding="utf-8")
            pack_path.write_text('{"binding":"changes"}\n', encoding="utf-8")
            tool_path.write_text("# deterministic fixture\n", encoding="utf-8")
            digest = coverage_validator.skill_registry.source_tree_digest(
                skill_root
            )
            tool_ref = {
                "path": "tools/scope_extractor.py",
                "sha256": hashlib.sha256(tool_path.read_bytes()).hexdigest(),
            }
            extractor = {
                "tool_id": "scope-extractor",
                "tool_version": "1.0",
                "trust_mode": "central-pinned",
                "implementation_ref": copy.deepcopy(tool_ref),
                "configuration_ref": copy.deepcopy(tool_ref),
                "dependency_lock_ref": copy.deepcopy(tool_ref),
                "input_sha256": digest.sha256,
                "output_sha256": SHA_A,
                "attestation_id": None,
            }
            source_refs = [
                {
                    "path": "skills/example-skill/SKILL.md",
                    "sha256": hashlib.sha256(
                        (skill_root / "SKILL.md").read_bytes()
                    ).hexdigest(),
                },
                {
                    "path": "skills/example-skill/references/claims.md",
                    "sha256": hashlib.sha256(claim_path.read_bytes()).hexdigest(),
                },
            ]
            data = {
                "inventory_id": "example-scope",
                "skill_id": "example-skill",
                "skill_registry_binding": {
                    "registry_path": "registry/skill-registry.yaml",
                    "registry_sha256": SHA_C,
                    "skill_path": skill_path.as_posix(),
                    "lifecycle": "development",
                    "source_tree_hash_domain": (
                        coverage_validator.skill_registry.TREE_HASH_DOMAIN_NAME
                    ),
                    "source_tree_sha256": digest.sha256,
                },
                "status": "complete",
                "skill_source_refs": source_refs,
                "enumeration": {
                    "method": "deterministic-extractor",
                    "scope_complete": True,
                    "extractor": extractor,
                    "reviewed_by": "contract-steward",
                    "reviewed_utc": "2026-07-24T12:00:00Z",
                },
                "subjects": [
                    {
                        "subject_id": "example-claim",
                        "subject_kind": "claim",
                        "evidence_class": "repository-policy",
                        "origin_refs": [
                            {
                                "path": (
                                    "skills/example-skill/references/claims.md"
                                ),
                                "sha256": hashlib.sha256(
                                    claim_path.read_bytes()
                                ).hexdigest(),
                                "selector": {
                                    "kind": "whole-file",
                                    "value": "*",
                                },
                            }
                        ],
                        "statement": "A claim from the non-pack Skill tree.",
                    }
                ],
                "blockers": [],
                "limitations": [],
            }
            extractor["output_sha256"] = canonical_json_sha256(
                data["subjects"]
            )
            record = coverage_validator.LoadedRecord(
                path=root / "scope.json",
                raw_sha256=SHA_A,
                data=data,
            )
            skill_data = {
                "skills": {
                    "example-skill": {
                        "path": skill_path.as_posix(),
                        "lifecycle": "development",
                        "source_tree_sha256": digest.sha256,
                    }
                }
            }
            processor = {
                "kind": "extractor",
                "version": "1.0",
                "implementation_ref": copy.deepcopy(tool_ref),
                "configuration_ref": copy.deepcopy(tool_ref),
                "dependency_lock_ref": copy.deepcopy(tool_ref),
                "attested_runs": [],
            }
            findings: list[coverage_validator.Finding] = []
            coverage_validator._scope_inventory_findings(
                record,
                repository_root=root,
                skill_registry_data=skill_data,
                skill_registry_sha256=SHA_C,
                consumer_registry={
                    "processors": {"scope-extractor": processor},
                },
                findings=findings,
            )
            self.assertNotIn(
                "SCOPE_SOURCE_SET_INCOMPLETE",
                {item.code for item in findings},
            )

            data["skill_source_refs"] = source_refs[:1]
            omitted_findings: list[coverage_validator.Finding] = []
            coverage_validator._scope_inventory_findings(
                record,
                repository_root=root,
                skill_registry_data=skill_data,
                skill_registry_sha256=SHA_C,
                consumer_registry={
                    "processors": {"scope-extractor": processor},
                },
                findings=omitted_findings,
            )
            self.assertIn(
                "SCOPE_SOURCE_SET_INCOMPLETE",
                {item.code for item in omitted_findings},
            )

    def test_central_registry_hashes_are_content_bound(self) -> None:
        def bad_scope_registry_hash(value):
            value["skill_registry_binding"]["registry_sha256"] = "0" * 64

        def bad_consumer_registry_hash(value):
            value["consumer_binding_refs"][0]["registry_sha256"] = "0" * 64

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_scope_inventory=bad_scope_registry_hash,
                    mutate_coverage=bad_consumer_registry_hash,
                )
            )
        codes = self.codes(result)
        self.assertIn("SCOPE_SKILL_REGISTRY_BINDING_INVALID", codes)
        self.assertIn("COVERAGE_CONSUMER_REGISTRY_HASH_MISMATCH", codes)

    def test_forged_license_and_processor_trust_ids_fail_closed(self) -> None:
        tool_path = ROOT / "tools" / "validate_official_document_coverage.py"
        tool_ref = {
            "path": "tools/validate_official_document_coverage.py",
            "sha256": hashlib.sha256(tool_path.read_bytes()).hexdigest(),
        }

        def forged_processor(value):
            value["discovery"]["enumerator"].update(
                trust_mode="central-pinned",
                implementation_ref=copy.deepcopy(tool_ref),
                configuration_ref=copy.deepcopy(tool_ref),
                dependency_lock_ref=copy.deepcopy(tool_ref),
            )

        def forged_license(value):
            value["trust_attestation"].update(
                trust_mode="central-pinned",
                trust_id="invented-license-trust",
            )

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_corpus=forged_processor,
                    mutate_license=forged_license,
                )
            )
        codes = self.codes(result)
        self.assertIn("PROCESSOR_TRUST_INVALID", codes)
        self.assertIn("LICENSE_TRUST_INVALID", codes)

    def test_cross_record_source_and_transformer_hashes_must_match(self) -> None:
        def forged_slice_identity(value):
            identity = value["sources"][0]["source_identity"]
            identity["value"] = SHA_A
            identity["raw_sha256"] = SHA_A
            value["sources"][0]["transformer"]["input_raw_sha256"] = SHA_B

        with tempfile.TemporaryDirectory() as raw_directory:
            result = self.validate(
                write_bundle(
                    Path(raw_directory),
                    mutate_slices=forged_slice_identity,
                )
            )
        codes = self.codes(result)
        self.assertIn("SLICE_SOURCE_IDENTITY_MISMATCH", codes)
        self.assertIn("SLICE_TRANSFORMER_INPUT_MISMATCH", codes)

    def test_cli_rejects_duplicate_key_strict_json(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            (
                corpus,
                slices,
                license_review,
                scope_inventory,
                coverage,
            ) = write_bundle(directory)
            corpus.write_bytes(
                b'{"schema_version":"1.0","schema_version":"1.0"}\n'
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "validate_official_document_coverage.py"),
                    "--corpus",
                    str(corpus),
                    "--slices",
                    str(slices),
                    "--license-review",
                    str(license_review),
                    "--scope-inventory",
                    str(scope_inventory),
                    "--coverage",
                    str(coverage),
                    "--source-root",
                    str(directory),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("STRICT_JSON_INVALID", completed.stderr)


class ExactQueryAuthorityLocatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        compact = json.loads(
            (
                ROOT
                / "skills/vasp-rigorous-calculations/references/"
                "source-pack-input-catalog.json"
            ).read_text(encoding="utf-8")
        )
        cls.allowed = sorted(
            item["api_request_url"] for item in compact["pages"]
        )[0]

    def authority(
        self,
        *,
        query_policy: str = "exact-allowlist",
        allowed_query_urls: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "allowed_https_origins": ["https://www.vasp.at"],
            "content_policy": {
                "allowed_path_prefixes": ["/wiki/"],
                "query_policy": query_policy,
                "allowed_query_urls": (
                    [self.allowed]
                    if allowed_query_urls is None
                    else allowed_query_urls
                ),
                "fragment_policy": "forbidden",
            },
        }

    def test_exact_allowlist_accepts_only_the_exact_raw_query_url(self) -> None:
        authority = self.authority()
        self.assertTrue(
            coverage_validator._url_matches_authority(
                self.allowed,
                authority,
            )
        )
        self.assertTrue(
            coverage_validator._url_matches_authority(
                "https://www.vasp.at/wiki/INCAR",
                authority,
            )
        )

    def test_query_mutations_and_parser_ambiguities_are_rejected(self) -> None:
        base, query = self.allowed.split("?", 1)
        pairs = query.split("&")
        variants = {
            "parameter-added": self.allowed + "&extra=1",
            "parameter-removed": base + "?" + "&".join(pairs[:-1]),
            "parameter-changed": self.allowed.replace(
                "oldid=16120",
                "oldid=16121",
                1,
            ),
            "duplicate-key": self.allowed + "&oldid=16120",
            "alternate-encoding": self.allowed.replace("%7C", "%7c", 1),
            "alternate-order": base
            + "?"
            + "&".join([pairs[1], pairs[0], *pairs[2:]]),
            "wrong-path": self.allowed.replace(
                "/wiki/api.php",
                "/private/api.php",
                1,
            ),
            "wrong-origin": self.allowed.replace(
                "https://www.vasp.at/",
                "https://evil.example/",
                1,
            ),
            "userinfo": self.allowed.replace(
                "https://www.vasp.at/",
                "https://user@www.vasp.at/",
                1,
            ),
            "fragment": self.allowed + "#section",
        }
        authority = self.authority()
        for label, value in variants.items():
            with self.subTest(label=label):
                self.assertFalse(
                    coverage_validator._url_matches_authority(
                        value,
                        authority,
                    )
                )

    def test_forbidden_policy_rejects_every_query(self) -> None:
        authority = self.authority(
            query_policy="forbidden",
            allowed_query_urls=[],
        )
        self.assertFalse(
            coverage_validator._url_matches_authority(
                self.allowed,
                authority,
            )
        )
        self.assertTrue(
            coverage_validator._url_matches_authority(
                "https://www.vasp.at/wiki/INCAR",
                authority,
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
