from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_active_only_distribution as distribution  # noqa: E402
import validate_official_document_coverage as coverage_validator  # noqa: E402


SEVEN_ACTIVE_SKILL_IDS = tuple(
    f"active-skill-{suffix}" for suffix in ("a", "b", "c", "d", "e", "f", "g")
)


def provider_token_payload() -> bytes:
    return b"sk" + b"-" + (b"A" * 32) + b"\n"


def private_home_payload() -> bytes:
    return b"/Users" + b"/actual-owner/private-project\n"


def restricted_potential_payload() -> bytes:
    return b"".join(
        (
            b"TI" + b"TEL = PAW_PBE X 01Jan2000\n",
            b"VRH" + b"FIN =X: s2p2\n",
            b"POM" + b"ASS = 1.0; ZVAL = 4.0\n",
            b"End of " + b"Dataset\n",
        )
    )


def canonical_bundle_entrypoint(skill_id: str) -> str:
    return f"skills/{skill_id}/references/official-source-pack/bundle.json"


def synthetic_active_files(
    active_skill_ids: tuple[str, ...] = ("active-skill",),
    *,
    expectation_overrides: dict[str, dict[str, str] | None] | None = None,
    omit_bundles: frozenset[str] = frozenset(),
) -> dict[str, bytes]:
    overrides = expectation_overrides or {}
    skill_registry = ['schema_version: "1.0"', "skills:"]
    expectations = ['schema_version: "1.0"', "skills:"]
    files = {
        path.relative_to(ROOT).as_posix(): path.read_bytes()
        for path in sorted((ROOT / "contracts").glob("*.schema.json"))
    }
    builder_lock = ROOT / "contracts" / "official-document-pack-builder-lock.json"
    files[builder_lock.relative_to(ROOT).as_posix()] = builder_lock.read_bytes()
    for tool_path in distribution.VERIFICATION_TOOL_PATHS:
        files[tool_path] = b"# verifier closure\n"
    for skill_id in active_skill_ids:
        skill_registry.extend(
            (
                f"  {skill_id}:",
                "    lifecycle: active",
                f"    path: skills/{skill_id}",
            )
        )
        specification = overrides.get(
            skill_id,
            {
                "entrypoint": canonical_bundle_entrypoint(skill_id),
                "expectation": "pack-required",
            },
        )
        if specification is not None:
            expectations.append(f"  {skill_id}:")
            expectations.extend(
                f"    {key}: {value}" for key, value in specification.items()
            )
        files[f"skills/{skill_id}/SKILL.md"] = b"# Active\n"
        if skill_id not in omit_bundles:
            files[canonical_bundle_entrypoint(skill_id)] = b'{"pack":"synthetic"}\n'
    files["registry/skill-registry.yaml"] = distribution._yaml_bytes(
        yaml.safe_load("\n".join(skill_registry) + "\n")
    )
    files["registry/official-document-bundle-expectations.yaml"] = (
        distribution._yaml_bytes(
            yaml.safe_load("\n".join(expectations) + "\n")
        )
    )
    implementation_path = "tools/build_active_only_distribution.py"
    configuration_path = sorted(files)[0]
    processor = {
        "synthetic-pack-enumerator": {
            "kind": "enumerator",
            "version": "1.0",
            "implementation_ref": {
                "path": implementation_path,
                "sha256": distribution._sha256(files[implementation_path]),
            },
            "configuration_ref": {
                "path": configuration_path,
                "sha256": distribution._sha256(files[configuration_path]),
            },
            "dependency_lock_ref": {
                "path": configuration_path,
                "sha256": distribution._sha256(files[configuration_path]),
            },
        }
    }
    live_registries = {
        "registry/software-registry.yaml": {
            "schema_version": "1.0",
            "software": {},
            "planned_software": {},
        },
        "registry/interface-registry.yaml": {
            "schema_version": "1.0",
            "interfaces": {},
        },
        "registry/operation-routes.yaml": {
            "schema_version": "1.0",
            "routes": {
                skill_id: {"lifecycle": "active"}
                for skill_id in active_skill_ids
            },
            "response_policy": {"terminal_intent_routes": {}},
        },
        "registry/official-source-authorities.yaml": {
            "schema_version": "1.0",
            "authorities": {},
        },
        "registry/official-document-consumers.yaml": {
            "schema_version": "1.0",
            "default_policy": "deny",
            "processors": processor,
            "bindings": [],
        },
        "registry/official-document-storage-discovery.yaml": {
            "schema_version": "1.0",
            "artifact_sets": {},
            "local_controls": [],
        },
        "registry/semantic-obligations.yaml": {
            "schema_version": "1.0",
            "obligations": {},
        },
    }
    files.update(
        {
            path: distribution._yaml_bytes(value)
            for path, value in live_registries.items()
        }
    )
    for registry_path in distribution.SOURCE_REGISTRY_PATHS:
        snapshot_path = distribution._source_snapshot_path(registry_path)
        files[snapshot_path] = files.get(
            registry_path,
            (ROOT / registry_path).read_bytes(),
        )
    return files


def synthetic_source_digests(files: dict[str, bytes]) -> dict[str, str]:
    return {
        distribution._source_snapshot_path(registry_path): distribution._sha256(
            files[distribution._source_snapshot_path(registry_path)]
        )
        for registry_path in distribution.SOURCE_REGISTRY_PATHS
    }


class ActiveOnlyDistributionTests(unittest.TestCase):
    def test_portable_compatibility_semantics_match_canonical_contracts(
        self,
    ) -> None:
        subjects = [{"subject_id": "subject-a"}]
        self.assertTrue(
            distribution._scope_enumeration_receipt_valid(
                {
                    "method": "canonical-reviewed-inventory",
                    "extractor": None,
                },
                expected_source_tree_sha256="a" * 64,
                subjects=subjects,
            )
        )
        source_inventory = {
            "a": {
                "disposition": "included",
                "source_identity": {
                    "content_mode": "external-content",
                    "locator": "https://docs.example.org/a.rst",
                    "receipt": {
                        "sha256": "c" * 64,
                        "bytes": 1024,
                    },
                },
            },
            "b": {
                "disposition": "included",
                "source_identity": {
                    "content_mode": "external-content",
                    "locator": "https://docs.example.org/b.rst",
                    "receipt": {
                        "sha256": "d" * 64,
                        "bytes": 128,
                    },
                },
            },
            "c": {
                "disposition": "excluded",
                "source_identity": {
                    "content_mode": "metadata-only",
                    "locator": "https://docs.example.org/c.json",
                    "identity": {
                        "sha256": "e" * 64,
                        "bytes": 16,
                    },
                },
            },
        }
        manifest_sources = {
            "b": {
                "source_identity": source_inventory["b"]["source_identity"],
            }
        }
        manifest_sources_mismatch = {
            "b": {
                "source_identity": {
                    "content_mode": "external-content",
                    "locator": "https://docs.example.org/b.rst",
                    "receipt": {
                        "sha256": "f" * 64,
                        "bytes": 128,
                    },
                }
            }
        }
        manifest_sources_complete = {
            "a": {
                "source_identity": source_inventory["a"]["source_identity"],
            },
            "b": {
                "source_identity": source_inventory["b"]["source_identity"],
            },
        }
        self.assertTrue(
            distribution._slice_source_inventory_valid(
                source_inventory,
                manifest_sources,
                status="partial",
            )
        )
        self.assertFalse(
            distribution._slice_source_inventory_valid(
                source_inventory,
                manifest_sources_mismatch,
                status="partial",
            )
        )
        self.assertTrue(
            distribution._slice_source_inventory_valid(
                source_inventory,
                manifest_sources,
                status="partial",
            )
        )
        self.assertFalse(
            distribution._slice_source_inventory_valid(
                source_inventory,
                manifest_sources,
                status="complete",
            )
        )
        self.assertTrue(
            distribution._slice_source_inventory_valid(
                source_inventory,
                {
                    "a": {
                        "source_identity": source_inventory["a"]["source_identity"],
                    },
                    "b": {
                        "source_identity": source_inventory["b"]["source_identity"],
                    },
                },
                status="complete",
            )
        )
        self.assertTrue(
            distribution._corpus_source_partition_valid(
                {
                    "a": {
                        "disposition": "included",
                        "source_identity": source_inventory["a"]["source_identity"],
                    },
                    "b": {
                        "disposition": "included",
                        "source_identity": source_inventory["b"]["source_identity"],
                    },
                    "c": {
                        "disposition": "excluded",
                        "source_identity": source_inventory["c"]["source_identity"],
                    },
                },
            )
        )
        self.assertFalse(
            distribution._corpus_source_partition_valid(
                {
                    "a": {
                        "disposition": "included",
                        "source_identity": source_inventory["a"]["source_identity"],
                    },
                    "b": {
                        "disposition": "unknown",
                        "source_identity": source_inventory["b"]["source_identity"],
                    },
                },
            )
        )
        # A tagged total map does not require both dispositions to be present.
        self.assertTrue(
            distribution._corpus_source_partition_valid(
                {"a": {"disposition": "included"}, "b": {"disposition": "excluded"}},
            )
        )
        self.assertTrue(
            distribution._corpus_source_partition_valid(
                {"a": {"disposition": "included"}, "b": {"disposition": "included"}},
            )
        )
        self.assertEqual(
            distribution._single_pack_filename(
                "nested/record.data",
                "compatibility/path",
            ),
            "nested/record.data",
        )
        oversized_bundle = distribution._json_bytes(
            {"payload": "x" * distribution.MAX_BUNDLE_BYTES}
        )
        with self.assertRaisesRegex(
            distribution.DistributionError,
            "pack JSON is invalid",
        ):
            distribution._strict_json_object(
                oversized_bundle,
                "bundle.json",
                max_bytes=distribution.MAX_BUNDLE_BYTES,
            )
        externalized = coverage_validator.ExternalizedArtifact(
            path="skills/example/source.txt",
            sha256="b" * 64,
            size=10,
        )
        self.assertEqual(
            coverage_validator._externalized_slice_selection_error(
                externalized,
                selector_kind="whole-source",
                start=None,
                end=None,
                content_sha256="c" * 64,
            ),
            "SLICE_CONTENT_HASH_MISMATCH",
        )
        self.assertEqual(
            coverage_validator._externalized_slice_selection_error(
                externalized,
                selector_kind="byte-range",
                start=0,
                end=11,
                content_sha256="d" * 64,
            ),
            "SLICE_RANGE_INVALID",
        )

    def test_active_pack_protocol_uses_exact_v11_record_families(self) -> None:
        self.assertEqual(
            distribution.PACK_RECORD_FAMILIES,
            {
                "corpora": ("official-corpus-manifest@1.1", "corpus_id"),
                "slice_manifests": (
                    "document-slice-manifest@1.1",
                    "slice_manifest_id",
                ),
                "scope_inventory": (
                    "skill-document-scope-inventory@1.0",
                    "inventory_id",
                ),
                "coverage": (
                    "skill-document-coverage@1.1",
                    "coverage_id",
                ),
            },
        )

    def test_embedded_source_identity_uses_real_local_bytes_hash_and_path(
        self,
    ) -> None:
        authority: dict[str, object] = {}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = b"exact embedded bytes"
            relative = "content/manual.txt"
            target = root / relative
            target.parent.mkdir(parents=True)
            target.write_bytes(payload)

            def findings_for(identity: dict[str, object]) -> set[str]:
                findings: list[coverage_validator.Finding] = []
                coverage_validator._source_inventory_v11_entries(
                    {
                        "source-one": {
                            "disposition": "included",
                            "source_identity": identity,
                        }
                    },
                    authority=authority,
                    location="corpus/test",
                    source_root=root,
                    findings=findings,
                )
                return {finding.code for finding in findings}

            valid_identity = {
                "content_mode": "embedded-content",
                "locator": relative,
                "sha256": distribution._sha256(payload),
                "bytes": len(payload),
            }
            self.assertFalse(
                {
                    "CORPUS_SOURCE_CONTENT_UNAVAILABLE",
                    "CORPUS_SOURCE_CONTENT_HASH_MISMATCH",
                    "CORPUS_SOURCE_CONTENT_BYTES_MISMATCH",
                }
                & findings_for(valid_identity)
            )
            for field, value, expected in (
                (
                    "locator",
                    "content/missing.txt",
                    "CORPUS_SOURCE_CONTENT_UNAVAILABLE",
                ),
                (
                    "sha256",
                    "0" * 64,
                    "CORPUS_SOURCE_CONTENT_HASH_MISMATCH",
                ),
                (
                    "bytes",
                    len(payload) + 1,
                    "CORPUS_SOURCE_CONTENT_BYTES_MISMATCH",
                ),
            ):
                with self.subTest(field=field):
                    malformed = dict(valid_identity)
                    malformed[field] = value
                    self.assertIn(expected, findings_for(malformed))

    def test_external_backed_metadata_slice_binds_locator_and_authority(
        self,
    ) -> None:
        source_locator = "https://docs.example.org/manual.html"
        authority = {
            "allowed_https_origins": ["https://docs.example.org"],
            "content_policy": {
                "source_kinds": [],
                "allowed_path_prefixes": ["/"],
                "query_policy": "forbidden",
                "allowed_query_urls": [],
                "fragment_policy": "forbidden",
            },
        }
        source_identity = {
            "content_mode": "external-content",
            "locator": source_locator,
            "receipt": {
                "retrieval_method": "https-get",
                "retrieved_utc": "2026-07-25T00:00:00Z",
                "raw_sha256": "1" * 64,
                "raw_bytes": 4,
            },
        }

        authority_findings: list[coverage_validator.Finding] = []
        coverage_validator._source_inventory_v11_entries(
            {
                "source-one": {
                    "disposition": "included",
                    "source_identity": source_identity,
                }
            },
            authority=authority,
            location="corpus/test",
            source_root=ROOT,
            findings=authority_findings,
        )
        self.assertNotIn(
            "CORPUS_SOURCE_LOCATOR_MISMATCH",
            {finding.code for finding in authority_findings},
        )
        off_authority = {
            **source_identity,
            "locator": "https://other.example.org/manual.html",
        }
        authority_findings = []
        coverage_validator._source_inventory_v11_entries(
            {
                "source-one": {
                    "disposition": "included",
                    "source_identity": off_authority,
                }
            },
            authority=authority,
            location="corpus/test",
            source_root=ROOT,
            findings=authority_findings,
        )
        self.assertIn(
            "CORPUS_SOURCE_LOCATOR_MISMATCH",
            {finding.code for finding in authority_findings},
        )

        def slice_findings(locator: str) -> set[str]:
            corpus_data = {
                "corpus_id": "corpus-one",
                "status": "partial",
                "source_inventory": {
                    "source-one": {
                        "disposition": "included",
                        "source_identity": source_identity,
                        "loss_ids": [],
                    }
                },
            }
            corpus_raw = distribution._json_bytes(corpus_data)
            corpus = coverage_validator.LoadedRecord(
                path=Path("corpus.json"),
                raw_sha256=distribution._sha256(corpus_raw),
                data=corpus_data,
            )
            slices = [
                {
                    "slice_id": "slice-one",
                    "selector": {
                        "layer": "raw-source",
                        "kind": "byte-range",
                        "value": "0:2",
                    },
                    "raw_byte_range": {
                        "start_byte": 0,
                        "byte_count": 2,
                    },
                    "content": {
                        "content_mode": "metadata-only",
                        "locator": locator,
                        "identity": {
                            "sha256": "2" * 64,
                            "bytes": 2,
                        },
                        "hash_basis": "metadata-identity-bytes",
                    },
                    "subject_ids": [],
                    "loss_accounting": {
                        "closure_status": "complete",
                        "entries": [],
                    },
                }
            ]
            source_accounting = {
                "closure_status": "complete",
                "entries": [],
            }
            processor_output = (
                coverage_validator._canonical_json_sha256(
                    {
                        "slices": slices,
                        "source_loss_accounting": source_accounting,
                    }
                )
            )
            slice_data = {
                "slice_manifest_id": "slices-one",
                "corpus_ref": {
                    "corpus_id": "corpus-one",
                    "sha256": corpus.raw_sha256,
                },
                "status": "partial",
                "sources": {
                    "source-one": {
                        "source_identity": source_identity,
                        "raw_source_extent_bytes": 4,
                        "processor": {
                            "processor_id": "fixture-transformer",
                            "processor_version": "1.0",
                            "assurance_mode": "unverified",
                            "input_sha256": "1" * 64,
                            "output_sha256": processor_output,
                            "deterministic": True,
                            "attestations": [],
                        },
                        "slices": slices,
                        "source_loss_accounting": source_accounting,
                    }
                },
                "blockers": [],
            }
            record_raw = distribution._json_bytes(slice_data)
            record = coverage_validator.LoadedRecord(
                path=Path("slices.json"),
                raw_sha256=distribution._sha256(record_raw),
                data=slice_data,
            )
            findings: list[coverage_validator.Finding] = []
            coverage_validator._slice_manifest_findings(
                record,
                corpora={"corpus-one": corpus},
                authorities={},
                authority_projection={},
                consumer_registry={"processors": {}},
                consumer_registry_sha256="3" * 64,
                source_root=ROOT,
                repository_root=ROOT,
                findings=findings,
            )
            return {finding.code for finding in findings}

        self.assertNotIn(
            "SLICE_CONTENT_MODE_MISMATCH",
            slice_findings(source_locator),
        )
        self.assertIn(
            "SLICE_CONTENT_MODE_MISMATCH",
            slice_findings("https://docs.example.org/other.html"),
        )

    def _processor_validation_fixture(
        self,
        root: Path,
        *,
        kind: str,
        duplicate_run: bool,
    ) -> tuple[
        list[dict[str, object]],
        dict[str, dict[str, object]],
        frozenset[str],
    ]:
        payloads = {
            "artifacts/implementation.py": b"# implementation\n",
            "artifacts/configuration.json": b"{}\n",
            "artifacts/dependencies.lock": b"fixture==1.0\n",
            "artifacts/run.json": b'{"attested":true}\n',
        }
        for relative, payload in payloads.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)

        def ref(path: str, *, include_bytes: bool) -> dict[str, object]:
            payload = payloads[path]
            identity: dict[str, object] = {
                "path": path,
                "sha256": distribution._sha256(payload),
            }
            if include_bytes:
                identity["bytes"] = len(payload)
            return identity

        processor_id = f"fixture-{kind}"
        input_sha256 = "4" * 64
        output_sha256 = "5" * 64
        central_refs = {
            "implementation_ref": ref(
                "artifacts/implementation.py",
                include_bytes=False,
            ),
            "configuration_ref": ref(
                "artifacts/configuration.json",
                include_bytes=False,
            ),
            "dependency_lock_ref": ref(
                "artifacts/dependencies.lock",
                include_bytes=False,
            ),
        }
        run = {
            "attestation_id": "run-one",
            "input_sha256": input_sha256,
            "output_sha256": output_sha256,
            "attestation_ref": ref(
                "artifacts/run.json",
                include_bytes=False,
            ),
        }
        processors = {
            processor_id: {
                "kind": kind,
                "version": "1.0",
                **central_refs,
                "attested_runs": [
                    dict(run)
                    for _ in range(2 if duplicate_run else 1)
                ],
            }
        }
        if kind == "enumerator":
            processor = {
                "processor_id": processor_id,
                "processor_version": "1.0",
                "assurance_mode": "attested",
                **{
                    field: ref(
                        str(reference["path"]),
                        include_bytes=True,
                    )
                    for field, reference in central_refs.items()
                },
                "input_sha256": input_sha256,
                "output_sha256": output_sha256,
                "attestation_id": "run-one",
                "deterministic": True,
            }
            records = [
                {
                    "contract_name": "official-corpus-manifest",
                    "corpus_id": "corpus-one",
                    "status": "partial",
                    "discovery": {"processor": processor},
                }
            ]
        elif kind == "transformer":
            attestation_specs = (
                (
                    "implementation",
                    "implementation-one",
                    "artifacts/implementation.py",
                ),
                (
                    "configuration",
                    "configuration-one",
                    "artifacts/configuration.json",
                ),
                (
                    "dependency-lock",
                    "dependency-one",
                    "artifacts/dependencies.lock",
                ),
                ("execution", "run-one", "artifacts/run.json"),
            )
            processor = {
                "processor_id": processor_id,
                "processor_version": "1.0",
                "assurance_mode": "attested",
                "input_sha256": input_sha256,
                "output_sha256": output_sha256,
                "deterministic": True,
                "attestations": [
                    {
                        "kind": attestation_kind,
                        "attestation_id": attestation_id,
                        "artifact": ref(path, include_bytes=True),
                    }
                    for attestation_kind, attestation_id, path in attestation_specs
                ],
            }
            records = [
                {
                    "contract_name": "document-slice-manifest",
                    "slice_manifest_id": "slices-one",
                    "status": "partial",
                    "sources": {
                        "source-one": {
                            "processor": processor,
                        }
                    },
                }
            ]
        else:
            processor = {
                "tool_id": processor_id,
                "tool_version": "1.0",
                "trust_mode": "platform-attested",
                **central_refs,
                "input_sha256": input_sha256,
                "output_sha256": output_sha256,
                "attestation_id": "run-one",
                "deterministic": True,
            }
            records = [
                {
                    "contract_name": "skill-document-scope-inventory",
                    "inventory_id": "scope-one",
                    "status": "partial",
                    "enumeration": {"extractor": processor},
                }
            ]
        return records, processors, frozenset(payloads)

    def test_three_processor_classes_reject_duplicate_attested_run(
        self,
    ) -> None:
        for kind in ("enumerator", "transformer", "extractor"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                records, processors, manifest_paths = (
                    self._processor_validation_fixture(
                        root,
                        kind=kind,
                        duplicate_run=True,
                    )
                )
                with self.assertRaisesRegex(
                    distribution.DistributionError,
                    "duplicate central runs",
                ):
                    distribution._validate_pack_processor_refs(
                        root,
                        records,
                        processors=processors,
                        manifest_paths=manifest_paths,
                    )

    def test_platform_attested_extractor_is_valid_under_partial_status(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records, processors, manifest_paths = (
                self._processor_validation_fixture(
                    root,
                    kind="extractor",
                    duplicate_run=False,
                )
            )
            self.assertIsNone(
                distribution._validate_pack_processor_refs(
                    root,
                    records,
                    processors=processors,
                    manifest_paths=manifest_paths,
                )
            )

    def test_portable_context_tracks_only_locally_consumed_receipts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target_relative = "skills/fixture/SKILL.md"
            target_path = root / target_relative
            target_raw = b"# Fixture\n"
            receipt = {
                "path": target_relative,
                "sha256": distribution._sha256(target_raw),
                "size": len(target_raw),
            }

            def context() -> coverage_validator.PortableValidationContext:
                return coverage_validator.PortableValidationContext(
                    repository_root=root,
                    contracts_directory=root / "contracts",
                    interface_registry_path=root / "registry/interface.yaml",
                    authority_registry_path=root / "registry/authority.yaml",
                    software_registry_path=root / "registry/software.yaml",
                    skill_registry_path=root / "registry/skills.yaml",
                    consumer_registry_path=root / "registry/consumers.yaml",
                    externalized_receipts={target_relative: receipt},
                )

            missing_context = context()
            missing_findings: list[coverage_validator.Finding] = []
            missing = coverage_validator._safe_local_bytes(
                root,
                target_relative,
                location="fixture/source",
                findings=missing_findings,
                failure_code="FIXTURE_UNAVAILABLE",
                portable_context=missing_context,
            )
            self.assertIsInstance(
                missing,
                coverage_validator.ExternalizedArtifact,
            )
            self.assertEqual(missing_findings, [])
            self.assertEqual(
                missing_context.used_externalized_paths,
                {target_relative},
            )

            target_path.parent.mkdir(parents=True)
            target_path.write_bytes(target_raw)
            present_context = context()
            present_findings: list[coverage_validator.Finding] = []
            present = coverage_validator._safe_local_bytes(
                root,
                target_relative,
                location="fixture/source",
                findings=present_findings,
                failure_code="FIXTURE_UNAVAILABLE",
                portable_context=present_context,
            )
            self.assertEqual(present, target_raw)
            self.assertEqual(present_findings, [])
            self.assertEqual(present_context.used_externalized_paths, set())

    def test_synthetic_noncontract_pack_is_rejected_by_unpack_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            archive = base / "active.tar"
            files = synthetic_active_files()
            distribution.write_distribution_archive(
                files,
                active_skill_ids=("active-skill",),
                source_commit="a" * 40,
                source_registry_digests=synthetic_source_digests(files),
                output_path=archive,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "official-document pack",
            ):
                distribution.verify_archive(archive)

    def test_source_registry_digest_must_be_reproducible_from_manifested_snapshot(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            archive = base / "active.tar"
            files = synthetic_active_files()
            snapshot = "registry/source-snapshots/skill-registry.yaml"
            files[snapshot] = b'schema_version: "1.0"\nskills: {}\n'
            source_digests = synthetic_source_digests(files)
            source_digests[snapshot] = "b" * 64
            distribution.write_distribution_archive(
                files,
                active_skill_ids=("active-skill",),
                source_commit="a" * 40,
                source_registry_digests=source_digests,
                output_path=archive,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "source registry snapshot",
            ):
                distribution.verify_archive(archive)

    def test_unregistered_source_registry_snapshot_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "extra-snapshot.tar"
            files = synthetic_active_files()
            files["registry/source-snapshots/unregistered.yaml"] = b"x: 1\n"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=("active-skill",),
                source_commit="a" * 40,
                source_registry_digests=synthetic_source_digests(files),
                output_path=archive,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "snapshot inventory",
            ):
                distribution.verify_archive(archive)

    def test_unpacked_verifier_rejects_nonclosed_active_bundle_expectations(self) -> None:
        canonical = canonical_bundle_entrypoint("active-skill")
        cases = (
            (
                "legacy expectation",
                {
                    "active-skill": {
                        "entrypoint": canonical,
                        "expectation": "legacy-missing",
                    }
                },
                frozenset(),
                "pack-required",
            ),
            (
                "noncanonical entrypoint",
                {
                    "active-skill": {
                        "entrypoint": (
                            "skills/active-skill/references/other-pack/bundle.json"
                        ),
                        "expectation": "pack-required",
                    }
                },
                frozenset(),
                "noncanonical",
            ),
            (
                "record with extra field",
                {
                    "active-skill": {
                        "entrypoint": canonical,
                        "expectation": "pack-required",
                        "note": "not-allowed",
                    }
                },
                frozenset(),
                "record is not exact",
            ),
            (
                "missing exact record",
                {"active-skill": None},
                frozenset(),
                "not exact active-only metadata",
            ),
            (
                "bundle omitted from manifest and tree",
                {},
                frozenset({"active-skill"}),
                "missing from the manifest",
            ),
        )
        for label, overrides, omitted, message in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temporary:
                archive = Path(temporary) / "not-closed.tar"
                distribution.write_distribution_archive(
                    synthetic_active_files(
                        expectation_overrides=overrides,
                        omit_bundles=omitted,
                    ),
                    active_skill_ids=("active-skill",),
                    source_commit="a" * 40,
                    source_registry_digests={},
                    output_path=archive,
                )
                with self.assertRaisesRegex(
                    distribution.DistributionError,
                    message,
                ):
                    distribution.verify_archive(archive)

    def test_archive_verifier_rejects_manifested_bundle_missing_from_tar(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            archive = base / "closed.tar"
            tampered = base / "missing-member.tar"
            distribution.write_distribution_archive(
                synthetic_active_files(),
                active_skill_ids=("active-skill",),
                source_commit="a" * 40,
                source_registry_digests={},
                output_path=archive,
            )
            omitted = canonical_bundle_entrypoint("active-skill")
            with tarfile.open(archive, "r:") as source, tarfile.open(
                tampered,
                "w",
                format=tarfile.PAX_FORMAT,
            ) as target:
                for member in source.getmembers():
                    if member.name == omitted:
                        continue
                    payload = source.extractfile(member)
                    self.assertIsNotNone(payload)
                    target.addfile(member, payload)
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "archive inventory does not match",
            ):
                distribution.verify_archive(tampered)

    def test_synthetic_archive_bytes_are_deterministic_but_invalid_pack_is_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            files = synthetic_active_files(SEVEN_ACTIVE_SKILL_IDS)
            archives = (base / "first.tar", base / "second.tar")
            write_reports = []
            for archive in archives:
                write_reports.append(
                    distribution.write_distribution_archive(
                        files,
                        active_skill_ids=SEVEN_ACTIVE_SKILL_IDS,
                        source_commit="a" * 40,
                        source_registry_digests=synthetic_source_digests(files),
                        output_path=archive,
                    )
                )
                with self.assertRaisesRegex(
                    distribution.DistributionError,
                    "official-document pack",
                ):
                    distribution.verify_archive(
                        archive,
                    )
            self.assertEqual(archives[0].read_bytes(), archives[1].read_bytes())
            self.assertEqual(
                write_reports[0]["archive_sha256"],
                write_reports[1]["archive_sha256"],
            )

    def test_archive_verifier_rejects_noncanonical_eof_padding_and_trailing_bytes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            canonical = base / "canonical.tar"
            files = synthetic_active_files()
            distribution.write_distribution_archive(
                files,
                active_skill_ids=("active-skill",),
                source_commit="a" * 40,
                source_registry_digests=synthetic_source_digests(files),
                output_path=canonical,
            )
            canonical_raw = canonical.read_bytes()
            self.assertEqual(canonical_raw[-1], 0)
            cases = {
                "trailing-payload": canonical_raw
                + b"UNMANIFESTED-TRAILING-PAYLOAD",
                "eof-padding": canonical_raw[:-1] + b"\x01",
            }
            for label, raw in cases.items():
                with self.subTest(case=label):
                    archive = base / f"{label}.tar"
                    archive.write_bytes(raw)
                    with self.assertRaisesRegex(
                        distribution.DistributionError,
                        "canonical normalized tar encoding",
                    ):
                        distribution.verify_archive(archive)

    def test_clean_commit_binding_rejects_ignored_or_non_head_selected_bytes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def git(*arguments: str) -> str:
                result = subprocess.run(
                    ["git", *arguments],
                    cwd=root,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout.strip()

            git("init", "--quiet")
            tracked_path = "contracts/tracked.txt"
            (root / "contracts").mkdir()
            (root / tracked_path).write_bytes(b"tracked bytes\n")
            (root / ".gitignore").write_text(
                "*.ignored\n",
                encoding="utf-8",
            )
            git("add", ".gitignore", tracked_path)
            git(
                "-c",
                "user.name=Active Distribution Test",
                "-c",
                "user.email=active-distribution@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            )
            commit = git("rev-parse", "HEAD")
            clean = distribution.SourceSelection(
                active_skill_ids=(),
                development_skill_ids=(),
                files={tracked_path: b"tracked bytes\n"},
                modes={tracked_path: 0o644},
                source_registry_digests={},
                excluded_legacy_artifacts=(),
            )
            distribution._require_selection_matches_clean_commit(
                root,
                clean,
                commit,
            )

            forged = distribution.SourceSelection(
                active_skill_ids=(),
                development_skill_ids=(),
                files={tracked_path: b"self-consistent forged bytes\n"},
                modes={tracked_path: 0o644},
                source_registry_digests={},
                excluded_legacy_artifacts=(),
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "source bytes differ",
            ):
                distribution._require_selection_matches_clean_commit(
                    root,
                    forged,
                    commit,
                )

            ignored_path = "contracts/generated.ignored"
            (root / ignored_path).write_bytes(b"stable ignored residue\n")
            self.assertEqual(
                git("status", "--porcelain=v1", "--untracked-files=all"),
                "",
            )
            ignored = distribution.SourceSelection(
                active_skill_ids=(),
                development_skill_ids=(),
                files={
                    tracked_path: b"tracked bytes\n",
                    ignored_path: b"stable ignored residue\n",
                },
                modes={
                    tracked_path: 0o644,
                    ignored_path: 0o644,
                },
                source_registry_digests={},
                excluded_legacy_artifacts=(),
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "not tracked by the declared Git commit",
            ):
                distribution._require_selection_matches_clean_commit(
                    root,
                    ignored,
                    commit,
                )

    def test_writer_rejects_development_skill_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "active Skill",
            ):
                distribution.write_distribution_archive(
                    {"skills/dev-skill/SKILL.md": b"# Development\n"},
                    active_skill_ids=("active-skill",),
                    source_commit="a" * 40,
                    source_registry_digests={},
                    output_path=Path(temporary) / "bad.tar",
                )

    def test_writer_rejects_legacy_official_artifact_and_sensitive_paths(self) -> None:
        bad_paths = (
            "skills/qe-rigorous-calculations/references/official-index.json",
            "skills/active-skill/runtime/private-record.json",
            "skills/active-skill/POTCAR",
            ".env",
        )
        for index, path in enumerate(bad_paths):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temporary:
                with self.assertRaises(distribution.DistributionError):
                    distribution.write_distribution_archive(
                        {path: b"not releasable\n"},
                        active_skill_ids=(
                            "active-skill",
                            "qe-rigorous-calculations",
                        ),
                        source_commit="a" * 40,
                        source_registry_digests={},
                        output_path=Path(temporary) / f"bad-{index}.tar",
                    )

    def test_shared_policy_rejects_content_only_payloads_without_leaking_bytes(
        self,
    ) -> None:
        cases = (
            (
                "provider-token",
                provider_token_payload(),
                "RCP-CONTENT-002/provider-token",
            ),
            (
                "private-home",
                private_home_payload(),
                "RCP-CONTENT-004/private-home",
            ),
            (
                "restricted-potential",
                restricted_potential_payload(),
                "RCP-CONTENT-005/restricted-potential-content",
            ),
        )
        for label, payload, expected_code in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temporary:
                files = synthetic_active_files()
                path = f"skills/active-skill/references/{label}.md"
                files[path] = payload
                with self.assertRaises(distribution.DistributionError) as raised:
                    distribution.write_distribution_archive(
                        files,
                        active_skill_ids=("active-skill",),
                        source_commit="a" * 40,
                        source_registry_digests=synthetic_source_digests(files),
                        output_path=Path(temporary) / f"{label}.tar",
                    )
                message = str(raised.exception)
                self.assertIn(path, message)
                self.assertIn(expected_code, message)
                self.assertNotIn(payload.decode("utf-8").strip(), message)

    def test_source_selection_scans_filtered_registry_transform_bytes(self) -> None:
        original = distribution._filtered_registries

        def transformed(*args, **kwargs):
            result = original(*args, **kwargs)
            result["registry/skill-registry.yaml"] += provider_token_payload()
            return result

        with mock.patch.object(
            distribution,
            "_filtered_registries",
            side_effect=transformed,
        ):
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "RCP-CONTENT-002/provider-token",
            ):
                distribution.collect_source_selection(ROOT)

    def test_final_manifest_transform_bytes_are_scanned(self) -> None:
        token = provider_token_payload().strip().decode("ascii")
        receipt_path = (
            "skills/qe-rigorous-calculations/references/"
            f"official-{token}.md"
        )
        files = synthetic_active_files()
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(distribution.DistributionError) as raised:
                distribution.write_distribution_archive(
                    files,
                    active_skill_ids=("active-skill",),
                    source_commit="a" * 40,
                    source_registry_digests=synthetic_source_digests(files),
                    excluded_legacy_artifacts=(
                        {
                            "path": receipt_path,
                            "sha256": "b" * 64,
                            "size": 1,
                        },
                    ),
                    output_path=Path(temporary) / "manifest-payload.tar",
                )
            message = str(raised.exception)
            self.assertIn("ACTIVE_ONLY_MANIFEST.json", message)
            self.assertIn("RCP-CONTENT-002/provider-token", message)
            self.assertNotIn(token, message)

    def test_verify_tree_rescans_manifested_content_before_hash_validation(
        self,
    ) -> None:
        files = synthetic_active_files()
        entries, normalized, modes = distribution._canonical_file_entries(
            files,
            active_skill_ids=("active-skill",),
            modes=None,
        )
        manifest = distribution._manifest(
            entries=entries,
            active_skill_ids=("active-skill",),
            source_commit="a" * 40,
            source_registry_digests=synthetic_source_digests(files),
            excluded_legacy_artifacts=(),
            source_state="candidate-worktree",
            protected_branch="not-asserted",
            build_command=distribution.BUILD_COMMAND,
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path, raw in normalized.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                os.chmod(target, modes[path])
            (root / distribution.MANIFEST_PATH).write_bytes(
                distribution._json_bytes(manifest)
            )
            target = root / "skills/active-skill/SKILL.md"
            target.write_bytes(provider_token_payload())
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "RCP-CONTENT-002/provider-token",
            ):
                distribution.verify_tree(root)

    def test_archive_verifier_rejects_nested_archive_member_before_extraction(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            archive = base / "nested-member.tar"
            extraction = base / "extracted"
            nested_path = "skills/active-skill/references/payload.zip"
            with tarfile.open(
                archive,
                "w",
                format=tarfile.PAX_FORMAT,
            ) as handle:
                raw = b"not-a-reviewed-nested-archive"
                info = tarfile.TarInfo(nested_path)
                info.size = len(raw)
                info.mode = 0o644
                handle.addfile(info, io.BytesIO(raw))
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "RCP-PATH-005/nested-archive",
            ):
                distribution.verify_archive(
                    archive,
                    extraction_root=extraction,
                )
            self.assertFalse((extraction / nested_path).exists())

    def test_writer_requires_shared_policy_in_portable_tool_closure(self) -> None:
        files = synthetic_active_files()
        files.pop("tools/release_content_policy.py")
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "verification tool closure is missing",
            ):
                distribution.write_distribution_archive(
                    files,
                    active_skill_ids=("active-skill",),
                    source_commit="a" * 40,
                    source_registry_digests=synthetic_source_digests(files),
                    output_path=Path(temporary) / "missing-policy.tar",
                )

    def test_unsafe_secret_bearing_path_is_redacted_with_stable_code(self) -> None:
        token = provider_token_payload().strip().decode("ascii")
        unsafe_path = f"skills/active-skill/{token}\nrecord.md"
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(distribution.DistributionError) as raised:
                distribution.write_distribution_archive(
                    {unsafe_path: b"payload\n"},
                    active_skill_ids=("active-skill",),
                    source_commit="a" * 40,
                    source_registry_digests={},
                    output_path=Path(temporary) / "unsafe.tar",
                )
            message = str(raised.exception)
            self.assertIn("<unsafe-path>", message)
            self.assertIn("RCP-PATH-001/unsafe-path", message)
            self.assertNotIn(token, message)

    def test_unpacked_verifier_rejects_non_active_consumer_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            archive = base / "metadata.tar"
            files = synthetic_active_files()
            files["registry/official-document-consumers.yaml"] = (
                b'schema_version: "1.0"\ndefault_policy: deny\nbindings:\n'
                b"  - consumer_skill_id: development-skill\n"
                b"    consumer_lifecycle: development\n"
            )
            distribution.write_distribution_archive(
                files,
                active_skill_ids=("active-skill",),
                source_commit="a" * 40,
                source_registry_digests={},
                output_path=archive,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "consumer",
            ):
                distribution.verify_archive(archive)

    def test_verifier_rejects_path_traversal_and_links(self) -> None:
        for member_name, member_type in (
            ("../escape", tarfile.REGTYPE),
            ("skills/active-skill/link", tarfile.SYMTYPE),
            ("skills/active-skill/hard", tarfile.LNKTYPE),
        ):
            with self.subTest(member=member_name), tempfile.TemporaryDirectory() as temporary:
                archive = Path(temporary) / "hostile.tar"
                with tarfile.open(archive, "w", format=tarfile.PAX_FORMAT) as handle:
                    info = tarfile.TarInfo(member_name)
                    info.type = member_type
                    if member_type == tarfile.REGTYPE:
                        info.size = 1
                        handle.addfile(info, io.BytesIO(b"x"))
                    else:
                        info.linkname = "target"
                        handle.addfile(info)
                with self.assertRaises(distribution.DistributionError):
                    distribution.verify_archive(archive)

    def test_real_selection_has_exact_active_authority_and_verifier_closure(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        consumers = yaml.safe_load(
            selection.files[
                "registry/official-document-consumers.yaml"
            ]
        )
        authorities = yaml.safe_load(
            selection.files[
                "registry/official-source-authorities.yaml"
            ]
        )
        self.assertEqual(
            set(authorities["authorities"]),
            {
                binding["authority_id"]
                for binding in consumers["bindings"]
            },
        )
        self.assertEqual(len(authorities["authorities"]), 15)
        self.assertEqual(len(consumers["bindings"]), 20)
        self.assertTrue(
            set(distribution.VERIFICATION_TOOL_PATHS).issubset(selection.files)
        )
        self.assertIn(distribution.DEPENDENCY_MANIFEST_PATH, selection.files)
        self.assertEqual(
            set(selection.source_registry_digests),
            {
                distribution._source_snapshot_path(path)
                for path in distribution.SOURCE_REGISTRY_PATHS
            },
        )
        for path, digest in selection.source_registry_digests.items():
            self.assertEqual(distribution._sha256(selection.files[path]), digest)

    def test_real_repository_build_is_reproducible_and_active_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            first = base / "first.tar"
            second = base / "second.tar"
            first_report = distribution.build_distribution(ROOT, first)
            second_report = distribution.build_distribution(ROOT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                first_report["archive_sha256"],
                second_report["archive_sha256"],
            )
            self.assertEqual(first_report["active_skill_count"], 7)
            extracted = base / "unpacked-first"
            second_extracted = base / "unpacked-second"
            verified = distribution.verify_archive(
                first,
                extraction_root=extracted,
            )
            second_verified = distribution.verify_archive(
                second,
                extraction_root=second_extracted,
            )
            self.assertEqual(verified, second_verified)
            packaged = subprocess.run(
                [
                    sys.executable,
                    str(
                        extracted
                        / "tools"
                        / "build_active_only_distribution.py"
                    ),
                    "verify-tree",
                    str(extracted),
                ],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertEqual(packaged.returncode, 0, packaged.stderr)
            self.assertEqual(
                json.loads(packaged.stdout)["verification"],
                "passed",
            )
            policy_module = (
                extracted / "tools" / "release_content_policy.py"
            )
            policy_raw = policy_module.read_bytes()
            policy_module.unlink()
            missing_policy = subprocess.run(
                [
                    sys.executable,
                    str(
                        extracted
                        / "tools"
                        / "build_active_only_distribution.py"
                    ),
                    "verify-tree",
                    str(extracted),
                ],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONPATH": "",
                },
            )
            self.assertNotEqual(missing_policy.returncode, 0)
            policy_module.write_bytes(policy_raw + b"\n# tampered policy module\n")
            tampered_policy = subprocess.run(
                [
                    sys.executable,
                    str(
                        extracted
                        / "tools"
                        / "build_active_only_distribution.py"
                    ),
                    "verify-tree",
                    str(extracted),
                ],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONPATH": "",
                },
            )
            self.assertNotEqual(tampered_policy.returncode, 0)
            self.assertNotIn("tampered policy module", tampered_policy.stderr)
            policy_module.write_bytes(policy_raw)
            self.assertEqual(verified["verification"], "passed")
            active = set(verified["active_skill_ids"])
            self.assertTrue(
                all(
                    Path(path).parts[1] in active
                    for path in verified["file_paths"]
                    if Path(path).parts[0] == "skills"
                )
            )
            self.assertEqual(verified["legacy_official_artifact_count"], 0)
            self.assertEqual(verified["official_document_pack_audit"], "partial")
            self.assertEqual(verified["official_document_pack_count"], 7)
            self.assertEqual(verified["source_registry_snapshot_count"], 10)
            self.assertGreater(
                verified["official_document_externalized_source_count"],
                0,
            )

            consumers = yaml.safe_load(
                (
                    extracted
                    / "registry"
                    / "official-document-consumers.yaml"
                ).read_text(encoding="utf-8")
            )
            authorities = yaml.safe_load(
                (
                    extracted
                    / "registry"
                    / "official-source-authorities.yaml"
                ).read_text(encoding="utf-8")
            )
            authority_closure = {
                binding["authority_id"] for binding in consumers["bindings"]
            }
            self.assertEqual(
                set(authorities["authorities"]),
                authority_closure,
            )

    def test_real_archive_rejects_rewrapped_malformed_pack_json(self) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        target = canonical_bundle_entrypoint("cif-structure-analysis")
        files[target] = b'{"pack": invalid json}\n'
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "malformed.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=selection.source_registry_digests,
                output_path=archive,
                modes=selection.modes,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "official-document pack",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_authority_superset_outside_active_bindings(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        files["registry/official-source-authorities.yaml"] = files[
            distribution._source_snapshot_path(
                "registry/official-source-authorities.yaml"
            )
        ]
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "authority-superset.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=selection.source_registry_digests,
                output_path=archive,
                modes=selection.modes,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "exact active consumer binding closure",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_consumer_binding_drift_from_source_snapshot(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        registry_path = "registry/official-document-consumers.yaml"
        consumers = yaml.safe_load(files[registry_path])
        consumers["bindings"][0]["provider_id"] = "tampered-provider"
        files[registry_path] = yaml.safe_dump(
            consumers,
            allow_unicode=False,
            default_flow_style=False,
            sort_keys=True,
            width=1000,
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "consumer-binding-drift.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=selection.source_registry_digests,
                output_path=archive,
                modes=selection.modes,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "canonical source snapshot projection",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_live_registry_projection_drift(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        for label, registry_path in (
            ("interface", "registry/interface-registry.yaml"),
            ("route", "registry/operation-routes.yaml"),
            (
                "storage",
                "registry/official-document-storage-discovery.yaml",
            ),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temporary:
                files = dict(selection.files)
                registry = yaml.safe_load(files[registry_path])
                if label == "interface":
                    interface_id = sorted(registry["interfaces"])[0]
                    registry["interfaces"][interface_id]["display_name"] = (
                        "tampered active interface"
                    )
                else:
                    registry["projection_tamper"] = True
                files[registry_path] = distribution._yaml_bytes(registry)
                archive = Path(temporary) / f"{label}-projection-drift.tar"
                distribution.write_distribution_archive(
                    files,
                    active_skill_ids=selection.active_skill_ids,
                    source_commit="a" * 40,
                    source_registry_digests=selection.source_registry_digests,
                    output_path=archive,
                    modes=selection.modes,
                    excluded_legacy_artifacts=(
                        selection.excluded_legacy_artifacts
                    ),
                )
                with self.assertRaisesRegex(
                    distribution.DistributionError,
                    "canonical source snapshot projection",
                ):
                    distribution.verify_archive(archive)

    def test_real_archive_rejects_self_consistent_forged_source_tree_identity(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        loaded = {
            registry_path: yaml.safe_load(
                files[distribution._source_snapshot_path(registry_path)]
            )
            for registry_path in distribution.SOURCE_REGISTRY_PATHS
        }
        forged_digest = "8" * 64
        loaded["registry/skill-registry.yaml"]["skills"][
            "cif-structure-analysis"
        ]["source_tree_sha256"] = forged_digest
        source_skill_path = distribution._source_snapshot_path(
            "registry/skill-registry.yaml"
        )
        files[source_skill_path] = distribution._yaml_bytes(
            loaded["registry/skill-registry.yaml"]
        )
        files.update(
            distribution._filtered_registries(
                loaded,
                selection.active_skill_ids,
            )
        )

        pack_root = (
            "skills/cif-structure-analysis/references/"
            "official-source-pack/"
        )
        scope_path = f"{pack_root}scope-inventory.json"
        coverage_path = f"{pack_root}coverage.json"
        scope = json.loads(files[scope_path])
        scope["skill_registry_binding"]["registry_sha256"] = (
            distribution._sha256(files[source_skill_path])
        )
        scope["skill_registry_binding"]["source_tree_sha256"] = forged_digest
        scope["enumeration"]["extractor"]["input_sha256"] = forged_digest
        files[scope_path] = distribution._json_bytes(scope)
        coverage = json.loads(files[coverage_path])
        coverage["scope_inventory_ref"]["sha256"] = distribution._sha256(
            files[scope_path]
        )
        files[coverage_path] = distribution._json_bytes(coverage)

        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "forged-source-tree.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=synthetic_source_digests(files),
                output_path=archive,
                modes=selection.modes,
                excluded_legacy_artifacts=(
                    selection.excluded_legacy_artifacts
                ),
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "source tree",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_semantically_invalid_source_registry_snapshot(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        loaded = {
            registry_path: yaml.safe_load(
                files[distribution._source_snapshot_path(registry_path)]
            )
            for registry_path in distribution.SOURCE_REGISTRY_PATHS
        }
        loaded["registry/software-registry.yaml"]["aggregate_codes"].append(
            loaded["registry/software-registry.yaml"]["aggregate_codes"][0]
        )
        source_path = distribution._source_snapshot_path(
            "registry/software-registry.yaml"
        )
        files[source_path] = distribution._yaml_bytes(
            loaded["registry/software-registry.yaml"]
        )
        files.update(
            distribution._filtered_registries(
                loaded,
                selection.active_skill_ids,
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "invalid-consumer-source.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=synthetic_source_digests(files),
                output_path=archive,
                modes=selection.modes,
                excluded_legacy_artifacts=(
                    selection.excluded_legacy_artifacts
                ),
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "AUTHORITY_REGISTRY_INVALID",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_nonactive_contract_lifecycle_snapshot(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        loaded = {
            registry_path: yaml.safe_load(
                files[distribution._source_snapshot_path(registry_path)]
            )
            for registry_path in distribution.SOURCE_REGISTRY_PATHS
        }
        interface = loaded["registry/interface-registry.yaml"]["interfaces"][
            "official-corpus-manifest@1.1"
        ]
        interface["lifecycle"] = "planned"
        interface["schema_path"] = None
        interface["schema_sha256"] = None
        source_path = distribution._source_snapshot_path(
            "registry/interface-registry.yaml"
        )
        files[source_path] = distribution._yaml_bytes(
            loaded["registry/interface-registry.yaml"]
        )
        files.update(
            distribution._filtered_registries(
                loaded,
                selection.active_skill_ids,
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "planned-contract-source.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=synthetic_source_digests(files),
                output_path=archive,
                modes=selection.modes,
                excluded_legacy_artifacts=(
                    selection.excluded_legacy_artifacts
                ),
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "CONTRACT_LIFECYCLE_INVALID",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_dangling_processor_implementation_hash(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        files["tools/build_official_document_packs.py"] += b"\n# tampered\n"
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "processor-tamper.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=selection.source_registry_digests,
                output_path=archive,
                modes=selection.modes,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "consumer-processors",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_rewrapped_deleted_pack_record(self) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        pack_root = (
            "skills/cif-structure-analysis/references/official-source-pack/"
        )
        bundle = json.loads(files[f"{pack_root}bundle.json"])
        deleted_name = bundle["records"]["corpora"][0]
        del files[f"{pack_root}{deleted_name}"]
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "missing-record.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=selection.source_registry_digests,
                output_path=archive,
                modes=selection.modes,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "official-document pack",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_rewrapped_record_reference_hash_tamper(self) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        coverage_path = (
            "skills/cif-structure-analysis/references/"
            "official-source-pack/coverage.json"
        )
        coverage = json.loads(files[coverage_path])
        coverage["corpus_refs"][0]["sha256"] = "0" * 64
        files[coverage_path] = (
            json.dumps(
                coverage,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "hash-tamper.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=selection.source_registry_digests,
                output_path=archive,
                modes=selection.modes,
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "official-document pack",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_rewrapped_forged_record_producer(self) -> None:
        selection = distribution.collect_source_selection(ROOT)
        files = dict(selection.files)
        coverage_path = (
            "skills/cif-structure-analysis/references/"
            "official-source-pack/coverage.json"
        )
        coverage = json.loads(files[coverage_path])
        coverage["producer"]["tool_id"] = "forged-builder"
        files[coverage_path] = (
            json.dumps(
                coverage,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "forged-producer.tar"
            distribution.write_distribution_archive(
                files,
                active_skill_ids=selection.active_skill_ids,
                source_commit="a" * 40,
                source_registry_digests=selection.source_registry_digests,
                output_path=archive,
                modes=selection.modes,
                excluded_legacy_artifacts=(
                    selection.excluded_legacy_artifacts
                ),
            )
            with self.assertRaisesRegex(
                distribution.DistributionError,
                "canonical builder identity",
            ):
                distribution.verify_archive(archive)

    def test_real_archive_rejects_semantic_processor_and_mapping_mutations(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        pack_root = (
            "skills/cif-structure-analysis/references/"
            "official-source-pack/"
        )
        coverage_path = f"{pack_root}coverage.json"
        scope_path = f"{pack_root}scope-inventory.json"
        corpus_path = f"{pack_root}corpus-ase-3-29.json"
        slice_path = f"{pack_root}slices-ase-3-29.json"
        for case, message in (
            ("official-disposition", "has invalid coverage logic"),
            ("scope-output", "scope extractor receipt"),
            ("slice-output", "processor does not bind exact IO"),
            ("cross-skill-local-evidence", "subject origin .* does not resolve"),
            (
                "corpus-url",
                "external source identity locator is invalid",
            ),
            (
                "corpus-source-linkage",
                "slice manifest includes source IDs outside the referenced "
                "corpus included set",
            ),
        ):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                files = dict(selection.files)
                coverage = json.loads(files[coverage_path])
                if case == "official-disposition":
                    mapping = next(
                        item
                        for item in coverage["mappings"].values()
                        if item["mapping_status"] == "partial"
                        and item["disposition"] == "partial"
                    )
                    mapping.update(
                        {
                            "disposition": "not-applicable",
                            "limitations": [],
                            "mapping_status": "complete",
                            "slice_refs": [],
                        }
                    )
                elif case == "scope-output":
                    scope = json.loads(files[scope_path])
                    scope["enumeration"]["extractor"]["output_sha256"] = "3" * 64
                    files[scope_path] = distribution._json_bytes(scope)
                    coverage["scope_inventory_ref"]["sha256"] = (
                        distribution._sha256(files[scope_path])
                    )
                elif case == "slice-output":
                    slices = json.loads(files[slice_path])
                    next(iter(slices["sources"].values()))["processor"][
                        "output_sha256"
                    ] = "4" * 64
                    files[slice_path] = distribution._json_bytes(slices)
                    slice_id = slices["slice_manifest_id"]
                    next(
                        item
                        for item in coverage["slice_manifest_refs"]
                        if item["slice_manifest_id"] == slice_id
                    )["sha256"] = distribution._sha256(files[slice_path])
                elif case == "cross-skill-local-evidence":
                    scope = json.loads(files[scope_path])
                    subject = next(
                        item
                        for item in scope["subjects"]
                        if item["evidence_class"] != "official-provider-required"
                    )
                    external_path = "tools/strict_json.py"
                    subject["origin_refs"][0] = {
                        "path": external_path,
                        "selector": {
                            "kind": "whole-file",
                            "value": "*",
                        },
                        "sha256": distribution._sha256(files[external_path]),
                    }
                    scope["enumeration"]["extractor"]["output_sha256"] = (
                        distribution._canonical_projection_sha256(
                            scope["subjects"]
                        )
                    )
                    files[scope_path] = distribution._json_bytes(scope)
                    coverage["scope_inventory_ref"]["sha256"] = (
                        distribution._sha256(files[scope_path])
                    )
                elif case in {"corpus-url", "corpus-source-linkage"}:
                    corpus = json.loads(files[corpus_path])
                    source_id = next(iter(corpus["source_inventory"]))
                    if case == "corpus-url":
                        corpus["source_inventory"][source_id][
                            "source_identity"
                        ]["locator"] = (
                            "https://example.com/forged-official-doc"
                        )
                    else:
                        del corpus["source_inventory"][source_id]
                    corpus["discovery"]["processor"]["output_sha256"] = (
                        distribution._canonical_projection_sha256(
                            corpus["source_inventory"]
                        )
                    )
                    files[corpus_path] = distribution._json_bytes(corpus)
                    corpus_sha = distribution._sha256(files[corpus_path])
                    corpus_id = corpus["corpus_id"]
                    next(
                        item
                        for item in coverage["corpus_refs"]
                        if item["corpus_id"] == corpus_id
                    )["sha256"] = corpus_sha
                    slices = json.loads(files[slice_path])
                    slices["corpus_ref"]["sha256"] = corpus_sha
                    if case == "corpus-url":
                        slice_source = slices["sources"][source_id]
                        slice_source["source_identity"] = corpus[
                            "source_inventory"
                        ][source_id]["source_identity"]
                        for item in slice_source["slices"]:
                            item["content"]["locator"] = corpus[
                                "source_inventory"
                            ][source_id]["source_identity"]["locator"]
                        slice_source["processor"]["output_sha256"] = (
                            distribution._canonical_projection_sha256(
                                {
                                    "slices": slice_source["slices"],
                                    "source_loss_accounting": slice_source[
                                        "source_loss_accounting"
                                    ],
                                }
                            )
                        )
                    files[slice_path] = distribution._json_bytes(slices)
                    next(
                        item
                        for item in coverage["slice_manifest_refs"]
                        if item["slice_manifest_id"]
                        == slices["slice_manifest_id"]
                    )["sha256"] = distribution._sha256(files[slice_path])
                files[coverage_path] = distribution._json_bytes(coverage)
                archive = Path(temporary) / f"{case}.tar"
                distribution.write_distribution_archive(
                    files,
                    active_skill_ids=selection.active_skill_ids,
                    source_commit="a" * 40,
                    source_registry_digests=selection.source_registry_digests,
                    output_path=archive,
                    modes=selection.modes,
                    excluded_legacy_artifacts=(
                        selection.excluded_legacy_artifacts
                    ),
                )
                with self.assertRaisesRegex(
                    distribution.DistributionError,
                    message,
                ):
                    distribution.verify_archive(archive)

    def test_real_archive_rejects_canonical_semantic_false_pass_mutations(
        self,
    ) -> None:
        selection = distribution.collect_source_selection(ROOT)
        pack_root = (
            "skills/cif-structure-analysis/references/"
            "official-source-pack/"
        )
        coverage_path = f"{pack_root}coverage.json"
        scope_path = f"{pack_root}scope-inventory.json"
        corpus_path = f"{pack_root}corpus-ase-3-29.json"
        slice_path = f"{pack_root}slices-ase-3-29.json"

        def update_slice(
            files: dict[str, bytes],
            coverage: dict[str, object],
            slices: dict[str, object],
        ) -> None:
            for source in slices["sources"].values():
                projection = {
                    key: source[key]
                    for key in (
                        "slices",
                        "source_loss_accounting",
                    )
                }
                source["processor"]["output_sha256"] = (
                    distribution._canonical_projection_sha256(projection)
                )
            files[slice_path] = distribution._json_bytes(slices)
            next(
                item
                for item in coverage["slice_manifest_refs"]
                if item["slice_manifest_id"] == slices["slice_manifest_id"]
            )["sha256"] = distribution._sha256(files[slice_path])

        def update_scope(
            files: dict[str, bytes],
            coverage: dict[str, object],
            scope: dict[str, object],
        ) -> None:
            scope["enumeration"]["extractor"]["output_sha256"] = (
                distribution._canonical_projection_sha256(scope["subjects"])
            )
            files[scope_path] = distribution._json_bytes(scope)
            coverage["scope_inventory_ref"]["sha256"] = (
                distribution._sha256(files[scope_path])
            )

        def update_corpus(
            files: dict[str, bytes],
            coverage: dict[str, object],
            corpus: dict[str, object],
        ) -> None:
            files[corpus_path] = distribution._json_bytes(corpus)
            corpus_sha = distribution._sha256(files[corpus_path])
            next(
                item
                for item in coverage["corpus_refs"]
                if item["corpus_id"] == corpus["corpus_id"]
            )["sha256"] = corpus_sha
            slices = json.loads(files[slice_path])
            slices["corpus_ref"]["sha256"] = corpus_sha
            files[slice_path] = distribution._json_bytes(slices)
            next(
                item
                for item in coverage["slice_manifest_refs"]
                if item["slice_manifest_id"] == slices["slice_manifest_id"]
            )["sha256"] = distribution._sha256(files[slice_path])

        cases = (
            ("slice-full-extent", "whole-source requires full extent"),
            (
                "slice-content-locator",
                "content locator must match corpus source locator",
            ),
            ("scope-origin-selector", "SCOPE_SUBJECT_ORIGIN_INVALID"),
            ("corpus-blocker-overclaim", "COMPLETENESS_STATUS_OVERCLAIM"),
            (
                "corpus-self-asserted-complete",
                "processor cannot claim complete under unverified mode",
            ),
            (
                "corpus-version-scope",
                "source universe or authority scope is not exact",
            ),
        )
        for case, expected_code in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                files = dict(selection.files)
                coverage = json.loads(files[coverage_path])
                if case in {
                    "slice-full-extent",
                    "slice-content-locator",
                }:
                    slices = json.loads(files[slice_path])
                    first_source = next(iter(slices["sources"].values()))
                    first_slice = first_source["slices"][0]
                    if case == "slice-full-extent":
                        first_slice["raw_byte_range"]["start_byte"] = 1
                        first_slice["raw_byte_range"]["byte_count"] = (
                            first_source["raw_source_extent_bytes"] - 1
                        )
                    else:
                        first_slice["content"]["locator"] = (
                            "https://example.com/forged-receipt"
                        )
                    update_slice(files, coverage, slices)
                elif case == "scope-origin-selector":
                    scope = json.loads(files[scope_path])
                    scope["subjects"][0]["origin_refs"][0]["selector"][
                        "value"
                    ] = "not-star"
                    update_scope(files, coverage, scope)
                else:
                    corpus = json.loads(files[corpus_path])
                    if case == "corpus-blocker-overclaim":
                        corpus["blockers"].append(
                            {
                                "code": "portable-red-team-blocker",
                                "description": (
                                    "Synthetic blocker proves status ceiling replay."
                                ),
                                "dimension": "inventory",
                            }
                        )
                    elif case == "corpus-self-asserted-complete":
                        corpus["discovery"][
                            "upstream_universe_complete"
                        ] = True
                        corpus["discovery"]["inventory_scope"] = (
                            "upstream-universe"
                        )
                        corpus["status"] = "complete"
                    else:
                        corpus["version_scope"]["value"] = "forged-version"
                    update_corpus(files, coverage, corpus)
                files[coverage_path] = distribution._json_bytes(coverage)
                archive = Path(temporary) / f"{case}.tar"
                distribution.write_distribution_archive(
                    files,
                    active_skill_ids=selection.active_skill_ids,
                    source_commit="a" * 40,
                    source_registry_digests=selection.source_registry_digests,
                    output_path=archive,
                    modes=selection.modes,
                    excluded_legacy_artifacts=(
                        selection.excluded_legacy_artifacts
                    ),
                )
                with self.assertRaisesRegex(
                    distribution.DistributionError,
                    expected_code,
                ):
                    distribution.verify_archive(archive)

    def test_tag_ci_builds_compares_verifies_and_hashes_active_artifact(
        self,
    ) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")
        strict_gate = workflow.index(
            "python tools/validate_all_skills.py"
        )
        active_step = workflow.index(
            "Build and verify reproducible active-only tag artifact"
        )
        self.assertLess(strict_gate, active_step)
        clean_gate = workflow.index(
            "git status --porcelain=v1 --untracked-files=all"
        )
        first_build = workflow.index(
            "python tools/build_active_only_distribution.py build"
        )
        self.assertLess(active_step, clean_gate)
        self.assertLess(clean_gate, first_build)
        self.assertIn(
            "Tag artifact build requires a clean tracked and untracked "
            "Git worktree.",
            workflow,
        )
        self.assertEqual(
            workflow.count(
                "python tools/build_active_only_distribution.py build"
            ),
            2,
        )
        self.assertEqual(
            workflow.count("--require-clean-commit"),
            2,
        )
        self.assertEqual(
            workflow.count(
                "python tools/build_active_only_distribution.py verify"
            ),
            2,
        )
        self.assertIn("cmp --", workflow)
        self.assertIn('cd "$task_artifact_dir"', workflow)
        self.assertIn(
            "sha256sum vibe-dft-active-only.tar | tee SHA256SUMS",
            workflow,
        )
        self.assertNotIn(
            'sha256sum "$task_artifact_dir/vibe-dft-active-only.tar"',
            workflow,
        )
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertNotIn("gh release", workflow)


if __name__ == "__main__":
    unittest.main()
