#!/usr/bin/env python3
"""Production semantics for five published postprocess/structure legacy records.

The JSON schemas in this module's scope predate canonical ``recordRef`` and
``fileRef`` objects.  This evaluator therefore closes their legacy string-ID
and path fields only inside one already validated immutable bundle: parent
records must be unique, active, integrity-verified, and topologically earlier;
file claims must resolve to exact raw-byte SHA-256 and byte-count observations.

No handler performs I/O, executes software, reparses artifacts, accepts a
scientific conclusion, or authorizes an action.  ``pass`` means only that the
advertised bounded technical/numerical assertion was established from the
frozen context supplied by :mod:`validate_bundle`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
from pathlib import PurePosixPath
import re
from typing import Any


OBLIGATIONS_BY_CONTRACT: dict[str, tuple[str, ...]] = {
    "artifact-manifest": (
        "LEGACY_ARTIFACT_STATUS_CHECK_CONSISTENT",
        "LEGACY_ARTIFACT_OUTPUT_ARTIFACT_HASH_RESOLVES",
        "LEGACY_ARTIFACT_SOURCE_LINEAGE_PREEXISTS",
        "LEGACY_ARTIFACT_TECHNICAL_CLAIM_CEILING",
    ),
    "normalized-dataset": (
        "LEGACY_DATASET_VALIDATION_CHECK_CONSISTENT",
        "LEGACY_DATASET_SOURCE_ARTIFACT_HASH_RESOLVES",
        "LEGACY_DATASET_OUTPUT_ARTIFACT_HASH_RESOLVES",
        "LEGACY_DATASET_TOOL_LINEAGE_PREEXISTS",
        "LEGACY_DATASET_MATURITY_EVIDENCE_CONSISTENT",
        "LEGACY_DATASET_NUMERICAL_CANDIDATE_CEILING",
    ),
    "postprocess-plan": (
        "LEGACY_PLAN_STATUS_READINESS_CONSISTENT",
        "LEGACY_PLAN_SOURCE_ARTIFACT_RESOLVES",
        "LEGACY_PLAN_STEP_GRAPH_CONSISTENT",
        "LEGACY_PLAN_NO_POSITIVE_CLAIM_CEILING",
    ),
    "tool-execution": (
        "LEGACY_TOOL_EXECUTION_PLAN_LINEAGE_PREEXISTS",
        "LEGACY_TOOL_EXECUTION_STATUS_RUNTIME_CONSISTENT",
        "LEGACY_TOOL_EXECUTION_FILE_ARTIFACT_HASH_RESOLVES",
        "LEGACY_TOOL_EXECUTION_PLAN_STEP_CONSISTENT",
        "LEGACY_TOOL_EXECUTION_TECHNICAL_CLAIM_CEILING",
    ),
    "structure-manifest": (
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
    ),
}

CONTRACT_NAMES = frozenset(OBLIGATIONS_BY_CONTRACT)
OBLIGATION_IDS = frozenset(
    obligation
    for obligations in OBLIGATIONS_BY_CONTRACT.values()
    for obligation in obligations
)
_EXPECTED_CONTRACT = {
    obligation: contract
    for contract, obligations in OBLIGATIONS_BY_CONTRACT.items()
    for obligation in obligations
}
_PLACEHOLDER_SHA256 = "0" * 64
_STRUCTURE_FINGERPRINT_ALGORITHM = "sha256-ordered-cell-sites-v1"
_STRUCTURE_FINGERPRINT_CANONICALIZATION = "json-sort-keys-compact-utf8-v1"
_STRUCTURE_FINGERPRINT_DECIMALS = 10
_STRUCTURE_PUBLISHED_DECIMALS = 6
_POSITIVE_SCIENCE = re.compile(
    r"\b(?:scientifically accepted|thermodynamically stable|dynamically stable|"
    r"physically (?:valid|credible)|synthesis feasible|experimentally validated|"
    r"scientific acceptance (?:is )?(?:accepted|established|confirmed|validated))\b",
    re.IGNORECASE,
)
_NEGATION_BEFORE = re.compile(
    r"(?:\bnot\b|\bnever\b|\bno\b|\bdoes not\b|\bcannot\b)\W{0,24}$",
    re.IGNORECASE,
)

# Fixed IUPAC symbols provide an independent check of the redundant atomic
# number fields without importing ASE or trusting bundle-selected code.
_ELEMENTS = (
    "X H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe "
    "Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn "
    "Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re "
    "Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm "
    "Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og"
).split()
_ATOMIC_NUMBER = {symbol: index for index, symbol in enumerate(_ELEMENTS)}


@dataclass(frozen=True)
class _Problem(Exception):
    status: str
    code: str
    location: str
    message: str


def _fail(code: str, location: str, message: str) -> None:
    raise _Problem("fail", code, location, message)


def _block(code: str, location: str, message: str) -> None:
    raise _Problem("blocked", code, location, message)


def _result(
    obligation_id: str,
    status: str,
    *,
    code: str | None = None,
    location: str = "$",
    message: str,
) -> dict[str, Any]:
    return {
        "obligation_id": obligation_id,
        "status": status,
        "finding_codes": [] if code is None else [code],
        "location": location,
        "message": message,
        "handler_id": f"bundle-semantics-legacy-v1.{obligation_id}",
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[Any]:
    return value if isinstance(value, (list, tuple)) else ()


def _current(context: Mapping[str, Any], expected_contract: str) -> Mapping[str, Any]:
    current = _mapping(context.get("current_record"))
    if current.get("contract_name") != expected_contract:
        _block(
            "LEGACY_OBLIGATION_CONTRACT_MISMATCH",
            "$.contract_name",
            "The obligation is not owned by the current legacy contract.",
        )
    if current.get("lifecycle") != "active" or current.get(
        "integrity_verified_active"
    ) is not True:
        _block(
            "LEGACY_RECORD_INTEGRITY_UNVERIFIED",
            "$",
            "The current record is not an active integrity-verified interface instance.",
        )
    data = current.get("data")
    if not isinstance(data, Mapping):
        _block(
            "LEGACY_RECORD_DATA_UNAVAILABLE",
            "$",
            "The current parsed record is unavailable.",
        )
    return data


def _current_index(context: Mapping[str, Any]) -> int:
    value = context.get("current_record_index")
    if not isinstance(value, int) or isinstance(value, bool):
        _block(
            "LEGACY_RECORD_INDEX_UNAVAILABLE",
            "$",
            "The current topological index is unavailable.",
        )
    return value


def _parent_record(
    context: Mapping[str, Any],
    contract_name: str,
    record_id: object,
    location: str,
) -> Mapping[str, Any]:
    if not isinstance(record_id, str) or not record_id:
        _fail(
            "LEGACY_PARENT_ID_INVALID",
            location,
            "A nonempty parent record ID is required.",
        )
    records = context.get("records_by_identity")
    if not isinstance(records, Mapping):
        _block(
            "LEGACY_PARENT_INDEX_UNAVAILABLE",
            location,
            "The bundle record index is unavailable.",
        )
    matches = [
        value
        for key, value in records.items()
        if isinstance(key, tuple)
        and len(key) == 3
        and key[0] == contract_name
        and key[2] == record_id
        and isinstance(value, Mapping)
    ]
    if not matches:
        _block(
            "LEGACY_PARENT_RECORD_UNRESOLVED",
            location,
            f"No {contract_name}@1.0 parent with this ID exists in the bundle.",
        )
    if len(matches) != 1 or matches[0].get("schema_version") != "1.0":
        _fail(
            "LEGACY_PARENT_RECORD_AMBIGUOUS",
            location,
            "The legacy string ID does not resolve uniquely to the required version.",
        )
    parent = matches[0]
    if parent.get("lifecycle") != "active" or parent.get(
        "integrity_verified_active"
    ) is not True:
        _block(
            "LEGACY_PARENT_RECORD_UNVERIFIED",
            location,
            "The parent record is not active and integrity verified.",
        )
    parent_index = parent.get("index")
    if not isinstance(parent_index, int):
        _block(
            "LEGACY_PARENT_INDEX_UNAVAILABLE",
            location,
            "The parent topological index is unavailable.",
        )
    if parent_index >= _current_index(context):
        _fail(
            "LEGACY_PARENT_RECORD_NOT_PREEXISTING",
            location,
            "Legacy lineage must point strictly backward in the immutable bundle DAG.",
        )
    if not isinstance(parent.get("data"), Mapping):
        _block(
            "LEGACY_PARENT_RECORD_DATA_UNAVAILABLE",
            location,
            "The resolved parent payload is unavailable.",
        )
    return parent


def _artifact_candidate(
    context: Mapping[str, Any], path_or_label: object, location: str
) -> Mapping[str, Any]:
    if not isinstance(path_or_label, str) or not path_or_label:
        _fail(
            "LEGACY_ARTIFACT_LABEL_INVALID",
            location,
            "A nonempty safe artifact label is required.",
        )
    artifacts = context.get("artifacts_by_label")
    if not isinstance(artifacts, Mapping):
        _block(
            "LEGACY_ARTIFACT_INDEX_UNAVAILABLE",
            location,
            "The bundle artifact index is unavailable.",
        )
    candidate = artifacts.get(path_or_label)
    if not isinstance(candidate, Mapping):
        basename = PurePosixPath(path_or_label).name
        candidate = artifacts.get(basename)
    if not isinstance(candidate, Mapping):
        _block(
            "LEGACY_ARTIFACT_UNRESOLVED",
            location,
            "The claimed file is not present in the immutable bundle inventory.",
        )
    metadata = _mapping(candidate.get("metadata"))
    if metadata.get("availability") != "present":
        _block(
            "LEGACY_ARTIFACT_NOT_PRESENT",
            location,
            "The claimed artifact is not locally present.",
        )
    return candidate


def _require_artifact_bytes(
    context: Mapping[str, Any],
    file_record: Mapping[str, Any],
    location: str,
    *,
    label_field: str = "path",
) -> None:
    label = file_record.get(label_field)
    digest = file_record.get("sha256")
    size = file_record.get("bytes")
    if digest == _PLACEHOLDER_SHA256:
        _fail(
            "LEGACY_PLACEHOLDER_HASH_FORBIDDEN",
            f"{location}/sha256",
            "An all-zero placeholder digest cannot count as evidence.",
        )
    candidate = _artifact_candidate(context, label, f"{location}/{label_field}")
    metadata = _mapping(candidate.get("metadata"))
    actual_digest = candidate.get("raw_sha256")
    actual_size = candidate.get("bytes")
    declared_digest = metadata.get("sha256")
    declared_size = metadata.get("bytes")
    if (
        not isinstance(digest, str)
        or digest != actual_digest
        or digest != declared_digest
        or not isinstance(size, int)
        or size != actual_size
        or size != declared_size
    ):
        _fail(
            "LEGACY_ARTIFACT_OUTPUT_HASH_MISMATCH",
            location,
            "Record hash/size does not equal the bundle's exact raw artifact observation.",
        )
    if candidate.get("integrity_verified") is not True:
        _block(
            "LEGACY_ARTIFACT_INTEGRITY_UNVERIFIED",
            location,
            "The exact artifact bytes have not passed bundle-core integrity verification.",
        )


def _require_artifact_presence(
    context: Mapping[str, Any], path_or_label: object, location: str
) -> None:
    candidate = _artifact_candidate(context, path_or_label, location)
    if candidate.get("integrity_verified") is not True:
        _block(
            "LEGACY_ARTIFACT_INTEGRITY_UNVERIFIED",
            location,
            "The source artifact has not passed exact bundle-core integrity verification.",
        )


def _positive_science_text(value: object) -> bool:
    strings: list[str] = []

    def walk(item: object) -> None:
        if isinstance(item, str):
            strings.append(item)
        elif isinstance(item, Mapping):
            for nested in item.values():
                walk(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                walk(nested)

    walk(value)
    for text in strings:
        for match in _POSITIVE_SCIENCE.finditer(text):
            prefix = text[max(0, match.start() - 40) : match.start()]
            if not _NEGATION_BEFORE.search(prefix):
                return True
    return False


def _finite(value: object, location: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        _fail(
            "LEGACY_NUMERIC_VALUE_INVALID",
            location,
            "A finite numeric value is required.",
        )
    return float(value)


def _vector(value: object, length: int, location: str) -> tuple[float, ...]:
    values = _sequence(value)
    if len(values) != length:
        _fail(
            "LEGACY_VECTOR_SHAPE_INVALID",
            location,
            f"A vector of length {length} is required.",
        )
    return tuple(_finite(item, f"{location}/{index}") for index, item in enumerate(values))


def _matrix3(value: object, location: str) -> tuple[tuple[float, ...], ...]:
    rows = _sequence(value)
    if len(rows) != 3:
        _fail(
            "LEGACY_CELL_SHAPE_INVALID", location, "A 3x3 cell matrix is required."
        )
    return tuple(_vector(row, 3, f"{location}/{index}") for index, row in enumerate(rows))


def _close(left: float, right: float, *, tolerance: float = 2e-5) -> bool:
    return math.isclose(left, right, rel_tol=2e-6, abs_tol=tolerance)


def _vector_close(left: Sequence[float], right: Sequence[float]) -> bool:
    return len(left) == len(right) and all(_close(a, b) for a, b in zip(left, right))


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


_HANDLERS: dict[str, Callable[[Mapping[str, Any]], None]] = {}


def _handler(obligation_id: str) -> Callable[[Callable[[Mapping[str, Any]], None]], Callable[[Mapping[str, Any]], None]]:
    def register(function: Callable[[Mapping[str, Any]], None]) -> Callable[[Mapping[str, Any]], None]:
        if obligation_id in _HANDLERS:
            raise RuntimeError(f"duplicate legacy obligation handler: {obligation_id}")
        _HANDLERS[obligation_id] = function
        return function

    return register


# ---------------------------------------------------------------------------
# Artifact manifest


@_handler("LEGACY_ARTIFACT_STATUS_CHECK_CONSISTENT")
def _artifact_status(context: Mapping[str, Any]) -> None:
    data = _current(context, "artifact-manifest")
    status = data.get("status")
    validation = _mapping(data.get("validation"))
    validation_status = validation.get("status")
    checks = list(_sequence(validation.get("checks")))
    files = list(_sequence(data.get("data_files"))) + list(
        _sequence(data.get("figure_files"))
    )
    if len(checks) != len(set(checks)) or any(
        not isinstance(item, str) or not item.strip() for item in checks
    ):
        _fail(
            "LEGACY_ARTIFACT_CHECKS_INVALID",
            "$.validation.checks",
            "Validation checks must be unique nonempty descriptions.",
        )
    if status == "complete":
        if validation_status not in {"pass", "warn"} or not checks or not files:
            _fail(
                "LEGACY_ARTIFACT_COMPLETE_STATUS_MISMATCH",
                "$",
                "Complete requires output files and nonempty pass/warn technical checks.",
            )
    elif status == "partial":
        if validation_status not in {"warn", "block"} or not checks or not files:
            _fail(
                "LEGACY_ARTIFACT_PARTIAL_STATUS_MISMATCH",
                "$",
                "Partial requires retained files and explicit warn/block checks.",
            )
    elif status in {"failed", "blocked"}:
        if validation_status != "block":
            _fail(
                "LEGACY_ARTIFACT_TERMINAL_STATUS_MISMATCH",
                "$.validation.status",
                "Failed or blocked artifacts require blocked validation.",
            )
    if status in {"complete", "partial"} and not _sequence(data.get("claim_boundary")):
        _fail(
            "LEGACY_ARTIFACT_CLAIM_BOUNDARY_MISSING",
            "$.claim_boundary",
            "A technically usable artifact requires an explicit claim boundary.",
        )


@_handler("LEGACY_ARTIFACT_OUTPUT_ARTIFACT_HASH_RESOLVES")
def _artifact_outputs(context: Mapping[str, Any]) -> None:
    data = _current(context, "artifact-manifest")
    for group in ("data_files", "figure_files"):
        for index, item in enumerate(_sequence(data.get(group))):
            _require_artifact_bytes(
                context, _mapping(item), f"$.{group}/{index}"
            )


@_handler("LEGACY_ARTIFACT_SOURCE_LINEAGE_PREEXISTS")
def _artifact_lineage(context: Mapping[str, Any]) -> None:
    data = _current(context, "artifact-manifest")
    source_ids = list(_sequence(data.get("source_run_ids")))
    if not source_ids or len(source_ids) != len(set(source_ids)):
        _fail(
            "LEGACY_ARTIFACT_SOURCE_IDS_INVALID",
            "$.source_run_ids",
            "Source run IDs must be nonempty and unique.",
        )
    for index, source_id in enumerate(source_ids):
        parent = _parent_record(
            context,
            "run-manifest",
            source_id,
            f"$.source_run_ids/{index}",
        )
        parent_data = _mapping(parent.get("data"))
        if data.get("code") != "mixed" and parent_data.get("code") != data.get("code"):
            _fail(
                "LEGACY_ARTIFACT_SOURCE_CODE_MISMATCH",
                f"$.source_run_ids/{index}",
                "Artifact and source run code identities differ.",
            )


@_handler("LEGACY_ARTIFACT_TECHNICAL_CLAIM_CEILING")
def _artifact_ceiling(context: Mapping[str, Any]) -> None:
    data = _current(context, "artifact-manifest")
    if _positive_science_text(data.get("claim_boundary")):
        _fail(
            "LEGACY_ARTIFACT_SCIENTIFIC_CLAIM_FORBIDDEN",
            "$.claim_boundary",
            "An artifact manifest cannot assert scientific acceptance or physical validity.",
        )


# ---------------------------------------------------------------------------
# Normalized dataset


@_handler("LEGACY_DATASET_VALIDATION_CHECK_CONSISTENT")
def _dataset_validation(context: Mapping[str, Any]) -> None:
    data = _current(context, "normalized-dataset")
    validation = _mapping(data.get("validation"))
    overall = validation.get("status")
    checks = list(_sequence(validation.get("checks")))
    ids = [item.get("id") for item in checks if isinstance(item, Mapping)]
    statuses = [item.get("status") for item in checks if isinstance(item, Mapping)]
    if not checks or len(ids) != len(checks) or len(ids) != len(set(ids)):
        _fail(
            "LEGACY_DATASET_CHECK_SET_INVALID",
            "$.validation.checks",
            "Dataset checks must be nonempty objects with unique IDs.",
        )
    expected = (
        "block"
        if any(status in {"fail", "not-run"} for status in statuses)
        else "warn"
        if any(status == "warn" for status in statuses)
        else "pass"
    )
    if overall != expected:
        _fail(
            "LEGACY_DATASET_VALIDATION_AGGREGATE_MISMATCH",
            "$.validation.status",
            "Dataset validation status is not the exact aggregate of its checks.",
        )


@_handler("LEGACY_DATASET_SOURCE_ARTIFACT_HASH_RESOLVES")
def _dataset_sources(context: Mapping[str, Any]) -> None:
    data = _current(context, "normalized-dataset")
    positive = _mapping(data.get("validation")).get("status") in {"pass", "warn"}
    for index, item in enumerate(_sequence(data.get("source_files"))):
        source = _mapping(item)
        location = f"$.source_files/{index}"
        if source.get("hash_status") == "present":
            _require_artifact_bytes(
                context, source, location, label_field="label"
            )
        elif source.get("sha256") is not None:
            _fail(
                "LEGACY_DATASET_UNAVAILABLE_SOURCE_HASHED",
                f"{location}/sha256",
                "Unavailable source states cannot self-report a resolved digest.",
            )
        elif positive:
            _block(
                "LEGACY_DATASET_SOURCE_EVIDENCE_UNAVAILABLE",
                location,
                "Pass/warn numerical candidates require every source artifact to resolve.",
            )


@_handler("LEGACY_DATASET_OUTPUT_ARTIFACT_HASH_RESOLVES")
def _dataset_outputs(context: Mapping[str, Any]) -> None:
    data = _current(context, "normalized-dataset")
    for index, item in enumerate(_sequence(data.get("data_files"))):
        _require_artifact_bytes(
            context, _mapping(item), f"$.data_files/{index}"
        )


@_handler("LEGACY_DATASET_TOOL_LINEAGE_PREEXISTS")
def _dataset_tool_lineage(context: Mapping[str, Any]) -> None:
    data = _current(context, "normalized-dataset")
    execution_ids = list(
        _sequence(_mapping(data.get("provenance")).get("tool_execution_ids"))
    )
    if len(execution_ids) != len(set(execution_ids)):
        _fail(
            "LEGACY_DATASET_TOOL_IDS_DUPLICATE",
            "$.provenance.tool_execution_ids",
            "Tool execution lineage IDs must be unique.",
        )
    for index, execution_id in enumerate(execution_ids):
        _parent_record(
            context,
            "tool-execution",
            execution_id,
            f"$.provenance.tool_execution_ids/{index}",
        )


@_handler("LEGACY_DATASET_MATURITY_EVIDENCE_CONSISTENT")
def _dataset_maturity(context: Mapping[str, Any]) -> None:
    data = _current(context, "normalized-dataset")
    validation_status = _mapping(data.get("validation")).get("status")
    maturity = data.get("maturity")
    sources = list(_sequence(data.get("source_files")))
    if maturity == "design-only" and validation_status != "block":
        _fail(
            "LEGACY_DATASET_DESIGN_ONLY_POSITIVE",
            "$.maturity",
            "A design-only route cannot emit a pass/warn numerical dataset.",
        )
    if maturity in {
        "format-fixture-validated",
        "real-artifact-validated",
        "tool-integration-validated",
    } and validation_status in {"pass", "warn"}:
        if not sources or any(
            _mapping(source).get("hash_status") != "present" for source in sources
        ):
            _block(
                "LEGACY_DATASET_MATURITY_SOURCE_EVIDENCE_MISSING",
                "$.source_files",
                "This maturity state requires resolved source artifacts.",
            )
    if maturity == "tool-integration-validated":
        execution_ids = list(
            _sequence(_mapping(data.get("provenance")).get("tool_execution_ids"))
        )
        if not execution_ids:
            _block(
                "LEGACY_DATASET_TOOL_INTEGRATION_EVIDENCE_MISSING",
                "$.provenance.tool_execution_ids",
                "Tool-integration maturity requires a prior tool execution.",
            )
        for index, execution_id in enumerate(execution_ids):
            parent = _parent_record(
                context,
                "tool-execution",
                execution_id,
                f"$.provenance.tool_execution_ids/{index}",
            )
            if _mapping(parent.get("data")).get("status") != "succeeded":
                _fail(
                    "LEGACY_DATASET_TOOL_INTEGRATION_NOT_SUCCEEDED",
                    f"$.provenance.tool_execution_ids/{index}",
                    "Tool-integration maturity requires a succeeded execution record.",
                )


@_handler("LEGACY_DATASET_NUMERICAL_CANDIDATE_CEILING")
def _dataset_ceiling(context: Mapping[str, Any]) -> None:
    data = _current(context, "normalized-dataset")
    if _positive_science_text(data.get("limitations")):
        _fail(
            "LEGACY_DATASET_SCIENTIFIC_CLAIM_FORBIDDEN",
            "$.limitations",
            "A normalized dataset cannot assert scientific acceptance or stability.",
        )


# ---------------------------------------------------------------------------
# Postprocess plan


@_handler("LEGACY_PLAN_STATUS_READINESS_CONSISTENT")
def _plan_status(context: Mapping[str, Any]) -> None:
    data = _current(context, "postprocess-plan")
    status = data.get("status")
    blockers = list(_sequence(data.get("blockers")))
    steps = list(_sequence(data.get("steps")))
    backend = _mapping(data.get("backend"))
    required_missing = [
        index
        for index, item in enumerate(_sequence(data.get("source_files")))
        if _mapping(item).get("required") is True
        and _mapping(item).get("present") is not True
    ]
    if status == "planned":
        if (
            blockers
            or required_missing
            or not steps
            or not backend
            or backend.get("available") is not True
            or backend.get("maturity") == "design-only"
        ):
            _fail(
                "LEGACY_PLAN_READY_STATE_MISMATCH",
                "$",
                "Planned requires available non-design backend, all required sources, steps, and no blockers.",
            )
    elif status == "blocked":
        if not blockers or steps:
            _fail(
                "LEGACY_PLAN_BLOCKED_STATE_MISMATCH",
                "$",
                "Blocked plans require stable blockers and cannot advertise executable steps.",
            )


@_handler("LEGACY_PLAN_SOURCE_ARTIFACT_RESOLVES")
def _plan_sources(context: Mapping[str, Any]) -> None:
    data = _current(context, "postprocess-plan")
    for index, item in enumerate(_sequence(data.get("source_files"))):
        source = _mapping(item)
        if source.get("present") is True:
            _require_artifact_presence(
                context, source.get("path"), f"$.source_files/{index}/path"
            )


@_handler("LEGACY_PLAN_STEP_GRAPH_CONSISTENT")
def _plan_graph(context: Mapping[str, Any]) -> None:
    data = _current(context, "postprocess-plan")
    steps = list(_sequence(data.get("steps")))
    if not steps:
        return
    backend = _mapping(data.get("backend"))
    source_paths = {
        item.get("path")
        for item in _sequence(data.get("source_files"))
        if isinstance(item, Mapping) and item.get("present") is True
    }
    step_ids: set[object] = set()
    produced: set[object] = set()
    for index, item in enumerate(steps):
        step = _mapping(item)
        step_id = step.get("step_id")
        if step_id in step_ids:
            _fail(
                "LEGACY_PLAN_STEP_ID_DUPLICATE",
                f"$.steps/{index}/step_id",
                "Step IDs must be unique.",
            )
        step_ids.add(step_id)
        expected_action = (
            "external" if backend.get("kind") == "external-executable" else "python"
        )
        if (
            step.get("adapter") != backend.get("id")
            or step.get("action") != expected_action
        ):
            _fail(
                "LEGACY_PLAN_STEP_BACKEND_MISMATCH",
                f"$.steps/{index}",
                "Step adapter/action does not match the selected backend.",
            )
        inputs = list(_sequence(step.get("inputs")))
        outputs = list(_sequence(step.get("outputs")))
        if len(inputs) != len(set(inputs)) or len(outputs) != len(set(outputs)):
            _fail(
                "LEGACY_PLAN_STEP_FILE_DUPLICATE",
                f"$.steps/{index}",
                "Step input and output labels must be unique.",
            )
        if set(inputs).intersection(outputs):
            _fail(
                "LEGACY_PLAN_STEP_INPLACE_FORBIDDEN",
                f"$.steps/{index}",
                "A fail-closed plan cannot overwrite an input in place.",
            )
        if any(output in source_paths or output in produced for output in outputs):
            _fail(
                "LEGACY_PLAN_OUTPUT_COLLISION",
                f"$.steps/{index}/outputs",
                "Step outputs collide with source or prior output labels.",
            )
        unavailable_inputs = [
            value for value in inputs if value not in source_paths and value not in produced
        ]
        if unavailable_inputs:
            _fail(
                "LEGACY_PLAN_STEP_DEPENDENCY_NOT_PREEXISTING",
                f"$.steps/{index}/inputs",
                "Each step may consume only a source or a topologically earlier output.",
            )
        produced.update(outputs)


@_handler("LEGACY_PLAN_NO_POSITIVE_CLAIM_CEILING")
def _plan_ceiling(context: Mapping[str, Any]) -> None:
    data = _current(context, "postprocess-plan")
    if _positive_science_text(
        {
            "parameters": data.get("parameters"),
            "steps": data.get("steps"),
            "blockers": data.get("blockers"),
        }
    ):
        _fail(
            "LEGACY_PLAN_POSITIVE_SCIENTIFIC_CLAIM_FORBIDDEN",
            "$",
            "A postprocess plan has a no-positive-claim ceiling.",
        )


# ---------------------------------------------------------------------------
# Tool execution


def _execution_plan(context: Mapping[str, Any]) -> Mapping[str, Any]:
    data = _current(context, "tool-execution")
    return _parent_record(
        context, "postprocess-plan", data.get("plan_id"), "$.plan_id"
    )


@_handler("LEGACY_TOOL_EXECUTION_PLAN_LINEAGE_PREEXISTS")
def _execution_lineage(context: Mapping[str, Any]) -> None:
    _execution_plan(context)


@_handler("LEGACY_TOOL_EXECUTION_STATUS_RUNTIME_CONSISTENT")
def _execution_status(context: Mapping[str, Any]) -> None:
    data = _current(context, "tool-execution")
    dry_run = data.get("dry_run")
    status = data.get("status")
    started = _parse_time(data.get("started_utc"))
    finished = _parse_time(data.get("finished_utc"))
    duration = data.get("duration_s")
    return_code = data.get("return_code")
    outputs = list(_sequence(data.get("outputs")))
    logs = (data.get("stdout"), data.get("stderr"))
    if dry_run is True:
        if (
            status != "dry-run"
            or started is not None
            or finished is not None
            or duration is not None
            or return_code is not None
            or outputs
            or any(item is not None for item in logs)
        ):
            _fail(
                "LEGACY_TOOL_DRY_RUN_RUNTIME_EVIDENCE_FORBIDDEN",
                "$",
                "A dry run cannot carry runtime, return-code, log, or output evidence.",
            )
        return
    if status == "dry-run":
        _fail(
            "LEGACY_TOOL_DRY_RUN_FLAG_MISMATCH",
            "$.dry_run",
            "dry-run status requires dry_run=true.",
        )
    if status == "blocked":
        if (
            started is not None
            or finished is not None
            or duration is not None
            or return_code is not None
            or outputs
            or any(item is not None for item in logs)
            or not _sequence(data.get("limitations"))
        ):
            _fail(
                "LEGACY_TOOL_BLOCKED_RUNTIME_EVIDENCE_FORBIDDEN",
                "$",
                "Blocked means no execution evidence and requires a limitation.",
            )
        return
    if started is None or finished is None or not isinstance(duration, (int, float)):
        _fail(
            "LEGACY_TOOL_RUNTIME_EVIDENCE_MISSING",
            "$",
            "Executed states require complete timezone-aware timing evidence.",
        )
    if finished < started:
        _fail(
            "LEGACY_TOOL_TIME_ORDER_INVALID",
            "$.finished_utc",
            "Execution cannot finish before it starts.",
        )
    elapsed = (finished - started).total_seconds()
    duration_value = _finite(duration, "$.duration_s")
    if abs(elapsed - duration_value) > max(2.0, 0.2 * max(elapsed, duration_value)):
        _fail(
            "LEGACY_TOOL_DURATION_MISMATCH",
            "$.duration_s",
            "Monotonic duration is incompatible with recorded wall-clock timestamps.",
        )
    if any(item is None for item in logs):
        _fail(
            "LEGACY_TOOL_LOG_EVIDENCE_MISSING",
            "$",
            "Every executed state requires hashed stdout and stderr records.",
        )
    if status == "succeeded" and return_code != 0:
        _fail(
            "LEGACY_TOOL_SUCCESS_RETURN_CODE_MISMATCH",
            "$.return_code",
            "Succeeded requires return code zero.",
        )
    if status == "failed" and (
        not isinstance(return_code, int)
        or return_code == 0
        or not _sequence(data.get("limitations"))
    ):
        _fail(
            "LEGACY_TOOL_FAILED_STATE_MISMATCH",
            "$",
            "Failed requires nonzero return code and an explicit limitation.",
        )
    if status == "timed-out" and (
        return_code is not None or not _sequence(data.get("limitations"))
    ):
        _fail(
            "LEGACY_TOOL_TIMEOUT_STATE_MISMATCH",
            "$",
            "Timed-out requires null return code and an explicit limitation.",
        )


@_handler("LEGACY_TOOL_EXECUTION_FILE_ARTIFACT_HASH_RESOLVES")
def _execution_files(context: Mapping[str, Any]) -> None:
    data = _current(context, "tool-execution")
    for group in ("inputs", "outputs"):
        for index, item in enumerate(_sequence(data.get(group))):
            _require_artifact_bytes(
                context, _mapping(item), f"$.{group}/{index}"
            )
    for field in ("stdout", "stderr"):
        item = data.get(field)
        if item is not None:
            _require_artifact_bytes(context, _mapping(item), f"$.{field}")


@_handler("LEGACY_TOOL_EXECUTION_PLAN_STEP_CONSISTENT")
def _execution_step(context: Mapping[str, Any]) -> None:
    data = _current(context, "tool-execution")
    parent = _execution_plan(context)
    plan = _mapping(parent.get("data"))
    if plan.get("status") != "planned":
        _fail(
            "LEGACY_TOOL_PLAN_NOT_READY",
            "$.plan_id",
            "A tool execution must derive from a technically ready plan.",
        )
    matches = [
        item
        for item in _sequence(plan.get("steps"))
        if isinstance(item, Mapping) and item.get("step_id") == data.get("step_id")
    ]
    if len(matches) != 1:
        _fail(
            "LEGACY_TOOL_PLAN_STEP_UNRESOLVED",
            "$.step_id",
            "Execution step ID must resolve uniquely in its parent plan.",
        )
    step = matches[0]
    backend = _mapping(plan.get("backend"))
    if data.get("backend") != backend.get("id") or step.get("adapter") != data.get(
        "backend"
    ):
        _fail(
            "LEGACY_TOOL_PLAN_BACKEND_MISMATCH",
            "$.backend",
            "Execution backend differs from the selected plan adapter.",
        )
    if list(_sequence(data.get("command"))) != list(_sequence(step.get("command"))):
        _fail(
            "LEGACY_TOOL_PLAN_COMMAND_MISMATCH",
            "$.command",
            "Executed argv differs from the immutable planned argv.",
        )
    inputs = [item.get("path") for item in _sequence(data.get("inputs")) if isinstance(item, Mapping)]
    outputs = [item.get("path") for item in _sequence(data.get("outputs")) if isinstance(item, Mapping)]
    if inputs != list(_sequence(step.get("inputs"))):
        _fail(
            "LEGACY_TOOL_PLAN_INPUT_MISMATCH",
            "$.inputs",
            "Execution inputs differ from the planned ordered input labels.",
        )
    expected_outputs = list(_sequence(step.get("outputs")))
    if data.get("status") == "succeeded" and outputs != expected_outputs:
        _fail(
            "LEGACY_TOOL_PLAN_OUTPUT_MISMATCH",
            "$.outputs",
            "Succeeded execution outputs differ from the planned ordered outputs.",
        )
    if any(output not in expected_outputs for output in outputs):
        _fail(
            "LEGACY_TOOL_UNPLANNED_OUTPUT",
            "$.outputs",
            "Execution records an output not declared by its plan step.",
        )


@_handler("LEGACY_TOOL_EXECUTION_TECHNICAL_CLAIM_CEILING")
def _execution_ceiling(context: Mapping[str, Any]) -> None:
    data = _current(context, "tool-execution")
    if _positive_science_text(data.get("limitations")):
        _fail(
            "LEGACY_TOOL_SCIENTIFIC_CLAIM_FORBIDDEN",
            "$.limitations",
            "Tool completion cannot assert scientific acceptance or physical validity.",
        )


# ---------------------------------------------------------------------------
# Legacy structure manifest


def _structure(context: Mapping[str, Any]) -> Mapping[str, Any]:
    return _current(context, "structure-manifest")


@_handler("LEGACY_STRUCTURE_STATUS_CHECK_CONSISTENT")
def _structure_status(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    validation = _mapping(data.get("validation"))
    checks = list(_sequence(validation.get("checks")))
    ids = [item.get("id") for item in checks if isinstance(item, Mapping)]
    states = [item.get("status") for item in checks if isinstance(item, Mapping)]
    if not checks or len(ids) != len(checks) or len(ids) != len(set(ids)):
        _fail(
            "LEGACY_STRUCTURE_CHECK_SET_INVALID",
            "$.validation.checks",
            "Structure diagnostics must be nonempty and uniquely identified.",
        )
    expected_validation = (
        "block"
        if any(state in {"fail", "not-run"} for state in states)
        else "warn"
        if any(state == "warn" for state in states)
        else "pass"
    )
    expected_status = {"pass": "PASS", "warn": "WARN", "block": "BLOCK"}[
        expected_validation
    ]
    if validation.get("status") != expected_validation or data.get("status") != expected_status:
        _fail(
            "LEGACY_STRUCTURE_STATUS_AGGREGATE_MISMATCH",
            "$",
            "Top-level and validation statuses are not the exact aggregate of diagnostics.",
        )
    flags = _mapping(data.get("flags"))
    structure = _mapping(data.get("structure"))
    neighbor = _mapping(structure.get("nearest_distances"))
    if data.get("status") == "PASS" and (
        _sequence(flags.get("short_distances"))
        or _sequence(flags.get("partial_occupancy_rows"))
        or _mapping(data.get("parser")).get("status") == "degraded"
        or neighbor.get("neighbor_search_complete") is not True
    ):
        _fail(
            "LEGACY_STRUCTURE_PASS_HIDES_WARNING",
            "$.status",
            "PASS cannot hide short distances, occupancy ambiguity, parser degradation, or incomplete neighbor search.",
        )


@_handler("LEGACY_STRUCTURE_SOURCE_ARTIFACT_HASH_RESOLVES")
def _structure_source_artifact(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    source = _mapping(data.get("source"))
    _require_artifact_bytes(
        context,
        {
            "path": source.get("label"),
            "sha256": source.get("sha256"),
            "bytes": source.get("bytes"),
        },
        "$.source",
    )


def _plain_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(item) for item in value]
    return value


def _fingerprint_digest(fingerprint_input: Mapping[str, Any]) -> str:
    try:
        raw = json.dumps(
            _plain_json(fingerprint_input),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        _fail(
            "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_INVALID",
            "$.structure_identity.fingerprint_input",
            "The fingerprint preimage is not finite canonical JSON data.",
        )
    return hashlib.sha256(raw).hexdigest()


def _structure_fingerprint_input(data: Mapping[str, Any]) -> dict[str, Any]:
    structure = _mapping(data.get("structure"))
    cell = _mapping(structure.get("cell"))
    return {
        "cell_vectors_ang": [
            [
                round(
                    _finite(value, "$.structure.cell.vectors_ang"),
                    _STRUCTURE_FINGERPRINT_DECIMALS,
                )
                for value in row
            ]
            for row in _sequence(cell.get("vectors_ang"))
        ],
        "pbc": [bool(value) for value in _sequence(structure.get("pbc"))],
        "sites": [
            {
                "atomic_number": int(_mapping(site).get("atomic_number")),
                "fractional": [
                    round(
                        _finite(value, "$.structure.sites.fractional") % 1.0,
                        _STRUCTURE_FINGERPRINT_DECIMALS,
                    )
                    for value in _sequence(_mapping(site).get("fractional"))
                ],
            }
            for site in _sequence(structure.get("sites"))
        ],
    }


def _structure_fingerprint(data: Mapping[str, Any]) -> str:
    return _fingerprint_digest(_structure_fingerprint_input(data))


def _quantized(value: object, location: str) -> float:
    rounded = round(_finite(value, location), _STRUCTURE_PUBLISHED_DECIMALS)
    return 0.0 if rounded == 0 else rounded


def _wrapped_quantized(value: object, location: str) -> float:
    rounded = round(
        _finite(value, location) % 1.0,
        _STRUCTURE_PUBLISHED_DECIMALS,
    )
    return 0.0 if rounded in {0.0, 1.0} else rounded


def _require_fingerprint_precision(value: object, location: str) -> float:
    number = _finite(value, location)
    if number != round(number, _STRUCTURE_FINGERPRINT_DECIMALS):
        _fail(
            "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_PRECISION_INVALID",
            location,
            "Fingerprint inputs must be normalized to at most 10 decimal places.",
        )
    return number


def _verify_fingerprint_input_matches_structure(
    data: Mapping[str, Any], fingerprint_input: Mapping[str, Any]
) -> None:
    structure = _mapping(data.get("structure"))
    published_cell = _matrix3(
        _mapping(structure.get("cell")).get("vectors_ang"),
        "$.structure.cell.vectors_ang",
    )
    preimage_cell = _matrix3(
        fingerprint_input.get("cell_vectors_ang"),
        "$.structure_identity.fingerprint_input.cell_vectors_ang",
    )
    for row in range(3):
        for column in range(3):
            preimage_value = _require_fingerprint_precision(
                preimage_cell[row][column],
                f"$.structure_identity.fingerprint_input.cell_vectors_ang/{row}/{column}",
            )
            if _quantized(
                preimage_value,
                "$.structure_identity.fingerprint_input.cell_vectors_ang",
            ) != _quantized(
                published_cell[row][column],
                "$.structure.cell.vectors_ang",
            ):
                _fail(
                    "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_CELL_MISMATCH",
                    f"$.structure_identity.fingerprint_input.cell_vectors_ang/{row}/{column}",
                    "The fingerprint cell differs from the published cell after six-decimal quantization.",
                )

    preimage_pbc = list(_sequence(fingerprint_input.get("pbc")))
    published_pbc = list(_sequence(structure.get("pbc")))
    if (
        len(preimage_pbc) != 3
        or any(not isinstance(value, bool) for value in preimage_pbc)
        or preimage_pbc != published_pbc
    ):
        _fail(
            "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_PBC_MISMATCH",
            "$.structure_identity.fingerprint_input.pbc",
            "The fingerprint periodicity flags differ from the published structure.",
        )

    preimage_sites = list(_sequence(fingerprint_input.get("sites")))
    published_sites = list(_sequence(structure.get("sites")))
    if len(preimage_sites) != len(published_sites):
        _fail(
            "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_SITE_COUNT_MISMATCH",
            "$.structure_identity.fingerprint_input.sites",
            "The ordered fingerprint site count differs from the published site table.",
        )
    for index, (preimage_item, published_item) in enumerate(
        zip(preimage_sites, published_sites)
    ):
        preimage_site = _mapping(preimage_item)
        published_site = _mapping(published_item)
        atomic_number = preimage_site.get("atomic_number")
        if (
            not isinstance(atomic_number, int)
            or isinstance(atomic_number, bool)
            or atomic_number != published_site.get("atomic_number")
        ):
            _fail(
                "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_SITE_ORDER_MISMATCH",
                f"$.structure_identity.fingerprint_input.sites/{index}/atomic_number",
                "Fingerprint atomic numbers must match the published site order exactly.",
            )
        preimage_fractional = _vector(
            preimage_site.get("fractional"),
            3,
            f"$.structure_identity.fingerprint_input.sites/{index}/fractional",
        )
        published_fractional = _vector(
            published_site.get("fractional"),
            3,
            f"$.structure.sites/{index}/fractional",
        )
        for axis, (preimage_value, published_value) in enumerate(
            zip(preimage_fractional, published_fractional)
        ):
            normalized = _require_fingerprint_precision(
                preimage_value,
                f"$.structure_identity.fingerprint_input.sites/{index}/fractional/{axis}",
            )
            if not 0.0 <= normalized <= 1.0:
                _fail(
                    "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_NOT_WRAPPED",
                    f"$.structure_identity.fingerprint_input.sites/{index}/fractional/{axis}",
                    "Fingerprint fractional coordinates must be wrapped into the unit interval.",
                )
            if _wrapped_quantized(
                normalized,
                "$.structure_identity.fingerprint_input.sites.fractional",
            ) != _wrapped_quantized(
                published_value,
                "$.structure.sites.fractional",
            ):
                _fail(
                    "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_COORDINATE_MISMATCH",
                    f"$.structure_identity.fingerprint_input.sites/{index}/fractional/{axis}",
                    "Fingerprint fractional coordinates differ from the published ordered sites after wrapped six-decimal quantization.",
                )


@_handler("LEGACY_STRUCTURE_SOURCE_IDENTITY_CONSISTENT")
def _structure_identity(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    source = _mapping(data.get("source"))
    input_record = _mapping(data.get("input"))
    document = _mapping(data.get("document"))
    selected = _mapping(document.get("selected_block"))
    execution = _mapping(data.get("execution"))
    provenance = _mapping(data.get("provenance"))
    options = _mapping(provenance.get("command_options"))
    source_block = _mapping(source.get("data_block"))
    identities = (
        source_block,
        _mapping(input_record.get("data_block")),
        selected,
        _mapping(execution.get("data_block")),
        _mapping(options.get("data_block")),
    )
    if any(identity != source_block for identity in identities[1:]):
        _fail(
            "LEGACY_STRUCTURE_DATA_BLOCK_IDENTITY_MISMATCH",
            "$.document.selected_block",
            "All duplicated selected data-block identities must match exactly.",
        )
    if (
        source.get("label") != input_record.get("name")
        or source.get("sha256") != input_record.get("sha256")
        or source.get("bytes") != input_record.get("size_bytes")
    ):
        _fail(
            "LEGACY_STRUCTURE_SOURCE_IDENTITY_MISMATCH",
            "$.input",
            "Source and input label/hash/size fields must identify the same exact CIF bytes.",
        )
    expected_id = f"structure-{str(source.get('sha256'))[:16]}-b{source_block.get('index')}"
    if data.get("manifest_id") != expected_id:
        _fail(
            "LEGACY_STRUCTURE_MANIFEST_ID_MISMATCH",
            "$.manifest_id",
            "Manifest ID must be derived from source SHA-256 and selected block index.",
        )
    blocks = list(_sequence(document.get("blocks")))
    matching_blocks = [
        block
        for block in blocks
        if isinstance(block, Mapping)
        and block.get("index") == selected.get("index")
        and block.get("name") == selected.get("name")
    ]
    if len(matching_blocks) != 1:
        _fail(
            "LEGACY_STRUCTURE_SELECTED_BLOCK_UNRESOLVED",
            "$.document.selected_block",
            "Selected data block must resolve uniquely in the parsed document inventory.",
        )
    for field in (
        "short_distance_threshold_ang",
        "neighbor_cutoff_ang",
        "maximum_neighbor_cutoff_ang",
        "symprec",
        "angle_tolerance",
        "bond_match",
    ):
        if execution.get(field) != options.get(field):
            _fail(
                "LEGACY_STRUCTURE_ANALYSIS_OPTION_MISMATCH",
                f"$.execution.{field}",
                "Execution and provenance command options differ.",
            )
    identity = _mapping(data.get("structure_identity"))
    if identity.get("algorithm") != _STRUCTURE_FINGERPRINT_ALGORITHM:
        _fail(
            "LEGACY_STRUCTURE_FINGERPRINT_ALGORITHM_UNSUPPORTED",
            "$.structure_identity.algorithm",
            "The structure fingerprint algorithm is not the supported v1 algorithm.",
        )
    fingerprint_input = identity.get("fingerprint_input")
    canonicalization = identity.get("canonicalization")
    if fingerprint_input is None and canonicalization is None:
        if identity.get("value") != _structure_fingerprint(data):
            _block(
                "LEGACY_STRUCTURE_FINGERPRINT_UNVERIFIABLE",
                "$.structure_identity.value",
                "This backward-compatible record omits the exact fingerprint preimage, and its high-precision v1 identity cannot be reproduced from the six-decimal published structure payload.",
            )
    elif not isinstance(fingerprint_input, Mapping) or canonicalization is None:
        _fail(
            "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_INCOMPLETE",
            "$.structure_identity",
            "Fingerprint input and canonicalization must be present together.",
        )
    else:
        if canonicalization != _STRUCTURE_FINGERPRINT_CANONICALIZATION:
            _fail(
                "LEGACY_STRUCTURE_FINGERPRINT_CANONICALIZATION_UNSUPPORTED",
                "$.structure_identity.canonicalization",
                "The fingerprint canonicalization identifier is unsupported.",
            )
        if identity.get("value") != _fingerprint_digest(fingerprint_input):
            _fail(
                "LEGACY_STRUCTURE_FINGERPRINT_PREIMAGE_HASH_MISMATCH",
                "$.structure_identity.value",
                "The declared fingerprint is not the SHA-256 of the exact published fingerprint input.",
            )
        _verify_fingerprint_input_matches_structure(data, fingerprint_input)


@_handler("LEGACY_STRUCTURE_SITE_COMPOSITION_CONSISTENT")
def _structure_composition(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    structure = _mapping(data.get("structure"))
    sites = list(_sequence(structure.get("sites")))
    if structure.get("atom_count") != len(sites):
        _fail(
            "LEGACY_STRUCTURE_ATOM_COUNT_MISMATCH",
            "$.structure.atom_count",
            "Atom count must equal the complete site table length.",
        )
    indices = [site.get("index") for site in sites if isinstance(site, Mapping)]
    if indices != list(range(len(sites))):
        _fail(
            "LEGACY_STRUCTURE_SITE_INDEX_MISMATCH",
            "$.structure.sites",
            "Site indices must be unique, ordered, and contiguous from zero.",
        )
    counts = Counter()
    styles = _mapping(structure.get("element_styles"))
    for index, item in enumerate(sites):
        site = _mapping(item)
        symbol = site.get("symbol")
        atomic_number = site.get("atomic_number")
        if _ATOMIC_NUMBER.get(symbol) != atomic_number:
            _fail(
                "LEGACY_STRUCTURE_ATOMIC_NUMBER_MISMATCH",
                f"$.structure.sites/{index}",
                "Element symbol and independent atomic number table disagree.",
            )
        if _mapping(styles.get(symbol)).get("atomic_number") != atomic_number:
            _fail(
                "LEGACY_STRUCTURE_STYLE_ELEMENT_MISMATCH",
                f"$.structure.element_styles.{symbol}",
                "Element style atomic number differs from the site identity.",
            )
        counts[symbol] += 1
    if dict(sorted(counts.items())) != dict(
        sorted(_mapping(structure.get("element_counts")).items())
    ):
        _fail(
            "LEGACY_STRUCTURE_ELEMENT_COUNT_MISMATCH",
            "$.structure.element_counts",
            "Element counts must be recomputed from the complete site table.",
        )
    metadata = _mapping(_mapping(data.get("document")).get("metadata"))
    atom_sites = list(_sequence(metadata.get("atom_sites")))
    if metadata.get("atom_site_count") != len(atom_sites):
        _fail(
            "LEGACY_STRUCTURE_SOURCE_SITE_COUNT_MISMATCH",
            "$.document.metadata.atom_site_count",
            "Parsed source atom-site count differs from its row inventory.",
        )
    if structure.get("source_atom_site_count") != metadata.get("atom_site_count"):
        _fail(
            "LEGACY_STRUCTURE_DUPLICATE_SOURCE_COUNT_MISMATCH",
            "$.structure.source_atom_site_count",
            "Duplicated source atom-site counts disagree.",
        )
    document_partial = sorted(_sequence(metadata.get("partial_occupancy_rows")))
    flag_partial = sorted(
        _sequence(_mapping(data.get("flags")).get("partial_occupancy_rows"))
    )
    if document_partial != flag_partial:
        _fail(
            "LEGACY_STRUCTURE_OCCUPANCY_FLAG_MISMATCH",
            "$.flags.partial_occupancy_rows",
            "Partial-occupancy flags differ from parsed source metadata.",
        )


def _cell_metrics(cell: Sequence[Sequence[float]]) -> tuple[list[float], list[float], float]:
    lengths = [math.sqrt(sum(value * value for value in row)) for row in cell]

    def angle(left: Sequence[float], right: Sequence[float]) -> float:
        denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(
            sum(value * value for value in right)
        )
        if denominator == 0:
            return 0.0
        cosine = max(-1.0, min(1.0, sum(a * b for a, b in zip(left, right)) / denominator))
        return math.degrees(math.acos(cosine))

    angles = [angle(cell[1], cell[2]), angle(cell[0], cell[2]), angle(cell[0], cell[1])]
    determinant = (
        cell[0][0] * (cell[1][1] * cell[2][2] - cell[1][2] * cell[2][1])
        - cell[0][1] * (cell[1][0] * cell[2][2] - cell[1][2] * cell[2][0])
        + cell[0][2] * (cell[1][0] * cell[2][1] - cell[1][1] * cell[2][0])
    )
    return lengths, angles, abs(determinant)


@_handler("LEGACY_STRUCTURE_COORDINATE_CELL_CONSISTENT")
def _structure_coordinates(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    structure = _mapping(data.get("structure"))
    cell_record = _mapping(structure.get("cell"))
    cell = _matrix3(cell_record.get("vectors_ang"), "$.structure.cell.vectors_ang")
    lengths, angles, volume = _cell_metrics(cell)
    declared_metrics = [
        cell_record.get("a"),
        cell_record.get("b"),
        cell_record.get("c"),
        cell_record.get("alpha"),
        cell_record.get("beta"),
        cell_record.get("gamma"),
    ]
    for index, (actual, declared) in enumerate(zip(lengths + angles, declared_metrics)):
        if not _close(actual, _finite(declared, f"$.structure.cell.metric/{index}"), tolerance=5e-5):
            _fail(
                "LEGACY_STRUCTURE_CELL_METRIC_MISMATCH",
                "$.structure.cell",
                "Cell lengths/angles do not match the lattice vectors.",
            )
    declared_volume = structure.get("volume_ang3")
    if declared_volume is not None and not _close(
        volume, _finite(declared_volume, "$.structure.volume_ang3"), tolerance=5e-4
    ):
        _fail(
            "LEGACY_STRUCTURE_VOLUME_MISMATCH",
            "$.structure.volume_ang3",
            "Cell volume does not match the lattice determinant.",
        )
    sites = list(_sequence(structure.get("sites")))
    cart_values: list[tuple[float, ...]] = []
    frac_values: list[tuple[float, ...]] = []
    for index, item in enumerate(sites):
        site = _mapping(item)
        fractional = _vector(site.get("fractional"), 3, f"$.structure.sites/{index}/fractional")
        cartesian = _vector(site.get("cartesian_ang"), 3, f"$.structure.sites/{index}/cartesian_ang")
        expected = tuple(
            sum(fractional[row] * cell[row][column] for row in range(3))
            for column in range(3)
        )
        if not _vector_close(cartesian, expected):
            _fail(
                "LEGACY_STRUCTURE_COORDINATE_TRANSFORM_MISMATCH",
                f"$.structure.sites/{index}",
                "Fractional and Cartesian site coordinates disagree with the cell.",
            )
        cart_values.append(cartesian)
        frac_values.append(fractional)
    coordinates = _mapping(structure.get("coordinates"))
    samples = list(_sequence(coordinates.get("coordinate_sample")))
    if coordinates.get("coordinate_sample_limit") != len(samples) or len(samples) != min(len(sites), 10):
        _fail(
            "LEGACY_STRUCTURE_COORDINATE_SAMPLE_COUNT_MISMATCH",
            "$.structure.coordinates.coordinate_sample",
            "Coordinate sample count must match its limit and the first ten sites.",
        )
    for index, sample in enumerate(samples):
        item = _mapping(sample)
        site = _mapping(sites[index])
        if (
            item.get("index") != site.get("index")
            or item.get("symbol") != site.get("symbol")
            or not _vector_close(
                _vector(item.get("cartesian_ang"), 3, "$.structure.coordinates.sample"),
                cart_values[index],
            )
            or not _vector_close(
                _vector(item.get("fractional"), 3, "$.structure.coordinates.sample"),
                frac_values[index],
            )
        ):
            _fail(
                "LEGACY_STRUCTURE_COORDINATE_SAMPLE_MISMATCH",
                f"$.structure.coordinates.coordinate_sample/{index}",
                "Coordinate sample differs from the complete site table.",
            )


def _edge_geometry(
    edge: Mapping[str, Any],
    sites: Sequence[Any],
    cell: Sequence[Sequence[float]],
    location: str,
) -> tuple[int, int, tuple[int, int, int], float, tuple[int, ...]]:
    i = edge.get("i")
    j = edge.get("j")
    if not isinstance(i, int) or not isinstance(j, int) or not (0 <= i < len(sites)) or not (0 <= j < len(sites)):
        _fail(
            "LEGACY_STRUCTURE_NEIGHBOR_SITE_INVALID",
            location,
            "Neighbor endpoints must resolve to site indices.",
        )
    shift_values = _sequence(edge.get("shift"))
    if len(shift_values) != 3 or any(not isinstance(value, int) for value in shift_values):
        _fail(
            "LEGACY_STRUCTURE_NEIGHBOR_SHIFT_INVALID",
            f"{location}/shift",
            "Periodic shift must be an integer vector of length three.",
        )
    shift = tuple(int(value) for value in shift_values)
    left = _mapping(sites[i])
    right = _mapping(sites[j])
    symbols = list(_sequence(edge.get("symbols")))
    if symbols != [left.get("symbol"), right.get("symbol")]:
        _fail(
            "LEGACY_STRUCTURE_NEIGHBOR_SYMBOL_MISMATCH",
            f"{location}/symbols",
            "Neighbor symbols differ from the endpoint sites.",
        )
    left_cart = _vector(left.get("cartesian_ang"), 3, f"{location}/left")
    right_cart = _vector(right.get("cartesian_ang"), 3, f"{location}/right")
    expected_vector = tuple(
        right_cart[column]
        + sum(shift[row] * cell[row][column] for row in range(3))
        - left_cart[column]
        for column in range(3)
    )
    stored_vector = _vector(edge.get("vector_ang"), 3, f"{location}/vector_ang")
    if not _vector_close(stored_vector, expected_vector):
        _fail(
            "LEGACY_STRUCTURE_NEIGHBOR_VECTOR_MISMATCH",
            f"{location}/vector_ang",
            "Neighbor vector does not match sites, cell, and periodic shift.",
        )
    distance = math.sqrt(sum(value * value for value in expected_vector))
    if not _close(distance, _finite(edge.get("distance_ang"), f"{location}/distance_ang")):
        _fail(
            "LEGACY_STRUCTURE_NEIGHBOR_DISTANCE_MISMATCH",
            f"{location}/distance_ang",
            "Neighbor distance does not equal the vector norm.",
        )
    forward = (i, j, *shift)
    reverse = (j, i, *(-value for value in shift))
    key = min(forward, reverse)
    if tuple(_sequence(edge.get("periodic_edge_key"))) != key:
        _fail(
            "LEGACY_STRUCTURE_NEIGHBOR_KEY_MISMATCH",
            f"{location}/periodic_edge_key",
            "Periodic edge key is not the canonical undirected endpoint/shift key.",
        )
    return i, j, shift, distance, key


@_handler("LEGACY_STRUCTURE_NEIGHBOR_SUMMARY_CONSISTENT")
def _structure_neighbors(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    structure = _mapping(data.get("structure"))
    sites = list(_sequence(structure.get("sites")))
    cell = _matrix3(_mapping(structure.get("cell")).get("vectors_ang"), "$.structure.cell.vectors_ang")
    neighbor = _mapping(structure.get("nearest_distances"))
    sample = list(_sequence(neighbor.get("nearest_pairs_sample")))
    pair_count = neighbor.get("pair_count")
    periodic_count = neighbor.get("periodic_edge_count")
    if pair_count != periodic_count or not isinstance(pair_count, int):
        _fail(
            "LEGACY_STRUCTURE_NEIGHBOR_COUNT_MISMATCH",
            "$.structure.nearest_distances",
            "Pair and periodic-edge counts must agree.",
        )
    if len(sample) != min(pair_count, 50):
        _fail(
            "LEGACY_STRUCTURE_NEIGHBOR_SAMPLE_COUNT_MISMATCH",
            "$.structure.nearest_distances.nearest_pairs_sample",
            "Neighbor sample length must equal min(pair_count, 50).",
        )
    keys: set[tuple[int, ...]] = set()
    distances: list[float] = []
    multiplicity = 0
    for index, item in enumerate(sample):
        edge = _mapping(item)
        *_, distance, key = _edge_geometry(
            edge, sites, cell, f"$.structure.nearest_distances.nearest_pairs_sample/{index}"
        )
        if key in keys:
            _fail(
                "LEGACY_STRUCTURE_NEIGHBOR_KEY_DUPLICATE",
                "$.structure.nearest_distances.nearest_pairs_sample",
                "Canonical periodic edge keys must be unique.",
            )
        keys.add(key)
        distances.append(distance)
        multiplicity += int(edge.get("directed_multiplicity", 0))
    directed_count = neighbor.get("directed_neighbor_count")
    if not isinstance(directed_count, int) or directed_count < multiplicity:
        _fail(
            "LEGACY_STRUCTURE_DIRECTED_COUNT_MISMATCH",
            "$.structure.nearest_distances.directed_neighbor_count",
            "Directed count cannot be smaller than sampled edge multiplicities.",
        )
    if pair_count <= 50 and directed_count != multiplicity:
        _fail(
            "LEGACY_STRUCTURE_DIRECTED_COUNT_MISMATCH",
            "$.structure.nearest_distances.directed_neighbor_count",
            "Complete sampled edge multiplicities must sum to directed count.",
        )
    if distances:
        if not _close(min(distances), _finite(neighbor.get("min_distance_ang"), "$.structure.nearest_distances.min_distance_ang")):
            _fail(
                "LEGACY_STRUCTURE_NEIGHBOR_MINIMUM_MISMATCH",
                "$.structure.nearest_distances.min_distance_ang",
                "Minimum neighbor distance differs from the edge inventory.",
            )
        maximum = _finite(neighbor.get("max_distance_within_cutoff_ang"), "$.structure.nearest_distances.max_distance_within_cutoff_ang")
        if pair_count <= 50 and not _close(max(distances), maximum):
            _fail(
                "LEGACY_STRUCTURE_NEIGHBOR_MAXIMUM_MISMATCH",
                "$.structure.nearest_distances.max_distance_within_cutoff_ang",
                "Maximum neighbor distance differs from the complete edge inventory.",
            )
        if pair_count > 50 and maximum + 2e-5 < max(distances):
            _fail(
                "LEGACY_STRUCTURE_NEIGHBOR_MAXIMUM_MISMATCH",
                "$.structure.nearest_distances.max_distance_within_cutoff_ang",
                "Claimed maximum is smaller than a sampled distance.",
            )
    nearest = list(_sequence(neighbor.get("nearest_neighbor_bond_pairs")))
    if neighbor.get("nearest_neighbor_bond_count") != len(nearest):
        _fail(
            "LEGACY_STRUCTURE_NEAREST_BOND_COUNT_MISMATCH",
            "$.structure.nearest_distances.nearest_neighbor_bond_count",
            "Nearest-neighbor bond count differs from its complete pair list.",
        )
    nearest_keys: set[tuple[int, ...]] = set()
    for index, item in enumerate(nearest):
        *_, key = _edge_geometry(
            _mapping(item),
            sites,
            cell,
            f"$.structure.nearest_distances.nearest_neighbor_bond_pairs/{index}",
        )
        if key in nearest_keys:
            _fail(
                "LEGACY_STRUCTURE_NEAREST_BOND_DUPLICATE",
                "$.structure.nearest_distances.nearest_neighbor_bond_pairs",
                "Nearest-neighbor bond pairs must have unique canonical keys.",
            )
        nearest_keys.add(key)
    cutoff = _finite(neighbor.get("neighbor_cutoff_ang"), "$.structure.nearest_distances.neighbor_cutoff_ang")
    maximum_cutoff = _finite(neighbor.get("maximum_neighbor_cutoff_ang"), "$.structure.nearest_distances.maximum_neighbor_cutoff_ang")
    if cutoff > maximum_cutoff:
        _fail(
            "LEGACY_STRUCTURE_NEIGHBOR_CUTOFF_MISMATCH",
            "$.structure.nearest_distances",
            "Effective neighbor cutoff cannot exceed its declared maximum.",
        )


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


@_handler("LEGACY_STRUCTURE_BOND_MATCH_CONSISTENT")
def _structure_bond_match(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    neighbor = _mapping(
        _mapping(data.get("structure")).get("nearest_distances")
    )
    match = _mapping(neighbor.get("bond_length_match"))
    query = _mapping(match.get("query"))
    execution_query = _mapping(_mapping(data.get("execution")).get("bond_match"))
    provenance_query = _mapping(
        _mapping(_mapping(data.get("provenance")).get("command_options")).get(
            "bond_match"
        )
    )
    if query != execution_query or query != provenance_query:
        _fail(
            "LEGACY_STRUCTURE_BOND_QUERY_MISMATCH",
            "$.structure.nearest_distances.bond_length_match.query",
            "Bond query must equal the execution and provenance options.",
        )
    pair = query.get("element_pair")
    target = query.get("target_distance_ang")
    tolerance = _finite(query.get("tolerance_ang"), "$.structure.nearest_distances.bond_length_match.query.tolerance_ang")
    requested = pair is not None or target is not None
    nearest = [
        dict(item)
        for item in _sequence(neighbor.get("nearest_neighbor_bond_pairs"))
        if isinstance(item, Mapping)
    ]
    if not requested:
        if (
            match.get("status") != "NOT_REQUESTED"
            or match.get("candidate_count") != 0
            or match.get("match_count") != 0
            or _sequence(match.get("matches"))
            or match.get("closest_candidate") is not None
        ):
            _fail(
                "LEGACY_STRUCTURE_BOND_NOT_REQUESTED_MISMATCH",
                "$.structure.nearest_distances.bond_length_match",
                "NOT_REQUESTED must not fabricate candidates or matches.",
            )
        return
    normalized_pair = tuple(sorted(pair)) if isinstance(pair, (list, tuple)) else None
    candidates = []
    for edge in nearest:
        if normalized_pair is not None and tuple(sorted(edge.get("symbols", ()))) != normalized_pair:
            continue
        distance = _finite(edge.get("distance_ang"), "$.structure.nearest_distances.bond_length_match")
        delta = abs(distance - float(target)) if target is not None else None
        candidates.append({**edge, "absolute_delta_ang": _rounded(delta)})
    candidates.sort(
        key=lambda item: (
            float(item["absolute_delta_ang"]) if item["absolute_delta_ang"] is not None else 0.0,
            float(item["distance_ang"]),
            int(item["i"]),
            int(item["j"]),
            tuple(item.get("shift", (0, 0, 0))),
        )
    )
    expected_matches = (
        list(candidates)
        if target is None
        else [
            item
            for item in candidates
            if float(item["absolute_delta_ang"]) <= tolerance
        ]
    )
    expected_closest = None if target is None or not candidates else candidates[0]
    expected_status = "MATCHED" if expected_matches else "NO_MATCH"
    if (
        match.get("status") != expected_status
        or match.get("candidate_count") != len(candidates)
        or match.get("match_count") != len(expected_matches)
        or list(_sequence(match.get("matches"))) != expected_matches
        or match.get("closest_candidate") != expected_closest
    ):
        _fail(
            "LEGACY_STRUCTURE_BOND_MATCH_RECOMPUTE_MISMATCH",
            "$.structure.nearest_distances.bond_length_match",
            "Bond candidates, deltas, closest edge, count, or status differ from recomputation.",
        )


@_handler("LEGACY_STRUCTURE_VIEW_ARTIFACTS_RESOLVE")
def _structure_views(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    axes: set[object] = set()
    for index, item in enumerate(_sequence(data.get("views"))):
        view = _mapping(item)
        if view.get("axis") in axes:
            _fail(
                "LEGACY_STRUCTURE_VIEW_AXIS_DUPLICATE",
                f"$.views/{index}/axis",
                "At most one view may represent each cell axis.",
            )
        axes.add(view.get("axis"))
        for field in ("path", "markdown_path"):
            _require_artifact_presence(
                context, view.get(field), f"$.views/{index}/{field}"
            )


@_handler("LEGACY_STRUCTURE_TRANSFORMATION_LINEAGE_PREEXISTS")
def _structure_transformation_lineage(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    records = context.get("records_by_identity")
    if not isinstance(records, Mapping):
        _block(
            "LEGACY_STRUCTURE_PARENT_INDEX_UNAVAILABLE",
            "$.transformations",
            "Bundle record index is unavailable.",
        )
    current_index = _current_index(context)
    for index, item in enumerate(_sequence(data.get("transformations"))):
        transformation = _mapping(item)
        fingerprint = transformation.get("parent_fingerprint")
        candidates = [
            value
            for value in records.values()
            if isinstance(value, Mapping)
            # The dispatcher recursively freezes ``current_record`` and the
            # record index independently, so object identity is not a stable
            # way to exclude the current record.  Topological indices are
            # unique inside a valid bundle and survive that boundary.
            and value.get("index") != current_index
            and value.get("contract_name") == "structure-manifest"
            and isinstance(value.get("data"), Mapping)
            and _mapping(value["data"].get("structure_identity")).get("value")
            == fingerprint
        ]
        if not candidates:
            _block(
                "LEGACY_STRUCTURE_TRANSFORM_PARENT_UNRESOLVED",
                f"$.transformations/{index}/parent_fingerprint",
                "Transformation parent fingerprint does not resolve in the bundle.",
            )
        prior_candidates = [
            candidate
            for candidate in candidates
            if isinstance(candidate.get("index"), int)
            and candidate["index"] < current_index
        ]
        if not prior_candidates:
            _fail(
                "LEGACY_STRUCTURE_TRANSFORM_PARENT_NOT_PREEXISTING",
                f"$.transformations/{index}",
                "A matching transformation parent exists only at the current or a later topological position.",
            )
        if len(prior_candidates) != 1:
            _fail(
                "LEGACY_STRUCTURE_TRANSFORM_PARENT_AMBIGUOUS",
                f"$.transformations/{index}/parent_fingerprint",
                "Transformation parent fingerprint is not unique.",
            )
        parent = prior_candidates[0]
        if (
            parent.get("integrity_verified_active") is not True
            or parent.get("lifecycle") != "active"
        ):
            _block(
                "LEGACY_STRUCTURE_TRANSFORM_PARENT_UNVERIFIED",
                f"$.transformations/{index}",
                "Transformation parent is not active and integrity verified.",
            )
        if not isinstance(parent.get("index"), int) or parent["index"] >= current_index:
            _fail(
                "LEGACY_STRUCTURE_TRANSFORM_PARENT_NOT_PREEXISTING",
                f"$.transformations/{index}",
                "Transformation parent must be topologically earlier.",
            )
        parent_count = _mapping(parent.get("data")).get("structure", {}).get(
            "atom_count"
        )
        mapping = list(_sequence(transformation.get("site_mapping")))
        if len(mapping) != _mapping(data.get("structure")).get("atom_count") or any(
            value is not None
            and (
                not isinstance(value, int)
                or not isinstance(parent_count, int)
                or value < 0
                or value >= parent_count
            )
            for value in mapping
        ):
            _fail(
                "LEGACY_STRUCTURE_TRANSFORM_SITE_MAPPING_INVALID",
                f"$.transformations/{index}/site_mapping",
                "Site mapping must cover every child site and resolve parent indices.",
            )


@_handler("LEGACY_STRUCTURE_NUMERICAL_CANDIDATE_CEILING")
def _structure_ceiling(context: Mapping[str, Any]) -> None:
    data = _structure(context)
    not_assessed = list(_sequence(data.get("not_assessed")))
    limitations = list(_sequence(data.get("limitations")))
    if not not_assessed or not limitations:
        _fail(
            "LEGACY_STRUCTURE_CLAIM_BOUNDARY_MISSING",
            "$",
            "A structure candidate requires explicit limitations and not-assessed domains.",
        )
    joined = " ".join(str(item).lower() for item in not_assessed)
    if not any(token in joined for token in ("physical", "stability", "synthesis")):
        _fail(
            "LEGACY_STRUCTURE_SCIENTIFIC_SCOPE_NOT_EXCLUDED",
            "$.not_assessed",
            "Physical validity, stability, or synthesis must remain explicitly unassessed.",
        )
    if _positive_science_text({"limitations": limitations, "not_assessed": not_assessed}):
        _fail(
            "LEGACY_STRUCTURE_SCIENTIFIC_CLAIM_FORBIDDEN",
            "$",
            "A legacy structure manifest cannot assert stability, physical validity, or scientific acceptance.",
        )


def evaluate(
    obligation_ids: Sequence[str], context: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Evaluate each requested owned obligation exactly once and fail closed."""

    if isinstance(obligation_ids, str):
        requested: Sequence[Any] = (obligation_ids,)
    else:
        try:
            requested = tuple(obligation_ids)
        except TypeError:
            requested = ()
    distinct: list[str] = []
    for item in requested:
        if isinstance(item, str) and item and item not in distinct:
            distinct.append(item)
    results: list[dict[str, Any]] = []
    safe_context = context if isinstance(context, Mapping) else {}
    current_contract = _mapping(safe_context.get("current_record")).get(
        "contract_name"
    )
    for obligation_id in distinct:
        handler = _HANDLERS.get(obligation_id)
        if handler is None:
            results.append(
                _result(
                    obligation_id,
                    "blocked",
                    code="SEMANTIC_OBLIGATION_HANDLER_MISSING",
                    message="No fixed legacy production handler owns this obligation.",
                )
            )
            continue
        if _EXPECTED_CONTRACT[obligation_id] != current_contract:
            results.append(
                _result(
                    obligation_id,
                    "blocked",
                    code="LEGACY_OBLIGATION_CONTRACT_MISMATCH",
                    location="$.contract_name",
                    message="This obligation is not advertised by the current contract.",
                )
            )
            continue
        try:
            handler(safe_context)
        except _Problem as problem:
            results.append(
                _result(
                    obligation_id,
                    problem.status,
                    code=problem.code,
                    location=problem.location,
                    message=problem.message,
                )
            )
        except Exception as exc:
            results.append(
                _result(
                    obligation_id,
                    "blocked",
                    code="LEGACY_SEMANTIC_EVALUATOR_INTERNAL_ERROR",
                    message=(
                        "The fixed evaluator could not complete deterministically: "
                        f"{type(exc).__name__}."
                    ),
                )
            )
        else:
            results.append(
                _result(
                    obligation_id,
                    "pass",
                    message=(
                        "The bounded legacy semantic assertion was established from "
                        "integrity-verified bundle evidence; no scientific acceptance is implied."
                    ),
                )
            )
    return results


if set(_HANDLERS) != OBLIGATION_IDS:
    raise RuntimeError("legacy semantic handler registry is incomplete")


__all__ = [
    "CONTRACT_NAMES",
    "OBLIGATIONS_BY_CONTRACT",
    "OBLIGATION_IDS",
    "evaluate",
]
