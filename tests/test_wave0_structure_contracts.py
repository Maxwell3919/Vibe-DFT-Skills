"""Executable acceptance tests for the Wave 0 structure handoff contracts.

The fixtures deliberately exercise the state transitions which a fast,
low-reasoning agent is most likely to guess incorrectly.  Every negative case
is a mutation of an otherwise valid record so a rejection is attributable to
the intended fail-closed rule rather than to an incomplete placeholder.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from tools import bundle_semantics, bundle_semantics_structure

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATHS = {
    "common": ROOT / "contracts" / "common-definitions-1.0.schema.json",
    "snapshot": ROOT / "contracts" / "structure-snapshot.schema.json",
    "molecular": ROOT / "contracts" / "molecular-structure-manifest.schema.json",
    "transformation": ROOT
    / "contracts"
    / "structure-transformation-manifest.schema.json",
    "export": ROOT / "contracts" / "structure-export-manifest.schema.json",
    "trajectory": ROOT / "contracts" / "atomistic-trajectory-manifest.schema.json",
}

SCHEMAS = {
    name: json.loads(path.read_text(encoding="utf-8"))
    for name, path in SCHEMA_PATHS.items()
}
REGISTRY = Registry()
for loaded_schema in SCHEMAS.values():
    REGISTRY = REGISTRY.with_resource(
        loaded_schema["$id"], Resource.from_contents(loaded_schema)
    )

VALIDATORS = {
    name: Draft202012Validator(
        schema,
        registry=REGISTRY,
        format_checker=FormatChecker(),
    )
    for name, schema in SCHEMAS.items()
    if name != "common"
}

HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
NOW = "2026-07-18T12:00:00Z"

REQUIRED_SEMANTIC_OBLIGATIONS = {
    "snapshot": {
        "structure-site-identity-not-unique",
        "structure-composition-site-mismatch",
        "structure-periodicity-cell-mismatch",
        "structure-coordinate-representation-mismatch",
        "structure-charge-spin-electron-parity-mismatch",
        "structure-identity-fingerprint-mismatch",
        "record-reference-dag-invalid",
    },
    "molecular": {
        "molecular-snapshot-hash-mismatch",
        "molecular-site-reference-missing",
        "molecular-charge-multiplicity-electron-parity-mismatch",
        "molecular-connectivity-inconsistent",
        "molecular-fragment-coverage-inconsistent",
        "molecular-extraction-lineage-mismatch",
        "record-reference-dag-invalid",
    },
    "transformation": {
        "structure-transform-reference-hash-mismatch",
        "structure-transform-mapping-id-not-unique",
        "structure-transform-site-reference-missing",
        "structure-transform-mapping-coverage-incomplete",
        "structure-transform-relation-cardinality-mismatch",
        "structure-transform-image-shift-inconsistent",
        "structure-transform-operation-semantics-mismatch",
        "structure-transform-roundtrip-fingerprint-mismatch",
        "structure-transform-tolerance-unverified",
        "record-reference-dag-invalid",
    },
    "export": {
        "structure-export-source-hash-mismatch",
        "structure-export-file-hash-mismatch",
        "structure-export-output-index-not-unique",
        "structure-export-atom-map-incomplete",
        "structure-export-unit-map-inconsistent",
        "structure-export-target-profile-mismatch",
        "structure-export-roundtrip-fingerprint-mismatch",
        "structure-export-loss-undisclosed",
        "record-reference-dag-invalid",
    },
    "trajectory": {
        "trajectory-source-lineage-hash-mismatch",
        "trajectory-file-hash-mismatch",
        "trajectory-segment-id-not-unique",
        "trajectory-frame-index-not-unique",
        "trajectory-frame-count-mismatch",
        "trajectory-atom-count-site-order-mismatch",
        "trajectory-segment-range-invalid",
        "trajectory-continuity-mismatch",
        "trajectory-time-axis-nonmonotonic",
        "trajectory-pbc-cell-mismatch",
        "record-reference-dag-invalid",
    },
}

READINESS_SURFACES = {
    "snapshot": "calculation-readiness",
    "molecular": "calculation-readiness",
    "transformation": "calculation-use",
    "export": "calculation-use",
    "trajectory": "analysis-readiness",
}


def record_ref(
    contract_name: str,
    record_id: str,
    role: str = "source",
    sha256: str = HASH_A,
) -> dict[str, Any]:
    return {
        "contract_name": contract_name,
        "schema_version": "1.0",
        "record_id": record_id,
        "sha256": sha256,
        "role": role,
    }


def file_ref(
    label: str,
    role: str,
    format_name: str,
    media_type: str = "text/plain",
    *,
    availability: str = "present",
    sha256: str | None = HASH_A,
    byte_count: int | None = 128,
) -> dict[str, Any]:
    return {
        "role": role,
        "label": label,
        "media_type": media_type,
        "format": format_name,
        "format_version": None,
        "availability": availability,
        "sha256": sha256,
        "bytes": byte_count,
        "sensitivity": "private",
        "redistribution": "runtime-only",
    }


def software_identity() -> dict[str, Any]:
    return {
        "software_id": "ase",
        "version": "3.26.0",
        "build_id": None,
        "executable_sha256": HASH_B,
        "identity_status": "exact-match",
        "version_evidence": [
            file_ref("ase-version.txt", "version-evidence", "plain-text")
        ],
        "capability_profile_id": "ase-structure-transform",
    }


def producer() -> dict[str, Any]:
    return {
        "skill_id": "wave0-structure-contracts",
        "skill_version": "1.0.0",
        "tool_id": "schema-fixture-builder",
        "tool_version": "1.0.0",
        "generated_utc": NOW,
    }


def maturity() -> dict[str, Any]:
    return {
        "implementation": "implemented",
        "validation": "synthetic-validated",
        "claim_ceiling": "input_gates_only",
    }


def gate_summary(
    status: str = "pass", semantic_schema: str | None = None
) -> dict[str, Any]:
    passed = status == "pass"
    summary = {
        "status": status,
        "maximum_action": "stage-local-files" if passed else "inspect-only",
        "claim_ceiling": "input_gates_only" if passed else "no_positive_claim",
        "checks": [
            {
                "check_id": "structure-contract-check",
                "status": "pass" if passed else "blocked",
                "decisive": True,
                "finding_codes": [] if passed else ["fixture-blocked"],
                "evidence_refs": [],
                "validated_by": {
                    "actor_type": "deterministic-tool",
                    "actor_id": "wave0-schema-tests",
                    "role": "validator",
                },
                "validated_utc": NOW,
                "limitations": [],
            }
        ],
    }
    if passed and semantic_schema is not None:
        summary["checks"].extend(
            {
                "check_id": finding_id,
                "status": "pass",
                "decisive": True,
                "finding_codes": [],
                "evidence_refs": [],
                "validated_by": {
                    "actor_type": "deterministic-tool",
                    "actor_id": "wave0-schema-tests",
                    "role": "validator",
                },
                "validated_utc": NOW,
                "limitations": [],
            }
            for finding_id in sorted(REQUIRED_SEMANTIC_OBLIGATIONS[semantic_schema])
        )
    return summary


def readiness(status: str = "ready", *blockers: str) -> dict[str, Any]:
    return {
        "status": status,
        "blocker_codes": list(blockers),
        "decision_ref": None,
    }


def string_parameter(name: str, value: str) -> dict[str, Any]:
    return {
        "name": name,
        "value_kind": "string",
        "number_value": None,
        "integer_value": None,
        "boolean_value": None,
        "string_value": value,
        "integer_vector3_value": None,
        "integer_matrix3_value": None,
        "number_vector_value": None,
        "number_matrix3_value": None,
        "unit": None,
        "source": "protocol",
        "source_ref": None,
        "decisive": True,
    }


def integer_state(value: int) -> dict[str, Any]:
    return {
        "status": "known",
        "value": value,
        "source": "user",
        "evidence_refs": [],
    }


def positive_integer_state(value: int) -> dict[str, Any]:
    return {
        "status": "known",
        "value": value,
        "source": "user",
        "evidence_refs": [],
    }


def periodic_snapshot() -> dict[str, Any]:
    return {
        "contract_name": "structure-snapshot",
        "schema_version": "1.0",
        "snapshot_id": "snapshot-si2-ready",
        "structure_kind": "periodic-crystal",
        "periodicity": {
            "dimensions": 3,
            "pbc": [True, True, True],
            "boundary_condition": "periodic-3d",
        },
        "cell": {
            "status": "present",
            "vectors_ang": [
                [5.43, 0.0, 0.0],
                [0.0, 5.43, 0.0],
                [0.0, 0.0, 5.43],
            ],
            "rank": 3,
        },
        "sites": [
            {
                "site_id": "site-si-000",
                "ordinal": 0,
                "element": "Si",
                "atomic_number": 14,
                "isotope": None,
                "occupancy": 1.0,
                "ordering_state": "ordered",
                "cartesian_ang": [0.0, 0.0, 0.0],
                "fractional": [0.0, 0.0, 0.0],
                "formal_charge_e": None,
                "magnetic_moment_mu_b": None,
            },
            {
                "site_id": "site-si-001",
                "ordinal": 1,
                "element": "Si",
                "atomic_number": 14,
                "isotope": None,
                "occupancy": 1.0,
                "ordering_state": "ordered",
                "cartesian_ang": [1.3575, 1.3575, 1.3575],
                "fractional": [0.25, 0.25, 0.25],
                "formal_charge_e": None,
                "magnetic_moment_mu_b": None,
            },
        ],
        "composition": {
            "formula": "Si2",
            "elements": [{"element": "Si", "site_count": 2, "occupancy_sum": 2.0}],
        },
        "charge_state": {
            "status": "known",
            "net_charge_e": 0.0,
            "source": "user",
            "evidence_refs": [],
        },
        "spin_state": {
            "status": "not-applicable",
            "multiplicity": None,
            "total_magnetization_mu_b": None,
            "source": "user",
            "evidence_refs": [],
        },
        "constraints": [],
        "identity": {
            "algorithm": "sha256-canonical-ordered-structure-v1",
            "value": HASH_B,
            "canonicalization": "ordered-sites-cartesian-cell-v1",
            "coordinate_precision_ang": 1.0e-8,
            "site_order_sha256": HASH_C,
        },
        "source_refs": [],
        "source_files": [
            file_ref(
                "silicon.cif",
                "source-structure",
                "cif",
                "chemical/x-cif",
            )
        ],
        "calculation_readiness": readiness(),
        "validation": gate_summary(semantic_schema="snapshot"),
        "maturity": maturity(),
        "provenance": producer(),
        "limitations": [],
        "extension_refs": [],
    }


def molecular_manifest() -> dict[str, Any]:
    snapshot = record_ref(
        "structure-snapshot", "snapshot-h2-molecule", "molecular-geometry"
    )
    return {
        "contract_name": "molecular-structure-manifest",
        "schema_version": "1.0",
        "molecular_structure_id": "molecule-h2-singlet",
        "snapshot_ref": snapshot,
        "net_charge": integer_state(0),
        "multiplicity": positive_integer_state(1),
        "electron_count": {
            "status": "known",
            "value": 2,
            "derivation": "from-charge-and-nuclei",
            "evidence_refs": [],
        },
        "connectivity": {
            "status": "explicit",
            "backend": None,
            "bonds": [
                {
                    "bond_id": "bond-h-h",
                    "site_ids": ["site-h-000", "site-h-001"],
                    "order": "single",
                    "source": "explicit",
                    "evidence_refs": [],
                }
            ],
            "limitations": [],
        },
        "fragments": [
            {
                "fragment_id": "fragment-whole-h2",
                "site_ids": ["site-h-000", "site-h-001"],
                "role": "whole-molecule",
                "net_charge": integer_state(0),
                "multiplicity": positive_integer_state(1),
            }
        ],
        "conformer": {
            "conformer_id": "conformer-h2-ground",
            "state_label": "equilibrium candidate",
            "parent_conformer_ref": None,
            "generation_method": "user-supplied",
            "energy_ranking_status": "not-assessed",
        },
        "electronic_state": {
            "state_label": "X1Sigma",
            "state_kind": "ground",
            "root_index": None,
            "symmetry_label": "1Sigma-g-plus",
            "evidence_refs": [],
        },
        "isotopes": [],
        "constraints": [],
        "extraction_boundary": {
            "kind": "native-molecule",
            "parent_periodic_snapshot_ref": None,
            "transformation_ref": None,
            "capping_policy": "none",
            "created_site_ids": [],
            "removed_site_ids": [],
            "capped_site_ids": [],
            "boundary_decision_ref": None,
        },
        "calculation_readiness": readiness(),
        "validation": gate_summary(semantic_schema="molecular"),
        "maturity": maturity(),
        "provenance": producer(),
        "limitations": [],
        "extension_refs": [],
    }


def site_mapping(
    mapping_id: str,
    parent: dict[str, Any],
    parent_site_id: str | None,
    child: dict[str, Any],
    child_site_id: str | None,
    relation: str,
    image_shift: list[int] | None,
    confidence: str,
) -> dict[str, Any]:
    return {
        "mapping_id": mapping_id,
        "parent_ref": copy.deepcopy(parent),
        "parent_site_id": parent_site_id,
        "child_ref": copy.deepcopy(child),
        "child_site_id": child_site_id,
        "relation": relation,
        "image_shift": image_shift,
        "confidence": confidence,
        "rationale_code": f"{relation}-by-fixture",
    }


def rich_blocked_transformation() -> dict[str, Any]:
    parent_one = record_ref("structure-snapshot", "snapshot-parent-one", "parent")
    parent_two = record_ref(
        "structure-snapshot", "snapshot-parent-two", "parent", HASH_B
    )
    child_one = record_ref("structure-snapshot", "snapshot-child-one", "child", HASH_B)
    child_two = record_ref("structure-snapshot", "snapshot-child-two", "child", HASH_C)
    return {
        "contract_name": "structure-transformation-manifest",
        "schema_version": "1.0",
        "transformation_id": "transform-merge-rich",
        "operation_class": "merge",
        "operation_profile_id": "merge-preserve-provenance-v1",
        "parents": [parent_one, parent_two],
        "children": [child_one, child_two],
        "backend": software_identity(),
        "parameters": [string_parameter("merge-policy", "preserve-source-order")],
        "random_seed": None,
        "site_mapping": [
            site_mapping(
                "mapping-replicated-zero",
                parent_one,
                "site-source-one",
                child_one,
                "site-child-one",
                "replicated",
                [0, 0, 0],
                "exact",
            ),
            site_mapping(
                "mapping-replicated-image",
                parent_one,
                "site-source-one",
                child_two,
                "site-child-image",
                "replicated",
                [1, 0, 0],
                "exact",
            ),
            site_mapping(
                "mapping-created-cap",
                parent_two,
                None,
                child_one,
                "site-created-cap",
                "created",
                None,
                "declared",
            ),
            site_mapping(
                "mapping-removed-old",
                parent_two,
                "site-removed-old",
                child_one,
                None,
                "removed",
                None,
                "exact",
            ),
            site_mapping(
                "mapping-capped-boundary",
                parent_two,
                "site-boundary-parent",
                child_two,
                "site-boundary-child",
                "capped",
                None,
                "ambiguous",
            ),
            site_mapping(
                "mapping-merged-source-one",
                parent_one,
                "site-merge-source-one",
                child_one,
                "site-merged-child",
                "merged",
                None,
                "exact",
            ),
            site_mapping(
                "mapping-merged-source-two",
                parent_two,
                "site-merge-source-two",
                child_one,
                "site-merged-child",
                "merged",
                None,
                "exact",
            ),
            site_mapping(
                "mapping-split-child-one",
                parent_one,
                "site-split-source",
                child_one,
                "site-split-child-one",
                "split",
                None,
                "declared",
            ),
            site_mapping(
                "mapping-split-child-two",
                parent_one,
                "site-split-source",
                child_two,
                "site-split-child-two",
                "split",
                None,
                "declared",
            ),
        ],
        "mapping_status": "ambiguous",
        "roundtrip": {
            "classification": "lossy",
            "comparison_snapshot_ref": None,
            "tolerance_ang": None,
            "evidence_refs": [],
            "loss_codes": ["boundary-sites-changed"],
        },
        "calculation_use": readiness("blocked", "mapping-ambiguous"),
        "validation": gate_summary("blocked"),
        "maturity": maturity(),
        "provenance": producer(),
        "limitations": ["Boundary mapping requires a human decision."],
        "extension_refs": [],
    }


def ready_exact_transformation() -> dict[str, Any]:
    parent = record_ref("structure-snapshot", "snapshot-before-reorder", "parent")
    child = record_ref("structure-snapshot", "snapshot-after-reorder", "child", HASH_B)
    return {
        "contract_name": "structure-transformation-manifest",
        "schema_version": "1.0",
        "transformation_id": "transform-reorder-exact",
        "operation_class": "reorder",
        "operation_profile_id": "stable-site-reorder-v1",
        "parents": [parent],
        "children": [child],
        "backend": software_identity(),
        "parameters": [string_parameter("reorder-policy", "element-then-site-id")],
        "random_seed": None,
        "site_mapping": [
            site_mapping(
                "mapping-same-site",
                parent,
                "site-si-000",
                child,
                "site-si-000",
                "same",
                [0, 0, 0],
                "exact",
            )
        ],
        "mapping_status": "exact",
        "roundtrip": {
            "classification": "exact",
            "comparison_snapshot_ref": child,
            "tolerance_ang": 0,
            "evidence_refs": [
                record_ref(
                    "bundle-evidence-record",
                    "validation-reorder-roundtrip",
                    "roundtrip-evidence",
                )
            ],
            "loss_codes": [],
        },
        "calculation_use": readiness(),
        "validation": gate_summary(semantic_schema="transformation"),
        "maturity": maturity(),
        "provenance": producer(),
        "limitations": [],
        "extension_refs": [],
    }


def export_manifest() -> dict[str, Any]:
    source = record_ref("structure-snapshot", "snapshot-si2-ready", "source-structure")
    reconstructed = record_ref(
        "structure-snapshot", "snapshot-si2-poscar-roundtrip", "roundtrip"
    )
    return {
        "contract_name": "structure-export-manifest",
        "schema_version": "1.0",
        "export_id": "export-si2-poscar",
        "snapshot_ref": source,
        "transformation_refs": [
            record_ref(
                "structure-transformation-manifest",
                "transform-reorder-exact",
                "pre-export-transform",
            )
        ],
        "target": {
            "format": "poscar",
            "format_version": "5",
            "target_code": "vasp",
            "coordinate_representation": "fractional",
            "cell_representation": "explicit",
        },
        "export_files": [file_ref("POSCAR", "structure-export", "poscar")],
        "atom_order_mapping": [
            {
                "output_index": 0,
                "output_label": "Si1",
                "source_site_id": "site-si-000",
            },
            {
                "output_index": 1,
                "output_label": "Si2",
                "source_site_id": "site-si-001",
            },
        ],
        "unit_mapping": {
            "input_length_unit": "angstrom",
            "output_length_unit": "angstrom",
            "conversion_factor": 1.0,
        },
        "code_profile_id": "vasp-poscar-export-v1",
        "roundtrip_validation": {
            "classification": "exact",
            "reconstructed_snapshot_ref": reconstructed,
            "tolerance_ang": 0,
            "evidence_refs": [
                record_ref(
                    "bundle-evidence-record",
                    "validation-poscar-roundtrip",
                    "roundtrip-evidence",
                )
            ],
            "loss_codes": [],
        },
        "calculation_use": readiness(),
        "validation": gate_summary(semantic_schema="export"),
        "maturity": maturity(),
        "provenance": producer(),
        "limitations": [],
        "extension_refs": [],
    }


def trajectory_manifest() -> dict[str, Any]:
    run_ref = record_ref(
        "calculation-record-envelope", "calculation-md-si2", "source-run"
    )
    structure_ref = record_ref(
        "structure-snapshot", "snapshot-si2-md-initial", "initial-structure"
    )
    return {
        "contract_name": "atomistic-trajectory-manifest",
        "schema_version": "1.0",
        "trajectory_id": "trajectory-si2-md",
        "sequence_kind": "time-trajectory",
        "initial_structure_ref": structure_ref,
        "source_run_ref": run_ref,
        "topology": {
            "status": "present",
            "ref": record_ref(
                "structure-snapshot", "snapshot-si2-md-topology", "topology"
            ),
        },
        "files": [
            file_ref(
                "trajectory.xtc",
                "trajectory",
                "xtc",
                "application/octet-stream",
                byte_count=4096,
            )
        ],
        "format": {"name": "xtc", "version": None, "compression": "lossless"},
        "frame_count": 100,
        "atom_count": 2,
        "site_order": ["site-si-000", "site-si-001"],
        "pbc": [True, True, True],
        "cell_mode": "fixed",
        "coordinate_unit": "nanometer",
        "time_axis": {
            "status": "present-regular",
            "start": 0.0,
            "step": 0.002,
            "unit": "ps",
            "values_file": None,
        },
        "available_fields": [
            {
                "name": "positions",
                "unit": "nanometer",
                "file_role": "trajectory",
                "completeness": "all-frames",
            }
        ],
        "segments": [
            {
                "segment_id": "segment-md-main",
                "parent_segment_id": None,
                "source_run_ref": run_ref,
                "first_frame": 0,
                "last_frame": 99,
                "start_step": 0,
                "end_step": 99,
                "checkpoint_ref": None,
                "continuity_from_parent": "not-applicable",
            }
        ],
        "continuity": {
            "status": "continuous",
            "gap_count": 0,
            "overlap_count": 0,
            "evidence_refs": [
                record_ref(
                    "bundle-evidence-record",
                    "validation-trajectory-continuity",
                    "continuity-evidence",
                )
            ],
        },
        "frame_index": file_ref(
            "trajectory-index.json",
            "frame-index",
            "json",
            "application/json",
            byte_count=1024,
        ),
        "analysis_readiness": readiness(),
        "validation": gate_summary(semantic_schema="trajectory"),
        "maturity": maturity(),
        "provenance": producer(),
        "limitations": [],
        "extension_refs": [],
    }


RECORD_ID_FIELDS = {
    "structure-snapshot": "snapshot_id",
    "molecular-structure-manifest": "molecular_structure_id",
    "structure-transformation-manifest": "transformation_id",
    "structure-export-manifest": "export_id",
    "atomistic-trajectory-manifest": "trajectory_id",
}
RECORD_REF_FIELDS = {
    "contract_name",
    "schema_version",
    "record_id",
    "sha256",
    "role",
}


def document_identity(document: dict[str, Any]) -> tuple[str, str, str]:
    contract_name = document["contract_name"]
    id_field = RECORD_ID_FIELDS.get(contract_name, "record_id")
    return contract_name, document["schema_version"], document[id_field]


def iter_record_refs(node: Any):
    if isinstance(node, dict):
        if set(node) == RECORD_REF_FIELDS:
            yield node
            return
        for value in node.values():
            yield from iter_record_refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from iter_record_refs(value)


def write_json_document(
    path: Path,
    document: dict[str, Any],
    *,
    pretty: bool,
    trailing_newline: bool = True,
) -> str:
    if pretty:
        text = json.dumps(document, ensure_ascii=False, indent=2)
    else:
        text = json.dumps(
            document,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    if trailing_newline:
        text += "\n"
    raw = text.encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def audit_record_ref_bundle(paths: list[Path]) -> set[str]:
    findings: set[str] = set()
    documents: dict[tuple[str, str, str], dict[str, Any]] = {}
    raw_hashes: dict[tuple[str, str, str], str] = {}
    order: dict[tuple[str, str, str], int] = {}

    for index, path in enumerate(paths):
        raw = path.read_bytes()
        try:
            document = json.loads(raw.decode("utf-8"))
            identity = document_identity(document)
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
            findings.add("record-reference-target-not-utf8-json")
            continue
        if identity in documents:
            findings.add("record-reference-target-identity-duplicate")
            continue
        documents[identity] = document
        raw_hashes[identity] = hashlib.sha256(raw).hexdigest()
        order[identity] = index

    edges: dict[tuple[str, str, str], set[tuple[str, str, str]]] = {
        identity: set() for identity in documents
    }
    for source, document in documents.items():
        for ref in iter_record_refs(document):
            target = (
                ref["contract_name"],
                ref["schema_version"],
                ref["record_id"],
            )
            if target not in documents:
                findings.add("record-reference-target-missing")
                continue
            edges[source].add(target)
            if source == target:
                findings.add("record-reference-self")
            if order[target] >= order[source]:
                findings.add("record-reference-topology-order-invalid")
            if raw_hashes[target] != ref["sha256"]:
                findings.add("record-reference-hash-mismatch")

    visiting: set[tuple[str, str, str]] = set()
    visited: set[tuple[str, str, str]] = set()

    def visit(node: tuple[str, str, str]) -> None:
        if node in visiting:
            findings.add("record-reference-cycle")
            return
        if node in visited:
            return
        visiting.add(node)
        for target in edges[node]:
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for identity in edges:
        visit(identity)

    if findings:
        findings.add("record-reference-dag-invalid")
    return findings


PERIODIC_STRUCTURE_DIGEST = (
    "8b70d7b8343ac62b0d0b07777e2e7a0b62ff13e39562e639408825f68d334b23"
)
PERIODIC_SITE_ORDER_DIGEST = (
    "4334fa29c932a37dd664b66da0e84a20cdd76db96ba3570ecb59217901059697"
)
PARSER_COMPONENT_HASH = "d" * 64


def sealed_periodic_snapshot(snapshot_id: str) -> dict[str, Any]:
    snapshot = periodic_snapshot()
    snapshot["snapshot_id"] = snapshot_id
    snapshot["identity"]["value"] = PERIODIC_STRUCTURE_DIGEST
    snapshot["identity"]["site_order_sha256"] = PERIODIC_SITE_ORDER_DIGEST
    snapshot["source_refs"] = []
    return snapshot


def h2_snapshot() -> dict[str, Any]:
    snapshot = sealed_periodic_snapshot("snapshot-h2-molecule")
    snapshot["structure_kind"] = "isolated-molecule"
    snapshot["periodicity"] = {
        "dimensions": 0,
        "pbc": [False, False, False],
        "boundary_condition": "isolated",
    }
    snapshot["cell"] = {"status": "not-applicable", "vectors_ang": None, "rank": 0}
    snapshot["sites"] = [
        {
            "site_id": "site-h-000",
            "ordinal": 0,
            "element": "H",
            "atomic_number": 1,
            "isotope": None,
            "occupancy": 1.0,
            "ordering_state": "ordered",
            "cartesian_ang": [0.0, 0.0, 0.0],
            "fractional": None,
            "formal_charge_e": None,
            "magnetic_moment_mu_b": None,
        },
        {
            "site_id": "site-h-001",
            "ordinal": 1,
            "element": "H",
            "atomic_number": 1,
            "isotope": None,
            "occupancy": 1.0,
            "ordering_state": "ordered",
            "cartesian_ang": [0.74, 0.0, 0.0],
            "fractional": None,
            "formal_charge_e": None,
            "magnetic_moment_mu_b": None,
        },
    ]
    snapshot["composition"] = {
        "formula": "H2",
        "elements": [{"element": "H", "site_count": 2, "occupancy_sum": 2.0}],
    }
    snapshot["identity"][
        "value"
    ] = "09f613fef1d8cba75e7c96c1e7f15aa3f6e7ac163a5cac0f325c48469956cef6"
    snapshot["identity"][
        "site_order_sha256"
    ] = "cbd1e70c1bfb9e27e4e5995089031493d7d25be3a41b312b6485e9b6a5304959"
    return snapshot


def generic_record(contract_name: str, record_id: str, **extra: Any) -> dict[str, Any]:
    return {
        "contract_name": contract_name,
        "schema_version": "1.0",
        "record_id": record_id,
        **extra,
    }


def semantic_record_view(
    data: dict[str, Any], sha256: str, index: int
) -> dict[str, Any]:
    contract_name, schema_version, record_id = document_identity(data)
    return {
        "contract_name": contract_name,
        "schema_version": schema_version,
        "record_id": record_id,
        "index": index,
        "data": data,
        "raw_sha256": sha256,
        "lifecycle": "active",
        "integrity_verified_active": True,
    }


def parser_observation(
    parser_id: str, source_raw_sha256: str, observations: dict[str, Any]
) -> tuple[dict[str, Any], ...]:
    return (
        {
            "parser_id": parser_id,
            "parser_version": "1.0.0",
            "parser_component_sha256": PARSER_COMPONENT_HASH,
            "source_raw_sha256": source_raw_sha256,
            "status": "pass",
            "observations": observations,
        },
    )


def semantic_artifact_view(
    ref: dict[str, Any],
    index: int,
    observations: dict[str, Any] | None = None,
    parser_id: str = "vibe.structure.synthetic-parser",
) -> dict[str, Any]:
    return {
        "label": ref["label"],
        "index": index,
        "metadata": copy.deepcopy(ref),
        "raw_sha256": ref["sha256"],
        "bytes": ref["bytes"],
        "integrity_verified": True,
        "parser_observations": (
            ()
            if observations is None
            else parser_observation(parser_id, ref["sha256"], observations)
        ),
    }


def semantic_context(
    records: list[tuple[dict[str, Any], str]],
    current_position: int,
    *,
    artifacts: list[dict[str, Any]] | None = None,
    registry_snapshots: dict[str, Any] | None = None,
) -> dict[str, Any]:
    views: dict[tuple[str, str, str], dict[str, Any]] = {}
    ordered_views: list[dict[str, Any]] = []
    for index, (data, digest) in enumerate(records):
        view = semantic_record_view(data, digest, index)
        identity = (
            view["contract_name"],
            view["schema_version"],
            view["record_id"],
        )
        views[identity] = view
        ordered_views.append(view)
    artifact_map = {artifact["label"]: artifact for artifact in (artifacts or [])}
    return {
        "current_record": ordered_views[current_position],
        "current_record_index": current_position,
        "records_by_identity": views,
        "artifacts_by_label": artifact_map,
        "core_checks": {
            "record-reference-dag": {"status": "pass", "finding_codes": []},
            "record-reference-integrity": {"status": "pass", "finding_codes": []},
            "artifact-integrity": {"status": "pass", "finding_codes": []},
            "privacy-boundary": {"status": "pass", "finding_codes": []},
        },
        "registry_snapshots": registry_snapshots or {},
    }


def snapshot_semantic_context() -> dict[str, Any]:
    snapshot = sealed_periodic_snapshot("snapshot-si2-ready")
    return semantic_context([(snapshot, HASH_A)], 0)


def molecular_semantic_context() -> dict[str, Any]:
    snapshot = h2_snapshot()
    molecule = molecular_manifest()
    return semantic_context([(snapshot, HASH_A), (molecule, HASH_C)], 1)


def molecular_extraction_negative_semantic_context() -> dict[str, Any]:
    parent = sealed_periodic_snapshot("snapshot-periodic-parent")
    child = h2_snapshot()
    parent_ref = record_ref(
        "structure-snapshot", "snapshot-periodic-parent", "parent", HASH_A
    )
    child_ref = record_ref(
        "structure-snapshot", "snapshot-h2-molecule", "child", HASH_B
    )
    decision = generic_record("decision-record", "decision-extraction-boundary")
    transform = ready_exact_transformation()
    transform["transformation_id"] = "transform-extract-cluster"
    transform["operation_class"] = "extract-cluster"
    transform["operation_profile_id"] = "extract-cluster-declared-v1"
    transform["parents"] = [parent_ref]
    transform["children"] = [child_ref]
    transform["site_mapping"] = [
        site_mapping(
            "mapping-remove-si-zero",
            parent_ref,
            "site-si-000",
            child_ref,
            None,
            "removed",
            None,
            "exact",
        ),
        site_mapping(
            "mapping-remove-si-one",
            parent_ref,
            "site-si-001",
            child_ref,
            None,
            "removed",
            None,
            "exact",
        ),
        site_mapping(
            "mapping-create-h-zero",
            parent_ref,
            None,
            child_ref,
            "site-h-000",
            "created",
            None,
            "exact",
        ),
        site_mapping(
            "mapping-create-h-one",
            parent_ref,
            None,
            child_ref,
            "site-h-001",
            "created",
            None,
            "exact",
        ),
    ]
    transform["roundtrip"] = {
        "classification": "lossy",
        "comparison_snapshot_ref": None,
        "tolerance_ang": None,
        "evidence_refs": [],
        "loss_codes": ["periodic-sites-replaced"],
    }
    transform["calculation_use"] = readiness("blocked", "lossy-extraction-transform")
    transform["validation"] = gate_summary("blocked")
    molecule = molecular_manifest()
    molecule["snapshot_ref"]["sha256"] = HASH_B
    molecule["extraction_boundary"] = {
        "kind": "cluster-from-periodic",
        "parent_periodic_snapshot_ref": record_ref(
            "structure-snapshot",
            "snapshot-periodic-parent",
            "extraction-parent",
            HASH_A,
        ),
        "transformation_ref": record_ref(
            "structure-transformation-manifest",
            "transform-extract-cluster",
            "extraction-transform",
            HASH_C,
        ),
        "capping_policy": "none",
        "created_site_ids": ["site-h-000"],
        "removed_site_ids": ["site-si-000", "site-si-001"],
        "capped_site_ids": [],
        "boundary_decision_ref": record_ref(
            "decision-record",
            "decision-extraction-boundary",
            "boundary-decision",
            HASH_A,
        ),
    }
    return semantic_context(
        [
            (parent, HASH_A),
            (child, HASH_B),
            (decision, HASH_A),
            (transform, HASH_C),
            (molecule, HASH_C),
        ],
        4,
    )


def transformation_semantic_context() -> dict[str, Any]:
    parent = sealed_periodic_snapshot("snapshot-before-reorder")
    child = sealed_periodic_snapshot("snapshot-after-reorder")
    evidence = generic_record("bundle-evidence-record", "validation-reorder-roundtrip")
    transform = ready_exact_transformation()
    transform["site_mapping"].append(
        site_mapping(
            "mapping-same-site-one",
            transform["parents"][0],
            "site-si-001",
            transform["children"][0],
            "site-si-001",
            "same",
            [0, 0, 0],
            "exact",
        )
    )
    return semantic_context(
        [
            (parent, HASH_A),
            (child, HASH_B),
            (evidence, HASH_A),
            (transform, HASH_C),
        ],
        3,
        registry_snapshots={
            "known_operations": ["reorder"],
            "operation_templates": {},
        },
    )


def export_semantic_context() -> dict[str, Any]:
    source = sealed_periodic_snapshot("snapshot-si2-ready")
    reconstructed = sealed_periodic_snapshot("snapshot-si2-poscar-roundtrip")
    evidence = generic_record("bundle-evidence-record", "validation-poscar-roundtrip")
    export = export_manifest()
    export["transformation_refs"] = []
    poscar_ref = export["export_files"][0]
    parsed = {
        "format": "poscar",
        "target_code": "vasp",
        "coordinate_representation": "fractional",
        "cell_representation": "explicit",
        "atom_count": 2,
        "atom_labels": ["Si1", "Si2"],
        "length_unit": "angstrom",
        "cartesian_coordinates": [
            [0.0, 0.0, 0.0],
            [1.3575, 1.3575, 1.3575],
        ],
        "cell_vectors": [
            [5.43, 0.0, 0.0],
            [0.0, 5.43, 0.0],
            [0.0, 0.0, 5.43],
        ],
        "lost_features": [],
    }
    profile = {
        "format": "poscar",
        "target_code": "vasp",
        "coordinate_representation": "fractional",
        "cell_representation": "explicit",
        "atom_label_pattern": r"Si[1-9][0-9]*",
        "preserves_features": [
            "cell",
            "labels",
            "precision",
            "site-identity",
        ],
        "loss_codes": {
            "cell": "cell-lost",
            "labels": "labels-lost",
            "precision": "precision-lost",
            "site-identity": "site-identity-lost",
        },
    }
    artifact = semantic_artifact_view(
        poscar_ref,
        0,
        parsed,
        "vibe.structure-export.poscar-v1",
    )
    return semantic_context(
        [
            (source, HASH_A),
            (reconstructed, HASH_A),
            (evidence, HASH_A),
            (export, HASH_C),
        ],
        3,
        artifacts=[artifact],
        registry_snapshots={
            "structure_export_profiles": {"vasp-poscar-export-v1": profile}
        },
    )


def trajectory_semantic_context() -> dict[str, Any]:
    initial = sealed_periodic_snapshot("snapshot-si2-md-initial")
    topology = sealed_periodic_snapshot("snapshot-si2-md-topology")
    source_run = generic_record("calculation-record-envelope", "calculation-md-si2")
    evidence = generic_record(
        "bundle-evidence-record", "validation-trajectory-continuity"
    )
    trajectory = trajectory_manifest()
    trajectory["frame_count"] = 3
    trajectory["segments"][0]["last_frame"] = 2
    trajectory["segments"][0]["end_step"] = 2
    trajectory_file_ref = trajectory["files"][0]
    frame_index_ref = trajectory["frame_index"]
    primary = semantic_artifact_view(
        trajectory_file_ref,
        0,
        {
            "frame_count": 3,
            "atom_counts": [2, 2, 2],
            "site_orders": [
                ["site-si-000", "site-si-001"],
                ["site-si-000", "site-si-001"],
                ["site-si-000", "site-si-001"],
            ],
            "times": [0.0, 0.002, 0.004],
            "steps": [0, 1, 2],
            "cells": [
                [[5.43, 0.0, 0.0], [0.0, 5.43, 0.0], [0.0, 0.0, 5.43]],
                [[5.43, 0.0, 0.0], [0.0, 5.43, 0.0], [0.0, 0.0, 5.43]],
                [[5.43, 0.0, 0.0], [0.0, 5.43, 0.0], [0.0, 0.0, 5.43]],
            ],
        },
        "vibe.trajectory.xtc-v1",
    )
    frame_index = semantic_artifact_view(
        frame_index_ref,
        1,
        {
            "frame_indices": [0, 1, 2],
            "frame_locators": ["frame-0", "frame-1", "frame-2"],
        },
        "vibe.frame-index-json-v1",
    )
    return semantic_context(
        [
            (initial, HASH_A),
            (topology, HASH_A),
            (source_run, HASH_A),
            (evidence, HASH_A),
            (trajectory, HASH_C),
        ],
        4,
        artifacts=[primary, frame_index],
    )


SEMANTIC_CONTEXT_BUILDERS = {
    "snapshot": snapshot_semantic_context,
    "molecular": molecular_semantic_context,
    "transformation": transformation_semantic_context,
    "export": export_semantic_context,
    "trajectory": trajectory_semantic_context,
}


def semantic_context_for_obligation(obligation_id: str) -> dict[str, Any]:
    for schema_name, obligation_ids in REQUIRED_SEMANTIC_OBLIGATIONS.items():
        if obligation_id in obligation_ids:
            return SEMANTIC_CONTEXT_BUILDERS[schema_name]()
    raise KeyError(obligation_id)


def current_semantic_data(context: dict[str, Any]) -> dict[str, Any]:
    return context["current_record"]["data"]


def record_data(
    context: dict[str, Any], contract_name: str, record_id: str
) -> dict[str, Any]:
    return context["records_by_identity"][(contract_name, "1.0", record_id)]["data"]


def parsed_artifact_data(context: dict[str, Any], label: str) -> dict[str, Any]:
    return context["artifacts_by_label"][label]["parser_observations"][0][
        "observations"
    ]


def minimal_negative_context(
    obligation_id: str, schema_name: str | None = None
) -> dict[str, Any]:
    if obligation_id == "molecular-extraction-lineage-mismatch":
        context = molecular_extraction_negative_semantic_context()
    else:
        context = (
            SEMANTIC_CONTEXT_BUILDERS[schema_name]()
            if schema_name is not None
            else semantic_context_for_obligation(obligation_id)
        )
    data = current_semantic_data(context)

    if obligation_id == "structure-site-identity-not-unique":
        data["sites"][1]["site_id"] = data["sites"][0]["site_id"]
    elif obligation_id == "structure-composition-site-mismatch":
        data["composition"]["elements"][0]["site_count"] = 1
    elif obligation_id == "structure-periodicity-cell-mismatch":
        data["cell"]["vectors_ang"][2] = [0.0, 0.0, 0.0]
    elif obligation_id == "structure-coordinate-representation-mismatch":
        data["sites"][1]["cartesian_ang"][0] += 0.1
    elif obligation_id == "structure-charge-spin-electron-parity-mismatch":
        data["spin_state"] = {
            "status": "known",
            "multiplicity": 2,
            "total_magnetization_mu_b": None,
            "source": "user",
            "evidence_refs": [],
        }
    elif obligation_id == "structure-identity-fingerprint-mismatch":
        data["identity"]["value"] = HASH_C
    elif obligation_id == "molecular-snapshot-hash-mismatch":
        data["snapshot_ref"]["sha256"] = HASH_C
    elif obligation_id == "molecular-site-reference-missing":
        data["connectivity"]["bonds"][0]["site_ids"][1] = "site-h-missing"
    elif obligation_id == "molecular-charge-multiplicity-electron-parity-mismatch":
        data["electron_count"]["value"] = 3
    elif obligation_id == "molecular-connectivity-inconsistent":
        duplicate = copy.deepcopy(data["connectivity"]["bonds"][0])
        duplicate["bond_id"] = "bond-h-h-duplicate"
        duplicate["site_ids"].reverse()
        data["connectivity"]["bonds"].append(duplicate)
    elif obligation_id == "molecular-fragment-coverage-inconsistent":
        data["fragments"][0]["site_ids"].pop()
    elif obligation_id == "molecular-extraction-lineage-mismatch":
        pass
    elif obligation_id == "structure-transform-reference-hash-mismatch":
        data["parents"][0]["sha256"] = HASH_C
    elif obligation_id == "structure-transform-mapping-id-not-unique":
        data["site_mapping"][1]["mapping_id"] = data["site_mapping"][0]["mapping_id"]
    elif obligation_id == "structure-transform-site-reference-missing":
        data["site_mapping"][0]["child_site_id"] = "site-missing"
    elif obligation_id == "structure-transform-mapping-coverage-incomplete":
        data["site_mapping"].pop()
    elif obligation_id == "structure-transform-relation-cardinality-mismatch":
        data["site_mapping"][0]["relation"] = "replicated"
    elif obligation_id == "structure-transform-image-shift-inconsistent":
        data["site_mapping"][0]["image_shift"] = [1, 0, 0]
    elif obligation_id == "structure-transform-operation-semantics-mismatch":
        data["operation_class"] = "add-sites"
    elif obligation_id == "structure-transform-roundtrip-fingerprint-mismatch":
        child = record_data(context, "structure-snapshot", "snapshot-after-reorder")
        child["sites"][0]["cartesian_ang"][0] += 0.1
    elif obligation_id == "structure-transform-tolerance-unverified":
        data["roundtrip"]["classification"] = "equivalent-with-tolerance"
        data["roundtrip"]["tolerance_ang"] = 0.01
        child = record_data(context, "structure-snapshot", "snapshot-after-reorder")
        child["sites"][0]["cartesian_ang"][0] += 0.1
    elif obligation_id == "structure-export-source-hash-mismatch":
        data["snapshot_ref"]["sha256"] = HASH_C
    elif obligation_id == "structure-export-file-hash-mismatch":
        data["export_files"][0]["sha256"] = HASH_C
    elif obligation_id == "structure-export-output-index-not-unique":
        data["atom_order_mapping"][1]["output_index"] = 0
    elif obligation_id == "structure-export-atom-map-incomplete":
        data["atom_order_mapping"][1]["source_site_id"] = "site-missing"
    elif obligation_id == "structure-export-unit-map-inconsistent":
        data["unit_mapping"]["conversion_factor"] = 2.0
    elif obligation_id == "structure-export-target-profile-mismatch":
        parsed_artifact_data(context, "POSCAR")["format"] = "xyz"
    elif obligation_id == "structure-export-roundtrip-fingerprint-mismatch":
        reconstructed = record_data(
            context, "structure-snapshot", "snapshot-si2-poscar-roundtrip"
        )
        reconstructed["sites"][0]["cartesian_ang"][0] += 0.1
    elif obligation_id == "structure-export-loss-undisclosed":
        profile = context["registry_snapshots"]["structure_export_profiles"][
            "vasp-poscar-export-v1"
        ]
        profile["preserves_features"].remove("labels")
        parsed_artifact_data(context, "POSCAR")["lost_features"] = ["labels"]
    elif obligation_id == "trajectory-source-lineage-hash-mismatch":
        data["source_run_ref"]["sha256"] = HASH_C
    elif obligation_id == "trajectory-file-hash-mismatch":
        data["files"][0]["sha256"] = HASH_C
    elif obligation_id == "trajectory-segment-id-not-unique":
        duplicate = copy.deepcopy(data["segments"][0])
        duplicate["first_frame"] = 1
        duplicate["last_frame"] = 2
        duplicate["start_step"] = 1
        duplicate["end_step"] = 2
        data["segments"].append(duplicate)
    elif obligation_id == "trajectory-frame-index-not-unique":
        parsed_artifact_data(context, "trajectory-index.json")["frame_indices"] = [
            0,
            0,
            2,
        ]
    elif obligation_id == "trajectory-frame-count-mismatch":
        parsed_artifact_data(context, "trajectory.xtc")["frame_count"] = 2
    elif obligation_id == "trajectory-atom-count-site-order-mismatch":
        parsed_artifact_data(context, "trajectory.xtc")["atom_counts"][1] = 1
    elif obligation_id == "trajectory-segment-range-invalid":
        data["segments"][0]["last_frame"] = 3
    elif obligation_id == "trajectory-continuity-mismatch":
        parsed_artifact_data(context, "trajectory.xtc")["steps"] = [0, 2, 3]
    elif obligation_id == "trajectory-time-axis-nonmonotonic":
        parsed_artifact_data(context, "trajectory.xtc")["times"][1] = 0.0
    elif obligation_id == "trajectory-pbc-cell-mismatch":
        parsed_artifact_data(context, "trajectory.xtc")["cells"][1][0][0] = 5.5
    elif obligation_id == "record-reference-dag-invalid":
        context["core_checks"]["record-reference-dag"] = {
            "status": "fail",
            "finding_codes": ["RECORD_REF_FORWARD_REFERENCE"],
        }
    else:
        raise KeyError(obligation_id)
    return context


class Wave0StructureContractTests(unittest.TestCase):
    maxDiff = None

    def assert_valid(self, schema_name: str, instance: dict[str, Any]) -> None:
        errors = list(VALIDATORS[schema_name].iter_errors(instance))
        details = "\n".join(
            f"/{'/'.join(map(str, error.absolute_path))}: {error.message}"
            for error in sorted(errors, key=lambda item: str(item.absolute_path))
        )
        self.assertFalse(errors, details)

    def assert_invalid(self, schema_name: str, instance: dict[str, Any]) -> None:
        errors = list(VALIDATORS[schema_name].iter_errors(instance))
        self.assertTrue(errors, f"{schema_name} unexpectedly accepted invalid record")

    def test_schemas_are_draft_2020_12_and_strict_objects(self) -> None:
        for name, schema in SCHEMAS.items():
            with self.subTest(schema=name):
                self.assertEqual(
                    schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
                )
                self.assertTrue(schema["$id"].startswith("urn:vibe-dft-skills:"))
                Draft202012Validator.check_schema(schema)
                self._assert_all_typed_objects_are_closed(schema, path=name)

    def test_schema_document_kind_and_record_id_metadata_are_exact(self) -> None:
        common = SCHEMAS["common"]
        self.assertEqual(common["x-vibe-document-kind"], "definition-library")
        self.assertNotIn("x-vibe-record-id-field", common)

        expected_record_ids = {
            "snapshot": "snapshot_id",
            "molecular": "molecular_structure_id",
            "transformation": "transformation_id",
            "export": "export_id",
            "trajectory": "trajectory_id",
        }
        for schema_name, id_field in expected_record_ids.items():
            schema = SCHEMAS[schema_name]
            with self.subTest(schema=schema_name):
                self.assertEqual(
                    schema["x-vibe-document-kind"], "content-addressed-record"
                )
                self.assertEqual(schema["x-vibe-record-id-field"], id_field)
                self.assertIn(id_field, schema["required"])
                self.assertIn(id_field, schema["properties"])
                id_schema = schema["properties"][id_field]
                self.assertTrue(
                    id_schema.get("type") == "string"
                    or id_schema.get("$ref", "").endswith("#/$defs/safeId")
                )

    def test_semantic_obligation_catalogs_are_stable_and_fail_closed(self) -> None:
        expected_keys = {
            "finding_id",
            "scope",
            "enforcement",
            "blocks",
            "assertion",
            "evidence_required",
        }
        for schema_name, expected_ids in REQUIRED_SEMANTIC_OBLIGATIONS.items():
            schema = SCHEMAS[schema_name]
            obligations = schema.get("x-vibe-semantic-obligations")
            with self.subTest(schema=schema_name, check="catalog"):
                self.assertIsInstance(obligations, list)
                self.assertTrue(obligations)
                self.assertIn("structural conformance only", schema["$comment"])

            actual_ids = [item["finding_id"] for item in obligations]
            with self.subTest(schema=schema_name, check="stable-ids"):
                self.assertEqual(set(actual_ids), expected_ids)
                self.assertEqual(len(actual_ids), len(set(actual_ids)))

            for obligation in obligations:
                with self.subTest(
                    schema=schema_name, finding_id=obligation["finding_id"]
                ):
                    self.assertEqual(set(obligation), expected_keys)
                    self.assertRegex(
                        obligation["finding_id"], r"^[a-z][a-z0-9-]{2,127}$"
                    )
                    self.assertIn(
                        obligation["scope"],
                        {"intra-record", "cross-record", "artifact-content"},
                    )
                    self.assertEqual(
                        obligation["enforcement"],
                        "external-semantic-validator-required",
                    )
                    self.assertIn(READINESS_SURFACES[schema_name], obligation["blocks"])
                    self.assertIn("positive-claim", obligation["blocks"])
                    self.assertTrue(obligation["assertion"].strip())
                    self.assertTrue(obligation["evidence_required"])
                    self.assertEqual(
                        len(obligation["evidence_required"]),
                        len(set(obligation["evidence_required"])),
                    )

    def test_production_evaluator_passes_every_structure_obligation(self) -> None:
        expected_result_fields = {
            "obligation_id",
            "status",
            "finding_codes",
            "location",
            "message",
            "handler_id",
        }
        expected_unique = set().union(*REQUIRED_SEMANTIC_OBLIGATIONS.values())
        self.assertEqual(bundle_semantics_structure.OBLIGATION_IDS, expected_unique)
        self.assertEqual(len(expected_unique), 40)

        evaluated_rows = 0
        for schema_name, obligation_ids in REQUIRED_SEMANTIC_OBLIGATIONS.items():
            context = SEMANTIC_CONTEXT_BUILDERS[schema_name]()
            before = copy.deepcopy(context)
            results = bundle_semantics_structure.evaluate(
                sorted(obligation_ids), context
            )
            evaluated_rows += len(results)
            self.assertEqual(context, before, f"{schema_name} context was mutated")
            self.assertEqual(len(results), len(obligation_ids))
            self.assertEqual(
                [item["obligation_id"] for item in results],
                sorted(obligation_ids),
            )
            for result in results:
                with self.subTest(
                    schema=schema_name, obligation=result["obligation_id"]
                ):
                    self.assertEqual(set(result), expected_result_fields)
                    self.assertEqual(result["status"], "pass", result)
                    self.assertEqual(result["finding_codes"], [])
                    self.assertTrue(result["location"])
                    self.assertTrue(result["message"])
                    self.assertEqual(
                        result["handler_id"],
                        f"bundle-semantics-structure.{result['obligation_id']}",
                    )
        self.assertEqual(evaluated_rows, 44)

    def test_each_of_44_advertised_obligations_has_a_minimal_negative(self) -> None:
        evaluated_rows = 0
        for schema_name, obligation_ids in REQUIRED_SEMANTIC_OBLIGATIONS.items():
            for obligation_id in sorted(obligation_ids):
                with self.subTest(schema=schema_name, obligation=obligation_id):
                    context = minimal_negative_context(obligation_id, schema_name)
                    self.assert_valid(schema_name, current_semantic_data(context))
                    results = bundle_semantics_structure.evaluate(
                        [obligation_id], context
                    )
                    evaluated_rows += len(results)
                    self.assertEqual(len(results), 1)
                    result = results[0]
                    self.assertEqual(result["obligation_id"], obligation_id)
                    self.assertEqual(result["status"], "fail", result)
                    self.assertTrue(result["finding_codes"])
                    self.assertTrue(result["location"])
                    self.assertTrue(result["message"])
                    self.assertEqual(
                        result["handler_id"],
                        f"bundle-semantics-structure.{obligation_id}",
                    )
        self.assertEqual(evaluated_rows, 44)

    def test_each_minimal_negative_is_detected_by_its_production_handler(
        self,
    ) -> None:
        checked: set[str] = set()
        for schema_name, obligation_ids in REQUIRED_SEMANTIC_OBLIGATIONS.items():
            for obligation_id in sorted(obligation_ids):
                if obligation_id in checked:
                    continue
                checked.add(obligation_id)
                context = minimal_negative_context(obligation_id, schema_name)
                original = bundle_semantics_structure._HANDLERS[obligation_id]
                try:
                    bundle_semantics_structure._HANDLERS[obligation_id] = (
                        lambda _state: None
                    )
                    result = bundle_semantics_structure.evaluate(
                        [obligation_id], context
                    )[0]
                finally:
                    bundle_semantics_structure._HANDLERS[obligation_id] = original
                with self.subTest(obligation=obligation_id):
                    self.assertEqual(
                        result["status"],
                        "pass",
                        "Negative fixture was rejected outside its named handler.",
                    )
        self.assertEqual(checked, bundle_semantics_structure.OBLIGATION_IDS)

    def test_production_evaluator_fails_closed_for_unknown_or_missing_context(
        self,
    ) -> None:
        context = snapshot_semantic_context()
        unknown = bundle_semantics_structure.evaluate(
            ["unknown-structure-obligation"], context
        )
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0]["status"], "blocked")
        self.assertEqual(
            unknown[0]["finding_codes"],
            ["SEMANTIC_OBLIGATION_HANDLER_MISSING"],
        )
        self.assertIsNone(unknown[0]["handler_id"])

        incomplete = copy.deepcopy(context)
        incomplete.pop("registry_snapshots")
        missing = bundle_semantics_structure.evaluate(
            ["structure-site-identity-not-unique"], incomplete
        )
        self.assertEqual(missing[0]["status"], "blocked")
        self.assertIn("STRUCTURE_SEMANTIC_CONTEXT_INVALID", missing[0]["finding_codes"])

        duplicate = bundle_semantics_structure.evaluate(
            [
                "structure-site-identity-not-unique",
                "structure-site-identity-not-unique",
            ],
            context,
        )
        self.assertEqual(len(duplicate), 1)
        self.assertEqual(duplicate[0]["status"], "pass")

        inactive = snapshot_semantic_context()
        inactive["current_record"]["lifecycle"] = "planned"
        inactive["current_record"]["integrity_verified_active"] = False
        result = bundle_semantics_structure.evaluate(
            ["structure-site-identity-not-unique"], inactive
        )[0]
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["finding_codes"],
            ["STRUCTURE_CURRENT_RECORD_NOT_INTEGRITY_VERIFIED_ACTIVE"],
        )

        target_inactive = molecular_semantic_context()
        target = target_inactive["records_by_identity"][
            ("structure-snapshot", "1.0", "snapshot-h2-molecule")
        ]
        target["lifecycle"] = "planned"
        target["integrity_verified_active"] = False
        result = bundle_semantics_structure.evaluate(
            ["molecular-snapshot-hash-mismatch"], target_inactive
        )[0]
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["finding_codes"],
            ["RECORD_REF_TARGET_NOT_INTEGRITY_VERIFIED_ACTIVE"],
        )

    def test_artifact_content_obligations_block_without_core_parser_observation(
        self,
    ) -> None:
        cases = {
            "structure-export-target-profile-mismatch": ("export", "POSCAR"),
            "trajectory-frame-index-not-unique": (
                "trajectory",
                "trajectory-index.json",
            ),
        }
        for obligation_id, (schema_name, label) in cases.items():
            with self.subTest(obligation=obligation_id):
                context = SEMANTIC_CONTEXT_BUILDERS[schema_name]()
                context["artifacts_by_label"][label]["parser_observations"] = ()
                context["artifacts_by_label"][label]["metadata"]["observations"] = {
                    "self_declared": True
                }
                result = bundle_semantics.evaluate_advertised_obligations(
                    [obligation_id],
                    context,
                    evaluator=bundle_semantics_structure.evaluate,
                )[0]
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(
                    result["finding_codes"],
                    ["STRUCTURE_PARSED_ARTIFACT_EVIDENCE_MISSING"],
                )

        context = export_semantic_context()
        observation = context["artifacts_by_label"]["POSCAR"]["parser_observations"][0]
        observation["source_raw_sha256"] = HASH_B
        with self.assertRaisesRegex(
            ValueError, "parser observation identity or payload is invalid"
        ):
            bundle_semantics.evaluate_advertised_obligations(
                ["structure-export-target-profile-mismatch"],
                context,
                evaluator=bundle_semantics_structure.evaluate,
            )

    def test_shared_dispatcher_accepts_structure_evaluator_results(self) -> None:
        evaluated_rows = 0
        for schema_name, advertised in REQUIRED_SEMANTIC_OBLIGATIONS.items():
            context = SEMANTIC_CONTEXT_BUILDERS[schema_name]()
            obligation_ids = sorted(advertised)
            results = bundle_semantics.evaluate_advertised_obligations(
                obligation_ids,
                context,
                evaluator=bundle_semantics_structure.evaluate,
            )
            evaluated_rows += len(results)
            self.assertEqual(len(results), len(obligation_ids))
            self.assertEqual(
                [result["obligation_id"] for result in results], obligation_ids
            )
            for result in results:
                with self.subTest(
                    schema=schema_name, obligation=result["obligation_id"]
                ):
                    self.assertEqual(result["status"], "pass", result)
                    self.assertTrue(result["handler_id"])
        self.assertEqual(evaluated_rows, 44)

    def test_operation_and_continuity_handlers_use_observed_deltas(self) -> None:
        transform_context = transformation_semantic_context()
        transform_data = current_semantic_data(transform_context)
        transform_data["operation_class"] = "translate"
        result = bundle_semantics_structure.evaluate(
            ["structure-transform-operation-semantics-mismatch"],
            transform_context,
        )[0]
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["finding_codes"],
            ["STRUCTURE_TRANSFORM_OPERATION_HANDLER_NOT_IMPLEMENTED"],
        )

        transform_context = transformation_semantic_context()
        child = record_data(
            transform_context, "structure-snapshot", "snapshot-after-reorder"
        )
        child["sites"][0]["cartesian_ang"][0] += 0.1
        result = bundle_semantics_structure.evaluate(
            ["structure-transform-operation-semantics-mismatch"],
            transform_context,
        )[0]
        self.assertEqual(result["status"], "fail")
        self.assertEqual(
            result["finding_codes"],
            ["STRUCTURE_TRANSFORM_OPERATION_SEMANTICS_MISMATCH"],
        )

        trajectory_context = trajectory_semantic_context()
        parsed_artifact_data(trajectory_context, "trajectory.xtc")["steps"] = [
            0,
            2,
            3,
        ]
        result = bundle_semantics_structure.evaluate(
            ["trajectory-continuity-mismatch"], trajectory_context
        )[0]
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["finding_codes"], ["TRAJECTORY_CONTINUITY_MISMATCH"])

    def test_zero_image_shift_is_well_defined_for_nonperiodic_reorder(self) -> None:
        context = transformation_semantic_context()
        parent = h2_snapshot()
        parent["snapshot_id"] = "snapshot-before-reorder"
        child = h2_snapshot()
        child["snapshot_id"] = "snapshot-after-reorder"
        context["records_by_identity"][
            ("structure-snapshot", "1.0", "snapshot-before-reorder")
        ]["data"] = parent
        context["records_by_identity"][
            ("structure-snapshot", "1.0", "snapshot-after-reorder")
        ]["data"] = child
        transform = current_semantic_data(context)
        for index, mapping in enumerate(transform["site_mapping"]):
            mapping["parent_site_id"] = f"site-h-00{index}"
            mapping["child_site_id"] = f"site-h-00{index}"
        result = bundle_semantics_structure.evaluate(
            ["structure-transform-image-shift-inconsistent"], context
        )[0]
        self.assertEqual(result["status"], "pass", result)

    def test_structure_evaluator_has_no_path_io_or_raw_reparse_escape_hatch(
        self,
    ) -> None:
        source = inspect.getsource(bundle_semantics_structure)
        for forbidden in (
            "json.loads",
            "Path(",
            "open(",
            "read_bytes",
            "read_text",
            "subprocess",
            "urllib",
            "requests",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_ready_fixtures_bind_obligations_without_post_record_backrefs(self) -> None:
        fixtures = {
            "snapshot": (periodic_snapshot(), "calculation_readiness"),
            "molecular": (molecular_manifest(), "calculation_readiness"),
            "transformation": (ready_exact_transformation(), "calculation_use"),
            "export": (export_manifest(), "calculation_use"),
            "trajectory": (trajectory_manifest(), "analysis_readiness"),
        }
        for schema_name, (fixture, readiness_field) in fixtures.items():
            with self.subTest(schema=schema_name):
                self.assertEqual(fixture[readiness_field]["status"], "ready")
                self.assertEqual(fixture["validation"]["status"], "pass")
                checks = {
                    check["check_id"]: check
                    for check in fixture["validation"]["checks"]
                }
                self.assertTrue(
                    REQUIRED_SEMANTIC_OBLIGATIONS[schema_name].issubset(checks)
                )
                for finding_id in REQUIRED_SEMANTIC_OBLIGATIONS[schema_name]:
                    self.assertEqual(checks[finding_id]["status"], "pass")
                    self.assertTrue(checks[finding_id]["decisive"])
                    self.assertEqual(checks[finding_id]["evidence_refs"], [])
                    self.assertTrue(
                        next(
                            item["evidence_required"]
                            for item in SCHEMAS[schema_name][
                                "x-vibe-semantic-obligations"
                            ]
                            if item["finding_id"] == finding_id
                        )
                    )

    def _assert_all_typed_objects_are_closed(self, node: Any, path: str) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                self.assertIs(
                    node.get("additionalProperties"),
                    False,
                    f"open object definition at {path}",
                )
            for key, value in node.items():
                self._assert_all_typed_objects_are_closed(value, f"{path}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                self._assert_all_typed_objects_are_closed(value, f"{path}/{index}")

    def test_claim_ceiling_enum_is_exact_and_old_spellings_are_rejected(self) -> None:
        expected = [
            "no_positive_claim",
            "documented_behavior_only",
            "input_gates_only",
            "technical_run_gates_only",
            "numerical_candidate_only",
            "eligible_for_expert_review",
        ]
        self.assertEqual(SCHEMAS["common"]["$defs"]["claimCeiling"]["enum"], expected)

        claim_validator = Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": (
                    "urn:vibe-dft-skills:contract:common-definitions:1.0"
                    "#/$defs/claimCeiling"
                ),
            },
            registry=REGISTRY,
        )
        for value in expected:
            with self.subTest(valid=value):
                self.assertFalse(list(claim_validator.iter_errors(value)))

        obsolete = [
            "no-positive-claim",
            "documented-behavior-only",
            "input-gates-only",
            "technical-run-gates-only",
            "convergence_candidate_only",
            "convergence-candidate-only",
            "eligible-for-expert-review",
        ]
        for value in obsolete:
            with self.subTest(obsolete=value):
                self.assertTrue(list(claim_validator.iter_errors(value)))

    def test_side_effect_vocabulary_is_canonical_nonempty_and_unique(self) -> None:
        expected = [
            "read-only",
            "network-read",
            "local-write",
            "local-execution",
            "remote-read",
            "remote-write",
            "scheduler-submit",
            "scheduler-control",
            "external-publish",
            "destructive-delete",
        ]
        common_defs = SCHEMAS["common"]["$defs"]
        self.assertEqual(common_defs["sideEffect"]["enum"], expected)
        self.assertEqual(
            common_defs["sideEffectSet"],
            {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"$ref": "#/$defs/sideEffect"},
            },
        )

        side_effect_validator = Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": (
                    "urn:vibe-dft-skills:contract:common-definitions:1.0"
                    "#/$defs/sideEffect"
                ),
            },
            registry=REGISTRY,
        )
        side_effect_set_validator = Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": (
                    "urn:vibe-dft-skills:contract:common-definitions:1.0"
                    "#/$defs/sideEffectSet"
                ),
            },
            registry=REGISTRY,
        )

        for value in expected:
            with self.subTest(valid=value):
                self.assertFalse(list(side_effect_validator.iter_errors(value)))
        for obsolete in ["external-execution", "remote-execution"]:
            with self.subTest(obsolete=obsolete):
                self.assertTrue(list(side_effect_validator.iter_errors(obsolete)))

        self.assertFalse(
            list(
                side_effect_set_validator.iter_errors(
                    ["read-only", "network-read", "local-write"]
                )
            )
        )
        self.assertTrue(list(side_effect_set_validator.iter_errors([])))
        self.assertTrue(
            list(side_effect_set_validator.iter_errors(["local-write", "local-write"]))
        )
        self.assertTrue(
            list(side_effect_set_validator.iter_errors(["external-execution"]))
        )

    def test_scientific_acceptance_vocabulary_is_exact_snake_case(self) -> None:
        expected = [
            "not_assessed",
            "requires_human_review",
            "accepted",
            "rejected",
        ]
        self.assertEqual(
            SCHEMAS["common"]["$defs"]["scientificAcceptance"]["enum"],
            expected,
        )
        validator = Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": (
                    "urn:vibe-dft-skills:contract:common-definitions:1.0"
                    "#/$defs/scientificAcceptance"
                ),
            },
            registry=REGISTRY,
        )
        for value in expected:
            with self.subTest(valid=value):
                self.assertFalse(list(validator.iter_errors(value)))

        obsolete = [
            "not-assessed",
            "requires-human-review",
            "requires_expert_review",
            "requires-expert-review",
        ]
        for value in obsolete:
            with self.subTest(obsolete=value):
                self.assertTrue(list(validator.iter_errors(value)))

    def test_short_registered_software_ids_do_not_weaken_general_record_ids(
        self,
    ) -> None:
        software_validator = Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": (
                    "urn:vibe-dft-skills:contract:common-definitions:1.0"
                    "#/$defs/softwareIdentity"
                ),
            },
            registry=REGISTRY,
            format_checker=FormatChecker(),
        )
        identity = software_identity()
        identity["software_id"] = "qe"
        self.assertFalse(list(software_validator.iter_errors(identity)))

        identity["software_id"] = "q"
        self.assertTrue(list(software_validator.iter_errors(identity)))

        record_id_validator = Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": (
                    "urn:vibe-dft-skills:contract:common-definitions:1.0"
                    "#/$defs/safeId"
                ),
            },
            registry=REGISTRY,
        )
        self.assertTrue(list(record_id_validator.iter_errors("qe")))

    def test_record_ref_hash_semantics_are_exact_raw_bytes_not_projections(
        self,
    ) -> None:
        common = SCHEMAS["common"]
        semantics = common["x-vibe-record-ref-hash-semantics"]
        self.assertEqual(
            semantics,
            {
                "algorithm": "sha256",
                "target_scope": "resolved-target-json-document-in-same-bundle",
                "media_type": "application/json",
                "text_encoding": "utf-8",
                "byte_basis": "exact-raw-file-bytes",
                "canonicalization": "none",
                "bundle_local_resolution_required": True,
                "projection_hash_allowed": False,
                "placeholder_hash_counts_as_resolved_evidence": False,
            },
        )

        record_ref_schema = common["$defs"]["recordRef"]
        expected_fields = {
            "contract_name",
            "schema_version",
            "record_id",
            "sha256",
            "role",
        }
        self.assertEqual(set(record_ref_schema["required"]), expected_fields)
        self.assertEqual(set(record_ref_schema["properties"]), expected_fields)

        description = record_ref_schema["properties"]["sha256"]["description"]
        required_phrases = [
            "exact raw file bytes",
            "resolved target UTF-8 JSON document",
            "same bundle",
            "No canonicalization",
            "projection",
            "schema-valid placeholder digest is not resolved evidence",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, description)

        self.assertEqual(semantics["canonicalization"], "none")
        self.assertEqual(semantics["byte_basis"], "exact-raw-file-bytes")
        self.assertFalse(semantics["projection_hash_allowed"])
        self.assertFalse(semantics["placeholder_hash_counts_as_resolved_evidence"])
        self.assertEqual(
            common["x-vibe-record-ref-graph-semantics"],
            {
                "topology": "immutable-dag",
                "same_bundle_required": True,
                "target_must_preexist_referrer": True,
                "self_reference_allowed": False,
                "cycles_allowed": False,
                "post_record_back_reference_allowed": False,
            },
        )

    def test_snapshot_removes_the_transformation_back_reference_field(self) -> None:
        snapshot_schema = SCHEMAS["snapshot"]
        self.assertNotIn("parent_transformation_refs", snapshot_schema["required"])
        self.assertNotIn("parent_transformation_refs", snapshot_schema["properties"])

        obsolete_backref = periodic_snapshot()
        obsolete_backref["parent_transformation_refs"] = [
            record_ref(
                "structure-transformation-manifest",
                "transform-impossible-cycle",
                "parent-transformation",
            )
        ]
        self.assert_invalid("snapshot", obsolete_backref)

    def test_real_raw_byte_bundle_forms_an_immutable_record_ref_dag(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            bundle = Path(temporary_directory)
            paths: list[Path] = []

            def persist(
                filename: str,
                document: dict[str, Any],
                role: str,
                *,
                pretty: bool,
            ) -> dict[str, Any]:
                path = bundle / filename
                digest = write_json_document(path, document, pretty=pretty)
                paths.append(path)
                contract_name, schema_version, record_id = document_identity(document)
                self.assertEqual(schema_version, "1.0")
                return record_ref(contract_name, record_id, role, digest)

            evidence_ref = persist(
                "00-evidence.json",
                {
                    "contract_name": "bundle-evidence-record",
                    "schema_version": "1.0",
                    "record_id": "shared-structure-evidence",
                    "evidence_kind": "pre-record-deterministic-checks",
                },
                "evidence",
                pretty=True,
            )
            decision_ref = persist(
                "01-decision.json",
                {
                    "contract_name": "decision-record",
                    "schema_version": "1.0",
                    "record_id": "decision-cluster-boundary",
                    "decision_kind": "pre-record-boundary-choice",
                },
                "boundary-decision",
                pretty=False,
            )
            run_ref = persist(
                "02-source-run.json",
                {
                    "contract_name": "calculation-record-envelope",
                    "schema_version": "1.0",
                    "record_id": "calculation-md-si2",
                    "record_kind": "pre-existing-source-run",
                },
                "source-run",
                pretty=True,
            )

            parent = periodic_snapshot()
            parent["snapshot_id"] = "snapshot-before-reorder"
            self.assert_valid("snapshot", parent)
            parent_ref = persist(
                "03-parent-snapshot.json", parent, "parent", pretty=True
            )

            child = periodic_snapshot()
            child["snapshot_id"] = "snapshot-after-reorder"
            child["identity"]["value"] = HASH_C
            self.assertNotIn("parent_transformation_refs", child)
            self.assert_valid("snapshot", child)
            child_ref = persist("04-child-snapshot.json", child, "child", pretty=False)

            transformation = ready_exact_transformation()
            transformation["parents"] = [copy.deepcopy(parent_ref)]
            transformation["children"] = [copy.deepcopy(child_ref)]
            transformation["site_mapping"][0]["parent_ref"] = copy.deepcopy(parent_ref)
            transformation["site_mapping"][0]["child_ref"] = copy.deepcopy(child_ref)
            transformation["roundtrip"]["comparison_snapshot_ref"] = copy.deepcopy(
                child_ref
            )
            transformation["roundtrip"]["evidence_refs"] = [copy.deepcopy(evidence_ref)]
            self.assert_valid("transformation", transformation)
            transformation_ref = persist(
                "05-transformation.json",
                transformation,
                "extraction-transform",
                pretty=True,
            )

            molecular = molecular_manifest()
            molecular["snapshot_ref"] = copy.deepcopy(child_ref)
            molecular["extraction_boundary"] = {
                "kind": "cluster-from-periodic",
                "parent_periodic_snapshot_ref": copy.deepcopy(parent_ref),
                "transformation_ref": copy.deepcopy(transformation_ref),
                "capping_policy": "none",
                "created_site_ids": [],
                "removed_site_ids": [],
                "capped_site_ids": [],
                "boundary_decision_ref": copy.deepcopy(decision_ref),
            }
            self.assert_valid("molecular", molecular)
            persist(
                "06-molecular.json",
                molecular,
                "molecular-manifest",
                pretty=False,
            )

            export = export_manifest()
            export["snapshot_ref"] = copy.deepcopy(child_ref)
            export["transformation_refs"] = [copy.deepcopy(transformation_ref)]
            export["roundtrip_validation"]["reconstructed_snapshot_ref"] = (
                copy.deepcopy(child_ref)
            )
            export["roundtrip_validation"]["evidence_refs"] = [
                copy.deepcopy(evidence_ref)
            ]
            self.assert_valid("export", export)
            persist("07-export.json", export, "structure-export", pretty=True)

            trajectory = trajectory_manifest()
            trajectory["initial_structure_ref"] = copy.deepcopy(child_ref)
            trajectory["source_run_ref"] = copy.deepcopy(run_ref)
            trajectory["topology"] = {
                "status": "present",
                "ref": copy.deepcopy(child_ref),
            }
            trajectory["segments"][0]["source_run_ref"] = copy.deepcopy(run_ref)
            trajectory["continuity"]["evidence_refs"] = [copy.deepcopy(evidence_ref)]
            self.assert_valid("trajectory", trajectory)
            persist("08-trajectory.json", trajectory, "trajectory", pretty=False)

            self.assertEqual(audit_record_ref_bundle(paths), set())

    def test_self_reference_and_snapshot_transformation_cycle_are_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            bundle = Path(temporary_directory)

            self_referencing = periodic_snapshot()
            self_referencing["snapshot_id"] = "snapshot-self-reference"
            self_referencing["extension_refs"] = [
                record_ref(
                    "structure-snapshot",
                    "snapshot-self-reference",
                    "extension",
                )
            ]
            self.assert_valid("snapshot", self_referencing)
            self_path = bundle / "self.json"
            write_json_document(self_path, self_referencing, pretty=True)
            self_findings = audit_record_ref_bundle([self_path])
            self.assertIn("record-reference-self", self_findings)
            self.assertIn("record-reference-dag-invalid", self_findings)

            evidence_path = bundle / "evidence.json"
            evidence_document = {
                "contract_name": "bundle-evidence-record",
                "schema_version": "1.0",
                "record_id": "cycle-evidence-record",
            }
            evidence_hash = write_json_document(
                evidence_path, evidence_document, pretty=False
            )
            evidence_ref = record_ref(
                "bundle-evidence-record",
                "cycle-evidence-record",
                "roundtrip-evidence",
                evidence_hash,
            )

            parent = periodic_snapshot()
            parent["snapshot_id"] = "snapshot-cycle-parent"
            parent_path = bundle / "parent.json"
            parent_hash = write_json_document(parent_path, parent, pretty=True)
            parent_ref = record_ref(
                "structure-snapshot",
                "snapshot-cycle-parent",
                "parent",
                parent_hash,
            )

            child = periodic_snapshot()
            child["snapshot_id"] = "snapshot-cycle-child"
            child_path = bundle / "child.json"
            child_hash_before_backref = write_json_document(
                child_path, child, pretty=False
            )
            child_ref = record_ref(
                "structure-snapshot",
                "snapshot-cycle-child",
                "child",
                child_hash_before_backref,
            )

            transformation = ready_exact_transformation()
            transformation["parents"] = [copy.deepcopy(parent_ref)]
            transformation["children"] = [copy.deepcopy(child_ref)]
            transformation["site_mapping"][0]["parent_ref"] = copy.deepcopy(parent_ref)
            transformation["site_mapping"][0]["child_ref"] = copy.deepcopy(child_ref)
            transformation["roundtrip"]["comparison_snapshot_ref"] = copy.deepcopy(
                child_ref
            )
            transformation["roundtrip"]["evidence_refs"] = [evidence_ref]
            self.assert_valid("transformation", transformation)
            transformation_path = bundle / "transformation.json"
            transformation_hash = write_json_document(
                transformation_path, transformation, pretty=True
            )

            child["extension_refs"] = [
                record_ref(
                    "structure-transformation-manifest",
                    transformation["transformation_id"],
                    "forbidden-backref",
                    transformation_hash,
                )
            ]
            self.assert_valid("snapshot", child)
            write_json_document(child_path, child, pretty=False)

            cycle_findings = audit_record_ref_bundle(
                [evidence_path, parent_path, transformation_path, child_path]
            )
            self.assertIn("record-reference-cycle", cycle_findings)
            self.assertIn("record-reference-topology-order-invalid", cycle_findings)
            self.assertIn("record-reference-hash-mismatch", cycle_findings)
            self.assertIn("record-reference-dag-invalid", cycle_findings)

    def test_projection_hash_and_whitespace_changed_target_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            bundle = Path(temporary_directory)
            target_document = {
                "contract_name": "bundle-evidence-record",
                "schema_version": "1.0",
                "record_id": "raw-byte-target-record",
                "payload": {"value": 1, "note": "spacing is significant"},
            }
            target_path = bundle / "target.json"
            raw_hash = write_json_document(target_path, target_document, pretty=True)

            source = periodic_snapshot()
            source["snapshot_id"] = "snapshot-raw-byte-source"
            source["extension_refs"] = [
                record_ref(
                    "bundle-evidence-record",
                    "raw-byte-target-record",
                    "extension",
                    raw_hash,
                )
            ]
            source_path = bundle / "source.json"
            write_json_document(source_path, source, pretty=False)
            self.assertEqual(audit_record_ref_bundle([target_path, source_path]), set())

            raw_before_whitespace_change = target_path.read_bytes()
            target_path.write_bytes(raw_before_whitespace_change + b"  \n")
            self.assertEqual(
                json.loads(raw_before_whitespace_change.decode("utf-8")),
                json.loads(target_path.read_bytes().decode("utf-8")),
            )
            self.assertNotEqual(
                hashlib.sha256(raw_before_whitespace_change).hexdigest(),
                hashlib.sha256(target_path.read_bytes()).hexdigest(),
            )
            whitespace_findings = audit_record_ref_bundle([target_path, source_path])
            self.assertIn("record-reference-hash-mismatch", whitespace_findings)

            write_json_document(target_path, target_document, pretty=True)
            projection_bytes = json.dumps(
                {"record_id": target_document["record_id"]},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            projection_hash = hashlib.sha256(projection_bytes).hexdigest()
            self.assertNotEqual(projection_hash, raw_hash)
            source["extension_refs"][0]["sha256"] = projection_hash
            write_json_document(source_path, source, pretty=False)
            projection_findings = audit_record_ref_bundle([target_path, source_path])
            self.assertIn("record-reference-hash-mismatch", projection_findings)
            self.assertIn("record-reference-dag-invalid", projection_findings)

    def test_positive_records_cover_all_structure_contracts(self) -> None:
        fixtures = {
            "snapshot": periodic_snapshot(),
            "molecular": molecular_manifest(),
            "transformation": ready_exact_transformation(),
            "export": export_manifest(),
            "trajectory": trajectory_manifest(),
        }
        for schema_name, fixture in fixtures.items():
            with self.subTest(schema=schema_name):
                self.assert_valid(schema_name, fixture)

    def test_partial_occupancy_and_disorder_are_valid_only_when_blocked(self) -> None:
        for ordering_state, occupancy, blocker in [
            ("partial-occupancy", 0.5, "partial-occupancy"),
            ("disordered", 1.0, "site-disorder"),
        ]:
            blocked = periodic_snapshot()
            blocked["sites"][0]["ordering_state"] = ordering_state
            blocked["sites"][0]["occupancy"] = occupancy
            blocked["calculation_readiness"] = readiness("blocked", blocker)
            blocked["validation"] = gate_summary("blocked")
            with self.subTest(state=ordering_state, mode="blocked"):
                self.assert_valid("snapshot", blocked)

            guessed_ready = copy.deepcopy(blocked)
            guessed_ready["calculation_readiness"] = readiness()
            guessed_ready["validation"] = gate_summary()
            with self.subTest(state=ordering_state, mode="guessed-ready"):
                self.assert_invalid("snapshot", guessed_ready)

    def test_periodicity_cell_and_coordinate_modes_are_consistent(self) -> None:
        periodic = periodic_snapshot()
        self.assert_valid("snapshot", periodic)

        wrong_pbc = copy.deepcopy(periodic)
        wrong_pbc["periodicity"]["pbc"] = [True, True, False]
        self.assert_invalid("snapshot", wrong_pbc)

        missing_cell = copy.deepcopy(periodic)
        missing_cell["cell"] = {
            "status": "not-applicable",
            "vectors_ang": None,
            "rank": 0,
        }
        self.assert_invalid("snapshot", missing_cell)

        missing_fractional = copy.deepcopy(periodic)
        missing_fractional["sites"][0]["fractional"] = None
        self.assert_invalid("snapshot", missing_fractional)

        isolated = periodic_snapshot()
        isolated["snapshot_id"] = "snapshot-isolated-si2"
        isolated["structure_kind"] = "isolated-cluster"
        isolated["periodicity"] = {
            "dimensions": 0,
            "pbc": [False, False, False],
            "boundary_condition": "isolated",
        }
        isolated["cell"] = {
            "status": "not-applicable",
            "vectors_ang": None,
            "rank": 0,
        }
        for site in isolated["sites"]:
            site["fractional"] = None
        self.assert_valid("snapshot", isolated)

        isolated_with_fractional = copy.deepcopy(isolated)
        isolated_with_fractional["sites"][0]["fractional"] = [0.0, 0.0, 0.0]
        self.assert_invalid("snapshot", isolated_with_fractional)

    def test_unknown_charge_or_spin_cannot_be_guessed_ready(self) -> None:
        for state_name, value_fields, blocker in [
            (
                "charge_state",
                {"net_charge_e": None},
                "charge-unknown",
            ),
            (
                "spin_state",
                {"multiplicity": None, "total_magnetization_mu_b": None},
                "spin-unknown",
            ),
        ]:
            blocked = periodic_snapshot()
            blocked[state_name]["status"] = "unknown"
            blocked[state_name]["source"] = "not-available"
            blocked[state_name].update(value_fields)
            blocked["calculation_readiness"] = readiness("blocked", blocker)
            blocked["validation"] = gate_summary("blocked")
            with self.subTest(state=state_name, mode="blocked"):
                self.assert_valid("snapshot", blocked)

            guessed_ready = copy.deepcopy(blocked)
            guessed_ready["calculation_readiness"] = readiness()
            guessed_ready["validation"] = gate_summary()
            with self.subTest(state=state_name, mode="guessed-ready"):
                self.assert_invalid("snapshot", guessed_ready)

    def test_molecular_unknown_quantum_state_is_fail_closed(self) -> None:
        blocked = molecular_manifest()
        blocked["net_charge"] = {
            "status": "unknown",
            "value": None,
            "source": "not-available",
            "evidence_refs": [],
        }
        blocked["multiplicity"] = copy.deepcopy(blocked["net_charge"])
        blocked["electron_count"] = {
            "status": "unknown",
            "value": None,
            "derivation": "not-available",
            "evidence_refs": [],
        }
        blocked["calculation_readiness"] = readiness(
            "blocked",
            "charge-unknown",
            "multiplicity-unknown",
            "electron-count-unknown",
        )
        blocked["validation"] = gate_summary("blocked")
        self.assert_valid("molecular", blocked)

        guessed_ready = copy.deepcopy(blocked)
        guessed_ready["calculation_readiness"] = readiness()
        guessed_ready["validation"] = gate_summary()
        self.assert_invalid("molecular", guessed_ready)

    def test_cluster_extraction_requires_parent_transform_and_decision(self) -> None:
        record = molecular_manifest()
        record["extraction_boundary"] = {
            "kind": "cluster-from-periodic",
            "parent_periodic_snapshot_ref": record_ref(
                "structure-snapshot", "snapshot-periodic-parent", "parent"
            ),
            "transformation_ref": record_ref(
                "structure-transformation-manifest",
                "transform-extract-cluster",
                "extraction-transform",
            ),
            "capping_policy": "hydrogen",
            "created_site_ids": ["site-cap-h-000"],
            "removed_site_ids": ["site-periodic-outside"],
            "capped_site_ids": ["site-boundary-capped"],
            "boundary_decision_ref": record_ref(
                "decision-record", "decision-cluster-boundary", "boundary-decision"
            ),
        }
        self.assert_valid("molecular", record)

        for missing_field in [
            "parent_periodic_snapshot_ref",
            "transformation_ref",
            "boundary_decision_ref",
        ]:
            mutated = copy.deepcopy(record)
            mutated["extraction_boundary"][missing_field] = None
            with self.subTest(missing=missing_field):
                self.assert_invalid("molecular", mutated)

    def test_rich_transformation_carries_multi_parent_and_one_to_many_lineage(
        self,
    ) -> None:
        record = rich_blocked_transformation()
        self.assert_valid("transformation", record)
        self.assertEqual(len(record["parents"]), 2)
        repeated = [
            item
            for item in record["site_mapping"]
            if item["parent_site_id"] == "site-source-one"
        ]
        self.assertEqual(len(repeated), 2)
        self.assertEqual(
            {item["relation"] for item in record["site_mapping"]},
            {"replicated", "merged", "split", "created", "removed", "capped"},
        )
        merged = [
            item
            for item in record["site_mapping"]
            if item["child_site_id"] == "site-merged-child"
        ]
        split = [
            item
            for item in record["site_mapping"]
            if item["parent_site_id"] == "site-split-source"
        ]
        self.assertEqual(len(merged), 2)
        self.assertEqual(len(split), 2)

        one_parent = copy.deepcopy(record)
        one_parent["parents"] = one_parent["parents"][:1]
        self.assert_invalid("transformation", one_parent)

    def test_transformation_mapping_relations_reject_invented_lineage(self) -> None:
        cases: list[tuple[str, int, str, Any]] = [
            ("created-parent", 2, "parent_site_id", "invented-parent-site"),
            ("created-child", 2, "child_site_id", None),
            ("removed-parent", 3, "parent_site_id", None),
            ("removed-child", 3, "child_site_id", "invented-child-site"),
            ("replicated-image", 0, "image_shift", None),
            ("capped-parent", 4, "parent_site_id", None),
            ("capped-child", 4, "child_site_id", None),
            ("merged-child", 5, "child_site_id", None),
            ("split-parent", 7, "parent_site_id", None),
        ]
        for name, mapping_index, field, value in cases:
            mutated = rich_blocked_transformation()
            mutated["site_mapping"][mapping_index][field] = value
            with self.subTest(case=name):
                self.assert_invalid("transformation", mutated)

        ambiguous_as_exact = rich_blocked_transformation()
        ambiguous_as_exact["mapping_status"] = "exact"
        self.assert_invalid("transformation", ambiguous_as_exact)

    def test_transformation_parameters_are_typed_not_free_form(self) -> None:
        wrong_slot = ready_exact_transformation()
        wrong_slot["parameters"][0]["integer_value"] = 2
        self.assert_invalid("transformation", wrong_slot)

        invented_key = ready_exact_transformation()
        invented_key["parameters"][0]["opaque_options"] = {"guess": True}
        self.assert_invalid("transformation", invented_key)

    def test_transformation_roundtrip_requires_comparison_evidence_and_tolerance(
        self,
    ) -> None:
        exact = ready_exact_transformation()
        self.assert_valid("transformation", exact)

        mutations = []
        nonzero_exact_tolerance = copy.deepcopy(exact)
        nonzero_exact_tolerance["roundtrip"]["tolerance_ang"] = 1.0e-6
        mutations.append(("nonzero-exact-tolerance", nonzero_exact_tolerance))

        missing_comparison = copy.deepcopy(exact)
        missing_comparison["roundtrip"]["comparison_snapshot_ref"] = None
        mutations.append(("missing-comparison", missing_comparison))

        missing_evidence = copy.deepcopy(exact)
        missing_evidence["roundtrip"]["evidence_refs"] = []
        mutations.append(("missing-evidence", missing_evidence))

        zero_equivalence_tolerance = copy.deepcopy(exact)
        zero_equivalence_tolerance["roundtrip"][
            "classification"
        ] = "equivalent-with-tolerance"
        mutations.append(("zero-equivalence-tolerance", zero_equivalence_tolerance))

        for name, mutated in mutations:
            with self.subTest(case=name):
                self.assert_invalid("transformation", mutated)

    def test_export_requires_content_hash_and_safe_local_label(self) -> None:
        missing_hash = export_manifest()
        del missing_hash["export_files"][0]["sha256"]
        self.assert_invalid("export", missing_hash)

        absolute_label = export_manifest()
        absolute_label["export_files"][0]["label"] = "/tmp/POSCAR"
        self.assert_invalid("export", absolute_label)

        wrong_target = export_manifest()
        wrong_target["target"]["target_code"] = "qe"
        self.assert_invalid("export", wrong_target)

    def test_lossy_export_is_valid_as_evidence_but_never_ready(self) -> None:
        lossy = export_manifest()
        lossy["roundtrip_validation"] = {
            "classification": "lossy",
            "reconstructed_snapshot_ref": None,
            "tolerance_ang": None,
            "evidence_refs": [],
            "loss_codes": ["site-labels-not-roundtrippable"],
        }
        lossy["calculation_use"] = readiness("blocked", "lossy-format-roundtrip")
        lossy["validation"] = gate_summary("blocked")
        self.assert_valid("export", lossy)

        guessed_ready = copy.deepcopy(lossy)
        guessed_ready["calculation_use"] = readiness()
        guessed_ready["validation"] = gate_summary()
        self.assert_invalid("export", guessed_ready)

        unexplained_loss = copy.deepcopy(lossy)
        unexplained_loss["roundtrip_validation"]["loss_codes"] = []
        self.assert_invalid("export", unexplained_loss)

    def test_trajectory_continuity_and_time_axis_are_not_guessable(self) -> None:
        wrong_count = trajectory_manifest()
        wrong_count["continuity"]["gap_count"] = 1
        self.assert_invalid("trajectory", wrong_count)

        no_time = trajectory_manifest()
        no_time["time_axis"] = {
            "status": "not-applicable",
            "start": None,
            "step": None,
            "unit": None,
            "values_file": None,
        }
        self.assert_invalid("trajectory", no_time)

        gapped = trajectory_manifest()
        gapped["segments"][0]["last_frame"] = 49
        gapped["segments"][0]["end_step"] = 49
        gapped["segments"].append(
            {
                "segment_id": "segment-md-restart",
                "parent_segment_id": "segment-md-main",
                "source_run_ref": record_ref(
                    "calculation-record-envelope",
                    "calculation-md-si2-restart",
                    "source-run",
                ),
                "first_frame": 50,
                "last_frame": 99,
                "start_step": 51,
                "end_step": 100,
                "checkpoint_ref": None,
                "continuity_from_parent": "gapped",
            }
        )
        gapped["continuity"]["status"] = "gapped"
        gapped["continuity"]["gap_count"] = 1
        gapped["analysis_readiness"] = readiness("blocked", "trajectory-gap")
        gapped["validation"] = gate_summary("blocked")
        self.assert_valid("trajectory", gapped)

        guessed_continuous = copy.deepcopy(gapped)
        guessed_continuous["analysis_readiness"] = readiness()
        guessed_continuous["validation"] = gate_summary()
        self.assert_invalid("trajectory", guessed_continuous)

    def test_trajectory_unresolved_or_unavailable_inputs_are_blocked(self) -> None:
        unresolved = trajectory_manifest()
        unresolved["topology"] = {"status": "unresolved", "ref": None}
        unresolved["analysis_readiness"] = readiness("blocked", "topology-unresolved")
        unresolved["validation"] = gate_summary("blocked")
        self.assert_valid("trajectory", unresolved)

        unresolved["analysis_readiness"] = readiness()
        unresolved["validation"] = gate_summary()
        self.assert_invalid("trajectory", unresolved)

        external = trajectory_manifest()
        external["files"][0]["availability"] = "external"
        external["analysis_readiness"] = readiness(
            "blocked", "trajectory-file-external"
        )
        external["validation"] = gate_summary("blocked")
        self.assert_valid("trajectory", external)

        external["analysis_readiness"] = readiness()
        external["validation"] = gate_summary()
        self.assert_invalid("trajectory", external)

        missing_index = trajectory_manifest()
        missing_index["frame_index"]["availability"] = "missing"
        missing_index["frame_index"]["sha256"] = None
        missing_index["frame_index"]["bytes"] = None
        missing_index["analysis_readiness"] = readiness(
            "blocked", "frame-index-missing"
        )
        missing_index["validation"] = gate_summary("blocked")
        self.assert_valid("trajectory", missing_index)

        missing_index["analysis_readiness"] = readiness()
        missing_index["validation"] = gate_summary()
        self.assert_invalid("trajectory", missing_index)

    def test_irregular_time_axis_requires_a_present_values_file(self) -> None:
        irregular = trajectory_manifest()
        irregular["time_axis"] = {
            "status": "present-irregular",
            "start": 0.0,
            "step": None,
            "unit": "ps",
            "values_file": file_ref(
                "trajectory-times.json",
                "time-index",
                "json",
                "application/json",
            ),
        }
        self.assert_valid("trajectory", irregular)

        external_values = copy.deepcopy(irregular)
        external_values["time_axis"]["values_file"]["availability"] = "external"
        self.assert_invalid("trajectory", external_values)

    def test_root_and_nested_unexpected_properties_are_rejected(self) -> None:
        fixtures_and_nested_paths = [
            ("snapshot", periodic_snapshot(), ["sites", 0]),
            ("molecular", molecular_manifest(), ["connectivity"]),
            (
                "transformation",
                ready_exact_transformation(),
                ["site_mapping", 0],
            ),
            ("export", export_manifest(), ["target"]),
            ("trajectory", trajectory_manifest(), ["continuity"]),
        ]
        for schema_name, fixture, path in fixtures_and_nested_paths:
            at_root = copy.deepcopy(fixture)
            at_root["agent_guess"] = "not-registered"
            with self.subTest(schema=schema_name, location="root"):
                self.assert_invalid(schema_name, at_root)

            nested = copy.deepcopy(fixture)
            target: Any = nested
            for component in path:
                target = target[component]
            target["agent_guess"] = "not-registered"
            with self.subTest(schema=schema_name, location="nested"):
                self.assert_invalid(schema_name, nested)


if __name__ == "__main__":
    unittest.main()
