from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from migrate_official_document_catalogs_v11 import (  # noqa: E402
    LEGACY_RECORD_ACTIONS,
    MIGRATION_INVENTORY_LIMITATION,
    MigrationError,
    convert_catalog_v10_to_v11,
)
from official_source_authorities import validate_and_project  # noqa: E402
from registry_yaml import load_yaml_strict  # noqa: E402


@dataclass(frozen=True)
class CatalogCase:
    skill_id: str
    provider: dict[str, object]
    authority: dict[str, str]
    authority_projection: dict[str, object]
    scope_catalog: dict[str, object]
    catalog: dict[str, object]
    inventory_projection: dict[str, object]


@dataclass(frozen=True)
class HarnessResult:
    converted: tuple[dict[str, object], ...]
    inputs_unchanged: int
    schema_valid: int


def _catalog_cases() -> tuple[CatalogCase, ...]:
    authorities = load_yaml_strict(
        ROOT / "registry" / "official-source-authorities.yaml",
        "official-source-authorities.yaml",
    )
    software = load_yaml_strict(
        ROOT / "registry" / "software-registry.yaml",
        "software-registry.yaml",
    )
    failures, projections = validate_and_project(
        authorities,
        software_data=software,
        source_root=ROOT,
    )
    if failures:
        raise AssertionError(f"authority registry invalid: {failures}")

    cases: list[CatalogCase] = []
    for seed_path in sorted(ROOT.glob("skills/*/references/source-pack-seed.json")):
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        scope = json.loads(
            (ROOT / seed["scope_catalog_ref"]["path"]).read_text(encoding="utf-8")
        )
        for provider in seed["providers"]:
            if provider["adapter_id"] != "declarative-catalog-v1":
                continue
            catalog_path = ROOT / provider["source_ref"]["path"]
            raw = catalog_path.read_bytes()
            catalog = json.loads(raw)
            included = [
                source
                for source in catalog["sources"]
                if source.get("disposition") == "included"
            ]
            if not included:
                raise AssertionError(f"{catalog_path}: no included source")
            cases.append(
                CatalogCase(
                    skill_id=seed["skill_id"],
                    provider=provider,
                    authority={"authority_id": provider["authority_id"]},
                    authority_projection=projections[provider["authority_id"]],
                    scope_catalog=scope,
                    catalog=catalog,
                    inventory_projection={
                        # The one-time migration binds the exact catalog bytes as
                        # its technical inventory while choosing an authority-
                        # covered locator from the included source universe.
                        "locator": included[0]["locator"],
                        "identity": {
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "bytes": len(raw),
                        },
                        "canonical_preimage_bytes": raw,
                    },
                )
            )
    return tuple(cases)


def run_catalog_harness(
    cases: tuple[CatalogCase, ...],
    schema: dict[str, object],
) -> HarnessResult:
    """Pure conversion/validation harness over already-loaded catalog cases."""

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    converted: list[dict[str, object]] = []
    unchanged = 0
    schema_valid = 0
    for case in cases:
        before = copy.deepcopy(case.catalog)
        output = convert_catalog_v10_to_v11(
            case.catalog,
            provider=case.provider,
            authority=case.authority,
            authority_projection=case.authority_projection,
            scope_catalog=case.scope_catalog,
            inventory_projection=case.inventory_projection,
        )
        if case.catalog == before:
            unchanged += 1
        errors = sorted(validator.iter_errors(output), key=lambda item: list(item.path))
        if not errors:
            schema_valid += 1
        converted.append(output)
    return HarnessResult(tuple(converted), unchanged, schema_valid)


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


class OfficialDocumentCatalogMigrationV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        first_seed_path = sorted(
            ROOT.glob("skills/*/references/source-pack-seed.json")
        )[0]
        first_seed = json.loads(first_seed_path.read_text(encoding="utf-8"))
        first_declarative = next(
            provider
            for provider in first_seed["providers"]
            if provider["adapter_id"] == "declarative-catalog-v1"
        )
        first_catalog = json.loads(
            (ROOT / first_declarative["source_ref"]["path"]).read_text(
                encoding="utf-8"
            )
        )
        if first_catalog.get("schema_version") == "1.1":
            raise unittest.SkipTest(
                "one-time v1.0 source fixtures were atomically migrated to v1.1"
            )
        cls.cases = _catalog_cases()
        cls.schema = json.loads(
            (ROOT / "contracts" / "official-document-source-catalog-1.1.schema.json")
            .read_text(encoding="utf-8")
        )

    def test_exact_typed_legacy_ledger_shape(self) -> None:
        counts: dict[tuple[str, str], int] = {}
        for entry in LEGACY_RECORD_ACTIONS:
            key = (entry.record_type, entry.action)
            counts[key] = counts.get(key, 0) + 1
        self.assertEqual(
            {
                record_type: sum(
                    count
                    for (candidate_type, _), count in counts.items()
                    if candidate_type == record_type
                )
                for record_type in {
                    "blocker",
                    "loss",
                    "subject",
                    "limitation",
                    "exclusion",
                }
            },
            {
                "blocker": 10,
                "loss": 10,
                "subject": 26,
                "limitation": 12,
                "exclusion": 2,
            },
        )
        self.assertEqual(
            {action: counts.get(("blocker", action), 0) for action in {"drop", "rename", "rewrite"}},
            {"drop": 5, "rename": 4, "rewrite": 1},
        )
        self.assertEqual(
            {action: counts.get(("loss", action), 0) for action in {"drop", "rename", "preserve", "rewrite"}},
            {"drop": 2, "rename": 1, "preserve": 1, "rewrite": 6},
        )
        self.assertEqual(
            {action: counts.get(("subject", action), 0) for action in {"drop", "rename"}},
            {"drop": 5, "rename": 21},
        )
        self.assertEqual(
            {action: counts.get(("limitation", action), 0) for action in {"drop", "rewrite"}},
            {"drop": 2, "rewrite": 10},
        )
        self.assertEqual(counts.get(("exclusion", "rewrite")), 2)

    def test_every_legacy_ledger_entry_matches_one_real_catalog_record(self) -> None:
        record_keys = {
            "blocker": ("blockers", "code"),
            "loss": ("losses", "loss_id"),
            "subject": ("subjects", "subject_id"),
            "exclusion": ("reviewed_exclusions", "source_id"),
        }
        for action in LEGACY_RECORD_ACTIONS:
            hits = 0
            scope_hits = 0
            for case in self.cases:
                if case.provider["input_id"] != action.provider_input_id:
                    continue
                if action.record_type == "limitation":
                    hits += case.catalog["limitations"].count(action.record_id)
                    continue
                collection, identity_key = record_keys[action.record_type]
                for record in case.catalog[collection]:
                    if record.get(identity_key) != action.record_id:
                        continue
                    self.assertEqual(_canonical_sha256(record), action.expected_sha256)
                    hits += 1
                if action.record_type == "subject":
                    scope_hits += sum(
                        subject.get("subject_id") == action.record_id
                        and action.provider_input_id
                        in subject.get("provider_input_ids", [])
                        and subject.get("statement")
                        == action.expected_scope_statement
                        for subject in case.scope_catalog["subjects"]
                    )
            with self.subTest(
                record_type=action.record_type,
                provider_input_id=action.provider_input_id,
                record_id=action.record_id,
            ):
                self.assertEqual(hits, 1)
                if action.record_type == "subject":
                    self.assertEqual(scope_hits, 1)

    def test_all_55_catalogs_convert_and_validate_without_mutating_inputs(self) -> None:
        self.assertEqual(len(self.cases), 55)
        result = run_catalog_harness(self.cases, self.schema)
        self.assertEqual(len(result.converted), 55)
        self.assertEqual(result.inputs_unchanged, 55)
        self.assertEqual(result.schema_valid, 55)

        included = [
            source
            for catalog in result.converted
            for source in catalog["discovered_sources"].values()
            if source["disposition"] == "included"
        ]
        selectors = [
            selector for source in included for selector in source["selectors"]
        ]
        self.assertEqual(len(included), 265)
        self.assertTrue(
            all(source["content"]["content_mode"] == "external-content" for source in included)
        )
        self.assertEqual(len(selectors), 265)
        self.assertEqual(
            sum(
                selector["kind"] == "whole-source"
                and selector["layer"] == "raw-source"
                for selector in selectors
            ),
            259,
        )
        self.assertEqual(
            sum(
                selector["kind"] == "json-pointer"
                and selector["layer"] == "derived-artifact"
                for selector in selectors
            ),
            6,
        )
        self.assertTrue(
            all(
                MIGRATION_INVENTORY_LIMITATION in catalog["limitations"]
                for catalog in result.converted
            )
        )

    def test_receipts_and_selected_identities_are_exact_legacy_projections(self) -> None:
        result = run_catalog_harness(self.cases, self.schema)
        outputs = iter(result.converted)
        for case in self.cases:
            output = next(outputs)
            for source in case.catalog["sources"]:
                if source.get("disposition") != "included":
                    continue
                projected = output["discovered_sources"][source["source_id"]]
                legacy_receipt = source["slices"][0]["external_receipt"]
                self.assertEqual(
                    projected["content"]["receipt"],
                    {
                        key: legacy_receipt[key]
                        for key in (
                            "retrieval_method",
                            "retrieved_utc",
                            "raw_sha256",
                            "raw_bytes",
                        )
                    },
                )
                self.assertEqual(
                    projected["selectors"][0]["selected_identity"],
                    {
                        "sha256": legacy_receipt["selected_sha256"],
                        "bytes": legacy_receipt["selected_bytes"],
                    },
                )

    def test_gromacs_energy_terms_false_positive_is_unchanged(self) -> None:
        case = next(
            item
            for item in self.cases
            if item.provider["input_id"] == "gromacs-docs"
        )
        output = convert_catalog_v10_to_v11(
            case.catalog,
            provider=case.provider,
            authority=case.authority,
            authority_projection=case.authority_projection,
            scope_catalog=case.scope_catalog,
            inventory_projection=case.inventory_projection,
        )
        subject_id = "recipe.extract-energy-series"
        legacy = next(
            item for item in case.catalog["subjects"] if item["subject_id"] == subject_id
        )
        scope = next(
            item
            for item in case.scope_catalog["subjects"]
            if item["subject_id"] == subject_id
            and "gromacs-docs" in item["provider_input_ids"]
        )
        self.assertEqual(output["subjects"][subject_id]["title"], legacy["title"])
        self.assertEqual(output["subjects"][subject_id]["statement"], scope["statement"])

    def test_boolean_byte_count_fails_closed(self) -> None:
        case = next(
            item
            for item in self.cases
            if item.provider["input_id"] == "gromacs-docs"
        )
        catalog = copy.deepcopy(case.catalog)
        catalog["sources"][0]["external_identity"]["raw_bytes"] = True
        with self.assertRaisesRegex(MigrationError, "SOURCE_BYTES_TYPE"):
            convert_catalog_v10_to_v11(
                catalog,
                provider=case.provider,
                authority=case.authority,
                authority_projection=case.authority_projection,
                scope_catalog=case.scope_catalog,
                inventory_projection=case.inventory_projection,
            )


if __name__ == "__main__":
    unittest.main()
