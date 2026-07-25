from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock


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
    ) -> builder.BuildContext:
        skill_root = root / "skills" / skill_id
        (skill_root / "references").mkdir(parents=True, exist_ok=True)
        return builder.BuildContext(
            root=root,
            snapshot=SimpleNamespace(
                registry_sha256={
                    builder.CONSUMER_REGISTRY_NAME: "c" * 64,
                }
            ),
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

    def real_context(self, skill_id: str) -> builder.BuildContext:
        skill_root = ROOT / "skills" / skill_id
        seed_path = skill_root / "references" / "source-pack-seed.json"
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        return builder.BuildContext(
            root=ROOT,
            snapshot=SimpleNamespace(
                registry_sha256={
                    builder.CONSUMER_REGISTRY_NAME: "c" * 64,
                }
            ),
            skill_id=skill_id,
            skill_root=skill_root,
            seed_path=seed_path,
            seed=seed,
        )

    @staticmethod
    def authority_for(
        provider: dict[str, object],
        version_scope: dict[str, object],
    ) -> tuple[dict[str, object], dict[str, object]]:
        return (
            {
                "provider_id": provider["provider_id"],
                "lifecycle": "active",
            },
            {"version_scopes": [version_scope]},
        )

    @staticmethod
    def external_identity() -> dict[str, object]:
        return {
            "content_mode": "external-content",
            "locator": "https://example.invalid/manual.txt",
            "receipt": {
                "retrieval_method": "https-get",
                "retrieved_utc": "2026-07-24T00:00:00Z",
                "raw_sha256": "a" * 64,
                "raw_bytes": 100,
            },
        }

    @staticmethod
    def selector(
        *,
        layer: str = "raw-source",
        kind: str = "whole-source",
        value: str = "*",
        selected_sha256: str = "a" * 64,
        selected_bytes: int = 100,
    ) -> dict[str, object]:
        return {
            "selector_id": "selector-one",
            "layer": layer,
            "kind": kind,
            "value": value,
            "subject_ids": ["subject-one"],
            "loss_ids": [],
            "selected_identity": {
                "sha256": selected_sha256,
                "bytes": selected_bytes,
            },
        }

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

    def test_external_whole_source_requires_exact_selected_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            identity = self.external_identity()
            emitted = builder._slice_from_catalog(
                context=context,
                provider={"input_id": "provider-one"},
                source={"source_id": "source-one"},
                identity=identity,
                selector=self.selector(),
                raw_source_extent_bytes=100,
            )
            self.assertEqual(
                emitted["content"]["receipt"]["selected_content"],
                {"sha256": "a" * 64, "bytes": 100},
            )

            mismatch = self.selector(selected_sha256="b" * 64)
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "must match source receipt identity",
            ):
                builder._slice_from_catalog(
                    context=context,
                    provider={"input_id": "provider-one"},
                    source={"source_id": "source-one"},
                    identity=identity,
                    selector=mismatch,
                    raw_source_extent_bytes=100,
                )

    def test_derived_selector_preserves_independent_selected_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            emitted = builder._slice_from_catalog(
                context=context,
                provider={"input_id": "provider-one"},
                source={"source_id": "source-one"},
                identity=self.external_identity(),
                selector=self.selector(
                    layer="derived-artifact",
                    kind="source-symbol",
                    value="CONTROL",
                    selected_sha256="b" * 64,
                    selected_bytes=17,
                ),
                raw_source_extent_bytes=100,
            )
        self.assertEqual(
            emitted["content"]["identity"],
            {"sha256": "b" * 64, "bytes": 17},
        )
        self.assertEqual(
            emitted["raw_byte_range"],
            {"start_byte": 0, "byte_count": 100},
        )

    def test_selected_identity_is_required_and_strictly_typed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            cases = []
            missing = self.selector()
            missing.pop("selected_identity")
            cases.append(missing)
            boolean_extent = self.selector()
            boolean_extent["selected_identity"]["bytes"] = True
            cases.append(boolean_extent)
            extra_field = self.selector()
            extra_field["selected_identity"]["source"] = "invented"
            cases.append(extra_field)
            for selector in cases:
                with self.subTest(selector=selector), self.assertRaisesRegex(
                    builder.PackBuildError,
                    "selected_identity",
                ):
                    builder._slice_from_catalog(
                        context=context,
                        provider={"input_id": "provider-one"},
                        source={"source_id": "source-one"},
                        identity=self.external_identity(),
                        selector=selector,
                        raw_source_extent_bytes=100,
                    )

    def test_raw_byte_range_identity_extent_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory))
            selector = self.selector(
                kind="byte-range",
                value="10:20",
                selected_sha256="b" * 64,
                selected_bytes=19,
            )
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "bytes must equal selector byte-range byte_count",
            ):
                builder._slice_from_catalog(
                    context=context,
                    provider={"input_id": "provider-one"},
                    source={"source_id": "source-one"},
                    identity=self.external_identity(),
                    selector=selector,
                    raw_source_extent_bytes=100,
                )

    def test_qe_adapter_emits_exact_1159_derived_slices(self) -> None:
        context = self.real_context("qe-rigorous-calculations")
        provider = context.seed["providers"][0]
        authority = self.authority_for(
            provider,
            {
                "scope": "exact",
                "exact_version": "7.5",
                "minimum_version": None,
                "maximum_version": None,
                "release_series": None,
            },
        )
        with mock.patch.object(builder, "_authority", return_value=authority):
            result = builder._qe_adapter(context, provider)
        included = [
            item
            for item in result.source_inventory.values()
            if item["disposition"] == "included"
        ]
        slices = [
            item
            for source in result.slice_sources.values()
            for item in source["slices"]
        ]
        self.assertEqual(len(included), 35)
        self.assertEqual(len(result.source_inventory), 36)
        self.assertEqual(len(slices), 1159)
        self.assertEqual(
            {item["selector"]["layer"] for item in slices},
            {"derived-artifact"},
        )
        self.assertTrue(
            all(
                item["content"]["content_mode"] == "metadata-only"
                and item["content"]["identity"]["bytes"] > 0
                and len(item["content"]["identity"]["sha256"]) == 64
                for item in slices
            )
        )
        builder._validate_provider_projection(context, result)

    def test_vasp_adapter_emits_162_exact_source_identities(self) -> None:
        context = self.real_context("vasp-rigorous-calculations")
        provider = context.seed["providers"][0]
        authority = self.authority_for(
            provider,
            {
                "scope": "latest-at-retrieval",
                "exact_version": None,
                "minimum_version": None,
                "maximum_version": None,
                "release_series": None,
            },
        )
        with mock.patch.object(builder, "_authority", return_value=authority):
            result = builder._vasp_adapter(context, provider)
        self.assertEqual(len(result.source_inventory), 162)
        self.assertEqual(len(result.slice_sources), 162)
        self.assertEqual(
            {
                item["source_kind"]
                for item in result.source_inventory.values()
            },
            {"api-record", "reference-page"},
        )
        for source_id, source in result.slice_sources.items():
            inventory_identity = result.source_inventory[source_id][
                "source_identity"
            ]
            self.assertEqual(source["source_identity"], inventory_identity)
            self.assertEqual(len(source["slices"]), 1)
            self.assertEqual(
                source["slices"][0]["content"]["receipt"][
                    "selected_content"
                ],
                {
                    "sha256": inventory_identity["receipt"]["raw_sha256"],
                    "bytes": inventory_identity["receipt"]["raw_bytes"],
                },
            )
        builder._validate_provider_projection(context, result)

    def test_blockers_route_only_to_declared_dimensions(self) -> None:
        blockers = [
            {
                "code": "corpus-only",
                "description": "Corpus gap.",
                "dimensions": ["corpus"],
            },
            {
                "code": "slices-only",
                "description": "Slice gap.",
                "dimensions": ["slices"],
            },
            {
                "code": "both",
                "description": "Shared gap.",
                "dimensions": ["corpus", "slices"],
            },
            {
                "code": "runtime-only",
                "description": "Runtime gap.",
                "dimensions": ["runtime"],
            },
        ]
        corpus = builder._output_blockers(
            blockers,
            label="corpus",
            dimension="corpus",
        )
        slices = builder._output_blockers(
            blockers,
            label="slices",
            dimension="slices",
        )
        self.assertEqual(
            {item["code"] for item in corpus},
            {"corpus-only", "both"},
        )
        self.assertEqual(
            {item["code"] for item in slices},
            {"slices-only", "both"},
        )
        self.assertTrue(
            all(item["dimensions"] == ["slices"] for item in builder._blocking_loss_blockers([
                {
                    "loss_id": "missing-slice",
                    "disposition": "blocked",
                }
            ]))
        )

    def valid_outputs(
        self,
        context: builder.BuildContext,
    ) -> dict[str, bytes]:
        provider_ids = sorted(
            item["input_id"] for item in context.seed["providers"]
        )
        bundle = {
            "bundle_type": "official-document-coverage",
            "schema_version": "1.0",
            "skill_id": context.skill_id,
            "records": {
                "corpora": [
                    f"corpus-{input_id}.json"
                    for input_id in provider_ids
                ],
                "slice_manifests": [
                    f"slices-{input_id}.json"
                    for input_id in provider_ids
                ],
                "scope_inventory": "scope-inventory.json",
                "coverage": "coverage.json",
            },
        }
        outputs = {
            name: b"{}\n"
            for name in builder._expected_output_names(context)
        }
        outputs["bundle.json"] = builder.canonical_json_bytes(bundle)
        return outputs

    def test_bundle_requires_exact_ordered_four_family_records(self) -> None:
        seed = {
            "providers": [
                {"input_id": "zeta"},
                {"input_id": "alpha"},
            ],
            "limitations": ["synthetic"],
            "blockers": [],
            "status_ceiling": "partial",
        }
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory), seed=seed)
            outputs = self.valid_outputs(context)
            builder._validate_output_closure(context, outputs)

            wrong_order = copy.deepcopy(outputs)
            bundle = json.loads(wrong_order["bundle.json"])
            bundle["records"]["corpora"].reverse()
            wrong_order["bundle.json"] = builder.canonical_json_bytes(bundle)
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "exact ordered provider set",
            ):
                builder._validate_output_closure(context, wrong_order)

            fifth_key = copy.deepcopy(outputs)
            bundle = json.loads(fifth_key["bundle.json"])
            bundle["records"]["license_reviews"] = []
            fifth_key["bundle.json"] = builder.canonical_json_bytes(bundle)
            with self.assertRaisesRegex(
                builder.PackBuildError,
                "records keys must be exactly",
            ):
                builder._validate_output_closure(context, fifth_key)

    def test_output_closure_rejects_fifth_file_and_unsafe_name(self) -> None:
        seed = {
            "providers": [{"input_id": "provider-one"}],
            "limitations": ["synthetic"],
            "blockers": [],
            "status_ceiling": "partial",
        }
        with tempfile.TemporaryDirectory() as directory:
            context = self.context(Path(directory), seed=seed)
            for name in (
                "license-review-provider-one.json",
                "../escape.json",
            ):
                outputs = self.valid_outputs(context)
                outputs[name] = b"{}\n"
                with self.subTest(name=name), self.assertRaisesRegex(
                    builder.PackBuildError,
                    "output set differs",
                ):
                    builder._validate_output_closure(context, outputs)

    def test_atomic_replace_commits_exact_pack(self) -> None:
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
            expected = {"bundle.json": b'{"new":true}\n'}
            builder._atomic_replace_pack(context, expected)
            self.assertEqual(
                builder._pack_inventory(pack, label="committed"),
                expected,
            )
            self.assertFalse(
                any(
                    item.name.startswith(".source-pack-")
                    for item in pack.parent.iterdir()
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

    def test_all_builds_finish_before_transaction_mutation(self) -> None:
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
                mock.patch.object(builder, "_atomic_replace_packs") as replace,
                self.assertRaisesRegex(builder.PackBuildError, "second failed"),
            ):
                builder._build_selected_with_snapshot(
                    root,
                    SimpleNamespace(),
                    ("first-skill", "second-skill"),
                    check=False,
                )
            replace.assert_not_called()


if __name__ == "__main__":
    unittest.main()
