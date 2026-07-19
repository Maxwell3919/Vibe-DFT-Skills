from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
VALIDATOR = TOOLS / "validate_bundle.py"
sys.path.insert(0, str(TOOLS))

import bundle_semantics  # noqa: E402
import registry_snapshot  # noqa: E402
import strict_json  # noqa: E402
import validate_contract  # noqa: E402
import validate_bundle  # noqa: E402


NOW = "2026-07-18T12:00:00Z"


def raw_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def producer() -> dict[str, Any]:
    return {
        "skill_id": "vibe-dft-skills",
        "skill_version": "1.0",
        "tool_id": "bundle-test-builder",
        "tool_version": "1.0",
        "generated_utc": NOW,
    }


def run_record(
    *,
    record_id: str = "run-test-001",
    status: str = "completed",
    scientific_acceptance: str = "not_assessed",
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "record_id": record_id,
        "code": "qe",
        "code_version": "7.5-test",
        "task_type": "single-point",
        "case_id": "case-test-001",
        "scientific_protocol_id": "protocol-test-001",
        "status": status,
        "scientific_acceptance": scientific_acceptance,
        "configuration": {},
        "metrics": {},
        "evidence": [],
        "limitations": ["Synthetic technical fixture; no scientific claim."],
        "provenance": {
            "collector": "bundle-test-builder",
            "collector_version": "1.0",
            "generated_utc": NOW,
        },
    }


def artifact_entry(
    raw: bytes,
    *,
    path: str = "artifact.bin",
    label: str = "artifact.bin",
    sensitivity: str = "public",
    redistribution: str = "redistributable",
) -> dict[str, Any]:
    return {
        "artifact_index": 0,
        "path": path,
        "label": label,
        "role": "technical-output",
        "media_type": "application/octet-stream",
        "format": "binary-data",
        "format_version": None,
        "availability": "present",
        "sha256": sha256(raw),
        "bytes": len(raw),
        "sensitivity": sensitivity,
        "redistribution": redistribution,
        "license_boundary": {
            "status": "not-applicable",
            "license_id": None,
            "redistribution_basis": (
                "runtime-only"
                if redistribution == "runtime-only"
                else "not-applicable"
            ),
            "limitations": [],
        },
        "supports_positive_claim": False,
    }


def manifest_for(
    raw_record: bytes,
    *,
    record_id: str = "run-test-001",
    bundle_mode: str = "portable-public",
    artifacts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "contract_name": "bundle-manifest",
        "schema_version": "1.0",
        "bundle_id": "bundle-test-001",
        "bundle_mode": bundle_mode,
        "created_utc": NOW,
        "records": [
            {
                "topological_index": 0,
                "path": "record.json",
                "label": "technical-run-record",
                "contract_name": "run-manifest",
                "schema_version": "1.0",
                "record_id": record_id,
                "sha256": sha256(raw_record),
            }
        ],
        "artifacts": artifacts or [],
        "privacy_policy": {
            "reject_credentials": True,
            "reject_private_identifiers": True,
            "reject_absolute_paths": True,
            "reject_path_traversal": True,
            "reject_restricted_payloads": True,
        },
        "producer": producer(),
        "limitations": ["Synthetic bundle fixture."],
    }


class BundleValidationTests(unittest.TestCase):
    def make_bundle(
        self,
        directory: Path,
        *,
        record: dict[str, Any] | None = None,
        raw_record: bytes | None = None,
        bundle_mode: str = "portable-public",
        artifact_raw: bytes | None = None,
        sensitivity: str = "public",
        redistribution: str = "redistributable",
    ) -> tuple[Path, Path]:
        selected_record = record or run_record()
        selected_raw = raw_record if raw_record is not None else raw_json(selected_record)
        directory.joinpath("record.json").write_bytes(selected_raw)
        artifacts: list[dict[str, Any]] = []
        if artifact_raw is not None:
            directory.joinpath("artifact.bin").write_bytes(artifact_raw)
            artifacts.append(
                artifact_entry(
                    artifact_raw,
                    sensitivity=sensitivity,
                    redistribution=redistribution,
                )
            )
        manifest = manifest_for(
            selected_raw,
            record_id=selected_record.get("record_id", "run-test-001"),
            bundle_mode=bundle_mode,
            artifacts=artifacts,
        )
        manifest_path = directory / "bundle.json"
        manifest_path.write_bytes(raw_json(manifest))
        return manifest_path, directory / "report.json"

    def run_bundle(
        self,
        manifest: Path,
        report: Path,
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(manifest),
                "--report",
                str(report),
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_bundle_contracts_are_cataloged_content_addressed_records(self) -> None:
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        manifest = catalog.resolve("bundle-manifest")
        report = catalog.resolve("bundle-validation-report")
        self.assertEqual(manifest.document_kind, "content-addressed-record")
        self.assertEqual(manifest.record_id_field, "bundle_id")
        self.assertEqual(report.document_kind, "content-addressed-record")
        self.assertEqual(report.record_id_field, "report_id")

    def test_catalog_trust_root_is_bound_to_the_schema_bytes_that_were_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            contracts = Path(raw_directory) / "contracts"
            contracts.mkdir()
            source = ROOT / "contracts" / "bundle-manifest.schema.json"
            copied = contracts / source.name
            original_raw = source.read_bytes()
            copied.write_bytes(original_raw)
            definitions = ROOT / "contracts" / "common-definitions-1.0.schema.json"
            contracts.joinpath(definitions.name).write_bytes(definitions.read_bytes())
            catalog = validate_contract.load_catalog(contracts)
            contract = catalog.resolve("bundle-manifest")

            copied.write_bytes(original_raw + b" ")
            trust_root = validate_bundle._catalog_trust_root(catalog, {})

        entry = next(
            item
            for item in trust_root["catalog_entries"]
            if item["schema_id"] == contract.schema_id
        )
        self.assertEqual(entry["sha256"], sha256(original_raw))
        self.assertNotEqual(entry["sha256"], sha256(original_raw + b" "))

    def test_registry_catalog_binding_rejects_a_different_schema_snapshot(self) -> None:
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        contract = catalog.resolve("bundle-manifest")
        registry = {
            "interfaces": {
                "bundle-manifest@1.0": {
                    "lifecycle": "active",
                    "schema_path": "contracts/bundle-manifest.schema.json",
                    "schema_sha256": sha256(contract.path.read_bytes() + b" "),
                }
            }
        }
        with self.assertRaises(validate_bundle.BundleSetupError) as caught:
            validate_bundle._assert_registry_catalog_binding(registry, catalog)
        self.assertIn("REGISTRY_CATALOG_SNAPSHOT_MISMATCH", str(caught.exception))

    def test_active_technical_run_bundle_passes_integrity_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(directory)
            result = self.run_bundle(manifest, report_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = strict_json.loads_object(report_path.read_bytes(), report_path.name)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(
            report["assurance"], "integrity-verified-no-positive-claim"
        )
        self.assertEqual(report["record_results"][0]["status"], "pass")
        self.assertEqual(report["summary"]["error_findings"], 0)
        self.assertEqual(report["human_trust"]["status"], "not-required")
        self.assertFalse(report["validator_execution"]["dynamic_module_selection"])

    def test_exact_raw_bytes_hash_detects_whitespace_change(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(directory)
            directory.joinpath("record.json").write_bytes(
                directory.joinpath("record.json").read_bytes() + b" "
            )
            result = self.run_bundle(manifest, report_path)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(report["status"], "fail")
        self.assertIn(
            "RECORD_RAW_SHA256_MISMATCH",
            {item["code"] for item in report["findings"]},
        )

    def test_strict_record_json_rejects_duplicate_bom_nonfinite_nonobject_and_surrogate(self) -> None:
        cases = {
            "nested-duplicate": b'{"record_id":"run-test-001","nested":{"x":1,"x":2}}',
            "bom": b"\xef\xbb\xbf{}",
            "nan": b'{"record_id":"run-test-001","value":NaN}',
            "infinity": b'{"record_id":"run-test-001","value":Infinity}',
            "array": b"[]",
            "lone-surrogate": b'{"record_id":"run-test-001","value":"\\ud800"}',
        }
        for label, raw in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as raw_directory:
                directory = Path(raw_directory)
                manifest, report_path = self.make_bundle(directory, raw_record=raw)
                result = self.run_bundle(manifest, report_path)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                report = json.loads(report_path.read_text(encoding="utf-8"))
                self.assertIn(
                    "RECORD_JSON_INVALID",
                    {item["code"] for item in report["findings"]},
                )

    def test_unlisted_symlink_and_hardlink_entries_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(directory)
            directory.joinpath("extra.txt").write_text("extra", encoding="utf-8")
            result = self.run_bundle(manifest, report_path)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("UNLISTED_BUNDLE_ENTRY", {x["code"] for x in report["findings"]})

        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(directory)
            target = directory / "target.json"
            directory.joinpath("record.json").replace(target)
            directory.joinpath("record.json").symlink_to(target.name)
            result = self.run_bundle(manifest, report_path)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("SYMLINK_REJECTED", {x["code"] for x in report["findings"]})

        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(directory)
            alias = directory / "alias.json"
            os.link(directory / "record.json", alias)
            result = self.run_bundle(manifest, report_path)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            codes = {x["code"] for x in report["findings"]}
            self.assertTrue(
                {"HARDLINK_ALIAS_REJECTED", "UNLISTED_BUNDLE_ENTRY"}.intersection(codes)
            )

    def test_portable_rejects_private_local_allows_it_and_restricted_payload_never_passes(self) -> None:
        private_raw = b"private scientific output\n"
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(
                directory,
                artifact_raw=private_raw,
                sensitivity="private",
                redistribution="runtime-only",
            )
            result = self.run_bundle(manifest, report_path)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("PRIVATE_ARTIFACT_INCLUDED", {x["code"] for x in report["findings"]})

        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(
                directory,
                bundle_mode="local-validation",
                artifact_raw=private_raw,
                sensitivity="private",
                redistribution="runtime-only",
            )
            refused = self.run_bundle(manifest, report_path)
            self.assertEqual(refused.returncode, 2)
            self.assertIn("LOCAL_VALIDATION_AUTHORIZATION_REQUIRED", refused.stderr)
            allowed = self.run_bundle(
                manifest, report_path, "--allow-local-validation"
            )
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                report["distribution_boundary"],
                "local-only-no-external-publication",
            )

        restricted_raw = b"TITEL  = PAW_PBE restricted payload\n"
        for mode, extra in (
            ("portable-public", ()),
            ("local-validation", ("--allow-local-validation",)),
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw_directory:
                directory = Path(raw_directory)
                manifest, report_path = self.make_bundle(
                    directory,
                    bundle_mode=mode,
                    artifact_raw=restricted_raw,
                )
                result = self.run_bundle(manifest, report_path, *extra)
                self.assertEqual(result.returncode, 2, result.stderr)
                report = json.loads(report_path.read_text(encoding="utf-8"))
                self.assertIn(
                    "RESTRICTED_DFT_PAYLOAD_INCLUDED",
                    {x["code"] for x in report["findings"]},
                )

    def test_accepted_legacy_run_is_invalid_not_scientifically_authenticated(self) -> None:
        record = run_record(status="completed", scientific_acceptance="accepted")
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(directory, record=record)
            result = self.run_bundle(manifest, report_path)
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["assurance"], "invalid")
        self.assertIn(
            "RECORD_SCHEMA_INVALID",
            {x["code"] for x in report["findings"]},
        )

    def test_report_identity_does_not_collide_across_validation_runs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, first_path = self.make_bundle(directory)
            first = self.run_bundle(manifest, first_path)
            self.assertEqual(first.returncode, 0, first.stderr)
            first_report = json.loads(first_path.read_text(encoding="utf-8"))
            second = self.run_bundle(manifest, first_path, "--force")
            self.assertEqual(second.returncode, 0, second.stderr)
            second_report = json.loads(first_path.read_text(encoding="utf-8"))

        self.assertNotEqual(first_report["validation_run_id"], second_report["validation_run_id"])
        self.assertNotEqual(first_report["report_id"], second_report["report_id"])

    def test_report_schema_rejects_inconsistent_positive_trust_and_summary_states(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(directory)
            result = self.run_bundle(manifest, report_path)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = strict_json.loads_object(report_path.read_bytes(), report_path.name)
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        contract = catalog.resolve("bundle-validation-report")
        self.assertEqual(
            validate_bundle._schema_error_locations(contract, report, catalog), []
        )

        blocked_summary = copy.deepcopy(report)
        blocked_summary["summary"]["blocked_checks"] = 1
        self.assertTrue(
            validate_bundle._schema_error_locations(
                contract, blocked_summary, catalog
            )
        )
        external_human = copy.deepcopy(report)
        external_human["human_trust"].update(
            status="requires-external-trust",
            human_authenticity="not-established",
            required_decision_ids=["decision-test-001"],
        )
        self.assertTrue(
            validate_bundle._schema_error_locations(
                contract, external_human, catalog
            )
        )
        invented_trust = copy.deepcopy(report)
        invented_trust["external_source_trust"]["status"] = "established"
        self.assertTrue(
            validate_bundle._schema_error_locations(
                contract, invented_trust, catalog
            )
        )

    def test_noncanonical_trust_root_requires_maintenance_and_never_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            manifest, report_path = self.make_bundle(directory)
            copied_registry = directory / "registry.yaml"
            copied_registry.write_bytes(
                (ROOT / "registry" / "interface-registry.yaml").read_bytes()
            )
            refused = self.run_bundle(
                manifest,
                report_path,
                "--interface-registry",
                str(copied_registry),
            )
            self.assertEqual(refused.returncode, 2)
            self.assertIn("UNTRUSTED_VALIDATOR_TRUST_ROOT", refused.stderr)

        with tempfile.TemporaryDirectory() as raw_directory:
            outer = Path(raw_directory)
            bundle_directory = outer / "bundle"
            bundle_directory.mkdir()
            manifest, report_path = self.make_bundle(bundle_directory)
            copied_registry = outer / "registry.yaml"
            copied_registry.write_bytes(
                (ROOT / "registry" / "interface-registry.yaml").read_bytes()
            )
            result = self.run_bundle(
                manifest,
                report_path,
                "--interface-registry",
                str(copied_registry),
                "--maintenance",
            )
            self.assertEqual(result.returncode, 3, result.stderr)
            report = strict_json.loads_object(report_path.read_bytes(), report_path.name)
            self.assertEqual(report["status"], "blocked")
            self.assertIn(
                "UNTRUSTED_VALIDATOR_TRUST_ROOT",
                {item["code"] for item in report["findings"]},
            )

    def test_dispatcher_context_identity_and_defect_paths_fail_closed(self) -> None:
        record_view = {
            "contract_name": "run-manifest",
            "schema_version": "1.0",
            "record_id": "run-test-001",
            "index": 0,
            "data": run_record(),
            "raw_sha256": "a" * 64,
            "lifecycle": "active",
            "integrity_verified_active": True,
        }
        identity = ("run-manifest", "1.0", "run-test-001")
        context = {
            "current_record": record_view,
            "current_record_index": 0,
            "records_by_identity": {identity: record_view},
            "artifacts_by_label": {},
            "core_checks": {
                "record-reference-dag": {"status": "pass", "finding_codes": []},
                "record-reference-integrity": {"status": "pass", "finding_codes": []},
                "artifact-integrity": {"status": "pass", "finding_codes": []},
                "privacy-boundary": {"status": "pass", "finding_codes": []},
            },
            "registry_snapshots": {},
        }
        result = bundle_semantics.evaluate_advertised_obligations(
            ["UNKNOWN_DOMAIN_OBLIGATION"], context
        )
        self.assertEqual(result[0]["status"], "blocked")
        self.assertIn("OBLIGATION_HANDLER_UNAVAILABLE", result[0]["finding_codes"])

        duplicate = bundle_semantics.evaluate_advertised_obligations(
            ["UNKNOWN_DOMAIN_OBLIGATION", "UNKNOWN_DOMAIN_OBLIGATION"], context
        )
        self.assertIn("DUPLICATE_ADVERTISED_OBLIGATION", duplicate[0]["finding_codes"])

        mixed_invalid = bundle_semantics.evaluate_advertised_obligations(
            ["UNKNOWN_DOMAIN_OBLIGATION", None], context
        )
        self.assertTrue(all(item["status"] == "blocked" for item in mixed_invalid))
        self.assertTrue(
            all("INVALID_ADVERTISED_OBLIGATION" in item["finding_codes"] for item in mixed_invalid)
        )

        with mock.patch.object(
            bundle_semantics.importlib,
            "import_module",
            side_effect=SyntaxError("broken trusted module"),
        ):
            self.assertIsNone(bundle_semantics.builtin_evaluator("run-manifest"))

        wrong_version = copy.deepcopy(context)
        wrong_version["records_by_identity"] = {
            ("run-manifest", "2.0", "run-test-001"): record_view
        }
        with self.assertRaises(ValueError):
            bundle_semantics.read_only_context(wrong_version)

    def test_dispatcher_enforces_exact_one_owner_and_frozen_artifact_seam(self) -> None:
        record_view = {
            "contract_name": "run-manifest",
            "schema_version": "1.0",
            "record_id": "run-test-001",
            "index": 0,
            "data": run_record(),
            "raw_sha256": "a" * 64,
            "lifecycle": "active",
            "integrity_verified_active": True,
        }
        artifact_view = {
            "label": "output.dat",
            "index": 0,
            "metadata": {
                "label": "output.dat",
                "availability": "present",
                "sha256": "b" * 64,
                "bytes": 4,
            },
            "raw_sha256": "b" * 64,
            "bytes": 4,
            "integrity_verified": True,
            "parser_observations": (),
        }
        identity = ("run-manifest", "1.0", "run-test-001")
        context = {
            "current_record": record_view,
            "current_record_index": 0,
            "records_by_identity": {identity: record_view},
            "artifacts_by_label": {"output.dat": artifact_view},
            "core_checks": {},
            "registry_snapshots": {},
        }
        observed: dict[str, object] = {}

        def evaluator(obligations: object, frozen: object) -> list[dict[str, object]]:
            assert isinstance(frozen, dict) or hasattr(frozen, "keys")
            artifact = frozen["artifacts_by_label"]["output.dat"]
            observed["fields"] = set(artifact)
            observed["metadata_fields"] = set(artifact["metadata"])
            observed["parser_observations"] = artifact["parser_observations"]
            return [
                {
                    "obligation_id": "TEST_DOMAIN_OBLIGATION",
                    "status": "pass",
                    "finding_codes": [],
                    "location": "test:domain",
                    "message": "Strict frozen context observed.",
                    "handler_id": "test-domain-v1",
                }
            ]

        result = bundle_semantics.evaluate_advertised_obligations(
            ["TEST_DOMAIN_OBLIGATION"], context, evaluator=evaluator
        )
        self.assertEqual(result[0]["status"], "pass")
        self.assertEqual(
            observed["fields"],
            {
                "label",
                "index",
                "metadata",
                "raw_sha256",
                "bytes",
                "integrity_verified",
                "parser_observations",
            },
        )
        self.assertNotIn("path", observed["metadata_fields"])
        self.assertEqual(observed["parser_observations"], ())

        malformed_status_codes = bundle_semantics.evaluate_advertised_obligations(
            ["TEST_DOMAIN_OBLIGATION"],
            context,
            evaluator=lambda obligations, frozen: [
                {
                    "obligation_id": "TEST_DOMAIN_OBLIGATION",
                    "status": "pass",
                    "finding_codes": ["PASS_MUST_NOT_CARRY_FINDINGS"],
                    "location": "test:domain",
                    "message": "Malformed trusted result.",
                    "handler_id": "test-domain-v1",
                }
            ],
        )
        self.assertEqual(malformed_status_codes[0]["status"], "blocked")
        self.assertIn(
            "DOMAIN_EVALUATOR_RESULT_INVALID",
            malformed_status_codes[0]["finding_codes"],
        )

        poisoned = copy.deepcopy(context)
        poisoned["artifacts_by_label"]["output.dat"]["parser_observations"] = (
            {
                "parser_id": "trusted-parser",
                "parser_version": "1.0",
                "parser_component_sha256": "c" * 64,
                "source_raw_sha256": "d" * 64,
                "status": "pass",
                "observations": {},
            },
        )
        never_called = mock.Mock(return_value=[])
        with self.assertRaises(ValueError):
            bundle_semantics.evaluate_advertised_obligations(
                ["TEST_DOMAIN_OBLIGATION"], poisoned, evaluator=never_called
            )
        never_called.assert_not_called()

        modules = {
            name: mock.Mock(CONTRACT_NAMES=("run-manifest",), evaluate=mock.Mock())
            for name in bundle_semantics.BUILTIN_DOMAIN_MODULES
        }
        with mock.patch.object(
            bundle_semantics.importlib,
            "import_module",
            side_effect=lambda name: modules[name],
        ):
            self.assertIsNone(bundle_semantics.builtin_evaluator("run-manifest"))
            self.assertTrue(bundle_semantics.builtin_ownership_errors())

        for contract_name, obligation_id in (
            (
                "artifact-manifest",
                "LEGACY_ARTIFACT_OUTPUT_ARTIFACT_HASH_RESOLVES",
            ),
            (
                "normalized-dataset",
                "LEGACY_DATASET_SOURCE_ARTIFACT_HASH_RESOLVES",
            ),
            (
                "tool-execution",
                "LEGACY_TOOL_EXECUTION_FILE_ARTIFACT_HASH_RESOLVES",
            ),
        ):
            with self.subTest(domain_owned_obligation=obligation_id):
                domain_record = copy.deepcopy(record_view)
                domain_record["contract_name"] = contract_name
                domain_record["record_id"] = f"{contract_name}-test-001"
                domain_record["data"] = {}
                domain_identity = (
                    contract_name,
                    "1.0",
                    domain_record["record_id"],
                )
                domain_context = copy.deepcopy(context)
                domain_context["current_record"] = domain_record
                domain_context["records_by_identity"] = {
                    domain_identity: domain_record
                }
                domain_result = bundle_semantics.evaluate_advertised_obligations(
                    [obligation_id],
                    domain_context,
                    evaluator=bundle_semantics.builtin_evaluator(contract_name),
                )[0]
                self.assertTrue(
                    domain_result["handler_id"].startswith(
                        "bundle-semantics-legacy-v1."
                    )
                )

    def test_reference_graph_and_file_reference_core_fail_closed(self) -> None:
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        run_contract = catalog.resolve("run-manifest")

        def loaded(
            index: int,
            record_id: str,
            raw_hash: str,
            data: dict[str, Any],
        ) -> validate_bundle.LoadedRecord:
            return validate_bundle.LoadedRecord(
                index=index,
                entry={
                    "topological_index": index,
                    "path": f"record-{index}.json",
                    "label": f"record-{index}",
                    "contract_name": "run-manifest",
                    "schema_version": "1.0",
                    "record_id": record_id,
                    "sha256": raw_hash,
                },
                raw=b"{}",
                actual_sha256=raw_hash,
                data=data,
                contract=run_contract,
                lifecycle="active",
            )

        self_hash = "1" * 64
        self_ref = {
            "contract_name": "run-manifest",
            "schema_version": "1.0",
            "record_id": "run-self",
            "sha256": self_hash,
            "role": "parent",
        }
        source = loaded(0, "run-self", self_hash, {"parent": self_ref})
        findings: list[validate_bundle.Finding] = []
        validate_bundle._record_reference_results([source], findings, catalog)
        codes = {item.code for item in findings}
        self.assertIn("RECORD_REF_SELF_REFERENCE", codes)
        self.assertIn("RECORD_REF_CYCLE", codes)

        unknown_ref = {
            **self_ref,
            "contract_name": "unknown-contract",
            "record_id": "missing",
        }
        unknown = loaded(0, "run-unknown", "2" * 64, {"parent": unknown_ref})
        findings = []
        validate_bundle._record_reference_results([unknown], findings, catalog)
        self.assertIn(
            "RECORD_REF_TARGET_UNKNOWN_CONTRACT",
            {item.code for item in findings},
        )

        projection_ref = {
            **self_ref,
            "contract_name": "validation-report",
            "record_id": "report-missing",
        }
        projection = loaded(0, "run-projection", "3" * 64, {"parent": projection_ref})
        findings = []
        validate_bundle._record_reference_results([projection], findings, catalog)
        self.assertIn(
            "RECORD_REF_TARGET_NOT_CONTENT_ADDRESSED",
            {item.code for item in findings},
        )

        file_ref = {
            "role": "technical-output",
            "label": "external.dat",
            "media_type": "application/octet-stream",
            "format": "binary-data",
            "format_version": None,
            "availability": "external",
            "sha256": "4" * 64,
            "bytes": 12,
            "sensitivity": "private",
            "redistribution": "runtime-only",
        }
        record = loaded(0, "run-file-ref", "5" * 64, {"file": file_ref})
        artifact = validate_bundle.LoadedArtifact(
            0,
            {
                "artifact_index": 0,
                "path": None,
                **file_ref,
                "license_boundary": {
                    "status": "unknown",
                    "license_id": None,
                    "redistribution_basis": "runtime-only",
                    "limitations": [],
                },
                "supports_positive_claim": False,
            },
        )
        findings = []
        results = validate_bundle._file_reference_results([record], [artifact], findings)
        self.assertEqual(results[0]["status"], "pass")
        self.assertEqual(findings, [])

    def test_official_source_external_trust_uses_exact_canonical_snapshot_pin(self) -> None:
        version_scope = {
            "scope": "exact",
            "exact_version": "2026.2",
            "minimum_version": None,
            "maximum_version": None,
            "release_series": None,
        }
        content_hash = "6" * 64
        data = {
            "authority": {
                "authority_registry_id": "cp2k-official-manual",
                "canonical_url": "https://manual.cp2k.org/cp2k-2026_2-branch/CP2K_INPUT.html",
            },
            "version_scope": version_scope,
            "content": {
                "status": "embedded-open",
                "identity_mode": "pinned-canonical-snapshot",
                "raw_sha256": content_hash,
                "bytes": 128,
                "pinned_source_ref": {
                    "authority_registry_id": "cp2k-official-manual",
                    "snapshot_id": "cp2k-manual-2026-2",
                    "source_id": "cp2k-input",
                },
                "trust_state": "canonical-snapshot-verified",
            },
            "license": {
                "status": "known-open",
                "identifier": "GPL-2.0-or-later",
                "terms_url": "https://github.com/cp2k/cp2k/blob/master/LICENSE",
                "redistribution": "redistributable",
            },
            "claim_ceiling": "documented_behavior_only",
        }
        policy = {
            "cp2k-official-manual": {
                "canonical_snapshot": {
                    "snapshot_id": "cp2k-manual-2026-2",
                    "integrity_verified": True,
                    "sources_by_id": {
                        "cp2k-input": {
                            "canonical_url": data["authority"]["canonical_url"],
                            "version_scope": version_scope,
                            "raw_sha256": content_hash,
                            "bytes": 128,
                        }
                    },
                },
                "license_status": "known-open",
                "license_identifier": "GPL-2.0-or-later",
                "license_terms_urls": [
                    "https://github.com/cp2k/cp2k/blob/master/LICENSE"
                ],
                "redistribution": ["redistributable"],
            }
        }
        record = validate_bundle.LoadedRecord(
            0,
            {
                "contract_name": "official-source-record",
                "schema_version": "1.0",
                "record_id": "source-cp2k-input",
            },
            data=data,
        )
        self.assertFalse(
            validate_bundle._source_requires_external_trust(record, policy)
        )

        for field, value in (
            ("raw_sha256", "7" * 64),
            ("bytes", 129),
        ):
            with self.subTest(field=field):
                mutated = copy.deepcopy(record)
                mutated.data["content"][field] = value
                self.assertTrue(
                    validate_bundle._source_requires_external_trust(mutated, policy)
                )
        mutated = copy.deepcopy(record)
        mutated.data["content"]["pinned_source_ref"]["source_id"] = "unknown"
        self.assertTrue(validate_bundle._source_requires_external_trust(mutated, policy))
        wrong_license = copy.deepcopy(record)
        wrong_license.data["license"]["identifier"] = "MIT"
        self.assertTrue(
            validate_bundle._source_requires_external_trust(wrong_license, policy)
        )
        restricted = copy.deepcopy(record)
        restricted.data["license"]["status"] = "known-restricted"
        restricted.data["license"]["redistribution"] = "restricted"
        self.assertTrue(validate_bundle._source_requires_external_trust(restricted, policy))

    def test_active_interface_set_has_a_production_validation_path(self) -> None:
        snapshot = registry_snapshot.load_registry_snapshot(ROOT, validate_sources=False)
        catalog = validate_contract.load_catalog(ROOT / "contracts")
        active = {
            interface_id: specification
            for interface_id, specification in snapshot.interfaces["interfaces"].items()
            if specification["lifecycle"] == "active"
        }
        self.assertEqual(len(active), 26)
        self.assertEqual(bundle_semantics.builtin_ownership_errors(), [])
        special_paths = {
            "agent-action-envelope@1.0": TOOLS / "validate_agent_answer.py",
            "bundle-manifest@1.0": VALIDATOR,
            "bundle-validation-report@1.0": VALIDATOR,
        }
        for interface_id, specification in active.items():
            with self.subTest(interface=interface_id):
                name, version = interface_id.rsplit("@", 1)
                contract = catalog.resolve(interface_id)
                if interface_id in special_paths:
                    self.assertTrue(special_paths[interface_id].is_file())
                    self.assertEqual(
                        specification.get("classification", {}).get("routing_scope"),
                        "governance-only",
                    )
                    continue
                self.assertTrue(contract.is_record_ref_target)
                self.assertTrue(validate_bundle._contract_obligation_ids(contract))
                self.assertIsNotNone(bundle_semantics.builtin_evaluator(name))

        for interface_id in (
            "activation-checklist@1.0",
            "promotion-delta@1.0",
            "task-maturity@1.0",
            "validation-report@1.0",
        ):
            self.assertEqual(
                snapshot.interfaces["interfaces"][interface_id]["lifecycle"],
                "planned",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
