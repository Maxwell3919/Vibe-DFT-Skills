from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_official_document_packs as builder  # noqa: E402


class OfficialDocumentPackBuilderTests(unittest.TestCase):
    def context(
        self,
        root: Path,
        *,
        skill_id: str = "demo-skill",
        seed: dict[str, object] | None = None,
        snapshot: object | None = None,
    ) -> builder.BuildContext:
        skill_root = root / "skills" / skill_id
        (skill_root / "references").mkdir(parents=True, exist_ok=True)
        return builder.BuildContext(
            root=root,
            snapshot=snapshot or SimpleNamespace(),
            skill_id=skill_id,
            skill_root=skill_root,
            seed_path=skill_root / "references" / "source-pack-seed.json",
            seed=seed
            or {
                "providers": [],
                "limitations": ["synthetic"],
                "blockers": [],
                "status_ceiling": "partial",
            },
        )

    @staticmethod
    def provider(
        *,
        license_record: dict[str, object] | None = None,
    ) -> builder.ProviderBuild:
        identity = {
            "kind": "sha256",
            "value": "a" * 64,
            "raw_sha256": "a" * 64,
            "raw_bytes": 10,
            "resolver_receipt": None,
        }
        slice_record = {
            "slice_id": "slice-one",
            "loss_ids": ["loss-one"],
        }
        return builder.ProviderBuild(
            input_id="provider-one",
            authority_id="authority-one",
            provider_id="provider-one",
            version_scope={},
            retrieved_utc="2026-07-24T00:00:00Z",
            authority_root="https://example.invalid/",
            authority_revision="r1",
            inventory_format="declarative-source-catalog-v1",
            inventory_locator="catalog.json",
            inventory_sha256="b" * 64,
            upstream_universe_complete=False,
            included_sources=(
                {
                    "source_id": "source-one",
                    "identity": identity,
                },
            ),
            reviewed_exclusions=(),
            source_slices=(
                {
                    "source_id": "source-one",
                    "source_identity": identity,
                    "slices": [slice_record],
                    "loss_ledger": [
                        {
                            "loss_id": "loss-one",
                            "affected_slice_ids": ["slice-one"],
                        }
                    ],
                },
            ),
            subject_slice_ids={"subject-one": ("slice-one",)},
            license=copy.deepcopy(license_record or {}),
            limitations=(),
            blockers=(),
        )

    def test_strict_json_rejects_duplicate_bom_nan_and_oversize(self) -> None:
        payloads = {
            "duplicate": b'{"a":1,"a":2}\n',
            "bom": b"\xef\xbb\xbf{}\n",
            "nan": b'{"a":NaN}\n',
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, raw in payloads.items():
                path = root / f"{name}.json"
                path.write_bytes(raw)
                with self.subTest(name=name), self.assertRaises(
                    builder.PackBuildError
                ):
                    builder._load_json_object(path, name)
            oversized = root / "oversized.json"
            oversized.write_bytes(b"{}\n")
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "maximum JSON byte length",
            ):
                builder._load_json_object(
                    oversized,
                    "oversized",
                    max_bytes=2,
                )

    def test_seed_and_specialized_contracts_reject_status_ids_refs_and_version(
        self,
    ) -> None:
        seed_schema = json.loads(
            (ROOT / "contracts" / "official-document-pack-seed.schema.json")
            .read_text(encoding="utf-8")
        )
        seed_validator = Draft202012Validator(
            seed_schema,
            format_checker=FormatChecker(),
        )
        seed = json.loads(
            (
                ROOT
                / "skills"
                / "qe-rigorous-calculations"
                / "references"
                / "source-pack-seed.json"
            ).read_text(encoding="utf-8")
        )
        mutations = []
        invalid_status = copy.deepcopy(seed)
        invalid_status["status_ceiling"] = "complete"
        mutations.append(invalid_status)
        invalid_id = copy.deepcopy(seed)
        invalid_id["skill_id"] = "QE Skill"
        mutations.append(invalid_id)
        invalid_extractor = copy.deepcopy(seed)
        invalid_extractor["scope_extractor_id"] = "../unsafe"
        mutations.append(invalid_extractor)
        invalid_ref = copy.deepcopy(seed)
        invalid_ref["providers"][0]["source_ref"]["path"] = "../escape.json"
        mutations.append(invalid_ref)
        missing_options = copy.deepcopy(seed)
        missing_options["providers"][0].pop("options_ref")
        mutations.append(missing_options)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertTrue(list(seed_validator.iter_errors(mutation)))

        qe_schema = json.loads(
            (ROOT / "contracts" / "qe-source-pack-input.schema.json")
            .read_text(encoding="utf-8")
        )
        qe_validator = Draft202012Validator(
            qe_schema,
            format_checker=FormatChecker(),
        )
        qe_catalog = json.loads(
            (
                ROOT
                / "skills"
                / "qe-rigorous-calculations"
                / "references"
                / "source-pack-input-catalog.json"
            ).read_text(encoding="utf-8")
        )
        missing_contract = copy.deepcopy(qe_catalog)
        missing_contract.pop("contract_name")
        invalid_version = copy.deepcopy(qe_catalog)
        invalid_version["manuals"][0]["version"] = "latest"
        path_like_name = copy.deepcopy(qe_catalog)
        path_like_name["manuals"][0]["name"] = "INPUT_pw/../../secrets"
        unsafe_character_name = copy.deepcopy(qe_catalog)
        unsafe_character_name["manuals"][0]["name"] = "INPUT_pw.x"
        self.assertTrue(list(qe_validator.iter_errors(missing_contract)))
        self.assertTrue(list(qe_validator.iter_errors(invalid_version)))
        self.assertTrue(list(qe_validator.iter_errors(path_like_name)))
        self.assertTrue(list(qe_validator.iter_errors(unsafe_character_name)))

        vasp_schema = json.loads(
            (ROOT / "contracts" / "vasp-source-pack-input.schema.json")
            .read_text(encoding="utf-8")
        )
        vasp_validator = Draft202012Validator(
            vasp_schema,
            format_checker=FormatChecker(),
        )
        vasp_catalog = json.loads(
            (
                ROOT
                / "skills"
                / "vasp-rigorous-calculations"
                / "references"
                / "source-pack-input-catalog.json"
            ).read_text(encoding="utf-8")
        )
        vasp_catalog["contract_name"] = "wrong-contract"
        self.assertTrue(list(vasp_validator.iter_errors(vasp_catalog)))

        source_schema = json.loads(
            (
                ROOT
                / "contracts"
                / "official-document-source-catalog.schema.json"
            ).read_text(encoding="utf-8")
        )
        source_validator = Draft202012Validator(
            source_schema,
            format_checker=FormatChecker(),
        )
        source_catalog = json.loads(
            (
                ROOT
                / "skills"
                / "catmap-microkinetics"
                / "references"
                / "source-pack-source-catalog-catmap.json"
            ).read_text(encoding="utf-8")
        )
        source_catalog["sources"][0]["slices"][0]["selector"]["value"] = (
            "descriptive whole-source label"
        )
        self.assertTrue(list(source_validator.iter_errors(source_catalog)))
        missing_blocker_dimensions = json.loads(
            (
                ROOT
                / "skills"
                / "catmap-microkinetics"
                / "references"
                / "source-pack-source-catalog-catmap.json"
            ).read_text(encoding="utf-8")
        )
        missing_blocker_dimensions["blockers"][0].pop("dimensions", None)
        self.assertTrue(
            list(source_validator.iter_errors(missing_blocker_dimensions))
        )

    def test_every_live_seed_binds_its_exact_scope_extractor(self) -> None:
        seed_paths = sorted(
            (ROOT / "skills").glob("*/references/source-pack-seed.json")
        )
        self.assertEqual(len(seed_paths), 26)
        for seed_path in seed_paths:
            seed = json.loads(seed_path.read_text(encoding="utf-8"))
            scope_path = ROOT / seed["scope_catalog_ref"]["path"]
            scope = json.loads(scope_path.read_text(encoding="utf-8"))
            with self.subTest(skill_id=seed["skill_id"]):
                self.assertEqual(scope["skill_id"], seed["skill_id"])
                self.assertEqual(
                    seed["scope_extractor_id"],
                    scope["extractor_id"],
                )

    def test_live_seeds_do_not_retain_resolved_registration_state_blockers(
        self,
    ) -> None:
        snapshot = builder.load_registry_snapshot(
            ROOT,
            validate_sources=True,
        )
        for seed_path in sorted(
            (ROOT / "skills").glob("*/references/source-pack-seed.json")
        ):
            skill_id = seed_path.parents[1].name
            with self.subTest(skill_id=skill_id):
                builder.load_seed(ROOT, snapshot, skill_id)

    def test_output_blocker_codes_are_safe_and_collisions_fail_closed(
        self,
    ) -> None:
        projected = builder._output_blockers(
            [
                {
                    "code": "DOC.BODY.BYTES.EXTERNAL",
                    "description": "Official body bytes remain external.",
                    "dimensions": ["corpus", "slices"],
                }
            ],
            label="synthetic",
            dimension="corpus",
        )
        self.assertEqual(
            projected,
            [
                {
                    "code": "doc.body.bytes.external",
                    "description": "Official body bytes remain external.",
                }
            ],
        )
        with self.assertRaisesRegex(
            builder.PackBuildError,
            "collide after safe output projection",
        ):
            builder._output_blockers(
                [
                    {
                        "code": "A:B",
                        "description": "First.",
                        "dimensions": ["corpus"],
                    },
                    {
                        "code": "a-b",
                        "description": "Second.",
                        "dimensions": ["corpus"],
                    },
                ],
                label="synthetic",
                dimension="corpus",
            )

    def test_output_subject_ids_are_safe_and_collisions_fail_closed(
        self,
    ) -> None:
        self.assertEqual(
            builder._output_id_map(
                ["ase:cif-materialization", "section:SKILL:purpose"],
                label="synthetic",
            ),
            {
                "ase:cif-materialization": "ase-cif-materialization",
                "section:SKILL:purpose": "section-skill-purpose",
            },
        )
        with self.assertRaisesRegex(
            builder.PackBuildError,
            "collide after safe output projection",
        ):
            builder._output_id_map(
                ["A:B", "a-b"],
                label="synthetic",
            )

    def test_output_version_scope_follows_corpus_contract(self) -> None:
        rolling_digest = "c" * 64
        exact = builder._output_version_scope(
            {
                "kind": "exact",
                "value": "1.2.3",
                "retrieved_utc": "2026-07-24T00:00:00Z",
                "snapshot_identity": {
                    "kind": "revision",
                    "value": "abc",
                    "content_sha256": "b" * 64,
                },
            },
        )
        self.assertEqual(
            exact,
            {
                "kind": "exact",
                "value": "1.2.3",
                "retrieved_utc": None,
                "snapshot_identity": None,
            },
        )
        rolling = builder._output_version_scope(
            {
                "kind": "latest-at-retrieval",
                "value": "rolling label",
                "retrieved_utc": "2026-07-24T00:00:00Z",
                "snapshot_identity": None,
            },
            rolling_snapshot_sha256=rolling_digest,
        )
        self.assertEqual(rolling["value"], None)
        self.assertEqual(rolling["retrieved_utc"], "2026-07-24T00:00:00Z")
        self.assertEqual(
            rolling["snapshot_identity"],
            {
                "kind": "sha256",
                "value": rolling_digest,
                "content_sha256": rolling_digest,
            },
        )
        with self.assertRaisesRegex(
            builder.PackBuildError,
            "catalog-provided rolling snapshot identity",
        ):
            builder._output_version_scope(
                {
                    "kind": "latest-at-retrieval",
                    "value": None,
                    "retrieved_utc": "2026-07-24T00:00:00Z",
                    "snapshot_identity": {
                        "kind": "manifest",
                        "value": "input-only-manifest-label",
                        "content_sha256": "b" * 64,
                    },
                },
                rolling_snapshot_sha256=rolling_digest,
            )
        with self.assertRaisesRegex(
            builder.PackBuildError,
            "independent rolling snapshot identity",
        ):
            builder._output_version_scope(
                {
                    "kind": "latest-at-retrieval",
                    "value": None,
                    "retrieved_utc": "2026-07-24T00:00:00Z",
                    "snapshot_identity": None,
                }
            )
        unversioned = builder._output_version_scope(
            {
                "kind": "unversioned",
                "value": "descriptive input-only label",
                "retrieved_utc": "2026-07-24T00:00:00Z",
                "snapshot_identity": None,
            },
        )
        self.assertEqual(
            unversioned,
            {
                "kind": "unversioned",
                "value": None,
                "retrieved_utc": None,
                "snapshot_identity": None,
            },
        )
        for kind in ("revision", "release-line"):
            with self.subTest(kind=kind):
                projected = builder._output_version_scope(
                    {
                        "kind": kind,
                        "value": "immutable-label",
                        "retrieved_utc": "2026-07-24T00:00:00Z",
                        "snapshot_identity": {
                            "kind": "revision",
                            "value": "abc",
                            "content_sha256": "b" * 64,
                        },
                    },
                )
                self.assertEqual(
                    projected,
                    {
                        "kind": kind,
                        "value": "immutable-label",
                        "retrieved_utc": None,
                        "snapshot_identity": None,
                    },
                )

    def test_rolling_source_identity_aggregate_is_stable_and_sensitive(
        self,
    ) -> None:
        included = [
            {
                "source_id": "source-b",
                "locator": "https://example.invalid/b",
                "identity": {
                    "kind": "revision",
                    "value": "revision-b",
                    "raw_sha256": "b" * 64,
                    "raw_bytes": 20,
                    "resolver_receipt": None,
                },
            },
            {
                "source_id": "source-a",
                "locator": "https://example.invalid/a",
                "identity": {
                    "kind": "external-receipt",
                    "value": "receipt-a",
                    "raw_sha256": "a" * 64,
                    "raw_bytes": 10,
                    "resolver_receipt": None,
                },
            },
        ]
        exclusions = [
            {
                "source_id": "excluded-b",
                "reason_code": "out-of-scope",
            },
            {
                "source_id": "excluded-a",
                "reason_code": "obsolete",
            },
        ]
        kwargs = {
            "authority_id": "authority-one",
            "provider_id": "provider-one",
            "retrieved_utc": "2026-07-24T00:00:00Z",
        }
        expected = builder._source_identity_aggregate_sha256(
            included_sources=included,
            reviewed_exclusions=exclusions,
            **kwargs,
        )
        self.assertEqual(
            expected,
            builder._source_identity_aggregate_sha256(
                included_sources=list(reversed(included)),
                reviewed_exclusions=list(reversed(exclusions)),
                **kwargs,
            ),
        )
        changed = copy.deepcopy(included)
        changed[0]["identity"]["raw_sha256"] = "c" * 64
        self.assertNotEqual(
            expected,
            builder._source_identity_aggregate_sha256(
                included_sources=changed,
                reviewed_exclusions=exclusions,
                **kwargs,
            ),
        )

    def test_builder_rejects_unregistered_version_aliases(self) -> None:
        exact_registration = [
            {
                "scope": "exact",
                "exact_version": "16-C.01-public-reference",
                "minimum_version": None,
                "maximum_version": None,
                "release_series": None,
            }
        ]
        builder._require_registered_version_scope(
            skill_id="synthetic-skill",
            input_id="matching-revision",
            version_scope={
                "kind": "revision",
                "value": "16-C.01-public-reference",
                "retrieved_utc": None,
                "snapshot_identity": None,
            },
            registered_scopes=exact_registration,
        )
        with self.assertRaisesRegex(
            builder.PackBuildError,
            "aliases and version normalization are not inferred",
        ):
            builder._require_registered_version_scope(
                skill_id="synthetic-skill",
                input_id="descriptive-revision",
                version_scope={
                    "kind": "revision",
                    "value": (
                        "Gaussian 16 Rev. C.01 public reference"
                    ),
                    "retrieved_utc": None,
                    "snapshot_identity": None,
                },
                registered_scopes=exact_registration,
            )

    def test_safe_id_preserves_the_full_contract_domain(self) -> None:
        legal = "a" * 128
        self.assertEqual(builder._safe_id(legal), legal)
        projected = builder._safe_id("b" * 129)
        self.assertEqual(len(projected), 128)
        self.assertRegex(projected, r"^[a-z0-9][a-z0-9._-]{0,127}$")

    def test_blocking_catalog_loss_becomes_provider_blocker(self) -> None:
        losses = [
            {
                "loss_id": "missing-native-reference",
                "description": "The licensed native reference is unavailable.",
                "disposition": "blocked",
            },
            {
                "loss_id": "normalized-navigation",
                "description": "Navigation chrome was normalized.",
                "disposition": "accepted",
            },
        ]
        self.assertEqual(
            builder._blocking_loss_blockers(losses),
            [
                {
                    "code": "loss-missing-native-reference",
                    "description": (
                        "The provider document projection has an unresolved "
                        "blocking "
                        "official-document loss: missing-native-reference."
                    ),
                    "dimensions": ["slices"],
                }
            ],
        )

    def test_registration_state_blockers_are_rejected_at_seed_and_catalog(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            builder.PackBuildError,
            "central registration state",
        ):
            builder._reject_registration_state_blockers(
                seed_blockers=[
                    "The authority and consumer binding are absent centrally."
                ],
                catalog_blockers=[],
                label="synthetic seed",
            )
        with self.assertRaisesRegex(
            builder.PackBuildError,
            "central registration state",
        ):
            builder._reject_registration_state_blockers(
                seed_blockers=[],
                catalog_blockers=[
                    {
                        "code": "JSONSCHEMA.AUTHORITY.UNREGISTERED",
                        "description": "Synthetic stale registration state.",
                    }
                ],
                label="synthetic catalog",
            )
        for stale in (
            "The central authority proposal has not been reviewed.",
            "The central consumer-binding proposal has not been activated.",
            (
                "The central authority and consumer-binding proposal has not "
                "been reviewed or activated."
            ),
        ):
            with (
                self.subTest(stale=stale),
                self.assertRaisesRegex(
                    builder.PackBuildError,
                    "central registration state",
                ),
            ):
                builder._reject_registration_state_blockers(
                    seed_blockers=[stale],
                    catalog_blockers=[],
                    label="synthetic stale registration state",
                )
        builder._reject_registration_state_blockers(
            seed_blockers=[
                "Central processor attestation remains unresolved."
            ],
            catalog_blockers=[
                {
                    "code": "SLURM.SITE.UNVALIDATED",
                    "description": "No installed site policy was validated.",
                }
            ],
            label="genuine evidence blockers",
        )

    def test_blocking_loss_projection_and_provider_ceiling_remain_aligned(
        self,
    ) -> None:
        for materiality in ("none", "non-material", "material", "unknown"):
            for disposition in (
                "accepted",
                "preserved",
                "external-only",
                "blocked",
            ):
                loss = {
                    "loss_id": f"{materiality}-{disposition}",
                    "description": "Synthetic loss.",
                    "materiality": materiality,
                    "disposition": disposition,
                }
                projected = builder._output_loss(loss, ["slice-one"])
                blocks_slice_assurance = (
                    projected["severity"] == "blocking"
                    and projected["disposition"] in {"omitted", "unresolved"}
                )
                self.assertEqual(
                    bool(builder._blocking_loss_blockers([loss])),
                    blocks_slice_assurance,
                )

    def test_gaussian_blocking_loss_does_not_pollute_license_dimension(
        self,
    ) -> None:
        snapshot = builder.load_registry_snapshot(
            ROOT,
            validate_sources=True,
        )
        context = builder.load_seed(
            ROOT,
            snapshot,
            "gaussian-rigorous-calculations",
        )
        outputs = builder._build_one(context)
        c01 = json.loads(
            outputs["slices-gaussian-g16-c01-public.json"]
        )
        self.assertEqual(c01["status"], "partial")
        corpus = json.loads(
            outputs["corpus-gaussian-g16-c02-delta.json"]
        )
        self.assertEqual(corpus["status"], "partial")
        self.assertNotIn(
            "loss-g16-c02-no-complete-reference",
            {item["code"] for item in corpus["blockers"]},
        )
        slices = json.loads(
            outputs["slices-gaussian-g16-c02-delta.json"]
        )
        self.assertEqual(slices["status"], "blocked")
        self.assertIn(
            "loss-g16-c02-no-complete-reference",
            {item["code"] for item in slices["blockers"]},
        )
        license_review = json.loads(
            outputs["license-review-gaussian-g16-c02-delta.json"]
        )
        self.assertEqual(license_review["status"], "partial")
        self.assertEqual(license_review["blockers"], [])
        self.assertNotIn(
            "loss-g16-c02-no-complete-reference",
            {item["code"] for item in license_review["blockers"]},
        )
        builder._semantic_validate_outputs(context, outputs)

    def test_runtime_and_body_blockers_are_dimension_scoped(self) -> None:
        snapshot = builder.load_registry_snapshot(
            ROOT,
            validate_sources=True,
        )
        context = builder.load_seed(
            ROOT,
            snapshot,
            "gpumd-rigorous-simulations",
        )
        outputs = builder._build_one(context)
        corpus = json.loads(outputs["corpus-gpumd-docs.json"])
        slices = json.loads(outputs["slices-gpumd-docs.json"])
        license_review = json.loads(
            outputs["license-review-gpumd-docs.json"]
        )
        corpus_codes = {item["code"] for item in corpus["blockers"]}
        slice_codes = {item["code"] for item in slices["blockers"]}
        license_codes = {item["code"] for item in license_review["blockers"]}
        self.assertIn("doc.body.bytes.external", corpus_codes)
        self.assertIn("doc.body.bytes.external", slice_codes)
        self.assertIn("doc.build.replay.missing", slice_codes)
        for code in (
            "runtime.gpu.native.unverified",
            "model.data.license.identity.missing",
        ):
            self.assertNotIn(code, corpus_codes)
            self.assertNotIn(code, slice_codes)
            self.assertNotIn(code, license_codes)
        self.assertEqual(license_review["status"], "partial")
        self.assertEqual(license_review["blockers"], [])
        serialized_license = json.dumps(license_review, sort_keys=True)
        catalog_path = ROOT / context.seed["providers"][0]["source_ref"]["path"]
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        for blocker in catalog["blockers"]:
            self.assertNotIn(blocker["description"], serialized_license)
        builder._semantic_validate_outputs(context, outputs)

    def test_vasp_real_pack_remains_partial_and_closes_bounded_scope(
        self,
    ) -> None:
        snapshot = builder.load_registry_snapshot(
            ROOT,
            validate_sources=True,
        )
        context = builder.load_seed(
            ROOT,
            snapshot,
            "vasp-rigorous-calculations",
        )
        outputs = builder._build_one(context)
        corpus = json.loads(
            outputs["corpus-vasp-wiki-pages.json"]
        )
        slices = json.loads(
            outputs["slices-vasp-wiki-pages.json"]
        )
        license_review = json.loads(
            outputs["license-review-vasp-wiki-pages.json"]
        )
        coverage = json.loads(outputs["coverage.json"])
        self.assertEqual(corpus["status"], "partial")
        self.assertEqual(slices["status"], "partial")
        self.assertEqual(license_review["status"], "partial")
        self.assertEqual(coverage["status"], "partial")
        self.assertEqual(
            {item["source_id"] for item in corpus["included_sources"]},
            {item["source_id"] for item in slices["sources"]},
        )
        self.assertEqual(len(corpus["included_sources"]), 162)
        self.assertTrue(
            all(
                item["selector"]["kind"] == "whole-source"
                and item["storage_mode"] == "metadata-only"
                for source in slices["sources"]
                for item in source["slices"]
            )
        )
        provider_mappings = [
            item
            for item in coverage["mappings"]
            if item["official_disposition"] == "partial"
        ]
        local_mappings = [
            item
            for item in coverage["mappings"]
            if item["official_disposition"] == "not-applicable"
        ]
        self.assertEqual(len(provider_mappings), 38)
        self.assertEqual(len(local_mappings), 3)
        self.assertTrue(
            all(item["slice_refs"] for item in provider_mappings)
        )
        self.assertTrue(
            all(
                not item["slice_refs"]
                and item["coverage_status"] == "complete"
                for item in local_mappings
            )
        )
        self.assertEqual(
            license_review["trust_attestation"]["trust_mode"],
            "unverified",
        )
        self.assertEqual(
            license_review["evidence"],
            [
                {
                    "evidence_id": "vasp-wiki-pages-license-evidence",
                    "locator": "https://www.vasp.at/wiki/Main_page",
                    "revision": None,
                    "sha256": None,
                    "hash_basis": "unattested-external-locator",
                    "terms_content_ref": None,
                }
            ],
        )
        builder._semantic_validate_outputs(context, outputs)

    def test_rolling_source_scope_binds_each_raw_identity(self) -> None:
        corpus_scope = {
            "kind": "latest-at-retrieval",
            "value": None,
            "retrieved_utc": "2026-07-24T00:00:00Z",
            "snapshot_identity": {
                "kind": "sha256",
                "value": "a" * 64,
                "content_sha256": "a" * 64,
            },
        }
        first = builder._source_version_scope(
            corpus_scope,
            raw_sha256="b" * 64,
        )
        second = builder._source_version_scope(
            corpus_scope,
            raw_sha256="c" * 64,
        )
        self.assertEqual(
            first["snapshot_identity"]["content_sha256"],
            "b" * 64,
        )
        self.assertEqual(
            second["snapshot_identity"]["content_sha256"],
            "c" * 64,
        )
        self.assertEqual(first["retrieved_utc"], corpus_scope["retrieved_utc"])
        self.assertEqual(second["retrieved_utc"], corpus_scope["retrieved_utc"])

    def test_declarative_inventory_uses_exact_canonical_partition(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            provider = {
                "input_id": "manual",
                "source_ref": {
                    "path": "skills/demo-skill/references/catalog.json",
                    "sha256": "a" * 64,
                },
            }
            authority = {
                "canonical_snapshot": {
                    "manifest_path": (
                        "skills/demo-skill/references/official-manual/"
                        "manifest.json"
                    )
                }
            }
            projection = {
                "canonical_snapshot": {
                    "index_raw_sha256": "b" * 64,
                    "manifest_raw_sha256": "c" * 64,
                    "upstream_sources_by_id": {
                        "source-one": {},
                        "source-two": {},
                    },
                    "sources_by_id": {"source-one": {}},
                }
            }
            self.assertEqual(
                builder._declarative_inventory_projection(
                    context,
                    provider,
                    authority_entry=authority,
                    authority_projection=projection,
                    mapped_discovered_ids={"source-one", "source-two"},
                    upstream_universe_complete=True,
                ),
                (
                    "cp2k-official-index-v1",
                    (
                        "skills/demo-skill/references/official-manual/"
                        "index.json"
                    ),
                    "b" * 64,
                    True,
                ),
            )

            self.assertEqual(
                builder._declarative_inventory_projection(
                    context,
                    provider,
                    authority_entry={},
                    authority_projection={},
                    mapped_discovered_ids={"source-one"},
                    upstream_universe_complete=True,
                ),
                (
                    "declarative-source-catalog-v1",
                    "skills/demo-skill/references/catalog.json",
                    "a" * 64,
                    False,
                ),
            )
            self.assertEqual(
                builder._declarative_inventory_projection(
                    context,
                    provider,
                    authority_entry=authority,
                    authority_projection=projection,
                    mapped_discovered_ids={"source-one"},
                    upstream_universe_complete=False,
                ),
                (
                    "cp2k-canonical-manifest-v1",
                    (
                        "skills/demo-skill/references/official-manual/"
                        "manifest.json"
                    ),
                    "c" * 64,
                    False,
                ),
            )
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "does not exactly equal the canonical index",
            ):
                builder._declarative_inventory_projection(
                    context,
                    provider,
                    authority_entry=authority,
                    authority_projection=projection,
                    mapped_discovered_ids={"source-one"},
                    upstream_universe_complete=True,
                )

    def test_declarative_adapter_rejects_any_content_ref(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            provider_input = {
                "input_id": "provider-one",
                "source_ref": {"path": "unused", "sha256": "0" * 64},
            }
            catalog = {
                "blockers": [],
                "sources": [
                    {
                        "source_id": "source-one",
                        "content_ref": {
                            "path": "skills/demo-skill/references/body.txt",
                            "sha256": "0" * 64,
                            "bytes": 1,
                        },
                        "slices": [],
                    }
                ]
            }
            authority = {
                "redistribution_policy": {"bundle_content": "forbidden"}
            }
            with (
                mock.patch.object(
                    builder,
                    "_authority",
                    return_value=(authority, {}),
                ),
                mock.patch.object(
                    builder,
                    "_load_schema_bound_ref",
                    return_value=catalog,
                ),
                self.assertRaisesRegex(
                    builder.PackBuildError,
                    "only external identity and metadata receipts",
                ),
            ):
                builder._declarative_adapter(context, provider_input)

        skill_root = ROOT / "skills" / "catmap-microkinetics"
        seed_path = skill_root / "references" / "source-pack-seed.json"
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        provider_input = seed["providers"][0]
        catalog_path = ROOT / provider_input["source_ref"]["path"]
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        snapshot = SimpleNamespace(
            registry_sha256={
                builder.CONSUMER_REGISTRY_NAME: "c" * 64,
            }
        )
        context = builder.BuildContext(
            root=ROOT,
            snapshot=snapshot,
            skill_id=seed["skill_id"],
            skill_root=skill_root,
            seed_path=seed_path,
            seed=seed,
        )
        authority = {
            "redistribution_policy": {"bundle_content": "forbidden"}
        }
        projection = {
            "canonical_urls": [
                "https://github.com/SUNCAT-Center/catmap/"
            ]
        }
        scope = {
            "subjects": [
                {
                    "subject_id": item["subject_id"],
                    "evidence_class": "official-provider-required",
                    "expected_disposition": "partial",
                    "provider_input_ids": [provider_input["input_id"]],
                }
                for item in catalog["subjects"]
            ]
        }
        with (
            mock.patch.object(
                builder,
                "_authority",
                return_value=(authority, projection),
            ),
            mock.patch.object(
                builder,
                "_scope_catalog",
                return_value=scope,
            ),
            mock.patch.object(
                builder,
                "_processor",
                return_value={},
            ),
        ):
            result = builder._declarative_adapter(context, provider_input)
        source = catalog["sources"][0]
        identity = result.included_sources[0]["identity"]
        receipt = result.source_slices[0]["slices"][0]["content_receipt"]
        self.assertEqual(
            source["external_identity"]["raw_sha256"],
            identity["raw_sha256"],
        )
        self.assertEqual(
            source["metadata_evidence_ref"]["sha256"],
            receipt["evidence_sha256"],
        )
        self.assertNotEqual(
            source["metadata_evidence_ref"]["sha256"],
            identity["raw_sha256"],
        )

        broken = copy.deepcopy(catalog)
        broken["sources"][0]["external_identity"]["evidence_sha256"] = (
            "0" * 64
        )
        with (
            mock.patch.object(
                builder,
                "_authority",
                return_value=(authority, projection),
            ),
            mock.patch.object(
                builder,
                "_load_schema_bound_ref",
                return_value=broken,
            ),
            self.assertRaisesRegex(
                builder.PackBuildError,
                "metadata sidecar must exactly bind",
            ),
        ):
            builder._declarative_adapter(context, provider_input)

    def test_declarative_adapter_rejects_duplicate_subject_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            provider_input = {
                "input_id": "provider-one",
                "source_ref": {"path": "unused", "sha256": "0" * 64},
            }
            catalog = {
                "blockers": [],
                "sources": [],
                "reviewed_exclusions": [],
                "losses": [],
                "subjects": [
                    {"subject_id": "subject-one", "title": "First"},
                    {"subject_id": "subject-one", "title": "Changed title"},
                ],
            }
            authority = {
                "redistribution_policy": {"bundle_content": "forbidden"}
            }
            scope = {
                "subjects": [
                    {
                        "subject_id": "subject-one",
                        "evidence_class": "official-provider-required",
                        "provider_input_ids": ["provider-one"],
                    }
                ]
            }
            with (
                mock.patch.object(
                    builder,
                    "_authority",
                    return_value=(authority, {}),
                ),
                mock.patch.object(
                    builder,
                    "_load_schema_bound_ref",
                    return_value=catalog,
                ),
                mock.patch.object(
                    builder,
                    "_scope_catalog",
                    return_value=scope,
                ),
                self.assertRaisesRegex(
                    builder.PackBuildError,
                    "duplicate catalog subject_id",
                ),
            ):
                builder._declarative_adapter(context, provider_input)

    def test_provider_projection_rejects_dangling_loss(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            provider = self.provider()
            broken_source = copy.deepcopy(provider.source_slices[0])
            broken_source["slices"][0]["loss_ids"] = ["missing-loss"]
            broken = builder.ProviderBuild(
                **{
                    **provider.__dict__,
                    "source_slices": (broken_source,),
                }
            )
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "dangling slice loss ID",
            ):
                builder._validate_provider_projection(context, broken)

    def test_provider_projection_allows_an_explicit_empty_subject_gap(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            provider = self.provider()
            gap = builder.ProviderBuild(
                **{
                    **provider.__dict__,
                    "subject_slice_ids": {"blocked-subject": ()},
                }
            )
            builder._validate_provider_projection(context, gap)

    def test_license_projection_preserves_legal_unverified_locator(self) -> None:
        central = {
            "status": "known-open",
            "identifier": "Example-1.0",
            "terms_urls": ["https://example.invalid/central-license"],
            "verification_status": "verified",
        }
        authority = {
            "license_policy": central,
            "redistribution_policy": {
                "bundle_content": "forbidden",
                "external_runtime_content": "platform-verification-required",
            },
            "provenance": {
                "official_fact_urls": ["https://example.invalid/facts"]
            },
        }
        snapshot = SimpleNamespace(
            official_source_authorities={
                "authorities": {"authority-one": authority}
            }
        )
        catalog_license = {
            "identity": {
                "identifier": "Unverified-Claim-1.0",
                "terms_urls": [
                    "https://example.invalid/unverified-claimed-license"
                ],
                "verification": "unverified",
            },
            "assessment": "unresolved",
            "allowed_storage_modes": ["metadata-only", "excluded"],
            "official_terms_locator": "https://example.invalid/unverified-terms",
            "limitations": ["The catalog review remains unverified."],
        }
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory), snapshot=snapshot)
            projection = builder._license_projection(
                context,
                self.provider(license_record=catalog_license),
            )
        self.assertEqual(
            projection["identity"],
            {
                "identifier": None,
                "terms_urls": [],
                "verification": "unknown",
            },
        )
        self.assertEqual(
            projection["evidence_locator"],
            "https://example.invalid/unverified-terms",
        )
        self.assertEqual(projection["assessment"], "unresolved")
        self.assertTrue(
            any(
                "downgraded to null/empty" in item
                for item in projection["limitations"]
            )
        )

    def test_license_projection_cannot_upgrade_or_force_metadata_mode(self) -> None:
        authority = {
            "license_policy": {
                "status": "unknown",
                "identifier": None,
                "terms_urls": [],
                "verification_status": "unresolved",
            },
            "redistribution_policy": {
                "bundle_content": "forbidden",
                "external_runtime_content": "unavailable",
            },
            "provenance": {
                "official_fact_urls": ["https://example.invalid/facts"]
            },
        }
        snapshot = SimpleNamespace(
            official_source_authorities={
                "authorities": {"authority-one": authority}
            }
        )
        base = {
            "identity": {
                "identifier": None,
                "terms_urls": [],
                "verification": "unknown",
            },
            "assessment": "unresolved",
            "allowed_storage_modes": ["metadata-only", "excluded"],
            "official_terms_locator": "https://example.invalid/terms",
            "limitations": ["Unknown license."],
        }
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory), snapshot=snapshot)
            upgraded = copy.deepcopy(base)
            upgraded["identity"] = {
                "identifier": "Claimed-1.0",
                "terms_urls": ["https://example.invalid/terms"],
                "verification": "verified",
            }
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "cannot upgrade",
            ):
                builder._license_projection(
                    context,
                    self.provider(license_record=upgraded),
                )
            no_metadata = copy.deepcopy(base)
            no_metadata["allowed_storage_modes"] = ["excluded"]
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "does not permit.*metadata-only",
            ):
                builder._license_projection(
                    context,
                    self.provider(license_record=no_metadata),
                )

    def test_dependency_lock_rejects_duplicate_reference_paths(self) -> None:
        lock = json.loads(
            (
                ROOT
                / "contracts"
                / "official-document-pack-builder-lock.json"
            ).read_text(encoding="utf-8")
        )
        references = [
            lock["dependency_manifest_ref"],
            *lock["configuration_contract_refs"],
            *lock["runtime_refs"],
            *lock["output_contract_refs"],
            *[
                item["input_contract_ref"]
                for item in lock["adapters"].values()
            ],
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for reference in references:
                source = ROOT / reference["path"]
                target = root / reference["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    shutil.copy2(source, target)
            builder_source = (
                ROOT / "tools" / "build_official_document_packs.py"
            )
            builder_target = (
                root / "tools" / "build_official_document_packs.py"
            )
            if not builder_target.exists():
                shutil.copy2(builder_source, builder_target)
            lock["configuration_contract_refs"].append(
                copy.deepcopy(lock["configuration_contract_refs"][0])
            )
            lock_path = (
                root
                / "contracts"
                / "official-document-pack-builder-lock.json"
            )
            lock_path.write_text(
                json.dumps(lock, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            context = self.context(root)
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "duplicate dependency path",
            ):
                builder._validate_dependency_lock(context)

    def test_live_dependency_lock_is_exact_and_runtime_checked(self) -> None:
        context = builder.BuildContext(
            root=ROOT,
            snapshot=SimpleNamespace(),
            skill_id="qe-rigorous-calculations",
            skill_root=ROOT / "skills" / "qe-rigorous-calculations",
            seed_path=(
                ROOT
                / "skills"
                / "qe-rigorous-calculations"
                / "references"
                / "source-pack-seed.json"
            ),
            seed={},
        )
        builder._validate_dependency_lock(context)

    def test_output_closure_is_fixed_and_rejects_unsafe_extra_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            seed = {
                "providers": [{"input_id": "provider-one"}],
                "limitations": ["synthetic"],
                "blockers": [],
                "status_ceiling": "partial",
            }
            context = self.context(Path(directory), seed=seed)
            outputs = {
                name: b"{}\n"
                for name in builder._expected_output_names(context)
            }
            builder._validate_output_closure(context, outputs)
            outputs["../escape.json"] = b"{}\n"
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "output set differs",
            ):
                builder._validate_output_closure(context, outputs)

    def test_pack_inventory_rejects_symlink_hardlink_and_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for kind in ("symlink", "hardlink", "directory"):
                pack = root / kind
                pack.mkdir()
                original = pack / "original.json"
                original.write_bytes(b"{}\n")
                if kind == "symlink":
                    (pack / "alias.json").symlink_to(original)
                elif kind == "hardlink":
                    os.link(original, pack / "alias.json")
                else:
                    (pack / "nested").mkdir()
                with self.subTest(kind=kind), self.assertRaises(
                    builder.PackBuildError
                ):
                    builder._pack_inventory(pack, label=kind)

    def test_atomic_replace_rolls_back_original_pack_on_install_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self.context(root)
            pack = (
                context.skill_root
                / "references"
                / "official-source-pack"
            )
            pack.mkdir()
            (pack / "old.json").write_bytes(b'{"old":true}\n')
            real_replace = os.replace
            replace_count = 0

            def fail_install(source: object, target: object) -> None:
                nonlocal replace_count
                replace_count += 1
                if replace_count == 2:
                    raise OSError("synthetic install failure")
                real_replace(source, target)

            with (
                mock.patch.object(
                    builder.os,
                    "replace",
                    side_effect=fail_install,
                ),
                self.assertRaisesRegex(
                    builder.PackBuildError,
                    "synthetic install failure",
                ),
            ):
                builder._atomic_replace_pack(
                    context,
                    {"bundle.json": b"{}\n"},
                )
            self.assertEqual(
                builder._pack_inventory(pack, label="restored"),
                {"old.json": b'{"old":true}\n'},
            )
            self.assertFalse(
                any(
                    item.name.startswith(".source-pack-")
                    for item in pack.parent.iterdir()
                )
            )

    def test_atomic_replace_rolls_back_when_parent_fsync_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self.context(root)
            references = context.skill_root / "references"
            pack = references / "official-source-pack"
            pack.mkdir()
            old = {"old.json": b'{"old":true}\n'}
            (pack / "old.json").write_bytes(old["old.json"])
            real_fsync = os.fsync
            calls = 0

            def fail_parent_fsync(descriptor: int) -> None:
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("synthetic parent fsync failure")
                real_fsync(descriptor)

            with (
                mock.patch.object(
                    builder.os,
                    "fsync",
                    side_effect=fail_parent_fsync,
                ),
                self.assertRaisesRegex(
                    builder.PackBuildError,
                    "synthetic parent fsync failure",
                ),
            ):
                builder._atomic_replace_pack(
                    context,
                    {"bundle.json": b"{}\n"},
                )
            self.assertEqual(
                builder._pack_inventory(pack, label="restored-after-fsync"),
                old,
            )
            self.assertFalse(
                any(
                    item.name.startswith(".source-pack-")
                    for item in references.iterdir()
                )
            )

    def test_two_pack_transaction_rolls_back_every_prior_swap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self.context(root, skill_id="first-skill")
            second = self.context(root, skill_id="second-skill")
            old = {
                first.skill_id: b'{"old":"first"}\n',
                second.skill_id: b'{"old":"second"}\n',
            }
            for context in (first, second):
                pack = (
                    context.skill_root
                    / "references"
                    / "official-source-pack"
                )
                pack.mkdir()
                (pack / "old.json").write_bytes(old[context.skill_id])
            real_replace = os.replace

            def fail_second_install(source: object, target: object) -> None:
                source_path = Path(source)
                target_path = Path(target)
                if (
                    source_path.name.startswith(".source-pack-stage-")
                    and target_path
                    == second.skill_root
                    / "references"
                    / "official-source-pack"
                ):
                    raise OSError("synthetic second-pack install failure")
                real_replace(source, target)

            with (
                mock.patch.object(
                    builder.os,
                    "replace",
                    side_effect=fail_second_install,
                ),
                self.assertRaisesRegex(
                    builder.PackBuildError,
                    "synthetic second-pack install failure",
                ),
            ):
                builder._atomic_replace_packs(
                    (
                        (first, {"bundle.json": b'{"new":"first"}\n'}),
                        (second, {"bundle.json": b'{"new":"second"}\n'}),
                    )
                )
            for context in (first, second):
                references = context.skill_root / "references"
                pack = references / "official-source-pack"
                self.assertEqual(
                    builder._pack_inventory(
                        pack,
                        label=f"{context.skill_id}:restored",
                    ),
                    {"old.json": old[context.skill_id]},
                )
                self.assertFalse(
                    any(
                        item.name.startswith(".source-pack-")
                        for item in references.iterdir()
                    )
                )

    def test_post_fsync_tamper_restores_old_and_quarantines_conflict(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self.context(root)
            references = context.skill_root / "references"
            pack = references / "official-source-pack"
            pack.mkdir()
            old = b'{"old":true}\n'
            (pack / "old.json").write_bytes(old)
            real_fsync_directory = builder._fsync_directory
            tampered = False

            def fsync_then_tamper(path: Path) -> None:
                nonlocal tampered
                real_fsync_directory(path)
                if not tampered and pack.is_dir():
                    tampered = True
                    (pack / "bundle.json").write_bytes(
                        b'{"evil":true}\n'
                    )

            with (
                mock.patch.object(
                    builder,
                    "_fsync_directory",
                    side_effect=fsync_then_tamper,
                ),
                self.assertRaisesRegex(
                    builder.PackBuildError,
                    "changed before the command-wide commit point",
                ),
            ):
                builder._atomic_replace_pack(
                    context,
                    {"bundle.json": b"{}\n"},
                )
            self.assertEqual(
                builder._pack_inventory(pack, label="restored-after-tamper"),
                {"old.json": old},
            )
            conflict_paths = [
                item
                for item in references.iterdir()
                if item.name.startswith(".source-pack-conflict-")
            ]
            self.assertEqual(len(conflict_paths), 1)
            self.assertEqual(
                builder._pack_inventory(
                    conflict_paths[0],
                    label="quarantined-conflict",
                ),
                {"bundle.json": b'{"evil":true}\n'},
            )
            self.assertFalse(
                any(
                    item.name.startswith(
                        (
                            ".source-pack-stage-",
                            ".source-pack-backup-",
                            ".source-pack-rollback-",
                        )
                    )
                    for item in references.iterdir()
                )
            )

    def test_all_selected_builds_finish_before_any_pack_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contexts = {
                skill_id: self.context(root, skill_id=skill_id)
                for skill_id in ("first-skill", "second-skill")
            }

            def load(_root: Path, _snapshot: object, skill_id: str):
                return contexts[skill_id]

            with (
                mock.patch.object(builder, "load_seed", side_effect=load),
                mock.patch.object(
                    builder,
                    "_build_one",
                    side_effect=[{}, builder.PackBuildError("second failed")],
                ),
                mock.patch.object(builder, "_validate_output_closure"),
                mock.patch.object(builder, "_semantic_validate_outputs"),
                mock.patch.object(builder, "_pack_inventory", return_value=None),
                mock.patch.object(builder, "_changed_paths", return_value=["x"]),
                mock.patch.object(builder, "_atomic_replace_pack") as replace,
                self.assertRaisesRegex(builder.PackBuildError, "second failed"),
            ):
                builder._build_selected_with_snapshot(
                    root,
                    SimpleNamespace(),
                    ("first-skill", "second-skill"),
                    check=False,
                )
            replace.assert_not_called()

    def test_check_mode_reports_stale_closure_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self.context(root)
            with (
                mock.patch.object(builder, "load_seed", return_value=context),
                mock.patch.object(builder, "_build_one", return_value={}),
                mock.patch.object(builder, "_validate_output_closure"),
                mock.patch.object(builder, "_semantic_validate_outputs"),
                mock.patch.object(builder, "_pack_inventory", return_value={}),
                mock.patch.object(
                    builder,
                    "_changed_paths",
                    return_value=["stale-extra.json"],
                ),
                mock.patch.object(builder, "_atomic_replace_pack") as replace,
                self.assertRaisesRegex(
                    builder.PackBuildError,
                    "stale or have noncanonical closure",
                ),
            ):
                builder._build_selected_with_snapshot(
                    root,
                    SimpleNamespace(),
                    ("demo-skill",),
                    check=True,
                )
            replace.assert_not_called()

    def test_check_mode_rechecks_pack_after_change_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self.context(root)
            expected = {"bundle.json": b"{}\n"}
            mutated = {"bundle.json": b'{"mutated":true}\n'}
            with (
                mock.patch.object(builder, "load_seed", return_value=context),
                mock.patch.object(
                    builder,
                    "_build_one",
                    return_value=expected,
                ),
                mock.patch.object(builder, "_validate_output_closure"),
                mock.patch.object(builder, "_semantic_validate_outputs"),
                mock.patch.object(
                    builder,
                    "_pack_inventory",
                    side_effect=[expected, mutated],
                ),
                mock.patch.object(
                    builder,
                    "_changed_paths",
                    return_value=[],
                ),
                mock.patch.object(builder, "_atomic_replace_packs") as replace,
                self.assertRaisesRegex(
                    builder.PackBuildError,
                    "changed during the final",
                ),
            ):
                builder._build_selected_with_snapshot(
                    root,
                    SimpleNamespace(),
                    ("demo-skill",),
                    check=True,
                )
            replace.assert_not_called()


if __name__ == "__main__":
    unittest.main()
