from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
TESTS = ROOT / "tests"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

import build_official_document_dashboard as dashboard  # noqa: E402
import validate_official_document_bundles as bundle_audit  # noqa: E402
import test_official_document_v11_contracts as v11_contracts  # noqa: E402


def assurance_layers(status: str) -> dict[str, dict[str, object]]:
    return {
        name: {"status": status}
        for name in dashboard.ASSURANCE_LAYER_ORDER
    }


class OfficialDocumentDashboardTests(unittest.TestCase):
    def _v11_bundle_status(self) -> dict[str, str]:
        return {
            "overall": "partial",
            "corpus": "partial",
            "slices": "partial",
            "scope": "partial",
            "mappings": "partial",
        }

    def _v11_content(self, mode: str) -> dict[str, object]:
        if mode == "embedded-content":
            return copy.deepcopy(v11_contracts.embedded_slice_content())
        if mode == "external-content":
            return copy.deepcopy(v11_contracts.external_slice_content())
        if mode == "metadata-only":
            return copy.deepcopy(v11_contracts.metadata_slice_content())
        if mode == "excluded":
            return copy.deepcopy(v11_contracts.excluded_content())
        return {
            "content_mode": "other",
            "locator": "https://docs.example.org/other.txt",
            "identity": {
                "sha256": "4" * 64,
                "bytes": 4,
            },
        }

    def _v11_slice(
        self,
        *,
        slice_id: str,
        selector_kind: str,
        selector_value: str,
        mode: str,
        start_byte: int = 0,
        byte_count: int = 8,
    ) -> dict[str, object]:
        return {
            "slice_id": slice_id,
            "selector": {
                "layer": "raw-source",
                "kind": selector_kind,
                "value": selector_value,
            },
            "raw_byte_range": {
                "start_byte": start_byte,
                "byte_count": byte_count,
            },
            "content": self._v11_content(mode),
            "subject_ids": ["subject-one"],
            "loss_accounting": v11_contracts.loss_accounting(),
        }

    def _v11_pack_payloads(
        self,
        *,
        corpus_status: str,
        slice_status: str,
        coverage_status: dict[str, str],
        source_slices: dict[str, list[dict[str, object]]],
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        corpus = copy.deepcopy(v11_contracts.corpus_record())
        corpus["status"] = corpus_status
        corpus["authority_id"] = "example-authority"
        base_sources = copy.deepcopy(v11_contracts.slice_record()["sources"])
        manifest_sources: dict[str, object] = {}
        for source_id, slices in source_slices.items():
            source = copy.deepcopy(base_sources[source_id])
            source["slices"] = slices
            manifest_sources[source_id] = source
        if not manifest_sources:
            raise ValueError("sources may not be empty")

        slice_manifest = copy.deepcopy(v11_contracts.slice_record())
        slice_manifest["status"] = slice_status
        slice_manifest["sources"] = manifest_sources

        coverage = copy.deepcopy(v11_contracts.coverage_record())
        coverage["status"] = coverage_status
        return corpus, slice_manifest, coverage

    def pack_projection(
        self,
        *,
        slice_status: str = "partial",
        source_slices: dict[str, list[dict[str, object]]],
        corpus_status: str = "partial",
        coverage_status: dict[str, str] | None = None,
    ) -> tuple[
        dict[str, str],
        dict[str, dict[str, object]],
        tuple[str, ...],
    ]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = (
                root
                / "skills"
                / "example-skill"
                / "references"
                / "official-source-pack"
            )
            pack.mkdir(parents=True)
            records = {
                "corpora": ["corpus.json"],
                "slice_manifests": ["slices.json"],
                "scope_inventory": "scope.json",
                "coverage": "coverage.json",
            }
            coverage_status = (
                coverage_status
                if coverage_status is not None
                else self._v11_bundle_status()
            )
            corpus, slices_record, coverage = self._v11_pack_payloads(
                corpus_status=corpus_status,
                slice_status=slice_status,
                coverage_status=coverage_status,
                source_slices=source_slices,
            )
            payloads = {
                "bundle.json": {
                    "schema_version": "1.0",
                    "bundle_type": "official-document-coverage",
                    "skill_id": "example-skill",
                    "records": records,
                },
                "corpus.json": corpus,
                "slices.json": slices_record,
                "scope.json": {"status": "partial"},
                "coverage.json": coverage,
            }
            for name, payload in payloads.items():
                (pack / name).write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )
            result = bundle_audit.BundleResult(
                skill_id="example-skill",
                state="partial",
                entrypoint=(
                    "skills/example-skill/references/"
                    "official-source-pack/bundle.json"
                ),
                message="synthetic semantically valid incomplete pack",
            )
            return dashboard._load_pack_projection(root, result)

    def test_expected_rows_are_derived_from_verified_source_skill_set(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "registry"
            registry.mkdir()
            (registry / "skill-registry.yaml").write_text(
                "\n".join(
                    (
                        'schema_version: "1.0"',
                        "skills:",
                        "  alpha-skill:",
                        "    lifecycle: active",
                        "    path: skills/alpha-skill",
                        "  beta-skill:",
                        "    lifecycle: development",
                        "    path: skills/beta-skill",
                        "  future-skill:",
                        "    lifecycle: planned",
                        "    path: null",
                        "",
                    )
                ),
                encoding="utf-8",
            )
            expectation_path = (
                registry / "official-document-bundle-expectations.yaml"
            )
            expectation_text = "\n".join(
                (
                    'schema_version: "1.0"',
                    "migration_policy:",
                    "  temporary: true",
                    "  removal_condition: replace-with-pack-required-when-first-pack-is-added",
                    "  downgrade_policy: forbidden",
                    "skills:",
                    "  alpha-skill:",
                    "    expectation: pack-required",
                    "    entrypoint: skills/alpha-skill/references/official-source-pack/bundle.json",
                    "  beta-skill:",
                    "    expectation: pack-required",
                    "    entrypoint: skills/beta-skill/references/official-source-pack/bundle.json",
                    "",
                )
            )
            expectation_path.write_text(
                expectation_text,
                encoding="utf-8",
            )
            self.assertEqual(
                dashboard._expected_skills(root),
                {
                    "alpha-skill": (
                        "skills/alpha-skill/references/"
                        "official-source-pack/bundle.json"
                    ),
                    "beta-skill": (
                        "skills/beta-skill/references/"
                        "official-source-pack/bundle.json"
                    ),
                },
            )
            expectation_path.write_text(
                "\n".join(expectation_text.splitlines()[:-3]) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                dashboard.DashboardError,
                "expectation/Skill registry mismatch",
            ):
                dashboard._expected_skills(root)

    def test_current_trusted_full_authority_overlay_replaces_unknown(self) -> None:
        self.assertEqual(
            dashboard._apply_freshness_overlay(
                "unknown",
                {
                    "authority_statuses": {
                        "authority-a": "complete",
                        "authority-b": "complete",
                    },
                    "observed_utc": "2026-07-24T00:00:00Z",
                    "trust_id": "scheduled-drift-attestation-1",
                    "trust_mode": "platform-attested",
                    "valid_until_utc": "2026-07-25T00:00:00Z",
                },
                ("authority-a", "authority-b"),
                as_of_utc="2026-07-24T12:00:00Z",
            ),
            "complete",
        )

    def test_partial_stale_or_untrusted_overlay_cannot_upgrade_unknown(
        self,
    ) -> None:
        base = {
            "authority_statuses": {
                "authority-a": "complete",
                "authority-b": "complete",
            },
            "observed_utc": "2026-07-24T00:00:00Z",
            "trust_id": "scheduled-drift-attestation-1",
            "trust_mode": "platform-attested",
            "valid_until_utc": "2026-07-25T00:00:00Z",
        }
        partial = {
            **base,
            "authority_statuses": {"authority-a": "complete"},
        }
        stale = {
            **base,
            "valid_until_utc": "2026-07-24T06:00:00Z",
        }
        future = {
            **base,
            "observed_utc": "2026-07-24T18:00:00Z",
        }
        untrusted = {
            **base,
            "trust_id": None,
            "trust_mode": "unverified",
        }
        for overlay in (partial, stale, future, untrusted):
            with self.subTest(overlay=overlay):
                self.assertEqual(
                    dashboard._apply_freshness_overlay(
                        "unknown",
                        overlay,
                        ("authority-a", "authority-b"),
                        as_of_utc="2026-07-24T12:00:00Z",
                    ),
                    "unknown",
                )

    def test_blocked_authority_overlay_caps_freshness_even_if_partial(self) -> None:
        self.assertEqual(
            dashboard._apply_freshness_overlay(
                "unknown",
                {
                    "authority_statuses": {"authority-a": "blocked"},
                    "observed_utc": "2026-07-24T00:00:00Z",
                    "trust_id": None,
                    "trust_mode": "unverified",
                    "valid_until_utc": "2026-07-24T06:00:00Z",
                },
                ("authority-a", "authority-b"),
                as_of_utc="2026-07-24T12:00:00Z",
            ),
            "blocked",
        )

    def test_malformed_freshness_overlay_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            dashboard.DashboardError,
            "freshness overlay fields are not exact",
        ):
            dashboard._apply_freshness_overlay(
                "unknown",
                {
                    "authority_statuses": {"authority-a": "complete"},
                    "observed_utc": "2026-07-24T00:00:00Z",
                    "trust_mode": "platform-attested",
                    "valid_until_utc": "2026-07-25T00:00:00Z",
                },
                ("authority-a",),
                as_of_utc="2026-07-24T12:00:00Z",
            )

    def test_aggregate_partial_or_unknown_never_becomes_complete(self) -> None:
        self.assertEqual(
            dashboard.aggregate_statuses(("complete", "partial")),
            "partial",
        )
        self.assertEqual(
            dashboard.aggregate_statuses(("complete", "unknown")),
            "unknown",
        )
        self.assertEqual(
            dashboard.aggregate_statuses(("complete", "complete")),
            "complete",
        )

    def test_partial_bundle_semantics_caps_an_otherwise_complete_row(self) -> None:
        row = dashboard.make_skill_row(
            skill_id="example-skill",
            entrypoint=(
                "skills/example-skill/references/"
                "official-source-pack/bundle.json"
            ),
            bundle_semantic_state="partial",
            dimensions={
                name: "complete" for name in dashboard.DIMENSION_ORDER
            },
            assurance_layers=assurance_layers("complete"),
        )
        self.assertEqual(row["overall_status"], "partial")
        self.assertEqual(row["bundle_semantic_state"], "partial")

    def test_missing_bundle_cannot_claim_freshness_complete(self) -> None:
        row = dashboard.make_skill_row(
            skill_id="example-skill",
            entrypoint=(
                "skills/example-skill/references/"
                "official-source-pack/bundle.json"
            ),
            bundle_semantic_state="missing",
            dimensions={
                "corpus": "missing",
                "slice": "missing",
                "scope": "missing",
                "coverage": "missing",
                "freshness": "missing",
            },
            assurance_layers={
                **assurance_layers("missing"),
                "content_materialized": {"status": "blocked"},
            },
        )
        self.assertEqual(row["overall_status"], "blocked")
        self.assertNotEqual(row["dimensions"]["freshness"], "complete")

    def test_layers_distinguish_whole_source_metadata_from_materialized_slice(
        self,
    ) -> None:
        _, layers, _ = self.pack_projection(
            slice_status="partial",
            source_slices={
                "doc-embedded": [
                    self._v11_slice(
                        slice_id="whole-metadata",
                        selector_kind="whole-source",
                        selector_value="*",
                        mode="metadata-only",
                        start_byte=0,
                    ),
                    self._v11_slice(
                        slice_id="heading-content",
                        selector_kind="heading",
                        selector_value="SCF",
                        mode="embedded-content",
                        start_byte=16,
                    ),
                ]
            },
        )
        content = layers["content_materialized"]
        semantic = layers["semantic_slice"]
        self.assertEqual(content["status"], "partial")
        self.assertEqual(content["repository_materialized_slice_count"], 1)
        self.assertEqual(content["metadata_only_slice_count"], 1)
        self.assertEqual(semantic["status"], "partial")
        self.assertEqual(semantic["fine_grained_slice_count"], 1)
        self.assertEqual(semantic["whole_source_metadata_only_slice_count"], 1)
        self.assertEqual(
            semantic["fine_grained_materialized_slice_count"],
            1,
        )

    def test_whole_source_metadata_only_is_not_materialized_or_semantic(
        self,
    ) -> None:
        _, layers, _ = self.pack_projection(
            slice_status="partial",
            source_slices={
                "doc-embedded": [
                    self._v11_slice(
                        slice_id="whole-metadata",
                        selector_kind="whole-source",
                        selector_value="*",
                        mode="metadata-only",
                        start_byte=0,
                        byte_count=8,
                    )
                ]
            },
        )
        self.assertEqual(
            layers["content_materialized"]["status"],
            "missing",
        )
        self.assertEqual(layers["semantic_slice"]["status"], "missing")

    def test_blocked_slice_record_is_not_collapsed_to_partial(self) -> None:
        dimensions, layers, _ = self.pack_projection(
            slice_status="blocked",
            source_slices={
                "doc-embedded": [
                    self._v11_slice(
                        slice_id="heading-content",
                        selector_kind="heading",
                        selector_value="SCF",
                        mode="embedded-content",
                        start_byte=0,
                    )
                ]
            },
        )
        self.assertEqual(
            layers["content_materialized"]["status"],
            "blocked",
        )
        self.assertEqual(layers["semantic_slice"]["status"], "blocked")
        row = dashboard.make_skill_row(
            skill_id="example-skill",
            entrypoint=(
                "skills/example-skill/references/"
                "official-source-pack/bundle.json"
            ),
            bundle_semantic_state="partial",
            dimensions=dimensions,
            assurance_layers=layers,
        )
        self.assertEqual(row["assurance_status"], "blocked")
        self.assertEqual(row["overall_status"], "blocked")

    def test_valid_v11_pack_projection_reaches_projection(self) -> None:
        dimensions, layers, authorities = self.pack_projection(
            source_slices={
                "doc-embedded": [
                    self._v11_slice(
                        slice_id="embedded-only",
                        selector_kind="byte-range",
                        selector_value="0:16",
                        mode="embedded-content",
                        start_byte=0,
                        byte_count=16,
                    ),
                    self._v11_slice(
                        slice_id="external-only",
                        selector_kind="byte-range",
                        selector_value="16:24",
                        mode="external-content",
                        start_byte=16,
                        byte_count=8,
                    ),
                ]
            },
            coverage_status={
                "overall": "partial",
                "corpus": "partial",
                "slices": "partial",
                "scope": "partial",
                "mappings": "partial",
            },
        )
        self.assertEqual(dimensions["coverage"], "partial")
        self.assertEqual(layers["content_materialized"]["slice_count"], 2)
        self.assertEqual(
            layers["content_materialized"]["external_cache_content_slice_count"],
            0,
        )
        self.assertEqual(
            layers["content_materialized"]["external_runtime_content_slice_count"],
            1,
        )
        self.assertEqual(layers["inventory"]["discovered_source_count"], 4)
        self.assertEqual(layers["inventory"]["included_source_count"], 3)
        self.assertEqual(layers["inventory"]["reviewed_exclusion_count"], 1)
        self.assertEqual(authorities, ("example-authority",))

    def test_rejects_excluded_content_mode_in_pack_projection(self) -> None:
        with self.assertRaisesRegex(
            dashboard.DashboardError,
            "unsupported content mode",
        ):
            self.pack_projection(
                source_slices={
                    "doc-embedded": [
                        self._v11_slice(
                            slice_id="excluded",
                            selector_kind="byte-range",
                            selector_value="0:16",
                            mode="excluded",
                            start_byte=0,
                            byte_count=16,
                        )
                    ]
                },
            )

    def test_rejects_other_content_mode_in_pack_projection(self) -> None:
        with self.assertRaisesRegex(
            dashboard.DashboardError,
            "unsupported content mode",
        ):
            self.pack_projection(
                source_slices={
                    "doc-embedded": [
                        self._v11_slice(
                            slice_id="other-mode",
                            selector_kind="byte-range",
                            selector_value="0:16",
                            mode="other",
                            start_byte=0,
                            byte_count=16,
                        )
                    ]
                },
            )

    def test_invalid_technical_status_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            dashboard.DashboardError,
            "unsupported completeness status",
        ):
            self.pack_projection(
                source_slices={
                    "doc-embedded": [
                        self._v11_slice(
                            slice_id="embedded-only",
                            selector_kind="byte-range",
                            selector_value="0:16",
                            mode="embedded-content",
                            start_byte=0,
                            byte_count=16,
                        )
                    ]
                },
                coverage_status={
                    "overall": "partial",
                    "corpus": "partial",
                    "slices": "partial",
                    "scope": "blocked",
                    "mappings": "invalid",
                },
            )

    def test_repository_dashboard_has_exact_26_rows_and_dimension_totals(self) -> None:
        report = dashboard.build_dashboard(ROOT)
        self.assertEqual(report["expected_bundle_count"], 26)
        self.assertEqual(len(report["skills"]), 26)
        self.assertEqual(
            [item["skill_id"] for item in report["skills"]],
            sorted(item["skill_id"] for item in report["skills"]),
        )
        for dimension in dashboard.DIMENSION_ORDER:
            self.assertEqual(
                sum(report["summary"]["dimensions"][dimension].values()),
                26,
            )
        for layer in dashboard.ASSURANCE_LAYER_ORDER:
            self.assertEqual(
                sum(
                    report["summary"]["assurance_layers"][layer].values()
                ),
                26,
            )
        self.assertEqual(
            sum(report["summary"]["assurance_overall"].values()),
            26,
        )
        self.assertEqual(sum(report["summary"]["overall"].values()), 26)

    def test_dashboard_json_is_byte_deterministic(self) -> None:
        first = dashboard.dashboard_bytes(dashboard.build_dashboard(ROOT))
        second = dashboard.dashboard_bytes(dashboard.build_dashboard(ROOT))
        self.assertEqual(first, second)

    def test_dashboard_applies_qualified_freshness_overlay_to_one_row(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "registry"
            registry.mkdir()
            (registry / "skill-registry.yaml").write_text(
                '\n'.join(
                    (
                        'schema_version: "1.0"',
                        "skills:",
                        "  example-skill:",
                        "    lifecycle: development",
                        "    path: skills/example-skill",
                        "",
                    )
                ),
                encoding="utf-8",
            )
            (registry / "official-document-bundle-expectations.yaml").write_text(
                '\n'.join(
                    (
                        'schema_version: "1.0"',
                        "migration_policy:",
                        "  temporary: true",
                        "  removal_condition: replace-with-pack-required-when-first-pack-is-added",
                        "  downgrade_policy: forbidden",
                        "skills:",
                        "  example-skill:",
                        "    expectation: pack-required",
                        "    entrypoint: skills/example-skill/references/official-source-pack/bundle.json",
                        "",
                    )
                ),
                encoding="utf-8",
            )
            audit = bundle_audit.AuditReport(
                results=(
                    bundle_audit.BundleResult(
                        skill_id="example-skill",
                        state="partial",
                        entrypoint=(
                            "skills/example-skill/references/"
                            "official-source-pack/bundle.json"
                        ),
                        message="synthetic partial pack",
                    ),
                )
            )
            projection = (
                {
                    "corpus": "partial",
                    "slice": "partial",
                    "scope": "partial",
                    "coverage": "partial",
                    "freshness": "unknown",
                },
                assurance_layers("partial"),
                ("example-authority",),
            )
            with mock.patch.object(
                dashboard,
                "_load_pack_projection",
                return_value=projection,
            ):
                build_arguments = {
                    "bundle_report": audit,
                    "freshness_status_by_skill": {
                        "example-skill": {
                            "authority_statuses": {
                                "example-authority": "complete"
                            },
                            "observed_utc": "2026-07-24T00:00:00Z",
                            "trust_id": "scheduled-drift-attestation-1",
                            "trust_mode": "platform-attested",
                            "valid_until_utc": "2026-07-25T00:00:00Z",
                        }
                    },
                    "freshness_as_of_utc": "2026-07-24T12:00:00Z",
                }
                report = dashboard.build_dashboard(root, **build_arguments)
                repeated = dashboard.build_dashboard(root, **build_arguments)
            self.assertEqual(
                report["skills"][0]["dimensions"]["freshness"],
                "complete",
            )
            self.assertEqual(report["expected_bundle_count"], 1)
            self.assertEqual(
                dashboard.dashboard_bytes(report),
                dashboard.dashboard_bytes(repeated),
            )

    def test_missing_one_of_26_audit_results_is_rejected(self) -> None:
        live = bundle_audit.audit_repository(ROOT)
        truncated = bundle_audit.AuditReport(results=live.results[:-1])
        with self.assertRaisesRegex(
            dashboard.DashboardError,
            "exact expected Skill set",
        ):
            dashboard.build_dashboard(
                ROOT,
                bundle_report=truncated,
            )


if __name__ == "__main__":
    unittest.main()
