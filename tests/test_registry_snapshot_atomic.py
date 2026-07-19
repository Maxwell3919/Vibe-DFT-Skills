from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import audit_repository  # noqa: E402
from registry_snapshot import (  # noqa: E402
    RegistrySnapshotError,
    load_registry_snapshot,
)


class _SyntheticHygieneFinding:
    def render(self) -> str:
        return "HYGIENE_SYNTHETIC\tsynthetic\tstill audited"


class RegistrySnapshotAtomicTests(unittest.TestCase):
    def test_shared_snapshot_contains_all_six_exact_registry_documents(self) -> None:
        snapshot = load_registry_snapshot(ROOT, validate_sources=False)
        self.assertEqual(
            set(snapshot.registry_raw),
            {
                "skill-registry.yaml",
                "software-registry.yaml",
                "interface-registry.yaml",
                "environment-profiles.yaml",
                "operation-routes.yaml",
                "official-source-authorities.yaml",
            },
        )
        self.assertEqual(set(snapshot.registry_raw), set(snapshot.registry_sha256))
        self.assertEqual(len(snapshot.operation_routes["routes"]), 26)
        canonical = snapshot.active_official_source_authorities()[
            "cp2k-official-manual"
        ]["canonical_snapshot"]
        self.assertIs(canonical["integrity_verified"], True)
        self.assertEqual(len(canonical["sources_by_id"]), 86)

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
