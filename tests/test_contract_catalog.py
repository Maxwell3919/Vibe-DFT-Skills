from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
VALIDATOR = ROOT / "tools" / "validate_contract.py"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import validate_contract  # noqa: E402
from test_wave0_execution_contracts import calculation_envelope  # noqa: E402
from test_wave0_structure_contracts import periodic_snapshot  # noqa: E402


def write_schema(
    directory: Path,
    filename: str,
    schema_id: str,
    *,
    reference: str | None = None,
    document_kind: str = "content-addressed-record",
    record_id_field: str | None = "record_id",
) -> Path:
    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "type": "object",
        "additionalProperties": False,
        "properties": {},
    }
    identity = validate_contract.CANONICAL_ID_PATTERN.fullmatch(schema_id)
    if identity is not None:
        schema["x-vibe-document-kind"] = document_kind
        schema["required"] = ["contract_name", "schema_version"]
        schema["properties"] = {
            "contract_name": {"const": identity.group("name")},
            "schema_version": {"const": identity.group("version")},
        }
        if record_id_field is not None:
            schema["x-vibe-record-id-field"] = record_id_field
            schema["required"].append(record_id_field)
            schema["properties"][record_id_field] = {
                "type": "string",
                "pattern": "^[a-z0-9][a-z0-9._-]{2,127}$",
            }
    if reference is not None:
        schema["properties"]["linked"] = {"$ref": reference}
    path = directory / filename
    path.write_text(json.dumps(schema), encoding="utf-8")
    return path


class ContractCatalogTests(unittest.TestCase):
    def run_cli(
        self,
        contracts_dir: Path,
        selector: str,
        instance: Path,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--contracts-dir",
                str(contracts_dir),
                "--allow-draft",
                selector,
                str(instance),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_repository_catalog_discovers_meta_validates_and_closes_all_refs(self) -> None:
        catalog = validate_contract.load_catalog(CONTRACTS)
        expected = {path.name for path in CONTRACTS.glob("*.schema.json")}
        self.assertEqual(set(catalog.by_filename), expected)
        self.assertEqual(len(catalog.by_schema_id), len(expected))

        for contract in catalog.contracts:
            with self.subTest(contract=contract.name):
                self.assertEqual(
                    catalog.resolve(contract.canonical_id).canonical_id,
                    contract.canonical_id,
                )
                if contract.name == "common-definitions":
                    self.assertEqual(contract.catalog_kind, "definition-library")
                    self.assertEqual(contract.document_kind, "definition-library")
                    self.assertIsNone(contract.record_id_field)
                else:
                    self.assertEqual(contract.catalog_kind, "instance-contract")
                    self.assertIn(
                        contract.document_kind,
                        {"content-addressed-record", "projection"},
                    )
                    self.assertEqual(
                        contract.is_record_ref_target,
                        contract.document_kind == "content-addressed-record",
                    )

    def test_document_kind_and_record_id_metadata_fail_closed(self) -> None:
        mutations = {
            "missing-kind": lambda schema: schema.pop("x-vibe-document-kind"),
            "unknown-kind": lambda schema: schema.update(
                {"x-vibe-document-kind": "record-ish"}
            ),
            "missing-id-metadata": lambda schema: schema.pop(
                "x-vibe-record-id-field"
            ),
            "id-not-required": lambda schema: schema["required"].remove("record_id"),
            "id-not-safe": lambda schema: schema["properties"].update(
                {"record_id": {"type": "string"}}
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label), tempfile.TemporaryDirectory() as raw_directory:
                directory = Path(raw_directory)
                path = write_schema(
                    directory,
                    "alpha.schema.json",
                    "urn:vibe-dft-skills:contract:alpha:1.0",
                )
                schema = json.loads(path.read_text(encoding="utf-8"))
                mutate(schema)
                path.write_text(json.dumps(schema), encoding="utf-8")

                with self.assertRaises(validate_contract.CatalogError) as caught:
                    validate_contract.load_catalog(directory)
                if label in {"missing-kind", "unknown-kind", "missing-id-metadata"}:
                    self.assertIn("x-vibe", str(caught.exception))
                else:
                    self.assertIn("record ID field", str(caught.exception))

    def test_projection_cannot_declare_record_id_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            path = write_schema(
                directory,
                "alpha.schema.json",
                "urn:vibe-dft-skills:contract:alpha:1.0",
                document_kind="projection",
                record_id_field=None,
            )
            catalog = validate_contract.load_catalog(directory)
            self.assertEqual(catalog.resolve("alpha").document_kind, "projection")
            self.assertFalse(catalog.resolve("alpha").is_record_ref_target)

            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["x-vibe-record-id-field"] = "record_id"
            path.write_text(json.dumps(schema), encoding="utf-8")
            with self.assertRaises(validate_contract.CatalogError) as caught:
                validate_contract.load_catalog(directory)
            self.assertIn("projection must not declare", str(caught.exception))

    def test_legacy_record_id_fields_are_an_exact_allowlist(self) -> None:
        catalog = validate_contract.load_catalog(CONTRACTS)
        for filename, record_id_field in validate_contract.LEGACY_RECORD_ID_FIELDS.items():
            with self.subTest(filename=filename):
                contract = catalog.by_filename[filename]
                self.assertTrue(contract.is_legacy)
                self.assertEqual(contract.document_kind, "content-addressed-record")
                self.assertEqual(contract.record_id_field, record_id_field)
                self.assertTrue(contract.is_record_ref_target)

    def test_legacy_aliases_and_canonical_names_resolve_the_same_contract(self) -> None:
        catalog = validate_contract.load_catalog(CONTRACTS)
        for alias, filename in validate_contract.SCHEMAS.items():
            with self.subTest(alias=alias):
                legacy = catalog.resolve(alias)
                canonical = catalog.resolve(f"{legacy.name}@{legacy.version}")
                self.assertEqual(legacy.filename, filename)
                self.assertEqual(canonical.filename, filename)
                self.assertEqual(legacy.version, "1.0")

    def test_duplicate_schema_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            schema_id = "urn:vibe-dft-skills:contract:alpha:1.0"
            write_schema(directory, "alpha.schema.json", schema_id)
            write_schema(directory, "alpha-1.0.schema.json", schema_id)

            with self.assertRaises(validate_contract.CatalogError) as caught:
                validate_contract.load_catalog(directory)

        self.assertIn("duplicate $id", str(caught.exception))

    def test_meta_invalid_schema_and_filename_identity_mismatch_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            path = write_schema(
                directory,
                "alpha.schema.json",
                "urn:vibe-dft-skills:contract:alpha:1.0",
            )
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["type"] = "invented-json-type"
            path.write_text(json.dumps(schema), encoding="utf-8")
            with self.assertRaises(validate_contract.CatalogError) as caught:
                validate_contract.load_catalog(directory)
            self.assertIn("meta-validation failed", str(caught.exception))

        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            write_schema(
                directory,
                "alpha.schema.json",
                "urn:vibe-dft-skills:contract:beta:1.0",
            )
            with self.assertRaises(validate_contract.CatalogError) as caught:
                validate_contract.load_catalog(directory)
            self.assertIn("and the filename", str(caught.exception))

    def test_canonical_instance_identity_fields_are_required_and_consistent(self) -> None:
        mutations = {
            "missing-contract-property": lambda schema: schema["properties"].pop(
                "contract_name"
            ),
            "wrong-contract-const": lambda schema: schema["properties"][
                "contract_name"
            ].update(const="beta"),
            "contract-not-required": lambda schema: schema["required"].remove(
                "contract_name"
            ),
            "wrong-version-const": lambda schema: schema["properties"][
                "schema_version"
            ].update(const="2.0"),
            "version-not-required": lambda schema: schema["required"].remove(
                "schema_version"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label), tempfile.TemporaryDirectory() as raw_directory:
                directory = Path(raw_directory)
                path = write_schema(
                    directory,
                    "alpha.schema.json",
                    "urn:vibe-dft-skills:contract:alpha:1.0",
                )
                schema = json.loads(path.read_text(encoding="utf-8"))
                mutate(schema)
                path.write_text(json.dumps(schema), encoding="utf-8")

                with self.assertRaises(validate_contract.CatalogError) as caught:
                    validate_contract.load_catalog(directory)
                self.assertIn("self-description", str(caught.exception))

    def test_common_definitions_is_the_controlled_definition_library_exception(self) -> None:
        catalog = validate_contract.load_catalog(CONTRACTS)
        definitions = catalog.resolve("common-definitions")
        self.assertEqual(definitions.catalog_kind, "definition-library")
        self.assertFalse(definitions.is_legacy)
        self.assertNotIn("contract_name", definitions.schema.get("properties", {}))
        errors = validate_contract.validation_errors("common-definitions", {})
        self.assertTrue(any("not an instance-validation contract" in item for item in errors))

    def test_unresolved_urn_is_rejected_without_validation_input(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            write_schema(
                directory,
                "alpha.schema.json",
                "urn:vibe-dft-skills:contract:alpha:1.0",
                reference="urn:vibe-dft-skills:contract:missing:1.0#/$defs/value",
            )

            with self.assertRaises(validate_contract.CatalogError) as caught:
                validate_contract.load_catalog(directory)

        message = str(caught.exception)
        self.assertIn("unresolved reference", message)
        self.assertIn("urn:vibe-dft-skills:contract:missing:1.0", message)

    def test_ref_shaped_example_data_is_not_treated_as_a_schema_reference(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            path = write_schema(
                directory,
                "alpha.schema.json",
                "urn:vibe-dft-skills:contract:alpha:1.0",
            )
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["examples"] = [
                {"$ref": "https://example.invalid/literal-instance-value"}
            ]
            path.write_text(json.dumps(schema), encoding="utf-8")

            catalog = validate_contract.load_catalog(directory)

        self.assertEqual(catalog.resolve("alpha").name, "alpha")

    def test_non_allowlisted_http_id_and_remote_ref_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            write_schema(
                directory,
                "new-contract.schema.json",
                "https://example.invalid/vibe-dft-skills/new-contract.schema.json",
            )
            with self.assertRaises(validate_contract.CatalogError) as caught:
                validate_contract.load_catalog(directory)
            self.assertIn("canonical URN", str(caught.exception))

        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            write_schema(
                directory,
                "alpha.schema.json",
                "urn:vibe-dft-skills:contract:alpha:1.0",
                reference="https://example.invalid/not-in-the-local-catalog.schema.json",
            )
            with self.assertRaises(validate_contract.CatalogError) as caught:
                validate_contract.load_catalog(directory)
            self.assertIn("unresolved reference", str(caught.exception))

    def test_maintenance_cli_resolves_selectors_but_never_returns_active_assurance(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            instance = directory / "instance.json"
            instance.write_text("{}", encoding="utf-8")
            write_schema(
                directory,
                "run-manifest.schema.json",
                validate_contract.LEGACY_SCHEMA_IDS["run-manifest.schema.json"],
            )

            for selector in (
                "run",
                "run-manifest",
                "run-manifest@1.0",
                "urn:vibe-dft-skills:contract:run-manifest:1.0",
                validate_contract.LEGACY_SCHEMA_IDS["run-manifest.schema.json"],
            ):
                with self.subTest(selector=selector):
                    result = self.run_cli(directory, selector, instance)
                    self.assertEqual(result.returncode, 3, result.stderr)
                    self.assertIn("BLOCKED:", result.stdout)
                    self.assertIn("contract-only/no_positive_claim", result.stdout)

    def test_unknown_kind_and_unreadable_json_have_stable_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            write_schema(
                directory,
                "alpha.schema.json",
                "urn:vibe-dft-skills:contract:alpha:1.0",
            )
            valid_instance = directory / "valid.json"
            valid_instance.write_text("{}", encoding="utf-8")
            unknown = self.run_cli(directory, "missing", valid_instance)
            self.assertEqual(unknown.returncode, 2)
            self.assertIn("unknown contract kind 'missing'", unknown.stderr)
            self.assertNotIn("Traceback", unknown.stderr)

            unreadable = directory / "unreadable.json"
            unreadable.write_text("{", encoding="utf-8")
            malformed = self.run_cli(directory, "alpha", unreadable)
            self.assertEqual(malformed.returncode, 2)
            self.assertIn("STRICT_JSON_INVALID", malformed.stderr)
            self.assertIn("unreadable.json", malformed.stderr)
            self.assertNotIn("Traceback", malformed.stderr)

    def test_unreadable_schema_has_stable_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            (directory / "broken.schema.json").write_text("{", encoding="utf-8")
            instance = directory / "instance.json"
            instance.write_text("{}", encoding="utf-8")

            result = self.run_cli(directory, "broken", instance)

        self.assertEqual(result.returncode, 2)
        self.assertIn("STRICT_JSON_INVALID", result.stderr)
        self.assertIn("broken.schema.json", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_schema_catalog_rejects_ambiguous_and_resource_exhausting_json(self) -> None:
        cases = {
            "duplicate": b'{"$schema":"x","$schema":"y"}',
            "bom": b"\xef\xbb\xbf{}",
            "nan": b'{"value":NaN}',
            "infinity": b'{"value":Infinity}',
            "array": b"[]",
            "surrogate": b'{"value":"\\ud800"}',
            "deep": b"[" * 300 + b"0" + b"]" * 300,
            "huge-number": b'{"value":' + b"1" * 1025 + b"}",
        }
        for label, raw in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as raw_directory:
                directory = Path(raw_directory)
                (directory / "alpha.schema.json").write_bytes(raw)
                with self.assertRaises(validate_contract.CatalogError) as caught:
                    validate_contract.load_catalog(directory)
                message = str(caught.exception)
                self.assertIn("STRICT_JSON_INVALID", message)
                self.assertIn("alpha.schema.json", message)

    def test_new_calculation_contract_positive_negative_and_date_format(self) -> None:
        valid = calculation_envelope()
        self.assertEqual(
            validate_contract.validation_errors(
                "calculation-record-envelope",
                valid,
            ),
            [],
        )

        wrong_domain = copy.deepcopy(valid)
        wrong_domain["domain"] = "invented-dft-domain"
        self.assertTrue(
            validate_contract.validation_errors(
                "calculation-record-envelope",
                wrong_domain,
            )
        )

        bad_date = copy.deepcopy(valid)
        bad_date["producer"]["generated_utc"] = "2026-99-99"
        errors = validate_contract.validation_errors(
            "calculation-record-envelope",
            bad_date,
        )
        self.assertTrue(any("date-time" in error for error in errors), errors)

    def test_new_structure_contract_positive_and_negative(self) -> None:
        valid = periodic_snapshot()
        self.assertEqual(
            validate_contract.validation_errors("structure-snapshot", valid),
            [],
        )

        invalid = copy.deepcopy(valid)
        invalid["contract_name"] = "structure-guess"
        self.assertTrue(
            validate_contract.validation_errors("structure-snapshot", invalid)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
