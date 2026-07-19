from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bundle_semantics_legacy  # noqa: E402
import bundle_semantics  # noqa: E402
import validate_contract  # noqa: E402


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
TWO_HASH = "2" * 64
EMPTY_HASH = hashlib.sha256(b"").hexdigest()
NACL_CIF = """data_NaCl
_symmetry_space_group_name_H-M 'P 1'
_symmetry_Int_Tables_number 1
_cell_length_a 5.6402
_cell_length_b 5.6402
_cell_length_c 5.6402
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
loop_
_space_group_symop_operation_xyz
'x, y, z'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
Na1 Na 0 0 0 1
Cl1 Cl 0.5 0.5 0.5 1
"""
HIGH_PRECISION_CIF = NACL_CIF.replace(
    "5.6402", "5.6402123456"
).replace(
    "Na1 Na 0 0 0 1",
    "Na1 Na 0.99999999996 -0.00000000004 1.20000000004 1",
).replace(
    "0.5 0.5 0.5", "0.5123456789 0.4987654321 0.5000000123"
)


EXPECTED_OBLIGATIONS = {
    "artifact-manifest": {
        "LEGACY_ARTIFACT_STATUS_CHECK_CONSISTENT",
        "LEGACY_ARTIFACT_OUTPUT_ARTIFACT_HASH_RESOLVES",
        "LEGACY_ARTIFACT_SOURCE_LINEAGE_PREEXISTS",
        "LEGACY_ARTIFACT_TECHNICAL_CLAIM_CEILING",
        "LEGACY_ARTIFACT_PRIVACY_SAFE",
    },
    "normalized-dataset": {
        "LEGACY_DATASET_VALIDATION_CHECK_CONSISTENT",
        "LEGACY_DATASET_SOURCE_ARTIFACT_HASH_RESOLVES",
        "LEGACY_DATASET_OUTPUT_ARTIFACT_HASH_RESOLVES",
        "LEGACY_DATASET_TOOL_LINEAGE_PREEXISTS",
        "LEGACY_DATASET_MATURITY_EVIDENCE_CONSISTENT",
        "LEGACY_DATASET_NUMERICAL_CANDIDATE_CEILING",
        "LEGACY_DATASET_PRIVACY_SAFE",
    },
    "postprocess-plan": {
        "LEGACY_PLAN_STATUS_READINESS_CONSISTENT",
        "LEGACY_PLAN_SOURCE_ARTIFACT_RESOLVES",
        "LEGACY_PLAN_STEP_GRAPH_CONSISTENT",
        "LEGACY_PLAN_NO_POSITIVE_CLAIM_CEILING",
        "LEGACY_PLAN_PRIVACY_SAFE",
    },
    "tool-execution": {
        "LEGACY_TOOL_EXECUTION_PLAN_LINEAGE_PREEXISTS",
        "LEGACY_TOOL_EXECUTION_STATUS_RUNTIME_CONSISTENT",
        "LEGACY_TOOL_EXECUTION_FILE_ARTIFACT_HASH_RESOLVES",
        "LEGACY_TOOL_EXECUTION_PLAN_STEP_CONSISTENT",
        "LEGACY_TOOL_EXECUTION_TECHNICAL_CLAIM_CEILING",
        "LEGACY_TOOL_EXECUTION_PRIVACY_SAFE",
    },
    "structure-manifest": {
        "LEGACY_STRUCTURE_STATUS_CHECK_CONSISTENT",
        "LEGACY_STRUCTURE_SOURCE_ARTIFACT_HASH_RESOLVES",
        "LEGACY_STRUCTURE_SOURCE_IDENTITY_CONSISTENT",
        "LEGACY_STRUCTURE_SITE_COMPOSITION_CONSISTENT",
        "LEGACY_STRUCTURE_COORDINATE_CELL_CONSISTENT",
        "LEGACY_STRUCTURE_NEIGHBOR_SUMMARY_CONSISTENT",
        "LEGACY_STRUCTURE_BOND_MATCH_CONSISTENT",
        "LEGACY_STRUCTURE_VIEW_ARTIFACTS_RESOLVE",
        "LEGACY_STRUCTURE_TRANSFORMATION_LINEAGE_PREEXISTS",
        "LEGACY_STRUCTURE_NUMERICAL_CANDIDATE_CEILING",
        "LEGACY_STRUCTURE_PRIVACY_SAFE",
    },
}

NON_CORE_OBLIGATIONS = {
    name: {item for item in obligations if not item.endswith("_PRIVACY_SAFE")}
    for name, obligations in EXPECTED_OBLIGATIONS.items()
}


def schema_obligations(contract_name: str) -> set[str]:
    schema = json.loads(
        ROOT.joinpath("contracts", f"{contract_name}.schema.json").read_text(
            encoding="utf-8"
        )
    )
    result = set()
    for item in schema.get("x-vibe-semantic-obligations", []):
        result.add(item if isinstance(item, str) else item["finding_id"])
    return result


def record_view(
    contract_name: str,
    record_id: str,
    data: dict,
    *,
    index: int,
    verified: bool = True,
) -> dict:
    return {
        "contract_name": contract_name,
        "schema_version": "1.0",
        "record_id": record_id,
        "index": index,
        "data": data,
        "raw_sha256": hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "lifecycle": "active",
        "integrity_verified_active": verified,
    }


def artifact_view(
    label: str,
    digest: str,
    size: int,
    *,
    index: int = 0,
    verified: bool = True,
) -> dict:
    return {
        "label": label,
        "index": index,
        "metadata": {
            "label": label,
            "availability": "present",
            "sha256": digest,
            "bytes": size,
            "supports_positive_claim": False,
        },
        "raw_sha256": digest,
        "bytes": size,
        "integrity_verified": verified,
        "parser_observations": (),
    }


def context_for(
    contract_name: str,
    record_id: str,
    data: dict,
    *,
    index: int,
    parents: list[dict] | None = None,
    artifacts: dict[str, dict] | None = None,
) -> dict:
    current = record_view(contract_name, record_id, data, index=index)
    records = {
        (item["contract_name"], item["schema_version"], item["record_id"]): item
        for item in parents or []
    }
    records[(contract_name, "1.0", record_id)] = current
    return {
        "current_record": current,
        "current_record_index": index,
        "records_by_identity": records,
        "artifacts_by_label": artifacts or {},
        "core_checks": {
            "privacy-boundary": {"status": "pass", "finding_codes": []},
            "artifact-integrity": {"status": "pass", "finding_codes": []},
            "record-reference-dag": {"status": "pass", "finding_codes": []},
            "record-reference-integrity": {"status": "pass", "finding_codes": []},
        },
        "registry_snapshots": {},
    }


def evaluate(context: dict) -> dict[str, dict]:
    contract_name = context["current_record"]["contract_name"]
    results = bundle_semantics_legacy.evaluate(
        sorted(NON_CORE_OBLIGATIONS[contract_name]), context
    )
    return {result["obligation_id"]: result for result in results}


def statuses(context: dict) -> dict[str, str]:
    return {key: value["status"] for key, value in evaluate(context).items()}


def run_manifest(record_id: str = "run-example-001") -> dict:
    return {
        "schema_version": "1.0",
        "record_id": record_id,
        "code": "qe",
        "code_version": "7.5",
        "task_type": "bands",
        "case_id": "case-anonymous",
        "scientific_protocol_id": "protocol-001",
        "status": "completed",
        "scientific_acceptance": "not_assessed",
        "configuration": {},
        "metrics": {},
        "evidence": [],
        "limitations": ["Scientific acceptance is not assessed."],
        "provenance": {
            "collector": "test",
            "collector_version": "1",
            "generated_utc": "2026-07-18T00:00:00Z",
        },
    }


def artifact_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "artifact_id": "artifact-example-001",
        "source_run_ids": ["run-example-001"],
        "code": "qe",
        "artifact_type": "bands-table",
        "status": "complete",
        "data_files": [
            {"role": "table", "path": "bands.csv", "sha256": TWO_HASH, "bytes": 11}
        ],
        "figure_files": [],
        "validation": {"status": "pass", "checks": ["finite-energy"]},
        "claim_boundary": ["Technical postprocessing only; scientific acceptance is not assessed."],
        "provenance": {
            "tool": "test",
            "tool_version": "1",
            "generated_utc": "2026-07-18T00:00:00Z",
            "command": ["test"],
        },
    }


def dataset_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "dataset_id": "dataset-example-001",
        "observable": "bands",
        "code": "qe",
        "maturity": "real-artifact-validated",
        "representation": "table",
        "source_files": [
            {
                "role": "bands-output",
                "label": "bands.dat",
                "bytes": 7,
                "sha256": ONE_HASH,
                "hash_status": "present",
            }
        ],
        "dimensions": {"rows": 1},
        "columns": [
            {"name": "energy", "dtype": "float", "unit": "eV", "role": "energy"}
        ],
        "data_files": [
            {
                "role": "table",
                "path": "bands.csv",
                "format": "csv",
                "sha256": TWO_HASH,
                "bytes": 11,
            }
        ],
        "transformations": [],
        "validation": {
            "status": "pass",
            "checks": [{"id": "finite", "status": "pass", "message": "finite"}],
        },
        "limitations": ["Numerical candidate only; scientific acceptance is not assessed."],
        "provenance": {
            "producer": "test",
            "producer_version": "1",
            "generated_utc": "2026-07-18T00:00:00Z",
            "tool_execution_ids": [],
        },
    }


def plan_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "plan_id": "plan-example-001",
        "observable": "bands",
        "code": "qe",
        "status": "planned",
        "source_root_label": "source-run",
        "output_root_label": "derived-output",
        "source_files": [
            {"role": "bands-output", "path": "bands.dat", "required": True, "present": True}
        ],
        "parameters": {},
        "backend": {
            "id": "qe-bands",
            "kind": "builtin-python",
            "maturity": "real-artifact-validated",
            "available": True,
        },
        "steps": [
            {
                "step_id": "normalize",
                "operation": "normalize",
                "adapter": "qe-bands",
                "action": "python",
                "command": ["python3", "-B", "normalize.py"],
                "inputs": ["bands.dat"],
                "outputs": ["bands.csv"],
                "timeout_s": 60,
                "overwrite": False,
            }
        ],
        "blockers": [],
        "provenance": {
            "planner": "test",
            "planner_version": "1",
            "generated_utc": "2026-07-18T00:00:00Z",
        },
    }


def execution_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "execution_id": "execution-example-001",
        "plan_id": "plan-example-001",
        "step_id": "normalize",
        "backend": "qe-bands",
        "command": ["python3", "-B", "normalize.py"],
        "working_directory_label": "work-anonymous",
        "dry_run": False,
        "status": "succeeded",
        "started_utc": "2026-07-18T00:00:00Z",
        "finished_utc": "2026-07-18T00:00:01Z",
        "duration_s": 1.0,
        "return_code": 0,
        "inputs": [
            {"role": "input", "path": "bands.dat", "sha256": ONE_HASH, "bytes": 7}
        ],
        "outputs": [
            {"role": "output", "path": "bands.csv", "sha256": TWO_HASH, "bytes": 11}
        ],
        "stdout": {"path": "execution.stdout", "sha256": EMPTY_HASH, "bytes": 0},
        "stderr": {"path": "execution.stderr", "sha256": EMPTY_HASH, "bytes": 0},
        "limitations": ["Tool completion is not scientific acceptance."],
    }


def postprocess_artifacts() -> dict[str, dict]:
    return {
        "bands.dat": artifact_view("bands.dat", ONE_HASH, 7, index=0),
        "bands.csv": artifact_view("bands.csv", TWO_HASH, 11, index=1),
        "execution.stdout": artifact_view("execution.stdout", EMPTY_HASH, 0, index=2),
        "execution.stderr": artifact_view("execution.stderr", EMPTY_HASH, 0, index=3),
    }


class LegacyContractMetadataTests(unittest.TestCase):
    def test_owned_contract_set_is_disjoint_from_run_campaign_owner(self) -> None:
        self.assertEqual(
            set(bundle_semantics_legacy.CONTRACT_NAMES), set(EXPECTED_OBLIGATIONS)
        )
        self.assertFalse(
            {"run-manifest", "campaign-record", "recommendation-record"}.intersection(
                bundle_semantics_legacy.CONTRACT_NAMES
            )
        )

    def test_every_owned_schema_advertises_exact_machine_obligations(self) -> None:
        for contract_name, expected in EXPECTED_OBLIGATIONS.items():
            with self.subTest(contract_name=contract_name):
                self.assertEqual(schema_obligations(contract_name), expected)

    def test_authority_boundaries_are_explicit_and_cannot_accept_science(self) -> None:
        expected_ceiling = {
            "artifact-manifest": "numerical_candidate_only",
            "normalized-dataset": "numerical_candidate_only",
            "postprocess-plan": "no_positive_claim",
            "tool-execution": "technical_run_gates_only",
            "structure-manifest": "numerical_candidate_only",
        }
        for contract_name, ceiling in expected_ceiling.items():
            schema = json.loads(
                ROOT.joinpath("contracts", f"{contract_name}.schema.json").read_text()
            )
            boundary = schema["x-vibe-authority-boundary"]
            self.assertFalse(boundary["may_accept_scientific_claim"])
            self.assertFalse(boundary["may_authorize_execution"])
            self.assertEqual(boundary["maximum_claim_ceiling"], ceiling)

    def test_fixed_dispatcher_has_disjoint_exact_ownership(self) -> None:
        for contract_name in EXPECTED_OBLIGATIONS:
            with self.subTest(contract_name=contract_name):
                self.assertIs(
                    bundle_semantics.builtin_evaluator(contract_name),
                    bundle_semantics_legacy.evaluate,
                )
        for contract_name in (
            "run-manifest",
            "campaign-record",
            "recommendation-record",
        ):
            with self.subTest(contract_name=contract_name):
                self.assertIsNot(
                    bundle_semantics.builtin_evaluator(contract_name),
                    bundle_semantics_legacy.evaluate,
                )

    def test_handler_coverage_and_result_shape_are_exact(self) -> None:
        self.assertEqual(
            set(bundle_semantics_legacy.OBLIGATION_IDS),
            set().union(*NON_CORE_OBLIGATIONS.values()),
        )
        context = PlanSemanticsTests().good_context()
        requested = sorted(NON_CORE_OBLIGATIONS["postprocess-plan"])
        results = bundle_semantics_legacy.evaluate(requested + requested, context)
        self.assertEqual([item["obligation_id"] for item in results], requested)
        for result in results:
            self.assertEqual(
                set(result),
                {
                    "obligation_id",
                    "status",
                    "finding_codes",
                    "location",
                    "message",
                    "handler_id",
                },
            )
            self.assertTrue(result["handler_id"].startswith("bundle-semantics-legacy-v1."))

    def test_dispatcher_accounts_for_privacy_and_domain_obligations_once(self) -> None:
        contexts = [
            ArtifactSemanticsTests().good_context(),
            DatasetSemanticsTests().good_context(),
            PlanSemanticsTests().good_context(),
            ToolExecutionSemanticsTests().good_context(),
        ]
        for context in contexts:
            contract_name = context["current_record"]["contract_name"]
            with self.subTest(contract_name=contract_name):
                results = bundle_semantics.evaluate_advertised_obligations(
                    sorted(EXPECTED_OBLIGATIONS[contract_name]),
                    context,
                    evaluator=bundle_semantics_legacy.evaluate,
                )
                self.assertEqual(
                    {item["obligation_id"] for item in results},
                    EXPECTED_OBLIGATIONS[contract_name],
                )
                self.assertTrue(all(item["status"] == "pass" for item in results))
                for item in results:
                    expected_handler = (
                        "privacy-boundary"
                        if item["obligation_id"].endswith("_PRIVACY_SAFE")
                        else "bundle-semantics-legacy-v1."
                        + item["obligation_id"]
                    )
                    self.assertEqual(
                        item["handler_id"],
                        expected_handler,
                        "A bundle-core substring heuristic must not bypass the "
                        "legacy record-to-artifact consistency handler.",
                    )

        context = PlanSemanticsTests().good_context()
        context["core_checks"]["privacy-boundary"] = {
            "status": "blocked",
            "finding_codes": ["ABSOLUTE_PATH_DISCLOSED"],
        }
        results = bundle_semantics.evaluate_advertised_obligations(
            sorted(EXPECTED_OBLIGATIONS["postprocess-plan"]),
            context,
            evaluator=bundle_semantics_legacy.evaluate,
        )
        privacy = next(
            item
            for item in results
            if item["obligation_id"] == "LEGACY_PLAN_PRIVACY_SAFE"
        )
        self.assertEqual(privacy["status"], "blocked")
        self.assertIn("ABSOLUTE_PATH_DISCLOSED", privacy["finding_codes"])

    def test_malformed_context_and_unknown_obligation_never_pass(self) -> None:
        context = PlanSemanticsTests().good_context()
        context["current_record"]["integrity_verified_active"] = False
        results = bundle_semantics_legacy.evaluate(
            sorted(NON_CORE_OBLIGATIONS["postprocess-plan"]), context
        )
        self.assertTrue(all(item["status"] == "blocked" for item in results))
        unknown = bundle_semantics_legacy.evaluate(["UNKNOWN_LEGACY_OBLIGATION"], context)
        self.assertEqual(unknown[0]["status"], "blocked")
        self.assertIn("SEMANTIC_OBLIGATION_HANDLER_MISSING", unknown[0]["finding_codes"])

    def test_root_cause_mutations_remain_schema_valid(self) -> None:
        cases = []
        artifact = artifact_manifest()
        artifact["data_files"][0]["sha256"] = "f" * 64
        artifact["source_run_ids"] = ["nonexistent-run"]
        cases.append(("artifact", artifact))
        dataset = dataset_manifest()
        dataset["source_files"][0]["sha256"] = "e" * 64
        dataset["data_files"][0]["sha256"] = "f" * 64
        cases.append(("dataset", dataset))
        plan = plan_manifest()
        plan["source_files"][0].update({"path": "missing.dat", "present": True})
        cases.append(("plan", plan))
        execution = execution_manifest()
        execution["plan_id"] = "nonexistent-plan"
        execution["outputs"][0]["sha256"] = "f" * 64
        cases.append(("execution", execution))
        for selector, data in cases:
            with self.subTest(selector=selector):
                self.assertEqual(validate_contract.validation_errors(selector, data), [])


class ArtifactSemanticsTests(unittest.TestCase):
    def good_context(self) -> dict:
        run = record_view("run-manifest", "run-example-001", run_manifest(), index=0)
        return context_for(
            "artifact-manifest",
            "artifact-example-001",
            artifact_manifest(),
            index=1,
            parents=[run],
            artifacts={"bands.csv": postprocess_artifacts()["bands.csv"]},
        )

    def test_hash_bound_complete_artifact_passes_technical_obligations(self) -> None:
        self.assertEqual(set(statuses(self.good_context()).values()), {"pass"})

    def test_fabricated_output_hash_is_rejected(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["data_files"][0]["sha256"] = "f" * 64
        result = evaluate(context)["LEGACY_ARTIFACT_OUTPUT_ARTIFACT_HASH_RESOLVES"]
        self.assertEqual(result["status"], "fail")
        self.assertIn("LEGACY_ARTIFACT_OUTPUT_HASH_MISMATCH", result["finding_codes"])

    def test_missing_output_is_blocked_not_treated_as_complete(self) -> None:
        context = self.good_context()
        context["artifacts_by_label"] = {}
        self.assertEqual(
            statuses(context)["LEGACY_ARTIFACT_OUTPUT_ARTIFACT_HASH_RESOLVES"],
            "blocked",
        )

    def test_source_run_must_be_unique_verified_and_topologically_prior(self) -> None:
        context = self.good_context()
        context["records_by_identity"] = {
            key: value
            for key, value in context["records_by_identity"].items()
            if key[0] != "run-manifest"
        }
        self.assertEqual(
            statuses(context)["LEGACY_ARTIFACT_SOURCE_LINEAGE_PREEXISTS"], "blocked"
        )

        context = self.good_context()
        parent = context["records_by_identity"][("run-manifest", "1.0", "run-example-001")]
        parent["index"] = 2
        self.assertEqual(
            statuses(context)["LEGACY_ARTIFACT_SOURCE_LINEAGE_PREEXISTS"], "fail"
        )

    def test_complete_status_cannot_hide_blocked_validation(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["validation"]["status"] = "block"
        self.assertEqual(
            statuses(context)["LEGACY_ARTIFACT_STATUS_CHECK_CONSISTENT"], "fail"
        )

    def test_claim_boundary_cannot_assert_scientific_acceptance(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["claim_boundary"] = [
            "This artifact is scientifically accepted."
        ]
        self.assertEqual(
            statuses(context)["LEGACY_ARTIFACT_TECHNICAL_CLAIM_CEILING"], "fail"
        )


class DatasetSemanticsTests(unittest.TestCase):
    def good_context(self) -> dict:
        artifacts = postprocess_artifacts()
        return context_for(
            "normalized-dataset",
            "dataset-example-001",
            dataset_manifest(),
            index=2,
            artifacts={key: artifacts[key] for key in ("bands.dat", "bands.csv")},
        )

    def test_hash_bound_dataset_passes_only_numerical_candidate_obligations(self) -> None:
        self.assertEqual(set(statuses(self.good_context()).values()), {"pass"})

    def test_validation_pass_requires_nonempty_all_pass_checks(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["validation"]["checks"][0]["status"] = "warn"
        self.assertEqual(
            statuses(context)["LEGACY_DATASET_VALIDATION_CHECK_CONSISTENT"], "fail"
        )
        context = self.good_context()
        context["current_record"]["data"]["validation"]["checks"] = []
        self.assertEqual(
            statuses(context)["LEGACY_DATASET_VALIDATION_CHECK_CONSISTENT"], "fail"
        )

    def test_source_and_output_hashes_must_match_bundle_bytes(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["source_files"][0]["sha256"] = ZERO_HASH
        self.assertEqual(
            statuses(context)["LEGACY_DATASET_SOURCE_ARTIFACT_HASH_RESOLVES"], "fail"
        )
        context = self.good_context()
        context["current_record"]["data"]["data_files"][0]["bytes"] = 12
        self.assertEqual(
            statuses(context)["LEGACY_DATASET_OUTPUT_ARTIFACT_HASH_RESOLVES"], "fail"
        )

    def test_passing_dataset_cannot_use_redacted_or_unresolved_source(self) -> None:
        context = self.good_context()
        source = context["current_record"]["data"]["source_files"][0]
        source.update({"hash_status": "redacted", "sha256": None})
        self.assertEqual(
            statuses(context)["LEGACY_DATASET_SOURCE_ARTIFACT_HASH_RESOLVES"],
            "blocked",
        )

    def test_tool_integration_maturity_requires_prior_succeeded_execution(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        data["maturity"] = "tool-integration-validated"
        data["provenance"]["tool_execution_ids"] = []
        self.assertEqual(
            statuses(context)["LEGACY_DATASET_MATURITY_EVIDENCE_CONSISTENT"],
            "blocked",
        )

        execution = execution_manifest()
        execution["status"] = "failed"
        execution["return_code"] = 1
        parent = record_view(
            "tool-execution", "execution-example-001", execution, index=1
        )
        data["provenance"]["tool_execution_ids"] = ["execution-example-001"]
        context["records_by_identity"][("tool-execution", "1.0", "execution-example-001")] = parent
        self.assertEqual(
            statuses(context)["LEGACY_DATASET_MATURITY_EVIDENCE_CONSISTENT"], "fail"
        )

    def test_limitations_cannot_promote_dataset_to_scientific_acceptance(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["limitations"] = [
            "The material is thermodynamically stable and scientifically accepted."
        ]
        self.assertEqual(
            statuses(context)["LEGACY_DATASET_NUMERICAL_CANDIDATE_CEILING"], "fail"
        )


class PlanSemanticsTests(unittest.TestCase):
    def good_context(self) -> dict:
        return context_for(
            "postprocess-plan",
            "plan-example-001",
            plan_manifest(),
            index=0,
            artifacts={"bands.dat": postprocess_artifacts()["bands.dat"]},
        )

    def test_ready_hash_bound_plan_passes_no_positive_claim_obligations(self) -> None:
        self.assertEqual(set(statuses(self.good_context()).values()), {"pass"})

    def test_planned_status_requires_ready_backend_sources_steps_and_no_blockers(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        data["backend"]["available"] = False
        data["source_files"][0]["present"] = False
        data["blockers"] = ["blocked"]
        self.assertEqual(
            statuses(context)["LEGACY_PLAN_STATUS_READINESS_CONSISTENT"], "fail"
        )

    def test_self_reported_present_source_without_bundle_artifact_is_blocked(self) -> None:
        context = self.good_context()
        context["artifacts_by_label"] = {}
        self.assertEqual(
            statuses(context)["LEGACY_PLAN_SOURCE_ARTIFACT_RESOLVES"], "blocked"
        )

    def test_step_graph_rejects_duplicate_outputs_cycles_and_action_mismatch(self) -> None:
        context = self.good_context()
        second = copy.deepcopy(context["current_record"]["data"]["steps"][0])
        second["step_id"] = "normalize-2"
        context["current_record"]["data"]["steps"].append(second)
        self.assertEqual(
            statuses(context)["LEGACY_PLAN_STEP_GRAPH_CONSISTENT"], "fail"
        )

        context = self.good_context()
        context["current_record"]["data"]["steps"][0]["action"] = "external"
        self.assertEqual(
            statuses(context)["LEGACY_PLAN_STEP_GRAPH_CONSISTENT"], "fail"
        )

    def test_blocked_plan_requires_stable_reason_and_no_executable_steps(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        data["status"] = "blocked"
        data["blockers"] = []
        self.assertEqual(
            statuses(context)["LEGACY_PLAN_STATUS_READINESS_CONSISTENT"], "fail"
        )


class ToolExecutionSemanticsTests(unittest.TestCase):
    def good_context(self) -> dict:
        plan = record_view(
            "postprocess-plan", "plan-example-001", plan_manifest(), index=0
        )
        return context_for(
            "tool-execution",
            "execution-example-001",
            execution_manifest(),
            index=1,
            parents=[plan],
            artifacts=postprocess_artifacts(),
        )

    def test_hash_bound_plan_matched_success_passes_technical_obligations(self) -> None:
        self.assertEqual(set(statuses(self.good_context()).values()), {"pass"})

    def test_execution_requires_unique_prior_verified_plan(self) -> None:
        context = self.good_context()
        context["records_by_identity"] = {
            key: value
            for key, value in context["records_by_identity"].items()
            if key[0] != "postprocess-plan"
        }
        self.assertEqual(
            statuses(context)["LEGACY_TOOL_EXECUTION_PLAN_LINEAGE_PREEXISTS"],
            "blocked",
        )
        context = self.good_context()
        context["records_by_identity"][("postprocess-plan", "1.0", "plan-example-001")]["index"] = 2
        self.assertEqual(
            statuses(context)["LEGACY_TOOL_EXECUTION_PLAN_LINEAGE_PREEXISTS"], "fail"
        )

    def test_success_state_requires_zero_code_chronology_and_matching_duration(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        data["return_code"] = 2
        data["finished_utc"] = "2026-07-17T23:59:59Z"
        data["duration_s"] = 99
        self.assertEqual(
            statuses(context)["LEGACY_TOOL_EXECUTION_STATUS_RUNTIME_CONSISTENT"],
            "fail",
        )

    def test_plan_step_command_backend_and_io_must_match(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        data["command"] = ["different-tool"]
        data["backend"] = "different-backend"
        data["outputs"][0]["path"] = "different.csv"
        self.assertEqual(
            statuses(context)["LEGACY_TOOL_EXECUTION_PLAN_STEP_CONSISTENT"], "fail"
        )

    def test_success_outputs_and_logs_require_exact_bundle_bytes(self) -> None:
        context = self.good_context()
        context["artifacts_by_label"]["bands.csv"]["raw_sha256"] = ZERO_HASH
        context["artifacts_by_label"]["bands.csv"]["integrity_verified"] = False
        self.assertEqual(
            statuses(context)["LEGACY_TOOL_EXECUTION_FILE_ARTIFACT_HASH_RESOLVES"],
            "fail",
        )

    def test_dry_run_cannot_carry_runtime_or_output_evidence(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        data["dry_run"] = True
        data["status"] = "dry-run"
        self.assertEqual(
            statuses(context)["LEGACY_TOOL_EXECUTION_STATUS_RUNTIME_CONSISTENT"],
            "fail",
        )


class StructureSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls._temporary.name)
        cls.cif = cls.root / "nacl.cif"
        cls.json_path = cls.root / "structure.json"
        cls.markdown = cls.root / "structure.md"
        cls.views_dir = cls.root / "views"
        cls.cif.write_text(NACL_CIF, encoding="utf-8")
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["MPLCONFIGDIR"] = str(cls.root / "mpl")
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(
                    ROOT
                    / "skills"
                    / "cif-structure-analysis"
                    / "scripts"
                    / "analyze_cif.py"
                ),
                "--input",
                str(cls.cif),
                "--json",
                str(cls.json_path),
                "--markdown",
                str(cls.markdown),
                "--views-dir",
                str(cls.views_dir),
            ],
            capture_output=True,
            text=True,
            env=environment,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        cls.manifest = json.loads(cls.json_path.read_text(encoding="utf-8"))
        cls.source_hash = hashlib.sha256(cls.cif.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    def good_context(self) -> dict:
        artifacts = {
            self.cif.name: artifact_view(
                self.cif.name, self.source_hash, self.cif.stat().st_size
            )
        }
        for view in self.manifest["views"]:
            path = self.root / view["path"]
            artifacts[path.name] = artifact_view(
                path.name,
                hashlib.sha256(path.read_bytes()).hexdigest(),
                path.stat().st_size,
                index=len(artifacts),
            )
        return context_for(
            "structure-manifest",
            self.manifest["manifest_id"],
            copy.deepcopy(self.manifest),
            index=0,
            artifacts=artifacts,
        )

    def test_generated_hash_bound_manifest_passes_numerical_candidate_obligations(self) -> None:
        self.assertEqual(
            validate_contract.validation_errors("structure", self.manifest), []
        )
        self.assertEqual(set(statuses(self.good_context()).values()), {"pass"})

    def test_high_precision_generated_manifest_has_reproducible_identity(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            root = Path(raw_directory)
            cif = root / "high-precision.cif"
            manifest_path = root / "structure.json"
            markdown_path = root / "structure.md"
            cif.write_text(HIGH_PRECISION_CIF, encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(
                        ROOT
                        / "skills"
                        / "cif-structure-analysis"
                        / "scripts"
                        / "analyze_cif.py"
                    ),
                    "--input",
                    str(cif),
                    "--json",
                    str(manifest_path),
                    "--markdown",
                    str(markdown_path),
                ],
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                validate_contract.validation_errors("structure", manifest), []
            )
            fingerprint = manifest["structure_identity"]
            self.assertEqual(
                fingerprint["canonicalization"],
                "json-sort-keys-compact-utf8-v1",
            )
            canonical = json.dumps(
                fingerprint["fingerprint_input"],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("utf-8")
            self.assertEqual(
                fingerprint["value"], hashlib.sha256(canonical).hexdigest()
            )
            wrapped_site = fingerprint["fingerprint_input"]["sites"][0][
                "fractional"
            ]
            self.assertTrue(all(0.0 <= value <= 1.0 for value in wrapped_site))
            self.assertAlmostEqual(wrapped_site[2], 0.2, places=9)
            raw = cif.read_bytes()
            context = context_for(
                "structure-manifest",
                manifest["manifest_id"],
                manifest,
                index=0,
                artifacts={
                    cif.name: artifact_view(
                        cif.name, hashlib.sha256(raw).hexdigest(), len(raw)
                    )
                },
            )
            identity = evaluate(context)[
                "LEGACY_STRUCTURE_SOURCE_IDENTITY_CONSISTENT"
            ]
            self.assertEqual(identity["status"], "pass", identity)

            legacy = copy.deepcopy(manifest)
            legacy["structure_identity"].pop("fingerprint_input")
            legacy["structure_identity"].pop("canonicalization")
            legacy_context = context_for(
                "structure-manifest",
                legacy["manifest_id"],
                legacy,
                index=0,
                artifacts={
                    cif.name: artifact_view(
                        cif.name, hashlib.sha256(raw).hexdigest(), len(raw)
                    )
                },
            )
            unverifiable = evaluate(legacy_context)[
                "LEGACY_STRUCTURE_SOURCE_IDENTITY_CONSISTENT"
            ]
            self.assertEqual(unverifiable["status"], "blocked", unverifiable)
            self.assertIn(
                "LEGACY_STRUCTURE_FINGERPRINT_UNVERIFIABLE",
                unverifiable["finding_codes"],
            )

    def test_fingerprint_preimage_is_backward_compatible_but_cannot_be_self_filled(self) -> None:
        legacy_context = self.good_context()
        legacy_identity = legacy_context["current_record"]["data"][
            "structure_identity"
        ]
        legacy_identity.pop("fingerprint_input")
        legacy_identity.pop("canonicalization")
        self.assertEqual(
            evaluate(legacy_context)[
                "LEGACY_STRUCTURE_SOURCE_IDENTITY_CONSISTENT"
            ]["status"],
            "pass",
        )

        hash_tamper = self.good_context()
        identity = hash_tamper["current_record"]["data"]["structure_identity"]
        identity["fingerprint_input"]["cell_vectors_ang"][0][0] += 1e-10
        result = evaluate(hash_tamper)[
            "LEGACY_STRUCTURE_SOURCE_IDENTITY_CONSISTENT"
        ]
        self.assertEqual(result["status"], "fail")
        self.assertIn(
            "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_HASH_MISMATCH",
            result["finding_codes"],
        )

        self_filled = self.good_context()
        identity = self_filled["current_record"]["data"]["structure_identity"]
        identity["fingerprint_input"]["cell_vectors_ang"][0][0] += 0.01
        canonical = json.dumps(
            identity["fingerprint_input"],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        identity["value"] = hashlib.sha256(canonical).hexdigest()
        result = evaluate(self_filled)[
            "LEGACY_STRUCTURE_SOURCE_IDENTITY_CONSISTENT"
        ]
        self.assertEqual(result["status"], "fail")
        self.assertIn(
            "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_CELL_MISMATCH",
            result["finding_codes"],
        )

        incomplete = copy.deepcopy(self.manifest)
        incomplete["structure_identity"].pop("fingerprint_input")
        self.assertTrue(
            validate_contract.validation_errors("structure", incomplete),
            "canonicalization and fingerprint_input must be schema-dependent",
        )

    def test_source_hash_and_duplicate_identity_fields_must_match_bundle_bytes(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["source"]["sha256"] = ZERO_HASH
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_SOURCE_ARTIFACT_HASH_RESOLVES"],
            "fail",
        )
        context = self.good_context()
        context["current_record"]["data"]["input"]["sha256"] = ZERO_HASH
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_SOURCE_IDENTITY_CONSISTENT"], "fail"
        )

    def test_manifest_id_block_and_options_are_recomputed_not_trusted(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        data["manifest_id"] = "structure-0000000000000000-b0"
        data["execution"]["data_block"]["name"] = "wrong"
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_SOURCE_IDENTITY_CONSISTENT"], "fail"
        )

    def test_status_is_exact_aggregate_of_nonempty_checks(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        data["status"] = "PASS"
        data["validation"] = {
            "status": "pass",
            "checks": [{"id": "fabricated", "status": "warn", "message": "warning"}],
        }
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_STATUS_CHECK_CONSISTENT"], "fail"
        )

    def test_site_count_elements_indices_and_atomic_numbers_are_recomputed(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        data["structure"]["element_counts"]["Na"] = 99
        data["structure"]["sites"][0]["index"] = 1
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_SITE_COMPOSITION_CONSISTENT"], "fail"
        )

    def test_fractional_cartesian_coordinates_must_match_cell(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["structure"]["sites"][1][
            "cartesian_ang"
        ][0] += 1.0
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_COORDINATE_CELL_CONSISTENT"],
            "fail",
        )

    def test_neighbor_counts_indices_vectors_and_distances_are_recomputed(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["structure"]["nearest_distances"][
            "nearest_neighbor_bond_count"
        ] += 1
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_NEIGHBOR_SUMMARY_CONSISTENT"],
            "fail",
        )

    def test_bond_match_count_and_tolerance_cannot_be_self_reported(self) -> None:
        context = self.good_context()
        match = context["current_record"]["data"]["structure"]["nearest_distances"][
            "bond_length_match"
        ]
        match["status"] = "MATCHED"
        match["match_count"] = 1
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_BOND_MATCH_CONSISTENT"], "fail"
        )

    def test_transform_parent_fingerprint_must_resolve_to_prior_structure(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["transformations"] = [
            {
                "operation": "supercell",
                "backend": "test",
                "backend_version": "1",
                "parameters": {},
                "parent_fingerprint": ZERO_HASH,
                "site_mapping": [0, 1],
            }
        ]
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_TRANSFORMATION_LINEAGE_PREEXISTS"],
            "blocked",
        )

    def test_transform_parent_must_be_unique_verified_and_topologically_prior(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        parent_data = copy.deepcopy(self.manifest)
        parent_data["manifest_id"] = "structure-parent-001"
        parent = record_view(
            "structure-manifest", "structure-parent-001", parent_data, index=0
        )
        context["current_record_index"] = 1
        context["current_record"]["index"] = 1
        context["records_by_identity"] = {
            ("structure-manifest", "1.0", "parent-structure"): parent,
            (
                "structure-manifest",
                "1.0",
                context["current_record"]["record_id"],
            ): copy.deepcopy(context["current_record"]),
        }
        data["transformations"] = [
            {
                "operation": "identity-test",
                "backend": "test",
                "backend_version": "1",
                "parameters": {},
                "parent_fingerprint": parent_data["structure_identity"]["value"],
                "site_mapping": list(range(data["structure"]["atom_count"])),
            }
        ]
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_TRANSFORMATION_LINEAGE_PREEXISTS"],
            "pass",
        )
        parent["index"] = 2
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_TRANSFORMATION_LINEAGE_PREEXISTS"],
            "fail",
        )

    def test_view_files_must_be_integrity_verified_bundle_artifacts(self) -> None:
        context = self.good_context()
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_VIEW_ARTIFACTS_RESOLVE"], "pass"
        )
        removed = Path(context["current_record"]["data"]["views"][0]["path"]).name
        context["artifacts_by_label"].pop(removed)
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_VIEW_ARTIFACTS_RESOLVE"],
            "blocked",
        )

    def test_requested_neighbor_bond_match_is_recomputed(self) -> None:
        context = self.good_context()
        data = context["current_record"]["data"]
        nearest = data["structure"]["nearest_distances"]
        edge = copy.deepcopy(nearest["nearest_neighbor_bond_pairs"][0])
        query = {
            "element_pair": sorted(edge["symbols"]),
            "target_distance_ang": edge["distance_ang"],
            "tolerance_ang": 0.01,
        }
        candidates = [
            {**copy.deepcopy(item), "absolute_delta_ang": 0.0}
            for item in nearest["nearest_neighbor_bond_pairs"]
            if sorted(item["symbols"]) == query["element_pair"]
        ]
        candidates.sort(
            key=lambda item: (
                item["absolute_delta_ang"],
                item["distance_ang"],
                item["i"],
                item["j"],
                tuple(item["shift"]),
            )
        )
        match = nearest["bond_length_match"]
        match.update(
            {
                "status": "MATCHED",
                "query": query,
                "candidate_count": len(candidates),
                "match_count": len(candidates),
                "matches": candidates,
                "closest_candidate": candidates[0],
            }
        )
        data["execution"]["bond_match"] = copy.deepcopy(query)
        data["provenance"]["command_options"]["bond_match"] = copy.deepcopy(query)
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_BOND_MATCH_CONSISTENT"], "pass"
        )
        match["match_count"] = 2
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_BOND_MATCH_CONSISTENT"], "fail"
        )

    def test_not_assessed_boundary_cannot_be_removed_or_replaced_by_positive_science(self) -> None:
        context = self.good_context()
        context["current_record"]["data"]["not_assessed"] = []
        context["current_record"]["data"]["limitations"] = [
            "This structure is thermodynamically stable."
        ]
        self.assertEqual(
            statuses(context)["LEGACY_STRUCTURE_NUMERICAL_CANDIDATE_CEILING"],
            "fail",
        )


class LegacyBundleEndToEndTests(unittest.TestCase):
    @staticmethod
    def _raw_json(value: object) -> bytes:
        return (
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")

    @staticmethod
    def _bundle_artifact(raw: bytes, label: str, index: int, role: str) -> dict:
        suffix = Path(label).suffix.lower()
        media_type = {
            ".cif": "chemical/x-cif",
            ".csv": "text/csv",
            ".dat": "text/plain",
            ".stdout": "text/plain",
            ".stderr": "text/plain",
        }.get(suffix, "application/octet-stream")
        return {
            "artifact_index": index,
            "path": label,
            "label": label,
            "role": role,
            "media_type": media_type,
            "format": "cif" if suffix == ".cif" else "plain-data",
            "format_version": None,
            "availability": "present",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "sensitivity": "public",
            "redistribution": "redistributable",
            "license_boundary": {
                "status": "not-applicable",
                "license_id": None,
                "redistribution_basis": "not-applicable",
                "limitations": [],
            },
            "supports_positive_claim": False,
        }

    def test_real_portable_bundle_passes_then_semantic_hash_mutation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            outer = Path(raw_directory)
            generation = outer / "generation"
            bundle = outer / "bundle"
            generation.mkdir()
            bundle.mkdir()
            source_cif = generation / "nacl.cif"
            structure_json = generation / "structure.json"
            structure_markdown = generation / "structure.md"
            source_cif.write_text(NACL_CIF, encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(
                        ROOT
                        / "skills"
                        / "cif-structure-analysis"
                        / "scripts"
                        / "analyze_cif.py"
                    ),
                    "--input",
                    str(source_cif),
                    "--json",
                    str(structure_json),
                    "--markdown",
                    str(structure_markdown),
                ],
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            structure = json.loads(structure_json.read_text(encoding="utf-8"))

            artifact_raw = {
                "bands.dat": b"0.0 -1.0\n",
                "bands.csv": b"energy_ev\n-1.0\n",
                "execution.stdout": b"",
                "execution.stderr": b"",
                "nacl.cif": source_cif.read_bytes(),
            }
            for label, raw in artifact_raw.items():
                bundle.joinpath(label).write_bytes(raw)

            source_digest = hashlib.sha256(artifact_raw["bands.dat"]).hexdigest()
            output_digest = hashlib.sha256(artifact_raw["bands.csv"]).hexdigest()
            empty_digest = hashlib.sha256(b"").hexdigest()
            run = run_manifest()
            plan = plan_manifest()
            execution = execution_manifest()
            execution["inputs"][0].update(
                {"sha256": source_digest, "bytes": len(artifact_raw["bands.dat"])}
            )
            execution["outputs"][0].update(
                {"sha256": output_digest, "bytes": len(artifact_raw["bands.csv"])}
            )
            execution["stdout"].update({"sha256": empty_digest, "bytes": 0})
            execution["stderr"].update({"sha256": empty_digest, "bytes": 0})
            dataset = dataset_manifest()
            dataset["source_files"][0].update(
                {"sha256": source_digest, "bytes": len(artifact_raw["bands.dat"])}
            )
            dataset["data_files"][0].update(
                {"sha256": output_digest, "bytes": len(artifact_raw["bands.csv"])}
            )
            artifact = artifact_manifest()
            artifact["data_files"][0].update(
                {"sha256": output_digest, "bytes": len(artifact_raw["bands.csv"])}
            )

            records = [
                ("run-manifest", run["record_id"], run),
                ("postprocess-plan", plan["plan_id"], plan),
                ("tool-execution", execution["execution_id"], execution),
                ("normalized-dataset", dataset["dataset_id"], dataset),
                ("artifact-manifest", artifact["artifact_id"], artifact),
                ("structure-manifest", structure["manifest_id"], structure),
            ]
            record_entries = []
            raw_by_contract: dict[str, bytes] = {}
            path_by_contract: dict[str, str] = {}
            for index, (contract_name, record_id, data) in enumerate(records):
                raw = self._raw_json(data)
                path = f"record-{index:02d}-{contract_name}.json"
                bundle.joinpath(path).write_bytes(raw)
                raw_by_contract[contract_name] = raw
                path_by_contract[contract_name] = path
                record_entries.append(
                    {
                        "topological_index": index,
                        "path": path,
                        "label": f"record-{index:02d}-{contract_name}",
                        "contract_name": contract_name,
                        "schema_version": "1.0",
                        "record_id": record_id,
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }
                )
            roles = {
                "bands.dat": "postprocess-input",
                "bands.csv": "postprocess-output",
                "execution.stdout": "tool-stdout",
                "execution.stderr": "tool-stderr",
                "nacl.cif": "structure-source",
            }
            artifact_entries = [
                self._bundle_artifact(raw, label, index, roles[label])
                for index, (label, raw) in enumerate(artifact_raw.items())
            ]
            manifest = {
                "contract_name": "bundle-manifest",
                "schema_version": "1.0",
                "bundle_id": "bundle-legacy-e2e-001",
                "bundle_mode": "portable-public",
                "created_utc": "2026-07-18T00:00:00Z",
                "records": record_entries,
                "artifacts": artifact_entries,
                "privacy_policy": {
                    "reject_credentials": True,
                    "reject_private_identifiers": True,
                    "reject_absolute_paths": True,
                    "reject_path_traversal": True,
                    "reject_restricted_payloads": True,
                },
                "producer": {
                    "skill_id": "vibe-dft-skills",
                    "skill_version": "1.0",
                    "tool_id": "legacy-e2e-test-builder",
                    "tool_version": "1.0",
                    "generated_utc": "2026-07-18T00:00:00Z",
                },
                "limitations": ["Synthetic technical bundle; no scientific claim."],
            }
            manifest_path = bundle / "bundle.json"
            report_path = bundle / "report.json"
            manifest_path.write_bytes(self._raw_json(manifest))

            validator = [
                sys.executable,
                "-B",
                str(ROOT / "tools" / "validate_bundle.py"),
                str(manifest_path),
                "--report",
                str(report_path),
            ]
            passed = subprocess.run(
                validator,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(passed.returncode, 0, passed.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                report["assurance"], "integrity-verified-no-positive-claim"
            )
            owned_results = [
                item
                for item in report["obligation_results"]
                if item["source_contract_name"] in EXPECTED_OBLIGATIONS
            ]
            self.assertEqual(
                len(owned_results), sum(map(len, EXPECTED_OBLIGATIONS.values()))
            )
            self.assertTrue(all(item["status"] == "pass" for item in owned_results))

            artifact["data_files"][0]["sha256"] = "f" * 64
            mutated_raw = self._raw_json(artifact)
            bundle.joinpath(path_by_contract["artifact-manifest"]).write_bytes(mutated_raw)
            artifact_entry_record = next(
                item
                for item in manifest["records"]
                if item["contract_name"] == "artifact-manifest"
            )
            artifact_entry_record["sha256"] = hashlib.sha256(mutated_raw).hexdigest()
            manifest_path.write_bytes(self._raw_json(manifest))
            failed = subprocess.run(
                [*validator, "--force"],
                capture_output=True,
                text=True,
                env=environment,
            )
            failed_report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                failed.returncode,
                2,
                json.dumps(
                    {
                        "stderr": failed.stderr,
                        "summary": failed_report.get("summary"),
                        "findings": failed_report.get("findings"),
                        "artifact_obligations": [
                            item
                            for item in failed_report.get("obligation_results", [])
                            if item.get("source_contract_name")
                            == "artifact-manifest"
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                ),
            )
            self.assertEqual(failed_report["status"], "fail")
            self.assertEqual(failed_report["assurance"], "invalid")
            self.assertIn(
                "LEGACY_ARTIFACT_OUTPUT_HASH_MISMATCH",
                {item["code"] for item in failed_report["findings"]},
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
