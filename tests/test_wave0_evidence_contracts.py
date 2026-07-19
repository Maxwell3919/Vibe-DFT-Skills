"""Acceptance tests for the Wave 0 official-source and evidence records.

The schemas deliberately describe immutable, non-human evidence.  External
authority-registry checks, exact raw-byte hashing, and whole-bundle DAG checks
remain machine semantic obligations; compact helpers below pin those semantics
without pretending that JSON Schema can resolve files or authenticate humans.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bundle_semantics  # noqa: E402
import bundle_semantics_evidence  # noqa: E402
import official_source_authorities  # noqa: E402
from registry_yaml import load_yaml_strict  # noqa: E402

SCHEMA_PATHS = {
    "common": ROOT / "contracts" / "common-definitions-1.0.schema.json",
    "official": ROOT / "contracts" / "official-source-record.schema.json",
    "evidence": ROOT / "contracts" / "evidence-record.schema.json",
}
SCHEMAS = {
    name: json.loads(path.read_text(encoding="utf-8"))
    for name, path in SCHEMA_PATHS.items()
}
REGISTRY = Registry()
for schema in SCHEMAS.values():
    REGISTRY = REGISTRY.with_resource(
        schema["$id"], Resource.from_contents(schema)
    )
VALIDATORS = {
    name: Draft202012Validator(
        schema,
        registry=REGISTRY,
        format_checker=FormatChecker(),
    )
    for name, schema in SCHEMAS.items()
    if name != "common"
}

SHA_A = "a" * 64
SHA_B = "b" * 64
NOW = "2026-07-18T12:00:00Z"

OFFICIAL_OBLIGATIONS = {
    "OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH",
    "OFFICIAL_SOURCE_PROVIDER_REGISTRY_MATCH",
    "OFFICIAL_SOURCE_CONTENT_RAW_BYTES_HASH_MATCH",
    "OFFICIAL_SOURCE_PRESENT_ARTIFACT_HASH_RESOLVES",
    "OFFICIAL_SOURCE_PINNED_CANONICAL_SNAPSHOT_MATCH",
    "OFFICIAL_SOURCE_RESOLVER_REF_HASH_RESOLVES",
    "OFFICIAL_SOURCE_RESOLVER_EVIDENCE_MATCH",
    "OFFICIAL_SOURCE_RESOLVER_EVIDENCE_NOT_TRUST_ROOT",
    "OFFICIAL_SOURCE_EXTERNAL_TRUST_ADAPTER_VERIFIES",
    "OFFICIAL_SOURCE_VERSION_SCOPE_MATCH",
    "OFFICIAL_SOURCE_STATUS_CLAIM_CEILING_MATCH",
    "OFFICIAL_SOURCE_LICENSE_REDISTRIBUTION_MATCH",
    "OFFICIAL_SOURCE_RESTRICTED_CONTENT_NOT_EMBEDDED",
    "OFFICIAL_SOURCE_METADATA_ONLY_NOT_DOCUMENTED_CLAIM",
    "OFFICIAL_SOURCE_PARENT_REFS_PREEXIST_RECORD",
    "OFFICIAL_SOURCE_RECORD_REF_DAG_ACYCLIC",
    "OFFICIAL_SOURCE_PRIVACY_LABELS_SAFE",
}
EVIDENCE_OBLIGATIONS = {
    "EVIDENCE_SUBJECT_REF_HASH_RESOLVES",
    "EVIDENCE_SOURCE_REF_HASH_RESOLVES",
    "EVIDENCE_PARENT_REF_HASH_RESOLVES",
    "EVIDENCE_REF_ROLE_MATCH",
    "EVIDENCE_PRESENT_ARTIFACT_RAW_BYTES_HASH_MATCH",
    "EVIDENCE_STATUS_ARTIFACT_AVAILABILITY_MATCH",
    "EVIDENCE_KIND_RESULT_CLAIM_CEILING_MATCH",
    "EVIDENCE_NONHUMAN_OBSERVER_REQUIRED",
    "EVIDENCE_CANNOT_AUTHORIZE_EXECUTION",
    "EVIDENCE_CANNOT_ACCEPT_SCIENCE",
    "EVIDENCE_CANNOT_ESTABLISH_EXTERNAL_SOURCE_AUTHORITY",
    "EVIDENCE_PARENT_REFS_PREEXIST_RECORD",
    "EVIDENCE_RECORD_REF_DAG_ACYCLIC",
    "EVIDENCE_PRIVACY_LABELS_SAFE",
}


def producer() -> dict[str, Any]:
    return {
        "skill_id": "wave0-evidence-contracts",
        "skill_version": "1.0.0",
        "tool_id": "synthetic-evidence-builder",
        "tool_version": "1.0.0",
        "generated_utc": NOW,
    }


def record_ref(
    contract_name: str,
    record_id: str,
    role: str,
    sha256: str = SHA_A,
) -> dict[str, Any]:
    return {
        "contract_name": contract_name,
        "schema_version": "1.0",
        "record_id": record_id,
        "sha256": sha256,
        "role": role,
    }


def file_ref(
    *,
    role: str = "native-status-evidence",
    label: str = "scheduler-status.json",
    availability: str = "present",
    sha256: str | None = SHA_A,
    byte_count: int | None = 128,
    sensitivity: str = "public",
    redistribution: str = "redistributable",
) -> dict[str, Any]:
    return {
        "role": role,
        "label": label,
        "media_type": "application/json",
        "format": "json",
        "format_version": "1.0",
        "availability": availability,
        "sha256": sha256,
        "bytes": byte_count,
        "sensitivity": sensitivity,
        "redistribution": redistribution,
    }


def official_source() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "contract_name": "official-source-record",
        "source_record_id": "official-qe-pw-guide-750",
        "authority": {
            "authority_registry_id": "qe-official-docs",
            "verification_status": "verified",
            "provider_id": "qe",
            "provider_label": "Quantum ESPRESSO",
            "source_kind": "official-manual",
            "source_title": "PW User Guide",
            "canonical_url": "https://docs.example.invalid/qe/pw-user-guide",
        },
        "version_scope": {
            "scope": "exact",
            "exact_version": "7.5",
            "minimum_version": None,
            "maximum_version": None,
            "release_series": None,
        },
        "retrieval": {
            "status": "retrieved",
            "retrieval_url": "https://docs.example.invalid/qe/pw-user-guide",
            "attempted_utc": NOW,
            "retrieved_utc": NOW,
            "response_status": 200,
        },
        "content": {
            "status": "embedded-open",
            "identity_mode": "pinned-canonical-snapshot",
            "artifact": file_ref(
                role="official-source-content",
                label="qe-pw-user-guide.html",
            ),
            "raw_sha256": SHA_A,
            "bytes": 128,
            "resolver_record_ref": None,
            "trust_adapter": None,
            "pinned_source_ref": {
                "authority_registry_id": "qe-official-docs",
                "snapshot_id": "qe-docs-7-5-test-snapshot",
                "source_id": "pw-user-guide",
            },
            "trust_state": "canonical-snapshot-verified",
        },
        "license": {
            "status": "known-open",
            "identifier": "GPL-2.0-or-later",
            "terms_url": "https://docs.example.invalid/qe/license",
            "redistribution": "redistributable",
        },
        "parent_source_refs": [],
        "claim_ceiling": "documented_behavior_only",
        "limitations": ["The source supports documented behavior only."],
        "producer": producer(),
    }


def metadata_only_source() -> dict[str, Any]:
    data = official_source()
    data["source_record_id"] = "official-qe-metadata-unknown"
    data["authority"]["verification_status"] = "unknown"
    data["version_scope"] = {
        "scope": "unknown",
        "exact_version": None,
        "minimum_version": None,
        "maximum_version": None,
        "release_series": None,
    }
    data["retrieval"] = {
        "status": "metadata-only",
        "retrieval_url": "https://docs.example.invalid/qe/reference",
        "attempted_utc": NOW,
        "retrieved_utc": None,
        "response_status": 200,
    }
    data["content"] = {
        "status": "metadata-only",
        "identity_mode": "unresolved",
        "artifact": None,
        "raw_sha256": None,
        "bytes": None,
        "resolver_record_ref": None,
        "trust_adapter": None,
        "pinned_source_ref": None,
        "trust_state": "unresolved",
    }
    data["license"] = {
        "status": "unknown",
        "identifier": None,
        "terms_url": None,
        "redistribution": "unknown",
    }
    data["claim_ceiling"] = "no_positive_claim"
    return data


def restricted_external_source() -> dict[str, Any]:
    data = official_source()
    data["source_record_id"] = "official-vendor-reference-001"
    data["authority"].update(
        {
            "authority_registry_id": "vendor-official-reference",
            "provider_id": "vasp",
            "provider_label": "VASP",
            "source_title": "Vendor Reference",
            "canonical_url": "https://docs.example.invalid/vendor/reference",
        }
    )
    data["retrieval"] = {
        "status": "resolved-external",
        "retrieval_url": "https://docs.example.invalid/vendor/reference",
        "attempted_utc": NOW,
        "retrieved_utc": NOW,
        "response_status": None,
    }
    data["content"] = {
        "status": "externally-resolved",
        "identity_mode": "platform-external-adapter",
        "artifact": file_ref(
            role="official-source-content",
            label="vendor-reference.html",
            availability="external",
            sensitivity="restricted",
            redistribution="restricted",
        ),
        "raw_sha256": SHA_A,
        "bytes": 128,
        "resolver_record_ref": record_ref(
            "evidence-record",
            "evidence-resolver-receipt-001",
            "official-source-resolver",
            SHA_B,
        ),
        "trust_adapter": {
            "adapter_registry_id": "trusted-source-resolver",
            "opaque_handle": "vendor-reference-handle-001",
            "verification_mode": "exact-raw-bytes",
        },
        "pinned_source_ref": None,
        "trust_state": "requires-external-trust",
    }
    data["license"] = {
        "status": "known-restricted",
        "identifier": "Vendor terms",
        "terms_url": "https://docs.example.invalid/vendor/terms",
        "redistribution": "restricted",
    }
    data["claim_ceiling"] = "documented_behavior_only"
    return data


def evidence_record(kind: str = "scheduler-observation") -> dict[str, Any]:
    if kind in {"input-validation", "structure-observation"}:
        ceiling = "input_gates_only"
    elif kind in {"convergence-study", "numerical-observation"}:
        ceiling = "numerical_candidate_only"
    else:
        ceiling = "technical_run_gates_only"
    return {
        "schema_version": "1.0",
        "contract_name": "evidence-record",
        "evidence_id": f"evidence-{kind}-001",
        "evidence_kind": kind,
        "status": "present",
        "observed_utc": NOW,
        "observed_by": {
            "actor_type": "deterministic-tool",
            "actor_id": "wave0-evidence-validator",
            "role": "evidence-observer",
        },
        "subject_refs": [
            record_ref(
                "execution-record",
                "execution-synthetic-001",
                "evidence-subject",
            )
        ],
        "source_refs": [
            record_ref(
                "official-source-record",
                "official-qe-pw-guide-750",
                "evidence-source",
            )
        ],
        "parent_evidence_refs": [],
        "artifacts": [file_ref()],
        "observation": {
            "result": "pass",
            "finding_codes": [],
            "summary": "The normalized synthetic observation passed.",
        },
        "claim_ceiling": ceiling,
        "authority_limits": {
            "may_authorize_execution": False,
            "may_assert_human_identity": False,
            "may_accept_scientific_claim": False,
            "may_establish_external_source_authority": False,
        },
        "limitations": ["This non-human record is evidence only."],
        "producer": producer(),
    }


def unknown_evidence() -> dict[str, Any]:
    data = evidence_record()
    data["evidence_id"] = "evidence-scheduler-unknown"
    data["status"] = "unknown"
    data["observed_utc"] = None
    data["artifacts"] = []
    data["observation"] = {
        "result": "unknown",
        "finding_codes": ["evidence-status-unknown"],
        "summary": "The observation status is unknown.",
    }
    data["claim_ceiling"] = "no_positive_claim"
    return data


def resolver_receipt() -> dict[str, Any]:
    data = evidence_record("artifact-integrity")
    data["evidence_id"] = "evidence-resolver-receipt-001"
    data["subject_refs"] = [
        record_ref(
            "environment-profile",
            "authority-registry-snapshot-001",
            "evidence-subject",
        )
    ]
    data["source_refs"] = []
    data["artifacts"] = [
        file_ref(
            role="resolver-receipt",
            label="resolver-receipt.json",
            sha256=SHA_B,
        )
    ]
    data["observation"]["summary"] = "The resolver emitted a provenance receipt only."
    data["limitations"] = [
        "The receipt is not an external authority or a copy of restricted source text."
    ]
    return data


def raw_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def present_artifact_findings(
    record: dict[str, Any],
    raw_by_label: dict[str, bytes],
) -> set[str]:
    """Evaluate the exact-byte artifact obligations for the two records."""

    if record["contract_name"] == "official-source-record":
        artifacts = [record["content"]["artifact"]]
        missing_code = "OFFICIAL_SOURCE_PRESENT_ARTIFACT_HASH_RESOLVES"
        mismatch_code = "OFFICIAL_SOURCE_CONTENT_RAW_BYTES_HASH_MATCH"
    else:
        artifacts = record["artifacts"]
        missing_code = "EVIDENCE_PRESENT_ARTIFACT_RAW_BYTES_HASH_MATCH"
        mismatch_code = missing_code

    findings: set[str] = set()
    for artifact in artifacts:
        if artifact is None or artifact["availability"] != "present":
            continue
        raw = raw_by_label.get(artifact["label"])
        if raw is None:
            findings.add(missing_code)
            continue
        digest = raw_sha256(raw)
        if artifact["sha256"] != digest or artifact["bytes"] != len(raw):
            findings.add(mismatch_code)
        if record["contract_name"] == "official-source-record" and (
            record["content"]["raw_sha256"] != digest
            or record["content"]["bytes"] != len(raw)
        ):
            findings.add(mismatch_code)
    return findings


def iter_record_refs(node: object) -> Iterable[dict[str, Any]]:
    if isinstance(node, dict):
        if set(node) == {
            "contract_name",
            "schema_version",
            "record_id",
            "sha256",
            "role",
        }:
            yield node
            return
        for value in node.values():
            yield from iter_record_refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from iter_record_refs(value)


def record_key(record: dict[str, Any]) -> tuple[str, str]:
    id_fields = {
        "official-source-record": "source_record_id",
        "evidence-record": "evidence_id",
    }
    contract_name = record["contract_name"]
    return contract_name, record[id_fields[contract_name]]


def bundle_findings(
    records: list[dict[str, Any]],
    raw_by_key: dict[tuple[str, str], bytes],
) -> set[str]:
    """Pin exact-raw-byte resolution and global recordRef DAG semantics."""

    keys = {record_key(record) for record in records}
    edges: dict[tuple[str, str], set[tuple[str, str]]] = {
        key: set() for key in keys
    }
    findings: set[str] = set()
    for record in records:
        source = record_key(record)
        for ref in iter_record_refs(record):
            target = (ref["contract_name"], ref["record_id"])
            if target not in keys:
                findings.add("RECORD_REF_UNRESOLVED")
                continue
            edges[source].add(target)
            if ref["sha256"] != raw_sha256(raw_by_key[target]):
                findings.add("RECORD_REF_RAW_BYTES_HASH_MISMATCH")

    state: dict[tuple[str, str], int] = {}

    def visit(node: tuple[str, str]) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        if any(visit(target) for target in edges[node]):
            return True
        state[node] = 2
        return False

    if any(visit(node) for node in edges if state.get(node, 0) == 0):
        findings.add("RECORD_REF_DAG_CYCLE")
    return findings


def authority_snapshots(*, include_adapter: bool = False) -> dict[str, Any]:
    restricted = restricted_external_source()
    qe_version_scope = copy.deepcopy(official_source()["version_scope"])
    restricted_version_scope = copy.deepcopy(restricted["version_scope"])
    snapshots: dict[str, Any] = {
        "official_source_authorities": {
            "qe-official-docs": {
                "lifecycle": "active",
                "provider_id": "qe",
                "allowed_https_origins": ["https://docs.example.invalid"],
                "allowed_path_prefixes": ["/qe/"],
                "locator_policy": {
                    "allowed_origins": ["https://docs.example.invalid"],
                    "allowed_path_prefixes": ["/qe/"],
                },
                "canonical_urls": ["https://docs.example.invalid/qe/"],
                "source_kinds": ["official-manual"],
                "version_scopes": [qe_version_scope],
                "content_identity_policy": {
                    "mode": "canonical-pinned-open-snapshot-or-platform-adapter",
                    "unpinned_action": "adapter-required",
                },
                "canonical_snapshot": {
                    "snapshot_id": "qe-docs-7-5-test-snapshot",
                    "manifest_raw_sha256": SHA_B,
                    "integrity_verified": True,
                    "sources_by_id": {
                        "pw-user-guide": {
                            "canonical_url": "https://docs.example.invalid/qe/pw-user-guide",
                            "version_scope": qe_version_scope,
                            "raw_sha256": SHA_A,
                            "bytes": 128,
                        }
                    },
                },
                "license_status": "known-open",
                "license_identifier": "GPL-2.0-or-later",
                "license_terms_urls": ["https://docs.example.invalid/qe/license"],
                "redistribution": ["redistributable"],
            },
            "vendor-official-reference": {
                "lifecycle": "active",
                "provider_id": "vasp",
                "allowed_https_origins": ["https://docs.example.invalid"],
                "allowed_path_prefixes": ["/vendor/"],
                "locator_policy": {
                    "allowed_origins": ["https://docs.example.invalid"],
                    "allowed_path_prefixes": ["/vendor/"],
                },
                "canonical_urls": ["https://docs.example.invalid/vendor/"],
                "source_kinds": ["official-manual"],
                "version_scopes": [restricted_version_scope],
                "content_identity_policy": {
                    "mode": "platform-adapter-only",
                    "unpinned_action": "adapter-required",
                },
                "canonical_snapshot": None,
                "license_status": "known-restricted",
                "license_identifier": "Vendor terms",
                "license_terms_urls": ["https://docs.example.invalid/vendor/terms"],
                "redistribution": ["runtime-only", "restricted"],
            },
        },
        "external_trust_adapter_results": {},
    }
    if include_adapter:
        content = restricted["content"]
        authority = restricted["authority"]
        adapter = content["trust_adapter"]
        snapshots["external_trust_adapter_results"] = {
            adapter["adapter_registry_id"]: {
                adapter["opaque_handle"]: {
                    "status": "verified",
                    "adapter_registry_id": adapter["adapter_registry_id"],
                    "opaque_handle": adapter["opaque_handle"],
                    "authority_registry_id": authority["authority_registry_id"],
                    "provider_id": authority["provider_id"],
                    "canonical_url": authority["canonical_url"],
                    "version_scope": copy.deepcopy(restricted["version_scope"]),
                    "raw_sha256": content["raw_sha256"],
                    "bytes": content["bytes"],
                }
            }
        }
    return snapshots


def record_view(
    data: dict[str, Any],
    *,
    raw_sha256_value: str,
    index: int,
    record_id: str | None = None,
) -> dict[str, Any]:
    id_fields = {
        "official-source-record": "source_record_id",
        "evidence-record": "evidence_id",
        "execution-record": "execution_id",
    }
    contract_name = data["contract_name"]
    selected_id = record_id or data[id_fields[contract_name]]
    return {
        "data": data,
        "raw_sha256": raw_sha256_value,
        "index": index,
        "lifecycle": "active",
        "integrity_verified_active": True,
        "contract_name": contract_name,
        "schema_version": data.get("schema_version", "1.0"),
        "record_id": selected_id,
    }


def official_context(
    value: dict[str, Any],
    *,
    include_adapter: bool = False,
) -> dict[str, Any]:
    records: dict[tuple[str, str, str], dict[str, Any]] = {}
    artifacts: dict[str, dict[str, Any]] = {}
    if value["content"]["status"] == "embedded-open":
        artifact = value["content"]["artifact"]
        artifacts[artifact["label"]] = {
            "label": artifact["label"],
            "index": 0,
            "metadata": {"availability": "present"},
            "raw_sha256": artifact["sha256"],
            "bytes": artifact["bytes"],
            "integrity_verified": True,
            "parser_observations": (),
        }
    elif value["content"]["status"] == "externally-resolved":
        receipt = resolver_receipt()
        records[("evidence-record", "1.0", receipt["evidence_id"])] = record_view(
            receipt,
            raw_sha256_value=SHA_B,
            index=1,
        )
        receipt_artifact = receipt["artifacts"][0]
        artifacts[receipt_artifact["label"]] = {
            "label": receipt_artifact["label"],
            "index": 0,
            "metadata": {"availability": "present"},
            "raw_sha256": receipt_artifact["sha256"],
            "bytes": receipt_artifact["bytes"],
            "integrity_verified": True,
            "parser_observations": (),
        }
    return {
        "current_record": record_view(
            value,
            raw_sha256_value=SHA_A,
            index=2,
        ),
        "current_record_index": 2,
        "records_by_identity": records,
        "artifacts_by_label": artifacts,
        "core_checks": {"record-reference-dag": {"status": "pass"}},
        "registry_snapshots": authority_snapshots(include_adapter=include_adapter),
    }


def evidence_context(value: dict[str, Any]) -> dict[str, Any]:
    execution = {
        "contract_name": "execution-record",
        "schema_version": "1.0",
        "execution_id": "execution-synthetic-001",
    }
    return {
        "current_record": record_view(
            value,
            raw_sha256_value=SHA_B,
            index=2,
        ),
        "current_record_index": 2,
        "records_by_identity": {
            ("execution-record", "1.0", "execution-synthetic-001"): record_view(
                execution,
                raw_sha256_value=SHA_A,
                index=0,
            ),
            ("official-source-record", "1.0", "official-qe-pw-guide-750"): record_view(
                official_source(),
                raw_sha256_value=SHA_A,
                index=1,
            ),
        },
        "artifacts_by_label": {
            "scheduler-status.json": {
                "label": "scheduler-status.json",
                "index": 0,
                "metadata": {"availability": "present"},
                "raw_sha256": SHA_A,
                "bytes": 128,
                "integrity_verified": True,
                "parser_observations": (),
            }
        },
        "core_checks": {"record-reference-dag": {"status": "pass"}},
        "registry_snapshots": authority_snapshots(),
    }


class Wave0EvidenceContractTests(unittest.TestCase):
    def assert_valid(self, name: str, value: dict[str, Any]) -> None:
        errors = sorted(VALIDATORS[name].iter_errors(value), key=lambda item: list(item.path))
        self.assertEqual([], [error.message for error in errors])

    def assert_invalid(self, name: str, value: dict[str, Any]) -> None:
        self.assertTrue(list(VALIDATORS[name].iter_errors(value)))

    def test_canonical_identity_strictness_and_shared_definitions(self) -> None:
        expected = {
            "official": ("official-source-record", "source_record_id"),
            "evidence": ("evidence-record", "evidence_id"),
        }
        for name, (contract_name, id_field) in expected.items():
            with self.subTest(schema=name):
                schema = SCHEMAS[name]
                self.assertEqual(schema["x-vibe-document-kind"], "content-addressed-record")
                self.assertEqual(schema["x-vibe-record-id-field"], id_field)
                self.assertFalse(schema["additionalProperties"])
                self.assertIn(id_field, schema["required"])
                self.assertEqual(schema["properties"]["contract_name"]["const"], contract_name)
                serialized = json.dumps(schema)
                for definition in ("recordRef", "fileRef", "producer", "claimCeiling"):
                    self.assertIn(f"#/$defs/{definition}", serialized)

        unexpected = official_source()
        unexpected["record_id"] = "generic-id-is-forbidden"
        self.assert_invalid("official", unexpected)
        missing_id = evidence_record()
        del missing_id["evidence_id"]
        self.assert_invalid("evidence", missing_id)

    def test_machine_semantic_obligations_and_trust_metadata_are_exact(self) -> None:
        self.assertEqual(
            set(SCHEMAS["official"]["x-vibe-semantic-obligations"]),
            OFFICIAL_OBLIGATIONS,
        )
        self.assertEqual(
            set(SCHEMAS["evidence"]["x-vibe-semantic-obligations"]),
            EVIDENCE_OBLIGATIONS,
        )
        for name, keyword in (
            ("official", "x-vibe-content-hash-semantics"),
            ("evidence", "x-vibe-artifact-hash-semantics"),
        ):
            semantics = SCHEMAS[name][keyword]
            self.assertEqual(semantics["byte_basis"], "exact-raw-file-bytes")
            self.assertEqual(semantics["canonicalization"], "none")
            self.assertFalse(semantics["placeholder_hash_counts_as_resolved_evidence"])

        boundary = SCHEMAS["evidence"]["x-vibe-authority-boundary"]
        self.assertFalse(boundary["may_authorize_execution"])
        self.assertFalse(boundary["may_assert_human_identity"])
        self.assertFalse(boundary["may_accept_scientific_claim"])
        self.assertFalse(boundary["may_establish_external_source_authority"])
        official_boundary = SCHEMAS["official"]["x-vibe-trust-boundary"]
        self.assertFalse(official_boundary["bundle_resolver_evidence_is_trust_root"])
        self.assertFalse(official_boundary["external_adapter_result_is_stored_in_record"])
        self.assertEqual(official_boundary["missing_external_adapter_requires_exit"], 3)

    def test_production_evaluator_accounts_every_obligation_with_frozen_shape(self) -> None:
        cases = (
            (OFFICIAL_OBLIGATIONS, official_context(official_source())),
            (EVIDENCE_OBLIGATIONS, evidence_context(evidence_record())),
        )
        expected_keys = {
            "obligation_id",
            "status",
            "finding_codes",
            "location",
            "message",
            "handler_id",
        }
        for obligations, context in cases:
            with self.subTest(record=context["current_record"]["contract_name"]):
                rows = bundle_semantics_evidence.evaluate(sorted(obligations), context)
                self.assertEqual(len(rows), len(obligations))
                self.assertEqual({row["obligation_id"] for row in rows}, obligations)
                self.assertTrue(all(set(row) == expected_keys for row in rows))
                self.assertTrue(all(row["handler_id"] == "bundle-semantics-evidence-v1" for row in rows))
                self.assertTrue(all(row["status"] == "pass" for row in rows), rows)

        unknown = bundle_semantics_evidence.evaluate(
            ["UNREGISTERED_EVIDENCE_OBLIGATION"],
            evidence_context(evidence_record()),
        )
        self.assertEqual(unknown[0]["obligation_id"], "UNREGISTERED_EVIDENCE_OBLIGATION")
        self.assertEqual(unknown[0]["status"], "blocked")
        self.assertEqual(unknown[0]["finding_codes"], ["OBLIGATION_HANDLER_UNAVAILABLE"])
        unknown_without_context = bundle_semantics_evidence.evaluate(
            ["UNREGISTERED_EVIDENCE_OBLIGATION"],
            {},
        )
        self.assertEqual(
            unknown_without_context[0]["finding_codes"],
            ["OBLIGATION_HANDLER_UNAVAILABLE"],
        )

    def test_fixed_builtin_dispatcher_routes_both_evidence_contracts(self) -> None:
        self.assertEqual(
            bundle_semantics_evidence.CONTRACT_NAMES,
            ("official-source-record", "evidence-record"),
        )
        cases = (
            (
                "official-source-record",
                OFFICIAL_OBLIGATIONS,
                official_context(official_source()),
            ),
            (
                "evidence-record",
                EVIDENCE_OBLIGATIONS,
                evidence_context(evidence_record()),
            ),
        )
        for contract_name, obligation_ids, context in cases:
            with self.subTest(contract_name=contract_name):
                current = context["current_record"]
                identity = (
                    current["contract_name"],
                    current["schema_version"],
                    current["record_id"],
                )
                context["records_by_identity"][identity] = current
                context["core_checks"] = {
                    handler_id: {"status": "pass", "finding_codes": []}
                    for handler_id in (
                        "record-reference-dag",
                        "record-reference-integrity",
                        "artifact-integrity",
                        "privacy-boundary",
                    )
                }
                evaluator = bundle_semantics.builtin_evaluator(contract_name)
                self.assertIs(evaluator, bundle_semantics_evidence.evaluate)
                rows = bundle_semantics.evaluate_advertised_obligations(
                    sorted(obligation_ids),
                    context,
                    evaluator=evaluator,
                )
                self.assertEqual(len(rows), len(obligation_ids))
                self.assertEqual(
                    {row["obligation_id"] for row in rows}, obligation_ids
                )
                self.assertTrue(all(row["status"] == "pass" for row in rows), rows)
                self.assertFalse(
                    any(
                        "OBLIGATION_HANDLER_UNAVAILABLE" in row["finding_codes"]
                        for row in rows
                    ),
                    rows,
                )

    def test_cp2k_repository_snapshot_pin_routes_without_external_adapter(self) -> None:
        authorities = official_source_authorities.load_registry()
        software = load_yaml_strict(
            ROOT / "registry" / "software-registry.yaml",
            "software-registry.yaml",
        )
        projection = official_source_authorities.active_authority_snapshot(
            authorities,
            software_data=software,
            source_root=ROOT,
        )
        self.assertEqual(
            {
                authority_id: (
                    entry["license_status"],
                    tuple(entry["redistribution"]),
                )
                for authority_id, entry in projection.items()
            },
            {
                "qe-official-docs": ("unknown", ("unknown",)),
                "vasp-official-wiki": (
                    "known-restricted",
                    ("runtime-only", "restricted"),
                ),
                "cp2k-official-manual": ("known-open", ("redistributable",)),
                "siesta-official-docs": (
                    "known-restricted",
                    ("runtime-only", "restricted"),
                ),
            },
        )
        cp2k = projection["cp2k-official-manual"]
        snapshot = cp2k["canonical_snapshot"]
        self.assertIsNotNone(snapshot)
        self.assertTrue(snapshot["integrity_verified"])
        self.assertEqual(len(snapshot["sources_by_id"]), 86)
        for authority_id in (
            "qe-official-docs",
            "vasp-official-wiki",
            "siesta-official-docs",
        ):
            self.assertIsNone(projection[authority_id]["canonical_snapshot"])
            self.assertEqual(
                projection[authority_id]["content_identity_policy"]["mode"],
                "platform-adapter-only",
            )

        source_id = "dft"
        source = snapshot["sources_by_id"][source_id]
        snapshot_raw = (
            ROOT
            / "skills"
            / "cp2k-rigorous-calculations"
            / "references"
            / "official-manual"
            / "dft.md"
        ).read_bytes()
        self.assertEqual(hashlib.sha256(snapshot_raw).hexdigest(), source["raw_sha256"])
        self.assertEqual(len(snapshot_raw), source["bytes"])

        value = official_source()
        value["source_record_id"] = "official-cp2k-dft-2026-2"
        value["authority"].update(
            {
                "authority_registry_id": "cp2k-official-manual",
                "provider_id": "cp2k",
                "provider_label": "CP2K",
                "source_title": "CP2K DFT reference",
                "canonical_url": source["canonical_url"],
            }
        )
        value["version_scope"] = copy.deepcopy(source["version_scope"])
        value["retrieval"]["retrieval_url"] = source["canonical_url"]
        value["content"].update(
            {
                "artifact": file_ref(
                    role="official-source-content",
                    label="cp2k-dft.md",
                    sha256=source["raw_sha256"],
                    byte_count=source["bytes"],
                ),
                "raw_sha256": source["raw_sha256"],
                "bytes": source["bytes"],
                "pinned_source_ref": {
                    "authority_registry_id": "cp2k-official-manual",
                    "snapshot_id": snapshot["snapshot_id"],
                    "source_id": source_id,
                },
            }
        )
        value["license"] = {
            "status": "known-open",
            "identifier": "GPL-2.0-or-later",
            "terms_url": "https://github.com/cp2k/cp2k/blob/master/LICENSE",
            "redistribution": "redistributable",
        }
        self.assert_valid("official", value)

        context = official_context(value)
        context["registry_snapshots"]["official_source_authorities"] = projection
        current = context["current_record"]
        context["records_by_identity"][
            (current["contract_name"], current["schema_version"], current["record_id"])
        ] = current
        context["core_checks"] = {
            handler_id: {"status": "pass", "finding_codes": []}
            for handler_id in (
                "record-reference-dag",
                "record-reference-integrity",
                "artifact-integrity",
                "privacy-boundary",
            )
        }
        evaluator = bundle_semantics.builtin_evaluator("official-source-record")
        rows = bundle_semantics.evaluate_advertised_obligations(
            sorted(OFFICIAL_OBLIGATIONS),
            context,
            evaluator=evaluator,
        )
        self.assertTrue(all(row["status"] == "pass" for row in rows), rows)

    def test_restricted_source_receipt_without_platform_adapter_is_exit_three_state(self) -> None:
        value = restricted_external_source()
        context = official_context(value, include_adapter=False)
        rows = bundle_semantics_evidence.evaluate(sorted(OFFICIAL_OBLIGATIONS), context)
        by_id = {row["obligation_id"]: row for row in rows}
        expected_blocked = {
            "OFFICIAL_SOURCE_CONTENT_RAW_BYTES_HASH_MATCH",
            "OFFICIAL_SOURCE_RESOLVER_EVIDENCE_NOT_TRUST_ROOT",
            "OFFICIAL_SOURCE_EXTERNAL_TRUST_ADAPTER_VERIFIES",
            "OFFICIAL_SOURCE_STATUS_CLAIM_CEILING_MATCH",
        }
        self.assertEqual(
            {key for key, row in by_id.items() if row["status"] == "blocked"},
            expected_blocked,
        )
        self.assertFalse(any(row["status"] == "fail" for row in rows), rows)
        for obligation_id in expected_blocked:
            self.assertIn(
                "OFFICIAL_SOURCE_EXTERNAL_TRUST_REQUIRED",
                by_id[obligation_id]["finding_codes"],
            )
        # The dispatcher maps any blocked obligation to requires_external_trust / exit 3.
        self.assertEqual(3 if any(row["status"] == "blocked" for row in rows) else 0, 3)

    def test_platform_injected_adapter_can_verify_restricted_source_without_embedding_text(self) -> None:
        value = restricted_external_source()
        context = official_context(value, include_adapter=True)
        rows = bundle_semantics_evidence.evaluate(sorted(OFFICIAL_OBLIGATIONS), context)
        self.assertTrue(all(row["status"] == "pass" for row in rows), rows)
        self.assertNotIn("vendor-reference.html", context["artifacts_by_label"])
        self.assertEqual(value["content"]["artifact"]["availability"], "external")
        self.assertEqual(value["content"]["trust_state"], "requires-external-trust")
        self.assertNotIn("full_text", value["content"])

    def test_forged_external_resolution_and_adapter_mismatches_fail_closed(self) -> None:
        value = restricted_external_source()
        missing_ref = copy.deepcopy(value)
        missing_ref["content"]["resolver_record_ref"] = None
        self.assert_invalid("official", missing_ref)

        missing_hash = copy.deepcopy(value)
        missing_hash["content"]["raw_sha256"] = None
        missing_hash["content"]["artifact"]["sha256"] = None
        self.assert_invalid("official", missing_hash)

        self_declared_verified = copy.deepcopy(value)
        self_declared_verified["content"]["trust_adapter"]["verified"] = True
        self.assert_invalid("official", self_declared_verified)

        self_authorizing_receipt = resolver_receipt()
        self_authorizing_receipt["authority_limits"][
            "may_establish_external_source_authority"
        ] = True
        self.assert_invalid("evidence", self_authorizing_receipt)

        context = official_context(value, include_adapter=True)
        adapters = context["registry_snapshots"]["external_trust_adapter_results"]
        result = adapters["trusted-source-resolver"]["vendor-reference-handle-001"]
        result["version_scope"] = {
            "scope": "exact",
            "exact_version": "forged-version",
            "minimum_version": None,
            "maximum_version": None,
            "release_series": None,
        }
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_EXTERNAL_TRUST_ADAPTER_VERIFIES"],
            context,
        )[0]
        self.assertEqual(row["status"], "fail")
        self.assertEqual(
            row["finding_codes"],
            ["OFFICIAL_SOURCE_EXTERNAL_TRUST_MISMATCH"],
        )

        authority_mismatch = official_context(value, include_adapter=True)
        authority_mismatch["current_record"]["data"]["authority"][
            "canonical_url"
        ] = "https://docs.example.invalid/other/reference"
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH"],
            authority_mismatch,
        )[0]
        self.assertEqual(row["status"], "fail")
        self.assertEqual(
            row["finding_codes"],
            ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MISMATCH"],
        )

        version_mismatch = official_context(value, include_adapter=True)
        version_mismatch["registry_snapshots"]["official_source_authorities"][
            "vendor-official-reference"
        ]["version_scopes"] = [
            {
                "scope": "exact",
                "exact_version": "other-version",
                "minimum_version": None,
                "maximum_version": None,
                "release_series": None,
            }
        ]
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_VERSION_SCOPE_MATCH"],
            version_mismatch,
        )[0]
        self.assertEqual(row["status"], "fail")
        self.assertEqual(
            row["finding_codes"],
            ["OFFICIAL_SOURCE_VERSION_SCOPE_MISMATCH"],
        )

    def test_restricted_source_bytes_and_unverified_record_views_are_rejected(self) -> None:
        value = restricted_external_source()
        embedded = copy.deepcopy(value)
        embedded["retrieval"]["status"] = "retrieved"
        embedded["retrieval"]["response_status"] = 200
        embedded["content"] = copy.deepcopy(official_source()["content"])
        self.assert_invalid("official", embedded)

        context = official_context(value, include_adapter=True)
        context["artifacts_by_label"]["vendor-reference.html"] = {
            "label": "vendor-reference.html",
            "index": 3,
            "metadata": {"availability": "present"},
            "raw_sha256": SHA_A,
            "bytes": 128,
            "integrity_verified": True,
        }
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_RESTRICTED_CONTENT_NOT_EMBEDDED"],
            context,
        )[0]
        self.assertEqual(row["status"], "fail")
        self.assertEqual(
            row["finding_codes"],
            ["OFFICIAL_SOURCE_RESTRICTED_CONTENT_EMBEDDED"],
        )

        unverified = official_context(value, include_adapter=True)
        receipt_key = (
            "evidence-record",
            "1.0",
            "evidence-resolver-receipt-001",
        )
        unverified["records_by_identity"][receipt_key]["integrity_verified_active"] = False
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_RESOLVER_REF_HASH_RESOLVES"],
            unverified,
        )[0]
        self.assertEqual(row["status"], "blocked")
        self.assertEqual(
            row["finding_codes"],
            ["OFFICIAL_SOURCE_RESOLVER_REF_UNRESOLVED"],
        )

    def test_reference_resolution_requires_canonical_triple_identity(self) -> None:
        canonical_key = (
            "evidence-record",
            "1.0",
            "evidence-resolver-receipt-001",
        )
        legacy_keys: tuple[object, ...] = (
            ("evidence-record", "evidence-resolver-receipt-001"),
            "evidence-record@1.0:evidence-resolver-receipt-001",
        )
        for legacy_key in legacy_keys:
            with self.subTest(legacy_key=legacy_key):
                context = official_context(
                    restricted_external_source(),
                    include_adapter=True,
                )
                record = context["records_by_identity"].pop(canonical_key)
                context["records_by_identity"][legacy_key] = record
                row = bundle_semantics_evidence.evaluate(
                    ["OFFICIAL_SOURCE_RESOLVER_REF_HASH_RESOLVES"],
                    context,
                )[0]
                self.assertEqual(row["status"], "blocked")
                self.assertEqual(
                    row["finding_codes"],
                    ["OFFICIAL_SOURCE_RESOLVER_REF_UNRESOLVED"],
                )

        mismatched_current_identity = official_context(official_source())
        mismatched_current_identity["current_record"]["record_id"] = "forged-id"
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH"],
            mismatched_current_identity,
        )[0]
        self.assertEqual(row["status"], "blocked")
        self.assertEqual(row["finding_codes"], ["OBLIGATION_CONTEXT_INCOMPLETE"])

    def test_artifact_index_requires_verified_raw_digest_without_alias_fallback(self) -> None:
        context = evidence_context(evidence_record())
        artifact = context["artifacts_by_label"]["scheduler-status.json"]
        artifact["sha256"] = artifact.pop("raw_sha256")
        row = bundle_semantics_evidence.evaluate(
            ["EVIDENCE_PRESENT_ARTIFACT_RAW_BYTES_HASH_MATCH"],
            context,
        )[0]
        self.assertEqual(row["status"], "blocked")
        self.assertEqual(
            row["finding_codes"],
            ["EVIDENCE_PRESENT_ARTIFACT_UNRESOLVED"],
        )

        unverified = evidence_context(evidence_record())
        unverified["artifacts_by_label"]["scheduler-status.json"][
            "integrity_verified"
        ] = False
        row = bundle_semantics_evidence.evaluate(
            ["EVIDENCE_PRESENT_ARTIFACT_RAW_BYTES_HASH_MATCH"],
            unverified,
        )[0]
        self.assertEqual(row["status"], "blocked")
        self.assertEqual(
            row["finding_codes"],
            ["EVIDENCE_PRESENT_ARTIFACT_UNRESOLVED"],
        )

    def test_positive_official_source_metadata_and_restricted_external_records(self) -> None:
        for value in (official_source(), metadata_only_source(), restricted_external_source()):
            with self.subTest(record=value["source_record_id"]):
                self.assert_valid("official", value)
        self.assert_valid("evidence", resolver_receipt())

    def test_official_source_unknown_authority_or_metadata_cannot_document_claim(self) -> None:
        for mutation in (
            lambda value: value["authority"].update(verification_status="unknown"),
            lambda value: value.update(content={
                "status": "metadata-only",
                "identity_mode": "unresolved",
                "artifact": None,
                "raw_sha256": None,
                "bytes": None,
                "resolver_record_ref": None,
                "trust_adapter": None,
                "pinned_source_ref": None,
                "trust_state": "unresolved",
            }),
        ):
            value = official_source()
            mutation(value)
            self.assert_invalid("official", value)

        metadata = metadata_only_source()
        metadata["claim_ceiling"] = "documented_behavior_only"
        self.assert_invalid("official", metadata)

    def test_version_scope_is_fail_closed_and_unknown_is_explicit(self) -> None:
        value = official_source()
        value["version_scope"]["exact_version"] = None
        self.assert_invalid("official", value)

        value = metadata_only_source()
        value["version_scope"]["exact_version"] = "guessed-7.5"
        self.assert_invalid("official", value)

        value = official_source()
        value["version_scope"] = {
            "scope": "range",
            "exact_version": None,
            "minimum_version": None,
            "maximum_version": None,
            "release_series": None,
        }
        self.assert_invalid("official", value)

        value = official_source()
        value["version_scope"] = {
            "scope": "range",
            "exact_version": None,
            "minimum_version": "7.4",
            "maximum_version": "7.5",
            "release_series": None,
        }
        self.assert_valid("official", value)

    def test_retrieval_content_status_cross_checks(self) -> None:
        value = official_source()
        value["retrieval"]["status"] = "metadata-only"
        value["retrieval"]["retrieved_utc"] = None
        self.assert_invalid("official", value)

        value = metadata_only_source()
        value["retrieval"]["status"] = "retrieved"
        value["retrieval"]["retrieved_utc"] = NOW
        self.assert_invalid("official", value)

        value = official_source()
        value["retrieval"]["response_status"] = 404
        self.assert_invalid("official", value)

    def test_license_and_redistribution_never_embed_restricted_text(self) -> None:
        value = official_source()
        value["license"].update(
            status="known-restricted",
            identifier="Vendor terms",
            redistribution="restricted",
        )
        self.assert_invalid("official", value)

        value = official_source()
        value["license"]["redistribution"] = "restricted"
        self.assert_invalid("official", value)

        value = metadata_only_source()
        value["license"]["identifier"] = "guessed-license"
        self.assert_invalid("official", value)

        value = official_source()
        value["content"]["full_text"] = "Restricted body must never be embedded."
        self.assert_invalid("official", value)

    def test_official_source_urls_labels_roles_and_privacy_are_safe(self) -> None:
        query_and_fragment = official_source()
        query_and_fragment["authority"]["canonical_url"] = (
            "https://docs.example.invalid/qe/reference?section=input#ecutwfc"
        )
        query_and_fragment["retrieval"]["retrieval_url"] = (
            "https://docs.example.invalid/qe/reference?section=input#ecutwfc"
        )
        self.assert_valid("official", query_and_fragment)

        mutations = []
        value = official_source()
        value["authority"]["canonical_url"] = "https://user@example.invalid/manual"
        mutations.append(value)
        value = official_source()
        value["retrieval"]["retrieval_url"] = "https://example.invalid/manual?token=value"
        mutations.append(value)
        value = official_source()
        value["authority"]["provider_label"] = "/Users/private/provider"
        mutations.append(value)
        value = official_source()
        value["limitations"] = ["Cached under /scratch/private/source.html"]
        mutations.append(value)
        value = official_source()
        value["parent_source_refs"] = [
            record_ref("official-source-record", "older-source-001", "evidence-source")
        ]
        mutations.append(value)
        for index, invalid in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assert_invalid("official", invalid)

    def test_authority_locator_policy_rejects_prefix_spoofing_and_url_state(self) -> None:
        invalid_urls = (
            "https://docs.example.invalid.evil/qe/pw-user-guide",
            "https://docs.example.invalid/not-qe/pw-user-guide",
            "https://docs.example.invalid/qe/%2e%2e/vendor/reference",
            "https://docs.example.invalid/qe/../vendor/reference",
            "https://docs.example.invalid/qe//vendor/reference",
            "https://docs.example.invalid/qe\\..\\vendor\\reference",
            "https://docs.example.invalid/qe/pw-user-guide?section=control",
            "https://docs.example.invalid/qe/pw-user-guide#control",
            "https://user@docs.example.invalid/qe/pw-user-guide",
        )
        for invalid_url in invalid_urls:
            with self.subTest(url=invalid_url):
                context = official_context(official_source())
                context["current_record"]["data"]["authority"][
                    "canonical_url"
                ] = invalid_url
                context["registry_snapshots"]["official_source_authorities"][
                    "qe-official-docs"
                ]["canonical_urls"].append(invalid_url)
                row = bundle_semantics_evidence.evaluate(
                    ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH"],
                    context,
                )[0]
                self.assertEqual(row["status"], "fail")
                self.assertEqual(
                    row["finding_codes"],
                    ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MISMATCH"],
                )

        retrieval_spoof = official_context(official_source())
        retrieval_spoof["current_record"]["data"]["retrieval"][
            "retrieval_url"
        ] = "https://attacker.example.invalid/unrelated"
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH"],
            retrieval_spoof,
        )[0]
        self.assertEqual(row["status"], "fail")
        self.assertEqual(
            row["finding_codes"],
            ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MISMATCH"],
        )

        explicit_default_port = official_context(official_source())
        explicit_url = "https://docs.example.invalid:443/qe/pw-user-guide"
        explicit_default_port["current_record"]["data"]["authority"][
            "canonical_url"
        ] = explicit_url
        explicit_default_port["current_record"]["data"]["retrieval"][
            "retrieval_url"
        ] = explicit_url
        explicit_entry = explicit_default_port["registry_snapshots"][
            "official_source_authorities"
        ]["qe-official-docs"]
        explicit_entry["allowed_https_origins"] = [
            "https://docs.example.invalid:443"
        ]
        explicit_entry["locator_policy"]["allowed_origins"] = [
            "https://docs.example.invalid:443"
        ]
        explicit_entry["canonical_urls"] = [
            "https://docs.example.invalid:443/qe/"
        ]
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH"],
            explicit_default_port,
        )[0]
        self.assertEqual(row["status"], "pass", row)

        nondefault_port = copy.deepcopy(explicit_default_port)
        nondefault_port["current_record"]["data"]["authority"][
            "canonical_url"
        ] = "https://docs.example.invalid:444/qe/pw-user-guide"
        nondefault_port["current_record"]["data"]["retrieval"][
            "retrieval_url"
        ] = "https://docs.example.invalid:444/qe/pw-user-guide"
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH"],
            nondefault_port,
        )[0]
        self.assertEqual(row["status"], "fail")

        planned = official_context(official_source())
        planned["registry_snapshots"]["official_source_authorities"][
            "qe-official-docs"
        ]["lifecycle"] = "planned"
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_MATCH"],
            planned,
        )[0]
        self.assertEqual(row["status"], "blocked")
        self.assertEqual(
            row["finding_codes"],
            ["OFFICIAL_SOURCE_AUTHORITY_REGISTRY_UNRESOLVED"],
        )

    def test_embedded_open_content_requires_verified_canonical_snapshot_pin(self) -> None:
        blocked_mutations = (
            lambda context: context["registry_snapshots"][
                "official_source_authorities"
            ]["qe-official-docs"].update(canonical_snapshot=None),
            lambda context: context["registry_snapshots"][
                "official_source_authorities"
            ]["qe-official-docs"]["canonical_snapshot"].update(
                integrity_verified=False
            ),
            lambda context: context["registry_snapshots"][
                "official_source_authorities"
            ]["qe-official-docs"]["content_identity_policy"].update(
                mode="platform-adapter-only"
            ),
        )
        for mutate in blocked_mutations:
            context = official_context(official_source())
            mutate(context)
            rows = bundle_semantics_evidence.evaluate(
                [
                    "OFFICIAL_SOURCE_PINNED_CANONICAL_SNAPSHOT_MATCH",
                    "OFFICIAL_SOURCE_STATUS_CLAIM_CEILING_MATCH",
                ],
                context,
            )
            self.assertTrue(all(row["status"] == "blocked" for row in rows), rows)
            self.assertTrue(
                all(
                    row["finding_codes"]
                    == ["OFFICIAL_SOURCE_CANONICAL_SNAPSHOT_UNAVAILABLE"]
                    for row in rows
                ),
                rows,
            )

        mismatches = (
            lambda context: context["current_record"]["data"]["content"][
                "pinned_source_ref"
            ].update(source_id="not-in-canonical-snapshot"),
            lambda context: context["registry_snapshots"][
                "official_source_authorities"
            ]["qe-official-docs"]["canonical_snapshot"]["sources_by_id"][
                "pw-user-guide"
            ].update(raw_sha256=SHA_B),
        )
        for mutate in mismatches:
            context = official_context(official_source())
            mutate(context)
            row = bundle_semantics_evidence.evaluate(
                ["OFFICIAL_SOURCE_PINNED_CANONICAL_SNAPSHOT_MATCH"],
                context,
            )[0]
            self.assertEqual(row["status"], "fail")
            self.assertTrue(
                row["finding_codes"][0].startswith(
                    "OFFICIAL_SOURCE_CANONICAL_SNAPSHOT_"
                )
            )

        self_asserted_manifest = official_source()
        self_asserted_manifest["content"]["pinned_source_ref"][
            "manifest_raw_sha256"
        ] = SHA_A
        self.assert_invalid("official", self_asserted_manifest)

    def test_license_authority_and_bundle_report_cannot_self_elevate_trust(self) -> None:
        for field, forged_value in (
            ("identifier", "MIT"),
            ("terms_url", "https://attacker.example.invalid/license"),
        ):
            forged = official_context(official_source())
            forged["current_record"]["data"]["license"][field] = forged_value
            row = bundle_semantics_evidence.evaluate(
                ["OFFICIAL_SOURCE_LICENSE_REDISTRIBUTION_MATCH"],
                forged,
            )[0]
            self.assertEqual(row["status"], "fail", (field, row))
            self.assertEqual(
                row["finding_codes"],
                ["OFFICIAL_SOURCE_LICENSE_REDISTRIBUTION_MISMATCH"],
            )

        conflated = official_context(restricted_external_source(), include_adapter=True)
        conflated["current_record"]["data"]["license"] = {
            "status": "known-open",
            "identifier": "Self-declared open",
            "terms_url": "https://docs.example.invalid/vendor/terms",
            "redistribution": "redistributable",
        }
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_LICENSE_REDISTRIBUTION_MATCH"],
            conflated,
        )[0]
        self.assertEqual(row["status"], "fail")
        self.assertEqual(
            row["finding_codes"],
            ["OFFICIAL_SOURCE_LICENSE_REDISTRIBUTION_MISMATCH"],
        )

        report_only = official_context(
            restricted_external_source(),
            include_adapter=False,
        )
        report_only["registry_snapshots"]["bundle_validation_report"] = {
            "status": "verified",
            "authority_registry_id": "vendor-official-reference",
        }
        row = bundle_semantics_evidence.evaluate(
            ["OFFICIAL_SOURCE_EXTERNAL_TRUST_ADAPTER_VERIFIES"],
            report_only,
        )[0]
        self.assertEqual(row["status"], "blocked")
        self.assertEqual(
            row["finding_codes"],
            ["OFFICIAL_SOURCE_EXTERNAL_TRUST_REQUIRED"],
        )

        self_reported = restricted_external_source()
        self_reported["official_fact_urls"] = [
            "https://attacker.example.invalid/not-official"
        ]
        self_asserted = restricted_external_source()
        self_asserted["trust_report"] = {"status": "verified"}
        self.assert_invalid("official", self_reported)
        self.assert_invalid("official", self_asserted)

    def test_all_generic_nonhuman_evidence_kinds_have_valid_positive_fixtures(self) -> None:
        kinds = SCHEMAS["evidence"]["properties"]["evidence_kind"]["enum"]
        for kind in kinds:
            with self.subTest(kind=kind):
                self.assert_valid("evidence", evidence_record(kind))

    def test_evidence_status_and_artifact_availability_are_fail_closed(self) -> None:
        value = evidence_record()
        value["artifacts"] = [
            file_ref(availability="missing", sha256=None, byte_count=None)
        ]
        self.assert_invalid("evidence", value)

        value = unknown_evidence()
        value["claim_ceiling"] = "technical_run_gates_only"
        self.assert_invalid("evidence", value)

        value = unknown_evidence()
        value["artifacts"] = [file_ref()]
        self.assert_invalid("evidence", value)

        value = evidence_record()
        value["artifacts"][0]["sha256"] = None
        self.assert_invalid("evidence", value)

        self.assert_valid("evidence", unknown_evidence())

    def test_evidence_result_and_kind_bound_claim_ceiling(self) -> None:
        value = evidence_record()
        value["observation"] = {
            "result": "fail",
            "finding_codes": ["scheduler-observation-failed"],
            "summary": "The scheduler observation failed.",
        }
        self.assert_invalid("evidence", value)

        value = evidence_record("input-validation")
        value["claim_ceiling"] = "technical_run_gates_only"
        self.assert_invalid("evidence", value)

        value = evidence_record("parser-result")
        value["claim_ceiling"] = "numerical_candidate_only"
        self.assert_invalid("evidence", value)

        value = evidence_record("convergence-study")
        value["claim_ceiling"] = "eligible_for_expert_review"
        self.assert_invalid("evidence", value)

    def test_evidence_is_nonhuman_nonauthoritative_and_role_bound(self) -> None:
        value = evidence_record()
        value["observed_by"]["actor_type"] = "human"
        self.assert_invalid("evidence", value)

        for field in (
            "may_authorize_execution",
            "may_assert_human_identity",
            "may_accept_scientific_claim",
            "may_establish_external_source_authority",
        ):
            value = evidence_record()
            value["authority_limits"][field] = True
            self.assert_invalid("evidence", value)

        value = evidence_record()
        value["subject_refs"][0]["role"] = "execution-authorization"
        self.assert_invalid("evidence", value)
        value = evidence_record()
        value["source_refs"][0]["role"] = "scientific-acceptance"
        self.assert_invalid("evidence", value)
        value = evidence_record()
        value["parent_evidence_refs"] = [
            record_ref("decision-record", "decision-001", "parent-evidence")
        ]
        self.assert_invalid("evidence", value)

    def test_evidence_privacy_labels_reject_paths_and_secret_like_assignments(self) -> None:
        value = evidence_record()
        value["observation"]["summary"] = "Read /Users/private/run/output.log"
        self.assert_invalid("evidence", value)

        value = evidence_record()
        value["limitations"] = ["access_token=value"]
        self.assert_invalid("evidence", value)

        value = evidence_record()
        value["artifacts"][0]["label"] = "private/run/output.log"
        self.assert_invalid("evidence", value)

    def test_exact_raw_bytes_not_reserialized_json_define_artifact_hash(self) -> None:
        artifact = {"status": "COMPLETED", "return_code": 0}
        compact = json.dumps(artifact, separators=(",", ":")).encode("utf-8")
        pretty = (json.dumps(artifact, indent=2) + "\n").encode("utf-8")
        self.assertNotEqual(raw_sha256(compact), raw_sha256(pretty))

        source = official_source()
        source["content"]["artifact"]["sha256"] = raw_sha256(pretty)
        source["content"]["artifact"]["bytes"] = len(pretty)
        source["content"]["raw_sha256"] = raw_sha256(pretty)
        source["content"]["bytes"] = len(pretty)
        self.assert_valid("official", source)
        self.assertEqual(source["content"]["raw_sha256"], raw_sha256(pretty))
        self.assertNotEqual(source["content"]["raw_sha256"], raw_sha256(compact))
        self.assertEqual(
            present_artifact_findings(
                source,
                {"qe-pw-user-guide.html": pretty},
            ),
            set(),
        )

        mismatched_source = copy.deepcopy(source)
        mismatched_source["content"]["raw_sha256"] = raw_sha256(compact)
        self.assertEqual(
            present_artifact_findings(
                mismatched_source,
                {"qe-pw-user-guide.html": pretty},
            ),
            {"OFFICIAL_SOURCE_CONTENT_RAW_BYTES_HASH_MATCH"},
        )

        evidence = evidence_record()
        evidence["artifacts"][0]["sha256"] = raw_sha256(pretty)
        evidence["artifacts"][0]["bytes"] = len(pretty)
        self.assert_valid("evidence", evidence)
        self.assertEqual(
            present_artifact_findings(
                evidence,
                {"scheduler-status.json": pretty},
            ),
            set(),
        )
        self.assertEqual(
            present_artifact_findings(
                evidence,
                {"scheduler-status.json": compact},
            ),
            {"EVIDENCE_PRESENT_ARTIFACT_RAW_BYTES_HASH_MATCH"},
        )

    def test_bundle_hash_resolution_and_cycle_detection_are_not_projection_based(self) -> None:
        first = official_source()
        first["claim_ceiling"] = "no_positive_claim"
        first_raw = (json.dumps(first, indent=2) + "\n").encode("utf-8")

        second = copy.deepcopy(first)
        second["source_record_id"] = "official-qe-pw-guide-751"
        second["parent_source_refs"] = [
            record_ref(
                "official-source-record",
                first["source_record_id"],
                "prior-official-source",
                raw_sha256(first_raw),
            )
        ]
        second_raw = (json.dumps(second, indent=2) + "\n").encode("utf-8")
        records = [first, second]
        raw_by_key = {
            record_key(first): first_raw,
            record_key(second): second_raw,
        }
        self.assertEqual(bundle_findings(records, raw_by_key), set())

        cyclic_first = copy.deepcopy(first)
        cyclic_first["parent_source_refs"] = [
            record_ref(
                "official-source-record",
                second["source_record_id"],
                "prior-official-source",
                raw_sha256(second_raw),
            )
        ]
        cyclic_first_raw = (json.dumps(cyclic_first, indent=2) + "\n").encode("utf-8")
        findings = bundle_findings(
            [cyclic_first, second],
            {
                record_key(cyclic_first): cyclic_first_raw,
                record_key(second): second_raw,
            },
        )
        self.assertIn("RECORD_REF_DAG_CYCLE", findings)
        self.assertIn("RECORD_REF_RAW_BYTES_HASH_MISMATCH", findings)


if __name__ == "__main__":
    unittest.main(verbosity=2)
