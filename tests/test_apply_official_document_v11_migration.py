from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from apply_official_document_v11_migration import (  # noqa: E402
    ApplyMigrationError,
    CP2K_MANUAL_LOCATOR_REPAIR,
    EXPECTED_DECLARATIVE_CATALOGS,
    EXPECTED_SEEDS,
    ProviderInput,
    _repair_cp2k_manual_v11_catalog,
    apply_changes_atomically,
    build_plan,
    enumerate_provider_inputs,
)
from migrate_official_document_catalogs_v11 import canonical_projection_bytes  # noqa: E402
from registry_yaml import load_yaml_strict  # noqa: E402
from validate_official_document_coverage import _url_matches_authority  # noqa: E402


class ApplyOfficialDocumentV11MigrationTests(unittest.TestCase):
    @staticmethod
    def _cp2k_repair_fixture(state: str) -> tuple[ProviderInput, dict[str, object]]:
        repair = CP2K_MANUAL_LOCATOR_REPAIR
        discovered = {}
        upstream = {}
        for index in range(repair.expected_excluded_sources):
            source_id = f"page-{index}.html"
            source_path = f"section/{source_id}"
            if state == "legacy" or (state == "mixed" and index):
                locator = repair.old_origin + source_path
            else:
                locator = repair.authority_root + source_path
            discovered[source_id] = {
                "content": {
                    "content_mode": "excluded",
                    "inventory_entry_identity": {
                        "bytes": index + 1,
                        "sha256": f"{index:064x}",
                    },
                    "locator": locator,
                },
                "disposition": "excluded",
                "rationale": "reviewed exclusion",
                "reason_code": "other",
                "source_kind": "other",
                "title": source_id,
            }
            upstream[source_id] = {
                "canonical_url": repair.authority_root + source_path,
                "source_path": source_path,
            }
        catalog = {
            "schema_version": "1.1",
            "authority_root": repair.authority_root,
            "discovered_sources": discovered,
            "discovery_processor": {
                "input_sha256": "a" * 64,
                "output_sha256": hashlib.sha256(
                    canonical_projection_bytes(discovered)
                ).hexdigest(),
                "processor_id": "synthetic",
            },
            "sentinel": {"preserved": True},
        }
        item = ProviderInput(
            seed_path=Path("/synthetic/seed.json"),
            scope_path=Path("/synthetic/scope.json"),
            catalog_path=Path("/synthetic/catalog.json"),
            provider={"input_id": repair.provider_input_id},
            seed={},
            scope={},
            catalog=catalog,
            catalog_bytes=json.dumps(catalog).encode(),
        )
        projection = {
            "allowed_https_origins": [repair.old_origin.rstrip("/")],
            "allowed_path_prefixes": ["/cp2k-2026_2-branch/"],
            "canonical_urls": [repair.authority_root],
            "canonical_snapshot": {"upstream_sources_by_id": upstream},
        }
        return item, projection

    def test_cp2k_legacy_locators_are_rebased_without_other_changes(self) -> None:
        item, projection = self._cp2k_repair_fixture("legacy")
        original = copy.deepcopy(item.catalog)
        repaired, payload = _repair_cp2k_manual_v11_catalog(item, projection)
        self.assertNotEqual(payload, item.catalog_bytes)
        expected = copy.deepcopy(original)
        for source_id, source in repaired["discovered_sources"].items():
            source_path = projection["canonical_snapshot"]["upstream_sources_by_id"][
                source_id
            ]["source_path"]
            self.assertEqual(
                source["content"]["locator"],
                CP2K_MANUAL_LOCATOR_REPAIR.authority_root + source_path,
            )
            expected["discovered_sources"][source_id]["content"]["locator"] = (
                CP2K_MANUAL_LOCATOR_REPAIR.authority_root + source_path
            )
        expected["discovery_processor"]["output_sha256"] = hashlib.sha256(
            canonical_projection_bytes(expected["discovered_sources"])
        ).hexdigest()
        self.assertEqual(repaired, expected)
        self.assertEqual(
            repaired["discovery_processor"]["input_sha256"],
            original["discovery_processor"]["input_sha256"],
        )

    def test_cp2k_repaired_locators_are_idempotent(self) -> None:
        item, projection = self._cp2k_repair_fixture("repaired")
        repaired, payload = _repair_cp2k_manual_v11_catalog(item, projection)
        self.assertIs(repaired, item.catalog)
        self.assertEqual(payload, item.catalog_bytes)

    def test_cp2k_repaired_locator_output_hash_drift_is_refreshed(self) -> None:
        item, projection = self._cp2k_repair_fixture("repaired")
        before_processor = copy.deepcopy(item.catalog["discovery_processor"])
        item.catalog["discovery_processor"]["output_sha256"] = "0" * 64
        repaired, payload = _repair_cp2k_manual_v11_catalog(item, projection)
        self.assertNotEqual(payload, item.catalog_bytes)
        expected_output = hashlib.sha256(
            canonical_projection_bytes(repaired["discovered_sources"])
        ).hexdigest()
        self.assertEqual(
            repaired["discovery_processor"]["output_sha256"],
            expected_output,
        )
        repaired["discovery_processor"]["output_sha256"] = before_processor[
            "output_sha256"
        ]
        self.assertEqual(
            repaired["discovery_processor"],
            before_processor,
        )

    def test_cp2k_mixed_locator_state_fails_closed(self) -> None:
        item, projection = self._cp2k_repair_fixture("mixed")
        with self.assertRaisesRegex(
            ApplyMigrationError, "CP2K_LOCATOR_REPAIR_MIXED_STATE"
        ):
            _repair_cp2k_manual_v11_catalog(item, projection)

    def test_cp2k_locator_drift_states_fail_closed(self) -> None:
        for drift, expected in (
            ("count", "CP2K_LOCATOR_REPAIR_COUNT_DRIFT"),
            ("nonexcluded", "CP2K_LOCATOR_REPAIR_NONEXCLUDED"),
            ("query", "CP2K_LOCATOR_REPAIR_QUERY_FRAGMENT_DRIFT"),
            ("fragment", "CP2K_LOCATOR_REPAIR_QUERY_FRAGMENT_DRIFT"),
            ("host", "CP2K_LOCATOR_REPAIR_LOCATOR_DRIFT"),
        ):
            with self.subTest(drift=drift):
                item, projection = self._cp2k_repair_fixture("legacy")
                source_id = next(iter(item.catalog["discovered_sources"]))
                source = item.catalog["discovered_sources"][source_id]
                if drift == "count":
                    del item.catalog["discovered_sources"][source_id]
                elif drift == "nonexcluded":
                    source["disposition"] = "included"
                elif drift == "query":
                    source["content"]["locator"] += "?drift=1"
                elif drift == "fragment":
                    source["content"]["locator"] += "#drift"
                else:
                    source["content"]["locator"] = source["content"][
                        "locator"
                    ].replace("manual.cp2k.org", "example.invalid")
                with self.assertRaisesRegex(ApplyMigrationError, expected):
                    _repair_cp2k_manual_v11_catalog(item, projection)

    def test_seed_enumeration_is_exact_and_ref_bound(self) -> None:
        seed_paths, provider_inputs = enumerate_provider_inputs(ROOT)
        self.assertEqual(len(seed_paths), EXPECTED_SEEDS)
        self.assertEqual(len(provider_inputs), EXPECTED_DECLARATIVE_CATALOGS)
        self.assertEqual(
            len({item.catalog_path for item in provider_inputs}),
            EXPECTED_DECLARATIVE_CATALOGS,
        )
        self.assertTrue(
            all(item.provider["adapter_id"] == "declarative-catalog-v1"
                for item in provider_inputs)
        )

    def test_repository_v11_graph_is_idempotent_and_closed(self) -> None:
        plan = build_plan(ROOT)
        self.assertEqual(plan.status, "up-to-date")
        self.assertEqual(plan.changes, {})
        self.assertEqual(len(plan.catalog_after), EXPECTED_DECLARATIVE_CATALOGS)
        self.assertEqual(len(plan.scope_after), EXPECTED_SEEDS)
        self.assertEqual(len(plan.seed_after), EXPECTED_SEEDS)
        authorities = load_yaml_strict(
            ROOT / "registry" / "official-source-authorities.yaml",
            "official-source-authorities.yaml",
        )
        authority = authorities["authorities"]["cp2k-official-manual"]
        cp2k = next(
            item
            for item in plan.provider_inputs
            if item.provider.get("input_id") == "cp2k-manual"
        )
        excluded = [
            source
            for source in cp2k.catalog["discovered_sources"].values()
            if source["disposition"] == "excluded"
        ]
        manifest = json.loads(
            (
                ROOT
                / "skills/cp2k-rigorous-calculations/references/manual-cache-receipts/manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            len(cp2k.catalog["discovered_sources"]),
            manifest["index_page_count"],
        )
        self.assertEqual(
            len(excluded),
            manifest["index_page_count"]
            - sum(
                source["disposition"] == "included"
                for source in cp2k.catalog["discovered_sources"].values()
            ),
        )
        self.assertGreaterEqual(
            len(excluded),
            CP2K_MANUAL_LOCATOR_REPAIR.expected_excluded_sources,
        )
        self.assertTrue(
            all(
                _url_matches_authority(source["content"]["locator"], authority)
                for source in excluded
            )
        )

    def test_atomic_apply_replaces_all_staged_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.json"
            second = root / "second.json"
            first.write_bytes(b"before-one")
            second.write_bytes(b"before-two")
            apply_changes_atomically(
                root,
                {first: b"after-one", second: b"after-two"},
            )
            self.assertEqual(first.read_bytes(), b"after-one")
            self.assertEqual(second.read_bytes(), b"after-two")
            self.assertEqual(
                list(root.glob(".official-doc-v11-inputs-*")),
                [],
            )

    def test_atomic_apply_restores_replaced_inputs_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.json"
            second = root / "second.json"
            first.write_bytes(b"before-one")
            second.write_bytes(b"before-two")
            calls = 0

            def fail_second_replace(source: object, target: object) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("synthetic replace failure")
                os.replace(source, target)

            with self.assertRaisesRegex(OSError, "synthetic replace failure"):
                apply_changes_atomically(
                    root,
                    {first: b"after-one", second: b"after-two"},
                    replace=fail_second_replace,
                )
            self.assertEqual(first.read_bytes(), b"before-one")
            self.assertEqual(second.read_bytes(), b"before-two")
            self.assertEqual(
                list(root.glob(".official-doc-v11-inputs-*")),
                [],
            )

    def test_atomic_apply_noop_creates_no_transaction_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apply_changes_atomically(root, {})
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
