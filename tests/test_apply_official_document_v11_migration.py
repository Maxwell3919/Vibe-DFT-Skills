from __future__ import annotations

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
    EXPECTED_DECLARATIVE_CATALOGS,
    EXPECTED_SEEDS,
    apply_changes_atomically,
    build_plan,
    enumerate_provider_inputs,
)


class ApplyOfficialDocumentV11MigrationTests(unittest.TestCase):
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
