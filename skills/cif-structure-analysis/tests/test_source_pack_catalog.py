"""Offline tests for the CIF source-pack extractor."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_source_pack_catalog.py"
SPEC = importlib.util.spec_from_file_location("cif_source_pack", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ROOT = MODULE.repository_root()
PROVIDER_CLASSES = {
    "software",
    "standard",
    "platform",
    "repository",
    "model-artifact",
    "dataset",
    "publisher",
}


class SourcePackCatalogTests(unittest.TestCase):
    def test_generated_inputs_are_current(self) -> None:
        self.assertEqual(MODULE.sync(check=True), ())

        fixture_payloads = []
        expected_paths = {
            path.relative_to(ROOT).as_posix()
            for path in MODULE.build_outputs(ROOT)
        }
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temp_dir:
                fixture_root = Path(temp_dir)
                fixture_skill = (
                    fixture_root / "skills" / MODULE.SKILL_ID
                )
                shutil.copytree(
                    ROOT / "skills" / MODULE.SKILL_ID,
                    fixture_skill,
                )
                for relative in expected_paths:
                    path = fixture_root / relative
                    if path.is_file():
                        path.unlink()

                self.assertEqual(
                    set(MODULE.sync(check=False, root=fixture_root)),
                    expected_paths,
                )
                self.assertEqual(
                    MODULE.sync(check=False, root=fixture_root),
                    (),
                )
                self.assertEqual(
                    MODULE.sync(check=True, root=fixture_root),
                    (),
                )
                fixture_payloads.append(
                    {
                        relative: (fixture_root / relative).read_bytes()
                        for relative in expected_paths
                    }
                )

        self.assertEqual(fixture_payloads[0], fixture_payloads[1])
        self.assertEqual(
            fixture_payloads[0],
            {
                relative: (ROOT / relative).read_bytes()
                for relative in expected_paths
            },
        )

    def test_scope_contains_exact_provider_and_public_symbol_sets(self) -> None:
        catalog = MODULE.scope_catalog(ROOT)
        subjects = {item["subject_id"]: item for item in catalog["subjects"]}
        self.assertEqual(
            {item for item in subjects if ":" in item and item.split(":", 1)[0] in {
                "iucr", "ase", "gemmi", "pycifrw", "spglib"
            }},
            {item[0] for item in MODULE.PROVIDER_SUBJECTS},
        )
        expected_tools = set()
        script_root = ROOT / "skills" / MODULE.SKILL_ID / "scripts"
        for path in [
            script_root / "analyze_cif.py",
            *sorted((script_root / "ciftool").glob("*.py")),
        ]:
            for symbol, _ in MODULE.public_symbols(path):
                expected_tools.add(
                    f"tool:{MODULE.safe_id(path.stem)}:{MODULE.safe_id(symbol)}"
                )
        self.assertEqual(
            {item for item in subjects if item.startswith("tool:")},
            expected_tools,
        )

    def test_authority_proposal_covers_every_seed_provider(self) -> None:
        refs = ROOT / "skills" / MODULE.SKILL_ID / "references"
        seed = json.loads(
            (refs / "source-pack-seed.json").read_text(encoding="utf-8")
        )
        proposal = json.loads(
            (refs / "source-pack-authority-proposal.json").read_text(
                encoding="utf-8"
            )
        )
        entries = [
            *proposal["authorities"],
            *proposal["existing_authority_bindings"],
        ]
        self.assertEqual(
            {
                (item["authority_id"], item["provider_id"])
                for item in entries
            },
            {
                (item["authority_id"], item["provider_id"])
                for item in seed["providers"]
            },
        )
        for item in [
            *entries,
            *proposal["provider_registry_proposals"],
        ]:
            self.assertIn(item["provider_class"], PROVIDER_CLASSES)
        for item in entries:
            binding = item["consumer_binding"]
            self.assertEqual(binding["consumer_skill_id"], MODULE.SKILL_ID)
            self.assertEqual(binding["authority_id"], item["authority_id"])
            self.assertEqual(binding["provider_id"], item["provider_id"])

    def test_seed_and_catalogs_match_strict_schemas(self) -> None:
        skill_refs = ROOT / "skills" / MODULE.SKILL_ID / "references"
        seed_path = skill_refs / "source-pack-seed.json"
        scope_path = skill_refs / "source-pack-scope.json"
        checks = [
            (
                "contracts/official-document-pack-seed.schema.json",
                seed_path,
            ),
            (
                "contracts/official-document-scope-catalog.schema.json",
                scope_path,
            ),
        ]
        checks.extend(
            (
                "contracts/official-document-source-catalog-1.1.schema.json",
                path,
            )
            for path in sorted((skill_refs / "source-pack-inputs").glob("*.json"))
        )
        for schema_path, value_path in checks:
            with self.subTest(path=value_path.name):
                schema = json.loads((ROOT / schema_path).read_text(encoding="utf-8"))
                value = json.loads(value_path.read_text(encoding="utf-8"))
                errors = sorted(
                    Draft202012Validator(
                        schema, format_checker=FormatChecker()
                    ).iter_errors(value),
                    key=lambda item: tuple(str(part) for part in item.absolute_path),
                )
                self.assertEqual([item.message for item in errors], [])

        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        scope_ref = seed["scope_catalog_ref"]
        self.assertEqual(scope_ref["path"], scope_path.relative_to(ROOT).as_posix())
        self.assertEqual(scope_ref["sha256"], MODULE.sha256_file(scope_path))

        providers = {
            item["input_id"]: item
            for item in seed["providers"]
        }
        self.assertEqual(
            set(providers),
            set(MODULE.PROVIDER_MIGRATION_SPECS),
        )
        catalog_paths = {
            path.stem: path
            for path in (skill_refs / "source-pack-inputs").glob("*.json")
        }
        self.assertEqual(set(catalog_paths), set(providers))

        legacy_catalogs = MODULE.legacy_provider_catalogs()
        for input_id, provider in providers.items():
            with self.subTest(identity=input_id):
                spec = MODULE.PROVIDER_MIGRATION_SPECS[input_id]
                catalog_path = ROOT / provider["source_ref"]["path"]
                catalog_bytes = catalog_path.read_bytes()
                catalog = json.loads(catalog_bytes)
                legacy_bytes = MODULE.canonical_json_bytes(
                    legacy_catalogs[input_id]
                )
                inventory_identity = {
                    "sha256": hashlib.sha256(legacy_bytes).hexdigest(),
                    "bytes": len(legacy_bytes),
                }

                self.assertEqual(provider["authority_id"], spec.authority_id)
                self.assertEqual(provider["provider_id"], spec.provider_id)
                self.assertEqual(
                    provider["source_ref"]["sha256"],
                    hashlib.sha256(catalog_bytes).hexdigest(),
                )
                self.assertEqual(catalog["schema_version"], "1.1")
                self.assertEqual(catalog["authority_id"], spec.authority_id)
                self.assertEqual(catalog["provider_id"], spec.provider_id)
                self.assertEqual(
                    catalog["inventory_identity"],
                    inventory_identity,
                )
                self.assertEqual(
                    catalog["authority_revision"],
                    inventory_identity["sha256"],
                )
                self.assertEqual(
                    catalog["discovery_processor"]["input_sha256"],
                    inventory_identity["sha256"],
                )
                self.assertEqual(
                    catalog["discovery_processor"]["output_sha256"],
                    MODULE.sha256_bytes(
                        MODULE.canonical_projection_bytes(
                            catalog["discovered_sources"]
                        )
                    ),
                )


if __name__ == "__main__":
    unittest.main()
