from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import audit_repository  # noqa: E402
import registry_snapshot  # noqa: E402
from registry_yaml import RegistryYAMLError  # noqa: E402
from registry_snapshot import (  # noqa: E402
    RegistrySnapshotError,
    load_registry_snapshot,
)


class _SyntheticHygieneFinding:
    def render(self) -> str:
        return "HYGIENE_SYNTHETIC\tsynthetic\tstill audited"


class RegistrySnapshotAtomicTests(unittest.TestCase):
    def test_shared_snapshot_contains_all_ten_exact_registry_documents(self) -> None:
        snapshot = load_registry_snapshot(ROOT, validate_sources=False)
        self.assertEqual(
            set(snapshot.registry_raw),
            {
                "active-evidence.yaml",
                "skill-registry.yaml",
                "software-registry.yaml",
                "interface-registry.yaml",
                "environment-profiles.yaml",
                "operation-routes.yaml",
                "official-source-authorities.yaml",
                "official-document-consumers.yaml",
                "official-document-bundle-expectations.yaml",
                "official-document-storage-discovery.yaml",
            },
        )
        self.assertEqual(set(snapshot.registry_raw), set(snapshot.registry_sha256))
        self.assertEqual(len(snapshot.operation_routes["routes"]), 26)
        canonical = snapshot.active_official_source_authorities()[
            "cp2k-official-manual"
        ]["canonical_snapshot"]
        # The repository stores only the CP2K receipt.  Integrity becomes true
        # only after the external provider cache is checked at runtime.
        self.assertIs(canonical["integrity_verified"], False)
        self.assertEqual(len(canonical["sources_by_id"]), 86)
        self.assertEqual(
            snapshot.official_document_consumers["default_policy"],
            "deny",
        )
        self.assertEqual(
            len(snapshot.official_document_consumers["bindings"]),
            57,
        )
        expected_bindings = {
            (
                seed["skill_id"],
                provider["authority_id"],
                provider["provider_id"],
            )
            for seed_path in sorted(
                (ROOT / "skills").glob("*/references/source-pack-seed.json")
            )
            for seed in [json.loads(seed_path.read_text(encoding="utf-8"))]
            for provider in seed["providers"]
        }
        actual_bindings = {
            (
                binding["consumer_skill_id"],
                binding["authority_id"],
                binding["provider_id"],
            )
            for binding in snapshot.official_document_consumers["bindings"]
        }
        self.assertEqual(actual_bindings, expected_bindings)
        self.assertEqual(
            snapshot.official_document_bundle_expectations["migration_policy"],
            {
                "temporary": True,
                "removal_condition": (
                    "replace-with-pack-required-when-first-pack-is-added"
                ),
                "downgrade_policy": "forbidden",
            },
        )
        self.assertEqual(
            set(snapshot.official_document_bundle_expectations["skills"]),
            set(snapshot.skills["skills"]),
        )
        self.assertEqual(
            snapshot.official_document_storage_discovery[
                "authority_registry"
            ],
            "registry/official-source-authorities.yaml",
        )
        self.assertEqual(
            snapshot.official_document_storage_discovery["migration_policy"][
                "waiver_policy"
            ],
            "forbidden",
        )

    def test_consumer_registry_missing_or_policy_drift_blocks_atomic_snapshot(
        self,
    ) -> None:
        original = registry_snapshot.load_yaml_strict_with_raw

        def missing(path, label):
            if label == "official-document-consumers.yaml":
                raise RegistryYAMLError(
                    "YAML_IO_ERROR",
                    label,
                    "synthetic missing consumer registry",
                )
            return original(path, label)

        with mock.patch.object(
            registry_snapshot,
            "load_yaml_strict_with_raw",
            side_effect=missing,
        ):
            with self.assertRaisesRegex(
                RegistrySnapshotError,
                "official_document_consumers",
            ):
                load_registry_snapshot(ROOT, validate_sources=False)

        def drifted(path, label):
            data, raw = original(path, label)
            if label == "official-document-consumers.yaml":
                data = copy.deepcopy(data)
                data["default_policy"] = "allow"
            return data, raw

        with mock.patch.object(
            registry_snapshot,
            "load_yaml_strict_with_raw",
            side_effect=drifted,
        ):
            with self.assertRaisesRegex(
                RegistrySnapshotError,
                "official-document-consumers.*only deny",
            ):
                load_registry_snapshot(ROOT, validate_sources=False)

    def test_consumer_registry_rejects_removed_license_trust_root_key(
        self,
    ) -> None:
        original = registry_snapshot.load_yaml_strict_with_raw

        def drifted(path, label):
            data, raw = original(path, label)
            if label == "official-document-consumers.yaml":
                data = copy.deepcopy(data)
                data["license_trust"] = {}
            return data, raw

        with mock.patch.object(
            registry_snapshot,
            "load_yaml_strict_with_raw",
            side_effect=drifted,
        ):
            with self.assertRaisesRegex(
                RegistrySnapshotError,
                "official-document-consumers.*unexpected key 'license_trust'",
            ):
                load_registry_snapshot(ROOT, validate_sources=False)

    def test_expectation_registry_missing_or_membership_drift_blocks_atomic_snapshot(
        self,
    ) -> None:
        original = registry_snapshot.load_yaml_strict_with_raw

        def missing(path, label):
            if label == "official-document-bundle-expectations.yaml":
                raise RegistryYAMLError(
                    "YAML_IO_ERROR",
                    label,
                    "synthetic missing expectation registry",
                )
            return original(path, label)

        with mock.patch.object(
            registry_snapshot,
            "load_yaml_strict_with_raw",
            side_effect=missing,
        ):
            with self.assertRaisesRegex(
                RegistrySnapshotError,
                "official_document_bundle_expectations",
            ):
                load_registry_snapshot(ROOT, validate_sources=False)

        def drifted(path, label):
            data, raw = original(path, label)
            if label == "official-document-bundle-expectations.yaml":
                data = copy.deepcopy(data)
                data["skills"].pop(next(iter(data["skills"])))
            return data, raw

        with mock.patch.object(
            registry_snapshot,
            "load_yaml_strict_with_raw",
            side_effect=drifted,
        ):
            with self.assertRaisesRegex(
                RegistrySnapshotError,
                "official-document-bundle-expectations.*do not match",
            ):
                load_registry_snapshot(ROOT, validate_sources=False)

    def test_storage_registry_missing_or_policy_drift_blocks_atomic_snapshot(
        self,
    ) -> None:
        original = registry_snapshot.load_yaml_strict_with_raw

        def missing(path, label):
            if label == "official-document-storage-discovery.yaml":
                raise RegistryYAMLError(
                    "YAML_IO_ERROR",
                    label,
                    "synthetic missing storage registry",
                )
            return original(path, label)

        with mock.patch.object(
            registry_snapshot,
            "load_yaml_strict_with_raw",
            side_effect=missing,
        ):
            with self.assertRaisesRegex(
                RegistrySnapshotError,
                "official_document_storage_discovery",
            ):
                load_registry_snapshot(ROOT, validate_sources=False)

        def drifted(path, label):
            data, raw = original(path, label)
            if label == "official-document-storage-discovery.yaml":
                data = copy.deepcopy(data)
                data["migration_policy"]["waiver_policy"] = "allow"
            return data, raw

        with mock.patch.object(
            registry_snapshot,
            "load_yaml_strict_with_raw",
            side_effect=drifted,
        ):
            with self.assertRaisesRegex(
                RegistrySnapshotError,
                "official-document-storage-discovery.*unsupported policy",
            ):
                load_registry_snapshot(ROOT, validate_sources=False)

    def test_root_audit_never_uses_partial_registry_state_after_snapshot_failure(self) -> None:
        with (
            mock.patch.object(
                audit_repository,
                "load_registry_snapshot",
                side_effect=RegistrySnapshotError("synthetic atomic drift"),
            ),
            mock.patch.object(
                audit_repository,
                "capability_catalog_errors",
            ) as capability_check,
            mock.patch.object(
                audit_repository,
                "audit_repository_hygiene",
                return_value=[_SyntheticHygieneFinding()],
            ) as hygiene_check,
        ):
            failures, snapshot = audit_repository.repository_audit(ROOT)

        self.assertIsNone(snapshot)
        self.assertTrue(any("synthetic atomic drift" in item for item in failures))
        self.assertTrue(any("HYGIENE_SYNTHETIC" in item for item in failures))
        capability_check.assert_not_called()
        hygiene_check.assert_called_once_with(ROOT.resolve(), skill_data=None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
